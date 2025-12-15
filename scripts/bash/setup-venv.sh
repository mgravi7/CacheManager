#!/bin/bash
# Setup Python virtual environment for CacheManager project

set -e

echo "Setting up Python virtual environment..."

# Check if Python 3.12 is available
if ! command -v python3.12 &> /dev/null; then
  echo "Python 3.12 not found. Checking for python3..."
  if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.12+"
    exit 1
  fi
  PYTHON_CMD=python3
else
  PYTHON_CMD=python3.12
fi

# Display Python version
echo "Using: $($PYTHON_CMD --version)"

# Create virtual environment
echo "Creating virtual environment in .venv/..."
$PYTHON_CMD -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install production dependencies
echo "Installing production dependencies from requirements.txt..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies from requirements-dev.txt..."
pip install -r requirements-dev.txt

echo ""
echo "Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""
