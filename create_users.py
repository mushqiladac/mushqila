#!/usr/bin/env python
"""
Standalone script to create default users for Mushqila B2B Travel Platform
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print("Trying to continue with basic setup...")
    
    # Minimal setup for user creation
    import sqlite3
    from datetime import datetime

def create_users_with_sqlite():
    """Create users directly with SQLite for testing"""
    try:
        # Connect to database
        db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Users to create
        users = [
            {
                'username': 'saddam110',
                'email': 'saddam110@mushqila.com',
                'password': 'Sinan210',
                'first_name': 'Saddam',
                'last_name': 'Admin',
                'user_type': 'admin',
                'phone': '+966500000001',
                'is_staff': 1,
                'is_superuser': 1,
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
                'is_staff': 1,
                'is_superuser': 0,
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
                'is_staff': 0,
                'is_superuser': 0,
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
                'is_staff': 0,
                'is_superuser': 0,
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
                'is_staff': 0,
                'is_superuser': 0,
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
                'is_staff': 0,
                'is_superuser': 0,
                'company_name_en': 'MHCL Holidays',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for user_data in users:
            username = user_data['username']
            email = user_data['email']
            
            # Check if user exists
            cursor.execute("SELECT id FROM accounts_user WHERE email = ?", (email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user
                cursor.execute("""
                    UPDATE accounts_user SET 
                        username = ?, first_name = ?, last_name = ?, user_type = ?, 
                        phone = ?, is_staff = ?, is_superuser = ?, 
                        company_name_en = ?, is_active = 1, status = 'active'
                    WHERE email = ?
                """, (
                    username, user_data['first_name'], user_data['last_name'],
                    user_data['user_type'], user_data['phone'],
                    user_data['is_staff'], user_data['is_superuser'],
                    user_data['company_name_en'], email
                ))
                
                print(f"🔄 Updated user: {username} ({email}) - {user_data['user_type']}")
                updated_count += 1
            else:
                # Create new user (without password hash for now)
                cursor.execute("""
                    INSERT INTO accounts_user (
                        username, email, first_name, last_name, user_type, phone,
                        is_staff, is_superuser, company_name_en, is_active, status,
                        date_joined, last_login
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active', ?, ?)
                """, (
                    username, email, user_data['first_name'], user_data['last_name'],
                    user_data['user_type'], user_data['phone'],
                    user_data['is_staff'], user_data['is_superuser'],
                    user_data['company_name_en'], datetime.now(), datetime.now()
                ))
                
                print(f"✅ Created user: {username} ({email}) - {user_data['user_type']}")
                created_count += 1
        
        conn.commit()
        conn.close()
        
        print('\n' + '='*50)
        print(f'Summary: {created_count} users created, {updated_count} users updated')
        print('\nDefault Users Created:')
        print('1. Admin: saddam110 / Sinan210')
        print('2. Manager: manager110 / Sinan210@')
        print('3. Agent 1: mhcl107 / Sinan217')
        print('4. Agent 2: mhcl104 / Sinan214')
        print('5. Agent 3: mhcl007 / Sinan217')
        print('6. Agent 4: mhcl112 / Sinan214')
        print('='*50)
        
        print('\n⚠️  Note: Passwords need to be set manually through Django admin or password reset')
        print('The users are created but passwords need to be hashed properly.')
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_users_with_django():
    """Create users using Django ORM"""
    try:
        from accounts.models import User, UserProfile
        from django.contrib.auth.hashers import make_password
        
        # Users to create
        users_data = [
            {
                'username': 'saddam110',
                'email': 'saddam110@mushqila.com',
                'password': make_password('Sinan210'),
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
                'password': make_password('Sinan210@'),
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
                'password': make_password('Sinan217'),
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
                'password': make_password('Sinan214'),
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
                'password': make_password('Sinan217'),
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
                'password': make_password('Sinan214'),
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
                    user.password = user_data['password']
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
                    
                    print(f'✅ Created user: {username} ({email}) - {user.get_user_type_display()}')
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
                    user.password = user_data['password']
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
                    
                    print(f'🔄 Updated user: {username} ({email}) - {user.get_user_type_display()}')
                    updated_count += 1
                    
            except Exception as e:
                print(f'❌ Error creating user {username}: {str(e)}')

        print('\n' + '='*50)
        print(f'Summary: {created_count} users created, {updated_count} users updated')
        print('\nDefault Users Created:')
        print('1. Admin: saddam110 / Sinan210')
        print('2. Manager: manager110 / Sinan210@')
        print('3. Agent 1: mhcl107 / Sinan217')
        print('4. Agent 2: mhcl104 / Sinan214')
        print('5. Agent 3: mhcl007 / Sinan217')
        print('6. Agent 4: mhcl112 / Sinan214')
        print('='*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Django user creation failed: {e}")
        return False

if __name__ == '__main__':
    print('Creating default users for Mushqila B2B Travel Platform...')
    
    # Try Django first, fallback to SQLite
    if not create_users_with_django():
        print("Falling back to SQLite direct creation...")
        create_users_with_sqlite()
    
    print('\n✅ User creation process completed!')
