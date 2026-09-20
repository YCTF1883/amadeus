"""向量库服务：文档加载、切分、写入 Chroma、检索。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader


if not os.environ.get("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"


DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"


class VectorStoreService:
    """封装 Chroma 向量库操作。"""

    def __init__(self):
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
        )
        self.vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=self.embeddings,
        )

    def _load_documents(self, file_path: Path, filename: str) -> list[Document]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return PyPDFLoader(str(file_path)).load()
        if suffix == ".docx":
            return Docx2txtLoader(str(file_path)).load()
        if suffix in {".txt", ".md", ".markdown", ".csv", ".json"}:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            return [Document(page_content=text, metadata={"source": filename})]
        raise ValueError(f"暂不支持的文件类型：{suffix or '未知'}")

    def add_file(self, file_path: Path, file_id: str, filename: str) -> int:
        docs = self._load_documents(file_path, filename)
        if not docs:
            raise ValueError("未能从文件中解析出文本")

        for doc in docs:
            doc.metadata.update({
                "file_id": file_id,
                "filename": filename,
                "source": filename,
                "source_type": "upload",
            })

        chunks = self.text_splitter.split_documents(docs)
        chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
        if not chunks:
            raise ValueError("文档内容为空，无法写入知识库")

        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx

        ids = [f"{file_id}_{idx}" for idx in range(len(chunks))]
        self.vectorstore.add_documents(chunks, ids=ids)
        return len(chunks)

    def add_text(self, text: str, source: str = "对话记录") -> int:
        chunks = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[{"source": source, "source_type": "manual"}],
        )
        self.vectorstore.add_documents(chunks)
        return len(chunks)

    def search_documents(self, query: str, k: int = 4) -> list[dict[str, Any]]:
        try:
            docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        except Exception:
            return []

        results = []
        for doc, score in docs_with_scores:
            results.append({
                "content": doc.page_content,
                "score": float(score),
                "source": doc.metadata.get("source") or doc.metadata.get("filename") or "未知来源",
                "file_id": doc.metadata.get("file_id", ""),
                "filename": doc.metadata.get("filename", doc.metadata.get("source", "")),
                "metadata": dict(doc.metadata),
            })
        return results

    def get_retriever(self, k: int = 4):
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def delete_file(self, file_id: str) -> int:
        records = self.vectorstore.get(where={"file_id": file_id})
        ids = records.get("ids", []) if records else []
        if ids:
            self.vectorstore.delete(ids=ids)
        return len(ids)


def format_search_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "知识库中没有找到相关文档。"

    lines = []
    for idx, item in enumerate(results, 1):
        source = item.get("source") or "未知来源"
        content = item.get("content", "").strip()
        lines.append(f"{idx}. 来源：{source}\n{content}")
    return "\n\n".join(lines)


_service: VectorStoreService | None = None


def get_vector_store_service() -> VectorStoreService:
    global _service
    if _service is None:
        _service = VectorStoreService()
    return _service
