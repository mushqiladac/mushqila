"""
Custom authentication backends for Mushqila B2B Travel Platform.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone

from .models import User, LoginHistory
from .utils import get_client_ip, log_user_activity, check_login_attempts, increment_login_attempts

logger = logging.getLogger(__name__)


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate using either email or username.
    Supports case-insensitive matching and login attempt limiting.
    """
    
    def authenticate(
        self, 
        request, 
        username: Optional[str] = None, 
        password: Optional[str] = None, 
        **kwargs
    ) -> Optional[AbstractBaseUser]:
        """
        Authenticate user with email/username and password.
        
        Args:
            request: HttpRequest object
            username: Username or email address
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        UserModel = get_user_model()
        
        if username is None or password is None:
            return None
        
        username = username.strip()
        
        # Get client IP for rate limiting
        ip_address = get_client_ip(request) if request else '0.0.0.0'
        
        # Check login attempts before proceeding
        allowed, message = check_login_attempts(ip_address, username)
        if not allowed:
            logger.warning(f"Login blocked for {username} from {ip_address}: {message}")
            self._log_failed_attempt(request, username, ip_address, 'rate_limit_exceeded')
            return None
        
        try:
            # Try to fetch user by email (case-insensitive) or username
            user = UserModel.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )
            
            # Check if user can authenticate
            if not self.user_can_authenticate(user):
                logger.warning(f"User {username} cannot authenticate (inactive/blocked)")
                self._log_failed_attempt(request, username, ip_address, 'account_not_authenticable')
                increment_login_attempts(ip_address, username)
                return None
            
            # Verify password
            if user.check_password(password):
                # Check account status
                status_check = self._check_account_status(user)
                if not status_check[0]:
                    logger.warning(f"Login failed for {username}: {status_check[1]}")
                    self._log_failed_attempt(request, username, ip_address, status_check[2])
                    increment_login_attempts(ip_address, username)
                    return None
                
                # Authentication successful
                self._log_successful_attempt(request, user, ip_address)
                return user
            else:
                # Invalid password
                logger.warning(f"Invalid password for {username}")
                self._log_failed_attempt(request, username, ip_address, 'invalid_password')
                increment_login_attempts(ip_address, username)
                return None
                
        except UserModel.DoesNotExist:
            # User not found - run dummy password check to prevent timing attacks
            UserModel().set_password(password)
            logger.warning(f"User not found: {username}")
            self._log_failed_attempt(request, username, ip_address, 'user_not_found')
            increment_login_attempts(ip_address, username)
            return None
        
        except UserModel.MultipleObjectsReturned:
            # Multiple users found (should not happen with unique email constraint)
            logger.error(f"Multiple users found for {username}")
            self._log_failed_attempt(request, username, ip_address, 'multiple_users')
            increment_login_attempts(ip_address, username)
            return None
        
        except Exception as e:
            # Unexpected error
            logger.error(f"Authentication error for {username}: {str(e)}", exc_info=True)
            self._log_failed_attempt(request, username, ip_address, 'system_error')
            return None
    
    def get_user(self, user_id: int) -> Optional[AbstractBaseUser]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found and can authenticate, None otherwise
        """
        try:
            user = User.objects.get(pk=user_id)
            return user if self.user_can_authenticate(user) else None
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}", exc_info=True)
            return None
    
    def user_can_authenticate(self, user: User) -> bool:
        """
        Check if user can authenticate.
        Override to add custom checks.
        
        Args:
            user: User object
            
        Returns:
            bool: True if user can authenticate
        """
        # Call parent method first
        if not super().user_can_authenticate(user):
            return False
        
        # Additional custom checks
        if user.status in [User.Status.BLOCKED, User.Status.SUSPENDED]:
            return False
        
        # Check if email is verified (optional - depends on requirements)
        if getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False) and not user.email_verified:
            return False
        
        return True
    
    def _check_account_status(self, user: User) -> Tuple[bool, str, str]:
        """
        Check account status before allowing authentication.
        
        Args:
            user: User object
            
        Returns:
            Tuple[bool, str, str]: (is_allowed, message, error_code)
        """
        if not user.is_active:
            return False, "Account is deactivated.", "account_inactive"
        
        if user.status == User.Status.BLOCKED:
            return False, "Account has been blocked.", "account_blocked"
        
        if user.status == User.Status.SUSPENDED:
            return False, "Account is suspended.", "account_suspended"
        
        if user.status == User.Status.INACTIVE:
            return False, "Account is inactive.", "account_inactive"
        
        # Check if KYC is required for this user type
        if (user.user_type in ['agent', 'super_agent'] and 
            getattr(settings, 'REQUIRE_KYC_FOR_AGENTS', True) and 
            not user.kyc_verified):
            return False, "KYC verification required.", "kyc_required"
        
        return True, "Account is active.", "active"
    
    def _log_successful_attempt(self, request, user: User, ip_address: str):
        """
        Log successful login attempt.
        
        Args:
            request: HttpRequest object
            user: User object
            ip_address: Client IP address
        """
        try:
            # Create login history record
            LoginHistory.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True
            )
            
            # Log activity
            log_user_activity(user, 'login_success', f'Login from {ip_address}', True)
            
            # Clear failed attempt counters
            from .utils import reset_login_attempts
            reset_login_attempts(ip_address, user.email)
            
            logger.info(f"Successful login: {user.email} from {ip_address}")
            
        except Exception as e:
            logger.error(f"Error logging successful login: {str(e)}", exc_info=True)
    
    def _log_failed_attempt(self, request, username: str, ip_address: str, reason: str):
        """
        Log failed login attempt.
        
        Args:
            request: HttpRequest object
            username: Username/email used
            ip_address: Client IP address
            reason: Failure reason
        """
        try:
            # Try to find user for logging
            user = None
            try:
                user = User.objects.get(
                    Q(email__iexact=username) | Q(username__iexact=username)
                )
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
            
            # Create login history record
            LoginHistory.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=False,
                failure_reason=reason
            )
            
            # Log activity
            log_user_activity(
                user, 
                'login_failed', 
                f'Failed login for {username} from {ip_address}: {reason}', 
                False
            )
            
            logger.warning(f"Failed login: {username} from {ip_address}: {reason}")
            
        except Exception as e:
            logger.error(f"Error logging failed login: {str(e)}", exc_info=True)


