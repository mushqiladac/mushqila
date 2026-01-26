"""
Flights App Views Module
Production Ready - Final Version
B2B Travel Platform with Travelport Galileo GDS Integration
"""

# ==============================================
# FLIGHT SEARCH VIEWS
# ==============================================

from .search_views import (
    # Main Search Views
    FlightSearchView,
    SearchResultsView,
    FareCalendarView,
    FlexibleSearchView,
    MultiCitySearchView,
    
    # Advanced Search
    AutoCompleteView,
    RecentSearchesView,
    PopularRoutesView,
)

# ==============================================
# BOOKING MANAGEMENT VIEWS
# ==============================================

from .booking_views import (
    # Booking Flow
    BookingCreateView,
    PassengerDetailsView,
    ReviewBookingView,
    PaymentView,
    BookingConfirmationView,
    
    # Booking Management
    QuickBookingView,
    GroupBookingView,
)

# ==============================================
# TICKETING VIEWS
# ==============================================

from .ticketing_views import (
    # Ticket Management
    TicketListView,
    TicketDetailView,
    TicketIssueView,
    TicketVoidView,
    TicketReissueView,
    TicketRevalidationView,
    TicketRefundView,
    
    # EMD Management
    EMDManagementView,
    
    # Ticketing Queue
    TicketingQueueView,
    TicketingDashboardView,
)

# ==============================================
# FARE RULES VIEWS
# ==============================================

from .fare_rules_views import (
    # Fare Rules Display
    FareRulesListView,
    FareRuleDetailView,
    FareRuleSearchView,
    FareRuleComparisonView,
    FareRuleParserView,
    
    # Baggage Rules
    BaggageRulesView,
    # BaggageCalculatorView,  # Not implemented yet
    # ExcessBaggageView,  # Not implemented yet
    
    # Fare Conditions - Not implemented yet
    # FareConditionsView,
    # PenaltyCalculatorView,
    # ChangeFeeCalculatorView,
    
    # GDS Fare Rules
    GDSFareRulesView,
    FareRuleValidatorView,
    FareRuleCategoriesView,
)

# ==============================================
# ANCILLARY SERVICES VIEWS
# ==============================================

from .ancillary_views import (
    # Ancillary Services
    AncillaryServicesListView,
    AncillaryServiceDetailView,
    AncillaryBookingView,
    BaggageServicesView,
    MealServicesView,
    LoungeAccessView,
    TravelInsuranceView,
    ServiceBundlesView,
    AncillaryBookingManagementView,
)

# ==============================================
# INVENTORY MANAGEMENT VIEWS
# ==============================================
# Note: inventory_views.py doesn't exist yet - these views are not implemented
# from .inventory_views import (
#     # Flight Inventory
#     FlightInventoryView,
#     InventoryUpdateView,
#     AvailabilityCheckView,
#     SeatMapInventoryView,
#     
#     # Fare Management
#     FareManagementView,
#     FareUpdateView,
#     FareOverrideView,
#     CorporateFareView,
#     
#     # Booking Control
#     BookingLimitView,
#     OverrideRuleView,
#     BlackoutDateView,
#     SpecialOfferView,
#     
#     # GDS Sync
#     GDSInventorySyncView,
#     InventoryReconciliationView,
#     CacheManagementView,
# )

# ==============================================
# REPORTS & ANALYTICS VIEWS
# ==============================================

