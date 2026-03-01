"""
B2C URL Configuration
"""
from django.urls import path
from . import views

app_name = 'b2c'

urlpatterns = [
    # Customer Dashboard
    path('dashboard/', views.CustomerDashboardView.as_view(), name='dashboard'),
    path('profile/', views.CustomerProfileView.as_view(), name='profile'),
    path('bookings/', views.CustomerBookingsView.as_view(), name='bookings'),
    
    # Flight Search & Booking
    path('search/', views.FlightSearchView.as_view(), name='search'),
    path('booking/<int:pk>/', views.FlightBookingView.as_view(), name='booking'),
    path('confirmation/<int:pk>/', views.BookingConfirmationView.as_view(), name='confirmation'),
    
    # Loyalty & Rewards
    path('loyalty/', views.LoyaltyDashboardView.as_view(), name='loyalty'),
    path('rewards/', views.RewardsView.as_view(), name='rewards'),
    path('rewards/redeem/<int:pk>/', views.RedeemRewardView.as_view(), name='redeem_reward'),
]
