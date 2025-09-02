import redis
from typing import Optional
from src.config.settings import REDIS_URL, REDIS_TTL


class RedisClient:
    """Redis client service for managing connection and operations"""

    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(REDIS_URL)
        self.ttl = REDIS_TTL

    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return self.redis_client.ping()
        except Exception:
            return False

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            return self.redis_client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Save value to Redis with TTL"""
        try:
            expire_time = ttl or self.ttl
            return self.redis_client.setex(key, expire_time, value)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False

    def get_connection_info(self) -> dict:
        """Get Redis connection information"""
        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "url": REDIS_URL,
            }
        except Exception:
            return {
                "connected": False,
                "error": "Cannot connect to Redis",
                "url": REDIS_URL,
            }


# Global Redis client instance
redis_client = RedisClient()
