# ⚡ Quick Fix: HTTP Access Issue

## 🔴 সমস্যা
```
http://13.60.112.227 কাজ করছে না
```

## ✅ সমাধান (5 মিনিট)

### 1️⃣ AWS Console এ যান
```
https://eu-north-1.console.aws.amazon.com/ec2/home?region=eu-north-1#Instances:
```

### 2️⃣ Instance খুঁজুন
- Instance ID: **i-0c70ddd0a58bb4dcf**
- Public IP: **13.60.112.227**

### 3️⃣ Security Group খুলুন
1. Instance ক্লিক করুন
2. নিচে **Security** tab
3. Security group link ক্লিক করুন

### 4️⃣ Rules যোগ করুন
1. **Inbound rules** tab
2. **Edit inbound rules**
3. **Add rule** → Type: **HTTP**, Source: **Anywhere-IPv4**
4. **Add rule** → Type: **HTTPS**, Source: **Anywhere-IPv4**
5. **Save rules**

### 5️⃣ Test করুন
```
http://13.60.112.227
```

---

## 🎯 Expected Rules

| Type | Port | Source | Description |
|------|------|--------|-------------|
| SSH | 22 | 0.0.0.0/0 | SSH access |
| HTTP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | 443 | 0.0.0.0/0 | Secure web |

---

## 🔄 Alternative: Port 8000 Test

যদি Security Group access না থাকে:

```bash
# EC2 Instance Connect
cd ~/mushqila
nano docker-compose.prod.yml

# Change: "80:8000" to "8000:8000"
# Save: Ctrl+O, Enter, Ctrl+X

docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Test: http://13.60.112.227:8000
```

---

## 📞 Need Help?

**Full Guide:** `AWS-SECURITY-GROUP-SETUP.md`  
**Troubleshooting:** `TROUBLESHOOTING-HTTP-ACCESS.md`

---

**Status:** Containers Running ✅  
**Issue:** Security Group ⏳  
**ETA:** 5 minutes ⚡
