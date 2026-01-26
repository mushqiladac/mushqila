# accounts/management/commands/initialize_accounts.py
"""
Management command to initialize chart of accounts
Creates default accounts for automated accounting system
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models.accounting import Account


class Command(BaseCommand):
    help = 'Initialize chart of accounts for automated accounting system'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing chart of accounts...')
        
        accounts_to_create = [
            # Assets
            {
                'code': '1001',
                'name': 'Cash and Cash Equivalents',
                'account_type': 'asset',
                'category': 'cash',
                'normal_balance': 'debit',
                'description': 'Cash in hand and bank accounts'
            },
            {
                'code': '1200',
                'name': 'Accounts Receivable',
                'account_type': 'asset',
                'category': 'receivable',
                'normal_balance': 'debit',
                'description': 'Amounts owed by agents and customers'
            },
            
            # Liabilities
            {
                'code': '2100',
                'name': 'Tax Payable',
                'account_type': 'liability',
                'category': 'payable',
                'normal_balance': 'credit',
                'description': 'VAT and other taxes payable'
            },
            {
                'code': '2200',
                'name': 'Commission Payable',
                'account_type': 'liability',
                'category': 'payable',
                'normal_balance': 'credit',
                'description': 'Commissions owed to agents'
            },
            
            # Revenue
            {
                'code': '4001',
                'name': 'Ticket Revenue',
                'account_type': 'revenue',
                'category': 'ticket_revenue',
                'normal_balance': 'credit',
                'description': 'Revenue from ticket sales'
            },
            {
                'code': '4002',
                'name': 'Ancillary Revenue',
                'account_type': 'revenue',
                'category': 'ancillary_revenue',
                'normal_balance': 'credit',
                'description': 'Revenue from ancillary services'
            },
            
            # Expenses
            {
                'code': '5002',
                'name': 'Payment Processing Fees',
                'account_type': 'expense',
                'category': 'payment_fees',
                'normal_balance': 'debit',
                'description': 'Fees for payment gateway and processing'
            },
            {
                'code': '5003',
                'name': 'Refund Processing Expenses',
                'account_type': 'expense',
                'category': 'refund_expenses',
                'normal_balance': 'debit',
                'description': 'Costs associated with refund processing'
            },
            {
                'code': '5004',
                'name': 'Commissions Paid',
                'account_type': 'expense',
                'category': 'commissions_paid',
                'normal_balance': 'debit',
                'description': 'Commissions paid to agents'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for account_data in accounts_to_create:
                account, created = Account.objects.update_or_create(
                    code=account_data['code'],
                    defaults={
                        'name': account_data['name'],
                        'account_type': account_data['account_type'],
                        'category': account_data['category'],
                        'normal_balance': account_data['normal_balance'],
                        'description': account_data['description'],
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created account: {account.code} - {account.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated account: {account.code} - {account.name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nChart of accounts initialized successfully!'
                f'\nCreated: {created_count} accounts'
                f'\nUpdated: {updated_count} accounts'
            )
        )
