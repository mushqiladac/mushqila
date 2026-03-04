# 🔧 EC2 Connection Refused - Fix Guide

## ❌ Error
```
ERR_CONNECTION_REFUSED
16.170.25.9 refused to connect
```

## 🎯 Possible Causes

### 1. EC2 Instance Stopped
**Most Common Cause**

### 2. Docker Containers Not Running

### 3. Security Group Port Blocked

### 4. Instance Terminated

## ✅ Solutions

### Solution 1: Start EC2 Instance (Most Likely)

**Via AWS Console:**
1. Go to: https://console.aws.amazon.com/ec2/
2. Click "Instances" in left sidebar
3. Find your instance (IP: 16.170.25.9)
4. Check "Instance state"
   - If "Stopped" → Select instance → Instance State → Start instance
   - If "Running" → Go to Solution 2

**Wait 2-3 minutes after starting**

### Solution 2: Check Docker Containers

**If instance is running but site not accessible:**

```bash
# SSH to EC2
ssh -i ~/.ssh/your-key.pem ubuntu@16.170.25.9

# Check if Docker is running
docker ps

# If no containers, start them
cd ~/mushqila
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web
```

### Solution 3: Check Security Group

**Via AWS Console:**
1. Go to EC2 → Instances
2. Select your instance
3. Click "Security" tab
4. Check "Security groups"
5. Click on security group name
6. Check "Inbound rules"

**Required Rules:**
- Type: HTTP, Port: 80, Source: 0.0.0.0/0
- Type: HTTPS, Port: 443, Source: 0.0.0.0/0
- Type: SSH, Port: 22, Source: 0.0.0.0/0
- Type: Custom TCP, Port: 8000, Source: 0.0.0.0/0

### Solution 4: Check Instance Status

**Via AWS Console:**
1. EC2 → Instances
2. Select instance
3. Check "Status checks"
   - Should show: 2/2 checks passed
   - If failing → Instance has issues

**Check System Log:**
1. Select instance
2. Actions → Monitor and troubleshoot → Get system log
3. Look for errors

## 🚀 Quick Fix Commands

### If you can SSH:

```bash
# 1. SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# 2. Check Docker
docker ps

# 3. If no containers running
cd ~/mushqila
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 4. Wait and test
sleep 30
curl http://localhost/

# 5. Check logs if still not working
docker-compose -f docker-compose.prod.yml logs --tail=100 web
```

### If you cannot SSH:

**Instance is likely stopped. Start it from AWS Console.**

## 🔍 Diagnostic Steps

### Step 1: Check Instance State
```bash
# From your local machine
ping 16.170.25.9

# If no response → Instance stopped or security group blocking ICMP
```

### Step 2: Try SSH
```bash
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# If "Connection refused" → Instance stopped
# If "Connection timeout" → Security group blocking SSH
# If "Permission denied" → Wrong key or username
```

### Step 3: Check from AWS Console
- Instance State: Should be "Running"
- Status Checks: Should be "2/2 checks passed"
- Public IP: Should be 16.170.25.9

## 📊 Common Scenarios

### Scenario 1: Instance Stopped
**Symptoms:**
- Connection refused
- Cannot SSH
- Cannot ping

**Fix:**
1. AWS Console → EC2 → Instances
2. Select instance → Instance State → Start instance
3. Wait 2-3 minutes
4. Try accessing again

### Scenario 2: Docker Not Running
**Symptoms:**
- Can SSH
- But website not accessible
- `docker ps` shows no containers

**Fix:**
```bash
cd ~/mushqila
docker-compose -f docker-compose.prod.yml up -d
```

### Scenario 3: Port 80 Issue
**Symptoms:**
- Can SSH
- Docker running
- But port 80 not accessible

**Fix:**
```bash
# Check what's using port 80
sudo lsof -i :80

# If nginx blocking
sudo systemctl stop nginx

# Restart Docker
docker-compose -f docker-compose.prod.yml restart web
```

### Scenario 4: Out of Memory
**Symptoms:**
- Instance running but slow
- Containers keep restarting
- SSH very slow

**Fix:**
```bash
# Check memory
free -h

# Clean Docker
docker system prune -af --volumes

# Restart containers
cd ~/mushqila
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## 🌐 After Fix - Test URLs

Once fixed, test these:
- Main: http://16.170.25.9/
- Landing: http://16.170.25.9/accounts/landing/
- Landing2: http://16.170.25.9/landing2/
- Admin: http://16.170.25.9/admin/
- Webmail: http://16.170.25.9/webmail/

## 💡 Prevention

### Auto-Start on Reboot
```bash
# SSH to EC2
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# Create systemd service
sudo nano /etc/systemd/system/mushqila.service

# Add this content:
[Unit]
Description=Mushqila Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/mushqila
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target

# Enable service
sudo systemctl enable mushqila.service
sudo systemctl start mushqila.service
```

## 📞 Need Help?

1. **Check AWS Console** - Is instance running?
2. **Try SSH** - Can you connect?
3. **Check Docker** - Are containers running?
4. **Check Logs** - Any errors?
5. **Restart Everything** - Last resort

---

**Most Common Fix:** Start the EC2 instance from AWS Console!
