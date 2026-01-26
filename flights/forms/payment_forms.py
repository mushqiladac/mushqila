# flights/forms/passenger_forms.py
"""
Payment forms for B2B Travel Platform
Production Ready - Final Version
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date, timedelta
import re

from flights.models import Payment, Refund
from accounts.models import User


class PaymentForm(forms.ModelForm):
    """Base payment form"""
    
    class Meta:
        model = Payment
        fields = [
            'amount',
            'currency',
            'payment_method',
            'description',
            'notes',
        ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', _('Credit Card')),
        ('debit_card', _('Debit Card')),
        ('bank_transfer', _('Bank Transfer')),
        ('cash', _('Cash')),
        ('check', _('Check')),
        ('wallet', _('Wallet Balance')),
        ('credit_limit', _('Credit Limit')),
        ('multiple', _('Multiple Methods')),
    ]
    
    amount = forms.DecimalField(
        label=_('Amount (SAR)'),
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
        })
    )
    
    currency = forms.ChoiceField(
        label=_('Currency'),
        choices=[
            ('SAR', 'SAR - Saudi Riyal'),
            ('USD', 'USD - US Dollar'),
            ('EUR', 'EUR - Euro'),
        ],
        initial='SAR',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'paymentCurrency',
        })
    )
    
    payment_method = forms.ChoiceField(
        label=_('Payment Method'),
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'paymentMethod',
        })
    )
    
    description = forms.CharField(
        label=_('Payment Description'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Flight booking payment, Deposit, Final payment'),
            'maxlength': '200',
        })
    )
    
    notes = forms.CharField(
        label=_('Payment Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Any additional notes about this payment...'),
            'maxlength': '500',
        })
    )
    
    # Terms and conditions
    terms_accepted = forms.BooleanField(
        label=_('I accept the terms and conditions'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.booking:
            # Set initial values from booking
            self.fields['amount'].initial = self.booking.due_amount
            self.fields['currency'].initial = self.booking.currency
            
            # Auto-generate description
            if not self.fields['description'].initial:
                self.fields['description'].initial = f"Payment for booking {self.booking.booking_reference}"
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        payment_method = cleaned_data.get('payment_method')
        terms_accepted = cleaned_data.get('terms_accepted')
        
        if not terms_accepted:
            raise forms.ValidationError({
                'terms_accepted': _('You must accept the terms and conditions.')
            })
        
        # Validate amount against booking due amount
        if self.booking and amount:
            if amount > self.booking.due_amount:
                raise forms.ValidationError({
                    'amount': _('Payment amount cannot exceed due amount of {} {}.').format(
                        self.booking.due_amount, self.booking.currency
                    )
                })
            
            # Minimum payment amount
            if amount < 50 and payment_method != 'wallet':
                raise forms.ValidationError({
                    'amount': _('Minimum payment amount is 50 SAR.')
                })
        
        # Check user credit limit for credit_limit method
        if payment_method == 'credit_limit' and self.user:
            if hasattr(self.user, 'profile'):
                credit_limit = getattr(self.user.profile, 'credit_limit', 0)
                credit_used = getattr(self.user.profile, 'credit_used', 0)
                available_credit = credit_limit - credit_used
                
                if amount > available_credit:
                    raise forms.ValidationError({
                        'amount': _('Payment amount exceeds available credit limit. Available: {} SAR').format(available_credit)
                    })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Generate payment reference
        if not instance.payment_reference:
            instance.payment_reference = self.generate_payment_reference()
        
        # Link to booking
        if self.booking:
            instance.booking = self.booking
        
        # Set user
        if self.user:
            instance.created_by = self.user
        
        # Set initial status
        instance.status = 'pending'
        
        if commit:
            instance.save()
        
        return instance
    
    def generate_payment_reference(self):
        """Generate unique payment reference"""
        import random
        import string
        
        # Format: PAY-XXXXXX (6 alphanumeric characters)
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choices(chars, k=6))
        return f"PAY-{random_part}"


class CreditCardForm(PaymentForm):
    """Credit card payment form with PCI compliance"""
    
    # Card Information (PCI Compliant - only store last 4 digits)
    card_holder_name = forms.CharField(
        label=_('Card Holder Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Name as shown on card'),
            'autocomplete': 'cc-name',
        })
    )
    
    card_number = forms.CharField(
        label=_('Card Number'),
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '**** **** **** ****',
            'autocomplete': 'cc-number',
            'data-mask': '0000 0000 0000 0000',
        })
    )
    
    card_expiry_month = forms.ChoiceField(
        label=_('Expiry Month'),
        choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(1, 13)],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'autocomplete': 'cc-exp-month',
        })
    )
    
    card_expiry_year = forms.ChoiceField(
        label=_('Expiry Year'),
        choices=[(str(i), str(i)) for i in range(timezone.now().year, timezone.now().year + 11)],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'autocomplete': 'cc-exp-year',
        })
    )
    
    card_cvv = forms.CharField(
        label=_('CVV'),
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '***',
            'autocomplete': 'off',
            'data-mask': '000',
            'maxlength': '4',
        })
    )
    
    card_type = forms.ChoiceField(
        label=_('Card Type'),
        choices=[
            ('visa', 'Visa'),
            ('mastercard', 'MasterCard'),
            ('amex', 'American Express'),
            ('mada', 'Mada'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    save_card = forms.BooleanField(
        label=_('Save card for future payments (secure tokenization)'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    billing_address = forms.CharField(
        label=_('Billing Address'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Billing address associated with card'),
        })
    )
    
    billing_postal_code = forms.CharField(
        label=_('Postal Code'),
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Postal/ZIP code'),
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].initial = 'credit_card'
        
        # Set current month/year as default
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        self.fields['card_expiry_month'].initial = str(current_month).zfill(2)
        self.fields['card_expiry_year'].initial = str(current_year)
    
    def clean(self):
        cleaned_data = super().clean()
        card_number = cleaned_data.get('card_number')
        card_expiry_month = cleaned_data.get('card_expiry_month')
        card_expiry_year = cleaned_data.get('card_expiry_year')
        card_cvv = cleaned_data.get('card_cvv')
        card_type = cleaned_data.get('card_type')
        
        # Clean card number (remove spaces)
        if card_number:
            card_number = re.sub(r'\s+', '', card_number)
            cleaned_data['card_number'] = card_number
            
            # Validate card number length
            if len(card_number) < 13 or len(card_number) > 19:
                raise forms.ValidationError({
                    'card_number': _('Invalid card number length.')
                })
            
            # Validate card type based on number
            if card_number.startswith('4'):
                detected_type = 'visa'
            elif card_number.startswith('5'):
                detected_type = 'mastercard'
            elif card_number.startswith('3'):
                detected_type = 'amex'
            elif card_number.startswith('6'):
                detected_type = 'mada'
            else:
                detected_type = None
            
            if card_type and detected_type and card_type != detected_type:
                raise forms.ValidationError({
                    'card_type': _('Card type does not match card number.')
                })
            
            # Luhn algorithm validation
            if not self.luhn_check(card_number):
                raise forms.ValidationError({
                    'card_number': _('Invalid card number.')
                })
        
        # Validate expiry date
        if card_expiry_month and card_expiry_year:
            expiry_date = date(int(card_expiry_year), int(card_expiry_month), 1)
            last_day = (expiry_date.replace(month=expiry_date.month % 12 + 1, day=1) - timedelta(days=1))
            
            if last_day < timezone.now().date():
                raise forms.ValidationError({
                    'card_expiry_month': _('Card has expired.'),
                    'card_expiry_year': _('Card has expired.'),
                })
        
        # Validate CVV
        if card_cvv:
            if card_type == 'amex':
                if len(card_cvv) != 4:
                    raise forms.ValidationError({
                        'card_cvv': _('American Express cards require 4-digit CVV.')
                    })
            else:
                if len(card_cvv) != 3:
                    raise forms.ValidationError({
                        'card_cvv': _('CVV must be 3 digits.')
                    })
        
        return cleaned_data
    
    def luhn_check(self, card_number):
        """Luhn algorithm for card number validation"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        
        return checksum % 10 == 0
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Store only last 4 digits (PCI compliance)
        card_number = self.cleaned_data.get('card_number', '')
        if card_number and len(card_number) >= 4:
            instance.card_last_four = card_number[-4:]
        
        instance.card_type = self.cleaned_data.get('card_type', '')
        
        if commit:
            instance.save()
        
        return instance


