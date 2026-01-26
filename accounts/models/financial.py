# accounts/models/financial.py
"""
Financial models for B2B Travel Mushqila - Saudi Arabia
Payments, invoices, refunds, commissions - Production ready
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class Payment(models.Model):
    """Payment model"""
    
    class PaymentMethod(models.TextChoices):
        MADA = 'mada', _('Mada')
        VISA = 'visa', _('Visa')
        MASTERCARD = 'mastercard', _('MasterCard')
        APPLE_PAY = 'apple_pay', _('Apple Pay')
        STC_PAY = 'stc_pay', _('STC Pay')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        WALLET = 'wallet', _('Wallet')
        CASH = 'cash', _('Cash')
        CHEQUE = 'cheque', _('Cheque')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SUCCESS = 'success', _('Success')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded')
        PARTIAL_REFUND = 'partial_refund', _('Partially Refunded')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_id = models.CharField(_('payment ID'), max_length=50, unique=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts_payments')
    
    amount = models.DecimalField(_('amount'), max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(_('VAT amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_('total amount'), max_digits=12, decimal_places=2)
    
    payment_method = models.CharField(_('payment method'), max_length=50, choices=PaymentMethod.choices)
    status = models.CharField(_('status'), max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    reference_number = models.CharField(_('reference number'), max_length=100, blank=True)
    transaction_id = models.CharField(_('transaction ID'), max_length=100, blank=True)
    bank_name = models.CharField(_('bank name'), max_length=100, blank=True)
    cheque_number = models.CharField(_('cheque number'), max_length=50, blank=True)
    
    description = models.TextField(_('description'), blank=True)
    description_ar = models.TextField(_('description (Arabic)'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        return f"{self.payment_id} - {self.user.email} - {self.total_amount} SAR"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            import time
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:6].upper()
            self.payment_id = f"PAY{timestamp}{unique_id}"
        
        if not self.total_amount:
            self.total_amount = self.amount + self.vat_amount
        
        if self.status == self.PaymentStatus.SUCCESS and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """Invoice model"""
    
    class InvoiceStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ISSUED = 'issued', _('Issued')
        PAID = 'paid', _('Paid')
        OVERDUE = 'overdue', _('Overdue')
        CANCELLED = 'cancelled', _('Cancelled')
        PARTIAL_PAID = 'partial_paid', _('Partially Paid')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(_('invoice number'), max_length=50, unique=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts_invoices')
    
    flight_booking = models.ForeignKey('FlightBooking', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_invoices')
    hotel_booking = models.ForeignKey('HotelBooking', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_invoices')
    hajj_package = models.ForeignKey('HajjPackage', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_invoices')
    umrah_package = models.ForeignKey('UmrahPackage', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_invoices')
    
    subtotal = models.DecimalField(_('subtotal'), max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(_('VAT amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_('total amount'), max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(_('paid amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_('status'), max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    issue_date = models.DateField(_('issue date'), default=timezone.now)
    due_date = models.DateField(_('due date'))
    payment_date = models.DateField(_('payment date'), null=True, blank=True)
    
    notes = models.TextField(_('notes'), blank=True)
    notes_ar = models.TextField(_('notes (Arabic)'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = timezone.now().year
            month = timezone.now().strftime('%m')
            
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{year}-{month}-'
            ).order_by('invoice_number').last()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.invoice_number = f"INV-{year}-{month}-{new_number:04d}"
        
        if not self.due_date:
            self.due_date = self.issue_date + timezone.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def update_payment_status(self):
        """Update invoice payment status"""
        if self.paid_amount >= self.total_amount:
            self.status = self.InvoiceStatus.PAID
            if not self.payment_date:
                self.payment_date = timezone.now()
        elif self.paid_amount > 0:
            self.status = self.InvoiceStatus.PARTIAL_PAID
        elif timezone.now().date() > self.due_date:
            self.status = self.InvoiceStatus.OVERDUE
        else:
            self.status = self.InvoiceStatus.ISSUED
        
        self.save()


class Refund(models.Model):
    """Refund model"""
    
    class RefundStatus(models.TextChoices):
        REQUESTED = 'requested', _('Requested')
        APPROVED = 'approved', _('Approved')
        PROCESSED = 'processed', _('Processed')
        REJECTED = 'rejected', _('Rejected')
        CANCELLED = 'cancelled', _('Cancelled')
    
    class RefundMethod(models.TextChoices):
        WALLET = 'wallet', _('Wallet Credit')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        ORIGINAL_PAYMENT = 'original_payment', _('Original Payment Method')
        CHEQUE = 'cheque', _('Cheque')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refund_id = models.CharField(_('refund ID'), max_length=50, unique=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts_refunds')
    
    flight_booking = models.ForeignKey('FlightBooking', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_refunds')
    hotel_booking = models.ForeignKey('HotelBooking', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_refunds')
    
    original_payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_refunds')
    refund_amount = models.DecimalField(_('refund amount'), max_digits=12, decimal_places=2)
    refund_method = models.CharField(_('refund method'), max_length=30, choices=RefundMethod.choices)
    
    status = models.CharField(_('status'), max_length=20, choices=RefundStatus.choices, default=RefundStatus.REQUESTED)
    reason = models.TextField(_('reason'))
    admin_notes = models.TextField(_('admin notes'), blank=True)
    
    requested_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_requested_refunds')
    
    # ✅ FIXED: related_name আপডেট
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='accounts_approved_refunds')
    
    processed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='accounts_processed_refunds')
    
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('refund')
        verbose_name_plural = _('refunds')
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.refund_id} - {self.user.email} - {self.refund_amount} SAR"
    
    def save(self, *args, **kwargs):
        if not self.refund_id:
            import time
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:6].upper()
            self.refund_id = f"REF{timestamp}{unique_id}"
        
        if self.status == self.RefundStatus.APPROVED and not self.approved_at:
            self.approved_at = timezone.now()
        elif self.status == self.RefundStatus.PROCESSED and not self.processed_at:
            self.processed_at = timezone.now()
        
        super().save(*args, **kwargs)


class CommissionTransaction(models.Model):
    """Commission transactions"""
    
    class CommissionStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        EARNED = 'earned', _('Earned')
        PAID = 'paid', _('Paid')
        CANCELLED = 'cancelled', _('Cancelled')
        FORFEITED = 'forfeited', _('Forfeited')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(_('transaction ID'), max_length=50, unique=True)
    agent = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts_commission_transactions')
    
    booking = models.ForeignKey('FlightBooking', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_commissions')
    hotel_booking = models.ForeignKey('HotelBooking', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_commissions')
    hajj_booking = models.ForeignKey('HajjPackage', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts_commissions')
    
    amount = models.DecimalField(_('amount'), max_digits=12, decimal_places=2)
    commission_rate = models.DecimalField(_('commission rate'), max_digits=5, decimal_places=2)
    status = models.CharField(_('status'), max_length=20, choices=CommissionStatus.choices, default=CommissionStatus.PENDING)
    
    payment_date = models.DateField(_('payment date'), null=True, blank=True)
    remarks = models.TextField(_('remarks'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('commission transaction')
        verbose_name_plural = _('commission transactions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commission: {self.agent.email} - {self.amount} SAR"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import time
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:6].upper()
            self.transaction_id = f"COM{timestamp}{unique_id}"
        
        super().save(*args, **kwargs)