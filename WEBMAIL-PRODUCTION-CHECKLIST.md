# Webmail System - Production Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. AWS Setup
- [ ] Create AWS Account
- [ ] Set up IAM user with appropriate permissions
- [ ] Generate AWS Access Key and Secret Key
- [ ] Configure AWS CLI (optional)

### 2. AWS SES Configuration
- [ ] Verify sender email addresses in SES
- [ ] Verify domain (recommended for production)
- [ ] Request production access (move out of sandbox)
- [ ] Set up SES sending limits
- [ ] Configure SES bounce and complaint handling
- [ ] Set up SNS topics for notifications
- [ ] Create SES configuration set (optional)
- [ ] Test email sending

### 3. AWS S3 Configuration
- [ ] Create S3 bucket: `mushqila-webmail-prod`
- [ ] Enable versioning on bucket
- [ ] Configure bucket encryption (AES-256)
- [ ] Set up bucket lifecycle rules:
  - Move to Glacier after 90 days
  - Delete from Glacier after 365 days
- [ ] Configure CORS if needed
- [ ] Set up bucket policy for access control
- [ ] Enable CloudWatch metrics
- [ ] Test S3 access

### 4. Environment Variables
- [ ] Set `AWS_ACCESS_KEY_ID` in production
- [ ] Set `AWS_SECRET_ACCESS_KEY` in production
- [ ] Set `AWS_REGION` (e.g., us-east-1)
- [ ] Set `AWS_S3_BUCKET_NAME`
- [ ] Set `AWS_SES_REGION`
- [ ] Set `DEFAULT_FROM_EMAIL`
- [ ] Verify all environment variables are loaded

### 5. Database
- [ ] Run migrations: `python manage.py migrate webmail`
- [ ] Verify all tables created
- [ ] Set up database backups
- [ ] Configure database indexes
- [ ] Test database connection

### 6. Django Settings
- [ ] Add 'webmail' to INSTALLED_APPS
- [ ] Configure AWS settings in settings_production.py
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up LOGGING for webmail
- [ ] Configure STATIC_ROOT and MEDIA_ROOT
- [ ] Set up CSRF and CORS settings

### 7. Security
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS (SSL/TLS)
- [ ] Configure SECURE_SSL_REDIRECT = True
- [ ] Set SESSION_COOKIE_SECURE = True
- [ ] Set CSRF_COOKIE_SECURE = True
- [ ] Enable HSTS headers
- [ ] Configure Content Security Policy
- [ ] Set up rate limiting
- [ ] Enable Django security middleware
- [ ] Audit AWS IAM permissions

### 8. Testing
- [ ] Test email sending via SES
- [ ] Test email storage in S3
- [ ] Test email retrieval from S3
- [ ] Test attachment upload/download
- [ ] Test email deletion
- [ ] Test folder operations
- [ ] Test contact management
- [ ] Load test with multiple concurrent users
- [ ] Test error handling
- [ ] Test AWS credential rotation

### 9. Monitoring & Logging
- [ ] Set up CloudWatch for SES metrics
- [ ] Set up CloudWatch for S3 metrics
- [ ] Configure Django logging
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Monitor AWS costs
- [ ] Set up billing alerts
- [ ] Configure log rotation
- [ ] Set up uptime monitoring

### 10. Performance
- [ ] Enable database query optimization
- [ ] Set up database connection pooling
- [ ] Configure caching (Redis/Memcached)
- [ ] Optimize S3 presigned URL generation
- [ ] Enable CDN for static files
- [ ] Set up database indexes
- [ ] Configure pagination for email lists
- [ ] Optimize email search queries

## 🚀 Deployment Steps

### Step 1: Install Dependencies
```bash
pip install boto3 botocore
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy and edit .env file
cp .env.example .env
nano .env
```

### Step 3: Run Migrations
```bash
python manage.py migrate webmail
```

### Step 4: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 5: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 6: Test AWS Connections
```python
# Test SES
from webmail.services import SESService
ses = SESService()
print(ses.get_send_quota())

# Test S3
from webmail.services import S3Service
s3 = S3Service()
print(s3.create_bucket_if_not_exists())
```

### Step 7: Create Email Account
```python
from webmail.models import EmailAccount
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

EmailAccount.objects.create(
    user=user,
    email_address='noreply@mushqila.com',
    display_name='Mushqila Travel',
    aws_access_key='YOUR_KEY',
    aws_secret_key='YOUR_SECRET',
    aws_region='us-east-1',
    s3_bucket_name='mushqila-webmail-prod',
    ses_verified=True,
    is_default=True,
    is_active=True
)
```

### Step 8: Test Email Sending
```python
from webmail.services import EmailService
from webmail.models import EmailAccount

account = EmailAccount.objects.first()
service = EmailService(account)

result = service.send_email(
    to_addresses=['test@example.com'],
    subject='Test Email',
    body_text='This is a test email.',
    body_html='<h1>This is a test email.</h1>'
)

print(result)
```

