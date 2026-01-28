# flights/urls.py
"""
URL Configuration for Flights App
B2B Travel Platform with Travelport Galileo GDS Integration
"""

from django.urls import path, include
from .views import (
    # Search Views
    search_views,
    # Booking Views
    booking_views,
    booking_management,
    # Ticketing Views
    ticketing_views,
    # Fare Rules Views
    fare_rules_views,
    # Ancillary Views
    ancillary_views,
    # Reporting Views
    reporting_views,
    # Seat Map Views
    seat_map_views,
    # API Views
    api_views,
)

app_name = 'flights'

# Web URLs (for web interface)
web_patterns = [
    # ==============================================
    # FLIGHT SEARCH
    # ==============================================
    path('search/', search_views.FlightSearchView.as_view(), name='search'),
    path('search/results/', search_views.SearchResultsView.as_view(), name='search_results'),
    path('search/fare-calendar/', search_views.FareCalendarView.as_view(), name='fare_calendar'),
    path('search/low-fare/', search_views.LowFareSearchView.as_view(), name='low_fare_search'),
    path('search/schedule/', search_views.ScheduleSearchView.as_view(), name='schedule_search'),
    path('search/multi-city/', search_views.MultiCitySearchView.as_view(), name='multi_city_search'),
    path('search/flexible-dates/', search_views.FlexibleDatesView.as_view(), name='flexible_dates'),
    path('search/advanced/', search_views.AdvancedSearchView.as_view(), name='advanced_search'),
    path('search/history/', search_views.SearchHistoryView.as_view(), name='search_history'),
    path('search/saved/', search_views.SavedSearchesView.as_view(), name='saved_searches'),

    # ==============================================
    # BOOKING MANAGEMENT
    # ==============================================
    path('booking/create/', booking_views.BookingCreateView.as_view(), name='booking_create'),
    path('booking/<uuid:booking_id>/passengers/', booking_views.PassengerDetailsView.as_view(), name='passenger_details'),
    path('booking/<uuid:booking_id>/seats/', booking_views.SeatSelectionView.as_view(), name='seat_selection'),
    path('booking/<uuid:booking_id>/ancillaries/', booking_views.AncillaryServicesView.as_view(), name='ancillary_services'),
    path('booking/<uuid:booking_id>/review/', booking_views.ReviewBookingView.as_view(), name='review_booking'),
    path('booking/<uuid:booking_id>/payment/', booking_views.PaymentView.as_view(), name='payment'),
    path('booking/<uuid:booking_id>/confirmation/', booking_views.BookingConfirmationView.as_view(), name='booking_confirmation'),

    # Booking Management
    path('bookings/', booking_management.BookingListView.as_view(), name='booking_list'),
    path('booking/<uuid:booking_id>/', booking_management.BookingDetailView.as_view(), name='booking_detail'),
    path('booking/<uuid:booking_id>/update/', booking_management.BookingUpdateView.as_view(), name='booking_update'),
    path('booking/<uuid:booking_id>/cancel/', booking_management.BookingCancelView.as_view(), name='booking_cancel'),
    path('booking/<uuid:booking_id>/void/', booking_management.BookingVoidView.as_view(), name='booking_void'),
    path('booking/<uuid:booking_id>/reissue/', booking_management.BookingReissueView.as_view(), name='booking_reissue'),

    # PNR Management
    path('pnr/<str:pnr_code>/', booking_management.PNRRetrieveView.as_view(), name='pnr_retrieve'),
    path('pnr/<str:pnr_code>/modify/', booking_management.PNRModifyView.as_view(), name='pnr_modify'),
    path('pnr/<str:pnr_code>/cancel/', booking_management.PNCancelView.as_view(), name='pnr_cancel'),

    # ==============================================
    # TICKETING
    # ==============================================
    path('ticketing/', ticketing_views.TicketListView.as_view(), name='ticket_list'),
    path('ticket/<uuid:ticket_id>/', ticketing_views.TicketDetailView.as_view(), name='ticket_detail'),
    path('ticket/<uuid:ticket_id>/issue/', ticketing_views.TicketIssueView.as_view(), name='ticket_issue'),
    path('ticket/<uuid:ticket_id>/void/', ticketing_views.TicketVoidView.as_view(), name='ticket_void'),
    path('ticket/<uuid:ticket_id>/reissue/', ticketing_views.TicketReissueView.as_view(), name='ticket_reissue'),
    path('ticket/<uuid:ticket_id>/refund/', ticketing_views.TicketRefundView.as_view(), name='ticket_refund'),

    # EMD Management
    path('emd/', ticketing_views.EMDListView.as_view(), name='emd_list'),
    path('emd/create/', ticketing_views.EMDCreateView.as_view(), name='emd_create'),
    path('emd/<uuid:emd_id>/void/', ticketing_views.EMDVoidView.as_view(), name='emd_void'),

    # ==============================================
    # FARE RULES
    # ==============================================
    path('fare-rules/', fare_rules_views.FareRulesListView.as_view(), name='fare_rules_list'),
    path('fare-rule/<uuid:rule_id>/', fare_rules_views.FareRuleDetailView.as_view(), name='fare_rule_detail'),
    path('fare-rules/search/', fare_rules_views.FareRuleSearchView.as_view(), name='fare_rule_search'),

    # ==============================================
    # ANCILLARY SERVICES
    # ==============================================
    path('ancillaries/', ancillary_views.AncillaryServicesView.as_view(), name='ancillary_services_list'),
    path('ancillary/<uuid:service_id>/book/', ancillary_views.AncillaryBookingView.as_view(), name='ancillary_booking'),

    # ==============================================
    # SEAT MAPS
    # ==============================================
    path('seat-map/<uuid:flight_id>/', seat_map_views.SeatMapView.as_view(), name='seat_map'),

    # ==============================================
    # REPORTING
    # ==============================================
    path('reports/', reporting_views.ReportsDashboardView.as_view(), name='reports_dashboard'),
    path('reports/bookings/', reporting_views.BookingReportsView.as_view(), name='booking_reports'),
    path('reports/revenue/', reporting_views.RevenueReportsView.as_view(), name='revenue_reports'),
    path('reports/flights/', reporting_views.FlightReportsView.as_view(), name='flight_reports'),
]

