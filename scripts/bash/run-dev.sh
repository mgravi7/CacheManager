#!/bin/bash
# Run FastAPI development server

set -e

echo "Starting FastAPI development server..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
  echo "Activating virtual environment..."
  if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
  else
    echo "Virtual environment not found. Please run setup-venv.sh first."
    exit 1
  fi
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
  echo "uvicorn not found. Please install dependencies:"
  echo "  pip install -r requirements.txt"
  exit 1
fi

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Run uvicorn
echo "Starting server at http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo ""

uvicorn user_api.main:app --host 0.0.0.0 --port 8000 --reload
