# Amadeus 环境搭建指南

## 前置条件

| 依赖 | 说明 |
|------|------|
| Python 3.11+ | `D:\miniconda3\python.exe` |
| Node.js | 前端 Vite 构建 |
| GPT-SoVITS | `D:\GPT_Project\GPT-SoVITS\` |
| sovits conda 环境 | `D:\conda_envs\sovits\` (Python 3.10 + CUDA 11.8 + PyTorch) |

## 1. 克隆仓库

```bash
git clone <repo-url>
cd amadeus
```

## 2. 环境变量

复制 `.env.example` 为 `.env`，填入各 API Key：

```bash
cp .env.example .env
```

`.env` 已加入 `.gitignore`，不会提交到 GitHub。

## 3. 后端启动

```bash
cd backend
D:\miniconda3\python.exe -m uvicorn app.main:app --reload --port 8000
```

首次启动会自动安装依赖（`pip install -r requirements.txt`）。

## 4. 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 5. 语音合成（可选）

需要 GPT-SoVITS 项目 + Kurisu 训练模型。

### 5.1 启动 TTS API

```bash
D:\conda_envs\sovits\python.exe D:\amadeus\start_sovits_api.py
```

### 5.2 模型文件位置

| 文件 | 路径 |
|------|------|
| GPT 权重 | `D:\GPT_Project\GPT-SoVITS\GPT_weights_v4\kurisu-e15.ckpt` |
| SoVITS 权重 | `D:\GPT_Project\GPT-SoVITS\SoVITS_weights_v4\kurisu_e8_s9472_l32.pth` |
| 参考音频 | `D:\GPT_Project\train_data\kurisu\sliced\crs_0904.wav...` |
| sovits Python | `D:\conda_envs\sovits\python.exe` |

### 5.3 训练数据

800 条牧濑红莉栖日文语音素材（来自官方游戏提取），位于 `D:\GPT_Project\train_data\kurisu\`。

训练流程：音频切片 → ASR 标注 → GPT 训练（15 epoch）→ SoVITS 训练（8 epoch）。

## 6. 项目架构

```
用户输入
  ↓
STT (FunASR 中文识别) ──→ Agent (LangGraph + LLM)
  ↓                              ↓
前端 (Vue 3)  ←── 流式文本  ←── Qwen / DeepSeek API
  ↓
日文翻译 (LLM) → GPT-SoVITS API → 语音输出
```

## 7. API Key 申请

| 服务 | 地址 |
|------|------|
| DeepSeek | https://platform.deepseek.com |
| 阿里百炼 | https://dashscope.console.aliyun.com/apiKey |
| QQ邮箱 SMTP | QQ邮箱设置 → 账户 → POP3/SMTP |

## 8. 常见问题

**Q: TTS 出现 500 错误**
确认 GPT-SoVITS API 已启动（端口 9880），且模型权重路径正确。

**Q: NLTK 错误 `averaged_perceptron_tagger_eng`**
```bash
D:\conda_envs\sovits\python.exe -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"
```
