"""知识库文件管理服务：上传、MD5 去重、元数据记录。"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from backend.app.services.vector_store_service import get_vector_store_service


DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
UPLOAD_DIR = DATA_DIR / "knowledge_uploads"
DB_PATH = DATA_DIR / "knowledge_files.db"


class KnowledgeBaseService:
    """管理知识库文件生命周期。"""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_files (
                    file_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    md5 TEXT NOT NULL UNIQUE,
                    size INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    upload_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    path TEXT NOT NULL,
                    error TEXT DEFAULT ''
                )
                """
            )
            conn.commit()

    @staticmethod
    def _safe_filename(filename: str) -> str:
        name = os.path.basename(filename or "document.txt")
        return "".join(c for c in name if c not in '<>:"/\\|?*').strip() or "document.txt"

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return dict(row)

    def get_by_md5(self, md5: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_files WHERE md5 = ?",
                (md5,),
            ).fetchone()
        return self._row_to_dict(row)

    def list_files(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM knowledge_files ORDER BY upload_time DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    async def upload_file(self, file: UploadFile) -> dict[str, Any]:
        content = await file.read()
        if not content:
            raise ValueError("上传文件为空")

        md5 = hashlib.md5(content).hexdigest()
        existing = self.get_by_md5(md5)
        if existing:
            existing["duplicate"] = True
            return existing

        file_id = uuid.uuid4().hex
        filename = self._safe_filename(file.filename or "document.txt")
        saved_path = UPLOAD_DIR / f"{file_id}_{filename}"
        saved_path.write_bytes(content)

        record = {
            "file_id": file_id,
            "filename": filename,
            "md5": md5,
            "size": len(content),
            "chunk_count": 0,
            "upload_time": datetime.now().isoformat(timespec="seconds"),
            "status": "processing",
            "path": str(saved_path),
            "error": "",
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO knowledge_files
                (file_id, filename, md5, size, chunk_count, upload_time, status, path, error)
                VALUES (:file_id, :filename, :md5, :size, :chunk_count, :upload_time, :status, :path, :error)
                """,
                record,
            )
            conn.commit()

        try:
            chunk_count = get_vector_store_service().add_file(
                file_path=saved_path,
                file_id=file_id,
                filename=filename,
            )
            record["chunk_count"] = chunk_count
            record["status"] = "ready"
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE knowledge_files
                    SET chunk_count = ?, status = ?, error = ''
                    WHERE file_id = ?
                    """,
                    (chunk_count, "ready", file_id),
                )
                conn.commit()
        except Exception as exc:
            record["status"] = "failed"
            record["error"] = str(exc)
            with self._connect() as conn:
                conn.execute(
                    "UPDATE knowledge_files SET status = ?, error = ? WHERE file_id = ?",
                    ("failed", str(exc), file_id),
                )
                conn.commit()
            raise

        record["duplicate"] = False
        return record

    def delete_file(self, file_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_files WHERE file_id = ?",
                (file_id,),
            ).fetchone()
            if row is None:
                return False

            get_vector_store_service().delete_file(file_id)

            path = Path(row["path"])
            if path.exists():
                path.unlink()

            conn.execute("DELETE FROM knowledge_files WHERE file_id = ?", (file_id,))
            conn.commit()
            return True


_service: KnowledgeBaseService | None = None


def get_knowledge_base_service() -> KnowledgeBaseService:
    global _service
    if _service is None:
        _service = KnowledgeBaseService()
    return _service
