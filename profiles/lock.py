"""
Redis-based distributed locking mechanism.

Provides thread-safe locking for critical operations like cashouts.
"""
import logging
from typing import Optional, Any

import redis
from django.conf import settings


logger = logging.getLogger('gymgem')


def get_redis_client() -> redis.Redis:
    """
    Get a Redis client using centralized settings.
    """
    return redis.Redis(
        host=getattr(settings, 'REDIS_HOST', '127.0.0.1'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_DB', 0),
        password=getattr(settings, 'REDIS_PASSWORD', None),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


class RedisLock:
    """
    Distributed lock using Redis SET NX with TTL.
    
    Usage:
        with RedisLock("my-lock-key", ttl=300):
            # Critical section
            do_something()
    
    Raises:
        RuntimeError: If lock cannot be acquired.
    """
    
    def __init__(self, key: str, ttl: int = 300) -> None:
        """
        Initialize the lock.
        
        Args:
            key: Unique identifier for this lock.
            ttl: Time-to-live in seconds (default 300 = 5 minutes).
        """
        self.key = key
        self.ttl = ttl
        self._acquired = False

    def __enter__(self) -> 'RedisLock':
        """Attempt to acquire the lock."""
        try:
            client = get_redis_client()
            acquired = client.set(self.key, "1", nx=True, ex=self.ttl)
            
            if not acquired:
                logger.warning("Lock '%s' already held by another process", self.key)
                raise RuntimeError(f"Lock already acquired: {self.key}")
            
            self._acquired = True
            logger.debug("Lock '%s' acquired with TTL=%d", self.key, self.ttl)
            return self
            
        except redis.RedisError as e:
            logger.error("Redis error while acquiring lock '%s': %s", self.key, str(e))
            raise RuntimeError(f"Failed to acquire lock: {e}")

    def __exit__(
        self,
        exc_type: Optional[type],
        exc: Optional[BaseException],
        tb: Any
    ) -> None:
        """Release the lock."""
        if self._acquired:
            try:
                client = get_redis_client()
                client.delete(self.key)
                logger.debug("Lock '%s' released", self.key)
            except redis.RedisError as e:
                logger.error(
                    "Redis error while releasing lock '%s': %s",
                    self.key,
                    str(e)
                )
