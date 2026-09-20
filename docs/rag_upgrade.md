# Amadeus RAG 商业化升级说明

## 目标

本次升级不是把 Amadeus 改成普通 Streamlit Demo，而是在现有角色智能体项目上补齐校园实训指导书要求的标准 RAG 能力：

- 文档上传
- MD5 去重
- 知识库文件管理
- Chroma 向量库入库和检索
- `ChatPromptTemplate`
- LCEL 链式调用
- `StrOutputParser`
- RAG 回答来源展示

最终定位：**Agent-RAG 智能助手**。

## 新增后端结构

```text
backend/app/services/
├── knowledge_base_service.py   # 文件上传、MD5、SQLite 元数据
├── vector_store_service.py     # 文档加载、切分、Embedding、Chroma
└── rag_service.py              # PromptTemplate + LLM + OutputParser
```

## 新增 API

| 接口 | 作用 |
|---|---|
| `POST /api/knowledge/upload` | 上传文档并写入知识库 |
| `GET /api/knowledge/files` | 查看知识库文件列表 |
| `DELETE /api/knowledge/files/{file_id}` | 删除文件及其向量片段 |
| `POST /api/rag/chat` | 标准 RAG 文档问答 |

## 支持文件类型

第一阶段支持：

- `.pdf`
- `.docx`
- `.txt`
- `.md`
- `.csv`
- `.json`

## 和指导书的对应关系

| 指导书要求 | Amadeus 实现 |
|---|---|
| 知识库构建 | `KnowledgeBaseService` + `VectorStoreService` |
| MD5 文件校验 | 上传时计算 MD5，重复文件直接跳过 |
| Chroma 向量库 | 继续使用 `data/chroma_db` |
| 文本切分 | `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)` |
| PromptTemplate | `RagService` 中使用 `ChatPromptTemplate` |
| OutputParser | `RagService` 中使用 `StrOutputParser` |
| LCEL | `self.prompt | self.llm | StrOutputParser()` |
| 会话历史 | 主系统使用 LangGraph `AsyncSqliteSaver`，比 `FileChatMessageHistory` 更适合 Agent 状态 |
| 前端页面 | 用 Vue 3 知识库控制台替代 Streamlit，更工程化 |

## 两条问答链路

### 1. 标准 RAG 链路

```text
用户在 RAG Console 提问
→ /api/rag/chat
→ 检索 Chroma
→ PromptTemplate 注入上下文
→ LLM 生成答案
→ 返回 answer + sources
```

适合：严肃文档问答、实训验收、答辩展示。

### 2. Agent-RAG 链路

```text
用户和 Amadeus 聊天
→ LangGraph Agent 判断是否需要检索
→ 调用 search_knowledge_base 工具
→ VectorStoreService 检索 Chroma
→ Amadeus 用角色语气回答
```

适合：角色化 AI 助手、工具调用展示、面试项目亮点。

## 商业化价值

这次升级让项目从“角色聊天 Demo”变成更完整的知识库产品雏形：

- 用户可以上传自己的资料
- 系统能管理知识文件和切片数量
- 回答能展示引用来源
- 后端有清晰服务分层
- 前端有可操作的 RAG 控制台
- Agent 可复用标准知识库能力

简历表述可以写：

> 基于 FastAPI + Vue3 + LangGraph + LangChain 构建 Agent-RAG 智能助手系统，支持文档上传、MD5 去重、Chroma 向量检索、LCEL 检索增强生成、SSE 流式响应、工具调用可视化和 GPT-SoVITS 语音交互。