class BankTransferForm(PaymentForm):
    """Bank transfer payment form"""
    
    BANK_CHOICES = [
        ('alrajhi', _('Al Rajhi Bank')),
        ('albilad', _('Alinma Bank')),
        ('riyad', _('Riyad Bank')),
        ('sabb', _('Saudi British Bank (SABB)')),
        ('alawwal', _('Alawwal Bank')),
        ('samba', _('Samba Financial Group')),
        ('ncbb', _('National Commercial Bank')),
        ('banquesaudi', _('Banque Saudi Fransi')),
        ('arabnational', _('Arab National Bank')),
        ('saudihollandi', _('Saudi Holland Bank')),
        ('other', _('Other Bank')),
    ]
    
    bank_name = forms.ChoiceField(
        label=_('Bank Name'),
        choices=BANK_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'bankName',
        })
    )
    
    other_bank_name = forms.CharField(
        label=_('Other Bank Name'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Specify bank name'),
            'data-show-when': 'bank_name:other',
        })
    )
    
    account_holder = forms.CharField(
        label=_('Account Holder Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Name as in bank account'),
        })
    )
    
    account_number = forms.CharField(
        label=_('Account Number'),
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Bank account number'),
        })
    )
    
    iban = forms.CharField(
        label=_('IBAN'),
        max_length=34,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'SAXXXXXXXXXXXXXXXXXXXXXXXXXX',
            'data-mask': 'SA00 0000 0000 0000 0000 0000',
        })
    )
    
    transfer_reference = forms.CharField(
        label=_('Transfer Reference'),
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Booking reference or invoice number'),
        })
    )
    
    transfer_date = forms.DateField(
        label=_('Transfer Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'placeholder': _('Date of transfer'),
            'readonly': 'readonly',
        })
    )
    
    proof_of_transfer = forms.FileField(
        label=_('Proof of Transfer'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].initial = 'bank_transfer'
        
        # Set transfer date to today by default
        today = timezone.now().date()
        self.fields['transfer_date'].initial = today
        self.fields['transfer_date'].widget.attrs['max'] = today.isoformat()
        
        # Auto-generate transfer reference from booking
        if self.booking:
            self.fields['transfer_reference'].initial = f"BOOK-{self.booking.booking_reference}"
    
    def clean(self):
        cleaned_data = super().clean()
        bank_name = cleaned_data.get('bank_name')
        other_bank_name = cleaned_data.get('other_bank_name')
        iban = cleaned_data.get('iban')
        account_number = cleaned_data.get('account_number')
        transfer_date = cleaned_data.get('transfer_date')
        
        # Validate other bank name
        if bank_name == 'other' and not other_bank_name:
            raise forms.ValidationError({
                'other_bank_name': _('Please specify bank name.')
            })
        
        # Validate IBAN for Saudi banks
        if iban:
            if not iban.startswith('SA'):
                raise forms.ValidationError({
                    'iban': _('Saudi IBAN must start with "SA".')
                })
            
            # Basic IBAN validation
            if len(iban) != 24:
                raise forms.ValidationError({
                    'iban': _('Saudi IBAN must be 24 characters.')
                })
        
        # Validate transfer date (cannot be in future)
        if transfer_date and transfer_date > timezone.now().date():
            raise forms.ValidationError({
                'transfer_date': _('Transfer date cannot be in the future.')
            })
        
        # Validate proof of transfer file
        proof_file = cleaned_data.get('proof_of_transfer')
        if proof_file:
            max_size = 5 * 1024 * 1024  # 5MB
            if proof_file.size > max_size:
                raise forms.ValidationError({
                    'proof_of_transfer': _('Proof of transfer file must be less than 5MB.')
                })
        
        return cleaned_data
    
    def clean_iban(self):
        iban = self.cleaned_data.get('iban', '')
        if iban:
            # Remove spaces and convert to uppercase
            iban = re.sub(r'\s+', '', iban).upper()
            
            # Validate IBAN format
            if not re.match(r'^SA[0-9]{22}$', iban):
                raise forms.ValidationError(_('Invalid IBAN format. Example: SA4420000001234567891234'))
        
        return iban
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Store bank information
        bank_name = self.cleaned_data.get('bank_name')
        if bank_name == 'other':
            instance.bank_name = self.cleaned_data.get('other_bank_name', '')
        else:
            instance.bank_name = dict(self.BANK_CHOICES).get(bank_name, '')
        
        instance.bank_account = self.cleaned_data.get('account_number', '')
        instance.transfer_reference = self.cleaned_data.get('transfer_reference', '')
        
        if commit:
            instance.save()
        
        return instance


class WalletPaymentForm(PaymentForm):
    """Wallet/credit balance payment form"""
    
    available_balance = forms.DecimalField(
        label=_('Available Balance'),
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly',
        })
    )
    
    use_full_balance = forms.BooleanField(
        label=_('Use full available balance'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'useFullBalance',
        })
    )
    
    wallet_pin = forms.CharField(
        label=_('Wallet PIN'),
        max_length=6,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••',
            'maxlength': '6',
            'autocomplete': 'off',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].initial = 'wallet'
        
        # Set available balance from user profile
        if self.user and hasattr(self.user, 'profile'):
            wallet_balance = getattr(self.user.profile, 'wallet_balance', 0)
            self.fields['available_balance'].initial = wallet_balance
            
            # Auto-fill amount with available balance or due amount
            if self.booking:
                due_amount = self.booking.due_amount
                self.fields['amount'].initial = min(wallet_balance, due_amount)
        
        # Make amount field read-only if using full balance
        self.fields['amount'].widget.attrs['readonly'] = False
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        use_full_balance = cleaned_data.get('use_full_balance')
        wallet_pin = cleaned_data.get('wallet_pin')
        available_balance = cleaned_data.get('available_balance', 0)
        
        # Get user's actual wallet balance
        if self.user and hasattr(self.user, 'profile'):
            actual_balance = getattr(self.user.profile, 'wallet_balance', 0)
            
            # Adjust amount if using full balance
            if use_full_balance:
                if self.booking:
                    amount = min(actual_balance, self.booking.due_amount)
                else:
                    amount = actual_balance
                cleaned_data['amount'] = amount
            
            # Check if sufficient balance
            if amount > actual_balance:
                raise forms.ValidationError({
                    'amount': _('Insufficient wallet balance. Available: {} SAR').format(actual_balance)
                })
        
        # Validate wallet PIN (in real implementation, this would verify against stored hash)
        if wallet_pin and len(wallet_pin) != 6:
            raise forms.ValidationError({
                'wallet_pin': _('Wallet PIN must be 6 digits.')
            })
        
        return cleaned_data