class PhoneNumberBackend(ModelBackend):
    """
    Authenticate using phone number.
    Useful for OTP-based or SMS-based authentication.
    """
    
    def authenticate(self, request, phone: Optional[str] = None, password: Optional[str] = None, **kwargs):
        """
        Authenticate user with phone number and password.
        
        Args:
            request: HttpRequest object
            phone: Phone number
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        UserModel = get_user_model()
        
        if phone is None or password is None:
            return None
        
        phone = phone.strip()
        
        # Get client IP for rate limiting
        ip_address = get_client_ip(request) if request else '0.0.0.0'
        
        # Check login attempts
        allowed, message = check_login_attempts(ip_address, phone)
        if not allowed:
            logger.warning(f"Phone login blocked for {phone} from {ip_address}: {message}")
            return None
        
        try:
            # Try to fetch user by phone number
            user = UserModel.objects.get(phone=phone)
            
            # Check if user can authenticate
            if not self.user_can_authenticate(user):
                logger.warning(f"User with phone {phone} cannot authenticate")
                increment_login_attempts(ip_address, phone)
                return None
            
            # Verify password
            if user.check_password(password):
                # Check account status
                status_check = EmailOrUsernameBackend._check_account_status(self, user)
                if not status_check[0]:
                    logger.warning(f"Phone login failed for {phone}: {status_check[1]}")
                    increment_login_attempts(ip_address, phone)
                    return None
                
                # Authentication successful
                EmailOrUsernameBackend._log_successful_attempt(self, request, user, ip_address)
                return user
            else:
                # Invalid password
                logger.warning(f"Invalid password for phone {phone}")
                increment_login_attempts(ip_address, phone)
                return None
                
        except UserModel.DoesNotExist:
            # User not found
            UserModel().set_password(password)
            logger.warning(f"User not found with phone: {phone}")
            increment_login_attempts(ip_address, phone)
            return None
        
        except Exception as e:
            logger.error(f"Phone authentication error for {phone}: {str(e)}", exc_info=True)
            return None


class TwoFactorBackend(ModelBackend):
    """
    Two-factor authentication backend.
    Requires password and TOTP token.
    """
    
    def authenticate(
        self, 
        request, 
        username: Optional[str] = None, 
        password: Optional[str] = None, 
        token: Optional[str] = None,
        **kwargs
    ):
        """
        Authenticate with username/email, password, and TOTP token.
        
        Args:
            request: HttpRequest object
            username: Username or email
            password: Password
            token: TOTP token
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if token is None:
            return None
        
        # First authenticate with primary backend
        primary_backend = EmailOrUsernameBackend()
        user = primary_backend.authenticate(request, username, password)
        
        if user is None:
            return None
        
        # Check if 2FA is enabled for user
        if not user.two_factor_auth:
            return user
        
        # Verify TOTP token
        if self._verify_totp_token(user, token):
            logger.info(f"2FA successful for user: {user.email}")
            return user
        else:
            logger.warning(f"Invalid 2FA token for user: {user.email}")
            return None
    
    def _verify_totp_token(self, user: User, token: str) -> bool:
        """
        Verify TOTP token.
        In production, integrate with a TOTP library like pyotp.
        
        Args:
            user: User object
            token: TOTP token
            
        Returns:
            bool: True if token is valid
        """
        # This is a placeholder implementation
        # In production, use: pip install pyotp
        
        try:
            # Check if user has TOTP secret
            if not hasattr(user, 'totp_secret') or not user.totp_secret:
                return False
            
            # In production, use:
            # import pyotp
            # totp = pyotp.TOTP(user.totp_secret)
            # return totp.verify(token, valid_window=1)
            
            # For now, return True for development
            # Remove this in production
            if settings.DEBUG and token == "123456":
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying TOTP token: {str(e)}", exc_info=True)
            return False


