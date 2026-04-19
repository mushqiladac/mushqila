# 🚀 Manual Deployment - এখনই Deploy করুন

## সমস্যা
GitHub Actions SSH authentication fail করছে, কিন্তু আপনার 500 error fix টা production এ যাওয়া দরকার।

## সমাধান - Manual Deployment (5 মিনিট)

### Step 1: SSH দিয়ে Server এ Connect করুন

```bash
ssh -i "C:\Users\user\Desktop\Mushqila\mushqila-keys.pem" ubuntu@16.170.25.9
```

### Step 2: Project Directory তে যান

```bash
cd /home/ubuntu/mushqila
```

### Step 3: Local Changes Stash করুন (যদি থাকে)

```bash
git stash
```

### Step 4: Latest Code Pull করুন

```bash
git pull origin main
```

### Step 5: Docker Containers Restart করুন

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache web
docker-compose -f docker-compose.prod.yml up -d
```

### Step 6: Migrations Run করুন

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Step 7: Static Files Collect করুন

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Step 8: Container Status Check করুন

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Step 9: Logs Check করুন

```bash
docker-compose -f docker-compose.prod.yml logs web --tail=50
```

### Step 10: Test করুন

Browser এ যান: https://mushqila.com/accounts/login/

✅ যদি login page load হয়, তাহলে deployment successful!

---

## 🔧 GitHub Actions SSH Fix (পরে করবেন)

GitHub Actions এর SSH problem fix করতে:

### Option 1: SSH Key Regenerate করুন

```bash
# Server এ নতুন SSH key pair তৈরি করুন
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions_key -N ""

# Public key authorized_keys এ add করুন
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys

# Private key দেখুন
cat ~/.ssh/github_actions_key
```

এই private key টা GitHub Secret `EC2_SSH_KEY` তে update করুন।

### Option 2: EC2 SSH Configuration Check করুন

```bash
# SSH config check করুন
sudo nano /etc/ssh/sshd_config
```

নিশ্চিত করুন:
```
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication no
```

SSH service restart করুন:
```bash
sudo systemctl restart sshd
```

### Option 3: Authorized Keys Permission Fix করুন

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

---

## 📊 Current Status

- ✅ Code fix pushed to GitHub (commit 8c6e240)
- ✅ `config/urls.py` duplicate lines removed
- ✅ `static/robots.txt` added
- ❌ GitHub Actions SSH authentication failing
- ⏳ Manual deployment needed

---

## 🎯 Next Steps

1. **এখনই করুন**: Manual deployment (উপরের steps follow করুন)
2. **পরে করুন**: GitHub Actions SSH fix (Option 1, 2, or 3)
3. **Test করুন**: Login page এবং অন্যান্য pages

---

## 💡 Tips

- Manual deployment সবসময় কাজ করবে
- GitHub Actions fix করতে সময় নিন, rush করবেন না
- প্রতিবার code change এর পর manual deploy করতে পারবেন
- GitHub Actions fix হলে automatic deployment হবে

---

**Created**: 2026-04-07
**Status**: Ready to deploy manually
