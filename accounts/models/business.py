# accounts/models/business.py
"""
Business and operational models for B2B Travel Argentina - Saudi Arabia
Fixed and production ready
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class Document(models.Model):
    """KYC Documents for users"""
    
    class DocumentType(models.TextChoices):
        PASSPORT = 'passport', _('Passport')
        SAUDI_ID = 'saudi_id', _('Saudi National ID')
        IQAMA = 'iqama', _('Iqama')
        DRIVING_LICENSE = 'driving_license', _('Driving License')
        TRADE_LICENSE = 'trade_license', _('Trade License')
        VAT_CERTIFICATE = 'vat_certificate', _('VAT Certificate')
        COMMERCIAL_REGISTRATION = 'commercial_registration', _('Commercial Registration')
        SCTA_LICENSE = 'scta_license', _('SCTA License')
        HAJJ_LICENSE = 'hajj_license', _('Hajj License')
        BANK_STATEMENT = 'bank_statement', _('Bank Statement')
        OTHER = 'other', _('Other')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        VERIFIED = 'verified', _('Verified')
        REJECTED = 'rejected', _('Rejected')
        EXPIRED = 'expired', _('Expired')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DocumentType.choices)
    document_number = models.CharField(max_length=100)
    document_file = models.FileField(upload_to='documents/%Y/%m/%d/')
    front_image = models.ImageField(upload_to='documents/front/%Y/%m/%d/', blank=True, null=True)
    back_image = models.ImageField(upload_to='documents/back/%Y/%m/%d/', blank=True, null=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'document_type']),
            models.Index(fields=['status', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_document_type_display()}"
    
    def is_valid(self):
        """Check if document is valid and not expired"""
        if self.status != self.Status.VERIFIED:
            return False
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False
        return True


class LoginHistory(models.Model):
    """User login history"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=2, blank=True, default='SA')
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('login history')
        verbose_name_plural = _('login histories')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else f"Failed: {self.failure_reason}"
        return f"{self.user.email} - {self.ip_address} - {status}"


class AgentHierarchy(models.Model):
    """Agent hierarchy structure"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_agent = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='children_agents',
        limit_choices_to={'user_type__in': ['super_agent', 'agent']}
    )
    child_agent = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='parent_hierarchy',
        limit_choices_to={'user_type__in': ['agent', 'sub_agent']}
    )
    hierarchy_level = models.IntegerField(_('Hierarchy Level'), default=1)
    commission_share = models.DecimalField(
        _('Commission Share'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Percentage of commission shared with parent agent')
    )
    is_active = models.BooleanField(_('is active'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('agent hierarchy')
        verbose_name_plural = _('agent hierarchies')
        unique_together = ['parent_agent', 'child_agent']
        indexes = [
            models.Index(fields=['parent_agent', 'is_active']),
            models.Index(fields=['child_agent']),
        ]
    
    def __str__(self):
        return f"{self.parent_agent.email} → {self.child_agent.email}"
    
    def calculate_shared_commission(self, commission_amount):
        """Calculate commission to be shared with parent"""
        return (commission_amount * self.commission_share) / Decimal('100')


class CreditRequest(models.Model):
    """Credit limit increase requests"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        UNDER_REVIEW = 'under_review', _('Under Review')
        CANCELLED = 'cancelled', _('Cancelled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='credit_requests')
    current_limit = models.DecimalField(_('Current Credit Limit'), max_digits=12, decimal_places=2)
    requested_limit = models.DecimalField(_('Requested Credit Limit'), max_digits=12, decimal_places=2)
    purpose = models.TextField(_('Purpose'), blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_credit_requests')
    review_notes = models.TextField(_('Review Notes'), blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('credit request')
        verbose_name_plural = _('credit requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.current_limit} → {self.requested_limit}"
    
    def get_increase_amount(self):
        """Get requested increase amount"""
        return self.requested_limit - self.current_limit
    
    def can_be_approved(self):
        """Check if credit request can be approved"""
        return (
            self.status == self.Status.PENDING and
            self.user.kyc_verified and
            self.user.status == 'active'
        )


class SMSCode(models.Model):
    """SMS verification codes for Saudi phone numbers"""
    
    class Purpose(models.TextChoices):
        LOGIN = 'login', _('Login')
        REGISTRATION = 'registration', _('Registration')
        PHONE_VERIFICATION = 'phone_verification', _('Phone Verification')
        PASSWORD_RESET = 'password_reset', _('Password Reset')
        TRANSACTION = 'transaction', _('Transaction')
        KYC = 'kyc', _('KYC Verification')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('SMS code')
        verbose_name_plural = _('SMS codes')
        indexes = [
            models.Index(fields=['phone', 'purpose', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.phone} - {self.code} - {self.purpose}"
    
    def is_expired(self):
        """Check if SMS code is expired"""
        return self.expires_at < timezone.now()


class IPWhitelist(models.Model):
    """IP whitelist for corporate users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='whitelisted_ips')
    ip_address = models.GenericIPAddressField()
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('IP whitelist')
        verbose_name_plural = _('IP whitelists')
        unique_together = ['user', 'ip_address']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"


class ComplianceCheck(models.Model):
    """Compliance checks for users"""
    
    class CheckType(models.TextChoices):
        KYC = 'kyc', _('KYC Check')
        AML = 'aml', _('AML Check')
        SANCTION = 'sanction', _('Sanction Check')
        PEP = 'pep', _('PEP Check')
        BACKGROUND = 'background', _('Background Check')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PASSED = 'passed', _('Passed')
        FAILED = 'failed', _('Failed')
        FLAGGED = 'flagged', _('Flagged')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='compliance_checks')
    check_type = models.CharField(max_length=20, choices=CheckType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    performed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_checks')
    performed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('compliance check')
        verbose_name_plural = _('compliance checks')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.check_type} - {self.status}"