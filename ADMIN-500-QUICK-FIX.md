# Django Admin 500 Error - Quick Fix

## Problem
```
https://mushqila.com/admin/
Server Error (500)
```

## Root Cause
Django admin static files (CSS, JS) are not collected or not accessible.

## Solution

### Option 1: Run Fix Script (Recommended)

```bash
# On production server
ssh ubuntu@ip-172-31-36-20
cd ~/mushqila

# Download and run fix script
wget https://raw.githubusercontent.com/mushqiladac/mushqila/main/fix-admin-static-files.sh
chmod +x fix-admin-static-files.sh
./fix-admin-static-files.sh
```

### Option 2: Manual Fix

```bash
# SSH to production server
ssh ubuntu@ip-172-31-36-20
cd ~/mushqila

# Step 1: Collect static files
docker-compose exec web python manage.py collectstatic --noinput --clear

# Step 2: Set permissions
docker-compose exec web chown -R www-data:www-data /app/staticfiles

# Step 3: Restart web container
docker-compose restart web

# Step 4: Check logs
docker-compose logs -f web
```

### Option 3: Check Settings

Verify these settings in `config/settings.py`:

```python
# Static files configuration
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for serving static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Middleware (WhiteNoise should be after SecurityMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← This line
    # ... other middleware
]
```

## Verification

### Test Admin Access
```bash
# From your local machine
curl -I https://mushqila.com/admin/

# Should return:
# HTTP/2 200 OK  (or 302 redirect to login)
# NOT 500 error
```

### Check Static Files
```bash
# On production server
docker-compose exec web ls -la /app/staticfiles/admin/

# Should show admin static files:
# css/
# js/
# img/
# fonts/
```

### Check Nginx Logs
```bash
# On production server
docker-compose logs nginx | grep admin

# Look for 404 errors on static files
```

## Common Issues

### Issue 1: Static files not collected
**Solution**: Run `collectstatic` command

### Issue 2: Permission denied
**Solution**: Set proper ownership with `chown`

### Issue 3: WhiteNoise not installed
**Solution**: Check `requirements.txt` has `whitenoise`

### Issue 4: STATIC_ROOT not set
**Solution**: Verify `STATIC_ROOT` in settings.py

### Issue 5: DEBUG=True in production
**Solution**: Set `DEBUG=False` in `.env.production`

## Debug Commands

### Check Environment Variables
```bash
docker-compose exec web env | grep -E "DEBUG|STATIC"
```

### Check Django Settings
```bash
docker-compose exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.STATIC_ROOT)
>>> print(settings.STATIC_URL)
>>> print(settings.DEBUG)
```

### Test Static File Serving
```bash
# Test if static files are accessible
curl https://mushqila.com/static/admin/css/base.css
```

### Check Container Logs
```bash
# Real-time logs
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 web

# Filter for errors
docker-compose logs web | grep -i error
```

## Prevention

### Add to Deployment Script

Update `.github/workflows/deploy.yml` to always collect static files:

```yaml
- name: Collect Static Files
  run: |
    docker-compose exec -T web python manage.py collectstatic --noinput --clear
```

### Add Health Check

Create a health check endpoint to verify admin is working:

```python
# In a views.py
def health_check(request):
    from django.contrib import admin
    return JsonResponse({
        'status': 'ok',
        'admin_site': str(admin.site),
        'static_root': settings.STATIC_ROOT,
    })
```

## Expected Result

After fix:
- ✅ https://mushqila.com/admin/ → Shows login page
- ✅ Admin CSS/JS loads properly
- ✅ No 500 errors
- ✅ Can login and access admin panel

## If Still Not Working

### Check Database Connection
```bash
docker-compose exec web python manage.py dbshell
# Should connect to PostgreSQL
```

### Check Migrations
```bash
docker-compose exec web python manage.py showmigrations
# All should have [X] marks
```

### Check Superuser Exists
```bash
docker-compose exec web python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(is_superuser=True).exists()
True
```

### Enable Debug Temporarily
```bash
# Edit .env.production
DEBUG=True

# Restart
docker-compose restart web

# Visit admin to see actual error
# Then set DEBUG=False again
```

## Contact

If issue persists after trying all solutions:
1. Check logs: `docker-compose logs web`
2. Check nginx logs: `docker-compose logs nginx`
3. Check database: `docker-compose exec web python manage.py dbshell`
4. Enable DEBUG temporarily to see actual error

---

**Status**: Ready to fix
**Priority**: High
**Estimated Time**: 5 minutes
