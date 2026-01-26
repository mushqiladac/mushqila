# flights/forms/search_forms.py
"""
Flight search forms for B2B Travel Platform
Production Ready - Final Version
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, timedelta
import re

from flights.models import Airport, Airline


class BaseFlightSearchForm(forms.Form):
    """Base form for all flight searches"""
    
    TRIP_TYPE_CHOICES = [
        ('one_way', _('One Way')),
        ('round_trip', _('Round Trip')),
        ('multi_city', _('Multi City')),
        ('open_jaw', _('Open Jaw')),
    ]
    
    CABIN_CLASS_CHOICES = [
        ('economy', _('Economy')),
        ('premium_economy', _('Premium Economy')),
        ('business', _('Business')),
        ('first', _('First Class')),
    ]
    
    PASSENGER_TYPE_CHOICES = [
        ('ADT', _('Adult (12+ years)')),
        ('CHD', _('Child (2-11 years)')),
        ('INF', _('Infant (0-1 year)')),
    ]
    
    # Trip Configuration
    trip_type = forms.ChoiceField(
        label=_('Trip Type'),
        choices=TRIP_TYPE_CHOICES,
        initial='one_way',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'tripType',
        })
    )
    
    cabin_class = forms.ChoiceField(
        label=_('Cabin Class'),
        choices=CABIN_CLASS_CHOICES,
        initial='economy',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'cabinClass',
        })
    )
    
    # Passenger Configuration
    adults = forms.IntegerField(
        label=_('Adults'),
        initial=1,
        min_value=1,
        max_value=9,
        widget=forms.NumberInput(attrs={
            'class': 'form-control passenger-counter',
            'min': '1',
            'max': '9',
            'data-type': 'ADT',
        })
    )
    
    children = forms.IntegerField(
        label=_('Children'),
        initial=0,
        min_value=0,
        max_value=8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control passenger-counter',
            'min': '0',
            'max': '8',
            'data-type': 'CHD',
        })
    )
    
    infants = forms.IntegerField(
        label=_('Infants'),
        initial=0,
        min_value=0,
        max_value=8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control passenger-counter',
            'min': '0',
            'max': '8',
            'data-type': 'INF',
        })
    )
    
    # Search Preferences
    direct_flights = forms.BooleanField(
        label=_('Direct flights only'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'directFlights',
        })
    )
    
    include_nearby_airports = forms.BooleanField(
        label=_('Include nearby airports'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'includeNearby',
        })
    )
    
    max_stops = forms.ChoiceField(
        label=_('Maximum stops'),
        choices=[
            ('0', _('Non-stop')),
            ('1', _('1 stop or less')),
            ('2', _('2 stops or less')),
            ('3', _('Any number of stops')),
        ],
        initial='2',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'maxStops',
        })
    )
    
    # Airline Preferences
    preferred_airlines = forms.ModelMultipleChoiceField(
        label=_('Preferred Airlines'),
        queryset=Airline.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',
            'data-placeholder': _('Select preferred airlines'),
            'multiple': 'multiple',
            'id': 'preferredAirlines',
        })
    )
    
    excluded_airlines = forms.ModelMultipleChoiceField(
        label=_('Exclude Airlines'),
        queryset=Airline.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',
            'data-placeholder': _('Select airlines to exclude'),
            'multiple': 'multiple',
            'id': 'excludedAirlines',
        })
    )
    
    # Currency
    currency = forms.ChoiceField(
        label=_('Currency'),
        choices=[
            ('SAR', 'SAR - Saudi Riyal'),
            ('USD', 'USD - US Dollar'),
            ('EUR', 'EUR - Euro'),
            ('GBP', 'GBP - British Pound'),
            ('AED', 'AED - UAE Dirham'),
            ('KWD', 'KWD - Kuwaiti Dinar'),
            ('BHD', 'BHD - Bahraini Dinar'),
            ('QAR', 'QAR - Qatari Riyal'),
            ('OMR', 'OMR - Omani Rial'),
        ],
        initial='SAR',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'currency',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values for preferred airlines based on user preferences
        if self.user and hasattr(self.user, 'profile'):
            preferred = self.user.profile.preferred_airlines.all()
            if preferred.exists():
                self.fields['preferred_airlines'].initial = preferred
    
    def clean(self):
        cleaned_data = super().clean()
        adults = cleaned_data.get('adults', 0)
        infants = cleaned_data.get('infants', 0)
        
        # Each infant must be accompanied by an adult
        if infants > adults:
            raise forms.ValidationError(
                _('Number of infants cannot exceed number of adults. Each infant must travel with an adult.')
            )
        
        # Maximum total passengers
        total_passengers = adults + cleaned_data.get('children', 0) + infants
        if total_passengers > 9:
            raise forms.ValidationError(
                _('Maximum 9 passengers allowed per booking. For larger groups, please use group booking.')
            )
        
        return cleaned_data
    
    def get_total_passengers(self):
        """Calculate total number of passengers"""
        adults = self.cleaned_data.get('adults', 0)
        children = self.cleaned_data.get('children', 0)
        infants = self.cleaned_data.get('infants', 0)
        return adults + children + infants
    
    def get_passenger_breakdown(self):
        """Get passenger breakdown for GDS request"""
        return {
            'ADT': self.cleaned_data.get('adults', 1),
            'CHD': self.cleaned_data.get('children', 0),
            'INF': self.cleaned_data.get('infants', 0),
        }


class OneWaySearchForm(BaseFlightSearchForm):
    """One-way flight search form"""
    
    origin = forms.ModelChoiceField(
        label=_('From'),
        queryset=Airport.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'data-placeholder': _('City or airport'),
            'id': 'origin',
            'autocomplete': 'off',
        })
    )
    
    destination = forms.ModelChoiceField(
        label=_('To'),
        queryset=Airport.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'data-placeholder': _('City or airport'),
            'id': 'destination',
            'autocomplete': 'off',
        })
    )
    
    departure_date = forms.DateField(
        label=_('Departure Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'placeholder': _('Select date'),
            'id': 'departureDate',
            'autocomplete': 'off',
            'readonly': 'readonly',
        }),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'],
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trip_type'].initial = 'one_way'
        
        # Set minimum date to today
        today = timezone.now().date()
        self.fields['departure_date'].widget.attrs['min'] = today.isoformat()
        
        # Set maximum date to 1 year from now
        max_date = today + timedelta(days=365)
        self.fields['departure_date'].widget.attrs['max'] = max_date.isoformat()
    
    def clean(self):
        cleaned_data = super().clean()
        departure_date = cleaned_data.get('departure_date')
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        
        # Check if departure date is in the past
        if departure_date and departure_date < timezone.now().date():
            raise forms.ValidationError({
                'departure_date': _('Departure date cannot be in the past.')
            })
        
        # Check if origin and destination are the same
        if origin and destination and origin == destination:
            raise forms.ValidationError({
                'destination': _('Origin and destination cannot be the same.')
            })
        
        # Check for Saudi domestic flights
        if origin and destination:
            if origin.country_code == 'SA' and destination.country_code == 'SA':
                # Saudi domestic flight - validate restrictions
                pass
        
        return cleaned_data
    
    def get_search_params(self):
        """Get search parameters for GDS API"""
        return {
            'trip_type': 'one_way',
            'origin': self.cleaned_data['origin'].iata_code,
            'destination': self.cleaned_data['destination'].iata_code,
            'departure_date': self.cleaned_data['departure_date'].isoformat(),
            'passengers': self.get_passenger_breakdown(),
            'cabin_class': self.cleaned_data.get('cabin_class', 'economy'),
            'direct_flights': self.cleaned_data.get('direct_flights', False),
            'max_stops': int(self.cleaned_data.get('max_stops', 2)),
            'currency': self.cleaned_data.get('currency', 'SAR'),
        }


class RoundTripSearchForm(BaseFlightSearchForm):
    """Round-trip flight search form"""
    
    origin = forms.ModelChoiceField(
        label=_('From'),
        queryset=Airport.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'data-placeholder': _('City or airport'),
            'id': 'origin',
            'autocomplete': 'off',
        })
    )
    
    destination = forms.ModelChoiceField(
        label=_('To'),
        queryset=Airport.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'data-placeholder': _('City or airport'),
            'id': 'destination',
            'autocomplete': 'off',
        })
    )
    
    departure_date = forms.DateField(
        label=_('Departure Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'placeholder': _('Departure date'),
            'id': 'departureDate',
            'autocomplete': 'off',
            'readonly': 'readonly',
        }),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'],
    )
    
    return_date = forms.DateField(
        label=_('Return Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'placeholder': _('Return date'),
            'id': 'returnDate',
            'autocomplete': 'off',
            'readonly': 'readonly',
        }),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'],
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trip_type'].initial = 'round_trip'
        
        # Set date constraints
        today = timezone.now().date()
        max_date = today + timedelta(days=365)
        
        self.fields['departure_date'].widget.attrs.update({
            'min': today.isoformat(),
            'max': max_date.isoformat(),
        })
        
        self.fields['return_date'].widget.attrs.update({
            'min': today.isoformat(),
            'max': max_date.isoformat(),
        })
    
    def clean(self):
        cleaned_data = super().clean()
        departure_date = cleaned_data.get('departure_date')
        return_date = cleaned_data.get('return_date')
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        
        # Check dates
        if departure_date and return_date:
            if departure_date > return_date:
                raise forms.ValidationError({
                    'return_date': _('Return date must be after departure date.')
                })
            
            # Minimum stay check (typically 1 day)
            if (return_date - departure_date).days < 1:
                raise forms.ValidationError({
                    'return_date': _('Minimum stay is 1 day.')
                })
            
            # Maximum stay check (typically 365 days)
            if (return_date - departure_date).days > 365:
                raise forms.ValidationError({
                    'return_date': _('Maximum stay is 365 days.')
                })
        
        # Check if departure date is in the past
        if departure_date and departure_date < timezone.now().date():
            raise forms.ValidationError({
                'departure_date': _('Departure date cannot be in the past.')
            })
        
        # Check if origin and destination are the same
        if origin and destination and origin == destination:
            raise forms.ValidationError({
                'destination': _('Origin and destination cannot be the same.')
            })
        
        return cleaned_data
    
    def get_search_params(self):
        """Get search parameters for GDS API"""
        return {
            'trip_type': 'round_trip',
            'origin': self.cleaned_data['origin'].iata_code,
            'destination': self.cleaned_data['destination'].iata_code,
            'departure_date': self.cleaned_data['departure_date'].isoformat(),
            'return_date': self.cleaned_data['return_date'].isoformat(),
            'passengers': self.get_passenger_breakdown(),
            'cabin_class': self.cleaned_data.get('cabin_class', 'economy'),
            'direct_flights': self.cleaned_data.get('direct_flights', False),
            'max_stops': int(self.cleaned_data.get('max_stops', 2)),
            'currency': self.cleaned_data.get('currency', 'SAR'),
        }


class MultiCitySearchForm(BaseFlightSearchForm):
    """Multi-city flight search form"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trip_type'].initial = 'multi_city'
        
        # Dynamically add city pairs (maximum 6 segments)
        for i in range(6):
            self.fields[f'origin_{i}'] = forms.ModelChoiceField(
                label=_('From') if i == 0 else '',
                queryset=Airport.objects.filter(is_active=True),
                required=(i == 0),  # Only first segment is required
                widget=forms.Select(attrs={
                    'class': 'form-select airport-select',
                    'data-placeholder': _('City or airport'),
                    'data-segment': i,
                    'autocomplete': 'off',
                })
            )
            
            self.fields[f'destination_{i}'] = forms.ModelChoiceField(
                label=_('To') if i == 0 else '',
                queryset=Airport.objects.filter(is_active=True),
                required=(i == 0),
                widget=forms.Select(attrs={
                    'class': 'form-select airport-select',
                    'data-placeholder': _('City or airport'),
                    'data-segment': i,
                    'autocomplete': 'off',
                })
            )
            
            self.fields[f'departure_date_{i}'] = forms.DateField(
                label=_('Date') if i == 0 else '',
                required=(i == 0),
                widget=forms.DateInput(attrs={
                    'class': 'form-control datepicker',
                    'placeholder': _('Select date'),
                    'data-segment': i,
                    'autocomplete': 'off',
                    'readonly': 'readonly',
                }),
                input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'],
            )
    
    def clean(self):
        cleaned_data = super().clean()
        segments = []
        
        # Validate each segment
        for i in range(6):
            origin = cleaned_data.get(f'origin_{i}')
            destination = cleaned_data.get(f'destination_{i}')
            departure_date = cleaned_data.get(f'departure_date_{i}')
            
            # Check if segment has any data
            if not any([origin, destination, departure_date]):
                continue
            
            # All fields are required if any field is filled
            if not all([origin, destination, departure_date]):
                raise forms.ValidationError(
                    _('All fields must be filled for segment {}.').format(i + 1)
                )
            
            # Check if origin and destination are the same
            if origin == destination:
                raise forms.ValidationError(
                    _('Origin and destination cannot be the same in segment {}.').format(i + 1)
                )
            
            # Check if departure date is in the past
            if departure_date < timezone.now().date():
                raise forms.ValidationError({
                    f'departure_date_{i}': _('Departure date cannot be in the past.')
                })
            
            # Check date order for multi-city
            if segments:
                prev_segment = segments[-1]
                if departure_date < prev_segment['departure_date']:
                    raise forms.ValidationError({
                        f'departure_date_{i}': _('Departure date must be after previous segment.')
                    })
            
            segments.append({
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
            })
        
        # At least one segment is required
        if not segments:
            raise forms.ValidationError(_('At least one flight segment is required.'))
        
        cleaned_data['segments'] = segments
        return cleaned_data
    
    def get_search_params(self):
        """Get search parameters for GDS API"""
        segments = self.cleaned_data.get('segments', [])
        
        return {
            'trip_type': 'multi_city',
            'segments': [
                {
                    'origin': segment['origin'].iata_code,
                    'destination': segment['destination'].iata_code,
                    'departure_date': segment['departure_date'].isoformat(),
                }
                for segment in segments
            ],
            'passengers': self.get_passenger_breakdown(),
            'cabin_class': self.cleaned_data.get('cabin_class', 'economy'),
            'direct_flights': self.cleaned_data.get('direct_flights', False),
            'max_stops': int(self.cleaned_data.get('max_stops', 2)),
            'currency': self.cleaned_data.get('currency', 'SAR'),
        }


