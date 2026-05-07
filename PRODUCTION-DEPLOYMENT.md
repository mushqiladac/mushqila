# Production Deployment Guide - Mushqila Finance App

## Overview
This guide covers deploying the Mushqila Finance App with PostgreSQL in production environment.

## Prerequisites

### System Requirements
- Python 3.8+
- PostgreSQL 12+
- Node.js (for frontend assets, if applicable)
- Git

### Database Setup
PostgreSQL must be installed and running before deployment.

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### CentOS/RHEL
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Windows
Download and install from: https://www.postgresql.org/download/windows/

#### macOS
```bash
brew install postgresql
brew services start postgresql
```

## Quick Deployment

### Option 1: Automated Deployment (Recommended)

#### Linux/macOS
```bash
chmod +x deploy_production.sh
./deploy_production.sh
```

#### Windows PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy_production.ps1
```

### Option 2: Manual Deployment

#### 1. Environment Configuration
Copy and configure the production environment file:
```bash
cp .env.production.example .env.production
```

Edit `.env.production` with your actual values:
```env
# Database Configuration
DB_NAME=mushqila
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Django Settings
SECRET_KEY=your-very-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Database Setup
```bash
# Create database
sudo -u postgres createdb mushqila

# Create user and grant privileges
sudo -u postgres psql << EOF
CREATE USER mushqila_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mushqila TO mushqila_user;
ALTER USER mushqila_user CREATEDB;
\q
EOF
```

#### 4. Run Migrations
```bash
export DJANGO_SETTINGS_MODULE=config.settings_production
python manage.py migrate
```

#### 5. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

#### 6. Create Users
```bash
python create_production_users.py
```

#### 7. Create Superuser
```bash
python manage.py createsuperuser
```

## Default Users

The deployment creates the following users automatically:

### Admin User
- **Email:** saddam110@mushqila.com
- **Password:** Sinan210
- **Role:** Admin
- **Access:** Full system access

### Manager User
- **Email:** manager110@mushqila.com
- **Password:** Sinan210@
- **Role:** Manager
- **Access:** Management functions

### Regular Users
1. **Email:** mhcl107@mushqila.com | **Password:** Sinan217
2. **Email:** mhcl104@mushqila.com | **Password:** Sinan214
3. **Email:** mhcl108@mushqila.com | **Password:** Sinan218
4. **Email:** mhcl007@mushqila.com | **Password:** Sinan207
5. **Email:** mhcl112@mushqila.com | **Password:** Sinan212

## Login System

The finance app includes role-based login with user type selection:

1. **Admin:** Full system administration
2. **Manager:** User management and approval functions
3. **User:** Standard finance operations

Users must select their correct role during login for successful authentication.

## Production Server

### Using Gunicorn (Recommended)
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 config.wsgi:application
```

### Using Django Development Server (Testing Only)
```bash
export DJANGO_SETTINGS_MODULE=config.settings_production
python manage.py runserver 0.0.0.0:8000
```

## Security Configuration

### Environment Variables
- Set `SECRET_KEY` to a strong, random value
- Set `DEBUG=False` in production
- Configure `ALLOWED_HOSTS` with your domain(s)

### Database Security
- Use strong database passwords
- Restrict database access to application server only
- Enable SSL for database connections

### Web Server Configuration
Configure Nginx or Apache to serve static files and proxy requests to Django.

#### Nginx Example
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /static/ {
        alias /path/to/mushqila/staticfiles/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Logging

### Logs Location
- Application logs: `logs/django.log`
- Error logs: `logs/django_error.log`

### Log Rotation
Logs are automatically rotated when they reach 15MB with 10 backup copies.

## Backup Strategy

### Database Backup
```bash
# Daily backup
pg_dump -h localhost -U postgres mushqila > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U postgres mushqila > $BACKUP_DIR/mushqila_$DATE.sql
find $BACKUP_DIR -name "mushqila_*.sql" -mtime +7 -delete
```

### Static Files Backup
```bash
tar -czf static_backup_$(date +%Y%m%d).tar.gz staticfiles/
```

## Troubleshooting

### Common Issues

#### Database Connection Error
```
Error: could not translate host name "db" to address
```
**Solution:** Ensure PostgreSQL is running and DB_HOST is set to 'localhost' in production.

#### Migration Issues
```bash
# Reset migrations (last resort)
python manage.py migrate finance zero
python manage.py migrate finance
```

#### Static File Issues
```bash
# Clear and recollect static files
rm -rf staticfiles/
python manage.py collectstatic --noinput
```

### Performance Optimization

1. **Database Connection Pooling**
   - Set `CONN_MAX_AGE=600` in settings

2. **Caching**
   - Configure Redis for session and cache storage
   - Enable template fragment caching

3. **Static File Serving**
   - Use CDN for static files in production
   - Enable gzip compression

## Support

For deployment issues:
1. Check logs: `tail -f logs/django.log`
2. Verify database connectivity: `python manage.py dbshell`
3. Test configuration: `python manage.py check --deploy`

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_NAME` | Database name | mushqila |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | - |
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `SECRET_KEY` | Django secret key | - |
| `DEBUG` | Debug mode | False |
| `ALLOWED_HOSTS` | Allowed domains | localhost,127.0.0.1 |
| `EMAIL_HOST` | SMTP server | smtp.gmail.com |
| `EMAIL_PORT` | SMTP port | 587 |
| `EMAIL_USE_TLS` | Use TLS | True |
