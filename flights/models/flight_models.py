# flights/models/flight_models.py
"""
Core flight models for B2B Travel Platform
Integrated with Travelport Galileo GDS
Production Ready - Final Version
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid
import json


class Airline(models.Model):
    """Airline information with GDS integration"""
    
    class AirlineType(models.TextChoices):
        SCHEDULED = 'scheduled', _('Scheduled')
        CHARTER = 'charter', _('Charter')
        LOW_COST = 'low_cost', _('Low Cost')
        REGIONAL = 'regional', _('Regional')
    
    code = models.CharField(_('IATA Code'), max_length=2, primary_key=True)
    iata_code = models.CharField(_('3-Letter IATA'), max_length=3, unique=True)
    icao_code = models.CharField(_('ICAO Code'), max_length=4, unique=True)
    name = models.CharField(_('Airline Name'), max_length=200)
    name_ar = models.CharField(_('Arabic Name'), max_length=200, blank=True)
    airline_type = models.CharField(_('Airline Type'), max_length=20, 
                                   choices=AirlineType.choices, 
                                   default=AirlineType.SCHEDULED)
    country = models.CharField(_('Country'), max_length=100)
    country_code = models.CharField(_('Country Code'), max_length=2)
    logo = models.ImageField(_('Logo'), upload_to='airlines/logos/', blank=True, null=True)
    
    # GDS Integration Fields
    gds_carrier_code = models.CharField(_('GDS Carrier Code'), max_length=10, blank=True)
    travelport_code = models.CharField(_('Travelport Code'), max_length=10, blank=True)
    sabre_code = models.CharField(_('Sabre Code'), max_length=10, blank=True)
    amadeus_code = models.CharField(_('Amadeus Code'), max_length=10, blank=True)
    
    # Operational Fields
    is_active = models.BooleanField(_('Is Active'), default=True)
    commission_rate = models.DecimalField(_('Commission Rate'), max_digits=5, 
                                         decimal_places=2, default=Decimal('0.00'))
    preferred_supplier = models.BooleanField(_('Preferred Supplier'), default=False)
    baggage_policy_url = models.URLField(_('Baggage Policy URL'), blank=True)
    contact_email = models.EmailField(_('Contact Email'), blank=True)
    contact_phone = models.CharField(_('Contact Phone'), max_length=20, blank=True)
    
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('airline')
        verbose_name_plural = _('airlines')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['country', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_gds_code(self, gds_provider='travelport'):
        """Get GDS specific carrier code"""
        gds_map = {
            'travelport': self.travelport_code or self.gds_carrier_code,
            'sabre': self.sabre_code or self.gds_carrier_code,
            'amadeus': self.amadeus_code or self.gds_carrier_code,
        }
        return gds_map.get(gds_provider, self.code)


class Airport(models.Model):
    """Airport information with comprehensive details"""
    
    class AirportType(models.TextChoices):
        INTERNATIONAL = 'international', _('International')
        DOMESTIC = 'domestic', _('Domestic')
        REGIONAL = 'regional', _('Regional')
        MILITARY = 'military', _('Military')
    
    iata_code = models.CharField(_('IATA Code'), max_length=3, primary_key=True)
    icao_code = models.CharField(_('ICAO Code'), max_length=4, unique=True)
    name = models.CharField(_('Airport Name'), max_length=200)
    name_ar = models.CharField(_('Arabic Name'), max_length=200, blank=True)
    city = models.CharField(_('City'), max_length=100)
    city_ar = models.CharField(_('Arabic City'), max_length=100, blank=True)
    country = models.CharField(_('Country'), max_length=100)
    country_code = models.CharField(_('Country Code'), max_length=2)
    region = models.CharField(_('Region'), max_length=100, blank=True)
    airport_type = models.CharField(_('Airport Type'), max_length=20, 
                                   choices=AirportType.choices, 
                                   default=AirportType.INTERNATIONAL)
    
    # Geographical Information
    timezone = models.CharField(_('Timezone'), max_length=50)
    latitude = models.DecimalField(_('Latitude'), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_('Longitude'), max_digits=9, decimal_places=6)
    elevation = models.IntegerField(_('Elevation (ft)'), null=True, blank=True)
    
    # Operational Information
    is_active = models.BooleanField(_('Is Active'), default=True)
    has_international = models.BooleanField(_('Has International Flights'), default=True)
    has_domestic = models.BooleanField(_('Has Domestic Flights'), default=True)
    number_of_terminals = models.PositiveIntegerField(_('Number of Terminals'), default=1)
    number_of_runways = models.PositiveIntegerField(_('Number of Runways'), default=1)
    
    # Contact Information
    website = models.URLField(_('Website'), blank=True)
    contact_phone = models.CharField(_('Contact Phone'), max_length=20, blank=True)
    emergency_phone = models.CharField(_('Emergency Phone'), max_length=20, blank=True)
    
    # GDS Information
    gds_codes = models.JSONField(_('GDS Codes'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('airport')
        verbose_name_plural = _('airports')
        ordering = ['city', 'name']
        indexes = [
            models.Index(fields=['iata_code', 'is_active']),
            models.Index(fields=['city', 'country']),
            models.Index(fields=['country_code', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.iata_code} - {self.name}, {self.city}"
    
    def get_gds_code(self, gds_provider='travelport'):
        """Get GDS specific airport code"""
        return self.gds_codes.get(gds_provider, self.iata_code)
    
    def is_saudi_airport(self):
        """Check if airport is in Saudi Arabia"""
        return self.country_code == 'SA'


class Aircraft(models.Model):
    """Aircraft type information"""
    
    icao_code = models.CharField(_('ICAO Code'), max_length=4, primary_key=True)
    iata_code = models.CharField(_('IATA Code'), max_length=3, unique=True)
    manufacturer = models.CharField(_('Manufacturer'), max_length=100)
    model = models.CharField(_('Model'), max_length=100)
    name = models.CharField(_('Aircraft Name'), max_length=100)
    
    # Specifications
    wake_category = models.CharField(_('Wake Category'), max_length=1, 
                                    choices=[('L', 'Light'), ('M', 'Medium'), ('H', 'Heavy')])
    engine_type = models.CharField(_('Engine Type'), max_length=50, blank=True)
    engine_count = models.PositiveIntegerField(_('Engine Count'), default=2)
    
    # Capacity
    max_passengers = models.PositiveIntegerField(_('Max Passengers'))
    typical_seating = models.JSONField(_('Typical Seating'), default=dict, blank=True)
    cargo_capacity = models.DecimalField(_('Cargo Capacity (kg)'), max_digits=10, 
                                        decimal_places=2, null=True, blank=True)
    
    # Dimensions
    length = models.DecimalField(_('Length (m)'), max_digits=6, decimal_places=2)
    wingspan = models.DecimalField(_('Wingspan (m)'), max_digits=6, decimal_places=2)
    height = models.DecimalField(_('Height (m)'), max_digits=6, decimal_places=2)
    
    # Performance
    range_km = models.PositiveIntegerField(_('Range (km)'))
    cruise_speed = models.PositiveIntegerField(_('Cruise Speed (km/h)'))
    max_speed = models.PositiveIntegerField(_('Max Speed (km/h)'))
    
    # GDS Information
    gds_equipment_codes = models.JSONField(_('GDS Equipment Codes'), default=dict, blank=True)
    
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('aircraft')
        verbose_name_plural = _('aircraft')
        ordering = ['manufacturer', 'model']
    
    def __str__(self):
        return f"{self.icao_code} - {self.manufacturer} {self.model}"


class FlightSearch(models.Model):
    """Flight search queries with comprehensive tracking"""
    
    class SearchType(models.TextChoices):
        ONE_WAY = 'one_way', _('One Way')
        ROUND_TRIP = 'round_trip', _('Round Trip')
        MULTI_CITY = 'multi_city', _('Multi City')
        OPEN_JAW = 'open_jaw', _('Open Jaw')
    
    class CabinClass(models.TextChoices):
        ECONOMY = 'economy', _('Economy')
        PREMIUM_ECONOMY = 'premium_economy', _('Premium Economy')
        BUSINESS = 'business', _('Business')
        FIRST = 'first', _('First Class')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                           related_name='flight_searches', verbose_name=_('User'))
    search_type = models.CharField(_('Search Type'), max_length=20, 
                                  choices=SearchType.choices, default=SearchType.ONE_WAY)
    
    # Search Parameters
    origin = models.ForeignKey(Airport, on_delete=models.PROTECT, 
                              related_name='search_origins', verbose_name=_('Origin'))
    destination = models.ForeignKey(Airport, on_delete=models.PROTECT, 
                                   related_name='search_destinations', verbose_name=_('Destination'))
    departure_date = models.DateField(_('Departure Date'))
    return_date = models.DateField(_('Return Date'), null=True, blank=True)
    
    # Passenger Configuration
    adults = models.PositiveIntegerField(_('Adults'), default=1)
    children = models.PositiveIntegerField(_('Children'), default=0)
    infants = models.PositiveIntegerField(_('Infants'), default=0)
    infant_on_lap = models.BooleanField(_('Infant on Lap'), default=False)
    
    # Search Preferences
    cabin_class = models.CharField(_('Cabin Class'), max_length=20, 
                                  choices=CabinClass.choices, default=CabinClass.ECONOMY)
    direct_flights_only = models.BooleanField(_('Direct Flights Only'), default=False)
    max_stops = models.PositiveIntegerField(_('Maximum Stops'), default=2)
    flexible_dates = models.BooleanField(_('Flexible Dates'), default=False)
    flexible_plus_minus = models.PositiveIntegerField(_('Flexible Days +/-'), default=3)
    include_nearby_airports = models.BooleanField(_('Include Nearby Airports'), default=False)
    
    # Airline Preferences
    preferred_airlines = models.ManyToManyField(Airline, blank=True, 
                                               verbose_name=_('Preferred Airlines'))
    excluded_airlines = models.ManyToManyField(Airline, blank=True, 
                                              related_name='excluded_searches',
                                              verbose_name=_('Excluded Airlines'))
    
    # Fare Preferences
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    max_price = models.DecimalField(_('Maximum Price'), max_digits=12, 
                                   decimal_places=2, null=True, blank=True)
    min_price = models.DecimalField(_('Minimum Price'), max_digits=12, 
                                   decimal_places=2, null=True, blank=True)
    
    # GDS Configuration
    gds_providers = models.JSONField(_('GDS Providers'), default=list, blank=True)
    search_hash = models.CharField(_('Search Hash'), max_length=64, unique=True, 
                                  db_index=True)
    
    # Results Tracking
    results_count = models.PositiveIntegerField(_('Results Count'), default=0)
    search_duration = models.DurationField(_('Search Duration'), null=True, blank=True)
    cached_until = models.DateTimeField(_('Cached Until'), null=True, blank=True)
    
    # Analytics
    user_agent = models.TextField(_('User Agent'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    device_type = models.CharField(_('Device Type'), max_length=50, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('flight search')
        verbose_name_plural = _('flight searches')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['search_hash']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['origin', 'destination', 'departure_date']),
            models.Index(fields=['cached_until']),
        ]
    
    def __str__(self):
        return f"{self.origin} → {self.destination} - {self.departure_date}"
    
    def get_total_passengers(self):
        """Calculate total number of passengers"""
        return self.adults + self.children + self.infants
    
    def is_round_trip(self):
        """Check if search is round trip"""
        return self.search_type == self.SearchType.ROUND_TRIP and self.return_date
    
    def get_search_params(self):
        """Get search parameters as dictionary"""
        return {
            'search_type': self.search_type,
            'origin': self.origin.iata_code,
            'destination': self.destination.iata_code,
            'departure_date': self.departure_date.isoformat(),
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'adults': self.adults,
            'children': self.children,
            'infants': self.infants,
            'cabin_class': self.cabin_class,
            'currency': self.currency,
        }


class FlightSegment(models.Model):
    """Individual flight segment with GDS integration"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Flight Information
    flight_number = models.CharField(_('Flight Number'), max_length=10)
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, 
                               verbose_name=_('Airline'))
    
    # Route Information
    origin = models.ForeignKey(Airport, on_delete=models.PROTECT, 
                              related_name='segment_origins', verbose_name=_('Origin'))
    destination = models.ForeignKey(Airport, on_delete=models.PROTECT, 
                                   related_name='segment_destinations', verbose_name=_('Destination'))
    
    # Schedule Information
    departure_time = models.DateTimeField(_('Departure Time'))
    arrival_time = models.DateTimeField(_('Arrival Time'))
    duration = models.DurationField(_('Duration'))
    
    # Aircraft Information
    aircraft = models.ForeignKey(Aircraft, on_delete=models.SET_NULL, 
                                null=True, blank=True, verbose_name=_('Aircraft'))
    aircraft_type = models.CharField(_('Aircraft Type'), max_length=10, blank=True)
    
    # Cabin Information
    cabin_class = models.CharField(_('Cabin Class'), max_length=20)
    booking_class = models.CharField(_('Booking Class'), max_length=1)
    fare_basis = models.CharField(_('Fare Basis'), max_length=20, blank=True)
    
    # Operational Information
    stop_count = models.PositiveIntegerField(_('Stop Count'), default=0)
    stop_cities = models.JSONField(_('Stop Cities'), default=list, blank=True)
    mileage = models.PositiveIntegerField(_('Mileage'), default=0)
    operated_by = models.ForeignKey(Airline, on_delete=models.PROTECT, 
                                  related_name='operated_segments', 
                                  null=True, blank=True, verbose_name=_('Operated By'))
    code_share = models.BooleanField(_('Code Share'), default=False)
    code_share_flight_number = models.CharField(_('Code Share Flight Number'), 
                                               max_length=10, blank=True)
    
    # GDS Integration
    gds_segment_id = models.CharField(_('GDS Segment ID'), max_length=100, blank=True)
    gds_provider = models.CharField(_('GDS Provider'), max_length=20, default='travelport')
    gds_status = models.CharField(_('GDS Status'), max_length=20, 
                                 choices=[('active', 'Active'), ('canceled', 'Canceled')], 
                                 default='active')
    
    # Metadata
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('flight segment')
        verbose_name_plural = _('flight segments')
        ordering = ['departure_time']
        indexes = [
            models.Index(fields=['airline', 'flight_number', 'departure_time']),
            models.Index(fields=['origin', 'destination', 'departure_time']),
            models.Index(fields=['gds_segment_id']),
        ]
    
    def __str__(self):
        return f"{self.airline.code}{self.flight_number}: {self.origin} → {self.destination}"
    
    def get_flight_designator(self):
        """Get flight designator (airline code + flight number)"""
        return f"{self.airline.code}{self.flight_number}"
    
    def is_direct(self):
        """Check if segment is direct (no stops)"""
        return self.stop_count == 0
    
    def get_stop_duration(self):
        """Calculate stop duration if applicable"""
        if self.stop_count > 0 and 'stop_times' in self.metadata:
            return sum(stop['duration'] for stop in self.metadata['stop_times'])
        return None


