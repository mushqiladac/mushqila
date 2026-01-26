#!/bin/bash

# Initial EC2 Setup Script
# Run this ONCE on your EC2 instance after first login

set -e

echo "🔧 Setting up EC2 instance for Mushqila deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add ubuntu user to docker group
echo "👤 Adding user to docker group..."
sudo usermod -aG docker ubuntu

# Install Git
echo "📚 Installing Git..."
sudo apt-get install -y git

# Install netcat for database health check
echo "🔌 Installing netcat..."
sudo apt-get install -y netcat

# Clone repository
echo "📥 Cloning repository..."
cd /home/ubuntu
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila

# Create .env.production file
echo "📝 Creating .env.production file..."
cat > .env.production << 'EOF'
# Production Environment Variables
DEBUG=False
SECRET_KEY=CHANGE-THIS-TO-RANDOM-SECRET-KEY
ALLOWED_HOSTS=16.170.104.186,mushqila.com,www.mushqila.com

# AWS RDS Database
DB_NAME=mushqila
DB_USER=postgres
DB_PASSWORD=YOUR-RDS-PASSWORD
DB_HOST=database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com
DB_PORT=5432

# AWS SES Email
EMAIL_HOST=email-smtp.eu-north-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=AKIAUQETDVDPECKLURNW
EMAIL_HOST_PASSWORD=BGa2ERSVz5NxV9Od/sX2ONERAdtSrq9tJfStFJaYXmXm
DEFAULT_FROM_EMAIL=noreply@mushqila.com

# Travelport Galileo
TRAVELPORT_USERNAME=your_username
TRAVELPORT_PASSWORD=your_password
TRAVELPORT_BRANCH_CODE=P702214
TRAVELPORT_TARGET_BRANCH=P702214
TRAVELPORT_BASE_URL=https://americas-uapi.travelport.com
TRAVELPORT_REST_URL=https://americas-uapi.travelport.com/B2BGateway/connect/rest

REDIS_URL=redis://redis:6379/0
EOF

echo "⚠️  IMPORTANT: Edit .env.production and update:"
echo "   - SECRET_KEY (generate random string)"
echo "   - DB_PASSWORD (your RDS password)"
echo "   - TRAVELPORT credentials"

# Make deploy script executable
chmod +x deploy.sh

echo "✅ EC2 setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env.production with your actual credentials"
echo "2. Run: ./deploy.sh"
echo "3. Configure GitHub Actions secret EC2_SSH_KEY"
