# AWS SES Webmail Quick Start (বাংলা)

## দ্রুত শুরু করার জন্য স্টেপ

### ১. AWS Credentials সংগ্রহ করুন

AWS Console থেকে:
1. IAM > Users > Create user
2. User name: `mushqila-webmail`
3. Programmatic access select করুন
4. Permissions: `AmazonSESFullAccess` + `AmazonS3FullAccess`
5. Access Key ID এবং Secret Access Key save করুন

### ২. .env ফাইল আপডেট করুন

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1

# S3 Configuration
AWS_S3_BUCKET_NAME=mushqila-emails

# SES Configuration
AWS_SES_REGION=us-east-1

# Email Settings
DEFAULT_FROM_EMAIL=noreply@mushqila.com
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=AKIAXXXXXXXXXXXXXXXX
EMAIL_HOST_PASSWORD=YOUR_SMTP_PASSWORD

# Webmail Domain
WEBMAIL_DOMAIN=mushqila.com

# Site URL
SITE_URL=https://mushqila.com
```

### ৩. S3 Bucket তৈরি করুন

AWS S3 Console এ:
1. Create bucket: `mushqila-emails`
2. Region: `us-east-1` (same as SES)
3. Block public access: Keep enabled
4. Versioning: Enable (recommended)
5. Encryption: Enable

### ৪. Domain Verify করুন

SES Console এ:
1. Verified identities > Create identity
2. Domain: `mushqila.com`
3. DNS records copy করুন
4. আপনার domain registrar এ DNS records add করুন:
   - 3টি DKIM CNAME records
   - 1টি MX record
   - 1টি SPF TXT record
   - 1টি DMARC TXT record

### ৫. Email Receiving Setup করুন

SES Console > Email receiving:
1. Create rule set: `mushqila-webmail-rules`
2. Set as active
3. Create rule:
   - Recipient: `mushqila.com`
   - Action: S3 (bucket: `mushqila-emails`, prefix: `incoming/`)

### ৬. Django Setup

#### Migration চালান:
```bash
python manage.py migrate webmail
```

#### Existing accounts setup করুন:
```bash
python manage.py setup_all_email_accounts
```

#### Verification status check করুন:
```bash
python manage.py verify_email_accounts
```

### ৭. নতুন Email Account তৈরি করুন

#### Admin Panel থেকে:
1. `/admin/` এ যান
2. Webmail > Email accounts > Add
3. সব তথ্য পূরণ করুন
4. Save করুন
5. Automatically SES এ verification email যাবে

#### Command Line থেকে:
```bash
python manage.py create_webmail_account \
  --email user@mushqila.com \
  --password SecurePass123 \
  --first-name "User" \
  --last-name "Name" \
  --alternate-email "user@gmail.com"
```

### ৮. Email Verify করুন

1. User এর email check করুন
2. AWS verification link এ click করুন
3. Verification status check করুন:
```bash
python manage.py verify_email_accounts --email user@mushqila.com
```

### ৯. Test করুন

#### Email Send Test:
```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test.',
    'user@mushqila.com',
    ['recipient@example.com'],
)
```

#### Email Receive Test:
1. অন্য email থেকে `user@mushqila.com` এ email পাঠান
2. S3 bucket check করুন: `incoming/` folder
3. Webmail inbox check করুন

---

## Automatic Features

### নতুন Email Account তৈরি হলে Automatically:

✅ SES এ verification email পাঠানো হয়
✅ S3 এ inbox folder structure তৈরি হয়:
   - `user@mushqila.com/inbox/`
   - `user@mushqila.com/sent/`
   - `user@mushqila.com/drafts/`
   - `user@mushqila.com/trash/`
   - `user@mushqila.com/attachments/`
✅ Database এ S3 configuration save হয়

### Email Account Delete হলে Automatically:

✅ SES থেকে identity remove হয়
✅ S3 folders preserve থাকে (backup এর জন্য)

---

## Troubleshooting

### Problem: Email verification email আসছে না

**Solution:**
1. Spam folder check করুন
2. SES sandbox mode থেকে production mode এ যান
3. AWS account verification complete করুন

### Problem: S3 folder তৈরি হচ্ছে না

**Solution:**
1. AWS credentials check করুন
2. IAM permissions check করুন (S3 PutObject)
3. Bucket name সঠিক আছে কিনা check করুন

### Problem: Email send হচ্ছে না

**Solution:**
1. Email verified কিনা check করুন
2. SES sending limits check করুন
3. SMTP credentials সঠিক আছে কিনা check করুন

### Problem: Email receive হচ্ছে না

**Solution:**
1. MX records সঠিকভাবে configured আছে কিনা check করুন
2. SES receipt rule active আছে কিনা check করুন
3. S3 bucket permissions check করুন

---

## Important Commands

```bash
# নতুন email account তৈরি
python manage.py create_webmail_account --email user@mushqila.com --password Pass123

# সব accounts setup করুন
python manage.py setup_all_email_accounts

# Verification status check
python manage.py verify_email_accounts

# Specific email verify check
python manage.py verify_email_accounts --email user@mushqila.com

# Force reconfigure
python manage.py setup_all_email_accounts --force

# Existing accounts এ default password set
python manage.py set_default_passwords
```

---

## Production Checklist

✅ AWS SES production access approved
✅ Domain verified in SES
✅ DNS records configured (DKIM, SPF, DMARC, MX)
✅ S3 bucket created and configured
✅ IAM user created with proper permissions
✅ Email receiving rule set configured
✅ Django settings configured
✅ Migrations applied
✅ Test email sent successfully
✅ Test email received successfully
✅ SSL/TLS enabled for webmail
✅ Backup strategy in place

---

## Cost Estimation

### AWS SES:
- First 62,000 emails/month: FREE (if sent from EC2)
- After that: $0.10 per 1,000 emails

### AWS S3:
- First 5 GB storage: FREE
- After that: $0.023 per GB/month
- Data transfer: First 100 GB/month FREE

### Example:
- 10,000 emails/month
- 1 GB storage
- Cost: ~$0 (within free tier)

---

## Security Best Practices

1. ✅ AWS credentials কখনো git এ commit করবেন না
2. ✅ .env ফাইল .gitignore এ রাখুন
3. ✅ IAM user এ minimum required permissions দিন
4. ✅ S3 bucket public access block করুন
5. ✅ Email encryption enable করুন
6. ✅ Regular backup নিন
7. ✅ CloudWatch monitoring enable করুন
8. ✅ Rate limiting implement করুন

---

## Next Steps

1. Email receiving webhook implement করুন
2. Real-time email notification setup করুন
3. Email search functionality improve করুন
4. Attachment handling optimize করুন
5. Email templates তৈরি করুন
6. Spam filtering implement করুন
7. Email analytics add করুন

---

## Support

সমস্যা হলে:
1. Django logs check করুন
2. AWS CloudWatch logs check করুন
3. Management commands দিয়ে debug করুন
4. Documentation পড়ুন: `AWS-SES-WEBMAIL-COMPLETE-SETUP.md`
