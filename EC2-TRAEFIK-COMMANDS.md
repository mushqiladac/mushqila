# 🚀 EC2 Traefik Deployment - Exact Commands

## 📋 Prerequisites

1. **Cloudflare API Token** - Get from: https://dash.cloudflare.com
   - My Profile → API Tokens → Create Token
   - Template: "Edit zone DNS"
   - Zone: mushqila.com
   - Copy the token

2. **GitHub Token** - Use your personal access token if needed

## 🔧 Step-by-Step Commands

### Step 1: SSH to EC2

```bash
ssh -i your-key.pem ubuntu@16.170.25.9
```

### Step 2: Navigate to Project

```bash
cd ~/mushqila
```

### Step 3: Pull Latest Code

```bash
git pull origin main
```

If it asks for credentials:
- Username: `mushqiladac`
- Password: `your_github_token`

### Step 4: Update .env.production

```bash
nano .env.production
```

Add these lines at the end (replace `YOUR_TOKEN_HERE` with actual Cloudflare token):

```bash
# Cloudflare API for SSL
CLOUDFLARE_EMAIL=mushqiladac@gmail.com
CLOUDFLARE_API_TOKEN=YOUR_TOKEN_HERE

# Django HTTPS Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

Also update this line (change http to https):
```bash
CSRF_TRUSTED_ORIGINS=https://mushqila.com,https://www.mushqila.com
```

Save and exit:
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

### Step 5: Create Docker Network

```bash
docker network create proxy
```

If it says "already exists", that's fine - continue.

### Step 6: Setup SSL Certificate Storage

```bash
mkdir -p traefik-data
touch traefik-data/acme.json
chmod 600 traefik-data/acme.json
```

Verify permissions:
```bash
ls -la traefik-data/acme.json
```

Should show: `-rw------- 1 ubuntu ubuntu 0 ... acme.json`

### Step 7: Stop Current Deployment

```bash
docker-compose -f docker-compose.prod.yml down
```

### Step 8: Start Traefik Deployment

```bash
docker-compose -f docker-compose.traefik.yml up -d --build
```

This will take 2-3 minutes to build and start.

### Step 9: Check Container Status

```bash
docker-compose -f docker-compose.traefik.yml ps
```

You should see:
- traefik (Up)
- mushqila_web (Up)
- mushqila_redis (Up)
- mushqila_celery (Up)
- mushqila_celery_beat (Up)

### Step 10: Monitor SSL Certificate Generation

```bash
docker logs traefik -f
```

Wait for these messages:
- "Certificates obtained for domains [mushqila.com www.mushqila.com]"
- "Server responded with a certificate"

This takes 2-3 minutes. Press `Ctrl+C` when you see the success message.

### Step 11: Test HTTPS

```bash
# Test HTTPS
curl -I https://mushqila.com

# Test HTTP redirect
curl -I http://mushqila.com

# Check certificate details
echo | openssl s_client -servername mushqila.com -connect mushqila.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Step 12: Test in Browser

Open these URLs in your browser:
- https://mushqila.com (should show green padlock)
- https://www.mushqila.com
- https://mushqila.com/admin/
- https://mushqila.com/webmail/
- https://traefik.mushqila.com (username: admin, password: admin)

## ✅ Success Indicators

You'll know it's working when:

1. **Green Padlock** in browser address bar
2. **HTTPS** in URL (not HTTP)
3. **No "Not Secure" warning**
4. **Admin login works** without CSRF errors
5. **Traefik logs show** "Certificates obtained"

## 🐛 Troubleshooting

### Problem: Certificate not generating

```bash
# Check Cloudflare API
docker logs traefik | grep -i cloudflare

# Check DNS
nslookup mushqila.com

# Should show: 16.170.25.9
```

**Solution:** Verify Cloudflare API token is correct in .env.production

### Problem: CSRF errors on admin login

```bash
# Check CSRF_TRUSTED_ORIGINS
cat .env.production | grep CSRF_TRUSTED_ORIGINS

# Should show: https://mushqila.com,https://www.mushqila.com
```

