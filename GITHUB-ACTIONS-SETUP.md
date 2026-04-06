# 🚀 GitHub Actions Zero-Downtime Deployment Setup

## Overview
এই setup automatic deployment করবে যখনই তুমি `main` branch এ code push করবে। Zero-downtime এবং automatic rollback সহ।

---

## ✨ Features

1. **Zero Downtime** - Site কখনো down হবে না
2. **Automatic Backup** - প্রতিবার deploy এর আগে backup নেয়
3. **Smart Rollback** - Failed হলে automatically previous version restore করে
4. **Clean Deployment** - পুরনো cache files delete করে fresh deployment
5. **Health Check** - Deploy এর পর site check করে
6. **Keep Last 3 Backups** - Disk space save করার জন্য

---

## 📋 Setup Steps

### Step 1: GitHub Repository Settings

1. তোমার GitHub repository তে যাও: https://github.com/mushqiladac/mushqila
2. **Settings** tab click করো
3. Left sidebar → **Secrets and variables** → **Actions**
4. **New repository secret** click করো

### Step 2: Add Secrets

তিনটা secrets add করতে হবে:

#### Secret 1: EC2_HOST
```
Name: EC2_HOST
Value: 16.170.25.9
```
Click **Add secret**

#### Secret 2: EC2_USER
```
Name: EC2_USER
Value: ubuntu
```
Click **Add secret**

#### Secret 3: EC2_SSH_KEY
```
Name: EC2_SSH_KEY
Value: [তোমার SSH private key এর content]
```

**SSH Key কিভাবে copy করবে:**

Windows PowerShell:
```powershell
Get-Content your-key.pem | clip
```

অথবা manually:
1. তোমার `.pem` file open করো Notepad দিয়ে
2. সব content copy করো (-----BEGIN RSA PRIVATE KEY----- থেকে -----END RSA PRIVATE KEY----- পর্যন্ত)
3. GitHub এ paste করো

Click **Add secret**

---

## 🎯 How It Works

### Deployment Flow

```
1. Code Push to GitHub (main branch)
        ↓
2. GitHub Actions Triggered
        ↓
3. Create Backup of Current Deployment
        ↓
4. Pull Latest Code from GitHub
        ↓
5. Clean Old Cache Files
        ↓
6. Build New Docker Images
        ↓
7. Start New Containers (Zero Downtime)
        ↓
8. Run Database Migrations
        ↓
9. Collect Static Files
        ↓
10. Health Check
        ↓
11. Remove Old Containers
        ↓
12. Keep Last 3 Backups
        ↓
13. ✅ Deployment Complete!
```

### If Deployment Fails:
```
❌ Error Detected
        ↓
Stop New Containers
        ↓
Restore from Backup
        ↓
Start Old Containers
        ↓
✅ Rollback Complete
```

---

## 🧪 Testing the Setup

### Test 1: Manual Trigger

1. GitHub repository → **Actions** tab
2. Left sidebar → **Deploy to EC2 with Zero Downtime**
3. **Run workflow** button → **Run workflow**
4. Watch the deployment process

### Test 2: Automatic Trigger

1. Make a small change in any file:
```bash
# Local machine
echo "# Test deployment" >> README.md
git add README.md
git commit -m "Test: GitHub Actions deployment"
git push origin main
```

2. GitHub → **Actions** tab
3. Watch the deployment automatically start

---

## 📊 Monitoring Deployment

### View Logs

1. GitHub → **Actions** tab
2. Click on the running/completed workflow
3. Click on **deploy** job
4. Expand each step to see detailed logs

### Check Deployment Status

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# Check containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f web

# Check backups
ls -lh ~/mushqila_backup_*
```

---

## 🔧 Configuration

### Workflow File Location
```
.github/workflows/deploy.yml
```

### Customize Deployment

#### Change Backup Retention (default: 3)
Edit `.github/workflows/deploy.yml`:
```yaml
# Line: Keep last 3 backups
ls -dt mushqila_backup_* | tail -n +4 | xargs -r sudo rm -rf
# Change +4 to +6 for keeping 5 backups
```

#### Add Slack/Email Notifications
Add at the end of workflow:
```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 🛡️ Security Best Practices

### 1. Protect Main Branch
1. GitHub → **Settings** → **Branches**
2. **Add branch protection rule**
3. Branch name: `main`
4. Enable:
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date

### 2. Rotate SSH Keys Regularly
```bash
# Generate new key pair
ssh-keygen -t rsa -b 4096 -f mushqila-deploy-key

# Add public key to EC2
ssh-copy-id -i mushqila-deploy-key.pub ubuntu@16.170.25.9

# Update GitHub secret with new private key
```

### 3. Use Deploy Keys (Recommended)
Instead of personal SSH key, use deploy keys:
1. GitHub → **Settings** → **Deploy keys**
2. **Add deploy key**
3. Paste public key
4. ✅ Allow write access

---

## 📝 Deployment Checklist

