# accounts/forms/auth_forms.py
"""
Authentication forms for B2B Travel Mushqila - Saudi Arabia
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from ..models import User, SMSCode
import re


class LoginForm(forms.Form):
    """Login form with email/phone option"""
    
    LOGIN_CHOICES = [
        ('email', _('Email')),
        ('phone', _('Phone'))
    ]
    
    login_type = forms.ChoiceField(
        label=_('Login With'),
        choices=LOGIN_CHOICES,
        initial='email',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    email = forms.EmailField(
        label=_('Email Address'),
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@domain.com',
            'autocomplete': 'email',
            'id': 'email_field'
        })
    )
    
    phone = forms.CharField(
        label=_('Phone Number'),
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX',
            'autocomplete': 'tel',
            'id': 'phone_field'
        })
    )
    
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your password'),
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        label=_('Remember me'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
    def clean(self):
        cleaned_data = super().clean()
        login_type = cleaned_data.get('login_type')
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')
        password = cleaned_data.get('password')
        
        if login_type == 'email':
            if not email:
                self.add_error('email', _('Email is required.'))
            else:
                user = authenticate(self.request, username=email, password=password)
                if user is None:
                    self.add_error('password', _('Invalid email or password.'))
                elif not user.is_active:
                    self.add_error('email', _('Your account is inactive. Please contact support.'))
                else:
                    cleaned_data['user'] = user
        else:  # phone login
            if not phone:
                self.add_error('phone', _('Phone number is required.'))
            else:
                # Normalize phone number
                if phone.startswith('0'):
                    phone = '+966' + phone[1:]
                elif not phone.startswith('+'):
                    phone = '+966' + phone
                
                try:
                    user = User.objects.get(phone=phone)
                    if not user.check_password(password):
                        self.add_error('password', _('Invalid phone number or password.'))
                    elif not user.is_active:
                        self.add_error('phone', _('Your account is inactive. Please contact support.'))
                    else:
                        cleaned_data['user'] = user
                except User.DoesNotExist:
                    self.add_error('phone', _('No account found with this phone number.'))
        
        return cleaned_data


class OTPVerificationForm(forms.Form):
    """OTP verification form"""
    
    otp_code = forms.CharField(
        label=_('Verification Code'),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'maxlength': '6',
            'style': 'letter-spacing: 10px; font-size: 24px;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.purpose = kwargs.pop('purpose', SMSCode.Purpose.LOGIN)
        super().__init__(*args, **kwargs)
    
    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code')
        
        if not otp_code.isdigit():
            raise ValidationError(_('OTP code must contain only digits.'))
        
        # Verify OTP
        try:
            sms_code = SMSCode.objects.get(
                phone=self.user.phone,
                code=otp_code,
                purpose=self.purpose,
                is_used=False
            )
            
            if sms_code.is_expired():
                raise ValidationError(_('OTP code has expired. Please request a new one.'))
            
            sms_code.is_used = True
            sms_code.save()
            
        except SMSCode.DoesNotExist:
            raise ValidationError(_('Invalid OTP code. Please try again.'))
        
        return otp_code


class TwoFactorForm(forms.Form):
    """Two-factor authentication form"""
    
    verification_code = forms.CharField(
        label=_('2FA Code'),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '123456',
            'autocomplete': 'off',
            'style': 'letter-spacing: 5px;'
        }),
        help_text=_('Enter the 6-digit code from your authenticator app.')
    )
    
    remember_device = forms.BooleanField(
        label=_('Remember this device for 30 days'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        
        if not code.isdigit() or len(code) != 6:
            raise ValidationError(_('Please enter a valid 6-digit code.'))
        
        # Here you would validate against the user's 2FA secret
        # For now, we'll just validate format
        return code


class PhoneVerificationForm(forms.Form):
    """Phone verification form"""
    
    phone = forms.CharField(
        label=_('Phone Number'),
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX',
            'readonly': 'readonly'
        })
    )
    
    verification_code = forms.CharField(
        label=_('Verification Code'),
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'maxlength': '6'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['phone'].initial = self.user.phone
    
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        
        try:
            sms_code = SMSCode.objects.get(
                phone=self.user.phone,
                code=code,
                purpose=SMSCode.Purpose.PHONE_VERIFICATION,
                is_used=False
            )
            
            if sms_code.is_expired():
                raise ValidationError(_('Verification code has expired. Please request a new one.'))
            
            sms_code.is_used = True
            sms_code.save()
            
        except SMSCode.DoesNotExist:
            raise ValidationError(_('Invalid verification code.'))
        
        return code