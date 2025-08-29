#tải env, constants (K_LAST_MESSAGES, SUMMARY_THRESHOLD_N,…)
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

VENICE_API_URL = os.getenv("VENICE_API_URL")
VENICE_API_KEY = os.getenv("VENICE_API_KEY")
VENICE_MODEL_CHAT = os.getenv("VENICE_MODEL_CHAT", "venice-chat")
VENICE_MODEL_SUMMARY = os.getenv("VENICE_MODEL_SUMMARY", "venice-summary")

K_LAST_MESSAGES = int(os.getenv("K_LAST_MESSAGES", "5"))
SUMMARY_THRESHOLD_N = int(os.getenv("SUMMARY_THRESHOLD_N", "10"))