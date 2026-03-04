# 🔧 Fix EC2 SSH Connection Failed

## ❌ Error
```
Failed to connect to your instance
Error establishing SSH connection to your instance. Try again later.
```

## 🎯 Possible Causes & Solutions

### 1. EC2 Instance Stopped/Terminated
**Check in AWS Console:**
- Go to EC2 Dashboard
- Check instance state (should be "running")
- If stopped, click "Start instance"

### 2. Security Group Rules
**Check SSH Port 22:**
- Go to EC2 → Security Groups
- Find your instance's security group
- Inbound rules should have:
  - Type: SSH
  - Port: 22
  - Source: 0.0.0.0/0 (or your IP)

### 3. Wrong Key Pair
**Verify you're using correct .pem file:**
```bash
# Check if key file exists
ls -la ~/.ssh/*.pem

# Check permissions (should be 400)
chmod 400 ~/.ssh/your-key.pem

# Try connecting manually
ssh -i ~/.ssh/your-key.pem ubuntu@16.170.25.9
```

### 4. Instance IP Changed
**Check current IP:**
- Go to EC2 Dashboard
- Check "Public IPv4 address"
- If changed, update your connection

### 5. Network/Firewall Issues
**Test connectivity:**
```bash
# Ping the server
ping 16.170.25.9

# Test SSH port
telnet 16.170.25.9 22

# OR
nc -zv 16.170.25.9 22
```

### 6. Instance Overloaded (70% Memory)
**Possible causes:**
- Too many Docker containers
- Memory exhausted
- CPU at 100%

**Solution:** Restart instance from AWS Console

## 🚀 Quick Fixes

### Fix 1: Restart EC2 Instance
1. Go to AWS Console → EC2
2. Select your instance
3. Instance State → Reboot instance
4. Wait 2-3 minutes
5. Try connecting again

### Fix 2: Check Security Group
```bash
# From AWS CLI (if installed)
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Should show port 22 open
```

### Fix 3: Connect via AWS Console
1. Go to EC2 Dashboard
2. Select your instance
3. Click "Connect" button
4. Choose "EC2 Instance Connect"
5. Click "Connect" (browser-based terminal)

### Fix 4: Use Different SSH Client
```bash
# Windows (PowerShell)
ssh -i "C:\path\to\key.pem" ubuntu@16.170.25.9

# Windows (PuTTY)
# Convert .pem to .ppk using PuTTYgen first

# Mac/Linux
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9
```

## 🔍 Diagnostic Commands

### Check Instance Status
```bash
# From AWS CLI
aws ec2 describe-instance-status --instance-ids i-xxxxx
```

### Check System Logs
1. Go to EC2 Dashboard
2. Select instance
3. Actions → Monitor and troubleshoot → Get system log

### Check Instance Metrics
1. Go to EC2 Dashboard
2. Select instance
3. Monitoring tab
4. Check CPU, Network, Disk metrics

## 📝 Common Issues

### Issue 1: "Permission denied (publickey)"
**Solution:**
```bash
# Fix key permissions
chmod 400 ~/.ssh/your-key.pem

# Use correct username
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9  # Ubuntu AMI
ssh -i ~/.ssh/key.pem ec2-user@16.170.25.9  # Amazon Linux
```

### Issue 2: "Connection timed out"
**Causes:**
- Security group blocking port 22
- Instance stopped
- Network issue

**Solution:**
- Check security group rules
- Verify instance is running
- Check your internet connection

### Issue 3: "Host key verification failed"
**Solution:**
```bash
# Remove old host key
ssh-keygen -R 16.170.25.9

# Try connecting again
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9
```

## 🌐 Alternative: Use AWS Systems Manager

If SSH completely fails:

1. Go to AWS Console → Systems Manager
2. Session Manager
3. Start session
4. Select your instance
5. Click "Start session"

(No SSH key needed!)

## ✅ After Connecting

Once connected, run these to fix port 80 issue:

```bash
cd ~/mushqila
docker-compose -f docker-compose.prod.yml down -v
sudo systemctl stop nginx 2>/dev/null || true
sudo kill -9 $(sudo lsof -t -i:80) 2>/dev/null || true
docker-compose -f docker-compose.prod.yml up -d --build
```

## 📞 Need Help?

1. **Check AWS Console** - Verify instance is running
2. **Check Security Groups** - Port 22 should be open
3. **Try EC2 Instance Connect** - Browser-based terminal
4. **Restart Instance** - Sometimes fixes connection issues
5. **Check System Logs** - Look for errors

---

**Most Common Fix:** Restart the EC2 instance from AWS Console and wait 2-3 minutes before connecting.
