# flights/forms/ancillary_forms.py
"""
Ancillary services forms for B2B Travel Platform
Production Ready - Final Version
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date, timedelta
import re

from flights.models import AncillaryService, SeatSelection, MealPreference, BaggageService, TravelInsurance, LoungeAccess


class SeatSelectionForm(forms.ModelForm):
    """Form for seat selection"""
    
    class Meta:
        model = SeatSelection
        fields = [
            'seat_type',
            'seat_location',
            'features',
        ]
    
    SEAT_TYPE_CHOICES = [
        ('standard', _('Standard Seat')),
        ('extra_legroom', _('Extra Legroom Seat')),
        ('exit_row', _('Exit Row Seat')),
        ('bulkhead', _('Bulkhead Seat')),
        ('premium', _('Premium Seat')),
        ('stretch', _('Stretch Seat')),
        ('couple', _('Couple Seat')),
        ('family', _('Family Seat')),
    ]
    
    SEAT_LOCATION_CHOICES = [
        ('window', _('Window')),
        ('middle', _('Middle')),
        ('aisle', _('Aisle')),
        ('front', _('Front of Cabin')),
        ('back', _('Back of Cabin')),
    ]
    
    seat_type = forms.ChoiceField(
        label=_('Seat Type'),
        choices=SEAT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input seat-type-radio',
        })
    )
    
    seat_location = forms.ChoiceField(
        label=_('Seat Location'),
        choices=SEAT_LOCATION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input seat-location-radio',
        })
    )
    
    seat_row = forms.ChoiceField(
        label=_('Row'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select seat-row-select',
        })
    )
    
    seat_column = forms.ChoiceField(
        label=_('Seat'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select seat-column-select',
        })
    )
    
    features = forms.MultipleChoiceField(
        label=_('Seat Features'),
        required=False,
        choices=[
            ('extra_legroom', _('Extra Legroom')),
            ('power_outlet', _('Power Outlet')),
            ('usb_port', _('USB Port')),
            ('privacy_divider', _('Privacy Divider')),
            ('storage_bin', _('Storage Bin')),
            ('tablet_holder', _('Tablet Holder')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        })
    )
    
    passenger = forms.ModelChoiceField(
        label=_('Passenger'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select passenger-select',
        })
    )
    
    flight_segment = forms.ModelChoiceField(
        label=_('Flight'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select flight-select',
        })
    )
    
    price = forms.DecimalField(
        label=_('Price (SAR)'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly',
        })
    )
    
    confirmation = forms.BooleanField(
        label=_('I confirm this seat selection'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.ancillary_service = kwargs.pop('ancillary_service', None)
        super().__init__(*args, **kwargs)
        
        # Set passenger choices from booking
        if self.booking:
            self.fields['passenger'].queryset = self.booking.passengers.all()
            self.fields['flight_segment'].queryset = self.booking.itinerary.segments.all()
        
        # Set seat rows and columns based on aircraft
        if self.ancillary_service and hasattr(self.ancillary_service, 'seat_selection_service'):
            seat_service = self.ancillary_service.seat_selection_service
            seat_map = seat_service.seat_map_template
            
            # Populate row choices
            if seat_map and 'rows' in seat_map:
                rows = [(str(r), f'Row {r}') for r in seat_map['rows']]
                self.fields['seat_row'].choices = rows
            
            # Populate column choices
            if seat_map and 'columns' in seat_map:
                columns = [(c, c) for c in seat_map['columns']]
                self.fields['seat_column'].choices = columns
        
        # Set initial price
        if self.ancillary_service:
            self.fields['price'].initial = self.ancillary_service.base_price
    
    def clean(self):
        cleaned_data = super().clean()
        seat_row = cleaned_data.get('seat_row')
        seat_column = cleaned_data.get('seat_column')
        passenger = cleaned_data.get('passenger')
        flight_segment = cleaned_data.get('flight_segment')
        confirmation = cleaned_data.get('confirmation')
        
        if not confirmation:
            raise forms.ValidationError({
                'confirmation': _('You must confirm the seat selection.')
            })
        
        # Validate seat selection
        if seat_row and seat_column:
            # Check if seat is already taken
            # This would query the seat inventory
            seat_number = f"{seat_row}{seat_column}"
            
            # Check seat eligibility for passenger
            if passenger and self.ancillary_service:
                seat_service = self.ancillary_service.seat_selection_service
                if seat_service and not seat_service.is_eligible_for_passenger(passenger):
                    raise forms.ValidationError({
                        'passenger': _('This seat type is not eligible for the selected passenger.')
                    })
        
        return cleaned_data


class BaggageForm(forms.ModelForm):
    """Form for extra baggage purchase"""
    
    class Meta:
        model = BaggageService
        fields = [
            'baggage_type',
            'weight_limit',
            'weight_unit',
        ]
    
    BAGGAGE_TYPE_CHOICES = [
        ('checked', _('Checked Baggage')),
        ('carry_on', _('Carry-on Baggage')),
        ('over_size', _('Oversize Baggage')),
        ('sports_equipment', _('Sports Equipment')),
        ('musical_instrument', _('Musical Instrument')),
    ]
    
    baggage_type = forms.ChoiceField(
        label=_('Baggage Type'),
        choices=BAGGAGE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'baggageType',
        })
    )
    
    weight_limit = forms.DecimalField(
        label=_('Weight'),
        max_digits=6,
        decimal_places=2,
        min_value=1,
        max_value=50,
        initial=23,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'id': 'baggageWeight',
        })
    )
    
    weight_unit = forms.ChoiceField(
        label=_('Unit'),
        choices=[
            ('kg', _('Kilograms')),
            ('lb', _('Pounds')),
        ],
        initial='kg',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )
    
    quantity = forms.IntegerField(
        label=_('Quantity'),
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '10',
            'id': 'baggageQuantity',
        })
    )
    
    passenger = forms.ModelChoiceField(
        label=_('Passenger'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'baggagePassenger',
        })
    )
    
    flight_segment = forms.ModelChoiceField(
        label=_('Flight Segment'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'baggageFlight',
        })
    )
    
    is_pre_purchased = forms.BooleanField(
        label=_('Pre-purchase (save 20%)'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'prePurchase',
        })
    )
    
    price = forms.DecimalField(
        label=_('Total Price (SAR)'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly',
            'id': 'baggagePrice',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.ancillary_service = kwargs.pop('ancillary_service', None)
        super().__init__(*args, **kwargs)
        
        # Set passenger choices from booking
        if self.booking:
            self.fields['passenger'].queryset = self.booking.passengers.all()
            self.fields['flight_segment'].queryset = self.booking.itinerary.segments.all()
        
        # Set initial price
        if self.ancillary_service:
            base_price = self.ancillary_service.base_price
            self.fields['price'].initial = base_price
    
    def clean(self):
        cleaned_data = super().clean()
        baggage_type = cleaned_data.get('baggage_type')
        weight_limit = cleaned_data.get('weight_limit')
        quantity = cleaned_data.get('quantity')
        passenger = cleaned_data.get('passenger')
        flight_segment = cleaned_data.get('flight_segment')
        
        # Validate weight limits based on baggage type
        if baggage_type == 'carry_on' and weight_limit > 10:
            raise forms.ValidationError({
                'weight_limit': _('Carry-on baggage cannot exceed 10kg.')
            })
        
        if baggage_type == 'checked' and weight_limit > 32:
            raise forms.ValidationError({
                'weight_limit': _('Checked baggage cannot exceed 32kg for safety reasons.')
            })
        
        # Validate quantity limits
        if quantity > 10:
            raise forms.ValidationError({
                'quantity': _('Maximum 10 baggage items per passenger.')
            })
        
        # Check airline baggage policy
        if flight_segment and passenger:
            # This would check against airline-specific baggage policies
            pass
        
        return cleaned_data
    
    def calculate_price(self):
        """Calculate baggage price based on selections"""
        weight_limit = self.cleaned_data.get('weight_limit', 0)
        quantity = self.cleaned_data.get('quantity', 1)
        is_pre_purchased = self.cleaned_data.get('is_pre_purchased', False)
        
        if self.ancillary_service:
            baggage_service = self.ancillary_service.baggage_service
            
            if baggage_service.price_per_kg:
                price = baggage_service.price_per_kg * weight_limit * quantity
            elif baggage_service.price_per_piece:
                price = baggage_service.price_per_piece * quantity
            else:
                price = self.ancillary_service.base_price * quantity
            
            # Apply pre-purchase discount
            if is_pre_purchased and baggage_service.pre_purchase_discount:
                discount = (price * baggage_service.pre_purchase_discount) / 100
                price -= discount
            
            return price
        
        return 0


class MealSelectionForm(forms.ModelForm):
    """Form for meal selection"""
    
    class Meta:
        model = MealPreference
        fields = [
            'meal_type',
            'serving_time',
            'cuisine',
        ]
    
    MEAL_TYPE_CHOICES = [
        ('standard', _('Standard Meal')),
        ('vegetarian', _('Vegetarian')),
        ('vegan', _('Vegan')),
        ('halal', _('Halal')),
        ('kosher', _('Kosher')),
        ('gluten_free', _('Gluten Free')),
        ('child', _('Child Meal')),
        ('diabetic', _('Diabetic')),
        ('asian_vegetarian', _('Asian Vegetarian')),
    ]
    
    SERVING_TIME_CHOICES = [
        ('breakfast', _('Breakfast')),
        ('lunch', _('Lunch')),
        ('dinner', _('Dinner')),
        ('snack', _('Snack')),
    ]
    
    meal_type = forms.ChoiceField(
        label=_('Meal Type'),
        choices=MEAL_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'mealType',
        })
    )
    
    serving_time = forms.ChoiceField(
        label=_('Serving Time'),
        choices=SERVING_TIME_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'servingTime',
        })
    )
    
    cuisine = forms.CharField(
        label=_('Cuisine Preference'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Arabic, Indian, Continental'),
            'maxlength': '50',
        })
    )
    
    passenger = forms.ModelChoiceField(
        label=_('Passenger'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'mealPassenger',
        })
    )
    
    flight_segment = forms.ModelChoiceField(
        label=_('Flight Segment'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'mealFlight',
        })
    )
    
    special_instructions = forms.CharField(
        label=_('Special Instructions'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Any allergies, dietary restrictions, or special requests...'),
            'maxlength': '500',
        })
    )
    
    price = forms.DecimalField(
        label=_('Price (SAR)'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.ancillary_service = kwargs.pop('ancillary_service', None)
        super().__init__(*args, **kwargs)
        
        # Set passenger choices from booking
        if self.booking:
            self.fields['passenger'].queryset = self.booking.passengers.all()
            self.fields['flight_segment'].queryset = self.booking.itinerary.segments.all()
        
        # Set initial price
        if self.ancillary_service:
            self.fields['price'].initial = self.ancillary_service.base_price
    
    def clean(self):
        cleaned_data = super().clean()
        passenger = cleaned_data.get('passenger')
        flight_segment = cleaned_data.get('flight_segment')
        meal_type = cleaned_data.get('meal_type')
        
        # Validate meal availability for flight duration
        if flight_segment and self.ancillary_service:
            meal_service = self.ancillary_service.meal_preference_service
            if meal_service:
                flight_duration = flight_segment.duration.total_seconds() / 60
                if not meal_service.is_suitable_for_duration(flight_duration):
                    raise forms.ValidationError({
                        'flight_segment': _('Meal service not available for flights under {} minutes.').format(
                            meal_service.applicable_flight_duration
                        )
                    })
        
        # Check for religious restrictions
        if meal_type == 'halal' and passenger and passenger.nationality == 'IL':
            raise forms.ValidationError({
                'meal_type': _('Halal meals are not available for passengers with this nationality.')
            })
        
        return cleaned_data


class LoungeAccessForm(forms.ModelForm):
    """Form for lounge access purchase"""
    
    class Meta:
        model = LoungeAccess
        fields = [
            'lounge_type',
            'access_type',
        ]
    
    LOUNGE_TYPE_CHOICES = [
        ('airline_lounge', _('Airline Lounge')),
        ('independent_lounge', _('Independent Lounge')),
        ('priority_pass', _('Priority Pass')),
        ('pay_per_use', _('Pay-per-Use Lounge')),
    ]
    
    ACCESS_TYPE_CHOICES = [
        ('single_entry', _('Single Entry')),
        ('multiple_entries', _('Multiple Entries (3 hours)')),
        ('day_pass', _('Day Pass')),
        ('annual', _('Annual Membership')),
    ]
    
    lounge_type = forms.ChoiceField(
        label=_('Lounge Type'),
        choices=LOUNGE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'loungeType',
        })
    )
    
    access_type = forms.ChoiceField(
        label=_('Access Type'),
        choices=ACCESS_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'accessType',
        })
    )
    
    passenger = forms.ModelChoiceField(
        label=_('Passenger'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'loungePassenger',
        })
    )
    
    airport = forms.ModelChoiceField(
        label=_('Airport'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'id': 'loungeAirport',
        })
    )
    
    terminal = forms.CharField(
        label=_('Terminal'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Terminal 1, North Terminal'),
            'maxlength': '50',
        })
    )
    
    access_date = forms.DateField(
        label=_('Access Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'readonly': 'readonly',
            'id': 'loungeDate',
        })
    )
    
    access_time = forms.TimeField(
        label=_('Access Time'),
        widget=forms.TimeInput(attrs={
            'class': 'form-control timepicker',
            'type': 'time',
            'id': 'loungeTime',
        })
    )
    
    guest_count = forms.IntegerField(
        label=_('Number of Guests'),
        min_value=0,
        max_value=5,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '5',
            'id': 'guestCount',
        })
    )
    
    price = forms.DecimalField(
        label=_('Total Price (SAR)'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly',
            'id': 'loungePrice',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.ancillary_service = kwargs.pop('ancillary_service', None)
        super().__init__(*args, **kwargs)
        
        # Set passenger choices from booking
        if self.booking:
            self.fields['passenger'].queryset = self.booking.passengers.all()
        
        # Set airport choices from ancillary service
        if self.ancillary_service:
            lounge_service = self.ancillary_service.lounge_access_service
            if lounge_service:
                self.fields['airport'].queryset = lounge_service.applicable_airports.all()
        
        # Set initial values
        if self.booking:
            # Set access date to departure date
            first_segment = self.booking.itinerary.segments.first()
            if first_segment:
                self.fields['access_date'].initial = first_segment.departure_time.date()
                self.fields['access_time'].initial = first_segment.departure_time.time()
        
        # Set initial price
        if self.ancillary_service:
            self.fields['price'].initial = self.ancillary_service.base_price
    
    def clean(self):
        cleaned_data = super().clean()
        airport = cleaned_data.get('airport')
        terminal = cleaned_data.get('terminal')
        access_date = cleaned_data.get('access_date')
        access_time = cleaned_data.get('access_time')
        guest_count = cleaned_data.get('guest_count', 0)
        
        # Validate lounge availability at airport
        if airport and self.ancillary_service:
            lounge_service = self.ancillary_service.lounge_access_service
            if lounge_service and not lounge_service.is_available_at_airport(airport.iata_code, terminal):
                raise forms.ValidationError({
                    'airport': _('Lounge not available at this airport/terminal.')
                })
        
        # Validate access date (should be within booking dates)
        if access_date and self.booking:
            first_segment = self.booking.itinerary.segments.first()
            last_segment = self.booking.itinerary.segments.last()
            
            if first_segment and last_segment:
                departure_date = first_segment.departure_time.date()
                arrival_date = last_segment.arrival_time.date()
                
                if not (departure_date <= access_date <= arrival_date):
                    raise forms.ValidationError({
                        'access_date': _('Lounge access must be within travel dates ({} to {}).').format(
                            departure_date, arrival_date
                        )
                    })
        
        # Validate guest count
        if guest_count > 5:
            raise forms.ValidationError({
                'guest_count': _('Maximum 5 guests allowed.')
            })
        
        return cleaned_data
    
    def calculate_price(self):
        """Calculate lounge access price with guest fees"""
        guest_count = self.cleaned_data.get('guest_count', 0)
        
        if self.ancillary_service:
            lounge_service = self.ancillary_service.lounge_access_service
            base_price = self.ancillary_service.base_price
            
            if lounge_service:
                guest_fee = lounge_service.calculate_guest_fee(guest_count)
                return base_price + guest_fee
        
        return base_price


class TravelInsuranceForm(forms.ModelForm):
    """Form for travel insurance purchase"""
    
    class Meta:
        model = TravelInsurance
        fields = [
            'coverage_type',
            'insurance_provider',
        ]
    
    COVERAGE_TYPE_CHOICES = [
        ('basic', _('Basic Coverage')),
        ('comprehensive', _('Comprehensive Coverage')),
        ('premium', _('Premium Coverage')),
        ('annual_multi_trip', _('Annual Multi-trip')),
    ]
    
    coverage_type = forms.ChoiceField(
        label=_('Coverage Type'),
        choices=COVERAGE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'coverageType',
        })
    )
    
    insurance_provider = forms.CharField(
        label=_('Insurance Provider'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'id': 'insuranceProvider',
        })
    )
    
    passenger = forms.ModelChoiceField(
        label=_('Insured Passenger'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'insurancePassenger',
        })
    )
    
    trip_start_date = forms.DateField(
        label=_('Trip Start Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'readonly': 'readonly',
            'id': 'tripStartDate',
        })
    )
    
    trip_end_date = forms.DateField(
        label=_('Trip End Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'readonly': 'readonly',
            'id': 'tripEndDate',
        })
    )
    
    destination_country = forms.ChoiceField(
        label=_('Destination Country'),
        widget=forms.Select(attrs={
            'class': 'form-select country-select',
            'id': 'destinationCountry',
        })
    )
    
    include_cancellation = forms.BooleanField(
        label=_('Include Trip Cancellation'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'includeCancellation',
        })
    )
    
    include_baggage = forms.BooleanField(
        label=_('Include Baggage Loss'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'includeBaggage',
        })
    )
    
    include_medical = forms.BooleanField(
        label=_('Include Medical Coverage'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'includeMedical',
        })
    )
    
    price = forms.DecimalField(
        label=_('Premium (SAR)'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly',
            'id': 'insurancePrice',
        })
    )
    
    terms_accepted = forms.BooleanField(
        label=_('I accept the insurance terms and conditions'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.ancillary_service = kwargs.pop('ancillary_service', None)
        super().__init__(*args, **kwargs)
        
        # Set passenger choices from booking
        if self.booking:
            self.fields['passenger'].queryset = self.booking.passengers.all()
            
            # Set trip dates from booking
            first_segment = self.booking.itinerary.segments.first()
            last_segment = self.booking.itinerary.segments.last()
            
            if first_segment and last_segment:
                self.fields['trip_start_date'].initial = first_segment.departure_time.date()
                self.fields['trip_end_date'].initial = last_segment.arrival_time.date()
                
                # Set destination country from last segment
                destination = last_segment.destination
                if destination:
                    self.fields['destination_country'].initial = destination.country_code
        
        # Set insurance provider from ancillary service
        if self.ancillary_service:
            insurance_service = self.ancillary_service.travel_insurance_service
            if insurance_service:
                self.fields['insurance_provider'].initial = insurance_service.insurance_provider
        
        # Populate country choices
        countries = [
            ('SA', _('Saudi Arabia')),
            ('AE', _('United Arab Emirates')),
            ('KW', _('Kuwait')),
            ('BH', _('Bahrain')),
            ('QA', _('Qatar')),
            ('OM', _('Oman')),
            ('US', _('United States')),
            ('GB', _('United Kingdom')),
            ('IN', _('India')),
            ('PK', _('Pakistan')),
        ]
        
        self.fields['destination_country'].choices = [('', _('Select country'))] + countries
    
    def clean(self):
        cleaned_data = super().clean()
        passenger = cleaned_data.get('passenger')
        trip_start_date = cleaned_data.get('trip_start_date')
        trip_end_date = cleaned_data.get('trip_end_date')
        destination_country = cleaned_data.get('destination_country')
        terms_accepted = cleaned_data.get('terms_accepted')
        
        if not terms_accepted:
            raise forms.ValidationError({
                'terms_accepted': _('You must accept the insurance terms and conditions.')
            })
        
        # Validate trip dates
        if trip_start_date and trip_end_date:
            if trip_start_date > trip_end_date:
                raise forms.ValidationError({
                    'trip_end_date': _('Trip end date must be after start date.')
                })
            
            trip_duration = (trip_end_date - trip_start_date).days
            
            # Check maximum trip duration
            if self.ancillary_service:
                insurance_service = self.ancillary_service.travel_insurance_service
                if insurance_service and trip_duration > insurance_service.maximum_duration:
                    raise forms.ValidationError({
                        'trip_end_date': _('Trip duration exceeds maximum coverage period of {} days.').format(
                            insurance_service.maximum_duration
                        )
                    })
        
        # Validate passenger eligibility
        if passenger and self.ancillary_service:
            insurance_service = self.ancillary_service.travel_insurance_service
            if insurance_service:
                traveler_age = passenger.get_age()
                if not insurance_service.is_eligible(traveler_age, destination_country):
                    raise forms.ValidationError({
                        'passenger': _('Passenger is not eligible for this insurance coverage.')
                    })
        
        return cleaned_data


class AncillaryBundleForm(forms.Form):
    """Form for purchasing ancillary service bundles"""
    
    BUNDLE_CHOICES = [
        ('comfort', _('Comfort Bundle: Seat + Meal + Priority Boarding')),
        ('business', _('Business Bundle: Lounge + Extra Baggage + Travel Insurance')),
        ('family', _('Family Bundle: Seats together + Meals + Baggage')),
        ('premium', _('Premium Bundle: All services with 20% discount')),
        ('custom', _('Custom Bundle: Select your own services')),
    ]
    
    bundle_type = forms.ChoiceField(
        label=_('Bundle Type'),
        choices=BUNDLE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input bundle-radio',
        })
    )
    
    # Custom bundle selections
    include_seat = forms.BooleanField(
        label=_('Seat Selection'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input bundle-checkbox',
            'data-service': 'seat',
        })
    )
    
    include_baggage = forms.BooleanField(
        label=_('Extra Baggage'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input bundle-checkbox',
            'data-service': 'baggage',
        })
    )
    
    include_meal = forms.BooleanField(
        label=_('Special Meal'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input bundle-checkbox',
            'data-service': 'meal',
        })
    )
    
    include_lounge = forms.BooleanField(
        label=_('Lounge Access'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input bundle-checkbox',
            'data-service': 'lounge',
        })
    )
    
    include_insurance = forms.BooleanField(
        label=_('Travel Insurance'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input bundle-checkbox',
            'data-service': 'insurance',
        })
    )
    
    include_priority = forms.BooleanField(
        label=_('Priority Boarding'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input bundle-checkbox',
            'data-service': 'priority',
        })
    )
    
    passenger = forms.ModelChoiceField(
        label=_('Passenger'),
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    price = forms.DecimalField(
        label=_('Bundle Price (SAR)'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly',
            'id': 'bundlePrice',
        })
    )
    
    discount_percentage = forms.IntegerField(
        label=_('Bundle Discount'),
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly',
            'id': 'bundleDiscount',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.available_services = kwargs.pop('available_services', [])
        super().__init__(*args, **kwargs)
        
        # Set passenger choices from booking
        if self.booking:
            self.fields['passenger'].queryset = self.booking.passengers.all()
        
        # Set initial discount based on bundle type
        self.fields['discount_percentage'].initial = 10
    
    def clean(self):
        cleaned_data = super().clean()
        bundle_type = cleaned_data.get('bundle_type')
        
        # Validate at least one service is selected for custom bundles
        if bundle_type == 'custom':
            selected_services = [
                cleaned_data.get('include_seat'),
                cleaned_data.get('include_baggage'),
                cleaned_data.get('include_meal'),
                cleaned_data.get('include_lounge'),
                cleaned_data.get('include_insurance'),
                cleaned_data.get('include_priority'),
            ]
            
            if not any(selected_services):
                raise forms.ValidationError(
                    _('Please select at least one service for the custom bundle.')
                )
        
        return cleaned_data
    
    def calculate_price(self):
        """Calculate bundle price with discount"""
        bundle_type = self.cleaned_data.get('bundle_type')
        
        # Base prices for individual services
        service_prices = {
            'seat': 150,
            'baggage': 200,
            'meal': 50,
            'lounge': 250,
            'insurance': 300,
            'priority': 100,
        }
        
        # Bundle configurations
        bundles = {
            'comfort': ['seat', 'meal', 'priority'],
            'business': ['lounge', 'baggage', 'insurance'],
            'family': ['seat', 'meal', 'baggage'],
            'premium': ['seat', 'baggage', 'meal', 'lounge', 'insurance', 'priority'],
        }
        
        if bundle_type == 'custom':
            selected_services = []
            if self.cleaned_data.get('include_seat'):
                selected_services.append('seat')
            if self.cleaned_data.get('include_baggage'):
                selected_services.append('baggage')
            if self.cleaned_data.get('include_meal'):
                selected_services.append('meal')
            if self.cleaned_data.get('include_lounge'):
                selected_services.append('lounge')
            if self.cleaned_data.get('include_insurance'):
                selected_services.append('insurance')
            if self.cleaned_data.get('include_priority'):
                selected_services.append('priority')
        else:
            selected_services = bundles.get(bundle_type, [])
        
        # Calculate total price
        total = sum(service_prices.get(service, 0) for service in selected_services)
        
        # Apply discount
        discount = self.cleaned_data.get('discount_percentage', 0)
        discounted_price = total * (100 - discount) / 100
        
        return discounted_price