# Start Docker containers for CacheManager project

Write-Host "Starting Docker containers..." -ForegroundColor Cyan

# Check if Docker is running
try {
  docker info | Out-Null
} catch {
  Write-Host "Docker is not running. Please start Docker Desktop." -ForegroundColor Red
  exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
  Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
  Copy-Item .env.example .env
  Write-Host ".env file created. You can customize it before running again." -ForegroundColor Green
}

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
  Write-Host "docker-compose.yml not found in current directory." -ForegroundColor Red
  exit 1
}

# Start containers
Write-Host "Starting Redis and FastAPI containers..." -ForegroundColor Cyan
docker-compose up -d --build

# Wait a moment for containers to initialize
Write-Host "Waiting for containers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check container status
Write-Host ""
Write-Host "Container Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "Containers started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Services available at:" -ForegroundColor Yellow
Write-Host "  - FastAPI: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Redis: localhost:6379 (password required)" -ForegroundColor White
Write-Host ""
Write-Host "To view logs, run:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "To run tests in Docker, run:" -ForegroundColor Yellow
Write-Host "  .\scripts\powershell\docker-test.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To stop containers, run:" -ForegroundColor Yellow
Write-Host "  .\scripts\powershell\docker-down.ps1" -ForegroundColor White
Write-Host ""
