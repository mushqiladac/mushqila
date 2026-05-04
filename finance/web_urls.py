"""
Finance App Web URLs for PC Interface
Flutter mobile app এর পাশাপাশি PC web interface জন্য
"""
from django.urls import path
from . import views
from .views import web_views

app_name = 'finance'

urlpatterns = [
    # Authentication URLs
    path('login/', web_views.finance_login, name='login'),
    path('logout/', web_views.finance_logout, name='logout'),
    path('create-user/', web_views.create_user, name='create_user'),
    
    # Dashboard URLs
    path('dashboard/', web_views.finance_dashboard, name='dashboard'),
    
    # Ticket Management URLs
    path('tickets/', web_views.ticket_list, name='ticket_list'),
    path('tickets/create/', web_views.ticket_create, name='ticket_create'),
    
    # Submission URLs
    path('submissions/', web_views.submission_list, name='submission_list'),
    path('submissions/<int:submission_id>/', web_views.submission_detail, name='submission_detail'),
    
    # Profile URLs
    path('profile/', web_views.profile_view, name='profile'),
    path('profile/update/', web_views.update_profile, name='update_profile'),
]
