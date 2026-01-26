"""
Booking and reservation models for B2B Travel Platform
Production Ready - Final Version
FIXED: related_name clashes with accounts app models
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class Passenger(models.Model):
    """Passenger information with comprehensive details"""
    
    class PassengerType(models.TextChoices):
        ADULT = 'ADT', _('Adult')
        CHILD = 'CHD', _('Child')
        INFANT = 'INF', _('Infant')
        STUDENT = 'STU', _('Student')
        SENIOR = 'SRC', _('Senior Citizen')
        MILITARY = 'MIL', _('Military')
    
    class Title(models.TextChoices):
        MR = 'MR', _('Mr.')
        MRS = 'MRS', _('Mrs.')
        MS = 'MS', _('Ms.')
        MISS = 'MISS', _('Miss')
        DR = 'DR', _('Dr.')
        PROF = 'PROF', _('Prof.')
        SHEIKH = 'SHEIKH', _('Sheikh')
        HAJJ = 'HAJJ', _('Hajj')
        UMRAH = 'UMRAH', _('Umrah')
    
    class Gender(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Personal Information
    title = models.CharField(_('Title'), max_length=10, choices=Title.choices, default=Title.MR)
    first_name = models.CharField(_('First Name'), max_length=100)
    middle_name = models.CharField(_('Middle Name'), max_length=100, blank=True)
    last_name = models.CharField(_('Last Name'), max_length=100)
    arabic_first_name = models.CharField(_('Arabic First Name'), max_length=100, blank=True)
    arabic_last_name = models.CharField(_('Arabic Last Name'), max_length=100, blank=True)
    
    # Demographics
    date_of_birth = models.DateField(_('Date of Birth'))
    gender = models.CharField(_('Gender'), max_length=1, choices=Gender.choices)
    passenger_type = models.CharField(_('Passenger Type'), max_length=3, 
                                     choices=PassengerType.choices, default=PassengerType.ADULT)
    nationality = models.CharField(_('Nationality'), max_length=2)  # ISO country code
    
    # Contact Information
    contact_email = models.EmailField(_('Contact Email'), blank=True)
    contact_phone = models.CharField(_('Contact Phone'), max_length=20, blank=True)
    contact_phone_country = models.CharField(_('Phone Country'), max_length=2, blank=True)
    
    # Document Information
    passport_number = models.CharField(_('Passport Number'), max_length=50, blank=True)
    passport_issuing_country = models.CharField(_('Passport Issuing Country'), max_length=2, blank=True)
    passport_issue_date = models.DateField(_('Passport Issue Date'), null=True, blank=True)
    passport_expiry_date = models.DateField(_('Passport Expiry Date'), null=True, blank=True)
    
    national_id = models.CharField(_('National ID'), max_length=50, blank=True)
    iqama_number = models.CharField(_('Iqama Number'), max_length=50, blank=True)
    iqama_expiry = models.DateField(_('Iqama Expiry'), null=True, blank=True)
    
    # Frequent Flyer Information
    frequent_flyer_number = models.CharField(_('Frequent Flyer Number'), max_length=50, blank=True)
    frequent_flyer_airline = models.ForeignKey('flights.Airline', on_delete=models.SET_NULL, 
                                              null=True, blank=True, 
                                              verbose_name=_('Frequent Flyer Airline'))
    frequent_flyer_tier = models.CharField(_('Frequent Flyer Tier'), max_length=20, blank=True)
    
    # Special Requirements
    special_requests = models.TextField(_('Special Requests'), blank=True)
    meal_preference = models.CharField(_('Meal Preference'), max_length=50, blank=True)
    seat_preference = models.CharField(_('Seat Preference'), max_length=20, blank=True)
    medical_conditions = models.TextField(_('Medical Conditions'), blank=True)
    wheelchair_assistance = models.BooleanField(_('Wheelchair Assistance'), default=False)
    unaccompanied_minor = models.BooleanField(_('Unaccompanied Minor'), default=False)
    
    # Contact Person (for children/elderly)
    emergency_contact_name = models.CharField(_('Emergency Contact Name'), max_length=100, blank=True)
    emergency_contact_phone = models.CharField(_('Emergency Contact Phone'), max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(_('Emergency Contact Relationship'), 
                                                     max_length=50, blank=True)
    
    # Saudi Arabia Specific
    hajj_visa_number = models.CharField(_('Hajj Visa Number'), max_length=50, blank=True)
    umrah_visa_number = models.CharField(_('Umrah Visa Number'), max_length=50, blank=True)
    saudi_entry_date = models.DateField(_('Saudi Entry Date'), null=True, blank=True)
    saudi_exit_date = models.DateField(_('Saudi Exit Date'), null=True, blank=True)
    
    # GDS Information
    gds_passenger_id = models.CharField(_('GDS Passenger ID'), max_length=100, blank=True)
    
    # Metadata
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('passenger')
        verbose_name_plural = _('passengers')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['passport_number']),
            models.Index(fields=['national_id']),
            models.Index(fields=['frequent_flyer_number']),
        ]
    
    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    def get_full_name(self):
        """Get passenger's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        """Calculate passenger's age"""
        today = timezone.now().date()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age
    
    def is_passport_valid(self):
        """Check if passport is valid for travel"""
        if not self.passport_expiry_date:
            return False
        # Passport should be valid for at least 6 months
        six_months_later = timezone.now().date() + timezone.timedelta(days=180)
        return self.passport_expiry_date > six_months_later


class Booking(models.Model):
    """Flight booking/reservation with comprehensive tracking"""
    
    class BookingStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        TICKETED = 'ticketed', _('Ticketed')
        CANCELLED = 'cancelled', _('Cancelled')
        VOIDED = 'voided', _('Voided')
        REFUNDED = 'refunded', _('Refunded')
        PARTIAL_REFUND = 'partial_refund', _('Partially Refunded')
        ON_HOLD = 'on_hold', _('On Hold')
        WAITLISTED = 'waitlisted', _('Waitlisted')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        AUTHORIZED = 'authorized', _('Authorized')
        PAID = 'paid', _('Paid')
        PARTIAL_PAID = 'partial_paid', _('Partially Paid')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')
        CANCELLED = 'cancelled', _('Cancelled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Booking Identification
    booking_reference = models.CharField(_('Booking Reference'), max_length=10, unique=True)
    pnr = models.CharField(_('PNR'), max_length=10, blank=True)  # GDS PNR
    gds_booking_ref = models.CharField(_('GDS Booking Reference'), max_length=100, blank=True)
    
    # Booking Information
    itinerary = models.ForeignKey('FlightItinerary', on_delete=models.PROTECT, 
                                 verbose_name=_('Itinerary'))
    
    # FIXED: Changed related_name to avoid clash with accounts.FlightBooking
    agent = models.ForeignKey('accounts.User', on_delete=models.PROTECT, 
                             related_name='flight_reservations', verbose_name=_('Agent'))
    
    corporate_client = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                        null=True, blank=True, 
                                        related_name='corporate_flight_bookings',
                                        verbose_name=_('Corporate Client'))
    cost_center = models.CharField(_('Cost Center'), max_length=50, blank=True)
    
    # Passenger Information
    passengers = models.ManyToManyField(Passenger, through='BookingPassenger')
    total_passengers = models.PositiveIntegerField(_('Total Passengers'), default=1)
    
    # Status Tracking
    status = models.CharField(_('Status'), max_length=20, 
                             choices=BookingStatus.choices, default=BookingStatus.PENDING)
    payment_status = models.CharField(_('Payment Status'), max_length=20, 
                                     choices=PaymentStatus.choices, 
                                     default=PaymentStatus.PENDING)
    booking_source = models.CharField(_('Booking Source'), max_length=50, 
                                     choices=[('web', 'Web'), ('mobile', 'Mobile'), 
                                             ('api', 'API'), ('manual', 'Manual')],
                                     default='web')
    
    # Pricing Information
    total_amount = models.DecimalField(_('Total Amount'), max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(_('Paid Amount'), max_digits=12, decimal_places=2, default=0)
    due_amount = models.DecimalField(_('Due Amount'), max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Commission & Markup
    commission_amount = models.DecimalField(_('Commission Amount'), max_digits=12, 
                                           decimal_places=2, default=0)
    markup_amount = models.DecimalField(_('Markup Amount'), max_digits=12, 
                                       decimal_places=2, default=0)
    discount_amount = models.DecimalField(_('Discount Amount'), max_digits=12, 
                                         decimal_places=2, default=0)
    
    # Payment Information
    payment_method = models.CharField(_('Payment Method'), max_length=50, blank=True)
    payment_gateway = models.CharField(_('Payment Gateway'), max_length=50, blank=True)
    payment_transaction_id = models.CharField(_('Payment Transaction ID'), max_length=100, blank=True)
    payment_date = models.DateTimeField(_('Payment Date'), null=True, blank=True)
    
    # Ticketing Information
    ticket_time_limit = models.DateTimeField(_('Ticket Time Limit'), null=True, blank=True)
    ticketing_deadline = models.DateTimeField(_('Ticketing Deadline'), null=True, blank=True)
    void_before = models.DateTimeField(_('Void Before'), null=True, blank=True)
    cancellation_deadline = models.DateTimeField(_('Cancellation Deadline'), null=True, blank=True)
    
    # Special Instructions
    special_instructions = models.TextField(_('Special Instructions'), blank=True)
    internal_notes = models.TextField(_('Internal Notes'), blank=True)
    customer_remarks = models.TextField(_('Customer Remarks'), blank=True)
    
    # GDS Configuration
    gds_pcc = models.CharField(_('GDS PCC'), max_length=10, blank=True)
    gds_provider = models.CharField(_('GDS Provider'), max_length=20, default='travelport')
    gds_queue = models.CharField(_('GDS Queue'), max_length=10, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    confirmed_at = models.DateTimeField(_('Confirmed At'), null=True, blank=True)
    ticketed_at = models.DateTimeField(_('Ticketed At'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('Cancelled At'), null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['pnr']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment_status', 'due_amount']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate due amount"""
        if self.total_amount and self.paid_amount:
            self.due_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)
    
    def is_fully_paid(self):
        """Check if booking is fully paid"""
        return self.payment_status == self.PaymentStatus.PAID and self.due_amount <= 0
    
    def can_be_cancelled(self):
        """Check if booking can be cancelled"""
        if self.status in [self.BookingStatus.CANCELLED, self.BookingStatus.VOIDED]:
            return False
        
        if self.cancellation_deadline and timezone.now() > self.cancellation_deadline:
            return False
        
        return True
    
    def get_cancellation_penalty(self):
        """Calculate cancellation penalty"""
        # Implement based on fare rules and cancellation policy
        return Decimal('0.00')
    
    def get_refund_amount(self):
        """Calculate refund amount if cancelled"""
        if not self.can_be_cancelled():
            return Decimal('0.00')
        
        penalty = self.get_cancellation_penalty()
        return max(self.paid_amount - penalty, Decimal('0.00'))


