from django.urls import path
from . import views

app_name = 'webmail'

urlpatterns = [
    # Authentication
    path('login/', views.webmail_login, name='login'),
    
    # Main views
    path('', views.inbox, name='inbox'),
    path('inbox/', views.inbox, name='inbox'),
    path('compose/', views.compose, name='compose'),
    path('email/<uuid:email_id>/', views.email_detail, name='email_detail'),
    path('email/<uuid:email_id>/delete/', views.delete_email, name='delete_email'),
    
    # Search
    path('search/', views.search_emails, name='search'),
    
    # Contacts
    path('contacts/', views.contacts, name='contacts'),
    
    # Settings
    path('account/setup/', views.account_setup, name='account_setup'),
    path('change-password/', views.change_password, name='change_password'),
]
