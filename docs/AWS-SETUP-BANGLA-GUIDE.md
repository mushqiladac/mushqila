# 🚀 AWS SES Email Setup - সম্পূর্ণ বাংলা গাইড

## 📧 Email Addresses যা তৈরি হবে:
1. shahin_sarker@mushqila.com
2. aysha@mushqila.com
3. refat@mushqila.com
4. support@mushqila.com
5. eliuss@mushqila.com

---

## Part 1: AWS Console Setup (30 মিনিট)

### Step 1: AWS Console এ Login করো

1. যাও: https://console.aws.amazon.com/
2. তোমার AWS account দিয়ে login করো
3. **Region select করো**: Top-right corner থেকে **US East (N. Virginia)** select করো
   - ⚠️ Important: Email receiving শুধু us-east-1 region এ কাজ করে

---

### Step 2: Domain Verify করো (SES)

#### 2.1 SES Console খোলো
1. Services → Search করো "SES" → **Amazon Simple Email Service** click করো
2. Left sidebar → **Verified identities** click করো
3. **Create identity** button click করো

#### 2.2 Domain Add করো
```
Identity type: Domain (select করো)
Domain: mushqila.com
Advanced DKIM settings: Easy DKIM - RSA_2048_BIT (default রাখো)
```
4. **Create identity** button click করো

#### 2.3 DNS Records Copy করো
SES তোমাকে কিছু DNS records দেখাবে। এগুলো copy করে রাখো:

**তিন ধরনের records পাবে:**
1. **DKIM Records** (3টা CNAME record)
2. **MX Record** (Email receiving এর জন্য)
3. **Verification Record** (1টা CNAME)

---

### Step 3: Route 53 এ DNS Records Add করো

#### 3.1 Route 53 Console খোলো
1. Services → Search করো "Route 53"
2. Left sidebar → **Hosted zones** click করো
3. **mushqila.com** click করো

#### 3.2 DKIM Records Add করো (3টা)
SES থেকে যে 3টা CNAME record পেয়েছো, প্রতিটার জন্য:

1. **Create record** button click করো
2. Fill করো:
   ```
   Record type: CNAME
   Record name: [SES থেকে copy করা name - যেমন: abc123._domainkey]
   Value: [SES থেকে copy করা value]
   TTL: 300
   ```
3. **Create records** click করো
4. এভাবে 3টা CNAME record add করো

#### 3.3 MX Record Add করো (Email Receiving)
1. **Create record** button click করো
2. Fill করো:
   ```
   Record type: MX
   Record name: mushqila.com (blank রাখতে পারো)
   Value: 10 inbound-smtp.us-east-1.amazonaws.com
   TTL: 300
   ```
3. **Create records** click করো

#### 3.4 SPF Record Add করো (Optional but recommended)
1. **Create record** button click করো
2. Fill করো:
   ```
   Record type: TXT
   Record name: mushqila.com (blank রাখো)
   Value: "v=spf1 include:amazonses.com ~all"
   TTL: 300
   ```
3. **Create records** click করো

#### 3.5 DMARC Record Add করো (Optional)
1. **Create record** button click করো
2. Fill করো:
   ```
   Record type: TXT
   Record name: _dmarc
   Value: "v=DMARC1; p=quarantine; rua=mailto:support@mushqila.com"
   TTL: 300
   ```
3. **Create records** click করো

⏰ **Wait করো**: DNS records propagate হতে 10-30 মিনিট লাগতে পারে

---

### Step 4: Domain Verification Check করো

#### 4.1 SES Console এ ফিরে যাও
1. Services → SES
2. **Verified identities** → **mushqila.com** click করো

#### 4.2 Status Check করো
- **Identity status**: Verified (green) দেখাবে
- **DKIM status**: Successful (green) দেখাবে
- যদি Pending দেখায়, আরো 10-15 মিনিট wait করো

---

### Step 5: S3 Bucket তৈরি করো (Email Storage)

#### 5.1 S3 Console খোলো
1. Services → Search করো "S3"
2. **Create bucket** button click করো

#### 5.2 Bucket Configure করো
```
Bucket name: mushqila-incoming-emails
Region: US East (N. Virginia) us-east-1
Block all public access: ✓ Checked (keep it private)
Bucket Versioning: Disabled
```
3. **Create bucket** click করো

