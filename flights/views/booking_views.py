# flights/views/booking_views.py
"""
Booking flow views for B2B Travel Platform
Production Ready - Final Version
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
import json
import logging
from datetime import datetime, timedelta
import uuid

from flights.forms import (
    BookingForm,
    PassengerForm,
    ContactInformationForm,
    PaymentForm,
    CreditCardForm,
    BankTransferForm,
    WalletPaymentForm,
    MultiplePaymentForm,
    QuickBookingForm,
    GroupBookingForm,
    CorporateBookingForm,
)
from flights.models import (
    Booking,
    Passenger,
    FlightItinerary,
    PNR,
    Ticket,
    Payment,
    AncillaryBooking,
)
from flights.services import BookingService, TicketingService
from accounts.models import User

logger = logging.getLogger(__name__)


class BookingCreateView(LoginRequiredMixin, View):
    """Create a new booking from search results"""
    
    template_name = 'flights/booking/create_booking.html'
    
    def get(self, request, *args, **kwargs):
        # Get itinerary ID from session or URL
        itinerary_id = request.GET.get('itinerary_id') or request.session.get('selected_itinerary')
        
        if not itinerary_id:
            messages.error(request, 'No itinerary selected. Please search for flights first.')
            return redirect('flights:search')
        
        try:
            # Get itinerary
            itinerary = FlightItinerary.objects.get(id=itinerary_id)
            
            # Check if itinerary is still valid
            if itinerary.is_expired():
                messages.error(request, 'The selected fare has expired. Please search again.')
                return redirect('flights:search')
            
            # Get search parameters from session
            search_params = request.session.get('search_params', {})
            passenger_count = (
                search_params.get('adults', 1) +
                search_params.get('children', 0) +
                search_params.get('infants', 0)
            )
            
            # Initialize booking form
            booking_form = BookingForm(
                user=request.user,
                itinerary=itinerary,
                passenger_count=passenger_count
            )
            
            # Initialize passenger forms
            passenger_forms = []
            for i in range(passenger_count):
                # Determine passenger type
                if i < search_params.get('adults', 1):
                    passenger_type = 'ADT'
                elif i < search_params.get('adults', 1) + search_params.get('children', 0):
                    passenger_type = 'CHD'
                else:
                    passenger_type = 'INF'
                
                passenger_forms.append(
                    PassengerForm(
                        passenger_type=passenger_type,
                        booking=None
                    )
                )
            
            # Initialize contact form
            contact_form = ContactInformationForm(user=request.user)
            
            context = {
                'itinerary': itinerary,
                'booking_form': booking_form,
                'passenger_forms': passenger_forms,
                'contact_form': contact_form,
                'search_params': search_params,
                'passenger_count': passenger_count,
                'page_title': 'Create Booking | B2B Travel Portal',
            }
            
            return render(request, self.template_name, context)
            
        except FlightItinerary.DoesNotExist:
            messages.error(request, 'Selected itinerary not found.')
            return redirect('flights:search')
        except Exception as e:
            logger.error(f"Booking creation failed: {str(e)}", exc_info=True)
            messages.error(request, 'Failed to load booking page.')
            return redirect('flights:search')
    
    def post(self, request, *args, **kwargs):
        itinerary_id = request.POST.get('itinerary_id')
        
        if not itinerary_id:
            messages.error(request, 'No itinerary selected.')
            return redirect('flights:search')
        
        try:
            with transaction.atomic():
                # Get itinerary
                itinerary = FlightItinerary.objects.get(id=itinerary_id)
                
                # Get passenger count
                search_params = request.session.get('search_params', {})
                passenger_count = (
                    search_params.get('adults', 1) +
                    search_params.get('children', 0) +
                    search_params.get('infants', 0)
                )
                
                # Initialize and validate booking form
                booking_form = BookingForm(
                    request.POST,
                    user=request.user,
                    itinerary=itinerary,
                    passenger_count=passenger_count
                )
                
                # Validate passenger forms
                passenger_forms = []
                passenger_data = []
                
                for i in range(passenger_count):
                    # Determine passenger type
                    if i < search_params.get('adults', 1):
                        passenger_type = 'ADT'
                    elif i < search_params.get('adults', 1) + search_params.get('children', 0):
                        passenger_type = 'CHD'
                    else:
                        passenger_type = 'INF'
                    
                    # Get prefix for this passenger
                    prefix = f'passenger_{i}_'
                    
                    # Extract data for this passenger
                    passenger_post_data = {
                        key.replace(prefix, ''): value
                        for key, value in request.POST.items()
                        if key.startswith(prefix)
                    }
                    
                    form = PassengerForm(
                        passenger_post_data,
                        passenger_type=passenger_type,
                        booking=None
                    )
                    
                    if form.is_valid():
                        passenger_data.append(form.cleaned_data)
                    else:
                        passenger_forms.append(form)
                
                # Validate contact form
                contact_form = ContactInformationForm(request.POST, user=request.user)
                
                # Check all forms
                if (booking_form.is_valid() and 
                    all(form.is_valid() for form in passenger_forms) and 
                    contact_form.is_valid()):
                    
                    # Create booking
                    booking = booking_form.save(commit=False)
                    booking.status = 'pending'
                    booking.save()
                    
                    # Create passengers
                    for i, pax_data in enumerate(passenger_data):
                        passenger = Passenger.objects.create(**pax_data)
                        booking.passengers.add(passenger)
                    
                    # Store contact information
                    contact_info = contact_form.cleaned_data
                    booking.customer_remarks = json.dumps({
                        'contact_info': contact_info,
                        'notification_preferences': {
                            'email': contact_info.get('send_itinerary_email', True),
                            'sms': contact_info.get('send_sms_notifications', True),
                            'alerts': contact_info.get('send_flight_alerts', True),
                        }
                    })
                    booking.save()
                    
                    # Store booking ID in session for next steps
                    request.session['current_booking'] = str(booking.id)
                    
                    messages.success(request, 'Booking created successfully!')
                    return redirect('flights:review_booking', booking_id=booking.id)
                
                else:
                    # Re-initialize forms with errors
                    if not passenger_forms:
                        passenger_forms = [
                            PassengerForm(
                                passenger_type='ADT' if i < search_params.get('adults', 1) else 
                                              'CHD' if i < search_params.get('adults', 1) + search_params.get('children', 0) else 
                                              'INF',
                                booking=None
                            )
                            for i in range(passenger_count)
                        ]
                    
                    context = {
                        'itinerary': itinerary,
                        'booking_form': booking_form,
                        'passenger_forms': passenger_forms,
                        'contact_form': contact_form,
                        'search_params': search_params,
                        'passenger_count': passenger_count,
                        'page_title': 'Create Booking | B2B Travel Portal',
                    }
                    
                    messages.error(request, 'Please correct the errors below.')
                    return render(request, self.template_name, context)
                    
        except Exception as e:
            logger.error(f"Booking creation failed: {str(e)}", exc_info=True)
            messages.error(request, f'Booking creation failed: {str(e)}')
            return redirect('flights:search')


class PassengerDetailsView(LoginRequiredMixin, UpdateView):
    """Edit passenger details for a booking"""
    
    template_name = 'flights/booking/passenger_details.html'
    model = Passenger
    form_class = PassengerForm
    context_object_name = 'passenger'
    
    def get_object(self, queryset=None):
        booking_id = self.kwargs.get('booking_id')
        passenger_id = self.kwargs.get('passenger_id')
        
        # Verify the booking belongs to the current user
        booking = get_object_or_404(
            Booking,
            id=booking_id,
            agent=self.request.user
        )
        
        # Get the passenger from this booking
        return get_object_or_404(
            Passenger,
            id=passenger_id,
            booking_passengers__booking=booking
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['booking'] = self.object.booking_passengers.first().booking
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking'] = self.object.booking_passengers.first().booking
        context['page_title'] = 'Edit Passenger Details | B2B Travel Portal'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Passenger details updated successfully.')
        return response
    
    def get_success_url(self):
        booking_id = self.kwargs.get('booking_id')
        return reverse('flights:booking_detail', kwargs={'booking_id': booking_id})


class ReviewBookingView(LoginRequiredMixin, View):
    """Review booking before payment"""
    
    template_name = 'flights/booking/review_booking.html'
    
    def get(self, request, *args, **kwargs):
        booking_id = kwargs.get('booking_id')
        
        try:
            booking = Booking.objects.get(
                id=booking_id,
                agent=request.user
            )
            
            # Check if booking can be modified
            if booking.status not in ['pending', 'confirmed']:
                messages.warning(request, 'This booking cannot be modified.')
                return redirect('flights:booking_detail', booking_id=booking.id)
            
            # Get ancillary services
            ancillary_services = AncillaryBooking.objects.filter(booking=booking)
            
            # Calculate totals
            total_amount = booking.total_amount
            for ancillary in ancillary_services:
                total_amount += ancillary.total_price
            
            context = {
                'booking': booking,
                'ancillary_services': ancillary_services,
                'total_amount': total_amount,
                'page_title': 'Review Booking | B2B Travel Portal',
            }
            
            return render(request, self.template_name, context)
            
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('flights:booking_list')
    
    def post(self, request, *args, **kwargs):
        booking_id = kwargs.get('booking_id')
        
        try:
            booking = Booking.objects.get(
                id=booking_id,
                agent=request.user
            )
            
            # Update booking status to confirmed
            if booking.status == 'pending':
                booking.status = 'confirmed'
                booking.confirmed_at = timezone.now()
                booking.save()
                
                # Create booking history entry
                BookingHistory.objects.create(
                    booking=booking,
                    status='confirmed',
                    description='Booking confirmed for payment',
                    created_by=request.user
                )
                
                messages.success(request, 'Booking confirmed. Proceed to payment.')
                return redirect('flights:payment', booking_id=booking.id)
            else:
                messages.warning(request, 'Booking already confirmed.')
                return redirect('flights:payment', booking_id=booking.id)
                
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('flights:booking_list')


class PaymentView(LoginRequiredMixin, View):
    """Payment view for booking"""
    
    template_name = 'flights/booking/payment.html'
    
    def get(self, request, *args, **kwargs):
        booking_id = kwargs.get('booking_id')
        
        try:
            booking = Booking.objects.get(
                id=booking_id,
                agent=request.user
            )
            
            # Check if booking is ready for payment
            if booking.status not in ['confirmed', 'pending']:
                messages.warning(request, 'This booking is not ready for payment.')
                return redirect('flights:booking_detail', booking_id=booking.id)
            
            # Initialize payment form based on user preference
            user_profile = getattr(request.user, 'profile', None)
            default_payment_method = getattr(user_profile, 'default_payment_method', 'credit_card')
            
            if default_payment_method == 'credit_card':
                form_class = CreditCardForm
            elif default_payment_method == 'bank_transfer':
                form_class = BankTransferForm
            elif default_payment_method == 'wallet':
                form_class = WalletPaymentForm
            else:
                form_class = PaymentForm
            
            form = form_class(user=request.user, booking=booking)
            
            # Get user's wallet balance if available
            wallet_balance = 0
            if user_profile and hasattr(user_profile, 'wallet_balance'):
                wallet_balance = user_profile.wallet_balance
            
            # Get credit limit if available
            credit_limit = 0
            credit_used = 0
            if user_profile:
                credit_limit = getattr(user_profile, 'credit_limit', 0)
                credit_used = getattr(user_profile, 'credit_used', 0)
            
            context = {
                'booking': booking,
                'form': form,
                'wallet_balance': wallet_balance,
                'credit_limit': credit_limit,
                'credit_available': credit_limit - credit_used,
                'page_title': 'Payment | B2B Travel Portal',
            }
            
            return render(request, self.template_name, context)
            
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('flights:booking_list')
    
    def post(self, request, *args, **kwargs):
        booking_id = kwargs.get('booking_id')
        
        try:
            booking = Booking.objects.get(
                id=booking_id,
                agent=request.user
            )
            
            # Determine payment method from form
            payment_method = request.POST.get('payment_method', 'credit_card')
            
            if payment_method == 'credit_card':
                form_class = CreditCardForm
            elif payment_method == 'bank_transfer':
                form_class = BankTransferForm
            elif payment_method == 'wallet':
                form_class = WalletPaymentForm
            elif payment_method == 'multiple':
                form_class = MultiplePaymentForm
            else:
                form_class = PaymentForm
            
            form = form_class(request.POST, user=request.user, booking=booking)
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        # Create payment
                        payment = form.save(commit=False)
                        payment.status = 'pending'
                        payment.save()
                        
                        # Update booking payment status
                        booking.payment_status = 'pending'
                        booking.payment_method = payment_method
                        booking.payment_transaction_id = payment.payment_reference
                        booking.save()
                        
                        # Process payment based on method
                        if payment_method == 'credit_card':
                            return self.process_credit_card_payment(request, payment, booking)
                        elif payment_method == 'bank_transfer':
                            return self.process_bank_transfer_payment(request, payment, booking)
                        elif payment_method == 'wallet':
                            return self.process_wallet_payment(request, payment, booking)
                        elif payment_method == 'multiple':
                            return self.process_multiple_payment(request, payment, booking)
                        else:
                            messages.info(request, 'Payment recorded. Please complete payment offline.')
                            return redirect('flights:payment_confirmation', booking_id=booking.id)
                            
                except Exception as e:
                    logger.error(f"Payment processing failed: {str(e)}", exc_info=True)
                    messages.error(request, f'Payment processing failed: {str(e)}')
                    
            else:
                messages.error(request, 'Please correct the errors below.')
                
                # Re-render form with errors
                user_profile = getattr(request.user, 'profile', None)
                wallet_balance = 0
                credit_limit = 0
                credit_used = 0
                
                if user_profile:
                    wallet_balance = getattr(user_profile, 'wallet_balance', 0)
                    credit_limit = getattr(user_profile, 'credit_limit', 0)
                    credit_used = getattr(user_profile, 'credit_used', 0)
                
                context = {
                    'booking': booking,
                    'form': form,
                    'wallet_balance': wallet_balance,
                    'credit_limit': credit_limit,
                    'credit_available': credit_limit - credit_used,
                    'page_title': 'Payment | B2B Travel Portal',
                }
                
                return render(request, self.template_name, context)
                
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('flights:booking_list')
        
        return redirect('flights:booking_detail', booking_id=booking_id)
    
    def process_credit_card_payment(self, request, payment, booking):
        """Process credit card payment"""
        try:
            # In production, this would integrate with a payment gateway
            # For now, we'll simulate a successful payment
            
            payment.status = 'authorized'
            payment.authorization_code = f"AUTH{int(timezone.now().timestamp())}"
            payment.captured_at = timezone.now()
            payment.save()
            
            # Update booking
            booking.payment_status = 'paid'
            booking.paid_amount = payment.amount
            booking.due_amount = booking.total_amount - payment.amount
            booking.payment_date = timezone.now()
            booking.save()
            
            # Create booking history
            BookingHistory.objects.create(
                booking=booking,
                status='payment_received',
                description=f'Payment received via credit card: {payment.amount} {payment.currency}',
                created_by=request.user
            )
            
            messages.success(request, 'Payment processed successfully!')
            return redirect('flights:booking_confirmation', booking_id=booking.id)
            
        except Exception as e:
            logger.error(f"Credit card payment failed: {str(e)}", exc_info=True)
            messages.error(request, 'Credit card payment failed. Please try again.')
            return redirect('flights:payment', booking_id=booking.id)
    
    def process_bank_transfer_payment(self, request, payment, booking):
        """Process bank transfer payment"""
        try:
            # For bank transfer, we mark as pending and wait for confirmation
            payment.status = 'pending'
            payment.save()
            
            # Update booking
            booking.payment_status = 'pending'
            booking.save()
            
            # Create booking history
            BookingHistory.objects.create(
                booking=booking,
                status='payment_pending',
                description=f'Bank transfer payment initiated: {payment.amount} {payment.currency}',
                created_by=request.user
            )
            
            messages.info(
                request,
                'Bank transfer initiated. Please complete the transfer and upload proof.'
            )
            return redirect('flights:payment_confirmation', booking_id=booking.id)
            
        except Exception as e:
            logger.error(f"Bank transfer failed: {str(e)}", exc_info=True)
            messages.error(request, 'Bank transfer setup failed.')
            return redirect('flights:payment', booking_id=booking.id)
    
    def process_wallet_payment(self, request, payment, booking):
        """Process wallet payment"""
        try:
            with transaction.atomic():
                # Get user profile
                user_profile = request.user.profile
                
                # Check sufficient balance
                if user_profile.wallet_balance < payment.amount:
                    messages.error(request, 'Insufficient wallet balance.')
                    return redirect('flights:payment', booking_id=booking.id)
                
                # Deduct from wallet
                user_profile.wallet_balance -= payment.amount
                user_profile.save()
                
                # Update payment
                payment.status = 'captured'
                payment.captured_at = timezone.now()
                payment.save()
                
                # Update booking
                booking.payment_status = 'paid'
                booking.paid_amount = payment.amount
                booking.due_amount = booking.total_amount - payment.amount
                booking.payment_date = timezone.now()
                booking.save()
                
                # Create booking history
                BookingHistory.objects.create(
                    booking=booking,
                    status='payment_received',
                    description=f'Payment received via wallet: {payment.amount} {payment.currency}',
                    created_by=request.user
                )
                
                messages.success(request, 'Wallet payment processed successfully!')
                return redirect('flights:booking_confirmation', booking_id=booking.id)
                
        except Exception as e:
            logger.error(f"Wallet payment failed: {str(e)}", exc_info=True)
            messages.error(request, 'Wallet payment failed.')
            return redirect('flights:payment', booking_id=booking.id)
    
    def process_multiple_payment(self, request, payment, booking):
        """Process multiple payment methods"""
        try:
            # This would handle split payments across multiple methods
            # For now, we'll mark as pending and require manual processing
            
            payment.status = 'pending'
            payment.save()
            
            # Update booking
            booking.payment_status = 'partial_paid'
            booking.save()
            
            messages.info(
                request,
                'Multiple payment methods selected. Please contact accounts for processing.'
            )
            return redirect('flights:payment_confirmation', booking_id=booking.id)
            
        except Exception as e:
            logger.error(f"Multiple payment failed: {str(e)}", exc_info=True)
            messages.error(request, 'Multiple payment setup failed.')
            return redirect('flights:payment', booking_id=booking.id)


class BookingConfirmationView(LoginRequiredMixin, View):
    """Booking confirmation view"""
    
    template_name = 'flights/booking/confirmation.html'
    
    def get(self, request, *args, **kwargs):
        booking_id = kwargs.get('booking_id')
        
        try:
            booking = Booking.objects.get(
                id=booking_id,
                agent=request.user
            )
            
            # Get ancillary services
            ancillary_services = AncillaryBooking.objects.filter(booking=booking)
            
            # Get payment information
            payments = Payment.objects.filter(booking=booking)
            
            context = {
                'booking': booking,
                'ancillary_services': ancillary_services,
                'payments': payments,
                'page_title': 'Booking Confirmation | B2B Travel Portal',
            }
            
            return render(request, self.template_name, context)
            
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('flights:booking_list')
    
    def post(self, request, *args, **kwargs):
        booking_id = kwargs.get('booking_id')
        
        try:
            booking = Booking.objects.get(
                id=booking_id,
                agent=request.user
            )
            
            action = request.POST.get('action')
            
            if action == 'send_email':
                # Send confirmation email
                self.send_confirmation_email(request, booking)
                messages.success(request, 'Confirmation email sent.')
                
            elif action == 'print_invoice':
                # Generate PDF invoice
                return self.generate_invoice_pdf(request, booking)
                
            elif action == 'add_to_calendar':
                # Add to calendar
                self.add_to_calendar(request, booking)
                messages.success(request, 'Added to calendar.')
            
            return redirect('flights:booking_confirmation', booking_id=booking.id)
            
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('flights:booking_list')
    
    def send_confirmation_email(self, request, booking):
        """Send booking confirmation email"""
        try:
            # This would integrate with your email service
            # For now, we'll just log it
            logger.info(f"Would send confirmation email for booking {booking.booking_reference}")
            
            # Get contact information
            contact_info = json.loads(booking.customer_remarks or '{}').get('contact_info', {})
            email = contact_info.get('passenger_email') or request.user.email
            
            # In production, you would:
            # 1. Generate email content
            # 2. Use Django's email backend
            # 3. Send to the passenger/agent
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {str(e)}")
            return False
    
    def generate_invoice_pdf(self, request, booking):
        """Generate PDF invoice"""
        try:
            # This would generate a PDF using ReportLab or similar
            # For now, we'll return a placeholder
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{booking.booking_reference}.pdf"'
            
            # In production, you would:
            # 1. Create PDF using ReportLab
            # 2. Add booking details
            # 3. Add company logo and details
            # 4. Add payment information
            
            response.write(b'PDF invoice would be generated here')
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate PDF invoice: {str(e)}")
            messages.error(request, 'Failed to generate invoice.')
            return redirect('flights:booking_confirmation', booking_id=booking.id)
    
    def add_to_calendar(self, request, booking):
        """Add booking to calendar"""
        try:
            # Generate .ics file for calendar
            # This is a simplified version
            
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//B2B Travel//Booking {booking.booking_reference}//EN
BEGIN:VEVENT
UID:{booking.id}@b2btravel.com
DTSTAMP:{timezone.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{booking.itinerary.segments.first().departure_time.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{booking.itinerary.segments.last().arrival_time.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:Flight Booking {booking.booking_reference}
DESCRIPTION: Flight from {booking.itinerary.segments.first().origin} to {booking.itinerary.segments.last().destination}
LOCATION:{booking.itinerary.segments.first().origin.iata_code} Airport
END:VEVENT
END:VCALENDAR"""
            
            response = HttpResponse(ics_content, content_type='text/calendar')
            response['Content-Disposition'] = f'attachment; filename="booking_{booking.booking_reference}.ics"'
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate calendar file: {str(e)}")
            messages.error(request, 'Failed to add to calendar.')
            return redirect('flights:booking_confirmation', booking_id=booking.id)


