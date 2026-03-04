# 🔧 Fix Port 80 Already in Use Error

## ❌ Error
```
Error response from daemon: failed to bind host port for 0.0.0.0:80:172.18.0.3:8000/tcp: address already in use
```

## 🎯 Solution

Port 80 already in use by old container or nginx. Run these commands:

### Step 1: Stop All Containers
```bash
cd ~/mushqila
docker-compose -f docker-compose.prod.yml down -v
```

### Step 2: Find What's Using Port 80
```bash
sudo lsof -i :80
```

### Step 3: Kill Process Using Port 80
```bash
# If nginx is using it
sudo systemctl stop nginx

# OR if it's a docker container
sudo docker ps -a | grep 80
sudo docker stop <container_id>
sudo docker rm <container_id>

# OR kill the process directly
sudo kill -9 $(sudo lsof -t -i:80)
```

### Step 4: Verify Port is Free
```bash
sudo lsof -i :80
# Should return nothing
```

### Step 5: Start Fresh
```bash
cd ~/mushqila
docker-compose -f docker-compose.prod.yml up -d --build
```

### Step 6: Check Status
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs --tail=50 web
```

### Step 7: Test
```bash
curl http://localhost:8000/webmail/
curl http://localhost/webmail/
```

## 🚀 Quick Fix (One Command)

```bash
cd ~/mushqila && \
docker-compose -f docker-compose.prod.yml down -v && \
sudo systemctl stop nginx 2>/dev/null || true && \
sudo kill -9 $(sudo lsof -t -i:80) 2>/dev/null || true && \
sleep 2 && \
docker-compose -f docker-compose.prod.yml up -d --build && \
sleep 30 && \
docker-compose -f docker-compose.prod.yml ps && \
curl http://localhost/webmail/
```

## 📝 Alternative: Use Different Port

If you want to keep nginx running, edit `docker-compose.prod.yml`:

```yaml
services:
  web:
    ports:
      - "8080:8000"  # Change from 80:8000 to 8080:8000
```

Then access at: http://16.170.25.9:8080/webmail/

## ✅ Expected Result

After fixing:
- Port 80 should be free
- Containers should start successfully
- Webmail accessible at http://16.170.25.9/webmail/
