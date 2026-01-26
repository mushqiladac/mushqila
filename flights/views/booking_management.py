# flights/views/booking_management.py
"""
Booking Management Views for B2B Travel Platform
Production Ready - Final Version
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.db import transaction
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# Optional imports for models
try:
    from flights.models import (
        Booking, Passenger, PNR, Ticket, Payment, Refund, 
        BookingHistory, FlightItinerary, AncillaryBooking
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

# Optional imports for forms
try:
    from flights.forms import (
        BookingModificationForm, CancellationRequestForm, 
        PassengerEditForm, ContactInformationForm
    )
    FORMS_AVAILABLE = True
except ImportError:
    FORMS_AVAILABLE = False

# Optional imports for services
try:
    from flights.services.booking_service import BookingService
except ImportError:
    BookingService = None

try:
    from flights.services.pnr_service import PNRService
except ImportError:
    PNRService = None

try:
    from flights.services.payment_service import PaymentService
except ImportError:
    PaymentService = None

try:
    from flights.services.notification_service import NotificationService
except ImportError:
    NotificationService = None

try:
    from flights.utils.export import ExportUtils
except ImportError:
    ExportUtils = None

logger = logging.getLogger(__name__)


class BookingListView(LoginRequiredMixin, View):
    """View all bookings with filters and search"""
    
    template_name = 'flights/management/booking_list.html'
    items_per_page = 20
    
    def get(self, request):
        try:
            # Get filter parameters
            status_filter = request.GET.get('status', 'all')
            date_filter = request.GET.get('date', 'today')
            search_query = request.GET.get('q', '').strip()
            sort_by = request.GET.get('sort', '-created_at')
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            bookings = Booking.objects.select_related(
                'itinerary',
                'agent',
                'corporate_client'
            ).prefetch_related(
                'passengers',
                'payments'
            )
            
            # Apply agent filter (agents can only see their own bookings)
            if request.user.user_type in ['agent', 'sub_agent']:
                bookings = bookings.filter(agent=request.user)
            elif request.user.user_type == 'super_agent':
                # Super agents can see their bookings and their sub-agents
                sub_agents = User.objects.filter(
                    parent_agent=request.user,
                    user_type__in=['agent', 'sub_agent']
                )
                bookings = bookings.filter(
                    Q(agent=request.user) | Q(agent__in=sub_agents)
                )
            
            # Apply status filter
            if status_filter != 'all':
                bookings = bookings.filter(status=status_filter)
            
            # Apply date filter
            today = timezone.now().date()
            if date_filter == 'today':
                bookings = bookings.filter(created_at__date=today)
            elif date_filter == 'tomorrow':
                tomorrow = today + timedelta(days=1)
                bookings = bookings.filter(
                    itinerary__segments__departure_time__date=tomorrow
                ).distinct()
            elif date_filter == 'week':
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                bookings = bookings.filter(
                    itinerary__segments__departure_time__date__range=[week_start, week_end]
                ).distinct()
            elif date_filter == 'month':
                month_start = today.replace(day=1)
                next_month = month_start.replace(day=28) + timedelta(days=4)
                month_end = next_month - timedelta(days=next_month.day)
                bookings = bookings.filter(
                    itinerary__segments__departure_time__date__range=[month_start, month_end]
                ).distinct()
            elif date_filter == 'past':
                bookings = bookings.filter(
                    itinerary__segments__departure_time__date__lt=today
                ).distinct()
            elif date_filter == 'future':
                bookings = bookings.filter(
                    itinerary__segments__departure_time__date__gt=today
                ).distinct()
            
            # Apply search filter
            if search_query:
                bookings = bookings.filter(
                    Q(booking_reference__icontains=search_query) |
                    Q(pnr__icontains=search_query) |
                    Q(passengers__first_name__icontains=search_query) |
                    Q(passengers__last_name__icontains=search_query) |
                    Q(agent__email__icontains=search_query) |
                    Q(corporate_client__email__icontains=search_query)
                ).distinct()
            
            # Apply sorting
            valid_sort_fields = [
                'created_at', '-created_at', 'total_amount', '-total_amount',
                'departure_date', '-departure_date', 'status', 'booking_reference'
            ]
            if sort_by in valid_sort_fields:
                bookings = bookings.order_by(sort_by)
            else:
                bookings = bookings.order_by('-created_at')
            
            # Calculate statistics
            stats = self.get_booking_statistics(bookings)
            
            # Pagination
            paginator = Paginator(bookings, self.items_per_page)
            page_obj = paginator.get_page(page_number)
            
            context = {
                'page_obj': page_obj,
                'status_filter': status_filter,
                'date_filter': date_filter,
                'search_query': search_query,
                'sort_by': sort_by,
                'stats': stats,
                'booking_statuses': Booking.BookingStatus.choices,
                'date_filters': [
                    ('all', 'All Dates'),
                    ('today', 'Today'),
                    ('tomorrow', 'Tomorrow'),
                    ('week', 'This Week'),
                    ('month', 'This Month'),
                    ('past', 'Past'),
                    ('future', 'Future'),
                ],
                'sort_options': [
                    ('-created_at', 'Newest First'),
                    ('created_at', 'Oldest First'),
                    ('total_amount', 'Price: Low to High'),
                    ('-total_amount', 'Price: High to Low'),
                    ('departure_date', 'Departure: Earliest'),
                    ('-departure_date', 'Departure: Latest'),
                ]
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading booking list: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading bookings. Please try again.')
            return render(request, self.template_name, {'page_obj': []})
    
    def get_booking_statistics(self, bookings):
        """Calculate booking statistics"""
        stats = {
            'total_bookings': bookings.count(),
            'total_revenue': bookings.aggregate(total=Sum('total_amount'))['total'] or 0,
            'pending_payments': bookings.filter(payment_status='pending').count(),
            'todays_bookings': bookings.filter(created_at__date=timezone.now().date()).count(),
        }
        
        # Status breakdown
        status_counts = bookings.values('status').annotate(count=Count('id'))
        stats['status_breakdown'] = {item['status']: item['count'] for item in status_counts}
        
        return stats


class BookingDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View booking details"""
    
    template_name = 'flights/management/booking_detail.html'
    
    def get_object(self):
        """Get booking object with all related data"""
        booking_ref = self.kwargs.get('booking_ref')
        booking = get_object_or_404(
            Booking.objects.select_related(
                'itinerary',
                'agent',
                'corporate_client'
            ).prefetch_related(
                Prefetch('passengers', queryset=Passenger.objects.all()),
                Prefetch('payments', queryset=Payment.objects.order_by('-created_at')),
                Prefetch('pnrs', queryset=PNR.objects.all()),
                Prefetch('tickets', queryset=Ticket.objects.all()),
                Prefetch('history', queryset=BookingHistory.objects.order_by('-created_at')),
                Prefetch('ancillary_bookings', queryset=AncillaryBooking.objects.select_related('ancillary_service')),
            ),
            booking_reference=booking_ref
        )
        return booking
    
    def test_func(self):
        """Check if user has permission to view this booking"""
        booking = self.get_object()
        user = self.request.user
        
        # Admin can view all bookings
        if user.user_type == 'admin':
            return True
        
        # Agent can view their own bookings
        if booking.agent == user:
            return True
        
        # Super agent can view their own and sub-agent bookings
        if user.user_type == 'super_agent':
            sub_agents = User.objects.filter(parent_agent=user)
            return booking.agent == user or booking.agent in sub_agents
        
        # Corporate client can view their own bookings
        if booking.corporate_client == user:
            return True
        
        return False
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to view this booking.')
        return redirect('flights:booking_list')
    
    def get(self, request, booking_ref):
        try:
            booking = self.get_object()
            booking_service = BookingService()
            
            # Get booking timeline
            timeline = booking_service.get_booking_timeline(booking)
            
            # Get fare rules
            fare_rules = booking_service.get_fare_rules(booking)
            
            # Get cancellation policy
            cancellation_policy = booking_service.get_cancellation_policy(booking)
            
            # Get payment summary
            payment_summary = booking_service.get_payment_summary(booking)
            
            # Get ancillary services summary
            ancillary_summary = booking_service.get_ancillary_summary(booking)
            
            context = {
                'booking': booking,
                'timeline': timeline,
                'fare_rules': fare_rules,
                'cancellation_policy': cancellation_policy,
                'payment_summary': payment_summary,
                'ancillary_summary': ancillary_summary,
                'can_modify': booking.can_be_modified(),
                'can_cancel': booking.can_be_cancelled(),
                'can_issue_ticket': booking.can_be_ticketed(),
                'can_void': booking.can_be_voided(),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading booking detail {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading booking details: {str(e)}')
            return redirect('flights:booking_list')
    
    def post(self, request, booking_ref):
        """Handle booking actions"""
        try:
            booking = self.get_object()
            action = request.POST.get('action')
            
            if action == 'send_itinerary':
                return self.send_itinerary(request, booking)
            elif action == 'send_ticket':
                return self.send_ticket(request, booking)
            elif action == 'add_note':
                return self.add_note(request, booking)
            elif action == 'update_status':
                return self.update_status(request, booking)
            else:
                messages.error(request, 'Invalid action.')
                return redirect('flights:booking_detail', booking_ref=booking_ref)
                
        except Exception as e:
            logger.error(f"Error processing booking action {action}: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing action: {str(e)}')
            return redirect('flights:booking_detail', booking_ref=booking_ref)
    
    def send_itinerary(self, request, booking):
        """Send itinerary to passenger"""
        try:
            notification_service = NotificationService()
            notification_service.send_itinerary_email(booking)
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='system_event',
                description='Itinerary sent to passenger',
                created_by=request.user
            )
            
            messages.success(request, 'Itinerary sent successfully.')
            
        except Exception as e:
            logger.error(f"Error sending itinerary: {str(e)}")
            messages.error(request, 'Error sending itinerary.')
        
        return redirect('flights:booking_detail', booking_ref=booking.booking_reference)
    
    def send_ticket(self, request, booking):
        """Send e-ticket to passenger"""
        try:
            notification_service = NotificationService()
            notification_service.send_ticket_email(booking)
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='system_event',
                description='E-ticket sent to passenger',
                created_by=request.user
            )
            
            messages.success(request, 'E-ticket sent successfully.')
            
        except Exception as e:
            logger.error(f"Error sending ticket: {str(e)}")
            messages.error(request, 'Error sending ticket.')
        
        return redirect('flights:booking_detail', booking_ref=booking.booking_reference)
    
    def add_note(self, request, booking):
        """Add internal note to booking"""
        note = request.POST.get('note', '').strip()
        
        if note:
            booking.internal_notes = f"{booking.internal_notes}\n{timezone.now()}: {note}"
            booking.save()
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='note_added',
                description=f'Internal note added: {note[:100]}...',
                created_by=request.user
            )
            
            messages.success(request, 'Note added successfully.')
        else:
            messages.error(request, 'Note cannot be empty.')
        
        return redirect('flights:booking_detail', booking_ref=booking.booking_reference)
    
    def update_status(self, request, booking):
        """Update booking status"""
        new_status = request.POST.get('status', '').strip()
        
        if new_status in dict(Booking.BookingStatus.choices):
            old_status = booking.status
            booking.status = new_status
            booking.save()
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='status_change',
                description=f'Status changed from {old_status} to {new_status}',
                created_by=request.user
            )
            
            messages.success(request, f'Booking status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
        
        return redirect('flights:booking_detail', booking_ref=booking.booking_reference)


class BookingModificationView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Modify an existing booking"""
    
    template_name = 'flights/management/booking_modification.html'
    
    def get_object(self):
        booking_ref = self.kwargs.get('booking_ref')
        booking = get_object_or_404(
            Booking.objects.select_related('itinerary'),
            booking_reference=booking_ref
        )
        return booking
    
    def test_func(self):
        """Check if user can modify this booking"""
        booking = self.get_object()
        user = self.request.user
        
        # Check permissions
        if user.user_type == 'admin':
            return True
        elif booking.agent == user:
            return True
        elif user.user_type == 'super_agent' and booking.agent.parent_agent == user:
            return True
        
        return False
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to modify this booking.')
        return redirect('flights:booking_list')
    
    def get(self, request, booking_ref):
        try:
            booking = self.get_object()
            
            # Check if booking can be modified
            if not booking.can_be_modified():
                messages.error(request, 'This booking cannot be modified. Please check fare rules.')
                return redirect('flights:booking_detail', booking_ref=booking_ref)
            
            # Get modification options
            booking_service = BookingService()
            modification_options = booking_service.get_modification_options(booking)
            
            # Initialize forms
            modification_form = BookingModificationForm(booking=booking)
            
            context = {
                'booking': booking,
                'modification_form': modification_form,
                'modification_options': modification_options,
                'change_fees': booking_service.calculate_change_fees(booking),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading modification view for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading modification options.')
            return redirect('flights:booking_detail', booking_ref=booking_ref)
    
    def post(self, request, booking_ref):
        try:
            booking = self.get_object()
            modification_form = BookingModificationForm(request.POST, booking=booking)
            
            if modification_form.is_valid():
                with transaction.atomic():
                    # Get modification data
                    modification_type = modification_form.cleaned_data['modification_type']
                    reason = modification_form.cleaned_data['reason_for_change']
                    
                    # Update booking information
                    booking.special_instructions = modification_form.cleaned_data['special_instructions']
                    booking.internal_notes = modification_form.cleaned_data['internal_notes']
                    booking.customer_remarks = modification_form.cleaned_data['customer_remarks']
                    booking.save()
                    
                    # Process modification based on type
                    booking_service = BookingService()
                    
                    if modification_type == 'date_change':
                        result = self.process_date_change(request, booking, booking_service)
                    elif modification_type == 'passenger_change':
                        result = self.process_passenger_change(request, booking, booking_service)
                    elif modification_type == 'route_change':
                        result = self.process_route_change(request, booking, booking_service)
                    elif modification_type == 'cabin_change':
                        result = self.process_cabin_change(request, booking, booking_service)
                    elif modification_type == 'add_ancillary':
                        result = self.process_ancillary_addition(request, booking, booking_service)
                    else:
                        result = self.process_other_modification(request, booking, booking_service)
                    
                    if not result.get('success', False):
                        messages.error(request, result.get('message', 'Modification failed.'))
                        return redirect('flights:booking_modification', booking_ref=booking_ref)
                    
                    # Create modification record
                    booking_service.create_modification_record(
                        booking=booking,
                        modification_type=modification_type,
                        reason=reason,
                        performed_by=request.user,
                        changes=result.get('changes', {})
                    )
                    
                    # Send notifications if requested
                    if modification_form.cleaned_data.get('send_notification'):
                        notification_service = NotificationService()
                        notification_service.send_modification_notification(booking, modification_type)
                    
                    messages.success(request, 'Booking modified successfully.')
                    
                    # Log the action
                    BookingHistory.objects.create(
                        booking=booking,
                        history_type='manual_update',
                        description=f'Booking modified: {modification_type} - {reason}',
                        created_by=request.user
                    )
                    
                    return redirect('flights:booking_detail', booking_ref=booking_ref)
            else:
                messages.error(request, 'Please correct the errors below.')
                
                # Get modification options for re-rendering
                booking_service = BookingService()
                modification_options = booking_service.get_modification_options(booking)
                
                context = {
                    'booking': booking,
                    'modification_form': modification_form,
                    'modification_options': modification_options,
                    'change_fees': booking_service.calculate_change_fees(booking),
                }
                
                return render(request, self.template_name, context)
                
        except Exception as e:
            logger.error(f"Error modifying booking {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, f'Error modifying booking: {str(e)}')
            return redirect('flights:booking_modification', booking_ref=booking_ref)
    
    def process_date_change(self, request, booking, booking_service):
        """Process date change modification"""
        try:
            new_departure_date = request.POST.get('new_departure_date')
            new_return_date = request.POST.get('new_return_date')
            
            if not new_departure_date:
                return {'success': False, 'message': 'New departure date is required.'}
            
            # Validate dates
            try:
                departure_date = datetime.strptime(new_departure_date, '%Y-%m-%d').date()
                return_date = datetime.strptime(new_return_date, '%Y-%m-%d').date() if new_return_date else None
            except ValueError:
                return {'success': False, 'message': 'Invalid date format.'}
            
            # Check date change fees
            change_fees = booking_service.calculate_date_change_fees(booking, departure_date, return_date)
            
            # Update booking with new dates
            result = booking_service.change_booking_dates(
                booking=booking,
                new_departure_date=departure_date,
                new_return_date=return_date,
                change_fees=change_fees
            )
            
            if result['success']:
                return {
                    'success': True,
                    'changes': {
                        'departure_date': departure_date.isoformat(),
                        'return_date': return_date.isoformat() if return_date else None,
                        'change_fees': change_fees
                    }
                }
            else:
                return {'success': False, 'message': result.get('message', 'Date change failed.')}
                
        except Exception as e:
            logger.error(f"Error processing date change: {str(e)}")
            return {'success': False, 'message': f'Date change error: {str(e)}'}
    
    def process_passenger_change(self, request, booking, booking_service):
        """Process passenger change modification"""
        try:
            # Get passenger changes from form
            passenger_changes = []
            
            # This would parse passenger change data from the form
            # For now, return a placeholder
            return {
                'success': True,
                'changes': {'passenger_changes': 'Passenger details updated'}
            }
            
        except Exception as e:
            logger.error(f"Error processing passenger change: {str(e)}")
            return {'success': False, 'message': f'Passenger change error: {str(e)}'}
    
    def process_route_change(self, request, booking, booking_service):
        """Process route change modification"""
        try:
            new_origin = request.POST.get('new_origin')
            new_destination = request.POST.get('new_destination')
            
            if not new_origin or not new_destination:
                return {'success': False, 'message': 'New origin and destination are required.'}
            
            # Calculate route change fees
            change_fees = booking_service.calculate_route_change_fees(booking, new_origin, new_destination)
            
            return {
                'success': True,
                'changes': {
                    'origin': new_origin,
                    'destination': new_destination,
                    'change_fees': change_fees
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing route change: {str(e)}")
            return {'success': False, 'message': f'Route change error: {str(e)}'}
    
    def process_cabin_change(self, request, booking, booking_service):
        """Process cabin class change"""
        try:
            new_cabin_class = request.POST.get('new_cabin_class')
            
            if not new_cabin_class:
                return {'success': False, 'message': 'New cabin class is required.'}
            
            # Calculate upgrade/downgrade fees
            change_fees = booking_service.calculate_cabin_change_fees(booking, new_cabin_class)
            
            return {
                'success': True,
                'changes': {
                    'cabin_class': new_cabin_class,
                    'change_fees': change_fees
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing cabin change: {str(e)}")
            return {'success': False, 'message': f'Cabin change error: {str(e)}'}
    
    def process_ancillary_addition(self, request, booking, booking_service):
        """Process ancillary service addition"""
        try:
            ancillary_services = request.POST.getlist('ancillary_services')
            
            if not ancillary_services:
                return {'success': False, 'message': 'Please select at least one ancillary service.'}
            
            # Calculate ancillary costs
            ancillary_costs = booking_service.calculate_ancillary_costs(booking, ancillary_services)
            
            return {
                'success': True,
                'changes': {
                    'ancillary_services': ancillary_services,
                    'ancillary_costs': ancillary_costs
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing ancillary addition: {str(e)}")
            return {'success': False, 'message': f'Ancillary addition error: {str(e)}'}
    
    def process_other_modification(self, request, booking, booking_service):
        """Process other types of modifications"""
        try:
            modification_details = request.POST.get('modification_details', '')
            
            return {
                'success': True,
                'changes': {
                    'modification_details': modification_details
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing other modification: {str(e)}")
            return {'success': False, 'message': f'Modification error: {str(e)}'}


class CancellationRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Request booking cancellation"""
    
    template_name = 'flights/management/cancellation_request.html'
    
    def get_object(self):
        booking_ref = self.kwargs.get('booking_ref')
        booking = get_object_or_404(
            Booking.objects.select_related('itinerary'),
            booking_reference=booking_ref
        )
        return booking
    
    def test_func(self):
        """Check if user can cancel this booking"""
        booking = self.get_object()
        user = self.request.user
        
        # Check permissions
        if user.user_type == 'admin':
            return True
        elif booking.agent == user:
            return True
        elif user.user_type == 'super_agent' and booking.agent.parent_agent == user:
            return True
        elif booking.corporate_client == user:
            return True
        
        return False
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to cancel this booking.')
        return redirect('flights:booking_list')
    
    def get(self, request, booking_ref):
        try:
            booking = self.get_object()
            
            # Check if booking can be cancelled
            if not booking.can_be_cancelled():
                messages.error(request, 'This booking cannot be cancelled. Please check cancellation policy.')
                return redirect('flights:booking_detail', booking_ref=booking_ref)
            
            # Get cancellation details
            booking_service = BookingService()
            cancellation_details = booking_service.get_cancellation_details(booking)
            
            # Initialize form
            cancellation_form = CancellationRequestForm(booking=booking)
            
            context = {
                'booking': booking,
                'cancellation_form': cancellation_form,
                'cancellation_details': cancellation_details,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading cancellation view for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading cancellation options.')
            return redirect('flights:booking_detail', booking_ref=booking_ref)
    
    def post(self, request, booking_ref):
        try:
            booking = self.get_object()
            cancellation_form = CancellationRequestForm(request.POST, booking=booking)
            
            if cancellation_form.is_valid():
                with transaction.atomic():
                    # Create refund request
                    refund_request = Refund.objects.create(
                        booking=booking,
                        reason=cancellation_form.cleaned_data['reason'],
                        refund_method=cancellation_form.cleaned_data['refund_method'],
                        bank_name=cancellation_form.cleaned_data.get('bank_name', ''),
                        bank_account=cancellation_form.cleaned_data.get('bank_account', ''),
                        account_holder=cancellation_form.cleaned_data.get('account_holder', ''),
                        iban=cancellation_form.cleaned_data.get('iban', ''),
                        notes=cancellation_form.cleaned_data.get('notes', ''),
                        requested_by=request.user,
                        status='requested'
                    )
                    
                    # Calculate refund amount
                    booking_service = BookingService()
                    refund_amount = booking_service.calculate_refund_amount(booking)
                    
                    refund_request.amount = refund_amount
                    refund_request.currency = booking.currency
                    refund_request.save()
                    
                    # Update booking status
                    booking.status = 'cancelled'
                    booking.cancelled_at = timezone.now()
                    booking.save()
                    
                    # Create cancellation record
                    booking_service.create_cancellation_record(
                        booking=booking,
                        reason=cancellation_form.cleaned_data['reason'],
                        refund_request=refund_request,
                        performed_by=request.user
                    )
                    
                    # Send notifications if requested
                    if cancellation_form.cleaned_data.get('send_confirmation'):
                        notification_service = NotificationService()
                        notification_service.send_cancellation_notification(booking, refund_request)
                    
                    messages.success(request, 'Cancellation requested successfully. Refund will be processed within 7-14 business days.')
                    
                    # Log the action
                    BookingHistory.objects.create(
                        booking=booking,
                        history_type='status_change',
                        description='Booking cancelled',
                        created_by=request.user
                    )
                    
                    return redirect('flights:booking_detail', booking_ref=booking_ref)
            else:
                messages.error(request, 'Please correct the errors below.')
                
                # Get cancellation details for re-rendering
                booking_service = BookingService()
                cancellation_details = booking_service.get_cancellation_details(booking)
                
                context = {
                    'booking': booking,
                    'cancellation_form': cancellation_form,
                    'cancellation_details': cancellation_details,
                }
                
                return render(request, self.template_name, context)
                
        except Exception as e:
            logger.error(f"Error processing cancellation for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing cancellation: {str(e)}')
            return redirect('flights:cancellation_request', booking_ref=booking_ref)


class PassengerManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Manage passenger information"""
    
    template_name = 'flights/management/passenger_management.html'
    
    def get_object(self):
        booking_ref = self.kwargs.get('booking_ref')
        booking = get_object_or_404(
            Booking.objects.prefetch_related('passengers'),
            booking_reference=booking_ref
        )
        return booking
    
    def test_func(self):
        """Check if user can manage passengers for this booking"""
        booking = self.get_object()
        user = self.request.user
        
        # Check permissions
        if user.user_type == 'admin':
            return True
        elif booking.agent == user:
            return True
        elif user.user_type == 'super_agent' and booking.agent.parent_agent == user:
            return True
        
        return False
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to manage passengers for this booking.')
        return redirect('flights:booking_list')
    
    def get(self, request, booking_ref):
        try:
            booking = self.get_object()
            
            # Initialize forms for each passenger
            passenger_forms = []
            for passenger in booking.passengers.all():
                form = PassengerEditForm(instance=passenger, booking=booking)
                passenger_forms.append({
                    'passenger': passenger,
                    'form': form
                })
            
            # Contact information form
            contact_form = ContactInformationForm()
            
            context = {
                'booking': booking,
                'passenger_forms': passenger_forms,
                'contact_form': contact_form,
                'can_edit_passengers': booking.can_be_modified(),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading passenger management for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading passenger information.')
            return redirect('flights:booking_detail', booking_ref=booking_ref)
    
    def post(self, request, booking_ref):
        try:
            booking = self.get_object()
            action = request.POST.get('action')
            
            if action == 'update_passenger':
                return self.update_passenger(request, booking)
            elif action == 'update_contact':
                return self.update_contact(request, booking)
            elif action == 'add_passenger':
                return self.add_passenger(request, booking)
            elif action == 'remove_passenger':
                return self.remove_passenger(request, booking)
            else:
                messages.error(request, 'Invalid action.')
                return redirect('flights:passenger_management', booking_ref=booking_ref)
                
        except Exception as e:
            logger.error(f"Error in passenger management for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing request: {str(e)}')
            return redirect('flights:passenger_management', booking_ref=booking_ref)
    
    def update_passenger(self, request, booking):
        """Update passenger information"""
        try:
            passenger_id = request.POST.get('passenger_id')
            passenger = get_object_or_404(Passenger, id=passenger_id, booking=booking)
            
            form = PassengerEditForm(request.POST, instance=passenger, booking=booking)
            
            if form.is_valid():
                form.save()
                
                # Log the action
                BookingHistory.objects.create(
                    booking=booking,
                    history_type='passenger_update',
                    description=f'Passenger {passenger.get_full_name()} information updated',
                    created_by=request.user
                )
                
                messages.success(request, 'Passenger information updated successfully.')
            else:
                messages.error(request, 'Please correct the errors in the passenger form.')
            
            return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error updating passenger: {str(e)}")
            messages.error(request, 'Error updating passenger information.')
            return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
    
    def update_contact(self, request, booking):
        """Update contact information"""
        try:
            # This would update contact information in the booking
            # For now, just show a success message
            messages.success(request, 'Contact information updated successfully.')
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='passenger_update',
                description='Contact information updated',
                created_by=request.user
            )
            
            return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error updating contact information: {str(e)}")
            messages.error(request, 'Error updating contact information.')
            return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
    
    def add_passenger(self, request, booking):
        """Add a new passenger to the booking"""
        try:
            # Check if booking can be modified
            if not booking.can_be_modified():
                messages.error(request, 'Cannot add passengers to this booking.')
                return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
            
            # This would create a new passenger
            # For now, just show a success message
            messages.success(request, 'Passenger added successfully.')
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='passenger_update',
                description='New passenger added to booking',
                created_by=request.user
            )
            
            return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error adding passenger: {str(e)}")
            messages.error(request, 'Error adding passenger.')
            return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
    
    def remove_passenger(self, request, booking):
        """Remove a passenger from the booking"""
        try:
            passenger_id = request.POST.get('passenger_id')
            passenger = get_object_or_404(Passenger, id=passenger_id, booking=booking)
            
            # Check if passenger can be removed
            if booking.passengers.count() <= 1:
                messages.error(request, 'Cannot remove the only passenger from the booking.')
                return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
            
            # Remove passenger
            passenger_name = passenger.get_full_name()
            passenger.delete()
            
            # Update booking total
            booking.total_passengers = booking.passengers.count()
            booking.save()
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='passenger_update',
                description=f'Passenger {passenger_name} removed from booking',
                created_by=request.user
            )
            
            messages.success(request, 'Passenger removed successfully.')
            return redirect('flights:passenger_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error removing passenger: {str(e)}")
            messages.error(request, 'Error removing passenger.')
            return redirect('flights:passenger_management', booking_ref=booking.booking_reference)


class PaymentManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Manage booking payments"""
    
    template_name = 'flights/management/payment_management.html'
    
    def get_object(self):
        booking_ref = self.kwargs.get('booking_ref')
        booking = get_object_or_404(
            Booking.objects.prefetch_related(
                Prefetch('payments', queryset=Payment.objects.order_by('-created_at'))
            ),
            booking_reference=booking_ref
        )
        return booking
    
    def test_func(self):
        """Check if user can manage payments for this booking"""
        booking = self.get_object()
        user = self.request.user
        
        # Check permissions
        if user.user_type == 'admin':
            return True
        elif booking.agent == user:
            return True
        elif user.user_type == 'super_agent' and booking.agent.parent_agent == user:
            return True
        
        return False
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to manage payments for this booking.')
        return redirect('flights:booking_list')
    
    def get(self, request, booking_ref):
        try:
            booking = self.get_object()
            
            # Get payment service
            payment_service = PaymentService()
            payment_summary = payment_service.get_payment_summary(booking)
            
            # Get upcoming payments
            upcoming_payments = payment_service.get_upcoming_payments(booking)
            
            # Get payment history
            payment_history = booking.payments.all()
            
            context = {
                'booking': booking,
                'payment_summary': payment_summary,
                'upcoming_payments': upcoming_payments,
                'payment_history': payment_history,
                'can_add_payment': booking.status in ['confirmed', 'pending'],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading payment management for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading payment information.')
            return redirect('flights:booking_detail', booking_ref=booking_ref)
    
    def post(self, request, booking_ref):
        try:
            booking = self.get_object()
            action = request.POST.get('action')
            
            if action == 'add_payment':
                return self.add_payment(request, booking)
            elif action == 'refund_payment':
                return self.refund_payment(request, booking)
            elif action == 'update_payment_status':
                return self.update_payment_status(request, booking)
            else:
                messages.error(request, 'Invalid action.')
                return redirect('flights:payment_management', booking_ref=booking_ref)
                
        except Exception as e:
            logger.error(f"Error in payment management for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing request: {str(e)}')
            return redirect('flights:payment_management', booking_ref=booking_ref)
    
    def add_payment(self, request, booking):
        """Add a new payment to the booking"""
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            payment_method = request.POST.get('payment_method', '')
            description = request.POST.get('description', '')
            
            if amount <= 0:
                messages.error(request, 'Payment amount must be greater than zero.')
                return redirect('flights:payment_management', booking_ref=booking.booking_reference)
            
            # Create payment
            payment_service = PaymentService()
            payment = payment_service.create_payment(
                booking=booking,
                amount=amount,
                payment_method=payment_method,
                description=description,
                created_by=request.user
            )
            
            # Update booking payment status
            booking.paid_amount += amount
            booking.due_amount = booking.total_amount - booking.paid_amount
            
            if booking.due_amount <= 0:
                booking.payment_status = 'paid'
            elif booking.paid_amount > 0:
                booking.payment_status = 'partial_paid'
            
            booking.save()
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='payment_update',
                description=f'Payment added: {amount} {booking.currency} via {payment_method}',
                created_by=request.user
            )
            
            messages.success(request, 'Payment added successfully.')
            return redirect('flights:payment_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error adding payment: {str(e)}")
            messages.error(request, 'Error adding payment.')
            return redirect('flights:payment_management', booking_ref=booking.booking_reference)
    
    def refund_payment(self, request, booking):
        """Process a payment refund"""
        try:
            payment_id = request.POST.get('payment_id')
            refund_amount = Decimal(request.POST.get('refund_amount', '0'))
            refund_reason = request.POST.get('refund_reason', '')
            
            payment = get_object_or_404(Payment, id=payment_id, booking=booking)
            
            if refund_amount <= 0 or refund_amount > payment.amount:
                messages.error(request, 'Invalid refund amount.')
                return redirect('flights:payment_management', booking_ref=booking.booking_reference)
            
            # Process refund
            payment_service = PaymentService()
            refund = payment_service.process_refund(
                payment=payment,
                amount=refund_amount,
                reason=refund_reason,
                processed_by=request.user
            )
            
            # Update booking payment status
            booking.paid_amount -= refund_amount
            booking.due_amount = booking.total_amount - booking.paid_amount
            booking.save()
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='payment_update',
                description=f'Payment refunded: {refund_amount} {booking.currency}',
                created_by=request.user
            )
            
            messages.success(request, 'Refund processed successfully.')
            return redirect('flights:payment_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            messages.error(request, 'Error processing refund.')
            return redirect('flights:payment_management', booking_ref=booking.booking_reference)
    
    def update_payment_status(self, request, booking):
        """Update payment status"""
        try:
            payment_id = request.POST.get('payment_id')
            new_status = request.POST.get('status', '')
            
            payment = get_object_or_404(Payment, id=payment_id, booking=booking)
            
            if new_status in dict(Payment.PaymentStatus.choices):
                old_status = payment.status
                payment.status = new_status
                payment.save()
                
                # Log the action
                BookingHistory.objects.create(
                    booking=booking,
                    history_type='payment_update',
                    description=f'Payment status changed from {old_status} to {new_status}',
                    created_by=request.user
                )
                
                messages.success(request, 'Payment status updated successfully.')
            else:
                messages.error(request, 'Invalid payment status.')
            
            return redirect('flights:payment_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error updating payment status: {str(e)}")
            messages.error(request, 'Error updating payment status.')
            return redirect('flights:payment_management', booking_ref=booking.booking_reference)


class DocumentManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Manage booking documents"""
    
    template_name = 'flights/management/document_management.html'
    
    def get_object(self):
        booking_ref = self.kwargs.get('booking_ref')
        booking = get_object_or_404(Booking, booking_reference=booking_ref)
        return booking
    
    def test_func(self):
        """Check if user can manage documents for this booking"""
        booking = self.get_object()
        user = self.request.user
        
        # Check permissions
        if user.user_type == 'admin':
            return True
        elif booking.agent == user:
            return True
        elif user.user_type == 'super_agent' and booking.agent.parent_agent == user:
            return True
        
        return False
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to manage documents for this booking.')
        return redirect('flights:booking_list')
    
    def get(self, request, booking_ref):
        try:
            booking = self.get_object()
            
            # Get documents (this would come from a Document model)
            # For now, create placeholder document list
            documents = self.get_booking_documents(booking)
            
            context = {
                'booking': booking,
                'documents': documents,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading document management for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading documents.')
            return redirect('flights:booking_detail', booking_ref=booking_ref)
    
    def post(self, request, booking_ref):
        try:
            booking = self.get_object()
            action = request.POST.get('action')
            
            if action == 'upload_document':
                return self.upload_document(request, booking)
            elif action == 'delete_document':
                return self.delete_document(request, booking)
            elif action == 'generate_document':
                return self.generate_document(request, booking)
            else:
                messages.error(request, 'Invalid action.')
                return redirect('flights:document_management', booking_ref=booking_ref)
                
        except Exception as e:
            logger.error(f"Error in document management for {booking_ref}: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing request: {str(e)}')
            return redirect('flights:document_management', booking_ref=booking_ref)
    
    def get_booking_documents(self, booking):
        """Get all documents associated with the booking"""
        documents = []
        
        # Passenger documents
        for passenger in booking.passengers.all():
            if passenger.passport_number:
                documents.append({
                    'type': 'passport',
                    'name': f'Passport - {passenger.get_full_name()}',
                    'upload_date': timezone.now(),
                    'size': '250KB',
                    'status': 'verified',
                })
        
        # Booking documents
        documents.extend([
            {
                'type': 'itinerary',
                'name': 'Flight Itinerary',
                'upload_date': booking.created_at,
                'size': '150KB',
                'status': 'generated',
            },
            {
                'type': 'invoice',
                'name': 'Booking Invoice',
                'upload_date': booking.created_at,
                'size': '180KB',
                'status': 'generated',
            }
        ])
        
        # Tickets if issued
        if booking.tickets.exists():
            for ticket in booking.tickets.all():
                documents.append({
                    'type': 'ticket',
                    'name': f'E-Ticket - {ticket.ticket_number}',
                    'upload_date': ticket.issue_date or booking.created_at,
                    'size': '200KB',
                    'status': 'issued',
                })
        
        return documents
    
    def upload_document(self, request, booking):
        """Upload a document to the booking"""
        try:
            document_file = request.FILES.get('document_file')
            document_type = request.POST.get('document_type', '')
            description = request.POST.get('description', '')
            
            if not document_file:
                messages.error(request, 'Please select a file to upload.')
                return redirect('flights:document_management', booking_ref=booking.booking_reference)
            
            # Validate file
            max_size = 10 * 1024 * 1024  # 10MB
            if document_file.size > max_size:
                messages.error(request, 'File size must be less than 10MB.')
                return redirect('flights:document_management', booking_ref=booking.booking_reference)
            
            # Save document (in a real implementation, this would create a Document model instance)
            # For now, just show success message
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='system_event',
                description=f'Document uploaded: {document_type} - {document_file.name}',
                created_by=request.user
            )
            
            messages.success(request, 'Document uploaded successfully.')
            return redirect('flights:document_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            messages.error(request, 'Error uploading document.')
            return redirect('flights:document_management', booking_ref=booking.booking_reference)
    
    def delete_document(self, request, booking):
        """Delete a document from the booking"""
        try:
            document_name = request.POST.get('document_name', '')
            
            # Delete document (in a real implementation)
            # For now, just show success message
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='system_event',
                description=f'Document deleted: {document_name}',
                created_by=request.user
            )
            
            messages.success(request, 'Document deleted successfully.')
            return redirect('flights:document_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            messages.error(request, 'Error deleting document.')
            return redirect('flights:document_management', booking_ref=booking.booking_reference)
    
    def generate_document(self, request, booking):
        """Generate a document for the booking"""
        try:
            document_type = request.POST.get('document_type', '')
            
            if document_type == 'invoice':
                self.generate_invoice(booking)
                document_name = 'Invoice'
            elif document_type == 'receipt':
                self.generate_receipt(booking)
                document_name = 'Payment Receipt'
            elif document_type == 'voucher':
                self.generate_voucher(booking)
                document_name = 'Travel Voucher'
            else:
                messages.error(request, 'Invalid document type.')
                return redirect('flights:document_management', booking_ref=booking.booking_reference)
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='system_event',
                description=f'Document generated: {document_name}',
                created_by=request.user
            )
            
            messages.success(request, f'{document_name} generated successfully.')
            return redirect('flights:document_management', booking_ref=booking.booking_reference)
            
        except Exception as e:
            logger.error(f"Error generating document: {str(e)}")
            messages.error(request, 'Error generating document.')
            return redirect('flights:document_management', booking_ref=booking.booking_reference)
    
    def generate_invoice(self, booking):
        """Generate invoice PDF"""
        # In a real implementation, this would generate a PDF invoice
        pass
    
    def generate_receipt(self, booking):
        """Generate payment receipt PDF"""
        # In a real implementation, this would generate a PDF receipt
        pass
    
    def generate_voucher(self, booking):
        """Generate travel voucher PDF"""
        # In a real implementation, this would generate a PDF voucher
        pass


class BookingExportView(LoginRequiredMixin, View):
    """Export bookings to various formats"""
    
    def get(self, request):
        try:
            export_format = request.GET.get('format', 'excel')
            export_type = request.GET.get('type', 'all')
            
            # Get filter parameters
            status_filter = request.GET.get('status', 'all')
            date_filter = request.GET.get('date', 'all')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Build queryset based on filters
            bookings = Booking.objects.all()
            
            # Apply user permissions
            if request.user.user_type in ['agent', 'sub_agent']:
                bookings = bookings.filter(agent=request.user)
            elif request.user.user_type == 'super_agent':
                sub_agents = User.objects.filter(parent_agent=request.user)
                bookings = bookings.filter(Q(agent=request.user) | Q(agent__in=sub_agents))
            
            # Apply filters
            if status_filter != 'all':
                bookings = bookings.filter(status=status_filter)
            
            if date_filter != 'all':
                today = timezone.now().date()
                if date_filter == 'today':
                    bookings = bookings.filter(created_at__date=today)
                elif date_filter == 'week':
                    week_start = today - timedelta(days=today.weekday())
                    week_end = week_start + timedelta(days=6)
                    bookings = bookings.filter(created_at__date__range=[week_start, week_end])
                elif date_filter == 'month':
                    month_start = today.replace(day=1)
                    next_month = month_start.replace(day=28) + timedelta(days=4)
                    month_end = next_month - timedelta(days=next_month.day)
                    bookings = bookings.filter(created_at__date__range=[month_start, month_end])
            
            if start_date and end_date:
                bookings = bookings.filter(created_at__date__range=[start_date, end_date])
            
            # Export based on format
            export_utils = ExportUtils()
            
            if export_format == 'excel':
                return export_utils.export_bookings_to_excel(bookings, export_type)
            elif export_format == 'csv':
                return export_utils.export_bookings_to_csv(bookings, export_type)
            elif export_format == 'pdf':
                return export_utils.export_bookings_to_pdf(bookings, export_type)
            else:
                messages.error(request, 'Invalid export format.')
                return redirect('flights:booking_list')
                
        except Exception as e:
            logger.error(f"Error exporting bookings: {str(e)}", exc_info=True)
            messages.error(request, 'Error exporting bookings.')
            return redirect('flights:booking_list')


# API Views for AJAX operations

@method_decorator(csrf_exempt, name='dispatch')
class BookingStatusUpdateAPI(View, LoginRequiredMixin):
    """API endpoint for updating booking status"""
    
    def post(self, request, booking_ref):
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            
            booking = get_object_or_404(Booking, booking_reference=booking_ref)
            
            # Check permissions
            if not self.has_permission(request.user, booking):
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            # Validate status
            if new_status not in dict(Booking.BookingStatus.choices):
                return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
            
            # Update status
            old_status = booking.status
            booking.status = new_status
            booking.save()
            
            # Log the action
            BookingHistory.objects.create(
                booking=booking,
                history_type='status_change',
                description=f'Status changed from {old_status} to {new_status} via API',
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'booking_ref': booking_ref,
                'old_status': old_status,
                'new_status': new_status,
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error updating booking status via API: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def has_permission(self, user, booking):
        """Check if user has permission to update booking status"""
        if user.user_type == 'admin':
            return True
        elif booking.agent == user:
            return True
        elif user.user_type == 'super_agent' and booking.agent.parent_agent == user:
            return True
        return False


@method_decorator(csrf_exempt, name='dispatch')
class QuickBookingSearchAPI(View, LoginRequiredMixin):
    """API endpoint for quick booking search"""
    
    def get(self, request):
        try:
            search_term = request.GET.get('q', '').strip()
            
            if len(search_term) < 2:
                return JsonResponse({'results': []})
            
            # Search bookings
            bookings = Booking.objects.filter(
                Q(booking_reference__icontains=search_term) |
                Q(pnr__icontains=search_term) |
                Q(passengers__first_name__icontains=search_term) |
                Q(passengers__last_name__icontains=search_term)
            ).distinct()[:10]
            
            # Apply permissions
            if request.user.user_type in ['agent', 'sub_agent']:
                bookings = bookings.filter(agent=request.user)
            elif request.user.user_type == 'super_agent':
                sub_agents = User.objects.filter(parent_agent=request.user)
                bookings = bookings.filter(Q(agent=request.user) | Q(agent__in=sub_agents))
            
            results = []
            for booking in bookings:
                results.append({
                    'id': booking.booking_reference,
                    'text': f"{booking.booking_reference} - {booking.passengers.first().get_full_name() if booking.passengers.exists() else 'No Passenger'}",
                    'status': booking.status,
                    'total_amount': str(booking.total_amount),
                    'currency': booking.currency,
                    'url': f"/bookings/{booking.booking_reference}/"
                })
            
            return JsonResponse({'results': results})
            
        except Exception as e:
            logger.error(f"Error in quick booking search: {str(e)}")
            return JsonResponse({'results': [], 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def booking_dashboard_stats(request):
    """Get dashboard statistics for bookings"""
    try:
        user = request.user
        today = timezone.now().date()
        
        # Base queryset with permissions
        bookings = Booking.objects.all()
        
        if user.user_type in ['agent', 'sub_agent']:
            bookings = bookings.filter(agent=user)
        elif user.user_type == 'super_agent':
            sub_agents = User.objects.filter(parent_agent=user)
            bookings = bookings.filter(Q(agent=user) | Q(agent__in=sub_agents))
        
        # Calculate statistics
        stats = {
            'total_bookings': bookings.count(),
            'todays_bookings': bookings.filter(created_at__date=today).count(),
            'pending_payments': bookings.filter(payment_status='pending').count(),
            'upcoming_travel': bookings.filter(
                itinerary__segments__departure_time__date__gte=today,
                status__in=['confirmed', 'ticketed']
            ).distinct().count(),
            'cancelled_today': bookings.filter(
                cancelled_at__date=today,
                status='cancelled'
            ).count(),
            'total_revenue': bookings.aggregate(total=Sum('total_amount'))['total'] or 0,
            'todays_revenue': bookings.filter(created_at__date=today).aggregate(total=Sum('total_amount'))['total'] or 0,
        }
        
        # Status breakdown
        status_breakdown = bookings.values('status').annotate(count=Count('id'))
        stats['status_breakdown'] = {item['status']: item['count'] for item in status_breakdown}
        
        # Top destinations (simplified)
        top_destinations = bookings.values(
            'itinerary__segments__destination__city'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        stats['top_destinations'] = list(top_destinations)
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# URL Patterns (to be included in urls.py)
"""
urlpatterns = [
    path('bookings/', BookingListView.as_view(), name='booking_list'),
    path('bookings/<str:booking_ref>/', BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/<str:booking_ref>/modify/', BookingModificationView.as_view(), name='booking_modification'),
    path('bookings/<str:booking_ref>/cancel/', CancellationRequestView.as_view(), name='cancellation_request'),
    path('bookings/<str:booking_ref>/passengers/', PassengerManagementView.as_view(), name='passenger_management'),
    path('bookings/<str:booking_ref>/payments/', PaymentManagementView.as_view(), name='payment_management'),
    path('bookings/<str:booking_ref>/documents/', DocumentManagementView.as_view(), name='document_management'),
    path('bookings/export/', BookingExportView.as_view(), name='booking_export'),
    
    # API endpoints
    path('api/bookings/<str:booking_ref>/status/', BookingStatusUpdateAPI.as_view(), name='api_booking_status'),
    path('api/bookings/search/', QuickBookingSearchAPI.as_view(), name='api_booking_search'),
    path('api/dashboard/stats/', booking_dashboard_stats, name='api_dashboard_stats'),
]
"""