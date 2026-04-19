# AWS SES Webmail সম্পূর্ণ Setup গাইড

## Overview

এই গাইডে AWS SES ব্যবহার করে প্রতিটি ইমেইল একাউন্টের জন্য আলাদা inbox setup করা হবে। নতুন email account তৈরি হলে automatically SES এ verify এবং S3 এ inbox folder তৈরি হবে।

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS SES Configuration                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Email Sending (SES SMTP/API)                            │
│     user1@mushqila.com ──> SES ──> Recipient                │
│     user2@mushqila.com ──> SES ──> Recipient                │
│                                                               │
│  2. Email Receiving (SES + S3)                              │
│     Sender ──> SES ──> S3 Bucket                            │
│                    │                                          │
│                    └──> SNS/Lambda ──> Django Webhook       │
│                                                               │
│  3. S3 Storage Structure                                     │
│     s3://mushqila-emails/                                    │
│         ├── user1@mushqila.com/                             │
│         │   ├── inbox/                                       │
│         │   ├── sent/                                        │
│         │   └── attachments/                                 │
│         ├── user2@mushqila.com/                             │
│         │   ├── inbox/                                       │
│         │   ├── sent/                                        │
│         │   └── attachments/                                 │
│         └── ...                                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## পূর্বশর্ত (Prerequisites)

1. AWS Account
2. Domain name (যেমন: mushqila.com)
3. Domain এর DNS access
4. AWS CLI installed (optional)

---

## Part 1: AWS SES Initial Setup

### Step 1: AWS SES Account Setup

#### 1.1 AWS Console এ লগিন করুন
- https://console.aws.amazon.com/ses/

#### 1.2 Region Select করুন
- **Recommended**: `us-east-1` (N. Virginia)
- অথবা আপনার কাছের region

#### 1.3 Production Access Request করুন
SES initially "Sandbox Mode" এ থাকে। Production এ যেতে:

1. SES Console > **Account Dashboard**
2. **Request production access** ক্লিক করুন
3. Form পূরণ করুন:
   - **Mail Type**: Transactional
   - **Website URL**: https://mushqila.com
   - **Use Case Description**: 
     ```
     We are building a webmail system for our travel agency. 
     Users will send and receive booking confirmations, 
     customer communications, and business emails.
     ```
   - **Compliance**: Confirm you'll follow AWS policies
4. Submit করুন (approval সাধারণত 24 ঘন্টার মধ্যে আসে)

---

### Step 2: Domain Verification

#### 2.1 Domain Add করুন

1. SES Console > **Verified identities**
2. **Create identity** ক্লিক করুন
3. Select **Domain**
4. Domain name দিন: `mushqila.com`
5. **Assign a default configuration set**: (optional)
6. **Use a custom MAIL FROM domain**: (recommended)
   - MAIL FROM domain: `mail.mushqila.com`
7. **Create identity** ক্লিক করুন

#### 2.2 DNS Records Add করুন

AWS আপনাকে কিছু DNS records দেবে। আপনার domain registrar এ যান এবং এই records add করুন:

**DKIM Records** (3টি CNAME):
```
Name: xxxxx._domainkey.mushqila.com
Type: CNAME
Value: xxxxx.dkim.amazonses.com
```

**SPF Record** (TXT):
```
Name: mushqila.com
Type: TXT
Value: "v=spf1 include:amazonses.com ~all"
```

**DMARC Record** (TXT):
```
Name: _dmarc.mushqila.com
Type: TXT
Value: "v=DMARC1; p=quarantine; rua=mailto:dmarc@mushqila.com"
```

**MX Record** (for receiving):
```
Name: mushqila.com
Type: MX
Priority: 10
Value: inbound-smtp.us-east-1.amazonaws.com
```

**MAIL FROM MX Record**:
```
Name: mail.mushqila.com
Type: MX
Priority: 10
Value: feedback-smtp.us-east-1.amazonses.com
```

**MAIL FROM SPF Record**:
```
Name: mail.mushqila.com
Type: TXT
Value: "v=spf1 include:amazonses.com ~all"
```

#### 2.3 Verification Check করুন

DNS records add করার পর (propagation এ 15 মিনিট - 48 ঘন্টা লাগতে পারে):

1. SES Console > **Verified identities**
2. আপনার domain select করুন
3. **DomainKeys Identified Mail (DKIM)** status check করুন
4. Status **Successful** হলে domain verified

---

### Step 3: Email Receiving Setup

#### 3.1 Receipt Rule Set তৈরি করুন

1. SES Console > **Email receiving** > **Rule sets**
2. **Create rule set** ক্লিক করুন
3. Rule set name: `mushqila-webmail-rules`
4. **Set as active** check করুন
5. Create করুন

#### 3.2 Receipt Rule তৈরি করুন

