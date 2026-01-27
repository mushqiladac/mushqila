# 🌐 Domain Setup Guide - mushqila.com

## Step 1: Namecheap DNS Configuration

### Login to Namecheap
1. Go to: https://www.namecheap.com
2. Login to your account
3. Go to **Domain List**
4. Click **Manage** next to **mushqila.com**

### Add DNS Records
1. Click on **Advanced DNS** tab
2. In **Host Records** section, add these records:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| **A Record** | @ | 13.60.112.227 | Automatic |
| **A Record** | www | 13.60.112.227 | Automatic |

**Explanation**:
- `@` → mushqila.com (root domain)
- `www` → www.mushqila.com (www subdomain)
- `13.60.112.227` → Your EC2 Elastic IP

### Save Changes
Click **Save All Changes** button

**⏱️ Propagation Time**: 5-30 minutes (sometimes up to 24 hours)

---

## Step 2: Update Django Settings

### Connect to EC2
Use **EC2 Instance Connect** from AWS Console

### Update Environment File
```bash
cd ~/mushqila
nano .env.production
```

### Update ALLOWED_HOSTS Line
Find this line:
```
ALLOWED_HOSTS=13.60.112.227,ec2-13-60-112-227.eu-north-1.compute.amazonaws.com,localhost
```

Change to:
```
ALLOWED_HOSTS=13.60.112.227,ec2-13-60-112-227.eu-north-1.compute.amazonaws.com,mushqila.com,www.mushqila.com
```

**Save**: Press `Ctrl+O`, then `Enter`, then `Ctrl+X`

### Restart Containers
```bash
docker-compose -f docker-compose.prod.yml restart
```

---

## Step 3: Verify DNS Propagation

### Check DNS (from your computer)
```bash
# Windows PowerShell
nslookup mushqila.com
nslookup www.mushqila.com

# Should show: 13.60.112.227
```

### Online Tools
- https://dnschecker.org
- Enter: mushqila.com
- Should show: 13.60.112.227

---

## Step 4: Test Your Domain

Once DNS propagates, test these URLs:
- http://mushqila.com
- http://www.mushqila.com
- http://13.60.112.227 (should still work)

---

## Step 5: Setup SSL/HTTPS (Optional but Recommended)

### Install Certbot
```bash
# Via EC2 Instance Connect
sudo apt update
sudo apt install -y certbot python3-certbot-nginx nginx
```

### Configure Nginx
```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/mushqila
```

Paste this configuration:
```nginx
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
```

Save and enable:
```bash
sudo ln -s /etc/nginx/sites-available/mushqila /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Get SSL Certificate
```bash
sudo certbot --nginx -d mushqila.com -d www.mushqila.com
```

Follow prompts:
- Enter email address
- Agree to terms
- Choose: Redirect HTTP to HTTPS (option 2)

### Auto-renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot will auto-renew before expiry
```

---

## Final URLs

After setup complete:

✅ **HTTP**: 
- http://mushqila.com
- http://www.mushqila.com

✅ **HTTPS** (after SSL setup):
- https://mushqila.com
- https://www.mushqila.com

✅ **Admin Panel**:
- https://mushqila.com/admin

---

## Troubleshooting

### Domain not working?
1. **Check DNS propagation**: Use dnschecker.org
2. **Wait longer**: Can take up to 24 hours
3. **Clear browser cache**: Ctrl+Shift+Delete
4. **Try incognito mode**: Ctrl+Shift+N

### SSL not working?
1. **Check nginx status**: `sudo systemctl status nginx`
2. **Check certbot logs**: `sudo certbot certificates`
3. **Restart nginx**: `sudo systemctl restart nginx`

### Application error?
1. **Check containers**: `docker-compose -f docker-compose.prod.yml ps`
2. **Check logs**: `docker-compose -f docker-compose.prod.yml logs web`
3. **Restart**: `docker-compose -f docker-compose.prod.yml restart`

---

## Summary Checklist

- [ ] Add A records in Namecheap (@ and www)
- [ ] Update ALLOWED_HOSTS in .env.production
- [ ] Restart Docker containers
- [ ] Wait for DNS propagation (5-30 min)
- [ ] Test domain: mushqila.com
- [ ] Setup SSL with Certbot (optional)
- [ ] Test HTTPS: https://mushqila.com

---

**Domain**: mushqila.com  
**IP**: 13.60.112.227  
**Status**: Ready to configure  
**SSL**: Optional (recommended for production)
