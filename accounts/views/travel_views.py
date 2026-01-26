# accounts/views/travel_views.py
"""
Travel booking views for B2B Travel Mushqila - Saudi Arabia
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, F
from datetime import datetime, timedelta
import json

from ..models import (
    FlightBooking, HotelBooking, HajjPackage, UmrahPackage,
    ServiceSupplier, Transaction, Invoice, UserActivityLog
)
from ..forms import (
    FlightBookingForm, HotelBookingForm, HajjBookingForm,
    UmrahBookingForm, VisaApplicationForm
)


class FlightBookingView(LoginRequiredMixin, CreateView):
    """Flight booking view"""
    
    template_name = 'accounts/travel/flight_booking.html'
    form_class = FlightBookingForm
    success_url = reverse_lazy('flight_booking_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Check if user has sufficient balance or credit
                user = self.request.user
                total_amount = form.cleaned_data.get('total_amount', 0)
                
                if not self.can_book_flight(user, total_amount):
                    messages.error(
                        self.request,
                        _('Insufficient balance or credit. Please add funds to your wallet.')
                    )
                    return self.form_invalid(form)
                
                # Save booking
                booking = form.save()
                
                # Create transaction
                transaction = Transaction.objects.create(
                    user=user,
                    transaction_type=Transaction.TransactionType.BOOKING,
                    amount=-total_amount,  # Negative for deduction
                    currency='SAR',
                    status=Transaction.Status.COMPLETED,
                    description=f'Flight booking for {booking.passenger_name}',
                    balance_before=user.wallet_balance,
                    balance_after=user.wallet_balance - total_amount,
                    metadata={
                        'booking_id': booking.booking_id,
                        'passenger_name': booking.passenger_name,
                        'airline': booking.airline.name,
                        'flight_number': booking.flight_number
                    }
                )
                
                # Update user balance
                user.wallet_balance = F('wallet_balance') - total_amount
                user.save()
                user.refresh_from_db()  # Refresh to get updated balance
                
                # Update user profile statistics
                profile = user.profile
                profile.total_bookings += 1
                profile.total_sales += total_amount
                profile.total_commission += booking.commission_amount
                profile.save()
                
                # Log activity
                UserActivityLog.objects.create(
                    user=user,
                    activity_type=UserActivityLog.ActivityType.BOOKING,
                    description=f"Flight booked for {booking.passenger_name} - {booking.booking_id}",
                    ip_address=self.get_client_ip(),
                    success=True,
                    metadata={
                        'booking_id': booking.booking_id,
                        'amount': str(total_amount),
                        'passenger': booking.passenger_name
                    }
                )
                
                # Create invoice
                self.create_invoice(booking, total_amount)
                
                messages.success(
                    self.request,
                    _('Flight booked successfully! Booking ID: %(booking_id)s') % 
                    {'booking_id': booking.booking_id}
                )
                
                return redirect('flight_booking_detail', pk=booking.pk)
        
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def can_book_flight(self, user, amount):
        """Check if user can book flight"""
        available_funds = user.wallet_balance + max(0, user.available_credit())
        return available_funds >= amount
    
    def create_invoice(self, booking, total_amount):
        """Create invoice for booking"""
        from ..models import Invoice
        
        invoice = Invoice.objects.create(
            user=booking.agent,
            flight_booking=booking,
            subtotal=booking.base_fare,
            vat_amount=booking.vat,
            total_amount=total_amount,
            status=Invoice.InvoiceStatus.ISSUED,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            notes=f'Flight booking for {booking.passenger_name}'
        )
        
        return invoice
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Book Flight')
        context['user'] = self.request.user
        context['available_balance'] = self.request.user.wallet_balance
        context['available_credit'] = self.request.user.available_credit()
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class FlightBookingListView(LoginRequiredMixin, ListView):
    """Flight booking list view"""
    
    template_name = 'accounts/travel/flight_booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            # Admin can see all bookings
            queryset = FlightBooking.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            # Super agent can see bookings from their sub-agents
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            queryset = FlightBooking.objects.filter(agent__in=sub_agents)
        else:
            # Regular users can only see their own bookings
            queryset = FlightBooking.objects.filter(agent=user)
        
        # Apply filters
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(departure_date__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(departure_date__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        user = self.request.user
        if user.user_type == User.UserType.ADMIN:
            total_bookings = FlightBooking.objects.count()
            total_sales = FlightBooking.objects.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            pending_bookings = FlightBooking.objects.filter(
                status=FlightBooking.BookingStatus.PENDING
            ).count()
        
        elif user.user_type == User.UserType.SUPER_AGENT:
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            total_bookings = FlightBooking.objects.filter(
                agent__in=sub_agents
            ).count()
            total_sales = FlightBooking.objects.filter(
                agent__in=sub_agents
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            pending_bookings = FlightBooking.objects.filter(
                agent__in=sub_agents,
                status=FlightBooking.BookingStatus.PENDING
            ).count()
        
        else:
            total_bookings = FlightBooking.objects.filter(agent=user).count()
            total_sales = FlightBooking.objects.filter(
                agent=user
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            pending_bookings = FlightBooking.objects.filter(
                agent=user,
                status=FlightBooking.BookingStatus.PENDING
            ).count()
        
        context.update({
            'page_title': _('Flight Bookings'),
            'total_bookings': total_bookings,
            'total_sales': total_sales,
            'pending_bookings': pending_bookings,
            'status_choices': FlightBooking.BookingStatus.choices,
        })
        
        return context


class FlightBookingDetailView(LoginRequiredMixin, DetailView):
    """Flight booking detail view"""
    
    template_name = 'accounts/travel/flight_booking_detail.html'
    model = FlightBooking
    context_object_name = 'booking'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            return FlightBooking.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            return FlightBooking.objects.filter(agent__in=sub_agents)
        else:
            return FlightBooking.objects.filter(agent=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Flight Booking Details')
        
        # Get related invoice if exists
        try:
            context['invoice'] = self.object.invoices.first()
        except:
            context['invoice'] = None
        
        return context


class HotelBookingView(LoginRequiredMixin, CreateView):
    """Hotel booking view"""
    
    template_name = 'accounts/travel/hotel_booking.html'
    form_class = HotelBookingForm
    success_url = reverse_lazy('hotel_booking_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Check if user has sufficient balance or credit
                user = self.request.user
                total_amount = form.cleaned_data.get('total_amount', 0)
                
                if not self.can_book_hotel(user, total_amount):
                    messages.error(
                        self.request,
                        _('Insufficient balance or credit. Please add funds to your wallet.')
                    )
                    return self.form_invalid(form)
                
                # Save booking
                booking = form.save()
                
                # Create transaction
                transaction = Transaction.objects.create(
                    user=user,
                    transaction_type=Transaction.TransactionType.BOOKING,
                    amount=-total_amount,  # Negative for deduction
                    currency='SAR',
                    status=Transaction.Status.COMPLETED,
                    description=f'Hotel booking for {booking.guest_name}',
                    balance_before=user.wallet_balance,
                    balance_after=user.wallet_balance - total_amount,
                    metadata={
                        'booking_id': booking.booking_id,
                        'guest_name': booking.guest_name,
                        'hotel': booking.hotel.name,
                        'check_in': booking.check_in.isoformat(),
                        'check_out': booking.check_out.isoformat()
                    }
                )
                
                # Update user balance
                user.wallet_balance = F('wallet_balance') - total_amount
                user.save()
                user.refresh_from_db()  # Refresh to get updated balance
                
                # Update user profile statistics
                profile = user.profile
                profile.total_bookings += 1
                profile.total_sales += total_amount
                profile.total_commission += booking.commission_amount
                profile.save()
                
                # Log activity
                UserActivityLog.objects.create(
                    user=user,
                    activity_type=UserActivityLog.ActivityType.BOOKING,
                    description=f"Hotel booked for {booking.guest_name} - {booking.booking_id}",
                    ip_address=self.get_client_ip(),
                    success=True,
                    metadata={
                        'booking_id': booking.booking_id,
                        'amount': str(total_amount),
                        'guest': booking.guest_name
                    }
                )
                
                # Create invoice
                self.create_invoice(booking, total_amount)
                
                messages.success(
                    self.request,
                    _('Hotel booked successfully! Booking ID: %(booking_id)s') % 
                    {'booking_id': booking.booking_id}
                )
                
                return redirect('hotel_booking_detail', pk=booking.pk)
        
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def can_book_hotel(self, user, amount):
        """Check if user can book hotel"""
        available_funds = user.wallet_balance + max(0, user.available_credit())
        return available_funds >= amount
    
    def create_invoice(self, booking, total_amount):
        """Create invoice for booking"""
        from ..models import Invoice
        
        invoice = Invoice.objects.create(
            user=booking.agent,
            hotel_booking=booking,
            subtotal=booking.total_amount,
            vat_amount=0,  # Assuming VAT included in room rate
            total_amount=total_amount,
            status=Invoice.InvoiceStatus.ISSUED,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            notes=f'Hotel booking for {booking.guest_name}'
        )
        
        return invoice
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Book Hotel')
        context['user'] = self.request.user
        context['available_balance'] = self.request.user.wallet_balance
        context['available_credit'] = self.request.user.available_credit()
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class HotelBookingListView(LoginRequiredMixin, ListView):
    """Hotel booking list view"""
    
    template_name = 'accounts/travel/hotel_booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            # Admin can see all bookings
            queryset = HotelBooking.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            # Super agent can see bookings from their sub-agents
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            queryset = HotelBooking.objects.filter(agent__in=sub_agents)
        else:
            # Regular users can only see their own bookings
            queryset = HotelBooking.objects.filter(agent=user)
        
        # Apply filters
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(check_in__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(check_in__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        user = self.request.user
        if user.user_type == User.UserType.ADMIN:
            total_bookings = HotelBooking.objects.count()
            total_sales = HotelBooking.objects.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            pending_bookings = HotelBooking.objects.filter(
                status=HotelBooking.BookingStatus.PENDING
            ).count()
        
        elif user.user_type == User.UserType.SUPER_AGENT:
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            total_bookings = HotelBooking.objects.filter(
                agent__in=sub_agents
            ).count()
            total_sales = HotelBooking.objects.filter(
                agent__in=sub_agents
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            pending_bookings = HotelBooking.objects.filter(
                agent__in=sub_agents,
                status=HotelBooking.BookingStatus.PENDING
            ).count()
        
        else:
            total_bookings = HotelBooking.objects.filter(agent=user).count()
            total_sales = HotelBooking.objects.filter(
                agent=user
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            pending_bookings = HotelBooking.objects.filter(
                agent=user,
                status=HotelBooking.BookingStatus.PENDING
            ).count()
        
        context.update({
            'page_title': _('Hotel Bookings'),
            'total_bookings': total_bookings,
            'total_sales': total_sales,
            'pending_bookings': pending_bookings,
            'status_choices': HotelBooking.BookingStatus.choices,
        })
        
        return context


class HotelBookingDetailView(LoginRequiredMixin, DetailView):
    """Hotel booking detail view"""
    
    template_name = 'accounts/travel/hotel_booking_detail.html'
    model = HotelBooking
    context_object_name = 'booking'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            return HotelBooking.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            return HotelBooking.objects.filter(agent__in=sub_agents)
        else:
            return HotelBooking.objects.filter(agent=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Hotel Booking Details')
        
        # Get related invoice if exists
        try:
            context['invoice'] = self.object.invoices.first()
        except:
            context['invoice'] = None
        
        return context


class HajjBookingView(LoginRequiredMixin, TemplateView):
    """Hajj booking view"""
    
    template_name = 'accounts/travel/hajj_booking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available Hajj packages
        packages = HajjPackage.objects.filter(
            status=HajjPackage.PackageStatus.AVAILABLE
        ).order_by('base_price')
        
        # Get Hajj booking form
        form = HajjBookingForm()
        
        context.update({
            'page_title': _('Hajj Packages'),
            'packages': packages,
            'form': form,
            'user': self.request.user,
        })
        
        return context
    
    def post(self, request):
        form = HajjBookingForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    package = form.cleaned_data['package']
                    pilgrims = form.cleaned_data['pilgrims']
                    total_amount = package.base_price * pilgrims
                    
                    # Check if user has sufficient balance
                    if not self.can_book_hajj(request.user, total_amount):
                        messages.error(
                            request,
                            _('Insufficient balance. Please add funds to your wallet.')
                        )
                        return redirect('hajj_booking')
                    
                    # Create Hajj booking (you need to create HajjBooking model)
                    # This is a simplified version
                    
                    # Create transaction
                    transaction = Transaction.objects.create(
                        user=request.user,
                        transaction_type=Transaction.TransactionType.HAJJ,
                        amount=-total_amount,
                        currency='SAR',
                        status=Transaction.Status.COMPLETED,
                        description=f'Hajj package booking for {pilgrims} pilgrims',
                        balance_before=request.user.wallet_balance,
                        balance_after=request.user.wallet_balance - total_amount,
                        metadata={
                            'package': package.package_code,
                            'pilgrims': pilgrims,
                            'total_amount': str(total_amount)
                        }
                    )
                    
                    # Update user balance
                    request.user.wallet_balance = F('wallet_balance') - total_amount
                    request.user.save()
                    
                    # Update package availability
                    package.available_slots -= pilgrims
                    package.save()
                    
                    # Update user profile
                    profile = request.user.profile
                    profile.hajj_bookings += pilgrims
                    profile.total_bookings += 1
                    profile.total_sales += total_amount
                    profile.save()
                    
                    # Log activity
                    UserActivityLog.objects.create(
                        user=request.user,
                        activity_type=UserActivityLog.ActivityType.HAJJ_BOOKING,
                        description=f"Hajj package booked: {package.name} for {pilgrims} pilgrims",
                        ip_address=self.get_client_ip(request),
                        success=True
                    )
                    
                    messages.success(
                        request,
                        _('Hajj package booked successfully for %(pilgrims)s pilgrims!') % 
                        {'pilgrims': pilgrims}
                    )
                    
                    return redirect('dashboard')
            
            except Exception as e:
                messages.error(request, str(e))
        
        else:
            messages.error(request, _('Please correct the errors below.'))
        
        return redirect('hajj_booking')
    
    def can_book_hajj(self, user, amount):
        """Check if user can book Hajj package"""
        return user.wallet_balance >= amount
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UmrahBookingView(LoginRequiredMixin, TemplateView):
    """Umrah booking view"""
    
    template_name = 'accounts/travel/umrah_booking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available Umrah packages
        packages = UmrahPackage.objects.all().order_by('base_price')
        
        # Get Umrah booking form
        form = UmrahBookingForm()
        
        context.update({
            'page_title': _('Umrah Packages'),
            'packages': packages,
            'form': form,
            'user': self.request.user,
        })
        
        return context
    
    def post(self, request):
        form = UmrahBookingForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    package = form.cleaned_data['package']
                    travelers = form.cleaned_data['travelers']
                    total_amount = package.base_price * travelers
                    
                    # Check if user has sufficient balance
                    if not self.can_book_umrah(request.user, total_amount):
                        messages.error(
                            request,
                            _('Insufficient balance. Please add funds to your wallet.')
                        )
                        return redirect('umrah_booking')
                    
                    # Create Umrah booking (you need to create UmrahBooking model)
                    # This is a simplified version
                    
                    # Create transaction
                    transaction = Transaction.objects.create(
                        user=request.user,
                        transaction_type=Transaction.TransactionType.UMRAH,
                        amount=-total_amount,
                        currency='SAR',
                        status=Transaction.Status.COMPLETED,
                        description=f'Umrah package booking for {travelers} travelers',
                        balance_before=request.user.wallet_balance,
                        balance_after=request.user.wallet_balance - total_amount,
                        metadata={
                            'package': package.package_code,
                            'travelers': travelers,
                            'total_amount': str(total_amount)
                        }
                    )
                    
                    # Update user balance
                    request.user.wallet_balance = F('wallet_balance') - total_amount
                    request.user.save()
                    
                    # Update user profile
                    profile = request.user.profile
                    profile.umrah_bookings += travelers
                    profile.total_bookings += 1
                    profile.total_sales += total_amount
                    profile.save()
                    
                    # Log activity
                    UserActivityLog.objects.create(
                        user=request.user,
                        activity_type=UserActivityLog.ActivityType.UMRAH_BOOKING,
                        description=f"Umrah package booked: {package.name} for {travelers} travelers",
                        ip_address=self.get_client_ip(request),
                        success=True
                    )
                    
                    messages.success(
                        request,
                        _('Umrah package booked successfully for %(travelers)s travelers!') % 
                        {'travelers': travelers}
                    )
                    
                    return redirect('dashboard')
            
            except Exception as e:
                messages.error(request, str(e))
        
        else:
            messages.error(request, _('Please correct the errors below.'))
        
        return redirect('umrah_booking')
    
    def can_book_umrah(self, user, amount):
        """Check if user can book Umrah package"""
        return user.wallet_balance >= amount
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CancelBookingView(LoginRequiredMixin, View):
    """Cancel booking view"""
    
    def post(self, request, booking_type, pk):
        booking_type = booking_type.lower()  # flight or hotel
        
        if booking_type == 'flight':
            booking = get_object_or_404(FlightBooking, pk=pk, agent=request.user)
            model = FlightBooking
        elif booking_type == 'hotel':
            booking = get_object_or_404(HotelBooking, pk=pk, agent=request.user)
            model = HotelBooking
        else:
            messages.error(request, _('Invalid booking type.'))
            return redirect('dashboard')
        
        # Check if booking can be cancelled
        if booking.status not in [model.BookingStatus.PENDING, model.BookingStatus.CONFIRMED]:
            messages.error(request, _('This booking cannot be cancelled.'))
            return redirect(f'{booking_type}_booking_detail', pk=pk)
        
        try:
            with transaction.atomic():
                # Update booking status
                booking.status = model.BookingStatus.CANCELLED
                booking.save()
                
                # Refund amount to user wallet
                refund_amount = booking.total_amount * Decimal('0.8')  # 80% refund
                
                # Create refund transaction
                Transaction.objects.create(
                    user=request.user,
                    transaction_type=Transaction.TransactionType.REFUND,
                    amount=refund_amount,
                    currency='SAR',
                    status=Transaction.Status.COMPLETED,
                    description=f'Refund for cancelled {booking_type} booking',
                    balance_before=request.user.wallet_balance,
                    balance_after=request.user.wallet_balance + refund_amount,
                    metadata={
                        'booking_id': booking.booking_id,
                        'refund_amount': str(refund_amount)
                    }
                )
                
                # Update user balance
                request.user.wallet_balance = F('wallet_balance') + refund_amount
                request.user.save()
                
                # Log activity
                UserActivityLog.objects.create(
                    user=request.user,
                    activity_type=UserActivityLog.ActivityType.BOOKING,
                    description=f"{booking_type.title()} booking cancelled: {booking.booking_id}",
                    ip_address=self.get_client_ip(request),
                    success=True
                )
                
                messages.success(
                    request,
                    _('Booking cancelled successfully. %(amount)s SAR has been refunded to your wallet.') % 
                    {'amount': refund_amount}
                )
        
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect(f'{booking_type}_booking_detail', pk=pk)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SearchFlightsView(LoginRequiredMixin, TemplateView):
    """Search flights view"""
    
    template_name = 'accounts/travel/search_flights.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get airlines
        airlines = ServiceSupplier.objects.filter(
            supplier_type=ServiceSupplier.SupplierType.AIRLINE,
            is_active=True
        )
        
        context.update({
            'page_title': _('Search Flights'),
            'airlines': airlines,
        })
        
        return context
    
    def post(self, request):
        # This would typically call an external flight API
        # For now, we'll return a mock response
        
        departure = request.POST.get('departure')
        destination = request.POST.get('destination')
        departure_date = request.POST.get('departure_date')
        travelers = request.POST.get('travelers', 1)
        travel_class = request.POST.get('class', 'Economy')
        
        # Mock flight data
        flights = [
            {
                'airline': 'Saudia',
                'flight_number': 'SV 123',
                'departure_time': '08:00',
                'arrival_time': '10:00',
                'duration': '2h',
                'price': 450.00,
                'stops': 0,
            },
            {
                'airline': 'Flynas',
                'flight_number': 'XY 456',
                'departure_time': '10:30',
                'arrival_time': '12:30',
                'duration': '2h',
                'price': 380.00,
                'stops': 0,
            },
            {
                'airline': 'Flyadeal',
                'flight_number': 'F3 789',
                'departure_time': '14:00',
                'arrival_time': '16:30',
                'duration': '2h 30m',
                'price': 320.00,
                'stops': 0,
            },
        ]
        
        return render(request, 'accounts/travel/flight_results.html', {
            'page_title': _('Flight Results'),
            'flights': flights,
            'search_params': {
                'departure': departure,
                'destination': destination,
                'departure_date': departure_date,
                'travelers': travelers,
                'class': travel_class,
            }
        })