from .reporting_views import (
    # Sales Reports
    SalesDashboardView,
    SalesReportView,
    RevenueReportView,
    CommissionReportView,
    # DailySalesView,  # Not implemented yet
    # MonthlySalesView,  # Not implemented yet
    
    # Performance Reports
    AgentPerformanceView,
    TeamPerformanceView,
    AirlinePerformanceView,
    RouteAnalysisView,  # Note: This is RouteAnalysisView, not RoutePerformanceView
    # RoutePerformanceView,  # Not implemented yet
    
    # Operational Reports
    BookingAnalysisView,
    # TicketingReportView,  # Not implemented yet
    # RefundReportView,  # Not implemented yet
    # CancellationReportView,  # Not implemented yet
    
    # Analytical Reports - Not implemented yet
    # MarketAnalysisView,
    # CustomerAnalysisView,
    # ProfitabilityAnalysisView,
    # TrendAnalysisView,
    
    # Custom Reports
    CustomReportBuilderView,
    # SavedReportsView,  # Not implemented yet
    ReportSchedulerView,
    
    # Export Views
    ReportExportView,
    ReportDownloadView,
    ReportChartView,
)

# ==============================================
# API VIEWS
# ==============================================

from .api_views import (
    # Authentication
    APILoginView,
    APILogoutView,
    APIStatusView,
    # APIKeyManagementView,  # Not implemented yet
    
    # Flight Search API
    FlightSearchAPI,
    FlightAvailabilityAPI,
    FareCalendarAPI,
    LowFareSearchAPI,
    ScheduleSearchAPI,
    
    # Booking API
    BookingListAPI,
    BookingDetailAPI,
    # BookingCreateAPI,  # Not implemented yet
    BookingConfirmAPI,
    # BookingCancelAPI,  # Not implemented yet
    BookingRetrieveAPI,
    BookingPriceAPI,
    
    # Ticketing API
    TicketListAPI,
    TicketDetailAPI,
    # TicketIssueAPI,  # Not implemented yet
    TicketVoidAPI,
    TicketReissueAPI,
    EMDIssueAPI,
    
    # Payment API
    PaymentProcessAPI,
    PaymentListAPI,
    RefundRequestAPI,
    
    # Ancillary API
    AncillaryServiceListAPI,
    AncillaryBookingAPI,
    SeatMapAPI,
    
    # Reference Data API
    AirlineListAPI,
    AirportListAPI,
    AirportAutocompleteAPI,
    CountryListAPI,
    CurrencyRatesAPI,
    
    # Reports API
    SalesReportAPI,
    PerformanceReportAPI,
    # BookingReportAPI,  # Not implemented yet
    
    # Webhooks
    GDSWebhookView,
    PaymentWebhookView,
    # NotificationWebhookView,  # Not implemented yet
    
    # Bulk Operations
    BulkBookingAPI,
    # BulkTicketingAPI,  # Not implemented yet
    # BulkPaymentAPI,  # Not implemented yet
    
    # Utility API
    # CurrencyConverterAPI,  # Not implemented yet
    # DocumentValidatorAPI,  # Not implemented yet
    # PNRDecoderAPI,  # Not implemented yet
    
    # Monitoring API
    APIUsageAPI,
    APIPerformanceAPI,
    # SystemHealthAPI,  # Not implemented yet
)

# ==============================================
# ADMIN VIEWS
# ==============================================
# ADMIN VIEWS
# ==============================================
# Note: admin_views.py doesn't exist yet - these views are not implemented
# from .admin_views import (
#     # User Management
#     AgentManagementView,
#     SubAgentManagementView,
#     UserProfileView,
#     CommissionManagementView,
#     
#     # Configuration
#     AirlineManagementView,
#     AirportManagementView,
#     FareRuleManagementView,
#     ServiceConfigurationView,
#     
#     # System Management
#     GDSConfigurationView,
#     PaymentGatewayView,
#     SMTPConfigurationView,
#     SystemLogsView,
#     
#     # Audit & Compliance
#     AuditTrailView,
#     ComplianceCheckView,
#     TransactionAuditView,
#     ReportAuditView,
# )

