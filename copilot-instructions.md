# GitHub Copilot Instructions for CacheManager Project

## Project Overview
This is a proof-of-concept Cache Manager implementation using Redis, Python 3.12, and FastAPI. The project demonstrates type-safe, async-first caching patterns with Redis as the backend.

## Architecture

### Core Components
1. **AsyncCacheBase** - Generic base class for all cache implementations
2. **Derived Cache Classes** - Type-safe implementations (UserUUIDtoIdCache, UserIdToUUIDCache)
3. **CacheManager** - Singleton managing Redis connection pool and cache instances
4. **User API** - FastAPI REST endpoints demonstrating cache usage
5. **User DAL** - Data Access Layer with cache integration

### Technology Stack
- Python 3.12
- FastAPI (async web framework)
- Redis 7.x (Alpine) - containerized
- redis-py 5.x (async Python client)
- pytest + pytest-asyncio (testing)
- Docker + Docker Compose

## Code Standards & Patterns

### 1. Async/Await Throughout
- **Always use async/await** for I/O operations
- All Redis operations must be async
- FastAPI endpoints use async def
- DAL methods are async
- Tests use pytest-asyncio

```python
# Good
async def get_user(user_id: int) -> User:
    cached = await cache_manager.id_to_uuid_cache.get(user_id)
    ...

# Bad - Don't use sync Redis calls
def get_user(user_id: int) -> User:
    cached = cache.get(user_id)  # Blocks event loop
```

### 2. Type Safety & Generics
- **Full type hints on all functions and methods**
- Use Generic types in base classes
- Leverage Pydantic models for data validation
- Enable strict mypy checking

```python
# Good
from typing import Generic, TypeVar, Optional

K = TypeVar('K')
V = TypeVar('V')

class AsyncCacheBase(Generic[K, V]):
    async def get(self, key: K) -> Optional[V]:
        ...

# Bad - Missing type hints
class AsyncCacheBase:
    async def get(self, key):  # No types
        ...
```

### 3. Singleton Pattern for CacheManager
- Thread-safe singleton implementation
- Single Redis connection pool shared across app
- Lazy initialization of cache instances
- Proper cleanup on shutdown

```python
# Pattern to follow
class CacheManager:
    _instance: Optional['CacheManager'] = None
    
    def __new__(cls) -> 'CacheManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 4. Security Best Practices
- **Never hardcode secrets** - use environment variables
- Redis passwords via environment variables
- Input validation using Pydantic models
- Proper error handling without exposing internals
- Sanitize logs (no sensitive data)

```python
# Good
redis_password = os.getenv("REDIS_PASSWORD")

# Bad
redis_password = "my_secret_password"  # Never do this
```

### 5. Concurrency & Performance
- Use connection pooling for Redis
- Implement proper timeout handling
- Avoid blocking operations in async code
- Cache invalidation strategy clearly defined
- Efficient serialization (JSON for simple types)

### 6. Error Handling
- Graceful degradation when cache unavailable
- Specific exception types
- Proper logging at appropriate levels
- Don't swallow exceptions silently

```python
# Good
try:
    return await self._redis.get(key)
except redis.ConnectionError as e:
    logger.error(f"Redis connection failed: {e}")
    raise CacheConnectionError("Cache unavailable") from e

# Bad
try:
    return await self._redis.get(key)
except:  # Too broad
    pass  # Silent failure
```

### 7. Documentation Style
- **Concise and focused** - avoid verbose docstrings
- Document why, not what (code should be self-explanatory)
- Type hints reduce need for parameter documentation
- Focus on non-obvious behavior, edge cases, and important context

```python
# Good - Concise, explains the "why"
async def get(self, key: K) -> Optional[V]:
    """Returns None if key not found or expired."""
    ...

# Bad - Too verbose
async def get(self, key: K) -> Optional[V]:
    """
    Retrieves a value from the cache.
    
    Args:
        key: The key to look up in the cache
        
    Returns:
        The cached value if found, otherwise None
        
    Raises:
        CacheConnectionError: If Redis connection fails
    """
    ...
```

### 8. Testing Guidelines
- Use pytest-asyncio for async tests
- Mock Redis for unit tests
- Integration tests with real Redis container
- Test both success and failure paths
- Use fixtures for common setups

### 9. Script and Configuration File Standards
- **NO EMOJIS** in shell scripts (.sh, .ps1, .bat) - they cause encoding issues
- **Pure ASCII characters only** in scripts for maximum compatibility
- Use UTF-8 without BOM for all text files
- Use standard ASCII double quotes (") not smart quotes or Unicode variants
- Keep scripts simple and readable with clear text output
- Test scripts on both Windows (PowerShell) and Linux (Bash) if applicable

```powershell
# Good - Plain ASCII, works everywhere
Write-Host "Setup complete!" -ForegroundColor Green

# Bad - Emojis can cause parsing errors
Write-Host "✅ Setup complete!" -ForegroundColor Green
```

## File Organization

### Source Code Structure
```
src/
├── cache_manager/       # Cache implementation
│   ├── async_cache_base.py
│   ├── user_uuid_to_id_cache.py
│   ├── user_id_to_uuid_cache.py
│   └── cache_manager.py
└── user_api/           # FastAPI application
    ├── main.py         # App entry + lifespan
    ├── api.py          # Endpoints
    ├── dal.py          # Data Access Layer
    └── models.py       # Pydantic models
```

### Test Structure
- Mirror source structure
- Prefix test files with `test_`
- Group related tests in classes

## Development Workflow

### Local Development
1. Use Python virtual environment
2. Install dev dependencies from requirements-dev.txt
3. Run Redis via Docker Compose
4. Use scripts for common tasks

### Code Quality
- Run mypy for type checking
- Use black for formatting (line length: 100)
- Follow PEP 8 conventions
- Keep functions focused and small

## Common Patterns to Follow

### Cache Key Generation
```python
def _get_cache_key(self, user_id: int) -> str:
    return f"user:id:{user_id}"
```

### FastAPI Lifespan for Redis Connection
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache_manager.connect()
    yield
    await cache_manager.disconnect()
```

### DAL Cache Integration
```python
async def get_user_by_id(user_id: int) -> Optional[User]:
    # Try cache first
    uuid = await cache_manager.id_to_uuid_cache.get(user_id)
    if uuid:
        return await _get_user_by_uuid(uuid)
    
    # Fallback to data source
    user = await _fetch_from_source(user_id)
    if user:
        await cache_manager.id_to_uuid_cache.set(user_id, user.uuid)
    return user
```

## Reminders

- This is a POC - focus on clarity and demonstrating patterns
- Other developers will extend AsyncCacheBase - make it easy to understand
- Type safety helps catch errors early
- Async everywhere for scalability
- Keep code clean, secure, and performant
- **Reliability over aesthetics** - no emojis in scripts, pure ASCII for compatibility
