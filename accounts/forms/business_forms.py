# accounts/forms/business_forms.py
"""
Business operation forms for B2B Travel Mushqila - Saudi Arabia
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from ..models import Document, CreditRequest, AgentHierarchy, IPWhitelist
import os


class DocumentUploadForm(forms.ModelForm):
    """Document upload form for KYC"""
    
    class Meta:
        model = Document
        fields = ['document_type', 'document_file', 'front_image', 'back_image', 'document_number', 'issue_date', 'expiry_date']
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'document_type'
            }),
            'document_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'front_image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png'
            }),
            'back_image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png'
            }),
            'document_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Document number')
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set allowed file types
        self.fields['document_file'].validators.append(
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])
        )
        self.fields['front_image'].validators.append(
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        )
        self.fields['back_image'].validators.append(
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        )
        
        # Set file size limits (10MB)
        self.fields['document_file'].widget.attrs.update({
            'data-max-size': '10485760'  # 10MB in bytes
        })
    
    def clean_document_file(self):
        document_file = self.cleaned_data.get('document_file')
        
        if document_file:
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if document_file.size > max_size:
                raise ValidationError(_('File size must be less than 10MB.'))
            
            # Check file extension
            ext = os.path.splitext(document_file.name)[1].lower()
            if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                raise ValidationError(_('Only PDF, JPG, JPEG, and PNG files are allowed.'))
        
        return document_file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class CreditRequestForm(forms.ModelForm):
    """Credit limit increase request form"""
    
    purpose = forms.CharField(
        label=_('Purpose of Credit Increase'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Please explain why you need a credit limit increase...')
        }),
        required=True
    )
    
    class Meta:
        model = CreditRequest
        fields = ['current_limit', 'requested_limit', 'purpose']
        widgets = {
            'current_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'step': '0.01'
            }),
            'requested_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['current_limit'].initial = self.user.credit_limit
    
    def clean_requested_limit(self):
        current_limit = self.cleaned_data.get('current_limit')
        requested_limit = self.cleaned_data.get('requested_limit')
        
        if requested_limit <= current_limit:
            raise ValidationError(_('Requested limit must be greater than current limit.'))
        
        # Maximum credit limit check (1,000,000 SAR)
        if requested_limit > 1000000:
            raise ValidationError(_('Maximum credit limit is 1,000,000 SAR.'))
        
        return requested_limit
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
            instance.current_limit = self.user.credit_limit
        if commit:
            instance.save()
        return instance


class AgentHierarchyForm(forms.ModelForm):
    """Agent hierarchy management form"""
    
    parent_agent = forms.ModelChoiceField(
        label=_('Parent Agent'),
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'parent_agent'
        })
    )
    
    child_agent = forms.ModelChoiceField(
        label=_('Child Agent'),
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'child_agent'
        })
    )
    
    commission_share = forms.DecimalField(
        label=_('Commission Share (%)'),
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '10.00'
        })
    )
    
    class Meta:
        model = AgentHierarchy
        fields = ['parent_agent', 'child_agent', 'hierarchy_level', 'commission_share']
        widgets = {
            'hierarchy_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filter agents based on user type
        from ..models import User
        
        if self.request and self.request.user.is_authenticated:
            if self.request.user.user_type == User.UserType.ADMIN:
                # Admin can see all super agents and agents
                self.fields['parent_agent'].queryset = User.objects.filter(
                    user_type__in=[User.UserType.SUPER_AGENT, User.UserType.AGENT],
                    status=User.Status.ACTIVE
                )
                self.fields['child_agent'].queryset = User.objects.filter(
                    user_type__in=[User.UserType.AGENT, User.UserType.SUB_AGENT],
                    status=User.Status.ACTIVE
                ).exclude(
                    pk__in=AgentHierarchy.objects.filter(is_active=True).values_list('child_agent_id', flat=True)
                )
            elif self.request.user.user_type == User.UserType.SUPER_AGENT:
                # Super agent can only assign their sub-agents
                self.fields['parent_agent'].queryset = User.objects.filter(
                    pk=self.request.user.pk
                )
                self.fields['child_agent'].queryset = User.objects.filter(
                    user_type=User.UserType.AGENT,
                    status=User.Status.ACTIVE
                ).exclude(
                    pk__in=AgentHierarchy.objects.filter(is_active=True).values_list('child_agent_id', flat=True)
                )
    
    def clean(self):
        cleaned_data = super().clean()
        parent_agent = cleaned_data.get('parent_agent')
        child_agent = cleaned_data.get('child_agent')
        
        if parent_agent and child_agent:
            if parent_agent == child_agent:
                raise ValidationError(_('Parent and child agent cannot be the same.'))
            
            # Check if hierarchy already exists
            if AgentHierarchy.objects.filter(
                parent_agent=parent_agent,
                child_agent=child_agent,
                is_active=True
            ).exists():
                raise ValidationError(_('This hierarchy relationship already exists.'))
            
            # Check circular hierarchy
            if self.check_circular_hierarchy(parent_agent, child_agent):
                raise ValidationError(_('Circular hierarchy detected.'))
        
        return cleaned_data
    
    def check_circular_hierarchy(self, parent, child):
        """Check for circular hierarchy"""
        # If child is already a parent of the parent somewhere in the hierarchy
        visited = set()
        queue = [child]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # Get all parents of current
            parents = AgentHierarchy.objects.filter(
                child_agent=current,
                is_active=True
            ).values_list('parent_agent_id', flat=True)
            
            if parent.pk in parents:
                return True
            
            for parent_id in parents:
                try:
                    parent_user = User.objects.get(pk=parent_id)
                    queue.append(parent_user)
                except User.DoesNotExist:
                    continue
        
        return False


class IPWhitelistForm(forms.ModelForm):
    """IP whitelist form"""
    
    ip_address = forms.GenericIPAddressField(
        label=_('IP Address'),
        protocol='both',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '192.168.1.1'
        })
    )
    
    description = forms.CharField(
        label=_('Description'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Office IP, VPN, etc.')
        })
    )
    
    class Meta:
        model = IPWhitelist
        fields = ['ip_address', 'description', 'is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_ip_address(self):
        ip_address = self.cleaned_data.get('ip_address')
        
        if self.user and IPWhitelist.objects.filter(
            user=self.user,
            ip_address=ip_address
        ).exists():
            raise ValidationError(_('This IP address is already whitelisted.'))
        
        return ip_address
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class KYCVerificationForm(forms.Form):
    """KYC verification form for admin"""
    
    STATUS_CHOICES = [
        (Document.Status.VERIFIED, _('Verified')),
        (Document.Status.REJECTED, _('Rejected')),
        (Document.Status.EXPIRED, _('Expired')),
    ]
    
    status = forms.ChoiceField(
        label=_('Verification Status'),
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    verification_notes = forms.CharField(
        label=_('Verification Notes'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Add notes about verification...')
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.document = kwargs.pop('document', None)
        super().__init__(*args, **kwargs)
        
        if self.document:
            self.fields['status'].initial = self.document.status
            self.fields['verification_notes'].initial = self.document.verification_notes