#!/usr/bin/env python
"""
Quick diagnostic script to check login page errors
Run this with: python manage.py shell < check_login_error.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from accounts.views.auth_views import LoginView

print("=" * 60)
print("CHECKING LOGIN VIEW")
print("=" * 60)

try:
    # Create a test request
    factory = RequestFactory()
    request = factory.get('/accounts/login/')
    request.user = AnonymousUser()
    
    # Try to instantiate the view
    view = LoginView.as_view()
    
    print("✓ LoginView imported successfully")
    
    # Try to get the response
    response = view(request)
    
    print(f"✓ LoginView rendered successfully")
    print(f"  Status Code: {response.status_code}")
    
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    
    import traceback
    print("\nFull traceback:")
    print(traceback.format_exc())

print("\n" + "=" * 60)
print("CHECKING REQUIRED MODELS")
print("=" * 60)

try:
    from accounts.models import User, UserProfile
    from accounts.models.core import UserActivityLog
    
    print("✓ User model imported")
    print("✓ UserProfile model imported")
    print("✓ UserActivityLog model imported")
    
    # Check if tables exist
    print(f"\nUser count: {User.objects.count()}")
    print(f"UserProfile count: {UserProfile.objects.count()}")
    print(f"UserActivityLog count: {UserActivityLog.objects.count()}")
    
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}")
    print(f"  Message: {str(e)}")

print("\n" + "=" * 60)
print("CHECKING URL CONFIGURATION")
print("=" * 60)

try:
    from django.urls import reverse
    
    urls_to_check = [
        'accounts:login',
        'accounts:register',
        'accounts:password_reset',
        'accounts:agent_dashboard',
        'accounts:admin_dashboard',
        'accounts:supplier_dashboard',
    ]
    
    for url_name in urls_to_check:
        try:
            url = reverse(url_name)
            print(f"✓ {url_name}: {url}")
        except Exception as e:
            print(f"✗ {url_name}: {str(e)}")
            
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}")
    print(f"  Message: {str(e)}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
