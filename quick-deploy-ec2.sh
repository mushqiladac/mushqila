#!/bin/bash
# Quick EC2 Deployment Script for Mushqila
# Run this on your EC2 instance: bash quick-deploy-ec2.sh

set -e  # Exit on any error

echo "=========================================="
echo "Mushqila Quick Deployment Script"
echo "=========================================="

# Step 1: Update system
echo "Step 1: Updating system..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Docker and Docker Compose
echo "Step 2: Installing Docker..."
sudo apt install -y docker.io docker-compose git

# Step 3: Start Docker service
echo "Step 3: Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Step 4: Clone repository
echo "Step 4: Cloning repository..."
cd ~
if [ -d "mushqila" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd mushqila
    git pull
else
    git clone https://github.com/mushqiladac/mushqila.git
    cd mushqila
fi

# Step 5: Create .env.production file
echo "Step 5: Creating .env.production file..."
cat > .env.production << 'EOF'
# Django Settings
DEBUG=False
SECRET_KEY=django-insecure-prod-$(openssl rand -hex 32)
ALLOWED_HOSTS=13.60.112.227,ec2-13-60-112-227.eu-north-1.compute.amazonaws.com,localhost

# Database Settings (RDS)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mushqila_db
DB_USER=postgres
DB_PASSWORD=Sinan129380
DB_HOST=database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com
DB_PORT=5432

# Redis Settings
REDIS_HOST=redis
REDIS_PORT=6379

# Celery Settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Galileo API Settings
GALILEO_API_URL=
GALILEO_USERNAME=
GALILEO_PASSWORD=
GALILEO_PCC=
EOF

# Step 6: Build and start Docker containers
echo "Step 6: Building Docker containers (this may take 5-10 minutes)..."
sudo docker-compose -f docker-compose.prod.yml build

echo "Step 7: Starting containers..."
sudo docker-compose -f docker-compose.prod.yml up -d

# Step 8: Wait for containers to be ready
echo "Step 8: Waiting for containers to start..."
sleep 10

# Step 9: Run database migrations
echo "Step 9: Running database migrations..."
sudo docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Step 10: Collect static files
echo "Step 10: Collecting static files..."
sudo docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Step 11: Initialize chart of accounts
echo "Step 11: Initializing chart of accounts..."
sudo docker-compose -f docker-compose.prod.yml exec -T web python manage.py initialize_accounts || echo "Accounts already initialized"

# Step 12: Check container status
echo "Step 12: Checking container status..."
sudo docker-compose -f docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Your application is now running at:"
echo "  http://13.60.112.227"
echo "  http://ec2-13-60-112-227.eu-north-1.compute.amazonaws.com"
echo ""
echo "Next steps:"
echo "1. Create superuser: sudo docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo "2. Access admin panel: http://13.60.112.227/admin"
echo "3. View logs: sudo docker-compose -f docker-compose.prod.yml logs -f web"
echo ""
echo "=========================================="
