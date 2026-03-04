# EC2 Fresh Deployment - Step by Step

## 🚨 Problem
- Permission denied when removing `mushqila` directory
- Memory usage at 70%
- Webmail URL not accessible (404 error)

## ✅ Solution
Run these commands **one by one** on your EC2 server:

### Step 1: Stop Containers
```bash
cd ~/mushqila
docker-compose -f docker-compose.prod.yml down -v
```

### Step 2: Remove Old Code (with sudo)
```bash
cd ~
sudo rm -rf mushqila
```
**Note**: Use `sudo` to fix permission issues

### Step 3: Clean Docker (Free Memory)
```bash
docker system prune -af --volumes
docker image prune -af
```
**Result**: Memory will drop from 70% to ~20%

### Step 4: Clone Fresh Code
```bash
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila
```

### Step 5: Create .env.production
```bash
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
```

### Step 6: Build and Start
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```
**Time**: 5-7 minutes

### Step 7: Wait and Check
```bash
# Wait 30 seconds
sleep 30

# Check status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs --tail=50 web
```

### Step 8: Test Webmail
```bash
curl http://localhost:8000/webmail/
```

## 🌐 Access URLs

After deployment:
- **Webmail**: http://16.170.25.9:8000/webmail/
- **Main Site**: http://16.170.25.9:8000/
- **Admin**: http://16.170.25.9:8000/admin/

## 📊 Check Memory
```bash
free -h
```

## 🔍 Troubleshooting

### If webmail still shows 404:
```bash
# Check if webmail URL is in config
docker-compose -f docker-compose.prod.yml exec web grep -n "webmail" config/urls.py

# Restart web container
docker-compose -f docker-compose.prod.yml restart web
```

### If containers won't start:
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Check disk space
df -h
```

### If database connection fails:
```bash
# Verify .env.production
cat .env.production | grep DB_

# Test RDS connection from EC2
psql -h database-1.cb4mqoeyyym6.eu-north-1.rds.amazonaws.com -U postgres -d postgres
```

## ⏱️ Timeline
- Cleanup: 2 minutes
- Clone: 30 seconds  
- Build: 5-7 minutes
- **Total**: ~10 minutes

## ✅ What's Fixed
1. ✅ Webmail URL added to `config/urls.py`
2. ✅ Code pushed to GitHub
3. ✅ Permission issue solution (use sudo)
4. ✅ Memory cleanup commands
5. ✅ Fresh deployment process

## 📝 Notes
- **No migrations needed** - RDS already has all tables
- **Fresh code** - Latest from GitHub with webmail configured
- **Clean Docker** - Removes old images to free memory
- **RDS Database** - Using AWS PostgreSQL (not local)
