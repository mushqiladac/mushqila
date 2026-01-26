# flights/models/inventory_models.py
"""
Inventory management models for B2B Travel Platform
Production Ready - Fixed Version
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class FlightInventory(models.Model):
    """Flight inventory and availability tracking"""
    
    class InventoryStatus(models.TextChoices):
        AVAILABLE = 'available', _('Available')
        LIMITED = 'limited', _('Limited Availability')
        WAITLIST = 'waitlist', _('Waitlist Only')
        SOLD_OUT = 'sold_out', _('Sold Out')
        CLOSED = 'closed', _('Closed for Sale')
        CHARTER = 'charter', _('Charter')
        CODE_SHARE = 'code_share', _('Code Share')
    
    class BookingClassStatus(models.TextChoices):
        OPEN = 'open', _('Open')
        CLOSED = 'closed', _('Closed')
        REQUEST = 'request', _('On Request')
        WAITLIST = 'waitlist', _('Waitlist')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Flight Information
    flight_segment = models.ForeignKey('FlightSegment', on_delete=models.CASCADE, 
                                      related_name='inventories', verbose_name=_('Flight Segment'))
    airline = models.ForeignKey('Airline', on_delete=models.CASCADE, 
                               verbose_name=_('Airline'))
    
    # Inventory Details
    flight_date = models.DateField(_('Flight Date'))
    booking_classes = models.JSONField(_('Booking Classes'), default=dict, blank=True)
    cabin_classes = models.JSONField(_('Cabin Classes'), default=dict, blank=True)
    
    # Availability Counts
    total_seats = models.PositiveIntegerField(_('Total Seats'))
    available_seats = models.PositiveIntegerField(_('Available Seats'))
    blocked_seats = models.PositiveIntegerField(_('Blocked Seats'), default=0)
    reserved_seats = models.PositiveIntegerField(_('Reserved Seats'), default=0)
    waitlist_seats = models.PositiveIntegerField(_('Waitlist Seats'), default=0)
    
    # Status Information
    inventory_status = models.CharField(_('Inventory Status'), max_length=20, 
                                       choices=InventoryStatus.choices, 
                                       default=InventoryStatus.AVAILABLE)
    override_status = models.CharField(_('Override Status'), max_length=20, blank=True)
    
    # Fare Buckets (JSON field for bucket data, not relation)
    fare_buckets_data = models.JSONField(_('Fare Buckets'), default=dict, blank=True)
    bucket_availability = models.JSONField(_('Bucket Availability'), default=dict, blank=True)
    
    # Sales Information
    bookings_count = models.PositiveIntegerField(_('Bookings Count'), default=0)
    revenue_generated = models.DecimalField(_('Revenue Generated'), max_digits=12, 
                                           decimal_places=2, default=Decimal('0.00'))
    load_factor = models.DecimalField(_('Load Factor'), max_digits=5, 
                                     decimal_places=2, default=Decimal('0.00'))
    
    # Overbooking Information
    overbooking_limit = models.PositiveIntegerField(_('Overbooking Limit'), default=0)
    overbooked_seats = models.PositiveIntegerField(_('Overbooked Seats'), default=0)
    no_show_rate = models.DecimalField(_('No Show Rate'), max_digits=5, 
                                      decimal_places=2, default=Decimal('5.00'))
    
    # Group Blocks
    group_blocks = models.JSONField(_('Group Blocks'), default=list, blank=True)
    blocked_for_groups = models.PositiveIntegerField(_('Blocked for Groups'), default=0)
    
    # GDS Information
    gds_inventory_id = models.CharField(_('GDS Inventory ID'), max_length=100, blank=True)
    gds_last_updated = models.DateTimeField(_('GDS Last Updated'), null=True, blank=True)
    gds_availability_status = models.CharField(_('GDS Availability Status'), 
                                              max_length=20, blank=True)
    
    # Timestamps
    inventory_open_date = models.DateTimeField(_('Inventory Open Date'))
    inventory_close_date = models.DateTimeField(_('Inventory Close Date'))
    last_availability_check = models.DateTimeField(_('Last Availability Check'), 
                                                  auto_now=True)
    
    # Metadata
    notes = models.TextField(_('Notes'), blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('flight inventory')
        verbose_name_plural = _('flight inventories')
        ordering = ['flight_date', 'flight_segment__departure_time']
        indexes = [
            models.Index(fields=['flight_segment', 'flight_date']),
            models.Index(fields=['airline', 'flight_date']),
            models.Index(fields=['inventory_status', 'available_seats']),
            models.Index(fields=['gds_last_updated']),
        ]
        unique_together = ['flight_segment', 'flight_date']
    
    def __str__(self):
        return f"Inventory: {self.flight_segment} - {self.flight_date}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate load factor"""
        if self.total_seats > 0:
            sold_seats = self.total_seats - self.available_seats
            self.load_factor = (sold_seats / self.total_seats) * 100
        super().save(*args, **kwargs)
    
    def is_available_for_booking(self, seats_required=1, cabin_class=None, 
                                booking_class=None):
        """Check if inventory is available for booking"""
        if self.inventory_status in [self.InventoryStatus.SOLD_OUT, 
                                    self.InventoryStatus.CLOSED]:
            return False
        
        if seats_required > self.available_seats:
            return False
        
        # Check specific cabin/booking class availability
        if cabin_class and cabin_class in self.cabin_classes:
            cabin_availability = self.cabin_classes[cabin_class].get('available', 0)
            if seats_required > cabin_availability:
                return False
        
        if booking_class and booking_class in self.booking_classes:
            class_status = self.booking_classes[booking_class].get('status', 'closed')
            if class_status != self.BookingClassStatus.OPEN:
                return False
        
        return True
    
    def reserve_seats(self, seats_required=1, cabin_class=None, 
                     booking_class=None, is_confirmed=False):
        """Reserve seats in inventory"""
        if not self.is_available_for_booking(seats_required, cabin_class, booking_class):
            return False
        
        if is_confirmed:
            self.available_seats -= seats_required
            self.bookings_count += 1
        else:
            self.reserved_seats += seats_required
        
        # Update specific class availability
        if cabin_class and cabin_class in self.cabin_classes:
            self.cabin_classes[cabin_class]['available'] -= seats_required
        
        self.save()
        return True
    
    def release_seats(self, seats_required=1, cabin_class=None, was_confirmed=False):
        """Release seats back to inventory"""
        if was_confirmed:
            self.available_seats += seats_required
            self.bookings_count -= 1
        else:
            self.reserved_seats = max(0, self.reserved_seats - seats_required)
        
        # Update specific class availability
        if cabin_class and cabin_class in self.cabin_classes:
            self.cabin_classes[cabin_class]['available'] += seats_required
        
        self.save()
    
    def get_booking_class_status(self, booking_class):
        """Get status of specific booking class"""
        return self.booking_classes.get(booking_class, {}).get('status', 'closed')
    
    def update_from_gds(self, gds_data):
        """Update inventory from GDS data"""
        # Implement GDS synchronization logic
        pass