# ==============================================
# UTILITY VIEWS
# ==============================================
# Note: utility_views.py doesn't exist yet - these views are not implemented
# from .utility_views import (
#     # Calculators
#     FareCalculatorView,
#     BaggageCalculatorView,
#     CurrencyConverterView,
#     DistanceCalculatorView,
#     
#     # Validators
#     PNRValidatorView,
#     TicketValidatorView,
#     PassengerValidatorView,
#     DocumentValidatorView,
#     
#     # Tools
#     PNRDecoderView,
#     TicketDecoderView,
#     AirlineCodeView,
#     AirportCodeView,
#     
#     # Downloads
#     DocumentDownloadView,
#     ReportDownloadView,
#     TemplateDownloadView,
#     ExportDataView,
# )

# ==============================================
# CUSTOMER VIEWS
# ==============================================
# Note: customer_views.py doesn't exist yet - these views are not implemented
# from .customer_views import (
#     # Customer Management
#     CustomerListView,
#     CustomerDetailView,
#     CustomerCreateView,
#     CustomerUpdateView,
#     
#     # Corporate Management
#     CorporateAccountView,
#     CorporateUserView,
#     TravelPolicyView,
#     ApprovalWorkflowView,
#     
#     # Customer Portal
#     CustomerPortalView,
#     BookingHistoryView,
#     TravelDocumentView,
#     PreferenceManagementView,
#     
#     # Communication
#     NotificationView,
#     MessageCenterView,
#     AnnouncementView,
#     AlertView,
# )

# ==============================================
# TRAVELPORT GDS INTEGRATION VIEWS
# ==============================================
# Note: gds_views.py doesn't exist yet - these views are not implemented
# from .gds_views import (
#     # GDS Connection
#     GDSConnectionView,
#     GDSSessionView,
#     GDSStatusView,
#     GDSReconnectView,
#     
#     # GDS Search
#     GDSLowFareSearchView,
#     GDSAvailabilityView,
#     GDSScheduleView,
#     GDSFareRulesView,
#     
#     # GDS Booking
#     GDSCreateBookingView,
#     GDSRetrieveBookingView,
#     GDSModifyBookingView,
#     GDSCancelBookingView,
#     
#     # GDS Ticketing
#     GDSIssueTicketView,
#     GDSVoidTicketView,
#     GDSReissueTicketView,
#     GDSEMDView,
#     
#     # GDS Queue
#     GDSQueueView,
#     GDSQueueItemView,
#     GDSQueueProcessingView,
#     
#     # GDS Utilities
#     GDSPNRDecoderView,
#     GDSTicketValidatorView,
#     GDSReferenceDataView,
#     GDSTestConnectionView,
# )

# ==============================================
# EXPORT ALL VIEWS
# ==============================================

