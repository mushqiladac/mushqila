# 🔧 Webmail URL Namespace Fix

## ❌ Error Fixed
```
NoReverseMatch at /accounts/landing/
'webmail' is not a registered namespace
```

## ✅ Solution Applied

### 1. Added Webmail URL to config/urls.py
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('flights/', include('flights.urls', namespace='flights')),
    path('webmail/', include('webmail.urls', namespace='webmail')),  # ✅ ADDED
    path('', HomeView.as_view(), name='home'),
    path('', include('b2c.urls')),
]
```

### 2. Verified webmail/urls.py has app_name
```python
app_name = 'webmail'  # ✅ EXISTS
```

### 3. Verified webmail in INSTALLED_APPS
```python
INSTALLED_APPS = [
    ...
    'webmail',  # ✅ EXISTS
]
```

## 🚀 How to Apply

### Local Development:
```bash
# Restart Docker container
docker-compose restart web

# Wait 10 seconds
# Then test in browser: http://localhost:8000/accounts/landing/
```

### EC2 Production:
```bash
# SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# Pull latest code
cd ~/mushqila
git pull origin main

# Restart containers
docker-compose -f docker-compose.prod.yml restart web

# Wait and test
sleep 10
curl http://localhost/accounts/landing/
```

## 🌐 Webmail Access URLs

After fix:
- **Webmail Inbox**: http://localhost:8000/webmail/
- **Webmail from Footer**: Click envelope icon in footer
- **Direct Inbox**: http://localhost:8000/webmail/inbox/
- **Compose**: http://localhost:8000/webmail/compose/
- **Contacts**: http://localhost:8000/webmail/contacts/

## 📝 What Changed

### Footer Social Icons (landing.html & landing2.html):
```html
<div class="d-flex gap-3">
    <a href="https://www.youtube.com/@mushqila" class="text-white-50">
        <i class="fab fa-youtube fa-lg"></i>
    </a>
    <a href="https://www.facebook.com/@mushqila" class="text-white-50">
        <i class="fab fa-facebook fa-lg"></i>
    </a>
    <a href="+966507572999" class="text-white-50">
        <i class="fab fa-whatsapp fa-lg"></i>
    </a>
    <a href="{% url 'webmail:inbox' %}" class="text-white-50" title="Webmail">
        <i class="fas fa-envelope fa-lg"></i>  <!-- ✅ NEW -->
    </a>
</div>
```

## ✅ Verification Steps

1. **Check URL is registered:**
   ```bash
   docker-compose exec web python manage.py show_urls | grep webmail
   ```

2. **Test webmail access:**
   ```bash
   curl http://localhost:8000/webmail/
   ```

3. **Test landing page:**
   ```bash
   curl http://localhost:8000/accounts/landing/
   ```

4. **Check in browser:**
   - Go to: http://localhost:8000/accounts/landing/
   - Scroll to footer
   - Click envelope icon
   - Should redirect to webmail inbox

## 🔍 Troubleshooting

### If still getting error:

1. **Clear browser cache** (Ctrl+Shift+R)

2. **Restart Docker completely:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **Check logs:**
   ```bash
   docker-compose logs web
   ```

4. **Verify URL patterns:**
   ```bash
   docker-compose exec web python manage.py shell
   >>> from django.urls import reverse
   >>> reverse('webmail:inbox')
   '/webmail/inbox/'
   ```

## 📊 Status

- ✅ config/urls.py updated
- ✅ webmail namespace registered
- ✅ Footer links updated
- ✅ Code pushed to GitHub
- ⏳ Waiting for Docker restart

---

**Next Step**: Restart Docker and test in browser!
