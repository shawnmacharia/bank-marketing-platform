"""
Fast bulk loader that uses PostgreSQL COPY FROM STDIN.
It adds three audit columns:
    _loaded_at   – timestamp (UTC) when the batch was inserted
    _batch_id    – UUID identifying the batch (one UUID per file)
    _source_file – the original filename (e.g. bank-full.csv)

The COPY command expects columns in the exact order of the table definition:
    age, job, marital, education, default, balance,
    housing, loan, contact, day, month, duration,
    campaign, pdays, previous, poutcome, y,
    _loaded_at, _batch_id, _source_file
"""
import uuid
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import pandas as pd
from ..utils.db import get_cursor

# -------------------------------------------------------------------------
# Ordered list of the raw columns as they appear in the CSV / Bronze table.
# Keeping this list in one place guarantees that the DataFrame we create
# matches the DB column order exactly.
# -------------------------------------------------------------------------
RAW_COLUMNS = [
    "age", "job", "marital", "education", "default", "balance",
    "housing", "loan", "contact", "day", "month", "duration",
    "campaign", "pdays", "previous", "poutcome", "y",
]

METADATA_COLUMNS = ["_loaded_at", "_batch_id", "_source_file"]

def _prepare_dataframe(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """
    Append audit columns to the raw DataFrame and re‑order columns.
    """
    batch_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)

    df["_loaded_at"] = now_utc.isoformat()
    df["_batch_id"] = batch_id
    df["_source_file"] = source_file

    # Ensure the final order matches the table definition
    final_cols = RAW_COLUMNS + METADATA_COLUMNS
    df = df[final_cols]
    return df, batch_id, len(df)

def _copy_to_postgres(df: pd.DataFrame):
    """
    Perform COPY … FROM STDIN using a CSV in memory.
    """
    # Pandas can write a CSV directly to a StringIO buffer.
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=False, sep=",", quoting=1)  # quoting=1 → csv.QUOTE_MINIMAL
    csv_buffer.seek(0)

    copy_sql = """
        COPY bronze.bank_marketing_raw
        FROM STDIN
        WITH (FORMAT csv, HEADER FALSE, DELIMITER ',', QUOTE '"')
    """

    with get_cursor(commit=True) as cur:
        cur.copy_expert(sql=copy_sql, file=csv_buffer)

def load_csv_to_bronze(csv_path: Path) -> str:
    """
    High‑level wrapper used by the runner script.
    Returns the batch_id that was generated for this load.
    """
    source_file = csv_path.name
    # 1️⃣ Extract
    from .extractor import read_raw_csv
    raw_df = read_raw_csv(csv_path)

    # 2️⃣ Transform (add audit columns)
    df_prepared, batch_id, rows = _prepare_dataframe(raw_df, source_file)

    # 3️⃣ Load
    _copy_to_postgres(df_prepared)

    print(f"[✔] Loaded {rows:,} rows from '{source_file}' → batch_id {batch_id}")
    return batch_id
