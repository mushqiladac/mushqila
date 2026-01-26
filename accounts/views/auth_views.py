# accounts/views/auth_views.py
"""
Authentication views for B2B Travel Mushqila - Saudi Arabia
FINAL PRODUCTION READY VERSION - COMPLETE FIXED VERSION
FIXED: Registration issues, login redirects, and database update problems
PRODUCTION READY - DO NOT MODIFY WITHOUT TESTING
"""

import random
import string
import uuid
from datetime import timedelta

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import View, FormView, TemplateView
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator

# Import models
from ..models import User, UserProfile
from ..models.core import UserActivityLog

# Import forms
from ..forms import (
    LoginForm, UserRegistrationForm, OTPVerificationForm,
    PhoneVerificationForm, PasswordResetForm, PasswordResetConfirmForm
)


class LoginView(BaseLoginView):
    """Custom login view with Saudi phone support - FIXED"""
    
    form_class = LoginForm
    template_name = 'accounts/auth/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Authenticate user and set session"""
        # Get user from form
        username = form.cleaned_data.get('email') or form.cleaned_data.get('phone')
        password = form.cleaned_data.get('password')
        
        # Authenticate user
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(self.request, user)
                
                # Log activity
                try:
                    UserActivityLog.objects.create(
                        user=user,
                        activity_type='login',
                        description=f"User logged in from {self.get_client_ip()}",
                        ip_address=self.get_client_ip(),
                        user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'login_method': 'email' if '@' in username else 'phone'
                        }
                    )
                except Exception as e:
                    print(f"Failed to log activity: {e}")
                
                # Update user last login info
                user.last_login_ip = self.get_client_ip()
                user.last_activity = timezone.now()
                user.save(update_fields=['last_login_ip', 'last_activity'])
                
                messages.success(self.request, _('Welcome back!'))
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, _('Your account is inactive.'))
        else:
            messages.error(self.request, _('Invalid email/phone or password.'))
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirect based on user type - FIXED"""
        user = self.request.user
        
        # Ensure user has a profile
        if not hasattr(user, 'profile'):
            try:
                UserProfile.objects.get_or_create(user=user)
            except:
                pass
        
        # FIXED: User type অনুযায়ী redirect
        if user.user_type == 'admin' or user.is_staff or user.is_superuser:
            return reverse_lazy('accounts:admin_dashboard')
        elif user.user_type in ['agent', 'super_agent', 'sub_agent', 'corporate']:
            return reverse_lazy('accounts:agent_dashboard')
        elif user.user_type == 'supplier':
            return reverse_lazy('accounts:supplier_dashboard')
        else:
            # Default fallback
            return reverse_lazy('accounts:dashboard_redirect')
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        email = form.data.get('email')
        phone = form.data.get('phone')
        
        # Log failed attempt
        try:
            if email:
                user = User.objects.filter(email=email).first()
            elif phone:
                user = User.objects.filter(phone=phone).first()
            else:
                user = None
            
            if user:
                UserActivityLog.objects.create(
                    user=user,
                    activity_type='login_failed',
                    description=f"Failed login attempt from {self.get_client_ip()}",
                    ip_address=self.get_client_ip(),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    metadata={'reason': 'invalid_credentials'}
                )
        except Exception as e:
            print(f"Failed to log failed attempt: {e}")
        
        messages.error(self.request, _('Invalid email/phone or password.'))
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Login')
        context['show_password_reset'] = True
        context['show_register_link'] = True
        return context


class LogoutView(LoginRequiredMixin, View):
    """Logout view - redirects to landing page after logout"""
    
    def get(self, request):
        # Log activity
        try:
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='logout',
                description=f"User logged out from {self.get_client_ip(request)}",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Failed to log logout activity: {e}")
        
        logout(request)
        messages.success(request, _('You have been successfully logged out.'))
        return redirect('accounts:home')
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


@method_decorator(sensitive_post_parameters('password1', 'password2'), name='dispatch')
class RegisterView(View):
    """
    User registration view - FIXED VERSION
    Solves both registration and database update issues
    """
    
    template_name = 'accounts/auth/register.html'
    
    def get(self, request):
        """Show registration form"""
        form = UserRegistrationForm()
        return render(request, self.template_name, {
            'form': form,
            'page_title': _('Register'),
            'site_name': 'Mushqila Travel'
        })
    
    def post(self, request):
        """Handle registration form submission"""
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save user using form's save method
                    user = form.save()
                    
                    print(f"✅ USER CREATED: ID={user.id}, Email={user.email}, Type={user.user_type}")
                    
                    # Auto-login the user
                    login(request, user)
                    print(f"✅ AUTO-LOGIN SUCCESSFUL: {user.email}")
                    
                    # CRITICAL: Ensure user is active and has correct status
                    user.is_active = True
                    user.status = 'active'
                    user.save(update_fields=['is_active', 'status'])
                    print(f"✅ USER ACTIVATED: Status={user.status}")
                    
                    # Create activity log
                    UserActivityLog.objects.create(
                        user=user,
                        activity_type='registration',
                        description=f"New registration: {user.email}",
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        metadata={'user_type': user.user_type}
                    )
                    
                    # Send welcome email (async)
                    self.send_welcome_email(request, user)
                    
                    messages.success(
                        request,
                        _('Registration successful! Welcome to Mushqila.')
                    )
                    
                    # Redirect based on user type
                    return self.redirect_to_dashboard(user)
                    
            except Exception as e:
                print(f"❌ REGISTRATION ERROR: {e}")
                import traceback
                traceback.print_exc()
                
                messages.error(
                    request,
                    _('Registration failed. Please try again or contact support.')
                )
        else:
            # Show form errors
            print(f"❌ FORM ERRORS: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        
        return render(request, self.template_name, {
            'form': form,
            'page_title': _('Register'),
            'site_name': 'Mushqila Travel'
        })
    
    def redirect_to_dashboard(self, user):
        """Redirect user to appropriate dashboard - FIXED"""
        print(f"🔀 REDIRECTING: {user.email} -> {user.user_type}")
        
        # Same logic as login view for consistency
        if user.user_type == 'admin' or user.is_staff or user.is_superuser:
            return redirect('accounts:admin_dashboard')
        elif user.user_type in ['agent', 'super_agent', 'sub_agent', 'corporate']:
            return redirect('accounts:agent_dashboard')
        elif user.user_type == 'supplier':
            return redirect('accounts:supplier_dashboard')
        else:
            return redirect('accounts:dashboard_redirect')
    
    def send_welcome_email(self, request, user):
        """Send welcome email (simplified version)"""
        try:
            subject = _('Welcome to Mushqila Travel!')
            
            # Get dashboard URL based on user type
            if user.user_type == 'admin':
                dashboard_url = request.build_absolute_uri(reverse_lazy('accounts:admin_dashboard'))
            elif user.user_type in ['agent', 'super_agent', 'sub_agent', 'corporate']:
                dashboard_url = request.build_absolute_uri(reverse_lazy('accounts:agent_dashboard'))
            elif user.user_type == 'supplier':
                dashboard_url = request.build_absolute_uri(reverse_lazy('accounts:supplier_dashboard'))
            else:
                dashboard_url = request.build_absolute_uri(reverse_lazy('accounts:dashboard_redirect'))
            
            message = f"""
