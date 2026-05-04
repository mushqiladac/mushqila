# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve
from accounts.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('flights/', include('flights.urls', namespace='flights')),
    path('webmail/', include('webmail.urls', namespace='webmail')),
    path('finance/', include('finance.urls', namespace='finance')),
    
    # API endpoints
    path('api/v1/webmail/', include('webmail.api_urls', namespace='webmail_api')),
    path('api/v1/b2b/', include('accounts.api_urls', namespace='accounts_api')),
    path('api/v1/finance/', include('finance.urls', namespace='finance_api')),
    
    path('', HomeView.as_view(), name='home'),
    path('', include('b2c.urls')),
    
    # Static files
    path('robots.txt', serve, {'path': 'robots.txt', 'document_root': settings.STATIC_ROOT}),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'accounts/images/sinan-logo.png')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = 'Mushqila B2B Travel Platform'
admin.site.site_title = 'Mushqila Admin'
admin.site.index_title = 'Administration Dashboard'
