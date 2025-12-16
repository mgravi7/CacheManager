"""
CacheManager package - Type-safe async caching with Redis.
"""

__version__ = "0.1.0"

from .async_cache_base import AsyncCacheBase
from .user_uuid_to_id_cache import UserUUIDtoIdCache
from .user_id_to_uuid_cache import UserIdToUUIDCache
from .cache_manager import CacheManager
from .exceptions import (
    CacheError,
    CacheSerializationError,
    CacheDeserializationError,
    CacheValidationError,
    CacheConnectionError,
)

__all__ = [
    "AsyncCacheBase",
    "UserUUIDtoIdCache",
    "UserIdToUUIDCache",
    "CacheManager",
    "CacheError",
    "CacheSerializationError",
    "CacheDeserializationError",
    "CacheValidationError",
    "CacheConnectionError",
]
