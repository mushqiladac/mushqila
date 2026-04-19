# Webmail Account Management Guide

## সুপার ইউজার দ্বারা নতুন ইমেইল একাউন্ট তৈরি

### Django Admin Panel থেকে

1. Admin panel এ লগিন করুন: `/admin/`
2. **Webmail > Email accounts** এ যান
3. **Add Email Account** বাটনে ক্লিক করুন
4. নিচের তথ্য পূরণ করুন:

#### Basic Information
- **User**: যে Django user এর সাথে এই email account যুক্ত হবে
- **Email address**: ইমেইল ঠিকানা (যেমন: user@mushqila.com)
- **First name**: প্রথম নাম
- **Last name**: শেষ নাম
- **Display name**: প্রদর্শন নাম (যেমন: John Doe)

#### Contact Information
- **Mobile number**: মোবাইল নম্বর (যেমন: +8801XXXXXXXXX)
- **Alternate email**: বিকল্প ইমেইল ঠিকানা

#### Password
- **Password**: ওয়েবমেইল লগিনের জন্য পাসওয়ার্ড (কমপক্ষে ৮ অক্ষর)
- **Confirm password**: পাসওয়ার্ড নিশ্চিত করুন

#### AWS SES Configuration
- **AWS Access Key**: AWS SES access key
- **AWS Secret Key**: AWS SES secret key
- **AWS Region**: AWS region (ডিফল্ট: us-east-1)
- **SES Verified**: ইমেইল SES এ verified কিনা

#### AWS S3 Configuration
- **S3 Bucket Name**: S3 bucket এর নাম
- **S3 Inbox Prefix**: S3 এ inbox folder prefix (ডিফল্ট: inbox/)

#### Email Settings
- **Signature**: ইমেইল সিগনেচার

#### Status
- **Is default**: এটি ডিফল্ট একাউন্ট কিনা
- **Is active**: একাউন্ট সক্রিয় কিনা

5. **Save** বাটনে ক্লিক করুন

### Command Line থেকে

নতুন ইমেইল একাউন্ট তৈরি করতে:

```bash
python manage.py create_webmail_account \
  --email user@mushqila.com \
  --password SecurePass123 \
  --first-name "John" \
  --last-name "Doe" \
  --mobile "+8801712345678" \
  --alternate-email "john.doe@gmail.com"
```

#### Parameters:
- `--email`: ইমেইল ঠিকানা (required)
- `--password`: পাসওয়ার্ড (required)
- `--first-name`: প্রথম নাম (optional)
- `--last-name`: শেষ নাম (optional)
- `--mobile`: মোবাইল নম্বর (optional)
- `--alternate-email`: বিকল্প ইমেইল (optional)
- `--user-id`: Existing user এর ID (optional, না দিলে নতুন user তৈরি হবে)
- `--display-name`: প্রদর্শন নাম (optional)

## ইউজার লগিন

### Webmail Login

ইউজার এখন তাদের ইমেইল ও পাসওয়ার্ড দিয়ে webmail এ লগিন করতে পারবে:

1. `/webmail/login/` এ যান
2. **Email Address** ফিল্ডে ইমেইল দিন
3. **Password** ফিল্ডে পাসওয়ার্ড দিন
4. **Sign In** বাটনে ক্লিক করুন

### পাসওয়ার্ড পরিবর্তন

লগিন করার পর ইউজার তাদের পাসওয়ার্ড পরিবর্তন করতে পারবে:

1. Webmail inbox এ যান
2. Settings বা Profile সেকশনে যান
3. **Change Password** অপশনে ক্লিক করুন
4. নিচের তথ্য দিন:
   - Current Password
   - New Password
   - Confirm New Password
5. **Change Password** বাটনে ক্লিক করুন

## Existing Accounts এর জন্য Default Password সেট করা

যদি আগে থেকে কোনো EmailAccount থাকে যাদের password নেই:

```bash
python manage.py set_default_passwords --default-password "changeme123"
```

এটি সব empty password গুলোতে default password সেট করবে। ইউজারদের প্রথম লগিনের পর পাসওয়ার্ড পরিবর্তন করতে বলুন।

## Migration চালানো

নতুন ফিল্ডগুলো database এ যুক্ত করতে:

```bash
python manage.py migrate webmail
```

## AWS SES Integration

সব ইমেইল AWS SES এর মাধ্যমে পাঠানো ও গ্রহণ করা হবে। নিশ্চিত করুন:

1. AWS SES এ ইমেইল ঠিকানা verified আছে
2. AWS credentials সঠিকভাবে configure করা আছে
3. S3 bucket তৈরি করা আছে email storage এর জন্য

## Security Notes

1. **Strong Passwords**: সবসময় শক্তিশালী পাসওয়ার্ড ব্যবহার করুন (কমপক্ষে ৮ অক্ষর)
2. **Password Hashing**: পাসওয়ার্ড Django এর `make_password()` দিয়ে hash করা হয়
3. **First Login**: প্রথম লগিনের পর ইউজারদের পাসওয়ার্ড পরিবর্তন করতে উৎসাহিত করুন
4. **AWS Credentials**: AWS credentials সুরক্ষিত রাখুন

## Troubleshooting

### Login Failed
- ইমেইল ঠিকানা সঠিক আছে কিনা চেক করুন
- পাসওয়ার্ড সঠিক আছে কিনা চেক করুন
- EmailAccount `is_active=True` আছে কিনা চেক করুন

### Password Reset
Admin panel থেকে password reset করতে:
1. Admin panel এ যান
2. Email Account খুলুন
3. Password ফিল্ডে নতুন পাসওয়ার্ড দিন
4. Confirm Password ফিল্ডে আবার দিন
5. Save করুন

## Example Usage

### সুপার ইউজার হিসেবে নতুন একাউন্ট তৈরি:

```python
from django.contrib.auth import get_user_model
from webmail.models import EmailAccount

User = get_user_model()

# Create user
user = User.objects.create_user(
    username='johndoe',
    email='john@mushqila.com',
    password='SecurePass123',
    first_name='John',
    last_name='Doe'
)

# Create email account
account = EmailAccount.objects.create(
    user=user,
    email_address='john@mushqila.com',
    first_name='John',
    last_name='Doe',
    display_name='John Doe',
    mobile_number='+8801712345678',
    alternate_email='john.doe@gmail.com',
    is_default=True,
    is_active=True
)

# Set password
account.set_password('SecurePass123')
account.save()
```

### ইউজার লগিন চেক:

```python
from webmail.models import EmailAccount

email = 'john@mushqila.com'
password = 'SecurePass123'

try:
    account = EmailAccount.objects.get(email_address=email, is_active=True)
    if account.check_password(password):
        print("Login successful!")
    else:
        print("Invalid password!")
except EmailAccount.DoesNotExist:
    print("Account not found!")
```
