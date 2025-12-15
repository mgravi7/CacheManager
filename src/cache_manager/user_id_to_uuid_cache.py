from uuid import UUID
from redis.asyncio import Redis
from .async_cache_base import AsyncCacheBase


class UserIdToUUIDCache(AsyncCacheBase[int, UUID]):
    def __init__(self, redis_client: Redis, ttl: int = 3600):
        super().__init__(
            redis_client,
            namespace="user:id-to-uuid",
            ttl=ttl,
            serializer=lambda v: str(v),
            deserializer=lambda b: UUID(b.decode("utf-8")),
        )

    def _make_key(self, key: int) -> str:
        return f"{self.namespace}:{key}"
