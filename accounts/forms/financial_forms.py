# accounts/forms/financial_forms.py
"""
Financial forms for B2B Travel Platform - Production Ready
Fixed for Django compatibility
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from ..models import Payment, Refund, Invoice
import re


class PaymentForm(forms.ModelForm):
    """Payment form"""
    
    AMOUNT_CHOICES = [
        ('', _('Select Amount')),
        ('1000', '1,000 SAR'),
        ('5000', '5,000 SAR'),
        ('10000', '10,000 SAR'),
        ('20000', '20,000 SAR'),
        ('50000', '50,000 SAR'),
        ('other', _('Other Amount')),
    ]
    
    amount_option = forms.ChoiceField(
        label=_('Payment Amount'),
        choices=AMOUNT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'amount_option',
            'onchange': 'toggleCustomAmount()'
        })
    )
    
    amount = forms.DecimalField(
        label=_('Custom Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        required=False,
        validators=[MinValueValidator(Decimal('100.00'))],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'custom_amount',
            'step': '0.01',
            'min': '100',
            'placeholder': 'Enter amount in SAR'
        })
    )
    
    payment_method = forms.ChoiceField(
        label=_('Payment Method'),
        choices=Payment.PaymentMethod.choices,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    description = forms.CharField(
        label=_('Payment Description'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Description for this payment...')
        }),
        required=False
    )
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'description']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        if self.invoice:
            self.fields['amount_option'].initial = 'other'
            self.fields['amount'].initial = self.invoice.total_amount - self.invoice.paid_amount
            self.fields['amount'].widget.attrs['readonly'] = True
        
        # Customize payment method choices
        self.fields['payment_method'].choices = [
            (Payment.PaymentMethod.MADA, _('Mada')),
            (Payment.PaymentMethod.VISA, _('Visa')),
            (Payment.PaymentMethod.MASTERCARD, _('MasterCard')),
            (Payment.PaymentMethod.BANK_TRANSFER, _('Bank Transfer')),
            (Payment.PaymentMethod.WALLET, _('Wallet Balance')),
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        amount_option = cleaned_data.get('amount_option')
        custom_amount = cleaned_data.get('amount')
        payment_method = cleaned_data.get('payment_method')
        
        # Determine amount
        amount = Decimal('0.00')
        if amount_option == 'other':
            if not custom_amount:
                self.add_error('amount', _('Please enter payment amount.'))
            else:
                amount = custom_amount
        elif amount_option:
            amount = Decimal(amount_option)
        
        cleaned_data['amount'] = amount
        
        # Validate amount
        if amount < Decimal('100.00'):
            self.add_error('amount', _('Minimum payment amount is 100 SAR.'))
        
        if amount > Decimal('50000.00'):
            self.add_error('amount', _('Maximum payment amount is 50,000 SAR per transaction.'))
        
        # Check wallet balance if paying with wallet
        if payment_method == Payment.PaymentMethod.WALLET and self.user:
            if self.user.wallet_balance < amount:
                self.add_error('payment_method', 
                    _('Insufficient wallet balance. Your balance: %(balance)s SAR') % 
                    {'balance': self.user.wallet_balance}
                )
        
        # Calculate VAT (15%)
        vat_amount = amount * Decimal('0.15')
        total_amount = amount + vat_amount
        
        cleaned_data['vat_amount'] = vat_amount
        cleaned_data['total_amount'] = total_amount
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
        instance.amount = self.cleaned_data.get('amount', Decimal('0.00'))
        instance.vat_amount = self.cleaned_data.get('vat_amount', Decimal('0.00'))
        instance.total_amount = self.cleaned_data.get('total_amount', Decimal('0.00'))
        
        if commit:
            instance.save()
        
        return instance


class DepositForm(forms.Form):
    """Deposit form for wallet"""
    
    deposit_amount = forms.DecimalField(
        label=_('Deposit Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('100.00'),
        max_value=Decimal('100000.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Enter amount in SAR'
        })
    )
    
    deposit_method = forms.ChoiceField(
        label=_('Deposit Method'),
        choices=[
            ('bank_transfer', _('Bank Transfer')),
            ('credit_card', _('Credit Card')),
            ('mada', _('Mada')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    reference_number = forms.CharField(
        label=_('Reference Number'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Bank transfer reference, etc.')
        })
    )
    
    deposit_slip = forms.FileField(
        label=_('Deposit Slip/Proof'),
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        deposit_amount = cleaned_data.get('deposit_amount')
        deposit_method = cleaned_data.get('deposit_method')
        reference_number = cleaned_data.get('reference_number')
        
        if deposit_method == 'bank_transfer' and not reference_number:
            self.add_error('reference_number', 
                _('Reference number is required for bank transfers.')
            )
        
        return cleaned_data


class WithdrawalForm(forms.Form):
    """Withdrawal form from wallet"""
    
    withdrawal_amount = forms.DecimalField(
        label=_('Withdrawal Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Enter amount in SAR'
        })
    )
    
    withdrawal_method = forms.ChoiceField(
        label=_('Withdrawal Method'),
        choices=[
            ('bank_transfer', _('Bank Transfer')),
            ('cheque', _('Cheque')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    bank_account = forms.CharField(
        label=_('Bank Account Details'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Bank name, account number, IBAN, etc.')
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['bank_account'].initial = self.get_user_bank_details()
    
    def get_user_bank_details(self):
        """Get user's bank details from profile"""
        if hasattr(self.user, 'profile'):
            profile = self.user.profile
            details = []
            if profile.bank_name_en:
                details.append(f"Bank: {profile.bank_name_en}")
            if profile.account_number:
                details.append(f"Account: {profile.account_number}")
            if profile.iban:
                details.append(f"IBAN: {profile.iban}")
            return "\n".join(details)
        return ""
    
    def clean_withdrawal_amount(self):
        amount = self.cleaned_data.get('withdrawal_amount')
        
        if amount < Decimal('100.00'):
            raise ValidationError(_('Minimum withdrawal amount is 100 SAR.'))
        
        if amount > Decimal('50000.00'):
            raise ValidationError(_('Maximum withdrawal amount is 50,000 SAR per transaction.'))
        
        # Check wallet balance
        if self.user and amount > self.user.wallet_balance:
            raise ValidationError(
                _('Insufficient wallet balance. Available: %(balance)s SAR') % 
                {'balance': self.user.wallet_balance}
            )
        
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        withdrawal_method = cleaned_data.get('withdrawal_method')
        bank_account = cleaned_data.get('bank_account')
        
        if withdrawal_method == 'bank_transfer' and not bank_account:
            self.add_error('bank_account', 
                _('Bank account details are required for bank transfers.')
            )
        
        return cleaned_data


