# accounts/services/automated_accounting_service.py
"""
Automated Accounting Service
Handles automatic posting of transactions to accounting system
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AutomatedAccountingService:
    """
    Service for automated accounting entries
    Implements double-entry bookkeeping for all transactions
    """
    
    def __init__(self):
        from accounts.models.accounting import Account, AccountingRule
        self.Account = Account
        self.AccountingRule = AccountingRule
    
    def post_ticket_issue(self, transaction_log):
        """
        Post ticket issue to accounting
        
        Debit: Accounts Receivable (Asset)
        Credit: Ticket Revenue (Revenue)
        Credit: Tax Payable (Liability)
        """
        try:
            with transaction.atomic():
                from accounts.models.accounting import JournalEntry
                
                reference = self._generate_reference('TI', transaction_log.id)
                
                # Get accounts
                receivable_account = self.Account.objects.get(code='1200')  # Accounts Receivable
                revenue_account = self.Account.objects.get(code='4001')     # Ticket Revenue
                tax_account = self.Account.objects.get(code='2100')         # Tax Payable
                
                # Debit: Accounts Receivable (Total Amount)
                JournalEntry.objects.create(
                    date=transaction_log.transaction_date.date(),
                    reference_number=reference,
                    transaction_type='ticket_issue',
                    description=transaction_log.description,
                    user=transaction_log.agent,
                    booking=transaction_log.booking,
                    account=receivable_account,
                    entry_type='debit',
                    amount=transaction_log.total_amount
                )
                
                # Credit: Ticket Revenue (Base Amount)
                JournalEntry.objects.create(
                    date=transaction_log.transaction_date.date(),
                    reference_number=reference,
                    transaction_type='ticket_issue',
                    description=transaction_log.description,
                    user=transaction_log.agent,
                    booking=transaction_log.booking,
                    account=revenue_account,
                    entry_type='credit',
                    amount=transaction_log.base_amount
                )
                
                # Credit: Tax Payable (Tax Amount)
                if transaction_log.tax_amount > 0:
                    JournalEntry.objects.create(
                        date=transaction_log.transaction_date.date(),
                        reference_number=reference,
                        transaction_type='ticket_issue',
                        description=f"Tax on {transaction_log.description}",
                        user=transaction_log.agent,
                        booking=transaction_log.booking,
                        account=tax_account,
                        entry_type='credit',
                        amount=transaction_log.tax_amount
                    )
                
                logger.info(f"Ticket issue posted to accounting: {reference}")
                return {'success': True, 'reference': reference}
                
        except Exception as e:
            logger.error(f"Error posting ticket issue: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def post_ticket_void(self, transaction_log):
        """
        Post ticket void to accounting (reversal of issue)
        
        Debit: Ticket Revenue (Revenue)
        Debit: Tax Payable (Liability)
        Credit: Accounts Receivable (Asset)
        """
        try:
            with transaction.atomic():
                from accounts.models.accounting import JournalEntry
                
                reference = self._generate_reference('TV', transaction_log.id)
                
                # Get accounts
                receivable_account = self.Account.objects.get(code='1200')
                revenue_account = self.Account.objects.get(code='4001')
                tax_account = self.Account.objects.get(code='2100')
                
                # Debit: Ticket Revenue (reversal)
                JournalEntry.objects.create(
                    date=transaction_log.transaction_date.date(),
                    reference_number=reference,
                    transaction_type='ticket_void',
                    description=transaction_log.description,
                    user=transaction_log.agent,
                    booking=transaction_log.booking,
                    account=revenue_account,
                    entry_type='debit',
                    amount=transaction_log.base_amount
                )
                
                # Debit: Tax Payable (reversal)
                if transaction_log.tax_amount > 0:
                    JournalEntry.objects.create(
                        date=transaction_log.transaction_date.date(),
                        reference_number=reference,
                        transaction_type='ticket_void',
                        description=f"Tax reversal on {transaction_log.description}",
                        user=transaction_log.agent,
                        booking=transaction_log.booking,
                        account=tax_account,
                        entry_type='debit',
                        amount=transaction_log.tax_amount
                    )
                
                # Credit: Accounts Receivable (reversal)
                JournalEntry.objects.create(
                    date=transaction_log.transaction_date.date(),
                    reference_number=reference,
                    transaction_type='ticket_void',
                    description=transaction_log.description,
                    user=transaction_log.agent,
                    booking=transaction_log.booking,
                    account=receivable_account,
                    entry_type='credit',
                    amount=transaction_log.total_amount
                )
                
                logger.info(f"Ticket void posted to accounting: {reference}")
                return {'success': True, 'reference': reference}
                
        except Exception as e:
            logger.error(f"Error posting ticket void: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def post_ticket_refund(self, transaction_log):
        """
        Post ticket refund to accounting
        
        Debit: Ticket Revenue (Revenue reduction)
        Debit: Refund Expenses (Expense - penalty)
        Credit: Cash (Asset)
        """
        try:
            with transaction.atomic():
                from accounts.models.accounting import JournalEntry
                
                reference = self._generate_reference('TR', transaction_log.id)
                
                # Get accounts
                revenue_account = self.Account.objects.get(code='4001')     # Ticket Revenue
                cash_account = self.Account.objects.get(code='1001')        # Cash
                refund_expense_account = self.Account.objects.get(code='5003')  # Refund Expenses
                
                # Debit: Ticket Revenue (refund amount)
                JournalEntry.objects.create(
                    date=transaction_log.transaction_date.date(),
                    reference_number=reference,
                    transaction_type='ticket_refund',
                    description=transaction_log.description,
                    user=transaction_log.agent,
                    booking=transaction_log.booking,
                    account=revenue_account,
                    entry_type='debit',
                    amount=transaction_log.base_amount
                )
                
                # Debit: Refund Expenses (penalty/fee)
                if transaction_log.fee_amount > 0:
                    JournalEntry.objects.create(
                        date=transaction_log.transaction_date.date(),
                        reference_number=reference,
                        transaction_type='ticket_refund',
                        description=f"Refund penalty on {transaction_log.description}",
                        user=transaction_log.agent,
                        booking=transaction_log.booking,
                        account=refund_expense_account,
                        entry_type='debit',
                        amount=transaction_log.fee_amount
                    )
                
                # Credit: Cash (net refund amount)
                JournalEntry.objects.create(
                    date=transaction_log.transaction_date.date(),
                    reference_number=reference,
                    transaction_type='ticket_refund',
                    description=transaction_log.description,
                    user=transaction_log.agent,
                    booking=transaction_log.booking,
                    account=cash_account,
                    entry_type='credit',
                    amount=transaction_log.total_amount
                )
                
                logger.info(f"Ticket refund posted to accounting: {reference}")
                return {'success': True, 'reference': reference}
                
        except Exception as e:
            logger.error(f"Error posting ticket refund: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def post_payment_received(self, transaction_log):
        """
        Post payment received to accounting
        
        Debit: Cash (Asset)
        Debit: Payment Fees (Expense)
        Credit: Accounts Receivable (Asset)
        """
        try:
            with transaction.atomic():
                from accounts.models.accounting import JournalEntry
                
                reference = self._generate_reference('PR', transaction_log.id)
                
                # Get accounts
                cash_account = self.Account.objects.get(code='1001')        # Cash
                receivable_account = self.Account.objects.get(code='1200')  # Accounts Receivable
                fee_account = self.Account.objects.get(code='5002')         # Payment Fees
                
                # Debit: Cash (amount received)
                JournalEntry.objects.create(
                    date=transaction_log.transaction_date.date(),
                    reference_number=reference,
                    transaction_type='payment_received',
                    description=transaction_log.description,
                    user=transaction_log.agent,
                    booking=transaction_log.booking,
                    account=cash_account,
                    entry_type='debit',
                    amount=transaction_log.base_amount
                )
                
                # Debit: Payment Fees (processing fee)
                if transaction_log.fee_amount > 0:
                    JournalEntry.objects.create(
                        date=transaction_log.transaction_date.date(),
                        reference_number=reference,
                        transaction_type='payment_received',
                        description=f"Payment processing fee on {transaction_log.description}",
                        user=transaction_log.agent,
                        booking=transaction_log.booking,
                        account=fee_account,
                        entry_type='debit',
                        amount=transaction_log.fee_amount
                    )
                
                # Credit: Accounts Receivable
                total_credit = transaction_log.base_amount + transaction_log.fee_amount
                JournalEntry.objects.create(
                    date=transaction_log.transaction_date.date(),
                    reference_number=reference,
                    transaction_type='payment_received',
                    description=transaction_log.description,
                    user=transaction_log.agent,
                    booking=transaction_log.booking,
                    account=receivable_account,
                    entry_type='credit',
                    amount=total_credit
                )
                
                logger.info(f"Payment received posted to accounting: {reference}")
                return {'success': True, 'reference': reference}
                
        except Exception as e:
            logger.error(f"Error posting payment: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def post_commission_transaction(self, transaction_log):
        """
        Post commission transaction to accounting
        
        For Commission Earned:
        Debit: Commission Expense (Expense)
        Credit: Commission Payable (Liability)
        
        For Commission Paid:
        Debit: Commission Payable (Liability)
        Credit: Cash (Asset)
        """
        try:
            with transaction.atomic():
                from accounts.models.accounting import JournalEntry
                
                reference = self._generate_reference('CM', transaction_log.id)
                
                if transaction_log.transaction_type == 'commission_earned':
                    # Get accounts
                    expense_account = self.Account.objects.get(code='5004')  # Commissions Paid
                    payable_account = self.Account.objects.get(code='2200')  # Commission Payable
                    
                    # Debit: Commission Expense
                    JournalEntry.objects.create(
                        date=transaction_log.transaction_date.date(),
                        reference_number=reference,
                        transaction_type='commission_earned',
                        description=transaction_log.description,
                        user=transaction_log.agent,
                        account=expense_account,
                        entry_type='debit',
                        amount=transaction_log.commission_amount
                    )
                    
                    # Credit: Commission Payable
                    JournalEntry.objects.create(
                        date=transaction_log.transaction_date.date(),
                        reference_number=reference,
                        transaction_type='commission_earned',
                        description=transaction_log.description,
                        user=transaction_log.agent,
                        account=payable_account,
                        entry_type='credit',
                        amount=transaction_log.commission_amount
                    )
                    
                else:  # commission_paid
                    # Get accounts
                    payable_account = self.Account.objects.get(code='2200')  # Commission Payable
                    cash_account = self.Account.objects.get(code='1001')     # Cash
                    
                    # Debit: Commission Payable
                    JournalEntry.objects.create(
                        date=transaction_log.transaction_date.date(),
                        reference_number=reference,
                        transaction_type='commission_paid',
                        description=transaction_log.description,
                        user=transaction_log.agent,
                        account=payable_account,
                        entry_type='debit',
                        amount=transaction_log.commission_amount
                    )
                    
                    # Credit: Cash
                    JournalEntry.objects.create(
                        date=transaction_log.transaction_date.date(),
                        reference_number=reference,
                        transaction_type='commission_paid',
                        description=transaction_log.description,
                        user=transaction_log.agent,
                        account=cash_account,
                        entry_type='credit',
                        amount=transaction_log.commission_amount
                    )
                
                logger.info(f"Commission transaction posted to accounting: {reference}")
                return {'success': True, 'reference': reference}
                
        except Exception as e:
            logger.error(f"Error posting commission: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _generate_reference(self, prefix, transaction_id):
        """Generate unique reference number for journal entries"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}-{timestamp}-{str(transaction_id)[:8]}"
    
    def verify_double_entry(self, reference_number):
        """
        Verify that journal entries for a reference balance (debits = credits)
        """
        try:
            from accounts.models.accounting import JournalEntry
            from django.db.models import Sum
            
            entries = JournalEntry.objects.filter(reference_number=reference_number)
            
            debits = entries.filter(entry_type='debit').aggregate(
                total=Sum('amount'))['total'] or Decimal('0.00')
            credits = entries.filter(entry_type='credit').aggregate(
                total=Sum('amount'))['total'] or Decimal('0.00')
            
            is_balanced = debits == credits
            
            return {
                'balanced': is_balanced,
                'debits': debits,
                'credits': credits,
                'difference': debits - credits
            }
            
        except Exception as e:
            logger.error(f"Error verifying double entry: {str(e)}", exc_info=True)
            return {'balanced': False, 'error': str(e)}
