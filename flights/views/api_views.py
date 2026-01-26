# flights/views/api_views.py 
"""
REST API Views for B2B Travel Platform
Production Ready - Final Version
Integrated with Travelport Galileo GDS
"""

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse, Http404
from django.middleware.csrf import get_token
from django.utils import timezone
from django.db.models import Q, Count, Sum, F, Prefetch, Subquery, OuterRef, Case, When, Value
from django.db.models.functions import TruncDate, Extract, Coalesce
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import transaction, connection
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
import hashlib
import hmac
import base64
import uuid
from functools import wraps

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, viewsets, mixins

# Initialize logger early for use in exception handlers
logger = logging.getLogger(__name__)

# Optional imports for models
try:
    from flights.models import (
        Airline, Airport, Aircraft, FlightSearch, FlightSegment, FlightItinerary,
        Booking, Passenger, Ticket, PNR, Payment, Refund,
        AncillaryService, AncillaryBooking, SeatSelection, BaggageService,
        MealPreference, LoungeAccess, TravelInsurance,
        FareRule, BaggageRule,
        AvailabilityCache, BookingLimit, OverrideRule
    )
    MODELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some models not available: {str(e)}")
    MODELS_AVAILABLE = False
    # Create placeholder classes
    Airline = Airport = Aircraft = FlightSearch = FlightSegment = FlightItinerary = None
    Booking = Passenger = Ticket = PNR = Payment = Refund = None
    AncillaryService = AncillaryBooking = SeatSelection = BaggageService = None
    MealPreference = LoungeAccess = TravelInsurance = None
    FareRule = BaggageRule = None
    AvailabilityCache = BookingLimit = OverrideRule = None

# Optional imports for models that may not exist
try:
    from flights.models import EMD
except ImportError:
    EMD = None

try:
    from flights.models import CommissionTransaction
except ImportError:
    CommissionTransaction = None

try:
    from flights.models import SpecialAssistance
except ImportError:
    SpecialAssistance = None

try:
    from flights.models import FareCalculation
except ImportError:
    FareCalculation = None

try:
    from flights.models import TaxBreakdown
except ImportError:
    TaxBreakdown = None

try:
    from flights.models import ServiceCategory
except ImportError:
    ServiceCategory = None

try:
    from flights.models import ServiceBundle
except ImportError:
    ServiceBundle = None

try:
    from flights.models import TicketingRule
except ImportError:
    TicketingRule = None

try:
    from flights.models import TicketQueue
except ImportError:
    TicketQueue = None
# Optional imports for serializers
try:
    from flights.serializers import (
        AirlineSerializer, AirportSerializer, AircraftSerializer,
        FlightSearchSerializer, FlightSegmentSerializer, FlightItinerarySerializer,
        BookingSerializer, PassengerSerializer, TicketSerializer, PNRSerializer,
        PaymentSerializer, RefundSerializer,
        AncillaryServiceSerializer, AncillaryBookingSerializer, SeatSelectionSerializer,
        BaggageServiceSerializer, MealPreferenceSerializer, LoungeAccessSerializer,
        TravelInsuranceSerializer, FareRuleSerializer,
        BaggageRuleSerializer,
        AvailabilityCacheSerializer, BookingLimitSerializer,
        OverrideRuleSerializer, UserSerializer
    )
    SERIALIZERS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some serializers not available: {str(e)}")
    SERIALIZERS_AVAILABLE = False
    # Create placeholder classes
    AirlineSerializer = AirportSerializer = AircraftSerializer = None
    FlightSearchSerializer = FlightSegmentSerializer = FlightItinerarySerializer = None
    BookingSerializer = PassengerSerializer = TicketSerializer = PNRSerializer = None
    PaymentSerializer = RefundSerializer = None
    AncillaryServiceSerializer = AncillaryBookingSerializer = SeatSelectionSerializer = None
    BaggageServiceSerializer = MealPreferenceSerializer = LoungeAccessSerializer = None
    TravelInsuranceSerializer = FareRuleSerializer = None
    BaggageRuleSerializer = None
    AvailabilityCacheSerializer = BookingLimitSerializer = None
    OverrideRuleSerializer = UserSerializer = None

# Optional serializers that may not exist
try:
    from flights.serializers import EMDSerializer
except ImportError:
    EMDSerializer = None

try:
    from flights.serializers import CommissionTransactionSerializer
except ImportError:
    CommissionTransactionSerializer = None

try:
    from flights.serializers import SpecialAssistanceSerializer
except ImportError:
    SpecialAssistanceSerializer = None

try:
    from flights.serializers import FareCalculationSerializer
except ImportError:
    FareCalculationSerializer = None

try:
    from flights.serializers import TaxBreakdownSerializer
except ImportError:
    TaxBreakdownSerializer = None

try:
    from flights.serializers import ServiceCategorySerializer
except ImportError:
    ServiceCategorySerializer = None

try:
    from flights.serializers import ServiceBundleSerializer
except ImportError:
    ServiceBundleSerializer = None

try:
    from flights.serializers import TicketingRuleSerializer
except ImportError:
    TicketingRuleSerializer = None

try:
    from flights.serializers import TicketQueueSerializer
except ImportError:
    TicketQueueSerializer = None
# Optional service imports
try:
    from flights.services.flight_search import FlightSearchService
except ImportError:
    FlightSearchService = None

try:
    from flights.services.booking_service import BookingService
except ImportError:
    BookingService = None

try:
    from flights.services.ticketing_service import TicketingService
except ImportError:
    TicketingService = None

try:
    from flights.services.payment_service import PaymentService
except ImportError:
    PaymentService = None

try:
    from flights.services.refund_service import RefundService
except ImportError:
    RefundService = None

try:
    from flights.services.ancillary_service import AncillaryServiceManager
except ImportError:
    AncillaryServiceManager = None

try:
    from flights.services.gds_service import GDSFlightService, GDSBookingService, GDSTicketingService
except ImportError:
    GDSFlightService = GDSBookingService = GDSTicketingService = None

try:
    from flights.services.integration_service import IntegrationService
except ImportError:
    IntegrationService = None

try:
    from flights.services.notification_service import APINotificationService
except ImportError:
    APINotificationService = None

# Optional utils imports
try:
    from flights.utils.permissions import APIPermission
except ImportError:
    APIPermission = None

try:
    from flights.utils.validators import APIValidator
except ImportError:
    APIValidator = None

try:
    from flights.utils.cache import APICache
except ImportError:
    APICache = None

try:
    from flights.utils.rate_limit import APIRateLimit
except ImportError:
    APIRateLimit = None

try:
    from flights.utils.logging import APILogger
except ImportError:
    APILogger = None

try:
    from flights.utils.security import APISecurity
