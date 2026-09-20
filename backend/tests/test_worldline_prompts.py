import unittest

from backend.app.agent.prompts import AMADEUS_SYSTEM_PROMPT, build_worldline_message


class WorldlinePromptTests(unittest.TestCase):
    def test_system_prompt_allows_detailed_worldline_responses(self):
        self.assertIn("世界线模式时允许展开", AMADEUS_SYSTEM_PROMPT)
        self.assertIn("不要每次都先吐槽", AMADEUS_SYSTEM_PROMPT)
        self.assertIn("纯文本", AMADEUS_SYSTEM_PROMPT)

    def test_disabled_mode_keeps_original_message(self):
        self.assertEqual(
            build_worldline_message("普通问题", enabled=False, mode="observe"),
            "普通问题",
        )

    def test_observe_mode_requires_retrieval_and_analysis(self):
        message = build_worldline_message("如果牛顿没有研究引力？", enabled=True, mode="observe")
        self.assertIn("search_knowledge_base", message)
        self.assertIn("观测模式", message)
        self.assertIn("事实与推测", message)
        self.assertIn("像真人讨论问题", message)
        self.assertIn("不要输出 Markdown", message)
        self.assertNotIn("按以下结构输出", message)

    def test_immersive_mode_requires_retrieval_and_story(self):
        message = build_worldline_message("如果冈部没有发送 D-Mail？", enabled=True, mode="immersive")
        self.assertIn("search_knowledge_base", message)
        self.assertIn("沉浸模式", message)
        self.assertIn("场景", message)
        self.assertIn("自然地讲述", message)
        self.assertIn("不要输出 Markdown", message)



if __name__ == "__main__":
    unittest.main()
