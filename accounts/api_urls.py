# accounts/api_urls.py
"""
B2B Travel Platform API URLs for Flutter Mobile App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import (
    # Authentication
    register_view, login_view, logout_view, change_password_view,
    
    # Profile
    profile_view, profile_update_view,
    
    # Dashboard
    dashboard_stats_view,
    
    # ViewSets
    TransactionViewSet, FlightBookingViewSet, HotelBookingViewSet,
    HajjPackageViewSet, UmrahPackageViewSet, NotificationViewSet,
    DocumentViewSet, CreditRequestViewSet,
    
    # Locations
    saudi_regions_view, saudi_cities_view,
    
    # Suppliers
    service_suppliers_view,
)

app_name = 'accounts_api'

# Router for ViewSets
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'flight-bookings', FlightBookingViewSet, basename='flight-booking')
router.register(r'hotel-bookings', HotelBookingViewSet, basename='hotel-booking')
router.register(r'hajj-packages', HajjPackageViewSet, basename='hajj-package')
router.register(r'umrah-packages', UmrahPackageViewSet, basename='umrah-package')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'credit-requests', CreditRequestViewSet, basename='credit-request')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', register_view, name='register'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/', change_password_view, name='change_password'),
    
    # Profile endpoints
    path('profile/', profile_view, name='profile'),
    path('profile/update/', profile_update_view, name='profile_update'),
    
    # Dashboard endpoints
    path('dashboard/stats/', dashboard_stats_view, name='dashboard_stats'),
    
    # Location endpoints
    path('locations/regions/', saudi_regions_view, name='saudi_regions'),
    path('locations/cities/', saudi_cities_view, name='saudi_cities'),
    
    # Supplier endpoints
    path('suppliers/', service_suppliers_view, name='service_suppliers'),
    
    # Include router URLs
    path('', include(router.urls)),
]