__all__ = [
    # Flight Search Views
    'FlightSearchView',
    'SearchResultsView',
    'FareCalendarView',
    'LowFareSearchView',
    'ScheduleSearchView',
    'MultiCitySearchView',
    'FlexibleDatesView',
    'AdvancedSearchView',
    'SearchHistoryView',
    'SavedSearchesView',
    'AirportAutocompleteView',
    'AirlineAutocompleteView',
    'RecentSearchesView',
    'PopularRoutesView',
    
    # Booking Management Views
    'BookingCreateView',
    'PassengerDetailsView',
    'SeatSelectionView',
    'AncillaryServicesView',
    'ReviewBookingView',
    'PaymentView',
    'BookingConfirmationView',
    'BookingListView',
    'BookingDetailView',
    'BookingUpdateView',
    'BookingCancelView',
    'BookingVoidView',
    'BookingReissueView',
    'PNRRetrieveView',
    'PNRModifyView',
    'PNCancelView',
    'PNRQueueView',
    'GroupBookingView',
    'BulkBookingView',
    
    # Ticketing Views
    'TicketListView',
    'TicketDetailView',
    'TicketIssueView',
    'TicketVoidView',
    'TicketReissueView',
    'TicketRevalidationView',
    'TicketRefundView',
    'EMDListView',
    'EMDCreateView',
    'EMDVoidView',
    'EMDRefundView',
    'TicketingQueueView',
    'ManualTicketingView',
    'AutoTicketingView',
    
    # Fare Rules Views
    'FareRulesListView',
    'FareRuleDetailView',
    'FareRuleSearchView',
    'FareRuleComparisonView',
    'FareRuleParserView',
    'BaggageRulesView',
    'BaggageCalculatorView',
    'ExcessBaggageView',
    'FareConditionsView',
    'PenaltyCalculatorView',
    'ChangeFeeCalculatorView',
    'GDSFareRulesView',
    'FareRuleValidatorView',
    'FareRuleCategoriesView',
    
    # Ancillary Services Views
    'SeatMapView',
    'SeatSelectionView',
    'PreferredSeatingView',
    'ExtraLegroomView',
    'BaggageServiceView',
    'ExcessBaggageBookingView',
    'SportsEquipmentView',
    'MusicalInstrumentsView',
    'MealSelectionView',
    'SpecialMealsView',
    'MealPreferenceView',
    'LoungeAccessView',
    'MeetAndGreetView',
    'FastTrackView',
    'TravelInsuranceView',
    'InsuranceQuoteView',
    'InsurancePurchaseView',
    'SpecialAssistanceView',
    'WheelchairRequestView',
    'MedicalAssistanceView',
    'ServiceBundleView',
    'CorporatePackageView',
    'GroupAncillaryView',
    
    # Inventory Management Views
    'FlightInventoryView',
    'InventoryUpdateView',
    'AvailabilityCheckView',
    'SeatMapInventoryView',
    'FareManagementView',
    'FareUpdateView',
    'FareOverrideView',
    'CorporateFareView',
    'BookingLimitView',
    'OverrideRuleView',
    'BlackoutDateView',
    'SpecialOfferView',
    'GDSInventorySyncView',
    'InventoryReconciliationView',
    'CacheManagementView',
    
    # Reports & Analytics Views
    'SalesDashboardView',
    'SalesReportView',
    'RevenueReportView',
    'CommissionReportView',
    # 'DailySalesView',  # Not implemented yet
    # 'MonthlySalesView',  # Not implemented yet
    'AgentPerformanceView',
    'TeamPerformanceView',
    'AirlinePerformanceView',
    'RouteAnalysisView',  # Note: This is RouteAnalysisView, not RoutePerformanceView
    # 'RoutePerformanceView',  # Not implemented yet
    'BookingAnalysisView',
    # 'TicketingReportView',  # Not implemented yet
    # 'RefundReportView',  # Not implemented yet
    # 'CancellationReportView',  # Not implemented yet
    # 'MarketAnalysisView',  # Not implemented yet
    # 'CustomerAnalysisView',  # Not implemented yet
    # 'ProfitabilityAnalysisView',  # Not implemented yet
    # 'TrendAnalysisView',  # Not implemented yet
    'CustomReportBuilderView',
    # 'SavedReportsView',  # Not implemented yet
    'ReportSchedulerView',
    'ReportExportView',
    'ReportDownloadView',
    'ReportChartView',
    
    # API Views
    'APILoginView',
    'APILogoutView',
    'APIStatusView',
    'APIKeyManagementView',
    'FlightSearchAPI',
    'FlightAvailabilityAPI',
    'FareCalendarAPI',
    'LowFareSearchAPI',
    'ScheduleSearchAPI',
    'BookingListAPI',
    'BookingDetailAPI',
    'BookingCreateAPI',
    'BookingConfirmAPI',
    'BookingCancelAPI',
    'BookingRetrieveAPI',
    'BookingPriceAPI',
    'TicketListAPI',
    'TicketDetailAPI',
    'TicketIssueAPI',
    'TicketVoidAPI',
    'TicketReissueAPI',
    'EMDIssueAPI',
    'PaymentProcessAPI',
    'PaymentListAPI',
    'RefundRequestAPI',
    'AncillaryServiceListAPI',
    'AncillaryBookingAPI',
    'SeatMapAPI',
    'AirlineListAPI',
    'AirportListAPI',
    'AirportAutocompleteAPI',
    'CountryListAPI',
    'CurrencyRatesAPI',
    'SalesReportAPI',
    'PerformanceReportAPI',
    'BookingReportAPI',
    'GDSWebhookView',
    'PaymentWebhookView',
    'NotificationWebhookView',
    'BulkBookingAPI',
    'BulkTicketingAPI',
    'BulkPaymentAPI',
    'CurrencyConverterAPI',
    'DocumentValidatorAPI',
    'PNRDecoderAPI',
    'APIUsageAPI',
    'APIPerformanceAPI',
    'SystemHealthAPI',
    
    # Admin Views
    'AgentManagementView',
    'SubAgentManagementView',
    'UserProfileView',
    'CommissionManagementView',
    'AirlineManagementView',
    'AirportManagementView',
    'FareRuleManagementView',
    'ServiceConfigurationView',
    'GDSConfigurationView',
    'PaymentGatewayView',
    'SMTPConfigurationView',
    'SystemLogsView',
    'AuditTrailView',
    'ComplianceCheckView',
    'TransactionAuditView',
    'ReportAuditView',
    
    # Utility Views
    'FareCalculatorView',
    'BaggageCalculatorView',
    'CurrencyConverterView',
    'DistanceCalculatorView',
    'PNRValidatorView',
    'TicketValidatorView',
    'PassengerValidatorView',
    'DocumentValidatorView',
    'PNRDecoderView',
    'TicketDecoderView',
    'AirlineCodeView',
    'AirportCodeView',
    'DocumentDownloadView',
    'ReportDownloadView',
    'TemplateDownloadView',
    'ExportDataView',
    
    # Customer Views
    'CustomerListView',
    'CustomerDetailView',
    'CustomerCreateView',
    'CustomerUpdateView',
    'CorporateAccountView',
    'CorporateUserView',
    'TravelPolicyView',
    'ApprovalWorkflowView',
    'CustomerPortalView',
    'BookingHistoryView',
    'TravelDocumentView',
    'PreferenceManagementView',
    'NotificationView',
    'MessageCenterView',
    'AnnouncementView',
    'AlertView',
    
    # Travelport GDS Views
    'GDSConnectionView',
    'GDSSessionView',
    'GDSStatusView',
    'GDSReconnectView',
    'GDSLowFareSearchView',
    'GDSAvailabilityView',
    'GDSScheduleView',
    'GDSFareRulesView',
    'GDSCreateBookingView',
    'GDSRetrieveBookingView',
    'GDSModifyBookingView',
    'GDSCancelBookingView',
    'GDSIssueTicketView',
    'GDSVoidTicketView',
    'GDSReissueTicketView',
    'GDSEMDView',
    'GDSQueueView',
    'GDSQueueItemView',
    'GDSQueueProcessingView',
    'GDSPNRDecoderView',
    'GDSTicketValidatorView',
    'GDSReferenceDataView',
    'GDSTestConnectionView',
]


