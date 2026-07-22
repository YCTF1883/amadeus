@echo off
cd /d D:\GPT_Project\GPT-SoVITS
D:\conda_envs\sovits\python.exe api.py -s SoVITS_weights/kurisu_e8_s9472_l32.pth -g GPT_weights/kurisu-e15.ckpt -dr train_data/kurisu/sliced/crs_0893.wav_0000000000_0000082560.wav -dt "demo saidaku no mokuteki wa okane daro?" -dl ja -d cuda -p 9880
pause
