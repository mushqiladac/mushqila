# ⚡ Quick Setup Reference - Mushqila Webmail

## 🎯 5 Email Addresses
1. shahin_sarker@mushqila.com
2. aysha@mushqila.com
3. refat@mushqila.com
4. support@mushqila.com
5. eliuss@mushqila.com

---

## 📝 Quick Steps

### 1️⃣ AWS Console (30 min)
```
1. Login → AWS Console
2. Region → US East (N. Virginia)
3. SES → Verify Domain → mushqila.com
4. Route 53 → Add DNS Records (DKIM, MX, SPF)
5. S3 → Create Bucket → mushqila-incoming-emails
6. SES → Create Receipt Rule → Save to S3
```

### 2️⃣ EC2 Setup (5 min)
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9
cd ~/mushqila

# Update .env.production
nano .env.production
# Add:
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret
# AWS_S3_INCOMING_BUCKET=mushqila-incoming-emails

# Create email accounts
docker-compose -f docker-compose.prod.yml exec web python manage.py create_email_accounts
```

### 3️⃣ Test (5 min)
```
1. Login: https://mushqila.com/webmail/login/
2. Username: shahin_sarker
3. Password: Shahin@Mushqila2026
4. Send test email from Gmail
5. Run: python manage.py fetch_incoming_emails
6. Check inbox!
```

---

## 🔑 Default Passwords

| Username | Password |
|----------|----------|
| shahin_sarker | Shahin@Mushqila2026 |
| aysha | Aysha@Mushqila2026 |
| refat | Refat@Mushqila2026 |
| support | Support@Mushqila2026 |
| eliuss | Eliuss@Mushqila2026 |

⚠️ Change after first login!

---

## 📋 DNS Records to Add (Route 53)

### MX Record
```
Type: MX
Name: mushqila.com
Value: 10 inbound-smtp.us-east-1.amazonaws.com
TTL: 300
```

### SPF Record
```
Type: TXT
Name: mushqila.com
Value: "v=spf1 include:amazonses.com ~all"
TTL: 300
```

### DKIM Records (3টা - SES থেকে copy করো)
```
Type: CNAME
Name: [from SES]
Value: [from SES]
TTL: 300
```

---

## 🛠️ Useful Commands

```bash
# Create accounts
python manage.py create_email_accounts

# Fetch emails
python manage.py fetch_incoming_emails

# Check logs
docker-compose -f docker-compose.prod.yml logs -f web

# Django shell
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
```

---

## 📚 Full Guides

- **Detailed AWS Setup**: `AWS-SETUP-BANGLA-GUIDE.md`
- **Technical Details**: `AWS-SES-EMAIL-RECEIVING-SETUP.md`
- **Complete Documentation**: `WEBMAIL-SETUP-COMPLETE.md`

---

## ✅ Checklist

- [ ] AWS SES domain verified
- [ ] DNS records added
- [ ] S3 bucket created
- [ ] Receipt rule created
- [ ] .env.production updated
- [ ] Email accounts created
- [ ] Login tested
- [ ] Email receiving tested

---

**Total Time: ~40 minutes | Cost: FREE** 🚀
