# accounts/forms/user_forms.py
"""
User management forms for B2B Travel Mushqila - Saudi Arabia
FIXED: UserRegistrationForm with all fields and production ready
UPDATED: Fixed save() method to properly save user_type to database
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.db import transaction
import re

from ..models import User, UserProfile, SaudiCity, SaudiRegion


class UserRegistrationForm(UserCreationForm):
    """User registration form with Saudi specific validation - PRODUCTION READY"""
    
    # Personal Information
    first_name = forms.CharField(
        label=_('First Name'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('First Name'),
            'id': 'id_first_name'
        })
    )
    
    last_name = forms.CharField(
        label=_('Last Name'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Last Name'),
            'id': 'id_last_name'
        })
    )
    
    email = forms.EmailField(
        label=_('Email Address'),
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@domain.com',
            'autocomplete': 'email',
            'id': 'id_email'
        })
    )
    
    phone = forms.CharField(
        label=_('Phone Number'),
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX',
            'id': 'id_phone'
        }),
        validators=[
            RegexValidator(
                regex=r'^\+9665\d{8}$',
                message=_('Phone number must be in format: +9665XXXXXXXX')
            )
        ]
    )
    
    # User Type
    user_type = forms.ChoiceField(
        label=_('User Type'),
        choices=[
            ('agent', _('Travel Agent')),
            ('supplier', _('Service Supplier')),
            ('corporate', _('Corporate Client')),
        ],
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Company Information
    company_name_en = forms.CharField(
        label=_('Company Name (English)'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Company Name in English'),
            'id': 'id_company_name_en'
        })
    )
    
    company_name_ar = forms.CharField(
        label=_('Company Name (Arabic)'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اسم الشركة بالعربية'),
            'dir': 'rtl',
            'id': 'id_company_name_ar'
        })
    )
    
    company_registration = forms.CharField(
        label=_('Commercial Registration (CR) Number'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('CR Number'),
            'id': 'id_company_registration'
        })
    )
    
    vat_number = forms.CharField(
        label=_('VAT Number'),
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '3XXXXXXXXXXXXXX',
            'id': 'id_vat_number'
        })
    )
    
    # Address Information
    address_en = forms.CharField(
        label=_('Address (English)'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Full address in English'),
            'id': 'id_address_en'
        })
    )
    
    address_ar = forms.CharField(
        label=_('Address (Arabic)'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('العنوان الكامل بالعربية'),
            'dir': 'rtl',
            'id': 'id_address_ar'
        })
    )
    
    # Security
    password1 = forms.CharField(
        label=_('Password'),
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Create a strong password'),
            'autocomplete': 'new-password',
            'id': 'id_password1'
        }),
        help_text=_('Password must contain at least 8 characters, including uppercase, lowercase, numbers and special characters.')
    )
    
    password2 = forms.CharField(
        label=_('Confirm Password'),
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm your password'),
            'autocomplete': 'new-password',
            'id': 'id_password2'
        })
    )
    
    # Referral
    referral_code = forms.CharField(
        label=_('Referral Code (Optional)'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter referral code if any'),
            'id': 'id_referral_code'
        })
    )
    
    # Terms
    terms_agreed = forms.BooleanField(
        label=_('I agree to the Terms and Conditions'),
        required=True,
        error_messages={
            'required': _('You must agree to the terms and conditions.')
        },
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_terms_agreed'
        })
    )
    
    marketing_consent = forms.BooleanField(
        label=_('I agree to receive marketing communications'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_marketing_consent'
        })
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'user_type', 'company_name_en', 'company_name_ar',
            'company_registration', 'vat_number',
            'address_en', 'address_ar',
            'password1', 'password2', 'referral_code',
            'terms_agreed', 'marketing_consent'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove username field from UserCreationForm
        if 'username' in self.fields:
            del self.fields['username']
        
        # Set custom labels and help texts
        self.fields['password1'].help_text = password_validation.password_validators_help_text_html()
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if not email:
            raise ValidationError(_('Email address is required.'))
        
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('This email is already registered. Please use a different email.'))
        
        return email
    
    def clean_phone(self):
        """Validate Saudi phone number uniqueness and format"""
        phone = self.cleaned_data.get('phone', '').strip()
        
        if not phone:
            raise ValidationError(_('Phone number is required.'))
        
        # Normalize phone number
        phone = self.normalize_phone(phone)
        
        # Validate format
        if not re.match(r'^\+9665\d{8}$', phone):
            raise ValidationError(_('Phone number must be in Saudi format: +9665XXXXXXXX'))
        
        # Check uniqueness
        if User.objects.filter(phone=phone).exists():
            raise ValidationError(_('This phone number is already registered.'))
        
        return phone
    
    def normalize_phone(self, phone):
        """Normalize Saudi phone number format"""
        phone = phone.strip().replace(' ', '')
        
        if phone.startswith('0'):
            phone = '+966' + phone[1:]
        elif phone.startswith('966'):
            phone = '+' + phone
        elif phone.startswith('5') and len(phone) == 9:
            phone = '+966' + phone
        elif not phone.startswith('+'):
            phone = '+966' + phone[-9:]  # Take last 9 digits
        
        return phone
    
    def clean_company_registration(self):
        """Validate CR number uniqueness"""
        cr_number = self.cleaned_data.get('company_registration', '').strip()
        
        if cr_number:
            if User.objects.filter(company_registration=cr_number).exists():
                raise ValidationError(_('This CR number is already registered.'))
        
        return cr_number
    
    def clean_vat_number(self):
        """Validate VAT number format"""
        vat_number = self.cleaned_data.get('vat_number', '').strip()
        
        if vat_number:
            # Saudi VAT numbers are 15 digits starting with 3
            if not re.match(r'^3\d{14}$', vat_number):
                raise ValidationError(_('VAT number must be 15 digits starting with 3.'))
        
        return vat_number
    
    def clean_referral_code(self):
        """Validate referral code"""
        referral_code = self.cleaned_data.get('referral_code', '').strip().upper()
        
        if referral_code:
            # Format validation
            if not re.match(r'^SA[A-Z0-9]{8}$', referral_code):
                raise ValidationError(_('Referral code must be in format: SA followed by 8 characters/numbers'))
            
            # Existence validation
            if not User.objects.filter(referral_code=referral_code).exists():
                raise ValidationError(_('Invalid referral code.'))
        
        return referral_code
    
    def clean_password1(self):
        """Validate password strength"""
        password = self.cleaned_data.get('password1', '')
        
        if not password:
            raise ValidationError(_('Password is required.'))
        
        # Django's built-in validation
        try:
            password_validation.validate_password(password)
        except ValidationError as e:
            raise ValidationError(e.messages)
        
        # Custom validation
        if len(password) < 8:
            raise ValidationError(_('Password must be at least 8 characters long.'))
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Password must contain at least one uppercase letter.'))
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Password must contain at least one lowercase letter.'))
        if not re.search(r'[0-9]', password):
            raise ValidationError(_('Password must contain at least one number.'))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_('Password must contain at least one special character.'))
        
        return password
    
    def clean_terms_agreed(self):
        """Validate terms agreement"""
        terms_agreed = self.cleaned_data.get('terms_agreed')
        
        if not terms_agreed:
            raise ValidationError(_('You must agree to the terms and conditions.'))
        
        return terms_agreed
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # Password match validation
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', _('Passwords do not match.'))
        
        # Company name validation for agents and suppliers
        user_type = cleaned_data.get('user_type')
        company_name_en = cleaned_data.get('company_name_en', '')
        company_name_ar = cleaned_data.get('company_name_ar', '')
        
        if user_type in ['agent', 'supplier']:
            if not company_name_en and not company_name_ar:
                self.add_error('company_name_en', 
                             _('Company name is required for agents and suppliers.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save user with proper settings - FIXED VERSION"""
        try:
            with transaction.atomic():
                # Get cleaned data
                email = self.cleaned_data.get('email')
                phone = self.cleaned_data.get('phone')
                user_type = self.cleaned_data.get('user_type')
                first_name = self.cleaned_data.get('first_name')
                last_name = self.cleaned_data.get('last_name')
                company_name_en = self.cleaned_data.get('company_name_en', '')
                company_name_ar = self.cleaned_data.get('company_name_ar', '')
                company_registration = self.cleaned_data.get('company_registration', '')
                vat_number = self.cleaned_data.get('vat_number', '')
                address_en = self.cleaned_data.get('address_en', '')
                address_ar = self.cleaned_data.get('address_ar', '')
                referral_code = self.cleaned_data.get('referral_code', '')
                password = self.cleaned_data.get('password1')
                
                # Create user using CustomUserManager with transaction
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    phone=phone,
                    first_name=first_name,
                    last_name=last_name,
                    user_type=user_type,
                    company_name_en=company_name_en,
                    company_name_ar=company_name_ar,
                    company_registration=company_registration or None,
                    vat_number=vat_number or None,
                    address_en=address_en,
                    address_ar=address_ar,
                    status='pending',
                    is_active=True,
                )
                
                # Set referred_by if referral code provided
                if referral_code:
                    try:
                        referrer = User.objects.get(referral_code=referral_code)
                        user.referred_by = referrer
                        user.save(update_fields=['referred_by'])
                    except User.DoesNotExist:
                        pass  # Ignore if referral code not found
                
                # Generate referral code for the user if they are an agent
                if user.user_type in ['agent', 'super_agent', 'sub_agent']:
                    user.generate_referral_code()
                    user.save(update_fields=['referral_code'])
                
                # Create user profile
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'language': 'en',
                        'timezone': 'Asia/Riyadh'
                    }
                )
                
                return user
                
        except Exception as e:
            # Log error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving user: {str(e)}")
            raise ValidationError(_('An error occurred during registration. Please try again.'))


