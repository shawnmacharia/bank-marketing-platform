"""
Utility helpers for PostgreSQL connections and simple audit logging.
All connection parameters are read from the .env file.
"""

import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load the .env file that lives in the repo root
load_dotenv(
    dotenv_path=os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    )
)

def _make_conn():
    """Create a new psycopg2 connection using the .env values."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

@contextmanager
def get_conn():
    """Yield a live connection; close it when the block exits."""
    conn = _make_conn()
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_cursor(commit: bool = False):
    """
    Yield a cursor.
    If commit=True the transaction is COMMITTED on exit,
    otherwise it is rolled back on exception.
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

# -------------------------------------------------------------------------
# Simple audit-logging helper – used by the ingestion loader and the
# data-quality runner.
# -------------------------------------------------------------------------
def log_etl_batch(
    batch_id: str,
    table_name: str,
    rows_processed: int,
    status: str,
    duration_secs: float,
):
    """
    Insert a row into audit.etl_batch_log.
    """
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO audit.etl_batch_log
                (batch_id, table_name, load_date,
                 rows_processed, status, duration_secs)
            VALUES (%s, %s, now(), %s, %s, %s)
            """,
            (batch_id, table_name, rows_processed, status, duration_secs),
        )
