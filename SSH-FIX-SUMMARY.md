# 🔧 SSH Authentication Error - Quick Fix

## The Problem
```
ssh: unable to authenticate, attempted methods [none publickey], no supported methods remain
```

GitHub Actions can't connect to your EC2 server.

---

## ⚡ Quick Fix (Most Common)

### The Issue
Your SSH key in GitHub Secrets is probably not formatted correctly.

### The Solution

1. **Get your SSH key:**
   ```bash
   cat your-key.pem
   ```

2. **Verify it looks like this:**
   ```
   -----BEGIN RSA PRIVATE KEY-----
   MIIEpAIBAAKCAQEA...
   (many lines)
   ...
   -----END RSA PRIVATE KEY-----
   ```

3. **Update GitHub Secret:**
   - Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions
   - Find `EC2_SSH_KEY`
   - Click **Update**
   - Paste ENTIRE key (including BEGIN and END lines)
   - No extra spaces or blank lines
   - Click **Update secret**

4. **Retry deployment:**
   - Go to: https://github.com/mushqiladac/mushqila/actions
   - Click **Re-run jobs**

---

## 🧪 Test First

Before updating GitHub, test locally:

```bash
ssh -i your-key.pem ubuntu@16.170.25.9 "echo 'Works!'"
```

**If this works:** Just update GitHub secret properly

**If this fails:** See full guide below

---

## 📚 Full Solutions

### Solution 1: Fix Key Format
See: `FIX-SSH-AUTHENTICATION.md` - Solution 1

### Solution 2: Generate New Key
See: `FIX-SSH-AUTHENTICATION.md` - Solution 3

### Solution 3: Use AWS SSM (No SSH!)
See: `FIX-SSH-AUTHENTICATION.md` - Solution 4
- No SSH required
- More secure
- Works through AWS API

---

## 🛠️ Helper Script

Run this to test your key:

```bash
chmod +x fix-ssh-and-deploy.sh
./fix-ssh-and-deploy.sh your-key.pem
```

It will:
- Check key format
- Test SSH connection
- Guide you through fixing

---

## 🚨 Manual Deployment (Temporary)

If you need to deploy NOW while fixing SSH:

```bash
# SSH to server
ssh -i your-key.pem ubuntu@16.170.25.9

# Deploy manually
cd ~/mushqila
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## 📖 Complete Documentation

- `FIX-SSH-AUTHENTICATION.md` - Complete troubleshooting guide
- `fix-ssh-and-deploy.sh` - Automated testing script
- `.github/workflows/deploy-ssm.yml` - Alternative deployment (no SSH)

---

## ✅ Most Likely Fix

**90% of the time, it's just the GitHub secret format.**

Copy your ENTIRE key (including BEGIN and END lines) and update the `EC2_SSH_KEY` secret in GitHub.

That's it!
