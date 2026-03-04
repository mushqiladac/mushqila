#!/bin/bash
# Fix EC2 Permission Issues and Fresh Deploy

echo "🔧 Fixing EC2 Deployment - Permission Issues"
echo "=============================================="

# 1. Stop all containers first
echo "1️⃣ Stopping all containers..."
cd ~/mushqila 2>/dev/null || cd ~
docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true

# 2. Use sudo to remove the directory
echo "2️⃣ Removing old code with sudo..."
cd ~
sudo rm -rf mushqila

# 3. Clean Docker to free memory
echo "3️⃣ Cleaning Docker (70% -> 20% memory)..."
docker system prune -af --volumes
docker image prune -af

# 4. Fresh clone
echo "4️⃣ Cloning fresh code from GitHub..."
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila

# 5. Create .env.production
echo "5️⃣ Creating .env.production file..."
cat > .env.production << 'EOF'
SECRET_KEY=django-insecure-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
DEBUG=False
ALLOWED_HOSTS=16.170.25.9,localhost,127.0.0.1

DB_ENGINE=postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=Sinan210
DB_HOST=database-1.cb4mqoeyyym6.eu-north-1.rds.amazonaws.com
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@mushqila.com

AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=mushqila-webmail
AWS_SES_REGION=us-east-1

REDIS_URL=redis://redis:6379/1
USE_CELERY=False
USE_S3=False

COMPANY_NAME=Mushqila Travel
DEFAULT_CURRENCY=SAR
TIME_ZONE=Asia/Riyadh

LOG_LEVEL=INFO
EOF

# 6. Build and start
echo "6️⃣ Building and starting containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# 7. Wait for services
echo "7️⃣ Waiting for services to start (30 seconds)..."
sleep 30

# 8. Check status
echo "8️⃣ Checking container status..."
docker-compose -f docker-compose.prod.yml ps

# 9. Check logs
echo "9️⃣ Checking web container logs..."
docker-compose -f docker-compose.prod.yml logs --tail=50 web

# 10. Test webmail
echo "🔟 Testing webmail endpoint..."
curl -I http://localhost:8000/webmail/

echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo "🌐 Access URLs:"
echo "   - Webmail: http://16.170.25.9:8000/webmail/"
echo "   - Main Site: http://16.170.25.9:8000/"
echo "   - Admin: http://16.170.25.9:8000/admin/"
echo ""
echo "📊 Check memory: free -h"
echo "📋 Check logs: docker-compose -f docker-compose.prod.yml logs -f web"
