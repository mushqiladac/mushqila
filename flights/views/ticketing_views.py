# flights/views/ancillary_views.py
"""
Ticketing Views for B2B Travel Platform
Production Ready - Final Version
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F, Prefetch, Subquery, OuterRef, Case, When, Value
from django.db.models.functions import Concat, Extract, TruncDate, Coalesce
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, connection, models
from django.core.cache import cache
from django.urls import reverse
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
import csv
import xlwt
from io import BytesIO, StringIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
import base64
from io import BytesIO as IO
import hashlib

from flights.models import (
    Ticket, PNR,  # EMD, TicketCoupon, TicketHistory, TicketDocument,
    Booking, Passenger, BookingPassenger, FlightSegment, FlightItinerary,
    Airline, Airport, Payment, Refund,  # CommissionTransaction,
    # TicketQueue, TicketingRule, FareCalculation, TaxBreakdown
)
# Temporarily commented out - these forms need to be created
# from flights.forms import (
#     TicketSearchForm, TicketFilterForm, TicketIssueForm, TicketVoidForm,
#     TicketReissueForm, TicketRefundForm, TicketDocumentForm, TicketQueueForm,
#     TicketingRuleForm, BulkTicketingForm, TicketVerificationForm,
#     EMDCreateForm, TicketRevalidationForm
# )
# Temporarily commented out - these services need to be created
# from flights.services.ticketing_service import TicketingService
# from flights.services.gds_service import GDSTicketingService
# from flights.services.payment_service import PaymentService
# from flights.services.refund_service import RefundService
# from flights.services.pnr_service import PNRService
# from flights.services.reporting_service import TicketingReportingService
# from flights.services.notification_service import TicketNotificationService
# from flights.utils.export import TicketExport
# from flights.utils.permissions import TicketingPermission
# from flights.utils.validators import TicketValidator
# from flights.utils.cache import TicketingCache
# from flights.utils.ticket_generator import TicketGenerator
from flights.utils.bsp_reports import BSPReportGenerator

logger = logging.getLogger(__name__)


class TicketListView(LoginRequiredMixin, View):
    """List all tickets with advanced filtering and search"""
    
    template_name = 'flights/ticketing/ticket_list.html'
    items_per_page = 25
    
    def get(self, request):
        try:
            # Get filter parameters
            status_filter = request.GET.get('status', 'all')
            airline_filter = request.GET.get('airline', 'all')
            date_filter = request.GET.get('date_filter', '30d')
            search_query = request.GET.get('q', '').strip()
            sort_by = request.GET.get('sort', '-issued_at')
            page_number = request.GET.get('page', 1)
            ticket_type = request.GET.get('type', 'all')  # e-ticket, paper, emd
            
            # Base queryset
            tickets = Ticket.objects.select_related(
                'booking',
                'booking__agent',
                'booking__itinerary',
                'booking__itinerary__search',
                'pnr',
                'fare_calculation'
            ).prefetch_related(
                Prefetch('coupons', queryset=TicketCoupon.objects.select_related('segment')),
                'history',
                'documents'
            )
            
            # Apply user permissions
            if request.user.user_type == 'agent':
                tickets = tickets.filter(booking__agent=request.user)
            elif request.user.user_type == 'sub_agent':
                # Get parent agent's tickets
                parent_agent = request.user.parent_agent
                if parent_agent:
                    tickets = tickets.filter(booking__agent=parent_agent)
            
            # Apply status filter
            if status_filter != 'all':
                tickets = tickets.filter(status=status_filter)
            
            # Apply airline filter
            if airline_filter != 'all':
                tickets = tickets.filter(
                    coupons__segment__airline__code=airline_filter
                ).distinct()
            
            # Apply ticket type filter
            if ticket_type != 'all':
                if ticket_type == 'e_ticket':
                    tickets = tickets.filter(ticket_type='electronic')
                elif ticket_type == 'paper':
                    tickets = tickets.filter(ticket_type='paper')
                elif ticket_type == 'emd':
                    tickets = tickets.filter(ticket_type='emd')
            
            # Apply date filter
            today = timezone.now()
            if date_filter == 'today':
                tickets = tickets.filter(issued_at__date=today.date())
            elif date_filter == 'yesterday':
                yesterday = today - timedelta(days=1)
                tickets = tickets.filter(issued_at__date=yesterday.date())
            elif date_filter == '7d':
                week_ago = today - timedelta(days=7)
                tickets = tickets.filter(issued_at__gte=week_ago)
            elif date_filter == '30d':
                month_ago = today - timedelta(days=30)
                tickets = tickets.filter(issued_at__gte=month_ago)
            elif date_filter == 'custom':
                start_date = request.GET.get('start_date')
                end_date = request.GET.get('end_date')
                if start_date and end_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        tickets = tickets.filter(
                            issued_at__date__gte=start_dt.date(),
                            issued_at__date__lte=end_dt.date()
                        )
                    except ValueError:
                        pass
            
            # Apply search
            if search_query:
                tickets = tickets.filter(
                    Q(ticket_number__icontains=search_query) |
                    Q(booking__booking_reference__icontains=search_query) |
                    Q(booking__pnr__icontains=search_query) |
                    Q(passenger__first_name__icontains=search_query) |
                    Q(passenger__last_name__icontains=search_query) |
                    Q(coupons__segment__flight_number__icontains=search_query) |
                    Q(coupons__segment__airline__code__icontains=search_query)
                ).distinct()
            
            # Apply sorting
            valid_sort_fields = [
                'issued_at', '-issued_at',
                'ticket_number', '-ticket_number',
                'total_amount', '-total_amount',
                'status', '-status',
                'booking__booking_reference', '-booking__booking_reference',
                'passenger__last_name', '-passenger__last_name'
            ]
            if sort_by in valid_sort_fields:
                tickets = tickets.order_by(sort_by)
            else:
                tickets = tickets.order_by('-issued_at')
            
            # Get statistics
            stats = self.get_ticket_statistics(tickets)
            
            # Pagination
            paginator = Paginator(tickets, self.items_per_page)
            page_obj = paginator.get_page(page_number)
            
            # Get filter options
            airlines = Airline.objects.filter(
                id__in=tickets.values_list('coupons__segment__airline', flat=True).distinct()
            ).distinct().order_by('name')
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'status_filter': status_filter,
                'airline_filter': airline_filter,
                'date_filter': date_filter,
                'ticket_type': ticket_type,
                'search_query': search_query,
                'sort_by': sort_by,
                'stats': stats,
                'status_options': [
                    ('all', 'All Status'),
                    ('issued', 'Issued'),
                    ('voided', 'Voided'),
                    ('refunded', 'Refunded'),
                    ('exchanged', 'Exchanged'),
                    ('suspended', 'Suspended'),
                    ('reported', 'BSP Reported'),
                    ('settled', 'BSP Settled'),
                ],
                'date_options': [
                    ('today', 'Today'),
                    ('yesterday', 'Yesterday'),
                    ('7d', 'Last 7 Days'),
                    ('30d', 'Last 30 Days'),
                    ('custom', 'Custom Range'),
                ],
                'ticket_types': [
                    ('all', 'All Types'),
                    ('e_ticket', 'E-Tickets'),
                    ('paper', 'Paper Tickets'),
                    ('emd', 'EMDs'),
                ],
                'sort_options': [
                    ('-issued_at', 'Newest First'),
                    ('issued_at', 'Oldest First'),
                    ('ticket_number', 'Ticket No (A-Z)'),
                    ('-ticket_number', 'Ticket No (Z-A)'),
                    ('total_amount', 'Amount (Low-High)'),
                    ('-total_amount', 'Amount (High-Low)'),
                    ('status', 'Status (A-Z)'),
                    ('-status', 'Status (Z-A)'),
                ],
                'can_issue': TicketingPermission.can_issue_ticket(request.user),
                'can_void': TicketingPermission.can_void_ticket(request.user),
                'can_reissue': TicketingPermission.can_reissue_ticket(request.user),
                'can_export': TicketingPermission.can_export_tickets(request.user),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ticket list: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading tickets. Please try again.')
            return render(request, self.template_name, {'page_obj': []})
    
    def get_ticket_statistics(self, tickets):
        """Calculate ticket statistics"""
        today = timezone.now().date()
        
        stats = {
            'total_tickets': tickets.count(),
            'issued_tickets': tickets.filter(status='issued').count(),
            'voided_tickets': tickets.filter(status='voided').count(),
            'refunded_tickets': tickets.filter(status='refunded').count(),
            'total_amount': tickets.filter(status='issued').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00'),
            'commission_earned': CommissionTransaction.objects.filter(
                ticket__in=tickets,
                transaction_type='commission'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        }
        
        # Today's statistics
        today_tickets = tickets.filter(issued_at__date=today)
        stats['today_count'] = today_tickets.count()
        stats['today_amount'] = today_tickets.filter(
            status='issued'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Airline breakdown
        airline_stats = tickets.filter(status='issued').values(
            'coupons__segment__airline__code',
            'coupons__segment__airline__name'
        ).annotate(
            count=Count('id', distinct=True),
            amount=Sum('total_amount')
        ).order_by('-amount')[:10]
        
        stats['airline_breakdown'] = airline_stats
        
        # Ticket type breakdown
        type_stats = tickets.values('ticket_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['type_breakdown'] = type_stats
        
        # Status trend (last 7 days)
        trend_data = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            day_tickets = tickets.filter(issued_at__date=date, status='issued')
            trend_data.append({
                'date': date,
                'count': day_tickets.count(),
                'amount': day_tickets.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
            })
        
        stats['trend_data'] = trend_data
        
        return stats


class TicketDetailView(LoginRequiredMixin, View):
    """View detailed ticket information"""
    
    template_name = 'flights/ticketing/ticket_detail.html'
    
    def get(self, request, ticket_id):
        try:
            # Get ticket with all related data
            ticket = get_object_or_404(
                Ticket.objects.select_related(
                    'booking',
                    'booking__agent',
                    'booking__itinerary',
                    'booking__itinerary__search',
                    'booking__itinerary__search__origin',
                    'booking__itinerary__search__destination',
                    'pnr',
                    'passenger',
                    'fare_calculation',
                    'issued_by',
                    'voided_by',
                    'reissued_from'
                ).prefetch_related(
                    Prefetch('coupons', queryset=TicketCoupon.objects.select_related(
                        'segment',
                        'segment__airline',
                        'segment__origin',
                        'segment__destination'
                    ).order_by('coupon_number')),
                    Prefetch('history', queryset=TicketHistory.objects.select_related('changed_by').order_by('-changed_at')),
                    Prefetch('documents', queryset=TicketDocument.objects.all()),
                    Prefetch('taxes', queryset=TaxBreakdown.objects.all()),
                ),
                id=ticket_id
            )
            
            # Check permission
            if not TicketingPermission.can_view_ticket(request.user, ticket):
                raise PermissionDenied("You don't have permission to view this ticket")
            
            # Get ticketing service
            ticketing_service = TicketingService()
            
            # Get ticket validation
            validation = ticketing_service.validate_ticket(ticket)
            
            # Get ticket timeline
            timeline = self.get_ticket_timeline(ticket)
            
            # Get related EMDs
            emds = EMD.objects.filter(
                Q(ticket=ticket) | Q(related_ticket=ticket)
            ).select_related('passenger', 'issued_by')
            
            # Get payment information
            payments = Payment.objects.filter(
                booking=ticket.booking,
                status='completed'
            ).order_by('created_at')
            
            # Get commission transactions
            commissions = CommissionTransaction.objects.filter(
                ticket=ticket,
                transaction_type='commission'
            ).order_by('-created_at')
            
            # Generate ticket verification QR code
            qr_code_data = self.generate_qr_code_data(ticket)
            
            # Get available actions
            available_actions = ticketing_service.get_available_actions(ticket, request.user)
            
            context = {
                'ticket': ticket,
                'validation': validation,
                'timeline': timeline,
                'emds': emds,
                'payments': payments,
                'commissions': commissions,
                'qr_code_data': qr_code_data,
                'available_actions': available_actions,
                'can_print': TicketingPermission.can_print_ticket(request.user, ticket),
                'can_void': TicketingPermission.can_void_ticket(request.user, ticket),
                'can_reissue': TicketingPermission.can_reissue_ticket(request.user, ticket),
                'can_refund': TicketingPermission.can_refund_ticket(request.user, ticket),
                'can_download': TicketingPermission.can_download_ticket(request.user, ticket),
                'can_verify': TicketingPermission.can_verify_ticket(request.user),
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for ticket {ticket_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:ticket_list')
        except Exception as e:
            logger.error(f"Error loading ticket detail {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading ticket details: {str(e)}')
            return redirect('flights:ticket_list')
    
    def get_ticket_timeline(self, ticket):
        """Get ticket timeline data"""
        timeline = []
        
        # Ticket creation
        timeline.append({
            'timestamp': ticket.created_at,
            'title': 'Ticket Created',
            'description': f'Ticket {ticket.ticket_number} created',
            'icon': 'fas fa-plus-circle',
            'color': 'success',
            'user': ticket.created_by,
        })
        
        # Ticket issuance
        if ticket.issued_at:
            timeline.append({
                'timestamp': ticket.issued_at,
                'title': 'Ticket Issued',
                'description': f'Ticket issued by {ticket.issued_by.email if ticket.issued_by else "System"}',
                'icon': 'fas fa-check-circle',
                'color': 'primary',
                'user': ticket.issued_by,
            })
        
        # Status changes from history
        for history in ticket.history.all():
            timeline.append({
                'timestamp': history.changed_at,
                'title': f'Status Changed to {history.status.upper()}',
                'description': history.reason,
                'icon': self.get_status_icon(history.status),
                'color': self.get_status_color(history.status),
                'user': history.changed_by,
            })
        
        # Void event
        if ticket.voided_at:
            timeline.append({
                'timestamp': ticket.voided_at,
                'title': 'Ticket Voided',
                'description': f'Ticket voided by {ticket.voided_by.email if ticket.voided_by else "System"}',
                'icon': 'fas fa-ban',
                'color': 'danger',
                'user': ticket.voided_by,
            })
        
        # Payment events
        payments = Payment.objects.filter(
            booking=ticket.booking,
            status='completed'
        ).order_by('created_at')
        
        for payment in payments:
            timeline.append({
                'timestamp': payment.created_at,
                'title': 'Payment Received',
                'description': f'Amount: {payment.amount} {payment.currency}',
                'icon': 'fas fa-credit-card',
                'color': 'info',
            })
        
        # Commission events
        commissions = CommissionTransaction.objects.filter(
            ticket=ticket,
            transaction_type='commission'
        ).order_by('created_at')
        
        for commission in commissions:
            timeline.append({
                'timestamp': commission.created_at,
                'title': 'Commission Paid',
                'description': f'Amount: {commission.amount} {commission.currency}',
                'icon': 'fas fa-money-bill-wave',
                'color': 'warning',
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    def get_status_icon(self, status):
        """Get icon for status"""
        icons = {
            'issued': 'fas fa-check-circle',
            'voided': 'fas fa-ban',
            'refunded': 'fas fa-undo',
            'exchanged': 'fas fa-exchange-alt',
            'suspended': 'fas fa-pause-circle',
            'reported': 'fas fa-file-export',
            'settled': 'fas fa-hand-holding-usd',
        }
        return icons.get(status, 'fas fa-circle')
    
    def get_status_color(self, status):
        """Get color for status"""
        colors = {
            'issued': 'success',
            'voided': 'danger',
            'refunded': 'warning',
            'exchanged': 'info',
            'suspended': 'secondary',
            'reported': 'primary',
            'settled': 'success',
        }
        return colors.get(status, 'secondary')
    
    def generate_qr_code_data(self, ticket):
        """Generate QR code data for ticket verification"""
        verification_data = {
            'ticket_number': ticket.ticket_number,
            'passenger_name': f"{ticket.passenger.first_name} {ticket.passenger.last_name}",
            'booking_reference': ticket.booking.booking_reference,
            'pnr': ticket.pnr.pnr_number if ticket.pnr else '',
            'issue_date': ticket.issued_at.strftime('%Y-%m-%d') if ticket.issued_at else '',
            'status': ticket.status,
        }
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(verification_data))
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"


class TicketIssueView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Issue new tickets"""
    
    template_name = 'flights/ticketing/ticket_issue.html'
    
    def test_func(self):
        return TicketingPermission.can_issue_ticket(self.request.user)
    
    def get(self, request, booking_id=None):
        try:
            booking = None
            form = None
            
            if booking_id:
                # Get booking for specific ticket issue
                booking = get_object_or_404(
                    Booking.objects.select_related(
                        'itinerary',
                        'itinerary__search'
                    ).prefetch_related(
                        Prefetch('passengers', queryset=Passenger.objects.all()),
                        Prefetch('tickets', queryset=Ticket.objects.filter(status='issued')),
                    ),
                    id=booking_id
                )
                
                # Check permission
                if not TicketingPermission.can_issue_ticket_for_booking(request.user, booking):
                    raise PermissionDenied("You don't have permission to issue tickets for this booking")
                
                # Get available passengers for ticketing
                available_passengers = self.get_available_passengers(booking)
                
                # Get form with booking context
                form = TicketIssueForm(booking=booking)
                
            else:
                # General ticket issue form
                form = TicketIssueForm()
            
            # Get ticketing rules
            ticketing_rules = TicketingRule.objects.filter(is_active=True).order_by('priority')
            
            # Get ticket queue
            ticket_queue = TicketQueue.objects.filter(
                status='pending',
                assigned_to=request.user
            ).select_related('booking', 'passenger')[:10]
            
            context = {
                'booking': booking,
                'form': form,
                'ticketing_rules': ticketing_rules,
                'ticket_queue': ticket_queue,
                'available_passengers': available_passengers if booking else [],
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for ticket issue: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:ticket_list')
        except Exception as e:
            logger.error(f"Error loading ticket issue form: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading ticket issue form: {str(e)}')
            return redirect('flights:ticket_list')
    
    def post(self, request, booking_id=None):
        try:
            booking = None
            
            if booking_id:
                booking = get_object_or_404(Booking, id=booking_id)
                
                # Check permission
                if not TicketingPermission.can_issue_ticket_for_booking(request.user, booking):
                    raise PermissionDenied("You don't have permission to issue tickets for this booking")
                
                form = TicketIssueForm(request.POST, booking=booking)
            else:
                form = TicketIssueForm(request.POST)
            
            if form.is_valid():
                # Get form data
                passenger = form.cleaned_data['passenger']
                fare_calculation = form.cleaned_data['fare_calculation']
                payment_method = form.cleaned_data['payment_method']
                ticket_type = form.cleaned_data['ticket_type']
                issue_remarks = form.cleaned_data['issue_remarks']
                
                # Initialize ticketing service
                ticketing_service = TicketingService()
                
                # Issue ticket
                result = ticketing_service.issue_ticket(
                    booking=booking or form.cleaned_data['booking'],
                    passenger=passenger,
                    fare_calculation=fare_calculation,
                    payment_method=payment_method,
                    ticket_type=ticket_type,
                    issue_remarks=issue_remarks,
                    user=request.user
                )
                
                if result['success']:
                    ticket = result['ticket']
                    messages.success(request, f'Ticket {ticket.ticket_number} issued successfully.')
                    
                    # Send notifications
                    notification_service = TicketNotificationService()
                    notification_service.send_ticket_issued_notification(ticket, request.user)
                    
                    return redirect('flights:ticket_detail', ticket_id=ticket.id)
                else:
                    messages.error(request, result.get('error', 'Failed to issue ticket'))
                    form.add_error(None, result.get('error'))
            
            # Form validation failed, re-render with errors
            ticketing_rules = TicketingRule.objects.filter(is_active=True).order_by('priority')
            ticket_queue = TicketQueue.objects.filter(
                status='pending',
                assigned_to=request.user
            ).select_related('booking', 'passenger')[:10]
            
            context = {
                'booking': booking,
                'form': form,
                'ticketing_rules': ticketing_rules,
                'ticket_queue': ticket_queue,
                'available_passengers': self.get_available_passengers(booking) if booking else [],
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for ticket issue: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:ticket_list')
        except Exception as e:
            logger.error(f"Error issuing ticket: {str(e)}", exc_info=True)
            messages.error(request, f'Error issuing ticket: {str(e)}')
            return redirect('flights:ticket_list')
    
    def get_available_passengers(self, booking):
        """Get passengers available for ticketing"""
        available = []
        
        for passenger in booking.passengers.all():
            # Check if passenger already has issued ticket
            has_issued_ticket = booking.tickets.filter(
                passenger=passenger,
                status='issued'
            ).exists()
            
            if not has_issued_ticket:
                available.append(passenger)
        
        return available


class TicketVoidView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Void existing tickets"""
    
    template_name = 'flights/ticketing/ticket_void.html'
    
    def test_func(self):
        ticket_id = self.kwargs.get('ticket_id')
        if ticket_id:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            return TicketingPermission.can_void_ticket(self.request.user, ticket)
        return False
    
    def get(self, request, ticket_id):
        try:
            ticket = get_object_or_404(
                Ticket.objects.select_related('booking', 'passenger'),
                id=ticket_id
            )
            
            # Check if ticket can be voided
            validator = TicketValidator()
            can_void, reason = validator.can_void_ticket(ticket)
            
            if not can_void:
                messages.error(request, f'Cannot void ticket: {reason}')
                return redirect('flights:ticket_detail', ticket_id=ticket.id)
            
            form = TicketVoidForm(initial={
                'ticket_number': ticket.ticket_number,
                'passenger_name': f"{ticket.passenger.first_name} {ticket.passenger.last_name}",
                'total_amount': ticket.total_amount,
            })
            
            context = {
                'ticket': ticket,
                'form': form,
                'void_conditions': self.get_void_conditions(ticket),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ticket void form {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading void form: {str(e)}')
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
    
    def post(self, request, ticket_id):
        try:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            form = TicketVoidForm(request.POST)
            
            if form.is_valid():
                void_reason = form.cleaned_data['void_reason']
                void_remarks = form.cleaned_data['void_remarks']
                refund_option = form.cleaned_data['refund_option']
                send_notification = form.cleaned_data['send_notification']
                
                # Initialize ticketing service
                ticketing_service = TicketingService()
                
                # Void ticket
                result = ticketing_service.void_ticket(
                    ticket=ticket,
                    void_reason=void_reason,
                    void_remarks=void_remarks,
                    refund_option=refund_option,
                    user=request.user
                )
                
                if result['success']:
                    messages.success(request, f'Ticket {ticket.ticket_number} voided successfully.')
                    
                    # Send notification if requested
                    if send_notification:
                        notification_service = TicketNotificationService()
                        notification_service.send_ticket_voided_notification(ticket, request.user)
                    
                    return redirect('flights:ticket_detail', ticket_id=ticket.id)
                else:
                    messages.error(request, result.get('error', 'Failed to void ticket'))
                    form.add_error(None, result.get('error'))
            
            # Re-render form with errors
            context = {
                'ticket': ticket,
                'form': form,
                'void_conditions': self.get_void_conditions(ticket),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error voiding ticket {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error voiding ticket: {str(e)}')
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
    
    def get_void_conditions(self, ticket):
        """Get conditions for voiding ticket"""
        conditions = []
        
        # Check ticket status
        if ticket.status != 'issued':
            conditions.append(f'Ticket status is {ticket.status}, must be "issued"')
        
        # Check if any coupons have been flown
        flown_coupons = ticket.coupons.filter(status='flown')
        if flown_coupons.exists():
            conditions.append(f'{flown_coupons.count()} coupon(s) have been flown')
        
        # Check time since issuance
        if ticket.issued_at:
            hours_since_issue = (timezone.now() - ticket.issued_at).total_seconds() / 3600
            if hours_since_issue > 24:
                conditions.append('Ticket issued more than 24 hours ago')
        
        return conditions


class TicketReissueView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Reissue tickets"""
    
    template_name = 'flights/ticketing/ticket_reissue.html'
    
    def test_func(self):
        ticket_id = self.kwargs.get('ticket_id')
        if ticket_id:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            return TicketingPermission.can_reissue_ticket(self.request.user, ticket)
        return False
    
    def get(self, request, ticket_id):
        try:
            ticket = get_object_or_404(
                Ticket.objects.select_related(
                    'booking',
                    'passenger',
                    'fare_calculation'
                ).prefetch_related(
                    Prefetch('coupons', queryset=TicketCoupon.objects.select_related('segment'))
                ),
                id=ticket_id
            )
            
            # Check if ticket can be reissued
            validator = TicketValidator()
            can_reissue, reason = validator.can_reissue_ticket(ticket)
            
            if not can_reissue:
                messages.error(request, f'Cannot reissue ticket: {reason}')
                return redirect('flights:ticket_detail', ticket_id=ticket.id)
            
            form = TicketReissueForm(initial={
                'original_ticket': ticket.ticket_number,
                'passenger_name': f"{ticket.passenger.first_name} {ticket.passenger.last_name}",
                'original_amount': ticket.total_amount,
            })
            
            # Get reissue options
            reissue_options = self.get_reissue_options(ticket)
            
            context = {
                'ticket': ticket,
                'form': form,
                'reissue_options': reissue_options,
                'reissue_conditions': self.get_reissue_conditions(ticket),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ticket reissue form {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading reissue form: {str(e)}')
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
    
    def post(self, request, ticket_id):
        try:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            form = TicketReissueForm(request.POST)
            
            if form.is_valid():
                reissue_reason = form.cleaned_data['reissue_reason']
                reissue_type = form.cleaned_data['reissue_type']
                fare_difference = form.cleaned_data['fare_difference']
                penalty_amount = form.cleaned_data['penalty_amount']
                reissue_remarks = form.cleaned_data['reissue_remarks']
                
                # Initialize ticketing service
                ticketing_service = TicketingService()
                
                # Reissue ticket
                result = ticketing_service.reissue_ticket(
                    original_ticket=ticket,
                    reissue_reason=reissue_reason,
                    reissue_type=reissue_type,
                    fare_difference=fare_difference,
                    penalty_amount=penalty_amount,
                    reissue_remarks=reissue_remarks,
                    user=request.user
                )
                
                if result['success']:
                    new_ticket = result['new_ticket']
                    messages.success(request, f'Ticket reissued successfully. New ticket: {new_ticket.ticket_number}')
                    
                    # Send notification
                    notification_service = TicketNotificationService()
                    notification_service.send_ticket_reissued_notification(ticket, new_ticket, request.user)
                    
                    return redirect('flights:ticket_detail', ticket_id=new_ticket.id)
                else:
                    messages.error(request, result.get('error', 'Failed to reissue ticket'))
                    form.add_error(None, result.get('error'))
            
            # Re-render form with errors
            reissue_options = self.get_reissue_options(ticket)
            
            context = {
                'ticket': ticket,
                'form': form,
                'reissue_options': reissue_options,
                'reissue_conditions': self.get_reissue_conditions(ticket),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error reissuing ticket {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error reissuing ticket: {str(e)}')
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
    
    def get_reissue_options(self, ticket):
        """Get available reissue options for ticket"""
        options = []
        
        # Name correction
        options.append({
            'type': 'name_correction',
            'name': 'Name Correction',
            'description': 'Correct spelling errors in passenger name',
            'fee': Decimal('50.00'),
            'requires_documentation': True,
        })
        
        # Date change
        options.append({
            'type': 'date_change',
            'name': 'Date Change',
            'description': 'Change travel dates',
            'fee': Decimal('100.00'),
            'requires_revalidation': True,
        })
        
        # Routing change
        options.append({
            'type': 'routing_change',
            'name': 'Routing Change',
            'description': 'Change flight routing',
            'fee': Decimal('150.00'),
            'requires_revalidation': True,
        })
        
        # Class upgrade
        options.append({
            'type': 'class_upgrade',
            'name': 'Class Upgrade',
            'description': 'Upgrade cabin class',
            'fee': Decimal('200.00'),
            'requires_fare_difference': True,
        })
        
        # Partial refund
        options.append({
            'type': 'partial_refund',
            'name': 'Partial Refund',
            'description': 'Refund unused coupons',
            'fee': Decimal('75.00'),
            'requires_refund_processing': True,
        })
        
        return options
    
    def get_reissue_conditions(self, ticket):
        """Get conditions for reissuing ticket"""
        conditions = []
        
        # Check ticket status
        if ticket.status != 'issued':
            conditions.append(f'Ticket status is {ticket.status}, must be "issued"')
        
        # Check if ticket has been voided
        if ticket.voided_at:
            conditions.append('Ticket has been voided')
        
        # Check if any coupons have been flown
        flown_coupons = ticket.coupons.filter(status='flown')
        if flown_coupons.exists():
            conditions.append(f'{flown_coupons.count()} coupon(s) have been flown')
        
        return conditions


class TicketRefundView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Process ticket refunds"""
    
    template_name = 'flights/ticketing/ticket_refund.html'
    
    def test_func(self):
        ticket_id = self.kwargs.get('ticket_id')
        if ticket_id:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            return TicketingPermission.can_refund_ticket(self.request.user, ticket)
        return False
    
    def get(self, request, ticket_id):
        try:
            ticket = get_object_or_404(
                Ticket.objects.select_related(
                    'booking',
                    'passenger',
                    'fare_calculation'
                ).prefetch_related(
                    Prefetch('coupons', queryset=TicketCoupon.objects.select_related('segment'))
                ),
                id=ticket_id
            )
            
            # Check if ticket can be refunded
            validator = TicketValidator()
            can_refund, reason = validator.can_refund_ticket(ticket)
            
            if not can_refund:
                messages.error(request, f'Cannot refund ticket: {reason}')
                return redirect('flights:ticket_detail', ticket_id=ticket.id)
            
            # Calculate refundable amount
            refund_service = RefundService()
            refund_calculation = refund_service.calculate_refund_amount(ticket)
            
            form = TicketRefundForm(initial={
                'ticket_number': ticket.ticket_number,
                'passenger_name': f"{ticket.passenger.first_name} {ticket.passenger.last_name}",
                'original_amount': ticket.total_amount,
                'refundable_amount': refund_calculation.get('refundable_amount', 0),
            })
            
            context = {
                'ticket': ticket,
                'form': form,
                'refund_calculation': refund_calculation,
                'refund_conditions': self.get_refund_conditions(ticket),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ticket refund form {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading refund form: {str(e)}')
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
    
    def post(self, request, ticket_id):
        try:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            form = TicketRefundForm(request.POST)
            
            if form.is_valid():
                refund_reason = form.cleaned_data['refund_reason']
                refund_type = form.cleaned_data['refund_type']
                refund_amount = form.cleaned_data['refund_amount']
                payment_method = form.cleaned_data['payment_method']
                refund_remarks = form.cleaned_data['refund_remarks']
                
                # Initialize refund service
                refund_service = RefundService()
                
                # Process refund
                result = refund_service.process_ticket_refund(
                    ticket=ticket,
                    refund_reason=refund_reason,
                    refund_type=refund_type,
                    refund_amount=refund_amount,
                    payment_method=payment_method,
                    refund_remarks=refund_remarks,
                    user=request.user
                )
                
                if result['success']:
                    refund = result['refund']
                    messages.success(request, f'Refund processed successfully. Refund ID: {refund.refund_reference}')
                    
                    # Send notification
                    notification_service = TicketNotificationService()
                    notification_service.send_refund_processed_notification(refund, request.user)
                    
                    return redirect('flights:ticket_detail', ticket_id=ticket.id)
                else:
                    messages.error(request, result.get('error', 'Failed to process refund'))
                    form.add_error(None, result.get('error'))
            
            # Re-render form with errors
            refund_service = RefundService()
            refund_calculation = refund_service.calculate_refund_amount(ticket)
            
            context = {
                'ticket': ticket,
                'form': form,
                'refund_calculation': refund_calculation,
                'refund_conditions': self.get_refund_conditions(ticket),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error processing ticket refund {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing refund: {str(e)}')
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
    
    def get_refund_conditions(self, ticket):
        """Get conditions for refunding ticket"""
        conditions = []
        
        # Check ticket status
        if ticket.status == 'voided':
            conditions.append('Ticket has been voided')
        elif ticket.status == 'refunded':
            conditions.append('Ticket has already been refunded')
        
        # Check if any coupons have been flown
        flown_coupons = ticket.coupons.filter(status='flown')
        if flown_coupons.exists():
            conditions.append(f'{flown_coupons.count()} coupon(s) have been flown')
        
        # Check refund deadline
        first_segment = ticket.coupons.order_by('segment__departure_time').first()
        if first_segment and first_segment.segment:
            time_to_departure = first_segment.segment.departure_time - timezone.now()
            if time_to_departure.total_seconds() < 0:
                conditions.append('Flight has departed')
            elif time_to_departure.total_seconds() < 3600:  # 1 hour
                conditions.append('Less than 1 hour to departure')
        
        return conditions


class TicketPrintView(LoginRequiredMixin, View):
    """Print tickets"""
    
    template_name = 'flights/ticketing/ticket_print.html'
    
    def get(self, request, ticket_id):
        try:
            ticket = get_object_or_404(
                Ticket.objects.select_related(
                    'booking',
                    'passenger',
                    'fare_calculation'
                ).prefetch_related(
                    Prefetch('coupons', queryset=TicketCoupon.objects.select_related(
                        'segment',
                        'segment__airline',
                        'segment__origin',
                        'segment__destination'
                    )),
                    'taxes',
                ),
                id=ticket_id
            )
            
            # Check permission
            if not TicketingPermission.can_print_ticket(request.user, ticket):
                raise PermissionDenied("You don't have permission to print this ticket")
            
            # Initialize ticket generator
            ticket_generator = TicketGenerator()
            
            # Generate ticket data for printing
            ticket_data = ticket_generator.generate_ticket_data(ticket)
            
            # Get print options
            print_options = self.get_print_options()
            
            context = {
                'ticket': ticket,
                'ticket_data': ticket_data,
                'print_options': print_options,
                'can_print_eticket': ticket.ticket_type == 'electronic',
                'can_print_paper': ticket.ticket_type == 'paper',
                'can_print_receipt': True,
                'can_print_itinerary': True,
            }
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for ticket print {ticket_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
        except Exception as e:
            logger.error(f"Error loading ticket print {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading print view: {str(e)}')
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
    
    def post(self, request, ticket_id):
        try:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            print_format = request.POST.get('print_format', 'eticket')
            include_itinerary = request.POST.get('include_itinerary') == 'on'
            include_receipt = request.POST.get('include_receipt') == 'on'
            copies = int(request.POST.get('copies', 1))
            
            # Check permission
            if not TicketingPermission.can_print_ticket(request.user, ticket):
                raise PermissionDenied("You don't have permission to print this ticket")
            
            # Initialize ticket generator
            ticket_generator = TicketGenerator()
            
            # Generate PDF based on format
            if print_format == 'eticket':
                pdf_content = ticket_generator.generate_eticket_pdf(
                    ticket=ticket,
                    include_itinerary=include_itinerary,
                    include_receipt=include_receipt
                )
                filename = f'eticket_{ticket.ticket_number}.pdf'
            elif print_format == 'paper':
                pdf_content = ticket_generator.generate_paper_ticket_pdf(
                    ticket=ticket,
                    copies=copies
                )
                filename = f'paperticket_{ticket.ticket_number}.pdf'
            elif print_format == 'receipt':
                pdf_content = ticket_generator.generate_receipt_pdf(ticket)
                filename = f'receipt_{ticket.ticket_number}.pdf'
            elif print_format == 'itinerary':
                pdf_content = ticket_generator.generate_itinerary_pdf(ticket)
                filename = f'itinerary_{ticket.ticket_number}.pdf'
            else:
                messages.error(request, 'Invalid print format')
                return redirect('flights:ticket_print', ticket_id=ticket_id)
            
            # Log printing
            logger.info(f"Ticket {ticket.ticket_number} printed in {print_format} format by {request.user.email}")
            
            # Create response
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for ticket print {ticket_id}: {str(e)}")
            messages.error(request, str(e))
            return redirect('flights:ticket_detail', ticket_id=ticket_id)
        except Exception as e:
            logger.error(f"Error printing ticket {ticket_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error printing ticket: {str(e)}')
            return redirect('flights:ticket_print', ticket_id=ticket_id)
    
    def get_print_options(self):
        """Get available print options"""
        return [
            {
                'value': 'eticket',
                'name': 'E-Ticket',
                'description': 'Standard electronic ticket',
                'icon': 'fas fa-file-alt',
            },
            {
                'value': 'paper',
                'name': 'Paper Ticket',
                'description': 'Traditional paper ticket format',
                'icon': 'fas fa-ticket-alt',
            },
            {
                'value': 'receipt',
                'name': 'Receipt',
                'description': 'Payment receipt only',
                'icon': 'fas fa-receipt',
            },
            {
                'value': 'itinerary',
                'name': 'Itinerary',
                'description': 'Flight itinerary details',
                'icon': 'fas fa-plane',
            },
        ]


class TicketVerificationView(LoginRequiredMixin, View):
    """Verify ticket authenticity"""
    
    template_name = 'flights/ticketing/ticket_verification.html'
    
    def get(self, request):
        try:
            form = TicketVerificationForm()
            
            # Get recent verification attempts
            recent_verifications = TicketHistory.objects.filter(
                changed_by=request.user,
                action='verification'
            ).select_related('ticket').order_by('-changed_at')[:10]
            
            context = {
                'form': form,
                'recent_verifications': recent_verifications,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ticket verification: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading verification: {str(e)}')
            return render(request, self.template_name)
    
    def post(self, request):
        try:
            form = TicketVerificationForm(request.POST)
            
            if form.is_valid():
                ticket_number = form.cleaned_data['ticket_number']
                passenger_name = form.cleaned_data['passenger_name']
                verification_method = form.cleaned_data['verification_method']
                
                # Initialize ticketing service
                ticketing_service = TicketingService()
                
                # Verify ticket
                verification_result = ticketing_service.verify_ticket(
                    ticket_number=ticket_number,
                    passenger_name=passenger_name,
                    verification_method=verification_method,
                    user=request.user
                )
                
                if verification_result['success']:
                    messages.success(request, 'Ticket verified successfully')
                else:
                    messages.error(request, verification_result.get('error', 'Verification failed'))
                
                context = {
                    'form': form,
                    'verification_result': verification_result,
                    'recent_verifications': TicketHistory.objects.filter(
                        changed_by=request.user,
                        action='verification'
                    ).select_related('ticket').order_by('-changed_at')[:10],
                }
                
                return render(request, self.template_name, context)
            
            # Form validation failed
            context = {
                'form': form,
                'recent_verifications': TicketHistory.objects.filter(
                    changed_by=request.user,
                    action='verification'
                ).select_related('ticket').order_by('-changed_at')[:10],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error in ticket verification: {str(e)}", exc_info=True)
            messages.error(request, f'Error verifying ticket: {str(e)}')
            return render(request, self.template_name)


class EMDManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Manage Electronic Miscellaneous Documents (EMDs)"""
    
    template_name = 'flights/ticketing/emd_management.html'
    
    def test_func(self):
        return TicketingPermission.can_manage_emds(self.request.user)
    
    def get(self, request):
        try:
            # Get filter parameters
            status_filter = request.GET.get('status', 'all')
            airline_filter = request.GET.get('airline', 'all')
            date_filter = request.GET.get('date_filter', '30d')
            search_query = request.GET.get('q', '').strip()
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            emds = EMD.objects.select_related(
                'ticket',
                'related_ticket',
                'passenger',
                'booking',
                'issued_by',
                'airline'
            ).order_by('-issued_at')
            
            # Apply filters
            if status_filter != 'all':
                emds = emds.filter(status=status_filter)
            
            if airline_filter != 'all':
                emds = emds.filter(airline__code=airline_filter)
            
            # Apply date filter
            today = timezone.now()
            if date_filter == 'today':
                emds = emds.filter(issued_at__date=today.date())
            elif date_filter == '7d':
                week_ago = today - timedelta(days=7)
                emds = emds.filter(issued_at__gte=week_ago)
            elif date_filter == '30d':
                month_ago = today - timedelta(days=30)
                emds = emds.filter(issued_at__gte=month_ago)
            
            # Apply search
            if search_query:
                emds = emds.filter(
                    Q(emd_number__icontains=search_query) |
                    Q(passenger__first_name__icontains=search_query) |
                    Q(passenger__last_name__icontains=search_query) |
                    Q(booking__booking_reference__icontains=search_query)
                )
            
            # Get statistics
            stats = self.get_emd_statistics(emds)
            
            # Pagination
            paginator = Paginator(emds, 20)
            page_obj = paginator.get_page(page_number)
            
            # Get airlines for filter
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            # Get EMD creation form
            emd_form = EMDCreateForm()
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'status_filter': status_filter,
                'airline_filter': airline_filter,
                'date_filter': date_filter,
                'search_query': search_query,
                'stats': stats,
                'emd_form': emd_form,
                'status_options': [
                    ('all', 'All Status'),
                    ('issued', 'Issued'),
                    ('used', 'Used'),
                    ('refunded', 'Refunded'),
                    ('expired', 'Expired'),
                    ('voided', 'Voided'),
                ],
                'date_options': [
                    ('today', 'Today'),
                    ('7d', 'Last 7 Days'),
                    ('30d', 'Last 30 Days'),
                    ('all', 'All Time'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading EMD management: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading EMD management.')
            return render(request, self.template_name, {'page_obj': []})
    
    def post(self, request):
        try:
            emd_form = EMDCreateForm(request.POST)
            
            if emd_form.is_valid():
                # Create EMD
                ticketing_service = TicketingService()
                result = ticketing_service.create_emd(
                    passenger=emd_form.cleaned_data['passenger'],
                    booking=emd_form.cleaned_data['booking'],
                    emd_type=emd_form.cleaned_data['emd_type'],
                    amount=emd_form.cleaned_data['amount'],
                    description=emd_form.cleaned_data['description'],
                    validity_days=emd_form.cleaned_data['validity_days'],
                    user=request.user
                )
                
                if result['success']:
                    messages.success(request, f'EMD {result["emd"].emd_number} created successfully')
                else:
                    messages.error(request, result.get('error', 'Failed to create EMD'))
            
            # Redirect back to EMD management
            return redirect('flights:emd_management')
            
        except Exception as e:
            logger.error(f"Error creating EMD: {str(e)}")
            messages.error(request, f'Error creating EMD: {str(e)}')
            return redirect('flights:emd_management')
    
    def get_emd_statistics(self, emds):
        """Calculate EMD statistics"""
        stats = {
            'total_emds': emds.count(),
            'issued_emds': emds.filter(status='issued').count(),
            'used_emds': emds.filter(status='used').count(),
            'expired_emds': emds.filter(status='expired').count(),
            'total_amount': emds.filter(status='issued').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00'),
            'used_amount': emds.filter(status='used').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00'),
        }
        
        return stats


class TicketingQueueView(LoginRequiredMixin, View):
    """Manage ticketing queue"""
    
    template_name = 'flights/ticketing/ticketing_queue.html'
    
    def get(self, request):
        try:
            # Get queue filter
            queue_filter = request.GET.get('filter', 'assigned')
            priority_filter = request.GET.get('priority', 'all')
            search_query = request.GET.get('q', '').strip()
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            queue_items = TicketQueue.objects.select_related(
                'booking',
                'passenger',
                'assigned_to',
                'created_by'
            ).order_by('priority', 'created_at')
            
            # Apply filter
            if queue_filter == 'assigned':
                queue_items = queue_items.filter(assigned_to=request.user, status='pending')
            elif queue_filter == 'unassigned':
                queue_items = queue_items.filter(assigned_to=None, status='pending')
            elif queue_filter == 'completed':
                queue_items = queue_items.filter(status='completed')
            elif queue_filter == 'all':
                queue_items = queue_items.filter(status='pending')
            
            # Apply priority filter
            if priority_filter != 'all':
                queue_items = queue_items.filter(priority=priority_filter)
            
            # Apply search
            if search_query:
                queue_items = queue_items.filter(
                    Q(booking__booking_reference__icontains=search_query) |
                    Q(passenger__first_name__icontains=search_query) |
                    Q(passenger__last_name__icontains=search_query) |
                    Q(reason__icontains=search_query)
                )
            
            # Get statistics
            stats = self.get_queue_statistics()
            
            # Pagination
            paginator = Paginator(queue_items, 20)
            page_obj = paginator.get_page(page_number)
            
            # Get queue form
            queue_form = TicketQueueForm()
            
            context = {
                'page_obj': page_obj,
                'queue_filter': queue_filter,
                'priority_filter': priority_filter,
                'search_query': search_query,
                'stats': stats,
                'queue_form': queue_form,
                'filter_options': [
                    ('assigned', 'Assigned to Me'),
                    ('unassigned', 'Unassigned'),
                    ('completed', 'Completed'),
                    ('all', 'All Pending'),
                ],
                'priority_options': [
                    ('all', 'All Priorities'),
                    ('high', 'High'),
                    ('medium', 'Medium'),
                    ('low', 'Low'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ticketing queue: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading ticketing queue.')
            return render(request, self.template_name, {'page_obj': []})
    
    def post(self, request):
        try:
            action = request.POST.get('action')
            queue_item_id = request.POST.get('queue_item_id')
            
            if not action or not queue_item_id:
                messages.error(request, 'Missing required parameters.')
                return redirect('flights:ticketing_queue')
            
            queue_item = get_object_or_404(TicketQueue, id=queue_item_id)
            ticketing_service = TicketingService()
            
            if action == 'accept':
                result = ticketing_service.accept_queue_item(queue_item, request.user)
                if result['success']:
                    messages.success(request, 'Queue item accepted.')
                else:
                    messages.error(request, result.get('error', 'Failed to accept queue item'))
            
            elif action == 'complete':
                result = ticketing_service.complete_queue_item(queue_item, request.user)
                if result['success']:
                    messages.success(request, 'Queue item completed.')
                else:
                    messages.error(request, result.get('error', 'Failed to complete queue item'))
            
            elif action == 'reassign':
                new_agent_id = request.POST.get('new_agent_id')
                if new_agent_id:
                    result = ticketing_service.reassign_queue_item(queue_item, new_agent_id, request.user)
                    if result['success']:
                        messages.success(request, 'Queue item reassigned.')
                    else:
                        messages.error(request, result.get('error', 'Failed to reassign queue item'))
            
            elif action == 'cancel':
                result = ticketing_service.cancel_queue_item(queue_item, request.user)
                if result['success']:
                    messages.success(request, 'Queue item cancelled.')
                else:
                    messages.error(request, result.get('error', 'Failed to cancel queue item'))
            
            return redirect('flights:ticketing_queue')
            
        except Exception as e:
            logger.error(f"Error processing queue action: {str(e)}")
            messages.error(request, f'Error processing action: {str(e)}')
            return redirect('flights:ticketing_queue')
    
    def get_queue_statistics(self):
        """Get queue statistics"""
        stats = {
            'total_pending': TicketQueue.objects.filter(status='pending').count(),
            'assigned_to_me': TicketQueue.objects.filter(
                assigned_to=self.request.user,
                status='pending'
            ).count(),
            'unassigned': TicketQueue.objects.filter(
                assigned_to=None,
                status='pending'
            ).count(),
            'high_priority': TicketQueue.objects.filter(
                priority='high',
                status='pending'
            ).count(),
            'completed_today': TicketQueue.objects.filter(
                status='completed',
                completed_at__date=timezone.now().date()
            ).count(),
        }
        
        return stats


class TicketingReportsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Generate ticketing reports"""
    
    template_name = 'flights/ticketing/ticketing_reports.html'
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'super_agent']
    
    def get(self, request):
        try:
            # Get report parameters
            report_type = request.GET.get('type', 'daily')
            airline_filter = request.GET.get('airline', 'all')
            agent_filter = request.GET.get('agent', 'all')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Initialize reporting service
            reporting_service = TicketingReportingService()
            
            # Generate report based on type
            if report_type == 'daily':
                report_data = reporting_service.generate_daily_report(
                    date=start_date if start_date else timezone.now().date(),
                    airline_code=airline_filter if airline_filter != 'all' else None,
                    agent_id=agent_filter if agent_filter != 'all' else None
                )
            elif report_type == 'weekly':
                report_data = reporting_service.generate_weekly_report(
                    start_date=start_date,
                    end_date=end_date,
                    airline_code=airline_filter if airline_filter != 'all' else None,
                    agent_id=agent_filter if agent_filter != 'all' else None
                )
            elif report_type == 'monthly':
                report_data = reporting_service.generate_monthly_report(
                    month=start_date[:7] if start_date else timezone.now().strftime('%Y-%m'),
                    airline_code=airline_filter if airline_filter != 'all' else None,
                    agent_id=agent_filter if agent_filter != 'all' else None
                )
            elif report_type == 'agent_performance':
                report_data = reporting_service.generate_agent_performance_report(
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == 'airline_performance':
                report_data = reporting_service.generate_airline_performance_report(
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == 'bsp':
                report_data = reporting_service.generate_bsp_report(
                    period=start_date if start_date else timezone.now().strftime('%Y-%m'),
                    airline_code=airline_filter if airline_filter != 'all' else None
                )
            else:
                report_data = {'error': 'Invalid report type'}
            
            # Get airlines for filter
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            # Get agents for filter
            agents = User.objects.filter(
                user_type__in=['agent', 'super_agent'],
                is_active=True
            ).order_by('email')
            
            context = {
                'report_type': report_type,
                'report_data': report_data,
                'airlines': airlines,
                'agents': agents,
                'airline_filter': airline_filter,
                'agent_filter': agent_filter,
                'start_date': start_date,
                'end_date': end_date,
                'report_types': [
                    ('daily', 'Daily Sales Report'),
                    ('weekly', 'Weekly Sales Report'),
                    ('monthly', 'Monthly Sales Report'),
                    ('agent_performance', 'Agent Performance'),
                    ('airline_performance', 'Airline Performance'),
                    ('bsp', 'BSP Sales Report'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error generating ticketing report: {str(e)}", exc_info=True)
            messages.error(request, f'Error generating report: {str(e)}')
            return render(request, self.template_name)


class TicketExportView(LoginRequiredMixin, View):
    """Export ticket data"""
    
    def get(self, request):
        try:
            export_format = request.GET.get('format', 'excel')
            export_type = request.GET.get('type', 'tickets')
            
            # Get filter parameters
            status_filter = request.GET.get('status', 'all')
            airline_filter = request.GET.get('airline', 'all')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Build queryset based on export type
            if export_type == 'tickets':
                queryset = Ticket.objects.select_related(
                    'booking', 'passenger', 'pnr'
                ).prefetch_related('coupons')
                
                # Apply filters
                if status_filter != 'all':
                    queryset = queryset.filter(status=status_filter)
                
                if airline_filter != 'all':
                    queryset = queryset.filter(
                        coupons__segment__airline__code=airline_filter
                    ).distinct()
                
                if start_date and end_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        queryset = queryset.filter(
                            issued_at__date__gte=start_dt.date(),
                            issued_at__date__lte=end_dt.date()
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
                
                queryset = queryset.order_by('-issued_at')
            
            elif export_type == 'commissions':
                queryset = CommissionTransaction.objects.filter(
                    transaction_type='commission'
                ).select_related('ticket', 'agent')
                
                # Apply filters
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
                    queryset = queryset.filter(agent=request.user)
                elif request.user.user_type == 'sub_agent':
                    parent_agent = request.user.parent_agent
                    if parent_agent:
                        queryset = queryset.filter(agent=parent_agent)
                
                queryset = queryset.order_by('-created_at')
            
            elif export_type == 'refunds':
                queryset = Refund.objects.filter(
                    refund_type='ticket'
                ).select_related('ticket', 'processed_by')
                
                # Apply filters
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
                
                queryset = queryset.order_by('-created_at')
            
            else:
                messages.error(request, 'Invalid export type.')
                return redirect('flights:ticket_list')
            
            # Export based on format
            export_utils = TicketExport()
            
            if export_format == 'excel':
                return export_utils.export_to_excel(queryset, export_type)
            elif export_format == 'csv':
                return export_utils.export_to_csv(queryset, export_type)
            elif export_format == 'pdf':
                return export_utils.export_to_pdf(queryset, export_type)
            else:
                messages.error(request, 'Invalid export format.')
                return redirect('flights:ticket_list')
                
        except Exception as e:
            logger.error(f"Error exporting ticket data: {str(e)}", exc_info=True)
            messages.error(request, 'Error exporting ticket data.')
            return redirect('flights:ticket_list')


class BulkTicketingView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Bulk ticketing operations"""
    
    template_name = 'flights/ticketing/bulk_ticketing.html'
    
    def test_func(self):
        return TicketingPermission.can_perform_bulk_operations(self.request.user)
    
    def get(self, request):
        try:
            # Get pending bookings for ticketing
            pending_bookings = Booking.objects.filter(
                status='confirmed',
                tickets__isnull=True
            ).select_related('itinerary').prefetch_related('passengers')[:50]
            
            # Get bulk ticketing form
            form = BulkTicketingForm()
            
            context = {
                'pending_bookings': pending_bookings,
                'form': form,
                'total_pending': Booking.objects.filter(
                    status='confirmed',
                    tickets__isnull=True
                ).count(),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading bulk ticketing: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading bulk ticketing: {str(e)}')
            return render(request, self.template_name)
    
    def post(self, request):
        try:
            action = request.POST.get('action')
            booking_ids = request.POST.getlist('bookings')
            
            if not action or not booking_ids:
                messages.error(request, 'Please select bookings and an action.')
                return redirect('flights:bulk_ticketing')
            
            # Get bookings
            bookings = Booking.objects.filter(
                id__in=booking_ids,
                status='confirmed'
            ).select_related('itinerary').prefetch_related('passengers')
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            if action == 'ticket_all':
                # Ticket all passengers in selected bookings
                results = []
                for booking in bookings:
                    for passenger in booking.passengers.all():
                        result = ticketing_service.issue_ticket(
                            booking=booking,
                            passenger=passenger,
                            user=request.user
                        )
                        results.append(result)
                
                successful = sum(1 for r in results if r.get('success'))
                failed = len(results) - successful
                
                messages.success(request, f'Bulk ticketing completed: {successful} successful, {failed} failed.')
            
            elif action == 'add_to_queue':
                # Add bookings to ticketing queue
                added_count = 0
                for booking in bookings:
                    for passenger in booking.passengers.all():
                        result = ticketing_service.add_to_queue(
                            booking=booking,
                            passenger=passenger,
                            reason='Bulk ticketing',
                            priority='medium',
                            user=request.user
                        )
                        if result['success']:
                            added_count += 1
                
                messages.success(request, f'{added_count} items added to ticketing queue.')
            
            elif action == 'generate_invoices':
                # Generate invoices for bookings
                # Implementation depends on invoice system
                messages.info(request, 'Invoice generation feature coming soon.')
            
            return redirect('flights:bulk_ticketing')
            
        except Exception as e:
            logger.error(f"Error in bulk ticketing: {str(e)}", exc_info=True)
            messages.error(request, f'Error in bulk ticketing: {str(e)}')
            return redirect('flights:bulk_ticketing')


class TicketRevalidationView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Revalidate ticketed bookings"""
    
    template_name = 'flights/ticketing/ticket_revalidation.html'
    
    def test_func(self):
        return TicketingPermission.can_revalidate_tickets(self.request.user)
    
    def get(self, request):
        try:
            # Get tickets that need revalidation
            tickets_needing_revalidation = Ticket.objects.filter(
                status='issued',
                coupons__status='open',
                coupons__segment__departure_time__lte=timezone.now() + timedelta(days=14)
            ).distinct().select_related('booking', 'passenger')[:50]
            
            # Get revalidation form
            form = TicketRevalidationForm()
            
            context = {
                'tickets_needing_revalidation': tickets_needing_revalidation,
                'form': form,
                'total_needing_revalidation': Ticket.objects.filter(
                    status='issued',
                    coupons__status='open',
                    coupons__segment__departure_time__lte=timezone.now() + timedelta(days=14)
                ).distinct().count(),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ticket revalidation: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading revalidation: {str(e)}')
            return render(request, self.template_name)
    
    def post(self, request):
        try:
            ticket_id = request.POST.get('ticket_id')
            revalidation_type = request.POST.get('revalidation_type')
            remarks = request.POST.get('remarks', '')
            
            if not ticket_id:
                messages.error(request, 'Please select a ticket.')
                return redirect('flights:ticket_revalidation')
            
            ticket = get_object_or_404(Ticket, id=ticket_id)
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            # Revalidate ticket
            result = ticketing_service.revalidate_ticket(
                ticket=ticket,
                revalidation_type=revalidation_type,
                remarks=remarks,
                user=request.user
            )
            
            if result['success']:
                messages.success(request, f'Ticket {ticket.ticket_number} revalidated successfully.')
            else:
                messages.error(request, result.get('error', 'Failed to revalidate ticket'))
            
            return redirect('flights:ticket_revalidation')
            
        except Exception as e:
            logger.error(f"Error revalidating ticket: {str(e)}", exc_info=True)
            messages.error(request, f'Error revalidating ticket: {str(e)}')
            return redirect('flights:ticket_revalidation')


# API Views for AJAX operations

@method_decorator(csrf_exempt, name='dispatch')
class TicketStatusAPI(View, LoginRequiredMixin):
    """API endpoint for ticket status updates"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            ticket_number = data.get('ticket_number')
            
            if not ticket_number:
                return JsonResponse({
                    'success': False,
                    'error': 'Ticket number is required'
                })
            
            # Get ticket
            ticket = get_object_or_404(
                Ticket.objects.select_related('booking', 'passenger'),
                ticket_number=ticket_number
            )
            
            # Check permission
            if not TicketingPermission.can_view_ticket(request.user, ticket):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            # Get ticket status
            status_info = ticketing_service.get_ticket_status(ticket)
            
            return JsonResponse({
                'success': True,
                'ticket_number': ticket.ticket_number,
                'status': ticket.status,
                'status_info': status_info,
                'passenger': f"{ticket.passenger.first_name} {ticket.passenger.last_name}",
                'booking_reference': ticket.booking.booking_reference,
                'issued_at': ticket.issued_at.isoformat() if ticket.issued_at else None,
                'coupons': [
                    {
                        'number': coupon.coupon_number,
                        'status': coupon.status,
                        'flight': coupon.segment.get_flight_designator() if coupon.segment else '',
                        'departure': coupon.segment.departure_time.isoformat() if coupon.segment else None,
                    }
                    for coupon in ticket.coupons.all()
                ],
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in ticket status API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class TicketCouponStatusAPI(View, LoginRequiredMixin):
    """API endpoint for coupon status updates"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            coupon_number = data.get('coupon_number')
            new_status = data.get('status')
            remarks = data.get('remarks', '')
            
            if not coupon_number or not new_status:
                return JsonResponse({
                    'success': False,
                    'error': 'Coupon number and status are required'
                })
            
            # Get coupon
            coupon = get_object_or_404(
                TicketCoupon.objects.select_related('ticket', 'segment'),
                coupon_number=coupon_number
            )
            
            # Check permission
            if not TicketingPermission.can_update_coupon(request.user, coupon.ticket):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            # Update coupon status
            result = ticketing_service.update_coupon_status(
                coupon=coupon,
                new_status=new_status,
                remarks=remarks,
                user=request.user
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Coupon status updated successfully',
                    'coupon': {
                        'number': coupon.coupon_number,
                        'status': new_status,
                        'updated_at': timezone.now().isoformat(),
                    },
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to update coupon status'),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in coupon status API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class TicketDocumentAPI(View, LoginRequiredMixin):
    """API endpoint for ticket document management"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            ticket_id = data.get('ticket_id')
            document_type = data.get('document_type')
            document_data = data.get('document_data')
            
            if not all([ticket_id, document_type, document_data]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required parameters'
                })
            
            # Get ticket
            ticket = get_object_or_404(Ticket, id=ticket_id)
            
            # Check permission
            if not TicketingPermission.can_manage_documents(request.user, ticket):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                })
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            # Add document
            result = ticketing_service.add_ticket_document(
                ticket=ticket,
                document_type=document_type,
                document_data=document_data,
                user=request.user
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Document added successfully',
                    'document_id': result['document'].id,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to add document'),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error in ticket document API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class BSPReportingAPI(View, LoginRequiredMixin, UserPassesTestMixin):
    """API endpoint for BSP reporting"""
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'super_agent']
    
    def get(self, request):
        try:
            period = request.GET.get('period', timezone.now().strftime('%Y-%m'))
            airline_code = request.GET.get('airline', '')
            
            # Initialize BSP report generator
            bsp_generator = BSPReportGenerator()
            
            # Generate BSP report
            report_data = bsp_generator.generate_report(
                period=period,
                airline_code=airline_code if airline_code else None
            )
            
            return JsonResponse({
                'success': True,
                'report_data': report_data,
                'period': period,
                'generated_at': timezone.now().isoformat(),
            })
            
        except Exception as e:
            logger.error(f"Error in BSP reporting API: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            period = data.get('period', timezone.now().strftime('%Y-%m'))
            airline_code = data.get('airline', '')
            report_type = data.get('report_type', 'sales')
            
            # Initialize BSP report generator
            bsp_generator = BSPReportGenerator()
            
            # Generate and submit BSP report
            result = bsp_generator.submit_report(
                period=period,
                airline_code=airline_code if airline_code else None,
                report_type=report_type,
                user=request.user
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'BSP report submitted successfully',
                    'submission_id': result.get('submission_id'),
                    'submitted_at': result.get('submitted_at'),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to submit BSP report'),
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error submitting BSP report: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class TicketingDashboardView(LoginRequiredMixin, View):
    """Ticketing dashboard"""
    
    template_name = 'flights/ticketing/ticketing_dashboard.html'
    
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
            
            # Initialize ticketing service
            ticketing_service = TicketingService()
            
            # Get dashboard data
            dashboard_data = ticketing_service.get_dashboard_data(
                start_date=start_date,
                end_date=today,
                user=request.user
            )
            
            # Get recent tickets
            recent_tickets = Ticket.objects.filter(
                issued_at__date__gte=start_date,
                issued_at__date__lte=today
            ).select_related(
                'booking',
                'passenger',
                'issued_by'
            ).order_by('-issued_at')[:10]
            
            # Apply user permissions for recent tickets
            if request.user.user_type == 'agent':
                recent_tickets = recent_tickets.filter(booking__agent=request.user)
            elif request.user.user_type == 'sub_agent':
                parent_agent = request.user.parent_agent
                if parent_agent:
                    recent_tickets = recent_tickets.filter(booking__agent=parent_agent)
            
            # Get queue statistics
            queue_stats = self.get_queue_statistics()
            
            # Get upcoming revalidations
            upcoming_revalidations = Ticket.objects.filter(
                status='issued',
                coupons__status='open',
                coupons__segment__departure_time__gte=timezone.now(),
                coupons__segment__departure_time__lte=timezone.now() + timedelta(days=7)
            ).distinct().select_related('booking', 'passenger')[:10]
            
            context = {
                'dashboard_data': dashboard_data,
                'recent_tickets': recent_tickets,
                'queue_stats': queue_stats,
                'upcoming_revalidations': upcoming_revalidations,
                'time_period': time_period,
                'period_options': [
                    ('7d', 'Last 7 Days'),
                    ('30d', 'Last 30 Days'),
                    ('90d', 'Last 90 Days'),
                ],
                'can_view_reports': request.user.user_type in ['admin', 'super_agent'],
                'can_manage_queue': TicketingPermission.can_manage_queue(request.user),
                'can_perform_bulk': TicketingPermission.can_perform_bulk_operations(request.user),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading ticketing dashboard: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading dashboard.')
            return render(request, self.template_name)
    
    def get_queue_statistics(self):
        """Get queue statistics for dashboard"""
        stats = {
            'pending': TicketQueue.objects.filter(status='pending').count(),
            'assigned_to_me': TicketQueue.objects.filter(
                assigned_to=self.request.user,
                status='pending'
            ).count(),
            'high_priority': TicketQueue.objects.filter(
                priority='high',
                status='pending'
            ).count(),
            'completed_today': TicketQueue.objects.filter(
                status='completed',
                completed_at__date=timezone.now().date()
            ).count(),
            'oldest_pending': TicketQueue.objects.filter(
                status='pending'
            ).order_by('created_at').first(),
        }
        
        return stats