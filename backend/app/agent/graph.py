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
import asyncio
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

# 摘要触发阈值：消息超过此数量时自动总结
MAX_MESSAGES_BEFORE_SUMMARY = 30
KEEP_RECENT_MESSAGES = 10


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

    async def _maybe_summarize(self, config_: dict):
        """如果对话历史过长，自动总结旧消息并用摘要替换"""
        try:
            state = await self.graph.aget_state(config_)
            if not state or not state.values:
                return

            messages = list(state.values.get("messages", []))
            # 只统计人类和 AI 消息（排除工具调用消息）
            human_ai = [m for m in messages if isinstance(m, (HumanMessage, AIMessage)) and m.content]
            if len(human_ai) < MAX_MESSAGES_BEFORE_SUMMARY:
                return

            old_msgs = human_ai[:-KEEP_RECENT_MESSAGES]
            recent_msgs = messages[-KEEP_RECENT_MESSAGES:]

            # 把旧消息拼成摘要材料
            old_text = []
            for m in old_msgs[-20:]:  # 最多拼 20 条用于摘要
                role = "用户" if isinstance(m, HumanMessage) else "Amadeus"
                content = m.content
                if isinstance(content, list):
                    content = str(content)
                if content and len(str(content)) > 5:
                    old_text.append(f"[{role}]: {str(content)[:150]}")

            if not old_text:
                return

            # 让 LLM 总结
            summary_prompt = (
                "请用2-3句话总结以下对话。重点保留：用户个人信息（名字/喜好/计划）、"
                "重要决定、待办事项。用中文。\n\n" + "\n".join(old_text)
            )
            summary_resp = await self.llm.ainvoke([HumanMessage(content=summary_prompt)])
            summary_msg = HumanMessage(content=f"[📝 历史摘要] {summary_resp.content}")

            # 更新状态：摘要 + 最近消息
            new_messages = [summary_msg] + list(recent_msgs)
            await self.graph.aupdate_state(config_, {"messages": new_messages})
            print(f"  🧠 已总结对话历史: {len(human_ai)}条 → 摘要+{len(recent_msgs)}条")

        except Exception as e:
            print(f"  ⚠️ 摘要失败（不影��正常对话）: {e}")

    async def _auto_extract_profile(self, user_msg: str, assistant_reply: str):
        """后台分析对话，自动提取用户画像存入知识库"""
        try:
            # 只对有一定信息量的对话做分析
            if len(user_msg) < 5:
                return

            prompt = (
                "分析以下对话，判断用户是否透露了值得长期记住的个人信息。\n\n"
                f"用户: {user_msg}\n"
                f"Amadeus: {assistant_reply[:200]}\n\n"
                "如果包含以下类型的信息，提取为一句简洁的描述：\n"
                "- 姓名/昵称/称呼偏好\n"
                "- 学校/公司/职业方向\n"
                "- 喜好/兴趣/偏好\n"
                "- 计划/目标/日程\n\n"
                "如果没有值得记住的信息，回复 NONE。\n"
                "如果有，回复一句描述，例如：'用户叫小陆，CS本科在读，喜欢红莉栖，正在准备实习'"
            )
            resp = await self.llm.ainvoke(
                [HumanMessage(content=prompt)],
                # 用较低温度确保稳定输出
            )
            result = resp.content.strip()
            if result and result != "NONE" and len(result) > 3:
                from backend.app.agent.tools import _get_kb
                kb = _get_kb()
                kb.add_document(f"[用户画像] {result}", source="user_profile")
                print(f"  👤 自动提取用户画像: {result[:50]}...")

        except Exception as e:
            pass  # 静默失败，不能影响正常对话

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

        # 对话过长时自动摘要
        await self._maybe_summarize(config_)

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

        # 对话过长时自动摘要
        await self._maybe_summarize(config_)

        # 第一个事件：元信息（thread_id），方便前端建立会话
        yield json.dumps({"type": "meta", "thread_id": tid})

        full_reply = ""
        async for event in self.graph.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config_,
            version="v2",
        ):
            kind = event.get("event", "")
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk", None)
                if chunk and hasattr(chunk, "content") and chunk.content:
                    full_reply += chunk.content
                    yield chunk.content

        # 后台自动提取用户画像
        if full_reply.strip():
            asyncio.create_task(self._auto_extract_profile(message, full_reply))


# 全局单例
_agent_instance: Optional[AmadeusAgent] = None


def get_agent() -> AmadeusAgent:
    """获取 Amadeus Agent 单例（避免重复初始化 LLM 连接）"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AmadeusAgent()
    return _agent_instance
