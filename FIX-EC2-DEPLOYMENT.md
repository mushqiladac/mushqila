# Fix EC2 Deployment Issues

## Issues Found:
1. Port 80 already in use
2. SECRET_KEY parsing error with special characters

## Solution

Run these commands on your EC2 server:

```bash
# Step 1: Stop any existing containers
docker-compose -f docker-compose.prod.yml down

# Step 2: Find what's using port 80
sudo lsof -i :80

# Step 3: Stop the process using port 80 (usually nginx or apache)
sudo systemctl stop nginx
# OR
sudo systemctl stop apache2

# Step 4: Create a proper .env.production file (without special characters that cause issues)
cat > .env.production << 'EOF'
SECRET_KEY=django-insecure-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
DEBUG=False
ALLOWED_HOSTS=16.170.25.9,localhost,127.0.0.1

DB_ENGINE=postgresql
DB_NAME=mushqila_db
DB_USER=mushqila_user
DB_PASSWORD=mushqila_secure_password_2024
DB_HOST=db
DB_PORT=5432

GALILEO_PCC=YOUR_PCC_CODE
GALILEO_USERNAME=YOUR_API_USERNAME
GALILEO_PASSWORD=YOUR_API_PASSWORD
GALILEO_TARGET_BRANCH=YOUR_TARGET_BRANCH
GALILEO_PROVIDER_CODE=1G
GALILEO_TIMEOUT=30
GALILEO_DEBUG=False

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

# Step 5: Start services
docker-compose -f docker-compose.prod.yml up -d --build

# Step 6: Wait 10 seconds for services to start
sleep 10

# Step 7: Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Step 8: Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Step 9: Check status
docker-compose -f docker-compose.prod.yml ps
```

## Alternative: Use Port 8000 Instead of 80

If you can't stop the service on port 80, access via port 8000:

```bash
# Just start without nginx
docker-compose -f docker-compose.prod.yml up -d web db redis

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Access via
http://16.170.25.9:8000/webmail/
```

## Verify Deployment

```bash
# Check running containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Test webmail
curl http://localhost:8000/webmail/
```

## If Still Having Issues

```bash
# Complete cleanup and restart
docker-compose -f docker-compose.prod.yml down -v
docker system prune -f
docker-compose -f docker-compose.prod.yml up -d --build
```
