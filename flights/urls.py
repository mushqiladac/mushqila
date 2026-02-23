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
    path('search/multi-city/', search_views.MultiCitySearchView.as_view(), name='multi_city_search'),
    path('search/flexible/', search_views.FlexibleSearchView.as_view(), name='flexible_search'),
    path('search/autocomplete/', search_views.AutoCompleteView.as_view(), name='autocomplete'),
    path('search/recent/', search_views.RecentSearchesView.as_view(), name='recent_searches'),
    path('search/popular/', search_views.PopularRoutesView.as_view(), name='popular_routes'),

    # ==============================================
    # BOOKING MANAGEMENT
    # ==============================================
    path('booking/create/', booking_views.BookingCreateView.as_view(), name='booking_create'),
    path('booking/<uuid:booking_id>/passengers/', booking_views.PassengerDetailsView.as_view(), name='passenger_details'),
    path('booking/<uuid:booking_id>/review/', booking_views.ReviewBookingView.as_view(), name='review_booking'),
    path('booking/<uuid:booking_id>/payment/', booking_views.PaymentView.as_view(), name='payment'),
    path('booking/<uuid:booking_id>/confirmation/', booking_views.BookingConfirmationView.as_view(), name='booking_confirmation'),
    path('booking/group/', booking_views.GroupBookingView.as_view(), name='group_booking'),
    path('booking/quick/', booking_views.QuickBookingView.as_view(), name='quick_booking'),

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
    path('emd/', ticketing_views.EMDManagementView.as_view(), name='emd_list'),

    # ==============================================
    # FARE RULES
    # ==============================================
    path('fare-rules/', fare_rules_views.FareRulesListView.as_view(), name='fare_rules_list'),
    path('fare-rule/<uuid:rule_id>/', fare_rules_views.FareRuleDetailView.as_view(), name='fare_rule_detail'),
    path('fare-rules/search/', fare_rules_views.FareRuleSearchView.as_view(), name='fare_rule_search'),
    path('baggage-rules/', fare_rules_views.BaggageRulesView.as_view(), name='baggage_rules'),

    # ==============================================
    # ANCILLARY SERVICES
    # ==============================================
    path('ancillaries/', ancillary_views.AncillaryServicesListView.as_view(), name='ancillary_services_list'),
    path('ancillary/<uuid:service_id>/book/', ancillary_views.AncillaryBookingView.as_view(), name='ancillary_booking'),

    # ==============================================
    # REPORTING
    # ==============================================
    path('reports/', reporting_views.SalesDashboardView.as_view(), name='reports_dashboard'),
    path('reports/sales/', reporting_views.SalesReportView.as_view(), name='sales_report'),
    path('reports/agents/', reporting_views.AgentPerformanceView.as_view(), name='agent_reports'),
]

# API URLs (for B2B API integration)
api_patterns = [
    # ==============================================
    # FLIGHT SEARCH API
    # ==============================================
    path('api/search/', api_views.FlightSearchAPI.as_view(), name='api_search'),

    # ==============================================
    # BOOKING API
    # ==============================================
    path('api/booking/list/', api_views.BookingListAPI.as_view(), name='api_booking_list'),
    path('api/booking/<uuid:booking_id>/', api_views.BookingDetailAPI.as_view(), name='api_booking_detail'),

    # ==============================================
    # TICKETING API
    # ==============================================
    path('api/ticketing/list/', api_views.TicketListAPI.as_view(), name='api_ticket_list'),

    # ==============================================
    # PAYMENT API
    # ==============================================
    path('api/payment/process/', api_views.PaymentProcessAPI.as_view(), name='api_payment'),
    path('api/refund/request/', api_views.RefundRequestAPI.as_view(), name='api_refund'),
]

# Combine all URL patterns
urlpatterns = [
    # Web endpoints
    path('', include(web_patterns)),

    # API endpoints
    path('api/v1/', include(api_patterns)),
]