"""STT 引擎 — 常驻进程调用 sovits 环境做中文语音识别"""
import json
import os
import subprocess
import tempfile

SOVITS_PYTHON = "D:/conda_envs/sovits/python.exe"
WORKER_SCRIPT = os.path.join(os.path.dirname(__file__), "_stt_worker.py")

_worker = None


def _read_until(worker, marker: str):
    """读取工作进程输出，直到出现启动标记或进程退出。"""
    while True:
        line = worker.stdout.readline()
        if not line:
            raise RuntimeError("STT worker 进程在初始化时意外退出")
        if marker in line:
            return

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


def stop_worker(timeout: float = 5.0):
    """停止常驻 STT 工作进程并关闭通信管道。"""
    global _worker
    worker = _worker
    _worker = None
    if worker is None:
        return

    try:
        if worker.poll() is None:
            worker.terminate()
            try:
                worker.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait(timeout=timeout)
    except OSError:
        # 进程可能在 poll 与 terminate 之间自行退出。
        pass
    finally:
        for pipe_name in ("stdin", "stdout"):
            pipe = getattr(worker, pipe_name, None)
            if pipe is not None:
                try:
                    pipe.close()
                except OSError:
                    pass

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
