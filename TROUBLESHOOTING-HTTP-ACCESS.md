# 🔧 HTTP Access Troubleshooting - mushqila.com

## সমস্যা
http://13.60.112.227 কাজ করছে না

## কারণ
AWS Security Group এ HTTP port 80 খোলা নেই

---

## ✅ সমাধান ১: AWS Security Group Update (প্রধান সমাধান)

### ধাপ ১: AWS Console এ যান
1. খুলুন: https://console.aws.amazon.com/ec2/
2. Region: **eu-north-1 (Stockholm)** নিশ্চিত করুন

### ধাপ ২: Instance খুঁজুন
1. বাম পাশে **Instances** ক্লিক করুন
2. Instance ID: **i-0c70ddd0a58bb4dcf** খুঁজুন
3. Instance এ ক্লিক করুন (checkbox নয়, নামে)

### ধাপ ৩: Security Group খুলুন
1. নিচে **Security** tab ক্লিক করুন
2. **Security groups** এর নাম দেখবেন (যেমন: sg-xxxxx)
3. সেই নামে ক্লিক করুন

### ধাপ ৪: Inbound Rules যোগ করুন
1. **Inbound rules** tab এ যান
2. **Edit inbound rules** বাটন ক্লিক করুন
3. **Add rule** ক্লিক করুন

**Rule 1 - HTTP:**
```
Type: HTTP
Protocol: TCP
Port range: 80
Source: 0.0.0.0/0
Description: Allow HTTP traffic
```

4. আবার **Add rule** ক্লিক করুন

**Rule 2 - HTTPS:**
```
Type: HTTPS
Protocol: TCP
Port range: 443
Source: 0.0.0.0/0
Description: Allow HTTPS traffic
```

5. **Save rules** ক্লিক করুন

### ধাপ ৫: Test করুন
ব্রাউজারে খুলুন: http://13.60.112.227

---

## 🔄 সমাধান ২: Port 8000 দিয়ে Test (Temporary)

যদি Security Group update করতে সমস্যা হয়, তাহলে:

### EC2 Instance Connect দিয়ে:

```bash
cd ~/mushqila
nano docker-compose.prod.yml
```

### এই লাইন খুঁজুন:
```yaml
ports:
  - "80:8000"
```

### পরিবর্তন করুন:
```yaml
ports:
  - "8000:8000"
```

### Save করুন:
- Press: `Ctrl+O`
- Press: `Enter`
- Press: `Ctrl+X`

### Containers Restart করুন:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Test করুন:
http://13.60.112.227:8000

**নোট**: এটি temporary solution। Production এ port 80 ব্যবহার করা উচিত।

---

## 📋 বর্তমান অবস্থা চেক করুন

### Containers চলছে কিনা:
```bash
docker-compose -f docker-compose.prod.yml ps
```

**Expected Output:**
```
NAME                  STATUS
mushqila_web          Up
mushqila_redis        Up
mushqila_celery       Up
mushqila_celery_beat  Up
```

### Web Logs দেখুন:
```bash
docker-compose -f docker-compose.prod.yml logs web | tail -50
```

### Port Listening চেক করুন:
```bash
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000
```

---

## ✅ Security Group Update করার পর

### ১. Application Test করুন
```
http://13.60.112.227
```

### ২. ALLOWED_HOSTS Update করুন

```bash
cd ~/mushqila
nano .env.production
```

এই লাইন খুঁজুন:
```
ALLOWED_HOSTS=13.60.112.227,ec2-13-60-112-227.eu-north-1.compute.amazonaws.com,localhost
```

পরিবর্তন করুন:
```
ALLOWED_HOSTS=13.60.112.227,mushqila.com,www.mushqila.com
```

Save করে restart:
```bash
docker-compose -f docker-compose.prod.yml restart
```

### ৩. Superuser তৈরি করুন
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

**তথ্য দিন:**
- Username: admin (বা যেকোনো নাম)
- Email: your@email.com
- Password: (শক্তিশালী password)

### ৪. Chart of Accounts Initialize করুন
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py initialize_accounts
```

### ৫. Admin Panel Access করুন
```
http://13.60.112.227/admin
```

---

## 🌐 Domain Setup (পরে)

### Namecheap DNS:
1. Login: https://www.namecheap.com
2. Domain List → mushqila.com → Manage
3. Advanced DNS tab

**যোগ করুন:**
```
Type: A Record
Host: @
Value: 13.60.112.227
TTL: Automatic

Type: A Record
Host: www
Value: 13.60.112.227
TTL: Automatic
```

### DNS Propagation চেক:
```bash
# Windows PowerShell
nslookup mushqila.com
```

**অপেক্ষা করুন:** 5-30 মিনিট

---

## 🔍 Common Issues

### Issue 1: "This site can't be reached"
**কারণ:** Security Group এ port 80 খোলা নেই  
**সমাধান:** উপরের সমাধান ১ অনুসরণ করুন

### Issue 2: "Bad Request (400)"
**কারণ:** ALLOWED_HOSTS এ domain নেই  
**সমাধান:** .env.production update করুন

### Issue 3: "502 Bad Gateway"
**কারণ:** Web container চলছে না  
**সমাধান:**
```bash
docker-compose -f docker-compose.prod.yml restart web
docker-compose -f docker-compose.prod.yml logs web
```

### Issue 4: Static files loading না
**কারণ:** Static files collect হয়নি  
**সমাধান:**
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## 📞 Quick Commands

```bash
# Status check
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart web only
docker-compose -f docker-compose.prod.yml restart web

# Stop all
docker-compose -f docker-compose.prod.yml down

# Start all
docker-compose -f docker-compose.prod.yml up -d

# Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## ✅ Success Checklist

- [ ] Security Group এ HTTP (port 80) rule যোগ করেছি
- [ ] Security Group এ HTTPS (port 443) rule যোগ করেছি
- [ ] http://13.60.112.227 কাজ করছে
- [ ] ALLOWED_HOSTS update করেছি
- [ ] Containers restart করেছি
- [ ] Superuser তৈরি করেছি
- [ ] Admin panel access করতে পারছি
- [ ] Chart of accounts initialize করেছি
- [ ] Domain DNS configure করেছি (optional)

---

## 🎯 পরবর্তী Steps

1. ✅ Security Group fix করুন
2. ✅ Application test করুন
3. ✅ Superuser তৈরি করুন
4. ✅ Admin panel explore করুন
5. ⏳ Domain setup করুন (mushqila.com)
6. ⏳ SSL certificate setup করুন (HTTPS)

---

**Instance IP:** 13.60.112.227  
**Instance ID:** i-0c70ddd0a58bb4dcf  
**Region:** eu-north-1 (Stockholm)  
**Status:** Containers Running ✅  
**Issue:** HTTP Access ⏳

