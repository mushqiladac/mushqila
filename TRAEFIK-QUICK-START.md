# 🚀 Traefik SSL - Quick Start Guide

## ⚡ 5-Minute Setup

### 1️⃣ Get Cloudflare API Token

1. Go to: https://dash.cloudflare.com
2. My Profile → API Tokens → Create Token
3. Use "Edit zone DNS" template
4. Zone: mushqila.com
5. Copy the token

### 2️⃣ Update .env.production on EC2

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# Edit .env.production
cd ~/mushqila
nano .env.production
```

Add these lines at the end:

```bash
# Cloudflare API
CLOUDFLARE_EMAIL=mushqiladac@gmail.com
CLOUDFLARE_API_TOKEN=paste_your_token_here

# HTTPS Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
CSRF_TRUSTED_ORIGINS=https://mushqila.com,https://www.mushqila.com
```

Save: `Ctrl+X`, `Y`, `Enter`

### 3️⃣ Run Deployment Script

```bash
# Make script executable
chmod +x deploy-traefik.sh

# Run deployment
./deploy-traefik.sh
```

That's it! The script will:
- ✅ Create Docker network
- ✅ Setup SSL certificate storage
- ✅ Stop old deployment
- ✅ Start Traefik with SSL
- ✅ Generate Let's Encrypt certificate

### 4️⃣ Verify

Wait 2-3 minutes, then test:

```bash
# Test HTTPS
curl -I https://mushqila.com

# Check certificate
docker logs traefik | grep -i certificate
```

## 🌐 Access Your Site

- **Main:** https://mushqila.com
- **Admin:** https://mushqila.com/admin/
- **Webmail:** https://mushqila.com/webmail/
- **Traefik Dashboard:** https://traefik.mushqila.com

## 🔧 Manual Setup (if script fails)

```bash
# 1. Create network
docker network create proxy

# 2. Setup acme.json
mkdir -p traefik-data
touch traefik-data/acme.json
chmod 600 traefik-data/acme.json

# 3. Stop old deployment
docker-compose -f docker-compose.prod.yml down

# 4. Start Traefik
docker-compose -f docker-compose.traefik.yml up -d --build

# 5. Check logs
docker logs traefik -f
```

## 🐛 Troubleshooting

### Certificate not generating?

```bash
# Check Cloudflare API
docker logs traefik | grep -i cloudflare

# Check DNS
nslookup mushqila.com

# Check acme.json permissions
ls -la traefik-data/acme.json
# Should be: -rw------- (600)
```

### CSRF errors?

```bash
# Verify CSRF_TRUSTED_ORIGINS
cat .env.production | grep CSRF_TRUSTED_ORIGINS

# Restart web
docker-compose -f docker-compose.traefik.yml restart web
```

### 500 errors?

```bash
# Check web logs
docker-compose -f docker-compose.traefik.yml logs web --tail=100

# Check database connection
docker-compose -f docker-compose.traefik.yml exec web python manage.py check
```

## 📊 Useful Commands

```bash
# View all logs
docker-compose -f docker-compose.traefik.yml logs -f

# Check status
docker-compose -f docker-compose.traefik.yml ps

# Restart service
docker-compose -f docker-compose.traefik.yml restart web

# Stop everything
docker-compose -f docker-compose.traefik.yml down

# Update code and redeploy
git pull origin main
docker-compose -f docker-compose.traefik.yml up -d --build
```

## ✅ Success Checklist

- [ ] Cloudflare API token added to .env.production
- [ ] Deployment script ran successfully
- [ ] All containers running (check with `docker ps`)
- [ ] SSL certificate generated (check Traefik logs)
- [ ] https://mushqila.com loads with green padlock
- [ ] HTTP redirects to HTTPS
- [ ] Admin login works
- [ ] No CSRF errors

## 🎯 What You Get

- ✅ Automatic SSL certificates
- ✅ Auto HTTP → HTTPS redirect
- ✅ Certificate auto-renewal every 60 days
- ✅ Wildcard SSL (*.mushqila.com)
- ✅ Zero maintenance
- ✅ Production-ready setup

---

**Need help?** Check the full guide: `TRAEFIK-DEPLOY-BANGLA.md`
