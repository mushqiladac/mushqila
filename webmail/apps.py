from django.apps import AppConfig


class WebmailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webmail'
    verbose_name = 'Webmail System'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import webmail.signals  # noqa
        except ImportError:
            pass
