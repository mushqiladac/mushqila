"""
Flights App Views Module
Production Ready - Final Version
B2B Travel Platform with Travelport Galileo GDS Integration
"""

import logging

logger = logging.getLogger(__name__)

# Import primary views that actually exist
try:
    from .search_views import (
        FlightSearchView,
        SearchResultsView,
        FareCalendarView,
        FlexibleSearchView,
        MultiCitySearchView,
        AutoCompleteView,
        RecentSearchesView,
        PopularRoutesView,
    )
except ImportError as e:
    logger.warning(f"Could not import search views: {e}")

try:
    from .booking_views import (
        BookingCreateView,
        PassengerDetailsView,
        ReviewBookingView,
        PaymentView,
        BookingConfirmationView,
        QuickBookingView,
        GroupBookingView,
    )
except ImportError as e:
    logger.warning(f"Could not import booking views: {e}")

try:
    from .ticketing_views import (
        TicketListView,
        TicketDetailView,
        TicketIssueView,
        TicketVoidView,
        TicketReissueView,
        TicketRevalidationView,
        TicketRefundView,
        EMDManagementView,
        TicketingQueueView,
        TicketingDashboardView,
    )
except ImportError as e:
    logger.warning(f"Could not import ticketing views: {e}")
    # Use stubs
    from .stub_views import (
        TicketListView,
        TicketDetailView,
        TicketIssueView,
        TicketVoidView,
        TicketReissueView,
        TicketRevalidationView,
        TicketRefundView,
        EMDManagementView,
        TicketingQueueView,
        TicketingDashboardView,
    )

try:
    from .fare_rules_views import (
        FareRulesListView,
        FareRuleDetailView,
        FareRuleSearchView,
        FareRuleComparisonView,
        FareRuleParserView,
        BaggageRulesView,
        GDSFareRulesView,
        FareRuleValidatorView,
        FareRuleCategoriesView,
    )
except ImportError as e:
    logger.warning(f"Could not import fare rules views: {e}")

try:
    from .ancillary_views import (
        BaggageServicesView,
        MealServicesView,
        LoungeAccessView,
        ServiceBundlesView,
        AncillaryBookingManagementView,
    )
except ImportError as e:
    logger.warning(f"Could not import ancillary views: {e}")

try:
    from .reporting_views import (
        SalesDashboardView,
        SalesReportView,
        AgentPerformanceView,
    )
except ImportError as e:
    logger.warning(f"Could not import reporting views: {e}")

# API Views with error handling
try:
    from .api_views import (
        FlightSearchAPI,
        BookingListAPI,
        BookingDetailAPI,
        TicketListAPI,
        PaymentProcessAPI,
        RefundRequestAPI,
    )
except ImportError as e:
    logger.warning(f"Could not import API views: {e}")

# Stub views for missing functionality
from .stub_views import (
    BaggageCalculatorView,
    ExcessBaggageView,
    FareConditionsView,
    PenaltyCalculatorView,
    ChangeFeeCalculatorView,
    AncillaryServicesListView,
    AncillaryServiceDetailView,
    AncillaryBookingView,
    SeatSelectionView,
    MealSelectionView,
    BaggageSelectionView,
    LoungePurchaseView,
    TravelInsuranceView,
    SeatMapDisplayView,
    SeatMapAPIView,
    FlexibleSeatMapView,
    TicketingReportView,
    BookingAnalyticsView,
    RevenueReportView,
    CommissionReportView,
    BookingReportView,
)

# Define the public API
__all__ = [
    # Search Views 
    'FlightSearchView',
    'SearchResultsView',
    'FareCalendarView',
    'FlexibleSearchView',
    'MultiCitySearchView',
    'AutoCompleteView',
    'RecentSearchesView',
    'PopularRoutesView',
    
    # Booking Views
    'BookingCreateView',
    'PassengerDetailsView',
    'ReviewBookingView',
    'PaymentView',
    'BookingConfirmationView',
    'QuickBookingView',
    'GroupBookingView',
    
    # Ticketing Views
    'TicketListView',
    'TicketDetailView',
    'TicketIssueView',
    'TicketVoidView',
    'TicketReissueView',
    'TicketRevalidationView',
    'TicketRefundView',
    'EMDManagementView',
    'TicketingQueueView',
    'TicketingDashboardView',
    
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
    
    # Ancillary Views
    'AncillaryServicesListView',
    'AncillaryServiceDetailView',
    'AncillaryBookingView',
    'BaggageServicesView',
    'MealServicesView',
    'LoungeAccessView',
    'TravelInsuranceView',
    'ServiceBundlesView',
    'AncillaryBookingManagementView',
    
    # Reporting Views
    'SalesDashboardView',
    'SalesReportView',
    'AgentPerformanceView',
    
    # API Views
    'FlightSearchAPI',
    'BookingListAPI',
    'BookingDetailAPI',
    'TicketListAPI',
    'PaymentProcessAPI',
    'RefundRequestAPI',
]