#### 5.3 Bucket Policy Add করো
1. তোমার bucket select করো → **Permissions** tab
2. Scroll down → **Bucket policy** → **Edit** click করো
3. এই policy paste করো:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSESPuts",
            "Effect": "Allow",
            "Principal": {
                "Service": "ses.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::mushqila-incoming-emails/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceAccount": "YOUR_AWS_ACCOUNT_ID"
                }
            }
        }
    ]
}
```

4. **YOUR_AWS_ACCOUNT_ID** replace করো:
   - Top-right corner এ তোমার name click করো
   - Account ID copy করো (12 digit number)
   - Policy তে paste করো

5. **Save changes** click করো

---

### Step 6: SES Receipt Rule তৈরি করো

#### 6.1 Rule Set তৈরি করো
1. SES Console → Left sidebar → **Email receiving** → **Rule sets**
2. যদি কোনো rule set না থাকে:
   - **Create rule set** click করো
   - Name: `mushqila-rules`
   - **Create rule set** click করো
3. Rule set select করো → **Set as active** click করো

#### 6.2 Receipt Rule তৈরি করো
1. **Create rule** button click করো
2. **Rule name**: `receive-all-emails`

#### 6.3 Recipients Add করো
```
Add recipient condition:
- shahin_sarker@mushqila.com
- aysha@mushqila.com
- refat@mushqila.com
- support@mushqila.com
- eliuss@mushqila.com
```
অথবা blank রাখো (সব emails receive করবে)

#### 6.4 Actions Add করো

**Action 1: S3**
1. **Add new action** → **Deliver to S3 bucket**
2. Configure:
   ```
   S3 bucket: mushqila-incoming-emails
   Object key prefix: incoming/ (optional)
   Encrypt message: Yes (recommended)
   SNS Topic: None (for now)
   ```
3. **Next** click করো

#### 6.5 Rule Review & Create
1. Review করো সব settings
2. **Create rule** click করো

✅ **Done!** AWS setup complete!

---

## Part 2: Django App Setup (10 মিনিট)

### Step 1: Environment Variables Update করো

#### Local (.env)
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_SES_REGION=us-east-1

# Email Receiving
AWS_SES_RECEIVING_REGION=us-east-1
AWS_S3_INCOMING_BUCKET=mushqila-incoming-emails
```

#### Production (.env.production) - EC2 তে
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_SES_REGION=us-east-1

# Email Receiving
AWS_SES_RECEIVING_REGION=us-east-1
AWS_S3_INCOMING_BUCKET=mushqila-incoming-emails
```

⚠️ **AWS Credentials কোথায় পাবে?**
1. AWS Console → Top-right → Security credentials
2. **Access keys** section → **Create access key**
3. Copy করো: Access Key ID এবং Secret Access Key

---

### Step 2: Email Accounts তৈরি করো

#### Local Development:
```bash
python manage.py create_email_accounts
```

#### Production (EC2):
```bash
ssh -i your-key.pem ubuntu@16.170.25.9
cd ~/mushqila
docker-compose -f docker-compose.prod.yml exec web python manage.py create_email_accounts
```

**Output দেখবে:**
```
======================================================================
Creating 5 Email Accounts for Mushqila Team
======================================================================

✓ Created user: shahin_sarker
  ✓ Created email account: shahin_sarker@mushqila.com
    Username: shahin_sarker
    Password: Shahin@Mushqila2026
    Email: shahin_sarker@mushqila.com

✓ Created user: aysha
  ✓ Created email account: aysha@mushqila.com
    Username: aysha
    Password: Aysha@Mushqila2026
    Email: aysha@mushqila.com

... (বাকি 3টা)
```

---

## Part 3: Testing (5 মিনিট)

### Test 1: Login Test

1. Visit: https://mushqila.com/webmail/login/
2. Login করো:
   ```
   Username: shahin_sarker
   Password: Shahin@Mushqila2026
   ```
3. Successfully login হলে inbox দেখবে

### Test 2: Send Email Test

1. Gmail/Yahoo থেকে email পাঠাও:
   ```
   To: shahin_sarker@mushqila.com
   Subject: Test Email
   Body: This is a test email to check receiving
   ```

### Test 3: Check S3 Bucket

1. AWS Console → S3 → mushqila-incoming-emails
2. `incoming/` folder এ email file দেখতে পাবে

### Test 4: Fetch Email to Django

```bash
# EC2 তে run করো
docker-compose -f docker-compose.prod.yml exec web python manage.py fetch_incoming_emails
```

**Output:**
```
Fetching incoming emails from S3...
✓ Successfully fetched 1 new email(s)
  - Test Email from sender@gmail.com
