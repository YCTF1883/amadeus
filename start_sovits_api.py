"""启动 GPT-SoVITS API 服务（Kurisu 语音合成）
运行方式: D:/conda_envs/sovits/python.exe start_sovits_api.py
"""
import os, subprocess, sys

os.chdir(r"D:\GPT_Project\GPT-SoVITS")

cmd = [
    sys.executable,
    "api.py",
    "-s", "SoVITS_weights_v4/kurisu_e8_s9472_l32.pth",
    "-g", "GPT_weights_v4/kurisu-e15.ckpt",
    "-dr", r"D:\amadeus\assets\kurisu_ref.wav",
    "-dt", "そういうくだらないこと言ってると、ロボトミー手術してあんたの前頭葉をかき出すぞ",
    "-dl", "ja",
    "-d", "cuda",
    "-p", "9880",
]
subprocess.run(cmd)