1. Rule set select করুন
2. **Create rule** ক্লিক করুন
3. **Rule details**:
   - Rule name: `store-all-emails`
   - Status: **Enabled**
4. **Recipient conditions**:
   - Add recipient: `mushqila.com` (সব email receive করবে)
5. **Actions** add করুন:

**Action 1: S3 Action**
- Action type: **Deliver to S3 bucket**
- S3 bucket: `mushqila-emails` (নতুন bucket তৈরি করুন)
- Object key prefix: `incoming/`
- Encrypt message: **Yes** (optional)

**Action 2: SNS Action** (optional, for real-time notifications)
- Action type: **Publish to Amazon SNS topic**
- SNS topic: `webmail-incoming-emails` (নতুন topic তৈরি করুন)

6. **Create rule** ক্লিক করুন

---

## Part 2: S3 Bucket Setup

### Step 4: S3 Bucket তৈরি করুন

#### 4.1 Bucket তৈরি

1. S3 Console > **Create bucket**
2. Bucket name: `mushqila-emails`
3. Region: Same as SES (us-east-1)
4. **Block Public Access**: Keep all checked (private bucket)
5. **Versioning**: Enable (recommended)
6. **Encryption**: Enable (AES-256 or KMS)
7. Create bucket

#### 4.2 Bucket Policy সেট করুন

Bucket select করুন > **Permissions** > **Bucket policy**:

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
            "Resource": "arn:aws:s3:::mushqila-emails/*",
            "Condition": {
                "StringEquals": {
                    "aws:Referer": "YOUR_AWS_ACCOUNT_ID"
                }
            }
        }
    ]
}
```

**Note**: `YOUR_AWS_ACCOUNT_ID` replace করুন আপনার AWS account ID দিয়ে।

#### 4.3 Lifecycle Policy (optional)

Old emails automatically delete করার জন্য:

1. Bucket > **Management** > **Lifecycle rules**
2. **Create lifecycle rule**
3. Rule name: `delete-old-emails`
4. Scope: **Apply to all objects**
5. **Lifecycle rule actions**:
   - Expire current versions: 365 days
   - Delete expired object delete markers: Yes
6. Create rule

---

## Part 3: IAM User & Credentials

### Step 5: IAM User তৈরি করুন

#### 5.1 IAM User Create

1. IAM Console > **Users** > **Add users**
2. User name: `mushqila-webmail-service`
3. Access type: **Programmatic access**
4. Next

#### 5.2 Permissions Attach করুন

**Option 1: Attach existing policies**
- `AmazonSESFullAccess`
- `AmazonS3FullAccess`

**Option 2: Custom policy (recommended)**

Create policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail",
                "ses:VerifyEmailIdentity",
                "ses:DeleteIdentity",
                "ses:GetIdentityVerificationAttributes",
                "ses:ListIdentities"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::mushqila-emails",
                "arn:aws:s3:::mushqila-emails/*"
            ]
        }
    ]
}
```

#### 5.3 Credentials Save করুন

User তৈরি হওয়ার পর:
- **Access Key ID**: AKIAXXXXXXXXXXXXXXXX
- **Secret Access Key**: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

**Important**: এই credentials সুরক্ষিত রাখুন!

---

## Part 4: Django Integration

### Step 6: Environment Variables

`.env` ফাইলে যুক্ত করুন:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1

# S3 Configuration
AWS_S3_BUCKET_NAME=mushqila-emails
AWS_S3_CUSTOM_DOMAIN=mushqila-emails.s3.amazonaws.com

# SES Configuration
AWS_SES_REGION=us-east-1
AWS_SES_CONFIGURATION_SET=mushqila-webmail

# Email Settings
DEFAULT_FROM_EMAIL=noreply@mushqila.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=AKIAXXXXXXXXXXXXXXXX
EMAIL_HOST_PASSWORD=YOUR_SMTP_PASSWORD

# Domain
WEBMAIL_DOMAIN=mushqila.com
```

### Step 7: SMTP Password Generate করুন

SES SMTP password আলাদা:

1. IAM Console > **Users** > `mushqila-webmail-service`
2. **Security credentials** tab
3. **SMTP credentials** section
4. **Create SMTP credentials**
5. Password save করুন

অথবা Python script দিয়ে generate করুন:

```python
import hmac
import hashlib
import base64

def calculate_smtp_password(secret_key, region):
    message = "SendRawEmail"
    version = b'\x02'
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_and_version = version + signature
    smtp_password = base64.b64encode(signature_and_version)
    return smtp_password.decode('utf-8')

