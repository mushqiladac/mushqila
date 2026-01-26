"""
App configuration for Accounts app - Mushqila B2B Saudi Arabia
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = _('Accounts - Saudi Arabia')
    
    def ready(self):
        """Ready method for signals"""
        import accounts.signals  # Import accounting signals
        import accounts.signals.transaction_signals  # Import transaction tracking signals