class FlightItinerary(models.Model):
    """Complete flight itinerary with pricing"""
    
    class FareType(models.TextChoices):
        PUBLISHED = 'published', _('Published Fare')
        PRIVATE = 'private', _('Private Fare')
        NET = 'net', _('Net Fare')
        NEGOTIATED = 'negotiated', _('Negotiated Fare')
        CORPORATE = 'corporate', _('Corporate Fare')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    search = models.ForeignKey(FlightSearch, on_delete=models.CASCADE, 
                              related_name='itineraries', verbose_name=_('Search'))
    
    # Itinerary Information
    segments = models.ManyToManyField(FlightSegment, through='ItinerarySegment')
    total_duration = models.DurationField(_('Total Duration'))
    total_stops = models.PositiveIntegerField(_('Total Stops'), default=0)
    layover_times = models.JSONField(_('Layover Times'), default=list, blank=True)
    
    # Fare Conditions
    is_refundable = models.BooleanField(_('Is Refundable'), default=False)
    is_changeable = models.BooleanField(_('Is Changeable'), default=False)
    is_routable = models.BooleanField(_('Is Routable'), default=True)
    has_baggage = models.BooleanField(_('Has Baggage'), default=True)
    has_meal = models.BooleanField(_('Has Meal'), default=True)
    
    # Cabin Information
    cabin_class = models.CharField(_('Cabin Class'), max_length=20)
    fare_type = models.CharField(_('Fare Type'), max_length=50, 
                                choices=FareType.choices, default=FareType.PUBLISHED)
    
    # Pricing Information
    base_fare = models.DecimalField(_('Base Fare'), max_digits=12, decimal_places=2)
    tax = models.DecimalField(_('Tax'), max_digits=12, decimal_places=2)
    fees = models.DecimalField(_('Fees'), max_digits=12, decimal_places=2, default=0)
    total_fare = models.DecimalField(_('Total Fare'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Commission & Markup
    commission_amount = models.DecimalField(_('Commission Amount'), max_digits=12, 
                                           decimal_places=2, default=0)
    commission_rate = models.DecimalField(_('Commission Rate'), max_digits=5, 
                                         decimal_places=2, default=0)
    markup_amount = models.DecimalField(_('Markup Amount'), max_digits=12, 
                                       decimal_places=2, default=0)
    markup_rate = models.DecimalField(_('Markup Rate'), max_digits=5, 
                                     decimal_places=2, default=0)
    
    # Agent Pricing
    agent_price = models.DecimalField(_('Agent Price'), max_digits=12, decimal_places=2)
    customer_price = models.DecimalField(_('Customer Price'), max_digits=12, 
                                        decimal_places=2, null=True, blank=True)
    
    # Ticketing Information
    last_ticketing_date = models.DateTimeField(_('Last Ticketing Date'), 
                                              null=True, blank=True)
    minimum_connection_time = models.PositiveIntegerField(_('Minimum Connection Time (min)'), 
                                                         default=60)
    
    # GDS Integration
    gds_pcc = models.CharField(_('GDS PCC'), max_length=10, blank=True)
    gds_provider = models.CharField(_('GDS Provider'), max_length=20, default='travelport')
    gds_offer_id = models.CharField(_('GDS Offer ID'), max_length=100, blank=True)
    gds_fare_calc = models.TextField(_('GDS Fare Calculation'), blank=True)
    
    # Validity
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'))
    
    # Metadata
    fare_rules = models.JSONField(_('Fare Rules'), default=dict, blank=True)
    baggage_info = models.JSONField(_('Baggage Info'), default=dict, blank=True)
    restrictions = models.JSONField(_('Restrictions'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('flight itinerary')
        verbose_name_plural = _('flight itineraries')
        ordering = ['total_fare']
        indexes = [
            models.Index(fields=['search', 'total_fare']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['gds_offer_id']),
        ]
    
    def __str__(self):
        return f"Itinerary {self.id} - {self.total_fare} {self.currency}"
    
    def is_expired(self):
        """Check if itinerary is expired"""
        return timezone.now() > self.expires_at
    
    def get_total_passengers(self):
        """Get total passengers from search"""
        return self.search.get_total_passengers()
    
    def get_total_price(self):
        """Calculate total price for all passengers"""
        return self.total_fare * self.get_total_passengers()
    
    def get_agent_commission(self):
        """Calculate total commission for agent"""
        return self.commission_amount * self.get_total_passengers()
    
    def get_segments_ordered(self):
        """Get segments in correct order"""
        return self.segments.all().order_by('itinerarysegment__segment_order')


class ItinerarySegment(models.Model):
    """Through model for itinerary-segment relationship with order"""
    
    itinerary = models.ForeignKey(FlightItinerary, on_delete=models.CASCADE)
    segment = models.ForeignKey(FlightSegment, on_delete=models.CASCADE)
    segment_order = models.PositiveIntegerField(_('Segment Order'), default=0)
    layover_duration = models.DurationField(_('Layover Duration'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('itinerary segment')
        verbose_name_plural = _('itinerary segments')
        ordering = ['segment_order']
        unique_together = ['itinerary', 'segment_order']
    
    def __str__(self):
        return f"{self.itinerary} - Segment {self.segment_order}"


class FareRule(models.Model):
    """Detailed fare rules"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fare_basis = models.CharField(_('Fare Basis'), max_length=20, db_index=True)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, 
                               verbose_name=_('Airline'))
    
    # Rule Categories
    category = models.CharField(_('Category'), max_length=10, 
                              choices=[('MIN', 'Minimum Stay'),
                                      ('MAX', 'Maximum Stay'),
                                      ('PEN', 'Penalties'),
                                      ('COM', 'Combinations'),
                                      ('BLK', 'Blackout Dates'),
                                      ('RES', 'Reservations'),
                                      ('TKT', 'Ticketing'),
                                      ('CHD', 'Children'),
                                      ('INF', 'Infants'),
                                      ('MIL', 'Military'),
                                      ('SRC', 'Senior Citizen'),
                                      ('GRP', 'Group')])
    
    # Rule Details
    rule_number = models.CharField(_('Rule Number'), max_length=10)
    rule_text = models.TextField(_('Rule Text'))
    rule_text_ar = models.TextField(_('Rule Text (Arabic)'), blank=True)
    
    # Applicability
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, 
                              related_name='farerule_origins', null=True, blank=True)
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, 
                                   related_name='farerule_destinations', null=True, blank=True)
    cabin_class = models.CharField(_('Cabin Class'), max_length=20, blank=True)
    travel_date_start = models.DateField(_('Travel Date Start'), null=True, blank=True)
    travel_date_end = models.DateField(_('Travel Date End'), null=True, blank=True)
    booking_date_start = models.DateField(_('Booking Date Start'), null=True, blank=True)
    booking_date_end = models.DateField(_('Booking Date End'), null=True, blank=True)
    
    # GDS Information
    gds_rule_id = models.CharField(_('GDS Rule ID'), max_length=50, blank=True)
    gds_provider = models.CharField(_('GDS Provider'), max_length=20, default='travelport')
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('fare rule')
        verbose_name_plural = _('fare rules')
        ordering = ['fare_basis', 'category', 'rule_number']
        indexes = [
            models.Index(fields=['fare_basis', 'airline']),
            models.Index(fields=['category', 'travel_date_start']),
        ]
    
    def __str__(self):
        return f"{self.fare_basis} - {self.get_category_display()} - {self.rule_number}"


class BaggageRule(models.Model):
    """Baggage rules and allowances"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, 
                               verbose_name=_('Airline'))
    
    # Applicability
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, 
                              related_name='baggagerule_origins', null=True, blank=True)
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, 
                                   related_name='baggagerule_destinations', null=True, blank=True)
    cabin_class = models.CharField(_('Cabin Class'), max_length=20)
    fare_basis = models.CharField(_('Fare Basis'), max_length=20, blank=True)
    
    # Baggage Allowance
    checked_pieces = models.PositiveIntegerField(_('Checked Pieces'), default=0)
    checked_weight_kg = models.DecimalField(_('Checked Weight (kg)'), max_digits=6, 
                                           decimal_places=2, null=True, blank=True)
    checked_dimensions_cm = models.CharField(_('Checked Dimensions (cm)'), 
                                            max_length=50, blank=True)
    
    cabin_pieces = models.PositiveIntegerField(_('Cabin Pieces'), default=1)
    cabin_weight_kg = models.DecimalField(_('Cabin Weight (kg)'), max_digits=6, 
                                         decimal_places=2, null=True, blank=True)
    cabin_dimensions_cm = models.CharField(_('Cabin Dimensions (cm)'), 
                                          max_length=50, blank=True)
    
    # Additional Information
    sports_equipment = models.BooleanField(_('Sports Equipment Allowed'), default=False)
    musical_instruments = models.BooleanField(_('Musical Instruments Allowed'), default=False)
    pets_allowed = models.BooleanField(_('Pets Allowed'), default=False)
    
    # Excess Baggage
    excess_price_per_kg = models.DecimalField(_('Excess Price per kg'), max_digits=8, 
                                            decimal_places=2, null=True, blank=True)
    excess_price_per_piece = models.DecimalField(_('Excess Price per Piece'), max_digits=8, 
                                                decimal_places=2, null=True, blank=True)
    
    # GDS Information
    gds_rule_id = models.CharField(_('GDS Rule ID'), max_length=50, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('baggage rule')
        verbose_name_plural = _('baggage rules')
        ordering = ['airline', 'cabin_class']
        indexes = [
            models.Index(fields=['airline', 'cabin_class']),
            models.Index(fields=['origin', 'destination']),
        ]
    
    def __str__(self):
        return f"{self.airline.code} - {self.cabin_class}: {self.checked_pieces} pieces"
    
    def get_baggage_summary(self):
        """Get baggage summary for display"""
        if self.checked_weight_kg:
            return f"{self.checked_pieces}×{self.checked_weight_kg}kg"
        return f"{self.checked_pieces} pieces"