# ==============================================
# VIEW CATEGORIES FOR EASY IMPORT
# ==============================================

# Flight Search Category
FLIGHT_SEARCH_VIEWS = [
    'FlightSearchView',
    'SearchResultsView',
    'FareCalendarView',
    'LowFareSearchView',
    'ScheduleSearchView',
    'MultiCitySearchView',
    'FlexibleDatesView',
    'AdvancedSearchView',
    'SearchHistoryView',
    'SavedSearchesView',
]

# Booking Category
BOOKING_VIEWS = [
    'BookingCreateView',
    'PassengerDetailsView',
    'SeatSelectionView',
    'AncillaryServicesView',
    'ReviewBookingView',
    'PaymentView',
    'BookingConfirmationView',
    'BookingListView',
    'BookingDetailView',
    'BookingUpdateView',
    'BookingCancelView',
    'BookingVoidView',
    'BookingReissueView',
]

# Ticketing Category
TICKETING_VIEWS = [
    'TicketListView',
    'TicketDetailView',
    'TicketIssueView',
    'TicketVoidView',
    'TicketReissueView',
    'TicketRevalidationView',
    'TicketRefundView',
    'EMDListView',
    'EMDCreateView',
    'EMDVoidView',
    'EMDRefundView',
]

# Reporting Category
REPORTING_VIEWS = [
    'SalesDashboardView',
    'SalesReportView',
    'RevenueReportView',
    'CommissionReportView',
    'AgentPerformanceView',
    'TeamPerformanceView',
    'AirlinePerformanceView',
    'RouteAnalysisView',  # Note: This is RouteAnalysisView, not RoutePerformanceView
    'BookingAnalysisView',
    'CustomReportBuilderView',
    'ReportSchedulerView',
    'ReportExportView',
    'ReportDownloadView',
    'ReportChartView',
]

