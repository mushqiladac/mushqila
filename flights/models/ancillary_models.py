# flights/models/ancillary_models.py
"""
Ancillary services models for B2B Travel Platform
Production Ready - Final Version
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class AncillaryService(models.Model):
    """Base ancillary service model"""
    
    class ServiceType(models.TextChoices):
        SEAT_SELECTION = 'seat_selection', _('Seat Selection')
        EXTRA_BAGGAGE = 'extra_baggage', _('Extra Baggage')
        MEAL = 'meal', _('In-flight Meal')
        LOUNGE_ACCESS = 'lounge_access', _('Lounge Access')
        TRAVEL_INSURANCE = 'travel_insurance', _('Travel Insurance')
        PRIORITY_BOARDING = 'priority_boarding', _('Priority Boarding')
        FAST_TRACK = 'fast_track', _('Fast Track Security')
        HOTEL = 'hotel', _('Hotel Accommodation')
        CAR_RENTAL = 'car_rental', _('Car Rental')
        TRANSFER = 'transfer', _('Airport Transfer')
        ACTIVITY = 'activity', _('Travel Activity')
        WIFI = 'wifi', _('In-flight WiFi')
        ENTERTAINMENT = 'entertainment', _('Entertainment Package')
    
    class PricingType(models.TextChoices):
        FIXED = 'fixed', _('Fixed Price')
        PER_PERSON = 'per_person', _('Per Person')
        PER_SEGMENT = 'per_segment', _('Per Segment')
        PER_KG = 'per_kg', _('Per Kilogram')
        PER_DAY = 'per_day', _('Per Day')
        PERCENTAGE = 'percentage', _('Percentage of Fare')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Service Information
    service_code = models.CharField(_('Service Code'), max_length=20, unique=True)
    service_name = models.CharField(_('Service Name'), max_length=200)
    service_name_ar = models.CharField(_('Service Name (Arabic)'), max_length=200, blank=True)
    service_type = models.CharField(_('Service Type'), max_length=30, 
                                   choices=ServiceType.choices)
    
    # Description
    description = models.TextField(_('Description'), blank=True)
    description_ar = models.TextField(_('Description (Arabic)'), blank=True)
    features = models.JSONField(_('Features'), default=list, blank=True)
    terms_and_conditions = models.TextField(_('Terms and Conditions'), blank=True)
    
    # Provider Information
    provider = models.CharField(_('Service Provider'), max_length=100, blank=True)
    provider_code = models.CharField(_('Provider Code'), max_length=20, blank=True)
    is_third_party = models.BooleanField(_('Is Third Party'), default=False)
    
    # Pricing
    pricing_type = models.CharField(_('Pricing Type'), max_length=20, 
                                   choices=PricingType.choices, default=PricingType.FIXED)
    base_price = models.DecimalField(_('Base Price'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    commission_rate = models.DecimalField(_('Commission Rate'), max_digits=5, 
                                         decimal_places=2, default=Decimal('0.00'))
    
    # Applicability
    applicable_airlines = models.ManyToManyField('Airline', blank=True, 
                                                verbose_name=_('Applicable Airlines'))
    applicable_airports = models.ManyToManyField('Airport', blank=True, 
                                                verbose_name=_('Applicable Airports'))
    applicable_cabin_classes = models.JSONField(_('Applicable Cabin Classes'), 
                                               default=list, blank=True)
    applicable_countries = models.JSONField(_('Applicable Countries'), 
                                           default=list, blank=True)
    
    # Inventory and Availability
    is_available = models.BooleanField(_('Is Available'), default=True)
    available_from = models.DateField(_('Available From'), null=True, blank=True)
    available_until = models.DateField(_('Available Until'), null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(_('Stock Quantity'), null=True, blank=True)
    sold_quantity = models.PositiveIntegerField(_('Sold Quantity'), default=0)
    
    # Booking Rules
    advance_booking_days = models.PositiveIntegerField(_('Advance Booking Days'), default=0)
    last_minute_booking_hours = models.PositiveIntegerField(_('Last Minute Booking Hours'), 
                                                           default=24)
    maximum_per_booking = models.PositiveIntegerField(_('Maximum Per Booking'), default=10)
    minimum_per_booking = models.PositiveIntegerField(_('Minimum Per Booking'), default=1)
    
    # GDS Integration
    gds_service_code = models.CharField(_('GDS Service Code'), max_length=20, blank=True)
    gds_provider_code = models.CharField(_('GDS Provider Code'), max_length=20, blank=True)
    ssr_code = models.CharField(_('SSR Code'), max_length=4, blank=True)
    
    # Media
    image = models.ImageField(_('Service Image'), upload_to='ancillary/services/', 
                             blank=True, null=True)
    icon = models.CharField(_('Icon Class'), max_length=50, blank=True)
    
    # Metadata
    is_active = models.BooleanField(_('Is Active'), default=True)
    sort_order = models.PositiveIntegerField(_('Sort Order'), default=0)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  null=True, blank=True, 
                                  related_name='created_ancillary_services',
                                  verbose_name=_('Created By'))
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('ancillary service')
        verbose_name_plural = _('ancillary services')
        ordering = ['sort_order', 'service_name']
        indexes = [
            models.Index(fields=['service_code', 'is_active']),
            models.Index(fields=['service_type', 'is_available']),
            models.Index(fields=['is_active', 'available_until']),
        ]
    
    def __str__(self):
        return f"{self.service_code} - {self.service_name}"
    
    def is_available_for_booking(self, booking_date=None):
        """Check if service is available for booking"""
        if not self.is_active or not self.is_available:
            return False
        
        check_date = booking_date or timezone.now().date()
        
        if self.available_from and check_date < self.available_from:
            return False
        
        if self.available_until and check_date > self.available_until:
            return False
        
        if self.stock_quantity and self.sold_quantity >= self.stock_quantity:
            return False
        
        return True
    
    def calculate_price(self, quantity=1, base_fare=Decimal('0.00')):
        """Calculate price for the service"""
        if self.pricing_type == self.PricingType.FIXED:
            return self.base_price * quantity
        elif self.pricing_type == self.PricingType.PERCENTAGE:
            return (base_fare * self.base_price * quantity) / Decimal('100.00')
        else:
            return self.base_price * quantity
    
    def get_available_quantity(self):
        """Get available quantity"""
        if self.stock_quantity:
            return max(0, self.stock_quantity - self.sold_quantity)
        return None


class SeatSelection(models.Model):
    """Seat selection service"""
    
    class SeatType(models.TextChoices):
        STANDARD = 'standard', _('Standard Seat')
        EXTRA_LEGROOM = 'extra_legroom', _('Extra Legroom Seat')
        EXIT_ROW = 'exit_row', _('Exit Row Seat')
        BULKHEAD = 'bulkhead', _('Bulkhead Seat')
        PREMIUM = 'premium', _('Premium Seat')
        STRETCH = 'stretch', _('Stretch Seat')
        COUPLE = 'couple', _('Couple Seat')
        FAMILY = 'family', _('Family Seat')
        WHEELCHAIR = 'wheelchair', _('Wheelchair Accessible')
    
    class SeatLocation(models.TextChoices):
        WINDOW = 'window', _('Window')
        MIDDLE = 'middle', _('Middle')
        AISLE = 'aisle', _('Aisle')
        FRONT = 'front', _('Front of Cabin')
        BACK = 'back', _('Back of Cabin')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ancillary_service = models.OneToOneField(AncillaryService, on_delete=models.CASCADE, 
                                           related_name='seat_selection_service',
                                           verbose_name=_('Ancillary Service'))
    
    # Seat Configuration
    seat_type = models.CharField(_('Seat Type'), max_length=20, 
                                choices=SeatType.choices, default=SeatType.STANDARD)
    seat_location = models.CharField(_('Seat Location'), max_length=20, 
                                    choices=SeatLocation.choices, blank=True)
    
    # Aircraft Specific
    applicable_aircraft = models.ManyToManyField('Aircraft', blank=True, 
                                                verbose_name=_('Applicable Aircraft'))
    seat_map_template = models.JSONField(_('Seat Map Template'), default=dict, blank=True)
    
    # Seat Features
    features = models.JSONField(_('Seat Features'), default=list, blank=True)
    legroom_inches = models.DecimalField(_('Legroom (inches)'), max_digits=4, 
                                        decimal_places=1, null=True, blank=True)
    recline_degrees = models.PositiveIntegerField(_('Recline (degrees)'), null=True, blank=True)
    width_inches = models.DecimalField(_('Width (inches)'), max_digits=4, 
                                      decimal_places=1, null=True, blank=True)
    pitch_inches = models.DecimalField(_('Pitch (inches)'), max_digits=4, 
                                      decimal_places=1, null=True, blank=True)
    
    # Restrictions
    age_restriction = models.PositiveIntegerField(_('Age Restriction'), null=True, blank=True)
    height_restriction_cm = models.PositiveIntegerField(_('Height Restriction (cm)'), 
                                                       null=True, blank=True)
    weight_restriction_kg = models.PositiveIntegerField(_('Weight Restriction (kg)'), 
                                                       null=True, blank=True)
    mobility_requirements = models.TextField(_('Mobility Requirements'), blank=True)
    
    # Booking Rules
    can_select_in_advance = models.BooleanField(_('Can Select in Advance'), default=True)
    advance_selection_days = models.PositiveIntegerField(_('Advance Selection Days'), default=7)
    automatic_assignment = models.BooleanField(_('Automatic Assignment'), default=False)
    
    class Meta:
        verbose_name = _('seat selection')
        verbose_name_plural = _('seat selections')
    
    def __str__(self):
        return f"Seat Selection: {self.get_seat_type_display()}"
    
    def is_eligible_for_passenger(self, passenger):
        """Check if seat is eligible for passenger"""
        if self.age_restriction and passenger.get_age() < self.age_restriction:
            return False
        
        # Add more eligibility checks as needed
        return True


class MealPreference(models.Model):
    """In-flight meal service"""
    
    class MealType(models.TextChoices):
        STANDARD = 'standard', _('Standard Meal')
        VEGETARIAN = 'vegetarian', _('Vegetarian')
        VEGAN = 'vegan', _('Vegan')
        GLUTEN_FREE = 'gluten_free', _('Gluten Free')
        DAIRY_FREE = 'dairy_free', _('Dairy Free')
        NUT_FREE = 'nut_free', _('Nut Free')
        HALAL = 'halal', _('Halal')
        KOSHER = 'kosher', _('Kosher')
        HINDU = 'hindu', _('Hindu Vegetarian')
        JAIN = 'jain', _('Jain')
        ASIAN_VEGETARIAN = 'asian_vegetarian', _('Asian Vegetarian')
        CHILD_MEAL = 'child_meal', _('Child Meal')
        INFANT_MEAL = 'infant_meal', _('Infant Meal')
        DIABETIC = 'diabetic', _('Diabetic')
        LOW_SODIUM = 'low_sodium', _('Low Sodium')
        LOW_FAT = 'low_fat', _('Low Fat')
        FRUIT_PLATTER = 'fruit_platter', _('Fruit Platter')
    
    class ServingTime(models.TextChoices):
        BREAKFAST = 'breakfast', _('Breakfast')
        LUNCH = 'lunch', _('Lunch')
        DINNER = 'dinner', _('Dinner')
        SNACK = 'snack', _('Snack')
        ANYTIME = 'anytime', _('Anytime')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ancillary_service = models.OneToOneField(AncillaryService, on_delete=models.CASCADE, 
                                           related_name='meal_preference_service',
                                           verbose_name=_('Ancillary Service'))
    
    # Meal Information
    meal_type = models.CharField(_('Meal Type'), max_length=30, 
                                choices=MealType.choices, default=MealType.STANDARD)
    serving_time = models.CharField(_('Serving Time'), max_length=20, 
                                   choices=ServingTime.choices, default=ServingTime.ANYTIME)
    
    # Meal Details
    cuisine = models.CharField(_('Cuisine'), max_length=50, blank=True)
    description = models.TextField(_('Description'), blank=True)
    ingredients = models.JSONField(_('Ingredients'), default=list, blank=True)
    allergens = models.JSONField(_('Allergens'), default=list, blank=True)
    nutritional_info = models.JSONField(_('Nutritional Information'), default=dict, blank=True)
    
    # Flight Specific
    applicable_flight_duration = models.PositiveIntegerField(_('Applicable Flight Duration (min)'), 
                                                           null=True, blank=True)
    minimum_notice_hours = models.PositiveIntegerField(_('Minimum Notice (hours)'), default=24)
    
    # Special Requirements
    religious_compliance = models.TextField(_('Religious Compliance'), blank=True)
    health_certifications = models.JSONField(_('Health Certifications'), default=list, blank=True)
    
    class Meta:
        verbose_name = _('meal preference')
        verbose_name_plural = _('meal preferences')
    
    def __str__(self):
        return f"Meal: {self.get_meal_type_display()} - {self.get_serving_time_display()}"
    
    def is_suitable_for_duration(self, flight_duration_minutes):
        """Check if meal is suitable for flight duration"""
        if self.applicable_flight_duration:
            return flight_duration_minutes >= self.applicable_flight_duration
        return True


class BaggageService(models.Model):
    """Extra baggage service"""
    
    class BaggageType(models.TextChoices):
        CHECKED = 'checked', _('Checked Baggage')
        CARRY_ON = 'carry_on', _('Carry-on Baggage')
        OVER_SIZE = 'over_size', _('Oversize Baggage')
        SPORTS_EQUIPMENT = 'sports_equipment', _('Sports Equipment')
        MUSICAL_INSTRUMENT = 'musical_instrument', _('Musical Instrument')
        PET_CARRIER = 'pet_carrier', _('Pet Carrier')
        FRAGILE = 'fragile', _('Fragile Items')
        VALUABLES = 'valuables', _('Valuables')
    
    class WeightUnit(models.TextChoices):
        KG = 'kg', _('Kilograms')
        LB = 'lb', _('Pounds')
    
    class DimensionUnit(models.TextChoices):
        CM = 'cm', _('Centimeters')
        IN = 'in', _('Inches')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ancillary_service = models.OneToOneField(AncillaryService, on_delete=models.CASCADE, 
                                           related_name='baggage_service',
                                           verbose_name=_('Ancillary Service'))
    
    # Baggage Information
    baggage_type = models.CharField(_('Baggage Type'), max_length=30, 
                                   choices=BaggageType.choices, default=BaggageType.CHECKED)
    
    # Weight and Dimensions
    weight_limit = models.DecimalField(_('Weight Limit'), max_digits=6, decimal_places=2)
    weight_unit = models.CharField(_('Weight Unit'), max_length=2, 
                                  choices=WeightUnit.choices, default=WeightUnit.KG)
    
    length_limit = models.DecimalField(_('Length Limit'), max_digits=6, 
                                      decimal_places=2, null=True, blank=True)
    width_limit = models.DecimalField(_('Width Limit'), max_digits=6, 
                                     decimal_places=2, null=True, blank=True)
    height_limit = models.DecimalField(_('Height Limit'), max_digits=6, 
                                      decimal_places=2, null=True, blank=True)
    dimension_unit = models.CharField(_('Dimension Unit'), max_length=2, 
                                     choices=DimensionUnit.choices, default=DimensionUnit.CM)
    
    linear_limit = models.DecimalField(_('Linear Limit (L+W+H)'), max_digits=6, 
                                      decimal_places=2, null=True, blank=True)
    
    # Pricing
    price_per_kg = models.DecimalField(_('Price per kg'), max_digits=8, 
                                      decimal_places=2, null=True, blank=True)
    price_per_piece = models.DecimalField(_('Price per Piece'), max_digits=8, 
                                         decimal_places=2, null=True, blank=True)
    
    # Restrictions
    restricted_items = models.JSONField(_('Restricted Items'), default=list, blank=True)
    special_handling_required = models.BooleanField(_('Special Handling Required'), default=False)
    handling_fee = models.DecimalField(_('Handling Fee'), max_digits=8, 
                                      decimal_places=2, null=True, blank=True)
    
    # Pre-paid Options
    pre_purchase_discount = models.DecimalField(_('Pre-purchase Discount'), max_digits=5, 
                                               decimal_places=2, null=True, blank=True)
    airport_price_multiplier = models.DecimalField(_('Airport Price Multiplier'), max_digits=3, 
                                                  decimal_places=2, default=Decimal('1.5'))
    
    class Meta:
        verbose_name = _('baggage service')
        verbose_name_plural = _('baggage services')
    
    def __str__(self):
        return f"Baggage: {self.get_baggage_type_display()} - {self.weight_limit}{self.weight_unit}"
    
    def calculate_price(self, weight=None, pieces=1, is_pre_purchased=False):
        """Calculate baggage price"""
        if self.price_per_piece:
            price = self.price_per_piece * pieces
        elif self.price_per_kg and weight:
            price = self.price_per_kg * weight
        else:
            price = self.ancillary_service.base_price * pieces
        
        # Apply pre-purchase discount
        if is_pre_purchased and self.pre_purchase_discount:
            discount = (price * self.pre_purchase_discount) / Decimal('100.00')
            price -= discount
        
        return price


class TravelInsurance(models.Model):
    """Travel insurance service"""
    
    class CoverageType(models.TextChoices):
        BASIC = 'basic', _('Basic Coverage')
        COMPREHENSIVE = 'comprehensive', _('Comprehensive Coverage')
        PREMIUM = 'premium', _('Premium Coverage')
        ANNUAL_MULTI_TRIP = 'annual_multi_trip', _('Annual Multi-trip')
        SENIOR = 'senior', _('Senior Citizen')
        STUDENT = 'student', _('Student')
        FAMILY = 'family', _('Family')
        BUSINESS = 'business', _('Business Traveler')
    
    class DurationUnit(models.TextChoices):
        DAYS = 'days', _('Days')
        WEEKS = 'weeks', _('Weeks')
        MONTHS = 'months', _('Months')
        ANNUAL = 'annual', _('Annual')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ancillary_service = models.OneToOneField(AncillaryService, on_delete=models.CASCADE, 
                                           related_name='travel_insurance_service',
                                           verbose_name=_('Ancillary Service'))
    
    # Insurance Information
    coverage_type = models.CharField(_('Coverage Type'), max_length=30, 
                                    choices=CoverageType.choices, default=CoverageType.BASIC)
    insurance_provider = models.CharField(_('Insurance Provider'), max_length=100)
    policy_number_prefix = models.CharField(_('Policy Number Prefix'), max_length=10, blank=True)
    
    # Coverage Details
    coverage_amount = models.DecimalField(_('Coverage Amount'), max_digits=12, decimal_places=2)
    coverage_currency = models.CharField(_('Coverage Currency'), max_length=3, default='SAR')
    
    medical_coverage = models.DecimalField(_('Medical Coverage'), max_digits=12, 
                                          decimal_places=2, null=True, blank=True)
    trip_cancellation = models.DecimalField(_('Trip Cancellation Coverage'), max_digits=12, 
                                           decimal_places=2, null=True, blank=True)
    baggage_loss = models.DecimalField(_('Baggage Loss Coverage'), max_digits=12, 
                                      decimal_places=2, null=True, blank=True)
    flight_delay = models.DecimalField(_('Flight Delay Coverage'), max_digits=12, 
                                      decimal_places=2, null=True, blank=True)
    personal_accident = models.DecimalField(_('Personal Accident Coverage'), max_digits=12, 
                                           decimal_places=2, null=True, blank=True)
    
    # Duration
    minimum_duration = models.PositiveIntegerField(_('Minimum Duration'), default=1)
    maximum_duration = models.PositiveIntegerField(_('Maximum Duration'), default=365)
    duration_unit = models.CharField(_('Duration Unit'), max_length=10, 
                                    choices=DurationUnit.choices, default=DurationUnit.DAYS)
    
    # Age Restrictions
    minimum_age = models.PositiveIntegerField(_('Minimum Age'), default=0)
    maximum_age = models.PositiveIntegerField(_('Maximum Age'), null=True, blank=True)
    senior_age_threshold = models.PositiveIntegerField(_('Senior Age Threshold'), default=60)
    
    # Geographic Coverage
    covered_countries = models.JSONField(_('Covered Countries'), default=list, blank=True)
    excluded_countries = models.JSONField(_('Excluded Countries'), default=list, blank=True)
    worldwide_coverage = models.BooleanField(_('Worldwide Coverage'), default=False)
    
    # Claims Information
    deductible_amount = models.DecimalField(_('Deductible Amount'), max_digits=10, 
                                           decimal_places=2, null=True, blank=True)
    claims_process = models.TextField(_('Claims Process'), blank=True)
    emergency_contact = models.TextField(_('Emergency Contact'), blank=True)
    
    # Policy Documents
    policy_document = models.FileField(_('Policy Document'), upload_to='insurance/policies/', 
                                      blank=True, null=True)
    terms_and_conditions = models.TextField(_('Terms and Conditions'), blank=True)
    
    class Meta:
        verbose_name = _('travel insurance')
        verbose_name_plural = _('travel insurance')
    
    def __str__(self):
        return f"Insurance: {self.get_coverage_type_display()} - {self.insurance_provider}"
    
    def calculate_premium(self, duration_days, traveler_age, destination_country):
        """Calculate insurance premium"""
        base_premium = self.ancillary_service.base_price
        
        # Age adjustment
        if traveler_age >= self.senior_age_threshold:
            base_premium *= Decimal('1.5')
        
        # Destination adjustment
        if destination_country in self.excluded_countries:
            return None  # Not available for this destination
        
        # Duration adjustment
        if self.duration_unit == self.DurationUnit.DAYS:
            premium = base_premium * duration_days
        elif self.duration_unit == self.DurationUnit.WEEKS:
            premium = base_premium * (duration_days / 7)
        elif self.duration_unit == self.DurationUnit.MONTHS:
            premium = base_premium * (duration_days / 30)
        else:  # Annual
            premium = base_premium
        
        return premium
    
    def is_eligible(self, traveler_age, destination_country):
        """Check if traveler is eligible for insurance"""
        if self.minimum_age and traveler_age < self.minimum_age:
            return False
        
        if self.maximum_age and traveler_age > self.maximum_age:
            return False
        
        if destination_country in self.excluded_countries:
            return False
        
        return True


class LoungeAccess(models.Model):
    """Airport lounge access service"""
    
    class LoungeType(models.TextChoices):
        AIRLINE_LOUNGE = 'airline_lounge', _('Airline Lounge')
        INDEPENDENT_LOUNGE = 'independent_lounge', _('Independent Lounge')
        PRIORITY_PASS = 'priority_pass', _('Priority Pass')
        CREDIT_CARD_LOUNGE = 'credit_card_lounge', _('Credit Card Lounge')
        PAY_PER_USE = 'pay_per_use', _('Pay-per-Use Lounge')
    
    class AccessType(models.TextChoices):
        SINGLE_ENTRY = 'single_entry', _('Single Entry')
        MULTIPLE_ENTRIES = 'multiple_entries', _('Multiple Entries')
        UNLIMITED = 'unlimited', _('Unlimited')
        ANNUAL_MEMBERSHIP = 'annual_membership', _('Annual Membership')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ancillary_service = models.OneToOneField(AncillaryService, on_delete=models.CASCADE, 
                                           related_name='lounge_access_service',
                                           verbose_name=_('Ancillary Service'))
    
    # Lounge Information
    lounge_type = models.CharField(_('Lounge Type'), max_length=30, 
                                  choices=LoungeType.choices, default=LoungeType.AIRLINE_LOUNGE)
    access_type = models.CharField(_('Access Type'), max_length=30, 
                                  choices=AccessType.choices, default=AccessType.SINGLE_ENTRY)
    lounge_network = models.CharField(_('Lounge Network'), max_length=100, blank=True)
    
    # Airport Specific
    applicable_airports = models.ManyToManyField('Airport', 
                                                verbose_name=_('Applicable Airports'))
    terminal_locations = models.JSONField(_('Terminal Locations'), default=dict, blank=True)
    
    # Access Details
    maximum_guests = models.PositiveIntegerField(_('Maximum Guests'), default=0)
    guest_fee_per_person = models.DecimalField(_('Guest Fee per Person'), max_digits=8, 
                                              decimal_places=2, null=True, blank=True)
    maximum_stay_hours = models.DecimalField(_('Maximum Stay (hours)'), max_digits=4, 
                                            decimal_places=1, default=Decimal('3.0'))
    
    # Facilities
    facilities = models.JSONField(_('Facilities'), default=list, blank=True)
    food_beverage_included = models.BooleanField(_('Food & Beverage Included'), default=True)
    shower_facilities = models.BooleanField(_('Shower Facilities'), default=False)
    sleeping_pods = models.BooleanField(_('Sleeping Pods'), default=False)
    business_center = models.BooleanField(_('Business Center'), default=False)
    wifi_available = models.BooleanField(_('WiFi Available'), default=True)
    
    # Operating Hours
    operating_hours = models.JSONField(_('Operating Hours'), default=dict, blank=True)
    is_24_hours = models.BooleanField(_('24 Hours Operation'), default=False)
    
    # Access Requirements
    boarding_pass_required = models.BooleanField(_('Boarding Pass Required'), default=True)
    flight_class_restriction = models.CharField(_('Flight Class Restriction'), max_length=20, 
                                               blank=True)
    minimum_connection_time = models.PositiveIntegerField(_('Minimum Connection Time (min)'), 
                                                         default=60)
    
    class Meta:
        verbose_name = _('lounge access')
        verbose_name_plural = _('lounge access')
    
    def __str__(self):
        return f"Lounge Access: {self.get_lounge_type_display()}"
    
    def is_available_at_airport(self, airport_code, terminal=None):
        """Check if lounge is available at airport"""
        airport = self.applicable_airports.filter(iata_code=airport_code).first()
        if not airport:
            return False
        
        if terminal and self.terminal_locations:
            available_terminals = self.terminal_locations.get(airport_code, [])
            if terminal not in available_terminals:
                return False
        
        return True
    
    def calculate_guest_fee(self, guest_count):
        """Calculate guest fees"""
        if guest_count <= self.maximum_guests:
            return Decimal('0.00')
        
        extra_guests = guest_count - self.maximum_guests
        return self.guest_fee_per_person * extra_guests if self.guest_fee_per_person else Decimal('0.00')


class AncillaryBooking(models.Model):
    """Ancillary service bookings"""
    
    class BookingStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')
        USED = 'used', _('Used')
        EXPIRED = 'expired', _('Expired')
        REFUNDED = 'refunded', _('Refunded')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Main Booking Reference
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, 
                               related_name='ancillary_bookings', verbose_name=_('Booking'))
    passenger = models.ForeignKey('Passenger', on_delete=models.CASCADE, 
                                 null=True, blank=True, verbose_name=_('Passenger'))
    
    # Service Information
    ancillary_service = models.ForeignKey(AncillaryService, on_delete=models.PROTECT, 
                                         verbose_name=_('Ancillary Service'))
    service_type = models.CharField(_('Service Type'), max_length=30)
    
    # Booking Details
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)
    unit_price = models.DecimalField(_('Unit Price'), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_('Total Price'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Service Specific Details
    service_details = models.JSONField(_('Service Details'), default=dict, blank=True)
    service_date = models.DateField(_('Service Date'), null=True, blank=True)
    service_time = models.TimeField(_('Service Time'), null=True, blank=True)
    
    # Status Tracking
    status = models.CharField(_('Status'), max_length=20, 
                             choices=BookingStatus.choices, default=BookingStatus.PENDING)
    confirmed_at = models.DateTimeField(_('Confirmed At'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('Cancelled At'), null=True, blank=True)
    used_at = models.DateTimeField(_('Used At'), null=True, blank=True)
    
    # GDS Integration
    ssr_code = models.CharField(_('SSR Code'), max_length=4, blank=True)
    gds_service_id = models.CharField(_('GDS Service ID'), max_length=100, blank=True)
    gds_booking_ref = models.CharField(_('GDS Booking Reference'), max_length=100, blank=True)
    
    # Payment Information
    commission_amount = models.DecimalField(_('Commission Amount'), max_digits=10, 
                                           decimal_places=2, default=0)
    commission_rate = models.DecimalField(_('Commission Rate'), max_digits=5, 
                                         decimal_places=2, default=0)
    
    # Special Requirements
    special_requests = models.TextField(_('Special Requests'), blank=True)
    dietary_restrictions = models.TextField(_('Dietary Restrictions'), blank=True)
    
    # Voucher/Ticket Information
    voucher_number = models.CharField(_('Voucher Number'), max_length=50, blank=True)
    voucher_pdf = models.FileField(_('Voucher PDF'), upload_to='vouchers/%Y/%m/%d/', 
                                  blank=True, null=True)
    qr_code = models.ImageField(_('QR Code'), upload_to='qrcodes/ancillary/', 
                               blank=True, null=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('ancillary booking')
        verbose_name_plural = _('ancillary bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'status']),
            models.Index(fields=['ancillary_service', 'service_date']),
            models.Index(fields=['voucher_number']),
        ]
    
    def __str__(self):
        return f"Ancillary: {self.ancillary_service.service_code} for Booking {self.booking.booking_reference}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate total price"""
        if self.unit_price and self.quantity:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def can_be_cancelled(self):
        """Check if ancillary booking can be cancelled"""
        if self.status in [self.BookingStatus.CANCELLED, self.BookingStatus.USED, 
                          self.BookingStatus.EXPIRED]:
            return False
        
        # Check service specific cancellation rules
        service = self.ancillary_service
        if hasattr(service, 'cancellation_policy'):
            # Implement cancellation policy check
            pass
        
        return True
    
    def generate_voucher(self):
        """Generate service voucher"""
        # Implement voucher generation logic
        pass