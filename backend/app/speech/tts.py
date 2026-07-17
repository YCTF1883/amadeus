"""TTS 引擎 — 常驻进程调用 sovits 环境生成红莉栖语音"""
import subprocess
import tempfile
import os
import json

SOVITS_PYTHON = "D:/conda_envs/sovits/python.exe"
WORKER_SCRIPT = os.path.join(os.path.dirname(__file__), "_tts_worker.py")

_worker = None  # 常驻子进程


def _read_until(stream, marker: str):
    """一直读 stdout 直到某行包含 marker，跳过中间所有行"""
    while True:
        line = stream.stdout.readline()
        if not line:
            raise RuntimeError(f"TTS worker 进程意外退出（等待 {marker} 时管道关闭）")
        if marker in line:
            return


def _get_worker():
    """启动或返回 TTS 常驻进程"""
    global _worker
    if _worker is None or _worker.poll() is not None:
        _worker = subprocess.Popen(
            [SOVITS_PYTHON, WORKER_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        _read_until(_worker, "LOADING")
        _read_until(_worker, "READY")
    return _worker


async def synthesize(text: str, instruct: str = "") -> bytes:
    """将日语文本合成红莉栖语音，返回 WAV 音频字节"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        out_path = f.name

    try:
        worker = _get_worker()

        task = json.dumps({"text": text, "output": out_path, "instruct": instruct}, ensure_ascii=True)
        worker.stdin.write(task + "\n")
        worker.stdin.flush()

        # 跳过警告行，读到 OK 或 ERROR
        while True:
            line = worker.stdout.readline()
            if not line:
                raise RuntimeError("TTS worker 进程意外退出（管道关闭）")
            if "OK" in line:
                break
            if "ERROR" in line:
                raise RuntimeError(f"TTS 失败: {line.strip()}")

        with open(out_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)


def shutdown():
    """关闭 TTS 常驻进程（应用退出时调用）"""
    global _worker
    if _worker and _worker.poll() is None:
        _worker.stdin.write("EXIT\n")
        _worker.stdin.flush()
        _worker.wait(timeout=5)
    _worker = None