except ImportError:
    APISecurity = None

try:
    from flights.utils.monitoring import APIMonitoring
except ImportError:
    APIMonitoring = None

# Logger already initialized at the top of the file


# ==============================================
# CUSTOM PERMISSIONS
# ==============================================

class IsAgentUser(BasePermission):
    """Allow access only to agent users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type in ['agent', 'super_agent']


class IsSuperAgent(BasePermission):
    """Allow access only to super agent users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'super_agent'


class IsAdminUser(BasePermission):
    """Allow access only to admin users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'admin'


class HasAPIAccess(BasePermission):
    """Check if user has API access enabled"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.profile.api_access_enabled if hasattr(request.user, 'profile') else False


# ==============================================
# RATE LIMITING CLASSES
# ==============================================

class UserRateThrottle(UserRateThrottle):
    """Custom user rate throttle"""
    rate = '1000/hour'


class AgentRateThrottle(UserRateThrottle):
    """Agent-specific rate throttle"""
    rate = '5000/hour'


class SuperAgentRateThrottle(UserRateThrottle):
    """Super agent rate throttle"""
    rate = '10000/hour'


class SearchRateThrottle(UserRateThrottle):
    """Flight search rate throttle"""
    rate = '100/minute'


class BookingRateThrottle(UserRateThrottle):
    """Booking rate throttle"""
    rate = '50/minute'


# ==============================================
# PAGINATION CLASSES
# ==============================================

