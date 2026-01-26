# accounts/services/b2b_service.py
"""
B2B Platform Service Layer
Integrates accounts management with flights API
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied

from accounts.models import (
    User, BusinessUnit, PermissionGroup, APIKey, BusinessRule,
    SystemConfiguration, AuditLog, Transaction
)
from flights.services.galileo_client import galileo_client
from flights.services.flight_search_service import FlightSearchService
from flights.services.booking_service import BookingService

logger = logging.getLogger(__name__)

User = get_user_model()


class B2BPlatformService:
    """
    Central B2B Platform Service
    Manages business logic, permissions, and API integrations
    """

    def __init__(self):
        self.galileo = galileo_client
        self.flight_search = FlightSearchService()
        self.booking_service = BookingService()

    def authenticate_user(self, identifier: str, password: str, request=None) -> Optional[User]:
        """
        Enhanced authentication with B2B features

        Args:
            identifier: Email or phone
            password: User password
            request: HttpRequest object

        Returns:
            User object if authenticated, None otherwise
        """
        from accounts.backends import EmailOrUsernameBackend

        backend = EmailOrUsernameBackend()
        user = backend.authenticate(request, username=identifier, password=password)

        if user:
            # Check B2B business rules
            if not self._check_user_business_rules(user):
                logger.warning(f"User {user.email} blocked by business rules")
                return None

            # Log successful authentication
            self._log_audit_event(
                user=user,
                action_type='login',
                description=f"User {user.email} logged in successfully",
                metadata={'ip': self._get_client_ip(request)} if request else {}
            )

        return user

    def authorize_action(self, user: User, action: str, resource: str = None, context: Dict = None) -> bool:
        """
        Check if user is authorized for specific action

        Args:
            user: User object
            action: Action to check (e.g., 'book_flight', 'view_reports')
            resource: Specific resource (optional)
            context: Additional context

        Returns:
            True if authorized, False otherwise
        """
        # Check user status
        if user.status not in ['active']:
            return False

        # Check permission groups
        user_groups = user.groups.all()
        for group in user_groups:
            if self._check_group_permission(group, action, resource):
                return True

        # Check business rules
        if not self._check_action_business_rules(user, action, context):
            return False

        return False

    def process_flight_booking(self, user: User, booking_data: Dict) -> Dict:
        """
        Process flight booking with B2B business logic

        Args:
            user: User making the booking
            booking_data: Booking information

        Returns:
            Booking result
        """
        # Check authorization
        if not self.authorize_action(user, 'book_flight', context=booking_data):
            raise PermissionDenied("User not authorized to book flights")

        # Apply business rules
        booking_data = self._apply_booking_business_rules(user, booking_data)

        # Check credit limits
        if not self._check_credit_limits(user, booking_data):
            raise ValidationError("Insufficient credit limit")

        # Process booking through flights API
        with transaction.atomic():
            try:
                result = self.booking_service.create_booking(user, booking_data)

                # Update user balance
                self._update_user_balance(user, booking_data['total_amount'])

                # Log transaction
                self._create_transaction_record(user, booking_data, 'booking')

                # Log audit event
                self._log_audit_event(
                    user=user,
                    action_type='financial',
                    description=f"Flight booking created: {result.get('pnr')}",
                    metadata={'booking_id': result.get('booking_id'), 'amount': booking_data['total_amount']}
                )

                return result

            except Exception as e:
                logger.error(f"Booking failed for user {user.email}: {str(e)}")
                raise

    def get_user_dashboard_data(self, user: User) -> Dict:
        """
        Get personalized dashboard data for user

        Args:
            user: User object

        Returns:
            Dashboard data dictionary
        """
        cache_key = f'dashboard_{user.id}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        data = {
            'user_info': self._get_user_info(user),
            'business_metrics': self._get_business_metrics(user),
            'recent_activity': self._get_recent_activity(user),
            'widgets': self._get_user_widgets(user),
            'permissions': self._get_user_permissions(user),
        }

        # Cache for 5 minutes
        cache.set(cache_key, data, 300)

        return data

    def manage_api_key(self, user: User, action: str, key_data: Dict = None) -> Dict:
        """
        Manage API keys for external integrations

        Args:
            user: User requesting API key management
            action: 'create', 'update', 'delete', 'list'
            key_data: API key data for create/update

        Returns:
            API key management result
        """
        if not self.authorize_action(user, 'manage_api_keys'):
            raise PermissionDenied("User not authorized to manage API keys")

        if action == 'create':
            return self._create_api_key(user, key_data)
        elif action == 'update':
            return self._update_api_key(user, key_data)
        elif action == 'delete':
            return self._delete_api_key(user, key_data)
        elif action == 'list':
            return self._list_api_keys(user)

        raise ValidationError("Invalid action")

    def execute_business_rule(self, rule: 'BusinessRule', user: User, context: Dict) -> Any:
        """
        Execute a business rule

        Args:
            rule: BusinessRule instance
            user: User to apply rule to
            context: Rule execution context

        Returns:
            Rule execution result
        """
        if not rule.is_applicable(user, context):
            return None

        # Execute rule based on type
        if rule.rule_type == 'commission':
            return self._apply_commission_rule(rule, context)
        elif rule.rule_type == 'credit_limit':
            return self._apply_credit_limit_rule(rule, context)
        elif rule.rule_type == 'discount':
            return self._apply_discount_rule(rule, context)

        return None

    def get_system_configuration(self, key: str, default=None) -> Any:
        """
        Get system configuration value

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        try:
            config = SystemConfiguration.objects.get(key=key, is_active=True)
            return config.value
        except SystemConfiguration.DoesNotExist:
            return default

    def _check_user_business_rules(self, user: User) -> bool:
        """Check if user passes all applicable business rules"""
        rules = BusinessRule.objects.filter(
            rule_type='access_control',
            is_active=True
        )

        for rule in rules:
            if rule.is_applicable(user):
                # Check if rule blocks access
                if rule.action_value.get('block_access', False):
                    return False

        return True

    def _check_group_permission(self, group: PermissionGroup, action: str, resource: str = None) -> bool:
        """Check if permission group allows specific action"""
        permission_map = {
            'book_flight': group.can_book_flights,
            'manage_users': group.can_manage_users,
            'view_reports': group.can_view_reports,
            'manage_finances': group.can_manage_finances,
            'access_api': group.can_access_api,
            'manage_inventory': group.can_manage_inventory,
        }

        return permission_map.get(action, False)

    def _check_action_business_rules(self, user: User, action: str, context: Dict = None) -> bool:
        """Check business rules for specific action"""
        rules = BusinessRule.objects.filter(
            rule_type='permission',
            condition_value__action=action,
            is_active=True
        )

        for rule in rules:
            if rule.is_applicable(user, context):
                if not rule.action_value.get('allow', True):
                    return False

        return True

    def _apply_booking_business_rules(self, user: User, booking_data: Dict) -> Dict:
        """Apply business rules to booking data"""
        rules = BusinessRule.objects.filter(
            rule_type__in=['commission', 'discount', 'price_modifier'],
            is_active=True
        )

        for rule in rules:
            if rule.is_applicable(user, booking_data):
                booking_data = self._apply_rule_to_booking(rule, booking_data)

        return booking_data

    def _check_credit_limits(self, user: User, booking_data: Dict) -> bool:
        """Check if user has sufficient credit for booking"""
        amount = booking_data.get('total_amount', 0)
        available_credit = user.available_credit()

        return available_credit >= amount

    def _update_user_balance(self, user: User, amount: Decimal):
        """Update user balance after transaction"""
        user.current_balance -= amount
        user.save()

    def _create_transaction_record(self, user: User, data: Dict, transaction_type: str):
        """Create transaction record"""
        Transaction.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=data['total_amount'],
            description=f"{transaction_type.title()} - {data.get('description', '')}",
            reference=data.get('reference', ''),
            balance_before=user.current_balance + data['total_amount'],
            balance_after=user.current_balance
        )

    def _get_user_info(self, user: User) -> Dict:
        """Get basic user information for dashboard"""
        return {
            'id': user.id,
            'name': user.get_full_name(),
            'email': user.email,
            'user_type': user.user_type,
            'status': user.status,
            'company': user.get_company_name(),
            'credit_limit': float(user.credit_limit),
            'current_balance': float(user.current_balance),
            'wallet_balance': float(user.wallet_balance),
        }

    def _get_business_metrics(self, user: User) -> Dict:
        """Get business metrics for dashboard"""
        # This would aggregate data from various sources
        return {
            'total_bookings': 0,  # Calculate from bookings
            'monthly_revenue': 0.0,
            'commission_earned': 0.0,
            'pending_payments': 0.0,
        }

    def _get_recent_activity(self, user: User) -> List[Dict]:
        """Get recent user activity"""
        activities = AuditLog.objects.filter(
            user=user
        ).order_by('-created_at')[:10]

        return [{
            'action': activity.action_type,
            'description': activity.description,
            'timestamp': activity.created_at.isoformat(),
        } for activity in activities]

    def _get_user_widgets(self, user: User) -> List[Dict]:
        """Get dashboard widgets for user"""
        widgets = DashboardWidget.objects.filter(
            is_active=True,
            allowed_user_types__contains=[user.user_type]
        ) | DashboardWidget.objects.filter(
            is_active=True,
            allowed_groups__in=user.groups.all()
        ).distinct()

        return [{
            'id': widget.id,
            'type': widget.widget_type,
            'title': widget.title,
            'config': widget.config,
            'position': {'x': widget.position_x, 'y': widget.position_y},
            'size': {'width': widget.width, 'height': widget.height},
        } for widget in widgets]

    def _get_user_permissions(self, user: User) -> Dict:
        """Get user permissions"""
        permissions = {
            'can_book_flights': False,
            'can_manage_users': False,
            'can_view_reports': False,
            'can_manage_finances': False,
            'can_access_api': False,
        }

        for group in user.groups.all():
            permissions['can_book_flights'] |= group.can_book_flights
            permissions['can_manage_users'] |= group.can_manage_users
            permissions['can_view_reports'] |= group.can_view_reports
            permissions['can_manage_finances'] |= group.can_manage_finances
            permissions['can_access_api'] |= group.can_access_api

        return permissions

    def _create_api_key(self, user: User, key_data: Dict) -> Dict:
        """Create new API key"""
        api_key = APIKey.objects.create(
            user=user,
            name=key_data['name'],
            key_type=key_data.get('key_type', 'development'),
        )
        api_key.generate_keys()
        api_key.save()

        return {
            'id': api_key.id,
            'name': api_key.name,
            'api_key': api_key.api_key,
            'secret_key': api_key.secret_key,
            'status': api_key.status,
        }

    def _log_audit_event(self, user: User, action_type: str, description: str, metadata: Dict = None):
        """Log audit event"""
        AuditLog.objects.create(
            user=user,
            action_type=action_type,
            description=description,
            metadata=metadata or {}
        )

    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                return x_forwarded_for.split(',')[0]
            return request.META.get('REMOTE_ADDR', '')
        return ''

    # Additional helper methods would be implemented here...


# Singleton instance
b2b_service = B2BPlatformService()