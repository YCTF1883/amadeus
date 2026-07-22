# Amadeus — 牧濑红莉栖 AI 助手

## 项目概述

命运石之门主题的智能 Agent，牧濑红莉栖的数字化分身。Python 后端 + Vue 3 前端，DeepSeek 作为 LLM。

## 技术栈

| 层 | 技术 |
|------|------|
| LLM | DeepSeek (OpenAI 兼容，langchain-openai) |
| Agent 框架 | LangGraph + ReAct 模式 |
| 后端 | FastAPI (D:\miniconda3\python.exe, Python 3.13) |
| 前端 | Vue 3 + Vite (端口 5173) |
| 记忆 | AsyncSqliteSaver (Checkpoint) + ChromaDB (长期画像) + Summary Memory ✅ |
| RAG | ChromaDB + bge-small-zh-v1.5 (hf-mirror.com 镜像) |
| 语音识别 | FunASR paraformer-zh (待实现) |
| 语音合成 | Qwen-TTS + Christina-TTS 模型 ✅ |

## 目录结构

```
D:\amadeus\
├── backend\app\
│   ├── main.py              # FastAPI 入口 (含 /ws/voice WebSocket)
│   ├── config.py            # 配置（.env 读取）
│   ├── agent\
│   │   ├── graph.py         # Agent 核心（LangGraph ReAct）
│   │   ├── tools.py         # 8 个工具（时间/计算/提醒/邮件/知识库增删查/网络搜索）
│   │   └── prompts.py       # 红莉栖人设 System Prompt
│   ├── models\schemas.py    # Pydantic 请求/响应模型
│   ├── rag\knowledge_base.py # ChromaDB 向量知识库
│   └── speech\
│       ├── _tts_worker.py   # TTS 常驻子进程 (sovits 环境)
│       └── tts.py           # TTS 引擎封装 (subprocess stdin/stdout)
├── frontend\src\
│   ├── App.vue              # 主组件（Galgame 终端 UI + 语音按钮）
│   ├── composables\
│   │   ├── useChat.js       # SSE 流式聊天 + localStorage thread_id
│   │   └── useVoice.js      # WebSocket 语音客户端
│   └── style.css            # 暗色主题
├── data\                     # amadeus_memory.db + chroma_db
├── live2d\kurisu\           # 角色立绘 PNG
└── .env                     # API Key 等配置
```

## 关键文件路径

| 文件 | 路径 |
|------|------|
| Agent 核心 | `D:\amadeus\backend\app\agent\graph.py` |
| 工具定义 | `D:\amadeus\backend\app\agent\tools.py` |
| 人设 Prompt | `D:\amadeus\backend\app\agent\prompts.py` |
| FastAPI 路由 | `D:\amadeus\backend\app\main.py` |
| 知识库 | `D:\amadeus\backend\app\rag\knowledge_base.py` |
| TTS 引擎 | `D:\amadeus\backend\app\speech\tts.py` |
| TTS Worker | `D:\amadeus\backend\app\speech\_tts_worker.py` |
| 前端主组件 | `D:\amadeus\frontend\src\App.vue` |
| 聊天状态 | `D:\amadeus\frontend\src\composables\useChat.js` |
| 语音客户端 | `D:\amadeus\frontend\src\composables\useVoice.js` |

## 启动方式

```bash
# 后端
cd D:\amadeus\backend
python -m uvicorn app.main:app --reload

# 前端
cd D:\amadeus\frontend
npm run dev
```

## 当前进度

- Phase 1 ✅ Agent 骨架 + 基础对话
- Phase 2 ✅ RAG 知识库 + 邮件 + SQLite 记忆 + 安全删除
- Phase 3 ✅ 前端 UI + TTS 语音合成 + WebSocket 语音通道
- Phase 3.5 ✅ Summary Memory + 自动用户画像提取
- Phase 4 ⏸️ STT 语音识别 + Live2D 模型集成
- Phase 5 ⏸️ 自训练 GPT-SoVITS 红莉栖语音模型 + 动捕
- Phase 6 ⏸️ 打磨

## Phase 3 完成详情（2026-07-17）

### TTS 语音合成
- **模型**: Loke-60000/Christina-TTS (Qwen-TTS 格式, 日语 Kurisu 声音)
- **架构**: 子进程常驻模式 — `_tts_worker.py` 通过 stdin/stdout 接收任务
  - 模型只加载一次，后续调用 ~3s
  - 服务启动时预加载（后台线程），首次请求不等待
