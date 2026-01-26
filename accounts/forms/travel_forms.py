# accounts/forms/travel_forms.py
"""
Travel booking forms for B2B Travel Mushqila - Saudi Arabia
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator
from ..models import FlightBooking, HotelBooking, HajjPackage, UmrahPackage, ServiceSupplier
import re


class FlightBookingForm(forms.ModelForm):
    """Flight booking form"""
    
    passenger_name = forms.CharField(
        label=_('Passenger Name'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Full name as per passport')
        })
    )
    
    passenger_email = forms.EmailField(
        label=_('Passenger Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'passenger@example.com'
        }),
        required=False
    )
    
    passenger_phone = forms.CharField(
        label=_('Passenger Phone'),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX'
        }),
        required=False
    )
    
    departure_city = forms.CharField(
        label=_('Departure City'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Riyadh')
        })
    )
    
    arrival_city = forms.CharField(
        label=_('Arrival City'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Jeddah')
        })
    )
    
    departure_date = forms.SplitDateTimeField(
        label=_('Departure Date & Time'),
        widget=forms.SplitDateTimeWidget(
            date_attrs={
                'class': 'form-control',
                'type': 'date'
            },
            time_attrs={
                'class': 'form-control',
                'type': 'time'
            }
        )
    )
    
    arrival_date = forms.SplitDateTimeField(
        label=_('Arrival Date & Time'),
        widget=forms.SplitDateTimeWidget(
            date_attrs={
                'class': 'form-control',
                'type': 'date'
            },
            time_attrs={
                'class': 'form-control',
                'type': 'time'
            }
        )
    )
    
    base_fare = forms.DecimalField(
        label=_('Base Fare (SAR)'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    tax = forms.DecimalField(
        label=_('Tax (SAR)'),
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    vat = forms.DecimalField(
        label=_('VAT (SAR)'),
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    booking_class = forms.ChoiceField(
        label=_('Booking Class'),
        choices=[
            ('', _('Select Class')),
            ('Economy', 'Economy'),
            ('Premium Economy', 'Premium Economy'),
            ('Business', 'Business'),
            ('First', 'First Class'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    travel_type = forms.ChoiceField(
        label=_('Travel Type'),
        choices=FlightBooking.TravelType.choices,
        initial=FlightBooking.TravelType.DOMESTIC,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    airline = forms.ModelChoiceField(
        label=_('Airline'),
        queryset=ServiceSupplier.objects.filter(
            supplier_type=ServiceSupplier.SupplierType.AIRLINE,
            is_active=True
        ),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'airline_select'
        })
    )
    
    booking_notes = forms.CharField(
        label=_('Booking Notes'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Additional notes for this booking...')
        }),
        required=False
    )
    
    class Meta:
        model = FlightBooking
        fields = [
            'passenger_name', 'passenger_email', 'passenger_phone',
            'airline', 'flight_number', 'departure_city', 'arrival_city',
            'departure_airport', 'arrival_airport', 'departure_date',
            'arrival_date', 'travel_type', 'booking_class', 'base_fare',
            'tax', 'vat', 'booking_notes'
        ]
        widgets = {
            'flight_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SV 123'
            }),
            'departure_airport': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RUH'
            }),
            'arrival_airport': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'JED'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set VAT to 15% by default
        if not self.instance.pk:
            self.fields['vat'].initial = 0
    
    def clean(self):
        cleaned_data = super().clean()
        departure_date = cleaned_data.get('departure_date')
        arrival_date = cleaned_data.get('arrival_date')
        base_fare = cleaned_data.get('base_fare')
        tax = cleaned_data.get('tax') or 0
        vat = cleaned_data.get('vat') or 0
        
        if departure_date and arrival_date:
            if arrival_date <= departure_date:
                self.add_error('arrival_date', _('Arrival date must be after departure date.'))
        
        if base_fare:
            # Calculate total amount
            total = base_fare + tax + vat
            cleaned_data['total_amount'] = total
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.agent = self.user
        
        # Calculate total amount
        base_fare = self.cleaned_data.get('base_fare', 0)
        tax = self.cleaned_data.get('tax', 0) or 0
        vat = self.cleaned_data.get('vat', 0) or 0
        instance.total_amount = base_fare + tax + vat
        
        # Calculate commission
        if instance.agent.commission_rate:
            commission_rate = instance.agent.commission_rate
            if instance.travel_type == 'hajj':
                commission_rate *= 1.2
            elif instance.travel_type == 'umrah':
                commission_rate *= 1.15
            
            instance.commission_amount = (instance.base_fare * commission_rate) / 100
        
        if commit:
            instance.save()
        
        return instance


class HotelBookingForm(forms.ModelForm):
    """Hotel booking form"""
    
    guest_name = forms.CharField(
        label=_('Guest Name'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Full name as per ID')
        })
    )
    
    guest_email = forms.EmailField(
        label=_('Guest Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'guest@example.com'
        }),
        required=False
    )
    
    guest_phone = forms.CharField(
        label=_('Guest Phone'),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX'
        }),
        required=False
    )
    
    check_in = forms.DateField(
        label=_('Check-in Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    check_out = forms.DateField(
        label=_('Check-out Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    room_rate = forms.DecimalField(
        label=_('Room Rate per Night (SAR)'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    hotel = forms.ModelChoiceField(
        label=_('Hotel'),
        queryset=ServiceSupplier.objects.filter(
            supplier_type=ServiceSupplier.SupplierType.HOTEL,
            is_active=True
        ),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'hotel_select'
        })
    )
    
    booking_notes = forms.CharField(
        label=_('Booking Notes'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Special requests, room preferences, etc.')
        }),
        required=False
    )
    
    class Meta:
        model = HotelBooking
        fields = [
            'guest_name', 'guest_email', 'guest_phone',
            'hotel', 'check_in', 'check_out', 'rooms',
            'adults', 'children', 'room_rate', 'booking_notes'
        ]
        widgets = {
            'rooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'adults': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20'
            }),
            'children': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        rooms = cleaned_data.get('rooms') or 1
        room_rate = cleaned_data.get('room_rate') or 0
        
        if check_in and check_out:
            if check_out <= check_in:
                self.add_error('check_out', _('Check-out date must be after check-in date.'))
            
            # Calculate nights
            nights = (check_out - check_in).days
            if nights <= 0:
                self.add_error('check_out', _('Minimum stay is 1 night.'))
            
            cleaned_data['nights'] = nights
        
        if room_rate and rooms:
            # Calculate total amount
            nights = cleaned_data.get('nights', 1)
            total = room_rate * rooms * nights
            cleaned_data['total_amount'] = total
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.agent = self.user
        
        # Calculate total amount
        room_rate = self.cleaned_data.get('room_rate', 0)
        rooms = self.cleaned_data.get('rooms', 1)
        nights = self.cleaned_data.get('nights', 1)
        instance.total_amount = room_rate * rooms * nights
        
        # Calculate commission
        if instance.agent.commission_rate:
            commission_rate = instance.agent.commission_rate
            instance.commission_amount = (instance.total_amount * commission_rate) / 100
        
        if commit:
            instance.save()
        
        return instance


class HajjBookingForm(forms.Form):
    """Hajj package booking form"""
    
    package = forms.ModelChoiceField(
        label=_('Hajj Package'),
        queryset=HajjPackage.objects.filter(status=HajjPackage.PackageStatus.AVAILABLE),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'hajj_package'
        })
    )
    
    pilgrims = forms.IntegerField(
        label=_('Number of Pilgrims'),
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '10'
        })
    )
    
    contact_person = forms.CharField(
        label=_('Contact Person'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Name of main contact person')
        })
    )
    
    contact_email = forms.EmailField(
        label=_('Contact Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contact@example.com'
        })
    )
    
    contact_phone = forms.CharField(
        label=_('Contact Phone'),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX'
        })
    )
    
    special_requests = forms.CharField(
        label=_('Special Requests'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Any special requirements or requests...')
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        package = cleaned_data.get('package')
        pilgrims = cleaned_data.get('pilgrims')
        
        if package and pilgrims:
            if pilgrims > package.available_slots:
                self.add_error('pilgrims', 
                    _('Only %(slots)s slots available for this package.') % 
                    {'slots': package.available_slots}
                )
        
        return cleaned_data


class UmrahBookingForm(forms.Form):
    """Umrah package booking form"""
    
    package = forms.ModelChoiceField(
        label=_('Umrah Package'),
        queryset=UmrahPackage.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'umrah_package'
        })
    )
    
    travelers = forms.IntegerField(
        label=_('Number of Travelers'),
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '20'
        })
    )
    
    departure_date = forms.DateField(
        label=_('Preferred Departure Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    return_date = forms.DateField(
        label=_('Expected Return Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    contact_person = forms.CharField(
        label=_('Contact Person'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Name of main contact person')
        })
    )
    
    contact_email = forms.EmailField(
        label=_('Contact Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contact@example.com'
        })
    )
    
    contact_phone = forms.CharField(
        label=_('Contact Phone'),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        departure_date = cleaned_data.get('departure_date')
        return_date = cleaned_data.get('return_date')
        
        if departure_date and return_date:
            if return_date <= departure_date:
                self.add_error('return_date', _('Return date must be after departure date.'))
        
        return cleaned_data


class VisaApplicationForm(forms.Form):
    """Visa application form"""
    
    APPLICANT_TYPES = [
        ('individual', _('Individual')),
        ('family', _('Family')),
        ('group', _('Group')),
    ]
    
    applicant_type = forms.ChoiceField(
        label=_('Applicant Type'),
        choices=APPLICANT_TYPES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    full_name = forms.CharField(
        label=_('Full Name (as per passport)'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    passport_number = forms.CharField(
        label=_('Passport Number'),
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    nationality = forms.CharField(
        label=_('Nationality'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    date_of_birth = forms.DateField(
        label=_('Date of Birth'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    passport_expiry = forms.DateField(
        label=_('Passport Expiry Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    visa_type = forms.ChoiceField(
        label=_('Visa Type'),
        choices=[
            ('tourist', _('Tourist Visa')),
            ('business', _('Business Visa')),
            ('hajj', _('Hajj Visa')),
            ('umrah', _('Umrah Visa')),
            ('transit', _('Transit Visa')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    entry_date = forms.DateField(
        label=_('Intended Entry Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    exit_date = forms.DateField(
        label=_('Intended Exit Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    passport_copy = forms.FileField(
        label=_('Passport Copy'),
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    photo = forms.FileField(
        label=_('Passport Photo'),
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png'
        })
    )
    
    def clean_passport_expiry(self):
        expiry_date = self.cleaned_data.get('passport_expiry')
        entry_date = self.cleaned_data.get('entry_date')
        
        if expiry_date and entry_date:
            # Passport should be valid for at least 6 months from entry date
            import datetime
            six_months_later = entry_date + datetime.timedelta(days=180)
            
            if expiry_date < six_months_later:
                raise ValidationError(
                    _('Passport must be valid for at least 6 months from entry date.')
                )
        
        return expiry_date
    
    def clean(self):
        cleaned_data = super().clean()
        entry_date = cleaned_data.get('entry_date')
        exit_date = cleaned_data.get('exit_date')
        
        if entry_date and exit_date:
            if exit_date <= entry_date:
                self.add_error('exit_date', _('Exit date must be after entry date.'))
            
            # Check maximum stay
            stay_days = (exit_date - entry_date).days
            if stay_days > 90:
                self.add_error('exit_date', _('Maximum stay is 90 days.'))
        
        return cleaned_data