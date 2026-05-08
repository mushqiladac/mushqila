from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users for the Mushqila B2B Travel Platform'

    def handle(self, *args, **options):
        users_to_create = [
            {
                'email': 'saddam110@mushqila.com',
                'password': 'Sinan210',
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': User.UserType.ADMIN,
                'status': User.Status.ACTIVE,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'email_verified': True,
                'phone': '+966500000001',
                'company_name_en': 'Mushqila Admin',
            },
            {
                'email': 'manager110@mushqila.com',
                'password': 'Sinan210@',
                'first_name': 'Manager',
                'last_name': 'User',
                'user_type': User.UserType.MANAGER,
                'status': User.Status.ACTIVE,
                'is_staff': True,
                'is_superuser': False,
                'is_active': True,
                'email_verified': True,
                'phone': '+966500000002',
                'company_name_en': 'Mushqila Management',
            },
            {
                'email': 'mhcl107@mushqila.com',
                'password': 'Sinan217',
                'first_name': 'User',
                'last_name': 'MHCL107',
                'user_type': User.UserType.AGENT,
                'status': User.Status.ACTIVE,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'email_verified': True,
                'phone': '+966500000107',
                'company_name_en': 'MHCL Travel Agency 107',
            },
            {
                'email': 'mhcl104@mushqila.com',
                'password': 'Sinan214',
                'first_name': 'User',
                'last_name': 'MHCL104',
                'user_type': User.UserType.AGENT,
                'status': User.Status.ACTIVE,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'email_verified': True,
                'phone': '+966500000104',
                'company_name_en': 'MHCL Travel Agency 104',
            },
            {
                'email': 'mhcl108@mushqila.com',
                'password': 'Sinan218',
                'first_name': 'User',
                'last_name': 'MHCL108',
                'user_type': User.UserType.AGENT,
                'status': User.Status.ACTIVE,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'email_verified': True,
                'phone': '+966500000108',
                'company_name_en': 'MHCL Travel Agency 108',
            },
            {
                'email': 'mhcl007@mushqila.com',
                'password': 'Sinan207',
                'first_name': 'User',
                'last_name': 'MHCL007',
                'user_type': User.UserType.AGENT,
                'status': User.Status.ACTIVE,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'email_verified': True,
                'phone': '+966500000007',
                'company_name_en': 'MHCL Travel Agency 007',
            },
            {
                'email': 'mhcl112@mushqila.com',
                'password': 'Sinan212',
                'first_name': 'User',
                'last_name': 'MHCL112',
                'user_type': User.UserType.AGENT,
                'status': User.Status.ACTIVE,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'email_verified': True,
                'phone': '+966500000112',
                'company_name_en': 'MHCL Travel Agency 112',
            },
        ]

        created_count = 0
        updated_count = 0

        for user_data in users_to_create:
            email = user_data.pop('email')
            password = user_data.pop('password')
            
            # Set username to email if not provided
            user_data['username'] = email
            
            try:
                user, created = User.objects.update_or_create(
                    email=email,
                    defaults=user_data
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Created user: {email}')
                    )
                    created_count += 1
                else:
                    # Update existing user's password
                    user.set_password(password)
                    for key, value in user_data.items():
                        setattr(user, key, value)
                    user.save()
                    self.stdout.write(
                        self.style.WARNING(f'Updated existing user: {email}')
                    )
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating user {email}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} new users, Updated {updated_count} existing users'
            )
        )
