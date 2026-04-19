# Webmail App Update Summary

## যা যা পরিবর্তন করা হয়েছে

### 1. EmailAccount Model আপডেট (`webmail/models.py`)

নতুন ফিল্ড যুক্ত করা হয়েছে:
- `first_name` - প্রথম নাম
- `last_name` - শেষ নাম
- `password` - Webmail login এর জন্য hashed password
- `mobile_number` - মোবাইল নম্বর
- `alternate_email` - বিকল্প ইমেইল ঠিকানা

নতুন মেথড যুক্ত করা হয়েছে:
- `set_password(raw_password)` - Password hash করে সেভ করে
- `check_password(raw_password)` - Password verify করে

### 2. Forms তৈরি (`webmail/forms.py`)

তিনটি নতুন form তৈরি করা হয়েছে:

#### EmailAccountCreationForm
- সুপার ইউজার নতুন email account তৈরি করার জন্য
- Password ও confirm password validation সহ
- সব নতুন ফিল্ড সহ

#### EmailAccountChangeForm
- Existing email account আপডেট করার জন্য
- Optional password change সহ

#### WebmailLoginForm
- Email ও password দিয়ে webmail login এর জন্য
- EmailAccount এর বিপরীতে authentication

### 3. Admin Panel আপডেট (`webmail/admin.py`)

EmailAccountAdmin আপডেট করা হয়েছে:
- Custom forms ব্যবহার করা হচ্ছে
- নতুন ফিল্ডগুলো fieldsets এ যুক্ত করা হয়েছে
- Password section আলাদা করা হয়েছে
- List display তে নতুন ফিল্ড যুক্ত করা হয়েছে

### 4. Views আপডেট (`webmail/views.py`)

#### webmail_login
- Email ও password দিয়ে login করার জন্য আপডেট করা হয়েছে
- WebmailLoginForm ব্যবহার করা হচ্ছে
- EmailAccount এর password verify করা হচ্ছে

#### change_password
- EmailAccount এর password ও আপডেট করা হচ্ছে
- User ও EmailAccount উভয়ের password sync রাখা হচ্ছে

### 5. Login Template আপডেট (`webmail/templates/webmail/login.html`)

- Form rendering আপডেট করা হয়েছে
- Email field যুক্ত করা হয়েছে
- Form errors display করা হচ্ছে

### 6. Management Commands

#### create_webmail_account
নতুন email account তৈরি করার command:
```bash
python manage.py create_webmail_account \
  --email user@example.com \
  --password SecurePass123 \
  --first-name "John" \
  --last-name "Doe" \
  --mobile "+8801712345678" \
  --alternate-email "john@gmail.com"
```

#### set_default_passwords
Existing accounts এর জন্য default password সেট করার command:
```bash
python manage.py set_default_passwords --default-password "changeme123"
```

### 7. Migration

নতুন migration তৈরি হয়েছে:
- `0002_emailaccount_alternate_email_emailaccount_first_name_and_more.py`

## কিভাবে ব্যবহার করবেন

### Migration চালান:
```bash
python manage.py migrate webmail
```

### Existing accounts এর জন্য default password সেট করুন:
```bash
python manage.py set_default_passwords
```

### নতুন email account তৈরি করুন:

**Option 1: Admin Panel থেকে**
1. `/admin/` এ যান
2. Webmail > Email accounts > Add
3. সব তথ্য পূরণ করুন
4. Save করুন

**Option 2: Command Line থেকে**
```bash
python manage.py create_webmail_account \
  --email user@mushqila.com \
  --password SecurePass123 \
  --first-name "User" \
  --last-name "Name"
```

### ইউজার লগিন করুন:
1. `/webmail/login/` এ যান
2. Email ও password দিন
3. Sign In করুন

### পাসওয়ার্ড পরিবর্তন করুন:
1. Webmail inbox এ যান
2. Change Password অপশনে যান
3. নতুন password দিন

## Security Features

1. **Password Hashing**: Django এর `make_password()` ব্যবহার করা হচ্ছে
2. **Password Validation**: Minimum 8 characters required
3. **Confirm Password**: Password mismatch check করা হচ্ছে
4. **Session Management**: Login করার পর session maintain করা হচ্ছে

## AWS SES Integration

সব কিছু AWS SES এর মাধ্যমে কাজ করবে:
- Email sending: SES API
- Email receiving: SES + S3
- Email storage: S3 bucket

## Next Steps

1. Migration চালান
2. Existing accounts এর জন্য password সেট করুন
3. Test করুন নতুন account তৈরি করে
4. Test করুন login functionality
5. Test করুন password change functionality

## Documentation

বিস্তারিত documentation দেখুন: `WEBMAIL-ACCOUNT-MANAGEMENT.md`
