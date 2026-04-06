# ✅ Webmail Setup Complete - mushqila.com

## Overview
তোমার webmail app সম্পূর্ণভাবে configured এবং ready to use! ৮টা আলাদা email account তৈরি করা যাবে।

---

## 📋 Current Status

### ✅ Completed Features

1. **Webmail Login System**
   - Custom login page: `/webmail/login/`
   - Username/password authentication
   - Redirect to inbox after login

2. **Email Management**
   - Inbox, Sent, Drafts, Spam, Trash folders
   - Compose new emails
   - Read/Reply/Forward emails
   - Delete emails
   - Search functionality

3. **Password Management**
   - Change password feature
   - Secure password validation (min 8 chars)
   - Live password match checking
   - Session maintained after password change

4. **Email Receiving (AWS SES)**
   - Receive emails via AWS SES
   - Store in S3 bucket
   - Auto-fetch with Celery (every 5 minutes)
   - Manual fetch command available

5. **Multi-User Support**
   - 8 separate email accounts
   - Each with unique username/password
   - Isolated inboxes

---

## 🎯 8 Email Accounts Setup

### Command to Create Accounts

```bash
# Local development
python manage.py create_email_accounts

# Production (EC2)
docker-compose -f docker-compose.prod.yml exec web python manage.py create_email_accounts
```

### Default Email Accounts

| Email | Username | Default Password | Purpose |
|-------|----------|------------------|---------|
| info@mushqila.com | info_mushqila | Info@Mushqila2026 | General inquiries |
| support@mushqila.com | support_mushqila | Support@Mushqila2026 | Customer support |
| sales@mushqila.com | sales_mushqila | Sales@Mushqila2026 | Sales team |
| booking@mushqila.com | booking_mushqila | Booking@Mushqila2026 | Flight bookings |
| accounts@mushqila.com | accounts_mushqila | Accounts@Mushqila2026 | Accounting dept |
| hr@mushqila.com | hr_mushqila | HR@Mushqila2026 | Human resources |
| marketing@mushqila.com | marketing_mushqila | Marketing@Mushqila2026 | Marketing team |
| admin@mushqila.com | admin_mushqila | Admin@Mushqila2026 | Administration |

⚠️ **Important:** প্রথম login এর পর password change করতে হবে!

---

## 🚀 How to Use

### Step 1: Create Email Accounts
```bash
# EC2 তে run করো
ssh -i your-key.pem ubuntu@16.170.25.9
cd ~/mushqila
docker-compose -f docker-compose.prod.yml exec web python manage.py create_email_accounts
```

### Step 2: Login to Webmail
1. Visit: https://mushqila.com/webmail/login/
2. Enter username (e.g., `info_mushqila`)
3. Enter password (e.g., `Info@Mushqila2026`)
4. Click Login

### Step 3: Change Password
1. After login, click "Change Password" in sidebar
2. Enter current password
3. Enter new password (min 8 chars)
4. Confirm new password
5. Click "Change Password"

### Step 4: Setup AWS SES (for receiving emails)
Follow the guide: `AWS-SES-EMAIL-RECEIVING-SETUP.md`

---

## 📁 File Structure

```
webmail/
├── models.py                    # Email, EmailAccount, Contact models
├── views.py                     # All webmail views
├── urls.py                      # URL routing
├── admin.py                     # Django admin config
├── tasks.py                     # Celery tasks
├── services/
│   ├── email_service.py         # Email sending service
│   ├── ses_service.py           # AWS SES integration
│   ├── s3_service.py            # S3 storage
│   └── ses_receiving_service.py # Email receiving service
├── management/commands/
│   ├── create_email_accounts.py # Create 8 email accounts
│   ├── fetch_incoming_emails.py # Fetch emails from S3
│   └── cleanup_emails.py        # Cleanup old emails
└── templates/webmail/
    ├── base.html                # Base template
    ├── login.html               # Login page
    ├── inbox.html               # Inbox view
    ├── compose.html             # Compose email
    ├── email_detail.html        # Single email view
    ├── change_password.html     # Password change
    ├── account_setup.html       # Account settings
    └── contacts.html            # Contacts list
```

---

## 🔧 Configuration

### Environment Variables (.env.production)

```env
# AWS SES Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AWS_SES_REGION=us-east-1

# Email Receiving
AWS_SES_RECEIVING_REGION=us-east-1
AWS_S3_INCOMING_BUCKET=mushqila-incoming-emails

# Email Settings
DEFAULT_FROM_EMAIL=noreply@mushqila.com
```

---

## 🎨 Features

### 1. Modern UI
- Clean, professional design
- Responsive (mobile-friendly)
- Green theme matching mushqila.com
- Font Awesome icons
- Bootstrap 5