class UserUpdateForm(forms.ModelForm):
    """User profile update form"""
    
    email = forms.EmailField(
        label=_('Email'),
        disabled=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )
    
    phone = forms.CharField(
        label=_('Phone Number'),
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX'
        })
    )
    
    first_name = forms.CharField(
        label=_('First Name'),
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    last_name = forms.CharField(
        label=_('Last Name'),
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    company_name_en = forms.CharField(
        label=_('Company Name (English)'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    company_name_ar = forms.CharField(
        label=_('Company Name (Arabic)'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'dir': 'rtl'
        })
    )
    
    company_registration = forms.CharField(
        label=_('CR Number'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    vat_number = forms.CharField(
        label=_('VAT Number'),
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '3XXXXXXXXXXXXXX'
        })
    )
    
    scta_license = forms.CharField(
        label=_('SCTA License'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    hajj_license = forms.CharField(
        label=_('Hajj License'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    iata_number = forms.CharField(
        label=_('IATA Number'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    region = forms.ModelChoiceField(
        label=_('Region'),
        queryset=SaudiRegion.objects.filter(is_active=True),
        required=False,
        empty_label=_('Select Region'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_region'
        })
    )
    
    city = forms.ModelChoiceField(
        label=_('City'),
        queryset=SaudiCity.objects.none(),
        required=False,
        empty_label=_('Select City'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_city'
        })
    )
    
    address_en = forms.CharField(
        label=_('Address (English)'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Full address in English')
        }),
        required=False
    )
    
    address_ar = forms.CharField(
        label=_('Address (Arabic)'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('العنوان الكامل بالعربية'),
            'dir': 'rtl'
        }),
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'phone', 'first_name', 'last_name',
            'company_name_en', 'company_name_ar', 'company_registration',
            'vat_number', 'scta_license', 'hajj_license', 'iata_number',
            'region', 'city', 'address_en', 'address_ar'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values
        if self.instance.pk:
            if self.instance.city:
                self.fields['region'].initial = self.instance.city.region
                self.fields['city'].queryset = SaudiCity.objects.filter(
                    region=self.instance.city.region, 
                    is_active=True
                )
        
        # Add JavaScript for region-city dependency
        self.fields['region'].widget.attrs.update({
            'onchange': 'loadCities(this.value)'
        })
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('This phone number is already registered.'))
        
        # Validate format
        if not re.match(r'^\+9665\d{8}$', phone):
            raise ValidationError(_('Phone number must be in Saudi format: +9665XXXXXXXX'))
        
        return phone
    
    def clean_company_registration(self):
        cr_number = self.cleaned_data.get('company_registration')
        if cr_number and User.objects.filter(company_registration=cr_number).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('This CR number is already registered.'))
        return cr_number
    
    def clean_vat_number(self):
        vat_number = self.cleaned_data.get('vat_number')
        if vat_number and not re.match(r'^3\d{14}$', vat_number):
            raise ValidationError(_('VAT number must be 15 digits starting with 3.'))
        return vat_number


class UserProfileForm(forms.ModelForm):
    """User profile extension form"""
    
    business_type = forms.ChoiceField(
        label=_('Business Type'),
        choices=[
            ('', _('Select Business Type')),
            ('travel_agency', _('Travel Agency')),
            ('tour_operator', _('Tour Operator')),
            ('corporate_travel', _('Corporate Travel Management')),
            ('hajj_umrah', _('Hajj & Umrah Services')),
            ('ticketing', _('Ticketing Agency')),
            ('hotel_booking', _('Hotel Booking Agency')),
            ('transport', _('Transport Services')),
            ('other', _('Other'))
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=False
    )
    
    years_in_business = forms.IntegerField(
        label=_('Years in Business'),
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )
    
    bank_name_en = forms.CharField(
        label=_('Bank Name (English)'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )
    
    bank_name_ar = forms.CharField(
        label=_('Bank Name (Arabic)'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'dir': 'rtl'
        }),
        required=False
    )
    
    account_number = forms.CharField(
        label=_('Account Number'),
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )
    
    iban = forms.CharField(
        label=_('IBAN'),
        max_length=24,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'SAXXXXXXXXXXXXXXXXXXXX'
        }),
        required=False
    )
    
    language = forms.ChoiceField(
        label=_('Preferred Language'),
        choices=[
            ('en', 'English'),
            ('ar', 'Arabic')
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    timezone = forms.ChoiceField(
        label=_('Timezone'),
        choices=[
            ('Asia/Riyadh', 'Riyadh (GMT+3)'),
            ('Asia/Dammam', 'Dammam (GMT+3)'),
            ('Asia/Jeddah', 'Jeddah (GMT+3)'),
            ('UTC', 'UTC'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'business_type', 'years_in_business',
            'bank_name_en', 'bank_name_ar', 'account_number', 'iban',
            'language', 'timezone'
        ]
    
    def clean_iban(self):
        iban = self.cleaned_data.get('iban')
        if iban:
            # Basic IBAN validation for Saudi Arabia
            if not iban.startswith('SA'):
                raise ValidationError(_('IBAN must start with SA for Saudi Arabia.'))
            if len(iban) != 24:
                raise ValidationError(_('IBAN must be 24 characters long.'))
        return iban


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form"""
    
    old_password = forms.CharField(
        label=_("Current Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'autofocus': True,
            'class': 'form-control',
            'placeholder': _('Enter current password')
        }),
    )
    
    new_password1 = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'placeholder': _('Enter new password')
        }),
        strip=False,
        help_text=_("Password must contain at least 8 characters, including uppercase, lowercase, numbers and special characters.")
    )
    
    new_password2 = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'placeholder': _('Confirm new password')
        }),
        strip=False,
    )
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        
        # Django's built-in validation
        try:
            password_validation.validate_password(password, self.user)
        except ValidationError as e:
            raise ValidationError(e.messages)
        
        # Custom validation
        if len(password) < 8:
            raise ValidationError(_('Password must be at least 8 characters long.'))
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Password must contain at least one uppercase letter.'))
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Password must contain at least one lowercase letter.'))
        if not re.search(r'[0-9]', password):
            raise ValidationError(_('Password must contain at least one number.'))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_('Password must contain at least one special character.'))
        
        return password


class PasswordResetForm(forms.Form):
    """Password reset form"""
    
    email = forms.EmailField(
        label=_('Email Address'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email, is_active=True).exists():
            raise ValidationError(_('No account found with this email address.'))
        return email


class PasswordResetConfirmForm(forms.Form):
    """Password reset confirmation form"""
    
    new_password1 = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'placeholder': _('Enter new password')
        }),
        strip=False,
    )
    
    new_password2 = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'placeholder': _('Confirm new password')
        }),
        strip=False,
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', _('Passwords do not match.'))
        
        if password1:
            if len(password1) < 8:
                self.add_error('new_password1', _('Password must be at least 8 characters long.'))
            
            if not re.search(r'[A-Z]', password1):
                self.add_error('new_password1', _('Password must contain at least one uppercase letter.'))
            if not re.search(r'[a-z]', password1):
                self.add_error('new_password1', _('Password must contain at least one lowercase letter.'))
            if not re.search(r'[0-9]', password1):
                self.add_error('new_password1', _('Password must contain at least one number.'))
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
                self.add_error('new_password1', _('Password must contain at least one special character.'))
        
        return cleaned_data