class BookingPassenger(models.Model):
    """Mapping between booking and passengers with seat and fare information"""
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, 
                               verbose_name=_('Booking'))
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, 
                                 verbose_name=_('Passenger'))
    
    # Seat Information
    seat_number = models.CharField(_('Seat Number'), max_length=10, blank=True)
    seat_preference = models.CharField(_('Seat Preference'), max_length=20, blank=True)
    seat_assigned_at = models.DateTimeField(_('Seat Assigned At'), null=True, blank=True)
    
    # Ticket Information
    ticket_number = models.CharField(_('Ticket Number'), max_length=50, blank=True)
    ticket_status = models.CharField(_('Ticket Status'), max_length=20, 
                                    choices=[('open', 'Open'), ('issued', 'Issued'), 
                                            ('voided', 'Voided'), ('refunded', 'Refunded')],
                                    default='open')
    ticket_issue_date = models.DateTimeField(_('Ticket Issue Date'), null=True, blank=True)
    
    # Fare Information
    fare_basis = models.CharField(_('Fare Basis'), max_length=20, blank=True)
    fare_amount = models.DecimalField(_('Fare Amount'), max_digits=12, 
                                     decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(_('Tax Amount'), max_digits=12, 
                                    decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(_('Total Amount'), max_digits=12, 
                                      decimal_places=2, null=True, blank=True)
    
    # Baggage Information
    baggage_allowance = models.JSONField(_('Baggage Allowance'), default=dict, blank=True)
    excess_baggage = models.DecimalField(_('Excess Baggage Amount'), max_digits=10, 
                                        decimal_places=2, default=0)
    
    # Special Services
    meal_preference = models.CharField(_('Meal Preference'), max_length=50, blank=True)
    special_service_request = models.CharField(_('Special Service Request'), max_length=100, blank=True)
    ssr_codes = models.JSONField(_('SSR Codes'), default=list, blank=True)
    
    # Frequent Flyer
    frequent_flyer_applied = models.BooleanField(_('Frequent Flyer Applied'), default=False)
    frequent_flyer_points = models.PositiveIntegerField(_('Frequent Flyer Points'), default=0)
    
    # Check-in Information
    checked_in = models.BooleanField(_('Checked In'), default=False)
    check_in_time = models.DateTimeField(_('Check-in Time'), null=True, blank=True)
    boarding_pass_issued = models.BooleanField(_('Boarding Pass Issued'), default=False)
    boarding_pass_number = models.CharField(_('Boarding Pass Number'), max_length=50, blank=True)
    
    # GDS Information
    gds_passenger_ref = models.CharField(_('GDS Passenger Reference'), max_length=100, blank=True)
    gds_ticket_ref = models.CharField(_('GDS Ticket Reference'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('booking passenger')
        verbose_name_plural = _('booking passengers')
        unique_together = ['booking', 'passenger']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['booking', 'ticket_status']),
        ]
    
    def __str__(self):
        return f"{self.passenger} in {self.booking}"
    
    def is_ticketed(self):
        """Check if passenger is ticketed"""
        return self.ticket_status == 'issued' and self.ticket_number


class PNR(models.Model):
    """PNR (Passenger Name Record) management"""
    
    class PNRStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        CANCELLED = 'cancelled', _('Cancelled')
        TICKETED = 'ticketed', _('Ticketed')
        VOIDED = 'voided', _('Voided')
        HISTORICAL = 'historical', _('Historical')
    
    pnr_number = models.CharField(_('PNR Number'), max_length=10, primary_key=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, 
                               related_name='pnrs', verbose_name=_('Booking'))
    
    # PNR Information
    status = models.CharField(_('Status'), max_length=20, 
                             choices=PNRStatus.choices, default=PNRStatus.ACTIVE)
    creation_date = models.DateTimeField(_('Creation Date'))
    last_modified_date = models.DateTimeField(_('Last Modified Date'), auto_now=True)
    
    # GDS Information
    gds_provider = models.CharField(_('GDS Provider'), max_length=20, default='travelport')
    gds_pcc = models.CharField(_('GDS PCC'), max_length=10)
    gds_queue = models.CharField(_('GDS Queue'), max_length=10, blank=True)
    gds_owner = models.CharField(_('GDS Owner'), max_length=10, blank=True)
    
    # PNR Elements
    pnr_elements = models.JSONField(_('PNR Elements'), default=dict, blank=True)
    segment_information = models.JSONField(_('Segment Information'), default=list, blank=True)
    contact_information = models.JSONField(_('Contact Information'), default=dict, blank=True)
    form_of_payment = models.JSONField(_('Form of Payment'), default=dict, blank=True)
    ticket_information = models.JSONField(_('Ticket Information'), default=list, blank=True)
    remarks = models.JSONField(_('Remarks'), default=list, blank=True)
    
    # Timestamps
    ticketing_deadline = models.DateTimeField(_('Ticketing Deadline'), null=True, blank=True)
    void_before = models.DateTimeField(_('Void Before'), null=True, blank=True)
    
    # Metadata
    is_archived = models.BooleanField(_('Is Archived'), default=False)
    archived_date = models.DateTimeField(_('Archived Date'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('PNR')
        verbose_name_plural = _('PNRs')
        ordering = ['-creation_date']
        indexes = [
            models.Index(fields=['pnr_number', 'status']),
            models.Index(fields=['gds_provider', 'creation_date']),
        ]
    
    def __str__(self):
        return f"PNR: {self.pnr_number}"
    
    def is_active(self):
        """Check if PNR is active"""
        return self.status == self.PNRStatus.ACTIVE
    
    def can_be_ticketed(self):
        """Check if PNR can be ticketed"""
        if self.status != self.PNRStatus.ACTIVE:
            return False
        
        if self.ticketing_deadline and timezone.now() > self.ticketing_deadline:
            return False
        
        return True


class Ticket(models.Model):
    """Air ticket information"""
    
    class TicketStatus(models.TextChoices):
        OPEN = 'open', _('Open')
        ISSUED = 'issued', _('Issued')
        VOIDED = 'voided', _('Voided')
        REFUNDED = 'refunded', _('Refunded')
        EXCHANGED = 'exchanged', _('Exchanged')
        USED = 'used', _('Used')
    
    ticket_number = models.CharField(_('Ticket Number'), max_length=50, primary_key=True)
    booking_passenger = models.ForeignKey(BookingPassenger, on_delete=models.CASCADE, 
                                         related_name='tickets', verbose_name=_('Booking Passenger'))
    pnr = models.ForeignKey(PNR, on_delete=models.CASCADE, 
                           related_name='tickets', verbose_name=_('PNR'))
    
    # Ticket Information
    status = models.CharField(_('Status'), max_length=20, 
                             choices=TicketStatus.choices, default=TicketStatus.OPEN)
    issue_date = models.DateTimeField(_('Issue Date'), null=True, blank=True)
    void_date = models.DateTimeField(_('Void Date'), null=True, blank=True)
    refund_date = models.DateTimeField(_('Refund Date'), null=True, blank=True)
    
    # Fare Information
    fare_amount = models.DecimalField(_('Fare Amount'), max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(_('Tax Amount'), max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(_('Commission Amount'), max_digits=12, 
                                           decimal_places=2, default=0)
    total_amount = models.DecimalField(_('Total Amount'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Flight Information
    flight_coupons = models.JSONField(_('Flight Coupons'), default=list, blank=True)
    validity_period = models.JSONField(_('Validity Period'), default=dict, blank=True)
    endorsement_restrictions = models.TextField(_('Endorsement/Restrictions'), blank=True)
    
    # Payment Information
    form_of_payment = models.CharField(_('Form of Payment'), max_length=50, blank=True)
    payment_reference = models.CharField(_('Payment Reference'), max_length=100, blank=True)
    
    # GDS Information
    gds_ticket_id = models.CharField(_('GDS Ticket ID'), max_length=100, blank=True)
    gds_provider = models.CharField(_('GDS Provider'), max_length=20, default='travelport')
    gds_issuing_pcc = models.CharField(_('GDS Issuing PCC'), max_length=10, blank=True)
    
    # E-Ticket Information
    e_ticket_pdf = models.FileField(_('E-Ticket PDF'), upload_to='e-tickets/%Y/%m/%d/', 
                                   blank=True, null=True)
    itinerary_receipt = models.FileField(_('Itinerary Receipt'), 
                                        upload_to='receipts/%Y/%m/%d/', blank=True, null=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('ticket')
        verbose_name_plural = _('tickets')
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['ticket_number', 'status']),
            models.Index(fields=['pnr', 'status']),
            models.Index(fields=['issue_date']),
        ]
    
    def __str__(self):
        return f"Ticket: {self.ticket_number}"
    
    def is_issued(self):
        """Check if ticket is issued"""
        return self.status == self.TicketStatus.ISSUED and self.issue_date
    
    def can_be_voided(self):
        """Check if ticket can be voided"""
        if self.status != self.TicketStatus.ISSUED:
            return False
        
        # Typically tickets can be voided within 24 hours of issuance
        if self.issue_date:
            void_deadline = self.issue_date + timezone.timedelta(hours=24)
            return timezone.now() < void_deadline
        
        return False
    
    def get_flight_segments(self):
        """Get flight segments from coupons"""
        coupons = self.flight_coupons or []
        return [coupon.get('segment') for coupon in coupons if coupon.get('status') == 'open']


class Payment(models.Model):
    """Payment transactions for bookings"""
    
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'credit_card', _('Credit Card')
        DEBIT_CARD = 'debit_card', _('Debit Card')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        CASH = 'cash', _('Cash')
        CHECK = 'check', _('Check')
        WALLET = 'wallet', _('Wallet')
        CREDIT_LIMIT = 'credit_limit', _('Credit Limit')
        MULTIPLE = 'multiple', _('Multiple Methods')
    
    class PaymentStatus(models.TextChoices):
        INITIATED = 'initiated', _('Initiated')
        PENDING = 'pending', _('Pending')
        AUTHORIZED = 'authorized', _('Authorized')
        CAPTURED = 'captured', _('Captured')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded')
        PARTIAL_REFUND = 'partial_refund', _('Partially Refunded')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, 
                               related_name='payments', verbose_name=_('Booking'))
    
    # Payment Information
    payment_reference = models.CharField(_('Payment Reference'), max_length=50, unique=True)
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Payment Method Details
    payment_method = models.CharField(_('Payment Method'), max_length=20, 
                                     choices=PaymentMethod.choices)
    payment_gateway = models.CharField(_('Payment Gateway'), max_length=50, blank=True)
    gateway_transaction_id = models.CharField(_('Gateway Transaction ID'), max_length=100, blank=True)
    gateway_response = models.JSONField(_('Gateway Response'), default=dict, blank=True)
    
    # Payment Status
    status = models.CharField(_('Status'), max_length=20, 
                             choices=PaymentStatus.choices, default=PaymentStatus.INITIATED)
    authorization_code = models.CharField(_('Authorization Code'), max_length=50, blank=True)
    captured_at = models.DateTimeField(_('Captured At'), null=True, blank=True)
    
    # Card Information (PCI Compliant - store only last 4 digits)
    card_last_four = models.CharField(_('Card Last Four'), max_length=4, blank=True)
    card_type = models.CharField(_('Card Type'), max_length=20, blank=True)
    card_network = models.CharField(_('Card Network'), max_length=20, blank=True)
    
    # Bank Transfer Information
    bank_name = models.CharField(_('Bank Name'), max_length=100, blank=True)
    bank_account = models.CharField(_('Bank Account'), max_length=50, blank=True)
    transfer_reference = models.CharField(_('Transfer Reference'), max_length=100, blank=True)
    
    # Metadata
    description = models.TextField(_('Description'), blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    is_reconciled = models.BooleanField(_('Is Reconciled'), default=False)
    reconciled_at = models.DateTimeField(_('Reconciled At'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_reference']),
            models.Index(fields=['booking', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['gateway_transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_reference} - {self.amount} {self.currency}"
    
    def is_successful(self):
        """Check if payment was successful"""
        return self.status in [self.PaymentStatus.AUTHORIZED, self.PaymentStatus.CAPTURED]
    
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        return (self.is_successful() and 
                self.status != self.PaymentStatus.REFUNDED and
                self.status != self.PaymentStatus.PARTIAL_REFUND)


class Refund(models.Model):
    """Refund transactions"""
    
    class RefundStatus(models.TextChoices):
        REQUESTED = 'requested', _('Requested')
        APPROVED = 'approved', _('Approved')
        PROCESSED = 'processed', _('Processed')
        COMPLETED = 'completed', _('Completed')
        REJECTED = 'rejected', _('Rejected')
        CANCELLED = 'cancelled', _('Cancelled')
    
    class RefundMethod(models.TextChoices):
        ORIGINAL = 'original', _('Original Payment Method')
        CREDIT = 'credit', _('Credit Note')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        CASH = 'cash', _('Cash')
        WALLET = 'wallet', _('Wallet Credit')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, 
                               related_name='refunds', verbose_name=_('Booking'))
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, 
                               related_name='refunds', null=True, blank=True,
                               verbose_name=_('Original Payment'))
    
    # Refund Information
    refund_reference = models.CharField(_('Refund Reference'), max_length=50, unique=True)
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Refund Details
    refund_method = models.CharField(_('Refund Method'), max_length=20, 
                                    choices=RefundMethod.choices)
    status = models.CharField(_('Status'), max_length=20, 
                             choices=RefundStatus.choices, default=RefundStatus.REQUESTED)
    
    # Reason and Approval
    reason = models.TextField(_('Refund Reason'))
    rejection_reason = models.TextField(_('Rejection Reason'), blank=True)
    
    # FIXED: Changed related_name to avoid clash with accounts.Refund
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   null=True, blank=True, 
                                   related_name='flight_refunds_approved',
                                   verbose_name=_('Approved By'))
    
    approved_at = models.DateTimeField(_('Approved At'), null=True, blank=True)
    
    # Processing Information
    processing_fee = models.DecimalField(_('Processing Fee'), max_digits=10, 
                                        decimal_places=2, default=0)
    net_refund_amount = models.DecimalField(_('Net Refund Amount'), max_digits=12, 
                                           decimal_places=2, default=0)
    
    # Bank Information (for bank transfers)
    bank_name = models.CharField(_('Bank Name'), max_length=100, blank=True)
    bank_account = models.CharField(_('Bank Account'), max_length=50, blank=True)
    account_holder = models.CharField(_('Account Holder'), max_length=100, blank=True)
    iban = models.CharField(_('IBAN'), max_length=34, blank=True)
    
    # Wallet Credit (if applicable)
    wallet_credit_id = models.CharField(_('Wallet Credit ID'), max_length=50, blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(_('Requested At'), auto_now_add=True)
    processed_at = models.DateTimeField(_('Processed At'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    
    # Metadata
    notes = models.TextField(_('Notes'), blank=True)
    is_reconciled = models.BooleanField(_('Is Reconciled'), default=False)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('refund')
        verbose_name_plural = _('refunds')
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['refund_reference']),
            models.Index(fields=['booking', 'status']),
            models.Index(fields=['status', 'requested_at']),
        ]
    
    def __str__(self):
        return f"Refund {self.refund_reference} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate net refund amount"""
        if self.amount and self.processing_fee:
            self.net_refund_amount = self.amount - self.processing_fee
        super().save(*args, **kwargs)
    
    def is_completed(self):
        """Check if refund is completed"""
        return self.status == self.RefundStatus.COMPLETED
    
    def can_be_processed(self):
        """Check if refund can be processed"""
        return self.status == self.RefundStatus.APPROVED


class BookingHistory(models.Model):
    """Booking status history and audit trail"""
    
    class HistoryType(models.TextChoices):
        STATUS_CHANGE = 'status_change', _('Status Change')
        PAYMENT_UPDATE = 'payment_update', _('Payment Update')
        PASSENGER_UPDATE = 'passenger_update', _('Passenger Update')
        TICKET_UPDATE = 'ticket_update', _('Ticket Update')
        PRICE_UPDATE = 'price_update', _('Price Update')
        NOTE_ADDED = 'note_added', _('Note Added')
        SYSTEM_EVENT = 'system_event', _('System Event')
        MANUAL_UPDATE = 'manual_update', _('Manual Update')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, 
                               related_name='history', verbose_name=_('Booking'))
    
    # History Information
    history_type = models.CharField(_('History Type'), max_length=20, 
                                   choices=HistoryType.choices)
    description = models.TextField(_('Description'))
    details = models.JSONField(_('Details'), default=dict, blank=True)
    
    # User Information
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  null=True, blank=True, verbose_name=_('Created By'))
    user_type = models.CharField(_('User Type'), max_length=20, 
                                choices=[('agent', 'Agent'), ('admin', 'Admin'), 
                                        ('system', 'System'), ('customer', 'Customer')],
                                default='system')
    
    # IP and Device Information (for audit)
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    device_info = models.JSONField(_('Device Information'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('booking history')
        verbose_name_plural = _('booking histories')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'created_at']),
            models.Index(fields=['history_type', 'created_at']),
            models.Index(fields=['created_by', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.booking} - {self.get_history_type_display()} at {self.created_at}"