# accounts/signals/transaction_signals.py
"""
Automated Transaction Signals
Automatically creates accounting entries when ticketing operations occur
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='flights.Ticket')
def handle_ticket_issue(sender, instance, created, **kwargs):
    """
    Automatically create transaction log and accounting entries when ticket is issued
    """
    # Only process when status changes to 'issued' and issue_date is set
    if instance.status == 'issued' and instance.issue_date:
        # Check if transaction already exists to avoid duplicates
        from accounts.models.transaction_tracking import TransactionLog
        
        existing = TransactionLog.objects.filter(
            transaction_type='ticket_issue',
            metadata__ticket_number=instance.ticket_number
        ).exists()
        
        if existing:
            return
        
        try:
            with transaction.atomic():
                from accounts.services.automated_accounting_service import AutomatedAccountingService
                
                # Get booking from booking_passenger
                booking = instance.booking_passenger.booking
                
                # Create transaction log
                trans_log = TransactionLog.objects.create(
                    transaction_type='ticket_issue',
                    status='completed',
                    agent=booking.agent,
                    booking=booking,
                    base_amount=instance.fare_amount,
                    tax_amount=instance.tax_amount,
                    fee_amount=Decimal('0.00'),
                    commission_amount=instance.commission_amount or Decimal('0.00'),
                    total_amount=instance.total_amount,
                    currency=instance.currency,
                    description=f"Ticket issued: {instance.ticket_number}",
                    transaction_date=instance.issue_date,
                    metadata={
                        'ticket_number': instance.ticket_number,
                        'pnr': instance.pnr.pnr_number if instance.pnr else '',
                        'passenger': str(instance.booking_passenger.passenger)
                    }
                )
                
                # Post to accounting
                accounting_service = AutomatedAccountingService()
                result = accounting_service.post_ticket_issue(trans_log)
                
                if result['success']:
                    trans_log.accounting_posted = True
                    trans_log.accounting_posted_at = timezone.now()
                    trans_log.journal_entry_reference = result['reference']
                    trans_log.save()
                    
                    logger.info(f"Ticket issue posted to accounting: {instance.ticket_number}")
                else:
                    logger.error(f"Failed to post ticket issue to accounting: {result.get('error')}")
                    
        except Exception as e:
            logger.error(f"Error handling ticket issue: {str(e)}", exc_info=True)


@receiver(post_save, sender='flights.Ticket')
def handle_ticket_void(sender, instance, created, **kwargs):
    """
    Automatically create reversal entries when ticket is voided
    """
    # Only process when status changes to 'voided' and void_date is set
    if not created and instance.status == 'voided' and instance.void_date:
        # Check if void transaction already exists
        from accounts.models.transaction_tracking import TransactionLog
        
        existing = TransactionLog.objects.filter(
            transaction_type='ticket_void',
            metadata__ticket_number=instance.ticket_number
        ).exists()
        
        if existing:
            return
        
        try:
            with transaction.atomic():
                from accounts.services.automated_accounting_service import AutomatedAccountingService
                
                # Get booking from booking_passenger
                booking = instance.booking_passenger.booking
                
                # Find original issue transaction
                original_trans = TransactionLog.objects.filter(
                    metadata__ticket_number=instance.ticket_number,
                    transaction_type='ticket_issue',
                    is_reversed=False
                ).first()
                
                # Create void transaction
                void_trans = TransactionLog.objects.create(
                    transaction_type='ticket_void',
                    status='completed',
                    agent=booking.agent,
                    booking=booking,
                    base_amount=instance.fare_amount,
                    tax_amount=instance.tax_amount,
                    fee_amount=Decimal('0.00'),
                    commission_amount=instance.commission_amount or Decimal('0.00'),
                    total_amount=instance.total_amount,
                    currency=instance.currency,
                    description=f"Ticket voided: {instance.ticket_number}",
                    transaction_date=instance.void_date,
                    metadata={
                        'ticket_number': instance.ticket_number,
                        'pnr': instance.pnr.pnr_number if instance.pnr else '',
                        'void_date': instance.void_date.isoformat()
                    }
                )
                
                # Mark original as reversed
                if original_trans:
                    original_trans.is_reversed = True
                    original_trans.reversed_by = void_trans
                    original_trans.reversed_at = timezone.now()
                    original_trans.save()
                
                # Post to accounting
                accounting_service = AutomatedAccountingService()
                result = accounting_service.post_ticket_void(void_trans)
                
                if result['success']:
                    void_trans.accounting_posted = True
                    void_trans.accounting_posted_at = timezone.now()
                    void_trans.journal_entry_reference = result['reference']
                    void_trans.save()
                    
                    logger.info(f"Ticket void posted to accounting: {instance.ticket_number}")
                    
        except Exception as e:
            logger.error(f"Error handling ticket void: {str(e)}", exc_info=True)


@receiver(post_save, sender='flights.Ticket')
def handle_ticket_refund(sender, instance, created, **kwargs):
    """
    Automatically create refund entries when ticket is refunded
    """
    # Only process when status changes to 'refunded' and refund_date is set
    if not created and instance.status == 'refunded' and instance.refund_date:
        # Check if refund transaction already exists
        from accounts.models.transaction_tracking import TransactionLog
        
        existing = TransactionLog.objects.filter(
            transaction_type='ticket_refund',
            metadata__ticket_number=instance.ticket_number
        ).exists()
        
        if existing:
            return
        
        try:
            with transaction.atomic():
                from accounts.services.automated_accounting_service import AutomatedAccountingService
                
                # Get booking from booking_passenger
                booking = instance.booking_passenger.booking
                
                # Calculate refund amount (use total_amount as base, can be adjusted)
                refund_amount = instance.total_amount
                penalty_amount = Decimal('0.00')  # Can be calculated based on fare rules
                net_refund = refund_amount - penalty_amount
                
                # Create refund transaction
                refund_trans = TransactionLog.objects.create(
                    transaction_type='ticket_refund',
                    status='completed',
                    agent=booking.agent,
                    booking=booking,
                    base_amount=refund_amount,
                    tax_amount=Decimal('0.00'),
                    fee_amount=penalty_amount,
                    commission_amount=Decimal('0.00'),
                    total_amount=net_refund,
                    currency=instance.currency,
                    description=f"Ticket refunded: {instance.ticket_number}",
                    notes=f"Refund amount: {refund_amount}, Penalty: {penalty_amount}",
                    transaction_date=instance.refund_date,
                    metadata={
                        'ticket_number': instance.ticket_number,
                        'pnr': instance.pnr.pnr_number if instance.pnr else '',
                        'refund_amount': str(refund_amount),
                        'penalty_amount': str(penalty_amount),
                        'net_refund': str(net_refund),
                        'refund_date': instance.refund_date.isoformat()
                    }
                )
                
                # Post to accounting
                accounting_service = AutomatedAccountingService()
                result = accounting_service.post_ticket_refund(refund_trans)
                
                if result['success']:
                    refund_trans.accounting_posted = True
                    refund_trans.accounting_posted_at = timezone.now()
                    refund_trans.journal_entry_reference = result['reference']
                    refund_trans.save()
                    
                    logger.info(f"Ticket refund posted to accounting: {instance.ticket_number}")
                    
        except Exception as e:
            logger.error(f"Error handling ticket refund: {str(e)}", exc_info=True)


@receiver(post_save, sender='flights.Payment')
def handle_payment_received(sender, instance, created, **kwargs):
    """
    Automatically create transaction log when payment is received
    """
    # Only process completed payments
    if instance.status in ['captured', 'authorized']:
        # Check if payment transaction already exists
        from accounts.models.transaction_tracking import TransactionLog
        
        existing = TransactionLog.objects.filter(
            transaction_type='payment_received',
            metadata__payment_reference=instance.payment_reference
        ).exists()
        
        if existing:
            return
        
        try:
            with transaction.atomic():
                from accounts.services.automated_accounting_service import AutomatedAccountingService
                
                # Create payment transaction
                payment_trans = TransactionLog.objects.create(
                    transaction_type='payment_received',
                    status='completed',
                    agent=instance.booking.agent,
                    booking=instance.booking,
                    base_amount=instance.amount,
                    tax_amount=Decimal('0.00'),
                    fee_amount=Decimal('0.00'),
                    commission_amount=Decimal('0.00'),
                    total_amount=instance.amount,
                    currency=instance.currency,
                    description=f"Payment received: {instance.get_payment_method_display()}",
                    transaction_date=instance.captured_at or timezone.now(),
                    metadata={
                        'payment_reference': instance.payment_reference,
                        'payment_method': instance.payment_method,
                        'gateway_transaction_id': instance.gateway_transaction_id or ''
                    }
                )
                
                # Post to accounting
                accounting_service = AutomatedAccountingService()
                result = accounting_service.post_payment_received(payment_trans)
                
                if result['success']:
                    payment_trans.accounting_posted = True
                    payment_trans.accounting_posted_at = timezone.now()
                    payment_trans.journal_entry_reference = result['reference']
                    payment_trans.save()
                    
                    logger.info(f"Payment posted to accounting: {instance.payment_reference}")
                    
        except Exception as e:
            logger.error(f"Error handling payment: {str(e)}", exc_info=True)


@receiver(post_save, sender='accounts.CommissionTransaction')
def handle_commission_transaction(sender, instance, created, **kwargs):
    """
    Automatically create transaction log for commission transactions
    """
    if created:
        try:
            with transaction.atomic():
                from accounts.models.transaction_tracking import TransactionLog
                from accounts.services.automated_accounting_service import AutomatedAccountingService
                
                trans_type = 'commission_earned' if instance.transaction_type == 'earned' else 'commission_paid'
                
                # Create commission transaction
                comm_trans = TransactionLog.objects.create(
                    transaction_type=trans_type,
                    status='completed',
                    agent=instance.agent,
                    base_amount=instance.amount,
                    tax_amount=Decimal('0.00'),
                    fee_amount=Decimal('0.00'),
                    commission_amount=instance.amount,
                    total_amount=instance.amount,
                    currency=instance.currency,
                    description=f"Commission {instance.transaction_type}: {instance.description}",
                    transaction_date=timezone.now(),
                    metadata={
                        'commission_id': str(instance.id),
                        'transaction_type': instance.transaction_type
                    }
                )
                
                # Post to accounting
                accounting_service = AutomatedAccountingService()
                result = accounting_service.post_commission_transaction(comm_trans)
                
                if result['success']:
                    comm_trans.accounting_posted = True
                    comm_trans.accounting_posted_at = timezone.now()
                    comm_trans.journal_entry_reference = result['reference']
                    comm_trans.save()
                    
                    logger.info(f"Commission posted to accounting: {instance.id}")
                    
        except Exception as e:
            logger.error(f"Error handling commission: {str(e)}", exc_info=True)


@receiver(post_save, sender='accounts.TransactionLog')
def update_agent_ledger(sender, instance, created, **kwargs):
    """
    Automatically update agent ledger when transaction is created
    """
    if created and instance.status == 'completed':
        try:
            with transaction.atomic():
                from accounts.models.transaction_tracking import AgentLedger
                
                # Get current balance
                last_entry = AgentLedger.objects.filter(
                    agent=instance.agent
                ).order_by('-entry_date', '-created_at').first()
                
                current_balance = last_entry.balance_after if last_entry else Decimal('0.00')
                
                # Determine entry type and calculate new balance
                if instance.transaction_type in ['ticket_issue', 'payment_received', 'commission_earned']:
                    entry_type = 'credit'
                    new_balance = current_balance + instance.total_amount
                else:  # void, cancel, refund, commission_paid
                    entry_type = 'debit'
                    new_balance = current_balance - instance.total_amount
                
                # Create ledger entry
                AgentLedger.objects.create(
                    agent=instance.agent,
                    entry_date=instance.transaction_date.date(),
                    entry_type=entry_type,
                    amount=instance.total_amount,
                    balance_before=current_balance,
                    balance_after=new_balance,
                    transaction_log=instance,
                    description=instance.description
                )
                
                logger.info(f"Agent ledger updated for {instance.agent.get_full_name()}")
                
        except Exception as e:
            logger.error(f"Error updating agent ledger: {str(e)}", exc_info=True)


@receiver(post_save, sender='accounts.TransactionLog')
def update_daily_summary(sender, instance, created, **kwargs):
    """
    Automatically update daily transaction summary
    """
    if created and instance.status == 'completed':
        try:
            with transaction.atomic():
                from accounts.models.transaction_tracking import DailyTransactionSummary
                from django.db.models import F
                
                summary_date = instance.transaction_date.date()
                
                # Get or create daily summary
                summary, created = DailyTransactionSummary.objects.get_or_create(
                    agent=instance.agent,
                    summary_date=summary_date,
                    defaults={
                        'opening_balance': Decimal('0.00'),
                        'closing_balance': Decimal('0.00')
                    }
                )
                
                # Update counters based on transaction type
                if instance.transaction_type == 'ticket_issue':
                    summary.tickets_issued = F('tickets_issued') + 1
                    summary.total_sales = F('total_sales') + instance.total_amount
                elif instance.transaction_type == 'ticket_void':
                    summary.tickets_voided = F('tickets_voided') + 1
                elif instance.transaction_type == 'ticket_cancel':
                    summary.tickets_cancelled = F('tickets_cancelled') + 1
                elif instance.transaction_type == 'ticket_refund':
                    summary.tickets_refunded = F('tickets_refunded') + 1
                    summary.total_refunds = F('total_refunds') + instance.total_amount
                elif instance.transaction_type == 'ticket_reissue':
                    summary.tickets_reissued = F('tickets_reissued') + 1
                elif instance.transaction_type in ['commission_earned', 'commission_paid']:
                    summary.total_commissions = F('total_commissions') + instance.commission_amount
                
                summary.save()
                
                # Refresh to get actual values
                summary.refresh_from_db()
                
                # Calculate net revenue
                summary.net_revenue = summary.total_sales - summary.total_refunds
                summary.save()
                
                logger.info(f"Daily summary updated for {instance.agent.get_full_name()} on {summary_date}")
                
        except Exception as e:
            logger.error(f"Error updating daily summary: {str(e)}", exc_info=True)


@receiver(post_save, sender='accounts.TransactionLog')
def create_audit_log(sender, instance, created, **kwargs):
    """
    Create audit log entry for every transaction change
    """
    try:
        from accounts.models.transaction_tracking import TransactionAuditLog
        
        action_type = 'create' if created else 'update'
        
        TransactionAuditLog.objects.create(
            transaction_log=instance,
            action_type=action_type,
            action_description=f"Transaction {action_type}d: {instance.transaction_number}",
            state_after={
                'status': instance.status,
                'total_amount': str(instance.total_amount),
                'accounting_posted': instance.accounting_posted
            },
            performed_by=instance.processed_by,
            performed_at=timezone.now()
        )
        
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}", exc_info=True)