class ReferralCodeBackend(ModelBackend):
    """
    Authentication backend for referral code-based registration.
    """
    
    def authenticate(self, request, referral_code: Optional[str] = None, **kwargs):
        """
        Validate referral code.
        
        Args:
            request: HttpRequest object
            referral_code: Referral code
            
        Returns:
            User object if referral code is valid, None otherwise
        """
        if referral_code is None:
            return None
        
        try:
            # Find user by referral code
            referrer = User.objects.get(
                referral_code=referral_code,
                status=User.Status.ACTIVE,
                is_active=True
            )
            
            # Log referral code usage
            log_user_activity(
                referrer, 
                'referral_code_used', 
                f'Referral code used: {referral_code}', 
                True
            )
            
            return referrer
            
        except User.DoesNotExist:
            logger.warning(f"Invalid referral code: {referral_code}")
            return None
        except Exception as e:
            logger.error(f"Error validating referral code: {str(e)}", exc_info=True)
            return None


class SSOBackend(ModelBackend):
    """
    Single Sign-On (SSO) authentication backend.
    Integrates with external identity providers.
    """
    
    def authenticate(self, request, provider: Optional[str] = None, token: Optional[str] = None, **kwargs):
        """
        Authenticate using SSO provider.
        
        Args:
            request: HttpRequest object
            provider: SSO provider name (google, facebook, etc.)
            token: Access token from provider
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if provider is None or token is None:
            return None
        
        try:
            # Validate token with provider
            user_info = self._validate_sso_token(provider, token)
            if not user_info:
                return None
            
            # Get or create user
            user = self._get_or_create_sso_user(provider, user_info)
            
            if user and self.user_can_authenticate(user):
                # Log successful SSO login
                ip_address = get_client_ip(request) if request else '0.0.0.0'
                log_user_activity(user, 'sso_login', f'SSO login via {provider}', True)
                
                logger.info(f"SSO login successful: {user.email} via {provider}")
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"SSO authentication error: {str(e)}", exc_info=True)
            return None
    
    def _validate_sso_token(self, provider: str, token: str) -> Optional[dict]:
        """
        Validate SSO token with provider.
        
        Args:
            provider: SSO provider name
            token: Access token
            
        Returns:
            dict: User information if token valid, None otherwise
        """
        # This is a placeholder implementation
        # In production, integrate with:
        # - Google: google-auth library
        # - Facebook: facebook-sdk
        # - OAuth2: requests-oauthlib
        
        # For now, return dummy data for development
        if settings.DEBUG and token == "debug_token":
            return {
                'email': 'test@sso.com',
                'first_name': 'SSO',
                'last_name': 'User',
                'provider': provider,
                'provider_id': 'test_id'
            }
        
        return None
    
    def _get_or_create_sso_user(self, provider: str, user_info: dict) -> Optional[User]:
        """
        Get or create user from SSO information.
        
        Args:
            provider: SSO provider name
            user_info: User information from provider
            
        Returns:
            User object if successful, None otherwise
        """
        email = user_info.get('email')
        if not email:
            return None
        
        try:
            # Try to get existing user
            user = User.objects.get(email=email)
            
            # Update user information
            user.first_name = user_info.get('first_name', user.first_name)
            user.last_name = user_info.get('last_name', user.last_name)
            user.save(update_fields=['first_name', 'last_name', 'updated_at'])
            
            return user
            
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                email=email,
                username=email,
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', ''),
                user_type='customer',  # Default type for SSO users
                status='active',
                email_verified=True,  # Assume verified by provider
                is_active=True
            )
            
            # Set unusable password for SSO users
            user.set_unusable_password()
            user.save()
            
            logger.info(f"New SSO user created: {email} via {provider}")
            return user
            
        except Exception as e:
            logger.error(f"Error getting/creating SSO user: {str(e)}", exc_info=True)
            return None


class AgentBackend(ModelBackend):
    """
    Special authentication backend for agents only.
    Additional security checks for business accounts.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate agents with additional security checks.
        
        Args:
            request: HttpRequest object
            username: Username or email
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Use primary backend first
        primary_backend = EmailOrUsernameBackend()
        user = primary_backend.authenticate(request, username, password)
        
        if user is None:
            return None
        
        # Check if user is an agent type
        if not user.is_agent():
            logger.warning(f"Non-agent user attempted agent login: {user.email}")
            return None
        
        # Additional agent-specific checks
        if not user.kyc_verified and getattr(settings, 'REQUIRE_KYC_FOR_AGENTS', True):
            logger.warning(f"Agent without KYC attempted login: {user.email}")
            return None
        
        # Check business hours if configured
        if getattr(settings, 'ENFORCE_BUSINESS_HOURS', False):
            if not self._is_business_hours():
                logger.warning(f"Agent login outside business hours: {user.email}")
                return None
        
        return user
    
    def _is_business_hours(self) -> bool:
        """
        Check if current time is within business hours.
        
        Returns:
            bool: True if within business hours
        """
        now = timezone.localtime(timezone.now())
        
        # Default business hours: 9 AM to 6 PM, Monday to Friday
        business_hours = getattr(settings, 'BUSINESS_HOURS', {
            'start_hour': 9,
            'end_hour': 18,
            'days': [0, 1, 2, 3, 4]  # Monday to Friday
        })
        
        current_hour = now.hour
        current_day = now.weekday()  # Monday=0, Sunday=6
        
        # Check day
        if current_day not in business_hours['days']:
            return False
        
        # Check hour
        if not (business_hours['start_hour'] <= current_hour < business_hours['end_hour']):
            return False
        
        return True


