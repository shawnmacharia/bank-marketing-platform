"""
Simple extractor that reads a CSV (semicolon‑delimited) into a pandas DataFrame,
forcing all columns to string (TEXT) so the bronze layer stays raw.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

def read_raw_csv(csv_path: Path) -> pd.DataFrame:
    """
    Parameters
    ----------
    csv_path: Path
        Full path to the CSV file (e.g. data/raw/bank-full.csv)

    Returns
    -------
    pd.DataFrame
        DataFrame with all original columns (as strings) and **no** extra columns.
    """
    # The UCI file uses ';' as the delimiter
    df = pd.read_csv(csv_path, sep=";", dtype=str, keep_default_na=False, na_values=[])
    # Force *every* column to string (important for the Bronze TEXT schema)
    df = df.astype(str)
    return df
