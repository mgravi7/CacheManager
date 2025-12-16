# View Docker container logs

param(
    [string]$Service = "api"
)

Write-Host "Viewing logs for service: $Service" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

docker-compose logs -f $Service
