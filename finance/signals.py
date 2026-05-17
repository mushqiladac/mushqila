from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import CreditSale, FinanceNotification


@receiver(post_save, sender=CreditSale)
def handle_credit_sale_status_change(sender, instance, created, **kwargs):
    """
    Handle notifications when credit sale status changes
    """
    if not created:  # Only for updates, not creation
        # Check if payment status changed to paid
        if instance.payment_status == instance.PaymentStatus.PAID and instance.completed_date:
            # Create notification for successful payment completion
            FinanceNotification.objects.create(
                user=instance.user,
                notification_type=FinanceNotification.NotificationType.SUCCESS,
                title='Credit Sale Fully Paid',
                message=f'Your credit sale for ticket {instance.ticket_sale.ticket_number} has been fully paid.',
                ticket_sale=instance.ticket_sale
            )
        
        # Check if payment is overdue
        elif instance.is_overdue and instance.payment_status in [instance.PaymentStatus.PENDING, instance.PaymentStatus.PARTIAL]:
            # Create notification for overdue payment
            FinanceNotification.objects.create(
                user=instance.user,
                notification_type=FinanceNotification.NotificationType.WARNING,
                title='Payment Overdue',
                message=f'Your payment for ticket {instance.ticket_sale.ticket_number} is overdue by {instance.days_overdue} days.',
                ticket_sale=instance.ticket_sale
            )