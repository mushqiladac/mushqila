from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailAccount

User = get_user_model()


class EmailAccountCreationForm(forms.ModelForm):
    """Form for creating email accounts by superuser"""
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        min_length=8,
        help_text='Password must be at least 8 characters long'
    )
    
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    
    class Meta:
        model = EmailAccount
        fields = [
            'user', 'email_address', 'first_name', 'last_name',
            'display_name', 'mobile_number', 'alternate_email',
            'aws_access_key', 'aws_secret_key', 'aws_region',
            's3_bucket_name', 's3_inbox_prefix', 'signature',
            'is_default', 'is_active', 'ses_verified'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'email_address': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'user@example.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display Name'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+880XXXXXXXXXX'
            }),
            'alternate_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'alternate@example.com'
            }),
            'aws_access_key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'AWS Access Key'
            }),
            'aws_secret_key': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'AWS Secret Key'
            }),
            'aws_region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'us-east-1'
            }),
            's3_bucket_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'S3 Bucket Name'
            }),
            's3_inbox_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'inbox/'
            }),
            'signature': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Email signature'
            }),
        }
    
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match')
        
        return confirm_password
    
    def clean_email_address(self):
        email = self.cleaned_data.get('email_address')
        
        # Check if email already exists (for new accounts)
        if not self.instance.pk:
            if EmailAccount.objects.filter(email_address=email).exists():
                raise ValidationError('This email address is already registered')
        
        return email
    
    def save(self, commit=True):
        account = super().save(commit=False)
        
        # Set hashed password
        password = self.cleaned_data.get('password')
        if password:
            account.set_password(password)
        
        if commit:
            account.save()
        
        return account


class EmailAccountChangeForm(forms.ModelForm):
    """Form for updating email accounts"""
    
    password = forms.CharField(
        label='New Password (leave blank to keep current)',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        required=False,
        min_length=8
    )
    
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        required=False
    )
    
    class Meta:
        model = EmailAccount
        fields = [
            'user', 'email_address', 'first_name', 'last_name',
            'display_name', 'mobile_number', 'alternate_email',
            'aws_access_key', 'aws_secret_key', 'aws_region',
            's3_bucket_name', 's3_inbox_prefix', 'signature',
            'is_default', 'is_active', 'ses_verified'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'email_address': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'user@example.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display Name'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+880XXXXXXXXXX'
            }),
            'alternate_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'alternate@example.com'
            }),
            'aws_access_key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'AWS Access Key'
            }),
            'aws_secret_key': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'AWS Secret Key'
            }),
            'aws_region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'us-east-1'
            }),
            's3_bucket_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'S3 Bucket Name'
            }),
            's3_inbox_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'inbox/'
            }),
            'signature': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Email signature'
            }),
        }
    
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match')
        
        return confirm_password
    
    def save(self, commit=True):
        account = super().save(commit=False)
        
        # Update password only if provided
        password = self.cleaned_data.get('password')
        if password:
            account.set_password(password)
        
        if commit:
            account.save()
        
        return account


class WebmailLoginForm(forms.Form):
    """Login form for webmail using email and password"""
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            try:
                account = EmailAccount.objects.get(email_address=email, is_active=True)
                if not account.check_password(password):
                    raise ValidationError('Invalid email or password')
                
                # Store account in cleaned_data for later use
                cleaned_data['account'] = account
            except EmailAccount.DoesNotExist:
                raise ValidationError('Invalid email or password')
        
        return cleaned_data



class ForgotPasswordForm(forms.Form):
    """Form for requesting password reset"""
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'autofocus': True
        }),
        help_text='Enter your registered email address'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        try:
            account = EmailAccount.objects.get(email_address=email, is_active=True)
            
            # Check if alternate email exists
            if not account.alternate_email:
                raise ValidationError(
                    'No alternate email found for this account. Please contact administrator.'
                )
            
            # Store account in cleaned_data
            self.cleaned_data['account'] = account
            
        except EmailAccount.DoesNotExist:
            raise ValidationError('No active account found with this email address.')
        
        return email
    
    def send_reset_email(self):
        """Generate token and send reset email to alternate email"""
        account = self.cleaned_data.get('account')
        
        if not account:
            return False
        
        # Generate reset token
        token = account.generate_reset_token()
        
        # Prepare email
        subject = 'Webmail Password Reset - Temporary Password'
        message = f"""
Hello {account.first_name or account.display_name},

You have requested a password reset for your webmail account.

Your temporary password is: {token}

This temporary password is valid for 15 minutes only.

Please use this temporary password to login and then change your password immediately.

Login URL: {settings.SITE_URL}/webmail/login/

If you did not request this password reset, please ignore this email.

Best regards,
Mushqila Webmail Team
        """
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .token-box {{ background: white; border: 2px solid #667eea; padding: 20px; margin: 20px 0; text-align: center; border-radius: 10px; }}
        .token {{ font-size: 24px; font-weight: bold; color: #667eea; letter-spacing: 2px; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{account.first_name or account.display_name}</strong>,</p>
            
            <p>You have requested a password reset for your webmail account: <strong>{account.email_address}</strong></p>
            
            <div class="token-box">
                <p style="margin: 0; font-size: 14px; color: #666;">Your Temporary Password:</p>
                <p class="token">{token}</p>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important:</strong>
                <ul style="margin: 10px 0;">
                    <li>This temporary password is valid for <strong>15 minutes only</strong></li>
                    <li>Use it to login and change your password immediately</li>
                    <li>Do not share this password with anyone</li>
                </ul>
            </div>
            
            <div style="text-align: center;">
                <a href="{settings.SITE_URL}/webmail/login/" class="button">Login to Webmail</a>
            </div>
            
            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                If you did not request this password reset, please ignore this email or contact support if you have concerns.
            </p>
            
            <div class="footer">
                <p>Best regards,<br>Mushqila Webmail Team</p>
                <p>&copy; 2024 Mushqila. All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        try:
            # Send email to alternate email address
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[account.alternate_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending reset email: {e}")
            return False


class ResetPasswordForm(forms.Form):
    """Form for resetting password with temporary token"""
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )
    
    temporary_password = forms.CharField(
        label='Temporary Password',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter temporary password from email'
        }),
        help_text='Enter the temporary password sent to your alternate email'
    )
    
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        min_length=8,
        help_text='Password must be at least 8 characters long'
    )
    
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        temporary_password = cleaned_data.get('temporary_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # Check if passwords match
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('New passwords do not match')
        
        # Verify email and token
        if email and temporary_password:
            try:
                account = EmailAccount.objects.get(email_address=email, is_active=True)
                
                # Verify token
                if not account.is_reset_token_valid(temporary_password):
                    raise ValidationError(
                        'Invalid or expired temporary password. Please request a new one.'
                    )
                
                # Store account in cleaned_data
                cleaned_data['account'] = account
                
            except EmailAccount.DoesNotExist:
                raise ValidationError('Invalid email address')
        
        return cleaned_data
    
    def save(self):
        """Reset password and clear token"""
        account = self.cleaned_data.get('account')
        new_password = self.cleaned_data.get('new_password')
        
        if account and new_password:
            # Set new password
            account.set_password(new_password)
            
            # Also update User password
            account.user.set_password(new_password)
            account.user.save()
            
            # Clear reset token
            account.clear_reset_token()
            
            return True
        
        return False
