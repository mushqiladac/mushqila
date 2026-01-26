# accounts/management/commands/setup_accounting.py
"""
Management command to set up the accounting system
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Account, AccountingRule
from decimal import Decimal


class Command(BaseCommand):
    help = 'Set up the accounting system with default accounts and rules'

    def handle(self, *args, **options):
        self.stdout.write('Setting up accounting system...')

        with transaction.atomic():
            # Create default accounts
            self.create_default_accounts()

            # Create accounting rules
            self.create_accounting_rules()

        self.stdout.write(
            self.style.SUCCESS('Successfully set up accounting system')
        )

    def create_default_accounts(self):
        """Create default chart of accounts"""
        accounts_data = [
            # Assets
            {'code': '1001', 'name': 'Cash', 'type': 'asset', 'category': 'cash', 'normal_balance': 'debit'},
            {'code': '1101', 'name': 'Accounts Receivable', 'type': 'asset', 'category': 'receivable', 'normal_balance': 'debit'},

            # Liabilities
            {'code': '2001', 'name': 'Accounts Payable', 'type': 'liability', 'category': 'payable', 'normal_balance': 'credit'},
            {'code': '2101', 'name': 'Customer Deposits', 'type': 'liability', 'category': 'deposits', 'normal_balance': 'credit'},

            # Equity
            {'code': '3001', 'name': 'Retained Earnings', 'type': 'equity', 'category': 'retained', 'normal_balance': 'credit'},

            # Revenue
            {'code': '4001', 'name': 'Ticket Revenue', 'type': 'revenue', 'category': 'ticket_revenue', 'normal_balance': 'credit'},
            {'code': '4101', 'name': 'Ancillary Revenue', 'type': 'revenue', 'category': 'ancillary_revenue', 'normal_balance': 'credit'},
            {'code': '4201', 'name': 'Commission Revenue', 'type': 'revenue', 'category': 'commission_revenue', 'normal_balance': 'credit'},

            # Expenses
            {'code': '5001', 'name': 'Airline Ticket Costs', 'type': 'expense', 'category': 'airline_costs', 'normal_balance': 'debit'},
            {'code': '5101', 'name': 'Payment Processing Fees', 'type': 'expense', 'category': 'payment_fees', 'normal_balance': 'debit'},
            {'code': '5201', 'name': 'Refund Processing Expenses', 'type': 'expense', 'category': 'refund_expenses', 'normal_balance': 'debit'},
            {'code': '5301', 'name': 'Commissions Paid', 'type': 'expense', 'category': 'commissions_paid', 'normal_balance': 'debit'},
        ]

        for account_data in accounts_data:
            account, created = Account.objects.get_or_create(
                code=account_data['code'],
                defaults={
                    'name': account_data['name'],
                    'account_type': account_data['type'],
                    'category': account_data['category'],
                    'normal_balance': account_data['normal_balance'],
                    'description': f"Default {account_data['name']} account"
                }
            )
            if created:
                self.stdout.write(f"Created account: {account}")

    def create_accounting_rules(self):
        """Create default accounting rules for ticketing operations"""

        rules_data = [
            {
                'name': 'Ticket Issue',
                'rule_type': 'ticket_issue',
                'description': 'Accounting entries for ticket issuance',
                'debit_entries': [
                    {'account_code': '1101', 'amount_field': 'ticket_amount'},  # Accounts Receivable
                ],
                'credit_entries': [
                    {'account_code': '4001', 'amount_field': 'ticket_amount'},  # Ticket Revenue
                    {'account_code': '4201', 'amount_field': 'commission_amount'},  # Commission Revenue
                ],
            },
            {
                'name': 'Ticket Void',
                'rule_type': 'ticket_void',
                'description': 'Accounting entries for ticket voiding (reverse issue)',
                'debit_entries': [
                    {'account_code': '4001', 'amount_field': 'ticket_amount'},  # Ticket Revenue
                    {'account_code': '4201', 'amount_field': 'commission_amount'},  # Commission Revenue
                ],
                'credit_entries': [
                    {'account_code': '1101', 'amount_field': 'ticket_amount'},  # Accounts Receivable
                ],
            },
            {
                'name': 'Ticket Cancel',
                'rule_type': 'ticket_cancel',
                'description': 'Accounting entries for ticket cancellation',
                'debit_entries': [
                    {'account_code': '4001', 'amount_field': 'ticket_amount'},  # Ticket Revenue
                    {'account_code': '4201', 'amount_field': 'commission_amount'},  # Commission Revenue
                ],
                'credit_entries': [
                    {'account_code': '1101', 'amount_field': 'ticket_amount'},  # Accounts Receivable
                ],
            },
            {
                'name': 'Ticket Refund',
                'rule_type': 'ticket_refund',
                'description': 'Accounting entries for ticket refunds',
                'debit_entries': [
                    {'account_code': '5201', 'amount_field': 'fee_amount'},  # Refund Processing Expenses
                ],
                'credit_entries': [
                    {'account_code': '1001', 'amount_field': 'refund_amount'},  # Cash
                ],
            },
            {
                'name': 'Payment Received',
                'rule_type': 'payment_received',
                'description': 'Accounting entries for payment received',
                'debit_entries': [
                    {'account_code': '1001', 'amount_field': 'total_amount'},  # Cash
                ],
                'credit_entries': [
                    {'account_code': '1101', 'amount_field': 'total_amount'},  # Accounts Receivable
                ],
            },
        ]

        for rule_data in rules_data:
            rule, created = AccountingRule.objects.get_or_create(
                rule_type=rule_data['rule_type'],
                defaults={
                    'name': rule_data['name'],
                    'description': rule_data['description'],
                    'debit_entries': rule_data['debit_entries'],
                    'credit_entries': rule_data['credit_entries'],
                }
            )
            if created:
                self.stdout.write(f"Created accounting rule: {rule}")