# 🚀 Deploy SSL Setup to EC2 - Run These Commands

## ✅ Changes Pushed to GitHub
All configuration files have been pushed to GitHub. Now deploy to EC2.

## 📋 Step-by-Step Deployment

### 1️⃣ SSH into EC2
```bash
ssh -i your-key.pem ubuntu@16.170.25.9
```

### 2️⃣ Navigate to Project Directory
```bash
cd ~/mushqila
```

### 3️⃣ Pull Latest Changes from GitHub
```bash
git pull origin main
```

### 4️⃣ Update .env.production File
The `.env.production` file is not in GitHub (for security). Update it manually:

```bash
nano .env.production
```

Make sure it has this line:
```
ALLOWED_HOSTS=mushqila.com,www.mushqila.com,16.170.25.9,localhost,127.0.0.1
```

Save and exit (Ctrl+X, then Y, then Enter)

### 5️⃣ Run the SSL Setup Script
```bash
chmod +x complete-ssl-setup.sh
./complete-ssl-setup.sh
```

This script will:
- ✅ Remove Nginx default site conflict
- ✅ Verify Nginx configuration
- ✅ Stop Docker containers
- ✅ Start and enable Nginx
- ✅ Rebuild and start Docker containers
- ✅ Verify all services
- ✅ Test HTTP and HTTPS

### 6️⃣ Create Django Superuser
```bash
chmod +x create-superuser.sh
./create-superuser.sh
```

Or manually:
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
# Email: mushqiladac@gmail.com
# Password: Sinan210@
```

### 7️⃣ Verify Deployment
Open your browser and test:
- ✅ http://mushqila.com (should redirect to HTTPS)
- ✅ https://mushqila.com (should work with green padlock)
- ✅ https://www.mushqila.com (should work)
- ✅ https://mushqila.com/admin/ (admin panel)
- ✅ https://mushqila.com/webmail/login/ (webmail)

## 🔍 What Changed

### 1. docker-compose.prod.yml
- Changed port binding from `0.0.0.0:80` to `127.0.0.1:8000`
- This allows Nginx to handle ports 80/443 and proxy to Docker on port 8000

### 2. .env.production
- Updated ALLOWED_HOSTS to include IP address and all domains

### 3. New Scripts Created
- `complete-ssl-setup.sh` - Automated deployment script
- `create-superuser.sh` - Superuser creation script

### 4. New Documentation
- `SSL-DEPLOYMENT-GUIDE.md` - Comprehensive SSL setup guide
- `EC2-COMMANDS.md` - Quick command reference

## 🏗️ Architecture After Deployment

```
Internet (Port 443/80)
         ↓
    Nginx (Reverse Proxy)
    ├─ SSL Termination (Let's Encrypt)
    ├─ HTTP → HTTPS Redirect
    └─ Proxy to localhost:8000
         ↓
    Docker Container (Port 8000)
    └─ Django/Gunicorn
```

## ✅ Expected Results

After running the deployment script, you should see:

1. **Nginx Status**: Active and running
2. **Docker Containers**: 4 containers running (web, redis, celery, celery-beat)
3. **Port Bindings**:
   - Port 80: Nginx (HTTP)
   - Port 443: Nginx (HTTPS)
   - Port 8000: Docker (localhost only)
   - Port 6379: Redis
4. **SSL Certificate**: Valid until 2026-06-06
5. **Auto-Renewal**: Certbot timer active

## 🐛 Troubleshooting

### If the script fails:
```bash
# Check what went wrong
docker-compose -f docker-compose.prod.yml logs --tail=50
sudo tail -n 50 /var/log/nginx/error.log

# Try manual steps from SSL-DEPLOYMENT-GUIDE.md
```

### If HTTPS doesn't work:
```bash
# Check Nginx status
sudo systemctl status nginx

# Check SSL certificate
sudo certbot certificates

# Test Nginx configuration
sudo nginx -t
```

### If Docker containers won't start:
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web
```

## 📞 Support

If you encounter issues:
1. Check `SSL-DEPLOYMENT-GUIDE.md` for detailed troubleshooting
2. Check `EC2-COMMANDS.md` for common commands
3. Review logs: `docker-compose -f docker-compose.prod.yml logs -f`

## 🎉 Success Indicators

You'll know deployment is successful when:
- ✅ https://mushqila.com loads with green padlock
- ✅ Webmail link appears on landing page footer
- ✅ Admin panel accessible at https://mushqila.com/admin/
- ✅ No SSL certificate warnings in browser
- ✅ HTTP automatically redirects to HTTPS

## 📝 Next Steps After Deployment

1. Test all pages and functionality
2. Monitor logs for any errors
3. Set up monitoring/alerting (optional)
4. Configure backup strategy (optional)
5. Test webmail functionality
6. Test flight search when ready

---

**Ready to deploy? Run the commands above! 🚀**
