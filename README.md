# CacheManager

A proof-of-concept implementation demonstrating type-safe, async-first caching patterns using Redis, Python 3.12, and FastAPI.

## 🎯 Project Overview

This project showcases a production-ready cache management system with:

- **Type-safe cache implementations** using Python Generics
- **Async/await throughout** for high concurrency and scalability
- **Redis backend** with connection pooling
- **Singleton CacheManager** for efficient resource management
- **FastAPI REST endpoints** demonstrating cache usage
- **Extensible architecture** - easy to add new cache types

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│  ┌────────────────┐              ┌──────────────────────┐   │
│  │  User API      │──────────────│  User DAL            │   │
│  │  (REST)        │              │  (Data Access Layer) │   │
│  └────────────────┘              └──────────┬───────────┘   │
│                                              │               │
│                                              ▼               │
│                                   ┌──────────────────────┐   │
│                                   │   CacheManager       │   │
│                                   │   (Singleton)        │   │
│                                   └──────────┬───────────┘   │
│                                              │               │
│                     ┌────────────────────────┼────────────┐  │
│                     ▼                        ▼            ▼  │
│          ┌──────────────────┐    ┌──────────────────┐   ... │
│          │ UUIDtoIdCache    │    │ IdToUUIDCache    │       │
│          │ (derived)        │    │ (derived)        │       │
│          └────────┬─────────┘    └────────┬─────────┘       │
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
                    │   (Alpine 7.x)        │
                    └───────────────────────┘
```

## 📁 Project Structure

```
CacheManager/
├── src/
│   ├── cache_manager/              # Cache implementation
│   │   ├── async_cache_base.py     # Generic base class
│   │   ├── user_uuid_to_id_cache.py
│   │   ├── user_id_to_uuid_cache.py
│   │   └── cache_manager.py        # Singleton manager
│   │
│   ├── user_api/                   # FastAPI application
│   │   ├── main.py                 # App entry point
│   │   ├── api.py                  # REST endpoints
│   │   ├── dal.py                  # Data Access Layer
│   │   └── models.py               # Pydantic models
│   │
│   └── Dockerfile                  # FastAPI container
│
├── tests/                          # Test suite
│   ├── test_cache_manager/
│   └── test_user_api/
│
├── scripts/                        # Automation scripts
│   ├── bash/
│   └── powershell/
│
├── requirements.txt                # Production dependencies
├── requirements-dev.txt            # Development dependencies
└── docker-compose.yml              # Container orchestration
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Docker Desktop** with WSL 2 (Windows 11 Pro)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/mgravi7/CacheManager.git
cd CacheManager
```

### 2. Setup Python Virtual Environment

#### On Windows (PowerShell):
```powershell
.\scripts\powershell\setup-venv.ps1
```

#### On Linux/WSL (Bash):
```bash
chmod +x scripts/bash/setup-venv.sh
./scripts/bash/setup-venv.sh
```

This will:
- Create a virtual environment in `.venv/`
- Activate the virtual environment
- Install all dependencies from `requirements.txt` and `requirements-dev.txt`

### 3. Manual Virtual Environment Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Windows CMD:
.venv\Scripts\activate.bat

# Linux/WSL/Mac:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Start Docker Containers

#### On Windows (PowerShell):
```powershell
.\scripts\powershell\docker-up.ps1
```

#### On Linux/WSL (Bash):
```bash
./scripts/bash/docker-up.sh
```

This starts:
- Redis container (port 6379)
- FastAPI application (port 8000)

### 5. Verify Installation

```bash
# Check if containers are running
docker ps

# Access the API
curl http://localhost:8000/docs
```

## 🧪 Running Tests

#### On Windows (PowerShell):
```powershell
.\scripts\powershell\run-tests.ps1
```

#### On Linux/WSL (Bash):
```bash
./scripts/bash/run-tests.sh
```

Or manually:
```bash
# Activate virtual environment first
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_cache_manager/test_async_cache_base.py
```

## 📚 API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

- `GET /users/{user_id}` - Get user by ID (integer)
- `GET /users/uuid/{user_uuid}` - Get user by UUID

Both endpoints demonstrate cache usage:
1. Check cache first
2. If miss, fetch from data source
3. Populate cache
4. Return result

## 🔧 Development

### Code Quality Tools

```bash
# Type checking
mypy src/

# Code formatting (check only)
black --check src/ tests/

# Format code
black src/ tests/

# Linting
flake8 src/ tests/
```

### Environment Variables

For local development, create a `.env` file (see `.env.example`):

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password
REDIS_DB=0
```

## 🐳 Docker Commands

```bash
# Start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Rebuild containers
docker-compose up -d --build

# Access Redis CLI
docker exec -it cachemanager-redis-1 redis-cli -a your_password
```

## 🎓 Key Concepts

### AsyncCacheBase - Generic Base Class

```python
from typing import Generic, TypeVar, Optional

K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type

class AsyncCacheBase(Generic[K, V]):
    async def get(self, key: K) -> Optional[V]:
        """Retrieve value from cache"""
        ...
    
    async def set(self, key: K, value: V, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL"""
        ...
```

### Extending with Custom Cache Types

```python
class UserUUIDtoIdCache(AsyncCacheBase[UUID, int]):
    """Maps UUID -> User ID (int)"""
    
    def _get_cache_key(self, user_uuid: UUID) -> str:
        return f"user:uuid:{user_uuid}"
```

### Singleton CacheManager

```python
cache_manager = CacheManager()

# Access cache instances
user_id = await cache_manager.id_to_uuid_cache.get(user_uuid)
user_uuid = await cache_manager.uuid_to_id_cache.get(user_id)
```

## 🤝 Contributing

This is a proof-of-concept project demonstrating patterns for:
- Type-safe async cache implementations
- Redis integration with Python
- FastAPI best practices
- Extensible architecture

Feel free to extend with your own cache types!

## 📄 License

This is a proof-of-concept project for educational purposes.

## 🙋 Support

For questions or issues, please open an issue on GitHub.

---

**Built with ❤️ using Python 3.12, FastAPI, and Redis**
