# 🔧 Fix Hanging Curl on EC2

## 🎯 Current Issue

```bash
curl http://localhost/ | head -20
# Hangs at 0% - no response
```

**Container Status:**
- ✅ Docker containers running
- ✅ Gunicorn listening on 0.0.0.0:8000
- ✅ Port mapping: 0.0.0.0:80->8000/tcp
- ✅ Logs show: "GET / HTTP/1.1" 302
- ⚠️ Request hanging/not completing

## 🔍 Root Cause Analysis

The 302 redirect suggests Django is responding, but the request isn't completing. Possible causes:

1. **Database Connection Timeout** - RDS connection slow/hanging
2. **Static Files Issue** - Missing static files causing hang
3. **Middleware Blocking** - Some middleware waiting indefinitely
4. **DNS Resolution** - Container trying to resolve domain names
5. **Gunicorn Worker Timeout** - Workers not responding

## ✅ Solution Steps

### Step 1: Test from Browser (NOT localhost curl)

The issue might be specific to localhost curl. Test from actual browser:

```bash
# From your local machine browser:
http://mushqila.com
http://www.mushqila.com
http://16.170.25.9
```

**Why this might work:**
- Browser handles redirects better
- DNS propagation might be complete
- External access might bypass localhost issues

### Step 2: Check Database Connection

```bash
# SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# Test database connection
cd ~/mushqila
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell

# If it hangs, database is the issue
# Press Ctrl+C to exit

# Check database connectivity
docker-compose -f docker-compose.prod.yml exec web python -c "
from django.db import connection
try:
    connection.ensure_connection()
    print('✅ Database connected')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

### Step 3: Increase Gunicorn Timeout

The default timeout might be too short for RDS connection:

```bash
# SSH to EC2
cd ~/mushqila

# Edit entrypoint.sh to increase timeout
nano entrypoint.sh

# Find the gunicorn line and add --timeout 120:
# gunicorn config.wsgi:application \
#     --bind 0.0.0.0:8000 \
#     --workers 3 \
#     --threads 2 \
#     --timeout 120 \
#     --access-logfile - \
#     --error-logfile -

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Wait and test
sleep 30
```

### Step 4: Check .env.production Database Settings

```bash
# Verify RDS connection string
cat .env.production | grep DATABASE

# Should show:
# DATABASE_URL=postgresql://username:password@database-1.cb4mqoeyyym6.eu-north-1.rds.amazonaws.com:5432/postgres
```

### Step 5: Test with Simple Health Check

```bash
# Create a simple health endpoint that doesn't touch database
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# In shell:
from django.http import HttpResponse
from django.urls import path

# Test if Django is responding at all
```

### Step 6: Check Container Logs in Real-Time

```bash
# Watch logs while making request
docker-compose -f docker-compose.prod.yml logs -f web

# In another terminal, make request:
curl -v http://localhost/

# Look for:
# - Database connection errors
# - Timeout errors
# - Middleware errors
```

## 🚀 Quick Fix Commands

### Option 1: Restart with Fresh Build

```bash
cd ~/mushqila

# Stop everything
docker-compose -f docker-compose.prod.yml down

# Clean Docker cache
docker system prune -f

# Fresh build
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate

# Wait
sleep 60

# Test from browser (not curl)
# http://16.170.25.9
```

### Option 2: Test Direct Container Access

```bash
# Get container IP
docker inspect mushqila_web | grep IPAddress

# Test direct container access
curl http://<container-ip>:8000/

# If this works, port mapping is the issue
```

### Option 3: Check if it's Just Curl Issue

```bash
# Try wget instead of curl
wget -O- http://localhost/

# Try with timeout
curl --max-time 10 http://localhost/

# Try specific endpoint
curl http://localhost/admin/
```

## 🌐 Most Likely Solution

**The site is probably working fine from external access!**

The localhost curl hanging might be a Docker networking quirk. Test from:

1. **Your browser:** http://mushqila.com
2. **Your browser:** http://16.170.25.9
3. **External tool:** https://www.isitdownrightnow.com/

If these work, the deployment is successful and localhost curl is just a red herring.

## 📊 Expected Behavior

When working correctly:

```bash
# From browser:
http://mushqila.com → Redirects to /accounts/landing/
http://16.170.25.9 → Redirects to /accounts/landing/

# You should see:
# - Landing page with search widget
# - Payment logos in footer
# - Social media icons
# - Professional styling
```

## 🔍 Diagnostic Checklist

- [ ] Test from browser (not curl)
- [ ] Check if domain resolves: `nslookup mushqila.com`
- [ ] Check if port 80 is accessible externally
- [ ] Verify database connection
- [ ] Check Gunicorn timeout settings
- [ ] Review container logs for errors
- [ ] Test direct container IP access

## 💡 Why Localhost Curl Might Hang

1. **Docker Bridge Network** - Localhost routing through Docker bridge
2. **Redirect Loop** - 302 redirect might loop on localhost
3. **DNS Resolution** - Container trying to resolve localhost
4. **Gunicorn Binding** - Binding to 0.0.0.0 might not work with localhost

**Solution:** Test from external browser, not localhost curl!

## ✅ Success Indicators

If deployment is successful:

1. ✅ Containers running: `docker ps`
2. ✅ Gunicorn started: Logs show "Listening at: http://0.0.0.0:8000"
3. ✅ Static files collected: "186 static files copied"
4. ✅ Port mapped: "0.0.0.0:80->8000/tcp"
5. ✅ No error logs: Check `docker-compose logs web`

**Next:** Test from browser at http://mushqila.com

---

**TL;DR:** Don't trust localhost curl. Test from browser at http://mushqila.com or http://16.170.25.9
