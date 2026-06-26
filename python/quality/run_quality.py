"""
CLI to execute the data-quality suite for a bronze batch.
If no batch ID is supplied, the most recent batch (by _loaded_at) is used.
"""

import argparse
import logging
import sys
from datetime import datetime

from python.utils.db import get_cursor, log_etl_batch
from python.quality.data_quality import DataQualityChecker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_latest_batch_id():
    """Return the most recent _batch_id from the bronze table, or None."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT _batch_id
            FROM bronze.bank_marketing_raw
            ORDER BY _loaded_at DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        return row[0] if row else None


def run_all_checks(batch_id: str):
    """Run the full suite of checks and log the overall step."""
    start = datetime.utcnow()
    try:
        checker = DataQualityChecker(batch_id)

        # ---- Completeness (core columns we care about downstream) ----
        checker.check_completeness(
            columns=["age", "job", "education", "balance", "y"]
        )

        # ---- Validity -------------------------------------------------
        checker.check_validity()

        # ---- Uniqueness -----------------------------------------------
        checker.check_uniqueness()

        # ---- Referential integrity (placeholder for now) ---------------
        checker.check_referential_integrity()

        status = "SUCCESS"
        logging.info(f"✅ Data-quality checks finished for batch {batch_id}")

    except Exception as exc:
        status = "FAILURE"
        logging.exception(
            f"❌ Data-quality runner failed for batch {batch_id}: {exc}"
        )
        raise
    finally:
        duration = (datetime.utcnow() - start).total_seconds()
        # Log the *overall* quality run as an ETL batch entry.
        log_etl_batch(
            batch_id=batch_id,
            table_name="audit.data_quality_results",
            rows_processed=0,
            status=status,
            duration_secs=duration,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Run data-quality checks for a bronze batch"
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        help="Specific batch UUID. If omitted the latest batch is used.",
    )
    args = parser.parse_args()

    batch_id = args.batch_id or get_latest_batch_id()
    if not batch_id:
        raise SystemExit("❌ No batch found in bronze.bank_marketing_raw.")
    
    logging.info(f"Using batch_id: {batch_id}")
    run_all_checks(batch_id)


if __name__ == "__main__":
    main()
