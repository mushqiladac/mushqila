# Fix EC2 Deployment - Website Not Updating

## Problem
The deployment completed but the website is not showing updates. Error: `.env.production` file not found.

## Solution Steps

### Step 1: SSH into EC2
```bash
ssh -i "your-key.pem" ubuntu@your-ec2-ip
```

### Step 2: Navigate to Project
```bash
cd ~/mushqila
```

### Step 3: Check Current Status
```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web --tail=50
```

### Step 4: Create .env.production File
```bash
# Create the missing .env.production file
cat > .env.production << 'EOF'
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=your-ec2-ip,your-domain.com

# Database
DB_NAME=mushqila_db
DB_USER=mushqila_user
DB_PASSWORD=your-db-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EOF
```

### Step 5: Restart Containers
```bash
# Stop containers
docker-compose -f docker-compose.prod.yml down

# Start containers
docker-compose -f docker-compose.prod.yml up -d

# Wait for startup
sleep 10

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Restart to apply changes
docker-compose -f docker-compose.prod.yml restart
```

### Step 6: Clear Browser Cache
- Press `Ctrl + Shift + R` (Windows/Linux)
- Press `Cmd + Shift + R` (Mac)
- Or open in incognito/private mode

### Step 7: Verify Deployment
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check web logs
docker-compose -f docker-compose.prod.yml logs web --tail=100

# Test if site is accessible
curl http://localhost:8000/accounts/landing/
```

## Alternative: Use docker-compose.yml Instead

If docker-compose.prod.yml is causing issues, use the regular docker-compose.yml:

```bash
cd ~/mushqila

# Stop any running containers
docker-compose down

# Start with regular compose file
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static
docker-compose exec web python manage.py collectstatic --noinput
```

## Quick Fix Command (All-in-One)

```bash
cd ~/mushqila && \
docker-compose down && \
docker-compose up -d --build && \
sleep 10 && \
docker-compose exec web python manage.py migrate && \
docker-compose exec web python manage.py collectstatic --noinput && \
docker-compose restart && \
docker-compose ps
```

## Check Your Site
Visit: `http://your-ec2-ip:8000/accounts/landing/`

## Still Not Working?

### Check if port 8000 is accessible:
```bash
sudo netstat -tulpn | grep 8000
```

### Check Docker logs:
```bash
docker-compose logs -f web
```

### Restart everything:
```bash
docker-compose down -v
docker-compose up -d --build
```
