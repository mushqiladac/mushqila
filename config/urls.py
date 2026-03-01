# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import HomeView  # HomeView import করুন

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('flights/', include('flights.urls', namespace='flights')),
    path('', HomeView.as_view(), name='home'),
    path('', include('b2c.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = 'Mushqila B2B Travel Platform'
admin.site.site_title = 'Mushqila Admin'
admin.site.index_title = 'Administration Dashboard'