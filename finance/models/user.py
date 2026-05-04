from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.mail import send_mail
import random
import string
from decimal import Decimal


class FinanceUserManager(BaseUserManager):
    """Custom manager for Finance User model"""
    
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
        extra_fields.setdefault('user_type', FinanceUser.UserType.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class FinanceUser(AbstractUser):
    """Custom User Model for Finance App"""
    
    class UserType(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        MANAGER = 'manager', _('Manager')
        USER = 'user', _('User')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
        PENDING = 'pending', _('Pending')
    
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
    user_type = models.CharField(_('user type'), max_length=20, choices=UserType.choices, default=UserType.USER)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Profile information
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    alternative_email = models.EmailField(_('alternative email'), blank=True)
    
    # Financial information
    credit_limit = models.DecimalField(_('credit limit'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_balance = models.DecimalField(_('current balance'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_sales = models.DecimalField(_('total sales'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_commission = models.DecimalField(_('total commission'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Verification
    email_verified = models.BooleanField(_('email verified'), default=False)
    phone_verified = models.BooleanField(_('phone verified'), default=False)
    
    # OTP for password reset
    otp_code = models.CharField(_('OTP code'), max_length=6, blank=True)
    otp_expires_at = models.DateTimeField(_('OTP expires at'), null=True, blank=True)
    
    # Override groups and user_permissions to avoid reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="finance_user_set",
        related_query_name="finance_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="finance_user_set",
        related_query_name="finance_user",
    )
    
    # Login tracking
    last_login_ip = models.GenericIPAddressField(_('last login IP'), null=True, blank=True)
    
    # Django fields
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_superuser = models.BooleanField(_('superuser status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)
    
    objects = FinanceUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']
    
    class Meta:
        db_table = 'finance_users'
        verbose_name = _('Finance User')
        verbose_name_plural = _('Finance Users')
    
    def __str__(self):
        return self.email
        return f"{self.get_full_name()} ({self.email})"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    def generate_otp(self):
        """Generate 6-digit OTP code"""
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        from django.utils import timezone
        from datetime import timedelta
        self.otp_expires_at = timezone.now() + timedelta(minutes=10)
        self.save()
        return self.otp_code
    
    def is_otp_valid(self, otp_code):
        """Check if OTP is valid"""
        from django.utils import timezone
        return (
            self.otp_code == otp_code and 
            self.otp_expires_at and 
            self.otp_expires_at > timezone.now()
        )
    
    def clear_otp(self):
        """Clear OTP code"""
        self.otp_code = None
        self.otp_expires_at = None
        self.save()


class FinanceUserProfile(models.Model):
    """Extended user profile for Finance App"""
    
    user = models.OneToOneField(FinanceUser, on_delete=models.CASCADE, related_name='finance_profile')
    
    # Company Information
    company_name = models.CharField(_('company name'), max_length=255, blank=True)
    company_registration = models.CharField(_('CR Number'), max_length=50, blank=True)
    
    # Bank Information
    bank_name = models.CharField(_('bank name'), max_length=100, blank=True)
    account_number = models.CharField(_('account number'), max_length=50, blank=True)
    iban = models.CharField(_('IBAN'), max_length=24, blank=True)
    
    # Settings
    language = models.CharField(_('language'), max_length=10, choices=[('en', 'English'), ('ar', 'Arabic')], default='en')
    timezone = models.CharField(_('timezone'), max_length=50, default='Asia/Riyadh')
    
    # Statistics
    total_tickets_sold = models.IntegerField(_('total tickets sold'), default=0)
    total_commission = models.DecimalField(_('total commission'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Finance User Profile')
        verbose_name_plural = _('Finance User Profiles')
    
    def __str__(self):
        return f"Finance Profile: {self.user.email}"
