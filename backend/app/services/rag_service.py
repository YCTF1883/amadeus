"""标准 RAG 服务：PromptTemplate + Retriever + LCEL + OutputParser。"""
from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.app.config import config
from backend.app.services.vector_store_service import get_vector_store_service


class RagService:
    """面向文档问答的标准 RAG 链。"""

    def __init__(self):
        provider = config.LLM_PROVIDER
        extra_body = {}
        if provider == "qwen":
            api_key = config.QWEN_API_KEY
            base_url = config.QWEN_BASE_URL
            model = config.QWEN_MODEL
            extra_body = {"enable_thinking": False}
        else:
            api_key = config.DEEPSEEK_API_KEY
            base_url = config.DEEPSEEK_BASE_URL
            model = config.DEEPSEEK_MODEL

        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
            streaming=False,
            extra_body=extra_body,
        )
        self.vector_service = get_vector_store_service()
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "你是 Amadeus 的标准 RAG 问答模块。请严格根据给定知识库上下文回答。"
                "如果上下文没有答案，就说知识库中没有足够信息，不要编造。"
                "回答要清晰、简洁，并保留牧濑红莉栖式的理性语气。",
            ),
            (
                "human",
                "问题：{question}\n\n知识库上下文：\n{context}\n\n请基于上下文回答。",
            ),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    @staticmethod
    def _format_context(results: list[dict[str, Any]]) -> str:
        if not results:
            return ""
        blocks = []
        for idx, item in enumerate(results, 1):
            source = item.get("source") or "未知来源"
            content = item.get("content", "").strip()
            blocks.append(f"[片段{idx} | 来源：{source}]\n{content}")
        return "\n\n".join(blocks)

    @staticmethod
    def _format_sources(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sources = []
        seen = set()
        for item in results:
            key = (item.get("file_id"), item.get("source"), item.get("content", "")[:60])
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                "file_id": item.get("file_id", ""),
                "filename": item.get("filename") or item.get("source") or "未知来源",
                "source": item.get("source") or "未知来源",
                "score": item.get("score"),
                "snippet": item.get("content", "")[:220],
            })
        return sources

    async def ask(self, question: str, k: int = 4) -> dict[str, Any]:
        results = self.vector_service.search_documents(question, k=k)
        context = self._format_context(results)
        if not context:
            return {
                "answer": "知识库中没有找到足够相关的信息。先上传资料再问，实验才有数据基础。",
                "sources": [],
            }

        answer = await self.chain.ainvoke({
            "question": question,
            "context": context,
        })
        return {
            "answer": answer,
            "sources": self._format_sources(results),
        }


_service: RagService | None = None


def get_rag_service() -> RagService:
    global _service
    if _service is None:
        _service = RagService()
    return _service