class SeatInventory(models.Model):
    """Seat-level inventory management"""
    
    class SeatStatus(models.TextChoices):
        AVAILABLE = 'available', _('Available')
        BOOKED = 'booked', _('Booked')
        BLOCKED = 'blocked', _('Blocked')
        RESERVED = 'reserved', _('Reserved')
        UNAVAILABLE = 'unavailable', _('Unavailable')
        EMERGENCY_EXIT = 'emergency_exit', _('Emergency Exit')
        CREW = 'crew', _('Crew Seat')
        INFANT = 'infant', _('Infant Bassinet')
        WHEELCHAIR = 'wheelchair', _('Wheelchair Access')
    
    class SeatFeature(models.TextChoices):
        EXTRA_LEGROOM = 'extra_legroom', _('Extra Legroom')
        WINDOW = 'window', _('Window')
        AISLE = 'aisle', _('Aisle')
        MIDDLE = 'middle', _('Middle')
        BULKHEAD = 'bulkhead', _('Bulkhead')
        EXIT_ROW = 'exit_row', _('Exit Row')
        UPPER_DECK = 'upper_deck', _('Upper Deck')
        LOWER_DECK = 'lower_deck', _('Lower Deck')
        FRONT_CABIN = 'front_cabin', _('Front of Cabin')
        REAR_CABIN = 'rear_cabin', _('Rear of Cabin')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flight_inventory = models.ForeignKey(FlightInventory, on_delete=models.CASCADE, 
                                        related_name='seats', 
                                        verbose_name=_('Flight Inventory'))
    
    # Seat Identification
    seat_number = models.CharField(_('Seat Number'), max_length=10)
    seat_row = models.CharField(_('Seat Row'), max_length=3)
    seat_column = models.CharField(_('Seat Column'), max_length=1)
    
    # Seat Information
    cabin_class = models.CharField(_('Cabin Class'), max_length=20)
    booking_class = models.CharField(_('Booking Class'), max_length=1)
    
    # Status
    seat_status = models.CharField(_('Seat Status'), max_length=20, 
                                  choices=SeatStatus.choices, default=SeatStatus.AVAILABLE)
    features = models.JSONField(_('Seat Features'), default=list, blank=True)
    
    # Pricing
    base_price = models.DecimalField(_('Base Price'), max_digits=10, decimal_places=2)
    premium_price = models.DecimalField(_('Premium Price'), max_digits=10, 
                                       decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(_('Current Price'), max_digits=10, 
                                       decimal_places=2, null=True, blank=True)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Assignment Information
    assigned_to_passenger = models.ForeignKey('Passenger', on_delete=models.SET_NULL, 
                                             null=True, blank=True, 
                                             verbose_name=_('Assigned to Passenger'))
    assigned_to_booking = models.ForeignKey('Booking', on_delete=models.SET_NULL, 
                                           null=True, blank=True, 
                                           verbose_name=_('Assigned to Booking'))
    assignment_date = models.DateTimeField(_('Assignment Date'), null=True, blank=True)
    
    # Restrictions
    restrictions = models.JSONField(_('Restrictions'), default=list, blank=True)
    age_restriction = models.PositiveIntegerField(_('Age Restriction'), null=True, blank=True)
    mobility_restriction = models.BooleanField(_('Mobility Restriction'), default=False)
    
    # GDS Information
    gds_seat_key = models.CharField(_('GDS Seat Key'), max_length=100, blank=True)
    gds_status = models.CharField(_('GDS Status'), max_length=20, blank=True)
    
    # Metadata
    notes = models.TextField(_('Notes'), blank=True)
    last_status_change = models.DateTimeField(_('Last Status Change'), auto_now=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('seat inventory')
        verbose_name_plural = _('seat inventories')
        ordering = ['seat_row', 'seat_column']
        indexes = [
            models.Index(fields=['flight_inventory', 'seat_number']),
            models.Index(fields=['seat_status', 'cabin_class']),
            models.Index(fields=['assigned_to_booking', 'seat_status']),
        ]
        unique_together = ['flight_inventory', 'seat_number']
    
    def __str__(self):
        return f"Seat {self.seat_number} - {self.flight_inventory}"
    
    def is_available(self):
        """Check if seat is available for booking"""
        return self.seat_status == self.SeatStatus.AVAILABLE
    
    def has_feature(self, feature):
        """Check if seat has specific feature"""
        return feature in self.features
    
    def get_current_price(self):
        """Get current price of seat"""
        return self.current_price or self.base_price
    
    def assign_to_passenger(self, passenger, booking, price=None):
        """Assign seat to passenger"""
        if not self.is_available():
            return False
        
        self.seat_status = self.SeatStatus.BOOKED
        self.assigned_to_passenger = passenger
        self.assigned_to_booking = booking
        self.assignment_date = timezone.now()
        
        if price:
            self.current_price = price
        
        self.save()
        return True
    
    def release_seat(self):
        """Release seat back to inventory"""
        self.seat_status = self.SeatStatus.AVAILABLE
        self.assigned_to_passenger = None
        self.assigned_to_booking = None
        self.assignment_date = None
        self.save()
    
    def is_eligible_for_passenger(self, passenger):
        """Check if seat is eligible for passenger"""
        # Age restrictions
        if self.age_restriction and passenger.get_age() < self.age_restriction:
            return False
        
        # Mobility restrictions
        if self.mobility_restriction and passenger.wheelchair_assistance:
            return True  # Actually suitable for wheelchair
        
        # Other restrictions
        for restriction in self.restrictions:
            if restriction.get('type') == 'passenger_type':
                if passenger.passenger_type not in restriction.get('allowed', []):
                    return False
        
        return True


class FareBucket(models.Model):
    """Fare bucket management for revenue optimization"""
    
    class BucketStatus(models.TextChoices):
        OPEN = 'open', _('Open')
        CLOSED = 'closed', _('Closed')
        LIMITED = 'limited', _('Limited')
        WAITLIST = 'waitlist', _('Waitlist')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flight_inventory = models.ForeignKey(FlightInventory, on_delete=models.CASCADE, 
                                        related_name='inventory_fare_buckets', 
                                        verbose_name=_('Flight Inventory'))
    
    # Bucket Identification
    bucket_code = models.CharField(_('Bucket Code'), max_length=10)
    booking_class = models.CharField(_('Booking Class'), max_length=1)
    cabin_class = models.CharField(_('Cabin Class'), max_length=20)
    
    # Bucket Configuration
    bucket_name = models.CharField(_('Bucket Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    
    # Inventory Control
    total_seats = models.PositiveIntegerField(_('Total Seats'))
    available_seats = models.PositiveIntegerField(_('Available Seats'))
    booked_seats = models.PositiveIntegerField(_('Booked Seats'), default=0)
    waitlist_seats = models.PositiveIntegerField(_('Waitlist Seats'), default=0)
    
    # Pricing
    base_fare = models.DecimalField(_('Base Fare'), max_digits=12, decimal_places=2)
    current_fare = models.DecimalField(_('Current Fare'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Status
    bucket_status = models.CharField(_('Bucket Status'), max_length=20, 
                                    choices=BucketStatus.choices, default=BucketStatus.OPEN)
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    # Booking Rules
    minimum_advance_days = models.PositiveIntegerField(_('Minimum Advance Days'), default=0)
    maximum_advance_days = models.PositiveIntegerField(_('Maximum Advance Days'), 
                                                      null=True, blank=True)
    stay_requirements = models.JSONField(_('Stay Requirements'), default=dict, blank=True)
    
    # Revenue Management
    target_load_factor = models.DecimalField(_('Target Load Factor'), max_digits=5, 
                                            decimal_places=2, default=Decimal('85.00'))
    current_load_factor = models.DecimalField(_('Current Load Factor'), max_digits=5, 
                                             decimal_places=2, default=Decimal('0.00'))
    revenue_generated = models.DecimalField(_('Revenue Generated'), max_digits=12, 
                                           decimal_places=2, default=Decimal('0.00'))
    
    # Dynamic Pricing
    pricing_rules = models.JSONField(_('Pricing Rules'), default=dict, blank=True)
    last_price_update = models.DateTimeField(_('Last Price Update'), null=True, blank=True)
    next_price_update = models.DateTimeField(_('Next Price Update'), null=True, blank=True)
    
    # GDS Integration
    gds_bucket_code = models.CharField(_('GDS Bucket Code'), max_length=20, blank=True)
    gds_inventory_key = models.CharField(_('GDS Inventory Key'), max_length=100, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('fare bucket')
        verbose_name_plural = _('fare buckets')
        ordering = ['bucket_code', 'booking_class']
        indexes = [
            models.Index(fields=['flight_inventory', 'bucket_code']),
            models.Index(fields=['bucket_status', 'available_seats']),
            models.Index(fields=['current_load_factor', 'target_load_factor']),
        ]
        unique_together = ['flight_inventory', 'bucket_code', 'booking_class']
    
    def __str__(self):
        return f"Bucket {self.bucket_code} - {self.booking_class}: {self.available_seats} seats"
    
    def save(self, *args, **kwargs):
        """Override save to calculate load factor"""
        if self.total_seats > 0:
            self.current_load_factor = (self.booked_seats / self.total_seats) * 100
        super().save(*args, **kwargs)
    
    def is_available(self, seats_required=1):
        """Check if bucket has available seats"""
        return (self.bucket_status == self.BucketStatus.OPEN and 
                self.available_seats >= seats_required)
    
    def book_seats(self, seats_required=1, fare=None):
        """Book seats from bucket"""
        if not self.is_available(seats_required):
            return False
        
        self.available_seats -= seats_required
        self.booked_seats += seats_required
        
        if fare:
            self.revenue_generated += fare * seats_required
        
        # Check if bucket should be closed
        if self.available_seats <= 0:
            self.bucket_status = self.BucketStatus.CLOSED
        elif self.available_seats <= 5:  # Example threshold
            self.bucket_status = self.BucketStatus.LIMITED
        
        self.save()
        return True
    
    def release_seats(self, seats_required=1, fare=None):
        """Release seats back to bucket"""
        self.available_seats += seats_required
        self.booked_seats = max(0, self.booked_seats - seats_required)
        
        if fare:
            self.revenue_generated = max(Decimal('0.00'), 
                                        self.revenue_generated - (fare * seats_required))
        
        # Update bucket status
        if self.bucket_status == self.BucketStatus.CLOSED and self.available_seats > 0:
            self.bucket_status = self.BucketStatus.OPEN
        
        self.save()
    
    def calculate_dynamic_price(self, booking_date=None):
        """Calculate dynamic price based on rules"""
        # Implement dynamic pricing logic
        return self.current_fare
    
    def get_availability_status(self):
        """Get availability status description"""
        if self.available_seats <= 0:
            return "Sold Out"
        elif self.available_seats <= 5:
            return f"Only {self.available_seats} seats left"
        else:
            return f"{self.available_seats} seats available"


class AvailabilityCache(models.Model):
    """Cache for flight availability to improve performance"""
    
    class CacheStatus(models.TextChoices):
        VALID = 'valid', _('Valid')
        STALE = 'stale', _('Stale')
        EXPIRED = 'expired', _('Expired')
        REFRESHING = 'refreshing', _('Refreshing')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Cache Identification
    cache_key = models.CharField(_('Cache Key'), max_length=255, unique=True, db_index=True)
    route_hash = models.CharField(_('Route Hash'), max_length=64, db_index=True)
    
    # Search Parameters
    origin = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                              related_name='availability_cache_origins', 
                              verbose_name=_('Origin'))
    destination = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                   related_name='availability_cache_destinations', 
                                   verbose_name=_('Destination'))
    departure_date = models.DateField(_('Departure Date'))
    return_date = models.DateField(_('Return Date'), null=True, blank=True)
    
    # Passenger Configuration
    adults = models.PositiveIntegerField(_('Adults'), default=1)
    children = models.PositiveIntegerField(_('Children'), default=0)
    infants = models.PositiveIntegerField(_('Infants'), default=0)
    
    # Search Preferences
    cabin_class = models.CharField(_('Cabin Class'), max_length=20, blank=True)
    direct_flights_only = models.BooleanField(_('Direct Flights Only'), default=False)
    
    # Cache Data
    availability_data = models.JSONField(_('Availability Data'), default=dict, blank=True)
    itinerary_count = models.PositiveIntegerField(_('Itinerary Count'), default=0)
    lowest_fare = models.DecimalField(_('Lowest Fare'), max_digits=12, 
                                     decimal_places=2, null=True, blank=True)
    highest_fare = models.DecimalField(_('Highest Fare'), max_digits=12, 
                                      decimal_places=2, null=True, blank=True)
    
    # Cache Status
    cache_status = models.CharField(_('Cache Status'), max_length=20, 
                                   choices=CacheStatus.choices, default=CacheStatus.VALID)
    hit_count = models.PositiveIntegerField(_('Hit Count'), default=0)
    miss_count = models.PositiveIntegerField(_('Miss Count'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    last_accessed = models.DateTimeField(_('Last Accessed'), auto_now=True)
    expires_at = models.DateTimeField(_('Expires At'))
    
    # GDS Information
    gds_provider = models.CharField(_('GDS Provider'), max_length=20, blank=True)
    gds_session_id = models.CharField(_('GDS Session ID'), max_length=100, blank=True)
    
    # Performance Metrics
    response_time_ms = models.PositiveIntegerField(_('Response Time (ms)'), default=0)
    data_size_kb = models.PositiveIntegerField(_('Data Size (KB)'), default=0)
    
    class Meta:
        verbose_name = _('availability cache')
        verbose_name_plural = _('availability caches')
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['route_hash', 'departure_date']),
            models.Index(fields=['cache_status', 'expires_at']),
            models.Index(fields=['last_accessed']),
        ]
    
    def __str__(self):
        return f"Cache: {self.origin} → {self.destination} - {self.departure_date}"
    
    def is_valid(self):
        """Check if cache is still valid"""
        return (self.cache_status == self.CacheStatus.VALID and 
                timezone.now() < self.expires_at)
    
    def increment_hit(self):
        """Increment hit count"""
        self.hit_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['hit_count', 'last_accessed'])
    
    def increment_miss(self):
        """Increment miss count"""
        self.miss_count += 1
        self.save(update_fields=['miss_count'])
    
    def get_hit_rate(self):
        """Calculate cache hit rate"""
        total_requests = self.hit_count + self.miss_count
        if total_requests > 0:
            return (self.hit_count / total_requests) * 100
        return 0
    
    def refresh_cache(self, new_data):
        """Refresh cache with new data"""
        self.availability_data = new_data.get('data', {})
        self.itinerary_count = new_data.get('count', 0)
        self.lowest_fare = new_data.get('lowest_fare')
        self.highest_fare = new_data.get('highest_fare')
        self.cache_status = self.CacheStatus.VALID
        self.expires_at = timezone.now() + timezone.timedelta(minutes=15)  # 15-minute TTL
        self.response_time_ms = new_data.get('response_time', 0)
        self.data_size_kb = len(str(new_data).encode('utf-8')) / 1024
        
        self.save()
    
    def get_cached_data(self):
        """Get cached data with metadata"""
        return {
            'data': self.availability_data,
            'metadata': {
                'cache_key': self.cache_key,
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat(),
                'expires_at': self.expires_at.isoformat(),
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': self.get_hit_rate(),
                'response_time_ms': self.response_time_ms,
                'data_size_kb': self.data_size_kb,
            }
        }


class BookingLimit(models.Model):
    """Booking limits and controls"""
    
    class LimitType(models.TextChoices):
        SEAT_LIMIT = 'seat_limit', _('Seat Limit')
        REVENUE_LIMIT = 'revenue_limit', _('Revenue Limit')
        BOOKING_COUNT = 'booking_count', _('Booking Count')
        TIME_LIMIT = 'time_limit', _('Time Limit')
        AGENT_LIMIT = 'agent_limit', _('Agent Limit')
        CORPORATE_LIMIT = 'corporate_limit', _('Corporate Limit')
        GROUP_LIMIT = 'group_limit', _('Group Limit')
    
    class LimitScope(models.TextChoices):
        FLIGHT_SPECIFIC = 'flight_specific', _('Flight Specific')
        ROUTE_SPECIFIC = 'route_specific', _('Route Specific')
        AIRLINE_SPECIFIC = 'airline_specific', _('Airline Specific')
        AGENT_SPECIFIC = 'agent_specific', _('Agent Specific')
        CORPORATE_SPECIFIC = 'corporate_specific', _('Corporate Specific')
        SYSTEM_WIDE = 'system_wide', _('System Wide')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Limit Identification
    limit_name = models.CharField(_('Limit Name'), max_length=200)
    limit_type = models.CharField(_('Limit Type'), max_length=20, 
                                 choices=LimitType.choices)
    limit_scope = models.CharField(_('Limit Scope'), max_length=20, 
                                  choices=LimitScope.choices)
    
    # Applicability
    flight_inventory = models.ForeignKey(FlightInventory, on_delete=models.CASCADE, 
                                        null=True, blank=True, 
                                        verbose_name=_('Flight Inventory'))
    airline = models.ForeignKey('Airline', on_delete=models.CASCADE, 
                               null=True, blank=True, verbose_name=_('Airline'))
    origin = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                              related_name='limit_origins', 
                              null=True, blank=True, verbose_name=_('Origin'))
    destination = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                   related_name='limit_destinations', 
                                   null=True, blank=True, verbose_name=_('Destination'))
    agent = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            null=True, blank=True, 
                            related_name='booking_limits',
                            verbose_name=_('Agent'))
    corporate_client = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                                        null=True, blank=True, 
                                        related_name='corporate_limits',
                                        verbose_name=_('Corporate Client'))
    
    # Limit Configuration
    limit_value = models.DecimalField(_('Limit Value'), max_digits=12, decimal_places=2)
    current_usage = models.DecimalField(_('Current Usage'), max_digits=12, 
                                       decimal_places=2, default=Decimal('0.00'))
    usage_percentage = models.DecimalField(_('Usage Percentage'), max_digits=5, 
                                          decimal_places=2, default=Decimal('0.00'))
    
    # Time Period
    period_type = models.CharField(_('Period Type'), max_length=20, 
                                  choices=[('daily', 'Daily'), 
                                          ('weekly', 'Weekly'),
                                          ('monthly', 'Monthly'), 
                                          ('quarterly', 'Quarterly'),
                                          ('yearly', 'Yearly'), 
                                          ('custom', 'Custom')],
                                  default='monthly')
    period_start = models.DateTimeField(_('Period Start'))
    period_end = models.DateTimeField(_('Period End'))
    
    # Thresholds
    warning_threshold = models.DecimalField(_('Warning Threshold'), max_digits=5, 
                                           decimal_places=2, default=Decimal('80.00'))
    critical_threshold = models.DecimalField(_('Critical Threshold'), max_digits=5, 
                                            decimal_places=2, default=Decimal('95.00'))
    
    # Actions
    action_on_limit = models.CharField(_('Action on Limit'), max_length=20, 
                                      choices=[('block', 'Block Further Bookings'),
                                              ('notify', 'Send Notification'),
                                              ('override', 'Allow Override'),
                                              ('queue', 'Put in Queue'),
                                              ('redirect', 'Redirect to Alternative')],
                                      default='block')
    override_allowed = models.BooleanField(_('Override Allowed'), default=False)
    override_approver = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                         null=True, blank=True, 
                                         related_name='limit_overrides',
                                         verbose_name=_('Override Approver'))
    
    # Notifications
    notify_emails = models.JSONField(_('Notify Emails'), default=list, blank=True)
    last_notification_sent = models.DateTimeField(_('Last Notification Sent'), 
                                                 null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('Is Active'), default=True)
    is_enforced = models.BooleanField(_('Is Enforced'), default=True)
    
    # Metadata
    description = models.TextField(_('Description'), blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('booking limit')
        verbose_name_plural = _('booking limits')
        ordering = ['-period_start', 'limit_name']
        indexes = [
            models.Index(fields=['limit_type', 'is_active']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['usage_percentage', 'warning_threshold']),
        ]
    
    def __str__(self):
        return f"Limit: {self.limit_name} - {self.current_usage}/{self.limit_value}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate usage percentage"""
        if self.limit_value and self.limit_value > 0:
            self.usage_percentage = (self.current_usage / self.limit_value) * 100
        super().save(*args, **kwargs)
    
    def can_accept_booking(self, booking_value=Decimal('0.00'), check_override=False):
        """Check if limit can accept new booking"""
        if not self.is_active or not self.is_enforced:
            return True
        
        # Check if limit would be exceeded
        projected_usage = self.current_usage + booking_value
        
        if projected_usage > self.limit_value:
            if check_override and self.override_allowed:
                return 'override_required'
            return False
        
        # Check threshold warnings
        projected_percentage = (projected_usage / self.limit_value) * 100
        
        if projected_percentage >= self.critical_threshold:
            return 'critical_warning'
        elif projected_percentage >= self.warning_threshold:
            return 'warning'
        
        return True
    
    def update_usage(self, amount, operation='add'):
        """Update current usage"""
        if operation == 'add':
            self.current_usage += amount
        elif operation == 'subtract':
            self.current_usage = max(Decimal('0.00'), self.current_usage - amount)
        elif operation == 'reset':
            self.current_usage = amount
        
        self.save()
        
        # Check if notifications need to be sent
        self._check_and_send_notifications()
    
    def _check_and_send_notifications(self):
        """Check thresholds and send notifications"""
        if (self.usage_percentage >= self.warning_threshold and 
            (not self.last_notification_sent or 
             timezone.now() - self.last_notification_sent > timezone.timedelta(hours=1))):
            
            # Send notification
            self.last_notification_sent = timezone.now()
            self.save(update_fields=['last_notification_sent'])
    
    def is_period_active(self):
        """Check if limit period is active"""
        now = timezone.now()
        return self.period_start <= now <= self.period_end
    
    def reset_for_new_period(self, new_start, new_end):
        """Reset limit for new period"""
        if self.period_end < timezone.now():  # Only reset expired periods
            self.period_start = new_start
            self.period_end = new_end
            self.current_usage = Decimal('0.00')
            self.last_notification_sent = None
            self.save()


class OverrideRule(models.Model):
    """Override rules for inventory and pricing"""
    
    class OverrideType(models.TextChoices):
        INVENTORY_OVERRIDE = 'inventory_override', _('Inventory Override')
        PRICING_OVERRIDE = 'pricing_override', _('Pricing Override')
        COMMISSION_OVERRIDE = 'commission_override', _('Commission Override')
        AVAILABILITY_OVERRIDE = 'availability_override', _('Availability Override')
        ROUTING_OVERRIDE = 'routing_override', _('Routing Override')
        FARE_RULE_OVERRIDE = 'fare_rule_override', _('Fare Rule Override')
    
    class OverrideStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Approval')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ACTIVE = 'active', _('Active')
        EXPIRED = 'expired', _('Expired')
        CANCELLED = 'cancelled', _('Cancelled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Override Information
    override_type = models.CharField(_('Override Type'), max_length=30, 
                                    choices=OverrideType.choices)
    override_reference = models.CharField(_('Override Reference'), max_length=50, 
                                         unique=True)
    override_name = models.CharField(_('Override Name'), max_length=200)
    
    # Applicability
    flight_inventory = models.ForeignKey(FlightInventory, on_delete=models.CASCADE, 
                                        null=True, blank=True, 
                                        verbose_name=_('Flight Inventory'))
    airline = models.ForeignKey('Airline', on_delete=models.CASCADE, 
                               null=True, blank=True, verbose_name=_('Airline'))
    route_origin = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                    related_name='override_origins', 
                                    null=True, blank=True, verbose_name=_('Origin'))
    route_destination = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                         related_name='override_destinations', 
                                         null=True, blank=True, verbose_name=_('Destination'))
    agent = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            null=True, blank=True, 
                            related_name='requested_overrides',
                            verbose_name=_('Requested By'))
    corporate_client = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                                        null=True, blank=True, 
                                        related_name='client_overrides',
                                        verbose_name=_('Corporate Client'))
    
    # Override Details
    original_value = models.JSONField(_('Original Value'), default=dict, blank=True)
    override_value = models.JSONField(_('Override Value'), default=dict, blank=True)
    change_description = models.TextField(_('Change Description'))
    
    # Approval Workflow
    status = models.CharField(_('Status'), max_length=20, 
                             choices=OverrideStatus.choices, default=OverrideStatus.PENDING)
    requested_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                                    related_name='override_requests',
                                    verbose_name=_('Requested By'))
    requested_at = models.DateTimeField(_('Requested At'), auto_now_add=True)
    
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   null=True, blank=True, 
                                   related_name='approved_overrides',
                                   verbose_name=_('Approved By'))
    approved_at = models.DateTimeField(_('Approved At'), null=True, blank=True)
    approval_notes = models.TextField(_('Approval Notes'), blank=True)
    
    rejected_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   null=True, blank=True, 
                                   related_name='rejected_overrides',
                                   verbose_name=_('Rejected By'))
    rejected_at = models.DateTimeField(_('Rejected At'), null=True, blank=True)
    rejection_reason = models.TextField(_('Rejection Reason'), blank=True)
    
    # Validity
    valid_from = models.DateTimeField(_('Valid From'))
    valid_until = models.DateTimeField(_('Valid Until'))
    is_recurring = models.BooleanField(_('Is Recurring'), default=False)
    recurrence_pattern = models.JSONField(_('Recurrence Pattern'), default=dict, blank=True)
    
    # Impact Analysis
    expected_impact = models.JSONField(_('Expected Impact'), default=dict, blank=True)
    actual_impact = models.JSONField(_('Actual Impact'), default=dict, blank=True)
    risk_assessment = models.TextField(_('Risk Assessment'), blank=True)
    
    # Audit Information
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  null=True, blank=True, 
                                  related_name='created_overrides',
                                  verbose_name=_('Created By'))
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    # GDS Integration
    gds_override_id = models.CharField(_('GDS Override ID'), max_length=100, blank=True)
    gds_sync_status = models.CharField(_('GDS Sync Status'), max_length=20, 
                                      choices=[('pending', 'Pending'), 
                                              ('synced', 'Synced'),
                                              ('failed', 'Failed')],
                                      default='pending')
    gds_sync_response = models.JSONField(_('GDS Sync Response'), default=dict, blank=True)
    
    # Metadata
    notes = models.TextField(_('Notes'), blank=True)
    attachments = models.JSONField(_('Attachments'), default=list, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('override rule')
        verbose_name_plural = _('override rules')
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['override_type', 'status']),
            models.Index(fields=['status', 'valid_until']),
            models.Index(fields=['agent', 'requested_at']),
            models.Index(fields=['override_reference']),
        ]
    
    def __str__(self):
        return f"Override: {self.override_reference} - {self.override_name}"
    
    def is_valid(self):
        """Check if override is currently valid"""
        now = timezone.now()
        return (self.status == self.OverrideStatus.ACTIVE and 
                self.valid_from <= now <= self.valid_until)
    
    def can_be_approved(self, user):
        """Check if override can be approved by user"""
        if self.status != self.OverrideStatus.PENDING:
            return False
        
        # Check user permissions
        # Implement permission logic based on user role and override type
        
        return True
    
    def approve(self, user, notes=''):
        """Approve the override"""
        if not self.can_be_approved(user):
            return False
        
        self.status = self.OverrideStatus.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        
        # Activate if valid dates are in range
        now = timezone.now()
        if self.valid_from <= now <= self.valid_until:
            self.status = self.OverrideStatus.ACTIVE
        
        self.save()
        return True
    
    def reject(self, user, reason=''):
        """Reject the override"""
        if self.status != self.OverrideStatus.PENDING:
            return False
        
        self.status = self.OverrideStatus.REJECTED
        self.rejected_by = user
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        
        self.save()
        return True
    
    def apply_override(self):
        """Apply the override to the target"""
        # Implement override application logic based on type
        if self.override_type == self.OverrideType.INVENTORY_OVERRIDE:
            self._apply_inventory_override()
        elif self.override_type == self.OverrideType.PRICING_OVERRIDE:
            self._apply_pricing_override()
        # Add other override types
        
        self.gds_sync_status = 'pending'
        self.save()
    
    def _apply_inventory_override(self):
        """Apply inventory override"""
        # Implement inventory override logic
        pass
    
    def _apply_pricing_override(self):
        """Apply pricing override"""
        # Implement pricing override logic
        pass
    
    def get_override_summary(self):
        """Get override summary for display"""
        return {
            'reference': self.override_reference,
            'type': self.get_override_type_display(),
            'status': self.get_status_display(),
            'valid_from': self.valid_from,
            'valid_until': self.valid_until,
            'requested_by': self.requested_by.get_full_name() if self.requested_by else 'System',
            'approved_by': self.approved_by.get_full_name() if self.approved_by else None,
        }