**Solution:** Make sure it says `https://` not `http://`

```bash
# Restart web container
docker-compose -f docker-compose.traefik.yml restart web
```

### Problem: 500 Internal Server Error

```bash
# Check web logs
docker-compose -f docker-compose.traefik.yml logs web --tail=100

# Check for boto3 errors
docker-compose -f docker-compose.traefik.yml logs web | grep -i boto3
```

**Solution:** Rebuild without cache if boto3 is missing

```bash
docker-compose -f docker-compose.traefik.yml build --no-cache web
docker-compose -f docker-compose.traefik.yml up -d
```

### Problem: Containers not starting

```bash
# Check container status
docker-compose -f docker-compose.traefik.yml ps

# Check logs for errors
docker-compose -f docker-compose.traefik.yml logs
```

**Solution:** Check .env.production for syntax errors

### Problem: Can't access site

```bash
# Check if containers are running
docker ps

# Check Traefik logs
docker logs traefik --tail=50

# Check web logs
docker logs mushqila_web --tail=50
```

## 📊 Useful Commands

### View Logs
```bash
# All logs
docker-compose -f docker-compose.traefik.yml logs -f

# Traefik only
docker logs traefik -f

# Web only
docker logs mushqila_web -f

# Last 100 lines
docker-compose -f docker-compose.traefik.yml logs --tail=100
```

### Container Management
```bash
# Check status
docker-compose -f docker-compose.traefik.yml ps

# Restart all
docker-compose -f docker-compose.traefik.yml restart

# Restart specific service
docker-compose -f docker-compose.traefik.yml restart web

# Stop all
docker-compose -f docker-compose.traefik.yml down

# Start all
docker-compose -f docker-compose.traefik.yml up -d
```

### Django Management
```bash
# Run migrations
docker-compose -f docker-compose.traefik.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.traefik.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.traefik.yml exec web python manage.py createsuperuser

# Django shell
docker-compose -f docker-compose.traefik.yml exec web python manage.py shell

# Check for issues
docker-compose -f docker-compose.traefik.yml exec web python manage.py check
```

### Database
```bash
# Access database (if needed)
docker-compose -f docker-compose.traefik.yml exec web python manage.py dbshell
```

### Update Code
```bash
cd ~/mushqila
git pull origin main
docker-compose -f docker-compose.traefik.yml up -d --build
```

## 🔄 Rollback to Old Setup

If you need to go back to HTTP (not recommended):

```bash
# Stop Traefik
docker-compose -f docker-compose.traefik.yml down

# Start old setup
docker-compose -f docker-compose.prod.yml up -d
```

## 📝 Post-Deployment Checklist

- [ ] All containers running (`docker ps`)
- [ ] SSL certificate generated (check Traefik logs)
- [ ] https://mushqila.com loads with green padlock
- [ ] http://mushqila.com redirects to https://
- [ ] Admin login works (https://mushqila.com/admin/)
- [ ] Webmail accessible (https://mushqila.com/webmail/)
- [ ] No CSRF errors
- [ ] No 500 errors
- [ ] Traefik dashboard accessible (https://traefik.mushqila.com)

## 🎯 Expected Timeline

- **Step 1-6:** 5 minutes (setup)
- **Step 7-8:** 3 minutes (deployment)
- **Step 9-10:** 2-3 minutes (SSL certificate generation)
- **Step 11-12:** 2 minutes (testing)

**Total: ~15 minutes**

## 📞 Need Help?

Check these files:
- Full guide (Bangla): `TRAEFIK-DEPLOY-BANGLA.md`
- Quick start: `TRAEFIK-QUICK-START.md`
- Comparison: `TRAEFIK-VS-CURRENT.md`

Or run the automated script:
```bash
chmod +x deploy-traefik.sh
./deploy-traefik.sh
```

---

**Ready to deploy? Start with Step 1!** 🚀
