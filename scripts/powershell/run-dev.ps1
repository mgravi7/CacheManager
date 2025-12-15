# Run FastAPI development server

Write-Host "Starting FastAPI development server..." -ForegroundColor Cyan

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
  Write-Host "Activating virtual environment..." -ForegroundColor Yellow
  if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
  } else {
    Write-Host "Virtual environment not found. Please run setup-venv.ps1 first." -ForegroundColor Red
    exit 1
  }
}

# Check if uvicorn is installed
try {
  uvicorn --version | Out-Null
} catch {
  Write-Host "uvicorn not found. Please install dependencies:" -ForegroundColor Red
  Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
  exit 1
}

# Set PYTHONPATH to include src directory
$env:PYTHONPATH = "$PWD\src;$env:PYTHONPATH"

# Run uvicorn
Write-Host ""
Write-Host "Starting server at http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

uvicorn user_api.main:app --host 0.0.0.0 --port 8000 --reload
