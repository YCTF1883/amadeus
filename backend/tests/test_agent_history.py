import unittest
from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from backend.app.agent.graph import (
    AmadeusAgent,
    find_unanswered_tool_calls,
    sanitize_interrupted_tool_history,
)


class AgentHistoryTests(unittest.IsolatedAsyncioTestCase):
    def test_sanitize_removes_tool_results_that_arrived_after_user_retries(self):
        interrupted_call = {
            "name": "search_knowledge_base",
            "args": {"query": "牛顿"},
            "id": "call-1",
        }
        messages = [
            HumanMessage(content="如果牛顿没有出生？"),
            AIMessage(content="", tool_calls=[interrupted_call]),
            HumanMessage(content="早上好"),
            ToolMessage(content="调用已中断", tool_call_id="call-1"),
            HumanMessage(content="早上好"),
        ]

        cleaned, removed = sanitize_interrupted_tool_history(messages)

        self.assertEqual(removed, 2)
        self.assertEqual(
            [message.content for message in cleaned],
            ["如果牛顿没有出生？", "早上好", "早上好"],
        )

    def test_find_unanswered_tool_calls_ignores_completed_calls(self):
        messages = [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "search_knowledge_base", "args": {"query": "牛顿"}, "id": "call-1"},
                    {"name": "search_knowledge_base", "args": {"query": "微积分"}, "id": "call-2"},
                ],
            ),
            ToolMessage(content="检索完成", tool_call_id="call-1"),
        ]

        unanswered = find_unanswered_tool_calls(messages)

        self.assertEqual([tool_call["id"] for tool_call in unanswered], ["call-2"])

    async def test_repair_interrupted_tool_calls_rewrites_history_without_broken_exchange(self):
        messages = [
            HumanMessage(content="如果牛顿没有出生？"),
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "search_knowledge_base", "args": {"query": "牛顿"}, "id": "call-1"},
                    {"name": "search_knowledge_base", "args": {"query": "科学革命"}, "id": "call-2"},
                ],
            ),
        ]

        class FakeGraph:
            def __init__(self):
                self.update = None

            async def aget_state(self, config):
                return SimpleNamespace(values={"messages": messages})

            async def aupdate_state(self, config, values, as_node=None):
                self.update = (config, values, as_node)

        graph = FakeGraph()
        agent = AmadeusAgent.__new__(AmadeusAgent)
        agent.graph = graph
        config = {"configurable": {"thread_id": "session_test"}}

        repaired = await agent._repair_interrupted_tool_calls(config)

        self.assertEqual(repaired, 1)
        self.assertEqual(graph.update[0], config)
        self.assertEqual(graph.update[2], "tools")
        replacement = graph.update[1]["messages"]
        self.assertEqual(replacement[0].id, "__remove_all__")
        self.assertEqual([message.content for message in replacement[1:]], ["如果牛顿没有出生？"])


if __name__ == "__main__":
    unittest.main()
