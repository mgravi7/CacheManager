#!/bin/bash
# View Docker container logs

SERVICE=${1:-api}

echo "Viewing logs for service: $SERVICE"
echo "Press Ctrl+C to stop"
echo ""

docker-compose logs -f $SERVICE
