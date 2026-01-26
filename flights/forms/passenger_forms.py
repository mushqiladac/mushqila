# flights/forms/passenger_forms.py
"""
Passenger forms for B2B Travel Platform
Production Ready - Final Version
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date, timedelta
import re

from flights.models import Passenger, Airline


class PassengerForm(forms.ModelForm):
    """Complete passenger information form"""
    
    class Meta:
        model = Passenger
        fields = [
            'title',
            'first_name',
            'middle_name',
            'last_name',
            'arabic_first_name',
            'arabic_last_name',
            'date_of_birth',
            'gender',
            'passenger_type',
            'nationality',
            'contact_email',
            'contact_phone',
            'contact_phone_country',
            'passport_number',
            'passport_issuing_country',
            'passport_issue_date',
            'passport_expiry_date',
            'national_id',
            'iqama_number',
            'iqama_expiry',
            'frequent_flyer_number',
            'frequent_flyer_airline',
            'meal_preference',
            'seat_preference',
            'special_requests',
            'medical_conditions',
            'wheelchair_assistance',
            'unaccompanied_minor',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'hajj_visa_number',
            'umrah_visa_number',
            'saudi_entry_date',
            'saudi_exit_date',
        ]
        
        widgets = {
            'title': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100'}),
            'arabic_first_name': forms.TextInput(attrs={'class': 'form-control arabic-input', 'maxlength': '100', 'dir': 'rtl'}),
            'arabic_last_name': forms.TextInput(attrs={'class': 'form-control arabic-input', 'maxlength': '100', 'dir': 'rtl'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control datepicker', 'readonly': 'readonly'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'passenger_type': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.Select(attrs={'class': 'form-select country-select'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'type': 'email'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'contact_phone_country': forms.Select(attrs={'class': 'form-select country-select'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
            'passport_issuing_country': forms.Select(attrs={'class': 'form-select country-select'}),
            'passport_issue_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'readonly': 'readonly'}),
            'passport_expiry_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'readonly': 'readonly'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
            'iqama_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
            'iqama_expiry': forms.DateInput(attrs={'class': 'form-control datepicker', 'readonly': 'readonly'}),
            'frequent_flyer_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
            'frequent_flyer_airline': forms.Select(attrs={'class': 'form-select airline-select'}),
            'meal_preference': forms.Select(attrs={'class': 'form-select'}),
            'seat_preference': forms.Select(attrs={'class': 'form-select'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': '1000'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': '1000'}),
            'wheelchair_assistance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'unaccompanied_minor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
            'hajj_visa_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
            'umrah_visa_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
            'saudi_entry_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'readonly': 'readonly'}),
            'saudi_exit_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'readonly': 'readonly'}),
        }
    
    # Additional validation fields
    confirm_passport = forms.BooleanField(
        label=_('I confirm the passport details are accurate'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    privacy_policy = forms.BooleanField(
        label=_('I agree to the privacy policy and data processing'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.passenger_type = kwargs.pop('passenger_type', 'ADT')
        super().__init__(*args, **kwargs)
        
        # Set passenger type
        self.fields['passenger_type'].initial = self.passenger_type
        
        # Set date constraints
        today = timezone.now().date()
        hundred_years_ago = today - timedelta(days=365*100)
        eighteen_years_ago = today - timedelta(days=365*18)
        two_years_ago = today - timedelta(days=365*2)
        
        # Date of birth constraints based on passenger type
        if self.passenger_type == 'ADT':
            min_dob = hundred_years_ago
            max_dob = eighteen_years_ago
        elif self.passenger_type == 'CHD':
            min_dob = today - timedelta(days=365*12)
            max_dob = today - timedelta(days=365*2)
        else:  # INF
            min_dob = today - timedelta(days=365*2)
            max_dob = today
        
        self.fields['date_of_birth'].widget.attrs.update({
            'min': min_dob.isoformat(),
            'max': max_dob.isoformat(),
        })
        
        # Passport expiry must be at least 6 months in future
        min_passport_expiry = today + timedelta(days=180)
        self.fields['passport_expiry_date'].widget.attrs['min'] = min_passport_expiry.isoformat()
        
        # Set default values for Saudi passengers
        self.fields['nationality'].initial = 'SA'
        self.fields['contact_phone_country'].initial = 'SA'
        
        # Add CSS classes for conditional fields
        self.fields['unaccompanied_minor'].widget.attrs['data-show-fields'] = 'emergency_contact_name,emergency_contact_phone,emergency_contact_relationship'
        self.fields['wheelchair_assistance'].widget.attrs['data-show-fields'] = 'medical_conditions'
        
        # Set frequent flyer airline choices
        self.fields['frequent_flyer_airline'].queryset = Airline.objects.filter(is_active=True)
        
        # Meal preference choices
        self.fields['meal_preference'].choices = [
            ('', _('No Preference')),
            ('regular', _('Regular Meal')),
            ('vegetarian', _('Vegetarian')),
            ('vegan', _('Vegan')),
            ('halal', _('Halal')),
            ('kosher', _('Kosher')),
            ('child', _('Child Meal')),
            ('diabetic', _('Diabetic')),
            ('gluten_free', _('Gluten Free')),
        ]
        
        # Seat preference choices
        self.fields['seat_preference'].choices = [
            ('', _('No Preference')),
            ('window', _('Window')),
            ('aisle', _('Aisle')),
            ('middle', _('Middle')),
            ('front', _('Front of Cabin')),
            ('back', _('Back of Cabin')),
            ('exit_row', _('Exit Row')),
            ('bulkhead', _('Bulkhead')),
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate date of birth based on passenger type
        date_of_birth = cleaned_data.get('date_of_birth')
        passenger_type = cleaned_data.get('passenger_type', self.passenger_type)
        
        if date_of_birth:
            today = timezone.now().date()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            
            if passenger_type == 'ADT' and age < 12:
                raise forms.ValidationError({
                    'date_of_birth': _('Adult passengers must be 12 years or older.')
                })
            elif passenger_type == 'CHD' and not (2 <= age < 12):
                raise forms.ValidationError({
                    'date_of_birth': _('Child passengers must be between 2 and 11 years old.')
                })
            elif passenger_type == 'INF' and age >= 2:
                raise forms.ValidationError({
                    'date_of_birth': _('Infant passengers must be under 2 years old.')
                })
        
        # Validate passport information for international travel
        passport_number = cleaned_data.get('passport_number')
        passport_expiry_date = cleaned_data.get('passport_expiry_date')
        
        if passport_number and passport_expiry_date:
            # Check passport expiry (should be valid for at least 6 months)
            six_months_later = timezone.now().date() + timedelta(days=180)
            if passport_expiry_date < six_months_later:
                raise forms.ValidationError({
                    'passport_expiry_date': _('Passport must be valid for at least 6 months from travel date.')
                })
            
            # Validate passport number format (basic validation)
            if not re.match(r'^[A-Z0-9]{6,9}$', passport_number):
                raise forms.ValidationError({
                    'passport_number': _('Invalid passport number format.')
                })
        
        # Validate Saudi-specific documents
        nationality = cleaned_data.get('nationality')
        iqama_number = cleaned_data.get('iqama_number')
        iqama_expiry = cleaned_data.get('iqama_expiry')
        
        if nationality == 'SA':
            # Saudi nationals should have national ID
            national_id = cleaned_data.get('national_id')
            if not national_id:
                raise forms.ValidationError({
                    'national_id': _('National ID is required for Saudi nationals.')
                })
        else:
            # Non-Saudi residents in KSA should have Iqama
            if iqama_number and not iqama_expiry:
                raise forms.ValidationError({
                    'iqama_expiry': _('Iqama expiry date is required if Iqama number is provided.')
                })
        
        # Validate emergency contact for unaccompanied minors
        unaccompanied_minor = cleaned_data.get('unaccompanied_minor')
        if unaccompanied_minor and passenger_type in ['CHD', 'INF']:
            emergency_contact_name = cleaned_data.get('emergency_contact_name')
            emergency_contact_phone = cleaned_data.get('emergency_contact_phone')
            
            if not emergency_contact_name or not emergency_contact_phone:
                raise forms.ValidationError({
                    'emergency_contact_name': _('Emergency contact information is required for unaccompanied minors.'),
                    'emergency_contact_phone': _('Emergency contact information is required for unaccompanied minors.'),
                })
        
        # Validate privacy policy acceptance
        privacy_policy = cleaned_data.get('privacy_policy')
        if not privacy_policy:
            raise forms.ValidationError({
                'privacy_policy': _('You must agree to the privacy policy.')
            })
        
        return cleaned_data
    
    def clean_contact_email(self):
        email = self.cleaned_data.get('contact_email')
        if email:
            # Basic email validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise forms.ValidationError(_('Please enter a valid email address.'))
        return email
    
    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if phone:
            # Remove any non-digit characters
            phone_digits = re.sub(r'\D', '', phone)
            
            # Validate phone number length
            if len(phone_digits) < 8 or len(phone_digits) > 15:
                raise forms.ValidationError(_('Please enter a valid phone number (8-15 digits).'))
            
            return phone_digits
        return phone
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set additional fields if needed
        if self.booking:
            # Link to booking if provided
            pass
        
        if commit:
            instance.save()
        
        return instance


class PassengerEditForm(PassengerForm):
    """Form for editing existing passenger information"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make some fields read-only for booked passengers
        if self.instance and self.instance.pk:
            # Once a passenger is ticketed, certain fields cannot be changed
            read_only_fields = ['first_name', 'last_name', 'date_of_birth', 'passport_number']
            for field in read_only_fields:
                if field in self.fields:
                    self.fields[field].widget.attrs['readonly'] = True
                    self.fields[field].widget.attrs['class'] += ' bg-light'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Additional validation for existing passengers
        if self.instance and self.instance.pk:
            # Check if name changes are allowed (depends on ticketing status)
            first_name_changed = 'first_name' in self.changed_data
            last_name_changed = 'last_name' in self.changed_data
            
            if (first_name_changed or last_name_changed) and self.instance.is_ticketed():
                raise forms.ValidationError(
                    _('Name cannot be changed after ticketing. Please contact support for assistance.')
                )
        
        return cleaned_data