```

### Test 5: Check Webmail Inbox

1. Refresh webmail inbox
2. Email দেখতে পাবে!

---

## Part 4: Auto-Fetch Setup (Celery)

### Celery Beat Schedule (Already configured)

File: `config/settings.py`

```python
CELERY_BEAT_SCHEDULE = {
    'fetch-incoming-emails': {
        'task': 'webmail.tasks.fetch_incoming_emails',
        'schedule': 300.0,  # Every 5 minutes
    },
}
```

### Verify Celery is Running

```bash
# Check celery containers
docker-compose -f docker-compose.prod.yml ps

# Should see:
# mushqila_celery        Running
# mushqila_celery_beat   Running
```

### Check Celery Logs

```bash
# Celery worker logs
docker-compose -f docker-compose.prod.yml logs -f celery

# Celery beat logs
docker-compose -f docker-compose.prod.yml logs -f celery-beat
```

---

## 📋 Complete Checklist

### AWS Setup
- [ ] AWS Console এ login করেছো
- [ ] Region: US East (N. Virginia) select করেছো
- [ ] SES এ domain verify করেছো
- [ ] Route 53 এ DNS records add করেছো
- [ ] Domain verification successful
- [ ] S3 bucket তৈরি করেছো
- [ ] Bucket policy add করেছো
- [ ] SES receipt rule তৈরি করেছো
- [ ] AWS credentials copy করেছো

### Django Setup
- [ ] .env.production update করেছো
- [ ] Email accounts তৈরি করেছো
- [ ] Login test করেছো
- [ ] Password change করেছো

### Email Testing
- [ ] Test email পাঠিয়েছো
- [ ] S3 এ email দেখেছো
- [ ] Fetch command run করেছো
- [ ] Inbox এ email দেখেছো
- [ ] Celery running verify করেছো

---

## 🎯 Login Credentials

| Email | Username | Default Password |
|-------|----------|------------------|
| shahin_sarker@mushqila.com | shahin_sarker | Shahin@Mushqila2026 |
| aysha@mushqila.com | aysha | Aysha@Mushqila2026 |
| refat@mushqila.com | refat | Refat@Mushqila2026 |
| support@mushqila.com | support | Support@Mushqila2026 |
| eliuss@mushqila.com | eliuss | Eliuss@Mushqila2026 |

⚠️ **প্রথম login এর পর password change করো!**

---

## 🔧 Troubleshooting

### Problem 1: Domain verification pending
**Solution:** 
- DNS records properly add করেছো কিনা check করো
- 30 মিনিট wait করো
- Route 53 → Records check করো

### Problem 2: Email S3 তে আসছে না
**Solution:**
- MX record correctly add করেছো কিনা check করো
- Receipt rule active আছে কিনা check করো
- Test email সঠিক address এ পাঠিয়েছো কিনা check করো

### Problem 3: Fetch command কাজ করছে না
**Solution:**
```bash
# Check AWS credentials
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> import boto3
>>> s3 = boto3.client('s3')
>>> s3.list_buckets()
```

### Problem 4: Login করতে পারছি না
**Solution:**
```bash
# Reset password
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(username='shahin_sarker')
>>> user.set_password('Shahin@Mushqila2026')
>>> user.save()
```

---

## 📞 Support Commands

### Useful Commands

```bash
# Create email accounts
python manage.py create_email_accounts

# Fetch emails manually
python manage.py fetch_incoming_emails

# Check Django logs
docker-compose -f docker-compose.prod.yml logs -f web

# Check Celery logs
docker-compose -f docker-compose.prod.yml logs -f celery

# Django shell
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# List S3 bucket contents
aws s3 ls s3://mushqila-incoming-emails/incoming/
```

---

## 🎉 Summary

✅ **Setup Complete হলে:**
- 5টা email address কাজ করবে
- প্রতিটা আলাদা login credentials
- Email send/receive করতে পারবে
- Auto-fetch every 5 minutes
- Professional webmail interface

✅ **Total Time:** ~45 minutes
- AWS Setup: 30 min
- Django Setup: 10 min
- Testing: 5 min

✅ **Cost:** FREE (AWS Free Tier)
- SES: First 62,000 emails/month free
- S3: First 5GB free
- Data transfer: Minimal

---

**এখন শুরু করো! AWS Console এ যাও এবং Step 1 থেকে follow করো।** 🚀

**কোনো সমস্যা হলে troubleshooting section দেখো অথবা জানাও!**
