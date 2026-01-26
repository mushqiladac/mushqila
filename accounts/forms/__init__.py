# accounts/forms/__init__.py
"""
Forms for B2B Travel Mushqila - Saudi Arabia
"""

from .user_forms import *
from .auth_forms import *
from .business_forms import *
from .travel_forms import *
from .financial_forms import *

__all__ = [
    # User forms
    'UserRegistrationForm',
    'UserUpdateForm',
    'UserProfileForm',
    'PasswordChangeForm',
    'PasswordResetForm',
    'PasswordResetConfirmForm',
    
    # Auth forms
    'LoginForm',
    'OTPVerificationForm',
    'TwoFactorForm',
    
    # Business forms
    'DocumentUploadForm',
    'CreditRequestForm',
    'AgentHierarchyForm',
    'IPWhitelistForm',
    
    # Travel forms
    'FlightBookingForm',
    'HotelBookingForm',
    'HajjBookingForm',
    'UmrahBookingForm',
    'VisaApplicationForm',
    
    # Financial forms
    'PaymentForm',
    'RefundRequestForm',
    'DepositForm',
    'WithdrawalForm',
    'InvoiceForm',
]