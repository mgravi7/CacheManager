#!/bin/bash
# Stop Docker containers for CacheManager project

set -e

echo "🛑 Stopping Docker containers..."

# Check if docker-compose exists
if [ ! -f "docker-compose.yml" ]; then
  echo "❌ docker-compose.yml not found in current directory."
  exit 1
fi

# Stop and remove containers
docker-compose down

echo ""
echo "✅ Containers stopped successfully!"
echo ""
