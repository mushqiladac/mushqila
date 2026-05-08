# Run Mushqila Locally with Docker

## Prerequisites

1. **Docker Desktop** installed and running
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version` and `docker-compose --version`

2. **Git** (already have it)

3. **Port 8000** available (not used by other apps)

## Quick Start (3 Steps)

### Step 1: Build and Start Containers

```bash
# Build Docker images
docker-compose build

# Start all containers (web, db, redis)
docker-compose up -d

# Check if containers are running
docker-compose ps
```

Expected output:
```
NAME                IMAGE              STATUS
mushqila_web        mushqila-web       Up
mushqila_db         postgres:13        Up
mushqila_redis      redis:7-alpine     Up
```

### Step 2: Run Migrations and Create Superuser

```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create finance users (optional)
docker-compose exec web python manage.py create_finance_users
```

### Step 3: Access the Application

Open your browser:
- **Main Site**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **Finance App**: http://localhost:8000/finance/login/
- **Webmail**: http://localhost:8000/webmail/login/
- **B2B Dashboard**: http://localhost:8000/accounts/login/

## Detailed Commands

### Container Management

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# View logs
docker-compose logs -f web

# View specific service logs
docker-compose logs -f db
docker-compose logs -f redis
```

### Database Commands

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create migrations
docker-compose exec web python manage.py makemigrations

# Access database shell
docker-compose exec web python manage.py dbshell

# Access PostgreSQL directly
docker-compose exec db psql -U postgres -d mushqila
```

### Django Management Commands

```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Create finance users
docker-compose exec web python manage.py create_finance_users

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Run Django shell
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web python manage.py test
```

### Development Workflow

```bash
# 1. Make code changes in your editor
# 2. Changes are automatically reflected (volume mounted)
# 3. If you change models, run migrations:
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# 4. If you add new dependencies to requirements.txt:
docker-compose down
docker-compose build
docker-compose up -d
```

## Configuration Files

### .env.local
Local environment variables (already created):
- Database: PostgreSQL in Docker
- Redis: Redis in Docker
- Debug: True
- Allowed Hosts: localhost, 127.0.0.1

### docker-compose.yml
Defines 3 services:
- **web**: Django application (port 8000)
- **db**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)

## Troubleshooting

### Issue 1: Port 8000 already in use

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or use different port in docker-compose.yml
ports:
  - "8001:8000"  # Access at http://localhost:8001
```

### Issue 2: Database connection error

```bash
# Check if db container is running
docker-compose ps

# Restart db container
docker-compose restart db

# Check db logs
docker-compose logs db

# Recreate database
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
```

### Issue 3: Static files not loading

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check static files directory
docker-compose exec web ls -la /app/staticfiles/
```

### Issue 4: Container won't start

```bash
# View logs
docker-compose logs web

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Issue 5: Permission denied errors

```bash
# On Windows, make sure Docker Desktop has access to your drive
# Settings > Resources > File Sharing

# Rebuild with proper permissions
docker-compose down
docker-compose build
docker-compose up -d
```

## Testing Finance App Locally

```bash
# 1. Create finance users
docker-compose exec web python manage.py create_finance_users

# 2. Open browser
http://localhost:8000/finance/login/

# 3. Login with:
Email: saddam110@mushqila.com
Password: Sinan210
User Type: এডমিন

# 4. Should redirect to dashboard without errors
```

## Database Access

### Using Django Shell

```bash
docker-compose exec web python manage.py shell

# In shell:
from accounts.models import User
from finance.models.user import FinanceUser

# List all users
User.objects.all()

# List finance users
FinanceUser.objects.all()
```

### Using PostgreSQL Shell

```bash
# Access PostgreSQL
docker-compose exec db psql -U postgres -d mushqila

# List tables
\dt

# Query users
SELECT email, user_type, is_active FROM accounts_user;

# Exit
\q
```

## Useful Docker Commands

```bash
# Remove all stopped containers
docker-compose down

# Remove containers and volumes (fresh start)
docker-compose down -v

# View container resource usage
docker stats

# Execute bash in web container
docker-compose exec web bash

# View all Docker images
docker images

# Clean up unused Docker resources
docker system prune -a
```

## Development Tips

### 1. Live Reload
Code changes are automatically reflected because of volume mounting:
```yaml
volumes:
  - .:/app  # Your code is mounted
```

### 2. Debug with Print Statements
```python
# In your code
print("DEBUG: Variable value:", variable)

# View in logs
docker-compose logs -f web
```

### 3. Use Django Debug Toolbar (Optional)
```bash
# Install
docker-compose exec web pip install django-debug-toolbar

# Add to settings.py INSTALLED_APPS
'debug_toolbar',

# Add to urls.py
import debug_toolbar
urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
```

### 4. Database Backup
```bash
# Backup database
docker-compose exec db pg_dump -U postgres mushqila > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres mushqila < backup.sql
```

## Environment Comparison

| Feature | Local (.env.local) | Production (.env.production) |
|---------|-------------------|------------------------------|
| DEBUG | True | False |
| Database | Docker PostgreSQL | AWS RDS |
| Static Files | Django serves | Nginx serves |
| HTTPS | No | Yes |
| Domain | localhost:8000 | mushqila.com |

## Next Steps After Local Testing

1. **Test all features locally**
   - Login/Logout
   - Finance app
   - Webmail
   - Admin panel

2. **Run tests**
   ```bash
   docker-compose exec web python manage.py test
   ```

3. **Check for errors**
   ```bash
   docker-compose logs web | grep ERROR
   ```

4. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

5. **GitHub Actions will deploy to production**

## Stop and Clean Up

```bash
# Stop containers (keep data)
docker-compose down

# Stop and remove volumes (fresh start next time)
docker-compose down -v

# Remove all Docker resources
docker system prune -a
```

## Quick Reference

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f web

# Shell
docker-compose exec web python manage.py shell

# Migrations
docker-compose exec web python manage.py migrate

# Superuser
docker-compose exec web python manage.py createsuperuser

# Access
http://localhost:8000
```

---

**Status**: Ready for local development
**Docker Compose**: Configured with web, db, redis
**Environment**: .env.local created
