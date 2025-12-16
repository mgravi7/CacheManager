# Developer Guide - CacheManager

A focused guide for developers implementing and extending the CacheManager system.

## 📋 Table of Contents

- [Core Concepts](#core-concepts)
- [Implementation Patterns](#implementation-patterns)
- [Error Handling Strategy](#error-handling-strategy)
- [Creating Custom Cache Classes](#creating-custom-cache-classes)
- [Testing Guide](#testing-guide)
- [Common Scenarios](#common-scenarios)

---

## Core Concepts

### Architecture Philosophy

1. **Cache is a Luxury** - Apps must continue when cache fails
2. **Type Safety** - Full type hints prevent runtime errors
3. **Async First** - All I/O operations use async/await
4. **Fail Gracefully** - Log errors, don't crash
5. **Factory Pattern** - CacheManager is the single source for cache instances

### Key Components

| Component | Purpose | Thread-Safe |
|-----------|---------|-------------|
| `AsyncCacheBase` | Generic base class for all caches | Yes |
| `CacheManager` | Singleton managing Redis connection | Yes |
| `UserUUIDtoIdCache` | Example: UUID → ID mapping | Yes |
| `UserIdToUUIDCache` | Example: ID → UUID mapping | Yes |

---

## Implementation Patterns

### 1. Creating a Cache Instance (Factory Pattern)

**CacheManager acts as a factory** - always use it to get cache instances.

```python
from cache_manager import CacheManager

# Get singleton instance
cache_manager = CacheManager()

# Connect to Redis (in FastAPI lifespan or startup)
await cache_manager.connect(redis_url="redis://:password@redis:6379/0")

# Use the cache through the factory
user_id = await cache_manager.uuid_to_id_cache.get(user_uuid)

# CacheManager provides:
# - cache_manager.uuid_to_id_cache
# - cache_manager.id_to_uuid_cache
# - cache_manager.session_cache (if added)
# - ... all registered caches
```

### 2. FastAPI Integration Pattern

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from cache_manager import CacheManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    cache_manager = CacheManager()
    await cache_manager.connect(redis_url=os.getenv("REDIS_URL"))
    app.state.cache_manager = cache_manager
    
    yield
    
    await cache_manager.disconnect()

app = FastAPI(lifespan=lifespan)
```

### 3. Data Access Layer Pattern

```python
async def get_user_by_uuid(user_uuid: UUID) -> Optional[User]:
    cache_manager = CacheManager()
    
    # Try cache first
    user_id = await cache_manager.uuid_to_id_cache.get(user_uuid)
    if user_id:
        return await _fetch_user_by_id(user_id)
    
    # Cache miss - fetch from data source
    user = await _fetch_from_database(user_uuid)
    if user:
        # Populate both caches
        await cache_manager.uuid_to_id_cache.set(user_uuid, user.id)
        await cache_manager.id_to_uuid_cache.set(user.id, user_uuid)
    
    return user
```

---

## Error Handling Strategy

### Connection Errors (Graceful Degradation)

**Behavior**: Log error, return `None`, continue execution

```python
# Automatic handling in AsyncCacheBase
async def get(self, key: K) -> Optional[V]:
    try:
        value = await self.redis.get(redis_key)
        return self._deserialize(value) if value : None
    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        return None  # App continues without cache
```

**Your code doesn't need try/catch** - it's handled internally.

### Serialization Errors (Client Responsibility)

**Behavior**: Raise `CacheSerializationError`

```python
from cache_manager import CacheSerializationError

try:
    await cache.set(key, value)
except CacheSerializationError as e:
    logger.error(f"Cannot cache this value: {e}")
    # Handle appropriately - maybe skip caching
```

### Deserialization Errors (Auto-Invalidation)

**Behavior**: Log critical error, invalidate corrupt entry, return `None`

```python
# Automatic handling - corrupt data is removed
user_id = await cache.get(user_uuid)  # Returns None if corrupt
# Cache entry automatically deleted
```

### Validation Errors (Batch Limits)

**Behavior**: Raise `CacheValidationError` for >100 entries

```python
from cache_manager import CacheValidationError

try:
    results = await cache.mget(keys)  # Max 100 keys
except CacheValidationError as e:
    # Split into batches
    batch_size = 100
    results = {}
    for i in range(0, len(keys), batch_size):
        batch = keys[i:i+batch_size]
        batch_results = await cache.mget(batch)
        results.update(batch_results)
```

---

## Creating Custom Cache Classes

### Step 1: Define Your Cache Class

```python
from uuid import UUID
from redis.asyncio import Redis
from cache_manager import AsyncCacheBase

class SessionTokenCache(AsyncCacheBase[str, UUID]):
    """Maps session token to user UUID."""
    
    NAMESPACE = "session:token"
    
    def __init__(self, redis_client: Redis, ttl: int = 300):  # 5 min for sessions
        super().__init__(
            redis_client,
            namespace=self.NAMESPACE,
            ttl=ttl,
            serializer=lambda v: str(v),
            deserializer=lambda b: UUID(b.decode("utf-8")),
        )
    
    def _make_key(self, key: str) -> str:
        return f"{self.namespace}:{key}"
```

### Step 2: Add to CacheManager (Required)

**Important**: CacheManager follows the Factory Pattern. All cache instances **must** be 
registered in CacheManager to ensure:
- Consistent access pattern across the team
- Centralized lifecycle management
- Easy discoverability of available caches
- Simplified testing and mocking

```python
# In cache_manager.py
from .session_token_cache import SessionTokenCache

class CacheManager:
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.redis: Optional[Redis] = None
            self.uuid_to_id_cache: Optional[UserUUIDtoIdCache] = None
            self.id_to_uuid_cache: Optional[UserIdToUUIDCache] = None
            self.session_cache: Optional[SessionTokenCache] = None  # Add your cache
            self._initialized = True
    
    async def connect(self, redis_url: str = "redis://localhost:6379"):
        self.redis = from_url(redis_url, ...)
        
        # Register cache instances
        self.uuid_to_id_cache = UserUUIDtoIdCache(self.redis)
        self.id_to_uuid_cache = UserIdToUUIDCache(self.redis)
        self.session_cache = SessionTokenCache(self.redis)  # Initialize your cache
```

### Step 3: Use Your Cache Through CacheManager

**Always access caches through CacheManager** - never instantiate cache classes directly.

```python
# Correct - Factory Pattern
cache_manager = CacheManager()
await cache_manager.connect(redis_url)
user_uuid = await cache_manager.session_cache.get("token_abc123")

# Wrong - Direct instantiation breaks the pattern
# redis = from_url(...)
# cache = SessionTokenCache(redis)  # DON'T DO THIS
```

**Benefits of Factory Pattern:**
- Single Redis connection pool shared across all caches
- Consistent initialization and cleanup
- Easy to find all available cache types
- Testable with a single mock point

---

## Testing Guide

### Unit Tests (Fast, Mocked)

```python
import pytest
from unittest.mock import AsyncMock
from cache_manager import SessionTokenCache

@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_cache_get():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"550e8400-e29b-41d4-a716-446655440001"
    
    cache = SessionTokenCache(mock_redis, ttl=300)
    result = await cache.get("token123")
    
    assert str(result) == "550e8400-e29b-41d4-a716-446655440001"
```

### Integration Tests (Real Redis)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_cache_integration(redis_client):
    cache = SessionTokenCache(redis_client, ttl=300)
    test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
    
    await cache.set("token123", test_uuid)
    result = await cache.get("token123")
    
    assert result == test_uuid
```

### Run Tests

```bash
# All tests
docker-compose --profile test run --rm tests

# Unit tests only (fast)
docker-compose --profile test run --rm tests pytest -m unit

# Integration tests only
docker-compose --profile test run --rm tests pytest -m integration

# Specific test file
docker-compose --profile test run --rm tests pytest tests/test_cache_manager/test_integration.py -v
```

---

## Common Scenarios

### Scenario 1: Cache with Complex Objects

```python
import json
from dataclasses import dataclass, asdict
from cache_manager import AsyncCacheBase

@dataclass
class UserProfile:
    name: str
    email: str
    preferences: dict

class UserProfileCache(AsyncCacheBase[int, UserProfile]):
    
    NAMESPACE = "user:profile"
    
    def __init__(self, redis_client: Redis, ttl: int = 600):
        super().__init__(
            redis_client,
            namespace=self.NAMESPACE,
            ttl=ttl,
            serializer=lambda v: json.dumps(asdict(v)),
            deserializer=lambda b: UserProfile(**json.loads(b.decode())),
        )
    
    def _make_key(self, key: int) -> str:
        return f"{self.namespace}:{key}"
```

### Scenario 2: Batch Loading with Limit Handling

```python
async def load_users_with_caching(user_uuids: List[UUID]) -> List[User]:
    cache_manager = CacheManager()
    
    # Handle batch limit (100 max)
    batch_size = 100
    all_results = {}
    
    for i in range(0, len(user_uuids), batch_size):
        batch = user_uuids[i:i+batch_size]
        batch_results = await cache_manager.uuid_to_id_cache.mget(batch)
        all_results.update(batch_results)
    
    # Process results
    users = []
    cache_misses = []
    
    for uuid, user_id in all_results.items():
        if user_id:
            users.append(await fetch_user_by_id(user_id))
        else:
            cache_misses.append(uuid)
    
    # Fetch and cache misses
    if cache_misses:
        missed_users = await fetch_users_by_uuids(cache_misses)
        users.extend(missed_users)
        
        # Populate cache
        cache_data = {u.uuid: u.id for u in missed_users}
        await cache_manager.uuid_to_id_cache.mset(cache_data)
    
    return users
```

### Scenario 3: TTL Selection Guide

```python
# Short TTL (5 minutes = 300s): Frequently changing data
session_cache = SessionTokenCache(redis, ttl=300)

# Medium TTL (10 minutes = 600s): User profiles - DEFAULT
profile_cache = UserProfileCache(redis, ttl=600)

# Long TTL (15 minutes = 900s): Static reference data
settings_cache = AppSettingsCache(redis, ttl=900)
```

**TTL Decision Factors:**
- Data volatility (how often it changes)
- Staleness tolerance (how old can data be)
- Cache hit ratio vs. freshness tradeoff

### Scenario 4: Cache Invalidation

```python
async def update_user(user_id: int, user_uuid: UUID, updates: dict):
    # Update database
    await database.update_user(user_id, updates)
    
    # Invalidate both cache directions
    cache_manager = CacheManager()
    await cache_manager.id_to_uuid_cache.invalidate(user_id)
    await cache_manager.uuid_to_id_cache.invalidate(user_uuid)
```

### Scenario 5: Monitoring Cache Health

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/cache/health")
async def cache_health():
    cache_manager = CacheManager()
    
    if cache_manager.redis is None:
        return {"status": "disconnected", "healthy": False}
    
    try:
        await cache_manager.redis.ping()
        return {"status": "connected", "healthy": True}
    except Exception as e:
        return {"status": "error", "healthy": False, "error": str(e)}
```

### Scenario 6: Anti-Pattern - Direct Instantiation (Don't Do This!)

```python
# ❌ WRONG - Direct instantiation breaks Factory Pattern
from redis.asyncio import from_url
from cache_manager import UserUUIDtoIdCache

redis = from_url("redis://localhost:6379")
cache = UserUUIDtoIdCache(redis)  # BAD!
user_id = await cache.get(user_uuid)

# Problems with this approach:
# 1. Multiple Redis connections (resource waste)
# 2. Inconsistent access pattern across team
# 3. Hard to discover what caches exist
# 4. Difficult to test and mock
# 5. No centralized lifecycle management

# ✅ CORRECT - Use CacheManager factory
from cache_manager import CacheManager

cache_manager = CacheManager()
await cache_manager.connect("redis://localhost:6379")
user_id = await cache_manager.uuid_to_id_cache.get(user_uuid)

# Benefits:
# 1. Single Redis connection pool
# 2. Consistent pattern everyone follows
# 3. Easy to see all available caches
# 4. Simple to test (mock CacheManager)
# 5. Proper lifecycle management
```

---

## Best Practices

### ✅ Do

- Use full type hints with Generics
- Follow async/await patterns consistently
- Log errors appropriately (ERROR for connection, CRITICAL for corruption)
- Write both unit and integration tests
- Document TTL choices in code comments
- Handle `CacheValidationError` for batch operations >100
- **Always register new cache classes in CacheManager** (Factory Pattern)
- **Always access caches through CacheManager singleton**
- Declare NAMESPACE as a class-level constant

### ❌ Don't

- Don't wrap cache calls in try/except for connection errors (handled internally)
- Don't ignore `CacheSerializationError` - it indicates a client code issue
- Don't exceed 100 entries in `mget`/`mset` without batching
- Don't use blocking Redis calls (always use async)
- Don't hardcode Redis passwords (use environment variables)
- **Don't instantiate cache classes directly** - use CacheManager factory
- **Don't skip registering new caches in CacheManager** - breaks team consistency

---

## Quick Reference

### Common Imports

```python
from cache_manager import (
    CacheManager,
    AsyncCacheBase,
    CacheSerializationError,
    CacheValidationError,
)
from redis.asyncio import Redis
from typing import Optional, List, Dict
```

### Error Types

| Exception | When Raised | Action |
|-----------|-------------|--------|
| `CacheSerializationError` | Serialization fails | Fix client code |
| `CacheValidationError` | >100 entries in batch | Split into batches |
| `ConnectionError` | Redis unavailable | Logged automatically, returns None |

### TTL Recommendations

| Use Case | TTL | Example |
|----------|-----|---------|
| Sessions | 300s (5 min) | Active user sessions |
| User Profiles | 600s (10 min) | Balanced freshness |
| Reference Data | 900s (15 min) | Rarely changes |

---

**For Docker-specific commands and troubleshooting, see [DOCKER.md](DOCKER.md)**