Before first deployment:
- [ ] GitHub secrets configured (EC2_HOST, EC2_USER, EC2_SSH_KEY)
- [ ] SSH key has correct permissions on EC2
- [ ] Docker and docker-compose installed on EC2
- [ ] .env.production file exists on EC2
- [ ] Initial deployment done manually

After setup:
- [ ] Test manual workflow trigger
- [ ] Test automatic deployment (push to main)
- [ ] Verify zero downtime (site stays up)
- [ ] Check backup creation
- [ ] Test rollback (intentionally break something)

---

## 🚨 Troubleshooting

### Issue 1: SSH Connection Failed
**Error:** `Permission denied (publickey)`

**Solution:**
```bash
# Check SSH key format
cat your-key.pem
# Should start with: -----BEGIN RSA PRIVATE KEY-----

# Verify key on EC2
ssh -i your-key.pem ubuntu@16.170.25.9 "echo 'SSH works!'"
```

### Issue 2: Docker Command Not Found
**Error:** `docker: command not found`

**Solution:**
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Issue 3: Deployment Stuck
**Error:** Workflow running for too long

**Solution:**
```bash
# SSH to EC2 and check
ssh -i your-key.pem ubuntu@16.170.25.9
cd ~/mushqila

# Check what's running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs --tail=50

# If needed, restart manually
docker-compose -f docker-compose.prod.yml restart
```

### Issue 4: Health Check Failed
**Error:** `Health check failed! HTTP status: 502`

**Solution:**
```bash
# Check Nginx
sudo systemctl status nginx

# Check Docker containers
docker-compose -f docker-compose.prod.yml ps

# Check application logs
docker-compose -f docker-compose.prod.yml logs web

# Restart if needed
docker-compose -f docker-compose.prod.yml restart web
sudo systemctl restart nginx
```

---

## 📈 Advanced Features

### 1. Deploy to Staging First
Create `.github/workflows/deploy-staging.yml`:
```yaml
on:
  push:
    branches:
      - develop
```

### 2. Manual Approval for Production
Add to workflow:
```yaml
- name: Wait for approval
  uses: trstringer/manual-approval@v1
  with:
    approvers: mushqiladac
```

### 3. Database Backup Before Deploy
Add before migrations:
```yaml
- name: Backup Database
  run: |
    docker-compose -f docker-compose.prod.yml exec -T web \
      python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

### 4. Run Tests Before Deploy
Add before deployment:
```yaml
- name: Run Tests
  run: |
    docker-compose -f docker-compose.prod.yml exec -T web \
      python manage.py test
```

---

## 🎯 Deployment Scenarios

### Scenario 1: Normal Update
```bash
# Make changes
git add .
git commit -m "Update: Added new feature"
git push origin main

# GitHub Actions automatically deploys
# Zero downtime ✅
```

### Scenario 2: Emergency Rollback
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# List backups
ls -lh ~/mushqila_backup_*

# Restore specific backup
cd ~
sudo rm -rf mushqila
sudo mv mushqila_backup_20260312_143022 mushqila
cd mushqila
docker-compose -f docker-compose.prod.yml up -d
```

### Scenario 3: Hotfix
```bash
# Create hotfix branch
git checkout -b hotfix/critical-bug
# Fix the bug
git add .
git commit -m "Hotfix: Critical bug fix"
git push origin hotfix/critical-bug

# Merge to main
git checkout main
git merge hotfix/critical-bug
git push origin main

# Auto-deploys via GitHub Actions
```

---

## 📊 Monitoring & Logs

### View Deployment History
```bash
# On EC2
ls -lht ~/mushqila_backup_* | head -10
```

### Check Deployment Logs
```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs -f web

# Nginx logs
sudo tail -f /var/log/nginx/mushqila_access.log
sudo tail -f /var/log/nginx/mushqila_error.log

# System logs
sudo journalctl -u docker -f
```

---

## ✅ Success Indicators

After successful deployment, you should see:

1. **GitHub Actions**: Green checkmark ✅
2. **Site**: https://mushqila.com loads normally
3. **Webmail**: https://mushqila.com/webmail/ works
4. **No Downtime**: Site was accessible during entire deployment
5. **Backup Created**: New backup in `/home/ubuntu/mushqila_backup_*`
6. **Containers Running**: All 4 containers (web, redis, celery, celery-beat) running

---

## 🎉 Summary

✅ **What You Get:**
- Automatic deployment on every push to main
- Zero downtime deployments
- Automatic backups before each deployment
- Smart rollback on failure
- Clean deployments (no old cache)
- Health checks
- Backup retention (keeps last 3)

✅ **Deployment Time:** ~2-3 minutes

✅ **Manual Intervention:** None required

✅ **Rollback Time:** ~30 seconds (if needed)

---

## 📞 Support

**Need Help?**
- Check GitHub Actions logs
- SSH to EC2 and check Docker logs
- Review troubleshooting section
- Check backup directories

**Your CI/CD pipeline is ready!** 🚀

Every push to `main` branch will automatically deploy to production with zero downtime!
