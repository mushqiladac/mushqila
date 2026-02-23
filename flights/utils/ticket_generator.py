# flights/utils/ticket_generator.py
"""
Ticket Generator Utility
Generates ticket numbers and related data
"""

import logging

logger = logging.getLogger(__name__)


class TicketGenerator:
    """Utility class for generating tickets"""
    
    @staticmethod
    def generate_ticket_number(*args, **kwargs) -> str:
        """Generate a ticket number"""
        return '0014550000001'
    
    @staticmethod
    def generate_emd(*args, **kwargs) -> str:
        """Generate an EMD number"""
        return '0359999999999'
