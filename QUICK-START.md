# 🚀 Mushqila Quick Deployment Guide

## EC2 তে প্রথমবার Setup (One-time)

### 1. EC2 তে Connect করুন
```bash
ssh -i your-key.pem ubuntu@16.170.104.186
```

### 2. Setup Script চালান
```bash
cd /home/ubuntu
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila
chmod +x setup-ec2.sh
./setup-ec2.sh
```

### 3. Environment Variables Update করুন
```bash
nano .env.production
```

**এই values গুলো অবশ্যই পরিবর্তন করুন:**
```bash
# SECRET_KEY generate করুন:
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# .env.production এ update করুন:
SECRET_KEY=<generated-key>
DB_PASSWORD=<your-rds-password>
TRAVELPORT_USERNAME=<your-galileo-username>
TRAVELPORT_PASSWORD=<your-galileo-password>
```

### 4. Deploy করুন
```bash
./deploy.sh
```

### 5. Browser এ দেখুন
```
http://16.170.104.186
```

---

## GitHub CI/CD Setup

### 1. SSH Key Generate করুন (EC2 তে)
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions -N ""
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_actions  # এটা copy করুন
```

### 2. GitHub এ Secret যোগ করুন
1. যান: https://github.com/mushqiladac/mushqila/settings/secrets/actions
2. "New repository secret" ক্লিক করুন
3. Name: `EC2_SSH_KEY`
4. Value: উপরের private key paste করুন
5. "Add secret" ক্লিক করুন

### 3. Test করুন
```bash
# কোন পরিবর্তন করুন এবং push করুন
git add .
git commit -m "Test auto deployment"
git push origin main

# GitHub Actions automatically deploy করবে!
```

---

## প্রয়োজনীয় Commands

### Container দেখুন
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Logs দেখুন
```bash
docker-compose -f docker-compose.prod.yml logs -f web
```

### Restart করুন
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Superuser তৈরি করুন
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Database Migrate করুন
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

---

## সমস্যা সমাধান

### Database connect হচ্ছে না?
```bash
# RDS Security Group check করুন
# EC2 থেকে RDS এ port 5432 access আছে কিনা দেখুন
telnet database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com 5432
```

### Container restart হচ্ছে?
```bash
# Logs দেখুন
docker-compose -f docker-compose.prod.yml logs web
```

### Static files load হচ্ছে না?
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## পরবর্তী পদক্ষেপ

1. ✅ Domain setup করুন (mushqila.com)
2. ✅ SSL certificate install করুন (Let's Encrypt)
3. ✅ Nginx reverse proxy configure করুন
4. ✅ Regular backup setup করুন
5. ✅ Monitoring setup করুন

বিস্তারিত জানতে দেখুন: **DEPLOYMENT.md**
