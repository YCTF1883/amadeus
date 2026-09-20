"""
Pydantic 数据模型 — 定义 API 请求/响应的格式
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from datetime import datetime


class ChatMessage(BaseModel):
    """单条对话消息"""
    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """POST /api/chat 请求体"""
    message: str = Field(..., description="用户输入的消息", min_length=1)
    thread_id: Optional[str] = Field(
        default=None, description="会话ID，不传则开新会话。同一ID共享对话上下文"
    )
    history: Optional[list[ChatMessage]] = Field(
        default=[], description="之前的对话历史（可选）"
    )
    worldline_enabled: bool = Field(
        default=False, description="是否启用世界线推演"
    )
    worldline_mode: Literal["observe", "immersive"] = Field(
        default="observe", description="世界线模式：观测或沉浸"
    )


class ChatResponse(BaseModel):
    """聊天回复"""
    reply: str = Field(..., description="Amadeus 的回复")
    thread_id: str = Field(..., description="当前会话ID，下次请求时带回可继续对话")
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """健康检查返回"""
    status: str = "ok"
    version: str = "0.1.0"
    character: str = "Amadeus — 牧濑红莉栖"


class KnowledgeFile(BaseModel):
    """知识库文件元数据"""
    file_id: str
    filename: str
    md5: str
    size: int
    chunk_count: int = 0
    upload_time: str
    status: str
    error: str = ""
    duplicate: bool = False


class KnowledgeUploadResponse(BaseModel):
    """知识库上传结果"""
    message: str
    file: KnowledgeFile


class RagRequest(BaseModel):
    """标准 RAG 问答请求"""
    question: str = Field(..., description="用户问题", min_length=1)
    k: int = Field(default=4, description="检索片段数量", ge=1, le=10)
    conversation_id: Optional[str] = Field(default=None, description="预留会话ID")


class RagSource(BaseModel):
    """RAG 引用来源"""
    file_id: str = ""
    filename: str = "未知来源"
    source: str = "未知来源"
    score: Optional[float] = None
    snippet: str = ""


class RagResponse(BaseModel):
    """标准 RAG 问答响应"""
    answer: str
    sources: list[RagSource] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
