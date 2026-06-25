"""
Entry‑point to load every CSV found under data/raw/ into the Bronze layer.
Typical usage:
    $ python -m python.run_ingestion
"""

import sys
from pathlib import Path
import logging

# Ensure the repository root is on sys.path so imports work
repo_root = Path(__file__).resolve().parents[1]   # <repo_root>/python
sys.path.append(str(repo_root))

from ingestion.loader import load_csv_to_bronze

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    raw_folder = Path(__file__).resolve().parents[1] / "data" / "raw"
    if not raw_folder.is_dir():
        logging.error(f"Folder not found: {raw_folder}")
        sys.exit(1)

    csv_files = list(raw_folder.glob("*.csv"))
    if not csv_files:
        logging.warning(f"No CSV files found in {raw_folder}")
        sys.exit(0)

    for csv_path in csv_files:
        try:
            batch_id = load_csv_to_bronze(csv_path)
            logging.info(f"✅ Completed batch {batch_id}")
        except Exception as exc:
            logging.exception(f"❌ Failed to load {csv_path.name}: {exc}")

if __name__ == "__main__":
    main()
