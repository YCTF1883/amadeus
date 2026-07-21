"""STT 引擎 — 常驻进程调用 sovits 环境做中文语音识别"""
import subprocess, tempfile, os, json
from backend.app.speech.tts import _read_until

SOVITS_PYTHON = "D:/conda_envs/sovits/python.exe"
WORKER_SCRIPT = os.path.join(os.path.dirname(__file__), "_stt_worker.py")

_worker = None

def _get_worker():
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

async def transcribe(audio_bytes: bytes) -> str:
    """将音频字节识别为中文文本"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        audio_path = f.name

    try:
        worker = _get_worker()
        task = json.dumps({"audio": audio_path}, ensure_ascii=True)
        worker.stdin.write(task + "\n")
        worker.stdin.flush()

        while True:
            line = worker.stdout.readline()
            if not line:
                raise RuntimeError("STT worker 进程意外退出")
            result = json.loads(line)
            if "text" in result:
                return result["text"]
            if "error" in result:
                raise RuntimeError(f"STT 失败: {result['error']}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)