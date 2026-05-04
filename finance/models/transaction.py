from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class FinanceTransaction(models.Model):
    """Financial transaction tracking"""
    
    class TransactionType(models.TextChoices):
        SALE = 'sale', _('Ticket Sale')
        DEPOSIT = 'deposit', _('Deposit')
        WITHDRAWAL = 'withdrawal', _('Withdrawal')
        COMMISSION = 'commission', _('Commission')
        REFUND = 'refund', _('Refund')
        ADJUSTMENT = 'adjustment', _('Adjustment')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    user = models.ForeignKey('FinanceUser', on_delete=models.CASCADE, related_name='finance_transactions')
    ticket_sale = models.ForeignKey('TicketSale', on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    
    transaction_id = models.CharField(_('transaction ID'), max_length=50, unique=True)
    transaction_type = models.CharField(_('transaction type'), max_length=20, choices=TransactionType.choices)
    
    amount = models.DecimalField(_('amount'), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(_('currency'), max_length=3, default='SAR')
    
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PENDING)
    
    description = models.TextField(_('description'), blank=True)
    description_ar = models.TextField(_('description (Arabic)'), blank=True)
    reference = models.CharField(_('reference'), max_length=100, blank=True)
    
    # Balance tracking
    balance_before = models.DecimalField(_('balance before'), max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(_('balance after'), max_digits=12, decimal_places=2)
    
    # Additional metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Finance Transaction')
        verbose_name_plural = _('Finance Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.user.email} - {self.amount} SAR"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import uuid
            import time
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8].upper()
            self.transaction_id = f"FIN{timestamp}{unique_id}"
        super().save(*args, **kwargs)


class CreditSale(models.Model):
    """Credit sale management for receivables"""
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PARTIAL = 'partial', _('Partial Paid')
        PAID = 'paid', _('Fully Paid')
        OVERDUE = 'overdue', _('Overdue')
    
    ticket_sale = models.OneToOneField('TicketSale', on_delete=models.CASCADE, related_name='credit_sale')
    user = models.ForeignKey('FinanceUser', on_delete=models.CASCADE, related_name='credit_sales')
    
    # Credit details
    total_amount = models.DecimalField(_('total amount'), max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(_('paid amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    remaining_amount = models.DecimalField(_('remaining amount'), max_digits=12, decimal_places=2)
    
    # Payment schedule
    due_date = models.DateField(_('due date'))
    payment_status = models.CharField(_('payment status'), max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    # Tracking
    last_payment_date = models.DateField(_('last payment date'), null=True, blank=True)
    completed_date = models.DateField(_('completed date'), null=True, blank=True)
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Credit Sale')
        verbose_name_plural = _('Credit Sales')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['payment_status', 'due_date']),
        ]

    def __str__(self):
        return f"Credit Sale - {self.ticket_sale.ticket_number} ({self.get_payment_status_display()})"
    
    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        from django.utils import timezone
        return (
            self.payment_status in [self.PaymentStatus.PENDING, self.PaymentStatus.PARTIAL] and
            self.due_date < timezone.now().date()
        )
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            from django.utils import timezone
            return (timezone.now().date() - self.due_date).days
        return 0
    
    def save(self, *args, **kwargs):
        # Auto-calculate remaining amount
        self.remaining_amount = self.total_amount - self.paid_amount
        
        # Auto-update payment status
        if self.remaining_amount <= 0:
            self.payment_status = self.PaymentStatus.PAID
            if not self.completed_date:
                from django.utils import timezone
                self.completed_date = timezone.now().date()
        elif self.paid_amount > 0:
            self.payment_status = self.PaymentStatus.PARTIAL
        else:
            self.payment_status = self.PaymentStatus.PENDING
        
        super().save(*args, **kwargs)


class PaymentInstallment(models.Model):
    """Payment installments for credit sales"""
    
    credit_sale = models.ForeignKey(CreditSale, on_delete=models.CASCADE, related_name='installments')
    
    installment_number = models.PositiveIntegerField(_('installment number'))
    amount = models.DecimalField(_('amount'), max_digits=12, decimal_places=2)
    due_date = models.DateField(_('due date'))
    
    # Payment tracking
    paid_amount = models.DecimalField(_('paid amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_date = models.DateField(_('paid date'), null=True, blank=True)
    
    # Status
    is_paid = models.BooleanField(_('is paid'), default=False)
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Payment Installment')
        verbose_name_plural = _('Payment Installments')
        ordering = ['credit_sale', 'installment_number']
        unique_together = ('credit_sale', 'installment_number')

    def __str__(self):
        return f"Installment {self.installment_number} - {self.credit_sale.ticket_sale.ticket_number}"
