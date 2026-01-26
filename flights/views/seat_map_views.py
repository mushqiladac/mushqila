# flights/views/seat_map_views.py
"""
Seat Map Views for B2B Travel Platform
Production Ready - Final Version
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, F, Prefetch, Subquery, OuterRef, Sum, Avg
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
from decimal import Decimal
import re
import math
from collections import defaultdict
from io import BytesIO
import base64

# Optional imports for models
try:
    from flights.models import (
        SeatSelection, SeatInventory, SeatPreference, Aircraft,
        Booking, BookingPassenger, Passenger, FlightSegment, FlightItinerary,
        Airline, Airport, SeatMapConfiguration
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

# Optional imports for forms
try:
    from flights.forms import (
        SeatSelectionForm, SeatPreferenceForm, BulkSeatSelectionForm,
        SeatMapFilterForm, SeatUpgradeForm, SeatSwapForm
    )
    FORMS_AVAILABLE = True
except ImportError:
    FORMS_AVAILABLE = False

# Optional imports for services and utilities
try:
    from flights.services.seat_service import SeatService
except ImportError:
    SeatService = None

try:
    from flights.services.gds_service import GDSSeatService
except ImportError:
    GDSSeatService = None

try:
    from flights.services.booking_service import BookingService
except ImportError:
    BookingService = None

try:
    from flights.services.payment_service import PaymentService
except ImportError:
    PaymentService = None

try:
    from flights.utils.seat_map_generator import SeatMapGenerator
except ImportError:
    SeatMapGenerator = None

try:
    from flights.utils.cache import SeatMapCache
except ImportError:
    SeatMapCache = None

try:
    from flights.utils.permissions import SeatPermission
except ImportError:
    SeatPermission = None

try:
    from flights.utils.validators import SeatValidator
except ImportError:
    SeatValidator = None

try:
    from flights.utils.export import SeatMapExport
except ImportError:
    SeatMapExport = None

logger = logging.getLogger(__name__)


class SeatMapListView(LoginRequiredMixin, View):
    """List seat selections and seat map configurations"""
    
    template_name = 'flights/seat_map/seat_map_list.html'
    items_per_page = 20
    
    def get(self, request):
        try:
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            flight_filter = request.GET.get('flight', '')
            date_filter = request.GET.get('date', '')
            status_filter = request.GET.get('status', 'all')
            search_query = request.GET.get('q', '').strip()
            sort_by = request.GET.get('sort', '-created_at')
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            seat_selections = SeatSelection.objects.select_related(
                'booking',
                'booking__itinerary',
                'booking__itinerary__search',
                'segment',
                'segment__airline',
                'passenger',
                'seat_inventory'
            ).prefetch_related(
                'seat_preferences'
            )
            
            # Apply user permissions
            if request.user.user_type == 'agent':
                seat_selections = seat_selections.filter(booking__agent=request.user)
            elif request.user.user_type == 'sub_agent':
                # Get parent agent's bookings
                parent_agent = request.user.parent_agent
                if parent_agent:
                    seat_selections = seat_selections.filter(booking__agent=parent_agent)
            
            # Apply filters
            if airline_filter != 'all':
                seat_selections = seat_selections.filter(segment__airline__code=airline_filter)
            
            if flight_filter:
                seat_selections = seat_selections.filter(
                    Q(segment__flight_number__icontains=flight_filter) |
                    Q(segment__airline__code__icontains=flight_filter)
                )
            
            if date_filter:
                try:
                    date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    seat_selections = seat_selections.filter(segment__departure_time__date=date_obj)
                except ValueError:
                    pass
            
            if status_filter != 'all':
                seat_selections = seat_selections.filter(status=status_filter)
            
            # Apply search
            if search_query:
                seat_selections = seat_selections.filter(
                    Q(passenger__first_name__icontains=search_query) |
                    Q(passenger__last_name__icontains=search_query) |
                    Q(seat_number__icontains=search_query) |
                    Q(booking__booking_reference__icontains=search_query) |
                    Q(booking__pnr__icontains=search_query)
                )
            
            # Apply sorting
            valid_sort_fields = [
                'created_at', '-created_at',
                'segment__departure_time', '-segment__departure_time',
                'seat_number', '-seat_number',
                'price', '-price',
                'status', '-status'
            ]
            if sort_by in valid_sort_fields:
                seat_selections = seat_selections.order_by(sort_by)
            else:
                seat_selections = seat_selections.order_by('-created_at')
            
            # Get statistics
            stats = self.get_seat_map_statistics(seat_selections)
            
            # Pagination
            paginator = Paginator(seat_selections, self.items_per_page)
            page_obj = paginator.get_page(page_number)
            
            # Get filter options
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'airline_filter': airline_filter,
                'flight_filter': flight_filter,
                'date_filter': date_filter,
                'status_filter': status_filter,
                'search_query': search_query,
                'sort_by': sort_by,
                'stats': stats,
                'status_options': [
                    ('all', 'All Status'),
                    ('selected', 'Selected'),
                    ('confirmed', 'Confirmed'),
                    ('cancelled', 'Cancelled'),
                    ('pending', 'Pending'),
                ],
                'sort_options': [
                    ('-created_at', 'Newest First'),
                    ('created_at', 'Oldest First'),
                    ('segment__departure_time', 'Departure (Asc)'),
                    ('-segment__departure_time', 'Departure (Desc)'),
                    ('seat_number', 'Seat Number (A-Z)'),
                    ('-seat_number', 'Seat Number (Z-A)'),
                    ('price', 'Price (Low-High)'),
                    ('-price', 'Price (High-Low)'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading seat map list: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading seat selections. Please try again.')
            return render(request, self.template_name, {'page_obj': []})
    
    def get_seat_map_statistics(self, seat_selections):
        """Calculate seat map statistics"""
        today = timezone.now().date()
        
        stats = {
            'total_selections': seat_selections.count(),
            'confirmed_selections': seat_selections.filter(status='confirmed').count(),
            'pending_selections': seat_selections.filter(status='pending').count(),
            'cancelled_selections': seat_selections.filter(status='cancelled').count(),
            'total_revenue': seat_selections.filter(
                status='confirmed'
            ).aggregate(total=Sum('price'))['total'] or Decimal('0.00'),
            'average_price': seat_selections.filter(
                status='confirmed'
            ).aggregate(avg=Avg('price'))['avg'] or Decimal('0.00'),
        }
        
        # Today's statistics
        today_selections = seat_selections.filter(created_at__date=today)
        stats['today_count'] = today_selections.count()
        stats['today_revenue'] = today_selections.filter(
            status='confirmed'
        ).aggregate(total=Sum('price'))['total'] or Decimal('0.00')
        
        # Airline breakdown
        airline_stats = seat_selections.values(
            'segment__airline__code',
            'segment__airline__name'
        ).annotate(
            count=Count('id'),
            revenue=Sum('price')
        ).order_by('-count')[:10]
        
        stats['airline_breakdown'] = airline_stats
        
        # Seat type breakdown
        seat_type_stats = seat_selections.values('seat_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['seat_type_breakdown'] = {item['seat_type']: item['count'] for item in seat_type_stats}
        
        return stats


class SeatMapDetailView(LoginRequiredMixin, View):
    """View detailed seat map for a flight segment"""
    
    template_name = 'flights/seat_map/seat_map_detail.html'
    
    def get(self, request, segment_id):
        try:
            # Get flight segment
            segment = get_object_or_404(
                FlightSegment.objects.select_related(
                    'airline',
                    'origin',
                    'destination',
                    'aircraft'
                ),
                id=segment_id
            )
            
            # Check permission
            if not SeatPermission.can_view_seat_map(request.user, segment):
                raise PermissionDenied("You don't have permission to view this seat map")
            
            # Get seat service
            seat_service = SeatService()
            
            # Generate seat map
            seat_map_data = seat_service.generate_seat_map(segment)
            
            # Get seat inventory
            seat_inventory = SeatInventory.objects.filter(segment=segment).first()
            
            # Get seat selections for this segment
            seat_selections = SeatSelection.objects.filter(
                segment=segment,
                status__in=['selected', 'confirmed']
            ).select_related('passenger', 'booking')
            
            # Get seat preferences
            seat_preferences = SeatPreference.objects.filter(
                segment=segment
            ).select_related('passenger')
            
            # Get aircraft configuration
            aircraft_config = self.get_aircraft_configuration(segment.aircraft)
            
            # Calculate statistics
            stats = self.get_seat_map_statistics(segment, seat_map_data)
            
            context = {
                'segment': segment,
                'seat_map_data': seat_map_data,
                'seat_inventory': seat_inventory,
                'seat_selections': seat_selections,
                'seat_preferences': seat_preferences,
                'aircraft_config': aircraft_config,
                'stats': stats,
                'can_select_seats': SeatPermission.can_select_seats(request.user, segment),
                'can_modify_seats': SeatPermission.can_modify_seats(request.user, segment),
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for seat map {segment_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:seat_map_list')
        except Exception as e:
            logger.error(f"Error loading seat map detail {segment_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading seat map: {str(e)}')
            return redirect('flights:seat_map_list')
    
    def get_aircraft_configuration(self, aircraft):
        """Get aircraft configuration"""
        if not aircraft:
            return {}
        
        config = {
            'icao_code': aircraft.icao_code,
            'model': aircraft.model,
            'manufacturer': aircraft.manufacturer,
            'max_passengers': aircraft.max_passengers,
            'typical_seating': aircraft.typical_seating or {},
            'seat_map_available': bool(aircraft.typical_seating),
        }
        
        # Add seat layout if available
        if aircraft.typical_seating:
            config['seat_layout'] = aircraft.typical_seating.get('layout', {})
            config['seat_classes'] = aircraft.typical_seating.get('classes', {})
        
        return config
    
    def get_seat_map_statistics(self, segment, seat_map_data):
        """Calculate seat map statistics"""
        total_seats = 0
        available_seats = 0
        occupied_seats = 0
        blocked_seats = 0
        
        for deck in seat_map_data.get('decks', []):
            for row in deck.get('rows', []):
                for seat in row.get('seats', []):
                    total_seats += 1
                    if seat.get('status') == 'available':
                        available_seats += 1
                    elif seat.get('status') == 'occupied':
                        occupied_seats += 1
                    elif seat.get('status') == 'blocked':
                        blocked_seats += 1
        
        stats = {
            'total_seats': total_seats,
            'available_seats': available_seats,
            'occupied_seats': occupied_seats,
            'blocked_seats': blocked_seats,
            'occupancy_rate': (occupied_seats / total_seats * 100) if total_seats > 0 else 0,
            'availability_rate': (available_seats / total_seats * 100) if total_seats > 0 else 0,
        }
        
        # Add seat class breakdown
        class_breakdown = {}
        for deck in seat_map_data.get('decks', []):
            for row in deck.get('rows', []):
                for seat in row.get('seats', []):
                    seat_class = seat.get('class', 'economy')
                    if seat_class not in class_breakdown:
                        class_breakdown[seat_class] = {
                            'total': 0,
                            'available': 0,
                            'occupied': 0,
                            'blocked': 0,
                        }
                    
                    class_breakdown[seat_class]['total'] += 1
                    if seat.get('status') == 'available':
                        class_breakdown[seat_class]['available'] += 1
                    elif seat.get('status') == 'occupied':
                        class_breakdown[seat_class]['occupied'] += 1
                    elif seat.get('status') == 'blocked':
                        class_breakdown[seat_class]['blocked'] += 1
        
        stats['class_breakdown'] = class_breakdown
        
        return stats


class SeatSelectionView(LoginRequiredMixin, View):
    """Select seats for passengers"""
    
    template_name = 'flights/seat_map/seat_selection.html'
    
    def get(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(
                Booking.objects.select_related(
                    'itinerary',
                    'itinerary__search'
                ).prefetch_related(
                    Prefetch('passengers', queryset=Passenger.objects.all()),
                    Prefetch('bookingpassenger_set', queryset=BookingPassenger.objects.all()),
                ),
                id=booking_id
            )
            
            # Check permission
            if not SeatPermission.can_select_seats_for_booking(request.user, booking):
                raise PermissionDenied("You don't have permission to select seats for this booking")
            
            # Get seat service
            seat_service = SeatService()
            
            # Get available segments for seat selection
            segments = booking.itinerary.segments.all().order_by('departure_time')
            
            # Get seat map for each segment
            seat_maps = []
            for segment in segments:
                seat_map_data = seat_service.generate_seat_map(segment)
                seat_maps.append({
                    'segment': segment,
                    'seat_map': seat_map_data,
                })
            
            # Get passenger list
            passengers = booking.passengers.all()
            
            # Get existing seat selections
            existing_selections = SeatSelection.objects.filter(
                booking=booking,
                status__in=['selected', 'confirmed']
            ).select_related('segment', 'passenger')
            
            # Create mapping of passenger to seat selections
            passenger_seats = {}
            for selection in existing_selections:
                if selection.passenger_id not in passenger_seats:
                    passenger_seats[selection.passenger_id] = {}
                passenger_seats[selection.passenger_id][selection.segment_id] = selection
            
            context = {
                'booking': booking,
                'segments': segments,
                'seat_maps': seat_maps,
                'passengers': passengers,
                'passenger_seats': passenger_seats,
                'can_select_all': SeatPermission.can_select_multiple_seats(request.user),
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for seat selection {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error loading seat selection {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading seat selection: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)
    
    @method_decorator(csrf_exempt)
    def post(self, request, booking_id):
        try:
            data = json.loads(request.body)
            seat_selections = data.get('seat_selections', [])
            
            if not seat_selections:
                return JsonResponse({
                    'success': False,
                    'error': 'No seat selections provided'
                })
            
            # Get booking
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check permission
            if not SeatPermission.can_select_seats_for_booking(request.user, booking):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize seat service
            seat_service = SeatService()
            
            # Process seat selections
            result = seat_service.process_seat_selections(
                booking=booking,
                seat_selections=seat_selections,
                user=request.user
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Seats selected successfully',
                    'selections': result.get('selections', []),
                    'total_price': result.get('total_price', 0),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to select seats'),
                    'details': result.get('details', {}),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error processing seat selection {booking_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class SeatUpgradeView(LoginRequiredMixin, View):
    """Upgrade seat selection"""
    
    template_name = 'flights/seat_map/seat_upgrade.html'
    
    def get(self, request, selection_id):
        try:
            # Get seat selection
            seat_selection = get_object_or_404(
                SeatSelection.objects.select_related(
                    'booking',
                    'segment',
                    'segment__airline',
                    'passenger'
                ),
                id=selection_id
            )
            
            # Check permission
            if not SeatPermission.can_upgrade_seat(request.user, seat_selection):
                raise PermissionDenied("You don't have permission to upgrade this seat")
            
            # Get seat service
            seat_service = SeatService()
            
            # Get available upgrades
            available_upgrades = seat_service.get_available_upgrades(seat_selection)
            
            # Get upgrade form
            form = SeatUpgradeForm(
                initial={
                    'current_seat': seat_selection.seat_number,
                    'current_class': seat_selection.seat_class,
                }
            )
            
            context = {
                'seat_selection': seat_selection,
                'available_upgrades': available_upgrades,
                'form': form,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for seat upgrade {selection_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:seat_map_list')
        except Exception as e:
            logger.error(f"Error loading seat upgrade {selection_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading seat upgrade: {str(e)}')
            return redirect('flights:seat_map_list')
    
    def post(self, request, selection_id):
        try:
            # Get seat selection
            seat_selection = get_object_or_404(SeatSelection, id=selection_id)
            
            # Check permission
            if not SeatPermission.can_upgrade_seat(request.user, seat_selection):
                raise PermissionDenied("You don't have permission to upgrade this seat")
            
            form = SeatUpgradeForm(request.POST)
            
            if form.is_valid():
                # Get upgrade details
                upgrade_to = form.cleaned_data['upgrade_to']
                new_seat_number = form.cleaned_data['new_seat_number']
                payment_method = form.cleaned_data['payment_method']
                
                # Initialize seat service
                seat_service = SeatService()
                
                # Process upgrade
                result = seat_service.process_seat_upgrade(
                    seat_selection=seat_selection,
                    upgrade_to=upgrade_to,
                    new_seat_number=new_seat_number,
                    payment_method=payment_method,
                    user=request.user
                )
                
                if result['success']:
                    messages.success(request, result['message'])
                    return redirect('flights:seat_selection_detail', selection_id=seat_selection.id)
                else:
                    messages.error(request, result.get('error', 'Upgrade failed'))
                    form.add_error(None, result.get('error'))
            
            # Re-render form with errors
            available_upgrades = seat_service.get_available_upgrades(seat_selection)
            
            context = {
                'seat_selection': seat_selection,
                'available_upgrades': available_upgrades,
                'form': form,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for seat upgrade {selection_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:seat_map_list')
        except Exception as e:
            logger.error(f"Error processing seat upgrade {selection_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing seat upgrade: {str(e)}')
            return redirect('flights:seat_map_list')


class SeatSwapView(LoginRequiredMixin, View):
    """Swap seats between passengers"""
    
    template_name = 'flights/seat_map/seat_swap.html'
    
    def get(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(
                Booking.objects.select_related('itinerary').prefetch_related('passengers'),
                id=booking_id
            )
            
            # Check permission
            if not SeatPermission.can_swap_seats(request.user, booking):
                raise PermissionDenied("You don't have permission to swap seats for this booking")
            
            # Get segments
            segments = booking.itinerary.segments.all().order_by('departure_time')
            
            # Get current seat selections
            seat_selections = SeatSelection.objects.filter(
                booking=booking,
                status__in=['selected', 'confirmed']
            ).select_related('segment', 'passenger')
            
            # Group by segment
            segment_seats = {}
            for selection in seat_selections:
                if selection.segment_id not in segment_seats:
                    segment_seats[selection.segment_id] = []
                segment_seats[selection.segment_id].append(selection)
            
            # Get form
            form = SeatSwapForm(booking=booking)
            
            context = {
                'booking': booking,
                'segments': segments,
                'segment_seats': segment_seats,
                'form': form,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for seat swap {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error loading seat swap {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading seat swap: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)
    
    def post(self, request, booking_id):
        try:
            # Get booking
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check permission
            if not SeatPermission.can_swap_seats(request.user, booking):
                raise PermissionDenied("You don't have permission to swap seats for this booking")
            
            form = SeatSwapForm(booking, request.POST)
            
            if form.is_valid():
                # Get swap details
                segment = form.cleaned_data['segment']
                passenger1 = form.cleaned_data['passenger1']
                passenger2 = form.cleaned_data['passenger2']
                
                # Initialize seat service
                seat_service = SeatService()
                
                # Process seat swap
                result = seat_service.process_seat_swap(
                    booking=booking,
                    segment=segment,
                    passenger1=passenger1,
                    passenger2=passenger2,
                    user=request.user
                )
                
                if result['success']:
                    messages.success(request, result['message'])
                    return redirect('flights:booking_detail', booking_id=booking.id)
                else:
                    messages.error(request, result.get('error', 'Seat swap failed'))
                    form.add_error(None, result.get('error'))
            
            # Re-render form with errors
            segments = booking.itinerary.segments.all().order_by('departure_time')
            seat_selections = SeatSelection.objects.filter(
                booking=booking,
                status__in=['selected', 'confirmed']
            ).select_related('segment', 'passenger')
            
            segment_seats = {}
            for selection in seat_selections:
                if selection.segment_id not in segment_seats:
                    segment_seats[selection.segment_id] = []
                segment_seats[selection.segment_id].append(selection)
            
            context = {
                'booking': booking,
                'segments': segments,
                'segment_seats': segment_seats,
                'form': form,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for seat swap {booking_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:booking_detail', booking_id=booking_id)
        except Exception as e:
            logger.error(f"Error processing seat swap {booking_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing seat swap: {str(e)}')
            return redirect('flights:booking_detail', booking_id=booking_id)


class BulkSeatSelectionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Bulk seat selection for group bookings"""
    
    template_name = 'flights/seat_map/bulk_seat_selection.html'
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'super_agent', 'agent']
    
    def get(self, request):
        try:
            # Get booking IDs from query parameters
            booking_ids = request.GET.get('bookings', '').split(',')
            booking_ids = [bid.strip() for bid in booking_ids if bid.strip()]
            
            # Get bookings
            bookings = Booking.objects.filter(
                id__in=booking_ids,
                agent=request.user
            ).select_related('itinerary').prefetch_related('passengers')
            
            if not bookings.exists():
                messages.error(request, 'No valid bookings selected.')
                return redirect('flights:booking_list')
            
            # Get common segments
            segments = FlightSegment.objects.filter(
                itinerary__booking__in=bookings
            ).distinct().select_related('airline', 'aircraft').order_by('departure_time')
            
            # Get seat service
            seat_service = SeatService()
            
            # Get seat maps for each segment
            seat_maps = []
            for segment in segments:
                seat_map_data = seat_service.generate_seat_map(segment)
                seat_maps.append({
                    'segment': segment,
                    'seat_map': seat_map_data,
                })
            
            # Get form
            form = BulkSeatSelectionForm(segments=segments, bookings=bookings)
            
            context = {
                'bookings': bookings,
                'segments': segments,
                'seat_maps': seat_maps,
                'form': form,
                'total_passengers': sum(b.passengers.count() for b in bookings),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading bulk seat selection: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading bulk seat selection: {str(e)}')
            return redirect('flights:booking_list')
    
    def post(self, request):
        try:
            # Parse form data
            booking_ids = request.POST.getlist('bookings')
            segment_id = request.POST.get('segment')
            
            if not booking_ids or not segment_id:
                messages.error(request, 'Missing required parameters.')
                return redirect('flights:booking_list')
            
            # Get bookings and segment
            bookings = Booking.objects.filter(id__in=booking_ids, agent=request.user)
            segment = get_object_or_404(FlightSegment, id=segment_id)
            
            # Get seat assignments from form
            seat_assignments = {}
            for key, value in request.POST.items():
                if key.startswith('seat_'):
                    parts = key.split('_')
                    if len(parts) >= 3:
                        passenger_id = parts[1]
                        seat_assignments[passenger_id] = value
            
            # Initialize seat service
            seat_service = SeatService()
            
            # Process bulk seat selection
            result = seat_service.process_bulk_seat_selection(
                bookings=bookings,
                segment=segment,
                seat_assignments=seat_assignments,
                user=request.user
            )
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('flights:booking_list')
            else:
                messages.error(request, result.get('error', 'Bulk seat selection failed'))
                
                # Re-render form with errors
                segments = FlightSegment.objects.filter(
                    itinerary__booking__in=bookings
                ).distinct().select_related('airline', 'aircraft').order_by('departure_time')
                
                seat_maps = []
                for seg in segments:
                    seat_map_data = seat_service.generate_seat_map(seg)
                    seat_maps.append({
                        'segment': seg,
                        'seat_map': seat_map_data,
                    })
                
                form = BulkSeatSelectionForm(
                    segments=segments,
                    bookings=bookings,
                    data=request.POST
                )
                
                context = {
                    'bookings': bookings,
                    'segments': segments,
                    'seat_maps': seat_maps,
                    'form': form,
                    'total_passengers': sum(b.passengers.count() for b in bookings),
                }
                
                return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error processing bulk seat selection: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing bulk seat selection: {str(e)}')
            return redirect('flights:booking_list')


class SeatPreferenceView(LoginRequiredMixin, View):
    """Manage seat preferences"""
    
    template_name = 'flights/seat_map/seat_preference.html'
    
    def get(self, request):
        try:
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            passenger_filter = request.GET.get('passenger', '')
            preference_type = request.GET.get('type', 'all')
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            seat_preferences = SeatPreference.objects.select_related(
                'passenger',
                'segment',
                'segment__airline'
            )
            
            # Apply filters
            if airline_filter != 'all':
                seat_preferences = seat_preferences.filter(segment__airline__code=airline_filter)
            
            if passenger_filter:
                seat_preferences = seat_preferences.filter(
                    Q(passenger__first_name__icontains=passenger_filter) |
                    Q(passenger__last_name__icontains=passenger_filter)
                )
            
            if preference_type != 'all':
                seat_preferences = seat_preferences.filter(preference_type=preference_type)
            
            # Apply user permissions
            if request.user.user_type == 'agent':
                seat_preferences = seat_preferences.filter(
                    segment__itinerary__booking__agent=request.user
                )
            elif request.user.user_type == 'sub_agent':
                parent_agent = request.user.parent_agent
                if parent_agent:
                    seat_preferences = seat_preferences.filter(
                        segment__itinerary__booking__agent=parent_agent
                    )
            
            # Order by
            seat_preferences = seat_preferences.order_by('-created_at')
            
            # Pagination
            paginator = Paginator(seat_preferences, 20)
            page_obj = paginator.get_page(page_number)
            
            # Get airlines for filter
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'airline_filter': airline_filter,
                'passenger_filter': passenger_filter,
                'preference_type': preference_type,
                'preference_types': [
                    ('all', 'All Types'),
                    ('window', 'Window Seat'),
                    ('aisle', 'Aisle Seat'),
                    ('exit', 'Exit Row'),
                    ('front', 'Front of Cabin'),
                    ('rear', 'Rear of Cabin'),
                    ('bulkhead', 'Bulkhead'),
                    ('extra_legroom', 'Extra Legroom'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading seat preferences: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading seat preferences.')
            return render(request, self.template_name, {'page_obj': []})


class SeatMapConfigurationView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Configure seat maps for aircraft"""
    
    template_name = 'flights/seat_map/seat_map_configuration.html'
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'super_agent']
    
    def get(self, request):
        try:
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            aircraft_filter = request.GET.get('aircraft', '')
            search_query = request.GET.get('q', '').strip()
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            configurations = SeatMapConfiguration.objects.select_related(
                'airline',
                'aircraft'
            ).order_by('airline__name', 'aircraft__model')
            
            # Apply filters
            if airline_filter != 'all':
                configurations = configurations.filter(airline__code=airline_filter)
            
            if aircraft_filter:
                configurations = configurations.filter(
                    Q(aircraft__icao_code__icontains=aircraft_filter) |
                    Q(aircraft__model__icontains=aircraft_filter)
                )
            
            if search_query:
                configurations = configurations.filter(
                    Q(name__icontains=search_query) |
                    Q(airline__name__icontains=search_query) |
                    Q(aircraft__model__icontains=search_query)
                )
            
            # Pagination
            paginator = Paginator(configurations, 20)
            page_obj = paginator.get_page(page_number)
            
            # Get airlines for filter
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'airline_filter': airline_filter,
                'aircraft_filter': aircraft_filter,
                'search_query': search_query,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading seat map configurations: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading configurations.')
            return render(request, self.template_name, {'page_obj': []})


class SeatMapExportView(LoginRequiredMixin, View):
    """Export seat maps and selections"""
    
    def get(self, request):
        try:
            export_format = request.GET.get('format', 'excel')
            export_type = request.GET.get('type', 'selections')
            
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Build queryset based on export type
            if export_type == 'selections':
                queryset = SeatSelection.objects.select_related(
                    'booking',
                    'segment',
                    'segment__airline',
                    'passenger'
                )
                
                # Apply filters
                if airline_filter != 'all':
                    queryset = queryset.filter(segment__airline__code=airline_filter)
                
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
            
            elif export_type == 'inventory':
                queryset = SeatInventory.objects.select_related(
                    'segment',
                    'segment__airline'
                )
                
                # Apply filters
                if airline_filter != 'all':
                    queryset = queryset.filter(segment__airline__code=airline_filter)
            
            else:
                messages.error(request, 'Invalid export type.')
                return redirect('flights:seat_map_list')
            
            # Export based on format
            export_utils = SeatMapExport()
            
            if export_format == 'excel':
                return export_utils.export_to_excel(queryset, export_type)
            elif export_format == 'csv':
                return export_utils.export_to_csv(queryset, export_type)
            elif export_format == 'pdf':
                return export_utils.export_to_pdf(queryset, export_type)
            else:
                messages.error(request, 'Invalid export format.')
                return redirect('flights:seat_map_list')
                
        except Exception as e:
            logger.error(f"Error exporting seat data: {str(e)}", exc_info=True)
            messages.error(request, 'Error exporting seat data.')
            return redirect('flights:seat_map_list')


# API Views for AJAX operations

@method_decorator(csrf_exempt, name='dispatch')
class SeatMapAPI(View, LoginRequiredMixin):
    """API endpoint for seat map data"""
    
    def get(self, request, segment_id):
        try:
            # Get segment
            segment = get_object_or_404(FlightSegment, id=segment_id)
            
            # Check permission
            if not SeatPermission.can_view_seat_map(request.user, segment):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # Check cache first
            cache_key = f'seat_map_{segment_id}_{request.user.id}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return JsonResponse(cached_data)
            
            # Generate seat map
            seat_service = SeatService()
            seat_map_data = seat_service.generate_seat_map(segment)
            
            # Cache for 5 minutes
            cache.set(cache_key, seat_map_data, 300)
            
            return JsonResponse(seat_map_data)
            
        except Exception as e:
            logger.error(f"Error in seat map API {segment_id}: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SeatSelectionAPI(View, LoginRequiredMixin):
    """API endpoint for seat selection"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['segment_id', 'passenger_id', 'seat_number']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    })
            
            # Get objects
            segment = get_object_or_404(FlightSegment, id=data['segment_id'])
            passenger = get_object_or_404(Passenger, id=data['passenger_id'])
            
            # Check permission
            if not SeatPermission.can_select_seat(request.user, segment, passenger):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize seat service
            seat_service = SeatService()
            
            # Select seat
            result = seat_service.select_seat(
                segment=segment,
                passenger=passenger,
                seat_number=data['seat_number'],
                user=request.user,
                booking_id=data.get('booking_id')
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Seat selected successfully',
                    'selection': result.get('selection'),
                    'price': result.get('price'),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to select seat'),
                    'details': result.get('details', {}),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in seat selection API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class SeatAvailabilityAPI(View, LoginRequiredMixin):
    """API endpoint for seat availability"""
    
    def get(self, request, segment_id):
        try:
            # Get segment
            segment = get_object_or_404(FlightSegment, id=segment_id)
            
            # Check permission
            if not SeatPermission.can_view_seat_map(request.user, segment):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # Get seat class filter
            seat_class = request.GET.get('class', 'all')
            
            # Initialize seat service
            seat_service = SeatService()
            
            # Get available seats
            available_seats = seat_service.get_available_seats(
                segment=segment,
                seat_class=seat_class if seat_class != 'all' else None
            )
            
            return JsonResponse({
                'success': True,
                'available_seats': available_seats,
                'total_available': len(available_seats),
            })
            
        except Exception as e:
            logger.error(f"Error in seat availability API {segment_id}: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SeatPriceAPI(View, LoginRequiredMixin):
    """API endpoint for seat pricing"""
    
    def get(self, request):
        try:
            segment_id = request.GET.get('segment_id')
            seat_number = request.GET.get('seat_number')
            seat_class = request.GET.get('seat_class', 'economy')
            
            if not segment_id or not seat_number:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required parameters'
                })
            
            # Get segment
            segment = get_object_or_404(FlightSegment, id=segment_id)
            
            # Initialize seat service
            seat_service = SeatService()
            
            # Get seat price
            price_info = seat_service.get_seat_price(
                segment=segment,
                seat_number=seat_number,
                seat_class=seat_class
            )
            
            return JsonResponse({
                'success': True,
                'price_info': price_info,
            })
            
        except Exception as e:
            logger.error(f"Error in seat price API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class SeatHoldAPI(View, LoginRequiredMixin):
    """API endpoint for holding seats"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['segment_id', 'seat_numbers']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    })
            
            # Get segment
            segment = get_object_or_404(FlightSegment, id=data['segment_id'])
            
            # Check permission
            if not SeatPermission.can_hold_seats(request.user, segment):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize seat service
            seat_service = SeatService()
            
            # Hold seats
            result = seat_service.hold_seats(
                segment=segment,
                seat_numbers=data['seat_numbers'],
                user=request.user,
                hold_duration=data.get('hold_duration', 10)  # minutes
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Seats held successfully',
                    'hold_id': result.get('hold_id'),
                    'expires_at': result.get('expires_at'),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to hold seats'),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in seat hold API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class SeatReleaseAPI(View, LoginRequiredMixin):
    """API endpoint for releasing held seats"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            if 'hold_id' not in data:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required field: hold_id'
                })
            
            # Initialize seat service
            seat_service = SeatService()
            
            # Release seats
            result = seat_service.release_seats(
                hold_id=data['hold_id'],
                user=request.user
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Seats released successfully',
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to release seats'),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in seat release API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class SeatMapVisualizationView(LoginRequiredMixin, View):
    """Interactive seat map visualization"""
    
    template_name = 'flights/seat_map/seat_map_visualization.html'
    
    def get(self, request, segment_id):
        try:
            # Get segment
            segment = get_object_or_404(
                FlightSegment.objects.select_related(
                    'airline',
                    'aircraft',
                    'origin',
                    'destination'
                ),
                id=segment_id
            )
            
            # Check permission
            if not SeatPermission.can_view_seat_map(request.user, segment):
                raise PermissionDenied("You don't have permission to view this seat map")
            
            # Get seat service
            seat_service = SeatService()
            
            # Generate seat map with full details
            seat_map_data = seat_service.generate_seat_map(segment, detailed=True)
            
            # Get seat selections
            seat_selections = SeatSelection.objects.filter(
                segment=segment,
                status__in=['selected', 'confirmed']
            ).select_related('passenger', 'booking')
            
            # Get seat inventory
            seat_inventory = SeatInventory.objects.filter(segment=segment).first()
            
            # Prepare data for visualization
            visualization_data = {
                'segment': {
                    'id': segment.id,
                    'flight_number': segment.get_flight_designator(),
                    'airline': segment.airline.code,
                    'origin': segment.origin.iata_code,
                    'destination': segment.destination.iata_code,
                    'departure_time': segment.departure_time.isoformat(),
                    'aircraft': segment.aircraft.icao_code if segment.aircraft else 'Unknown',
                },
                'seat_map': seat_map_data,
                'seat_selections': [
                    {
                        'seat_number': sel.seat_number,
                        'passenger_name': f"{sel.passenger.first_name} {sel.passenger.last_name}",
                        'passenger_id': sel.passenger.id,
                        'status': sel.status,
                        'seat_class': sel.seat_class,
                        'price': float(sel.price) if sel.price else 0,
                    }
                    for sel in seat_selections
                ],
                'seat_inventory': {
                    'total_seats': seat_inventory.total_seats if seat_inventory else 0,
                    'available_seats': seat_inventory.available_seats if seat_inventory else 0,
                    'blocked_seats': seat_inventory.blocked_seats if seat_inventory else 0,
                } if seat_inventory else None,
                'interactive': True,
                'can_select_seats': SeatPermission.can_select_seats(request.user, segment),
                'can_modify_seats': SeatPermission.can_modify_seats(request.user, segment),
            }
            
            context = {
                'segment': segment,
                'visualization_data': json.dumps(visualization_data),
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for seat map visualization {segment_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:seat_map_list')
        except Exception as e:
            logger.error(f"Error loading seat map visualization {segment_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading seat map visualization: {str(e)}')
            return redirect('flights:seat_map_list')


class SeatMapReportView(LoginRequiredMixin, View):
    """Generate seat map reports"""
    
    template_name = 'flights/seat_map/seat_map_report.html'
    
    def get(self, request):
        try:
            # Get report parameters
            report_type = request.GET.get('type', 'occupancy')
            airline_filter = request.GET.get('airline', 'all')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Initialize seat service
            seat_service = SeatService()
            
            # Generate report based on type
            if report_type == 'occupancy':
                report_data = seat_service.generate_occupancy_report(
                    airline_code=airline_filter if airline_filter != 'all' else None,
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == 'revenue':
                report_data = seat_service.generate_revenue_report(
                    airline_code=airline_filter if airline_filter != 'all' else None,
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == 'preferences':
                report_data = seat_service.generate_preference_report(
                    airline_code=airline_filter if airline_filter != 'all' else None,
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
                'start_date': start_date,
                'end_date': end_date,
                'report_types': [
                    ('occupancy', 'Occupancy Report'),
                    ('revenue', 'Revenue Report'),
                    ('preferences', 'Preference Report'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error generating seat map report: {str(e)}", exc_info=True)
            messages.error(request, f'Error generating report: {str(e)}')
            return render(request, self.template_name)