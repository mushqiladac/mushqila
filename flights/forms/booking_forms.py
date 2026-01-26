# flights/forms/booking_forms.py
"""
Booking forms for B2B Travel Platform
Production Ready - Final Version
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid

from flights.models import Booking, Passenger, FlightItinerary
from accounts.models import User
from accounts.models.b2b import BusinessUnit


class BookingForm(forms.ModelForm):
    """Main booking form"""
    
    class Meta:
        model = Booking
        fields = [
            'special_instructions',
            'internal_notes',
            'customer_remarks',
            'cost_center',
            'booking_source',
        ]
    
    special_instructions = forms.CharField(
        label=_('Special Instructions'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Any special instructions for the airline...'),
            'maxlength': '500',
        })
    )
    
    internal_notes = forms.CharField(
        label=_('Internal Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Internal notes for agents...'),
            'maxlength': '1000',
        })
    )
    
    customer_remarks = forms.CharField(
        label=_('Customer Remarks'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Remarks from the customer...'),
            'maxlength': '500',
        })
    )
    
    cost_center = forms.CharField(
        label=_('Cost Center'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., DEPT-001, PROJECT-ABC'),
            'maxlength': '50',
        })
    )
    
    booking_source = forms.ChoiceField(
        label=_('Booking Source'),
        choices=[
            ('web', _('Web Portal')),
            ('mobile', _('Mobile App')),
            ('api', _('API Integration')),
            ('manual', _('Manual Booking')),
            ('call_center', _('Call Center')),
        ],
        initial='web',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    # Dynamic passenger forms will be added in __init__
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.itinerary = kwargs.pop('itinerary', None)
        self.passenger_count = kwargs.pop('passenger_count', 1)
        super().__init__(*args, **kwargs)
        
        # Set initial values
        if self.user:
            self.fields['booking_source'].initial = 'web'
            
            # Auto-generate cost center for corporate clients
            if hasattr(self.user, 'profile') and self.user.profile.corporate_client:
                self.fields['cost_center'].initial = f"CORP-{self.user.profile.company_code}"
        
        # Add passenger forms dynamically
        for i in range(self.passenger_count):
            self.fields[f'passenger_{i}_title'] = forms.ChoiceField(
                label=_('Title') if i == 0 else '',
                choices=[
                    ('MR', _('Mr.')),
                    ('MRS', _('Mrs.')),
                    ('MS', _('Ms.')),
                    ('MISS', _('Miss')),
                    ('DR', _('Dr.')),
                    ('PROF', _('Prof.')),
                ],
                widget=forms.Select(attrs={
                    'class': 'form-select',
                    'data-passenger-index': i,
                })
            )
            
            self.fields[f'passenger_{i}_first_name'] = forms.CharField(
                label=_('First Name') if i == 0 else '',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': _('First Name'),
                    'data-passenger-index': i,
                })
            )
            
            self.fields[f'passenger_{i}_last_name'] = forms.CharField(
                label=_('Last Name') if i == 0 else '',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': _('Last Name'),
                    'data-passenger-index': i,
                })
            )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate all passenger data
        passengers = []
        for i in range(self.passenger_count):
            title = cleaned_data.get(f'passenger_{i}_title')
            first_name = cleaned_data.get(f'passenger_{i}_first_name')
            last_name = cleaned_data.get(f'passenger_{i}_last_name')
            
            if not all([title, first_name, last_name]):
                raise forms.ValidationError(
                    _('All passenger information is required for passenger {}.').format(i + 1)
                )
            
            passengers.append({
                'title': title,
                'first_name': first_name,
                'last_name': last_name,
            })
        
        cleaned_data['passengers'] = passengers
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set booking reference
        if not instance.booking_reference:
            instance.booking_reference = self.generate_booking_reference()
        
        # Set agent
        if self.user:
            instance.agent = self.user
        
        # Set itinerary
        if self.itinerary:
            instance.itinerary = self.itinerary
        
        # Calculate total amount
        if self.itinerary:
            total_passengers = self.passenger_count
            instance.total_amount = self.itinerary.total_fare * total_passengers
            instance.currency = self.itinerary.currency
        
        if commit:
            instance.save()
            
            # Create passenger records
            passengers_data = self.cleaned_data.get('passengers', [])
            for i, passenger_data in enumerate(passengers_data):
                passenger = Passenger.objects.create(
                    title=passenger_data['title'],
                    first_name=passenger_data['first_name'],
                    last_name=passenger_data['last_name'],
                    # Additional fields would be filled in passenger details step
                )
                instance.passengers.add(passenger)
        
        return instance
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        
        # Format: AGT-XXXXXX (6 alphanumeric characters)
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choices(chars, k=6))
        
        # Add agent prefix if available
        prefix = 'AGT'
        if self.user and hasattr(self.user, 'profile'):
            agent_code = getattr(self.user.profile, 'agent_code', 'AGT')
            prefix = agent_code.upper()[:3]
        
        return f"{prefix}-{random_part}"


class QuickBookingForm(forms.Form):
    """Quick booking form for experienced agents"""
    
    PNR = forms.CharField(
        label=_('PNR / Booking Reference'),
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter PNR or booking reference'),
            'autocomplete': 'off',
            'autocapitalize': 'characters',
        })
    )
    
    airline = forms.CharField(
        label=_('Airline'),
        max_length=2,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., SV, EK, QR'),
            'autocomplete': 'off',
            'autocapitalize': 'characters',
        })
    )
    
    passenger_name = forms.CharField(
        label=_('Passenger Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Surname/First Name'),
        })
    )
    
    booking_date = forms.DateField(
        label=_('Booking Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'placeholder': _('Select booking date'),
            'readonly': 'readonly',
        })
    )
    
    total_amount = forms.DecimalField(
        label=_('Total Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
        })
    )
    
    payment_status = forms.ChoiceField(
        label=_('Payment Status'),
        choices=[
            ('pending', _('Pending')),
            ('partial', _('Partial Payment')),
            ('paid', _('Paid')),
            ('credit', _('On Credit')),
        ],
        initial='pending',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    def clean_PNR(self):
        pnr = self.cleaned_data.get('PNR', '').upper().strip()
        if not pnr:
            raise forms.ValidationError(_('PNR is required.'))
        
        # Validate PNR format (6 alphanumeric characters)
        if len(pnr) != 6 or not pnr.isalnum():
            raise forms.ValidationError(_('Invalid PNR format. Must be 6 alphanumeric characters.'))
        
        # Check if PNR already exists
        from flights.models import Booking
        if Booking.objects.filter(pnr=pnr).exists():
            raise forms.ValidationError(_('PNR already exists in the system.'))
        
        return pnr
    
    def clean_airline(self):
        airline = self.cleaned_data.get('airline', '').upper().strip()
        if not airline:
            raise forms.ValidationError(_('Airline code is required.'))
        
        # Validate airline code (2 letters)
        if len(airline) != 2 or not airline.isalpha():
            raise forms.ValidationError(_('Invalid airline code. Must be 2 letters.'))
        
        return airline


class GroupBookingForm(forms.ModelForm):
    """Group booking form for 10+ passengers"""
    
    class Meta:
        model = Booking
        fields = [
            'special_instructions',
            'internal_notes',
            'group_name',
            'group_leader',
            'group_size',
            'deposit_amount',
            'final_payment_date',
        ]
    
    group_name = forms.CharField(
        label=_('Group Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Hajj Group 2024, Corporate Retreat'),
        })
    )
    
    group_leader = forms.CharField(
        label=_('Group Leader'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Name of group leader'),
        })
    )
    
    group_size = forms.IntegerField(
        label=_('Group Size'),
        min_value=10,
        max_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '10',
            'max': '200',
        })
    )
    
    deposit_amount = forms.DecimalField(
        label=_('Deposit Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
        })
    )
    
    final_payment_date = forms.DateField(
        label=_('Final Payment Date'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'placeholder': _('Select final payment date'),
            'readonly': 'readonly',
        })
    )
    
    passenger_list_file = forms.FileField(
        label=_('Passenger List (Excel/CSV)'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set minimum date for final payment
        today = timezone.now().date()
        self.fields['final_payment_date'].widget.attrs['min'] = today.isoformat()
    
    def clean(self):
        cleaned_data = super().clean()
        group_size = cleaned_data.get('group_size')
        deposit_amount = cleaned_data.get('deposit_amount', 0)
        final_payment_date = cleaned_data.get('final_payment_date')
        
        # Validate group size
        if group_size and group_size < 10:
            raise forms.ValidationError({
                'group_size': _('Group booking requires minimum 10 passengers.')
            })
        
        # Validate final payment date
        if final_payment_date and final_payment_date < timezone.now().date():
            raise forms.ValidationError({
                'final_payment_date': _('Final payment date cannot be in the past.')
            })
        
        return cleaned_data


class CorporateBookingForm(forms.ModelForm):
    """Corporate booking form with cost center allocation"""
    
    class Meta:
        model = Booking
        fields = [
            'corporate_client',
            'cost_center',
            'project_code',
            'approval_code',
            'approver_name',
            'travel_purpose',
        ]
    
    corporate_client = forms.ModelChoiceField(
        label=_('Business Unit'),
        queryset=BusinessUnit.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select corporate-select',
            'data-placeholder': _('Select business unit'),
        })
    )
    
    cost_center = forms.CharField(
        label=_('Cost Center'),
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., DEPT-001, DIVISION-A'),
        })
    )
    
    project_code = forms.CharField(
        label=_('Project Code'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., PROJ-2024-001'),
        })
    )
    
    approval_code = forms.CharField(
        label=_('Approval Code'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Approval reference number'),
        })
    )
    
    approver_name = forms.CharField(
        label=_('Approver Name'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Name of person who approved'),
        })
    )
    
    travel_purpose = forms.ChoiceField(
        label=_('Travel Purpose'),
        choices=[
            ('business', _('Business Meeting')),
            ('conference', _('Conference/Event')),
            ('training', _('Training')),
            ('project', _('Project Work')),
            ('client_visit', _('Client Visit')),
            ('recruitment', _('Recruitment')),
            ('other', _('Other')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    travel_policy_acknowledged = forms.BooleanField(
        label=_('I confirm this booking complies with corporate travel policy'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        corporate_client = cleaned_data.get('corporate_client')
        travel_policy_acknowledged = cleaned_data.get('travel_policy_acknowledged')
        
        if corporate_client and not travel_policy_acknowledged:
            raise forms.ValidationError({
                'travel_policy_acknowledged': _('You must acknowledge compliance with travel policy.')
            })
        
        return cleaned_data


class BookingModificationForm(forms.ModelForm):
    """Form for modifying existing bookings"""
    
    class Meta:
        model = Booking
        fields = [
            'special_instructions',
            'internal_notes',
            'customer_remarks',
        ]
    
    modification_type = forms.ChoiceField(
        label=_('Modification Type'),
        choices=[
            ('date_change', _('Date Change')),
            ('passenger_change', _('Passenger Change')),
            ('route_change', _('Route Change')),
            ('cabin_change', _('Cabin Class Change')),
            ('add_ancillary', _('Add Ancillary Services')),
            ('other', _('Other')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'modificationType',
        })
    )
    
    reason_for_change = forms.CharField(
        label=_('Reason for Change'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Please specify reason for modification...'),
            'maxlength': '500',
        })
    )
    
    fee_acknowledged = forms.BooleanField(
        label=_('I acknowledge that change fees may apply'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    send_notification = forms.BooleanField(
        label=_('Send notification to passenger'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        super().__init__(*args, **kwargs)
        
        if self.booking:
            self.fields['special_instructions'].initial = self.booking.special_instructions
            self.fields['internal_notes'].initial = self.booking.internal_notes
            self.fields['customer_remarks'].initial = self.booking.customer_remarks
    
    def clean(self):
        cleaned_data = super().clean()
        modification_type = cleaned_data.get('modification_type')
        fee_acknowledged = cleaned_data.get('fee_acknowledged')
        
        if not fee_acknowledged:
            raise forms.ValidationError({
                'fee_acknowledged': _('You must acknowledge that change fees may apply.')
            })
        
        # Check if booking can be modified
        if self.booking and not self.booking.can_be_modified():
            raise forms.ValidationError(
                _('This booking cannot be modified. Please check the fare rules or contact support.')
            )
        
        return cleaned_data


class CancellationRequestForm(forms.Form):
    """Form for requesting booking cancellation"""
    
    CANCELLATION_REASON_CHOICES = [
        ('change_of_plans', _('Change of Plans')),
        ('found_cheaper', _('Found Cheaper Fare')),
        ('travel_restrictions', _('Travel Restrictions')),
        ('health_issues', _('Health Issues')),
        ('family_emergency', _('Family Emergency')),
        ('business_cancelled', _('Business Trip Cancelled')),
        ('flight_schedule', _('Flight Schedule Changed')),
        ('other', _('Other')),
    ]
    
    REFUND_PREFERENCE_CHOICES = [
        ('original', _('Refund to Original Payment Method')),
        ('credit', _('Travel Credit/Voucher')),
        ('wallet', _('Wallet Credit')),
        ('bank_transfer', _('Bank Transfer')),
    ]
    
    reason = forms.ChoiceField(
        label=_('Cancellation Reason'),
        choices=CANCELLATION_REASON_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'cancellationReason',
        })
    )
    
    reason_details = forms.CharField(
        label=_('Reason Details'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Please provide more details...'),
            'maxlength': '500',
        })
    )
    
    refund_preference = forms.ChoiceField(
        label=_('Refund Preference'),
        choices=REFUND_PREFERENCE_CHOICES,
        initial='original',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'refundPreference',
        })
    )
    
    bank_details = forms.CharField(
        label=_('Bank Details'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Bank name, account number, IBAN...'),
            'maxlength': '500',
        })
    )
    
    acknowledge_penalty = forms.BooleanField(
        label=_('I acknowledge that cancellation penalties may apply'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    send_confirmation = forms.BooleanField(
        label=_('Send cancellation confirmation'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        super().__init__(*args, **kwargs)
        
        if self.booking:
            # Set initial refund preference based on booking
            payment_method = self.booking.payment_method
            if payment_method == 'credit_card':
                self.fields['refund_preference'].initial = 'original'
            elif payment_method == 'wallet':
                self.fields['refund_preference'].initial = 'wallet'
    
    def clean(self):
        cleaned_data = super().clean()
        refund_preference = cleaned_data.get('refund_preference')
        bank_details = cleaned_data.get('bank_details')
        acknowledge_penalty = cleaned_data.get('acknowledge_penalty')
        
        if not acknowledge_penalty:
            raise forms.ValidationError({
                'acknowledge_penalty': _('You must acknowledge that cancellation penalties may apply.')
            })
        
        # Require bank details for bank transfer refund
        if refund_preference == 'bank_transfer' and not bank_details:
            raise forms.ValidationError({
                'bank_details': _('Bank details are required for bank transfer refund.')
            })
        
        # Check if booking can be cancelled
        if self.booking and not self.booking.can_be_cancelled():
            raise forms.ValidationError(
                _('This booking cannot be cancelled. Please check the cancellation policy or contact support.')
            )
        
        return cleaned_data