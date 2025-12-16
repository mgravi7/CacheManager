#!/bin/bash
# Start Docker containers for CacheManager project

set -e

echo "🐳 Starting Docker containers..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Please start Docker Desktop."
  exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
  echo "🔧 Creating .env file from .env.example..."
  cp .env.example .env
  echo "✅ .env file created. You can customize it before running again."
fi

# Check if docker-compose exists
if [ ! -f "docker-compose.yml" ]; then
  echo "❌ docker-compose.yml not found in current directory."
  exit 1
fi

# Start containers
echo "🚀 Starting Redis and FastAPI containers..."
docker-compose up -d --build

# Wait a moment for containers to initialize
echo "⏳ Waiting for containers to initialize..."
sleep 5

# Check container status
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "✅ Containers started successfully!"
echo ""
echo "🔗 Services available at:"
echo "  - FastAPI: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Redis: localhost:6379 (password required)"
echo ""
echo "To view logs, run:"
echo "  docker-compose logs -f"
echo ""
echo "To run tests in Docker, run:"
echo "  ./scripts/bash/docker-test.sh"
echo ""
echo "To stop containers, run:"
echo "  ./scripts/bash/docker-down.sh"
echo ""
