import redis
from typing import Optional
from src.config.settings import REDIS_URL, REDIS_TTL


class RedisClient:
    """Redis client service để quản lý connection và operations"""

    def __init__(self):
        """Khởi tạo Redis connection"""
        self.redis_client = redis.from_url(REDIS_URL)
        self.ttl = REDIS_TTL

    def ping(self) -> bool:
        """Kiểm tra kết nối Redis"""
        try:
            return self.redis_client.ping()
        except Exception:
            return False

    def get(self, key: str) -> Optional[str]:
        """Lấy giá trị từ Redis"""
        try:
            return self.redis_client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Lưu giá trị vào Redis với TTL"""
        try:
            expire_time = ttl or self.ttl
            return self.redis_client.setex(key, expire_time, value)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Xóa key từ Redis"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Kiểm tra key có tồn tại không"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False

    def get_connection_info(self) -> dict:
        """Lấy thông tin connection Redis"""
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
