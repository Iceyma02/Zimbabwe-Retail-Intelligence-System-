# db.py - Add this at the top
import os
import sqlite3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Check if running on Railway (has DATABASE_URL env var)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Use PostgreSQL on Railway
    engine = create_engine(DATABASE_URL)
    
    def query(sql, params=None):
        with engine.connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)
    
    def get_conn():
        return engine.connect()
    
    # ... rest of your functions stay the same
else:
    # Use SQLite locally
    DB_PATH = os.path.join(os.path.dirname(__file__), "zimretail_iq.db")
    
    def get_conn():
        return sqlite3.connect(DB_PATH)
    
    def query(sql, params=None):
        conn = get_conn()
        try:
            df = pd.read_sql_query(sql, conn, params=params)
        finally:
            conn.close()
        return df