class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API results"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """Large pagination for API results"""
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500


# ==============================================
# AUTHENTICATION API VIEWS
# ==============================================

@method_decorator(csrf_exempt, name='dispatch')
class APILoginView(View):
    """API Login endpoint - Get authentication token"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'error': 'Username and password are required'
                }, status=400)
            
            # Authenticate user
            user = authenticate(username=username, password=password)
            
            if user is None:
                # Log failed attempt
                APILogger.log_failed_login(request, username)
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=401)
            
            # Check if user has API access
            if not APIPermission.has_api_access(user):
                return JsonResponse({
                    'success': False,
                    'error': 'API access not enabled for this account'
                }, status=403)
            
            # Check if account is active
            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'error': 'Account is inactive'
                }, status=403)
            
            # Generate or get existing token
            token, created = Token.objects.get_or_create(user=user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            # Log successful login
            APILogger.log_successful_login(request, user)
            
            # Prepare user data
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company_name': user.profile.company_name if hasattr(user, 'profile') else '',
                'iata_number': user.profile.iata_number if hasattr(user, 'profile') else '',
                'currency': user.profile.currency if hasattr(user, 'profile') else 'SAR',
            }
            
            return JsonResponse({
                'success': True,
                'token': token.key,
                'user': user_data,
                'permissions': APIPermission.get_user_permissions(user),
                'settings': {
                    'rate_limit': APIRateLimit.get_user_rate_limit(user),
                    'api_version': '1.0',
                    'supported_features': APIPermission.get_supported_features(user),
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"API login error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class APILogoutView(View):
    """API Logout endpoint - Invalidate token"""
    
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            
            if auth_header.startswith('Token '):
                token_key = auth_header.split(' ')[1]
                try:
                    token = Token.objects.get(key=token_key)
                    token.delete()
                    
                    # Log logout
                    APILogger.log_logout(request, token.user)
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Logged out successfully'
                    })
                except Token.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': True,
                'message': 'Logged out'
            })
            
        except Exception as e:
            logger.error(f"API logout error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class APIStatusView(APIView):
    """API Status endpoint - Health check and system status"""
    
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        try:
            # Check database connection
            try:
                from django.db import connection
                connection.ensure_connection()
                db_status = 'connected'
            except Exception:
                db_status = 'disconnected'
            
            # Check cache connection
            try:
                cache.set('health_check', 'ok', 5)
                cache_status = 'connected' if cache.get('health_check') == 'ok' else 'disconnected'
            except Exception:
                cache_status = 'disconnected'
            
            # Get system statistics
            stats = {
                'total_airlines': Airline.objects.filter(is_active=True).count(),
                'total_airports': Airport.objects.filter(is_active=True).count(),
                'total_bookings_today': Booking.objects.filter(
                    created_at__date=timezone.now().date()
                ).count(),
                'total_tickets_today': Ticket.objects.filter(
                    issued_at__date=timezone.now().date(),
                    status='issued'
                ).count(),
                'system_uptime': APIMonitoring.get_system_uptime(),
                'api_requests_today': APIMonitoring.get_api_requests_count(),
                'average_response_time': APIMonitoring.get_average_response_time(),
            }
            
            # Get service status
            service_status = {
                'gds_connection': IntegrationService.check_gds_connection(),
                'payment_gateway': IntegrationService.check_payment_gateway(),
                'sms_service': IntegrationService.check_sms_service(),
                'email_service': IntegrationService.check_email_service(),
            }
            
            status_data = {
                'status': 'operational',
                'timestamp': timezone.now().isoformat(),
                'version': '1.0.0',
                'environment': 'production',
                'services': {
                    'database': db_status,
                    'cache': cache_status,
                    **service_status
                },
                'statistics': stats,
                'rate_limits': APIRateLimit.get_system_rate_limits(),
                'maintenance_window': None,
                'supported_endpoints': self.get_supported_endpoints(),
            }
            
            return Response(status_data)
            
        except Exception as e:
            logger.error(f"API status error: {str(e)}", exc_info=True)
            return Response({
                'status': 'degraded',
                'error': str(e),
                'timestamp': timezone.now().isoformat(),
            }, status=500)
    
    def get_supported_endpoints(self):
        """Get list of supported API endpoints"""
        return {
            'authentication': ['POST /api/v1/auth/login', 'POST /api/v1/auth/logout'],
            'flight_search': ['POST /api/v1/flights/search', 'GET /api/v1/flights/availability'],
            'booking': ['POST /api/v1/bookings', 'GET /api/v1/bookings', 'GET /api/v1/bookings/{id}'],
            'ticketing': ['POST /api/v1/tickets', 'GET /api/v1/tickets', 'POST /api/v1/tickets/{id}/void'],
            'ancillary': ['GET /api/v1/ancillary', 'POST /api/v1/ancillary/book'],
            'reports': ['GET /api/v1/reports/sales', 'GET /api/v1/reports/performance'],
        }


# ==============================================
# FLIGHT SEARCH API VIEWS
# ==============================================

class FlightSearchAPI(APIView):
    """Flight Search API - Search flights with Travelport GDS"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    throttle_classes = [SearchRateThrottle]
    
    def post(self, request):
        try:
            # Validate request
            validator = APIValidator()
            validation_result = validator.validate_flight_search_request(request.data)
            
            if not validation_result['valid']:
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation_result['errors']
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'flight_search')
            
            # Initialize flight search service
            flight_search_service = FlightSearchService()
            
            # Perform flight search
            search_data = request.data.copy()
            search_data['user'] = request.user
            
            search_result = flight_search_service.search_flights(
                user=request.user,
                search_data=search_data
            )
            
            # Cache search results
            if search_result.get('search_hash'):
                APICache.cache_search_results(
                    search_hash=search_result['search_hash'],
                    results=search_result,
                    user=request.user
                )
            
            # Add metadata
            search_result['metadata'] = {
                'search_id': search_result.get('search_id'),
                'search_hash': search_result.get('search_hash'),
                'results_count': len(search_result.get('itineraries', [])),
                'cache_hit': search_result.get('cache_hit', False),
                'processing_time': search_result.get('processing_time', 0),
                'gds_provider': search_result.get('gds_provider', 'travelport'),
            }
            
            return Response(search_result)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': str(e)
            }, status=400)
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'details': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Flight search API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'flight_search', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error',
                'request_id': request.META.get('HTTP_X_REQUEST_ID', '')
            }, status=500)


class FlightAvailabilityAPI(APIView):
    """Flight Availability API - Real-time seat availability"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    throttle_classes = [SearchRateThrottle]
    
    def get(self, request):
        try:
            # Get query parameters
            origin = request.GET.get('origin', '').upper()
            destination = request.GET.get('destination', '').upper()
            departure_date = request.GET.get('departure_date', '')
            airline = request.GET.get('airline', '').upper()
            cabin_class = request.GET.get('cabin_class', 'economy')
            
            # Validate parameters
            if not all([origin, destination, departure_date]):
                return Response({
                    'success': False,
                    'error': 'Missing required parameters: origin, destination, departure_date'
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'flight_availability')
            
            # Initialize GDS service
            gds_service = GDSFlightService()
            
            # Check availability
            availability_result = gds_service.check_availability(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                airline=airline if airline else None,
                cabin_class=cabin_class
            )
            
            return Response(availability_result)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Flight availability API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'flight_availability', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class FareCalendarAPI(APIView):
    """Fare Calendar API - Monthly fare trends"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def get(self, request):
        try:
            origin = request.GET.get('origin', '').upper()
            destination = request.GET.get('destination', '').upper()
            month = request.GET.get('month', '')
            year = request.GET.get('year', '')
            
            # Validate parameters
            if not all([origin, destination, month, year]):
                return Response({
                    'success': False,
                    'error': 'Missing required parameters: origin, destination, month, year'
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'fare_calendar')
            
            # Initialize flight search service
            flight_search_service = FlightSearchService()
            
            # Get fare calendar
            calendar_data = flight_search_service.get_fare_calendar(
                origin=origin,
                destination=destination,
                month=int(month),
                year=int(year)
            )
            
            return Response(calendar_data)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': 'Invalid parameters',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Fare calendar API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'fare_calendar', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class LowFareSearchAPI(APIView):
    """Low Fare Search API - Find cheapest fares"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    throttle_classes = [SearchRateThrottle]
    
    def post(self, request):
        try:
            # Validate request
            validator = APIValidator()
            validation_result = validator.validate_low_fare_search_request(request.data)
            
            if not validation_result['valid']:
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation_result['errors']
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'low_fare_search')
            
            # Initialize flight search service
            flight_search_service = FlightSearchService()
            
            # Perform low fare search
            search_data = request.data.copy()
            
            low_fare_result = flight_search_service.low_fare_search(
                search_data=search_data,
                user=request.user
            )
            
            return Response(low_fare_result)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Low fare search API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'low_fare_search', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class ScheduleSearchAPI(APIView):
    """Schedule Search API - Flight schedules only"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def get(self, request):
        try:
            origin = request.GET.get('origin', '').upper()
            destination = request.GET.get('destination', '').upper()
            departure_date = request.GET.get('departure_date', '')
            airline = request.GET.get('airline', '').upper()
            
            # Validate parameters
            if not all([origin, destination, departure_date]):
                return Response({
                    'success': False,
                    'error': 'Missing required parameters: origin, destination, departure_date'
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'schedule_search')
            
            # Initialize GDS service
            gds_service = GDSFlightService()
            
            # Get schedules
            schedule_result = gds_service.get_schedules(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                airline=airline if airline else None
            )
            
            return Response(schedule_result)
            
        except Exception as e:
            logger.error(f"Schedule search API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'schedule_search', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


# ==============================================
# BOOKING API VIEWS
# ==============================================

class BookingListAPI(generics.ListCreateAPIView):
    """Booking List and Create API - Manage bookings"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    throttle_classes = [BookingRateThrottle]
    serializer_class = BookingSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Apply user permissions
        if self.request.user.user_type == 'agent':
            queryset = Booking.objects.filter(agent=self.request.user)
        elif self.request.user.user_type == 'sub_agent':
            parent_agent = self.request.user.parent_agent
            if parent_agent:
                queryset = Booking.objects.filter(agent=parent_agent)
            else:
                queryset = Booking.objects.none()
        else:
            queryset = Booking.objects.all()
        
        # Apply filters
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        airline = self.request.GET.get('airline', '')
        if airline:
            queryset = queryset.filter(
                itinerary__segments__airline__code=airline
            ).distinct()
        
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(booking_reference__icontains=search) |
                Q(pnr__icontains=search) |
                Q(passengers__first_name__icontains=search) |
                Q(passengers__last_name__icontains=search)
            ).distinct()
        
        return queryset.select_related(
            'itinerary',
            'itinerary__search'
        ).prefetch_related(
            'passengers',
            'tickets'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Log API request
        APILogger.log_api_request(self.request, 'booking_create')
        
        # Initialize booking service
        booking_service = BookingService()
        
        # Get booking data
        booking_data = self.request.data.copy()
        
        # Create booking
        result = booking_service.create_booking(
            booking_data=booking_data,
            user=self.request.user
        )
        
        if result['success']:
            serializer.instance = result['booking']
        else:
            raise ValidationError(result.get('error', 'Booking creation failed'))
    
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Booking create API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'booking_create', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class BookingDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """Booking Detail API - View, update, cancel bookings"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    serializer_class = BookingSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        # Apply user permissions
        if self.request.user.user_type == 'agent':
            return Booking.objects.filter(agent=self.request.user)
        elif self.request.user.user_type == 'sub_agent':
            parent_agent = self.request.user.parent_agent
            if parent_agent:
                return Booking.objects.filter(agent=parent_agent)
            else:
                return Booking.objects.none()
        return Booking.objects.all()
    
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, id=self.kwargs['id'])
        
        # Check permission
        if not APIPermission.can_access_booking(self.request.user, obj):
            raise PermissionDenied("You don't have permission to access this booking")
        
        return obj
    
    def update(self, request, *args, **kwargs):
        try:
            # Log API request
            APILogger.log_api_request(request, 'booking_update')
            
            booking = self.get_object()
            booking_service = BookingService()
            
            # Update booking
            result = booking_service.update_booking(
                booking=booking,
                update_data=request.data,
                user=request.user
            )
            
            if result['success']:
                return Response(BookingSerializer(result['booking']).data)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Update failed')
                }, status=400)
                
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Booking update API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'booking_update', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    def destroy(self, request, *args, **kwargs):
        try:
            # Log API request
            APILogger.log_api_request(request, 'booking_delete')
            
            booking = self.get_object()
            booking_service = BookingService()
            
            # Cancel booking
            result = booking_service.cancel_booking(
                booking=booking,
                cancellation_reason=request.data.get('reason', 'API cancellation'),
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Booking cancelled successfully'
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Cancellation failed')
                }, status=400)
                
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Booking delete API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'booking_delete', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class BookingConfirmAPI(APIView):
    """Booking Confirmation API - Confirm PNR with GDS"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check permission
            if not APIPermission.can_access_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to access this booking")
            
            # Log API request
            APILogger.log_api_request(request, 'booking_confirm')
            
            # Initialize booking service
            booking_service = BookingService()
            
            # Confirm booking
            result = booking_service.confirm_booking(
                booking=booking,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Booking confirmed successfully',
                    'booking': BookingSerializer(result['booking']).data
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Confirmation failed')
                }, status=400)
                
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Booking confirm API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'booking_confirm', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class BookingRetrieveAPI(APIView):
    """Booking Retrieve API - Retrieve PNR from GDS"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request):
        try:
            pnr = request.data.get('pnr', '').strip().upper()
            
            if not pnr:
                return Response({
                    'success': False,
                    'error': 'PNR is required'
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'booking_retrieve')
            
            # Initialize GDS service
            gds_service = GDSBookingService()
            
            # Retrieve booking from GDS
            result = gds_service.retrieve_booking(pnr=pnr)
            
            if result['success']:
                return Response({
                    'success': True,
                    'booking': result['booking']
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Retrieval failed')
                }, status=400)
                
        except Exception as e:
            logger.error(f"Booking retrieve API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'booking_retrieve', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class BookingPriceAPI(APIView):
    """Booking Price API - Price itinerary before booking"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request):
        try:
            # Validate request
            validator = APIValidator()
            validation_result = validator.validate_price_request(request.data)
            
            if not validation_result['valid']:
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation_result['errors']
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'booking_price')
            
            # Initialize booking service
            booking_service = BookingService()
            
            # Price itinerary
            result = booking_service.price_itinerary(
                pricing_data=request.data,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'pricing': result['pricing']
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Pricing failed')
                }, status=400)
                
        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Booking price API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'booking_price', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