# API URLs (for B2B API integration)
api_patterns = [
    # ==============================================
    # FLIGHT SEARCH API
    # ==============================================
    path('api/search/', api_views.FlightSearchAPIView.as_view(), name='api_search'),
    path('api/search/low-fare/', api_views.LowFareSearchAPIView.as_view(), name='api_low_fare_search'),
    path('api/search/calendar/', api_views.FareCalendarAPIView.as_view(), name='api_fare_calendar'),
    path('api/search/advanced/', api_views.AdvancedSearchAPIView.as_view(), name='api_advanced_search'),

    # ==============================================
    # BOOKING API
    # ==============================================
    path('api/booking/create/', api_views.BookingCreateAPIView.as_view(), name='api_booking_create'),
    path('api/booking/<uuid:booking_id>/', api_views.BookingDetailAPIView.as_view(), name='api_booking_detail'),
    path('api/booking/<uuid:booking_id>/update/', api_views.BookingUpdateAPIView.as_view(), name='api_booking_update'),
    path('api/booking/<uuid:booking_id>/cancel/', api_views.BookingCancelAPIView.as_view(), name='api_booking_cancel'),
    path('api/booking/<uuid:booking_id>/confirm/', api_views.BookingConfirmAPIView.as_view(), name='api_booking_confirm'),

    # ==============================================
    # PNR API
    # ==============================================
    path('api/pnr/<str:pnr_code>/', api_views.PNRRetrieveAPIView.as_view(), name='api_pnr_retrieve'),
    path('api/pnr/<str:pnr_code>/update/', api_views.PNRUpdateAPIView.as_view(), name='api_pnr_update'),

    # ==============================================
    # TICKETING API
    # ==============================================
    path('api/ticketing/issue/', api_views.TicketIssueAPIView.as_view(), name='api_ticket_issue'),
    path('api/ticketing/void/', api_views.TicketVoidAPIView.as_view(), name='api_ticket_void'),
    path('api/ticketing/refund/', api_views.TicketRefundAPIView.as_view(), name='api_ticket_refund'),

    # ==============================================
    # ANCILLARY API
    # ==============================================
    path('api/ancillaries/', api_views.AncillaryServicesAPIView.as_view(), name='api_ancillaries'),
    path('api/ancillary/book/', api_views.AncillaryBookingAPIView.as_view(), name='api_ancillary_booking'),

    # ==============================================
    # UTILITY API
    # ==============================================
    path('api/airports/', api_views.AirportListAPIView.as_view(), name='api_airports'),
    path('api/airlines/', api_views.AirlineListAPIView.as_view(), name='api_airlines'),
    path('api/countries/', api_views.CountryListAPIView.as_view(), name='api_countries'),
]

# Combine all URL patterns
urlpatterns = [
    # Web endpoints
    path('', include(web_patterns)),

    # API endpoints
    path('api/v1/', include(api_patterns)),
]