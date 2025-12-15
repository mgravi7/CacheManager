# Run pytest tests for CacheManager project

Write-Host "🧪 Running tests..." -ForegroundColor Cyan

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
  Write-Host "⚠️  Virtual environment not activated. Activating..." -ForegroundColor Yellow
  if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
  } else {
    Write-Host "❌ Virtual environment not found. Please run setup-venv.ps1 first." -ForegroundColor Red
    exit 1
  }
}

# Check if pytest is installed
try {
  pytest --version | Out-Null
} catch {
  Write-Host "❌ pytest not found. Please install dependencies:" -ForegroundColor Red
  Write-Host "  pip install -r requirements-dev.txt" -ForegroundColor Yellow
  exit 1
}

# Run pytest with coverage
Write-Host "📊 Running tests with coverage..." -ForegroundColor Cyan
pytest

Write-Host ""
Write-Host "✅ Tests complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📄 Coverage report generated in htmlcov/index.html" -ForegroundColor Yellow
Write-Host ""
