"""
Fix PostgreSQL Authentication
This script helps configure PostgreSQL to allow local connections
"""
import os
import subprocess

print("="*60)
print("PostgreSQL Authentication Fix")
print("="*60)
print()

# Common PostgreSQL installation paths
possible_paths = [
    r"C:\Program Files\PostgreSQL\18",
    r"C:\Program Files\PostgreSQL\17",
    r"C:\Program Files\PostgreSQL\16",
    r"C:\Program Files\PostgreSQL\15",
    r"C:\Program Files (x86)\PostgreSQL\18",
    r"C:\Program Files (x86)\PostgreSQL\17",
]

postgres_path = None
for path in possible_paths:
    if os.path.exists(path):
        postgres_path = path
        print(f"✓ Found PostgreSQL at: {path}")
        break

if not postgres_path:
    print("✗ PostgreSQL installation not found in common locations")
    print("\nPlease manually locate your PostgreSQL installation folder")
    print("Common locations:")
    for path in possible_paths:
        print(f"  - {path}")
    exit(1)

# Paths
bin_path = os.path.join(postgres_path, "bin")
data_path = os.path.join(postgres_path, "data")
pg_hba_path = os.path.join(data_path, "pg_hba.conf")
psql_path = os.path.join(bin_path, "psql.exe")

print(f"✓ Binary path: {bin_path}")
print(f"✓ Data path: {data_path}")
print(f"✓ pg_hba.conf: {pg_hba_path}")
print()

# Check if pg_hba.conf exists
if not os.path.exists(pg_hba_path):
    print(f"✗ pg_hba.conf not found at: {pg_hba_path}")
    print("\nYour PostgreSQL data directory might be in a different location.")
    exit(1)

print("="*60)
print("INSTRUCTIONS TO FIX AUTHENTICATION:")
print("="*60)
print()
print("Option 1: Change authentication method to 'trust' (No password)")
print("-" * 60)
print(f"1. Open this file in Notepad as Administrator:")
print(f"   {pg_hba_path}")
print()
print("2. Find lines that look like:")
print("   host    all    all    127.0.0.1/32    scram-sha-256")
print("   host    all    all    ::1/128         scram-sha-256")
print()
print("3. Change 'scram-sha-256' to 'trust':")
print("   host    all    all    127.0.0.1/32    trust")
print("   host    all    all    ::1/128         trust")
print()
print("4. Save the file")
print()
print("5. Restart PostgreSQL service:")
print("   net stop postgresql-x64-18")
print("   net start postgresql-x64-18")
print()
print()
print("Option 2: Reset postgres user password")
print("-" * 60)
print("1. Open Command Prompt as Administrator")
print()
print(f"2. Run this command:")
print(f'   "{psql_path}" -U postgres -c "ALTER USER postgres PASSWORD \'EMR@55nondita\';"')
print()
print()
print("Option 3: Create database using psql")
print("-" * 60)
print("1. Open Command Prompt as Administrator")
print()
print(f"2. Navigate to PostgreSQL bin folder:")
print(f"   cd \"{bin_path}\"")
print()
print("3. Connect to PostgreSQL:")
print('   psql -U postgres')
print()
print("4. When prompted for password, enter your password")
print()
print("5. Create the database:")
print("   CREATE DATABASE mhcl;")
print("   \\q")
print()
print("="*60)
print()

# Try to create a batch file for easy execution
batch_content = f"""@echo off
echo Restarting PostgreSQL service...
net stop postgresql-x64-18
timeout /t 2
net start postgresql-x64-18
echo.
echo PostgreSQL service restarted!
pause
"""

with open("restart_postgres.bat", "w") as f:
    f.write(batch_content)

print("✓ Created 'restart_postgres.bat' - Run as Administrator to restart PostgreSQL")
print()

# Create a batch file to open pg_hba.conf
batch_content2 = f"""@echo off
echo Opening pg_hba.conf...
notepad "{pg_hba_path}"
"""

with open("open_pg_hba.bat", "w") as f:
    f.write(batch_content2)

print("✓ Created 'open_pg_hba.bat' - Run to edit pg_hba.conf")
print()
