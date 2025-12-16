from typing import Generic, TypeVar, Optional, Callable, List, Dict
import logging
from redis.asyncio import Redis
import redis.exceptions as redis_exceptions
from .exceptions import CacheSerializationError, CacheDeserializationError, CacheValidationError

K = TypeVar("K")
V = TypeVar("V")

logger = logging.getLogger(__name__)


class AsyncCacheBase(Generic[K, V]):
    """
    Generic async cache base class with Redis backend.

    Implements graceful degradation: cache is a luxury, not a requirement.
    Connection errors are logged but don't raise exceptions.
    Serialization errors raise CacheSerializationError (client responsibility).
    Deserialization errors auto-invalidate corrupt cache entries.
    """

    MAX_BATCH_SIZE = 100

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
        """
        Retrieve value from cache.

        Returns None if key not found, connection fails, or deserialization fails.
        Automatically invalidates corrupt cache entries.
        """
        try:
            redis_key = self._make_key(key)
            value = await self.redis.get(redis_key)

            if value is None:
                return None

            try:
                return self._deserialize(value)
            except Exception as e:
                logger.critical(
                    f"Deserialization failed for key {redis_key}, invalidating: {e}",
                    exc_info=True,
                )
                await self.invalidate(key)
                return None

        except (redis_exceptions.ConnectionError, redis_exceptions.TimeoutError) as e:
            logger.error(f"Redis connection failed for get({key}): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get({key}): {e}", exc_info=True)
            return None

    async def set(self, key: K, value: V) -> None:
        """
        Store value in cache with optional TTL.

        Raises CacheSerializationError if value cannot be serialized.
        Logs and ignores connection errors (graceful degradation).
        """
        try:
            redis_key = self._make_key(key)

            try:
                serialized = self._serialize(value)
            except Exception as e:
                logger.error(f"Serialization failed for key {redis_key}: {e}")
                raise CacheSerializationError(f"Cannot serialize value: {e}") from e

            if self.ttl:
                await self.redis.setex(redis_key, self.ttl, serialized)
            else:
                await self.redis.set(redis_key, serialized)

        except CacheSerializationError:
            raise
        except (redis_exceptions.ConnectionError, redis_exceptions.TimeoutError) as e:
            logger.error(f"Redis connection failed for set({key}): {e}")
        except Exception as e:
            logger.error(f"Unexpected error in set({key}): {e}", exc_info=True)

    async def invalidate(self, key: K) -> None:
        """Remove key from cache. Logs but doesn't raise on connection errors."""
        try:
            redis_key = self._make_key(key)
            await self.redis.delete(redis_key)
        except (redis_exceptions.ConnectionError, redis_exceptions.TimeoutError) as e:
            logger.error(f"Redis connection failed for invalidate({key}): {e}")
        except Exception as e:
            logger.error(f"Unexpected error in invalidate({key}): {e}", exc_info=True)

    async def mget(self, keys: List[K]) -> Dict[K, Optional[V]]:
        """
        Retrieve multiple values from cache.

        Enforces maximum of 100 keys per request.
        Returns dict with None for missing/failed keys.
        """
        if len(keys) > self.MAX_BATCH_SIZE:
            raise CacheValidationError(
                f"Cannot retrieve {len(keys)} keys. Maximum batch size is {self.MAX_BATCH_SIZE}. "
                f"Please split into multiple requests."
            )

        if not keys:
            return {}

        try:
            redis_keys = [self._make_key(k) for k in keys]
            values = await self.redis.mget(*redis_keys)

            result = {}
            for k, v in zip(keys, values):
                if v is None:
                    result[k] = None
                else:
                    try:
                        result[k] = self._deserialize(v)
                    except Exception as e:
                        logger.critical(
                            f"Deserialization failed for key {self._make_key(k)}, invalidating: {e}"
                        )
                        await self.invalidate(k)
                        result[k] = None

            return result

        except (redis_exceptions.ConnectionError, redis_exceptions.TimeoutError) as e:
            logger.error(f"Redis connection failed for mget({len(keys)} keys): {e}")
            return {k: None for k in keys}
        except Exception as e:
            logger.error(f"Unexpected error in mget({len(keys)} keys): {e}", exc_info=True)
            return {k: None for k in keys}

    async def mset(self, mapping: Dict[K, V]) -> None:
        """
        Store multiple values in cache.

        Enforces maximum of 100 entries per request.
        Raises CacheSerializationError if any value cannot be serialized.
        Logs but doesn't raise on connection errors.
        """
        if len(mapping) > self.MAX_BATCH_SIZE:
            raise CacheValidationError(
                f"Cannot store {len(mapping)} entries. Maximum batch size is {self.MAX_BATCH_SIZE}. "
                f"Please split into multiple requests."
            )

        if not mapping:
            return

        try:
            pipe = self.redis.pipeline()

            for k, v in mapping.items():
                redis_key = self._make_key(k)

                try:
                    serialized = self._serialize(v)
                except Exception as e:
                    logger.error(f"Serialization failed for key {redis_key}: {e}")
                    raise CacheSerializationError(f"Cannot serialize value for key {k}: {e}") from e

                if self.ttl:
                    pipe.setex(redis_key, self.ttl, serialized)
                else:
                    pipe.set(redis_key, serialized)

            await pipe.execute()

        except CacheSerializationError:
            raise
        except (redis_exceptions.ConnectionError, redis_exceptions.TimeoutError) as e:
            logger.error(f"Redis connection failed for mset({len(mapping)} entries): {e}")
        except Exception as e:
            logger.error(f"Unexpected error in mset({len(mapping)} entries): {e}", exc_info=True)

