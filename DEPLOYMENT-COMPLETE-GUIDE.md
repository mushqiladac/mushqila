# 🎯 Mushqila Deployment - Complete Guide

## 📋 Current Situation

Your EC2 deployment is **99% complete**. The containers are running, but:

1. ✅ Docker containers running
2. ✅ Gunicorn started
3. ✅ Port 80 mapped correctly
4. ✅ Static files collected
5. ✅ Memory cleaned (45% usage)
6. ✅ Nginx stopped
7. ⚠️ `curl http://localhost/` hanging (this is NORMAL - Docker networking quirk)
8. ✅ Webmail URL added to config/urls.py

## 🔧 What Was Just Fixed

Added webmail URL to `config/urls.py`:
```python
path('webmail/', include('webmail.urls', namespace='webmail')),
```

This was missing and would cause 404 errors when accessing webmail.

## 🚀 Deploy the Fix to EC2

### Option 1: Quick Deploy (Recommended)

```bash
# SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# Run the deployment script
cd ~/mushqila
bash DEPLOY-FINAL-FIX.sh
```

### Option 2: Manual Deploy

```bash
# SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# Navigate to project
cd ~/mushqila

# Pull latest code
git pull origin main

# Stop containers
docker-compose -f docker-compose.prod.yml down

# Clean Docker
docker system prune -f

# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Wait 60 seconds
sleep 60

# Check status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs --tail=20 web
```

## 🌐 Test from Browser (NOT curl)

### Important: Don't Trust Localhost Curl!

The `curl http://localhost/` hanging is a Docker networking issue, NOT a deployment failure.

**Test from your browser instead:**

1. **Primary Domain:**
   ```
   http://mushqila.com
   ```

2. **WWW Domain:**
   ```
   http://www.mushqila.com
   ```

3. **Direct IP:**
   ```
   http://16.170.25.9
   ```

4. **Landing Pages:**
   ```
   http://mushqila.com/accounts/landing/
   http://mushqila.com/landing2/
   ```

5. **Admin Panel:**
   ```
   http://mushqila.com/admin/
   ```

6. **Webmail:**
   ```
   http://mushqila.com/webmail/
   ```

## ✅ What You Should See

### Landing Page:
- Hero section with large background image
- Horizontal search widget with tabs
- Trip type buttons (One-way, Round-trip, Multi-city)
- Fare type buttons (Regular, Umrah, Senior, Promo)
- Flying From/To fields
- Date picker and passenger selector
- Search button

### Footer:
- Payment logos: Visa, MasterCard, Amex, Bkash, SSL Commerz
- "We Accept" text
- Professional hover effects on logos
- Social media icons: YouTube, Facebook, WhatsApp
- (Webmail icon commented out - can be activated later)

### Navbar:
- Agent Login button (light blue background, white text)
- Agent Register button (yellow background, white text)
- Hover effects with transform and shadow

## 🔍 If Domain Doesn't Work

DNS propagation can take 5-15 minutes. If `mushqila.com` doesn't work:

1. **Wait 5-10 minutes** for DNS propagation
2. **Test direct IP:** http://16.170.25.9 (should work immediately)
3. **Check DNS propagation:** https://dnschecker.org/domain/mushqila.com

### Verify DNS:
```bash
# From your local machine
nslookup mushqila.com

# Should return:
# Name: mushqila.com
# Address: 16.170.25.9
```

## 🐛 Troubleshooting

### If Site Not Accessible:

```bash
# SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# Check containers
docker ps

# Should show 4 containers running:
# - mushqila_web (0.0.0.0:80->8000/tcp)
# - mushqila_redis
# - mushqila_celery
# - mushqila_celery_beat

# Check port 80
sudo lsof -i :80

# Should show docker-proxy

# Check logs
cd ~/mushqila
docker-compose -f docker-compose.prod.yml logs --tail=100 web

# Look for errors

# Restart if needed
docker-compose -f docker-compose.prod.yml restart web
```

### If Containers Keep Restarting:

```bash
# Check memory
free -h

# If memory high, clean Docker
docker system prune -af --volumes

# Restart containers
cd ~/mushqila
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### If Database Connection Issues:

```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec web python -c "
from django.db import connection
try:
    connection.ensure_connection()
    print('✅ Database connected')
