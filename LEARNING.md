# Amadeus 项目学习路线

按优先级分四层，每层标注难度和面试价值。

---

## 🟢 第一层：核心必学（项目面试能讲清楚）

### 1. LangGraph ReAct Agent 模式

**在本项目的体现：** `graph.py` 里的 `create_react_agent`，LLM 自动决定调工具还是直接回复。

**学习目标：**
- ReAct = Reasoning（思考）+ Acting（调用工具），循环直到得出答案
- Agent 的三个组件：LLM（大脑）、Tools（手脚）、Memory（记忆）
- `astream_events` 流式输出原理：按事件类型过滤，`on_chat_model_stream` 就是逐字输出

**资源：** LangGraph 官方文档 → "Quick Start" + "Agent"

**面试话术：** "我做的 Amadeus 项目用 LangGraph 构建了 ReAct Agent，LLM 在每轮对话中可以自主决定查询知识库或直接回复，通过流式事件实现打字机效果。"

---

### 2. RAG + ChromaDB 向量知识库

**在本项目的体现：** `knowledge_base.py`、用户画像自动提取存入 ChromaDB。

**学习目标：**
- RAG = 检索增强生成：把知识切成向量存起来 → 提问时找最相似的片段 → 拼进 prompt
- ChromaDB 是轻量向量数据库，embedding 模型把文本转成向量
- embedding 的直观理解：语义相近的文字，向量空间里距离近
- 本项目的 trick：`user_profile` source 优先级更高（"关于你：" 前缀）

**资源：** LangChain "RAG" tutorial + ChromaDB 官方 Quickstart

**面试话术：** "用 ChromaDB 做用户画像的持久化存储，embedding 用本地模型生成，每次对话后后台异步分析，有新信息自动入库。"

---

### 3. FastAPI + WebSocket

**在本项目的体现：** `main.py` 里 `/ws/voice-chat` 全双工语音对话。

**学习目标：**
- FastAPI 的 async/await 异步模式（`async def` 不是多线程，是单线程事件循环）
- WebSocket vs HTTP：WS 是持久连接，双向推送，适合实时场景
- SSE（Server-Sent Events）用于流式文字推送：`text/event-stream`
- `asyncio.create_task()` 后台任务不阻塞主流程

**资源：** FastAPI 官方 tutorial → WebSocket 章节

**面试话术：** "语音对话用 WebSocket 做全双工通信，文字流式输出用 SSE，TTS 合成用 `asyncio.create_task` 后台异步执行，不阻塞用户看到回复。"

---

## 🟡 第二层：重要补充（让项目完整）

### 4. Vue 3 Composition API

**在本项目的体现：** `App.vue`、`useChat.js`、`useVoiceInput.js`

**学习目标：**
- `ref()` vs `reactive()`：ref 用于基本类型，reactive 用于对象
- `watch()` 监听数据变化自动执行（比如消息更新自动滚到底）
- composable（`useXxx`）就是 Vue 的"自定义 hook"，把逻辑抽成函数复用

**资源：** Vue 3 官方文档 "Composition API"

---

### 5. 流式输出（Streaming）原理

**在本项目的体现：** `chat_stream()` 逐字 yield token → 前端收到一个显示一个。

**学习目标：**
- LLM 生成 token → langgraph `astream_events` 逐事件 yield → FastAPI SSE `text/event-stream` → 前端 fetch ReadableStream
- 为什么比一次性返回体感好：用户不用等完整回复，看到第一个字就"有反馈了"
- 延迟分两种：首 token 延迟（关键）vs 完整回复延迟

**面试话术：** "流式输出把用户感知延迟从 10 秒降到 2 秒——第一个 token 出来用户就知道在回复了。"

---

## 🔵 第三层：进阶理解（加分项）

### 6. GPT-SoVITS 语音合成原理

**在本项目的体现：** Kurisu 语音模型训练 → `api.py` 推理。

