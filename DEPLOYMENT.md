# Mushqila AWS Deployment Guide

## 🚀 AWS EC2 Deployment with Docker & GitHub CI/CD

### Prerequisites
- AWS EC2 Instance: `i-035811fd86b8a4974`
- Elastic IP: `16.170.104.186`
- AWS RDS PostgreSQL: `database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com`
- AWS SES SMTP configured
- GitHub repository: `https://github.com/mushqiladac/mushqila.git`

---

## 📋 Step 1: Initial EC2 Setup (One-time)

### 1.1 Connect to EC2
```bash
ssh -i your-key.pem ubuntu@16.170.104.186
```

### 1.2 Run Setup Script
```bash
# Download and run setup script
curl -o setup-ec2.sh https://raw.githubusercontent.com/mushqiladac/mushqila/main/setup-ec2.sh
chmod +x setup-ec2.sh
./setup-ec2.sh
```

Or manually:
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt-get install -y git netcat

# Clone repository
cd /home/ubuntu
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila
```

---

## 🔐 Step 2: Configure Environment Variables

### 2.1 Edit Production Environment File
```bash
cd /home/ubuntu/mushqila
nano .env.production
```

### 2.2 Update These Values:
```bash
# Generate SECRET_KEY
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Update in .env.production:
SECRET_KEY=your-generated-secret-key
DB_PASSWORD=your-actual-rds-password
TRAVELPORT_USERNAME=your-galileo-username
TRAVELPORT_PASSWORD=your-galileo-password
```

---

## 🗄️ Step 3: Configure AWS RDS Database

### 3.1 Create Database
```bash
# Connect to RDS from EC2
sudo apt-get install -y postgresql-client

psql -h database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com \
     -U postgres \
     -d postgres

# In PostgreSQL:
CREATE DATABASE mushqila;
\q
```

### 3.2 Update RDS Security Group
- Allow inbound traffic from EC2 security group on port 5432
- Or allow from EC2 IP: `16.170.104.186`

---

## 🚢 Step 4: Deploy Application

### 4.1 First Deployment
```bash
cd /home/ubuntu/mushqila
chmod +x deploy.sh
./deploy.sh
```

### 4.2 Verify Deployment
```bash
# Check running containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f web

# Test application
curl http://localhost
```

### 4.3 Access Application
Open browser: `http://16.170.104.186`

---

## 🔄 Step 5: Setup GitHub Actions CI/CD

### 5.1 Generate SSH Key for GitHub Actions
```bash
# On EC2 instance
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions -N ""

# Add public key to authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Copy private key (you'll need this for GitHub)
cat ~/.ssh/github_actions
```

### 5.2 Add Secret to GitHub
1. Go to: `https://github.com/mushqiladac/mushqila/settings/secrets/actions`
2. Click "New repository secret"
3. Name: `EC2_SSH_KEY`
4. Value: Paste the private key content from above
5. Click "Add secret"

### 5.3 Test CI/CD
```bash
# Make a change and push to main branch
git add .
git commit -m "Test deployment"
git push origin main

# GitHub Actions will automatically deploy to EC2
```

---

## 🔧 Step 6: Configure Domain (Optional)

### 6.1 Update DNS Records
Point your domain to: `16.170.104.186`

```
A Record: mushqila.com → 16.170.104.186
A Record: www.mushqila.com → 16.170.104.186
```

### 6.2 Update ALLOWED_HOSTS
In `.env.production`:
```bash
ALLOWED_HOSTS=16.170.104.186,mushqila.com,www.mushqila.com
```

### 6.3 Setup SSL (Recommended)
```bash
# Install Nginx
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/mushqila

# Add configuration:
server {
    listen 80;
    server_name mushqila.com www.mushqila.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/mushqila/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/mushqila/media/;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/mushqila /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d mushqila.com -d www.mushqila.com
```

---

## 📊 Useful Commands

### Container Management
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart containers
docker-compose -f docker-compose.prod.yml restart

# Stop containers
docker-compose -f docker-compose.prod.yml down

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Django Management
```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Django shell
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
```

### Database Management
```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec web python manage.py dumpdata > backup.json

# Restore database
docker-compose -f docker-compose.prod.yml exec -T web python manage.py loaddata backup.json
```

### Monitoring
```bash
# Check disk space
df -h

# Check memory
free -h

# Check Docker stats
docker stats

# Check system logs
sudo journalctl -u docker -f
```

---

## 🐛 Troubleshooting

### Issue: Cannot connect to database
```bash
# Test RDS connection
telnet database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com 5432

# Check security groups
# Ensure EC2 can access RDS on port 5432
```

### Issue: Static files not loading
```bash
# Collect static files again
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --clear

# Check volume
docker volume ls
docker volume inspect mushqila_static_volume
```

### Issue: Container keeps restarting
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Check environment variables
docker-compose -f docker-compose.prod.yml exec web env
```

---

## 🔒 Security Checklist

- [ ] Change SECRET_KEY to random string
- [ ] Set DEBUG=False in production
- [ ] Configure RDS security groups properly
- [ ] Use strong database password
- [ ] Add .env.production to .gitignore
- [ ] Setup SSL certificate
- [ ] Configure firewall (UFW)
- [ ] Regular security updates
- [ ] Backup database regularly
- [ ] Monitor logs for suspicious activity

---

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/mushqiladac/mushqila/issues
- Email: support@mushqila.com
