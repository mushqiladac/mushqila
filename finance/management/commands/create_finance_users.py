"""
Management command to create FinanceUser accounts from existing accounts.User
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from finance.models.user import FinanceUser

User = get_user_model()


class Command(BaseCommand):
    help = 'Create FinanceUser accounts from existing accounts.User'

    def handle(self, *args, **options):
        # Define users to create
        users_data = [
            {
                'email': 'saddam110@mushqila.com',
                'password': 'Sinan210',
                'user_type': 'admin',
                'first_name': 'Saddam',
                'last_name': 'Admin',
                'phone': '+966500000001',
            },
            {
                'email': 'manager110@mushqila.com',
                'password': 'Sinan210@',
                'user_type': 'manager',
                'first_name': 'Manager',
                'last_name': 'User',
                'phone': '+966500000002',
            },
            {
                'email': 'mhcl107@mushqila.com',
                'password': 'Sinan217',
                'user_type': 'user',
                'first_name': 'MHCL',
                'last_name': '107',
                'phone': '+966500000107',
            },
            {
                'email': 'mhcl104@mushqila.com',
                'password': 'Sinan214',
                'user_type': 'user',
                'first_name': 'MHCL',
                'last_name': '104',
                'phone': '+966500000104',
            },
            {
                'email': 'mhcl108@mushqila.com',
                'password': 'Sinan218',
                'user_type': 'user',
                'first_name': 'MHCL',
                'last_name': '108',
                'phone': '+966500000108',
            },
            {
                'email': 'mhcl007@mushqila.com',
                'password': 'Sinan207',
                'user_type': 'user',
                'first_name': 'MHCL',
                'last_name': '007',
                'phone': '+966500000007',
            },
            {
                'email': 'mhcl112@mushqila.com',
                'password': 'Sinan212',
                'user_type': 'user',
                'first_name': 'MHCL',
                'last_name': '112',
                'phone': '+966500000112',
            },
        ]

        created_count = 0
        updated_count = 0
        error_count = 0

        for user_data in users_data:
            email = user_data['email']
            
            try:
                # Check if FinanceUser already exists
                finance_user, created = FinanceUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': email,
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'phone': user_data['phone'],
                        'user_type': user_data['user_type'],
                        'status': 'active',
                        'is_active': True,
                        'email_verified': True,
                        'phone_verified': True,
                    }
                )
                
                if created:
                    # Set password
                    finance_user.set_password(user_data['password'])
                    finance_user.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created FinanceUser: {email} ({user_data["user_type"]})'
                        )
                    )
                    created_count += 1
                else:
                    # Update existing user
                    finance_user.user_type = user_data['user_type']
                    finance_user.first_name = user_data['first_name']
                    finance_user.last_name = user_data['last_name']
                    finance_user.phone = user_data['phone']
                    finance_user.status = 'active'
                    finance_user.is_active = True
                    finance_user.set_password(user_data['password'])
                    finance_user.save()
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'⟳ Updated FinanceUser: {email} ({user_data["user_type"]})'
                        )
                    )
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error creating/updating {email}: {str(e)}'
                    )
                )
                error_count += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.WARNING(f'Updated: {updated_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        self.stdout.write('='*60)
        
        self.stdout.write('\n' + self.style.SUCCESS('✓ Finance users setup complete!'))
        self.stdout.write('\nYou can now login at: /finance/login/')
        self.stdout.write('\nAdmin: saddam110@mushqila.com / Sinan210')
        self.stdout.write('Manager: manager110@mushqila.com / Sinan210@')
