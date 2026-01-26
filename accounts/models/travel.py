"""
Travel service models for B2B Travel Mushqila - Saudi Arabia
Flight, Hotel, Hajj, Umrah, Visa services - Production ready
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class ServiceSupplier(models.Model):
    """Service suppliers (airlines, hotels, etc.)"""
    
    class SupplierType(models.TextChoices):
        AIRLINE = 'airline', _('Airline')
        HOTEL = 'hotel', _('Hotel')
        TRANSPORT = 'transport', _('Transport')
        INSURANCE = 'insurance', _('Insurance')
        VISA = 'visa', _('Visa Service')
        HAJJ = 'hajj', _('Hajj Service')
        UMRAH = 'umrah', _('Umrah Service')
        GUIDE = 'guide', _('Tour Guide')
        OTHER = 'other', _('Other')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('supplier name'), max_length=255)
    name_ar = models.CharField(_('supplier name (Arabic)'), max_length=255, blank=True)
    supplier_type = models.CharField(_('supplier type'), max_length=50, choices=SupplierType.choices)
    code = models.CharField(_('supplier code'), max_length=20, unique=True)
    commission_rate = models.DecimalField(_('commission rate'), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    contact_person = models.CharField(_('contact person'), max_length=255, blank=True)
    contact_email = models.EmailField(_('contact email'), blank=True)
    contact_phone = models.CharField(_('contact phone'), max_length=20, blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('service supplier')
        verbose_name_plural = _('service suppliers')
        ordering = ['name']
        indexes = [
            models.Index(fields=['supplier_type', 'is_active']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_supplier_type_display()})"


class FlightBooking(models.Model):
    """Flight booking model"""
    
    class BookingStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        TICKETED = 'ticketed', _('Ticketed')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded')
        VOID = 'void', _('Void')
    
    class TravelType(models.TextChoices):
        DOMESTIC = 'domestic', _('Domestic')
        INTERNATIONAL = 'international', _('International')
        HAJJ = 'hajj', _('Hajj')
        UMRAH = 'umrah', _('Umrah')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_id = models.CharField(_('booking ID'), max_length=50, unique=True)
    
    # ✅ FIXED: related_name আপডেট
    agent = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts_flight_bookings')
    
    passenger_name = models.CharField(_('passenger name'), max_length=255)
    passenger_name_ar = models.CharField(_('passenger name (Arabic)'), max_length=255, blank=True)
    passenger_email = models.EmailField(_('passenger email'), blank=True)
    passenger_phone = models.CharField(_('passenger phone'), max_length=20, blank=True)
    
    airline = models.ForeignKey(ServiceSupplier, on_delete=models.PROTECT, related_name='accounts_flights', limit_choices_to={'supplier_type': 'airline'})
    flight_number = models.CharField(_('flight number'), max_length=20)
    departure_city = models.CharField(_('departure city'), max_length=100)
    arrival_city = models.CharField(_('arrival city'), max_length=100)
    departure_airport = models.CharField(_('departure airport'), max_length=10)
    arrival_airport = models.CharField(_('arrival airport'), max_length=10)
    
    departure_date = models.DateTimeField(_('departure date'))
    arrival_date = models.DateTimeField(_('arrival date'))
    travel_type = models.CharField(_('travel type'), max_length=20, choices=TravelType.choices, default=TravelType.DOMESTIC)
    booking_class = models.CharField(_('booking class'), max_length=10)
    
    base_fare = models.DecimalField(_('base fare'), max_digits=10, decimal_places=2)
    tax = models.DecimalField(_('tax'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vat = models.DecimalField(_('VAT'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(_('commission amount'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_('status'), max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    pnr = models.CharField(_('PNR'), max_length=10, blank=True)
    ticket_number = models.CharField(_('ticket number'), max_length=20, blank=True)
    booking_notes = models.TextField(_('booking notes'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('flight booking')
        verbose_name_plural = _('flight bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_id']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['departure_date']),
            models.Index(fields=['pnr']),
        ]
    
    def __str__(self):
        return f"{self.booking_id} - {self.passenger_name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_id:
            import time
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:6].upper()
            self.booking_id = f"FLT{timestamp}{unique_id}"
        
        if not self.total_amount:
            self.total_amount = self.base_fare + self.tax + self.vat
        
        super().save(*args, **kwargs)
    
    def calculate_commission(self):
        """Calculate commission for this booking"""
        from decimal import Decimal
        if self.agent.commission_rate:
            commission_rate = self.agent.commission_rate
            if self.travel_type == 'hajj':
                commission_rate *= Decimal('1.2')
            elif self.travel_type == 'umrah':
                commission_rate *= Decimal('1.15')
            
            self.commission_amount = (self.base_fare * commission_rate) / Decimal('100')
        return self.commission_amount


class HotelBooking(models.Model):
    """Hotel booking model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_id = models.CharField(_('booking ID'), max_length=50, unique=True)
    
    # ✅ FIXED: related_name আপডেট
    agent = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts_hotel_bookings')
    
    hotel = models.ForeignKey(ServiceSupplier, on_delete=models.PROTECT, related_name='accounts_hotel_bookings', limit_choices_to={'supplier_type': 'hotel'})
    
    guest_name = models.CharField(_('guest name'), max_length=255)
    guest_email = models.EmailField(_('guest email'), blank=True)
    guest_phone = models.CharField(_('guest phone'), max_length=20, blank=True)
    
    check_in = models.DateField(_('check in'))
    check_out = models.DateField(_('check out'))
    nights = models.IntegerField(_('nights'), default=1)
    rooms = models.IntegerField(_('number of rooms'), default=1)
    adults = models.IntegerField(_('adults'), default=1)
    children = models.IntegerField(_('children'), default=0)
    
    room_rate = models.DecimalField(_('room rate'), max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(_('commission amount'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_('status'), max_length=20, choices=FlightBooking.BookingStatus.choices, default=FlightBooking.BookingStatus.PENDING)
    confirmation_number = models.CharField(_('confirmation number'), max_length=50, blank=True)
    booking_notes = models.TextField(_('booking notes'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('hotel booking')
        verbose_name_plural = _('hotel bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_id']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['check_in']),
        ]
    
    def __str__(self):
        return f"{self.booking_id} - {self.guest_name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_id:
            import time
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:6].upper()
            self.booking_id = f"HOT{timestamp}{unique_id}"
        
        if not self.total_amount:
            self.total_amount = self.room_rate * self.rooms * self.nights
        
        if not self.nights and self.check_in and self.check_out:
            self.nights = (self.check_out - self.check_in).days
        
        super().save(*args, **kwargs)


class HajjPackage(models.Model):
    """Hajj package model"""
    
    class PackageStatus(models.TextChoices):
        AVAILABLE = 'available', _('Available')
        SOLD_OUT = 'sold_out', _('Sold Out')
        COMING_SOON = 'coming_soon', _('Coming Soon')
        INACTIVE = 'inactive', _('Inactive')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package_code = models.CharField(_('package code'), max_length=50, unique=True)
    name = models.CharField(_('package name'), max_length=255)
    name_ar = models.CharField(_('package name (Arabic)'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    description_ar = models.TextField(_('description (Arabic)'), blank=True)
    
    duration_days = models.IntegerField(_('duration (days)'), default=30)
    hajj_year = models.IntegerField(_('hajj year'))
    
    # Accommodation
    makkah_hotel = models.CharField(_('makkah hotel'), max_length=255, blank=True)
    makkah_hotel_distance = models.CharField(_('makkah hotel distance'), max_length=50, blank=True)
    madinah_hotel = models.CharField(_('madinah hotel'), max_length=255, blank=True)
    madinah_hotel_distance = models.CharField(_('madinah hotel distance'), max_length=50, blank=True)
    
    # Transportation
    flight_included = models.BooleanField(_('flight included'), default=True)
    transport_included = models.BooleanField(_('transport included'), default=True)
    
    # Pricing
    base_price = models.DecimalField(_('base price'), max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(_('commission rate'), max_digits=5, decimal_places=2, default=Decimal('15.00'))
    available_slots = models.IntegerField(_('available slots'), default=0)
    total_slots = models.IntegerField(_('total slots'), default=0)
    
    status = models.CharField(_('status'), max_length=20, choices=PackageStatus.choices, default=PackageStatus.AVAILABLE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('hajj package')
        verbose_name_plural = _('hajj packages')
        ordering = ['-hajj_year', 'base_price']
    
    def __str__(self):
        return f"{self.package_code} - {self.name}"


class UmrahPackage(models.Model):
    """Umrah package model"""
    
    class PackageType(models.TextChoices):
        ECONOMY = 'economy', _('Economy')
        STANDARD = 'standard', _('Standard')
        DELUXE = 'deluxe', _('Deluxe')
        PREMIUM = 'premium', _('Premium')
        LUXURY = 'luxury', _('Luxury')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package_code = models.CharField(_('package code'), max_length=50, unique=True)
    name = models.CharField(_('package name'), max_length=255)
    name_ar = models.CharField(_('package name (Arabic)'), max_length=255)
    package_type = models.CharField(_('package type'), max_length=20, choices=PackageType.choices, default=PackageType.STANDARD)
    
    duration_days = models.IntegerField(_('duration (days)'), default=15)
    validity_from = models.DateField(_('validity from'))
    validity_to = models.DateField(_('validity to'))
    
    # Accommodation
    makkah_hotel = models.CharField(_('makkah hotel'), max_length=255)
    makkah_nights = models.IntegerField(_('makkah nights'), default=7)
    madinah_hotel = models.CharField(_('madinah hotel'), max_length=255, blank=True)
    madinah_nights = models.IntegerField(_('madinah nights'), default=0)
    
    # Inclusions
    flight_included = models.BooleanField(_('flight included'), default=True)
    visa_included = models.BooleanField(_('visa included'), default=True)
    transport_included = models.BooleanField(_('transport included'), default=True)
    ziyarat_included = models.BooleanField(_('ziyarat included'), default=True)
    
    # Pricing
    base_price = models.DecimalField(_('base price'), max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(_('commission rate'), max_digits=5, decimal_places=2, default=Decimal('12.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('umrah package')
        verbose_name_plural = _('umrah packages')
        ordering = ['package_type', 'base_price']
    
    def __str__(self):
        return f"{self.package_code} - {self.name}"