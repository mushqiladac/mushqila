import sys, traceback
import psycopg2

DB_NAME = 'mhcl'
DB_USER = 'postgres'
DB_PASSWORD = 'EMR@55Nondita'
DB_HOST = 'localhost'
DB_PORT = 5432

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()
    cur.execute('SELECT version();')
    print('CONNECTED:', cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print('CONNECTION FAILED:', e)
    traceback.print_exc()
    sys.exit(1)
