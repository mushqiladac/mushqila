"""
Custom template tags and filters for accounts app
"""

from django import template
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta

register = template.Library()


@register.filter
def user_type_display(user_type):
    """Display user-friendly user type names"""
    type_map = {
        'admin': _('Administrator'),
        'super_agent': _('Super Agent'),
        'agent': _('Travel Agent'),
        'sub_agent': _('Sub Agent'),
        'supplier': _('Service Supplier'),
        'corporate': _('Corporate Client'),
        'pilgrim': _('Pilgrim Service Provider'),
    }
    return type_map.get(user_type, user_type)


@register.filter
def status_display(status):
    """Display user-friendly status names"""
    status_map = {
        'active': _('Active'),
        'inactive': _('Inactive'),
        'suspended': _('Suspended'),
        'pending': _('Pending'),
        'blocked': _('Blocked'),
        'under_review': _('Under Review'),
    }
    return status_map.get(status, status)


@register.filter
def status_badge_class(status):
    """Return Bootstrap badge class for status"""
    class_map = {
        'active': 'badge-success',
        'inactive': 'badge-secondary',
        'suspended': 'badge-warning',
        'pending': 'badge-info',
        'blocked': 'badge-danger',
        'under_review': 'badge-warning',
    }
    return class_map.get(status, 'badge-secondary')


@register.filter
def currency_format(amount):
    """Format currency amounts"""
    if amount is None:
        return '0.00'
    try:
        return f"{float(amount):,.2f}"
    except (ValueError, TypeError):
        return '0.00'


@register.filter
def time_since(value):
    """Return time since a datetime"""
    if not value:
        return ''

    now = timezone.now()
    diff = now - value

    if diff.days > 365:
        years = diff.days // 365
        return _(f"{years} year{'s' if years > 1 else ''} ago")
    elif diff.days > 30:
        months = diff.days // 30
        return _(f"{months} month{'s' if months > 1 else ''} ago")
    elif diff.days > 0:
        return _(f"{diff.days} day{'s' if diff.days > 1 else ''} ago")
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return _(f"{hours} hour{'s' if hours > 1 else ''} ago")
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return _(f"{minutes} minute{'s' if minutes > 1 else ''} ago")
    else:
        return _('Just now')


@register.simple_tag
def get_user_balance(user):
    """Get user's current balance"""
    if hasattr(user, 'current_balance'):
        return user.current_balance
    return 0.00


@register.simple_tag
def get_user_credit_limit(user):
    """Get user's credit limit"""
    if hasattr(user, 'credit_limit'):
        return user.credit_limit
    return 0.00


@register.simple_tag
def get_available_credit(user):
    """Get user's available credit"""
    if hasattr(user, 'available_credit'):
        return user.available_credit()
    return 0.00