# Usage
secret_key = "YOUR_SECRET_ACCESS_KEY"
region = "us-east-1"
smtp_password = calculate_smtp_password(secret_key, region)
print(f"SMTP Password: {smtp_password}")
```

---

## Part 5: Automatic Email Account Setup

### Step 8: Auto-Configuration Service তৈরি করুন

`webmail/services/ses_auto_config.py` তৈরি করুন:

```python
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class SESAutoConfigService:
    """Automatically configure SES for new email accounts"""
    
    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
    
    def verify_email_identity(self, email_address):
        """Verify email address in SES"""
        try:
            response = self.ses_client.verify_email_identity(
                EmailAddress=email_address
            )
            logger.info(f"Verification email sent to {email_address}")
            return {
                'success': True,
                'message': f'Verification email sent to {email_address}'
            }
        except ClientError as e:
            logger.error(f"Error verifying email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_verification_status(self, email_address):
        """Check if email is verified"""
        try:
            response = self.ses_client.get_identity_verification_attributes(
                Identities=[email_address]
            )
            
            attributes = response.get('VerificationAttributes', {})
            status = attributes.get(email_address, {}).get('VerificationStatus', 'NotStarted')
            
            return {
                'success': True,
                'verified': status == 'Success',
                'status': status
            }
        except ClientError as e:
            logger.error(f"Error checking verification: {e}")
            return {
                'success': False,
                'verified': False,
                'error': str(e)
            }
    
    def create_s3_inbox_structure(self, email_address):
        """Create S3 folder structure for email account"""
        bucket_name = settings.AWS_S3_BUCKET_NAME
        
        folders = [
            f"{email_address}/inbox/",
            f"{email_address}/sent/",
            f"{email_address}/drafts/",
            f"{email_address}/trash/",
            f"{email_address}/attachments/"
        ]
        
        try:
            for folder in folders:
                # Create empty object to represent folder
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=folder,
                    Body=b''
                )
            
            logger.info(f"S3 inbox structure created for {email_address}")
            return {
                'success': True,
                'message': f'Inbox structure created for {email_address}'
            }
        except ClientError as e:
            logger.error(f"Error creating S3 structure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def setup_new_email_account(self, email_address):
        """Complete setup for new email account"""
        results = {
            'email': email_address,
            'steps': []
        }
        
        # Step 1: Verify email in SES
        verify_result = self.verify_email_identity(email_address)
        results['steps'].append({
            'step': 'SES Verification',
            'success': verify_result['success'],
            'message': verify_result.get('message') or verify_result.get('error')
        })
        
        # Step 2: Create S3 inbox structure
        s3_result = self.create_s3_inbox_structure(email_address)
        results['steps'].append({
            'step': 'S3 Inbox Creation',
            'success': s3_result['success'],
            'message': s3_result.get('message') or s3_result.get('error')
        })
        
        # Overall success
        results['success'] = all(step['success'] for step in results['steps'])
        
        return results
    
    def delete_email_account_resources(self, email_address):
        """Clean up SES and S3 resources for deleted account"""
        results = {
            'email': email_address,
            'steps': []
        }
        
        # Delete SES identity
        try:
            self.ses_client.delete_identity(Identity=email_address)
            results['steps'].append({
                'step': 'SES Identity Deletion',
                'success': True,
                'message': 'SES identity deleted'
            })
        except ClientError as e:
            results['steps'].append({
                'step': 'SES Identity Deletion',
                'success': False,
                'message': str(e)
            })
        
        # Delete S3 folders (optional - you may want to keep for backup)
        # Implement if needed
        
        results['success'] = all(step['success'] for step in results['steps'])
        return results
```

---

## Part 6: Django Signals for Auto-Setup

### Step 9: Signal তৈরি করুন

`webmail/signals.py` তৈরি বা আপডেট করুন:

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import EmailAccount
from .services.ses_auto_config import SESAutoConfigService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EmailAccount)
def auto_configure_email_account(sender, instance, created, **kwargs):
    """Automatically configure SES and S3 when new email account is created"""
    if created:
        logger.info(f"New email account created: {instance.email_address}")
        
        # Initialize auto-config service
        config_service = SESAutoConfigService()
        
        # Setup email account
        result = config_service.setup_new_email_account(instance.email_address)
        
        if result['success']:
            logger.info(f"Auto-configuration successful for {instance.email_address}")
            
            # Update account with S3 configuration
            instance.s3_bucket_name = config_service.s3_client.meta.config.__dict__.get('_user_provided_options', {}).get('bucket_name', '')
            instance.s3_inbox_prefix = f"{instance.email_address}/inbox/"
            instance.save(update_fields=['s3_bucket_name', 's3_inbox_prefix'])
        else:
            logger.error(f"Auto-configuration failed for {instance.email_address}: {result}")


@receiver(post_delete, sender=EmailAccount)
def cleanup_email_account_resources(sender, instance, **kwargs):
    """Clean up AWS resources when email account is deleted"""
    logger.info(f"Email account deleted: {instance.email_address}")
    
    # Initialize auto-config service
    config_service = SESAutoConfigService()
    
    # Cleanup resources
    result = config_service.delete_email_account_resources(instance.email_address)
    
    if result['success']:
        logger.info(f"Resource cleanup successful for {instance.email_address}")
    else:
        logger.error(f"Resource cleanup failed for {instance.email_address}: {result}")
```

### Step 10: Signals Register করুন

`webmail/apps.py` আপডেট করুন:

```python
from django.apps import AppConfig


class WebmailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webmail'
    
    def ready(self):
        import webmail.signals  # Import signals
```

`webmail/__init__.py` এ যুক্ত করুন:

```python
default_app_config = 'webmail.apps.WebmailConfig'
```

---

## Part 7: Management Commands

### Step 11: Verification Command

`webmail/management/commands/verify_email_accounts.py`:

```python
from django.core.management.base import BaseCommand
from webmail.models import EmailAccount
from webmail.services.ses_auto_config import SESAutoConfigService


class Command(BaseCommand):
    help = 'Check verification status of all email accounts'
    
    def handle(self, *args, **options):
        config_service = SESAutoConfigService()
        accounts = EmailAccount.objects.all()
        
        self.stdout.write(f"Checking {accounts.count()} email accounts...")
        self.stdout.write("=" * 60)
        
        for account in accounts:
            result = config_service.check_verification_status(account.email_address)
            
            if result['success']:
                status = "✓ VERIFIED" if result['verified'] else "✗ NOT VERIFIED"
                self.stdout.write(f"{account.email_address}: {status}")
                
                # Update database
                if result['verified'] and not account.ses_verified:
                    account.ses_verified = True
                    account.save(update_fields=['ses_verified'])
                    self.stdout.write(self.style.SUCCESS(f"  → Updated database"))
            else:
                self.stdout.write(self.style.ERROR(f"{account.email_address}: ERROR - {result.get('error')}"))
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Verification check complete!"))
```

### Step 12: Bulk Setup Command

`webmail/management/commands/setup_all_email_accounts.py`:

```python
from django.core.management.base import BaseCommand
from webmail.models import EmailAccount
from webmail.services.ses_auto_config import SESAutoConfigService


class Command(BaseCommand):
    help = 'Setup SES and S3 for all existing email accounts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if already configured'
        )
    
    def handle(self, *args, **options):
        config_service = SESAutoConfigService()
        accounts = EmailAccount.objects.all()
        force = options.get('force', False)
        
        self.stdout.write(f"Setting up {accounts.count()} email accounts...")
        self.stdout.write("=" * 60)
        
        for account in accounts:
            if account.ses_verified and not force:
                self.stdout.write(f"⊘ {account.email_address}: Already configured (use --force to reconfigure)")
                continue
            
            self.stdout.write(f"⚙ Setting up {account.email_address}...")
            
            result = config_service.setup_new_email_account(account.email_address)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f"✓ {account.email_address}: Setup complete"))
                for step in result['steps']:
                    status = "✓" if step['success'] else "✗"
                    self.stdout.write(f"  {status} {step['step']}: {step['message']}")
            else:
                self.stdout.write(self.style.ERROR(f"✗ {account.email_address}: Setup failed"))
                for step in result['steps']:
                    if not step['success']:
                        self.stdout.write(f"  ✗ {step['step']}: {step['message']}")
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Setup complete!"))
```

---

## Part 8: Testing

### Step 13: Test করুন

#### Test 1: নতুন Email Account তৈরি

```bash
python manage.py create_webmail_account \
  --email test@mushqila.com \
  --password TestPass123 \
  --first-name "Test" \
  --last-name "User" \
  --alternate-email "your-personal@gmail.com"
```

Check করুন:
1. SES Console এ email verification pending দেখাবে
2. S3 bucket এ folder structure তৈরি হয়েছে
3. Verification email পেয়েছেন

#### Test 2: Verification Status Check

```bash
python manage.py verify_email_accounts
```

#### Test 3: Email Send Test

Django shell:
```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from Mushqila Webmail.',
    'test@mushqila.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

#### Test 4: Email Receive Test

1. অন্য email থেকে `test@mushqila.com` এ email পাঠান
2. S3 bucket check করুন: `incoming/` folder এ email আসবে
3. Django এ email fetch করুন

---

## Summary

এই setup এর পর:

✅ Domain verified in SES
✅ Email sending configured
✅ Email receiving configured (SES → S3)
✅ S3 bucket with proper structure
✅ IAM user with proper permissions
✅ Automatic email account setup
✅ Automatic S3 inbox creation
✅ Signal-based automation
✅ Management commands for bulk operations

নতুন email account তৈরি হলে automatically:
1. SES এ verification email যাবে
2. S3 এ inbox folder structure তৈরি হবে
3. Database এ configuration save হবে

পরবর্তী ধাপ: Email receiving webhook এবং real-time email fetching implement করা।
