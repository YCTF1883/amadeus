from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import os
from pathlib import Path

class KnowledgeBase:
    """Amadeus 的知识库 —— 基于 ChromaDB + 本地 Embedding"""

    def __init__(self):

        # 1. Embedding 模型：BAAI/bge-small-zh-v1.5
        # 2. 文档切片器：chunk_size=500, chunk_overlap=50
        # 3. ChromaDB 持久化目录：data/chroma_db
        # 4. 初始化或加载向量库
        self.embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""])
        DB_DIR = Path(__file__).parent.parent.parent.parent / "data" / "chroma_db"
        self.persistent_dir = str(DB_DIR)
        os.makedirs(self.persistent_dir, exist_ok=True)
        self.vectorstore = Chroma(persist_directory=self.persistent_dir, embedding_function=self.embeddings)


    def add_document(self, text: str, source: str = "unknown") -> str:
        # 去重：先搜一下是否已有相似内容
        try:
            existing = self.vectorstore.similarity_search_with_score(text, k=1)
            if existing and len(existing) > 0:
                doc, score = existing[0]
                # ChromaDB 默认用 L2 距离，越小越相似。分数 < 0.5 视为重复
                if score < 0.5:
                    return f"知识库中已有相似内容，跳过重复存储。（来源：{source}）"
        except Exception:
            pass  # 空库或搜索失败时正常走插入流程

        # 切片
        chunks = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[{"source": source}]
        )
        # 存库
        self.vectorstore.add_documents(chunks)
        return f"已添加 {len(chunks)} 个文档片段。来源：{source}"

    def search(self, query: str, k: int = 3) -> str:

        # 1. vectorstore.similarity_search(query, k=k)
        # 2. 结果拼成一段文字返回
        docs = self.vectorstore.similarity_search(query, k=k)
        if not docs:
            return "知识库中没有找到相关文档。"

        results = []
        for doc in docs:
            src = doc.metadata.get("source", "未知来源")
            results.append(f"来源：{src}：{doc.page_content}")
        return "\n\n".join(results)


    def load_pdf(self, filepath: str) -> str:
        # 1. PyPDFLoader 加载 PDF
        # 2. 提取文本
        # 3. 调 self.add_document() 批量存入
        loader = PyPDFLoader(filepath)
        pages = loader.load()

        full_text = ""
        for page in pages:
            full_text += page.page_content + "\n"

        filename = os.path.basename(filepath)
        return self.add_document(full_text, source=filename)

    def delete_by_query(self, query: str, k: int = 5) -> str:
        """搜索并删除匹配的文档片段"""
        docs = self.vectorstore.similarity_search(query, k=k)
        if not docs:
            return "知识库中没有找到相关的信息，不需要删除。"

        # 获取这些文档的 ID 并删除
        ids_to_delete = [doc.id for doc in docs if doc.id]
        if ids_to_delete:
            self.vectorstore.delete(ids=ids_to_delete)

        deleted_sources = set(doc.metadata.get("source", "未知") for doc in docs)
        return f"已从知识库中删除 {len(ids_to_delete)} 条相关信息。来源：{', '.join(deleted_sources)}"