# 🚀 Complete Deployment Guide

## Quick Start

### Windows (PowerShell)
```powershell
.\deploy.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

---

## What Happens During Deployment

### Automatic Process (GitHub Actions)

```
┌─────────────────────────────────────────┐
│  1. Code Push Detected                  │
│     ↓                                   │
│  2. GitHub Actions Triggered            │
│     ↓                                   │
│  3. Create Backup                       │
│     • Timestamp: YYYYMMDD_HHMMSS        │
│     • Location: ~/mushqila_backup_*     │
│     ↓                                   │
│  4. Pull Latest Code                    │
│     • git fetch origin main             │
│     • git reset --hard origin/main      │
│     ↓                                   │
│  5. Clean Cache                         │
│     • Remove __pycache__                │
│     • Remove *.pyc files                │
│     ↓                                   │
│  6. Validate Syntax                     │
│     • Check Python syntax               │
│     • Fail fast if errors               │
│     ↓                                   │
│  7. Build Docker Images                 │
│     • docker-compose build --no-cache   │
│     ↓                                   │
│  8. Zero-Downtime Deploy                │
│     • Start new containers              │
│     • Wait for health check             │
│     • Switch traffic                    │
│     ↓                                   │
│  9. Run Migrations                      │
│     • python manage.py migrate          │
│     ↓                                   │
│ 10. Collect Static Files               │
│     • python manage.py collectstatic    │
│     ↓                                   │
│ 11. Ensure Admin User                   │
│     • Create if not exists              │
│     ↓                                   │
│ 12. Health Check                        │
│     • Test site response                │
│     • Verify 200/302 status             │
│     ↓                                   │
│ 13. Cleanup                             │
│     • Remove old containers             │
│     • Keep last 3 backups               │
│     ↓                                   │
│ 14. ✅ Deployment Complete!             │
└─────────────────────────────────────────┘
```

---

## Prerequisites

### 1. GitHub Secrets

Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions

Required secrets:
- `EC2_HOST`: 16.170.25.9
- `EC2_USER`: ubuntu
- `EC2_SSH_KEY`: Your SSH private key

### 2. EC2 Server Setup

```bash
# SSH to server
ssh -i your-key.pem ubuntu@16.170.25.9

# Verify Docker is installed
docker --version
docker-compose --version

# Verify project exists
ls -la ~/mushqila

# Verify .env.production exists
cat ~/mushqila/.env.production
```

### 3. Initial Manual Deployment (First Time Only)

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# Clone repository (if not exists)
cd ~
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila

# Create .env.production
cp .env.production.template .env.production
nano .env.production  # Edit with your values

# Initial deployment
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## Deployment Methods

### Method 1: Quick Deploy Script (Recommended)

**Windows:**
```powershell
.\deploy.ps1
```

**Linux/Mac:**
```bash
./deploy.sh
```

**Features:**
- Interactive commit message
- Automatic git operations
- Progress indicators
- Opens GitHub Actions in browser

### Method 2: Git Commands

```bash
# Add all changes
git add .

# Commit with message
git commit -m "Fix: Resolved 500 errors"

# Push to trigger deployment
git push origin main
```

### Method 3: GitHub Web Interface

1. Make changes in GitHub web editor
2. Commit directly to main branch
3. Deployment triggers automatically

### Method 4: Manual Trigger

1. Go to: https://github.com/mushqiladac/mushqila/actions
2. Select "Deploy to EC2 with Zero Downtime"
3. Click "Run workflow"
4. Select branch: main
5. Click "Run workflow"

---

## Monitoring Deployment

### GitHub Actions Dashboard

1. Go to: https://github.com/mushqiladac/mushqila/actions
2. Click on the running workflow
3. Click on "deploy" job
4. Watch real-time logs

### Server Logs

```bash
# SSH to server
ssh -i your-key.pem ubuntu@16.170.25.9

# Watch deployment logs
cd ~/mushqila
docker-compose -f docker-compose.prod.yml logs -f web

# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check specific service
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs redis
docker-compose -f docker-compose.prod.yml logs celery
```

### Application Logs

```bash
# Django logs
docker-compose -f docker-compose.prod.yml exec web tail -f /var/log/django.log

# Nginx logs
sudo tail -f /var/log/nginx/mushqila_access.log
sudo tail -f /var/log/nginx/mushqila_error.log

# System logs
sudo journalctl -u docker -f
```

---

## Verification Checklist

After deployment, verify:

### 1. Site Accessibility
- [ ] https://mushqila.com loads
- [ ] No 500 errors
- [ ] No 502 Bad Gateway
- [ ] SSL certificate valid

### 2. Core Functionality
- [ ] Login page works: https://mushqila.com/accounts/login/
- [ ] Admin panel accessible: https://mushqila.com/admin/
- [ ] Webmail works: https://mushqila.com/webmail/
- [ ] Landing page loads: https://mushqila.com/accounts/landing/

### 3. Static Files
- [ ] CSS loads properly
- [ ] Images display
- [ ] JavaScript works
- [ ] Favicon shows

### 4. Database
- [ ] Migrations applied
- [ ] Data intact
- [ ] No migration errors

### 5. Services
- [ ] Web container running
- [ ] Redis container running
- [ ] Celery worker running
- [ ] Celery beat running

### Quick Verification Commands

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Test site response
curl -I https://mushqila.com

# Check for errors
docker-compose -f docker-compose.prod.yml logs web | grep -i error

# Verify database
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations
```

