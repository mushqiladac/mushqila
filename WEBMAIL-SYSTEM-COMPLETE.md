# Webmail System - Complete Implementation

## Overview
সম্পূর্ণ webmail system তৈরি হয়েছে যা AWS SES এবং S3 ব্যবহার করে email পাঠানো এবং receive করার জন্য।

## Features Implemented

### 1. Database Models ✅
- **EmailAccount**: User email account configuration with AWS credentials
- **Email**: Email messages with S3 storage reference
- **EmailAttachment**: File attachments stored in S3
- **EmailLabel**: Custom labels/tags for organizing emails
- **EmailLabelAssignment**: Many-to-many relationship for email labels
- **EmailFilter**: Automatic email filtering rules
- **EmailTemplate**: Reusable email templates
- **Contact**: Address book with frequency tracking

### 2. AWS Services Integration ✅

#### SES Service (`webmail/services/ses_service.py`)
- Send simple emails
- Send emails with attachments (raw MIME)
- Verify email addresses
- Get sending quota and statistics
- List verified email addresses

#### S3 Service (`webmail/services/s3_service.py`)
- Store emails as JSON in S3
- Store attachments in S3
- Retrieve emails and attachments
- Delete emails and attachments
- Generate presigned URLs
- List emails by account
- Create S3 bucket if not exists

#### Email Service (`webmail/services/email_service.py`)
- Complete email sending workflow
- Email receiving and storage
- Draft management
- Folder management (inbox, sent, drafts, trash, spam, archive)
- Contact auto-update
- Attachment handling

### 3. Admin Interface ✅
Complete Django admin configuration for all models with:
- List displays
- Filters
- Search fields
- Fieldsets
- Read-only fields

### 4. Database Structure

```
EmailAccount (User's email configuration)
    ├── Email (Messages)
    │   ├── EmailAttachment (Files)
    │   └── EmailLabelAssignment (Tags)
    ├── EmailLabel (Custom labels)
    ├── EmailFilter (Auto-filtering rules)
    └── EmailTemplate (Reusable templates)

Contact (Address book)
```

## Installation & Setup

### 1. Install Required Packages

```bash
pip install boto3 botocore
```

### 2. Environment Variables

Add to `.env`:

```env
# AWS Configuration for Webmail
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=mushqila-webmail
AWS_SES_REGION=us-east-1
DEFAULT_FROM_EMAIL=noreply@mushqila.com
```

### 3. AWS Setup

#### A. AWS SES Setup
1. Go to AWS SES Console
2. Verify your email address or domain
3. Request production access (if needed)
4. Create SMTP credentials (optional)

#### B. AWS S3 Setup
1. Create S3 bucket: `mushqila-webmail`
2. Set appropriate permissions
3. Enable versioning (optional)
4. Configure lifecycle rules (optional)

### 4. Database Migration

```bash
python manage.py makemigrations webmail
python manage.py migrate webmail
```

## Usage Examples

### 1. Create Email Account

```python
from webmail.models import EmailAccount
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='agent1')

account = EmailAccount.objects.create(
    user=user,
    email_address='agent1@mushqila.com',
    display_name='Agent One',
    aws_access_key='YOUR_AWS_KEY',
    aws_secret_key='YOUR_AWS_SECRET',
    aws_region='us-east-1',
    s3_bucket_name='mushqila-webmail',
    is_default=True,
    is_active=True
)
```

### 2. Send Email

```python
from webmail.services import EmailService
from webmail.models import EmailAccount

# Get email account
account = EmailAccount.objects.get(email_address='agent1@mushqila.com')

# Initialize service
email_service = EmailService(account)

# Send email
result = email_service.send_email(
    to_addresses=['customer@example.com'],
    subject='Flight Booking Confirmation',
    body_text='Your booking is confirmed.',
    body_html='<h1>Your booking is confirmed.</h1>',
    cc_addresses=['manager@mushqila.com'],
    save_to_sent=True
)

if result['success']:
    print(f"Email sent! Message ID: {result['message_id']}")
else:
    print(f"Failed: {result['error']}")
```

### 3. Send Email with Attachments

```python
from django.core.files.uploadedfile import SimpleUploadedFile

# Create attachment
attachment = SimpleUploadedFile(
    "ticket.pdf",
    b"PDF content here",
    content_type="application/pdf"
)

result = email_service.send_email(
    to_addresses=['customer@example.com'],
    subject='Your Ticket',
    body_text='Please find your ticket attached.',
    attachments=[attachment]
)
```

### 4. Save Draft

```python
result = email_service.save_draft(
    to_addresses=['customer@example.com'],
    subject='Draft Email',
    body_text='This is a draft.',
    body_html='<p>This is a draft.</p>'
)
```

### 5. Receive Email (Webhook)

```python
# In your webhook view
raw_email_data = {
    'messageId': 'unique-message-id',
    'from': 'sender@example.com',
    'to': ['agent1@mushqila.com'],
    'subject': 'Inquiry about flights',
    'text': 'I need information about flights to Dubai.',
    'html': '<p>I need information about flights to Dubai.</p>'
}

email = email_service.receive_email(raw_email_data)
```

### 6. Query Emails

