import redis
import os
import threading
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,  # 👈 avoids manual decode
    )


class Cache:
    """Thread-safe singleton Redis cache."""

    _instance: redis.Redis | None = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.client = get_redis_client()

    def set(self, key: str, value: str, expire_seconds: int = 3600) -> None:
        self.client.setex(key, expire_seconds, value)

    def get(self, key: str) -> str | None:
        return self.client.get(key)


__all__ = ["Cache"]