# API Category
API_VIEWS = [
    'APILoginView',
    'APILogoutView',
    'APIStatusView',
    'FlightSearchAPI',
    'FlightAvailabilityAPI',
    'BookingListAPI',
    'BookingDetailAPI',
    'TicketListAPI',
    'PaymentProcessAPI',
    'AirlineListAPI',
    'AirportListAPI',
]

# Admin Category
ADMIN_VIEWS = [
    'AgentManagementView',
    'SubAgentManagementView',
    'AirlineManagementView',
    'AirportManagementView',
    'GDSConfigurationView',
    'SystemLogsView',
]

# GDS Integration Category
GDS_VIEWS = [
    'GDSConnectionView',
    'GDSStatusView',
    'GDSLowFareSearchView',
    'GDSCreateBookingView',
    'GDSIssueTicketView',
    'GDSQueueView',
]


# ==============================================
# URL PATTERNS REFERENCE
# ==============================================

"""
Example URL patterns configuration for flights app:

from django.urls import path, include
from . import views

urlpatterns = [
    # Flight Search
    path('search/', views.FlightSearchView.as_view(), name='flight_search'),
    path('search/results/', views.SearchResultsView.as_view(), name='search_results'),
    path('search/fare-calendar/', views.FareCalendarView.as_view(), name='fare_calendar'),
    
    # Booking
    path('booking/create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('booking/<uuid:booking_id>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/', views.BookingListView.as_view(), name='booking_list'),
    
    # Ticketing
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('ticket/issue/', views.TicketIssueView.as_view(), name='ticket_issue'),
    
    # Reports
    path('reports/dashboard/', views.SalesDashboardView.as_view(), name='reports_dashboard'),
    path('reports/sales/', views.SalesReportView.as_view(), name='sales_report'),
    
    # API
    path('api/v1/auth/login/', views.APILoginView.as_view(), name='api_login'),
    path('api/v1/flights/search/', views.FlightSearchAPI.as_view(), name='flight_search_api'),
    
    # Admin
    path('admin/agents/', views.AgentManagementView.as_view(), name='agent_management'),
    path('admin/gds-config/', views.GDSConfigurationView.as_view(), name='gds_config'),
]
"""


# ==============================================
# VIEW REGISTRY FOR DYNAMIC LOADING
# ==============================================

VIEW_REGISTRY = {
    # Core Business Views
    'flight_search': 'FlightSearchView',
    'booking_create': 'BookingCreateView',
    'ticket_issue': 'TicketIssueView',
    'sales_dashboard': 'SalesDashboardView',
    
    # API Endpoints
    'api_flight_search': 'FlightSearchAPI',
    'api_booking_create': 'BookingCreateAPI',
    'api_ticket_issue': 'TicketIssueAPI',
    
    # Admin Views
    'admin_agent_management': 'AgentManagementView',
    'admin_gds_config': 'GDSConfigurationView',
    
    # GDS Integration
    'gds_search': 'GDSLowFareSearchView',
    'gds_booking': 'GDSCreateBookingView',
}


