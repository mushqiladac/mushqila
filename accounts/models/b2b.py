# accounts/models/b2b.py
"""
B2B Platform Models for Advanced Business Management
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class BusinessUnit(models.Model):
    """Business Unit for Multi-tenant B2B Structure"""

    class UnitType(models.TextChoices):
        HEADQUARTER = 'headquarter', _('Headquarter')
        BRANCH = 'branch', _('Branch Office')
        DEPARTMENT = 'department', _('Department')
        DIVISION = 'division', _('Division')

    name = models.CharField(_('name'), max_length=255)
    code = models.CharField(_('code'), max_length=20, unique=True)
    unit_type = models.CharField(_('type'), max_length=20, choices=UnitType.choices)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_units')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_units')
    address = models.TextField(_('address'), blank=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    is_active = models.BooleanField(_('is active'), default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Business Unit')
        verbose_name_plural = _('Business Units')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class PermissionGroup(models.Model):
    """Custom Permission Groups for B2B Access Control"""

    name = models.CharField(_('name'), max_length=255)
    code = models.CharField(_('code'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)

    # Permissions
    can_book_flights = models.BooleanField(_('can book flights'), default=False)
    can_manage_users = models.BooleanField(_('can manage users'), default=False)
    can_view_reports = models.BooleanField(_('can view reports'), default=False)
    can_manage_finances = models.BooleanField(_('can manage finances'), default=False)
    can_access_api = models.BooleanField(_('can access API'), default=False)
    can_manage_inventory = models.BooleanField(_('can manage inventory'), default=False)

    # Advanced permissions
    booking_limit_daily = models.IntegerField(_('daily booking limit'), default=0, help_text=_('0 = unlimited'))
    booking_limit_monthly = models.IntegerField(_('monthly booking limit'), default=0, help_text=_('0 = unlimited'))
    credit_limit_override = models.BooleanField(_('can override credit limits'), default=False)
    commission_override = models.BooleanField(_('can override commissions'), default=False)

    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Permission Group')
        verbose_name_plural = _('Permission Groups')
        ordering = ['name']

    def __str__(self):
        return self.name


class APIKey(models.Model):
    """API Keys for External Integrations"""

    class KeyType(models.TextChoices):
        PRODUCTION = 'production', _('Production')
        SANDBOX = 'sandbox', _('Sandbox')
        DEVELOPMENT = 'development', _('Development')

    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
        EXPIRED = 'expired', _('Expired')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(_('name'), max_length=255)
    key_type = models.CharField(_('type'), max_length=20, choices=KeyType.choices, default=KeyType.DEVELOPMENT)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # API Key Details
    api_key = models.CharField(_('API Key'), max_length=64, unique=True)
    secret_key = models.CharField(_('Secret Key'), max_length=128)

    # Permissions
    allowed_ips = models.JSONField(_('allowed IPs'), default=list, blank=True)
    rate_limit_per_minute = models.IntegerField(_('rate limit per minute'), default=60)
    rate_limit_per_hour = models.IntegerField(_('rate limit per hour'), default=1000)

    # Usage Tracking
    total_requests = models.BigIntegerField(_('total requests'), default=0)
    requests_today = models.IntegerField(_('requests today'), default=0)
    last_request_at = models.DateTimeField(_('last request'), null=True, blank=True)

    # Validity
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('API Key')
        verbose_name_plural = _('API Keys')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['api_key']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.name} - {self.user.email}"

    def is_valid(self):
        """Check if API key is valid"""
        if self.status != self.Status.ACTIVE:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def generate_keys(self):
        """Generate new API and secret keys"""
        self.api_key = uuid.uuid4().hex
        self.secret_key = uuid.uuid4().hex + uuid.uuid4().hex


class BusinessRule(models.Model):
    """Dynamic Business Rules Engine"""

    class RuleType(models.TextChoices):
        COMMISSION = 'commission', _('Commission Rule')
        CREDIT_LIMIT = 'credit_limit', _('Credit Limit Rule')
        BOOKING_RESTRICTION = 'booking_restriction', _('Booking Restriction')
        PRICE_MODIFIER = 'price_modifier', _('Price Modifier')
        DISCOUNT = 'discount', _('Discount Rule')

    class ConditionType(models.TextChoices):
        USER_TYPE = 'user_type', _('User Type')
        USER_GROUP = 'user_group', _('User Group')
        BOOKING_AMOUNT = 'booking_amount', _('Booking Amount')
        DESTINATION = 'destination', _('Destination')
        SERVICE_TYPE = 'service_type', _('Service Type')
        TIME_RANGE = 'time_range', _('Time Range')
        CUSTOM = 'custom', _('Custom Condition')

    name = models.CharField(_('name'), max_length=255)
    rule_type = models.CharField(_('rule type'), max_length=30, choices=RuleType.choices)
    description = models.TextField(_('description'), blank=True)

    # Conditions
    condition_type = models.CharField(_('condition type'), max_length=30, choices=ConditionType.choices)
    condition_value = models.JSONField(_('condition value'), default=dict)

    # Actions
    action_value = models.JSONField(_('action value'), default=dict)

    # Applicability
    applicable_users = models.ManyToManyField(User, blank=True, related_name='business_rules')
    applicable_groups = models.ManyToManyField(PermissionGroup, blank=True, related_name='business_rules')

    # Control
    priority = models.IntegerField(_('priority'), default=0, help_text=_('Higher priority rules are applied first'))
    is_active = models.BooleanField(_('is active'), default=True)
    start_date = models.DateTimeField(_('start date'), null=True, blank=True)
    end_date = models.DateTimeField(_('end date'), null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Business Rule')
        verbose_name_plural = _('Business Rules')
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.rule_type})"

    def is_applicable(self, user, context=None):
        """Check if rule applies to given user and context"""
        if not self.is_active:
            return False

        # Check date validity
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False

        # Check user applicability
        if self.applicable_users.exists() and user not in self.applicable_users.all():
            return False

        # Check group applicability
        user_groups = user.groups.all()
        if self.applicable_groups.exists() and not self.applicable_groups.filter(id__in=user_groups.values_list('id', flat=True)).exists():
            return False

        # Check conditions
        return self._evaluate_condition(user, context)

    def _evaluate_condition(self, user, context):
        """Evaluate the rule condition"""
        condition_type = self.condition_type
        condition_value = self.condition_value

        if condition_type == self.ConditionType.USER_TYPE:
            return user.user_type == condition_value.get('user_type')

        elif condition_type == self.ConditionType.BOOKING_AMOUNT:
            amount = context.get('amount', 0) if context else 0
            min_amount = condition_value.get('min_amount', 0)
            max_amount = condition_value.get('max_amount', float('inf'))
            return min_amount <= amount <= max_amount

        elif condition_type == self.ConditionType.DESTINATION:
            destination = context.get('destination') if context else None
            return destination in condition_value.get('destinations', [])

        # Add more condition types as needed
        return True


class DashboardWidget(models.Model):
    """Customizable Dashboard Widgets"""

    class WidgetType(models.TextChoices):
        METRIC = 'metric', _('Metric Card')
        CHART = 'chart', _('Chart')
        TABLE = 'table', _('Data Table')
        ALERT = 'alert', _('Alert/Notification')
        QUICK_ACTION = 'quick_action', _('Quick Action')

    name = models.CharField(_('name'), max_length=255)
    widget_type = models.CharField(_('type'), max_length=20, choices=WidgetType.choices)
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True)

    # Configuration
    config = models.JSONField(_('configuration'), default=dict)
    data_source = models.CharField(_('data source'), max_length=255, blank=True)
    refresh_interval = models.IntegerField(_('refresh interval (seconds)'), default=300)

    # Permissions
    allowed_user_types = models.JSONField(_('allowed user types'), default=list)
    allowed_groups = models.ManyToManyField(PermissionGroup, blank=True, related_name='widgets')

    # Layout
    position_x = models.IntegerField(_('position X'), default=0)
    position_y = models.IntegerField(_('position Y'), default=0)
    width = models.IntegerField(_('width'), default=4)
    height = models.IntegerField(_('height'), default=3)

    is_active = models.BooleanField(_('is active'), default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_widgets')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Dashboard Widget')
        verbose_name_plural = _('Dashboard Widgets')
        ordering = ['position_y', 'position_x']

    def __str__(self):
        return self.title


class SystemConfiguration(models.Model):
    """System-wide Configuration Settings"""

    class ConfigType(models.TextChoices):
        GENERAL = 'general', _('General')
        FINANCIAL = 'financial', _('Financial')
        SECURITY = 'security', _('Security')
        API = 'api', _('API')
        NOTIFICATION = 'notification', _('Notification')

    key = models.CharField(_('key'), max_length=255, unique=True)
    config_type = models.CharField(_('type'), max_length=20, choices=ConfigType.choices, default=ConfigType.GENERAL)
    value = models.JSONField(_('value'), default=dict)
    description = models.TextField(_('description'), blank=True)

    is_system = models.BooleanField(_('is system setting'), default=False)
    is_editable = models.BooleanField(_('is editable'), default=True)

    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='config_updates')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('System Configuration')
        verbose_name_plural = _('System Configurations')
        ordering = ['config_type', 'key']

    def __str__(self):
        return f"{self.key} ({self.config_type})"


class AuditLog(models.Model):
    """Comprehensive Audit Logging"""

    class ActionType(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        API_ACCESS = 'api_access', _('API Access')
        FINANCIAL = 'financial', _('Financial Action')
        SECURITY = 'security', _('Security Event')

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action_type = models.CharField(_('action type'), max_length=20, choices=ActionType.choices)
    object_type = models.CharField(_('object type'), max_length=100)
    object_id = models.CharField(_('object ID'), max_length=100, blank=True)

    # Details
    description = models.TextField(_('description'))
    old_values = models.JSONField(_('old values'), default=dict, blank=True)
    new_values = models.JSONField(_('new values'), default=dict, blank=True)
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)

    # Context
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    session_id = models.CharField(_('session ID'), max_length=255, blank=True)

    # Status
    is_success = models.BooleanField(_('is success'), default=True)
    error_message = models.TextField(_('error message'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['object_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.created_at}"