# ==============================================
# TICKETING API VIEWS
# ==============================================

class TicketListAPI(generics.ListCreateAPIView):
    """Ticket List and Create API - Manage tickets"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    serializer_class = TicketSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Apply user permissions
        if self.request.user.user_type == 'agent':
            queryset = Ticket.objects.filter(booking__agent=self.request.user)
        elif self.request.user.user_type == 'sub_agent':
            parent_agent = self.request.user.parent_agent
            if parent_agent:
                queryset = Ticket.objects.filter(booking__agent=parent_agent)
            else:
                queryset = Ticket.objects.none()
        else:
            queryset = Ticket.objects.all()
        
        # Apply filters
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        ticket_type = self.request.GET.get('ticket_type', '')
        if ticket_type:
            queryset = queryset.filter(ticket_type=ticket_type)
        
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(issued_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(issued_at__date__lte=date_to)
        
        return queryset.select_related(
            'booking',
            'passenger',
            'pnr'
        ).prefetch_related(
            'coupons'
        ).order_by('-issued_at')
    
    def perform_create(self, serializer):
        # Log API request
        APILogger.log_api_request(self.request, 'ticket_create')
        
        # Initialize ticketing service
        ticketing_service = TicketingService()
        
        # Get ticket data
        ticket_data = self.request.data.copy()
        
        # Create ticket
        result = ticketing_service.issue_ticket_api(
            ticket_data=ticket_data,
            user=self.request.user
        )
        
        if result['success']:
            serializer.instance = result['ticket']
        else:
            raise ValidationError(result.get('error', 'Ticket issuance failed'))


class TicketDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """Ticket Detail API - View, update, void tickets"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    serializer_class = TicketSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        # Apply user permissions
        if self.request.user.user_type == 'agent':
            return Ticket.objects.filter(booking__agent=self.request.user)
        elif self.request.user.user_type == 'sub_agent':
            parent_agent = self.request.user.parent_agent
            if parent_agent:
                return Ticket.objects.filter(booking__agent=parent_agent)
            else:
                return Ticket.objects.none()
        return Ticket.objects.all()
    
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, id=self.kwargs['id'])
        
        # Check permission
        if not APIPermission.can_access_ticket(self.request.user, obj):
            raise PermissionDenied("You don't have permission to access this ticket")
        
        return obj


