# Deploy Webmail to EC2 Server

## 🚀 Quick Deployment Steps

Your webmail code is on GitHub but not yet deployed to EC2 server (16.170.25.9).

### Step 1: SSH to EC2 Server

```bash
ssh -i your-key.pem ubuntu@16.170.25.9
```

### Step 2: Navigate to Project Directory

```bash
cd mushqila
```

### Step 3: Pull Latest Code from GitHub

```bash
git pull origin main
```

### Step 4: Restart Docker Containers

```bash
# Stop containers
docker-compose -f docker-compose.prod.yml down

# Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build
```

### Step 5: Run Migrations (Important!)

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Step 6: Collect Static Files

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Step 7: Verify Deployment

Visit: `http://16.170.25.9:8000/webmail/`

---

## 🔍 Troubleshooting

### If webmail still not found:

1. **Check if webmail app is installed:**
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
```
Then in shell:
```python
from django.conf import settings
print('webmail' in settings.INSTALLED_APPS)
# Should print: True
```

2. **Check URL configuration:**
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py show_urls | grep webmail
```

3. **Check logs:**
```bash
docker-compose -f docker-compose.prod.yml logs web
```

4. **Restart services:**
```bash
docker-compose -f docker-compose.prod.yml restart
```

---

## 📋 Complete Deployment Commands (Copy-Paste)

```bash
# SSH to server
ssh -i your-key.pem ubuntu@16.170.25.9

# Navigate to project
cd mushqila

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web
```

---

## ✅ After Deployment

### Access Webmail:
- Main URL: `http://16.170.25.9:8000/webmail/`
- Inbox: `http://16.170.25.9:8000/webmail/inbox/`
- Compose: `http://16.170.25.9:8000/webmail/compose/`
- Settings: `http://16.170.25.9:8000/webmail/account-setup/`

### First Time Setup:
1. Login to your account
2. Go to webmail settings
3. Configure AWS SES credentials
4. Configure S3 bucket
5. Start using webmail!

---

## 🔐 AWS Configuration Needed

Before using webmail, you need:

1. **AWS SES** (for sending emails)
   - Verify your email address
   - Get SMTP credentials or API keys

2. **AWS S3** (for storing emails)
   - Create a bucket
   - Set appropriate permissions

3. **Update .env.production** on EC2:
```bash
# AWS SES Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_SES_REGION=us-east-1

# AWS S3 Configuration
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

---

## 📞 Need Help?

If deployment fails:
1. Check Docker logs: `docker-compose -f docker-compose.prod.yml logs`
2. Check if containers are running: `docker-compose -f docker-compose.prod.yml ps`
3. Verify migrations: `docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations webmail`

---

**Estimated Time:** 5-10 minutes
**Status:** Ready to deploy
