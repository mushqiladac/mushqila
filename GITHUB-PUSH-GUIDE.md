# GitHub Push Guide - Mushqila Project

## ✅ Pre-Push Checklist

সব কিছু ready! GitHub এ push করার আগে এই checklist follow করুন:

### 1. Files Ready ✅
- ✅ Dockerfile
- ✅ docker-compose.yml
- ✅ docker-compose.prod.yml
- ✅ requirements.txt
- ✅ .env.production (template)
- ✅ .github/workflows/deploy.yml
- ✅ entrypoint.sh
- ✅ deploy.sh
- ✅ setup-ec2.sh
- ✅ All documentation files

### 2. Sensitive Data Check ✅
- ✅ .gitignore configured
- ✅ .env files excluded
- ✅ *.pem files excluded
- ✅ db.sqlite3 excluded
- ✅ No passwords in code

### 3. Documentation ✅
- ✅ README.md
- ✅ DEPLOYMENT.md
- ✅ QUICK-START.md
- ✅ GALILEO-SETUP.md
- ✅ GALILEO-QUICK-REFERENCE.md
- ✅ PROJECT-SUMMARY.md
- ✅ TESTING.md

---

## 🚀 Push to GitHub

### Step 1: Initialize Git (if not done)
```bash
git init
git branch -M main
```

### Step 2: Add Remote
```bash
git remote add origin https://github.com/mushqiladac/mushqila.git
```

### Step 3: Stage All Files
```bash
git add .
```

### Step 4: Check Status
```bash
git status
```

Verify করুন যে sensitive files (`.env`, `*.pem`, `db.sqlite3`) staged নেই।

### Step 5: Commit
```bash
git commit -m "Complete AWS deployment setup with Galileo GDS integration

- Added Docker & Docker Compose configuration
- Implemented GitHub Actions CI/CD pipeline
- Created complete Galileo GDS integration
- Added comprehensive documentation
- Configured AWS RDS and SES
- Setup automated deployment scripts
- Added agent management and accounting system
"
```

### Step 6: Push to GitHub
```bash
git push -u origin main
```

অথবা force push (যদি repository already exist করে):
```bash
git push -u origin main --force
```

---

## 🔐 GitHub Secrets Setup

Push করার পর, GitHub repository তে secrets add করুন:

### Navigate to:
```
https://github.com/mushqiladac/mushqila/settings/secrets/actions
```

### Add Secret:
1. Click "New repository secret"
2. Name: `EC2_SSH_KEY`
3. Value: Your EC2 private key content
4. Click "Add secret"

---

## 🧪 Test GitHub Actions

### Trigger Deployment:
```bash
# Make a small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "Test CI/CD pipeline"
git push origin main
```

### Monitor Deployment:
```
https://github.com/mushqiladac/mushqila/actions
```

---

## 📋 Post-Push Checklist

### On GitHub:
- [ ] Repository created successfully
- [ ] All files visible
- [ ] No sensitive data exposed
- [ ] GitHub Actions workflow visible
- [ ] EC2_SSH_KEY secret added

### On AWS EC2:
- [ ] SSH to EC2: `ssh -i your-key.pem ubuntu@16.170.104.186`
- [ ] Clone repository: `git clone https://github.com/mushqiladac/mushqila.git`
- [ ] Run setup: `cd mushqila && chmod +x setup-ec2.sh && ./setup-ec2.sh`
- [ ] Configure .env.production
- [ ] Deploy: `./deploy.sh`

---

## 🔧 Common Issues

### Issue: Permission denied (publickey)
```bash
# Solution: Check SSH key
ssh -T git@github.com

# Or use HTTPS instead
git remote set-url origin https://github.com/mushqiladac/mushqila.git
```

### Issue: Large files rejected
```bash
# Solution: Check file sizes
find . -type f -size +50M

# Remove large files from git
git rm --cached large-file.zip
```

### Issue: Merge conflicts
```bash
# Solution: Pull first
git pull origin main --rebase
git push origin main
```

---

## 📊 Repository Structure on GitHub

```
mushqila/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── accounts/                   # User management app
├── flights/                    # Flight booking app
│   └── services/
│       ├── galileo_client.py   # Galileo API client
│       └── galileo_service.py  # Service layer
├── config/                     # Django settings
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Local development
├── docker-compose.prod.yml     # Production
├── .env.production             # Production env template
├── requirements.txt            # Python dependencies
├── entrypoint.sh              # Container entrypoint
├── deploy.sh                  # Deployment script
├── setup-ec2.sh               # EC2 setup script
├── README.md                  # Main documentation
├── DEPLOYMENT.md              # Deployment guide
├── GALILEO-SETUP.md           # Galileo integration
├── TESTING.md                 # Testing guide
└── PROJECT-SUMMARY.md         # Project overview
```

---

## ✅ Verification

### After Push, Verify:

1. **GitHub Repository**
   ```
   https://github.com/mushqiladac/mushqila
   ```

2. **GitHub Actions**
   ```
   https://github.com/mushqiladac/mushqila/actions
   ```

3. **Files Visible**
   - Check all documentation files are visible
   - Verify .gitignore is working (no .env files)

4. **Clone Test**
   ```bash
   # Test clone in a different directory
   cd /tmp
   git clone https://github.com/mushqiladac/mushqila.git
   cd mushqila
   ls -la
   ```

---

## 🎯 Next Steps After Push

1. ✅ **GitHub**: Repository pushed
2. ⏳ **AWS EC2**: Clone and setup
3. ⏳ **Environment**: Configure .env.production
4. ⏳ **Galileo**: Add API credentials
5. ⏳ **Deploy**: Run deployment script
6. ⏳ **Test**: Verify application

---

## 📞 Support

### GitHub Issues:
```
https://github.com/mushqiladac/mushqila/issues
```

### Documentation:
- DEPLOYMENT.md - AWS deployment
- GALILEO-SETUP.md - Galileo integration
- TESTING.md - Testing guide

---

**Ready to push! 🚀**

Run: `git push -u origin main`
