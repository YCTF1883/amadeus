# CLAUDE.md — Amadeus 项目交接文档

## 这是什么

Amadeus 是一个**牧濑红莉栖（Makise Kurisu）主题的 Agent-RAG AI 语音助手**，基于 LangGraph + LangChain + FastAPI + Vue 3 + GPT-SoVITS。支持文字对话、语音合成、网页搜索、邮件发送、文档上传、Chroma 知识库检索和标准 RAG 问答。

**你是接手本项目的新 AI（Claude Code / Codex）。每次开始工作前，请先读完本文和关键文件，理解架构再动手。**

---

## 技术栈一览

| 层 | 技术 | 关键文件 |
|----|------|---------|
| LLM | DeepSeek / 通义千问（OpenAI 兼容接口，通过 `LLM_PROVIDER` 切换） | `backend/app/agent/graph.py` |
| Agent 框架 | LangGraph `create_react_agent`（ReAct 模式） | `backend/app/agent/graph.py` |
| 工具 | 时间/计算/提醒/邮件/知识库/网页搜索/网页抓取 | `backend/app/agent/tools.py` |
| RAG | ChromaDB + BAAI/bge-small-zh-v1.5 + LangChain LCEL 标准链 | `backend/app/rag/knowledge_base.py`, `backend/app/services/*.py` |
| 知识库管理 | 文档上传、MD5 去重、SQLite 文件元数据、来源展示 | `backend/app/services/knowledge_base_service.py`, `frontend/src/composables/useKnowledge.js` |
| 记忆 | SQLite + AsyncSqliteSaver（LangGraph checkpointer） | `backend/app/agent/graph.py:75-79` |
| 后端 | FastAPI + SSE 流式 + WebSocket | `backend/app/main.py` |
| 配置 | python-dotenv，`.env` 文件 | `backend/app/config.py` |
| TTS | GPT-SoVITS HTTP API（Kurisu 语音模型，子进程架构） | `backend/app/speech/tts.py` |
| 前端 | Vue 3 Composition API + Vite | `frontend/src/App.vue` |
| 聊天逻辑 | 自定义 composable，SSE 流式解析 + 工具调用卡片 | `frontend/src/composables/useChat.js` |

---

## 启动方式

```
终端 1: GPT-SoVITS API   → D:/conda_envs/sovits/python.exe D:/amadeus/start_sovits_api.py
终端 2: Amadeus 后端      → cd D:/amadeus; $env:PYTHONIOENCODING="utf-8"; D:/conda_envs/amadeus/python.exe -m uvicorn backend.app.main:app --port 8000
终端 3: Amadeus 前端      → cd D:/amadeus/frontend; npm run dev
```

浏览器打开 `http://localhost:5173`。

---

## 核心架构（读代码前先理解这个）

```
用户发消息（浏览器）
       │
       ▼
FastAPI main.py 收到请求
       │
       ▼
AmadeusAgent.chat_stream()   ← graph.py:219
       │
       ├─ create_react_agent (LLM + Tools + Checkpointer)
       │      │
       │      ├─ Qwen 决定：直接回复 or 调工具？
       │      ├─ 调工具 → 执行 → 结果喂回 LLM → 继续
       │      └─ 不调工具 → 逐字流式输出
       │
       └─ astream_events("v2") → yield token
              │
              ├─ on_chat_model_stream → 文本 token
              ├─ on_tool_start       → JSON 事件（工具卡片）
              ├─ on_tool_end         → JSON 事件（工具结果）
              └─ on_tool_error       → JSON 事件（工具错误）
       │
       ▼
FastAPI StreamingResponse (SSE: text/event-stream)
       │
       ▼
前端 useChat.js 解析 SSE → App.vue 渲染
```

标准 RAG 子系统：

```
文档上传（Vue）
      │
      ▼
POST /api/knowledge/upload
      │
      ├─ KnowledgeBaseService：计算 MD5、文件去重、SQLite 元数据
      ├─ VectorStoreService：文档加载、文本切分、Embedding、写入 Chroma
      └─ RagService：ChatPromptTemplate | LLM | StrOutputParser
      │
      ▼
/api/rag/chat 返回答案 + sources 引用来源
```

---

## 关键设计决策（不要改，改了会坏）