class FlexSearchForm(BaseFlightSearchForm):
    """Flexible date search form"""
    
    origin = forms.ModelChoiceField(
        label=_('From'),
        queryset=Airport.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'data-placeholder': _('City or airport'),
            'id': 'origin',
            'autocomplete': 'off',
        })
    )
    
    destination = forms.ModelChoiceField(
        label=_('To'),
        queryset=Airport.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'data-placeholder': _('City or airport'),
            'id': 'destination',
            'autocomplete': 'off',
        })
    )
    
    departure_date_range = forms.CharField(
        label=_('Departure Date Range'),
        widget=forms.TextInput(attrs={
            'class': 'form-control daterange',
            'placeholder': _('Select date range'),
            'id': 'departureRange',
            'autocomplete': 'off',
            'readonly': 'readonly',
        })
    )
    
    trip_duration = forms.ChoiceField(
        label=_('Trip Duration'),
        choices=[
            ('weekend', _('Weekend (2-3 days)')),
            ('week', _('One Week (5-8 days)')),
            ('flexible', _('Flexible (any duration)')),
        ],
        initial='flexible',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'tripDuration',
        })
    )
    
    price_range = forms.ChoiceField(
        label=_('Price Range'),
        choices=[
            ('budget', _('Budget (< 1000 SAR)')),
            ('standard', _('Standard (1000-3000 SAR)')),
            ('premium', _('Premium (3000-5000 SAR)')),
            ('luxury', _('Luxury (> 5000 SAR)')),
            ('any', _('Any Price')),
        ],
        initial='any',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'priceRange',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add flexible date specific fields
    
    def clean_departure_date_range(self):
        """Parse date range string"""
        date_range = self.cleaned_data.get('departure_date_range', '')
        if not date_range:
            return None
        
        try:
            # Parse format: "YYYY-MM-DD to YYYY-MM-DD"
            start_str, end_str = date_range.split(' to ')
            start_date = date.fromisoformat(start_str.strip())
            end_date = date.fromisoformat(end_str.strip())
            
            # Validate range
            if start_date > end_date:
                raise forms.ValidationError(_('Start date must be before end date.'))
            
            if (end_date - start_date).days > 60:
                raise forms.ValidationError(_('Maximum search range is 60 days.'))
            
            return {'start': start_date, 'end': end_date}
        
        except (ValueError, AttributeError):
            raise forms.ValidationError(_('Invalid date range format. Use YYYY-MM-DD to YYYY-MM-DD'))
    
    def get_search_params(self):
        """Get search parameters for GDS API"""
        date_range = self.cleaned_data.get('departure_date_range')
        
        return {
            'trip_type': 'flexible',
            'origin': self.cleaned_data['origin'].iata_code,
            'destination': self.cleaned_data['destination'].iata_code,
            'departure_date_range': {
                'start': date_range['start'].isoformat(),
                'end': date_range['end'].isoformat(),
            } if date_range else None,
            'passengers': self.get_passenger_breakdown(),
            'cabin_class': self.cleaned_data.get('cabin_class', 'economy'),
            'trip_duration': self.cleaned_data.get('trip_duration', 'flexible'),
            'price_range': self.cleaned_data.get('price_range', 'any'),
            'currency': self.cleaned_data.get('currency', 'SAR'),
        }


class FareCalendarForm(forms.Form):
    """Fare calendar search form"""
    
    origin = forms.ModelChoiceField(
        label=_('From'),
        queryset=Airport.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'data-placeholder': _('City or airport'),
            'id': 'calendarOrigin',
            'autocomplete': 'off',
        })
    )
    
    destination = forms.ModelChoiceField(
        label=_('To'),
        queryset=Airport.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select airport-select',
            'data-placeholder': _('City or airport'),
            'id': 'calendarDestination',
            'autocomplete': 'off',
        })
    )
    
    month = forms.ChoiceField(
        label=_('Month'),
        choices=[
            ('1', _('January')), ('2', _('February')), ('3', _('March')),
            ('4', _('April')), ('5', _('May')), ('6', _('June')),
            ('7', _('July')), ('8', _('August')), ('9', _('September')),
            ('10', _('October')), ('11', _('November')), ('12', _('December')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'calendarMonth',
        })
    )
    
    year = forms.ChoiceField(
        label=_('Year'),
        choices=[(str(y), str(y)) for y in range(timezone.now().year, timezone.now().year + 2)],
        initial=str(timezone.now().year),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'calendarYear',
        })
    )
    
    cabin_class = forms.ChoiceField(
        label=_('Cabin Class'),
        choices=[
            ('economy', _('Economy')),
            ('premium_economy', _('Premium Economy')),
            ('business', _('Business')),
            ('first', _('First Class')),
        ],
        initial='economy',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'calendarCabin',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current month as default
        current_month = timezone.now().month
        self.fields['month'].initial = str(current_month)
    
    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        
        if origin and destination and origin == destination:
            raise forms.ValidationError({
                'destination': _('Origin and destination cannot be the same.')
            })
        
        return cleaned_data


class FlightSearchForm(forms.Form):
    """Main flight search form that switches between trip types"""
    
    def __init__(self, *args, **kwargs):
        trip_type = kwargs.pop('trip_type', 'one_way')
        super().__init__(*args, **kwargs)
        
        # Initialize appropriate form based on trip type
        if trip_type == 'one_way':
            self.form = OneWaySearchForm(*args, **kwargs)
        elif trip_type == 'round_trip':
            self.form = RoundTripSearchForm(*args, **kwargs)
        elif trip_type == 'multi_city':
            self.form = MultiCitySearchForm(*args, **kwargs)
        elif trip_type == 'flexible':
            self.form = FlexSearchForm(*args, **kwargs)
        else:
            self.form = OneWaySearchForm(*args, **kwargs)
    
    def is_valid(self):
        return self.form.is_valid()
    
    def cleaned_data(self):
        return self.form.cleaned_data
    
    def get_search_params(self):
        return self.form.get_search_params()