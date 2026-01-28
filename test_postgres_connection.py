import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connection parameters
params = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': 'EMR@55nondita'
}

print("Testing PostgreSQL connection...")
print(f"Host: {params['host']}")
print(f"Port: {params['port']}")
print(f"User: {params['user']}")
print()

try:
    # Try to connect to postgres database (default)
    print("1. Connecting to PostgreSQL server...")
    conn = psycopg2.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        database='postgres'  # Connect to default database
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    print("✓ Connected successfully!")
    
    # Check if mhcl database exists
    print("\n2. Checking if 'mhcl' database exists...")
    cursor.execute("SELECT 1 FROM pg_database WHERE datname='mhcl'")
    exists = cursor.fetchone()
    
    if exists:
        print("✓ Database 'mhcl' already exists!")
    else:
        print("✗ Database 'mhcl' does not exist.")
        print("\n3. Creating 'mhcl' database...")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('mhcl')))
        print("✓ Database 'mhcl' created successfully!")
    
    cursor.close()
    conn.close()
    
    # Test connection to mhcl database
    print("\n4. Testing connection to 'mhcl' database...")
    conn = psycopg2.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        database='mhcl'
    )
    print("✓ Successfully connected to 'mhcl' database!")
    conn.close()
    
    print("\n" + "="*50)
    print("SUCCESS! PostgreSQL is configured correctly.")
    print("You can now run: python manage.py migrate")
    print("="*50)
    
except psycopg2.OperationalError as e:
    print(f"\n✗ Connection failed!")
    print(f"Error: {e}")
    print("\nPossible solutions:")
    print("1. Check if PostgreSQL service is running")
    print("2. Verify the password is correct")
    print("3. Check if PostgreSQL is listening on localhost:5432")
    print("4. Check pg_hba.conf for authentication settings")
    
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
