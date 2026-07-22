"""
TTS 引擎 — 通过 HTTP 调用 GPT-SoVITS API 生成红莉栖语音

前置条件：GPT-SoVITS API 服务已启动（见 D:\amadeus\start_sovits_api.py）
"""
import httpx
from backend.app.config import config

# Kurisu 模型路径（硬编码，与 start_sovits_api.py 保持一致）
GPT_PATH = "GPT_weights_v4/kurisu-e15.ckpt"
SOVITS_PATH = "SoVITS_weights_v4/kurisu_e8_s9472_l32.pth"
_loaded = False


async def _ensure_model():
    """首次调用时加载 Kurisu 模型权重到 API"""
    global _loaded
    if _loaded:
        return
    async with httpx.AsyncClient(timeout=600.0) as client:
        resp = await client.post(
            f"{config.SOVITS_API_URL}/set_model",
            json={"gpt_model_path": GPT_PATH, "sovits_model_path": SOVITS_PATH},
        )
        resp.raise_for_status()
        print(f"✅ GPT-SoVITS Kurisu 模型已加载")
        _loaded = True


async def synthesize(text: str, language: str = "ja", speed: float = 0.9) -> bytes:
    """调用 GPT-SoVITS API 合成语音，返回 WAV 字节"""
    await _ensure_model()

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{config.SOVITS_API_URL}/",
            json={
                "text": text,
                "text_language": language,
                "speed": speed,
                "top_k": 25,
                "top_p": 1.0,
                "temperature": 1.2,
                "sample_steps": 8,
                "pause_second": 0.5,
            },
        )
        resp.raise_for_status()
        return resp.content
