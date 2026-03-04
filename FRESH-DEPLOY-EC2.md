# Fresh EC2 Deployment - Clean Install

## 🧹 Clean Up and Fresh Deploy

Run these commands on your EC2 server to do a fresh deployment:

```bash
# 1. Stop and remove all containers
docker-compose -f docker-compose.prod.yml down -v

# 2. Clean up Docker to free memory (70% -> ~20%)
docker system prune -af --volumes
docker image prune -af

# 3. Remove old code
cd ~
rm -rf mushqila

# 4. Fresh clone from GitHub
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila

# 5. Create .env.production file
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

# 6. Start fresh deployment
docker-compose -f docker-compose.prod.yml up -d --build

# 7. Wait for services to start
sleep 30

# 8. Check status
docker-compose -f docker-compose.prod.yml ps

# 9. Test webmail
curl http://localhost:8000/webmail/
```

## ✅ What This Does

1. **Cleans Docker** - Removes all old images/containers (frees 50%+ memory)
2. **Fresh Code** - Clones latest from GitHub with webmail URL configured
3. **Fresh Build** - Builds new containers from scratch
4. **Uses RDS** - Database already has all tables from earlier migration

## 🌐 Access After Deployment

- **Webmail**: http://16.170.25.9:8000/webmail/
- **Main Site**: http://16.170.25.9:8000/
- **Admin**: http://16.170.25.9:8000/admin/

## 📊 Memory Usage

- Before: ~70%
- After cleanup: ~20%
- After deployment: ~35-40%

## ⏱️ Estimated Time

- Cleanup: 2 minutes
- Clone: 30 seconds
- Build: 5-7 minutes
- Total: ~10 minutes

---

**Status**: Ready to deploy
**Database**: Already migrated (no migration needed)
**Code**: Latest on GitHub with webmail
