#!/bin/bash
# Run pytest tests for CacheManager project

set -e

echo "🧪 Running tests..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
  echo "⚠️  Virtual environment not activated. Activating..."
  if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
  else
    echo "❌ Virtual environment not found. Please run setup-venv.sh first."
    exit 1
  fi
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
  echo "❌ pytest not found. Please install dependencies:"
  echo "  pip install -r requirements-dev.txt"
  exit 1
fi

# Run pytest with coverage
echo "📊 Running tests with coverage..."
pytest

echo ""
echo "✅ Tests complete!"
echo ""
echo "📄 Coverage report generated in htmlcov/index.html"
echo ""
