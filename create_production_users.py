#!/usr/bin/env python
"""
Production script to create finance app users with PostgreSQL
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')

try:
    django.setup()
    from finance.models.user import FinanceUser
    
    def create_production_users():
        """Create users with specified credentials for production"""
        
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
                is_active=True,
                status='active'
            )
            print(f"✓ Created admin user: {admin_user.email}")
        except Exception as e:
            print(f"✗ Admin user already exists or error: {e}")
        
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
                is_active=True,
                status='active'
            )
            print(f"✓ Created manager user: {manager_user.email}")
        except Exception as e:
            print(f"✗ Manager user already exists or error: {e}")
        
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
                    is_active=True,
                    status='active'
                )
                print(f"✓ Created regular user: {user.email}")
            except Exception as e:
                print(f"✗ User {user_data['username']} already exists or error: {e}")
        
        print("\n✅ Production user creation process completed!")
        
        print("\n👥 Created/Updated Users:")
        print("1. Admin: saddam110@mushqila.com / Sinan210")
        print("2. Manager: manager110@mushqila.com / Sinan210@")
        print("3. User: mhcl107@mushqila.com / Sinan217")
        print("4. User: mhcl104@mushqila.com / Sinan214")
        print("5. User: mhcl108@mushqila.com / Sinan218")
        print("6. User: mhcl007@mushqila.com / Sinan207")
        print("7. User: mhcl112@mushqila.com / Sinan212")

    if __name__ == '__main__':
        print("Creating Production Finance App Users...")
        create_production_users()

except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print("Please ensure PostgreSQL is running and environment variables are set correctly.")
    print("Required environment variables:")
    print("- DB_NAME=mushqila")
    print("- DB_USER=postgres") 
    print("- DB_PASSWORD=your_password")
    print("- DB_HOST=localhost")
    print("- DB_PORT=5432")
