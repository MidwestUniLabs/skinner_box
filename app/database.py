# app/database.py
import psycopg2
import os

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DATABASE_HOST'),
        database=os.getenv('DATABASE'),
        user=os.getenv('USERMAME'),
        password=os.getenv('PASSWORD')
    )
    return conn

def push_log(log):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO logs (log) VALUES (%s)", (log,))
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def start_connection():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            log TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()