# AWS SES Email Receiving Setup - mushqila.com

## Overview
AWS SES দিয়ে `exam@mushqila.com`, `info@mushqila.com` ইত্যাদি email address এ email receive করা যাবে। এটা সম্পূর্ণ free (AWS এর মধ্যেই included)।

---

## ⚠️ Important Note
AWS SES Email Receiving শুধুমাত্র **US East (N. Virginia) - us-east-1** region এ available। তোমার current setup **eu-north-1** তে আছে, তাই receiving এর জন্য us-east-1 use করতে হবে।

---

## Step 1: AWS SES Email Receiving Enable করো

### 1.1 AWS Console এ যাও
- Region: **US East (N. Virginia)** select করো (top-right corner)
- Service: **Amazon SES** খুলো

### 1.2 Verify Domain
1. Left sidebar → **Verified identities** → **Create identity**
2. Identity type: **Domain**
3. Domain: `mushqila.com`
4. Advanced DKIM settings: **Easy DKIM** (recommended)
5. **Create identity** click করো

### 1.3 DNS Records Add করো
SES তোমাকে কিছু DNS records দেবে:

**Route 53 এ যাও:**
1. Services → **Route 53** → **Hosted zones**
2. `mushqila.com` select করো
3. **Create record** click করো

**Add these records:**

#### MX Record (Email Receiving)
```
Type: MX
Name: mushqila.com (or leave blank)
Value: 10 inbound-smtp.us-east-1.amazonaws.com
TTL: 300
```

#### DKIM Records (3টা CNAME record SES দেবে)
```
Type: CNAME
Name: [SES থেকে copy করো]
Value: [SES থেকে copy করো]
TTL: 300
```

#### SPF Record
```
Type: TXT
Name: mushqila.com
Value: "v=spf1 include:amazonses.com ~all"
TTL: 300
```

#### DMARC Record (Optional but recommended)
```
Type: TXT
Name: _dmarc.mushqila.com
Value: "v=DMARC1; p=quarantine; rua=mailto:dmarc@mushqila.com"
TTL: 300
```

---

## Step 2: S3 Bucket তৈরি করো (Email Storage)

### 2.1 S3 Bucket Create
1. Services → **S3** → **Create bucket**
2. Bucket name: `mushqila-incoming-emails`
3. Region: **US East (N. Virginia)**
4. Block all public access: **Enabled** (keep it private)
5. **Create bucket**

### 2.2 Bucket Policy Add করো
Bucket select করো → **Permissions** tab → **Bucket policy** → Edit

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

**Note:** `YOUR_AWS_ACCOUNT_ID` replace করো তোমার AWS Account ID দিয়ে (top-right corner এ পাবে)

---

## Step 3: SES Receipt Rule তৈরি করো

### 3.1 Rule Set Create
1. SES Console → Left sidebar → **Email receiving** → **Rule sets**
2. **Create rule set** (if not exists)
3. Rule set name: `mushqila-incoming-rules`
4. **Set as active rule set**

### 3.2 Receipt Rule Create
1. Rule set select করো → **Create rule**
2. Rule name: `store-all-emails`

**Recipients:**
- Add: `exam@mushqila.com`
- Add: `info@mushqila.com`
- Add: `support@mushqila.com`
- Or leave empty to receive all emails to any address

**Actions:**
1. **Add action** → **S3**
   - S3 bucket: `mushqila-incoming-emails`
   - Object key prefix: `incoming/` (optional)
   - Encrypt message: **Yes** (recommended)

2. **Add action** → **SNS** (Optional - for notifications)
   - Create SNS topic: `ses-email-received`
   - This will notify your app when email arrives

3. **Create rule**

---

## Step 4: Django App Update করো

### 4.1 Install boto3 (if not installed)
```bash
pip install boto3
```

### 4.2 Update .env.production
```env
# AWS SES Receiving (US East)
AWS_SES_RECEIVING_REGION=us-east-1
AWS_S3_INCOMING_BUCKET=mushqila-incoming-emails
AWS_SNS_EMAIL_TOPIC_ARN=arn:aws:sns:us-east-1:ACCOUNT_ID:ses-email-received
```

### 4.3 Create Email Fetching Service
File: `webmail/services/ses_receiving_service.py`

