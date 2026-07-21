"""STT 常驻工作进程 — 语音识别（中文）"""
import sys, os, json
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from funasr import AutoModel

print("LOADING", flush=True)
model = AutoModel(
    model = "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    vad_model="fsmn-vad",
    punc_model="ct-punc",
    device="cuda:0",
)

print("READY", flush=True)

for line in sys.stdin:
    line = line.strip()
    if not line: continue
    if line == "EXIT": break
    try:
        task = json.loads(line)
        audio_path = task["audio"]
        result = model.generate(input=audio_path)
        text = result[0]["text"] if result else ""
        print(json.dumps({"text": text}, ensure_ascii=True), flush=True)
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)