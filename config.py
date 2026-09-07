import os
from pathlib import Path
from dotenv import load_dotenv

# 加载本地 .env 文件
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# 大模型配置
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()

# 智能自适应识别：如果是谷歌 Gemini API Key (以 AIza 或 AQ. 开头)，自动配置谷歌官方端点与推荐模型
is_gemini = LLM_API_KEY.startswith("AIza") or LLM_API_KEY.startswith("AQ.")
default_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/" if is_gemini else "https://api.deepseek.com"
default_model = "gemini-3.5-flash-lite" if is_gemini else "deepseek-chat"

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip() or default_base_url
LLM_MODEL = os.getenv("LLM_MODEL", "").strip() or default_model

# 推送渠道配置
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "").strip() or "amenews123138"
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "").strip()
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY", "").strip()
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "").strip()
WECOM_WEBHOOK = os.getenv("WECOM_WEBHOOK", "").strip()
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "").strip()

# 邮件配置 (预设为 Gmail 邮箱)
MAIL_HOST = os.getenv("MAIL_HOST", "").strip() or "smtp.gmail.com"
MAIL_PORT = int(os.getenv("MAIL_PORT", "465").strip() or "465")
MAIL_USER = os.getenv("MAIL_USER", "").strip() or "897418752lb@gmail.com"
MAIL_PASS = os.getenv("MAIL_PASS", "").strip()
MAIL_TO = os.getenv("MAIL_TO", "").strip() or "897418752lb@gmail.com"

# 采集配置
MAX_HOURS_BACK = int(os.getenv("MAX_HOURS_BACK", "24"))
MAX_ITEMS_PER_FEED = int(os.getenv("MAX_ITEMS_PER_FEED", "8"))