---

## Rollback Procedures

### Automatic Rollback

If deployment fails, GitHub Actions automatically:
1. Stops new containers
2. Restores from backup
3. Starts old containers
4. Reports failure

### Manual Rollback

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# List available backups
ls -lht ~/mushqila_backup_*

# Example output:
# mushqila_backup_20260407_143022
# mushqila_backup_20260407_120015
# mushqila_backup_20260406_183045

# Stop current deployment
cd ~/mushqila
docker-compose -f docker-compose.prod.yml down

# Restore specific backup
cd ~
sudo rm -rf mushqila
sudo mv mushqila_backup_20260407_120015 mushqila

# Start restored version
cd mushqila
docker-compose -f docker-compose.prod.yml up -d

# Verify
docker-compose -f docker-compose.prod.yml ps
curl -I https://mushqila.com
```

### Rollback to Specific Commit

```bash
# SSH to EC2
cd ~/mushqila

# View commit history
git log --oneline -10

# Rollback to specific commit
git reset --hard COMMIT_HASH

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## Troubleshooting

### Issue 1: Deployment Stuck

**Symptoms:** Workflow running for >10 minutes

**Solution:**
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9
cd ~/mushqila

# Check what's happening
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs --tail=100

# Force restart if needed
docker-compose -f docker-compose.prod.yml restart
```

### Issue 2: 500 Internal Server Error

**Symptoms:** Site returns 500 error

**Solution:**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web | tail -100

# Common causes:
# 1. Syntax error in Python code
# 2. Missing environment variable
# 3. Database migration needed
# 4. Missing static files

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Restart
docker-compose -f docker-compose.prod.yml restart web
```

### Issue 3: 502 Bad Gateway

**Symptoms:** Nginx returns 502

**Solution:**
```bash
# Check if web container is running
docker-compose -f docker-compose.prod.yml ps web

# Check web container logs
docker-compose -f docker-compose.prod.yml logs web

# Restart web container
docker-compose -f docker-compose.prod.yml restart web

# Check Nginx
sudo systemctl status nginx
sudo systemctl restart nginx
```

### Issue 4: Static Files Not Loading

**Symptoms:** CSS/JS/Images not loading

**Solution:**
```bash
# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --clear

# Check static files location
docker-compose -f docker-compose.prod.yml exec web ls -la /app/staticfiles/

# Verify Nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

### Issue 5: Database Connection Error

**Symptoms:** Can't connect to database

**Solution:**
```bash
# Check database container
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Restart database
docker-compose -f docker-compose.prod.yml restart db

# Wait and restart web
sleep 5
docker-compose -f docker-compose.prod.yml restart web
```

---

## Performance Optimization

### 1. Enable Redis Caching

Already configured in production settings.

### 2. Optimize Static Files

```bash
# Compress static files
docker-compose -f docker-compose.prod.yml exec web python manage.py compress

# Enable Nginx gzip (already configured)
```

### 3. Database Optimization

```bash
# Run database optimization
docker-compose -f docker-compose.prod.yml exec web python manage.py optimize_db

# Analyze slow queries
docker-compose -f docker-compose.prod.yml exec web python manage.py show_slow_queries
```

---

## Security Best Practices

### 1. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Backup Strategy

- Automatic backups before each deployment
- Keep last 3 backups
- Manual backups before major changes

```bash
# Manual backup
cd ~
sudo cp -r mushqila mushqila_backup_manual_$(date +%Y%m%d_%H%M%S)
```

### 3. Monitor Logs

```bash
# Set up log rotation
sudo nano /etc/logrotate.d/mushqila

# Add:
/var/log/nginx/mushqila_*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx
    endscript
}
```

---

## Deployment Metrics

### Typical Deployment Times

- **Code Push to GitHub**: Instant
- **GitHub Actions Start**: 5-10 seconds
- **Backup Creation**: 10-15 seconds
- **Code Pull**: 5-10 seconds
- **Docker Build**: 60-90 seconds
- **Container Start**: 10-15 seconds
- **Migrations**: 5-10 seconds
- **Static Collection**: 10-15 seconds
- **Health Check**: 5 seconds
- **Total**: 2-4 minutes

### Zero Downtime Verification

During deployment:
```bash
# Run this in a loop to verify no downtime
while true; do
    curl -s -o /dev/null -w "%{http_code}\n" https://mushqila.com
    sleep 1
done

# Should always return 200 or 302, never connection errors
```

---

## Advanced Features

### 1. Deploy to Staging First

Create `.github/workflows/deploy-staging.yml`:
```yaml
on:
  push:
    branches:
      - develop
```

### 2. Scheduled Deployments

Add to workflow:
```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
```

### 3. Slack Notifications

Add to workflow:
```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Summary

✅ **Deployment is fully automated**
✅ **Zero downtime guaranteed**
✅ **Automatic backups**
✅ **Smart rollback on failure**
✅ **Health checks**
✅ **Syntax validation**

**To deploy, simply:**
```bash
git push origin main
```

**Monitor at:**
https://github.com/mushqiladac/mushqila/actions

**Site live at:**
https://mushqila.com

---

## Support

Need help? Check:
1. GitHub Actions logs
2. Server logs: `docker-compose logs`
3. This troubleshooting guide
4. Backup directories: `~/mushqila_backup_*`

**Your deployment pipeline is production-ready!** 🚀
