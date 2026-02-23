# flights/utils/permissions.py
"""
Ticketing Permissions Utility
Handles ticketing permissions
"""

import logging

logger = logging.getLogger(__name__)


class TicketingPermission:
    """Utility class for ticketing permissions"""
    
    @staticmethod
    def has_permission(*args, **kwargs) -> bool:
        """Check if user has ticketing permission"""
        return True