```python
import boto3
import email
from email import policy
from django.conf import settings
from webmail.models import Email, EmailAccount

class SESReceivingService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_SES_RECEIVING_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket = settings.AWS_S3_INCOMING_BUCKET
    
    def fetch_new_emails(self):
        """Fetch new emails from S3"""
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket,
            Prefix='incoming/'
        )
        
        if 'Contents' not in response:
            return []
        
        new_emails = []
        for obj in response['Contents']:
            email_key = obj['Key']
            
            # Download email from S3
            email_obj = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=email_key
            )
            
            # Parse email
            raw_email = email_obj['Body'].read()
            msg = email.message_from_bytes(raw_email, policy=policy.default)
            
            # Extract email details
            email_data = {
                'message_id': msg.get('Message-ID'),
                'from_address': msg.get('From'),
                'to_addresses': msg.get('To'),
                'subject': msg.get('Subject'),
                'date': msg.get('Date'),
                'body_text': self._get_body(msg, 'plain'),
                'body_html': self._get_body(msg, 'html'),
            }
            
            # Save to database
            self._save_email(email_data)
            new_emails.append(email_data)
            
            # Delete from S3 after processing
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=email_key
            )
        
        return new_emails
    
    def _get_body(self, msg, content_type):
        """Extract email body"""
        for part in msg.walk():
            if part.get_content_type() == f'text/{content_type}':
                return part.get_payload(decode=True).decode()
        return ''
    
    def _save_email(self, email_data):
        """Save email to database"""
        # Find recipient's account
        to_address = email_data['to_addresses'].split(',')[0].strip()
        account = EmailAccount.objects.filter(
            email_address__icontains=to_address
        ).first()
        
        if account:
            Email.objects.create(
                account=account,
                message_id=email_data['message_id'],
                from_address=email_data['from_address'],
                to_addresses=email_data['to_addresses'],
                subject=email_data['subject'],
                body_text=email_data['body_text'],
                body_html=email_data['body_html'],
                folder='inbox',
                is_read=False
            )
```

### 4.4 Create Management Command
File: `webmail/management/commands/fetch_incoming_emails.py`

```python
from django.core.management.base import BaseCommand
from webmail.services.ses_receiving_service import SESReceivingService

class Command(BaseCommand):
    help = 'Fetch incoming emails from AWS SES/S3'

    def handle(self, *args, **options):
        service = SESReceivingService()
        emails = service.fetch_new_emails()
        
        self.stdout.write(
            self.style.SUCCESS(f'Fetched {len(emails)} new emails')
        )
```

### 4.5 Setup Cron Job (Auto-fetch every 5 minutes)
Add to `config/settings.py`:

```python
# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'fetch-incoming-emails': {
        'task': 'webmail.tasks.fetch_incoming_emails',
        'schedule': 300.0,  # Every 5 minutes
    },
}
```

Create `webmail/tasks.py`:

```python
from celery import shared_task
from webmail.services.ses_receiving_service import SESReceivingService

@shared_task
def fetch_incoming_emails():
    service = SESReceivingService()
    emails = service.fetch_new_emails()
    return f'Fetched {len(emails)} emails'
```

---

## Step 5: Test Email Receiving

### 5.1 Send Test Email
Gmail/Yahoo থেকে email পাঠাও:
```
To: exam@mushqila.com
Subject: Test Email
Body: This is a test email
```

### 5.2 Check S3 Bucket
1. S3 Console → `mushqila-incoming-emails` bucket
2. `incoming/` folder এ email file দেখতে পাবে

### 5.3 Fetch Email to Django
```bash
# EC2 তে run করো
docker-compose -f docker-compose.prod.yml exec web python manage.py fetch_incoming_emails
```

### 5.4 Check Webmail
- Login: https://mushqila.com/webmail/login/
- Inbox এ email দেখতে পাবে

---

## Summary

✅ **What you get:**
- `exam@mushqila.com` এ email receive করতে পারবে
- `info@mushqila.com`, `support@mushqila.com` যেকোনো address তৈরি করতে পারবে
- S3 তে emails store হবে
- Django webmail app থেকে read করতে পারবে
- Completely free (AWS free tier এর মধ্যে)

✅ **Cost:**
- SES Receiving: Free
- S3 Storage: ~$0.023/GB/month (প্রথম 5GB free)
- Data Transfer: Minimal

---

## Next Steps

1. AWS Console এ যাও এবং Step 1-3 complete করো
2. DNS records add করো Route 53 এ
3. Test email পাঠাও
4. Django code update করো (Step 4)
5. Deploy to EC2

**Need help with any step?** Let me know! 🚀
