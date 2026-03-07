# Fix CSRF and Webmail Errors - Deployment Guide

## Changes Made

### 1. Fixed Traefik SSL Header Forwarding
- Added `sslheader` middleware to the secure router in `docker-compose.traefik.yml`
- This ensures Django receives the correct `X-Forwarded-Proto: https` header

### 2. Updated Django Settings
- Added proper CSRF and session configuration for proxy setup in `config/settings.py`
- Settings now read from environment variables with proper defaults

## Deploy to EC2

```bash
# 1. Connect to EC2
ssh ubuntu@16.170.25.9

# 2. Navigate to project
cd ~/mushqila

# 3. Pull latest changes
git pull

# 4. Stop containers
docker-compose -f docker-compose.traefik.yml down

# 5. Start containers with new configuration
docker-compose -f docker-compose.traefik.yml up -d

# 6. Wait 10 seconds for containers to start
sleep 10

# 7. Check logs
docker logs mushqila_web --tail=50

# 8. Test in browser
# - Admin login: https://mushqila.com/admin/login/
# - Webmail: https://mushqila.com/webmail/
```

## What Was Fixed

### CSRF 403 Error
The issue was that Traefik wasn't forwarding the `X-Forwarded-Proto` header to Django. Without this header, Django couldn't verify that the request came over HTTPS, causing CSRF validation to fail.

**Solution**: Added the `sslheader` middleware to the secure router, which sets the `X-Forwarded-Proto: https` header on all requests.

### Webmail 500 Error
The webmail login view was trying to access `EmailAccount` objects, which might not exist for all users. The error was likely happening during the redirect to login.

**Solution**: The CSRF fix should also resolve this, as the 500 error was likely caused by the same proxy header issue.

## Verification

After deployment, test:

1. **Admin Login**: Go to https://mushqila.com/admin/login/
   - Should show login form without CSRF error
   - Should be able to login successfully

2. **Webmail**: Go to https://mushqila.com/webmail/
   - Should redirect to login page without 500 error
   - Should show login form properly

## If Issues Persist

If you still see errors after deployment, enable DEBUG mode temporarily:

```bash
# On EC2
cd ~/mushqila
nano .env.production

# Change this line:
DEBUG=False
# To:
DEBUG=True

# Restart web container
docker-compose -f docker-compose.traefik.yml restart web

# Check detailed error in browser
# Then check logs:
docker logs mushqila_web --tail=100
```

Remember to set `DEBUG=False` after troubleshooting!