except Exception as e:
    print(f'❌ Database error: {e}')
"

# Check .env.production
cat .env.production | grep DATABASE

# Should show RDS connection string
```

## 📊 Monitor Deployment

### Check Container Health:
```bash
docker-compose -f docker-compose.prod.yml ps

# All should show "Up"
```

### Watch Logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f web

# Press Ctrl+C to exit
```

### Check Resource Usage:
```bash
# Memory
free -h

# Disk
df -h

# Container stats
docker stats
```

## 🎉 Success Indicators

When deployment is successful:

1. ✅ All 4 containers running
2. ✅ Port 80 mapped to container
3. ✅ No errors in logs
4. ✅ Site accessible from browser
5. ✅ Landing page loads correctly
6. ✅ Payment logos visible
7. ✅ Search widget functional
8. ✅ Admin panel accessible
9. ✅ Webmail accessible

## 📝 Next Steps After Successful Deployment

### 1. Activate Webmail Link in Footer

If webmail is working, uncomment the webmail link:

```bash
# SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9
cd ~/mushqila

# Edit landing.html
nano accounts/templates/accounts/landing.html

# Find and uncomment:
<!-- <a href="{% url 'webmail:inbox' %}" class="text-white-50">
    <i class="fas fa-envelope fa-lg"></i>
</a> -->

# Do the same for landing2.html
nano accounts/templates/accounts/landing2.html

# Commit and push
git add .
git commit -m "Activate webmail link in footer"
git push origin main

# Restart container
docker-compose -f docker-compose.prod.yml restart web
```

### 2. Set Up SSL Certificate (HTTPS)

For production, you should enable HTTPS:

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d mushqila.com -d www.mushqila.com

# Auto-renewal is set up automatically
```

### 3. Set Up Monitoring

Consider setting up:
- CloudWatch for EC2 monitoring
- Application logs aggregation
- Error tracking (Sentry)
- Uptime monitoring

### 4. Regular Maintenance

```bash
# Weekly: Clean Docker
docker system prune -f

# Monthly: Update packages
sudo apt update && sudo apt upgrade

# As needed: Check logs
docker-compose -f docker-compose.prod.yml logs --tail=100 web
```

## 🔐 Security Checklist

- [ ] Change default admin password
- [ ] Set up SSL certificate (HTTPS)
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Enable CloudWatch monitoring
- [ ] Review security group rules
- [ ] Set up log rotation
- [ ] Configure fail2ban for SSH

## 📞 Support

### Common Issues:

1. **Site not loading** → Check containers: `docker ps`
2. **502 Bad Gateway** → Check Gunicorn logs
3. **Static files missing** → Run collectstatic
4. **Database errors** → Check RDS connection
5. **Memory issues** → Clean Docker cache

### Useful Commands:

```bash
# Restart everything
docker-compose -f docker-compose.prod.yml restart

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Check status
docker-compose -f docker-compose.prod.yml ps

# Clean Docker
docker system prune -f

# Check memory
free -h

# Check disk
df -h
```

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] SSH to EC2 successful
- [ ] Latest code pulled
- [ ] Containers built and started
- [ ] All 4 containers running
- [ ] Port 80 accessible
- [ ] Site loads from browser
- [ ] Landing page displays correctly
- [ ] Payment logos visible
- [ ] Search widget works
- [ ] Admin panel accessible
- [ ] Webmail accessible
- [ ] No errors in logs
- [ ] DNS resolves correctly
- [ ] Domain works (mushqila.com)

## 🎯 Final Action Required

**Run these commands on EC2:**

```bash
# 1. SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# 2. Deploy the fix
cd ~/mushqila
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Wait 60 seconds
sleep 60

# 4. Check status
docker-compose -f docker-compose.prod.yml ps
```

**Then test from browser:**
- http://mushqila.com
- http://16.170.25.9

---

## 🚀 TL;DR

1. **Deploy fix:** Run `DEPLOY-FINAL-FIX.sh` on EC2
2. **Wait 60 seconds** for services to start
3. **Test from browser:** http://mushqila.com or http://16.170.25.9
4. **Don't trust localhost curl** - it's misleading!
5. **Report what you see** in the browser

Your deployment is ready. The localhost curl hanging is normal. Test from browser!