class TicketVoidAPI(APIView):
    """Ticket Void API - Void issued ticket"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request, ticket_id):
        try:
            # Get ticket
            ticket = get_object_or_404(Ticket, id=ticket_id)
            
            # Check permission
            if not APIPermission.can_access_ticket(request.user, ticket):
                raise PermissionDenied("You don't have permission to access this ticket")
            
            # Log API request
            APILogger.log_api_request(request, 'ticket_void')
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            # Void ticket
            result = ticketing_service.void_ticket_api(
                ticket=ticket,
                void_data=request.data,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Ticket voided successfully',
                    'ticket': TicketSerializer(result['ticket']).data
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Void failed')
                }, status=400)
                
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Ticket void API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'ticket_void', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class TicketReissueAPI(APIView):
    """Ticket Reissue API - Reissue/reroute ticket"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request, ticket_id):
        try:
            # Get ticket
            ticket = get_object_or_404(Ticket, id=ticket_id)
            
            # Check permission
            if not APIPermission.can_access_ticket(request.user, ticket):
                raise PermissionDenied("You don't have permission to access this ticket")
            
            # Log API request
            APILogger.log_api_request(request, 'ticket_reissue')
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            # Reissue ticket
            result = ticketing_service.reissue_ticket_api(
                original_ticket=ticket,
                reissue_data=request.data,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Ticket reissued successfully',
                    'original_ticket': TicketSerializer(ticket).data,
                    'new_ticket': TicketSerializer(result['new_ticket']).data
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Reissue failed')
                }, status=400)
                
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Ticket reissue API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'ticket_reissue', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class EMDIssueAPI(APIView):
    """EMD Issue API - Issue Electronic Miscellaneous Document"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request):
        try:
            # Validate request
            validator = APIValidator()
            validation_result = validator.validate_emd_request(request.data)
            
            if not validation_result['valid']:
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation_result['errors']
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'emd_issue')
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            # Issue EMD
            result = ticketing_service.issue_emd_api(
                emd_data=request.data,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'EMD issued successfully',
                    'emd': EMDSerializer(result['emd']).data
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'EMD issuance failed')
                }, status=400)
                
        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"EMD issue API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'emd_issue', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


# ==============================================
# PAYMENT API VIEWS
# ==============================================

class PaymentProcessAPI(APIView):
    """Payment Processing API - Process booking payments"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check permission
            if not APIPermission.can_access_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to access this booking")
            
            # Log API request
            APILogger.log_api_request(request, 'payment_process')
            
            # Initialize payment service
            payment_service = PaymentService()
            
            # Process payment
            result = payment_service.process_payment_api(
                booking=booking,
                payment_data=request.data,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Payment processed successfully',
                    'payment': PaymentSerializer(result['payment']).data,
                    'booking': BookingSerializer(result['booking']).data
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Payment processing failed')
                }, status=400)
                
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Payment process API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'payment_process', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class PaymentListAPI(generics.ListAPIView):
    """Payment List API - View payment history"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    serializer_class = PaymentSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Apply user permissions
        if self.request.user.user_type == 'agent':
            queryset = Payment.objects.filter(booking__agent=self.request.user)
        elif self.request.user.user_type == 'sub_agent':
            parent_agent = self.request.user.parent_agent
            if parent_agent:
                queryset = Payment.objects.filter(booking__agent=parent_agent)
            else:
                queryset = Payment.objects.none()
        else:
            queryset = Payment.objects.all()
        
        # Apply filters
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        payment_method = self.request.GET.get('payment_method', '')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.select_related(
            'booking'
        ).order_by('-created_at')


class RefundRequestAPI(APIView):
    """Refund Request API - Request refund for booking"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check permission
            if not APIPermission.can_access_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to access this booking")
            
            # Log API request
            APILogger.log_api_request(request, 'refund_request')
            
            # Initialize refund service
            refund_service = RefundService()
            
            # Request refund
            result = refund_service.request_refund_api(
                booking=booking,
                refund_data=request.data,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Refund requested successfully',
                    'refund': RefundSerializer(result['refund']).data
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Refund request failed')
                }, status=400)
                
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Refund request API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'refund_request', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


# ==============================================
# ANCILLARY SERVICES API VIEWS
# ==============================================

class AncillaryServiceListAPI(generics.ListAPIView):
    """Ancillary Service List API - Browse available services"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    serializer_class = AncillaryServiceSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = AncillaryService.objects.filter(is_active=True)
        
        # Apply filters
        service_type = self.request.GET.get('service_type', '')
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        airline = self.request.GET.get('airline', '')
        if airline:
            queryset = queryset.filter(airline__code=airline)
        
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.select_related(
            'airline',
            'category'
        ).order_by('airline__code', 'service_type', 'name')


class AncillaryBookingAPI(APIView):
    """Ancillary Booking API - Book ancillary services"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def post(self, request):
        try:
            # Validate request
            validator = APIValidator()
            validation_result = validator.validate_ancillary_booking_request(request.data)
            
            if not validation_result['valid']:
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation_result['errors']
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'ancillary_booking')
            
            # Initialize ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Book ancillary service
            result = ancillary_manager.book_service_api(
                booking_data=request.data,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Ancillary service booked successfully',
                    'booking': AncillaryBookingSerializer(result['booking']).data
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Booking failed')
                }, status=400)
                
        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Ancillary booking API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'ancillary_booking', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class SeatMapAPI(APIView):
    """Seat Map API - Get aircraft seat map"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def get(self, request):
        try:
            flight_number = request.GET.get('flight_number', '').strip()
            departure_date = request.GET.get('departure_date', '').strip()
            origin = request.GET.get('origin', '').upper()
            destination = request.GET.get('destination', '').upper()
            
            # Validate parameters
            if not all([flight_number, departure_date, origin, destination]):
                return Response({
                    'success': False,
                    'error': 'Missing required parameters: flight_number, departure_date, origin, destination'
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'seat_map')
            
            # Initialize GDS service
            gds_service = GDSFlightService()
            
            # Get seat map
            seat_map_result = gds_service.get_seat_map(
                flight_number=flight_number,
                departure_date=departure_date,
                origin=origin,
                destination=destination
            )
            
            return Response(seat_map_result)
            
        except Exception as e:
            logger.error(f"Seat map API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'seat_map', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


# ==============================================
# REFERENCE DATA API VIEWS
# ==============================================

class AirlineListAPI(generics.ListAPIView):
    """Airline List API - Get airline reference data"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess]
    serializer_class = AirlineSerializer
    pagination_class = LargeResultsSetPagination
    
    def get_queryset(self):
        queryset = Airline.objects.filter(is_active=True)
        
        # Apply filters
        country = self.request.GET.get('country', '')
        if country:
            queryset = queryset.filter(country_code=country)
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(country__icontains=search)
            )
        
        return queryset.order_by('name')


class AirportListAPI(generics.ListAPIView):
    """Airport List API - Get airport reference data"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess]
    serializer_class = AirportSerializer
    pagination_class = LargeResultsSetPagination
    
    def get_queryset(self):
        queryset = Airport.objects.filter(is_active=True)
        
        # Apply filters
        country = self.request.GET.get('country', '')
        if country:
            queryset = queryset.filter(country_code=country)
        
        city = self.request.GET.get('city', '')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(iata_code__icontains=search) |
                Q(name__icontains=search) |
                Q(city__icontains=search) |
                Q(country__icontains=search)
            )
        
        return queryset.order_by('city', 'name')


class AirportAutocompleteAPI(APIView):
    """Airport Autocomplete API - Search airports"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess]
    
    def get(self, request):
        try:
            query = request.GET.get('q', '').strip()
            
            if len(query) < 2:
                return Response({'results': []})
            
            airports = Airport.objects.filter(
                Q(iata_code__icontains=query) |
                Q(city__icontains=query) |
                Q(name__icontains=query) |
                Q(country__icontains=query)
            ).filter(is_active=True)[:20]
            
            results = []
            for airport in airports:
                results.append({
                    'id': airport.iata_code,
                    'code': airport.iata_code,
                    'name': airport.name,
                    'city': airport.city,
                    'country': airport.country,
                    'country_code': airport.country_code,
                    'display_text': f"{airport.iata_code} - {airport.city}, {airport.country}",
                })
            
            return Response({'results': results})
            
        except Exception as e:
            logger.error(f"Airport autocomplete API error: {str(e)}")
            return Response({'results': []}, status=500)


class CountryListAPI(APIView):
    """Country List API - Get country reference data"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess]
    
    def get(self, request):
        try:
            # Get cached country list
            countries = cache.get('country_list')
            
            if not countries:
                # Get unique countries from airports
                countries = list(Airport.objects.filter(
                    is_active=True
                ).values_list(
                    'country', 'country_code'
                ).distinct().order_by('country'))
                
                # Format as list of dicts
                countries = [
                    {'name': country[0], 'code': country[1]}
                    for country in countries
                ]
                
                # Cache for 24 hours
                cache.set('country_list', countries, 86400)
            
            return Response({
                'success': True,
                'countries': countries,
                'count': len(countries),
            })
            
        except Exception as e:
            logger.error(f"Country list API error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch country list'
            }, status=500)


# ==============================================
# REPORTS API VIEWS
# ==============================================

class SalesReportAPI(APIView):
    """Sales Report API - Generate sales reports"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def get(self, request):
        try:
            # Get parameters
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            report_type = request.GET.get('type', 'daily')
            airline = request.GET.get('airline', '')
            format = request.GET.get('format', 'json')
            
            # Validate parameters
            if not start_date or not end_date:
                # Default to last 30 days
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
            else:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Invalid date format. Use YYYY-MM-DD'
                    }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'sales_report')
            
            # Initialize reporting service
            from flights.services.reporting_service import SalesReportingService
            reporting_service = SalesReportingService()
            
            # Generate report
            if report_type == 'daily':
                report_data = reporting_service.generate_daily_sales_report(
                    start_date=start_date,
                    end_date=end_date,
                    airline_code=airline if airline else None,
                    agent_id=request.user.id if request.user.user_type != 'admin' else None
                )
            elif report_type == 'airline':
                report_data = reporting_service.generate_airline_sales_report(
                    start_date=start_date,
                    end_date=end_date,
                    agent_id=request.user.id if request.user.user_type != 'admin' else None
                )
            elif report_type == 'agent':
                if request.user.user_type != 'admin':
                    raise PermissionDenied("Only admin can access agent sales report")
                report_data = reporting_service.generate_agent_sales_report(
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid report type'
                }, status=400)
            
            # Format response
            if format == 'csv':
                # Generate CSV response
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Write header based on report type
                if report_type == 'daily':
                    writer.writerow(['Date', 'Bookings', 'Tickets', 'Revenue', 'Commission'])
                    for row in report_data.get('daily_data', []):
                        writer.writerow([
                            row['date'],
                            row['bookings'],
                            row['tickets'],
                            row['revenue'],
                            row['commission']
                        ])
                elif report_type == 'airline':
                    writer.writerow(['Airline', 'Bookings', 'Tickets', 'Revenue', 'Market Share'])
                    for row in report_data.get('airline_data', []):
                        writer.writerow([
                            row['airline'],
                            row['bookings'],
                            row['tickets'],
                            row['revenue'],
                            row['market_share']
                        ])
                
                response = HttpResponse(output.getvalue(), content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.csv"'
                return response
            
            else:
                # JSON response
                return Response({
                    'success': True,
                    'report_type': report_type,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'generated_at': timezone.now().isoformat(),
                    'data': report_data
                })
                
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=403)
        except Exception as e:
            logger.error(f"Sales report API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'sales_report', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


class PerformanceReportAPI(APIView):
    """Performance Report API - Agent performance metrics"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAgentUser]
    
    def get(self, request):
        try:
            # Get parameters
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            metrics = request.GET.getlist('metrics', ['bookings', 'revenue', 'conversion'])
            
            # Validate parameters
            if not start_date or not end_date:
                # Default to last 30 days
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
            else:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Invalid date format. Use YYYY-MM-DD'
                    }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'performance_report')
            
            # Calculate performance metrics
            performance_data = self.calculate_performance_metrics(
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                metrics=metrics
            )
            
            return Response({
                'success': True,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': metrics,
                'data': performance_data,
                'generated_at': timezone.now().isoformat(),
            })
            
        except Exception as e:
            logger.error(f"Performance report API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'performance_report', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    def calculate_performance_metrics(self, user, start_date, end_date, metrics):
        """Calculate performance metrics"""
        performance = {}
        
        # Get base queryset
        if user.user_type == 'agent':
            bookings_qs = Booking.objects.filter(agent=user)
            tickets_qs = Ticket.objects.filter(booking__agent=user)
        elif user.user_type == 'sub_agent':
            parent_agent = user.parent_agent
            if parent_agent:
                bookings_qs = Booking.objects.filter(agent=parent_agent)
                tickets_qs = Ticket.objects.filter(booking__agent=parent_agent)
            else:
                bookings_qs = Booking.objects.none()
                tickets_qs = Ticket.objects.none()
        else:
            bookings_qs = Booking.objects.all()
            tickets_qs = Ticket.objects.all()
        
        # Apply date filter
        bookings_qs = bookings_qs.filter(created_at__date__range=[start_date, end_date])
        tickets_qs = tickets_qs.filter(issued_at__date__range=[start_date, end_date])
        
        # Calculate metrics
        if 'bookings' in metrics:
            performance['total_bookings'] = bookings_qs.count()
            performance['confirmed_bookings'] = bookings_qs.filter(status='confirmed').count()
            performance['cancelled_bookings'] = bookings_qs.filter(status='cancelled').count()
        
        if 'revenue' in metrics:
            revenue_data = bookings_qs.filter(status='confirmed').aggregate(
                total_revenue=Sum('total_amount'),
                average_booking_value=Avg('total_amount')
            )
            performance['total_revenue'] = revenue_data['total_revenue'] or Decimal('0.00')
            performance['average_booking_value'] = revenue_data['average_booking_value'] or Decimal('0.00')
        
        if 'tickets' in metrics:
            performance['tickets_issued'] = tickets_qs.filter(status='issued').count()
            performance['tickets_voided'] = tickets_qs.filter(status='voided').count()
        
        if 'conversion' in metrics:
            total_searches = FlightSearch.objects.filter(
                user=user,
                created_at__date__range=[start_date, end_date]
            ).count()
            confirmed_bookings = bookings_qs.filter(status='confirmed').count()
            
            if total_searches > 0:
                performance['conversion_rate'] = (confirmed_bookings / total_searches) * 100
            else:
                performance['conversion_rate'] = Decimal('0.00')
        
        if 'ancillary' in metrics:
            ancillary_revenue = AncillaryBooking.objects.filter(
                booking__in=bookings_qs,
                status='confirmed'
            ).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
            performance['ancillary_revenue'] = ancillary_revenue
            performance['ancillary_per_booking'] = ancillary_revenue / performance.get('total_bookings', 1)
        
        return performance


# ==============================================
# WEBHOOK HANDLERS
# ==============================================

@method_decorator(csrf_exempt, name='dispatch')
class GDSWebhookView(View):
    """GDS Webhook Handler - Receive updates from Travelport GDS"""
    
    def post(self, request):
        try:
            # Verify webhook signature
            signature = request.headers.get('X-GDS-Signature', '')
            payload = request.body.decode('utf-8')
            
            if not self.verify_signature(signature, payload):
                return JsonResponse({'error': 'Invalid signature'}, status=401)
            
            # Parse payload
            data = json.loads(payload)
            event_type = data.get('event_type', '')
            
            # Log webhook
            APILogger.log_webhook(request, 'gds', event_type)
            
            # Process based on event type
            if event_type == 'booking_confirmed':
                self.handle_booking_confirmed(data)
            elif event_type == 'ticket_issued':
                self.handle_ticket_issued(data)
            elif event_type == 'booking_cancelled':
                self.handle_booking_cancelled(data)
            elif event_type == 'schedule_change':
                self.handle_schedule_change(data)
            elif event_type == 'fare_update':
                self.handle_fare_update(data)
            else:
                logger.warning(f"Unknown GDS webhook event: {event_type}")
            
            return JsonResponse({'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"GDS webhook error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def verify_signature(self, signature, payload):
        """Verify webhook signature"""
        # Implement signature verification based on GDS provider
        # This is a placeholder implementation
        secret = settings.GDS_WEBHOOK_SECRET
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def handle_booking_confirmed(self, data):
        """Handle booking confirmed webhook"""
        pnr = data.get('pnr', '')
        booking_reference = data.get('booking_reference', '')
        
        # Update booking status
        booking = Booking.objects.filter(
            Q(pnr=pnr) | Q(booking_reference=booking_reference)
        ).first()
        
        if booking:
            booking.status = 'confirmed'
            booking.confirmed_at = timezone.now()
            booking.save()
            
            # Send notification
            notification_service = APINotificationService()
            notification_service.send_booking_confirmed_notification(booking)
    
    def handle_ticket_issued(self, data):
        """Handle ticket issued webhook"""
        ticket_number = data.get('ticket_number', '')
        pnr = data.get('pnr', '')
        
        # Find booking by PNR
        booking = Booking.objects.filter(pnr=pnr).first()
        if booking:
            # Update ticket status
            ticket = Ticket.objects.filter(
                ticket_number=ticket_number,
                booking=booking
            ).first()
            
            if ticket:
                ticket.status = 'issued'
                ticket.issued_at = timezone.now()
                ticket.save()


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    """Payment Gateway Webhook Handler - Payment status updates"""
    
    def post(self, request):
        try:
            # Verify webhook signature
            signature = request.headers.get('X-Payment-Signature', '')
            payload = request.body.decode('utf-8')
            
            if not self.verify_payment_signature(signature, payload):
                return JsonResponse({'error': 'Invalid signature'}, status=401)
            
            # Parse payload
            data = json.loads(payload)
            event_type = data.get('event', '')
            payment_reference = data.get('payment_reference', '')
            
            # Log webhook
            APILogger.log_webhook(request, 'payment', event_type)
            
            # Find payment
            payment = Payment.objects.filter(payment_reference=payment_reference).first()
            if not payment:
                return JsonResponse({'error': 'Payment not found'}, status=404)
            
            # Process based on event type
            if event_type == 'payment.completed':
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.save()
                
                # Update booking payment status
                payment.booking.payment_status = 'paid'
                payment.booking.save()
                
                # Send notification
                notification_service = APINotificationService()
                notification_service.send_payment_completed_notification(payment)
            
            elif event_type == 'payment.failed':
                payment.status = 'failed'
                payment.failure_reason = data.get('failure_reason', '')
                payment.save()
            
            elif event_type == 'payment.refunded':
                payment.status = 'refunded'
                payment.save()
            
            return JsonResponse({'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Payment webhook error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def verify_payment_signature(self, signature, payload):
        """Verify payment webhook signature"""
        # Implement signature verification based on payment gateway
        # This is a placeholder implementation
        secret = settings.PAYMENT_WEBHOOK_SECRET
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


# ==============================================
# UTILITY API VIEWS
# ==============================================

class CurrencyRatesAPI(APIView):
    """Currency Exchange Rates API - Get current exchange rates"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess]
    
    def get(self, request):
        try:
            base_currency = request.GET.get('base', 'SAR')
            currencies = request.GET.getlist('currencies', ['USD', 'EUR', 'GBP', 'AED'])
            
            # Get cached rates
            cache_key = f'currency_rates_{base_currency}'
            rates = cache.get(cache_key)
            
            if not rates:
                # Fetch fresh rates from external API
                rates = self.fetch_currency_rates(base_currency, currencies)
                if rates:
                    # Cache for 1 hour
                    cache.set(cache_key, rates, 3600)
            
            return Response({
                'success': True,
                'base_currency': base_currency,
                'rates': rates,
                'last_updated': cache.get(f'{cache_key}_timestamp', timezone.now().isoformat()),
            })
            
        except Exception as e:
            logger.error(f"Currency rates API error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch currency rates'
            }, status=500)
    
    def fetch_currency_rates(self, base_currency, currencies):
        """Fetch currency rates from external API"""
        # This is a placeholder implementation
        # In production, integrate with a currency API like OpenExchangeRates
        try:
            # Mock rates for demonstration
            mock_rates = {
                'SAR': {'USD': 0.27, 'EUR': 0.25, 'GBP': 0.21, 'AED': 0.98},
                'USD': {'SAR': 3.75, 'EUR': 0.92, 'GBP': 0.79, 'AED': 3.67},
                'EUR': {'SAR': 4.07, 'USD': 1.09, 'GBP': 0.86, 'AED': 3.99},
                'GBP': {'SAR': 4.75, 'USD': 1.27, 'EUR': 1.16, 'AED': 4.66},
                'AED': {'SAR': 1.02, 'USD': 0.27, 'EUR': 0.25, 'GBP': 0.21},
            }
            
            if base_currency in mock_rates:
                return {
                    currency: rate 
                    for currency, rate in mock_rates[base_currency].items() 
                    if currency in currencies
                }
            
            return {}
        except Exception:
            return {}


# ==============================================
# BULK OPERATIONS API VIEWS
# ==============================================

class BulkBookingAPI(APIView):
    """Bulk Booking Operations API - Create multiple bookings"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsSuperAgent]
    
    def post(self, request):
        try:
            # Validate request
            validator = APIValidator()
            validation_result = validator.validate_bulk_booking_request(request.data)
            
            if not validation_result['valid']:
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation_result['errors']
                }, status=400)
            
            # Log API request
            APILogger.log_api_request(request, 'bulk_booking')
            
            # Initialize booking service
            booking_service = BookingService()
            
            # Process bulk bookings
            results = []
            for booking_data in request.data.get('bookings', []):
                try:
                    result = booking_service.create_booking(
                        booking_data=booking_data,
                        user=request.user,
                        bulk_mode=True
                    )
                    results.append({
                        'success': result['success'],
                        'booking_reference': result.get('booking', {}).booking_reference if result['success'] else None,
                        'error': result.get('error'),
                        'details': result.get('details', {})
                    })
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e)
                    })
            
            # Calculate summary
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful
            
            return Response({
                'success': True,
                'summary': {
                    'total': len(results),
                    'successful': successful,
                    'failed': failed
                },
                'results': results
            })
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Bulk booking API error: {str(e)}", exc_info=True)
            APILogger.log_api_error(request, 'bulk_booking', str(e))
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


# ==============================================
# API MONITORING AND ANALYTICS
# ==============================================

class APIUsageAPI(APIView):
    """API Usage Statistics - Admin only"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAdminUser]
    
    def get(self, request):
        try:
            # Get parameters
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            user_id = request.GET.get('user_id', '')
            endpoint = request.GET.get('endpoint', '')
            
            # Get usage statistics
            usage_stats = APIMonitoring.get_usage_statistics(
                start_date=start_date,
                end_date=end_date,
                user_id=user_id if user_id else None,
                endpoint=endpoint if endpoint else None
            )
            
            return Response({
                'success': True,
                'statistics': usage_stats,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            })
            
        except Exception as e:
            logger.error(f"API usage statistics error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch usage statistics'
            }, status=500)