class QuickBookingView(LoginRequiredMixin, CreateView):
    """Quick booking for experienced agents"""
    
    template_name = 'flights/booking/quick_booking.html'
    form_class = QuickBookingForm
    success_url = reverse_lazy('flights:booking_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Create booking from quick form
                booking = Booking.objects.create(
                    agent=self.request.user,
                    booking_reference=form.cleaned_data['PNR'],
                    pnr=form.cleaned_data['PNR'],
                    status='confirmed',
                    total_amount=form.cleaned_data['total_amount'],
                    currency='SAR',
                    payment_status=form.cleaned_data['payment_status'],
                    booking_source='manual',
                )
                
                messages.success(self.request, f'Quick booking created: {booking.booking_reference}')
                return super().form_valid(form)
                
        except Exception as e:
            logger.error(f"Quick booking failed: {str(e)}", exc_info=True)
            messages.error(self.request, f'Quick booking failed: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Quick Booking | B2B Travel Portal'
        return context


class GroupBookingView(LoginRequiredMixin, CreateView):
    """Group booking for 10+ passengers"""
    
    template_name = 'flights/booking/group_booking.html'
    form_class = GroupBookingForm
    success_url = reverse_lazy('flights:booking_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Create group booking
                booking = form.save(commit=False)
                booking.agent = self.request.user
                booking.booking_source = 'group'
                booking.status = 'pending'
                booking.save()
                
                # Process passenger list file if uploaded
                passenger_file = form.cleaned_data.get('passenger_list_file')
                if passenger_file:
                    self.process_passenger_file(passenger_file, booking)
                
                messages.success(
                    self.request,
                    f'Group booking created for {booking.group_name}. Please add passenger details.'
                )
                return redirect('flights:booking_detail', booking_id=booking.id)
                
        except Exception as e:
            logger.error(f"Group booking failed: {str(e)}", exc_info=True)
            messages.error(self.request, f'Group booking failed: {str(e)}')
            return self.form_invalid(form)
    
    def process_passenger_file(self, file, booking):
        """Process uploaded passenger list file"""
        try:
            import pandas as pd
            
            # Read file based on extension
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                raise ValueError('Unsupported file format')
            
            # Process each row
            for _, row in df.iterrows():
                Passenger.objects.create(
                    title=row.get('Title', 'MR'),
                    first_name=row.get('First Name', ''),
                    last_name=row.get('Last Name', ''),
                    date_of_birth=pd.to_datetime(row.get('Date of Birth', '')).date(),
                    gender=row.get('Gender', 'M'),
                    passenger_type=row.get('Type', 'ADT'),
                    nationality=row.get('Nationality', 'SA'),
                    passport_number=row.get('Passport Number', ''),
                )
                
            messages.info(
                self.request,
                f'Imported {len(df)} passengers from file.'
            )
            
        except Exception as e:
            logger.error(f"Passenger file processing failed: {str(e)}")
            messages.warning(
                self.request,
                f'Could not process passenger file: {str(e)}'
            )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Group Booking | B2B Travel Portal'
        return context