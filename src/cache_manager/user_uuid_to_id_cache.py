from uuid import UUID

from redis.asyncio import Redis

from .async_cache_base import AsyncCacheBase


class UserUUIDtoIdCache(AsyncCacheBase[UUID, int]):
    def __init__(self, redis_client: Redis, ttl: int = 3600):
        super().__init__(
            redis_client,
            namespace="user:uuid-to-id",
            ttl=ttl,
            serializer=lambda v: str(v),
            deserializer=lambda b: int(b.decode("utf-8")),
        )

    def _make_key(self, key: UUID) -> str:
        return f"{self.namespace}:{key}"
