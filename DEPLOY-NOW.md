# Deploy Webmail to EC2 - Quick Guide

## ✅ Everything is Ready!

- ✅ All webmail templates created
- ✅ Database migrations completed on RDS
- ✅ Code pushed to GitHub
- ✅ URLs configured

## 🚀 Deploy to EC2 (3 Simple Steps)

### Step 1: SSH to EC2
```bash
ssh -i your-key.pem ubuntu@16.170.25.9
```

### Step 2: Pull Latest Code
```bash
cd mushqila
git pull origin main
```

### Step 3: Restart Web Container
```bash
docker-compose -f docker-compose.prod.yml restart web
```

That's it! Webmail is now live!

## 🌐 Access Webmail

- **Main URL**: http://16.170.25.9/webmail/
- **Alternative**: http://16.170.25.9:8000/webmail/

## 📝 What Changed

The only change needed was adding this line to `config/urls.py`:
```python
path('webmail/', include('webmail.urls', namespace='webmail')),
```

This is already in the code you just pulled from GitHub.

## ✅ Verification

After restarting, check if it's working:
```bash
# On EC2
curl http://localhost:8000/webmail/
```

You should see HTML output (not a 404 error).

## 🎉 Done!

Your webmail system is now live with:
- Inbox management
- Email composer with rich text editor
- Contact management
- Search functionality
- AWS SES & S3 integration ready

---

**Note**: The database already has all webmail tables from the migrations we ran earlier, so no migration needed!
