# accounts/signals/accounting_signals.py
"""
Signals for automatic accounting entries
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from flights.models import Ticket, Payment, Refund
from accounts.services import AccountingService

User = get_user_model()


@receiver(post_save, sender=Ticket)
def handle_ticket_accounting(sender, instance, created, **kwargs):
    """Automatically create accounting entries for ticket operations"""
    if not created:
        # Only handle new tickets for now
        return

    try:
        # Get the user who created the ticket (assuming it's set in the view)
        # For now, we'll use a system user or the booking user
        user = instance.booking.user if instance.booking else None
        if not user:
            return

        # Record ticket issue accounting
        AccountingService.record_ticket_issue(instance, user)

    except Exception as e:
        # Log error but don't break the ticket creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create accounting entry for ticket {instance.id}: {str(e)}")


@receiver(post_save, sender=Refund)
def handle_refund_accounting(sender, instance, created, **kwargs):
    """Automatically create accounting entries for refunds"""
    if not created:
        return

    try:
        # Get the user who processed the refund
        user = instance.processed_by if hasattr(instance, 'processed_by') else None
        if not user and instance.ticket and instance.ticket.booking:
            user = instance.ticket.booking.user

        if not user:
            return

        # Record refund accounting
        AccountingService.record_ticket_refund(instance, user)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create accounting entry for refund {instance.id}: {str(e)}")


@receiver(post_save, sender=Payment)
def handle_payment_accounting(sender, instance, created, **kwargs):
    """Automatically create accounting entries for payments"""
    if not created:
        return

    try:
        # Get the user who made the payment
        user = instance.booking.user if instance.booking else None
        if not user:
            return

        # Record payment accounting
        AccountingService.record_payment_received(instance, user)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create accounting entry for payment {instance.id}: {str(e)}")


# Note: For void and cancel operations, we need to detect status changes
# This would require additional logic in the ticket model to track status changes
# For now, these would need to be called manually from the views when status changes occur