1. **LLM Provider 切换**：`graph.py:37-49` 通过 `config.LLM_PROVIDER` 判断 `qwen` vs `deepseek`，Qwen 用 `extra_body={"enable_thinking": False}` 禁用思维链
2. **流式输出**：用 `astream_events("v2")` 而非 `agent.stream()`（需要捕获工具事件 + 更细粒度控制）
3. **TTS 翻译**：中文 → 日文，白名单过滤保留平假名/片假名/汉字/英文/日文标点（正则：`[^぀-ゟ゠-ヿ一-鿿a-zA-Z0-9。、！？…ー〜！.,]`）
4. **专有名词映射**：翻译 prompt 强制输出片假名（如 凤凰院凶真 → ホウオウインキョウマ，真=ま 不是 しん），`main.py:140-150`
5. **语音模式**：`voice_mode=True` 时回复限制 30 字以内（`graph.py:239-243`）
6. **用户画像**：`_auto_extract_profile()` 后台异步分析，自动存入 ChromaDB（`source="user_profile"`），搜索时 `user_profile` 优先
7. **安全词删除**：`delete_from_knowledge_base` 需要说"一切都是命运石之门的选择"
8. **对话摘要**：超过 30 条消息自动总结，手写实现（非 LangChain SummarizationMiddleware），保留最近 10 条
9. **TTS 参考音频**：`assets/kurisu_ref.wav`，傲娇语气"ロボトミー手術してあんたの前頭葉をかき出すぞ"
10. **标准 RAG 子系统**：不要用它替换 LangGraph Agent；它是对齐实训指导书的文档问答链路，Agent 通过工具复用向量检索能力

---

## 不要做的事

- ❌ 不要改成 `create_agent`（LangChain 新版），当前 `create_react_agent` 是刻意保留的
- ❌ 不要删除 `.env` 内容或提交真实 API Key 到 Git
- ❌ 不要用黑名单过滤翻译字符（要用白名单）
- ❌ 不要改 `extra_body` 为 `model_kwargs`（Qwen 的 `enable_thinking` 必须走 `extra_body`）
- ❌ 不要把 TTS 的语言参数从 `ja` 改成别的
- ❌ 不要去掉 `ensure_ascii=True`（Windows 下 Unicode 保护）

---

## 修改指南

### 加新工具
1. 在 `tools.py` 用 `@tool` 装饰器写函数
2. 加入 `AVAILABLE_TOOLS` 列表
3. 前端 `App.vue` 的 `toolIcon()` / `toolLabel()` 加对应映射

### 改 Agent 行为
- 系统提示词 → `prompts.py` 的 `AMADEUS_SYSTEM_PROMPT`
- 回复长度 → `prompts.py` 或 `graph.py` 的 `voice_instruction`
- 模型参数（temperature 等）→ `config.py`

### 前端改动
- 消息渲染 → `App.vue` 的 `<template>` 中 `message-bubble`
- SSE 事件处理 → `useChat.js` 的 `handleToolStart/End`
- 样式全在 `App.vue` 的 `<style scoped>` 里

---

## 当前状态（2026-09-15）

- ✅ 文字对话：正常（DeepSeek / Qwen 可通过 `.env` 切换）
- ✅ 标准 RAG 子系统：文档上传、MD5 去重、SQLite 文件元数据、Chroma 入库、RAG 问答接口
- ✅ 知识库前端：左侧 RAG Console 支持上传、文件列表、删除、标准 RAG 提问、来源展示
- ✅ 语音合成（TTS）：正常（需启动 GPT-SoVITS API，HTTP 方式调用）
- ✅ 工具调用卡片：前端渲染 tool_start/tool_end 事件（执行中→结果）
- ✅ CRT 扫描线 + 思考动画（4方块闪烁）+ 系统状态面板（右上角）
- ✅ 用户画像自动提取：异步 `asyncio.create_task`，静默失败无提示
- ✅ `.gitignore`：数据库/ChromaDB/模型文件/api key 已排除
- ✅ LangSmith：已关闭（APAC 区域 403 无法解决，`.env` 中注释掉）
- ⚠️ 语音偶有中断：TTS `max_sec=54` 限制导致长文本被截断

---

## 用户（小陆）偏好

- 中文交流，简洁直接
- 正在学习：LangChain/LangGraph → 代码注释要清楚、面试导向
- 不喜欢：幻觉式编造、未经同意改代码、没搞清楚就动手
- 下个项目计划：企业管理相关（FastAPI + create_agent）

---

> **给 Codex/下一任 AI：先读完 graph.py → tools.py → main.py → App.vue 这四个核心文件再开始改代码。遇到不确定的事，先问用户，别猜。**
