"""
Utility helpers for PostgreSQL connections.
All connection parameters are read from the .env file.
"""

import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env from the repository root (one level up from this file)
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

def _make_conn():
    """
    Build a new psycopg2 connection using environment variables.
    """
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

@contextmanager
def get_conn():
    """
    Context manager that yields a live connection and closes it on exit.
    Usage:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    conn = _make_conn()
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_cursor(commit: bool = False):
    """
    Context manager that yields a cursor.
    If commit=True, the transaction is committed when the block exits
    (or rolled back on exception).
    """
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
