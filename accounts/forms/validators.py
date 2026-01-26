# accounts/forms/validators.py
"""
Custom validators for B2B Travel Mushqila - Saudi Arabia
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from decimal import Decimal


def validate_saudi_phone(value):
    """Validate Saudi phone number format"""
    pattern = r'^\+9665\d{8}$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Phone number must be in format: +9665XXXXXXXX'),
            code='invalid_phone'
        )


def validate_cr_number(value):
    """Validate Saudi Commercial Registration number"""
    if value:
        # Basic CR number validation
        if not re.match(r'^\d{10}$', value):
            raise ValidationError(
                _('Commercial Registration number must be 10 digits'),
                code='invalid_cr'
            )


def validate_vat_number(value):
    """Validate Saudi VAT number"""
    if value:
        # Saudi VAT numbers start with 3 and are 15 digits total
        if not re.match(r'^3\d{14}$', value):
            raise ValidationError(
                _('VAT number must start with 3 and be 15 digits'),
                code='invalid_vat'
            )


def validate_iban(value):
    """Validate IBAN for Saudi Arabia"""
    if value:
        # Saudi IBAN: SA followed by 22 digits
        if not re.match(r'^SA\d{22}$', value):
            raise ValidationError(
                _('IBAN must start with SA and be 24 characters total'),
                code='invalid_iban'
            )


def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        raise ValidationError(
            _('Password must be at least 8 characters long.'),
            code='password_too_short'
        )
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError(
            _('Password must contain at least one uppercase letter.'),
            code='password_no_upper'
        )
    
    if not re.search(r'[a-z]', password):
        raise ValidationError(
            _('Password must contain at least one lowercase letter.'),
            code='password_no_lower'
        )
    
    if not re.search(r'[0-9]', password):
        raise ValidationError(
            _('Password must contain at least one number.'),
            code='password_no_digit'
        )
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(
            _('Password must contain at least one special character.'),
            code='password_no_special'
        )


def validate_amount_range(value, min_amount=None, max_amount=None):
    """Validate amount range"""
    if min_amount is not None and value < Decimal(str(min_amount)):
        raise ValidationError(
            _('Amount must be at least %(min_amount)s SAR') % {'min_amount': min_amount},
            code='amount_too_low'
        )
    
    if max_amount is not None and value > Decimal(str(max_amount)):
        raise ValidationError(
            _('Amount cannot exceed %(max_amount)s SAR') % {'max_amount': max_amount},
            code='amount_too_high'
        )


def validate_file_size(file, max_size_mb=10):
    """Validate file size"""
    max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
    if file.size > max_size:
        raise ValidationError(
            _('File size must be less than %(max_size) MB') % {'max_size': max_size_mb},
            code='file_too_large'
        )


def validate_file_extension(file, allowed_extensions):
    """Validate file extension"""
    import os
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            _('File type not allowed. Allowed types: %(extensions)s') % 
            {'extensions': ', '.join(allowed_extensions)},
            code='invalid_file_type'
        )