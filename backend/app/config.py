"""
Amadeus 配置管理
从 .env 文件和环境变量中读取配置
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """全局配置单例"""

    # --- 安全词 ---
    DELETE_SAFETY_WORD: str = os.getenv("DELETE_SAFETY_WORD", "一切都是命运石之门的选择")

    # --- DeepSeek API ---
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # --- 服务 ---
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # --- Agent ---
    MAX_HISTORY_LENGTH: int = 20  # 最多保留多少轮对话历史
    AGENT_TEMPERATURE: float = 0.7  # 回复的创造性程度

    # --- 邮件 ---
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.qq.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")


    @classmethod
    def validate(cls) -> bool:
        """检查必要配置是否齐全"""
        if not cls.DEEPSEEK_API_KEY or cls.DEEPSEEK_API_KEY == "sk-your-api-key-here":
            print("⚠️  警告：未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置")
            return False
        return True






config = Config()
