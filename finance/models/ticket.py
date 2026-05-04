from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Airline(models.Model):
    """Airline model for ticket sales"""
    
    code = models.CharField(_('airline code'), max_length=5, unique=True)
    name = models.CharField(_('airline name'), max_length=120)
    name_ar = models.CharField(_('airline name (Arabic)'), max_length=120, blank=True)
    country = models.CharField(_('country'), max_length=100, blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Airline')
        verbose_name_plural = _('Airlines')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class PaymentMethod(models.Model):
    """Payment method options"""
    
    class MethodType(models.TextChoices):
        BANK = 'bank', _('Bank Transfer')
        SPAN = 'span', _('SPAN')
        BKASH = 'bkash', _('bKash')
        NAGAD = 'nagad', _('Nagad')
        CASH = 'cash', _('Cash')
        CARD = 'card', _('Credit/Debit Card')
        OTHER = 'other', _('Other')
    
    name = models.CharField(_('method name'), max_length=50, choices=MethodType.choices, unique=True)
    name_ar = models.CharField(_('method name (Arabic)'), max_length=50, blank=True)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class TicketSale(models.Model):
    """Ticket sale model for finance tracking"""
    
    class SaleStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ISSUED = 'issued', _('Issued')
        CANCELLED = 'cancelled', _('Cancelled')
    
    class SaleType(models.TextChoices):
        CASH = 'cash', _('Cash Sale')
        CREDIT = 'credit', _('Credit Sale')
    
    # Basic Information
    user = models.ForeignKey('FinanceUser', on_delete=models.PROTECT, related_name='ticket_sales')
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name='ticket_sales')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name='ticket_sales')
    
    # Ticket Details
    pnr = models.CharField(_('PNR'), max_length=20)
    ticket_number = models.CharField(_('ticket number'), max_length=30, unique=True)
    passenger_name = models.CharField(_('passenger name'), max_length=120)
    route = models.CharField(_('route'), max_length=120, blank=True)
    travel_date = models.DateField(_('travel date'), null=True, blank=True)
    
    # Financial Details
    purchase_price = models.DecimalField(
        _('purchase price'), 
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    selling_price = models.DecimalField(
        _('selling price'), 
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    commission_amount = models.DecimalField(
        _('commission amount'), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        _('tax amount'), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Status and Type
    sale_type = models.CharField(_('sale type'), max_length=20, choices=SaleType.choices, default=SaleType.CASH)
    status = models.CharField(_('status'), max_length=20, choices=SaleStatus.choices, default=SaleStatus.PENDING)
    
    # Credit Sale Specific Fields
    deposit_amount = models.DecimalField(
        _('deposit amount'), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        blank=True,
        null=True
    )
    due_amount = models.DecimalField(
        _('due amount'), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        blank=True,
        null=True
    )
    due_date = models.DateField(_('due date'), null=True, blank=True)
    
    # Additional Information
    remarks = models.TextField(_('remarks'), blank=True)
    reference_number = models.CharField(_('reference number'), max_length=50, blank=True)
    
    # Timestamps
    issue_date = models.DateField(_('issue date'), auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Ticket Sale')
        verbose_name_plural = _('Ticket Sales')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['airline']),
            models.Index(fields=['sale_type']),
            models.Index(fields=['issue_date']),
        ]

    def __str__(self):
        return f"{self.ticket_number} - {self.passenger_name} ({self.get_status_display()})"
    
    @property
    def profit_amount(self):
        """Calculate profit amount"""
        return self.selling_price - self.purchase_price
    
    @property
    def total_amount(self):
        """Calculate total amount including tax"""
        return self.selling_price + self.tax_amount
    
    def save(self, *args, **kwargs):
        # Auto-calculate due amount for credit sales
        if self.sale_type == self.SaleType.CREDIT:
            self.due_amount = self.total_amount - (self.deposit_amount or Decimal('0.00'))
        else:
            self.due_amount = Decimal('0.00')
        
        # Auto-calculate commission if not set
        if not self.commission_amount:
            self.commission_amount = self.profit_amount
        
        super().save(*args, **kwargs)