class IPWhitelistBackend(ModelBackend):
    """
    Authentication backend with IP whitelisting.
    Additional security layer for admin/super agent accounts.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate with IP whitelist check.
        
        Args:
            request: HttpRequest object
            username: Username or email
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Get client IP
        ip_address = get_client_ip(request) if request else '0.0.0.0'
        
        # Use primary backend first
        primary_backend = EmailOrUsernameBackend()
        user = primary_backend.authenticate(request, username, password)
        
        if user is None:
            return None
        
        # Check IP whitelist for admin/super agent accounts
        if user.user_type in ['admin', 'super_agent']:
            whitelist = getattr(settings, 'IP_WHITELIST', [])
            
            # Always allow localhost in development
            if settings.DEBUG and ip_address in ['127.0.0.1', '::1']:
                return user
            
            # Check if IP is in whitelist
            if not self._is_ip_whitelisted(ip_address, whitelist):
                logger.warning(f"IP not whitelisted for admin login: {ip_address}")
                return None
        
        return user
    
    def _is_ip_whitelisted(self, ip_address: str, whitelist: list) -> bool:
        """
        Check if IP address is in whitelist.
        Supports CIDR notation and IP ranges.
        
        Args:
            ip_address: IP address to check
            whitelist: List of IP addresses/CIDR blocks
            
        Returns:
            bool: True if IP is whitelisted
        """
        # Simple exact match for now
        # In production, use ipaddress module for CIDR support
        return ip_address in whitelist


# ==================== Backend Configuration ====================

def get_authentication_backends() -> list:
    """
    Get list of authentication backends based on settings.
    
    Returns:
        list: Authentication backend classes
    """
    backends = [
        'accounts.backends.EmailOrUsernameBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
    
    # Add optional backends based on settings
    if getattr(settings, 'ENABLE_PHONE_AUTH', False):
        backends.insert(0, 'accounts.backends.PhoneNumberBackend')
    
    if getattr(settings, 'ENABLE_SSO', False):
        backends.insert(0, 'accounts.backends.SSOBackend')
    
    if getattr(settings, 'ENABLE_2FA', False):
        backends.insert(0, 'accounts.backends.TwoFactorBackend')
    
    if getattr(settings, 'ENABLE_AGENT_BACKEND', False):
        backends.insert(0, 'accounts.backends.AgentBackend')
    
    if getattr(settings, 'ENABLE_IP_WHITELIST', False):
        backends.insert(0, 'accounts.backends.IPWhitelistBackend')
    
    return backends


def get_referral_backend():
    """
    Get referral authentication backend.
    
    Returns:
        ReferralCodeBackend: Referral backend instance
    """
    return ReferralCodeBackend()


# ==================== Settings Configuration ====================

# Add these to settings.py for backend configuration
"""
# Authentication backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
    'accounts.backends.PhoneNumberBackend',  # Optional
    'accounts.backends.TwoFactorBackend',    # Optional
    'accounts.backends.SSOBackend',          # Optional
    'django.contrib.auth.backends.ModelBackend',
]

