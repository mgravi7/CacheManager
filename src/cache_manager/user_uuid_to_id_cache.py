from uuid import UUID
from redis.asyncio import Redis
from .async_cache_base import AsyncCacheBase


class UserUUIDtoIdCache(AsyncCacheBase[UUID, int]):
    """
    Cache mapping User UUID to internal User ID.
    
    TTL Recommendations:
    - Default: 600 seconds (10 minutes) - Balanced approach for user profiles
    - 300 seconds (5 minutes) - Use for frequently changing data (e.g., user sessions)
    - 900 seconds (15 minutes) - Use for relatively static data (e.g., user preferences)
    
    The TTL is not enforced but should be chosen based on your use case and
    how frequently user data changes in your system.
    """
    
    def __init__(self, redis_client: Redis, ttl: int = 600):
        """
        Initialize UUID to ID cache.
        
        Args:
            redis_client: Async Redis client instance
            ttl: Time-to-live in seconds (default: 600 = 10 minutes)
        """
        super().__init__(
            redis_client,
            namespace="user:uuid-to-id",
            ttl=ttl,
            serializer=lambda v: str(v),
            deserializer=lambda b: int(b.decode("utf-8")),
        )

    def _make_key(self, key: UUID) -> str:
        return f"{self.namespace}:{key}"
