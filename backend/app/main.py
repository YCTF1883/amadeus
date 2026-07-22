"""
Amadeus 后端入口 —— FastAPI 应用

启动方式:
    cd backend
    python -m uvicorn app.main:app --reload --port 8000

API 文档（启动后访问）:
    http://localhost:8000/docs  （Swagger UI）
    http://localhost:8000/redoc （ReDoc）
"""
import json
import base64
import traceback
import asyncio
import re
from openai import AsyncOpenAI
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from backend.app.agent.graph import get_agent
from backend.app.speech.tts import synthesize
from backend.app.config import config
# ============================================
# 创建 FastAPI 应用
# ============================================
app = FastAPI(
    title="Amadeus API",
    description="命运石之门风格 AI 助手 —— 牧濑红莉栖的数字化分身",
    version="0.1.0",
)

# 允许跨域请求（前端开发时需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 生命周期事件
# ============================================
@app.on_event("startup")
async def startup():
    """服务启动时初始化 Agent"""
    try:
        get_agent()
        provider = config.LLM_PROVIDER
        model = config.QWEN_MODEL if provider == "qwen" else config.DEEPSEEK_MODEL
        print("✅ Amadeus Agent 初始化完成")
        print("   角色: 牧濑红莉栖 (Amadeus)")
        print(f"   LLM: {provider} / {model}")
    except Exception as e:
        print(f"⚠️  Agent 初始化失败: {e}")
        print("   请检查 .env 文件中的 API Key 配置")

    # 检查 GPT-SoVITS API 是否可达
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{config.SOVITS_API_URL}/")
            print(f"✅ GPT-SoVITS TTS API 已就绪 ({resp.status_code})")
    except Exception as e:
        print(f"⚠️  GPT-SoVITS TTS API 未连接 ({e})")
        print("   请先启动 GPT-SoVITS API 服务")


# ============================================
# API 路由
# ============================================
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """健康检查 —— 确认服务是否正常运行"""
    return HealthResponse()

@app.get("/")
async def root():
    return {"message": "Amadeus 正在运行。去 /docs 和我对话吧。"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口 —— 发送消息给 Amadeus

    示例请求:
    ```json
    {
        "message": "牧濑红莉栖，你今天在做什么？",
        "history": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "哼，有什么事就快说吧。"}
        ]
    }
    ```
    """
    try:
        agent = get_agent()
        reply, thread_id = await agent.chat(
            message=request.message,
            thread_id=request.thread_id,
        )
        return ChatResponse(reply=reply, thread_id=thread_id)

    except ValueError as e:
        # 配置错误（如 API Key 未设置）
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent 调用失败: {str(e)}")


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口 —— 像真人打字一样逐字返回回复

    返回格式: Server-Sent Events (SSE)
    前端用 EventSource 或 fetch + ReadableStream 接收
    """
    try:
        agent = get_agent()

        async def event_generator():
            async for token in agent.chat_stream(
                request.message,
                thread_id=request.thread_id,
            ):
                # SSE 格式：data: <内容>\n\n
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            },
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 中→日翻译（用 DeepSeek 快速翻译）
# ============================================
_translate_client = None


def _get_translate_client():
    global _translate_client
    if _translate_client is None:
        _translate_client = AsyncOpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )
    return _translate_client


async def _to_japanese(text: str) -> str:
    """把中文文本翻译成日文（牧濑红莉栖语气）"""
    client = _get_translate_client()
    resp = await client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个日文翻译助手。把用户输入的中文翻译成日文，"
                    "保持牧濑红莉栖（Makise Kurisu）的语气：自信、略带傲娇、偶尔用科学术语。"
                    "只输出日文译文，不要加任何解释或前缀。\n"
                    "【专有名词映射，输出纯片假名，不要加注音括号】\n"
                    "凤凰院凶真 → ホウオウインキョウマ\n"
                    "牧濑红莉栖 → マキセクリス\n"
                    "克里斯蒂娜 → クリスティーナ\n"
                    "冈部伦太郎 → オカベリンタロウ\n"
                    "桥田至 → ハシダイタル\n"
                    "椎名真由理 → シイナマユリ\n"
                    "漆原琉华 → ウルシバラルカ\n"
                    "菲利斯 → フェイリス\n"
                    "阿万音铃羽 → アマネスズハ\n"
                    "天王寺裕吾 → テンノウジユウゴ\n"
                    "命运石之门 → シュタインズ・ゲート\n"
                    "电话微波炉 → デンワレンジ\n"
                    "时间跳跃机 → タイムリープマシン\n"
                    "时间机器 → タイムマシン\n"
                    "未来道具研究所 → ミライガジェットケンキュウジョ\n"
                    "Amadeus → アマデウス\n"
                    "SERN → セルン\n"
                    "【重要】所有英文单词、数字、专有名词都要翻译成日文片假名。"
                    "只用平假名、片假名、汉字和日文标点（。、！？…ー〜）。"
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=512,
    )
    result = resp.choices[0].message.content.strip()
    # 只保留日文能发音的字符：平假名、片假名、汉字、数字、英文、常用标点
    result = re.sub(r'[^぀-ゟ゠-ヿ一-鿿'
                    r'a-zA-Z0-9。、！？…ー〜！.,]', '', result)
    return result


