# EC2 Quick Command Reference

## Deploy SSL Setup (Run This First!)

```bash
# Upload files to EC2 (run from your local machine)
scp -i your-key.pem .env.production ubuntu@16.170.25.9:~/mushqila/
scp -i your-key.pem docker-compose.prod.yml ubuntu@16.170.25.9:~/mushqila/
scp -i your-key.pem complete-ssl-setup.sh ubuntu@16.170.25.9:~/mushqila/
scp -i your-key.pem create-superuser.sh ubuntu@16.170.25.9:~/mushqila/

# SSH into EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# Navigate to project directory
cd ~/mushqila

# Pull latest code from GitHub
git pull origin main

# Run the SSL setup script
chmod +x complete-ssl-setup.sh
./complete-ssl-setup.sh

# Create superuser
chmod +x create-superuser.sh
./create-superuser.sh
```

## Common Commands

### Docker Management
```bash
# View running containers
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Nginx Management
```bash
# Check Nginx status
sudo systemctl status nginx

# Start Nginx
sudo systemctl start nginx

# Stop Nginx
sudo systemctl stop nginx

# Restart Nginx
sudo systemctl restart nginx

# Reload Nginx (without downtime)
sudo systemctl reload nginx

# Test Nginx configuration
sudo nginx -t

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### SSL Certificate Management
```bash
# Check certificate status
sudo certbot certificates

# Check auto-renewal timer
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run

# Force renewal (if needed)
sudo certbot renew --force-renewal

# View Let's Encrypt logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Django Management
```bash
# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Django shell
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Check Django settings
docker-compose -f docker-compose.prod.yml exec web python manage.py check
```

### System Monitoring
```bash
# Check port usage
sudo ss -tlnp | grep -E ':(80|443|8000|6379)'

# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check system logs
sudo journalctl -xe

# Check Docker logs
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Testing
```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://mushqila.com/

# Test HTTPS
curl -I https://mushqila.com/

# Test WWW subdomain
curl -I https://www.mushqila.com/

# Test from localhost
curl -I http://localhost/

# Test SSL certificate
openssl s_client -connect mushqila.com:443 -servername mushqila.com
```

### Git Operations
```bash
# Pull latest changes
git pull origin main

# Check current branch
git branch

# View recent commits
git log --oneline -10

# Check status
git status
```

### Database Operations
```bash
# Connect to PostgreSQL (RDS)
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell

# Backup database
docker-compose -f docker-compose.prod.yml exec web python manage.py dumpdata > backup.json

# Load data
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata backup.json
```

### Redis Operations
```bash
# Connect to Redis CLI
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Check Redis info
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO

# Monitor Redis commands
docker-compose -f docker-compose.prod.yml exec redis redis-cli MONITOR
```

### Celery Operations
```bash
# View Celery worker logs
docker-compose -f docker-compose.prod.yml logs -f celery

# View Celery beat logs
docker-compose -f docker-compose.prod.yml logs -f celery-beat

# Restart Celery worker
docker-compose -f docker-compose.prod.yml restart celery

# Restart Celery beat
docker-compose -f docker-compose.prod.yml restart celery-beat
```

## Emergency Commands

### If site is down:
```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps
sudo systemctl status nginx

# Restart everything
docker-compose -f docker-compose.prod.yml restart
sudo systemctl restart nginx

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=50
sudo tail -n 50 /var/log/nginx/error.log
```

### If SSL is broken:
```bash
# Check certificate
sudo certbot certificates

# Test Nginx config
sudo nginx -t

# Renew certificate
sudo certbot renew --force-renewal

# Restart Nginx
sudo systemctl restart nginx
```

### If Docker containers won't start:
```bash
# Stop everything
docker-compose -f docker-compose.prod.yml down

# Remove old containers
docker-compose -f docker-compose.prod.yml rm -f

# Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Important URLs

- **Main Site**: https://mushqila.com
- **Admin Panel**: https://mushqila.com/admin/
- **Webmail**: https://mushqila.com/webmail/login/
- **API Docs**: https://mushqila.com/api/docs/ (if configured)

## Important Credentials

- **Superuser Email**: mushqiladac@gmail.com
- **Superuser Password**: Sinan210@
- **Database**: RDS PostgreSQL (see .env.production)
- **Email**: AWS SES (see .env.production)

## Security Notes

1. Never commit `.env.production` to GitHub
2. Keep SSH key secure
3. Regularly update system packages: `sudo apt update && sudo apt upgrade`
4. Monitor SSL certificate expiration (auto-renews)
5. Review Nginx access logs for suspicious activity
6. Keep Docker images updated
