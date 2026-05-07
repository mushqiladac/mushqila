# accounts/management/commands/create_default_users.py
"""
Management command to create default users for Mushqila B2B Travel Platform
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, UserActivityLog
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Create default users with specified credentials'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating default users...'))
        
        # Define users to create
        users_data = [
            {
                'username': 'saddam110',
                'email': 'saddam110@mushqila.com',
                'password': 'Sinan210',
                'first_name': 'Saddam',
                'last_name': 'Admin',
                'user_type': 'admin',
                'phone': '+966500000001',
                'is_staff': True,
                'is_superuser': True,
                'company_name_en': 'Mushqila Travel Administration',
            },
            {
                'username': 'manager110',
                'email': 'manager110@mushqila.com',
                'password': 'Sinan210@',
                'first_name': 'Manager',
                'last_name': 'User',
                'user_type': 'manager',
                'phone': '+966500000002',
                'is_staff': True,
                'is_superuser': False,
                'company_name_en': 'Mushqila Travel Management',
            },
            {
                'username': 'mhcl107',
                'email': 'mhcl107@mushqila.com',
                'password': 'Sinan217',
                'first_name': 'User',
                'last_name': 'MHCL107',
                'user_type': 'agent',
                'phone': '+966500000107',
                'is_staff': False,
                'is_superuser': False,
                'company_name_en': 'MHCL Travel Agency',
            },
            {
                'username': 'mhcl104',
                'email': 'mhcl104@mushqila.com',
                'password': 'Sinan214',
                'first_name': 'User',
                'last_name': 'MHCL104',
                'user_type': 'agent',
                'phone': '+966500000104',
                'is_staff': False,
                'is_superuser': False,
                'company_name_en': 'MHCL Travel Services',
            },
            {
                'username': 'mhcl007',
                'email': 'mhcl007@mushqila.com',
                'password': 'Sinan217',
                'first_name': 'User',
                'last_name': 'MHCL007',
                'user_type': 'agent',
                'phone': '+966500000007',
                'is_staff': False,
                'is_superuser': False,
                'company_name_en': 'MHCL Tours',
            },
            {
                'username': 'mhcl112',
                'email': 'mhcl112@mushqila.com',
                'password': 'Sinan214',
                'first_name': 'User',
                'last_name': 'MHCL112',
                'user_type': 'agent',
                'phone': '+966500000112',
                'is_staff': False,
                'is_superuser': False,
                'company_name_en': 'MHCL Holidays',
            },
        ]

        created_count = 0
        updated_count = 0

        for user_data in users_data:
            username = user_data['username']
            email = user_data['email']
            
            try:
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': username,
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'user_type': user_data['user_type'],
                        'phone': user_data['phone'],
                        'is_staff': user_data['is_staff'],
                        'is_superuser': user_data['is_superuser'],
                        'company_name_en': user_data['company_name_en'],
                        'is_active': True,
                        'status': 'active',
                        'email_verified': True,
                        'phone_verified': True,
                        'kyc_verified': True,
                    }
                )
                
                if created:
                    user.set_password(user_data['password'])
                    user.save()
                    
                    # Create user profile
                    UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'business_type': 'travel_agency' if user.user_type == 'agent' else 'management',
                            'years_in_business': 5,
                            'language': 'en',
                            'timezone': 'Asia/Riyadh',
                        }
                    )
                    
                    # Log activity
                    UserActivityLog.objects.create(
                        user=user,
                        activity_type='registration',
                        description=f"Default user account created: {user.email}",
                        metadata={'created_by': 'management_command'}
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created user: {username} ({email}) - {user.get_user_type_display()}')
                    )
                    created_count += 1
                else:
                    # Update existing user
                    user.username = username
                    user.first_name = user_data['first_name']
                    user.last_name = user_data['last_name']
                    user.user_type = user_data['user_type']
                    user.phone = user_data['phone']
                    user.is_staff = user_data['is_staff']
                    user.is_superuser = user_data['is_superuser']
                    user.company_name_en = user_data['company_name_en']
                    user.is_active = True
                    user.status = 'active'
                    
                    # Update password if needed
                    if not user.check_password(user_data['password']):
                        user.set_password(user_data['password'])
                    
                    user.save()
                    
                    # Ensure profile exists
                    UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'business_type': 'travel_agency' if user.user_type == 'agent' else 'management',
                            'years_in_business': 5,
                            'language': 'en',
                            'timezone': 'Asia/Riyadh',
                        }
                    )
                    
                    self.stdout.write(
                        self.style.WARNING(f'🔄 Updated user: {username} ({email}) - {user.get_user_type_display()}')
                    )
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error creating user {username}: {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS(f'Summary: {created_count} users created, {updated_count} users updated'))
        self.stdout.write(self.style.SUCCESS('\nDefault Users Created:'))
        self.stdout.write(self.style.SUCCESS('1. Admin: saddam110 / Sinan210'))
        self.stdout.write(self.style.SUCCESS('2. Manager: manager110 / Sinan210@'))
        self.stdout.write(self.style.SUCCESS('3. Agent 1: mhcl107 / Sinan217'))
        self.stdout.write(self.style.SUCCESS('4. Agent 2: mhcl104 / Sinan214'))
        self.stdout.write(self.style.SUCCESS('5. Agent 3: mhcl007 / Sinan217'))
        self.stdout.write(self.style.SUCCESS('6. Agent 4: mhcl112 / Sinan214'))
        self.stdout.write(self.style.SUCCESS('='*50))
