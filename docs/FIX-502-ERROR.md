# Fix 502 Bad Gateway Error - Mushqila.com

## 🔴 Problem
Website showing: **502 Bad Gateway nginx/1.24.0 (Ubuntu)**

This means:
- ✅ Nginx is running
- ❌ Gunicorn (Django app server) is NOT running or not responding

---

## 🔧 Quick Fix (Run on Server)

### Step 1: SSH to Server
```bash
ssh root@mushqila.com
# or
ssh ubuntu@mushqila.com
```

### Step 2: Check Gunicorn Status
```bash
sudo systemctl status gunicorn
```

**If it shows "inactive (dead)" or "failed":**

### Step 3: Check Gunicorn Logs
```bash
sudo journalctl -u gunicorn -n 50 --no-pager
```

### Step 4: Restart Gunicorn
```bash
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

### Step 5: If Still Not Working, Check Django
```bash
cd /home/ubuntu/mushqila
# or
cd /root/mushqila

# Activate virtual environment
source venv/bin/activate

# Test Django
python manage.py check

# Check for errors
python manage.py runserver 0.0.0.0:8000
# Press Ctrl+C after checking
```

---

## 🔍 Common Issues & Solutions

### Issue 1: Gunicorn Service Not Found
```bash
# Check if gunicorn.service exists
ls -la /etc/systemd/system/gunicorn.service

# If not found, create it:
sudo nano /etc/systemd/system/gunicorn.service
```

**Gunicorn Service File:**
```ini
[Unit]
Description=Gunicorn daemon for Mushqila Django Project
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/mushqila
Environment="PATH=/home/ubuntu/mushqila/venv/bin"
ExecStart=/home/ubuntu/mushqila/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/home/ubuntu/mushqila/gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Then:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
```

---

### Issue 2: Database Connection Error
```bash
# Check database
cd /home/ubuntu/mushqila
source venv/bin/activate
python manage.py dbshell
# If error, check .env.production file
```

**Fix .env.production:**
```bash
nano .env.production
```

Make sure:
```env
DB_HOST=your-rds-endpoint.amazonaws.com
DB_NAME=mushqila
DB_USER=postgres
DB_PASSWORD=your-password
DB_PORT=5432
```

---

### Issue 3: Missing Dependencies
```bash
cd /home/ubuntu/mushqila
source venv/bin/activate
pip install -r requirements.txt
```

---

### Issue 4: Static Files Not Collected
```bash
cd /home/ubuntu/mushqila
source venv/bin/activate
python manage.py collectstatic --noinput
```

---

### Issue 5: Migrations Not Applied
```bash
cd /home/ubuntu/mushqila
source venv/bin/activate
python manage.py migrate
```

---

### Issue 6: Permission Issues
```bash
# Fix ownership
sudo chown -R ubuntu:www-data /home/ubuntu/mushqila
sudo chmod -R 755 /home/ubuntu/mushqila

# Fix socket permissions
sudo chmod 660 /home/ubuntu/mushqila/gunicorn.sock
```

---

## 🚀 Complete Restart Sequence

Run these commands in order:

```bash
# 1. Go to project directory
cd /home/ubuntu/mushqila

# 2. Activate virtual environment
source venv/bin/activate

# 3. Pull latest code
git pull origin main

# 4. Install dependencies
pip install -r requirements.txt

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Run migrations
python manage.py migrate

# 7. Restart Gunicorn
sudo systemctl restart gunicorn

# 8. Check status
sudo systemctl status gunicorn

# 9. Restart Nginx
sudo systemctl restart nginx

# 10. Check Nginx status
sudo systemctl status nginx

# 11. Check logs
sudo journalctl -u gunicorn -n 20 --no-pager
sudo tail -f /var/log/nginx/error.log
```

---

## 🔍 Check Nginx Configuration

```bash
# Test nginx config
sudo nginx -t

# View nginx config
sudo cat /etc/nginx/sites-available/mushqila

# Restart nginx
sudo systemctl restart nginx
```

---

## 📊 Monitor Logs in Real-Time

**Terminal 1 - Gunicorn logs:**
```bash
sudo journalctl -u gunicorn -f
```

**Terminal 2 - Nginx error logs:**
```bash
sudo tail -f /var/log/nginx/error.log
```

**Terminal 3 - Nginx access logs:**
```bash
sudo tail -f /var/log/nginx/access.log
```

---

## ⚡ Quick Diagnostic Script

Create and run this script on server:

```bash
nano check-status.sh
```

**Content:**
```bash
#!/bin/bash

echo "=== Mushqila Server Status Check ==="
echo ""

echo "1. Gunicorn Status:"
sudo systemctl status gunicorn | grep Active
echo ""

echo "2. Nginx Status:"
sudo systemctl status nginx | grep Active
echo ""

echo "3. Gunicorn Socket:"
ls -la /home/ubuntu/mushqila/gunicorn.sock
echo ""

echo "4. Recent Gunicorn Logs:"
sudo journalctl -u gunicorn -n 5 --no-pager
echo ""

echo "5. Recent Nginx Errors:"
sudo tail -n 5 /var/log/nginx/error.log
echo ""

echo "6. Disk Space:"
df -h | grep -E 'Filesystem|/$'
echo ""

echo "7. Memory Usage:"
free -h
echo ""

echo "=== End of Status Check ==="
```

**Run it:**
```bash
chmod +x check-status.sh
./check-status.sh
```

---

## 🆘 Emergency Recovery

If nothing works, restart everything:

```bash
# Stop all services
sudo systemctl stop gunicorn
sudo systemctl stop nginx

# Kill any hanging processes
sudo pkill -f gunicorn
sudo pkill -f nginx

# Start services
sudo systemctl start gunicorn
sudo systemctl start nginx

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

## 📞 Get Help

If still not working, check:

1. **Gunicorn logs:**
   ```bash
   sudo journalctl -u gunicorn -n 100 --no-pager > gunicorn-logs.txt
   ```

2. **Nginx error logs:**
   ```bash
   sudo tail -n 100 /var/log/nginx/error.log > nginx-errors.txt
   ```

3. **Django check:**
   ```bash
   cd /home/ubuntu/mushqila
   source venv/bin/activate
   python manage.py check > django-check.txt 2>&1
   ```

Send these files for debugging.

---

## ✅ Success Indicators

Website is working when:
- ✅ `systemctl status gunicorn` shows "active (running)"
- ✅ `systemctl status nginx` shows "active (running)"
- ✅ `ls -la /home/ubuntu/mushqila/gunicorn.sock` shows the socket file
- ✅ No errors in `sudo journalctl -u gunicorn -n 20`
- ✅ Website loads at https://mushqila.com

---

**Created:** 2026-04-19  
**Status:** Troubleshooting Guide  
**Priority:** 🔴 Critical
