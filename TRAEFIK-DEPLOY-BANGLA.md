# 🚀 Traefik দিয়ে Automatic SSL Setup - সম্পূর্ণ গাইড

## 📋 কি পাবেন?

- ✅ Automatic SSL certificate (Let's Encrypt)
- ✅ HTTP থেকে HTTPS তে auto redirect
- ✅ Wildcard SSL support (*.mushqila.com)
- ✅ Zero-config SSL - একবার setup করলে সব automatic
- ✅ Certificate auto-renewal (প্রতি 60 দিনে)

## 🎯 Step 1: Cloudflare API Token নিন

1. Cloudflare Dashboard এ যান: https://dash.cloudflare.com
2. My Profile → API Tokens → Create Token
3. "Edit zone DNS" template select করুন
4. Zone Resources: Include → Specific zone → mushqila.com
5. Continue to summary → Create Token
6. Token টি copy করে রাখুন (এটি আর দেখাবে না!)

## 🔧 Step 2: EC2 তে Commands Run করুন

```bash
# EC2 তে SSH করুন
ssh -i your-key.pem ubuntu@16.170.25.9

# Project directory তে যান
cd ~/mushqila

# Latest code pull করুন
git pull origin main

# Docker network তৈরি করুন
docker network create proxy

# acme.json file তৈরি করুন (SSL certificate এখানে save হবে)
mkdir -p traefik-data
touch traefik-data/acme.json
chmod 600 traefik-data/acme.json

# Verify permissions
ls -la traefik-data/acme.json
# Output হবে: -rw------- 1 ubuntu ubuntu 0 ... acme.json
```

## 📝 Step 3: .env.production Update করুন

```bash
# .env.production file edit করুন
nano .env.production
```

এই lines গুলো add করুন (file এর শেষে):

```bash
# Cloudflare API for SSL
CLOUDFLARE_EMAIL=mushqiladac@gmail.com
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here

# Django HTTPS Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https

# Update CSRF_TRUSTED_ORIGINS for HTTPS
CSRF_TRUSTED_ORIGINS=https://mushqila.com,https://www.mushqila.com
```

**গুরুত্বপূর্ণ:** `CLOUDFLARE_API_TOKEN` এর জায়গায় আপনার actual token paste করুন!

Save করুন: `Ctrl+X`, তারপর `Y`, তারপর `Enter`

## 🚀 Step 4: Traefik দিয়ে Deploy করুন

```bash
# পুরাতন deployment stop করুন
docker-compose -f docker-compose.prod.yml down

# Traefik দিয়ে start করুন
docker-compose -f docker-compose.traefik.yml up -d --build

# Status check করুন
docker-compose -f docker-compose.traefik.yml ps
```

## ⏳ Step 5: SSL Certificate Generation এর জন্য অপেক্ষা করুন

```bash
# Traefik logs দেখুন
docker logs traefik -f

# এই messages দেখার জন্য অপেক্ষা করুন:
# "Certificates obtained for domains [mushqila.com www.mushqila.com]"
# "Server responded with a certificate"

# 2-3 মিনিট পর Ctrl+C চাপুন
```

## ✅ Step 6: Test করুন

```bash
# HTTPS test করুন
curl -I https://mushqila.com

# HTTP redirect test করুন (এটি HTTPS এ redirect করবে)
curl -I http://mushqila.com

# Certificate details দেখুন
echo | openssl s_client -servername mushqila.com -connect mushqila.com:443 2>/dev/null | openssl x509 -noout -dates
```

## 🌐 Access Points

Deploy হওয়ার পর:

- **Main Site:** https://mushqila.com
- **WWW:** https://www.mushqila.com  
- **Admin:** https://mushqila.com/admin/
- **Webmail:** https://mushqila.com/webmail/
- **Traefik Dashboard:** https://traefik.mushqila.com
  - Username: `admin`
  - Password: `admin`

## 🔐 Traefik Dashboard Password Change করুন (Optional)

```bash
# Password hash generate করুন
sudo apt-get install apache2-utils -y
htpasswd -nb admin your_new_password

# Output copy করুন এবং docker-compose.traefik.yml এ update করুন
```

## 🐛 সমস্যা হলে

### Certificate generate হচ্ছে না

```bash
# DNS check করুন
nslookup mushqila.com
dig mushqila.com

# Cloudflare API check করুন
docker logs traefik | grep -i cloudflare

# acme.json permissions check করুন
ls -la traefik-data/acme.json
```

### CSRF Error আসছে

```bash
# .env.production check করুন
cat .env.production | grep CSRF_TRUSTED_ORIGINS

# Web container restart করুন
docker-compose -f docker-compose.traefik.yml restart web
```

### 500 Error আসছে

```bash
# Web logs দেখুন
docker-compose -f docker-compose.traefik.yml logs web --tail=100

# Database connection check করুন
docker-compose -f docker-compose.traefik.yml exec web python manage.py check
```

## 🔄 Code Update করার পর

```bash
cd ~/mushqila
git pull origin main
docker-compose -f docker-compose.traefik.yml up -d --build
docker-compose -f docker-compose.traefik.yml logs -f
```

## 📊 Useful Commands

```bash
# সব containers দেখুন
docker-compose -f docker-compose.traefik.yml ps

# Logs দেখুন
docker-compose -f docker-compose.traefik.yml logs -f

# Specific service logs
docker logs traefik -f
docker logs mushqila_web -f

# Container এ ঢুকুন
docker exec -it mushqila_web bash

# Database migrations run করুন (যদি প্রয়োজন হয়)
docker-compose -f docker-compose.traefik.yml exec web python manage.py migrate

# Static files collect করুন
docker-compose -f docker-compose.traefik.yml exec web python manage.py collectstatic --noinput

# Superuser তৈরি করুন (যদি প্রয়োজন হয়)
docker-compose -f docker-compose.traefik.yml exec web python manage.py createsuperuser
```

## 📝 Important Notes

1. **First Time Certificate:**
   - 2-5 মিনিট সময় লাগবে
   - Let's Encrypt rate limit: সপ্তাহে 5টি certificate per domain
   
2. **Auto Renewal:**
   - প্রতি 60 দিনে automatic renew হবে
   - কোন manual work লাগবে না

3. **Backup:**
   ```bash
   # acme.json backup করুন
   cp traefik-data/acme.json traefik-data/acme.json.backup
   ```

## ✅ Production Checklist

- [ ] Cloudflare API token পেয়েছি
- [ ] Docker network `proxy` তৈরি করেছি
- [ ] acme.json তৈরি করেছি (600 permissions)
- [ ] .env.production update করেছি
- [ ] Traefik deploy করেছি
- [ ] SSL certificate generate হয়েছে
- [ ] HTTP থেকে HTTPS redirect হচ্ছে
- [ ] সব pages HTTPS এ load হচ্ছে
- [ ] Admin login কাজ করছে
- [ ] Webmail access করতে পারছি

## 🎉 সফল হলে

আপনার site এখন:
- ✅ HTTPS দিয়ে secure
- ✅ Green padlock দেখাবে browser এ
- ✅ Automatic certificate renewal
- ✅ Professional production setup

---

**এখন deploy করুন এবং enjoy করুন automatic SSL!** 🚀
