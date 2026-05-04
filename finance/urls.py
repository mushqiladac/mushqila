from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet,
    DashboardViewSet,
    TicketSaleViewSet,
    AirlineViewSet,
    PaymentMethodViewSet,
    TransactionViewSet,
    CreditSaleViewSet,
    SubmissionViewSet,
    NotificationViewSet,
    NotificationTemplateViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='finance-auth')
router.register(r'dashboard', DashboardViewSet, basename='finance-dashboard')
router.register(r'tickets', TicketSaleViewSet, basename='finance-tickets')
router.register(r'airlines', AirlineViewSet, basename='finance-airlines')
router.register(r'payment-methods', PaymentMethodViewSet, basename='finance-payment-methods')
router.register(r'transactions', TransactionViewSet, basename='finance-transactions')
router.register(r'credit-sales', CreditSaleViewSet, basename='finance-credit-sales')
router.register(r'submissions', SubmissionViewSet, basename='finance-submissions')
router.register(r'notifications', NotificationViewSet, basename='finance-notifications')
router.register(r'notification-templates', NotificationTemplateViewSet, basename='finance-notification-templates')

# API URL patterns
app_name = 'finance'

urlpatterns = [
    # API endpoints
    path('api/v1/', include(router.urls)),
    
    # Web interface (optional, for admin access)
    path('', include([
        path('dashboard/', DashboardViewSet.as_view({'get': 'overview'}), name='web-dashboard'),
        path('login/', AuthViewSet.as_view({'post': 'login'}), name='web-login'),
    ])),
]
