"""
Integration tests for cache classes using real Redis.
"""
import pytest
from uuid import UUID
import asyncio

from cache_manager import (
    UserUUIDtoIdCache,
    UserIdToUUIDCache,
    CacheValidationError,
    CacheSerializationError,
)


@pytest.mark.integration
class TestUserUUIDtoIdCacheIntegration:
    """Integration tests for UserUUIDtoIdCache with real Redis."""
    
    @pytest.mark.asyncio
    async def test_set_and_get_value(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        
        await cache.set(test_uuid, 123)
        result = await cache.get(test_uuid)
        
        assert result == 123
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key_returns_none(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440099")
        
        result = await cache.get(test_uuid)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=1)  # 1 second TTL
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        
        await cache.set(test_uuid, 123)
        
        # Should exist immediately
        result = await cache.get(test_uuid)
        assert result == 123
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Should be expired
        result = await cache.get(test_uuid)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalidate_removes_key(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        
        await cache.set(test_uuid, 123)
        await cache.invalidate(test_uuid)
        result = await cache.get(test_uuid)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_key_format(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        
        await cache.set(test_uuid, 123)
        
        # Check Redis directly
        key = f"user:uuid-to-id:{test_uuid}"
        value = await redis_client.get(key)
        
        assert value == b"123"
    
    @pytest.mark.asyncio
    async def test_mget_multiple_keys(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        
        uuid1 = UUID("550e8400-e29b-41d4-a716-446655440001")
        uuid2 = UUID("550e8400-e29b-41d4-a716-446655440002")
        uuid3 = UUID("550e8400-e29b-41d4-a716-446655440003")
        
        await cache.set(uuid1, 1)
        await cache.set(uuid2, 2)
        # uuid3 not set
        
        result = await cache.mget([uuid1, uuid2, uuid3])
        
        assert result == {uuid1: 1, uuid2: 2, uuid3: None}
    
    @pytest.mark.asyncio
    async def test_mget_enforces_100_key_limit(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        
        keys = [UUID(f"550e8400-e29b-41d4-a716-{i:012d}") for i in range(101)]
        
        with pytest.raises(CacheValidationError):
            await cache.mget(keys)
    
    @pytest.mark.asyncio
    async def test_mset_multiple_values(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        
        uuid1 = UUID("550e8400-e29b-41d4-a716-446655440001")
        uuid2 = UUID("550e8400-e29b-41d4-a716-446655440002")
        
        await cache.mset({uuid1: 1, uuid2: 2})
        
        result1 = await cache.get(uuid1)
        result2 = await cache.get(uuid2)
        
        assert result1 == 1
        assert result2 == 2
    
    @pytest.mark.asyncio
    async def test_mset_enforces_100_entry_limit(self, redis_client):
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        
        mapping = {
            UUID(f"550e8400-e29b-41d4-a716-{i:012d}"): i 
            for i in range(101)
        }
        
        with pytest.raises(CacheValidationError):
            await cache.mset(mapping)


@pytest.mark.integration
class TestUserIdToUUIDCacheIntegration:
    """Integration tests for UserIdToUUIDCache with real Redis."""
    
    @pytest.mark.asyncio
    async def test_set_and_get_value(self, redis_client):
        cache = UserIdToUUIDCache(redis_client, ttl=600)
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        
        await cache.set(123, test_uuid)
        result = await cache.get(123)
        
        assert result == test_uuid
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key_returns_none(self, redis_client):
        cache = UserIdToUUIDCache(redis_client, ttl=600)
        
        result = await cache.get(999)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_key_format(self, redis_client):
        cache = UserIdToUUIDCache(redis_client, ttl=600)
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        
        await cache.set(123, test_uuid)
        
        # Check Redis directly
        key = "user:id-to-uuid:123"
        value = await redis_client.get(key)
        
        assert value == b"550e8400-e29b-41d4-a716-446655440001"
    
    @pytest.mark.asyncio
    async def test_bidirectional_caching(self, redis_client):
        """Test using both cache directions together."""
        uuid_to_id = UserUUIDtoIdCache(redis_client, ttl=600)
        id_to_uuid = UserIdToUUIDCache(redis_client, ttl=600)
        
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        test_id = 123
        
        # Set both directions
        await uuid_to_id.set(test_uuid, test_id)
        await id_to_uuid.set(test_id, test_uuid)
        
        # Retrieve from both directions
        retrieved_id = await uuid_to_id.get(test_uuid)
        retrieved_uuid = await id_to_uuid.get(test_id)
        
        assert retrieved_id == test_id
        assert retrieved_uuid == test_uuid


@pytest.mark.integration
class TestCacheManagerIntegration:
    """Integration tests for CacheManager singleton."""
    
    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        from cache_manager import CacheManager
        
        manager1 = CacheManager()
        manager2 = CacheManager()
        
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        from cache_manager import CacheManager
        import os
        
        manager = CacheManager()
        redis_url = os.getenv("REDIS_URL", "redis://:dev_redis_password_2024@localhost:6379/1")
        
        await manager.connect(redis_url)
        
        assert manager.redis is not None
        assert manager.uuid_to_id_cache is not None
        assert manager.id_to_uuid_cache is not None
        
        await manager.disconnect()
        
        assert manager.redis is None
        assert manager.uuid_to_id_cache is None
        assert manager.id_to_uuid_cache is None
    
    @pytest.mark.asyncio
    async def test_cache_operations_through_manager(self):
        from cache_manager import CacheManager
        import os
        
        manager = CacheManager()
        redis_url = os.getenv("REDIS_URL", "redis://:dev_redis_password_2024@localhost:6379/1")
        
        await manager.connect(redis_url)
        
        try:
            # Clear the test database first
            await manager.redis.flushdb()
            
            test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
            test_id = 123
            
            # Set and get through manager
            await manager.uuid_to_id_cache.set(test_uuid, test_id)
            result = await manager.uuid_to_id_cache.get(test_uuid)
            
            assert result == test_id
            
        finally:
            await manager.disconnect()


@pytest.mark.integration
class TestCacheErrorHandling:
    """Integration tests for error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_corrupt_data_auto_invalidates(self, redis_client):
        """Test that corrupt cache data is automatically invalidated."""
        cache = UserUUIDtoIdCache(redis_client, ttl=600)
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        
        # Manually insert corrupt data into Redis
        key = f"user:uuid-to-id:{test_uuid}"
        await redis_client.set(key, b"not_an_integer")
        
        # Should return None and invalidate
        result = await cache.get(test_uuid)
        assert result is None
        
        # Verify key was deleted
        exists = await redis_client.exists(key)
        assert exists == 0
