#!/bin/bash
# Run tests in Docker environment

set -e

echo "Running tests in Docker environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Please start Docker Desktop."
  exit 1
fi

# Check if redis is running
if ! docker-compose ps redis | grep -q "Up"; then
  echo "Redis container is not running. Starting services..."
  docker-compose up -d redis
  echo "Waiting for Redis to be ready..."
  sleep 5
fi

# Run tests using docker-compose with test profile
echo "Running pytest in Docker container..."
docker-compose --profile test run --rm tests

echo ""
echo "Tests complete!"
echo ""
