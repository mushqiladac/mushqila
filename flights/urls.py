from django.urls import path
from . import views

app_name = 'flights'

urlpatterns = [
    path('api/airport-search/', views.airport_search, name='airport_search'),
    path('api/flight-search/', views.flight_search, name='flight_search'),
]
