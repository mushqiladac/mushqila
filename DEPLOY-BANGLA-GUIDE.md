# 🚀 Deployment Guide - বাংলায়

## সমস্যা কি?

আপনার website এ 500 error ছিল। সেটা fix করা হয়েছে এবং GitHub এ push করা হয়েছে। কিন্তু GitHub Actions SSH authentication fail করছে, তাই automatic deployment হচ্ছে না।

## এখন কি করবেন?

### ✅ Option 1: PowerShell Script দিয়ে Deploy (সবচেয়ে সহজ)

1. PowerShell খুলুন (Administrator হিসেবে)

2. Project folder এ যান:
```powershell
cd C:\Users\user\Desktop\Mushqila
```

3. Script run করুন:
```powershell
.\deploy-manual.ps1
```

4. Script automatically সব কিছু করবে:
   - Server এ connect করবে
   - Latest code pull করবে
   - Docker containers restart করবে
   - Migrations run করবে
   - Static files collect করবে
   - Test করবে

5. শেষে message দেখবেন: "✅ Deployment successful!"

---

### ✅ Option 2: Manual Commands (Step by Step)

যদি script কাজ না করে, তাহলে manually করুন:

#### Step 1: Server এ Connect করুন

```powershell
ssh -i "C:\Users\user\Desktop\Mushqila\mushqila-keys.pem" ubuntu@16.170.25.9
```

#### Step 2: Project Directory তে যান

```bash
cd /home/ubuntu/mushqila
```

#### Step 3: Local Changes Stash করুন

```bash
git stash
```

#### Step 4: Latest Code Pull করুন

```bash
git pull origin main
```

আপনি দেখবেন:
```
Updating acaf5ca..8c6e240
Fast-forward
 config/urls.py | 2 --
 static/robots.txt | 1 +
 2 files changed, 1 insertion(+), 2 deletions(-)
```

#### Step 5: Docker Containers Restart করুন

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache web
docker-compose -f docker-compose.prod.yml up -d
```

#### Step 6: Migrations Run করুন

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

#### Step 7: Static Files Collect করুন

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

#### Step 8: Container Status Check করুন

```bash
docker-compose -f docker-compose.prod.yml ps
```

আপনি দেখবেন সব containers "Up" status এ আছে।

#### Step 9: Logs Check করুন

```bash
docker-compose -f docker-compose.prod.yml logs web --tail=50
```

কোন error থাকলে এখানে দেখবেন।

#### Step 10: Browser এ Test করুন

যান: https://mushqila.com/accounts/login/

✅ যদি login page ঠিকমতো load হয়, তাহলে deployment successful!

---

## 🔧 GitHub Actions Fix করুন (পরে)

GitHub Actions এর SSH problem fix করতে:

### Server এ নতুন SSH Key তৈরি করুন

1. Server এ SSH করুন:
```bash
ssh -i "C:\Users\user\Desktop\Mushqila\mushqila-keys.pem" ubuntu@16.170.25.9
```

2. Fix script run করুন:
```bash
cd /home/ubuntu/mushqila
bash fix-github-ssh.sh
```

3. Script শেষে একটা PRIVATE KEY দেখাবে। সেটা copy করুন।

4. GitHub এ যান:
   - Repository Settings → Secrets and variables → Actions
   - `EC2_SSH_KEY` secret edit করুন
   - নতুন private key paste করুন
   - Save করুন

5. GitHub Actions আবার test করুন:
   - Repository এ যান
   - Actions tab এ যান
   - "Re-run all jobs" click করুন

✅ এবার GitHub Actions কাজ করবে!

---

## 📊 Current Status

| Item | Status |
|------|--------|
| Code Fix | ✅ Done (pushed to GitHub) |
| Manual Deployment | ⏳ Pending (আপনাকে করতে হবে) |
| GitHub Actions | ❌ SSH authentication failing |
| Login Page | ⏳ Will work after deployment |

---

## 🎯 Summary

1. **এখনই করুন**: Manual deployment (Option 1 বা Option 2)
2. **Test করুন**: Login page check করুন
3. **পরে করুন**: GitHub Actions SSH fix করুন

---

## 💡 Important Notes

- Manual deployment সবসময় কাজ করবে
- GitHub Actions fix করতে rush করবেন না
- প্রতিবার code change এর পর manual deploy করতে পারবেন
- GitHub Actions fix হলে automatic deployment হবে

---

## 🆘 যদি কোন সমস্যা হয়

### Login page এখনও 500 error দেখাচ্ছে?

1. Server logs check করুন:
```bash
docker-compose -f docker-compose.prod.yml logs web --tail=100
```

2. Container status check করুন:
```bash
docker-compose -f docker-compose.prod.yml ps
```

3. Django shell এ যান:
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
```

4. URLs check করুন:
```python
from django.urls import get_resolver
print(get_resolver().url_patterns)
```

### SSH connection fail করছে?

1. SSH key permissions check করুন:
```powershell
icacls "C:\Users\user\Desktop\Mushqila\mushqila-keys.pem"
```

2. SSH key এর permissions ঠিক করুন:
```powershell
icacls "C:\Users\user\Desktop\Mushqila\mushqila-keys.pem" /inheritance:r
icacls "C:\Users\user\Desktop\Mushqila\mushqila-keys.pem" /grant:r "$($env:USERNAME):(R)"
```

---

**Created**: 2026-04-07  
**Last Updated**: 2026-04-07  
**Status**: Ready to deploy
