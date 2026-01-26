# accounts/views/b2b_views.py
"""
B2B Platform Views - Modern Dashboard and Management
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from accounts.models import (
    User, BusinessUnit, PermissionGroup, APIKey, BusinessRule,
    SystemConfiguration, AuditLog, Transaction
)
from accounts.services import b2b_service
from flights.models import Booking, FlightItinerary


class B2BDashboardView(LoginRequiredMixin, TemplateView):
    """Modern B2B Dashboard with Analytics"""

    template_name = 'accounts/b2b/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get dashboard data from B2B service
        dashboard_data = b2b_service.get_user_dashboard_data(self.request.user)

        context.update(dashboard_data)

        # Add additional metrics
        context['metrics'] = self._get_dashboard_metrics()
        context['charts'] = self._get_dashboard_charts()
        context['recent_bookings'] = self._get_recent_bookings()
        context['alerts'] = self._get_system_alerts()

        return context

    def _get_dashboard_metrics(self):
        """Get key performance metrics"""
        user = self.request.user
        today = timezone.now().date()
        month_start = today.replace(day=1)

        metrics = {
            'total_users': User.objects.filter(is_active=True).count(),
            'active_users': User.objects.filter(
                is_active=True,
                last_login__date__gte=today - timedelta(days=30)
            ).count(),
            'total_bookings': Booking.objects.filter(user=user).count(),
            'monthly_bookings': Booking.objects.filter(
                user=user,
                created_at__date__gte=month_start
            ).count(),
            'total_revenue': Booking.objects.filter(user=user).aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'monthly_revenue': Booking.objects.filter(
                user=user,
                created_at__date__gte=month_start
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
        }

        return metrics

    def _get_dashboard_charts(self):
        """Get chart data for dashboard"""
        user = self.request.user

        # Bookings by month (last 12 months)
        bookings_data = []
        for i in range(11, -1, -1):
            date = timezone.now() - timedelta(days=i*30)
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            count = Booking.objects.filter(
                user=user,
                created_at__date__gte=month_start,
                created_at__date__lte=month_end
            ).count()

            bookings_data.append({
                'month': month_start.strftime('%b %Y'),
                'count': count
            })

        # Revenue by month
        revenue_data = []
        for i in range(11, -1, -1):
            date = timezone.now() - timedelta(days=i*30)
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            revenue = Booking.objects.filter(
                user=user,
                created_at__date__gte=month_start,
                created_at__date__lte=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            revenue_data.append({
                'month': month_start.strftime('%b %Y'),
                'revenue': float(revenue)
            })

        return {
            'bookings_trend': bookings_data,
            'revenue_trend': revenue_data
        }

    def _get_recent_bookings(self):
        """Get recent bookings for dashboard"""
        bookings = Booking.objects.filter(
            user=self.request.user
        ).select_related('itinerary').order_by('-created_at')[:5]

        return [{
            'id': booking.id,
            'pnr': booking.pnr.pnr_number if booking.pnr else 'N/A',
            'destination': booking.itinerary.arrival_airport if booking.itinerary else 'N/A',
            'amount': float(booking.total_amount),
            'status': booking.status,
            'created_at': booking.created_at.strftime('%d %b %Y'),
        } for booking in bookings]

    def _get_system_alerts(self):
        """Get system alerts and notifications"""
        alerts = []

        user = self.request.user

        # Low balance alert
        if user.current_balance < user.credit_limit * 0.1:
            alerts.append({
                'type': 'warning',
                'message': f'Your balance is low: SAR {user.current_balance:.2f}',
                'action': 'Add Funds'
            })

        # Pending documents alert
        pending_docs = user.documents.filter(status='pending').count()
        if pending_docs > 0:
            alerts.append({
                'type': 'info',
                'message': f'You have {pending_docs} pending document(s) for review',
                'action': 'View Documents'
            })

        # System maintenance alert (example)
        # This would come from SystemConfiguration
        maintenance_mode = b2b_service.get_system_configuration('maintenance_mode', False)
        if maintenance_mode:
            alerts.append({
                'type': 'danger',
                'message': 'System is under maintenance. Some features may be unavailable.',
                'action': None
            })

        return alerts


class APIKeyManagementView(LoginRequiredMixin, TemplateView):
    """API Key Management Interface"""

    template_name = 'accounts/b2b/api_keys.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's API keys
        api_keys = APIKey.objects.filter(user=self.request.user)

        context['api_keys'] = [{
            'id': key.id,
            'name': key.name,
            'key_type': key.key_type,
            'status': key.status,
            'api_key': key.api_key[:8] + '...' + key.api_key[-4:],  # Masked
            'created_at': key.created_at.strftime('%d %b %Y'),
            'expires_at': key.expires_at.strftime('%d %b %Y') if key.expires_at else 'Never',
            'total_requests': key.total_requests,
        } for key in api_keys]

        return context

    def post(self, request, *args, **kwargs):
        """Handle API key operations"""
        action = request.POST.get('action')

        if action == 'create':
            return self._create_api_key(request)
        elif action == 'delete':
            return self._delete_api_key(request)

        return JsonResponse({'error': 'Invalid action'}, status=400)

    def _create_api_key(self, request):
        """Create new API key"""
        name = request.POST.get('name')
        key_type = request.POST.get('key_type', 'development')

        if not name:
            messages.error(request, 'API key name is required')
            return redirect('accounts:api_keys')

        try:
            result = b2b_service.manage_api_key(
                request.user,
                'create',
                {'name': name, 'key_type': key_type}
            )

            messages.success(
                request,
                f'API key "{result["name"]}" created successfully. '
                f'Key: {result["api_key"]}'
            )

        except Exception as e:
            messages.error(request, f'Failed to create API key: {str(e)}')

        return redirect('accounts:api_keys')

    def _delete_api_key(self, request):
        """Delete API key"""
        key_id = request.POST.get('key_id')

        try:
            b2b_service.manage_api_key(
                request.user,
                'delete',
                {'key_id': key_id}
            )

            messages.success(request, 'API key deleted successfully')

        except Exception as e:
            messages.error(request, f'Failed to delete API key: {str(e)}')

        return redirect('accounts:api_keys')


class BusinessRulesView(LoginRequiredMixin, TemplateView):
    """Business Rules Management"""

    template_name = 'accounts/b2b/business_rules.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get business rules
        rules = BusinessRule.objects.filter(is_active=True).order_by('-priority')

        context['business_rules'] = [{
            'id': rule.id,
            'name': rule.name,
            'rule_type': rule.rule_type,
            'condition_type': rule.condition_type,
            'priority': rule.priority,
            'is_active': rule.is_active,
            'created_at': rule.created_at.strftime('%d %b %Y'),
        } for rule in rules]

        return context


class SystemConfigurationView(LoginRequiredMixin, TemplateView):
    """System Configuration Management"""

    template_name = 'accounts/b2b/system_config.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get system configurations
        configs = SystemConfiguration.objects.filter(is_editable=True).order_by('config_type', 'key')

        context['configurations'] = [{
            'id': config.id,
            'key': config.key,
            'config_type': config.config_type,
            'value': config.value,
            'description': config.description,
            'updated_at': config.updated_at.strftime('%d %b %Y %H:%M'),
            'updated_by': config.updated_by.get_full_name() if config.updated_by else 'System',
        } for config in configs]

        return context


class AuditLogView(LoginRequiredMixin, ListView):
    """Audit Log Viewer"""

    template_name = 'accounts/b2b/audit_log.html'
    model = AuditLog
    paginate_by = 50
    context_object_name = 'audit_logs'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by user permissions
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)

        # Apply filters
        action_type = self.request.GET.get('action_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if action_type:
            queryset = queryset.filter(action_type=action_type)

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter options
        context['action_types'] = AuditLog.ActionType.choices

        return context


class UserManagementView(LoginRequiredMixin, ListView):
    """User Management Interface"""

    template_name = 'accounts/b2b/user_management.html'
    model = User
    paginate_by = 25
    context_object_name = 'users'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Apply filters
        user_type = self.request.GET.get('user_type')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')

        if user_type:
            queryset = queryset.filter(user_type=user_type)

        if status:
            queryset = queryset.filter(status=status)

        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(company_name_en__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter options
        context['user_types'] = User.UserType.choices
        context['statuses'] = User.Status.choices

        return context


@method_decorator(csrf_exempt, name='dispatch')
class APIProxyView(LoginRequiredMixin, View):
    """API Proxy for external integrations"""

    def post(self, request, *args, **kwargs):
        """Handle API requests from external systems"""

        # Validate API key
        api_key = self._validate_api_key(request)
        if not api_key:
            return JsonResponse({'error': 'Invalid API key'}, status=401)

        # Check rate limits
        if not self._check_rate_limits(api_key):
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)

        # Parse request
        try:
            data = json.loads(request.body)
            action = data.get('action')
            params = data.get('params', {})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Process request based on action
        try:
            result = self._process_api_request(api_key, action, params)

            # Log API access
            b2b_service._log_audit_event(
                user=api_key.user,
                action_type='api_access',
                description=f'API call: {action}',
                metadata={'api_key': api_key.name, 'action': action}
            )

            return JsonResponse(result)

        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    def _validate_api_key(self, request) -> Optional[APIKey]:
        """Validate API key from request"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        try:
            api_key = APIKey.objects.get(api_key=token, status='active')
            if api_key.is_valid():
                return api_key
        except APIKey.DoesNotExist:
            pass

        return None

    def _check_rate_limits(self, api_key: APIKey) -> bool:
        """Check if API key is within rate limits"""
        # This is a simplified implementation
        # In production, you'd use Redis or similar for distributed rate limiting

        cache_key = f'api_rate_{api_key.id}'
        current_count = cache.get(cache_key, 0)

        if current_count >= api_key.rate_limit_per_minute:
            return False

        cache.set(cache_key, current_count + 1, timeout=60)
        return True

    def _process_api_request(self, api_key: APIKey, action: str, params: Dict) -> Dict:
        """Process API request"""

        # Update API key usage
        api_key.total_requests += 1
        api_key.requests_today += 1
        api_key.last_request_at = timezone.now()
        api_key.save()

        # Route to appropriate service
        if action == 'search_flights':
            return self._handle_flight_search(api_key.user, params)
        elif action == 'create_booking':
            return self._handle_booking_creation(api_key.user, params)
        elif action == 'get_user_info':
            return self._handle_user_info(api_key.user, params)

        raise ValueError(f"Unknown action: {action}")

    def _handle_flight_search(self, user: User, params: Dict) -> Dict:
        """Handle flight search API request"""
        from flights.services import FlightSearchService

        search_service = FlightSearchService()
        return search_service.search_flights(user, params)

    def _handle_booking_creation(self, user: User, params: Dict) -> Dict:
        """Handle booking creation API request"""
        return b2b_service.process_flight_booking(user, params)

    def _handle_user_info(self, user: User, params: Dict) -> Dict:
        """Handle user info API request"""
        return b2b_service.get_user_dashboard_data(user)['user_info']