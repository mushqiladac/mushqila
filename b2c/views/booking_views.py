"""B2C Booking Views - Placeholder"""
from django.views.generic import TemplateView

class FlightSearchView(TemplateView):
    template_name = 'b2c/search.html'

class FlightBookingView(TemplateView):
    template_name = 'b2c/booking.html'

class BookingConfirmationView(TemplateView):
    template_name = 'b2c/confirmation.html'