Dear {user.get_full_name()},

Welcome to Mushqila Travel!

Your account has been created successfully.
Account Type: {user.get_user_type_display()}

Dashboard URL: {dashboard_url}

You can now login and start using our services.

Best regards,
Mushqila Travel Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            
            print(f"✅ Welcome email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Email error: {e}")
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class VerifyEmailView(TemplateView):
    """Email verification instruction view"""
    
    template_name = 'accounts/auth/verify_email.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Verify Email')
        context['support_email'] = getattr(settings, 'SUPPORT_EMAIL', 'support@mushqila.com')
        context['support_phone'] = '+966 50 099 3174'
        return context


class VerifyEmailConfirmView(View):
    """Email verification confirmation"""
    
    def get(self, request, user_id, token):
        try:
            # Get session token data
            session_data = request.session.get(f'verify_email_{user_id}')
            
            if not session_data:
                messages.error(request, _('Verification link has expired.'))
                return redirect('accounts:verify_email')
            
            session_token = session_data.get('token')
            timestamp_str = session_data.get('timestamp')
            
            if not session_token or not timestamp_str:
                messages.error(request, _('Invalid verification link.'))
                return redirect('accounts:verify_email')
            
            # Check token match
            if session_token != token:
                messages.error(request, _('Invalid verification link.'))
                return redirect('accounts:verify_email')
            
            # Check expiration (24 hours)
            try:
                from django.utils.dateparse import parse_datetime
                timestamp = parse_datetime(timestamp_str)
                if timezone.now() - timestamp > timedelta(hours=24):
                    messages.error(request, _('Verification link has expired.'))
                    # Clear expired token
                    del request.session[f'verify_email_{user_id}']
                    return redirect('accounts:verify_email')
            except:
                pass
            
            # Get user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                messages.error(request, _('Invalid user.'))
                return redirect('accounts:verify_email')
            
            # Verify email
            user.email_verified = True
            user.save(update_fields=['email_verified'])
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                activity_type='email_verification',
                description="Email verified successfully",
                ip_address=self.get_client_ip(request)
            )
            
            # Clear session token
            if f'verify_email_{user_id}' in request.session:
                del request.session[f'verify_email_{user_id}']
            
            messages.success(request, _('Email verified successfully! You can now login.'))
            
            # If user is logged in, redirect to appropriate dashboard
            if request.user.is_authenticated and request.user.id == user_id:
                # Use same redirect logic as login
                if request.user.user_type == 'admin' or request.user.is_staff or request.user.is_superuser:
                    return redirect('accounts:admin_dashboard')
                elif request.user.user_type in ['agent', 'super_agent', 'sub_agent', 'corporate']:
                    return redirect('accounts:agent_dashboard')
                elif request.user.user_type == 'supplier':
                    return redirect('accounts:supplier_dashboard')
                else:
                    return redirect('accounts:dashboard_redirect')
            else:
                return redirect('accounts:login')
            
        except Exception as e:
            print(f"❌ Email verification error: {e}")
            messages.error(request, _('An error occurred during verification.'))
            return redirect('accounts:verify_email')
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class VerifyPhoneView(LoginRequiredMixin, FormView):
    """Phone verification view"""
    
    template_name = 'accounts/auth/verify_phone.html'
    form_class = PhoneVerificationForm
    success_url = reverse_lazy('accounts:dashboard_redirect')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if already verified
        if request.user.phone_verified:
            messages.info(request, _('Your phone is already verified.'))
            # Redirect to appropriate dashboard
            if request.user.user_type == 'admin' or request.user.is_staff or request.user.is_superuser:
                return redirect('accounts:admin_dashboard')
            elif request.user.user_type in ['agent', 'super_agent', 'sub_agent', 'corporate']:
                return redirect('accounts:agent_dashboard')
            elif request.user.user_type == 'supplier':
                return redirect('accounts:supplier_dashboard')
            else:
                return redirect('accounts:dashboard_redirect')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Process phone verification"""
        try:
            user = self.request.user
            user.phone_verified = True
            user.save(update_fields=['phone_verified'])
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                activity_type='phone_verification',
                description="Phone number verified",
                ip_address=self.get_client_ip()
            )
            
            messages.success(self.request, _('Phone number verified successfully!'))
            
            # Redirect to appropriate dashboard after verification
            if user.user_type == 'admin' or user.is_staff or user.is_superuser:
                return redirect('accounts:admin_dashboard')
            elif user.user_type in ['agent', 'super_agent', 'sub_agent', 'corporate']:
                return redirect('accounts:agent_dashboard')
            elif user.user_type == 'supplier':
                return redirect('accounts:supplier_dashboard')
            else:
                return super().form_valid(form)
            
        except Exception as e:
            print(f"❌ Phone verification error: {e}")
            messages.error(self.request, _('Verification failed. Please try again.'))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Verify Phone')
        context['phone'] = self.request.user.phone
        context['masked_phone'] = self.mask_phone_number(self.request.user.phone)
        
        # For demo purposes, we'll show a fake code
        context['demo_code'] = ''.join(random.choices(string.digits, k=6))
        
        return context
    
    def mask_phone_number(self, phone):
        """Mask phone number for display"""
        if len(phone) > 6:
            return phone[:4] + '****' + phone[-2:]
        return phone
    
    def send_sms_code(self):
        """Send SMS verification code - Placeholder"""
        code = ''.join(random.choices(string.digits, k=6))
        
        print(f"[SMS] Verification code for {self.request.user.phone}: {code}")
        
        # Log SMS sending
        UserActivityLog.objects.create(
            user=self.request.user,
            activity_type='sms_sent',
            description="SMS verification code sent",
            metadata={'code': code, 'phone': self.request.user.phone}
        )
        
        return code
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class PasswordResetView(FormView):
    """Password reset request view"""
    
    template_name = 'accounts/auth/password_reset.html'
    form_class = PasswordResetForm
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        """Process password reset request"""
        email = form.cleaned_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Generate reset token
            token = str(uuid.uuid4())
            self.request.session[f'password_reset_{user.id}'] = {
                'token': token,
                'timestamp': timezone.now().isoformat()
            }
            
            # Send reset email
            self.send_reset_email(user, token)
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                activity_type='password_reset_requested',
                description="Password reset requested",
                ip_address=self.get_client_ip()
            )
            
            messages.success(
                self.request,
                _('Password reset instructions have been sent to your email.')
            )
            
        except User.DoesNotExist:
            # For security, don't reveal if user exists
            messages.success(
                self.request,
                _('If an account exists with this email, you will receive password reset instructions.')
            )
        
        return super().form_valid(form)
    
    def send_reset_email(self, user, token):
        """Send password reset email"""
        try:
            reset_url = self.request.build_absolute_uri(
                reverse_lazy('accounts:password_reset_confirm', kwargs={
                    'user_id': user.id,
                    'token': token
                })
            )
            
            subject = _('Password Reset Request - Mushqila Travel')
            
            message = f"""