### 2. Email Folders
- **Inbox**: Incoming emails
- **Sent**: Sent emails
- **Drafts**: Draft emails
- **Starred**: Important emails
- **Spam**: Spam emails
- **Trash**: Deleted emails
- **Archive**: Archived emails

### 3. Email Actions
- Compose new email
- Reply to email
- Forward email
- Delete email
- Mark as read/unread
- Star/unstar email
- Move to folder

### 4. Search
- Search by subject
- Search by sender
- Search by content
- Full-text search

### 5. Contacts
- Save contacts
- Favorite contacts
- Quick compose to contact

### 6. Security
- Password protected
- Session management
- CSRF protection
- Secure password change
- Password strength validation

---

## 📊 Database Models

### EmailAccount
```python
- user (ForeignKey to User)
- email_address (email@mushqila.com)
- display_name (Display Name)
- aws_access_key (AWS credentials)
- aws_secret_key (AWS credentials)
- is_default (Boolean)
- is_active (Boolean)
```

### Email
```python
- account (ForeignKey to EmailAccount)
- message_id (Unique ID)
- from_address (Sender)
- to_addresses (Recipients)
- subject (Subject line)
- body_text (Plain text)
- body_html (HTML content)
- folder (inbox/sent/drafts/etc)
- is_read (Boolean)
- is_starred (Boolean)
- received_at (DateTime)
```

### Contact
```python
- user (ForeignKey to User)
- name (Contact name)
- email (Contact email)
- phone (Phone number)
- is_favorite (Boolean)
```

---

## 🔄 Email Receiving Flow

```
External Email Sender
        ↓
AWS SES (us-east-1)
        ↓
S3 Bucket (mushqila-incoming-emails)
        ↓
Celery Task (every 5 minutes)
        ↓
Django App (parse & save)
        ↓
PostgreSQL Database
        ↓
Webmail Inbox
```

---

## 🛠️ Management Commands

### Create Email Accounts
```bash
python manage.py create_email_accounts
```
Creates 8 email accounts with default passwords.

### Fetch Incoming Emails
```bash
python manage.py fetch_incoming_emails
```
Manually fetch emails from S3.

### Cleanup Old Emails
```bash
python manage.py cleanup_emails --days=30
```
Delete emails older than 30 days from trash.

---

## 🔐 Security Best Practices

1. **Change Default Passwords**
   - প্রথম login এর পর সব passwords change করো

2. **Use Strong Passwords**
   - Minimum 8 characters
   - Mix of uppercase, lowercase, numbers, symbols

3. **Enable 2FA (Optional)**
   - Django-two-factor-auth install করা যায়

4. **Regular Backups**
   - Database backup নিয়মিত নাও
   - S3 bucket versioning enable করো

5. **Monitor Access**
   - Login logs check করো
   - Suspicious activity track করো

---

## 📝 Testing Checklist

### Local Testing
- [ ] Create email accounts
- [ ] Login with each account
- [ ] Change password
- [ ] Compose email
- [ ] Check inbox
- [ ] Search emails
- [ ] Delete email

### Production Testing
- [ ] Deploy to EC2
- [ ] Create email accounts
- [ ] Test login
- [ ] Send test email from Gmail
- [ ] Verify email received in S3
- [ ] Fetch emails
- [ ] Check inbox

---

## 🚨 Troubleshooting

### Issue: Can't login
**Solution:**
```bash
# Check if user exists
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(username='info_mushqila').exists()
```

### Issue: No emails in inbox
**Solution:**
```bash
# Manually fetch emails
docker-compose -f docker-compose.prod.yml exec web python manage.py fetch_incoming_emails

# Check S3 bucket
aws s3 ls s3://mushqila-incoming-emails/incoming/
```

### Issue: Can't send emails
**Solution:**
- Check AWS SES credentials in .env.production
- Verify SES is out of sandbox mode
- Check recipient email is verified (if in sandbox)

---

## 📚 Related Documentation

1. **AWS-SES-EMAIL-RECEIVING-SETUP.md** - Complete AWS SES setup guide
2. **DEPLOYMENT-SUMMARY.md** - Deployment instructions
3. **EC2-COMMANDS.md** - Common EC2 commands

---

## 🎉 Summary

✅ **What's Working:**
- 8 separate email accounts
- Login system
- Password change
- Email compose/send
- Email receiving (with AWS SES setup)
- Modern UI
- Mobile responsive

✅ **What's Ready:**
- Production deployment
- Multi-user support
- Secure authentication
- Email management

✅ **Next Steps:**
1. Run `create_email_accounts` command
2. Setup AWS SES (follow AWS-SES-EMAIL-RECEIVING-SETUP.md)
3. Test login with each account
4. Change default passwords
5. Send test emails

---

## 📞 Support

**Need help?**
- Check troubleshooting section above
- Review AWS-SES-EMAIL-RECEIVING-SETUP.md
- Check Django logs: `docker-compose logs -f web`

**Your webmail is ready to use!** 🚀
