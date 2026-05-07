from django.core.management.base import BaseCommand
from finance.models.user import FinanceUser


class Command(BaseCommand):
    help = 'Create finance app users with specified credentials'

    def handle(self, *args, **options):
        """Create users with specified credentials"""
        
        # Admin user
        try:
            admin_user = FinanceUser.objects.create_user(
                email='saddam110@mushqila.com',
                password='Sinan210',
                user_type='admin',
                first_name='Saddam',
                last_name='Admin',
                phone='+966500000001',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created admin user: {admin_user.email}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'✗ Admin user already exists or error: {e}')
            )
        
        # Manager user
        try:
            manager_user = FinanceUser.objects.create_user(
                email='manager110@mushqila.com',
                password='Sinan210@',
                user_type='manager',
                first_name='Manager',
                last_name='User',
                phone='+966500000002',
                is_staff=True,
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created manager user: {manager_user.email}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'✗ Manager user already exists or error: {e}')
            )
        
        # Regular users
        regular_users = [
            {'username': 'mhcl107', 'password': 'Sinan217', 'phone': '+966500000003'},
            {'username': 'mhcl104', 'password': 'Sinan214', 'phone': '+966500000004'},
            {'username': 'mhcl108', 'password': 'Sinan218', 'phone': '+966500000005'},  # Fixed duplicate mhcl107
            {'username': 'mhcl007', 'password': 'Sinan207', 'phone': '+966500000006'},
            {'username': 'mhcl112', 'password': 'Sinan212', 'phone': '+966500000007'}
        ]
        
        for user_data in regular_users:
            try:
                user = FinanceUser.objects.create_user(
                    email=f'{user_data["username"]}@mushqila.com',
                    password=user_data['password'],
                    user_type='user',
                    first_name=user_data['username'].upper(),
                    last_name='User',
                    phone=user_data['phone'],
                    is_active=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created regular user: {user.email}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'✗ User {user_data["username"]} already exists or error: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS('User creation process completed!'))
