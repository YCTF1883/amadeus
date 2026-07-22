# Amadeus 环境搭建指南

从头搭建 Amadeus 的完整步骤。如果只想要文字对话，TTS 部分可以跳过。

---

## 硬件要求

| 组件 | 最低 | 推荐 |
|------|------|------|
| GPU | 无（TTS 可用 CPU） | RTX 4060 8GB+ |
| 内存 | 8GB | 16GB+ |
| 磁盘 | 2GB（纯代码） | 30GB（含语音模型） |

---

## 1. 必需依赖

| 依赖 | 安装方式 |
|------|---------|
| Git | https://git-scm.com |
| Python 3.11+ | https://www.python.org 或 Miniconda |
| Node.js 18+ | https://nodejs.org |

---

## 2. 克隆并配置

```bash
git clone <repo-url>
cd amadeus
```

### 2.1 环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```ini
# 二选一：DeepSeek 或 Qwen（阿里百炼）
LLM_PROVIDER=qwen                    # deepseek | qwen

# DeepSeek
DEEPSEEK_API_KEY=sk-xxx              # https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Qwen（阿里百炼）
QWEN_API_KEY=sk-xxx                  # https://dashscope.console.aliyun.com/apiKey
QWEN_MODEL=qwen3.7-plus

# QQ邮箱（发邮件功能）
SMTP_USER=你的QQ号@qq.com
SMTP_PASSWORD=授权码                 # QQ邮箱设置 → 账户 → POP3/SMTP 获取
```

其他配置保持默认即可。

---

## 3. 安装项目依赖

### 3.1 后端（Python）

```bash
cd backend
pip install -r requirements.txt
```

### 3.2 前端（Node.js）

```bash
cd frontend
npm install
```

---

## 4. 启动

**终端 1 — 后端：**

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**终端 2 — 前端：**

```bash
cd frontend
npm run dev
```

浏览器打开 `http://localhost:5173`，文字对话即可使用。

---

## 5. 语音合成（TTS）— 可选

语音功能需要三个额外的组件，**它们不在本仓库中**：

| 组件 | 说明 | 大小 |
|------|------|------|
| GPT-SoVITS 项目 | 语音合成框架 | ~5GB |
| Kurisu 训练模型 | GPT + SoVITS 权重 | ~400MB |
| sovits Python 环境 | Python 3.10 + CUDA 11.8 + PyTorch | ~20GB |

### 5.1 克隆 GPT-SoVITS

```bash
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
# 按官方文档创建 conda 环境并安装依赖
```

### 5.2 获取 Kurisu 模型权重

当前模型通过 800 条牧濑红莉栖日文语音训练得到。权重文件需单独获取（不包含在本仓库中）。

放置到 GPT-SoVITS 目录下：

```
GPT_weights_v4/kurisu-e15.ckpt
SoVITS_weights_v4/kurisu_e8_s9472_l32.pth
```

### 5.3 启动 TTS API

```bash
# 用 sovits 环境的 Python 执行
D:\conda_envs\sovits\python.exe start_sovits_api.py
```

看到 `Uvicorn running on http://0.0.0.0:9880` 即成功。

### 5.4 完整启动顺序

```
终端 1: GPT-SoVITS API    ← 语音合成
终端 2: Amadeus 后端       ← Agent + 翻译
终端 3: Amadeus 前端       ← Vite dev server
```

---

## 6. 功能开关

| 功能 | 依赖 | 关掉的方法 |
|------|------|-----------|
| 文字对话 | `.env` 配好 API Key | — |
| 语音按钮 🔊 | TTS API 运行中 | 不启动 TTS API |
| 语音输入 🎤 | 浏览器麦克风权限 | 不点按钮 |
| 发邮件 | QQ邮箱 SMTP 授权码 | 不配 `SMTP_*` |

---

## 7. 常见问题

**Q: 启动后端报 `ModuleNotFoundError`**
```bash
pip install -r requirements.txt
```

**Q: 对话报 `DEEPSEEK_API_KEY` 相关错误**
检查 `.env` 中 `LLM_PROVIDER` 和对应 Key 是否匹配。

**Q: TTS 返回 500**
- 确认 GPT-SoVITS API 已启动（访问 http://127.0.0.1:9880/docs 验证）
- 确认模型权重文件路径正确

**Q: TTS 报 `averaged_perceptron_tagger_eng`**
```bash
D:\conda_envs\sovits\python.exe -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"
```

**Q: Qwen 模型回复带 `<thought>` 标记**
`.env` 中换用 `qwen3.7-flash`，或确认 `LLM_PROVIDER=qwen` 时已自动禁用思维链。

---

## 8. 项目架构

```
浏览器 (Vue 3)
    │
    ├── POST /api/chat/stream    → Agent (LangGraph)
    │                                   │
    │                              DeepSeek / Qwen API
    │
    ├── WebSocket /ws/voice       → STT → 翻译 → TTS API → 语音
    │
    └── WebSocket /ws/voice-chat  → 完整语音对话流程
```
