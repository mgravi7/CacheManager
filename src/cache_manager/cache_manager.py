from redis.asyncio import Redis, from_url
from typing import Optional
from .user_uuid_to_id_cache import UserUUIDtoIdCache
from .user_id_to_uuid_cache import UserIdToUUIDCache


class CacheManager:
    """
    Singleton cache manager for Redis connection and cache instances.
    
    Each cache class defines its own default TTL based on domain requirements.
    """
    
    _instance: Optional['CacheManager'] = None

    def __new__(cls) -> 'CacheManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.redis: Optional[Redis] = None
            self.uuid_to_id_cache: Optional[UserUUIDtoIdCache] = None
            self.id_to_uuid_cache: Optional[UserIdToUUIDCache] = None
            self._initialized = True

    async def connect(self, redis_url: str = "redis://localhost:6379") -> None:
        """
        Initialize Redis connection and cache instances.
        
        Each cache instance uses its own default TTL based on domain requirements.
        Cache classes can be overridden at instantiation if needed.
        """
        if self.redis is not None:
            return
        
        self.redis = from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
        
        # Cache instances use their own domain-specific defaults
        self.uuid_to_id_cache = UserUUIDtoIdCache(self.redis)
        self.id_to_uuid_cache = UserIdToUUIDCache(self.redis)

    async def disconnect(self) -> None:
        """Gracefully close Redis connection."""
        if self.redis:
            await self.redis.aclose()
            self.redis = None
            self.uuid_to_id_cache = None
            self.id_to_uuid_cache = None
