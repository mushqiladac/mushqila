# EC2 Manual Deployment Guide

## Prerequisites
- EC2 instance running: 16.170.104.186
- SSH key file (.pem)
- GitHub repository: https://github.com/mushqiladac/mushqila.git

---

## Step 1: SSH to EC2

```bash
ssh -i your-key.pem ubuntu@16.170.104.186
```

---

## Step 2: Install Docker & Docker Compose (if not installed)

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Logout and login again for docker group to take effect
exit
ssh -i your-key.pem ubuntu@16.170.104.186
```

---

## Step 3: Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila
```

---

## Step 4: Create .env.production File

```bash
nano .env.production
```

Add these variables (update with your actual values):

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-random-secret-key-here
ALLOWED_HOSTS=16.170.104.186,mushqila.com,www.mushqila.com

# Database (AWS RDS)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mushqila
DB_USER=postgres
DB_PASSWORD=your-rds-password
DB_HOST=database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com
DB_PORT=5432

# Email (AWS SES)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.eu-north-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=AKIAUQETDVDPECKLURNW
EMAIL_HOST_PASSWORD=your-ses-password
DEFAULT_FROM_EMAIL=noreply@mushqila.com

# Galileo GDS (when available)
TRAVELPORT_USERNAME=
TRAVELPORT_PASSWORD=
TRAVELPORT_BRANCH_CODE=P702214
TRAVELPORT_TARGET_BRANCH=
TRAVELPORT_PCC=

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

Save and exit (Ctrl+X, Y, Enter)

---

## Step 5: Generate SECRET_KEY

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy the output and update SECRET_KEY in .env.production

---

## Step 6: Build and Start Containers

```bash
# Build containers
docker-compose -f docker-compose.prod.yml build

# Start containers
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

---

## Step 7: Run Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Initialize chart of accounts
docker-compose -f docker-compose.prod.yml exec web python manage.py initialize_accounts

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## Step 8: Check Logs

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Check for errors
docker-compose -f docker-compose.prod.yml logs web | grep -i error
```

---

## Step 9: Test Application

### From EC2:
```bash
curl http://localhost:8000
```

### From Browser:
- Home: http://16.170.104.186
- Admin: http://16.170.104.186/admin
- Landing: http://16.170.104.186/accounts/landing/

---

## Useful Commands

### View Container Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### View Logs
```bash
# All logs
docker-compose -f docker-compose.prod.yml logs -f

# Web logs only
docker-compose -f docker-compose.prod.yml logs -f web

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 web
```

### Restart Containers
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Stop Containers
```bash
docker-compose -f docker-compose.prod.yml down
```

### Rebuild and Restart
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Execute Django Commands
```bash
# Django shell
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## Update Deployment (Future Updates)

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.104.186

# Navigate to project
cd /home/ubuntu/mushqila

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run migrations (if any)
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Check environment variables
docker-compose -f docker-compose.prod.yml exec web env | grep -i django
```

### Database connection error
```bash
# Test RDS connection
telnet database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com 5432

# Check RDS security group allows EC2 IP
```

### Static files not loading
```bash
# Collect static files again
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Check WhiteNoise configuration
docker-compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

### Port already in use
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

---

## Security Checklist

- [ ] .env.production has strong SECRET_KEY
- [ ] DEBUG=False in production
- [ ] Database password is secure
- [ ] RDS security group configured
- [ ] EC2 security group allows only necessary ports
- [ ] SSH key is secured
- [ ] Regular backups configured

---

## Success Criteria

✅ All containers running
✅ Web server responding (200 OK)
✅ Database connected
✅ Static files serving
✅ Admin panel accessible
✅ No errors in logs

---

**Deployment complete! Your application is now live! 🎉**
