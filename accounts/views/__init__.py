# accounts/views/__init__.py
"""
Views for B2B Travel Mushqila - Saudi Arabia
FIXED VERSION with DashboardView and all required imports
"""

# Import all views from modules
from .auth_views import (
    LoginView, LogoutView, RegisterView, 
    PasswordResetView, PasswordResetConfirmView, VerifyEmailConfirmView,
    VerifyEmailView, VerifyPhoneView, TwoFactorView,
    custom_404_view, custom_403_view, custom_500_view, custom_400_view
)

from .user_views import (
    ProfileView, ProfileUpdateView, UserProfileUpdateView,
    PasswordChangeView, KYCView, DocumentUploadView,
    DocumentDeleteView, SubmitKYCView, SecuritySettingsView,
    NotificationListView, MarkNotificationReadView,
    MarkAllNotificationsReadView, ActivityLogView, ReferralView
)

from .business_views import (
    AgentHierarchyView, CreditRequestView,
    CreditRequestListView, CreditRequestDetailView,
    IPWhitelistView
)

from .travel_views import (
    FlightBookingView, FlightBookingListView, FlightBookingDetailView,
    HotelBookingView, HotelBookingListView, HotelBookingDetailView,
    HajjBookingView, UmrahBookingView
)

from .financial_views import (
    WalletView, DepositView, WithdrawalView, PaymentView,
    InvoiceListView, InvoiceDetailView, TransactionHistoryView,
    CommissionView
)

# ✅ IMPORT DashboardView FROM dashboard_views
from .dashboard_views import (
    DashboardView,  # ✅ This is the class-based view
    dashboard_redirect, admin_dashboard, agent_dashboard, supplier_dashboard,
    supplier_services, supplier_service_create, supplier_service_detail,
    supplier_orders, supplier_order_detail, supplier_payments, supplier_analytics
)

from .admin_views import (
    UserListView, UserDetailView, PendingApprovalsView,
    KYCReviewView, AdminActivityLogsView, SystemSettingsView,
    UserStatusUpdateView, DocumentStatusUpdateView, AdminDashboardView
)

from .api_views import (
    UserAPIView, BookingAPIView, PaymentAPIView
)

from .accounting_views import (
    accounting_dashboard, account_list, journal_entries, trial_balance,
    create_account, accounting_rules, financial_reports,
    toggle_account_status, account_detail
)

# HomeView import করুন
try:
    from .home_views import HomeView, LandingPageView
except ImportError:
    # যদি home_views.py না থাকে
    from django.views.generic import TemplateView
    from django.utils.translation import gettext_lazy as _
    
    class HomeView(TemplateView):
        """Home page view"""
        template_name = 'accounts/home.html'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['page_title'] = _('Mushqila - B2B Travel Platform')
            return context
    
    class LandingPageView(TemplateView):
        """Landing page view"""
        template_name = 'accounts/landing.html'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['page_title'] = _('Mushqila - B2B Travel Platform')
            return context

# ✅ Explicit exports with DashboardView
__all__ = [
    # Home views
    'HomeView',
    'LandingPageView',
    
    # ✅ Dashboard View - ADDED
    'DashboardView',
    
    # Auth views
    'LoginView',
    'LogoutView',
    'RegisterView',
    'PasswordResetView',
    'PasswordResetConfirmView',
    'VerifyEmailView',
    'VerifyEmailConfirmView',
    'VerifyPhoneView',
    'TwoFactorView',
    'custom_404_view',
    'custom_403_view',
    'custom_500_view',
    'custom_400_view',
    
    # User views
    'ProfileView',
    'ProfileUpdateView',
    'UserProfileUpdateView',
    'PasswordChangeView',
    'KYCView',
    'DocumentUploadView',
    'DocumentDeleteView',
    'SubmitKYCView',
    'SecuritySettingsView',
    'NotificationListView',
    'MarkNotificationReadView',
    'MarkAllNotificationsReadView',
    'ActivityLogView',
    'ReferralView',
    
    # Business views
    'AgentHierarchyView',
    'CreditRequestView',
    'CreditRequestListView',
    'CreditRequestDetailView',
    'IPWhitelistView',
    
    # Travel views
    'FlightBookingView',
    'FlightBookingListView',
    'FlightBookingDetailView',  
    'HotelBookingView',
    'HotelBookingListView',
    'HotelBookingDetailView',   
    'HajjBookingView',
    'UmrahBookingView',
    
    # Financial views
    'WalletView',
    'DepositView',
    'WithdrawalView',
    'PaymentView',
    'InvoiceListView',
    'InvoiceDetailView',
    'TransactionHistoryView',
    'CommissionView',
    
    # Dashboard views (function-based)
    'dashboard_redirect',
    'admin_dashboard',
    'agent_dashboard',
    'supplier_dashboard',
    'supplier_services',
    'supplier_service_create',
    'supplier_service_detail',
    'supplier_orders',
    'supplier_order_detail',
    'supplier_payments',
    'supplier_analytics',
    
    # Admin views
    'AdminDashboardView',
    'UserListView',
    'UserDetailView',
    'PendingApprovalsView',
    'KYCReviewView',
    'AdminActivityLogsView',
    'SystemSettingsView',
    'UserStatusUpdateView',
    'DocumentStatusUpdateView',
    
    # API views
    'UserAPIView',
    'BookingAPIView',
    'PaymentAPIView',

    # Accounting views
    'accounting_dashboard',
    'account_list',
    'journal_entries',
    'trial_balance',
    'create_account',
    'accounting_rules',
    'financial_reports',
    'toggle_account_status',
    'account_detail',
]