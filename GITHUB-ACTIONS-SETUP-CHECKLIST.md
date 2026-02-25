# GitHub Actions Setup Checklist

## Required Information for GitHub Secrets

### 1. EC2 Connection Details
- **EC2_HOST**: Your EC2 instance public IP or domain
  - Example: `54.123.45.67` or `ec2-54-123-45-67.compute-1.amazonaws.com`
  
- **EC2_USERNAME**: SSH username (usually `ubuntu` for Ubuntu instances)
  - Example: `ubuntu`
  
- **EC2_SSH_KEY**: Your private SSH key content
  - Location: The `.pem` file you downloaded when creating EC2
  - Get content: `cat your-key.pem` (copy entire content including BEGIN/END lines)

### 2. RDS Database Details
- **DB_NAME**: PostgreSQL database name
  - Example: `mushqila_db`
  
- **DB_USER**: Database username
  - Example: `mushqila_user`
  
- **DB_PASSWORD**: Database password
  - The password you set when creating RDS
  
- **DB_HOST**: RDS endpoint
  - Example: `mushqila-db.abc123.us-east-1.rds.amazonaws.com`
  
- **DB_PORT**: Database port (default: `5432`)

### 3. Django Settings
- **SECRET_KEY**: Django secret key
  - Generate new: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
  
- **DEBUG**: Set to `False` for production
  
- **ALLOWED_HOSTS**: Your domain/IP
  - Example: `your-domain.com,54.123.45.67`

### 4. AWS SES Email Settings (Optional)
- **EMAIL_HOST**: SES SMTP endpoint
  - Example: `email-smtp.us-east-1.amazonaws.com`
  
- **EMAIL_PORT**: Usually `587`
  
- **EMAIL_HOST_USER**: SES SMTP username
  
- **EMAIL_HOST_PASSWORD**: SES SMTP password
  
- **DEFAULT_FROM_EMAIL**: Verified email address
  - Example: `noreply@yourdomain.com`

### 5. Redis (Optional - if using Celery)
- **REDIS_URL**: Redis connection URL
  - Example: `redis://localhost:6379/0`

---

## How to Add GitHub Secrets

1. Go to your GitHub repository: https://github.com/mushqiladac/mushqila
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret one by one

---

## Quick Setup Commands

### On Your Local Machine:

```bash
# 1. Get your SSH key content
cat path/to/your-key.pem

# 2. Generate Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### On EC2 Instance (First Time Setup):

```bash
# SSH into EC2
ssh -i "your-key.pem" ubuntu@your-ec2-ip

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# Clone repository
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila

# Create .env.production file
nano .env.production
```

### .env.production Template:

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-generated-secret-key
ALLOWED_HOSTS=your-domain.com,your-ec2-ip

# Database (RDS)
DB_NAME=mushqila_db
DB_USER=mushqila_user
DB_PASSWORD=your-db-password
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432

# Email (SES)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-ses-smtp-username
EMAIL_HOST_PASSWORD=your-ses-smtp-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0
```

---

## GitHub Actions Workflow File

The workflow file is already in `.github/workflows/deploy.yml`

Make sure it uses the correct branch (main instead of dwd):

```yaml
on:
  push:
    branches: [ main ]  # Changed from dwd to main
```

---

## Testing Deployment

After setting up secrets:

1. Make a small change to any file
2. Commit and push to main branch:
   ```bash
   git add .
   git commit -m "Test deployment"
   git push origin main
   ```
3. Go to GitHub → Actions tab
4. Watch the deployment process

---

## Troubleshooting

### If deployment fails:

1. Check GitHub Actions logs
2. SSH into EC2 and check:
   ```bash
   cd ~/mushqila
   docker-compose logs
   ```

### Common Issues:

- **SSH connection failed**: Check EC2 security group allows SSH (port 22)
- **Database connection failed**: Check RDS security group allows EC2 IP
- **Permission denied**: Make sure ubuntu user is in docker group

---

## Security Checklist

✅ Never commit `.env` files to GitHub
✅ Use GitHub Secrets for sensitive data
✅ Set DEBUG=False in production
✅ Use strong database passwords
✅ Restrict EC2 security group to necessary ports only
✅ Enable HTTPS (use Let's Encrypt)

---

## Next Steps After Setup

1. Configure domain DNS to point to EC2 IP
2. Setup SSL certificate (Let's Encrypt)
3. Configure Nginx as reverse proxy
4. Setup automated backups for RDS
5. Configure CloudWatch monitoring
