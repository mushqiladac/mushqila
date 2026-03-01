from django.apps import AppConfig


class B2cConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'b2c'
    verbose_name = 'B2C Customer Platform'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import b2c.signals
        except ImportError:
            pass
