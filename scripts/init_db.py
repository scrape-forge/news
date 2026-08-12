# -*- coding: utf-8 -*-
"""
Database Migration / Initialization Script for News Scraper.
Applies `scripts/schema.sql` to your PostgreSQL database.
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

SCHEMA_FILE = Path(__file__).parent / 'schema.sql'



def get_db_connection():
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = int(os.getenv('POSTGRES_PORT', '5432'))
    dbname = os.getenv('POSTGRES_DB', 'news_db')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', '')

    print(f"🔌 Connecting to PostgreSQL at {user}@{host}:{port}/{dbname}...", flush=True)
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )


def run_migration():
    if not SCHEMA_FILE.exists():
        print(f"❌ Schema file not found: {SCHEMA_FILE}")
        sys.exit(1)

    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        sql_statements = f.read()

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            print("📜 Applying database schema migration...", flush=True)
            cursor.execute(sql_statements)
            conn.commit()
            print("✅ Database migration completed successfully!")
            
            # Print table information
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'news_articles';
            """)
            table = cursor.fetchone()
            if table:
                print(f"📌 Table verified: '{table[0]}'")

        conn.close()
    except Exception as exc:
        print(f"❌ Migration failed: {exc}", flush=True)
        sys.exit(1)


if __name__ == '__main__':
    run_migration()
