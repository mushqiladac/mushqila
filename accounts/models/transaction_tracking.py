# accounts/models/transaction_tracking.py
"""
Automated Transaction Tracking System
Real-time tracking of all ticketing operations with automatic accounting updates
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class TransactionLog(models.Model):
    """
    Central transaction log for all ticketing operations
    Automatically tracks: Issue, Void, Cancel, Refund, Reissue
    """
    
    class TransactionType(models.TextChoices):
        TICKET_ISSUE = 'ticket_issue', _('Ticket Issue')
        TICKET_VOID = 'ticket_void', _('Ticket Void')
        TICKET_CANCEL = 'ticket_cancel', _('Ticket Cancel')
        TICKET_REFUND = 'ticket_refund', _('Ticket Refund')
        TICKET_REISSUE = 'ticket_reissue', _('Ticket Reissue')
        PAYMENT_RECEIVED = 'payment_received', _('Payment Received')
        PAYMENT_REFUNDED = 'payment_refunded', _('Payment Refunded')
        COMMISSION_EARNED = 'commission_earned', _('Commission Earned')
        COMMISSION_PAID = 'commission_paid', _('Commission Paid')
        ANCILLARY_PURCHASE = 'ancillary_purchase', _('Ancillary Purchase')
        ANCILLARY_REFUND = 'ancillary_refund', _('Ancillary Refund')
        EMD_ISSUE = 'emd_issue', _('EMD Issue')
        EMD_VOID = 'emd_void', _('EMD Void')
        EMD_REFUND = 'emd_refund', _('EMD Refund')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        REVERSED = 'reversed', _('Reversed')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_number = models.CharField(_('Transaction Number'), max_length=50, unique=True, db_index=True)
    
    # Transaction details
    transaction_type = models.CharField(_('Transaction Type'), max_length=30, 
                                       choices=TransactionType.choices, db_index=True)
    status = models.CharField(_('Status'), max_length=20, choices=Status.choices, 
                            default=Status.PENDING, db_index=True)
    
    # Related entities
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction_logs',
                             limit_choices_to={'user_type__in': ['agent', 'super_agent']})
    booking = models.ForeignKey('flights.Booking', on_delete=models.CASCADE, 
                               related_name='transaction_logs', null=True, blank=True)
    
    # Financial details
    base_amount = models.DecimalField(_('Base Amount'), max_digits=12, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])
    tax_amount = models.DecimalField(_('Tax Amount'), max_digits=12, decimal_places=2,
                                    default=Decimal('0.00'))
    fee_amount = models.DecimalField(_('Fee Amount'), max_digits=12, decimal_places=2,
                                    default=Decimal('0.00'))
    commission_amount = models.DecimalField(_('Commission Amount'), max_digits=12, decimal_places=2,
                                          default=Decimal('0.00'))
    total_amount = models.DecimalField(_('Total Amount'), max_digits=12, decimal_places=2,
                                      validators=[MinValueValidator(Decimal('0.00'))])
    
    # Currency
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Description and notes
    description = models.TextField(_('Description'))
    notes = models.TextField(_('Notes'), blank=True)
    
    # Accounting integration
    accounting_posted = models.BooleanField(_('Posted to Accounting'), default=False)
    accounting_posted_at = models.DateTimeField(_('Posted At'), null=True, blank=True)
    journal_entry_reference = models.CharField(_('Journal Entry Reference'), max_length=50, 
                                              blank=True, db_index=True)
    
    # Reversal tracking
    is_reversed = models.BooleanField(_('Is Reversed'), default=False)
    reversed_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reverses')
    reversed_at = models.DateTimeField(_('Reversed At'), null=True, blank=True)
    
    # Metadata
    transaction_date = models.DateTimeField(_('Transaction Date'), default=timezone.now, db_index=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='processed_transactions')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional data (JSON for flexibility)
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Transaction Log')
        verbose_name_plural = _('Transaction Logs')
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['agent', 'transaction_date']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['booking', 'transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()} - {self.total_amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Auto-generate transaction number if not set
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()
        
        # Calculate total if not set
        if not self.total_amount:
            self.total_amount = self.base_amount + self.tax_amount + self.fee_amount
        
        super().save(*args, **kwargs)
    
    def generate_transaction_number(self):
        """Generate unique transaction number"""
        from datetime import datetime
        prefix = {
            'ticket_issue': 'TI',
            'ticket_void': 'TV',
            'ticket_cancel': 'TC',
            'ticket_refund': 'TR',
            'ticket_reissue': 'TRE',
            'payment_received': 'PR',
            'payment_refunded': 'PRF',
            'commission_earned': 'CE',
            'commission_paid': 'CP',
            'ancillary_purchase': 'AP',
            'ancillary_refund': 'AR',
            'emd_issue': 'EI',
            'emd_void': 'EV',
            'emd_refund': 'ER',
        }.get(self.transaction_type, 'TX')
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}{timestamp}{str(uuid.uuid4())[:8].upper()}"


class AgentLedger(models.Model):
    """
    Agent-wise ledger for tracking all financial transactions
    Automatically updated when transactions occur
    """
    
    class EntryType(models.TextChoices):
        DEBIT = 'debit', _('Debit')
        CREDIT = 'credit', _('Credit')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ledger_entries',
                             limit_choices_to={'user_type__in': ['agent', 'super_agent']})
    
    # Entry details
    entry_date = models.DateField(_('Entry Date'), default=timezone.now, db_index=True)
    entry_type = models.CharField(_('Entry Type'), max_length=10, choices=EntryType.choices)
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2,
                               validators=[MinValueValidator(Decimal('0.01'))])
    
    # Running balance
    balance_before = models.DecimalField(_('Balance Before'), max_digits=12, decimal_places=2,
                                        default=Decimal('0.00'))
    balance_after = models.DecimalField(_('Balance After'), max_digits=12, decimal_places=2,
                                       default=Decimal('0.00'))
    
    # Reference
    transaction_log = models.ForeignKey(TransactionLog, on_delete=models.CASCADE,
                                       related_name='ledger_entries')
    description = models.TextField(_('Description'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Agent Ledger Entry')
        verbose_name_plural = _('Agent Ledger Entries')
        ordering = ['-entry_date', '-created_at']
        indexes = [
            models.Index(fields=['agent', 'entry_date']),
            models.Index(fields=['agent', 'entry_type']),
        ]
    
    def __str__(self):
        return f"{self.agent.get_full_name()} - {self.entry_type} - {self.amount}"


class DailyTransactionSummary(models.Model):
    """
    Daily summary of all transactions per agent
    Automatically generated at end of day
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_summaries',
                             limit_choices_to={'user_type__in': ['agent', 'super_agent']})
    summary_date = models.DateField(_('Summary Date'), db_index=True)
    
    # Transaction counts
    tickets_issued = models.IntegerField(_('Tickets Issued'), default=0)
    tickets_voided = models.IntegerField(_('Tickets Voided'), default=0)
    tickets_cancelled = models.IntegerField(_('Tickets Cancelled'), default=0)
    tickets_refunded = models.IntegerField(_('Tickets Refunded'), default=0)
    tickets_reissued = models.IntegerField(_('Tickets Reissued'), default=0)
    
    # Financial summary
    total_sales = models.DecimalField(_('Total Sales'), max_digits=12, decimal_places=2,
                                     default=Decimal('0.00'))
    total_refunds = models.DecimalField(_('Total Refunds'), max_digits=12, decimal_places=2,
                                       default=Decimal('0.00'))
    total_commissions = models.DecimalField(_('Total Commissions'), max_digits=12, decimal_places=2,
                                           default=Decimal('0.00'))
    net_revenue = models.DecimalField(_('Net Revenue'), max_digits=12, decimal_places=2,
                                     default=Decimal('0.00'))
    
    # Opening and closing balance
    opening_balance = models.DecimalField(_('Opening Balance'), max_digits=12, decimal_places=2,
                                         default=Decimal('0.00'))
    closing_balance = models.DecimalField(_('Closing Balance'), max_digits=12, decimal_places=2,
                                         default=Decimal('0.00'))
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Daily Transaction Summary')
        verbose_name_plural = _('Daily Transaction Summaries')
        ordering = ['-summary_date', 'agent']
        unique_together = ['agent', 'summary_date']
        indexes = [
            models.Index(fields=['agent', 'summary_date']),
            models.Index(fields=['summary_date']),
        ]
    
    def __str__(self):
        return f"{self.agent.get_full_name()} - {self.summary_date}"