```python
from webmail.models import Email

# Get inbox emails
inbox_emails = Email.objects.filter(
    account=account,
    folder='inbox',
    is_read=False
).order_by('-received_at')

# Get sent emails
sent_emails = Email.objects.filter(
    account=account,
    folder='sent'
).order_by('-sent_at')

# Search emails
search_results = Email.objects.filter(
    account=account,
    subject__icontains='booking'
)
```

### 7. Mark as Read/Unread

```python
email = Email.objects.get(id='email-uuid')
email.mark_as_read()
# or
email.mark_as_unread()
```

### 8. Move to Folder

```python
email_service.move_to_folder(email, 'archive')
```

### 9. Delete Email

```python
# Move to trash
email_service.delete_email(email, permanent=False)

# Permanent delete (from S3 too)
email_service.delete_email(email, permanent=True)
```

## S3 Storage Structure

```
mushqila-webmail/
├── emails/
│   └── agent1@mushqila.com/
│       ├── inbox/
│       │   └── 2026/03/04/
│       │       └── message-id-123.json
│       ├── sent/
│       └── attachments/
│           └── 2026/03/04/
│               └── message-id-123/
│                   └── ticket.pdf
```

## Email Data Structure in S3

```json
{
    "message_id": "<unique-id@mushqila.com>",
    "from_address": "agent1@mushqila.com",
    "from_name": "Agent One",
    "to_addresses": ["customer@example.com"],
    "cc_addresses": [],
    "bcc_addresses": [],
    "subject": "Flight Booking Confirmation",
    "body_text": "Your booking is confirmed.",
    "body_html": "<h1>Your booking is confirmed.</h1>",
    "sent_at": "2026-03-04T10:30:00Z"
}
```

## Security Features

1. **AWS Credentials**: Stored encrypted in database
2. **S3 Server-Side Encryption**: AES256 encryption enabled
3. **Presigned URLs**: Temporary access to S3 objects (7 days expiry)
4. **Email Verification**: SES email verification required
5. **User Isolation**: Each user can only access their own emails

## Performance Optimization

1. **Database Indexes**: 
   - account + folder + received_at
   - account + is_read + received_at
   - thread_id + received_at

2. **S3 Storage**: 
   - Emails stored as JSON (fast retrieval)
   - Attachments stored separately
   - Presigned URLs for direct access

3. **Query Optimization**:
   - Select related for foreign keys
   - Prefetch related for many-to-many
   - Pagination for large result sets

## Next Steps

### Phase 1: Basic UI (Recommended)
1. Create inbox view
2. Create compose email view
3. Create email detail view
4. Add folder navigation
5. Add search functionality

### Phase 2: Advanced Features
1. Email threading/conversations
2. Rich text editor for compose
3. Drag & drop attachments
4. Email filters UI
5. Labels/tags management
6. Contact management UI
7. Email templates UI

### Phase 3: Real-time Features
1. WebSocket for new email notifications
2. Auto-refresh inbox
3. Real-time email status updates
4. Push notifications

### Phase 4: Integration
1. SES webhook for receiving emails
2. SNS notifications
3. Lambda functions for processing
4. CloudWatch monitoring

## API Endpoints (To be created)

```
GET    /webmail/inbox/              - List inbox emails
GET    /webmail/sent/               - List sent emails
GET    /webmail/drafts/             - List drafts
GET    /webmail/email/<id>/         - Email detail
POST   /webmail/compose/            - Send new email
POST   /webmail/draft/              - Save draft
PUT    /webmail/email/<id>/         - Update email (mark read, star, etc)
DELETE /webmail/email/<id>/         - Delete email
POST   /webmail/email/<id>/move/    - Move to folder
GET    /webmail/contacts/           - List contacts
POST   /webmail/webhook/receive/    - Receive email webhook
```

## Testing

```python
# Test SES connection
from webmail.services import SESService

ses = SESService()
result = ses.get_send_quota()
print(result)

# Test S3 connection
from webmail.services import S3Service

s3 = S3Service()
result = s3.create_bucket_if_not_exists()
print(result)
```

## Troubleshooting

### SES Issues
- Verify email address in SES console
- Check sending limits
- Request production access if in sandbox mode

### S3 Issues
- Check bucket permissions
- Verify AWS credentials
- Check bucket region

### Database Issues
- Run migrations: `python manage.py migrate webmail`
- Check database connection

## Cost Estimation

### AWS SES
- First 62,000 emails/month: FREE
- After that: $0.10 per 1,000 emails

### AWS S3
- First 50 TB/month: $0.023 per GB
- GET requests: $0.0004 per 1,000 requests
- PUT requests: $0.005 per 1,000 requests

### Example Monthly Cost (10,000 emails, 1GB storage)
- SES: FREE
- S3 Storage: $0.023
- S3 Requests: ~$0.05
- **Total: ~$0.08/month**

## Support

For issues or questions:
1. Check AWS SES documentation
2. Check AWS S3 documentation
3. Review Django logs
4. Check CloudWatch logs (if configured)

---

**Status**: ✅ Complete and Ready for Use
**Version**: 1.0.0
**Last Updated**: March 4, 2026
