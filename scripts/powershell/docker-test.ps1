# Run tests in Docker environment

Write-Host "Running tests in Docker environment..." -ForegroundColor Cyan

# Check if Docker is running
try {
  docker info | Out-Null
} catch {
  Write-Host "Docker is not running. Please start Docker Desktop." -ForegroundColor Red
  exit 1
}

# Check if redis is running
$redisStatus = docker-compose ps redis
if ($redisStatus -notmatch "Up") {
  Write-Host "Redis container is not running. Starting services..." -ForegroundColor Yellow
  docker-compose up -d redis
  Write-Host "Waiting for Redis to be ready..." -ForegroundColor Yellow
  Start-Sleep -Seconds 5
}

# Run tests using docker-compose with test profile
Write-Host "Running pytest in Docker container..." -ForegroundColor Cyan
docker-compose --profile test run --rm tests

Write-Host ""
Write-Host "Tests complete!" -ForegroundColor Green
Write-Host ""
