# Docker Usage Guide - CacheManager

## Quick Start

### 1. Start All Services (Redis + API)

**Windows (PowerShell):**
```powershell
.\scripts\powershell\docker-up.ps1
```

**Linux/WSL (Bash):**
```bash
chmod +x scripts/bash/docker-up.sh
./scripts/bash/docker-up.sh
```

This will:
- Create `.env` file from `.env.example` if it doesn't exist
- Build the FastAPI Docker image
- Start Redis with password authentication
- Start the FastAPI application
- Show container status

### 2. Access the API

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 3. Run Tests in Docker

**Windows (PowerShell):**
```powershell
.\scripts\powershell\docker-test.ps1
```

**Linux/WSL (Bash):**
```bash
chmod +x scripts/bash/docker-test.sh
./scripts/bash/docker-test.sh
```

### 4. View Logs

**API Logs:**
```powershell
# Windows
.\scripts\powershell\docker-logs.ps1 api

# Linux
./scripts/bash/docker-logs.sh api
```

**Redis Logs:**
```powershell
# Windows
.\scripts\powershell\docker-logs.ps1 redis

# Linux
./scripts/bash/docker-logs.sh redis
```

**All Logs:**
```bash
docker-compose logs -f
```

### 5. Stop Services

**Windows (PowerShell):**
```powershell
.\scripts\powershell\docker-down.ps1
```

**Linux/WSL (Bash):**
```bash
./scripts/bash/docker-down.sh
```

---

## Docker Services

### Service: `redis`
- **Image**: redis:7-alpine
- **Port**: 6379
- **Password**: Set in `.env` (REDIS_PASSWORD)
- **Persistence**: Data stored in Docker volume `redis_data`
- **Health Check**: Automatic with retry logic

### Service: `api`
- **Build**: Custom from `src/Dockerfile`
- **Port**: 8000
- **Depends on**: redis (waits for health check)
- **Hot Reload**: Source code mounted for development
- **Environment**: REDIS_URL with password from `.env`

### Service: `tests`
- **Build**: Custom from `Dockerfile.test`
- **Profile**: `test` (only runs when explicitly called)
- **Purpose**: Run pytest in containerized environment
- **Environment**: Same as `api` service

---

## Environment Configuration

### .env File

Created automatically from `.env.example` when running `docker-up` scripts.

**Default values:**
```env
REDIS_PASSWORD=dev_redis_password_2024
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
CACHE_DEFAULT_TTL=3600
API_HOST=0.0.0.0
API_PORT=8000
```

**For Production:**
- Change `REDIS_PASSWORD` to a strong password
- Use proper secret management (Azure Key Vault, AWS Secrets Manager, etc.)
- Update `CACHE_DEFAULT_TTL` as needed

---

## Common Docker Commands

### Build and Start
```bash
# Build and start in background
docker-compose up -d --build

# Start without rebuilding
docker-compose up -d

# Start and view logs
docker-compose up
```

### View Status
```bash
# Show running containers
docker-compose ps

# Show all containers (including stopped)
docker-compose ps -a
```

### Logs
```bash
# View logs (all services)
docker-compose logs

# Follow logs (tail -f)
docker-compose logs -f

# Logs for specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100
```

### Execute Commands in Container
```bash
# Access API container shell
docker-compose exec api /bin/sh

# Access Redis CLI
docker-compose exec redis redis-cli -a dev_redis_password_2024

# Run a command in API container
docker-compose exec api python -c "print('Hello from container')"
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Stop and Remove
```bash
# Stop containers (keep volumes)
docker-compose down

# Stop and remove volumes (WARNING: deletes Redis data)
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### Run Tests
```bash
# Run tests with docker-compose
docker-compose --profile test run --rm tests

# Run specific test file
docker-compose --profile test run --rm tests pytest tests/test_cache_manager/test_async_cache_base.py

# Run with verbose output
docker-compose --profile test run --rm tests pytest -v

# Run with coverage
docker-compose --profile test run --rm tests pytest --cov=src
```

---

## Debugging in Docker

### 1. Check Container Health
```bash
docker-compose ps
docker inspect cachemanager-api --format='{{.State.Health.Status}}'
```

### 2. View Real-time Logs
```bash
# API logs
docker-compose logs -f api

# Redis logs
docker-compose logs -f redis
```

### 3. Access Container Shell
```bash
# API container
docker-compose exec api /bin/sh

# Inside container, you can:
cd /app
ls -la
python -m pytest
env | grep REDIS
```

### 4. Test Redis Connection
```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli -a dev_redis_password_2024

# Inside Redis CLI:
PING          # Should return PONG
KEYS *        # Show all keys
GET user:uuid-to-id:550e8400-e29b-41d4-a716-446655440001
```

### 5. Check Network Connectivity
```bash
# From API container, test Redis connection
docker-compose exec api python -c "
from redis.asyncio import from_url
import asyncio
async def test():
    r = from_url('redis://:dev_redis_password_2024@redis:6379/0')
    print(await r.ping())
    await r.aclose()
asyncio.run(test())
"
```

### 6. View Environment Variables
```bash
# Check environment in API container
docker-compose exec api env
```

---

## Volume Management

### View Volumes
```bash
docker volume ls
docker volume inspect cachemanager_redis_data
```

### Backup Redis Data
```bash
# Create backup
docker-compose exec redis redis-cli -a dev_redis_password_2024 SAVE
docker cp cachemanager-redis:/data/dump.rdb ./backup-dump.rdb
```

### Restore Redis Data
```bash
# Stop Redis
docker-compose stop redis

# Copy backup
docker cp ./backup-dump.rdb cachemanager-redis:/data/dump.rdb

# Start Redis
docker-compose start redis
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs api

# Check if ports are in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Redis Connection Errors
```bash
# Verify Redis is running
docker-compose ps redis

# Check Redis health
docker-compose exec redis redis-cli -a dev_redis_password_2024 PING

# Verify password in .env matches docker-compose.yml
cat .env | grep REDIS_PASSWORD
```

### Tests Failing
```bash
# Run tests with verbose output
docker-compose --profile test run --rm tests pytest -vv

# Check if Redis is accessible from test container
docker-compose --profile test run --rm tests python -c "
import os
print('REDIS_URL:', os.getenv('REDIS_URL'))
"
```

---

## Production Considerations

1. **Security**
   - Use strong Redis password
   - Don't commit `.env` to git (already in `.gitignore`)
   - Use secret management tools
   - Run containers as non-root user (already configured)

2. **Performance**
   - Increase Redis memory limit if needed
   - Configure Redis persistence (RDB/AOF)
   - Use connection pooling (already implemented)

3. **Monitoring**
   - Set up log aggregation (ELK, Splunk, etc.)
   - Monitor container health
   - Alert on Redis connection failures

4. **Scaling**
   - Use Redis Cluster for high availability
   - Deploy multiple API replicas behind load balancer
   - Configure appropriate resource limits

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start services in background |
| `docker-compose down` | Stop services |
| `docker-compose logs -f api` | View API logs |
| `docker-compose exec api /bin/sh` | Access API container |
| `docker-compose exec redis redis-cli -a <password>` | Access Redis CLI |
| `docker-compose --profile test run --rm tests` | Run tests |
| `docker-compose restart api` | Restart API service |
| `docker-compose ps` | Show container status |

---

**For more information, see the main [README.md](../README.md)**
