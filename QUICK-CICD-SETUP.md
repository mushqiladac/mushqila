# Quick CI/CD Setup Guide

## ✅ What's Done:
1. ✅ GitHub Actions workflow created (`.github/workflows/deploy.yml`)
2. ✅ Code pushed to `dwd` branch
3. ✅ SSH key file saved locally (`mhcl-key.pem`)

## 🔧 What You Need to Do:

### Step 1: Add GitHub Secrets

Go to: **https://github.com/mushqiladac/sinan/settings/secrets/actions**

Add these 3 secrets:

#### 1. EC2_HOST
```
Name: EC2_HOST
Value: 13.60.112.227
```

#### 2. EC2_USERNAME
```
Name: EC2_USERNAME
Value: ubuntu
```

#### 3. EC2_SSH_KEY
```
Name: EC2_SSH_KEY
Value: [Copy entire content from mhcl-key.pem file]
```

**To copy mhcl-key.pem content:**
```bash
# Open file in Notepad
notepad mhcl-key.pem

# Or use PowerShell
Get-Content mhcl-key.pem | clip
```

Then paste in GitHub secret field.

---

### Step 2: Test Deployment

After adding secrets:

1. Go to: **https://github.com/mushqiladac/sinan/actions**
2. Click on **"Deploy to EC2"** workflow
3. Click **"Run workflow"** button
4. Select branch: `dwd`
5. Click **"Run workflow"**

Watch the deployment in real-time!

---

### Step 3: Automatic Deployment

From now on, whenever you push to `dwd` branch:

```bash
git add .
git commit -m "Your changes"
git push origin dwd
```

GitHub Actions will automatically:
- ✅ Connect to EC2 server
- ✅ Pull latest code
- ✅ Rebuild Docker containers
- ✅ Run migrations
- ✅ Collect static files
- ✅ Restart application

---

## 🎯 Current Setup:

- **Repository**: https://github.com/mushqiladac/sinan
- **Branch**: dwd
- **EC2 IP**: 13.60.112.227
- **Application URL**: http://13.60.112.227:8000
- **RDS Database**: mushqila (postgres/Sinan129380)

---

## 📝 Quick Commands:

### Local Development:
```bash
# Run with SQLite
python manage.py migrate
python manage.py runserver
```

### Push to GitHub:
```bash
git add .
git commit -m "Your message"
git push origin dwd
```

### Manual EC2 Deployment:
```bash
ssh -i mhcl-key.pem ubuntu@13.60.112.227
cd ~/mushqila
git pull origin dwd
docker-compose -f docker-compose.prod.yml up -d --build
```

### Check EC2 Logs:
```bash
ssh -i mhcl-key.pem ubuntu@13.60.112.227
cd ~/mushqila
docker-compose -f docker-compose.prod.yml logs -f web
```

---

## 🚀 Next Steps:

1. ✅ Add GitHub Secrets (3 secrets)
2. ✅ Test workflow manually
3. ✅ Make a small change and push to test automatic deployment
4. ✅ Setup Nginx for port 80 access (optional)
5. ✅ Configure domain name (optional)

---

## 📞 Support:

If deployment fails:
1. Check GitHub Actions logs
2. SSH to EC2 and check Docker logs
3. Verify secrets are correctly added
4. Check EC2 Security Group allows SSH (port 22)