# Backend settings
ENABLE_PHONE_AUTH = True  # Enable phone number authentication
ENABLE_2FA = True         # Enable two-factor authentication
ENABLE_SSO = False        # Enable Single Sign-On
ENABLE_AGENT_BACKEND = True  # Special backend for agents
ENABLE_IP_WHITELIST = True   # IP whitelist for admin accounts

# SSO providers
SSO_PROVIDERS = {
    'google': {
        'CLIENT_ID': 'your-client-id',
        'CLIENT_SECRET': 'your-client-secret',
    },
    'facebook': {
        'APP_ID': 'your-app-id',
        'APP_SECRET': 'your-app-secret',
    }
}

# IP whitelist for admin accounts
IP_WHITELIST = [
    '192.168.1.0/24',  # Office network
    '203.0.113.0/24',  # VPN network
]

# Business hours for agent login
ENFORCE_BUSINESS_HOURS = True
BUSINESS_HOURS = {
    'start_hour': 9,
    'end_hour': 18,
    'days': [0, 1, 2, 3, 4],  # Monday to Friday
}

# Security settings
REQUIRE_EMAIL_VERIFICATION = True   # Require email verification for login
REQUIRE_KYC_FOR_AGENTS = True       # Require KYC for agent login
MAX_LOGIN_ATTEMPTS_PER_IP = 10      # Max login attempts per IP
MAX_LOGIN_ATTEMPTS_PER_EMAIL = 5    # Max login attempts per email
LOGIN_ATTEMPT_TIMEOUT = 300         # Lockout duration in seconds
"""