# b2c/views/__init__.py

from .customer_views import (
    CustomerDashboardView,
    CustomerProfileView,
    CustomerBookingsView,
)

from .booking_views import (
    FlightSearchView,
    FlightBookingView,
    BookingConfirmationView,
)

from .loyalty_views import (
    LoyaltyDashboardView,
    RewardsView,
    RedeemRewardView,
)

__all__ = [
    # Customer views
    'CustomerDashboardView',
    'CustomerProfileView',
    'CustomerBookingsView',
    
    # Booking views
    'FlightSearchView',
    'FlightBookingView',
    'BookingConfirmationView',
    
    # Loyalty views
    'LoyaltyDashboardView',
    'RewardsView',
    'RedeemRewardView',
]
