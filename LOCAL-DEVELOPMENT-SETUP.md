# 🖥️ Local Development Setup

## Prerequisites

### Windows এ Install করুন:

1. **Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop/
   - Install করুন এবং restart করুন
   - Docker Desktop চালু করুন

2. **Git** (যদি না থাকে)
   - Download: https://git-scm.com/download/win
   - Install করুন

---

## Setup Steps

### 1. Repository Clone করুন

```bash
# Command Prompt বা PowerShell এ
cd C:\Users\user\Desktop
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila
```

### 2. Environment File তৈরি করুন

`.env` file তৈরি করুন (development এর জন্য):

```bash
# PowerShell এ
notepad .env
```

এই content paste করুন:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-for-development-only
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Local PostgreSQL বা SQLite)
# Option 1: SQLite (সহজ)
DATABASE_URL=sqlite:///db.sqlite3

# Option 2: PostgreSQL (যদি local PostgreSQL থাকে)
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=mushqila_dev
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432

# Redis (Docker container থেকে)
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email (Development - Console backend)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Static/Media
STATIC_URL=/static/
MEDIA_URL=/media/
```

Save করুন (Ctrl+S, then close)

### 3. Docker Compose File (Development)

`docker-compose.yml` file check করুন বা তৈরি করুন:

```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: mushqila_dev_web
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - redis
    networks:
      - mushqila_network

  redis:
    image: redis:7-alpine
    container_name: mushqila_dev_redis
    ports:
      - "6379:6379"
    networks:
      - mushqila_network

  celery:
    build: .
    container_name: mushqila_dev_celery
    command: celery -A config worker -l info
    env_file:
      - .env
    volumes:
      - .:/app
    depends_on:
      - redis
      - web
    networks:
      - mushqila_network

  celery-beat:
    build: .
    container_name: mushqila_dev_celery_beat
    command: celery -A config beat -l info
    env_file:
      - .env
    volumes:
      - .:/app
    depends_on:
      - redis
      - web
    networks:
      - mushqila_network

volumes:
  static_volume:
  media_volume:

networks:
  mushqila_network:
    driver: bridge
```

### 4. Containers Build এবং Start করুন

```bash
# Docker Desktop চালু আছে কিনা check করুন

# Containers build করুন
docker-compose build

# Containers start করুন
docker-compose up -d

# Status check করুন
docker-compose ps
```

### 5. Database Migrate করুন

```bash
# Migrations run করুন
docker-compose exec web python manage.py migrate

# Static files collect করুন
docker-compose exec web python manage.py collectstatic --noinput

# Superuser তৈরি করুন
docker-compose exec web python manage.py createsuperuser

# Chart of accounts initialize করুন
docker-compose exec web python manage.py initialize_accounts
```

### 6. Application Access করুন

Browser এ খুলুন:
- **Main Site:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin

---

## Quick Commands

```bash
# Containers start করুন
docker-compose up -d

# Containers stop করুন
docker-compose down

# Logs দেখুন
docker-compose logs -f web

# Container এ shell access
docker-compose exec web bash

# Database shell
docker-compose exec web python manage.py dbshell

# Django shell
docker-compose exec web python manage.py shell

# Migrations তৈরি করুন
docker-compose exec web python manage.py makemigrations

# Migrations run করুন
docker-compose exec web python manage.py migrate

# Tests run করুন
docker-compose exec web python manage.py test

# Containers rebuild করুন
docker-compose up -d --build
```

---

## Troubleshooting

### Docker Desktop চালু নেই?
- Windows Start Menu → Docker Desktop
- Wait for "Docker Desktop is running"

### Port 8000 already in use?
```bash
# Port change করুন docker-compose.yml এ
ports:
  - "8001:8000"  # 8001 ব্যবহার করুন
```

### Database connection error?
- `.env` file check করুন
- SQLite ব্যবহার করুন (সহজ)

### Static files loading না?
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Container build error?
```bash
# Clean build করুন
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## Development Workflow

### Code Change করার পর:

1. **Python code change:**
   - Django auto-reload করবে
   - কিছু করতে হবে না

2. **Model change:**
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

3. **Static files change:**
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

4. **Requirements change:**
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

---

## VS Code Setup (Optional)

### Extensions Install করুন:
- Python
- Django
- Docker
- Remote - Containers

### Settings:
1. Open folder: `mushqila`
2. Select Python interpreter: Docker container
3. Debug configuration তৈরি করুন

---

## Production vs Development

| Feature | Development | Production |
|---------|-------------|------------|
| DEBUG | True | False |
| Database | SQLite/Local PG | RDS PostgreSQL |
| Server | runserver | Gunicorn |
| Port | 8000 | 80 |
| HTTPS | No | Yes (Certbot) |
| Domain | localhost | mushqila.com |
| Volumes | Code mounted | No mount |

---

## Next Steps

1. ✅ Local environment setup
2. ✅ Containers running
3. ✅ Database migrated
4. ✅ Superuser created
5. ⏳ Start development
6. ⏳ Test features
7. ⏳ Push to GitHub
8. ⏳ Deploy to EC2

---

**Local URL:** http://localhost:8000  
**Admin:** http://localhost:8000/admin  
**Status:** Development Environment
