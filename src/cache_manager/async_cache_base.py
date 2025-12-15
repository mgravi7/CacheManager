from typing import Generic, TypeVar, Optional, Callable, List, Dict
from uuid import UUID
from redis.asyncio import Redis

K = TypeVar("K")
V = TypeVar("V")


class AsyncCacheBase(Generic[K, V]):
    def __init__(
        self,
        redis_client: Redis,
        namespace: str,
        ttl: Optional[int],
        serializer: Callable[[V], str],
        deserializer: Callable[[bytes], V],
    ):
        self.redis = redis_client
        self.namespace = namespace
        self.ttl = ttl
        self._serialize = serializer
        self._deserialize = deserializer

    def _make_key(self, key: K) -> str:
        """Override in subclass to define key format (protected by convention)."""
        raise NotImplementedError

    async def get(self, key: K) -> Optional[V]:
        redis_key = self._make_key(key)
        value = await self.redis.get(redis_key)
        return self._deserialize(value) if value is not None else None

    async def set(self, key: K, value: V) -> None:
        redis_key = self._make_key(key)
        serialized = self._serialize(value)
        if self.ttl:
            await self.redis.setex(redis_key, self.ttl, serialized)
        else:
            await self.redis.set(redis_key, serialized)

    async def invalidate(self, key: K) -> None:
        redis_key = self._make_key(key)
        await self.redis.delete(redis_key)

    async def mget(self, keys: List[K]) -> Dict[K, Optional[V]]:
        redis_keys = [self._make_key(k) for k in keys]
        values = await self.redis.mget(*redis_keys)
        return {
            k: (self._deserialize(v) if v is not None else None)
            for k, v in zip(keys, values)
        }

    async def mset(self, mapping: Dict[K, V]) -> None:
        pipe = self.redis.pipeline()
        for k, v in mapping.items():
            redis_key = self._make_key(k)
            serialized = self._serialize(v)
            if self.ttl:
                pipe.setex(redis_key, self.ttl, serialized)
            else:
                pipe.set(redis_key, serialized)
        await pipe.execute()

