# accounts/models/core.py
"""
Core models for B2B Travel Mushqila - Saudi Arabia
Fixed and production ready
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from django.core.mail import send_mail
import random
import string
from decimal import Decimal


class CustomUserManager(BaseUserManager):
    """Custom manager for User model"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', User.UserType.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class SaudiRegion(models.Model):
    """Saudi Arabia regions"""
    
    class Region(models.TextChoices):
        RIYADH = 'riyadh', _('Riyadh Province')
        MAKKAH = 'makkah', _('Makkah Province')
        MADINAH = 'madinah', _('Madinah Province')
        EASTERN = 'eastern', _('Eastern Province')
        ASIR = 'asir', _('Asir Province')
        TABUK = 'tabuk', _('Tabuk Province')
        HAIL = 'hail', _('Hail Province')
        NORTHERN_BORDERS = 'northern_borders', _('Northern Borders Province')
        JIZAN = 'jizan', _('Jizan Province')
        NAJRAN = 'najran', _('Najran Province')
        AL_BAHAH = 'al_bahah', _('Al Bahah Province')
        AL_JOUF = 'al_jouf', _('Al Jouf Province')
        QASSIM = 'qassim', _('Qassim Province')
    
    region_code = models.CharField(max_length=20, choices=Region.choices, unique=True)
    name_ar = models.CharField(_('name (Arabic)'), max_length=100)
    name_en = models.CharField(_('name (English)'), max_length=100)
    capital_ar = models.CharField(_('capital (Arabic)'), max_length=100)
    capital_en = models.CharField(_('capital (English)'), max_length=100)
    is_active = models.BooleanField(_('is active'), default=True)
    
    class Meta:
        verbose_name = _('Saudi region')
        verbose_name_plural = _('Saudi regions')
        ordering = ['name_en']
    
    def __str__(self):
        return f"{self.name_en} ({self.region_code})"


