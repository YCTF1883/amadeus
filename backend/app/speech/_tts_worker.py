"""TTS 常驻工作进程 — 模型只加载一次，通过 stdin/stdout 接收任务"""
import sys
import os
import json
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel

# ============================================
# 启动时加载模型（只这一次）
# ============================================
print("LOADING", flush=True)
model = Qwen3TTSModel.from_pretrained(
    "D:/ai-tools/Christina-TTS",
    device_map="cuda:0",
    dtype=torch.bfloat16,
)
print("READY", flush=True)

# ============================================
# 循环接收任务
# 输入：一行 JSON {"text": "...", "output": "..."}
# 输出：一行 "OK" 或 "ERROR: ..."
# ============================================
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    if line == "EXIT":
        break

    try:
        task = json.loads(line)
        text = task["text"]
        output_path = task["output"]
        instruct = task.get("instruct", "")

        kwargs = {}
        if instruct:
            kwargs["instruct"] = instruct

        wavs, sr = model.generate_custom_voice(
            text=text,
            speaker="christina-jp",
            language="Japanese",
            **kwargs,
        )
        sf.write(output_path, wavs[0], sr)
        print("OK", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
