"""
Custom exceptions for CacheManager operations.
"""


class CacheError(Exception):
    """Base exception for all cache-related errors."""
    pass


class CacheSerializationError(CacheError):
    """Raised when value serialization fails."""
    pass


class CacheDeserializationError(CacheError):
    """Raised when value deserialization fails (typically logged, not raised)."""
    pass


class CacheValidationError(CacheError):
    """Raised when cache operation validation fails."""
    pass


class CacheConnectionError(CacheError):
    """Raised when Redis connection fails (typically logged, not raised)."""
    pass