class RefundRequestForm(forms.ModelForm):
    """Refund request form - FIXED: ClearableFileInput multiple files issue"""
    
    refund_amount = forms.DecimalField(
        label=_('Refund Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Enter refund amount'
        })
    )
    
    refund_method = forms.ChoiceField(
        label=_('Refund Method'),
        choices=Refund.RefundMethod.choices,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    reason = forms.CharField(
        label=_('Reason for Refund'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Please explain why you are requesting a refund...')
        })
    )
    
    # FIX: Using FileInput instead of ClearableFileInput for multiple files
    supporting_documents = forms.FileField(
        label=_('Supporting Documents'),
        required=False,
        widget=forms.FileInput(attrs={  # ✅ Changed from ClearableFileInput to FileInput
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = Refund
        fields = ['refund_method', 'reason']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.booking = kwargs.pop('booking', None)
        self.original_payment = kwargs.pop('original_payment', None)
        super().__init__(*args, **kwargs)
        
        if self.original_payment:
            self.fields['refund_amount'].initial = self.original_payment.amount
    
    def clean_refund_amount(self):
        amount = self.cleaned_data.get('refund_amount')
        
        if self.original_payment and amount > self.original_payment.amount:
            raise ValidationError(
                _('Refund amount cannot exceed original payment of %(payment)s SAR') % 
                {'payment': self.original_payment.amount}
            )
        
        return amount


class InvoiceForm(forms.ModelForm):
    """Invoice form"""
    
    issue_date = forms.DateField(
        label=_('Issue Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    due_date = forms.DateField(
        label=_('Due Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    notes = forms.CharField(
        label=_('Invoice Notes'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Additional notes for this invoice...')
        }),
        required=False
    )
    
    class Meta:
        model = Invoice
        fields = ['issue_date', 'due_date', 'notes']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.booking = kwargs.pop('booking', None)
        super().__init__(*args, **kwargs)
        
        # Set default due date (30 days from today)
        from django.utils import timezone
        import datetime
        today = timezone.now().date()
        self.fields['issue_date'].initial = today
        self.fields['due_date'].initial = today + datetime.timedelta(days=30)
    
    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')
        
        if issue_date and due_date:
            if due_date < issue_date:
                self.add_error('due_date', _('Due date cannot be before issue date.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
        if self.booking:
            instance.flight_booking = self.booking
        
        # Calculate amounts from booking
        if self.booking:
            instance.subtotal = self.booking.base_fare
            instance.vat_amount = self.booking.vat
            instance.total_amount = self.booking.total_amount
        
        if commit:
            instance.save()
        
        return instance


class CreditLimitForm(forms.Form):
    """Credit limit adjustment form (admin only)"""
    
    ACTION_CHOICES = [
        ('increase', _('Increase Credit Limit')),
        ('decrease', _('Decrease Credit Limit')),
        ('set', _('Set New Limit')),
    ]
    
    action = forms.ChoiceField(
        label=_('Action'),
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'onchange': 'toggleAmountFields()'
        })
    )
    
    new_limit = forms.DecimalField(
        label=_('New Credit Limit (SAR)'),
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'id': 'new_limit_field'
        })
    )
    
    adjustment_amount = forms.DecimalField(
        label=_('Adjustment Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'id': 'adjustment_field'
        })
    )
    
    reason = forms.CharField(
        label=_('Reason for Adjustment'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Reason for credit limit adjustment...')
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['new_limit'].help_text = _('Current limit: %(limit)s SAR') % {
                'limit': self.user.credit_limit
            }
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        new_limit = cleaned_data.get('new_limit')
        adjustment_amount = cleaned_data.get('adjustment_amount')
        
        if not self.user:
            raise ValidationError(_('User not specified.'))
        
        current_limit = self.user.credit_limit
        
        if action == 'set':
            if not new_limit:
                self.add_error('new_limit', _('New limit is required.'))
            elif new_limit < Decimal('0.00'):
                self.add_error('new_limit', _('Credit limit cannot be negative.'))
            elif new_limit > Decimal('1000000.00'):
                self.add_error('new_limit', _('Maximum credit limit is 1,000,000 SAR.'))
        
        elif action in ['increase', 'decrease']:
            if not adjustment_amount:
                self.add_error('adjustment_amount', _('Adjustment amount is required.'))
            elif adjustment_amount <= Decimal('0.00'):
                self.add_error('adjustment_amount', _('Adjustment amount must be positive.'))
            
            if action == 'increase':
                new_limit = current_limit + adjustment_amount
                if new_limit > Decimal('1000000.00'):
                    self.add_error('adjustment_amount', 
                        _('Resulting limit would exceed maximum of 1,000,000 SAR.')
                    )
            else:  # decrease
                new_limit = current_limit - adjustment_amount
                if new_limit < Decimal('0.00'):
                    self.add_error('adjustment_amount', 
                        _('Cannot decrease below 0 SAR.')
                    )
        
        cleaned_data['calculated_limit'] = new_limit
        
        return cleaned_data


# Additional financial forms for production

class CommissionForm(forms.Form):
    """Commission calculation form"""
    
    booking_amount = forms.DecimalField(
        label=_('Booking Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        })
    )
    
    commission_rate = forms.DecimalField(
        label=_('Commission Rate (%)'),
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        })
    )
    
    def calculate_commission(self):
        """Calculate commission amount"""
        booking_amount = self.cleaned_data.get('booking_amount', Decimal('0.00'))
        commission_rate = self.cleaned_data.get('commission_rate', Decimal('0.00'))
        
        commission_amount = (booking_amount * commission_rate) / Decimal('100.00')
        return commission_amount


class BankTransferForm(forms.Form):
    """Bank transfer details form"""
    
    bank_name = forms.CharField(
        label=_('Bank Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Al Rajhi Bank, SABB, etc.')
        })
    )
    
    account_name = forms.CharField(
        label=_('Account Holder Name'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Account holder name as in bank records')
        })
    )
    
    account_number = forms.CharField(
        label=_('Account Number'),
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Bank account number')
        })
    )
    
    iban = forms.CharField(
        label=_('IBAN'),
        max_length=34,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('SAXXXXXXXXXXXXXXXXXXXXXXXXXX')
        })
    )
    
    swift_code = forms.CharField(
        label=_('SWIFT/BIC Code'),
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Bank SWIFT code')
        })
    )
    
    def clean_iban(self):
        iban = self.cleaned_data.get('iban', '').strip().upper()
        
        # Basic IBAN validation for Saudi Arabia
        if iban and not iban.startswith('SA'):
            raise ValidationError(_('IBAN must start with "SA" for Saudi Arabia.'))
        
        if iban and len(iban) < 24:
            raise ValidationError(_('IBAN must be at least 24 characters.'))
        
        return iban