**学习目标（不需要会训练，要能讲清楚流程）：**
- GPT 阶段（语义 Token 生成）：把文本变成"语义 token 序列"，决定说什么
- SoVITS 阶段（声学特征合成）：把语义 token + 参考音频 → mel 频谱 → 波形
- 非自回归 vs 自回归：GPT-SoVITS 是前者，一次推理出整段；Christina-TTS 是后者，逐 token 生成，所以慢
- LoRA 微调：不训练整个大模型，只训练一个小矩阵旁路，然后把旁路"加"到原模型上

**面试话术：** "语音克隆的两阶段架构——GPT 负责语义到声学特征的映射，SoVITS 负责从声学特征合成波形。我用 800 条日文语料 + LoRA 微调，在 4060 上 30 分钟就完成了 GPT 阶段训练。"

---

### 7. FunASR / faster-whisper 语音识别

**在本项目的体现：** `stt.py` + `_stt_worker.py`（中文 ASR），训练时用 faster-whisper 做日文标注。

**学习目标：**
- ASR 三组件：VAD（检测有没有人说话）+ ASR（语音→文字）+ 标点恢复
- FunASR 的 paraformer 是非自回归模型，速度快
- faster-whisper 是 OpenAI Whisper 的 CTranslate2 加速版

---

### 8. 子进程架构（Worker Pattern）

**在本项目的体现：** TTS worker、STT worker 都是常驻子进程，通过 stdin/stdout 通信。

**学习目标：**
- 为什么用子进程：模型常驻内存避免每次加载（30 秒→0），管道通信比 HTTP 少一层网络开销
- `_read_until()` 等同步标记：等待特定输出后才认为子进程就绪
- Windows 下的坑：`ensure_ascii=True` 才能保证 Unicode 不损坏

---

## 🟣 第四层：魔鬼在细节（真实项目经验）

### 9. Prompt Engineering 实战

**在本项目的体现：** `prompts.py` 的人设 prompt、翻译 prompt 的专有名词映射表。

**关键技巧：**
- 角色设定的几个要素：身份（我是谁）、性格（怎么说话）、能力边界（能干什么、不能干什么）、规则（硬约束）
- 白名单过滤优于黑名单：`[^平假名-片假名-汉字]` 比"删掉括号、删掉星号…"靠谱
- thinking 模型（如 Qwen）的 `enable_thinking: False` 防止思维链泄露到回复

---

### 10. Windows + CUDA 环境管理

**踩过的坑：**
- torch CUDA 版本必须和 ctranslate2 的 CUDA 版本匹配，否则 DLL 加载失败
- conda 环境隔离：不同项目用不同 Python 版本和环境
- 模型文件结构：训练 checkpoint（含 optimizer 状态）≠ 推理权重（只含 config + weight）

---

## 📅 建议学习顺序

| 周 | 内容 | 时间 |
|----|------|------|
| 第 1 周 | FastAPI + WebSocket + SSE（跟官方 tutorial 写个小 demo） | 3-4 天 |
| 第 2 周 | LangGraph Agent（跑通 Quick Start，理解 ReAct 循环） | 3-4 天 |
| 第 3 周 | RAG + ChromaDB（跟 LangChain RAG tutorial 写个简单问答系统） | 3-4 天 |
| 第 4 周 | Vue 3 Composition API + 流式原理 | 2-3 天 |
| 第 5-6 周 | 语音合成原理 + ASR（理解流程，不强求跑通培训） | 有空就看 |

---

## 🎯 面试场景速查

| 面试官问 | 对应学哪个 |
|----------|-----------|
| "你这个项目的技术架构是什么" | 第 1、2、3 层全讲 |
| "RAG 怎么做" / "向量数据库原理" | 第 2 节 |
| "为什么做流式输出" | 第 5 节 |
| "Agent 怎么实现的" | 第 1 节 |
| "WebSocket 和 HTTP 的区别" | 第 3 节 |
| "语音合成怎么做" | 第 6 节 |
| "Python 异步编程" | 第 3 + 8 节 |
| "Prompt Engineering 经验" | 第 9 节 |
| "遇到什么技术难点" | 第 10 节 + CUDA DLL 兼容性 |
