import os
from dotenv import load_dotenv

load_dotenv()

# Bright Data
BRIGHT_DATA_API_TOKEN = os.getenv("BRIGHT_DATA_API_TOKEN", "")
BRIGHT_DATA_CUSTOMER_ID = os.getenv("BRIGHT_DATA_CUSTOMER_ID", "")
BRIGHT_DATA_UNLOCKER_ZONE = os.getenv("BRIGHT_DATA_UNLOCKER_ZONE", "unlocker")
BRIGHT_DATA_UNLOCKER_PASSWORD = os.getenv("BRIGHT_DATA_UNLOCKER_PASSWORD", "")
# SERP zone — falls back to unlocker zone if not separately configured
BRIGHT_DATA_SERP_ZONE = os.getenv("BRIGHT_DATA_SERP_ZONE", "") or os.getenv("BRIGHT_DATA_UNLOCKER_ZONE", "unlocker")
BRIGHT_DATA_SERP_PASSWORD = os.getenv("BRIGHT_DATA_SERP_PASSWORD", "") or os.getenv("BRIGHT_DATA_UNLOCKER_PASSWORD", "")
BRIGHT_DATA_SCRAPER_ZONE = os.getenv("BRIGHT_DATA_SCRAPER_ZONE", "scraper")
BRIGHT_DATA_SCRAPER_PASSWORD = os.getenv("BRIGHT_DATA_SCRAPER_PASSWORD", "")
BRIGHT_DATA_BROWSER_ZONE = os.getenv("BRIGHT_DATA_BROWSER_ZONE", "browser")
BRIGHT_DATA_BROWSER_PASSWORD = os.getenv("BRIGHT_DATA_BROWSER_PASSWORD", "")

# AI/ML API (aimlapi.com)
AIML_API_KEY = os.getenv("AIML_API_KEY", "")
AIML_API_BASE_URL = os.getenv("AIML_API_BASE_URL", "https://api.aimlapi.com/v1")
AIML_MODEL = os.getenv("AIML_MODEL", "gpt-4o-mini")
AIML_EMBEDDING_MODEL = os.getenv("AIML_EMBEDDING_MODEL", "text-embedding-3-small")

# Cognee
COGNEE_API_KEY = os.getenv("COGNEE_API_KEY", "")
COGNEE_DB_PATH = os.getenv("COGNEE_DB_PATH", "./cognee_data")

# TriggerWare.ai
TRIGGERWARE_API_KEY = os.getenv("TRIGGERWARE_API_KEY", "")
TRIGGERWARE_BASE_URL = os.getenv("TRIGGERWARE_BASE_URL", "https://api.triggerware.ai")
TRIGGERWARE_WEBHOOK_URL = os.getenv("TRIGGERWARE_WEBHOOK_URL", "")

# Speechmatics
SPEECHMATICS_API_KEY = os.getenv("SPEECHMATICS_API_KEY", "")
SPEECHMATICS_BASE_URL = "https://asr.api.speechmatics.com/v2"

# Engine settings
ENGINE_CHECK_INTERVAL_SECONDS = int(os.getenv("ENGINE_CHECK_INTERVAL_SECONDS", "300"))
ANOMALY_SIMILARITY_THRESHOLD = float(os.getenv("ANOMALY_SIMILARITY_THRESHOLD", "0.85"))
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# App
_cors_env = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = ["*"] if _cors_env == "*" else _cors_env.split(",")
SECRET_KEY = os.getenv("SECRET_KEY", "nexusintel-dev-secret-change-in-production")


def bright_data_proxy_url(zone: str, password: str) -> str:
    return (
        f"http://brd-customer-{BRIGHT_DATA_CUSTOMER_ID}"
        f"-zone-{zone}:{password}@brd.superproxy.io:22225"
    )


def is_bright_data_configured() -> bool:
    return bool(BRIGHT_DATA_CUSTOMER_ID and BRIGHT_DATA_UNLOCKER_PASSWORD)


def is_aiml_configured() -> bool:
    return bool(AIML_API_KEY)