Dear {user.get_full_name()},

You have requested to reset your password for Mushqila Travel.

Please click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email.

Best regards,
Mushqila Travel Team
            """
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #dc3545; 
                  color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; 
                   border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Password Reset Request</h2>
        </div>
        <div class="content">
            <h3>Dear {user.get_full_name()},</h3>
            <p>You have requested to reset your password for Mushqila Travel.</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link in your browser:</p>
            <p><code>{reset_url}</code></p>
            
            <div class="warning">
                <p><strong>⚠️ Important:</strong> This link will expire in 1 hour.</p>
                <p>If you did not request a password reset, please ignore this email.</p>
            </div>
        </div>
        <div class="footer">
            <p>Best regards,<br>Mushqila Travel Team</p>
            <p>Phone: +966 50 099 3174<br>Email: support@mushqila.com</p>
        </div>
    </div>
</body>
</html>
            """
            
            send_mail(
                subject=subject,
                message=message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"❌ Failed to send reset email: {e}")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Reset Password')
        context['show_login_link'] = True
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class PasswordResetConfirmView(FormView):
    """Password reset confirmation view"""
    
    template_name = 'accounts/auth/password_reset_confirm.html'
    form_class = PasswordResetConfirmForm
    success_url = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        """Verify reset token before processing"""
        self.user_id = kwargs.get('user_id')
        self.token = kwargs.get('token')
        
        # Verify token
        session_data = request.session.get(f'password_reset_{self.user_id}')
        
        if not session_data:
            messages.error(request, _('Invalid or expired reset link.'))
            return redirect('accounts:password_reset')
        
        session_token = session_data.get('token')
        timestamp_str = session_data.get('timestamp')
        
        if not session_token or not timestamp_str:
            messages.error(request, _('Invalid reset link.'))
            return redirect('accounts:password_reset')
        
        # Check token match
        if session_token != self.token:
            messages.error(request, _('Invalid reset link.'))
            return redirect('accounts:password_reset')
        
        # Check expiration (1 hour)
        try:
            from django.utils.dateparse import parse_datetime
            timestamp = parse_datetime(timestamp_str)
            if timezone.now() - timestamp > timedelta(hours=1):
                messages.error(request, _('Reset link has expired.'))
                # Clear expired token
                if f'password_reset_{self.user_id}' in request.session:
                    del request.session[f'password_reset_{self.user_id}']
                return redirect('accounts:password_reset')
        except:
            pass
        
        # Get user
        try:
            self.user = User.objects.get(id=self.user_id, is_active=True)
        except User.DoesNotExist:
            messages.error(request, _('Invalid user.'))
            return redirect('accounts:password_reset')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Process password reset"""
        try:
            # Set new password
            self.user.set_password(form.cleaned_data['new_password1'])
            self.user.save()
            
            # Clear session token
            if f'password_reset_{self.user_id}' in self.request.session:
                del self.request.session[f'password_reset_{self.user_id}']
            
            # Log activity
            UserActivityLog.objects.create(
                user=self.user,
                activity_type='password_reset_completed',
                description="Password reset successful",
                ip_address=self.get_client_ip()
            )
            
            messages.success(
                self.request, 
                _('Password reset successful! Please login with your new password.')
            )
            
            return super().form_valid(form)
            
        except Exception as e:
            print(f"❌ Password reset error: {e}")
            messages.error(self.request, _('An error occurred. Please try again.'))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Set New Password')
        context['user'] = self.user
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class TwoFactorView(LoginRequiredMixin, FormView):
    """Two-factor authentication view"""
    
    template_name = 'accounts/auth/two_factor.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Two-Factor Authentication')
        return context


# Custom Error Handlers
def custom_404_view(request, exception):
    """Custom 404 error page"""
    return render(request, 'accounts/404.html', status=404)


def custom_500_view(request):
    """Custom 500 error page"""
    return render(request, 'accounts/500.html', status=500)


def custom_403_view(request, exception):
    """Custom 403 error page"""
    return render(request, 'accounts/403.html', status=403)


def custom_400_view(request, exception):
    """Custom 400 error page"""
    return render(request, 'accounts/400.html', status=400)


# Additional utility views
class CheckAuthView(View):
    """Check authentication status - for AJAX calls"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return JsonResponse({
                'authenticated': True,
                'user': {
                    'id': request.user.id,
                    'email': request.user.email,
                    'user_type': request.user.user_type,
                    'full_name': request.user.get_full_name()
                }
            })
        return JsonResponse({'authenticated': False})


class CheckUserExistsView(View):
    """Check if user exists - for registration validation"""
    
    def post(self, request):
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        exists = False
        details = {}
        
        if email:
            exists = User.objects.filter(email=email).exists()
            if exists:
                details['email'] = 'Email already registered'
        
        if phone:
            phone_exists = User.objects.filter(phone=phone).exists()
            if phone_exists:
                exists = True
                details['phone'] = 'Phone number already registered'
        
        return JsonResponse({
            'exists': exists,
            'details': details
        })