"""
Local development settings for Finance App
Use SQLite database for local development
"""
from .settings import *

# Override database configuration for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable Galileo client for local development
GALILEO_ENABLED = False

# Use local email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug mode for local development
DEBUG = True

# Allow all hosts for local development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']