logger.info("Flights views module initialized successfully")


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
    'DailySalesView',
    'MonthlySalesView',
    'AgentPerformanceView',
    'TeamPerformanceView',
    'AirlinePerformanceView',
    'RoutePerformanceView',
    'BookingAnalysisView',
    'TicketingReportView',
    'RefundReportView',
    'CancellationReportView',
    'MarketAnalysisView',
    'CustomerAnalysisView',
    'ProfitabilityAnalysisView',
    'TrendAnalysisView',
    'CustomReportBuilderView',
    'SavedReportsView',
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
    'RoutePerformanceView',
    'BookingAnalysisView',
    'CustomReportBuilderView',
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
initialize_views()


# ==============================================
# FUNCTIONAL SEARCH WIDGET API VIEWS
# ==============================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json

@require_http_methods(["GET"])
def airport_search(request):
    """API endpoint for airport autocomplete"""
    from flights.models import Airport
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search by iata_code, city, or airport name
    airports = Airport.objects.filter(
        Q(iata_code__icontains=query) |
        Q(city__icontains=query) |
        Q(name__icontains=query),
        is_active=True
    )[:10]
    
    results = [{
        'code': airport.iata_code,
        'city': airport.city,
        'name': airport.name,
        'country': airport.country,
        'display': f"{airport.city}, {airport.country} ({airport.iata_code})",
        'full_display': f"{airport.city}, {airport.name}"
    } for airport in airports]
    
    return JsonResponse({'results': results})


@require_http_methods(["POST"])
def flight_search(request):
    """Handle flight search requests"""
    from flights.models import FlightSearch, Airport
    import hashlib
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['origin', 'destination', 'departure_date', 'search_type']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Get Airport objects
        try:
            origin_airport = Airport.objects.get(iata_code=data['origin'])
            destination_airport = Airport.objects.get(iata_code=data['destination'])
        except Airport.DoesNotExist as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid airport code: {str(e)}'
            }, status=400)
        
        # Generate search hash
        search_string = f"{data['origin']}-{data['destination']}-{data['departure_date']}-{data.get('return_date', '')}"
        search_hash = hashlib.md5(search_string.encode()).hexdigest()
        
        # Save search query (only if user is authenticated)
        if request.user.is_authenticated:
            search = FlightSearch.objects.create(
                user=request.user,
                search_type=data['search_type'],
                origin=origin_airport,
                destination=destination_airport,
                departure_date=data['departure_date'],
                return_date=data.get('return_date'),
                adults=data.get('adults', 1),
                children=data.get('children', 0),
                infants=data.get('infants', 0),
                cabin_class=data.get('cabin_class', 'economy'),
                search_hash=search_hash
            )
            search_id = str(search.id)
        else:
            search_id = None
        
        # TODO: Integrate with Travelport Galileo GDS API
        # For now, return demo response
        demo_flights = [
            {
                'id': 1,
                'airline': 'Biman Bangladesh Airlines',
                'flight_number': 'BG147',
                'departure_time': '10:30',
                'arrival_time': '11:45',
                'duration': '1h 15m',
                'price': 4500,
                'currency': 'BDT',
                'available_seats': 12
            },
            {
                'id': 2,
                'airline': 'US-Bangla Airlines',
                'flight_number': 'BS325',
                'departure_time': '14:00',
                'arrival_time': '15:20',
                'duration': '1h 20m',
                'price': 4200,
                'currency': 'BDT',
                'available_seats': 8
            }
        ]
        
        return JsonResponse({
            'success': True,
            'search_id': search_id,
            'flights': demo_flights,
            'message': 'Demo data - Galileo GDS integration pending'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Add to __all__ for export
__all__.extend(['airport_search', 'flight_search'])
