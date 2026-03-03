# Quick Fix: Create .env.production on EC2

## Problem
`.env.production` file is missing on EC2 server, causing Docker deployment to fail.

## Solution (2 Options)

### Option 1: Quick Create (Recommended)

Run these commands on your EC2 server:

```bash
# Create .env.production file
cat > .env.production << 'EOF'
SECRET_KEY=django-insecure-p8k#m2@v9x$w5n7q!r4t6y8u0i-change-this-later
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

# Now deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser (optional)
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Option 2: Download from GitHub

```bash
# Pull the template from GitHub
git pull origin main

# Copy template to production
cp .env.production.template .env.production

# Edit with your values
nano .env.production

# Deploy
docker-compose -f docker-compose.prod.yml up -d --build
```

## After Deployment

1. **Check if webmail is working:**
   ```
   http://16.170.25.9:8000/webmail/
   ```

2. **View logs if there are issues:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f web
   ```

3. **Check running containers:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

## Important Notes

1. **SECRET_KEY**: Change to a random 50+ character string in production
2. **DB_PASSWORD**: Use a strong password
3. **AWS Credentials**: Only needed if you want to use webmail features
4. **Email Settings**: Can use console backend for now (emails will print to logs)

## Generate Strong SECRET_KEY

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## Verify Deployment

```bash
# Check if all containers are running
docker-compose -f docker-compose.prod.yml ps

# Should show:
# - web (running)
# - db (running)
# - nginx (running)

# Test webmail URL
curl http://localhost:8000/webmail/
```

## Troubleshooting

### If webmail still not found:

```bash
# Check if webmail app is installed
docker-compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.conf import settings; print('webmail' in settings.INSTALLED_APPS)"

# Check migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations webmail

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### If database connection fails:

```bash
# Check database container
docker-compose -f docker-compose.prod.yml logs db

# Recreate database
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

## Quick Commands Reference

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

**Estimated Time:** 2-3 minutes
**Status:** Ready to fix
