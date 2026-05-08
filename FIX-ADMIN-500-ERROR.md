# Django Admin 500 Error Fix

## সমস্যা (Problem)
Django admin panel এ access করতে গেলে Server Error (500) দেখাচ্ছে:
```
URL: https://mushqila.com/admin/login/?next=/admin/
Error: Server Error (500)
```

## সম্ভাব্য কারণ (Possible Causes)

### 1. Static Files Missing (সবচেয়ে সম্ভাব্য)
Django admin এর CSS/JS files collect করা হয়নি।

### 2. Database Connection Issue
Database এর সাথে connection problem।

### 3. Missing Migrations
Database migrations run করা হয়নি।

### 4. Settings Configuration
DEBUG, ALLOWED_HOSTS, বা অন্য settings এ সমস্যা।

### 5. Permission Issues
Static files directory তে permission নেই।

## Quick Fix Commands

### Fix 1: Collect Static Files (সবচেয়ে গুরুত্বপূর্ণ)

```bash
# SSH to production server
ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com

# Navigate to project
cd ~/mushqila

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --clear

# Check if admin static files exist
docker-compose -f docker-compose.prod.yml exec web ls -la /app/staticfiles/admin/

# Restart web container
docker-compose -f docker-compose.prod.yml restart web
```

### Fix 2: Run Migrations

```bash
# Check for pending migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Restart
docker-compose -f docker-compose.prod.yml restart web
```

### Fix 3: Check Database Connection

```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell

# If successful, you'll see PostgreSQL prompt
# Type \q to exit
```

### Fix 4: Check Container Logs

```bash
# View recent logs
docker-compose -f docker-compose.prod.yml logs web --tail=100

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs web -f

# Look for error messages like:
# - "No such file or directory"
# - "Permission denied"
# - "Connection refused"
# - "OperationalError"
```

### Fix 5: Verify Settings

```bash
# Check Django settings
docker-compose -f docker-compose.prod.yml exec web python manage.py shell << EOF
from django.conf import settings
print(f"DEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
print(f"STATIC_URL: {settings.STATIC_URL}")
print(f"DATABASE: {settings.DATABASES['default']['NAME']}")
EOF
```

## Complete Fix Script

```bash
#!/bin/bash
# Complete fix for Django admin 500 error

cd ~/mushqila

echo "1. Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput --clear

echo "2. Running migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

echo "3. Running Django check..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py check

echo "4. Restarting containers..."
docker-compose -f docker-compose.prod.yml restart

echo "5. Waiting for restart..."
sleep 10

echo "6. Testing admin URL..."
curl -I https://mushqila.com/admin/

echo "Done! Try accessing admin now."
```

## Detailed Troubleshooting

### Step 1: Check Container Status

```bash
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                  STATUS
# mushqila_web          Up
# mushqila_db           Up
# mushqila_redis        Up
```

### Step 2: Check Static Files Directory

```bash
# Check if staticfiles directory exists
docker-compose -f docker-compose.prod.yml exec web ls -la /app/staticfiles/

# Check admin static files
docker-compose -f docker-compose.prod.yml exec web ls -la /app/staticfiles/admin/css/

# Expected: Should see admin CSS/JS files
```

### Step 3: Check Nginx Configuration

```bash
# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx --tail=50

# Check nginx is serving static files
curl -I https://mushqila.com/static/admin/css/base.css
```

### Step 4: Check Database

```bash
# Check database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py check --database default

# List all tables
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell << EOF
\dt
\q
EOF
```

### Step 5: Check Environment Variables

```bash
# Check .env.production file
cat ~/mushqila/.env.production | grep -E "DEBUG|ALLOWED_HOSTS|DB_"

# Expected:
# DEBUG=False
# ALLOWED_HOSTS=mushqila.com,www.mushqila.com
# DB_NAME=postgres
# DB_USER=postgres
# DB_PASSWORD=Sinan210
# DB_HOST=database-1.cb4mqoeyyym6.eu-north-1.rds.amazonaws.com
```

## Common Error Messages and Solutions

### Error: "No such file or directory: '/app/staticfiles/admin/css/base.css'"
**Solution:** Run collectstatic
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Error: "OperationalError: FATAL: password authentication failed"
**Solution:** Check database credentials in .env.production
```bash
# Update .env.production with correct credentials
DB_PASSWORD=Sinan210
DB_HOST=database-1.cb4mqoeyyym6.eu-north-1.rds.amazonaws.com
```

### Error: "DisallowedHost at /admin/"
**Solution:** Add domain to ALLOWED_HOSTS
```bash
# In .env.production
ALLOWED_HOSTS=mushqila.com,www.mushqila.com,16.171.21.135
```

### Error: "ProgrammingError: relation does not exist"
**Solution:** Run migrations
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## Verification Steps

After applying fixes, verify:

### 1. Check Admin Page
```bash
curl -I https://mushqila.com/admin/
# Expected: HTTP/2 200 or HTTP/2 302
```

### 2. Check Static Files
```bash
curl -I https://mushqila.com/static/admin/css/base.css
# Expected: HTTP/2 200
```

### 3. Check Login Page
```bash
curl https://mushqila.com/admin/login/ | grep "Django administration"
# Should see Django admin login page HTML
```

### 4. Test Login
- Go to: https://mushqila.com/admin/
- Login with superuser credentials
- Should see Django admin dashboard

## Create Superuser (If Needed)

```bash
# Create a new superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Or use existing user
docker-compose -f docker-compose.prod.yml exec web python manage.py shell << EOF
from accounts.models import User
user = User.objects.get(email='admin@mushqila.com')
user.is_superuser = True
user.is_staff = True
user.save()
print(f"User {user.email} is now superuser")
EOF
```

## Prevention

To prevent this issue in future deployments:

### 1. Update deploy.yml workflow
Ensure collectstatic runs in deployment:
```yaml
- name: Collect Static Files
  run: |
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput --clear
```

### 2. Add to deploy.sh
```bash
echo "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
```

### 3. Check Before Deploy
```bash
# Always run before deploying
python manage.py check --deploy
python manage.py collectstatic --noinput --dry-run
```

## Quick One-Liner Fix

```bash
ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com "cd ~/mushqila && docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput && docker-compose -f docker-compose.prod.yml restart web"
```

## Status Check

After fixes, check status:

```bash
# All in one check
cd ~/mushqila
echo "Container Status:" && docker-compose -f docker-compose.prod.yml ps
echo -e "\nStatic Files:" && docker-compose -f docker-compose.prod.yml exec web ls /app/staticfiles/admin/ | head -5
echo -e "\nAdmin URL:" && curl -I https://mushqila.com/admin/ 2>&1 | head -1
echo -e "\nDatabase:" && docker-compose -f docker-compose.prod.yml exec -T web python manage.py check --database default
```

## Expected Result

After successful fix:
- ✅ https://mushqila.com/admin/ returns 200 or 302
- ✅ Admin login page loads with proper styling
- ✅ Can login with superuser credentials
- ✅ Admin dashboard displays correctly

---

**Most Common Fix:** Run `collectstatic` and restart containers

**Priority:** High - Admin panel is critical for management

**Status:** Awaiting fix on production server