class MonthlyAgentReport(models.Model):
    """
    Monthly consolidated report for each agent
    Automatically generated at month end
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_reports',
                             limit_choices_to={'user_type__in': ['agent', 'super_agent']})
    
    # Period
    year = models.IntegerField(_('Year'))
    month = models.IntegerField(_('Month'))
    period_start = models.DateField(_('Period Start'))
    period_end = models.DateField(_('Period End'))
    
    # Transaction statistics
    total_transactions = models.IntegerField(_('Total Transactions'), default=0)
    tickets_issued = models.IntegerField(_('Tickets Issued'), default=0)
    tickets_voided = models.IntegerField(_('Tickets Voided'), default=0)
    tickets_cancelled = models.IntegerField(_('Tickets Cancelled'), default=0)
    tickets_refunded = models.IntegerField(_('Tickets Refunded'), default=0)
    
    # Financial summary
    gross_sales = models.DecimalField(_('Gross Sales'), max_digits=12, decimal_places=2,
                                     default=Decimal('0.00'))
    total_refunds = models.DecimalField(_('Total Refunds'), max_digits=12, decimal_places=2,
                                       default=Decimal('0.00'))
    net_sales = models.DecimalField(_('Net Sales'), max_digits=12, decimal_places=2,
                                   default=Decimal('0.00'))
    
    # Commission details
    commission_earned = models.DecimalField(_('Commission Earned'), max_digits=12, decimal_places=2,
                                           default=Decimal('0.00'))
    commission_paid = models.DecimalField(_('Commission Paid'), max_digits=12, decimal_places=2,
                                         default=Decimal('0.00'))
    net_commission = models.DecimalField(_('Net Commission'), max_digits=12, decimal_places=2,
                                        default=Decimal('0.00'))
    
    # Balance
    opening_balance = models.DecimalField(_('Opening Balance'), max_digits=12, decimal_places=2,
                                         default=Decimal('0.00'))
    closing_balance = models.DecimalField(_('Closing Balance'), max_digits=12, decimal_places=2,
                                         default=Decimal('0.00'))
    
    # Report data (detailed breakdown in JSON)
    detailed_data = models.JSONField(_('Detailed Data'), default=dict)
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='generated_monthly_reports')
    
    class Meta:
        verbose_name = _('Monthly Agent Report')
        verbose_name_plural = _('Monthly Agent Reports')
        ordering = ['-year', '-month', 'agent']
        unique_together = ['agent', 'year', 'month']
        indexes = [
            models.Index(fields=['agent', 'year', 'month']),
            models.Index(fields=['year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.agent.get_full_name()} - {self.year}/{self.month:02d}"


class TransactionAuditLog(models.Model):
    """
    Audit trail for all transaction changes
    Immutable log for compliance and tracking
    """
    
    class ActionType(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        REVERSE = 'reverse', _('Reverse')
        POST_ACCOUNTING = 'post_accounting', _('Post to Accounting')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_log = models.ForeignKey(TransactionLog, on_delete=models.CASCADE,
                                       related_name='audit_logs')
    
    # Action details
    action_type = models.CharField(_('Action Type'), max_length=20, choices=ActionType.choices)
    action_description = models.TextField(_('Action Description'))
    
    # Before and after state
    state_before = models.JSONField(_('State Before'), null=True, blank=True)
    state_after = models.JSONField(_('State After'), null=True, blank=True)
    
    # User and timestamp
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # IP and user agent for security
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    class Meta:
        verbose_name = _('Transaction Audit Log')
        verbose_name_plural = _('Transaction Audit Logs')
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['transaction_log', 'performed_at']),
            models.Index(fields=['performed_by', 'performed_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_log.transaction_number} - {self.get_action_type_display()} - {self.performed_at}"
