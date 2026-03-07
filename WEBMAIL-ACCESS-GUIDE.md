# Webmail Access Guide

## What's Been Fixed

### 1. CSRF Protection ✅
- CSRF_TRUSTED_ORIGINS configured for https://mushqila.com and https://www.mushqila.com
- Traefik SSL header middleware properly forwarding HTTPS protocol
- Admin login and webmail login now work without CSRF errors

### 2. Authentication Backend ✅
- Fixed `check_login_attempts()` function signature bug
- Authentication now works correctly for all login forms

### 3. Custom Webmail Login ✅
- Created beautiful custom login page at `/webmail/login/`
- Purple gradient design with professional branding
- Separate from main accounts login

## How to Access Webmail

### Option 1: Direct Login URL
```
https://mushqila.com/webmail/login/
```

### Option 2: Webmail Home (Auto-redirects)
```
https://mushqila.com/webmail/
```
This will automatically redirect to the login page if you're not authenticated.

## Login Credentials

Use your existing admin/user credentials:
- **Username**: mushqiladac (or your email)
- **Password**: Sinan210@

## Webmail Features

After logging in, you'll have access to:
- **Inbox**: View received emails
- **Compose**: Send new emails
- **Contacts**: Manage email contacts
- **Account Setup**: Configure email account settings
- **Search**: Search through emails

## Deployment Status

### On EC2 Production Server:
- ✅ HTTPS enabled with Let's Encrypt SSL
- ✅ Traefik reverse proxy configured
- ✅ CSRF protection working
- ✅ Authentication backend fixed
- ✅ Custom webmail login deployed

### URLs Working:
- ✅ https://mushqila.com (landing page)
- ✅ https://mushqila.com/admin/ (admin panel)
- ✅ https://mushqila.com/webmail/login/ (webmail login)
- ✅ https://mushqila.com/accounts/landing/ (public landing)

## Troubleshooting

### If you see "User does not exist" error:
Check which users exist in the database:
```bash
docker-compose -f docker-compose.traefik.yml exec -T web python manage.py shell << 'EOF'
from accounts.models import User
for u in User.objects.all():
    print(f"Username: {u.username}, Email: {u.email}")
EOF
```

### If webmail login doesn't work:
1. Make sure you've deployed the latest code:
   ```bash
   cd ~/mushqila
   git pull
   docker-compose -f docker-compose.traefik.yml build web
   docker-compose -f docker-compose.traefik.yml up -d
   ```

2. Check container logs:
   ```bash
   docker logs mushqila_web --tail=50
   ```

### If you need to create a new user:
```bash
docker-compose -f docker-compose.traefik.yml exec web python manage.py createsuperuser
```

## Next Steps

1. **Configure Email Account**: After logging in, go to Account Setup to configure your AWS SES credentials
2. **Test Email Sending**: Try composing and sending a test email
3. **Import Contacts**: Add contacts to your address book
4. **Customize Settings**: Adjust email preferences as needed

## Security Notes

- All traffic is encrypted with HTTPS
- CSRF protection is enabled
- Session cookies are secure
- Login attempts are rate-limited
- Passwords are hashed with Django's secure algorithm

## Support

If you encounter any issues:
1. Check the error message in the browser
2. Check Docker logs: `docker logs mushqila_web`
3. Verify database connectivity
4. Ensure all environment variables are set in `.env.production`
