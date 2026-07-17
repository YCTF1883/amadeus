"""测试 TTS 常驻进程"""
import asyncio
from tts import synthesize, shutdown

async def main():
    print("首次调用（加载模型 ≈30秒）...")
    audio = await synthesize("やあ、小陸。今日は何の実験をするの？")
    print(f"生成成功，音频大小: {len(audio)} bytes")

    print("\n第二次调用（模型已驻留 ≈3秒）...")
    audio = await synthesize("ふふ、なかなか面白いじゃない。")
    print(f"生成成功，音频大小: {len(audio)} bytes")

    shutdown()
    print("✅ 常驻模式测试通过")

asyncio.run(main())