"""
Amadeus 后端入口 —— FastAPI 应用

启动方式:
    cd backend
    python -m uvicorn app.main:app --reload --port 8000

API 文档（启动后访问）:
    http://localhost:8000/docs  （Swagger UI）
    http://localhost:8000/redoc （ReDoc）
"""
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from backend.app.agent.graph import get_agent

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
        print("✅ Amadeus Agent 初始化完成")
        print("   角色: 牧濑红莉栖 (Amadeus)")
        print("   LLM: DeepSeek")
    except Exception as e:
        print(f"⚠️  Agent 初始化失败: {e}")
        print("   请检查 .env 文件中的 DEEPSEEK_API_KEY 配置")


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
            async for token in agent.chat_stream(request.message):
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
