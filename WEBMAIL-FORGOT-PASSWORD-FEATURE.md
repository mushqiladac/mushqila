# Webmail Forgot Password Feature

## Overview

ইউজার যদি তাদের webmail password ভুলে যায়, তাহলে তারা একটা temporary password request করতে পারবে যা তাদের alternate email এ পাঠানো হবে। এই temporary password ১৫ মিনিটের জন্য valid থাকবে।

## Features

### 1. Forgot Password Request
- ইউজার তাদের email address দিয়ে password reset request করবে
- System একটা random 8-character temporary password generate করবে
- Temporary password alternate email এ পাঠানো হবে
- Token ১৫ মিনিটের জন্য valid থাকবে

### 2. Password Reset
- ইউজার temporary password ব্যবহার করে নতুন password সেট করবে
- Temporary password verify করা হবে
- Expiry check করা হবে (১৫ মিনিট)
- নতুন password সেট হওয়ার পর token clear হবে

### 3. Email Notification
- Professional HTML email template
- Temporary password clearly displayed
- Expiry warning included
- Direct login link provided

## Database Changes

### EmailAccount Model এ নতুন ফিল্ড:

```python
reset_token = models.CharField(max_length=100, blank=True)
reset_token_created = models.DateTimeField(null=True, blank=True)
```

### নতুন Methods:

```python
generate_reset_token()  # Generate and save token
is_reset_token_valid(token)  # Verify token and check expiry
clear_reset_token()  # Clear token after use
```

## URLs

```
/webmail/forgot-password/  - Request temporary password
/webmail/reset-password/   - Reset password with token
/webmail/login/            - Login page (with forgot password link)
```

## Forms

### 1. ForgotPasswordForm
- Email address input
- Validates email exists and is active
- Checks alternate email exists
- Sends reset email

### 2. ResetPasswordForm
- Email address
- Temporary password
- New password
- Confirm password
- Validates token and expiry

## Email Template

Email এ থাকবে:
- Professional design with gradient header
- Temporary password in highlighted box
- 15-minute expiry warning
- Direct login link
- Security instructions

## Security Features

1. **Token Generation**: Random 8-character alphanumeric token
2. **Token Expiry**: 15 minutes validity
3. **One-time Use**: Token cleared after successful reset
4. **Hashed Storage**: Passwords stored as hashed values
5. **Alternate Email**: Reset link sent to alternate email only

## Usage Flow

### Step 1: Request Password Reset

1. ইউজার `/webmail/forgot-password/` এ যায়
2. Email address দেয়
3. System check করে:
   - Email account exists এবং active
   - Alternate email configured আছে
4. Temporary password generate হয়
5. Email পাঠানো হয় alternate email এ

### Step 2: Reset Password

1. ইউজার alternate email check করে
2. Temporary password copy করে
3. `/webmail/reset-password/` এ যায়
4. Form fill করে:
   - Email address
   - Temporary password
   - New password
   - Confirm password
5. System verify করে:
   - Token valid আছে
   - Token expired হয়নি (১৫ মিনিট)
   - Passwords match করে
6. নতুন password সেট হয়
7. Token clear হয়
8. ইউজার login page এ redirect হয়

### Step 3: Login

1. ইউজার নতুন password দিয়ে login করে
2. Webmail inbox access করে

## Configuration

### Settings.py এ যুক্ত করুন:

```python
# Site URL for email links
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Email configuration (if not already configured)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@mushqila.com')
```

### .env ফাইলে যুক্ত করুন:

```env
SITE_URL=https://mushqila.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@mushqila.com
```

## Migration

```bash
# Create migrations
python manage.py makemigrations webmail

# Apply migrations
python manage.py migrate webmail
```

## Testing

### Test Forgot Password:

1. একটা email account তৈরি করুন alternate email সহ
2. `/webmail/forgot-password/` এ যান
3. Email address দিন
4. Alternate email check করুন
5. Temporary password পাবেন

### Test Reset Password:

1. Temporary password copy করুন
2. `/webmail/reset-password/` এ যান
3. Email, temporary password, এবং new password দিন
4. Submit করুন
5. Login page এ redirect হবে

### Test Expiry:

1. Temporary password request করুন
2. ১৫ মিনিট wait করুন
3. Reset করার চেষ্টা করুন
4. "Invalid or expired" error পাবেন

## Email Example

```
Subject: Webmail Password Reset - Temporary Password

Hello John,

You have requested a password reset for your webmail account.

Your temporary password is: aB3dE7fG

This temporary password is valid for 15 minutes only.

Please use this temporary password to login and then change your 
password immediately.

Login URL: https://mushqila.com/webmail/login/

If you did not request this password reset, please ignore this email.

Best regards,
Mushqila Webmail Team
```

## Error Handling

### Common Errors:

1. **Email not found**: "No active account found with this email address"
2. **No alternate email**: "No alternate email found for this account"
3. **Invalid token**: "Invalid or expired temporary password"
4. **Expired token**: "Invalid or expired temporary password"
5. **Password mismatch**: "New passwords do not match"

## Security Considerations

1. **Rate Limiting**: Consider adding rate limiting to prevent abuse
2. **Token Complexity**: 8-character alphanumeric provides good security
3. **Short Expiry**: 15 minutes reduces risk window
4. **Alternate Email**: Ensures user owns the account
5. **One-time Use**: Token cleared after successful reset

## Future Enhancements

1. Add rate limiting (max 3 requests per hour)
2. Add email verification for alternate email
3. Add SMS option for password reset
4. Add password strength meter
5. Add login attempt tracking
6. Add account lockout after failed attempts

## Troubleshooting

### Email not sending:

1. Check EMAIL_HOST settings
2. Check EMAIL_HOST_USER and PASSWORD
3. Check firewall/port settings
4. Check spam folder
5. Enable "Less secure app access" for Gmail

### Token not working:

1. Check system time is correct
2. Check timezone settings
3. Verify token hasn't expired
4. Check token was copied correctly

### Alternate email not set:

1. Admin should set alternate email in admin panel
2. Or use management command to update accounts
3. Or allow users to set alternate email in profile

## Admin Tasks

### Set alternate email for existing accounts:

```python
from webmail.models import EmailAccount

# Update single account
account = EmailAccount.objects.get(email_address='user@example.com')
account.alternate_email = 'user.alternate@gmail.com'
account.save()

# Bulk update
for account in EmailAccount.objects.filter(alternate_email=''):
    # Set alternate email based on some logic
    account.alternate_email = f"{account.user.username}@gmail.com"
    account.save()
```

### Clear expired tokens:

```python
from django.utils import timezone
from datetime import timedelta
from webmail.models import EmailAccount

# Clear tokens older than 15 minutes
expiry_time = timezone.now() - timedelta(minutes=15)
EmailAccount.objects.filter(
    reset_token_created__lt=expiry_time
).update(reset_token='', reset_token_created=None)
```

## Summary

Forgot password feature সম্পূর্ণভাবে implement করা হয়েছে:

✅ Temporary password generation
✅ Email notification to alternate email
✅ 15-minute expiry
✅ Password reset with token verification
✅ Professional email templates
✅ Security features
✅ Error handling
✅ User-friendly interface

ইউজাররা এখন সহজেই তাদের password reset করতে পারবে যদি ভুলে যায়।
