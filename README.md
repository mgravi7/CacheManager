# CacheManager

A proof-of-concept demonstrating type-safe, async-first caching patterns using Redis, Python 3.12, and FastAPI.

## 🎯 Overview

This project showcases a production-ready cache management system with:

- **Type-safe cache implementations** using Python Generics
- **Async/await throughout** for high concurrency
- **Redis backend** with connection pooling and password authentication
- **Graceful error handling** - cache failures don't crash your app
- **100-entry batch limits** to prevent resource abuse
- **Extensible architecture** - easy to add new cache types

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop with WSL 2 (Windows) or Docker (Linux/Mac)

### 1. Clone and Setup

```bash
git clone https://github.com/mgravi7/CacheManager.git
cd CacheManager

# Windows
.\scripts\powershell\setup-venv.ps1

# Linux/WSL
./scripts/bash/setup-venv.sh
```

### 2. Start Services

```bash
# Windows
.\scripts\powershell\docker-up.ps1

# Linux/WSL
./scripts/bash/docker-up.sh
```

### 3. Access the API

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 4. Run Tests

```bash
# Windows
.\scripts\powershell\docker-test.ps1

# Linux/WSL
./scripts/bash/docker-test.sh
```

## 📚 Documentation

- **[Developer Guide](docs/DEVELOPER-GUIDE.md)** - Implementation details, patterns, and examples
- **[Docker Guide](docs/DOCKER.md)** - Docker setup, commands, and troubleshooting

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────-─┐
│                     FastAPI Application                      │
│  ┌────────────────┐              ┌──────────────────────┐    │
│  │  User API      │──────────────│  User DAL            │    │
│  │  (REST)        │              │  (Data Access Layer) │    │
│  └────────────────┘              └─────────-─┬──────────┘    │
│                                              │               │
│                                              ▼               │
│                                   ┌──────────────────────┐   │
│                                   │   CacheManager       │   │
│                                   │   (Singleton)        │   │
│                                   └──────────┬───────────┘   │
│                                              │               │
│                     ┌────────────────────────┼────────────┐  │
│                     ▼                        ▼            ▼  │
│          ┌──────────────────┐    ┌──────────────────┐    ... │
│          │ UUIDtoIdCache    │    │ IdToUUIDCache    │        │
│          └────────┬─────────┘    └────────┬─────────┘        │
│                   │                       │                  │
│                   └───────────┬───────────┘                  │
│                               ▼                              │
│                   ┌───────────────────────┐                  │
│                   │  AsyncCacheBase       │                  │
│                   │  (Generic Base Class) │                  │
│                   └───────────┬───────────┘                  │
└───────────────────────────────┼──────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Redis Container     │
                    │   (Password Protected)│
                    └───────────────────────┘
```

## ✨ Key Features

### Type-Safe Generics
```python
class AsyncCacheBase(Generic[K, V]):
    async def get(self, key: K) -> Optional[V]: ...
    async def set(self, key: K, value: V) -> None: ...
```

### Graceful Error Handling
- **Cache is a luxury** - Connection failures logged, app continues
- **Auto-invalidation** - Corrupt cache entries automatically removed
- **Clear exceptions** - Serialization errors raised for client handling

### Batch Operations with Limits
- **100-entry maximum** for `mget()` and `mset()`
- Forces developers to consider performance implications
- Prevents accidental resource exhaustion

### Configurable TTL
- **Default**: 10 minutes (600 seconds)
- **Recommended range**: 5-15 minutes
- **Use case examples** included in code documentation

## 🧪 Testing

**37 comprehensive tests** covering:
- ✅ 20 unit tests (with mocks)
- ✅ 17 integration tests (with real Redis)
- ✅ 85%+ code coverage

```bash
# Run all tests
.\scripts\powershell\docker-test.ps1

# Run only unit tests (fast)
docker-compose --profile test run --rm tests pytest -m unit

# Run only integration tests
docker-compose --profile test run --rm tests pytest -m integration
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/` | GET | Get all users |
| `/users/{uuid}` | GET | Get user by UUID |
| `/health` | GET | Health check with Redis status |
| `/docs` | GET | Interactive API documentation |

## 🔧 Environment Configuration

Default configuration in `.env`:
```env
REDIS_PASSWORD=dev_redis_password_2024
CACHE_DEFAULT_TTL=600
```

**For Production**: Use strong passwords and proper secret management.

## 🤝 Contributing

This is a proof-of-concept project demonstrating patterns for your development team.

Key patterns to follow when extending:
1. Inherit from `AsyncCacheBase` for new cache types
2. Use full type hints with Generics
3. Follow async/await patterns
4. Handle errors gracefully (cache is a luxury)
5. Write both unit and integration tests

See [Developer Guide](docs/DEVELOPER-GUIDE.md) for detailed implementation patterns.

## 📄 License

This is a proof-of-concept project for educational and demonstration purposes.

---

**Built with ❤️ using Python 3.12, FastAPI, and Redis**
