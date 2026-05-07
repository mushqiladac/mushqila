#!/usr/bin/env python
"""
Direct SQLite script to create finance app users with specified credentials
"""
import os
import sqlite3
from datetime import datetime
import hashlib

def hash_password(password):
    """Simple password hashing for Django compatibility"""
    import hashlib
    import random
    salt = hashlib.sha1(str(random.random()).encode('utf8')).hexdigest()[:5]
    hashed = hashlib.sha1((salt + password).encode('utf8')).hexdigest()
    return f"sha1${salt}${hashed}"

def create_users_sqlite():
    """Create users directly with SQLite"""
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if finance_users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='finance_users'")
        if not cursor.fetchone():
            print("❌ finance_users table not found")
            return
        
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
                'is_active': 1,
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
                'is_active': 1,
            },
            {
                'username': 'mhcl107',
                'email': 'mhcl107@mushqila.com',
                'password': 'Sinan217',
                'first_name': 'MHCL107',
                'last_name': 'User',
                'user_type': 'user',
                'phone': '+966500000003',
                'is_staff': 0,
                'is_superuser': 0,
                'is_active': 1,
            },
            {
                'username': 'mhcl104',
                'email': 'mhcl104@mushqila.com',
                'password': 'Sinan214',
                'first_name': 'MHCL104',
                'last_name': 'User',
                'user_type': 'user',
                'phone': '+966500000004',
                'is_staff': 0,
                'is_superuser': 0,
                'is_active': 1,
            },
            {
                'username': 'mhcl007',
                'email': 'mhcl007@mushqila.com',
                'password': 'Sinan207',
                'first_name': 'MHCL007',
                'last_name': 'User',
                'user_type': 'user',
                'phone': '+966500000006',
                'is_staff': 0,
                'is_superuser': 0,
                'is_active': 1,
            },
            {
                'username': 'mhcl112',
                'email': 'mhcl112@mushqila.com',
                'password': 'Sinan212',
                'first_name': 'MHCL112',
                'last_name': 'User',
                'user_type': 'user',
                'phone': '+966500000007',
                'is_staff': 0,
                'is_superuser': 0,
                'is_active': 1,
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for user_data in users:
            # Check if user already exists
            cursor.execute("SELECT id FROM finance_users WHERE email = ?", (user_data['email'],))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user
                cursor.execute("""
                    UPDATE finance_users SET 
                        username = ?, 
                        password = ?, 
                        first_name = ?, 
                        last_name = ?, 
                        user_type = ?, 
                        phone = ?, 
                        is_staff = ?, 
                        is_superuser = ?, 
                        is_active = ?,
                        status = 'active'
                    WHERE email = ?
                """, (
                    user_data['username'],
                    hash_password(user_data['password']),
                    user_data['first_name'],
                    user_data['last_name'],
                    user_data['user_type'],
                    user_data['phone'],
                    user_data['is_staff'],
                    user_data['is_superuser'],
                    user_data['is_active'],
                    user_data['email']
                ))
                print(f"✓ Updated user: {user_data['email']}")
                updated_count += 1
            else:
                # Create new user
                cursor.execute("""
                    INSERT INTO finance_users (
                        username, email, password, first_name, last_name, 
                        user_type, phone, is_staff, is_superuser, is_active,
                        status, date_joined, last_login
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_data['username'],
                    user_data['email'],
                    hash_password(user_data['password']),
                    user_data['first_name'],
                    user_data['last_name'],
                    user_data['user_type'],
                    user_data['phone'],
                    user_data['is_staff'],
                    user_data['is_superuser'],
                    user_data['is_active'],
                    'active',
                    datetime.now().isoformat(),
                    None
                ))
                print(f"✓ Created user: {user_data['email']}")
                created_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ User creation process completed!")
        print(f"📊 Summary: {created_count} users created, {updated_count} users updated")
        
        print("\n👥 Created/Updated Users:")
        print("1. Admin: saddam110@mushqila.com / Sinan210")
        print("2. Manager: manager110@mushqila.com / Sinan210@")
        print("3. User: mhcl107@mushqila.com / Sinan217")
        print("4. User: mhcl104@mushqila.com / Sinan214")
        print("5. User: mhcl007@mushqila.com / Sinan207")
        print("6. User: mhcl112@mushqila.com / Sinan212")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("Creating Finance App Users with SQLite...")
    create_users_sqlite()