# ============================================
# WebSocket — 语音通道
# ============================================
@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    print("🔊 语音 WebSocket 已连接")

    try:
        while True:
            text = await websocket.receive_text()

            if not text.strip():
                continue

            print(f"  原文: {text[:40]}...")

            # 中→日翻译
            try:
                ja_text = await _to_japanese(text)
                print(f"  日文: {ja_text[:40]}...")
            except Exception as e:
                print(f"  翻译失败: {e}")
                ja_text = text  # 兜底：原文硬传

            # TTS 合成（instruct 控制语速）
            try:
                audio_bytes = await synthesize(ja_text, language="ja")
                await websocket.send_bytes(audio_bytes)
                print(f"  ✅ 已发送 {len(audio_bytes)} bytes")
            except Exception as e:
                print(f"  TTS 错误: {e}")
                await websocket.send_text(f"ERROR:{e}")

    except WebSocketDisconnect:
        print("🔊 语音 WebSocket 已断开")

# ============================================
# WebSocket — 语音对话（STT + Agent + TTS）
# ============================================
@app.websocket("/ws/voice-chat")
async def voice_chat_websocket(websocket: WebSocket):
    from backend.app.speech.stt import transcribe

    await websocket.accept()
    print("🎤 语音对话 WebSocket 已连接")

    try:
        while True:
            # 接收前端录制的音频（WAV 二进制）
            audio_bytes = await websocket.receive_bytes()

            if len(audio_bytes) < 1000:
                continue  # 太短，跳过

            print(f"  收到音频: {len(audio_bytes)} bytes")

            # 1. STT 识别
            try:
                text = await transcribe(audio_bytes)
                if not text.strip():
                    await websocket.send_text(json.dumps({"type": "error", "data": "没听清"}))
                    continue
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))
                continue

            print(f"  识别结果: {text[:50]}...")
            await websocket.send_text(json.dumps({"type": "stt", "data": text}))

            # 2. Agent 流式思考（中文短回复，显示在聊天窗）
            agent = get_agent()
            full_reply = ""
            async for token in agent.chat_stream(text, voice_mode=True):
                full_reply += token
                if token.strip().startswith('{"type"'):
                    continue
                await websocket.send_text(json.dumps({"type": "text", "data": token}))

            # 告知前端文字输出完成
            await websocket.send_text(json.dumps({"type": "stream_end"}))

            # 3. TTS 后台合成（中文→日语翻译→TTS）
            async def _gen_audio(reply_text: str):
                try:
                    ja_text = await _to_japanese(reply_text)
                    print(f"  日文: {ja_text[:40]}...")
                    audio = await synthesize(ja_text, language="ja")
                    b64 = base64.b64encode(audio).decode("ascii")
                    await websocket.send_text(json.dumps({"type": "audio", "data": b64}))
                    print(f"  ✅ 语音已发送")
                except Exception as e:
                    print(f"  TTS 错误: {e}")
                    await websocket.send_text(json.dumps({"type": "error", "data": f"语音生成失败: {e}"}))

            asyncio.create_task(_gen_audio(full_reply))

    except WebSocketDisconnect:
        print("🎤 语音对话 WebSocket 已断开")




# ============================================
# 直接运行入口
# ============================================
if __name__ == "__main__":
    import uvicorn
    from backend.app.config import config

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=config.SERVER_PORT,
        reload=config.DEBUG,
    )


