# accounts/decorators.py
"""
Custom decorators for B2B platform permissions
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def require_business_unit(view_func):
    """
    Decorator to ensure user has an active business unit
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'business_unit') or not request.user.business_unit:
            messages.error(request, 'Access denied: No active business unit')
            return redirect('accounts:profile')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_permission(permission_codename):
    """
    Decorator to check user permissions
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # For now, just check if user is authenticated and has business unit
            # In a full implementation, this would check specific permissions
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            if not hasattr(request.user, 'business_unit') or not request.user.business_unit:
                messages.error(request, 'Access denied: Business unit required')
                return redirect('accounts:profile')

            # TODO: Implement actual permission checking based on permission_codename
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator