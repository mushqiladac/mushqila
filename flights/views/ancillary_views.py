# flights/views/ancillary_views.py
"""
Ancillary Services Views for B2B Travel Platform
Production Ready - Final Version
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F, Prefetch, Subquery, OuterRef
from django.db.models.functions import Coalesce, TruncDate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, connection
from django.core.cache import cache
from django.urls import reverse
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
import csv
import xlwt
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Optional imports for models
try:
    from flights.models import (
        AncillaryService, AncillaryBooking, BaggageService, MealPreference,
        LoungeAccess, TravelInsurance, SeatSelection, SpecialAssistance,
        Booking, Passenger, FlightSegment, FlightItinerary,
        Airline, Airport, ServiceCategory, ServiceBundle
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

# Optional imports for forms
try:
    from flights.forms import (
        AncillaryServiceForm, AncillarySearchForm, AncillaryBookingForm,
        BaggageServiceForm, MealPreferenceForm, LoungeAccessForm,
        TravelInsuranceForm, SpecialAssistanceForm, ServiceBundleForm,
        BulkAncillaryForm, AncillaryFilterForm
    )
    FORMS_AVAILABLE = True
except ImportError:
    FORMS_AVAILABLE = False

# Optional imports for services
try:
    from flights.services.ancillary_service import AncillaryServiceManager
except ImportError:
    AncillaryServiceManager = None

try:
    from flights.services.booking_service import BookingService
except ImportError:
    BookingService = None

try:
    from flights.services.payment_service import PaymentService
except ImportError:
    PaymentService = None

try:
    from flights.services.gds_service import GDSAncillaryService
except ImportError:
    GDSAncillaryService = None

try:
    from flights.services.integration_service import AncillaryIntegrationService
except ImportError:
    AncillaryIntegrationService = None

try:
    from flights.utils.export import AncillaryExport
except ImportError:
    AncillaryExport = None

try:
    from flights.utils.permissions import AncillaryPermission
except ImportError:
    AncillaryPermission = None

try:
    from flights.utils.validators import AncillaryValidator
except ImportError:
    AncillaryValidator = None

try:
    from flights.utils.cache import AncillaryCache
except ImportError:
    AncillaryCache = None

logger = logging.getLogger(__name__)


class AncillaryServicesListView(LoginRequiredMixin, View):
    """List all ancillary services with filtering and search"""
    
    template_name = 'flights/ancillary/ancillary_services_list.html'
    items_per_page = 25
    
    def get(self, request):
        try:
            # Get filter parameters
            service_type = request.GET.get('type', 'all')
            airline_filter = request.GET.get('airline', 'all')
            category_filter = request.GET.get('category', 'all')
            status_filter = request.GET.get('status', 'active')
            search_query = request.GET.get('q', '').strip()
            sort_by = request.GET.get('sort', '-created_at')
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            services = AncillaryService.objects.select_related(
                'airline',
                'category'
            ).prefetch_related(
                'applicable_classes',
                'included_services'
            )
            
            # Apply service type filter
            if service_type != 'all':
                service_type_map = {
                    'baggage': 'baggage',
                    'meal': 'meal',
                    'lounge': 'lounge',
                    'insurance': 'insurance',
                    'seat': 'seat',
                    'assistance': 'assistance',
                    'bundle': 'bundle',
                }
                if service_type in service_type_map:
                    services = services.filter(service_type=service_type_map[service_type])
            
            # Apply airline filter
            if airline_filter != 'all':
                services = services.filter(airline__code=airline_filter)
            
            # Apply category filter
            if category_filter != 'all':
                services = services.filter(category__slug=category_filter)
            
            # Apply status filter
            if status_filter == 'active':
                services = services.filter(is_active=True)
            elif status_filter == 'inactive':
                services = services.filter(is_active=False)
            
            # Apply search
            if search_query:
                services = services.filter(
                    Q(name__icontains=search_query) |
                    Q(name_ar__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(description_ar__icontains=search_query) |
                    Q(code__icontains=search_query) |
                    Q(airline__name__icontains=search_query) |
                    Q(category__name__icontains=search_query)
                )
            
            # Apply sorting
            valid_sort_fields = [
                'name', '-name',
                'created_at', '-created_at',
                'updated_at', '-updated_at',
                'price', '-price',
                'airline__name', '-airline__name',
                'popularity', '-popularity'
            ]
            if sort_by in valid_sort_fields:
                services = services.order_by(sort_by)
            else:
                services = services.order_by('-created_at')
            
            # Get statistics
            stats = self.get_ancillary_statistics(services)
            
            # Pagination
            paginator = Paginator(services, self.items_per_page)
            page_obj = paginator.get_page(page_number)
            
            # Get filter options
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            categories = ServiceCategory.objects.filter(is_active=True).order_by('name')
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'categories': categories,
                'service_type': service_type,
                'airline_filter': airline_filter,
                'category_filter': category_filter,
                'status_filter': status_filter,
                'search_query': search_query,
                'sort_by': sort_by,
                'stats': stats,
                'service_types': [
                    ('all', 'All Services'),
                    ('baggage', 'Baggage Services'),
                    ('meal', 'Meal Services'),
                    ('lounge', 'Lounge Access'),
                    ('insurance', 'Travel Insurance'),
                    ('seat', 'Seat Selection'),
                    ('assistance', 'Special Assistance'),
                    ('bundle', 'Service Bundles'),
                ],
                'status_options': [
                    ('active', 'Active Only'),
                    ('inactive', 'Inactive Only'),
                    ('all', 'All Status'),
                ],
                'sort_options': [
                    ('-created_at', 'Newest First'),
                    ('created_at', 'Oldest First'),
                    ('-updated_at', 'Recently Updated'),
                    ('updated_at', 'Least Recently Updated'),
                    ('name', 'Name (A-Z)'),
                    ('-name', 'Name (Z-A)'),
                    ('price', 'Price (Low-High)'),
                    ('-price', 'Price (High-Low)'),
                    ('airline__name', 'Airline (A-Z)'),
                    ('-airline__name', 'Airline (Z-A)'),
                    ('-popularity', 'Most Popular'),
                    ('popularity', 'Least Popular'),
                ],
                'can_create': AncillaryPermission.can_create_service(request.user),
                'can_edit': AncillaryPermission.can_edit_service(request.user),
                'can_delete': AncillaryPermission.can_delete_service(request.user),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ancillary services list: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading ancillary services. Please try again.')
            return render(request, self.template_name, {'page_obj': []})
    
    def get_ancillary_statistics(self, services):
        """Calculate ancillary services statistics"""
        stats = {
            'total_services': services.count(),
            'active_services': services.filter(is_active=True).count(),
            'total_categories': ServiceCategory.objects.filter(is_active=True).count(),
            'total_airlines': Airline.objects.filter(
                ancillary_services__isnull=False
            ).distinct().count(),
            'total_revenue': AncillaryBooking.objects.filter(
                status='confirmed'
            ).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00'),
            'average_price': services.filter(
                is_active=True
            ).aggregate(avg=Avg('price'))['avg'] or Decimal('0.00'),
        }
        
        # Service type breakdown
        type_stats = services.values('service_type').annotate(
            count=Count('id'),
            revenue=Sum('price')
        ).order_by('-count')
        
        stats['type_breakdown'] = type_stats
        
        # Top selling services
        top_services = AncillaryBooking.objects.filter(
            status='confirmed',
            created_at__date__gte=timezone.now().date() - timedelta(days=30)
        ).values(
            'service__name',
            'service__service_type',
            'service__airline__code'
        ).annotate(
            sales_count=Count('id'),
            total_revenue=Sum('total_price')
        ).order_by('-sales_count')[:10]
        
        stats['top_services'] = top_services
        
        return stats


class AncillaryServiceDetailView(LoginRequiredMixin, View):
    """View detailed ancillary service information"""
    
    template_name = 'flights/ancillary/ancillary_service_detail.html'
    
    def get(self, request, service_id):
        try:
            # Get service with all related data
            service = get_object_or_404(
                AncillaryService.objects.select_related(
                    'airline',
                    'category'
                ).prefetch_related(
                    'applicable_classes',
                    'included_services',
                    'related_services',
                    'exclusions',
                    'prerequisites'
                ),
                id=service_id
            )
            
            # Get ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Get availability information
            availability = ancillary_manager.get_service_availability(service)
            
            # Get pricing information
            pricing_info = ancillary_manager.get_service_pricing(service)
            
            # Get similar services
            similar_services = AncillaryService.objects.filter(
                Q(service_type=service.service_type) |
                Q(category=service.category) |
                Q(airline=service.airline)
            ).exclude(id=service.id).select_related('airline', 'category')[:6]
            
            # Get recent bookings
            recent_bookings = AncillaryBooking.objects.filter(
                service=service,
                status='confirmed'
            ).select_related('booking', 'passenger')[:10]
            
            # Get service restrictions
            restrictions = ancillary_manager.get_service_restrictions(service)
            
            context = {
                'service': service,
                'availability': availability,
                'pricing_info': pricing_info,
                'similar_services': similar_services,
                'recent_bookings': recent_bookings,
                'restrictions': restrictions,
                'can_book': AncillaryPermission.can_book_service(request.user, service),
                'can_edit': AncillaryPermission.can_edit_service(request.user, service),
                'can_delete': AncillaryPermission.can_delete_service(request.user, service),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ancillary service detail {service_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading service details: {str(e)}')
            return redirect('flights:ancillary_services_list')


class AncillaryServiceCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Create new ancillary service"""
    
    template_name = 'flights/ancillary/ancillary_service_create.html'
    
    def test_func(self):
        return AncillaryPermission.can_create_service(self.request.user)
    
    def get(self, request):
        try:
            form = AncillaryServiceForm()
            
            # Get available categories and airlines
            categories = ServiceCategory.objects.filter(is_active=True)
            airlines = Airline.objects.filter(is_active=True)
            
            context = {
                'form': form,
                'categories': categories,
                'airlines': airlines,
                'service_types': [
                    ('baggage', 'Baggage Service'),
                    ('meal', 'Meal Service'),
                    ('lounge', 'Lounge Access'),
                    ('insurance', 'Travel Insurance'),
                    ('seat', 'Seat Selection'),
                    ('assistance', 'Special Assistance'),
                    ('bundle', 'Service Bundle'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ancillary service create form: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading service creation form.')
            return redirect('flights:ancillary_services_list')
    
    def post(self, request):
        try:
            form = AncillaryServiceForm(request.POST, request.FILES)
            
            if form.is_valid():
                # Save service
                service = form.save(commit=False)
                service.created_by = request.user
                
                # Set service code if not provided
                if not service.code:
                    service.code = self.generate_service_code(service)
                
                # Save service
                service.save()
                
                # Save many-to-many relationships
                form.save_m2m()
                
                # Log creation
                logger.info(f"Ancillary service created: {service.code} by {request.user.email}")
                
                messages.success(request, f'Service "{service.name}" created successfully.')
                return redirect('flights:ancillary_service_detail', service_id=service.id)
            
            # Form validation failed
            categories = ServiceCategory.objects.filter(is_active=True)
            airlines = Airline.objects.filter(is_active=True)
            
            context = {
                'form': form,
                'categories': categories,
                'airlines': airlines,
                'service_types': [
                    ('baggage', 'Baggage Service'),
                    ('meal', 'Meal Service'),
                    ('lounge', 'Lounge Access'),
                    ('insurance', 'Travel Insurance'),
                    ('seat', 'Seat Selection'),
                    ('assistance', 'Special Assistance'),
                    ('bundle', 'Service Bundle'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error creating ancillary service: {str(e)}", exc_info=True)
            messages.error(request, f'Error creating service: {str(e)}')
            
            # Re-render form with data
            categories = ServiceCategory.objects.filter(is_active=True)
            airlines = Airline.objects.filter(is_active=True)
            
            context = {
                'form': AncillaryServiceForm(request.POST, request.FILES),
                'categories': categories,
                'airlines': airlines,
                'service_types': [
                    ('baggage', 'Baggage Service'),
                    ('meal', 'Meal Service'),
                    ('lounge', 'Lounge Access'),
                    ('insurance', 'Travel Insurance'),
                    ('seat', 'Seat Selection'),
                    ('assistance', 'Special Assistance'),
                    ('bundle', 'Service Bundle'),
                ],
            }
            
            return render(request, self.template_name, context)
    
    def generate_service_code(self, service):
        """Generate unique service code"""
        base_code = f"{service.airline.code}_{service.service_type.upper()}"
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join([str(i) for i in range(4)])
        return f"{base_code}_{timestamp}_{random_str}"


class AncillaryServiceEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Edit existing ancillary service"""
    
    template_name = 'flights/ancillary/ancillary_service_edit.html'
    
    def test_func(self):
        service_id = self.kwargs.get('service_id')
        if service_id:
            service = get_object_or_404(AncillaryService, id=service_id)
            return AncillaryPermission.can_edit_service(self.request.user, service)
        return False
    
    def get(self, request, service_id):
        try:
            service = get_object_or_404(AncillaryService, id=service_id)
            form = AncillaryServiceForm(instance=service)
            
            # Get available categories and airlines
            categories = ServiceCategory.objects.filter(is_active=True)
            airlines = Airline.objects.filter(is_active=True)
            
            context = {
                'form': form,
                'service': service,
                'categories': categories,
                'airlines': airlines,
                'service_types': [
                    ('baggage', 'Baggage Service'),
                    ('meal', 'Meal Service'),
                    ('lounge', 'Lounge Access'),
                    ('insurance', 'Travel Insurance'),
                    ('seat', 'Seat Selection'),
                    ('assistance', 'Special Assistance'),
                    ('bundle', 'Service Bundle'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ancillary service edit form {service_id}: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading service edit form.')
            return redirect('flights:ancillary_service_detail', service_id=service_id)
    
    def post(self, request, service_id):
        try:
            service = get_object_or_404(AncillaryService, id=service_id)
            form = AncillaryServiceForm(request.POST, request.FILES, instance=service)
            
            if form.is_valid():
                # Update service
                updated_service = form.save(commit=False)
                updated_service.updated_by = request.user
                updated_service.updated_at = timezone.now()
                updated_service.save()
                
                # Save many-to-many relationships
                form.save_m2m()
                
                # Log update
                logger.info(f"Ancillary service updated: {service.code} by {request.user.email}")
                
                messages.success(request, f'Service "{updated_service.name}" updated successfully.')
                return redirect('flights:ancillary_service_detail', service_id=updated_service.id)
            
            # Form validation failed
            categories = ServiceCategory.objects.filter(is_active=True)
            airlines = Airline.objects.filter(is_active=True)
            
            context = {
                'form': form,
                'service': service,
                'categories': categories,
                'airlines': airlines,
                'service_types': [
                    ('baggage', 'Baggage Service'),
                    ('meal', 'Meal Service'),
                    ('lounge', 'Lounge Access'),
                    ('insurance', 'Travel Insurance'),
                    ('seat', 'Seat Selection'),
                    ('assistance', 'Special Assistance'),
                    ('bundle', 'Service Bundle'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error updating ancillary service {service_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error updating service: {str(e)}')
            return redirect('flights:ancillary_service_detail', service_id=service_id)


class AncillaryBookingView(LoginRequiredMixin, View):
    """Book ancillary services for passengers"""
    
    template_name = 'flights/ancillary/ancillary_booking.html'
    
    def get(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(
                Booking.objects.select_related(
                    'itinerary',
                    'itinerary__search'
                ).prefetch_related(
                    Prefetch('passengers', queryset=Passenger.objects.all()),
                    Prefetch('ancillarybookings', queryset=AncillaryBooking.objects.select_related('service')),
                ),
                id=booking_id
            )
            
            # Check permission
            if not AncillaryPermission.can_book_for_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to book ancillary services for this booking")
            
            # Get ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Get available services for this booking
            available_services = ancillary_manager.get_available_services_for_booking(booking)
            
            # Group services by type
            services_by_type = {}
            for service_type, services in available_services.items():
                services_by_type[service_type] = services
            
            # Get existing ancillary bookings
            existing_bookings = AncillaryBooking.objects.filter(
                booking=booking,
                status__in=['pending', 'confirmed']
            ).select_related('service', 'passenger', 'segment')
            
            # Calculate totals
            total_price = existing_bookings.filter(status='confirmed').aggregate(
                total=Sum('total_price')
            )['total'] or Decimal('0.00')
            
            # Get form
            form = AncillaryBookingForm(booking=booking)
            
            context = {
                'booking': booking,
                'services_by_type': services_by_type,
                'existing_bookings': existing_bookings,
                'total_price': total_price,
                'form': form,
                'service_types': [
                    ('baggage', 'Baggage'),
                    ('meal', 'Meals'),
                    ('lounge', 'Lounge'),
                    ('insurance', 'Insurance'),
                    ('seat', 'Seats'),
                    ('assistance', 'Assistance'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for ancillary booking {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error loading ancillary booking {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading ancillary booking: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)
    
    @method_decorator(csrf_exempt)
    def post(self, request, booking_id):
        try:
            data = json.loads(request.body)
            service_requests = data.get('service_requests', [])
            
            if not service_requests:
                return JsonResponse({
                    'success': False,
                    'error': 'No service requests provided'
                })
            
            # Get booking
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check permission
            if not AncillaryPermission.can_book_for_booking(request.user, booking):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Process service requests
            result = ancillary_manager.process_service_requests(
                booking=booking,
                service_requests=service_requests,
                user=request.user
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Ancillary services booked successfully',
                    'bookings': result.get('bookings', []),
                    'total_price': result.get('total_price', 0),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to book services'),
                    'details': result.get('details', {}),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error processing ancillary booking {booking_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class BaggageServicesView(LoginRequiredMixin, View):
    """Manage baggage services"""
    
    template_name = 'flights/ancillary/baggage_services.html'
    
    def get(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(
                Booking.objects.select_related('itinerary').prefetch_related('passengers'),
                id=booking_id
            )
            
            # Check permission
            if not AncillaryPermission.can_book_for_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to book baggage services for this booking")
            
            # Get baggage service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Get available baggage services
            baggage_services = ancillary_manager.get_baggage_services_for_booking(booking)
            
            # Get existing baggage bookings
            existing_baggage = AncillaryBooking.objects.filter(
                booking=booking,
                service__service_type='baggage',
                status__in=['pending', 'confirmed']
            ).select_related('service', 'passenger')
            
            # Get segments
            segments = booking.itinerary.segments.all().order_by('departure_time')
            
            # Get form
            form = BaggageServiceForm(booking=booking)
            
            context = {
                'booking': booking,
                'baggage_services': baggage_services,
                'existing_baggage': existing_baggage,
                'segments': segments,
                'form': form,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for baggage services {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error loading baggage services {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading baggage services: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)


class MealServicesView(LoginRequiredMixin, View):
    """Manage meal services"""
    
    template_name = 'flights/ancillary/meal_services.html'
    
    def get(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(
                Booking.objects.select_related('itinerary').prefetch_related('passengers'),
                id=booking_id
            )
            
            # Check permission
            if not AncillaryPermission.can_book_for_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to book meal services for this booking")
            
            # Get meal service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Get available meal services
            meal_services = ancillary_manager.get_meal_services_for_booking(booking)
            
            # Get existing meal bookings
            existing_meals = AncillaryBooking.objects.filter(
                booking=booking,
                service__service_type='meal',
                status__in=['pending', 'confirmed']
            ).select_related('service', 'passenger', 'segment')
            
            # Get segments
            segments = booking.itinerary.segments.all().order_by('departure_time')
            
            # Get form
            form = MealPreferenceForm(booking=booking)
            
            context = {
                'booking': booking,
                'meal_services': meal_services,
                'existing_meals': existing_meals,
                'segments': segments,
                'form': form,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for meal services {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error loading meal services {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading meal services: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)


class LoungeAccessView(LoginRequiredMixin, View):
    """Manage lounge access services"""
    
    template_name = 'flights/ancillary/lounge_access.html'
    
    def get(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(
                Booking.objects.select_related('itinerary').prefetch_related('passengers'),
                id=booking_id
            )
            
            # Check permission
            if not AncillaryPermission.can_book_for_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to book lounge access for this booking")
            
            # Get lounge service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Get available lounge services
            lounge_services = ancillary_manager.get_lounge_services_for_booking(booking)
            
            # Get existing lounge bookings
            existing_lounge = AncillaryBooking.objects.filter(
                booking=booking,
                service__service_type='lounge',
                status__in=['pending', 'confirmed']
            ).select_related('service', 'passenger')
            
            # Get airports
            airports = Airport.objects.filter(
                Q(iata_code=booking.itinerary.search.origin.iata_code) |
                Q(iata_code=booking.itinerary.search.destination.iata_code)
            ).distinct()
            
            # Get form
            form = LoungeAccessForm(booking=booking)
            
            context = {
                'booking': booking,
                'lounge_services': lounge_services,
                'existing_lounge': existing_lounge,
                'airports': airports,
                'form': form,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for lounge access {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error loading lounge access {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading lounge access: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)


class TravelInsuranceView(LoginRequiredMixin, View):
    """Manage travel insurance services"""
    
    template_name = 'flights/ancillary/travel_insurance.html'
    
    def get(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(
                Booking.objects.select_related('itinerary').prefetch_related('passengers'),
                id=booking_id
            )
            
            # Check permission
            if not AncillaryPermission.can_book_for_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to book travel insurance for this booking")
            
            # Get insurance service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Get available insurance services
            insurance_services = ancillary_manager.get_insurance_services_for_booking(booking)
            
            # Get existing insurance bookings
            existing_insurance = AncillaryBooking.objects.filter(
                booking=booking,
                service__service_type='insurance',
                status__in=['pending', 'confirmed']
            ).select_related('service', 'passenger')
            
            # Calculate coverage needs
            coverage_needs = self.calculate_coverage_needs(booking)
            
            # Get form
            form = TravelInsuranceForm(booking=booking)
            
            context = {
                'booking': booking,
                'insurance_services': insurance_services,
                'existing_insurance': existing_insurance,
                'coverage_needs': coverage_needs,
                'form': form,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for travel insurance {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error loading travel insurance {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading travel insurance: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)
    
    def calculate_coverage_needs(self, booking):
        """Calculate insurance coverage needs"""
        # Basic coverage calculation based on booking details
        total_fare = booking.total_amount
        trip_duration = 0
        
        if booking.itinerary.search.return_date:
            departure = booking.itinerary.search.departure_date
            return_date = booking.itinerary.search.return_date
            trip_duration = (return_date - departure).days
        
        coverage_needs = {
            'trip_cancellation': total_fare * Decimal('1.1'),  # 110% of fare
            'trip_interruption': total_fare * Decimal('1.5'),  # 150% of fare
            'medical_evacuation': Decimal('100000'),  # $100,000
            'medical_expenses': Decimal('50000'),     # $50,000
            'baggage_loss': Decimal('3000'),          # $3,000
            'baggage_delay': Decimal('500'),          # $500
            'trip_delay': Decimal('1000'),            # $1,000
            'recommended_coverage': {
                'basic': total_fare * Decimal('0.05'),
                'standard': total_fare * Decimal('0.08'),
                'premium': total_fare * Decimal('0.12'),
            }
        }
        
        # Adjust based on trip duration
        if trip_duration > 7:
            coverage_needs['medical_expenses'] = Decimal('100000')
            coverage_needs['medical_evacuation'] = Decimal('250000')
        
        return coverage_needs


class ServiceBundlesView(LoginRequiredMixin, View):
    """View and book service bundles"""
    
    template_name = 'flights/ancillary/service_bundles.html'
    
    def get(self, request):
        try:
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            bundle_type = request.GET.get('type', 'all')
            search_query = request.GET.get('q', '').strip()
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            bundles = ServiceBundle.objects.select_related(
                'airline',
                'category'
            ).prefetch_related(
                'included_services',
                'applicable_classes'
            ).filter(is_active=True)
            
            # Apply filters
            if airline_filter != 'all':
                bundles = bundles.filter(airline__code=airline_filter)
            
            if bundle_type != 'all':
                bundles = bundles.filter(bundle_type=bundle_type)
            
            if search_query:
                bundles = bundles.filter(
                    Q(name__icontains=search_query) |
                    Q(name_ar__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(description_ar__icontains=search_query) |
                    Q(code__icontains=search_query)
                )
            
            # Order by popularity
            bundles = bundles.order_by('-popularity', 'price')
            
            # Get bundle savings
            for bundle in bundles:
                bundle.total_individual_price = sum(
                    service.price for service in bundle.included_services.all() if service.is_active
                )
                if bundle.total_individual_price > 0:
                    bundle.savings_percentage = (
                        (bundle.total_individual_price - bundle.price) / bundle.total_individual_price * 100
                    )
                else:
                    bundle.savings_percentage = 0
            
            # Pagination
            paginator = Paginator(bundles, 12)
            page_obj = paginator.get_page(page_number)
            
            # Get airlines for filter
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'airline_filter': airline_filter,
                'bundle_type': bundle_type,
                'search_query': search_query,
                'bundle_types': [
                    ('all', 'All Bundles'),
                    ('economy', 'Economy Class'),
                    ('premium', 'Premium Economy'),
                    ('business', 'Business Class'),
                    ('first', 'First Class'),
                    ('family', 'Family'),
                    ('corporate', 'Corporate'),
                    ('frequent', 'Frequent Flyer'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading service bundles: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading service bundles.')
            return render(request, self.template_name, {'page_obj': []})


class AncillaryBookingManagementView(LoginRequiredMixin, View):
    """Manage ancillary bookings"""
    
    template_name = 'flights/ancillary/ancillary_booking_management.html'
    
    def get(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(
                Booking.objects.select_related('itinerary').prefetch_related(
                    Prefetch('ancillarybookings', queryset=AncillaryBooking.objects.select_related(
                        'service', 'passenger', 'segment'
                    ))
                ),
                id=booking_id
            )
            
            # Check permission
            if not AncillaryPermission.can_manage_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to manage ancillary services for this booking")
            
            # Get ancillary bookings
            ancillary_bookings = booking.ancillarybookings.all()
            
            # Group by service type
            bookings_by_type = {}
            for ab in ancillary_bookings:
                service_type = ab.service.service_type if ab.service else 'unknown'
                if service_type not in bookings_by_type:
                    bookings_by_type[service_type] = []
                bookings_by_type[service_type].append(ab)
            
            # Calculate totals
            totals = {
                'total_price': ancillary_bookings.filter(status='confirmed').aggregate(
                    total=Sum('total_price')
                )['total'] or Decimal('0.00'),
                'pending_price': ancillary_bookings.filter(status='pending').aggregate(
                    total=Sum('total_price')
                )['total'] or Decimal('0.00'),
                'cancelled_price': ancillary_bookings.filter(status='cancelled').aggregate(
                    total=Sum('total_price')
                )['total'] or Decimal('0.00'),
                'total_count': ancillary_bookings.count(),
            }
            
            # Get available actions for each booking
            available_actions = {}
            for ab in ancillary_bookings:
                available_actions[ab.id] = self.get_available_actions(ab, request.user)
            
            context = {
                'booking': booking,
                'bookings_by_type': bookings_by_type,
                'totals': totals,
                'available_actions': available_actions,
                'can_modify': AncillaryPermission.can_modify_booking(request.user, booking),
                'can_cancel': AncillaryPermission.can_cancel_booking(request.user, booking),
                'can_refund': AncillaryPermission.can_request_refund(request.user, booking),
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for ancillary management {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error loading ancillary management {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading ancillary management: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)
    
    def get_available_actions(self, ancillary_booking, user):
        """Get available actions for ancillary booking"""
        actions = []
        
        if AncillaryPermission.can_modify_booking(user, ancillary_booking.booking):
            if ancillary_booking.status in ['pending', 'confirmed']:
                actions.append('modify')
        
        if AncillaryPermission.can_cancel_booking(user, ancillary_booking.booking):
            if ancillary_booking.status in ['pending', 'confirmed']:
                actions.append('cancel')
        
        if AncillaryPermission.can_request_refund(user, ancillary_booking.booking):
            if ancillary_booking.status == 'confirmed':
                actions.append('refund')
        
        return actions


class AncillaryReportsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Generate ancillary services reports"""
    
    template_name = 'flights/ancillary/ancillary_reports.html'
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'super_agent']
    
    def get(self, request):
        try:
            # Get report parameters
            report_type = request.GET.get('type', 'sales')
            airline_filter = request.GET.get('airline', 'all')
            service_type_filter = request.GET.get('service_type', 'all')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Initialize ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Generate report based on type
            if report_type == 'sales':
                report_data = ancillary_manager.generate_sales_report(
                    airline_code=airline_filter if airline_filter != 'all' else None,
                    service_type=service_type_filter if service_type_filter != 'all' else None,
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == 'revenue':
                report_data = ancillary_manager.generate_revenue_report(
                    airline_code=airline_filter if airline_filter != 'all' else None,
                    service_type=service_type_filter if service_type_filter != 'all' else None,
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == 'popularity':
                report_data = ancillary_manager.generate_popularity_report(
                    airline_code=airline_filter if airline_filter != 'all' else None,
                    service_type=service_type_filter if service_type_filter != 'all' else None,
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == 'agent_performance':
                report_data = ancillary_manager.generate_agent_performance_report(
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                report_data = {'error': 'Invalid report type'}
            
            # Get airlines for filter
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            context = {
                'report_type': report_type,
                'report_data': report_data,
                'airlines': airlines,
                'airline_filter': airline_filter,
                'service_type_filter': service_type_filter,
                'start_date': start_date,
                'end_date': end_date,
                'report_types': [
                    ('sales', 'Sales Report'),
                    ('revenue', 'Revenue Report'),
                    ('popularity', 'Popularity Report'),
                    ('agent_performance', 'Agent Performance'),
                ],
                'service_types': [
                    ('all', 'All Services'),
                    ('baggage', 'Baggage'),
                    ('meal', 'Meals'),
                    ('lounge', 'Lounge'),
                    ('insurance', 'Insurance'),
                    ('seat', 'Seats'),
                    ('assistance', 'Assistance'),
                    ('bundle', 'Bundles'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error generating ancillary report: {str(e)}", exc_info=True)
            messages.error(request, f'Error generating report: {str(e)}')
            return render(request, self.template_name)


class AncillaryExportView(LoginRequiredMixin, View):
    """Export ancillary data"""
    
    def get(self, request):
        try:
            export_format = request.GET.get('format', 'excel')
            export_type = request.GET.get('type', 'services')
            
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            service_type_filter = request.GET.get('service_type', 'all')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Build queryset based on export type
            if export_type == 'services':
                queryset = AncillaryService.objects.select_related('airline', 'category')
                
                # Apply filters
                if airline_filter != 'all':
                    queryset = queryset.filter(airline__code=airline_filter)
                
                if service_type_filter != 'all':
                    queryset = queryset.filter(service_type=service_type_filter)
                
                queryset = queryset.order_by('airline__code', 'service_type', 'name')
            
            elif export_type == 'bookings':
                queryset = AncillaryBooking.objects.select_related(
                    'service',
                    'booking',
                    'passenger',
                    'segment'
                )
                
                # Apply filters
                if airline_filter != 'all':
                    queryset = queryset.filter(service__airline__code=airline_filter)
                
                if service_type_filter != 'all':
                    queryset = queryset.filter(service__service_type=service_type_filter)
                
                if start_date and end_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        queryset = queryset.filter(
                            created_at__date__gte=start_dt.date(),
                            created_at__date__lte=end_dt.date()
                        )
                    except ValueError:
                        pass
                
                # Apply user permissions
                if request.user.user_type == 'agent':
                    queryset = queryset.filter(booking__agent=request.user)
                elif request.user.user_type == 'sub_agent':
                    parent_agent = request.user.parent_agent
                    if parent_agent:
                        queryset = queryset.filter(booking__agent=parent_agent)
                
                queryset = queryset.order_by('-created_at')
            
            elif export_type == 'revenue':
                queryset = AncillaryBooking.objects.filter(
                    status='confirmed'
                ).select_related('service', 'booking')
                
                # Apply filters
                if airline_filter != 'all':
                    queryset = queryset.filter(service__airline__code=airline_filter)
                
                if service_type_filter != 'all':
                    queryset = queryset.filter(service__service_type=service_type_filter)
                
                if start_date and end_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        queryset = queryset.filter(
                            created_at__date__gte=start_dt.date(),
                            created_at__date__lte=end_dt.date()
                        )
                    except ValueError:
                        pass
                
                # Apply user permissions
                if request.user.user_type == 'agent':
                    queryset = queryset.filter(booking__agent=request.user)
                elif request.user.user_type == 'sub_agent':
                    parent_agent = request.user.parent_agent
                    if parent_agent:
                        queryset = queryset.filter(booking__agent=parent_agent)
                
                queryset = queryset.order_by('-created_at')
            
            else:
                messages.error(request, 'Invalid export type.')
                return redirect('flights:ancillary_services_list')
            
            # Export based on format
            export_utils = AncillaryExport()
            
            if export_format == 'excel':
                return export_utils.export_to_excel(queryset, export_type)
            elif export_format == 'csv':
                return export_utils.export_to_csv(queryset, export_type)
            elif export_format == 'pdf':
                return export_utils.export_to_pdf(queryset, export_type)
            else:
                messages.error(request, 'Invalid export format.')
                return redirect('flights:ancillary_services_list')
                
        except Exception as e:
            logger.error(f"Error exporting ancillary data: {str(e)}", exc_info=True)
            messages.error(request, 'Error exporting ancillary data.')
            return redirect('flights:ancillary_services_list')


# API Views for AJAX operations

@method_decorator(csrf_exempt, name='dispatch')
class AncillaryServiceAPI(View, LoginRequiredMixin):
    """API endpoint for ancillary service data"""
    
    def get(self, request):
        try:
            service_id = request.GET.get('service_id')
            service_code = request.GET.get('service_code')
            
            if not service_id and not service_code:
                return JsonResponse({'error': 'Service ID or Code is required'}, status=400)
            
            # Get service
            if service_id:
                service = get_object_or_404(
                    AncillaryService.objects.select_related('airline', 'category'),
                    id=service_id
                )
            else:
                service = get_object_or_404(
                    AncillaryService.objects.select_related('airline', 'category'),
                    code=service_code
                )
            
            # Prepare response data
            data = {
                'id': str(service.id),
                'code': service.code,
                'name': service.name,
                'name_ar': service.name_ar,
                'description': service.description,
                'description_ar': service.description_ar,
                'service_type': service.service_type,
                'category': {
                    'id': str(service.category.id) if service.category else None,
                    'name': service.category.name if service.category else None,
                    'slug': service.category.slug if service.category else None,
                },
                'airline': {
                    'code': service.airline.code,
                    'name': service.airline.name,
                    'name_ar': service.airline.name_ar,
                },
                'price': float(service.price) if service.price else 0,
                'currency': service.currency,
                'is_active': service.is_active,
                'availability': service.availability,
                'restrictions': service.restrictions,
                'included_services': [
                    {
                        'id': str(s.id),
                        'code': s.code,
                        'name': s.name,
                        'service_type': s.service_type,
                    }
                    for s in service.included_services.all()
                ],
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            logger.error(f"Error in ancillary service API: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AncillaryAvailabilityAPI(View, LoginRequiredMixin):
    """API endpoint for ancillary service availability"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['service_id', 'booking_id', 'passenger_id']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    })
            
            # Get objects
            service = get_object_or_404(AncillaryService, id=data['service_id'])
            booking = get_object_or_404(Booking, id=data['booking_id'])
            passenger = get_object_or_404(Passenger, id=data['passenger_id'])
            
            # Check if passenger belongs to booking
            if not booking.passengers.filter(id=passenger.id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Passenger does not belong to this booking'
                })
            
            # Check permission
            if not AncillaryPermission.can_book_for_booking(request.user, booking):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Check availability
            availability = ancillary_manager.check_service_availability(
                service=service,
                booking=booking,
                passenger=passenger,
                segment_id=data.get('segment_id')
            )
            
            return JsonResponse({
                'success': True,
                'available': availability['available'],
                'message': availability.get('message', ''),
                'restrictions': availability.get('restrictions', []),
                'alternatives': availability.get('alternatives', []),
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in ancillary availability API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class AncillaryBookingAPI(View, LoginRequiredMixin):
    """API endpoint for ancillary bookings"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['service_id', 'booking_id', 'passenger_id']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    })
            
            # Get objects
            service = get_object_or_404(AncillaryService, id=data['service_id'])
            booking = get_object_or_404(Booking, id=data['booking_id'])
            passenger = get_object_or_404(Passenger, id=data['passenger_id'])
            
            # Check if passenger belongs to booking
            if not booking.passengers.filter(id=passenger.id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Passenger does not belong to this booking'
                })
            
            # Check permission
            if not AncillaryPermission.can_book_for_booking(request.user, booking):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Create booking
            result = ancillary_manager.book_service(
                service=service,
                booking=booking,
                passenger=passenger,
                user=request.user,
                segment_id=data.get('segment_id'),
                quantity=data.get('quantity', 1),
                notes=data.get('notes', '')
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Service booked successfully',
                    'booking_id': str(result['booking'].id),
                    'total_price': float(result['total_price']),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to book service'),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in ancillary booking API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class AncillaryCancelAPI(View, LoginRequiredMixin):
    """API endpoint for cancelling ancillary bookings"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            if 'booking_id' not in data:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required field: booking_id'
                })
            
            # Get ancillary booking
            ancillary_booking = get_object_or_404(
                AncillaryBooking.objects.select_related('booking'),
                id=data['booking_id']
            )
            
            # Check permission
            if not AncillaryPermission.can_cancel_booking(request.user, ancillary_booking.booking):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Check if booking can be cancelled
            if ancillary_booking.status not in ['pending', 'confirmed']:
                return JsonResponse({
                    'success': False,
                    'error': f'Booking cannot be cancelled in current status: {ancillary_booking.status}'
                })
            
            # Initialize ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Cancel booking
            result = ancillary_manager.cancel_booking(
                ancillary_booking=ancillary_booking,
                user=request.user,
                reason=data.get('reason', ''),
                refund_requested=data.get('refund_requested', False)
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Booking cancelled successfully',
                    'refund_amount': float(result.get('refund_amount', 0)),
                    'refund_status': result.get('refund_status', 'none'),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to cancel booking'),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in ancillary cancel API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class AncillaryModifyAPI(View, LoginRequiredMixin):
    """API endpoint for modifying ancillary bookings"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            if 'booking_id' not in data:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required field: booking_id'
                })
            
            # Get ancillary booking
            ancillary_booking = get_object_or_404(
                AncillaryBooking.objects.select_related('booking'),
                id=data['booking_id']
            )
            
            # Check permission
            if not AncillaryPermission.can_modify_booking(request.user, ancillary_booking.booking):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Check if booking can be modified
            if ancillary_booking.status not in ['pending', 'confirmed']:
                return JsonResponse({
                    'success': False,
                    'error': f'Booking cannot be modified in current status: {ancillary_booking.status}'
                })
            
            # Initialize ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Modify booking
            result = ancillary_manager.modify_booking(
                ancillary_booking=ancillary_booking,
                user=request.user,
                service_id=data.get('new_service_id'),
                quantity=data.get('new_quantity'),
                segment_id=data.get('new_segment_id'),
                notes=data.get('notes', '')
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Booking modified successfully',
                    'price_difference': float(result.get('price_difference', 0)),
                    'new_total': float(result.get('new_total', 0)),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to modify booking'),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in ancillary modify API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class AncillaryDashboardView(LoginRequiredMixin, View):
    """Ancillary services dashboard"""
    
    template_name = 'flights/ancillary/ancillary_dashboard.html'
    
    def get(self, request):
        try:
            # Get time period
            time_period = request.GET.get('period', '30d')
            
            # Calculate date range
            today = timezone.now().date()
            if time_period == '7d':
                start_date = today - timedelta(days=7)
            elif time_period == '30d':
                start_date = today - timedelta(days=30)
            elif time_period == '90d':
                start_date = today - timedelta(days=90)
            else:
                start_date = today - timedelta(days=30)
            
            # Initialize ancillary service manager
            ancillary_manager = AncillaryServiceManager()
            
            # Get dashboard data
            dashboard_data = ancillary_manager.get_dashboard_data(
                start_date=start_date,
                end_date=today,
                user=request.user
            )
            
            # Get top services
            top_services = ancillary_manager.get_top_services(
                limit=10,
                start_date=start_date,
                end_date=today,
                user=request.user
            )
            
            # Get recent bookings
            recent_bookings = AncillaryBooking.objects.filter(
                status='confirmed',
                created_at__date__gte=start_date,
                created_at__date__lte=today
            ).select_related(
                'service',
                'booking',
                'passenger'
            ).order_by('-created_at')[:10]
            
            # Apply user permissions for recent bookings
            if request.user.user_type == 'agent':
                recent_bookings = recent_bookings.filter(booking__agent=request.user)
            elif request.user.user_type == 'sub_agent':
                parent_agent = request.user.parent_agent
                if parent_agent:
                    recent_bookings = recent_bookings.filter(booking__agent=parent_agent)
            
            context = {
                'dashboard_data': dashboard_data,
                'top_services': top_services,
                'recent_bookings': recent_bookings,
                'time_period': time_period,
                'period_options': [
                    ('7d', 'Last 7 Days'),
                    ('30d', 'Last 30 Days'),
                    ('90d', 'Last 90 Days'),
                ],
                'can_view_reports': request.user.user_type in ['admin', 'super_agent'],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ancillary dashboard: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading dashboard.')
            return render(request, self.template_name)


class AncillaryIntegrationView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Ancillary services integration with GDS"""
    
    template_name = 'flights/ancillary/ancillary_integration.html'
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'super_agent']
    
    def get(self, request):
        try:
            # Get integration parameters
            airline_code = request.GET.get('airline', '').upper()
            integration_type = request.GET.get('type', 'sync')
            
            # Initialize integration service
            integration_service = AncillaryIntegrationService()
            
            # Get integration status
            integration_status = integration_service.get_integration_status(airline_code)
            
            # Get available airlines
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            context = {
                'airline_code': airline_code,
                'integration_type': integration_type,
                'integration_status': integration_status,
                'airlines': airlines,
                'integration_types': [
                    ('sync', 'Synchronize Services'),
                    ('pricing', 'Update Pricing'),
                    ('availability', 'Check Availability'),
                    ('booking', 'Test Booking'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ancillary integration: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading integration: {str(e)}')
            return render(request, self.template_name)
    
    def post(self, request):
        try:
            airline_code = request.POST.get('airline', '').upper()
            integration_type = request.POST.get('type', 'sync')
            
            if not airline_code:
                messages.error(request, 'Airline code is required.')
                return redirect('flights:ancillary_integration')
            
            # Get airline
            airline = get_object_or_404(Airline, code=airline_code)
            
            # Initialize integration service
            integration_service = AncillaryIntegrationService()
            
            # Perform integration based on type
            if integration_type == 'sync':
                result = integration_service.synchronize_services(airline)
                message = result.get('message', 'Services synchronized successfully')
                
            elif integration_type == 'pricing':
                result = integration_service.update_pricing(airline)
                message = result.get('message', 'Pricing updated successfully')
                
            elif integration_type == 'availability':
                result = integration_service.check_availability(airline)
                message = result.get('message', 'Availability checked successfully')
                
            elif integration_type == 'booking':
                result = integration_service.test_booking(airline)
                message = result.get('message', 'Booking test completed')
                
            else:
                messages.error(request, 'Invalid integration type.')
                return redirect('flights:ancillary_integration')
            
            if result.get('success'):
                messages.success(request, message)
            else:
                messages.error(request, result.get('error', 'Integration failed'))
            
            return redirect('flights:ancillary_integration')
            
        except Exception as e:
            logger.error(f"Error in ancillary integration: {str(e)}", exc_info=True)
            messages.error(request, f'Error in integration: {str(e)}')
            return redirect('flights:ancillary_integration')