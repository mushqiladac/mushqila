# Start Docker - Quick Guide

## Docker Desktop is Not Running

Docker Desktop needs to be started before running containers.

## Steps to Start Docker

### 1. Start Docker Desktop
- Open Docker Desktop application from Windows Start Menu
- Wait for Docker to fully start (whale icon in system tray should be steady)
- You'll see "Docker Desktop is running" notification

### 2. Verify Docker is Running
```bash
docker ps
```

If Docker is running, you'll see a list of containers (or empty list if no containers are running).

### 3. Start Your Containers
Once Docker Desktop is running, use:

```bash
docker-compose up -d
```

Or to rebuild and start:

```bash
docker-compose up -d --build
```

## Quick Commands

### Start Docker Containers
```bash
docker-compose up -d
```

### Check Running Containers
```bash
docker ps
```

### View Logs
```bash
docker logs mushqila-web-1 --tail 50
```

### Stop Containers
```bash
docker-compose down
```

### Restart Containers
```bash
docker-compose restart
```

## After Starting Docker

Once Docker Desktop is running and containers are started:
- Your application will be available at: http://localhost:8000
- PostgreSQL database will be available at: localhost:5432

## Troubleshooting

### If Docker Desktop won't start:
1. Check if virtualization is enabled in BIOS
2. Restart your computer
3. Reinstall Docker Desktop if needed

### If containers won't start:
1. Check Docker Desktop logs
2. Run: `docker-compose logs`
3. Check for port conflicts (8000, 5432)

---

**Current Status**: Docker Desktop is not running
**Action Required**: Start Docker Desktop application
