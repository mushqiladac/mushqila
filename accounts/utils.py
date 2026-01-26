# accounts/utils.py
"""
Utility functions for the Accounts app - Saudi Arabia Version.
"""
import logging
import random
import string
import uuid
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ==================== Email Functions ====================

def send_verification_email(user, request) -> bool:
    """Send email verification link to user"""
    try:
        # Generate verification token
        token = str(uuid.uuid4())
        
        # Store token in cache for 24 hours
        cache_key = f'email_verify_{user.id}'
        cache.set(cache_key, token, timeout=86400)  # 24 hours
        
        # Build verification URL
        verification_url = request.build_absolute_uri(
            f'/accounts/verify-email/{user.id}/{token}/'
        )
        
        # Send email
        subject = _('Verify Your Email - Mushqila B2B Saudi Arabia')
        html_message = render_to_string('accounts/emails/verify_email.html', {
            'user': user,
            'verification_url': verification_url,
            'year': datetime.now().year,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {str(e)}")
        return False


def send_welcome_email(user) -> bool:
    """Send welcome email to new user"""
    try:
        subject = _('Welcome to Mushqila B2B Travel Platform - Saudi Arabia')
        html_message = render_to_string('accounts/emails/welcome.html', {
            'user': user,
            'year': datetime.now().year,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(form, request) -> bool:
    """Send password reset email"""
    try:
        opts = {
            'use_https': request.is_secure(),
            'token_generator': None,
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'email_template_name': 'accounts/emails/password_reset_email.html',
            'subject_template_name': 'accounts/emails/password_reset_subject.txt',
            'request': request,
            'html_email_template_name': 'accounts/emails/password_reset_email.html',
            'extra_email_context': {
                'year': datetime.now().year,
                'saudi_support_phone': getattr(settings, 'SAUDI_SUPPORT_PHONE', '+966920000000'),
            },
        }
        
        form.save(**opts)
        return True
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False


def send_deposit_notification_email(user, amount, transaction_id, currency) -> bool:
    """Send deposit notification email"""
    try:
        subject = _('Deposit Request Submitted - Mushqila B2B Saudi Arabia')
        html_message = render_to_string('accounts/emails/deposit_notification.html', {
            'user': user,
            'amount': amount,
            'transaction_id': transaction_id,
            'currency': currency,
            'year': datetime.now().year,
            'saudi_time': get_saudi_time(),
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending deposit notification email to {user.email}: {str(e)}")
        return False


def send_credit_request_email(user, amount, reason, currency) -> bool:
    """Send credit request email"""
    try:
        subject = _('Credit Limit Request - Mushqila B2B Saudi Arabia')
        
        # Send to user
        html_message_user = render_to_string('accounts/emails/credit_request_user.html', {
            'user': user,
            'amount': amount,
            'reason': reason,
            'currency': currency,
            'year': datetime.now().year,
        })
        plain_message_user = strip_tags(html_message_user)
        
        send_mail(
            subject=subject,
            message=plain_message_user,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message_user,
            fail_silently=True,
        )
        
        # Send to admin
        admin_emails = ['admin@mushqila.com']  # You can make this configurable
        html_message_admin = render_to_string('accounts/emails/credit_request_admin.html', {
            'user': user,
            'amount': amount,
            'reason': reason,
            'currency': currency,
            'year': datetime.now().year,
            'current_limit': user.credit_limit,
            'current_balance': user.current_balance,
        })
        plain_message_admin = strip_tags(html_message_admin)
        
        send_mail(
            subject=f'[Admin] {subject}',
            message=plain_message_admin,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=html_message_admin,
            fail_silently=True,
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending credit request email: {str(e)}")
        return False


def send_kyc_approved_email(user) -> bool:
    """Send KYC approved email"""
    try:
        subject = _('KYC Verification Approved - Mushqila B2B Saudi Arabia')
        html_message = render_to_string('accounts/emails/kyc_approved.html', {
            'user': user,
            'year': datetime.now().year,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending KYC approved email to {user.email}: {str(e)}")
        return False


def send_account_activated_email(user) -> bool:
    """Send account activated email"""
    try:
        subject = _('Account Activated - Mushqila B2B Saudi Arabia')
        html_message = render_to_string('accounts/emails/account_activated.html', {
            'user': user,
            'year': datetime.now().year,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending account activated email to {user.email}: {str(e)}")
        return False


# ==================== Utility Functions ====================

def generate_transaction_id() -> str:
    """Generate a unique transaction ID"""
    timestamp = int(timezone.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"TRX-{timestamp}-{random_str}"


def get_client_ip(request) -> str:
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def validate_file_upload(file_obj, max_size=5*1024*1024, allowed_types=None) -> Dict[str, Any]:
    """Validate file upload"""
    allowed_types = allowed_types or [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    if file_obj.size > max_size:
        return {
            'valid': False,
            'message': _(f'File size must be under {max_size // (1024*1024)}MB.')
        }
    
    if file_obj.content_type not in allowed_types:
        return {
            'valid': False,
            'message': _('Unsupported file type.')
        }
    
    return {'valid': True, 'message': _('File is valid.')}


def generate_referral_code() -> str:
    """Generate a unique referral code"""
    while True:
        code = 'SA' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        from .models import User
        if not User.objects.filter(referral_code=code).exists():
            return code


def check_credit_eligibility(user, requested_amount) -> Dict[str, Any]:
    """Check if user is eligible for credit increase"""
    from .models import User
    
    # Basic eligibility criteria
    if not user.kyc_verified:
        return {
            'eligible': False,
            'message': _('KYC verification is required for credit facilities.')
        }
    
    if user.status != User.Status.ACTIVE:
        return {
            'eligible': False,
            'message': _('Your account must be active to request credit.')
        }
    
    # Calculate credit utilization
    if user.credit_limit > 0:
        utilization = (abs(user.current_balance) / user.credit_limit) * 100
        if utilization > 80:  # 80% utilization threshold
            return {
                'eligible': False,
                'message': _('Your credit utilization is too high. Please clear some dues.')
            }
    
    # Check requested amount
    max_limits = {
        'agent': Decimal('100000.00'),
        'super_agent': Decimal('500000.00'),
        'sub_agent': Decimal('50000.00'),
        'corporate': Decimal('200000.00'),
        'pilgrim': Decimal('300000.00'),
    }
    
    max_limit = max_limits.get(user.user_type, Decimal('50000.00'))
    if requested_amount > max_limit:
        return {
            'eligible': False,
            'message': _('Requested amount exceeds maximum limit for your account type.')
        }
    
    return {
        'eligible': True,
        'message': _('Eligible for credit increase.'),
        'max_eligible_amount': max_limit
    }


def calculate_commission(amount, commission_rate, service_type='flight', is_domestic=True) -> Decimal:
    """Calculate commission based on service type"""
    base_commission = (amount * commission_rate) / 100
    
    # Apply modifiers based on service type
    if service_type == 'hajj':
        base_commission *= Decimal('1.2')  # 20% bonus for Hajj
    elif service_type == 'umrah':
        base_commission *= Decimal('1.15')  # 15% bonus for Umrah
    
    # Apply modifier for international
    if not is_domestic:
        base_commission *= Decimal('1.1')  # 10% bonus for international
    
    return base_commission


def log_user_activity(user, activity_type, description, success=True, **kwargs) -> None:
    """Log user activity"""
    from .models import UserActivityLog
    
    try:
        UserActivityLog.objects.create(
            user=user if user.is_authenticated else None,
            activity_type=activity_type,
            description=description,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            country_code=kwargs.get('country_code', 'SA'),
            metadata=kwargs.get('metadata', {}),
            success=success,
        )
    except Exception as e:
        logger.error(f"Error logging user activity: {str(e)}")


def send_sms_notification(phone, message) -> bool:
    """Send SMS notification"""
    try:
        # This is a placeholder. In production, integrate with SMS gateway
        # For Saudi Arabia, you might use STC, Mobily, or Zain gateway
        logger.info(f"[SMS] To: {phone}, Message: {message}")
        return True
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return False


def send_whatsapp_notification(phone, message) -> bool:
    """Send WhatsApp notification"""
    try:
        # This is a placeholder. In production, integrate with WhatsApp Business API
        logger.info(f"[WhatsApp] To: {phone}, Message: {message}")
        return True
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return False


def generate_otp(email) -> str:
    """Generate OTP for two-factor authentication"""
    # Generate 6-digit OTP
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Store in cache for 5 minutes
    cache_key = f'otp_{email}'
    cache.set(cache_key, otp, timeout=300)
    
    return otp


def verify_otp(email, otp_input, expected_otp=None) -> bool:
    """Verify OTP"""
    if expected_otp:
        # Compare with provided expected OTP
        return otp_input == expected_otp
    
    # Check in cache
    cache_key = f'otp_{email}'
    stored_otp = cache.get(cache_key)
    
    if not stored_otp:
        return False
    
    # Compare and clear cache if valid
    if otp_input == stored_otp:
        cache.delete(cache_key)
        return True
    
    return False


def calculate_vat(amount) -> Decimal:
    """Calculate VAT (15% in Saudi Arabia)"""
    return amount * Decimal('0.15')


def format_saudi_phone(phone) -> str:
    """Format phone number for Saudi Arabia"""
    if not phone:
        return phone
    
    phone = phone.strip()
    
    if phone.startswith('+966'):
        return phone
    elif phone.startswith('966'):
        return '+' + phone
    elif phone.startswith('0'):
        return '+966' + phone[1:]
    elif phone.isdigit() and len(phone) == 9:
        return '+966' + phone
    else:
        return phone


def validate_saudi_cr_number(cr_number) -> Tuple[bool, str]:
    """Validate Saudi Commercial Registration number"""
    if not cr_number:
        return False, _('CR number is required')
    
    # Remove any spaces or dashes
    cr_number = str(cr_number).replace(' ', '').replace('-', '')
    
    # Saudi CR numbers are typically numeric and have specific length
    if not cr_number.isdigit():
        return False, _('CR number must contain only digits')
    
    # Different lengths for different business types
    if len(cr_number) not in [10, 12, 15]:
        return False, _('Invalid CR number length')
    
    return True, cr_number


def check_login_attempts(identifier: str) -> Tuple[bool, int]:
    """
    Check if user has exceeded maximum login attempts
    
    Args:
        identifier: Email or phone identifier
        
    Returns:
        Tuple of (is_blocked, remaining_attempts)
    """
    cache_key = f'login_attempts_{identifier}'
    attempts = cache.get(cache_key, 0)
    
    max_attempts = 5
    lockout_time = 900  # 15 minutes
    
    # Check if user is currently locked out
    lockout_key = f'login_lockout_{identifier}'
    if cache.get(lockout_key):
        return True, 0
    
    remaining = max(0, max_attempts - attempts)
    return False, remaining


def increment_login_attempts(identifier: str) -> int:
    """
    Increment login attempts counter
    
    Args:
        identifier: Email or phone identifier
        
    Returns:
        Current number of attempts
    """
    cache_key = f'login_attempts_{identifier}'
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, timeout=900)  # 15 minutes
    
    max_attempts = 5
    if attempts >= max_attempts:
        # Lock out the user
        lockout_key = f'login_lockout_{identifier}'
        cache.set(lockout_key, True, timeout=900)  # 15 minutes lockout
    
    return attempts


def get_saudi_time() -> datetime:
    """Get current Saudi Arabia time (AST = UTC+3)"""
    return timezone.now() + timedelta(hours=3)


def clear_rate_limit(key) -> None:
    """Clear rate limiting for a specific key"""
    cache.delete(f'rate_limit_{key}')
    cache.delete(f'{key}_lockout')