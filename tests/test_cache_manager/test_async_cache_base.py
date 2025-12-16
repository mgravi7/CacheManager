"""
Unit tests for AsyncCacheBase using mocks.
"""
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import UUID
import redis.exceptions as redis_exceptions

from cache_manager import (
    AsyncCacheBase,
    CacheSerializationError,
    CacheValidationError,
)


class ConcreteTestCache(AsyncCacheBase[str, int]):
    """Concrete test implementation of AsyncCacheBase."""
    
    def _make_key(self, key: str) -> str:
        return f"test:{key}"


@pytest.mark.unit
class TestAsyncCacheBaseGet:
    """Test get() method."""
    
    @pytest.mark.asyncio
    async def test_get_returns_value_when_key_exists(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b"42"
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        result = await cache.get("mykey")
        
        assert result == 42
        mock_redis.get.assert_called_once_with("test:mykey")
    
    @pytest.mark.asyncio
    async def test_get_returns_none_when_key_not_found(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        result = await cache.get("missing")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_returns_none_on_connection_error(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = redis_exceptions.ConnectionError("Connection failed")
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        result = await cache.get("mykey")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_invalidates_on_deserialization_error(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b"invalid_data"
        mock_redis.delete = AsyncMock()
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())  # Will fail
        )
        
        result = await cache.get("corrupt_key")
        
        assert result is None
        mock_redis.delete.assert_called_once_with("test:corrupt_key")


@pytest.mark.unit
class TestAsyncCacheBaseSet:
    """Test set() method."""
    
    @pytest.mark.asyncio
    async def test_set_stores_value_with_ttl(self):
        mock_redis = AsyncMock()
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        await cache.set("mykey", 42)
        
        mock_redis.setex.assert_called_once_with("test:mykey", 600, "42")
    
    @pytest.mark.asyncio
    async def test_set_stores_value_without_ttl(self):
        mock_redis = AsyncMock()
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=None,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        await cache.set("mykey", 42)
        
        mock_redis.set.assert_called_once_with("test:mykey", "42")
    
    @pytest.mark.asyncio
    async def test_set_raises_on_serialization_error(self):
        mock_redis = AsyncMock()
        
        def bad_serializer(v):
            raise TypeError("Cannot serialize")
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=bad_serializer,
            deserializer=lambda b: int(b.decode())
        )
        
        with pytest.raises(CacheSerializationError):
            await cache.set("mykey", 42)
    
    @pytest.mark.asyncio
    async def test_set_handles_connection_error_gracefully(self):
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = redis_exceptions.ConnectionError("Connection failed")
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        # Should not raise
        await cache.set("mykey", 42)


@pytest.mark.unit
class TestAsyncCacheBaseInvalidate:
    """Test invalidate() method."""
    
    @pytest.mark.asyncio
    async def test_invalidate_removes_key(self):
        mock_redis = AsyncMock()
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        await cache.invalidate("mykey")
        
        mock_redis.delete.assert_called_once_with("test:mykey")
    
    @pytest.mark.asyncio
    async def test_invalidate_handles_connection_error_gracefully(self):
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = redis_exceptions.ConnectionError("Connection failed")
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        # Should not raise
        await cache.invalidate("mykey")


@pytest.mark.unit
class TestAsyncCacheBaseMget:
    """Test mget() method."""
    
    @pytest.mark.asyncio
    async def test_mget_returns_multiple_values(self):
        mock_redis = AsyncMock()
        mock_redis.mget.return_value = [b"1", b"2", b"3"]
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        result = await cache.mget(["key1", "key2", "key3"])
        
        assert result == {"key1": 1, "key2": 2, "key3": 3}
    
    @pytest.mark.asyncio
    async def test_mget_handles_missing_keys(self):
        mock_redis = AsyncMock()
        mock_redis.mget.return_value = [b"1", None, b"3"]
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        result = await cache.mget(["key1", "key2", "key3"])
        
        assert result == {"key1": 1, "key2": None, "key3": 3}
    
    @pytest.mark.asyncio
    async def test_mget_enforces_100_key_limit(self):
        mock_redis = AsyncMock()
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        keys = [f"key{i}" for i in range(101)]
        
        with pytest.raises(CacheValidationError) as exc_info:
            await cache.mget(keys)
        
        assert "100" in str(exc_info.value)
        assert "101" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_mget_returns_empty_dict_for_empty_list(self):
        mock_redis = AsyncMock()
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        result = await cache.mget([])
        
        assert result == {}
        mock_redis.mget.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_mget_handles_connection_error_gracefully(self):
        mock_redis = AsyncMock()
        mock_redis.mget.side_effect = redis_exceptions.ConnectionError("Connection failed")
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        result = await cache.mget(["key1", "key2"])
        
        assert result == {"key1": None, "key2": None}


@pytest.mark.unit
class TestAsyncCacheBaseMset:
    """Test mset() method."""
    
    @pytest.mark.asyncio
    async def test_mset_stores_multiple_values(self):
        mock_redis = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.setex = Mock()  # Sync method
        mock_pipeline.set = Mock()  # Sync method
        mock_pipeline.execute = AsyncMock()  # Async method
        mock_redis.pipeline = Mock(return_value=mock_pipeline)  # Sync method returning pipeline
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        await cache.mset({"key1": 1, "key2": 2})
        
        assert mock_pipeline.setex.call_count == 2
        mock_pipeline.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mset_enforces_100_entry_limit(self):
        mock_redis = AsyncMock()
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        mapping = {f"key{i}": i for i in range(101)}
        
        with pytest.raises(CacheValidationError) as exc_info:
            await cache.mset(mapping)
        
        assert "100" in str(exc_info.value)
        assert "101" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_mset_handles_empty_dict(self):
        mock_redis = AsyncMock()
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        await cache.mset({})
        
        mock_redis.pipeline.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_mset_raises_on_serialization_error(self):
        mock_redis = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.setex = Mock()
        mock_pipeline.execute = AsyncMock()
        mock_redis.pipeline = Mock(return_value=mock_pipeline)
        
        def bad_serializer(v):
            if v == 2:
                raise TypeError("Cannot serialize")
            return str(v)
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=bad_serializer,
            deserializer=lambda b: int(b.decode())
        )
        
        with pytest.raises(CacheSerializationError):
            await cache.mset({"key1": 1, "key2": 2})
    
    @pytest.mark.asyncio
    async def test_mset_handles_connection_error_gracefully(self):
        mock_redis = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.setex = Mock()
        mock_pipeline.execute = AsyncMock(side_effect=redis_exceptions.ConnectionError("Connection failed"))
        mock_redis.pipeline = Mock(return_value=mock_pipeline)
        
        cache = ConcreteTestCache(
            mock_redis,
            namespace="test",
            ttl=600,
            serializer=str,
            deserializer=lambda b: int(b.decode())
        )
        
        # Should not raise
        await cache.mset({"key1": 1, "key2": 2})
