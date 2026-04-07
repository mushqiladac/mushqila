# 🔧 Fix 502 Bad Gateway Error

## Problem
Site showing: `502 Bad Gateway nginx/1.24.0 (Ubuntu)`

This means Docker containers are not running or not accessible.

---

## Quick Fix (Run on EC2)

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# Navigate to project
cd ~/mushqila

# Check container status
docker-compose -f docker-compose.prod.yml ps

# If containers are not running, start them
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f web

# Check if port 8000 is accessible
curl http://localhost:8000/

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx
```

---

## Complete Fix Steps

### Step 1: Check Docker Containers
```bash
cd ~/mushqila
docker-compose -f docker-compose.prod.yml ps
```

**Expected output:**
```
NAME                   STATUS
mushqila_web           Up
mushqila_redis         Up
mushqila_celery        Up
mushqila_celery_beat   Up
```

### Step 2: If Containers Not Running
```bash
# Stop everything
docker-compose -f docker-compose.prod.yml down

# Remove old containers
docker system prune -f

# Start fresh
docker-compose -f docker-compose.prod.yml up -d --build

# Wait 10 seconds
sleep 10

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Step 3: Check Application Logs
```bash
# Web container logs
docker-compose -f docker-compose.prod.yml logs --tail=50 web

# Look for errors like:
# - Database connection errors
# - Missing environment variables
# - Python import errors
```

### Step 4: Test Port 8000
```bash
# Test if Django is responding
curl http://localhost:8000/

# Should return HTML or redirect (not connection refused)
```

### Step 5: Check Nginx Configuration
```bash
# Test Nginx config
sudo nginx -t

# Check Nginx error logs
sudo tail -f /var/log/nginx/mushqila_error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Step 6: Verify Port Bindings
```bash
# Check what's listening on ports
sudo ss -tlnp | grep -E ':(80|443|8000)'

# Should see:
# Port 80: Nginx
# Port 443: Nginx
# Port 8000: Docker (127.0.0.1:8000)
```

---

## Common Issues & Solutions

### Issue 1: Database Connection Error
**Symptoms:** Logs show "could not connect to database"

**Solution:**
```bash
# Check .env.production file
cat .env.production | grep DB_

# Verify RDS is accessible
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell
```

### Issue 2: Port 8000 Already in Use
**Symptoms:** "Address already in use"

**Solution:**
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Restart containers
docker-compose -f docker-compose.prod.yml restart
```

### Issue 3: Missing .env.production
**Symptoms:** Containers start but crash immediately

**Solution:**
```bash
# Check if file exists
ls -la .env.production

# If missing, create it
nano .env.production
# Add all required variables (see .env.production.template)
```

### Issue 4: Nginx Can't Connect to Docker
**Symptoms:** 502 error, Nginx logs show "connect() failed"

**Solution:**
```bash
# Check docker-compose.prod.yml port binding
cat docker-compose.prod.yml | grep "8000"

# Should be: "127.0.0.1:8000:8000"

# If wrong, fix it:
nano docker-compose.prod.yml
# Change to: "127.0.0.1:8000:8000"

# Restart
docker-compose -f docker-compose.prod.yml restart
```

---

## Emergency Rollback

If nothing works, rollback to previous version:

```bash
# List backups
ls -lht ~/mushqila_backup_*

# Restore latest backup
cd ~
sudo rm -rf mushqila
sudo mv mushqila_backup_YYYYMMDD_HHMMSS mushqila
cd mushqila

# Start containers
docker-compose -f docker-compose.prod.yml up -d

# Restart Nginx
sudo systemctl restart nginx
```

---

## Verification

After fix, verify:

```bash
# 1. Containers running
docker-compose -f docker-compose.prod.yml ps

# 2. Port 8000 responding
curl http://localhost:8000/

# 3. Nginx working
curl http://localhost/

# 4. HTTPS working
curl https://mushqila.com/

# 5. Check in browser
# Visit: https://mushqila.com
```

---

## Prevention

To avoid 502 errors in future:

1. **Always check logs** before and after deployment
2. **Test locally** before pushing to production
3. **Use GitHub Actions** for automated deployment
4. **Keep backups** (automatic with GitHub Actions workflow)
5. **Monitor** container health regularly

---

## Quick Commands Reference

```bash
# Check everything
docker-compose -f docker-compose.prod.yml ps
sudo systemctl status nginx
curl http://localhost:8000/

# Restart everything
docker-compose -f docker-compose.prod.yml restart
sudo systemctl restart nginx

# View logs
docker-compose -f docker-compose.prod.yml logs -f
sudo tail -f /var/log/nginx/mushqila_error.log

# Full restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
sudo systemctl restart nginx
```

---

**Run these commands on EC2 to fix the 502 error!** 🚀
