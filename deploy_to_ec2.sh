#!/bin/bash

# Deployment Script for EC2 Server
# Repository: https://github.com/mushqiladac/sinan.git
# Branch: dwd

echo "=========================================="
echo "Deploying to EC2 Server"
echo "=========================================="
echo ""

# Navigate to project directory
cd ~/mushqila || exit

echo "Step 1: Stopping containers..."
docker-compose -f docker-compose.prod.yml down

echo ""
echo "Step 2: Backing up current code..."
timestamp=$(date +%Y%m%d_%H%M%S)
cp -r ~/mushqila ~/mushqila_backup_$timestamp

echo ""
echo "Step 3: Fetching latest code from GitHub..."
git fetch origin

echo ""
echo "Step 4: Switching to dwd branch..."
git checkout dwd

echo ""
echo "Step 5: Pulling latest changes..."
git pull origin dwd

echo ""
echo "Step 6: Updating .env.production file..."
# RDS credentials are already updated in the file

echo ""
echo "Step 7: Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo ""
echo "Step 8: Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "Step 9: Running migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

echo ""
echo "Step 10: Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo ""
echo "Step 11: Checking container status..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Access your application at:"
echo "http://13.60.112.227:8000"
echo ""
echo "To view logs:"
echo "docker-compose -f docker-compose.prod.yml logs -f web"
echo ""
