# GitHub CI/CD Automatic Deployment Setup

## 🎯 Overview

এই guide follow করলে:
- ✅ GitHub এ code push করলে automatic EC2 তে deploy হবে
- ✅ Manual deployment এর দরকার নেই
- ✅ সব কিছু automatic হবে

---

## 📋 Prerequisites

- ✅ GitHub repository: https://github.com/mushqiladac/mushqila
- ✅ EC2 instance running: 16.170.104.186
- ✅ EC2 SSH key (.pem file)
- ⏳ EC2 initial setup (one-time)

---

## Part 1: GitHub Secrets Setup

### Step 1: Open GitHub Secrets Page

যান: https://github.com/mushqiladac/mushqila/settings/secrets/actions

### Step 2: Add EC2_SSH_KEY Secret

1. "New repository secret" button ক্লিক করুন
2. **Name:** `EC2_SSH_KEY`
3. **Value:** আপনার EC2 SSH private key এর সম্পূর্ণ content

#### SSH Key কিভাবে copy করবেন:

**Windows:**
```powershell
# PowerShell এ
Get-Content your-key.pem | clip

# অথবা Notepad দিয়ে open করে copy করুন
notepad your-key.pem
```

**Linux/Mac:**
```bash
cat your-key.pem
# Output copy করুন
```

#### Key Format Example:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
... (many lines)
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
-----END RSA PRIVATE KEY-----
```

4. "Add secret" ক্লিক করুন

### Step 3: Verify Secret Added

Secrets page এ `EC2_SSH_KEY` দেখতে পাবেন (value hidden থাকবে)

---

## Part 2: EC2 Initial Setup (One-time)

### Step 1: SSH to EC2

```bash
ssh -i your-key.pem ubuntu@16.170.104.186
```

### Step 2: Run Setup Commands

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version

# Logout and login again for docker group
exit
```

### Step 3: Login Again and Clone Repository

```bash
# SSH again
ssh -i your-key.pem ubuntu@16.170.104.186

# Clone repository
cd /home/ubuntu
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila
```

### Step 4: Create .env.production File

```bash
nano .env.production
```

Paste this content (update the values):

```env
# Django Settings
DEBUG=False
SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE
ALLOWED_HOSTS=16.170.104.186,mushqila.com,www.mushqila.com

# Database (AWS RDS)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mushqila
DB_USER=postgres
DB_PASSWORD=YOUR_RDS_PASSWORD
DB_HOST=database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com
DB_PORT=5432

# Email (AWS SES)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.eu-north-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=AKIAUQETDVDPECKLURNW
EMAIL_HOST_PASSWORD=YOUR_SES_PASSWORD
DEFAULT_FROM_EMAIL=noreply@mushqila.com

# Galileo GDS (when available)
TRAVELPORT_USERNAME=
TRAVELPORT_PASSWORD=
TRAVELPORT_BRANCH_CODE=P702214

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 5: Generate SECRET_KEY

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy output এবং .env.production এ SECRET_KEY update করুন:

```bash
nano .env.production
# Update SECRET_KEY line
```

### Step 6: Initial Deployment

```bash
# Build and start containers
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Initialize chart of accounts
docker-compose -f docker-compose.prod.yml exec web python manage.py initialize_accounts

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Step 7: Test Application

```bash
# Test from EC2
curl http://localhost:8000

# Check logs
docker-compose -f docker-compose.prod.yml logs -f web
```

Browser এ test করুন: http://16.170.104.186

---

## Part 3: Test CI/CD Workflow

### Step 1: Make a Small Change

Local machine এ:

```bash
# Create a test file
echo "# CI/CD Test" > TEST.md

# Commit and push
git add TEST.md
git commit -m "Test CI/CD deployment"
git push origin main
```

### Step 2: Monitor GitHub Actions

1. যান: https://github.com/mushqiladac/mushqila/actions
2. Latest workflow run দেখুন
3. "Deploy to AWS EC2" workflow ক্লিক করুন
4. Real-time logs দেখুন

