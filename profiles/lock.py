import redis
from django.conf import settings

# Lazily build a Redis client to avoid accessing settings at import-time
_redis_client = None

def _build_redis_client():
    host = getattr(settings, "REDIS_HOST", "localhost")
    port = getattr(settings, "REDIS_PORT", 6379)
    db = getattr(settings, "REDIS_DB", 0)
    password = getattr(settings, "REDIS_PASSWORD", None)
    return redis.StrictRedis(host=host, port=port, db=db, password=password)

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = _build_redis_client()
    return _redis_client

class RedisLock:
    def __init__(self, key, ttl=300):
        self.key = key
        self.ttl = ttl

    def __enter__(self):
        client = get_redis_client()
        acquired = client.set(self.key, "1", nx=True, ex=self.ttl)
        if not acquired:
            raise RuntimeError("Lock already acquired")
        return self

    def __exit__(self, exc_type, exc, tb):
        client = get_redis_client()
        client.delete(self.key)
