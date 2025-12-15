# Setup Python virtual environment for CacheManager project

Write-Host "Setting up Python virtual environment..." -ForegroundColor Cyan

# Check if Python 3.12 is available
$pythonCmd = $null
if (Get-Command python3.12 -ErrorAction SilentlyContinue) {
  $pythonCmd = "python3.12"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $pythonVersion = python --version 2>&1
  if ($pythonVersion -match "Python 3\.1[2-9]") {
    $pythonCmd = "python"
  }
}

if (-not $pythonCmd) {
  Write-Host "Python 3.12+ is not installed or not in PATH" -ForegroundColor Red
  Write-Host "Please install Python 3.12 or later from https://www.python.org/downloads/" -ForegroundColor Yellow
  exit 1
}

# Display Python version
$version = & $pythonCmd --version
Write-Host "Using: $version" -ForegroundColor Green

# Create virtual environment
Write-Host "Creating virtual environment in .venv/..." -ForegroundColor Cyan
& $pythonCmd -m venv .venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install production dependencies
Write-Host "Installing production dependencies from requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt

# Install development dependencies
Write-Host "Installing development dependencies from requirements-dev.txt..." -ForegroundColor Cyan
pip install -r requirements-dev.txt

Write-Host ""
Write-Host "Virtual environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment in the future, run:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To deactivate, run:" -ForegroundColor Yellow
Write-Host "  deactivate" -ForegroundColor White
Write-Host ""
