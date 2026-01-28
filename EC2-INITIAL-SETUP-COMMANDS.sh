#!/bin/bash
# EC2 Initial Setup Commands
# Run these commands on EC2 for first-time setup

echo "=========================================="
echo "EC2 Initial Setup for CI/CD Deployment"
echo "=========================================="

# Step 1: Update system
echo "Step 1: Updating system..."
sudo apt update
sudo apt upgrade -y

# Step 2: Install Docker
echo "Step 2: Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
rm get-docker.sh

# Step 3: Install Docker Compose
echo "Step 3: Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Step 4: Verify installations
echo "Step 4: Verifying installations..."
docker --version
docker-compose --version

# Step 5: Clone repository
echo "Step 5: Cloning repository..."
cd /home/ubuntu
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila

# Step 6: Create .env.production file
echo "Step 6: Creating .env.production file..."
cat > .env.production << 'EOF'
# Django Settings
DEBUG=False
SECRET_KEY=CHANGE_THIS_TO_RANDOM_SECRET_KEY
ALLOWED_HOSTS=16.170.104.186,mushqila.com,www.mushqila.com

# Database (AWS RDS)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mushqila
DB_USER=postgres
DB_PASSWORD=YOUR_RDS_PASSWORD_HERE
DB_HOST=database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com
DB_PORT=5432

# Email (AWS SES)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.eu-north-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=AKIAUQETDVDPECKLURNW
EMAIL_HOST_PASSWORD=YOUR_SES_PASSWORD_HERE
DEFAULT_FROM_EMAIL=noreply@mushqila.com

# Galileo GDS (when available)
TRAVELPORT_USERNAME=
TRAVELPORT_PASSWORD=
TRAVELPORT_BRANCH_CODE=P702214

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
EOF

echo ""
echo "=========================================="
echo "IMPORTANT: Edit .env.production file!"
echo "=========================================="
echo "Run: nano .env.production"
echo ""
echo "Update these values:"
echo "1. SECRET_KEY - Generate with: python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
echo "2. DB_PASSWORD - Your RDS password"
echo "3. EMAIL_HOST_PASSWORD - Your SES password"
echo ""
echo "After editing, run:"
echo "docker-compose -f docker-compose.prod.yml up -d"
echo "=========================================="
