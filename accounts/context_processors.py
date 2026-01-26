from .models import Notification


def unread_notifications_count(request):
    """
    Context processor to add unread notifications count to all templates
    """
    if request.user.is_authenticated:
        try:
            count = Notification.objects.filter(user=request.user, is_read=False).count()
            return {'unread_notifications_count': count}
        except Exception:
            return {'unread_notifications_count': 0}
    return {'unread_notifications_count': 0}


def site_settings(request):
    """
    Context processor for site-wide settings
    """
    return {
        'site_name': 'Mushqila B2B',
        'site_description': 'B2B Travel Agent Platform',
        'support_email': 'support@mushqila.com',
        'support_phone': '+880 1234 567890',
        'current_year': 2024,
    }