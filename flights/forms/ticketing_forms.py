# flights/forms/ticketing_forms.py
"""
Ticketing Forms for B2B Travel Platform
Production Ready - Final Version
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from flights.models import Ticket, Payment


class TicketSearchForm(forms.Form):
    """Form for searching tickets"""
    ticket_number = forms.CharField(
        label=_('Ticket Number'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ticket number',
        })
    )
    
    pnr = forms.CharField(
        label=_('PNR'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter PNR',
        })
    )
    
    passenger_name = forms.CharField(
        label=_('Passenger Name'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter passenger name',
        })
    )
    
    status = forms.ChoiceField(
        label=_('Status'),
        required=False,
        choices=[
            ('', 'All'),
            ('active', 'Active'),
            ('voided', 'Voided'),
            ('reissued', 'Reissued'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TicketFilterForm(forms.Form):
    """Form for filtering tickets"""
    date_from = forms.DateField(
        label=_('From Date'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    date_to = forms.DateField(
        label=_('To Date'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    airline = forms.CharField(
        label=_('Airline'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Airline Code',
        })
    )


class TicketIssueForm(forms.Form):
    """Form for issuing tickets"""
    booking_id = forms.IntegerField(
        label=_('Booking ID'),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    passenger_id = forms.IntegerField(
        label=_('Passenger ID'),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    ticket_number = forms.CharField(
        label=_('Ticket Number'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class TicketVoidForm(forms.Form):
    """Form for voiding tickets"""
    ticket_id = forms.IntegerField(
        label=_('Ticket ID'),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    reason = forms.CharField(
        label=_('Reason'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
        })
    )


class TicketReissueForm(forms.Form):
    """Form for reissuing tickets"""
    original_ticket_id = forms.IntegerField(
        label=_('Original Ticket ID'),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    new_ticket_number = forms.CharField(
        label=_('New Ticket Number'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class TicketRefundForm(forms.Form):
    """Form for refunding tickets"""
    ticket_id = forms.IntegerField(
        label=_('Ticket ID'),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    refund_amount = forms.DecimalField(
        label=_('Refund Amount'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
        })
    )
    
    reason = forms.CharField(
        label=_('Reason'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
        })
    )


class TicketDocumentForm(forms.Form):
    """Form for uploading ticket documents"""
    document = forms.FileField(
        label=_('Document'),
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    document_type = forms.ChoiceField(
        label=_('Document Type'),
        choices=[
            ('invoice', 'Invoice'),
            ('receipt', 'Receipt'),
            ('eticket', 'E-Ticket'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TicketQueueForm(forms.Form):
    """Form for managing ticket queue"""
    status = forms.ChoiceField(
        label=_('Status'),
        choices=[
            ('pending', 'Pending'),
            ('processed', 'Processed'),
            ('failed', 'Failed'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TicketingRuleForm(forms.Form):
    """Form for ticketing rules"""
    rule_name = forms.CharField(
        label=_('Rule Name'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        label=_('Description'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
        })
    )


class BulkTicketingForm(forms.Form):
    """Form for bulk ticketing operations"""
    file = forms.FileField(
        label=_('Upload File'),
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    operation = forms.ChoiceField(
        label=_('Operation'),
        choices=[
            ('issue', 'Issue'),
            ('void', 'Void'),
            ('reissue', 'Reissue'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TicketVerificationForm(forms.Form):
    """Form for verifying tickets"""
    ticket_number = forms.CharField(
        label=_('Ticket Number'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    verification_code = forms.CharField(
        label=_('Verification Code'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class EMDCreateForm(forms.Form):
    """Form for creating EMDs (Excess Mileage Documents)"""
    ticket_id = forms.IntegerField(
        label=_('Ticket ID'),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    emde_amount = forms.DecimalField(
        label=_('EMD Amount'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
        })
    )
    
    purpose = forms.CharField(
        label=_('Purpose'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
        })
    )


class TicketRevalidationForm(forms.Form):
    """Form for revalidating tickets"""
    ticket_id = forms.IntegerField(
        label=_('Ticket ID'),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    new_expiry_date = forms.DateField(
        label=_('New Expiry Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    reason = forms.CharField(
        label=_('Reason'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
        })
    )