- **环境隔离**: TTS 用 `D:\conda_envs\sovits\python.exe` (Python 3.10 + CUDA torch)
  - 主程序用 `D:\miniconda3\python.exe` (Python 3.13, CPU torch)
- **翻译层**: 中文回复 → DeepSeek 译成日语 → TTS 合成
- **WebSocket**: `/ws/voice` 接收文本，返回 WAV 二进制
- **前端**: `useVoice.js` + 每条 assistant 消息末尾的 🔊 按钮

### 遇到的问题及解决

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| flash-attn 警告干扰 stdout 解析 | Qwen-TTS 往 stdout 喷警告 | `_read_until()` 循环跳过垃圾行 |
| stderr=subprocess.PIPE 死锁 | flash-attn 警告填满管道 | 改为 `stderr=subprocess.DEVNULL` |
| TTS worker 管道关闭 | 中文文本传给日语模型导致崩溃 | 加中→日翻译层 |
| `ensure_ascii=False` 日文乱码 | Windows 子进程管道非 ASCII 编码问题 | 改为 `ensure_ascii=True` (\uXXXX) |
| pip 删 torch 后没重装 | 残留 torch 子包 (functorch/torchgen...) 让 scipy 误判，删后 sentence_transformers 需要 torch | 装 CPU 版 torch |
| websockets 版本旧 | langgraph_sdk 需要 >=13.0 | `pip install websockets --upgrade` |
| numpy 版本冲突 | numba 需要 <=2.4, 实际 2.5 | `pip install numpy==2.1.3` |
| Node 版本旧 | Vite 8 需要 >=20.19.0 | 升级到 Node 22.23.1 LTS |
| Christina-TTS 下载 | hf-mirror 浏览器下载文件命名冲突 | 手动下载 + ren 修复文件名 |

### 语音延迟分析

| 环节 | 耗时 |
|------|------|
| 中→日翻译 (DeepSeek API) | ~1s |
| TTS 模型推理 (RTX 4060) | ~3s |
| **合计** | **~4-5s** |

### 已知局限
- Christina-TTS 语速固定、无情绪控制、语调单一
- 后续需用 GPT-SoVITS 自训练带情感标签的红莉栖语音模型
- 无流式 TTS，需等全句生成完才能播放

## Phase 3.5 记忆系统优化（2026-07-17）

### 记忆架构（三层分离）

```
短期记忆 (Checkpoint)
  AsyncSqliteSaver → 对话历史 + 自动摘要
  ↕ 消息超过 30 轮时自动触发

长期记忆 (Store 模拟)
  ChromaDB user_profile → 自动提取用户画像
  ↕ 每次对话后 LLM 后台分析

知识库 (RAG)
  ChromaDB 通用 → 邮件记录、学习资料、手动存储
```

### Summary Memory
- 触发条件：人类 + AI 消息超过 30 条
- 保留最近 10 条消息，更早的用 LLM 总结为 2-3 句话
- 摘要以 `[📝 历史摘要]` 标记插入在消息列表开头
- 只统计 HumanMessage + AIMessage，跳过工具调用消息

### 自动用户画像提取
- 每次对话后后台异步执行（不影响响应速度）
- LLM 判断对话中是否有值得记住的个人信息
- 有则自动写入 ChromaDB，source 标记为 `user_profile`
- 搜索时 `user_profile` 结果优先展示

### 与 ChatGPT 建议的对比

| 建议 | 实现方式 | 状态 |
|------|----------|:---:|
| Store 长期记忆 | ChromaDB user_profile 模拟 | ✅ |
| Memory 自动提取 | 后台 LLM 分析 → user_profile | ✅ |
| Summary Memory | _maybe_summarize() 方案 | ✅ |
| Semantic Memory | ChromaDB 语义搜索（已有） | ✅ |
| Postgres/Redis | 暂不需要 | ⏸️ |

## 项目特性

- HuggingFace 用 `hf-mirror.com` 镜像（国内网络）
- 邮件自动存入知识库方便后续查询
- Prompt 要求 Agent 主动搜知识库，不说"让我查一下"
- 前端: 代码雨背景 + 世界线变动率 1.048596% + Kurisu 立绘呼吸光晕
- thread_id 自动存 localStorage，刷新/重启不丢会话
- 每条回复可点击 🔊 播放红莉栖语音

## 用户偏好

- 用户是小陆（CS 本科，Java/AI 方向，准备实习）
- 中文交流，用户手写代码，我辅助/解答
- 不擅自改代码（除非用户要求）
- 回复简洁，面试导向