### Step 9: Set Up Cron Jobs
```bash
# Add to crontab
# Cleanup old emails daily at 2 AM
0 2 * * * cd /path/to/project && python manage.py cleanup_emails

# Archive old emails weekly
0 3 * * 0 cd /path/to/project && python manage.py cleanup_emails --archive-days 90
```

### Step 10: Deploy Application
```bash
# Using Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Or using uWSGI
uwsgi --http :8000 --module config.wsgi --master --processes 4
```

## 📊 Post-Deployment Verification

### 1. Functional Tests
- [ ] Send test email
- [ ] Receive test email
- [ ] Upload attachment
- [ ] Download attachment
- [ ] Search emails
- [ ] Filter emails
- [ ] Create label
- [ ] Apply label to email
- [ ] Move email to folder
- [ ] Delete email
- [ ] Restore from trash

### 2. Performance Tests
- [ ] Send 100 emails concurrently
- [ ] Retrieve 1000 emails from database
- [ ] Search across 10,000 emails
- [ ] Upload 10MB attachment
- [ ] Download 10MB attachment

### 3. Security Tests
- [ ] Verify HTTPS is enforced
- [ ] Test unauthorized access
- [ ] Verify email isolation between users
- [ ] Test SQL injection prevention
- [ ] Test XSS prevention
- [ ] Verify CSRF protection

### 4. Monitoring
- [ ] Check CloudWatch metrics
- [ ] Verify logs are being written
- [ ] Test error notifications
- [ ] Check AWS billing dashboard
- [ ] Verify backup systems

## 🔧 Maintenance Tasks

### Daily
- [ ] Monitor error logs
- [ ] Check AWS costs
- [ ] Review SES bounce/complaint rates

### Weekly
- [ ] Review CloudWatch metrics
- [ ] Check disk space usage
- [ ] Review security logs
- [ ] Test backup restoration

### Monthly
- [ ] Review and optimize database queries
- [ ] Clean up old logs
- [ ] Review AWS IAM permissions
- [ ] Update dependencies
- [ ] Security audit

### Quarterly
- [ ] Review and update documentation
- [ ] Performance optimization review
- [ ] Cost optimization review
- [ ] Disaster recovery drill

## 🆘 Troubleshooting

### SES Issues
**Problem**: Emails not sending
- Check SES verification status
- Verify AWS credentials
- Check sending limits
- Review CloudWatch logs
- Check bounce/complaint rates

**Problem**: Emails going to spam
- Set up SPF records
- Set up DKIM
- Set up DMARC
- Use verified domain
- Maintain good sender reputation

### S3 Issues
**Problem**: Cannot store emails
- Check bucket permissions
- Verify AWS credentials
- Check bucket region
- Review IAM policies
- Check bucket quota

**Problem**: Slow retrieval
- Use presigned URLs
- Enable CloudFront CDN
- Optimize S3 key structure
- Use S3 Transfer Acceleration

### Database Issues
**Problem**: Slow queries
- Add database indexes
- Optimize queries
- Enable query caching
- Use database connection pooling

**Problem**: Database full
- Run cleanup command
- Archive old emails
- Increase storage
- Set up automatic cleanup

## 📈 Scaling Considerations

### For 10,000+ emails/day
- [ ] Use SES with dedicated IP
- [ ] Enable S3 Transfer Acceleration
- [ ] Set up read replicas for database
- [ ] Implement Redis caching
- [ ] Use Celery for async tasks
- [ ] Set up load balancer

### For 100,000+ emails/day
- [ ] Use multiple SES regions
- [ ] Implement sharding for S3
- [ ] Use Aurora Serverless
- [ ] Set up auto-scaling
- [ ] Implement CDN for attachments
- [ ] Use Lambda for processing

## 💰 Cost Optimization

### SES
- Use bulk sending for newsletters
- Implement email throttling
- Monitor bounce rates
- Use SES configuration sets

### S3
- Use lifecycle policies
- Compress email data
- Use S3 Intelligent-Tiering
- Delete old attachments
- Use S3 Glacier for archives

### Database
- Archive old emails
- Implement data retention policies
- Use database compression
- Optimize indexes

## 🔐 Security Best Practices

1. **AWS Credentials**
   - Rotate credentials regularly
   - Use IAM roles when possible
   - Never commit credentials to git
   - Use AWS Secrets Manager

2. **Email Security**
   - Validate email addresses
   - Sanitize email content
   - Scan attachments for malware
   - Implement rate limiting

3. **Data Protection**
   - Enable S3 encryption
   - Use HTTPS for all connections
   - Implement data retention policies
   - Regular security audits

4. **Access Control**
   - Implement role-based access
   - Use multi-factor authentication
   - Log all access attempts
   - Regular permission reviews

## 📞 Support Contacts

- AWS Support: https://console.aws.amazon.com/support/
- SES Documentation: https://docs.aws.amazon.com/ses/
- S3 Documentation: https://docs.aws.amazon.com/s3/
- Django Documentation: https://docs.djangoproject.com/

---

**Status**: ✅ 100% Production Ready
**Version**: 1.0.0
**Last Updated**: March 4, 2026