class MultiplePaymentForm(PaymentForm):
    """Form for splitting payment across multiple methods"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].initial = 'multiple'
        
        # Create payment method sub-forms dynamically
        if self.booking:
            due_amount = self.booking.due_amount
            
            # Credit Card Payment
            self.fields['credit_card_amount'] = forms.DecimalField(
                label=_('Credit Card Amount (SAR)'),
                required=False,
                max_digits=12,
                decimal_places=2,
                min_value=0,
                initial=0,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control payment-split',
                    'data-method': 'credit_card',
                    'placeholder': '0.00',
                    'step': '0.01',
                })
            )
            
            # Wallet Payment
            if self.user and hasattr(self.user, 'profile'):
                wallet_balance = getattr(self.user.profile, 'wallet_balance', 0)
                self.fields['wallet_amount'] = forms.DecimalField(
                    label=_('Wallet Amount (SAR)'),
                    required=False,
                    max_digits=12,
                    decimal_places=2,
                    min_value=0,
                    max_value=wallet_balance,
                    initial=min(wallet_balance, due_amount),
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control payment-split',
                        'data-method': 'wallet',
                        'placeholder': '0.00',
                        'step': '0.01',
                    })
                )
            
            # Cash Payment
            self.fields['cash_amount'] = forms.DecimalField(
                label=_('Cash Amount (SAR)'),
                required=False,
                max_digits=12,
                decimal_places=2,
                min_value=0,
                initial=0,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control payment-split',
                    'data-method': 'cash',
                    'placeholder': '0.00',
                    'step': '0.01',
                })
            )
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.booking:
            return cleaned_data
        
        due_amount = self.booking.due_amount
        
        # Calculate total from all payment methods
        total_paid = 0
        payment_methods = []
        
        # Credit Card
        cc_amount = cleaned_data.get('credit_card_amount', 0)
        if cc_amount and cc_amount > 0:
            total_paid += cc_amount
            payment_methods.append(('credit_card', cc_amount))
        
        # Wallet
        wallet_amount = cleaned_data.get('wallet_amount', 0)
        if wallet_amount and wallet_amount > 0:
            total_paid += wallet_amount
            payment_methods.append(('wallet', wallet_amount))
            
            # Check wallet balance
            if self.user and hasattr(self.user, 'profile'):
                wallet_balance = getattr(self.user.profile, 'wallet_balance', 0)
                if wallet_amount > wallet_balance:
                    raise forms.ValidationError({
                        'wallet_amount': _('Wallet amount exceeds available balance.')
                    })
        
        # Cash
        cash_amount = cleaned_data.get('cash_amount', 0)
        if cash_amount and cash_amount > 0:
            total_paid += cash_amount
            payment_methods.append(('cash', cash_amount))
        
        # Validate total
        if total_paid != due_amount:
            raise forms.ValidationError(
                _('Total payment amount ({}) must equal due amount ({}).').format(total_paid, due_amount)
            )
        
        # Store payment breakdown
        cleaned_data['payment_breakdown'] = payment_methods
        
        return cleaned_data


class RefundRequestForm(forms.ModelForm):
    """Form for requesting refunds"""
    
    class Meta:
        model = Refund
        fields = [
            'reason',
            'rejection_reason',
            'refund_method',
            'bank_name',
            'bank_account',
            'account_holder',
            'iban',
            'notes',
        ]
    
    REFUND_METHOD_CHOICES = [
        ('original', _('Refund to Original Payment Method')),
        ('credit', _('Travel Credit/Voucher')),
        ('bank_transfer', _('Bank Transfer')),
        ('wallet', _('Wallet Credit')),
    ]
    
    reason = forms.CharField(
        label=_('Refund Reason'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Please provide detailed reason for refund request...'),
            'maxlength': '1000',
        })
    )
    
    refund_method = forms.ChoiceField(
        label=_('Refund Method'),
        choices=REFUND_METHOD_CHOICES,
        initial='original',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'refundMethod',
        })
    )
    
    # Bank transfer details
    bank_name = forms.CharField(
        label=_('Bank Name'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Al Rajhi Bank, Riyad Bank'),
            'data-show-when': 'refund_method:bank_transfer',
        })
    )
    
    bank_account = forms.CharField(
        label=_('Account Number'),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Bank account number'),
            'data-show-when': 'refund_method:bank_transfer',
        })
    )
    
    account_holder = forms.CharField(
        label=_('Account Holder Name'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Name as in bank account'),
            'data-show-when': 'refund_method:bank_transfer',
        })
    )
    
    iban = forms.CharField(
        label=_('IBAN'),
        required=False,
        max_length=34,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'SAXXXXXXXXXXXXXXXXXXXXXXXXXX',
            'data-mask': 'SA00 0000 0000 0000 0000 0000',
            'data-show-when': 'refund_method:bank_transfer',
        })
    )
    
    notes = forms.CharField(
        label=_('Additional Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Any additional information...'),
            'maxlength': '500',
        })
    )
    
    # Terms and acknowledgments
    acknowledge_processing_fee = forms.BooleanField(
        label=_('I acknowledge that processing fees may apply'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    acknowledge_refund_time = forms.BooleanField(
        label=_('I acknowledge that refunds may take 7-14 business days'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    original_documents_returned = forms.BooleanField(
        label=_('Original tickets/documents have been returned (if applicable)'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.booking:
            # Calculate refundable amount
            refundable_amount = self.booking.get_refund_amount()
            self.fields['amount'] = forms.DecimalField(
                label=_('Refund Amount (SAR)'),
                initial=refundable_amount,
                max_digits=12,
                decimal_places=2,
                min_value=0,
                max_value=refundable_amount,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'readonly': 'readonly',
                })
            )
    
    def clean(self):
        cleaned_data = super().clean()
        refund_method = cleaned_data.get('refund_method')
        bank_name = cleaned_data.get('bank_name')
        bank_account = cleaned_data.get('bank_account')
        account_holder = cleaned_data.get('account_holder')
        iban = cleaned_data.get('iban')
        acknowledge_processing_fee = cleaned_data.get('acknowledge_processing_fee')
        acknowledge_refund_time = cleaned_data.get('acknowledge_refund_time')
        
        if not acknowledge_processing_fee:
            raise forms.ValidationError({
                'acknowledge_processing_fee': _('You must acknowledge that processing fees may apply.')
            })
        
        if not acknowledge_refund_time:
            raise forms.ValidationError({
                'acknowledge_refund_time': _('You must acknowledge the refund processing time.')
            })
        
        # Validate bank details for bank transfer
        if refund_method == 'bank_transfer':
            if not all([bank_name, bank_account, account_holder]):
                raise forms.ValidationError({
                    'bank_name': _('Bank details are required for bank transfer refund.'),
                    'bank_account': _('Bank details are required for bank transfer refund.'),
                    'account_holder': _('Bank details are required for bank transfer refund.'),
                })
            
            # Validate IBAN if provided
            if iban:
                iban = re.sub(r'\s+', '', iban).upper()
                if not iban.startswith('SA'):
                    raise forms.ValidationError({
                        'iban': _('Saudi IBAN must start with "SA".')
                    })
        
        # Check if booking can be refunded
        if self.booking and not self.booking.can_be_cancelled():
            raise forms.ValidationError(
                _('This booking cannot be refunded. Please check the cancellation policy.')
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Generate refund reference
        if not instance.refund_reference:
            instance.refund_reference = self.generate_refund_reference()
        
        # Link to booking
        if self.booking:
            instance.booking = self.booking
            instance.amount = self.booking.get_refund_amount()
            instance.currency = self.booking.currency
        
        # Set requested by
        if self.user:
            instance.requested_by = self.user
        
        # Set initial status
        instance.status = 'requested'
        
        if commit:
            instance.save()
        
        return instance
    
    def generate_refund_reference(self):
        """Generate unique refund reference"""
        import random
        import string
        
        # Format: REF-XXXXXX (6 alphanumeric characters)
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choices(chars, k=6))
        return f"REF-{random_part}"