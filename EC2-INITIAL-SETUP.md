# EC2 Initial Setup Commands

## Step 1: Connect to EC2

```bash
ssh -i "your-key.pem" ubuntu@16.170.25.9
```

## Step 2: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

## Step 3: Install Docker

```bash
# Install Docker
sudo apt install -y docker.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Enable Docker to start on boot
sudo systemctl enable docker
sudo systemctl start docker

# Logout and login again for group changes to take effect
exit
```

## Step 4: Reconnect and Verify

```bash
# Reconnect to EC2
ssh -i "your-key.pem" ubuntu@16.170.25.9

# Verify Docker installation
docker --version
docker-compose --version
```

## Step 5: Clone Repository

```bash
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila
```

## Step 6: Create .env File

```bash
nano .env
```

Paste this content:

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-generated-secret-key-here
ALLOWED_HOSTS=16.170.25.9,ec2-16-170-25-9.eu-north-1.compute.amazonaws.com

# Database (RDS PostgreSQL)
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=Sinan210
DB_HOST=database-1.cb4mqoeyyym6.eu-north-1.rds.amazonaws.com
DB_PORT=5432

# AWS SES Email
AWS_ACCESS_KEY_ID=[Your SES Access Key]
AWS_SECRET_ACCESS_KEY=[Your SES Secret Key]
AWS_REGION=eu-north-1
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.eu-north-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=[Your SES Access Key]
EMAIL_HOST_PASSWORD=[Your SES Secret Key]
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Redis (Optional)
REDIS_URL=redis://redis:6379/0
```

Save and exit (Ctrl+X, then Y, then Enter)

## Step 7: Generate Django Secret Key

```bash
# On your local machine, run:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copy the output and update SECRET_KEY in .env file
nano .env
# Replace 'your-generated-secret-key-here' with the generated key
```

## Step 8: Start Application

```bash
# Build and start containers
docker-compose up -d --build

# Wait for containers to start
sleep 15

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## Step 9: Check Status

```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs web

# Check if site is accessible
curl http://localhost:8000
```

## Step 10: Configure Security Group

Make sure your EC2 security group allows:
- Port 22 (SSH) from your IP
- Port 80 (HTTP) from anywhere (0.0.0.0/0)
- Port 8000 (Django) from anywhere (0.0.0.0/0)
- Port 443 (HTTPS) from anywhere (0.0.0.0/0) - for future SSL

## Step 11: Test Your Site

Open browser and visit:
```
http://16.170.25.9:8000
```

---

## Troubleshooting

### If containers won't start:
```bash
docker-compose logs
```

### If database connection fails:
```bash
# Check RDS security group allows EC2 IP
# Test connection:
docker-compose exec web python manage.py dbshell
```

### If you need to restart:
```bash
docker-compose down
docker-compose up -d
```

---

## After Initial Setup

Once everything works, you can use GitHub Actions for automatic deployment:

1. Make changes to code locally
2. Commit and push to main branch
3. GitHub Actions will automatically deploy to EC2

Test it:
```bash
git add .
git commit -m "Test auto deployment"
git push origin main
```

Then check GitHub Actions tab to see deployment progress.
