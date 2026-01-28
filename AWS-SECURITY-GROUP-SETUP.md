# 🔐 AWS Security Group Setup - Step by Step

## 🎯 লক্ষ্য
EC2 instance এ HTTP (port 80) এবং HTTPS (port 443) traffic allow করা

---

## 📍 Step 1: AWS Console এ Login করুন

1. খুলুন: https://console.aws.amazon.com/
2. Login করুন
3. উপরে ডানদিকে Region চেক করুন: **eu-north-1 (Stockholm)**

---

## 📍 Step 2: EC2 Dashboard এ যান

1. উপরে Search box এ লিখুন: **EC2**
2. **EC2** service এ ক্লিক করুন
3. অথবা সরাসরি: https://eu-north-1.console.aws.amazon.com/ec2/home?region=eu-north-1

---

## 📍 Step 3: Instance খুঁজুন

1. বাম sidebar এ **Instances** ক্লিক করুন
2. Instance list এ খুঁজুন:
   - **Instance ID:** i-0c70ddd0a58bb4dcf
   - **Name:** mhcl (যদি থাকে)
   - **Public IP:** 13.60.112.227

3. Instance এর **নামে** ক্লিক করুন (checkbox নয়)

---

## 📍 Step 4: Security Group খুলুন

Instance details page এ:

1. নিচে scroll করুন
2. **Security** tab খুঁজুন এবং ক্লিক করুন
3. **Security groups** section দেখবেন
4. Security group এর নাম দেখবেন (যেমন: **launch-wizard-1** বা **sg-xxxxx**)
5. সেই **নামে ক্লিক** করুন (নীল রঙের link)

---

## 📍 Step 5: Inbound Rules Edit করুন

Security Group page এ:

1. নিচে **Inbound rules** tab ক্লিক করুন
2. বর্তমান rules দেখবেন (সম্ভবত শুধু SSH - port 22)
3. **Edit inbound rules** বাটন ক্লিক করুন (উপরে ডানদিকে)

---

## 📍 Step 6: HTTP Rule যোগ করুন

Edit inbound rules page এ:

1. **Add rule** বাটন ক্লিক করুন

2. নতুন rule এ fill করুন:
   ```
   Type: HTTP
   Protocol: TCP (auto-filled)
   Port range: 80 (auto-filled)
   Source: Custom → 0.0.0.0/0
   Description: Allow HTTP traffic
   ```

3. **Source** এ ক্লিক করলে dropdown দেখবেন:
   - **Anywhere-IPv4** সিলেক্ট করুন
   - এটি automatically `0.0.0.0/0` set করবে

---

## 📍 Step 7: HTTPS Rule যোগ করুন

1. আবার **Add rule** বাটন ক্লিক করুন

2. নতুন rule এ fill করুন:
   ```
   Type: HTTPS
   Protocol: TCP (auto-filled)
   Port range: 443 (auto-filled)
   Source: Custom → 0.0.0.0/0
   Description: Allow HTTPS traffic
   ```

3. **Source** এ **Anywhere-IPv4** সিলেক্ট করুন

---

## 📍 Step 8: Rules Save করুন

1. নিচে scroll করুন
2. **Save rules** বাটন ক্লিক করুন (কমলা রঙের)
3. Success message দেখবেন

---

## 📍 Step 9: Verify Rules

Security Group page এ ফিরে আসবেন।

**Inbound rules** tab এ এখন দেখবেন:

| Type | Protocol | Port range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | 0.0.0.0/0 | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Allow HTTP traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Allow HTTPS traffic |

---

## 📍 Step 10: Test করুন

### Browser এ test করুন:
```
http://13.60.112.227
```

**Expected Result:**
- Application load হবে
- Login/Register page দেখবেন
- অথবা landing page দেখবেন

### যদি কাজ না করে:

1. **Browser cache clear করুন:**
   - Chrome/Edge: `Ctrl+Shift+Delete`
   - Clear cached images and files
   - Close and reopen browser

2. **Incognito mode try করুন:**
   - Chrome/Edge: `Ctrl+Shift+N`

3. **Different browser try করুন**

4. **Containers check করুন:**
   ```bash
   # EC2 Instance Connect দিয়ে
   cd ~/mushqila
   docker-compose -f docker-compose.prod.yml ps
   ```

---

## 🔍 Troubleshooting

### Security Group খুঁজে পাচ্ছি না?

**Method 1: Instance থেকে**
1. EC2 → Instances
2. Instance select করুন
3. নিচে **Security** tab
4. Security group link ক্লিক করুন

**Method 2: Direct**
1. EC2 Dashboard
2. বাম sidebar → **Security Groups**
3. List থেকে খুঁজুন

### Rules save হচ্ছে না?

**Check করুন:**
- আপনার AWS account এ permission আছে কিনা
- Region সঠিক আছে কিনা (eu-north-1)
- Browser console এ error আছে কিনা

### Application এখনও load হচ্ছে না?

**Check করুন:**

1. **Containers running:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. **Web logs:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs web | tail -50
   ```

3. **Port listening:**
   ```bash
   sudo netstat -tlnp | grep :80
   ```

4. **Restart containers:**
   ```bash
   docker-compose -f docker-compose.prod.yml restart
   ```

---

## 📱 Alternative: AWS CLI Method

যদি CLI configured থাকে:

```bash
# Security Group ID বের করুন
SG_ID=$(aws ec2 describe-instances \
  --instance-ids i-0c70ddd0a58bb4dcf \
  --region eu-north-1 \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

echo "Security Group ID: $SG_ID"

# HTTP rule যোগ করুন
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region eu-north-1

# HTTPS rule যোগ করুন
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region eu-north-1

# Verify
aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --region eu-north-1 \
  --query 'SecurityGroups[0].IpPermissions'
```

---

## ✅ Success Indicators

### ১. Security Group Rules
- ✅ HTTP (port 80) rule added
- ✅ HTTPS (port 443) rule added
- ✅ Source: 0.0.0.0/0 (Anywhere)

### ২. Application Access
- ✅ http://13.60.112.227 loads
- ✅ No "connection refused" error
- ✅ No "site can't be reached" error

### ৩. Containers Status
- ✅ All containers running
- ✅ Web logs show "Listening at: http://0.0.0.0:8000"
- ✅ No error messages

---

## 🎯 পরবর্তী Steps

Security Group setup complete হলে:

1. ✅ **Superuser তৈরি করুন:**
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   ```

2. ✅ **Admin panel access করুন:**
   ```
   http://13.60.112.227/admin
   ```

3. ✅ **Chart of accounts initialize করুন:**
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py initialize_accounts
   ```

4. ⏳ **Domain setup করুন:**
   - Namecheap DNS configure
   - ALLOWED_HOSTS update
   - DNS propagation wait

5. ⏳ **SSL setup করুন:**
   - Nginx install
   - Certbot setup
   - HTTPS enable

---

## 📚 Related Guides

- `TROUBLESHOOTING-HTTP-ACCESS.md` - HTTP access issues
- `DOMAIN-SETUP-GUIDE.md` - Domain configuration
- `DEPLOYMENT-COMPLETE-SUMMARY.md` - Full deployment overview

---

**Instance:** i-0c70ddd0a58bb4dcf  
**IP:** 13.60.112.227  
**Region:** eu-north-1  
**Task:** Security Group Configuration  
**Priority:** HIGH 🔴