### Step 3: Verify Deployment

Workflow complete হলে:

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.104.186

# Check if changes deployed
cd /home/ubuntu/mushqila
git log -1

# Check containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs --tail=50 web
```

Browser এ verify করুন: http://16.170.104.186

---

## 🎉 Success! CI/CD is Working!

এখন থেকে:
- ✅ GitHub এ code push করলে automatic deploy হবে
- ✅ 5-10 minutes এ deployment complete হবে
- ✅ Manual deployment এর দরকার নেই

---

## 📊 Workflow Details

### What Happens When You Push:

1. **GitHub Actions Triggered**
   - Code push detect করে
   - Workflow শুরু হয়

2. **Checkout Code**
   - Latest code checkout করে

3. **SSH to EC2**
   - EC2_SSH_KEY দিয়ে connect করে

4. **Deploy Steps:**
   ```bash
   cd /home/ubuntu/mushqila
   git pull origin main
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml build
   docker-compose -f docker-compose.prod.yml up -d
   docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate
   docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
   ```

5. **Deployment Complete**
   - Application restarted
   - New code live!

---

## 🔍 Troubleshooting

### Workflow Fails with "Permission denied"

**Problem:** EC2_SSH_KEY not configured or incorrect

**Solution:**
1. Verify secret exists: https://github.com/mushqiladac/mushqila/settings/secrets/actions
2. Check key format (must include BEGIN/END lines)
3. Re-add secret if needed

### Workflow Fails with "No such file or directory"

**Problem:** Repository not cloned on EC2

**Solution:**
```bash
ssh -i your-key.pem ubuntu@16.170.104.186
cd /home/ubuntu
git clone https://github.com/mushqiladac/mushqila.git
```

### Workflow Fails with "docker: command not found"

**Problem:** Docker not installed on EC2

**Solution:**
```bash
ssh -i your-key.pem ubuntu@16.170.104.186
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

### Application Not Responding After Deployment

**Problem:** Containers not running or error in code

**Solution:**
```bash
ssh -i your-key.pem ubuntu@16.170.104.186
cd /home/ubuntu/mushqila

# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Restart if needed
docker-compose -f docker-compose.prod.yml restart
```

---

## 📝 Useful Commands

### Monitor Deployment

```bash
# Watch GitHub Actions
https://github.com/mushqiladac/mushqila/actions

# SSH and check logs
ssh -i your-key.pem ubuntu@16.170.104.186
cd /home/ubuntu/mushqila
docker-compose -f docker-compose.prod.yml logs -f web
```

### Manual Deployment (if needed)

```bash
ssh -i your-key.pem ubuntu@16.170.104.186
cd /home/ubuntu/mushqila
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Rollback to Previous Version

```bash
ssh -i your-key.pem ubuntu@16.170.104.186
cd /home/ubuntu/mushqila
git log --oneline  # See commit history
git checkout <previous-commit-hash>
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

---

## ✅ Checklist

### Initial Setup:
- [ ] EC2_SSH_KEY added to GitHub Secrets
- [ ] EC2 instance running
- [ ] Docker installed on EC2
- [ ] Docker Compose installed on EC2
- [ ] Repository cloned on EC2
- [ ] .env.production created and configured
- [ ] Initial deployment successful
- [ ] Application accessible

### CI/CD Working:
- [ ] Test commit pushed
- [ ] GitHub Actions workflow triggered
- [ ] Workflow completed successfully
- [ ] Changes deployed to EC2
- [ ] Application working with new changes

---

## 🎯 Next Steps

1. **Test CI/CD:** Make a small change and push
2. **Monitor:** Watch GitHub Actions
3. **Verify:** Check application on EC2
4. **Celebrate:** CI/CD is working! 🎉

---

**Your CI/CD pipeline is ready! Happy deploying! 🚀**