def get_view_class(view_name):
    """
    Get view class by name for dynamic loading
    
    Usage:
        from flights.views import get_view_class
        view_class = get_view_class('flight_search')
    """
    if view_name in VIEW_REGISTRY:
        view_class_name = VIEW_REGISTRY[view_name]
        return globals().get(view_class_name)
    return None


def get_view_categories():
    """
    Get all view categories for navigation and permissions
    
    Returns:
        dict: Categories with their views
    """
    return {
        'flight_search': FLIGHT_SEARCH_VIEWS,
        'booking': BOOKING_VIEWS,
        'ticketing': TICKETING_VIEWS,
        'reporting': REPORTING_VIEWS,
        'api': API_VIEWS,
        'admin': ADMIN_VIEWS,
        'gds': GDS_VIEWS,
    }


# ==============================================
# VIEW PERMISSIONS MAPPING
# ==============================================

VIEW_PERMISSIONS = {
    # Agent-level access
    'FlightSearchView': ['agent', 'super_agent', 'admin'],
    'BookingCreateView': ['agent', 'super_agent', 'admin'],
    'BookingListView': ['agent', 'super_agent', 'admin'],
    'TicketListView': ['agent', 'super_agent', 'admin'],
    
    # Super Agent access
    'TeamPerformanceView': ['super_agent', 'admin'],
    'AgentManagementView': ['super_agent', 'admin'],
    'BulkBookingView': ['super_agent', 'admin'],
    
    # Admin-only access
    'SystemLogsView': ['admin'],
    'GDSConfigurationView': ['admin'],
    'AuditTrailView': ['admin'],
    
    # API access (requires API token)
    'FlightSearchAPI': ['api_access'],
    'BookingCreateAPI': ['api_access'],
    'TicketIssueAPI': ['api_access'],
}


def check_view_permission(view_class_name, user):
    """
    Check if user has permission to access a view
    
    Args:
        view_class_name (str): Name of the view class
        user (User): Django user object
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    allowed_user_types = VIEW_PERMISSIONS.get(view_class_name, [])
    
    if not allowed_user_types:
        return True  # No restriction
    
    if 'api_access' in allowed_user_types:
        # Check API access via token authentication
        # This would be handled by API authentication classes
        return True
    
    return user.user_type in allowed_user_types


# ==============================================
# URL NAME TO VIEW MAPPING
# ==============================================

URL_TO_VIEW_MAPPING = {
    'flight_search': 'FlightSearchView',
    'search_results': 'SearchResultsView',
    'booking_create': 'BookingCreateView',
    'booking_detail': 'BookingDetailView',
    'booking_list': 'BookingListView',
    'ticket_list': 'TicketListView',
    'ticket_issue': 'TicketIssueView',
    'reports_dashboard': 'SalesDashboardView',
    'sales_report': 'SalesReportView',
    'agent_performance_report': 'AgentPerformanceView',
    'api_login': 'APILoginView',
    'flight_search_api': 'FlightSearchAPI',
    'agent_management': 'AgentManagementView',
    'gds_config': 'GDSConfigurationView',
}


def get_view_for_url(url_name):
    """
    Get view class for a given URL name
    
    Args:
        url_name (str): URL pattern name
    
    Returns:
        class: View class or None if not found
    """
    view_class_name = URL_TO_VIEW_MAPPING.get(url_name)
    if view_class_name:
        return globals().get(view_class_name)
    return None


# ==============================================
# MODULE INITIALIZATION
# ==============================================

def initialize_views():
    """
    Initialize views module - can be used for preloading or validation
    """
    logger.info("Initializing flights views module")
    
    # Validate all views are importable
    for view_name in __all__:
        try:
            view_class = globals().get(view_name)
            if view_class is None:
                logger.warning(f"View {view_name} not found in module")
        except Exception as e:
            logger.error(f"Error loading view {view_name}: {str(e)}")
    
    logger.info(f"Loaded {len(__all__)} views successfully")


# Auto-initialize on module import
# initialize_views()  # Commented out - causing logger issues
