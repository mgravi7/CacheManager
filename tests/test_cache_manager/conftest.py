"""
Pytest fixtures for cache_manager tests.
"""
import pytest
import asyncio
from redis.asyncio import from_url
import os


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def redis_client():
    """
    Provide Redis client for integration tests.
    Uses Redis DB 1 for testing to avoid conflicts with app data.
    """
    redis_url = os.getenv("REDIS_URL", "redis://:dev_redis_password_2024@localhost:6379/1")
    
    client = from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=False,
    )
    
    # Clear test database before each test
    await client.flushdb()
    
    yield client
    
    # Cleanup after test
    await client.flushdb()
    await client.aclose()
