# Stop Docker containers for CacheManager project

Write-Host "🛑 Stopping Docker containers..." -ForegroundColor Cyan

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
  Write-Host "❌ docker-compose.yml not found in current directory." -ForegroundColor Red
  exit 1
}

# Stop and remove containers
docker-compose down

Write-Host ""
Write-Host "✅ Containers stopped successfully!" -ForegroundColor Green
Write-Host ""
