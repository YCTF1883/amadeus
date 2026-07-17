"""
Amadeus Agent 核心 —— LangGraph + DeepSeek

使用 LangGraph 的 ReAct (Reasoning + Acting) 模式：
1. 用户发消息 → LLM 分析
2. LLM 决定：直接回复，还是调用工具？
3. 如果调用工具 → 执行 → 结果喂回 LLM → 继续第 2 步
4. 如果直接回复 → 返回给用户

这个循环由 LangGraph 的 create_react_agent 自动管理
"""
import json
from typing import Optional, AsyncIterator, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pathlib import Path
from backend.app.config import config
from backend.app.agent.prompts import AMADEUS_SYSTEM_PROMPT
from backend.app.agent.tools import AVAILABLE_TOOLS


class AmadeusAgent:
    """Amadeus 智能体 —— 牧濑红莉栖的 AI 分身"""

    def __init__(self):
        """初始化 Agent：连接 DeepSeek，延迟构建 ReAct 图"""
        self._validate_config()

        # 1. 创建 LLM 客户端（DeepSeek 兼容 OpenAI 接口）
        self.llm = ChatOpenAI(
            model=config.DEEPSEEK_MODEL,
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            temperature=config.AGENT_TEMPERATURE,
            streaming=True,  # 开启流式输出
        )

        # 2. 记忆和 Graph 延迟初始化（因为 AsyncSqliteSaver 需要异步环境）
        self.memory = None
        self.graph = None

        # 每个对话会话用唯一 thread_id 隔离记忆
        self._thread_counter = 0

    async def _ensure_initialized(self):
        """首次调用时异步初始化记忆和 Graph"""
        if self.graph is not None:
            return

        # 初始化 SQLite 持久化记忆
        DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "amadeus_memory.db"
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(str(DB_PATH))
        self.memory = AsyncSqliteSaver(conn)
        await self.memory.setup()

        # 构建 ReAct Agent
        self.graph = create_react_agent(
            model=self.llm,
            tools=AVAILABLE_TOOLS,
            checkpointer=self.memory,
            prompt=SystemMessage(content=AMADEUS_SYSTEM_PROMPT),
        )

    def _validate_config(self):
        """检查配置是否就绪"""
        if not config.DEEPSEEK_API_KEY:
            raise ValueError(
                "❌ 未配置 DEEPSEEK_API_KEY！\n"
                "请执行以下步骤：\n"
                "1. 访问 https://platform.deepseek.com 获取 API Key\n"
                "2. 将 .env.example 复制为 .env\n"
                "3. 在 .env 中填入你的 API Key"
            )

    async def _get_thread_id(self) -> str:
        """生成新的会话线程 ID"""
        import uuid
        return f"session_{uuid.uuid4().hex[:8]}"

    async def chat(self, message: str, thread_id: Optional[str] = None) -> tuple[str, str]:
        """
        发送消息，获取完整回复

        Args:
            message: 用户输入
            thread_id: 会话ID，不传则开新会话

        Returns:
            (回复文本, thread_id) — 前端需要保存 thread_id 用于后续对话
        """
        await self._ensure_initialized()

        # 没有传 thread_id 就生成新的
        tid = thread_id or await self._get_thread_id()
        config_ = {"configurable": {"thread_id": tid}}

        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config_,
        )

        last_message = result["messages"][-1]
        return last_message.content, tid

    async def chat_stream(self, message: str, thread_id: Optional[str] = None) -> AsyncIterator[str]:
        """
        流式聊天 —— 一个字一个字地输出，像真人在打字

        Args:
            message: 用户输入
            thread_id: 会话ID，不传则开新会话

        Yields:
            首个 token 是 JSON 元信息 {"type":"meta","thread_id":"..."}
            后续是逐个文本 token（词/字）
        """
        await self._ensure_initialized()

        tid = thread_id or await self._get_thread_id()
        config_ = {"configurable": {"thread_id": tid}}

        # 第一个事件：元信息（thread_id），方便前端建立会话
        yield json.dumps({"type": "meta", "thread_id": tid})

        async for event in self.graph.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config_,
            version="v2",
        ):
            kind = event.get("event", "")
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk", None)
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield chunk.content


# 全局单例
_agent_instance: Optional[AmadeusAgent] = None


def get_agent() -> AmadeusAgent:
    """获取 Amadeus Agent 单例（避免重复初始化 LLM 连接）"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AmadeusAgent()
    return _agent_instance
