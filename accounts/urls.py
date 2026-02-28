# accounts/urls.py
"""
Production Ready URL Configuration for B2B Travel Mushqila
FIXED: Complete and working URL configuration
"""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import (
    auth_views as auth_views_module,
    home_views,
    financial_views,
    business_views,
    user_views,
    travel_views,
    admin_views,
    dashboard_views,
    b2b_views
)

app_name = 'accounts'

# API URLs
api_patterns = [
    # Authentication API
    path('auth/register/', auth_views_module.RegisterView.as_view(), name='api_register'),
    path('auth/login/', auth_views_module.LoginView.as_view(), name='api_login'),
    path('auth/logout/', auth_views_module.LogoutView.as_view(), name='api_logout'),
    
    # User profile API
    path('users/profile/', user_views.ProfileView.as_view(), name='api_profile'),
    
    # Bookings API
    path('bookings/flights/', travel_views.FlightBookingListView.as_view(), name='api_flight_bookings'),
    path('bookings/hotels/', travel_views.HotelBookingListView.as_view(), name='api_hotel_bookings'),
    
    # Payments API
    path('payments/', financial_views.PaymentView.as_view(), name='api_payments'),
    
    
]

# Web URLs (Template-based) - FIXED VERSION
web_patterns = [
    # ✅ MAIN HOME PAGE
    path('', home_views.LandingPageView.as_view(), name='home'),
    path('landing/', home_views.LandingPageView.as_view(), name='landing'),
    path('landing2/', home_views.Landing2PageView.as_view(), name='landing2'),

    
    # ✅ DASHBOARD URLS - CRITICAL FIXES
    
    path('dashboard/redirect/', dashboard_views.dashboard_redirect, name='dashboard_redirect'),
    
    # Role-based dashboard templates
    path('dashboard/admin/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/agent/', dashboard_views.agent_dashboard, name='agent_dashboard'),
    path('dashboard/supplier/', dashboard_views.supplier_dashboard, name='supplier_dashboard'),
    
    # Supplier Management
    path('supplier/services/', dashboard_views.supplier_services, name='supplier_services'),
    path('supplier/services/create/', dashboard_views.supplier_service_create, name='supplier_service_create'),
    path('supplier/services/<uuid:service_id>/', dashboard_views.supplier_service_detail, name='supplier_service_detail'),
    path('supplier/orders/', dashboard_views.supplier_orders, name='supplier_orders'),
    path('supplier/orders/<uuid:order_id>/', dashboard_views.supplier_order_detail, name='supplier_order_detail'),
    path('supplier/payments/', dashboard_views.supplier_payments, name='supplier_payments'),
    path('supplier/analytics/', dashboard_views.supplier_analytics, name='supplier_analytics'),
    
    # ✅ AUTHENTICATION - FIXED REGISTRATION
    path('login/', auth_views_module.LoginView.as_view(), name='login'),
    path('logout/', auth_views_module.LogoutView.as_view(), name='logout'),
    path('register/', auth_views_module.RegisterView.as_view(), name='register'),
    
    # Password management
    path('password/reset/', auth_views_module.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/<uidb64>/<token>/', 
         auth_views_module.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    
    # Verification
    path('verify/email/', auth_views_module.VerifyEmailView.as_view(), name='verify_email'),
    path('verify/email/<uuid:user_id>/<str:token>/', 
         auth_views_module.VerifyEmailConfirmView.as_view(), name='verify_email_confirm'),
    path('verify/phone/', auth_views_module.VerifyPhoneView.as_view(), name='verify_phone'),
    
    # ✅ PROFILE MANAGEMENT
    path('profile/', user_views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', user_views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/extended/edit/', user_views.UserProfileUpdateView.as_view(), name='profile_extended_update'),
    path('profile/security/', user_views.SecuritySettingsView.as_view(), name='security'),
    
    # ✅ KYC VERIFICATION
    path('profile/kyc/', user_views.KYCView.as_view(), name='kyc'),
    path('profile/kyc/verification/', user_views.KYCView.as_view(), name='kyc_verification'),
    
    # ✅ KYC DOCUMENTS
    path('profile/kyc/upload/', user_views.DocumentUploadView.as_view(), name='document_upload'),
    path('profile/kyc/upload/<str:document_type>/', user_views.DocumentUploadView.as_view(), name='document_upload_type'),
    path('profile/kyc/document/<uuid:document_id>/delete/', user_views.DocumentDeleteView.as_view(), name='document_delete'),
    path('profile/kyc/submit/', user_views.SubmitKYCView.as_view(), name='submit_kyc'),
    
    # ✅ NOTIFICATIONS & ACTIVITY
    path('profile/notifications/', user_views.NotificationListView.as_view(), name='notifications'),
    path('profile/notifications/<uuid:notification_id>/read/', 
         user_views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('profile/notifications/read-all/', 
         user_views.MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
    path('profile/activity-log/', user_views.ActivityLogView.as_view(), name='activity_log'),
    path('profile/referral/', user_views.ReferralView.as_view(), name='referral'),
    
    # ✅ BUSINESS OPERATIONS
    path('business/agents/', business_views.AgentHierarchyView.as_view(), name='agent_hierarchy'),
    path('business/add-agent-hierarchy/', business_views.AddAgentHierarchyView.as_view(), name='add_agent_hierarchy'),
    path('business/credit/', business_views.CreditRequestView.as_view(), name='credit_request'),
    path('business/credit/list/', business_views.CreditRequestListView.as_view(), name='credit_request_list'),
    path('business/credit/<uuid:pk>/', business_views.CreditRequestDetailView.as_view(), name='credit_request_detail'),
    path('business/approve-credit/<uuid:pk>/', business_views.ApproveCreditRequestView.as_view(), name='approve_credit_request'),
    path('business/reject-credit/<uuid:pk>/', business_views.RejectCreditRequestView.as_view(), name='reject_credit_request'),
    path('business/ip-whitelist/', business_views.IPWhitelistView.as_view(), name='ip_whitelist'),
    path('business/add-ip-whitelist/', business_views.AddIPWhitelistView.as_view(), name='add_ip_whitelist'),
    path('business/remove-ip-whitelist/<uuid:pk>/', business_views.RemoveIPWhitelistView.as_view(), name='remove_ip_whitelist'),
    
    # ✅ TRAVEL BOOKINGS
    path('travel/flights/', travel_views.FlightBookingListView.as_view(), name='flight_bookings'),
    path('travel/flights/create/', travel_views.FlightBookingView.as_view(), name='flight_booking_create'),
    path('travel/flights/<uuid:pk>/', travel_views.FlightBookingDetailView.as_view(), name='flight_booking_detail'),
    
    path('travel/hotels/', travel_views.HotelBookingListView.as_view(), name='hotel_bookings'),
    path('travel/hotels/create/', travel_views.HotelBookingView.as_view(), name='hotel_booking_create'),
    path('travel/hotels/<uuid:pk>/', travel_views.HotelBookingDetailView.as_view(), name='hotel_booking_detail'),
    
    path('travel/hajj/', travel_views.HajjBookingView.as_view(), name='hajj_booking'),
    path('travel/umrah/', travel_views.UmrahBookingView.as_view(), name='umrah_booking'),
    
    # ✅ FINANCIAL MANAGEMENT - ALL FIXED
    path('financial/wallet/', financial_views.WalletView.as_view(), name='wallet'),
    path('financial/deposit/', financial_views.DepositView.as_view(), name='deposit'),
    path('financial/withdraw/', financial_views.WithdrawalView.as_view(), name='withdraw'),
    path('financial/payments/', financial_views.PaymentView.as_view(), name='payments'),
    path('financial/invoices/', financial_views.InvoiceListView.as_view(), name='invoices'),
    path('financial/invoices/<uuid:pk>/', financial_views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('financial/transactions/', financial_views.TransactionHistoryView.as_view(), name='transactions'),
    path('financial/commission/', financial_views.CommissionView.as_view(), name='commission'),
    path('financial/refund-request/', financial_views.RefundRequestView.as_view(), name='refund_request'),
    
    # ✅ ADMIN MANAGEMENT
    path('admin/dashboard/', admin_views.AdminDashboardView.as_view(), name='admin_dashboard_class'),
    path('admin/users/', admin_views.UserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', admin_views.UserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<uuid:user_id>/update-status/', 
         admin_views.UserStatusUpdateView.as_view(), name='admin_user_status_update'),
    path('admin/pending-approvals/', admin_views.PendingApprovalsView.as_view(), name='admin_pending_approvals'),
    path('admin/kyc-review/', admin_views.KYCReviewView.as_view(), name='admin_kyc_review'),
    path('admin/documents/<uuid:document_id>/update-status/', 
         admin_views.DocumentStatusUpdateView.as_view(), name='admin_document_status_update'),
    path('admin/activity-logs/', admin_views.AdminActivityLogsView.as_view(), name='admin_activity_logs'),
    path('admin/system-settings/', admin_views.SystemSettingsView.as_view(), name='admin_system_settings'),
    
    # ✅ ADDITIONAL ADMIN PAGES
    path('admin/reports/', admin_views.AdminDashboardView.as_view(), name='admin_reports'),
    
    
    # ✅ DASHBOARD PAGES (FOR COMPATIBILITY)
    path('dashboard/profile/', user_views.ProfileView.as_view(), name='dashboard_profile'),
    path('dashboard/wallet/', financial_views.WalletView.as_view(), name='dashboard_wallet'),
    path('dashboard/bookings/', travel_views.FlightBookingListView.as_view(), name='dashboard_bookings'),

    # ✅ B2B PLATFORM MANAGEMENT
    path('b2b/dashboard/', b2b_views.B2BDashboardView.as_view(), name='b2b_dashboard'),
    path('b2b/api-keys/', b2b_views.APIKeyManagementView.as_view(), name='b2b_api_keys'),
    path('b2b/api-keys/create/', b2b_views.APIKeyManagementView.as_view(), name='b2b_api_key_create'),
    path('b2b/api-keys/<uuid:pk>/', b2b_views.APIKeyManagementView.as_view(), name='b2b_api_key_detail'),
    path('b2b/api-keys/<uuid:pk>/update/', b2b_views.APIKeyManagementView.as_view(), name='b2b_api_key_update'),
    path('b2b/api-keys/<uuid:pk>/delete/', b2b_views.APIKeyManagementView.as_view(), name='b2b_api_key_delete'),
    path('b2b/business-rules/', b2b_views.BusinessRulesView.as_view(), name='b2b_business_rules'),
    path('b2b/business-rules/create/', b2b_views.BusinessRulesView.as_view(), name='b2b_business_rule_create'),
    path('b2b/business-rules/<uuid:pk>/', b2b_views.BusinessRulesView.as_view(), name='b2b_business_rule_detail'),
    path('b2b/business-rules/<uuid:pk>/update/', b2b_views.BusinessRulesView.as_view(), name='b2b_business_rule_update'),
    path('b2b/business-rules/<uuid:pk>/delete/', b2b_views.BusinessRulesView.as_view(), name='b2b_business_rule_delete'),
    path('b2b/system-config/', b2b_views.SystemConfigurationView.as_view(), name='b2b_system_config'),
    path('b2b/audit-logs/', b2b_views.AuditLogView.as_view(), name='b2b_audit_logs'),
    path('b2b/users/', b2b_views.UserManagementView.as_view(), name='b2b_user_management'),
    path('b2b/users/<uuid:pk>/', b2b_views.UserManagementView.as_view(), name='b2b_user_detail'),
    path('b2b/api/proxy/', b2b_views.APIProxyView.as_view(), name='b2b_api_proxy'),

    # ✅ ACCOUNTING MANAGEMENT
    path('accounting/', include('accounts.accounting_urls')),
]
#path('activity-log/clear/', views.user_views.ActivityLogClearView.as_view(), name='activity_log_clear'),
#path('activity-log/export/', views.user_views.ActivityLogExportView.as_view(), name='activity_log_export'),

# Combine all URL patterns
urlpatterns = [
    # Web endpoints - root থেকে শুরু
    path('', include(web_patterns)),
    
    # API endpoints - separate namespace
    path('api/v1/', include(api_patterns)),
]

# ✅ Error handlers
handler404 = 'accounts.views.auth_views.custom_404_view'
handler403 = 'accounts.views.auth_views.custom_403_view'
handler500 = 'accounts.views.auth_views.custom_500_view'
handler400 = 'accounts.views.auth_views.custom_400_view'