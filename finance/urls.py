from django.urls import path, include

# Web interface URLs only
app_name = 'finance'

urlpatterns = [
    # Web interface pages
    path('', include('finance.web_urls')),
]
