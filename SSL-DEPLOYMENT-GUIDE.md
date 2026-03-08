# SSL Deployment Guide - mushqila.com

## Current Status
- ✅ SSL certificate obtained from Let's Encrypt (expires 2026-06-06)
- ✅ Certbot configured with auto-renewal
- ⚠️ Nginx has conflicts with default site
- ⚠️ Docker containers need reconfiguration

## What Was Done
1. Updated `.env.production` with correct ALLOWED_HOSTS including IP address
2. Modified `docker-compose.prod.yml` to bind to localhost:8000 instead of 0.0.0.0:80
3. Created deployment scripts for easy setup

## Deployment Steps

### Option 1: Automated Deployment (Recommended)
Run the complete setup script on EC2:

```bash
# Make script executable
chmod +x complete-ssl-setup.sh

# Run the script
./complete-ssl-setup.sh
```

This script will:
- Remove Nginx default site conflict
- Verify Nginx configuration
- Stop Docker containers
- Start and enable Nginx
- Rebuild and start Docker containers
- Verify all services
- Test HTTP and HTTPS
- Check SSL auto-renewal

### Option 2: Manual Deployment
If you prefer to run commands manually:

```bash
# 1. Remove Nginx default site
sudo rm -f /etc/nginx/sites-enabled/default

# 2. Test Nginx configuration
sudo nginx -t

# 3. Stop Docker containers
docker-compose -f docker-compose.prod.yml down

# 4. Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 5. Start Docker containers
docker-compose -f docker-compose.prod.yml up -d --build

# 6. Verify services
docker-compose -f docker-compose.prod.yml ps
sudo systemctl status nginx
sudo ss -tlnp | grep -E ':(80|443|8000)'

# 7. Test the site
curl -I https://mushqila.com/
```

## Create Superuser

After deployment is complete, create the Django superuser:

```bash
# Option 1: Using the script
chmod +x create-superuser.sh
./create-superuser.sh

# Option 2: Manual creation
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
# Email: mushqiladac@gmail.com
# Password: Sinan210@
```

## Verification Checklist

After deployment, verify:

- [ ] HTTP redirects to HTTPS: `curl -I http://mushqila.com/`
- [ ] HTTPS works: `curl -I https://mushqila.com/`
- [ ] WWW subdomain works: `curl -I https://www.mushqila.com/`
- [ ] Site loads in browser: https://mushqila.com
- [ ] Admin panel accessible: https://mushqila.com/admin/
- [ ] Webmail link works on landing page
- [ ] SSL certificate valid: Check browser padlock icon
- [ ] Auto-renewal configured: `sudo systemctl status certbot.timer`

## Architecture

```
Internet (Port 443/80)
         ↓
    Nginx (Reverse Proxy)
    - Handles SSL termination
    - Redirects HTTP → HTTPS
    - Proxies to localhost:8000
         ↓
    Docker Container (Port 8000)
    - Django/Gunicorn
    - Bound to 127.0.0.1:8000
```

## SSL Certificate Details

- **Certificate Path**: `/etc/letsencrypt/live/mushqila.com/fullchain.pem`
- **Private Key Path**: `/etc/letsencrypt/live/mushqila.com/privkey.pem`
- **Expiration Date**: 2026-06-06
- **Auto-Renewal**: Configured via systemd timer (certbot.timer)
- **Renewal Check**: Runs twice daily
- **Domains Covered**: mushqila.com, www.mushqila.com

## Nginx Configuration

The Nginx configuration at `/etc/nginx/sites-available/mushqila` includes:
- HTTP to HTTPS redirect
- SSL certificate configuration
- Proxy pass to localhost:8000
- Security headers
- Static file handling

## Troubleshooting

### If HTTPS doesn't work:
```bash
# Check Nginx status
sudo systemctl status nginx

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check SSL certificate
sudo certbot certificates

# Test Nginx configuration
sudo nginx -t
```

### If Docker containers aren't running:
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check container logs
docker-compose -f docker-compose.prod.yml logs web

# Restart containers
docker-compose -f docker-compose.prod.yml restart
```

### If port conflicts occur:
```bash
# Check what's using ports
sudo ss -tlnp | grep -E ':(80|443|8000)'

# Stop conflicting services
sudo systemctl stop apache2  # if Apache is running
```

## Files Modified

1. `.env.production` - Updated ALLOWED_HOSTS
2. `docker-compose.prod.yml` - Changed port binding to 127.0.0.1:8000
3. Created `complete-ssl-setup.sh` - Automated deployment script
4. Created `create-superuser.sh` - Superuser creation script

## Next Steps After Deployment

1. ✅ Push changes to GitHub
2. ✅ Deploy to EC2 using the script
3. ✅ Create superuser
4. Test all functionality:
   - Landing page
   - Webmail login
   - Admin panel
   - Flight search (when ready)
5. Monitor logs for any issues

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Nginx and Docker logs
3. Verify DNS settings point to EC2 IP: 16.170.25.9
4. Ensure security groups allow ports 80 and 443
