#!/bin/bash

# EC2 Deployment Commands for Sinan Travel Platform
# Run these commands on your EC2 instance

echo "=========================================="
echo "Starting Deployment Process..."
echo "=========================================="

# 1. Navigate to project directory
cd /home/ubuntu/sinan

# 2. Pull latest code from GitHub
echo "Pulling latest code from GitHub..."
git pull origin dwd

# 3. Stop running containers
echo "Stopping Docker containers..."
docker-compose down

# 4. Rebuild and start containers
echo "Building and starting Docker containers..."
docker-compose up -d --build

# 5. Wait for containers to start
echo "Waiting for containers to start..."
sleep 10

# 6. Run migrations
echo "Running database migrations..."
docker-compose exec -T web python manage.py migrate

# 7. Collect static files
echo "Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

# 8. Check container status
echo "Checking container status..."
docker-compose ps

# 9. View logs
echo "Viewing recent logs..."
docker-compose logs --tail=50

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Your site should be live at: http://your-ec2-ip:8000"
