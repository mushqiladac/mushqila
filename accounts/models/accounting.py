# accounts/models/accounting.py
"""
Automatic Accounting System for B2B Travel Platform
Complete financial accounting for all ticketing operations
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Account(models.Model):
    """Chart of Accounts for double-entry bookkeeping"""

    class AccountType(models.TextChoices):
        ASSET = 'asset', _('Asset')
        LIABILITY = 'liability', _('Liability')
        EQUITY = 'equity', _('Equity')
        REVENUE = 'revenue', _('Revenue')
        EXPENSE = 'expense', _('Expense')

    class AccountCategory(models.TextChoices):
        # Assets
        CASH = 'cash', _('Cash and Cash Equivalents')
        ACCOUNTS_RECEIVABLE = 'receivable', _('Accounts Receivable')
        INVENTORY = 'inventory', _('Inventory')

        # Liabilities
        ACCOUNTS_PAYABLE = 'payable', _('Accounts Payable')
        CUSTOMER_DEPOSITS = 'deposits', _('Customer Deposits')

        # Equity
        RETAINED_EARNINGS = 'retained', _('Retained Earnings')

        # Revenue
        TICKET_REVENUE = 'ticket_revenue', _('Ticket Revenue')
        ANCILLARY_REVENUE = 'ancillary_revenue', _('Ancillary Revenue')
        COMMISSION_REVENUE = 'commission_revenue', _('Commission Revenue')

        # Expenses
        AIRLINE_COSTS = 'airline_costs', _('Airline Ticket Costs')
        PAYMENT_FEES = 'payment_fees', _('Payment Processing Fees')
        REFUND_EXPENSES = 'refund_expenses', _('Refund Processing Expenses')
        COMMISSIONS_PAID = 'commissions_paid', _('Commissions Paid')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(_('Account Code'), max_length=20, unique=True)
    name = models.CharField(_('Account Name'), max_length=255)
    account_type = models.CharField(_('Account Type'), max_length=20, choices=AccountType.choices)
    category = models.CharField(_('Category'), max_length=30, choices=AccountCategory.choices)

    description = models.TextField(_('Description'), blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)

    # Accounting properties
    normal_balance = models.CharField(_('Normal Balance'), max_length=10,
                                    choices=[('debit', _('Debit')), ('credit', _('Credit'))])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_balance(self, as_of_date=None):
        """Calculate account balance as of given date"""
        if as_of_date is None:
            as_of_date = timezone.now().date()

        entries = JournalEntry.objects.filter(
            account=self,
            date__lte=as_of_date
        )

        debit_total = entries.filter(entry_type='debit').aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0.00')
        credit_total = entries.filter(entry_type='credit').aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0.00')

        if self.normal_balance == 'debit':
            return debit_total - credit_total
        else:
            return credit_total - debit_total


class JournalEntry(models.Model):
    """Double-entry accounting journal entries"""

    class EntryType(models.TextChoices):
        DEBIT = 'debit', _('Debit')
        CREDIT = 'credit', _('Credit')

    class TransactionType(models.TextChoices):
        TICKET_ISSUE = 'ticket_issue', _('Ticket Issue')
        TICKET_VOID = 'ticket_void', _('Ticket Void')
        TICKET_CANCEL = 'ticket_cancel', _('Ticket Cancel')
        TICKET_REFUND = 'ticket_refund', _('Ticket Refund')
        PAYMENT_RECEIVED = 'payment_received', _('Payment Received')
        PAYMENT_REFUNDED = 'payment_refunded', _('Payment Refunded')
        COMMISSION_EARNED = 'commission_earned', _('Commission Earned')
        COMMISSION_PAID = 'commission_paid', _('Commission Paid')
        ANCILLARY_SALE = 'ancillary_sale', _('Ancillary Sale')
        ANCILLARY_REFUND = 'ancillary_refund', _('Ancillary Refund')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(_('Date'), default=timezone.now)
    reference_number = models.CharField(_('Reference Number'), max_length=50, unique=True)

    # Transaction details
    transaction_type = models.CharField(_('Transaction Type'), max_length=30,
                                      choices=TransactionType.choices)
    description = models.TextField(_('Description'))

    # Related entities
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    booking = models.ForeignKey('flights.Booking', on_delete=models.CASCADE,
                               related_name='journal_entries', null=True, blank=True)
    ticket = models.ForeignKey('flights.Ticket', on_delete=models.CASCADE,
                              related_name='journal_entries', null=True, blank=True)
    payment = models.ForeignKey('flights.Payment', on_delete=models.CASCADE,
                               related_name='journal_entries', null=True, blank=True)

    # Accounting entry
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='entries')
    entry_type = models.CharField(_('Entry Type'), max_length=10, choices=EntryType.choices)
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2,
                               validators=[MinValueValidator(Decimal('0.01'))])

    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  related_name='created_entries')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Journal Entry')
        verbose_name_plural = _('Journal Entries')
        ordering = ['-date', '-created_at']
        unique_together = ['reference_number']

    def __str__(self):
        return f"{self.reference_number} - {self.get_transaction_type_display()} - {self.amount}"


class AccountingPeriod(models.Model):
    """Accounting periods for financial reporting"""

    class PeriodStatus(models.TextChoices):
        OPEN = 'open', _('Open')
        CLOSED = 'closed', _('Closed')
        LOCKED = 'locked', _('Locked')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Period Name'), max_length=100)
    start_date = models.DateField(_('Start Date'))
    end_date = models.DateField(_('End Date'))
    status = models.CharField(_('Status'), max_length=10, choices=PeriodStatus.choices,
                            default=PeriodStatus.OPEN)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Accounting Period')
        verbose_name_plural = _('Accounting Periods')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class AccountingRule(models.Model):
    """Automated accounting rules for different transaction types"""

    class RuleType(models.TextChoices):
        TICKET_ISSUE = 'ticket_issue', _('Ticket Issue')
        TICKET_VOID = 'ticket_void', _('Ticket Void')
        TICKET_CANCEL = 'ticket_cancel', _('Ticket Cancel')
        TICKET_REFUND = 'ticket_refund', _('Ticket Refund')
        PAYMENT_RECEIVED = 'payment_received', _('Payment Received')
        COMMISSION_EARNED = 'commission_earned', _('Commission Earned')
        ANCILLARY_SALE = 'ancillary_sale', _('Ancillary Sale')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Rule Name'), max_length=255)
    rule_type = models.CharField(_('Rule Type'), max_length=30, choices=RuleType.choices, unique=True)
    description = models.TextField(_('Description'), blank=True)

    # Debit entries (JSON format: [{"account_code": "1001", "amount_field": "total_amount"}])
    debit_entries = models.JSONField(_('Debit Entries'), default=list)

    # Credit entries (JSON format: [{"account_code": "4001", "amount_field": "total_amount"}])
    credit_entries = models.JSONField(_('Credit Entries'), default=list)

    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Accounting Rule')
        verbose_name_plural = _('Accounting Rules')
        ordering = ['rule_type']

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class FinancialReport(models.Model):
    """Generated financial reports"""

    class ReportType(models.TextChoices):
        PROFIT_LOSS = 'profit_loss', _('Profit & Loss Statement')
        BALANCE_SHEET = 'balance_sheet', _('Balance Sheet')
        CASH_FLOW = 'cash_flow', _('Cash Flow Statement')
        TRIAL_BALANCE = 'trial_balance', _('Trial Balance')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(_('Report Type'), max_length=20, choices=ReportType.choices)
    name = models.CharField(_('Report Name'), max_length=255)
    period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE, related_name='reports')

    # Report data (JSON format)
    data = models.JSONField(_('Report Data'))

    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Financial Report')
        verbose_name_plural = _('Financial Reports')
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.name} - {self.period}"