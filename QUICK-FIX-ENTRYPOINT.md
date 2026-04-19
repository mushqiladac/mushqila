# 🔧 Quick Fix: Missing entrypoint.sh

## সমস্যা
Docker build fail করছে কারণ `entrypoint.sh` file missing।

## সমাধান

### Step 1: Local থেকে GitHub এ Push করুন

Windows PowerShell এ:

```powershell
cd C:\Users\user\Desktop\Mushqila

# Add the new file
git add entrypoint.sh

# Commit
git commit -m "Add missing entrypoint.sh file"

# Push to GitHub
git push origin main
```

### Step 2: Server এ Pull করুন

Server SSH এ:

```bash
cd /home/ubuntu/mushqila

# Pull latest code
git pull origin main
```

### Step 3: Docker Build করুন

```bash
# Build with no cache
docker-compose -f docker-compose.prod.yml build --no-cache

# Start containers
docker-compose -f docker-compose.prod.yml up -d
```

### Step 4: Verify করুন

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web --tail=50
```

---

## ✅ এখন কি করবেন?

1. উপরের commands গুলো run করুন
2. Login page test করুন: https://mushqila.com/accounts/login/
3. যদি কাজ করে, তাহলে deployment successful! 🎉

---

**Created**: 2026-04-07