class SaudiCity(models.Model):
    """Saudi Arabia cities"""
    
    region = models.ForeignKey(SaudiRegion, on_delete=models.CASCADE, related_name='cities')
    name_ar = models.CharField(_('name (Arabic)'), max_length=100)
    name_en = models.CharField(_('name (English)'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=10, blank=True)
    is_major_city = models.BooleanField(_('is major city'), default=False)
    is_hajj_city = models.BooleanField(_('is hajj city'), default=False)
    is_umrah_city = models.BooleanField(_('is umrah city'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Saudi city')
        verbose_name_plural = _('Saudi cities')
        ordering = ['name_en']
    
    def __str__(self):
        return f"{self.name_en} ({self.region.name_en})"


class User(AbstractUser):
    """Custom User Model for B2B Travel Argentina - Saudi Arabia"""
    
    class UserType(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        SUPER_AGENT = 'super_agent', _('Super Agent')
        AGENT = 'agent', _('Travel Agent')
        SUB_AGENT = 'sub_agent', _('Sub Agent')
        SUPPLIER = 'supplier', _('Service Supplier')
        CORPORATE = 'corporate', _('Corporate Client')
        PILGRIM = 'pilgrim', _('Pilgrim Service Provider')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
        PENDING = 'pending', _('Pending')
        BLOCKED = 'blocked', _('Blocked')
        UNDER_REVIEW = 'under_review', _('Under Review')
    
    # Authentication
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=150, blank=True)
    
    # Saudi phone format
    phone_regex = RegexValidator(
        regex=r'^\+9665\d{8}$',
        message=_("Phone number must be in format: '+9665XXXXXXXX'")
    )
    phone = models.CharField(
        _('phone number'),
        max_length=15,
        unique=True,
        validators=[phone_regex],
        help_text=_('Saudi format: +9665XXXXXXXX')
    )
    
    # User type and status
    user_type = models.CharField(_('user type'), max_length=20, choices=UserType.choices, default=UserType.AGENT)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Company Information
    company_name_ar = models.CharField(_('company name (Arabic)'), max_length=255, blank=True)
    company_name_en = models.CharField(_('company name (English)'), max_length=255, blank=True)
    company_registration = models.CharField(_('CR Number'), max_length=50, blank=True, unique=True, null=True)
    vat_number = models.CharField(_('VAT Number'), max_length=15, blank=True)
    
    # Financial
    credit_limit = models.DecimalField(_('credit limit'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_balance = models.DecimalField(_('current balance'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    wallet_balance = models.DecimalField(_('wallet balance'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    commission_rate = models.DecimalField(_('commission rate'), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Referral system
    referral_code = models.CharField(_('referral code'), max_length=20, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    # Saudi specific licenses
    scta_license = models.CharField(_('SCTA License'), max_length=50, blank=True)
    hajj_license = models.CharField(_('Hajj License'), max_length=50, blank=True)
    iata_number = models.CharField(_('IATA Number'), max_length=20, blank=True)
    
    # Verification
    email_verified = models.BooleanField(_('email verified'), default=False)
    phone_verified = models.BooleanField(_('phone verified'), default=False)
    kyc_verified = models.BooleanField(_('KYC verified'), default=False)
    kyc_submitted = models.DateTimeField(_('KYC submitted'), null=True, blank=True)
    
    # Address
    city = models.ForeignKey(SaudiCity, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    address_ar = models.TextField(_('address (Arabic)'), blank=True)
    address_en = models.TextField(_('address (English)'), blank=True)
    
    # Timestamps
    last_login_ip = models.GenericIPAddressField(_('last login IP'), null=True, blank=True)
    last_activity = models.DateTimeField(_('last activity'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['user_type', 'status']),
            models.Index(fields=['referral_code']),
            models.Index(fields=['company_registration']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if not self.referral_code and self.is_agent():
            self.generate_referral_code()
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        """Generate unique referral code"""
        while True:
            code = 'SA' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not User.objects.filter(referral_code=code).exists():
                self.referral_code = code
                break
    
    def is_agent(self):
        """Check if user is an agent"""
        return self.user_type in [self.UserType.SUPER_AGENT, self.UserType.AGENT, self.UserType.SUB_AGENT]
    
    def available_credit(self):
        """Calculate available credit"""
        return max(Decimal('0.00'), self.credit_limit + self.current_balance)
    
    def get_company_name(self, language='en'):
        """Get company name in specified language"""
        if language == 'ar' and self.company_name_ar:
            return self.company_name_ar
        return self.company_name_en or self.company_name_ar or self.get_full_name()


class UserProfile(models.Model):
    """Extended user profile"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Business Information
    business_type = models.CharField(_('business type'), max_length=50, blank=True)
    years_in_business = models.IntegerField(_('years in business'), default=0)
    
    # Bank Information
    bank_name_ar = models.CharField(_('bank name (Arabic)'), max_length=100, blank=True)
    bank_name_en = models.CharField(_('bank name (English)'), max_length=100, blank=True)
    account_number = models.CharField(_('account number'), max_length=50, blank=True)
    iban = models.CharField(_('IBAN'), max_length=24, blank=True)
    
    # Statistics
    total_bookings = models.IntegerField(_('total bookings'), default=0)
    total_sales = models.DecimalField(_('total sales'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_commission = models.DecimalField(_('total commission'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    hajj_bookings = models.IntegerField(_('hajj bookings'), default=0)
    umrah_bookings = models.IntegerField(_('umrah bookings'), default=0)
    
    # Settings
    language = models.CharField(_('language'), max_length=10, choices=[('en', 'English'), ('ar', 'Arabic')], default='en')
    timezone = models.CharField(_('timezone'), max_length=50, default='Asia/Riyadh')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"Profile: {self.user.email}"


class Transaction(models.Model):
    """Transaction history"""
    
    class TransactionType(models.TextChoices):
        DEPOSIT = 'deposit', _('Deposit')
        WITHDRAWAL = 'withdrawal', _('Withdrawal')
        BOOKING = 'booking', _('Booking')
        HAJJ = 'hajj', _('Hajj Booking')
        UMRAH = 'umrah', _('Umrah Booking')
        REFUND = 'refund', _('Refund')
        COMMISSION = 'commission', _('Commission')
        ADJUSTMENT = 'adjustment', _('Adjustment')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=50, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='SAR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.TextField(blank=True)
    description_ar = models.TextField(_('description (Arabic)'), blank=True)
    reference = models.CharField(max_length=100, blank=True)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(_('VAT Amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.email} - {self.amount} SAR"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import uuid
            import time
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8].upper()
            self.transaction_id = f"TRX{timestamp}{unique_id}"
        super().save(*args, **kwargs)


class Notification(models.Model):
    """User notifications"""
    
    class NotificationType(models.TextChoices):
        INFO = 'info', _('Information')
        SUCCESS = 'success', _('Success')
        WARNING = 'warning', _('Warning')
        ERROR = 'error', _('Error')
        BOOKING = 'booking', _('Booking')
        HAJJ = 'hajj', _('Hajj')
        UMRAH = 'umrah', _('Umrah')
        PAYMENT = 'payment', _('Payment')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.INFO)
    title = models.CharField(max_length=255)
    title_ar = models.CharField(_('title (Arabic)'), max_length=255, blank=True)
    message = models.TextField()
    message_ar = models.TextField(_('message (Arabic)'), blank=True)
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class UserActivityLog(models.Model):
    """User activity logging"""
    
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        REGISTRATION = 'registration', _('Registration')
        PROFILE_UPDATE = 'profile_update', _('Profile Update')
        BOOKING = 'booking', _('Booking')
        PAYMENT = 'payment', _('Payment')
        KYC = 'kyc', _('KYC Submission')
        DOCUMENT = 'document', _('Document Upload')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs', null=True, blank=True)
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('user activity log')
        verbose_name_plural = _('user activity logs')
        ordering = ['-created_at']
    
    def __str__(self):
        user_info = self.user.email if self.user else 'Anonymous'
        return f"{user_info} - {self.activity_type}"