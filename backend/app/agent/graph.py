"""
Amadeus Agent 核心 —— LangGraph + DeepSeek

使用 LangGraph 的 ReAct (Reasoning + Acting) 模式：
1. 用户发消息 → LLM 分析
2. LLM 决定：直接回复，还是调用工具？
3. 如果调用工具 → 执行 → 结果喂回 LLM → 继续第 2 步
4. 如果直接回复 → 返回给用户

这个循环由 LangGraph 的 create_react_agent 自动管理
"""
from typing import Optional, AsyncIterator, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from backend.app.config import config
from backend.app.agent.prompts import AMADEUS_SYSTEM_PROMPT
from backend.app.agent.tools import AVAILABLE_TOOLS


class AmadeusAgent:
    """Amadeus 智能体 —— 牧濑红莉栖的 AI 分身"""

    def __init__(self):
        """初始化 Agent：连接 DeepSeek，构建 ReAct 图"""
        self._validate_config()

        # 1. 创建 LLM 客户端（DeepSeek 兼容 OpenAI 接口）
        self.llm = ChatOpenAI(
            model=config.DEEPSEEK_MODEL,
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            temperature=config.AGENT_TEMPERATURE,
            streaming=True,  # 开启流式输出
        )

        # 2. 创建对话记忆（服务重启后会丢失，Phase 2 换持久化方案）
        self.memory = MemorySaver()

        # 3. 构建 ReAct Agent
        self.graph = create_react_agent(
            model=self.llm,
            tools=AVAILABLE_TOOLS,
            checkpointer=self.memory,
            # prompt 参数设置系统提示词，每次调用时自动加到消息列表最前面
            prompt=SystemMessage(content=AMADEUS_SYSTEM_PROMPT),
        )

        # 每个对话会话用唯一 thread_id 隔离记忆
        self._thread_counter = 0

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
        """生成会话线程 ID（用于隔离不同对话的记忆）"""
        self._thread_counter += 1
        return f"session_{self._thread_counter}"

    async def chat(self, message: str, history: Optional[list] = None) -> str:
        """
        发送消息，获取完整回复

        Args:
            message: 用户输入
            history: 之前的对话历史（可选）

        Returns:
            Amadeus 的回复文本
        """
        # 构建消息列表
        messages = []

        # 如果有历史消息，先加入（system prompt 由 state_modifier 自动添加）
        if history:
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

        # 加入当前用户消息
        messages.append(HumanMessage(content=message))

        # 调用 Agent（state_modifier 会自动在开头加上系统提示词）
        config_ = {"configurable": {"thread_id": await self._get_thread_id()}}
        result = await self.graph.ainvoke(
            {"messages": messages},
            config=config_,
        )

        # 提取最后一条 AI 消息
        last_message = result["messages"][-1]
        return last_message.content

    async def chat_stream(self, message: str) -> AsyncIterator[str]:
        """
        流式聊天 —— 一个字一个字地输出，像真人在打字

        Args:
            message: 用户输入

        Yields:
            逐个 token（词/字）
        """
        messages = [HumanMessage(content=message)]
        config_ = {"configurable": {"thread_id": await self._get_thread_id()}}

        # astream_events 可以捕获流式输出的每个 token
        async for event in self.graph.astream_events(
            {"messages": messages},
            config=config_,
            version="v2",
        ):
            # 只处理 LLM 流式输出的 token
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
