#!/bin/bash

# Fix Production Deployment - Connect to AWS RDS
# This script will:
# 1. Stop all containers
# 2. Remove old database container
# 3. Start services with AWS RDS connection
# 4. Run migrations
# 5. Collect static files

set -e

echo "=========================================="
echo "Fixing Production Deployment"
echo "=========================================="

# Stop all containers
echo "Stopping all containers..."
docker-compose -f docker-compose.prod.yml down

# Remove old database volume (optional - only if you want to clean up)
echo "Removing old database volume..."
docker volume rm mushqila_postgres_data 2>/dev/null || echo "Volume already removed or doesn't exist"

# Pull latest code (if needed)
echo "Pulling latest code..."
git pull origin main || echo "Already up to date"

# Build and start services
echo "Starting services with AWS RDS..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 20

# Check if web container is running
if ! docker ps | grep -q mushqila_web; then
    echo "ERROR: Web container failed to start!"
    echo "Checking logs..."
    docker-compose -f docker-compose.prod.yml logs web
    exit 1
fi

# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collect static files
echo "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Show container status
echo ""
echo "=========================================="
echo "Deployment Status"
echo "=========================================="
docker-compose -f docker-compose.prod.yml ps

# Show recent logs
echo ""
echo "=========================================="
echo "Recent Web Container Logs"
echo "=========================================="
docker-compose -f docker-compose.prod.yml logs --tail=50 web

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Website should be accessible at: https://mushqila.com"
echo ""
echo "To check logs: docker-compose -f docker-compose.prod.yml logs -f web"
echo "To restart: docker-compose -f docker-compose.prod.yml restart web"
echo "=========================================="