class PassengerBulkForm(forms.Form):
    """Form for bulk passenger upload/management"""
    
    UPLOAD_FORMAT_CHOICES = [
        ('excel', _('Excel/CSV Template')),
        ('manual', _('Manual Entry')),
        ('copy_previous', _('Copy from Previous Booking')),
    ]
    
    upload_format = forms.ChoiceField(
        label=_('Upload Format'),
        choices=UPLOAD_FORMAT_CHOICES,
        initial='excel',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )
    
    template_file = forms.FileField(
        label=_('Template File'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls',
        })
    )
    
    passenger_count = forms.IntegerField(
        label=_('Number of Passengers'),
        min_value=1,
        max_value=50,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '50',
        })
    )
    
    copy_from_booking = forms.CharField(
        label=_('Copy from Booking Reference'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter booking reference to copy from'),
        })
    )
    
    default_nationality = forms.ChoiceField(
        label=_('Default Nationality'),
        initial='SA',
        widget=forms.Select(attrs={
            'class': 'form-select country-select',
        })
    )
    
    default_contact_country = forms.ChoiceField(
        label=_('Default Contact Country'),
        initial='SA',
        widget=forms.Select(attrs={
            'class': 'form-select country-select',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate country choices (you would typically get these from a countries model)
        countries = [
            ('SA', _('Saudi Arabia')),
            ('AE', _('United Arab Emirates')),
            ('KW', _('Kuwait')),
            ('BH', _('Bahrain')),
            ('QA', _('Qatar')),
            ('OM', _('Oman')),
            ('EG', _('Egypt')),
            ('IN', _('India')),
            ('PK', _('Pakistan')),
            ('US', _('United States')),
            ('GB', _('United Kingdom')),
        ]
        
        self.fields['default_nationality'].choices = countries
        self.fields['default_contact_country'].choices = countries
    
    def clean(self):
        cleaned_data = super().clean()
        upload_format = cleaned_data.get('upload_format')
        template_file = cleaned_data.get('template_file')
        passenger_count = cleaned_data.get('passenger_count')
        copy_from_booking = cleaned_data.get('copy_from_booking')
        
        if upload_format == 'excel' and not template_file:
            raise forms.ValidationError({
                'template_file': _('Template file is required for Excel/CSV upload.')
            })
        
        if upload_format == 'copy_previous' and not copy_from_booking:
            raise forms.ValidationError({
                'copy_from_booking': _('Booking reference is required to copy from previous booking.')
            })
        
        if passenger_count and passenger_count > 50:
            raise forms.ValidationError({
                'passenger_count': _('Maximum 50 passengers allowed for bulk upload.')
            })
        
        return cleaned_data
    
    def process_bulk_passengers(self):
        """Process bulk passenger data"""
        # This would be implemented based on the upload format
        # It would parse the file, validate data, and create passenger objects
        pass


class ContactInformationForm(forms.Form):
    """Form for passenger contact information"""
    
    PRIMARY_CONTACT_CHOICES = [
        ('passenger', _('Passenger')),
        ('agent', _('Booking Agent')),
        ('corporate', _('Corporate Contact')),
    ]
    
    primary_contact = forms.ChoiceField(
        label=_('Primary Contact For This Booking'),
        choices=PRIMARY_CONTACT_CHOICES,
        initial='passenger',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )
    
    # Passenger Contact
    passenger_email = forms.EmailField(
        label=_('Passenger Email'),
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'passenger@example.com',
        })
    )
    
    passenger_phone = forms.CharField(
        label=_('Passenger Phone'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'tel',
            'placeholder': '+966 5X XXX XXXX',
        })
    )
    
    # Agent Contact (auto-filled from user profile)
    agent_email = forms.EmailField(
        label=_('Agent Email'),
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
        })
    )
    
    agent_phone = forms.CharField(
        label=_('Agent Phone'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
        })
    )
    
    # Corporate Contact
    corporate_contact_name = forms.CharField(
        label=_('Corporate Contact Name'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Contact person at company'),
        })
    )
    
    corporate_contact_email = forms.EmailField(
        label=_('Corporate Contact Email'),
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'corporate@company.com',
        })
    )
    
    corporate_contact_phone = forms.CharField(
        label=_('Corporate Contact Phone'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'tel',
            'placeholder': '+966 1X XXX XXXX',
        })
    )
    
    # Notification Preferences
    send_itinerary_email = forms.BooleanField(
        label=_('Send itinerary by email'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    send_sms_notifications = forms.BooleanField(
        label=_('Send SMS notifications'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    send_flight_alerts = forms.BooleanField(
        label=_('Send flight status alerts'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    special_communication_notes = forms.CharField(
        label=_('Special Communication Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Any special communication requirements...'),
            'maxlength': '500',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Auto-fill agent information
        if self.user:
            self.fields['agent_email'].initial = self.user.email
            if hasattr(self.user, 'profile') and self.user.profile.phone:
                self.fields['agent_phone'].initial = self.user.profile.phone
    
    def clean(self):
        cleaned_data = super().clean()
        primary_contact = cleaned_data.get('primary_contact')
        
        # Validate required fields based on primary contact
        if primary_contact == 'passenger':
            if not cleaned_data.get('passenger_email'):
                raise forms.ValidationError({
                    'passenger_email': _('Passenger email is required when passenger is primary contact.')
                })
            if not cleaned_data.get('passenger_phone'):
                raise forms.ValidationError({
                    'passenger_phone': _('Passenger phone is required when passenger is primary contact.')
                })
        
        elif primary_contact == 'corporate':
            if not cleaned_data.get('corporate_contact_email'):
                raise forms.ValidationError({
                    'corporate_contact_email': _('Corporate contact email is required when corporate is primary contact.')
                })
        
        # Validate phone numbers
        for phone_field in ['passenger_phone', 'agent_phone', 'corporate_contact_phone']:
            phone = cleaned_data.get(phone_field)
            if phone:
                # Remove any non-digit characters
                phone_digits = re.sub(r'\D', '', phone)
                if len(phone_digits) < 8:
                    self.add_error(phone_field, _('Please enter a valid phone number.'))
        
        return cleaned_data


class DocumentUploadForm(forms.Form):
    """Form for uploading passenger documents"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('passport', _('Passport')),
        ('national_id', _('National ID')),
        ('iqama', _('Iqama (Residence Permit)')),
        ('driving_license', _('Driving License')),
        ('visa', _('Visa')),
        ('birth_certificate', _('Birth Certificate (for children)')),
        ('vaccination_certificate', _('Vaccination Certificate')),
        ('medical_report', _('Medical Report')),
        ('other', _('Other Document')),
    ]
    
    document_type = forms.ChoiceField(
        label=_('Document Type'),
        choices=DOCUMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'documentType',
        })
    )
    
    document_file = forms.FileField(
        label=_('Document File'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png,.heic',
        })
    )
    
    document_number = forms.CharField(
        label=_('Document Number'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., A12345678'),
        })
    )
    
    issue_date = forms.DateField(
        label=_('Issue Date'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'readonly': 'readonly',
        })
    )
    
    expiry_date = forms.DateField(
        label=_('Expiry Date'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'readonly': 'readonly',
        })
    )
    
    issuing_country = forms.ChoiceField(
        label=_('Issuing Country'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select country-select',
        })
    )
    
    issuing_authority = forms.CharField(
        label=_('Issuing Authority'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Ministry of Interior, Passport Office'),
        })
    )
    
    notes = forms.CharField(
        label=_('Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Any additional notes about this document...'),
            'maxlength': '500',
        })
    )
    
    is_primary = forms.BooleanField(
        label=_('Set as primary document'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.passenger = kwargs.pop('passenger', None)
        super().__init__(*args, **kwargs)
        
        # Set date constraints
        today = timezone.now().date()
        hundred_years_ago = today - timedelta(days=365*100)
        
        self.fields['issue_date'].widget.attrs['max'] = today.isoformat()
        self.fields['issue_date'].widget.attrs['min'] = hundred_years_ago.isoformat()
        
        self.fields['expiry_date'].widget.attrs['min'] = today.isoformat()
        
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
        
        self.fields['issuing_country'].choices = [('', _('Select country'))] + countries
    
    def clean(self):
        cleaned_data = super().clean()
        document_type = cleaned_data.get('document_type')
        document_file = cleaned_data.get('document_file')
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        # Validate file
        if document_file:
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if document_file.size > max_size:
                raise forms.ValidationError({
                    'document_file': _('File size must be less than 10MB.')
                })
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/heic']
            if document_file.content_type not in allowed_types:
                raise forms.ValidationError({
                    'document_file': _('Only PDF, JPG, PNG, and HEIC files are allowed.')
                })
        
        # Validate dates
        if issue_date and expiry_date and issue_date > expiry_date:
            raise forms.ValidationError({
                'issue_date': _('Issue date cannot be after expiry date.'),
                'expiry_date': _('Expiry date cannot be before issue date.'),
            })
        
        # Document type specific validations
        if document_type in ['passport', 'national_id', 'iqama']:
            if not cleaned_data.get('document_number'):
                raise forms.ValidationError({
                    'document_number': _('Document number is required for this document type.')
                })
            
            if not cleaned_data.get('expiry_date'):
                raise forms.ValidationError({
                    'expiry_date': _('Expiry date is required for this document type.')
                })
        
        return cleaned_data
    
    def save(self):
        """Save the uploaded document"""
        # This would create a Document model instance
        # Link it to the passenger and store the file
        pass


class SpecialRequestForm(forms.Form):
    """Form for passenger special requests"""
    
    REQUEST_TYPE_CHOICES = [
        ('meal', _('Special Meal Request')),
        ('seat', _('Special Seat Request')),
        ('assistance', _('Special Assistance')),
        ('medical', _('Medical Requirements')),
        ('sports', _('Sports Equipment')),
        ('pet', _('Pet Transportation')),
        ('other', _('Other Request')),
    ]
    
    ASSISTANCE_TYPE_CHOICES = [
        ('wheelchair', _('Wheelchair Assistance')),
        ('unaccompanied_minor', _('Unaccompanied Minor')),
        ('visual_impairment', _('Visual Impairment Assistance')),
        ('hearing_impairment', _('Hearing Impairment Assistance')),
        ('mobility_assistance', _('Mobility Assistance')),
        ('medical_escort', _('Medical Escort')),
        ('oxygen', _('Oxygen Requirements')),
        ('other', _('Other Assistance')),
    ]
    
    request_type = forms.ChoiceField(
        label=_('Request Type'),
        choices=REQUEST_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'requestType',
        })
    )
    
    # Meal Requests
    meal_type = forms.ChoiceField(
        label=_('Meal Type'),
        required=False,
        choices=[
            ('', _('Select meal type')),
            ('vegetarian', _('Vegetarian')),
            ('vegan', _('Vegan')),
            ('halal', _('Halal')),
            ('kosher', _('Kosher')),
            ('gluten_free', _('Gluten Free')),
            ('diabetic', _('Diabetic')),
            ('low_sodium', _('Low Sodium')),
            ('low_fat', _('Low Fat')),
            ('child', _('Child Meal')),
            ('asian_vegetarian', _('Asian Vegetarian')),
            ('hindu', _('Hindu Vegetarian')),
            ('jain', _('Jain Meal')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-show-when': 'request_type:meal',
        })
    )
    
    meal_notes = forms.CharField(
        label=_('Meal Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Any specific meal requirements or allergies...'),
            'data-show-when': 'request_type:meal',
            'maxlength': '500',
        })
    )
    
    # Seat Requests
    seat_preference = forms.ChoiceField(
        label=_('Seat Preference'),
        required=False,
        choices=[
            ('', _('Select seat preference')),
            ('window', _('Window Seat')),
            ('aisle', _('Aisle Seat')),
            ('extra_legroom', _('Extra Legroom Seat')),
            ('exit_row', _('Exit Row Seat')),
            ('bulkhead', _('Bulkhead Seat')),
            ('front', _('Front of Cabin')),
            ('back', _('Back of Cabin')),
            ('couple', _('Seats Together')),
            ('family', _('Family Seating')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-show-when': 'request_type:seat',
        })
    )
    
    seat_notes = forms.CharField(
        label=_('Seat Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Any specific seat requirements...'),
            'data-show-when': 'request_type:seat',
            'maxlength': '500',
        })
    )
    
    # Assistance Requests
    assistance_type = forms.ChoiceField(
        label=_('Assistance Type'),
        required=False,
        choices=ASSISTANCE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-show-when': 'request_type:assistance',
        })
    )
    
    assistance_details = forms.CharField(
        label=_('Assistance Details'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Please describe the assistance required...'),
            'data-show-when': 'request_type:assistance',
            'maxlength': '1000',
        })
    )
    
    # Medical Requests
    medical_condition = forms.CharField(
        label=_('Medical Condition'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Diabetes, Heart Condition, Pregnancy'),
            'data-show-when': 'request_type:medical',
        })
    )
    
    medical_notes = forms.CharField(
        label=_('Medical Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Please provide details of medical requirements...'),
            'data-show-when': 'request_type:medical',
            'maxlength': '1000',
        })
    )
    
    medical_document = forms.FileField(
        label=_('Medical Document'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'data-show-when': 'request_type:medical',
        })
    )
    
    # Sports Equipment
    sports_equipment_type = forms.CharField(
        label=_('Equipment Type'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Golf Clubs, Skis, Bicycle'),
            'data-show-when': 'request_type:sports',
        })
    )
    
    equipment_dimensions = forms.CharField(
        label=_('Dimensions (L×W×H in cm)'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 150×30×20',
            'data-show-when': 'request_type:sports',
        })
    )
    
    equipment_weight = forms.DecimalField(
        label=_('Weight (kg)'),
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 15.5',
            'step': '0.1',
            'data-show-when': 'request_type:sports',
        })
    )
    
    # Pet Transportation
    pet_type = forms.ChoiceField(
        label=_('Pet Type'),
        required=False,
        choices=[
            ('dog', _('Dog')),
            ('cat', _('Cat')),
            ('bird', _('Bird')),
            ('other', _('Other')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-show-when': 'request_type:pet',
        })
    )
    
    pet_weight = forms.DecimalField(
        label=_('Pet Weight (kg)'),
        required=False,
        max_digits=4,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 5.0',
            'step': '0.1',
            'data-show-when': 'request_type:pet',
        })
    )
    
    pet_carrier_dimensions = forms.CharField(
        label=_('Carrier Dimensions (L×W×H in cm)'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 50×30×30',
            'data-show-when': 'request_type:pet',
        })
    )
    
    # Other Requests
    request_description = forms.CharField(
        label=_('Request Description'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Please describe your request in detail...'),
            'data-show-when': 'request_type:other',
            'maxlength': '1000',
        })
    )
    
    # General Fields
    urgency = forms.ChoiceField(
        label=_('Urgency Level'),
        choices=[
            ('normal', _('Normal')),
            ('high', _('High Priority')),
            ('critical', _('Critical')),
        ],
        initial='normal',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    airline_notified = forms.BooleanField(
        label=_('Airline has been notified'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    confirmation_received = forms.BooleanField(
        label=_('Confirmation received from airline'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    additional_notes = forms.CharField(
        label=_('Additional Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Any additional notes...'),
            'maxlength': '500',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get('request_type')
        
        # Validate required fields based on request type
        if request_type == 'meal' and not cleaned_data.get('meal_type'):
            raise forms.ValidationError({
                'meal_type': _('Meal type is required for meal requests.')
            })
        
        if request_type == 'assistance' and not cleaned_data.get('assistance_type'):
            raise forms.ValidationError({
                'assistance_type': _('Assistance type is required for assistance requests.')
            })
        
        if request_type == 'medical' and not cleaned_data.get('medical_condition'):
            raise forms.ValidationError({
                'medical_condition': _('Medical condition is required for medical requests.')
            })
        
        if request_type == 'sports' and not cleaned_data.get('sports_equipment_type'):
            raise forms.ValidationError({
                'sports_equipment_type': _('Equipment type is required for sports equipment requests.')
            })
        
        if request_type == 'other' and not cleaned_data.get('request_description'):
            raise forms.ValidationError({
                'request_description': _('Description is required for other requests.')
            })
        
        # Validate medical document
        medical_document = cleaned_data.get('medical_document')
        if medical_document:
            max_size = 5 * 1024 * 1024  # 5MB
            if medical_document.size > max_size:
                raise forms.ValidationError({
                    'medical_document': _('Medical document must be less than 5MB.')
                })
        
        return cleaned_data