class APIPerformanceAPI(APIView):
    """API Performance Metrics - Admin only"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasAPIAccess, IsAdminUser]
    
    def get(self, request):
        try:
            # Get performance metrics
            performance_metrics = APIMonitoring.get_performance_metrics()
            
            # Get system health
            system_health = APIMonitoring.get_system_health()
            
            # Get recent errors
            recent_errors = APIMonitoring.get_recent_errors(limit=50)
            
            return Response({
                'success': True,
                'performance': performance_metrics,
                'system_health': system_health,
                'recent_errors': recent_errors,
                'timestamp': timezone.now().isoformat(),
            })
            
        except Exception as e:
            logger.error(f"API performance metrics error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch performance metrics'
            }, status=500)


# ==============================================
# URL CONFIGURATION FOR API ENDPOINTS
# ==============================================

"""
Add this to your flights/urls.py:

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import *

router = DefaultRouter()

urlpatterns = [
    # Authentication
    path('auth/login/', APILoginView.as_view(), name='api_login'),
    path('auth/logout/', APILogoutView.as_view(), name='api_logout'),
    path('status/', APIStatusView.as_view(), name='api_status'),
    
    # Flight Search
    path('flights/search/', FlightSearchAPI.as_view(), name='flight_search_api'),
    path('flights/availability/', FlightAvailabilityAPI.as_view(), name='flight_availability_api'),
    path('flights/fare-calendar/', FareCalendarAPI.as_view(), name='fare_calendar_api'),
    path('flights/low-fare-search/', LowFareSearchAPI.as_view(), name='low_fare_search_api'),
    path('flights/schedule-search/', ScheduleSearchAPI.as_view(), name='schedule_search_api'),
    
    # Booking
    path('bookings/', BookingListAPI.as_view(), name='booking_list_api'),
    path('bookings/<uuid:id>/', BookingDetailAPI.as_view(), name='booking_detail_api'),
    path('bookings/<uuid:booking_id>/confirm/', BookingConfirmAPI.as_view(), name='booking_confirm_api'),
    path('bookings/retrieve/', BookingRetrieveAPI.as_view(), name='booking_retrieve_api'),
    path('bookings/price/', BookingPriceAPI.as_view(), name='booking_price_api'),
    
    # Ticketing
    path('tickets/', TicketListAPI.as_view(), name='ticket_list_api'),
    path('tickets/<uuid:id>/', TicketDetailAPI.as_view(), name='ticket_detail_api'),
    path('tickets/<uuid:ticket_id>/void/', TicketVoidAPI.as_view(), name='ticket_void_api'),
    path('tickets/<uuid:ticket_id>/reissue/', TicketReissueAPI.as_view(), name='ticket_reissue_api'),
    path('emds/issue/', EMDIssueAPI.as_view(), name='emd_issue_api'),
    
    # Payment
    path('bookings/<uuid:booking_id>/payment/', PaymentProcessAPI.as_view(), name='payment_process_api'),
    path('payments/', PaymentListAPI.as_view(), name='payment_list_api'),
    path('bookings/<uuid:booking_id>/refund/', RefundRequestAPI.as_view(), name='refund_request_api'),
    
    # Ancillary Services
    path('ancillary/', AncillaryServiceListAPI.as_view(), name='ancillary_list_api'),
    path('ancillary/book/', AncillaryBookingAPI.as_view(), name='ancillary_booking_api'),
    path('seat-map/', SeatMapAPI.as_view(), name='seat_map_api'),
    
    # Reference Data
    path('airlines/', AirlineListAPI.as_view(), name='airline_list_api'),
    path('airports/', AirportListAPI.as_view(), name='airport_list_api'),
    path('airports/autocomplete/', AirportAutocompleteAPI.as_view(), name='airport_autocomplete_api'),
    path('countries/', CountryListAPI.as_view(), name='country_list_api'),
    
    # Reports
    path('reports/sales/', SalesReportAPI.as_view(), name='sales_report_api'),
    path('reports/performance/', PerformanceReportAPI.as_view(), name='performance_report_api'),
    
    # Utility
    path('currency-rates/', CurrencyRatesAPI.as_view(), name='currency_rates_api'),
    
    # Bulk Operations
    path('bulk/bookings/', BulkBookingAPI.as_view(), name='bulk_booking_api'),
    
    # Monitoring (Admin Only)
    path('monitoring/usage/', APIUsageAPI.as_view(), name='api_usage_api'),
    path('monitoring/performance/', APIPerformanceAPI.as_view(), name='api_performance_api'),
    
    # Webhooks
    path('webhooks/gds/', GDSWebhookView.as_view(), name='gds_webhook'),
    path('webhooks/payment/', PaymentWebhookView.as_view(), name='payment_webhook'),
]
"""