from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import (
    # Authentication
    login_view, logout_view, forgot_password_view,
    reset_password_view, change_password_view,
    
    # ViewSets
    EmailViewSet, ContactViewSet,
    
    # Account
    account_info_view, account_update_view,
    
    # Statistics
    email_stats_view,
    
    # Attachments
    attachment_download_view
)

app_name = 'webmail_api'

# Router for ViewSets
router = DefaultRouter()
router.register(r'emails', EmailViewSet, basename='email')
router.register(r'contacts', ContactViewSet, basename='contact')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/forgot-password/', forgot_password_view, name='forgot_password'),
    path('auth/reset-password/', reset_password_view, name='reset_password'),
    path('auth/change-password/', change_password_view, name='change_password'),
    
    # Account endpoints
    path('account/', account_info_view, name='account_info'),
    path('account/update/', account_update_view, name='account_update'),
    
    # Statistics endpoints
    path('stats/', email_stats_view, name='email_stats'),
    
    # Attachment endpoints
    path('attachments/<uuid:attachment_id>/download/', attachment_download_view, name='attachment_download'),
    
    # Include router URLs
    path('', include(router.urls)),
]
