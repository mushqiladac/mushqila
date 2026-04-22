"""
Django settings for mushqila project.
"""

from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-test-key')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Site URL for email links
SITE_URL = config('SITE_URL', default='http://localhost:8000')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize', 
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_filters',
    
    
    # Local apps
    'accounts',
    'flights',
    'b2c',
    'webmail',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.unread_notifications_count',
                'accounts.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ========================================
# Database configuration with optional SQLite fallback for local dev
# Use environment variable `DB_ENGINE=sqlite` to run with SQLite locally
# ========================================
DB_ENGINE = config('DB_ENGINE', default='postgres')

if DB_ENGINE == 'mushqila':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': BASE_DIR / 'mushqila',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='mushqila'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='EMR@55nondita'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 60,
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration for serving static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ========================================
# Email Configuration
# ========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='email-smtp.eu-north-1.amazonaws.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='AKIAUQETDVDPECKLURNW')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='BGa2ERSVz5NxV9Od/sX2ONERAdtSrq9tJfStFJaYXmXm')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@mushqila.com')

# ========================================
# Travelport Galileo GDS API Configuration
# ========================================
TRAVELPORT_USERNAME = config('TRAVELPORT_USERNAME', default='')
TRAVELPORT_PASSWORD = config('TRAVELPORT_PASSWORD', default='')
TRAVELPORT_BRANCH_CODE = config('TRAVELPORT_BRANCH_CODE', default='P702214')
TRAVELPORT_TARGET_BRANCH = config('TRAVELPORT_TARGET_BRANCH', default='P702214')
TRAVELPORT_BASE_URL = config('TRAVELPORT_BASE_URL', default='https://americas-uapi.travelport.com')
TRAVELPORT_REST_URL = config('TRAVELPORT_REST_URL', default='https://americas-uapi.travelport.com/B2BGateway/connect/rest')

# Galileo specific endpoints
GALILEO_AVAILABILITY_URL = f"{TRAVELPORT_REST_URL}/AirAvailabilitySearchReq"
GALILEO_LOWFARE_SEARCH_URL = f"{TRAVELPORT_REST_URL}/AirLowFareSearchReq"
GALILEO_BOOKING_URL = f"{TRAVELPORT_REST_URL}/AirBookReq"
GALILEO_CANCEL_URL = f"{TRAVELPORT_REST_URL}/AirCancelReq"
GALILEO_TICKET_URL = f"{TRAVELPORT_REST_URL}/AirTicketReq"

# ========================================
# FIX: Login/Logout URLs - THIS IS THE PROBLEM
# ========================================
LOGIN_URL = 'accounts:login'
# LOGIN_REDIRECT_URL = 'dashboard'  # REMOVE or COMMENT THIS LINE
LOGIN_REDIRECT_URL = 'accounts:home'  # Set to home instead of dashboard
LOGOUT_REDIRECT_URL = 'accounts:login'

# ===========================
# CSRF and Session Configuration for Proxy
# ===========================
# Get CSRF trusted origins from environment
csrf_origins = config('CSRF_TRUSTED_ORIGINS', default='')
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# Cookie settings for proxy setup
CSRF_COOKIE_DOMAIN = config('CSRF_COOKIE_DOMAIN', default=None)
SESSION_COOKIE_DOMAIN = config('SESSION_COOKIE_DOMAIN', default=None)

# Security settings for HTTPS
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Proxy SSL header
SECURE_PROXY_SSL_HEADER_NAME = config('SECURE_PROXY_SSL_HEADER', default='HTTP_X_FORWARDED_PROTO,https')
if SECURE_PROXY_SSL_HEADER_NAME:
    parts = SECURE_PROXY_SSL_HEADER_NAME.split(',')
    if len(parts) == 2:
        SECURE_PROXY_SSL_HEADER = (parts[0], parts[1])

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


# ===========================
# AWS Configuration for Webmail
# ===========================
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME', 'mushqila-webmail')

# AWS SES Configuration
AWS_SES_REGION = os.getenv('AWS_SES_REGION', AWS_REGION)
AWS_SES_CONFIGURATION_SET = os.getenv('AWS_SES_CONFIGURATION_SET', '')

# Email Settings
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@mushqila.com')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Can be changed to SES backend

# Webmail Domain
WEBMAIL_DOMAIN = os.getenv('WEBMAIL_DOMAIN', 'mushqila.com')

# Webmail Settings
WEBMAIL_MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25 MB
WEBMAIL_ALLOWED_ATTACHMENT_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
    'image/gif',
    'text/plain',
    'application/zip',
]
