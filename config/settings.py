"""
Django settings for mushqila project.
"""

from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-test-key')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['13.60.112.227','mushqila.com','www.mushqila.com','localhost','127.0.0.1','*']

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
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_filters',
    
    
    # Local apps
    'accounts',
    'flights',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
# Database Configuration
# ========================================
# Use PostgreSQL if DB_NAME is set, otherwise use SQLite
if config("DB_NAME", default=""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER", default="postgres"),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "connect_timeout": 10,
            }
        }
    }
else:
    # SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
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

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
