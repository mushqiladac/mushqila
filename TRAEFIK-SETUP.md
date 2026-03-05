# 🚀 Traefik SSL Setup for Mushqila

## 📋 Overview

This setup uses Traefik v2 as a reverse proxy with automatic SSL certificate management via Let's Encrypt.

## ✅ Features

- ✅ Automatic SSL certificates via Let's Encrypt
- ✅ Auto HTTP to HTTPS redirect
- ✅ Wildcard SSL support (*.mushqila.com)
- ✅ Certificate persistence in Docker volumes
- ✅ Zero-config SSL after initial setup
- ✅ Traefik dashboard for monitoring
- ✅ Secure headers middleware

## 🔧 Prerequisites

1. **Domain DNS Setup:**
   - Point `mushqila.com` A record to your server IP
   - Point `www.mushqila.com` CNAME to `mushqila.com`
   - Point `*.mushqila.com` A record to your server IP (for wildcard)

2. **Cloudflare API Token** (for DNS challenge):
   - Go to Cloudflare Dashboard
   - My Profile → API Tokens → Create Token
   - Use "Edit zone DNS" template
   - Zone Resources: Include → Specific zone → mushqila.com
   - Copy the token

## 📦 Installation Steps

### Step 1: Create Docker Network

```bash
docker network create proxy
```

### Step 2: Create acme.json File

```bash
mkdir -p traefik-data
touch traefik-data/acme.json
chmod 600 traefik-data/acme.json
```

### Step 3: Update .env.production

Add these lines to `.env.production`:

```bash
# Cloudflare API for SSL
CLOUDFLARE_EMAIL=mushqiladac@gmail.com
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here

# Django HTTPS Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

### Step 4: Update Django Settings

Add to `config/settings.py`:

```python
# HTTPS Settings for Production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

### Step 5: Deploy with Traefik

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Start with Traefik
docker-compose -f docker-compose.traefik.yml up -d

# Check logs
docker-compose -f docker-compose.traefik.yml logs -f traefik
```

### Step 6: Verify SSL

Wait 2-3 minutes for certificate generation, then test:

```bash
# Test HTTPS
curl -I https://mushqila.com

# Test HTTP redirect
curl -I http://mushqila.com
```

## 🌐 Access Points

After deployment:

- **Main Site:** https://mushqila.com
- **WWW:** https://www.mushqila.com
- **Admin:** https://mushqila.com/admin/
- **Traefik Dashboard:** https://traefik.mushqila.com
  - Username: `admin`
  - Password: `admin` (change this!)

## 🔐 Change Traefik Dashboard Password

```bash
# Generate new password hash
sudo apt-get install apache2-utils
htpasswd -nb admin your_new_password

# Copy the output and update in docker-compose.traefik.yml
# Replace the basicauth.users value
```

## 📊 Monitor Certificates

```bash
# Check Traefik logs
docker logs traefik -f

# Check acme.json
cat traefik-data/acme.json | jq
```

## 🐛 Troubleshooting

### Certificate Not Generated

1. **Check DNS:**
   ```bash
   nslookup mushqila.com
   dig mushqila.com
   ```

2. **Check Cloudflare API:**
   ```bash
   docker logs traefik | grep -i cloudflare
   ```

3. **Verify acme.json permissions:**
   ```bash
   ls -la traefik-data/acme.json
   # Should be: -rw------- (600)
   ```

### HTTP Not Redirecting to HTTPS

1. **Check Traefik config:**
   ```bash
   docker exec traefik cat /traefik.yml
   ```

2. **Restart Traefik:**
   ```bash
   docker-compose -f docker-compose.traefik.yml restart traefik
   ```

### Django CSRF Errors

1. **Update CSRF_TRUSTED_ORIGINS:**
   ```python
   CSRF_TRUSTED_ORIGINS = [
       'https://mushqila.com',
       'https://www.mushqila.com',
   ]
   ```

2. **Restart web container:**
   ```bash
   docker-compose -f docker-compose.traefik.yml restart web
   ```

## 🔄 Update Deployment

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.traefik.yml up -d --build

# Check status
docker-compose -f docker-compose.traefik.yml ps
```

## 📝 Important Notes

1. **First Certificate Generation:**
   - Takes 2-5 minutes
   - Let's Encrypt rate limit: 5 certificates per week per domain
   - Use staging environment for testing

2. **Certificate Renewal:**
   - Automatic every 60 days
   - Traefik handles this automatically
   - No manual intervention needed

3. **Backup acme.json:**
   ```bash
   cp traefik-data/acme.json traefik-data/acme.json.backup
   ```

4. **Staging Environment (for testing):**
   
   In `traefik-data/traefik.yml`, change:
   ```yaml
   certificatesResolvers:
     cloudflare:
       acme:
         caServer: https://acme-staging-v02.api.letsencrypt.org/directory
   ```

## 🎯 Production Checklist

- [ ] DNS records configured
- [ ] Cloudflare API token added to .env.production
- [ ] Docker network `proxy` created
- [ ] acme.json created with 600 permissions
- [ ] Traefik dashboard password changed
- [ ] Django HTTPS settings enabled
- [ ] CSRF_TRUSTED_ORIGINS updated
- [ ] SSL certificate generated successfully
- [ ] HTTP redirects to HTTPS
- [ ] All pages load over HTTPS
- [ ] No mixed content warnings

## 🚀 Quick Commands

```bash
# Start everything
docker-compose -f docker-compose.traefik.yml up -d

# Stop everything
docker-compose -f docker-compose.traefik.yml down

# View logs
docker-compose -f docker-compose.traefik.yml logs -f

# Restart specific service
docker-compose -f docker-compose.traefik.yml restart web

# Check certificate
echo | openssl s_client -servername mushqila.com -connect mushqila.com:443 2>/dev/null | openssl x509 -noout -dates
```

## 📞 Support

If you encounter issues:

1. Check Traefik logs: `docker logs traefik`
2. Check web logs: `docker-compose -f docker-compose.traefik.yml logs web`
3. Verify DNS: `nslookup mushqila.com`
4. Test SSL: `curl -vI https://mushqila.com`

---

**Ready to deploy with automatic SSL!** 🎉
