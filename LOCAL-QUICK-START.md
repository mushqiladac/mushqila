# 🚀 Local Development - Quick Start

## ✅ Prerequisites Check

1. **Docker Desktop চালু আছে কিনা check করুন:**
   - Windows Start Menu → Docker Desktop
   - System tray এ Docker icon দেখুন
   - "Docker Desktop is running" দেখা উচিত

2. **PowerShell বা Command Prompt খুলুন**

---

## 🎯 Step-by-Step Commands

### 1. Project Directory তে যান

```powershell
cd C:\Users\user\Desktop\mhcl
```

### 2. Existing Containers Stop করুন (যদি থাকে)

```powershell
docker-compose down
```

### 3. Containers Build এবং Start করুন

```powershell
# Build করুন (প্রথমবার বা code change এর পর)
docker-compose build

# Start করুন
docker-compose up -d

# Status check করুন
docker-compose ps
```

**Expected Output:**
```
NAME                COMMAND                  SERVICE   STATUS
mhcl-db-1          "docker-entrypoint.s…"   db        Up
mhcl-web-1         "python manage.py ru…"   web       Up
```

### 4. Database Setup করুন

```powershell
# Database migrations run করুন
docker-compose exec web python manage.py migrate

# Static files collect করুন
docker-compose exec web python manage.py collectstatic --noinput

# Superuser তৈরি করুন
docker-compose exec web python manage.py createsuperuser
```

**Superuser Prompt:**
```
Username: admin
Email: admin@example.com
Password: ********
Password (again): ********
```

### 5. Chart of Accounts Initialize করুন

```powershell
docker-compose exec web python manage.py initialize_accounts
```

### 6. Application Access করুন

Browser এ খুলুন:
- **Main Site:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin

---

## 📋 Common Commands

### Container Management

```powershell
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# View logs (all containers)
docker-compose logs -f

# View logs (web only)
docker-compose logs -f web

# Container status
docker-compose ps
```

### Django Management

```powershell
# Run migrations
docker-compose exec web python manage.py migrate

# Create migrations
docker-compose exec web python manage.py makemigrations

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Django shell
docker-compose exec web python manage.py shell

# Database shell
docker-compose exec web python manage.py dbshell

# Run tests
docker-compose exec web python manage.py test

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Container Shell Access

```powershell
# Web container shell
docker-compose exec web bash

# Database container shell
docker-compose exec db psql -U postgres -d mushqila
```

---

## 🔧 Troubleshooting

### Issue 1: "Cannot connect to Docker daemon"

**Solution:**
1. Docker Desktop চালু করুন
2. Wait for "Docker Desktop is running"
3. আবার try করুন

### Issue 2: Port 8000 already in use

**Solution:**
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
# ports: - "8001:8000"
```

### Issue 3: Database connection error

**Solution:**
```powershell
# Stop and remove all containers
docker-compose down -v

# Rebuild and start
docker-compose build
docker-compose up -d

# Run migrations again
docker-compose exec web python manage.py migrate
```

### Issue 4: Static files not loading

**Solution:**
```powershell
docker-compose exec web python manage.py collectstatic --noinput
```

### Issue 5: Container build error

**Solution:**
```powershell
# Clean build
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔄 Development Workflow

### When you change Python code:
- Django auto-reloads
- No action needed
- Just refresh browser

### When you change models:
```powershell
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### When you change static files (CSS/JS):
```powershell
docker-compose exec web python manage.py collectstatic --noinput
```

### When you change requirements.txt:
```powershell
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 📊 Check Application Health

### 1. Container Status
```powershell
docker-compose ps
```

**Expected:** All containers "Up"

### 2. Web Logs
```powershell
docker-compose logs web | Select-Object -Last 50
```

**Expected:** No errors, "Starting development server"

### 3. Database Connection
```powershell
docker-compose exec web python manage.py dbshell
```

**Expected:** PostgreSQL prompt

### 4. Browser Test
```
http://localhost:8000
```

**Expected:** Application loads

---

## 🎯 Quick Test Checklist

- [ ] Docker Desktop running
- [ ] Containers built: `docker-compose build`
- [ ] Containers started: `docker-compose up -d`
- [ ] Containers status: `docker-compose ps` (all Up)
- [ ] Migrations run: `docker-compose exec web python manage.py migrate`
- [ ] Static files collected
- [ ] Superuser created
- [ ] Chart of accounts initialized
- [ ] http://localhost:8000 loads
- [ ] http://localhost:8000/admin accessible

---

## 🆘 Need Help?

### View Logs
```powershell
# All logs
docker-compose logs

# Last 50 lines
docker-compose logs --tail=50

# Follow logs (live)
docker-compose logs -f

# Web container only
docker-compose logs -f web
```

### Container Info
```powershell
# List all containers
docker ps -a

# Container details
docker inspect mhcl-web-1

# Container stats
docker stats
```

### Clean Restart
```powershell
# Stop everything
docker-compose down -v

# Remove all images
docker system prune -a

# Start fresh
docker-compose build --no-cache
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## 📝 Next Steps After Setup

1. ✅ Local environment running
2. ✅ Database setup complete
3. ✅ Superuser created
4. ⏳ Test application features
5. ⏳ Make code changes
6. ⏳ Test changes locally
7. ⏳ Commit to Git
8. ⏳ Push to GitHub
9. ⏳ Deploy to EC2

---

**Local URL:** http://localhost:8000  
**Admin URL:** http://localhost:8000/admin  
**Database:** PostgreSQL (in Docker)  
**Status:** Development Mode
