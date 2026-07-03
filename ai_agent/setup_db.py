import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ==========================================
# STEP 2a — CONFIGURE THESE BEFORE RUNNING
# ==========================================
# PG_USER / PG_PASSWORD = your PostgreSQL superuser credentials.
# On a fresh install this is usually user: 'postgres', password: whatever
# you set during PostgreSQL installation.
#
# To run: python setup_db.py
# ==========================================
PG_USER = "postgres"                   # ← CONFIGURE: your postgres superuser
PG_PASSWORD = "your_postgres_password" # ← CONFIGURE: your postgres password
PG_HOST = "localhost"
PG_PORT = "5432"

# These are the app DB credentials that will be created automatically.
# After running this script, use these values in your .env:
#   DATABASE_URL=postgresql://ats_user:password@localhost:5432/ats_db
APP_DB_NAME = "ats_db"
APP_DB_USER = "ats_user"
APP_DB_PASS = "password"              # ← CONFIGURE: change for production

def initialize_database():
    print(f"Connecting to default PostgreSQL instance at {PG_HOST}:{PG_PORT}...")
    try:
        # Connect to default 'postgres' database to create the new user and db
        conn = psycopg2.connect(
            dbname="postgres",
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT
        )
        # Must be in autocommit mode to create database
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # 1. Create the user
        cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname='{APP_DB_USER}'")
        if not cursor.fetchone():
            print(f"Creating user '{APP_DB_USER}'...")
            cursor.execute(f"CREATE USER {APP_DB_USER} WITH PASSWORD '{APP_DB_PASS}';")
        else:
            print(f"User '{APP_DB_USER}' already exists.")

        # 2. Create the database
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{APP_DB_NAME}'")
        if not cursor.fetchone():
            print(f"Creating database '{APP_DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {APP_DB_NAME} OWNER {APP_DB_USER};")
        else:
            print(f"Database '{APP_DB_NAME}' already exists.")

        # 3. Grant privileges
        print(f"Granting privileges on '{APP_DB_NAME}' to '{APP_DB_USER}'...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {APP_DB_NAME} TO {APP_DB_USER};")

        cursor.close()
        conn.close()
        print("✅ Database initialization successful!")
        print(f"Database URL for your app: postgresql://{APP_DB_USER}:{APP_DB_PASS}@{PG_HOST}:{PG_PORT}/{APP_DB_NAME}")

    except Exception as e:
        print(f"❌ Error during initialization:\n{e}")
        print("\nMake sure your postgres service is running and credentials are correct.")

if __name__ == "__main__":
    initialize_database()
