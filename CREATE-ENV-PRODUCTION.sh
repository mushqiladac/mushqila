#!/bin/bash

# Script to create .env.production file on EC2 server
# Run this on your EC2 server: bash CREATE-ENV-PRODUCTION.sh

echo "Creating .env.production file..."

cat > .env.production << 'EOF'
# Mushqila Production Environment Variables

# =============================================================================
# DJANGO SETTINGS
# =============================================================================

SECRET_KEY=django-insecure-p8k#m2@v9x$w5n7q!r4t6y8u0i-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=16.170.25.9,localhost,127.0.0.1

# =============================================================================
# DATABASE SETTINGS (PostgreSQL)
# =============================================================================

DB_ENGINE=postgresql
DB_NAME=mushqila_db
DB_USER=mushqila_user
DB_PASSWORD=mushqila_secure_password_2024
DB_HOST=db
DB_PORT=5432

# =============================================================================
# GALILEO GDS API SETTINGS
# =============================================================================

GALILEO_PCC=YOUR_PCC_CODE
GALILEO_USERNAME=YOUR_API_USERNAME
GALILEO_PASSWORD=YOUR_API_PASSWORD
GALILEO_TARGET_BRANCH=YOUR_TARGET_BRANCH
GALILEO_PROVIDER_CODE=1G
GALILEO_AIR_ENDPOINT=https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/AirService
GALILEO_UNIVERSAL_ENDPOINT=https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/UniversalRecordService
GALILEO_UTIL_ENDPOINT=https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/UtilService
GALILEO_TIMEOUT=30
GALILEO_DEBUG=False

# =============================================================================
# EMAIL SETTINGS
# =============================================================================

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@mushqila.com
SERVER_EMAIL=server@mushqila.com
ADMIN_EMAIL=admin@mushqila.com

# =============================================================================
# AWS SETTINGS (for Webmail)
# =============================================================================

AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=mushqila-webmail
AWS_SES_REGION=us-east-1
USE_S3=False

# =============================================================================
# REDIS CACHE SETTINGS
# =============================================================================

REDIS_URL=redis://redis:6379/1

# =============================================================================
# CELERY SETTINGS
# =============================================================================

USE_CELERY=False
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# =============================================================================
# PAYMENT GATEWAY SETTINGS
# =============================================================================

PAYMENT_GATEWAY=stripe
STRIPE_PUBLIC_KEY=pk_test_your_public_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# =============================================================================
# BUSINESS SETTINGS
# =============================================================================

COMPANY_NAME=Mushqila Travel
COMPANY_EMAIL=info@mushqila.com
COMPANY_PHONE=+966-XXX-XXXX
DEFAULT_CURRENCY=SAR
DEFAULT_LANGUAGE=en
TIME_ZONE=Asia/Riyadh

# =============================================================================
# FEATURE FLAGS
# =============================================================================

ENABLE_B2C=True
ENABLE_B2B=True
ENABLE_LOYALTY=True
ENABLE_REFERRALS=True
ENABLE_REVIEWS=True
ENABLE_SOCIAL=True

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

LOG_LEVEL=INFO
ENABLE_FILE_LOGGING=True

# =============================================================================
# MONITORING
# =============================================================================

USE_SENTRY=False
SENTRY_DSN=your-sentry-dsn-url
GOOGLE_ANALYTICS_ID=UA-XXXXXXXXX-X

# =============================================================================
# BACKUP SETTINGS
# =============================================================================

BACKUP_ENABLED=True
BACKUP_RETENTION_DAYS=30
BACKUP_STORAGE_PATH=/backups
EOF

echo "✅ .env.production file created!"
echo ""
echo "⚠️  IMPORTANT: Edit .env.production and update these values:"
echo "   1. SECRET_KEY - Generate a new random key"
echo "   2. DB_PASSWORD - Set a strong database password"
echo "   3. AWS credentials (if using webmail)"
echo "   4. Email settings"
echo "   5. Galileo API credentials (when ready)"
echo ""
echo "To edit: nano .env.production"
echo ""
echo "After editing, run:"
echo "  docker-compose -f docker-compose.prod.yml up -d --build"
