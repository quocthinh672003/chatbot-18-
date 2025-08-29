#create redis client, helper for key following session_id
import redis
from app.config import REDIS_URL

_redis = redis.from_url(REDIS_URL, decode_responses=True)

def r():
    return _redis

def key_messages(session_id: str) -> str:
    return f"chat:{session_id}:messages"

def key_summary(session_id: str) -> str:
    return f"chat:{session_id}:summary"