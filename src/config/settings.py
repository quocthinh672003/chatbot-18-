import os
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_TTL = int(os.getenv("REDIS_TTL", 604800))  # 7 days

# Venice LLM Configuration
VENICE_BASE_URL = os.getenv("VENICE_BASE_URL", "https://api.venice.ai")
VENICE_API_KEY = os.getenv("VENICE_API_KEY", "")
VENICE_MODEL = os.getenv("VENICE_MODEL", "qwen3-4b")

# Memory Configuration
MAX_TOKEN_LIMIT = int(os.getenv("MAX_TOKEN_LIMIT", 2000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.5))
MEMORY_K = int(os.getenv("MEMORY_K", 5))  # Giữ k message gần nhất

# App Configuration
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
