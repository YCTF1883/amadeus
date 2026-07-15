"""
Pydantic 数据模型 — 定义 API 请求/响应的格式
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """单条对话消息"""
    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """POST /api/chat 请求体"""
    message: str = Field(..., description="用户输入的消息", min_length=1)
    history: Optional[list[ChatMessage]] = Field(
        default=[], description="之前的对话历史（可选）"
    )


class ChatResponse(BaseModel):
    """聊天回复"""
    reply: str = Field(..., description="Amadeus 的回复")
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """健康检查返回"""
    status: str = "ok"
    version: str = "0.1.0"
    character: str = "Amadeus — 牧濑红莉栖"
