# Quick EC2 Deployment Guide

## Step 1: Connect to EC2

```bash
ssh -i "your-key.pem" ubuntu@your-ec2-ip
```

## Step 2: Navigate to Project

```bash
cd /home/ubuntu/sinan
```

## Step 3: Pull Latest Code

```bash
git pull origin dwd
```

## Step 4: Deploy

```bash
# Stop containers
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## Step 5: Check Status

```bash
# Check containers
docker-compose ps

# View logs
docker-compose logs -f web
```

## Quick One-Line Deploy

```bash
cd /home/ubuntu/sinan && git pull origin dwd && docker-compose down && docker-compose up -d --build && docker-compose exec web python manage.py migrate && docker-compose exec web python manage.py collectstatic --noinput
```

## Troubleshooting

### If containers won't start:
```bash
docker-compose logs web
docker-compose logs db
```

### If port is busy:
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Reset everything:
```bash
docker-compose down -v
docker-compose up -d --build
```

## Access Your Site

- HTTP: `http://your-ec2-ip:8000`
- Admin: `http://your-ec2-ip:8000/admin`
- Landing: `http://your-ec2-ip:8000/accounts/landing/`
