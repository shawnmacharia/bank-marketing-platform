"""
Integration-style test that:

1. Writes a tiny CSV to data/raw/
2. Loads it with the existing bronze loader (producing a batch_id)
3. Executes the DataQualityChecker
4. Asserts that audit tables contain the expected rows.
"""

import csv
import os
import uuid
from pathlib import Path

import pytest

# Import the loader (already fully-implemented in Phase 2)
from python.ingestion.loader import load_csv_to_bronze
# Import the quality checker
from python.quality.data_quality import DataQualityChecker
# Utility DB helpers
from python.utils.db import get_cursor

# ----------------------------------------------------------------------
# Helper to clean up after the test (remove rows belonging to the test batch)
# ----------------------------------------------------------------------
def _cleanup_batch(batch_id: str):
    with get_cursor(commit=True) as cur:
        # Bronze rows
        cur.execute(
            "DELETE FROM bronze.bank_marketing_raw WHERE _batch_id = %s", (batch_id,)
        )
        # Audit rows (both batch log and data-quality results)
        cur.execute(
            "DELETE FROM audit.etl_batch_log WHERE batch_id = %s", (batch_id,)
        )
        cur.execute(
            "DELETE FROM audit.data_quality_results WHERE batch_id = %s",
            (batch_id,),
        )


# ----------------------------------------------------------------------
# Test data – 4 rows (2 distinct, one duplicate, 1 with invalid values)
# ----------------------------------------------------------------------
TEST_CSV_CONTENT = [
    # Header
    [
        "age",
        "job",
        "marital",
        "education",
        "default",
        "balance",
        "housing",
        "loan",
        "contact",
        "day",
        "month",
        "duration",
        "campaign",
        "pdays",
        "previous",
        "poutcome",
        "y",
    ],
    # Row 1 – valid
    [
        "25",
        "admin",
        "married",
        "tertiary",
        "no",
        "1000",
        "yes",
        "no",
        "cellular",
        "5",
        "may",
        "200",
        "1",
        "-1",
        "0",
        "unknown",
        "no",
    ],
    # Row 2 – invalid age (17) + negative duration (-1)
    [
        "17",
        "blue-collar",
        "single",
        "secondary",
        "no",
        "3000",
        "no",
        "yes",
        "telephone",
        "15",
        "jul",
        "-1",
        "2",
        "-1",
        "1",
        "failure",
        "yes",
    ],
    # Row 3 – exact duplicate of Row 1 (to test uniqueness)
    [
        "25",
        "admin",
        "married",
        "tertiary",
        "no",
        "1000",
        "yes",
        "no",
        "cellular",
        "5",
        "may",
        "200",
        "1",
        "-1",
        "0",
        "unknown",
        "no",
    ],
]

TEST_CSV_PATH = Path(__file__).parent.parent / "data" / "raw" / "test_quality.csv"


@pytest.fixture(scope="function")
def test_batch():
    """Create a test CSV, load it, yield the batch_id, then clean up."""
    # Ensure the data/raw folder exists
    TEST_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV file (semicolon-delimited as the source dataset expects)
    with open(TEST_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        for row in TEST_CSV_CONTENT:
            writer.writerow(row)

    # Load via the existing loader – returns the generated batch_id
    batch_id = load_csv_to_bronze(TEST_CSV_PATH)

    # Yield to test
    yield batch_id

    # ------------------------------------------------------------------
    # Teardown – remove all rows for this batch from bronze + audit
    # ------------------------------------------------------------------
    _cleanup_batch(batch_id)

    # Remove the test CSV file
    if TEST_CSV_PATH.is_file():
        os.remove(TEST_CSV_PATH)


def test_data_quality_completeness(test_batch):
    """
    Run completeness checks and verify audit results.
    """
    batch_id = test_batch

    # Execute completeness checks
    checker = DataQualityChecker(batch_id)
    checker.check_completeness(columns=["age", "job", "education", "balance", "y"])

    # Verify audit rows
    with get_cursor() as cur:
        # Count completeness checks
        cur.execute(
            """
            SELECT COUNT(*) FROM audit.data_quality_results
            WHERE batch_id = %s AND check_type = 'completeness'
            """,
            (batch_id,),
        )
        check_count = cur.fetchone()[0]
        assert check_count == 5  # 5 columns checked

        # Age completeness (should be 0 failures)
        cur.execute(
            """
            SELECT passed_rows, failed_rows
            FROM audit.data_quality_results
            WHERE batch_id = %s AND check_name = 'age_not_null'
            """,
            (batch_id,),
        )
        passed, failed = cur.fetchone()
        assert passed == 3  # all 3 rows have a non-null age
        assert failed == 0


def test_data_quality_validity(test_batch):
    """
    Run validity checks and verify that invalid data is caught.
    """
    batch_id = test_batch

    # Execute validity checks
    checker = DataQualityChecker(batch_id)
    checker.check_validity()

    # Verify audit rows
    with get_cursor() as cur:
        # Age validity (one row age 17 should fail)
        cur.execute(
            """
            SELECT passed_rows, failed_rows
            FROM audit.data_quality_results
            WHERE batch_id = %s AND check_name = 'age_out_of_range'
            """,
            (batch_id,),
        )
        passed, failed = cur.fetchone()
        assert passed == 2  # two rows have age in 18-100 range
        assert failed == 1  # one row (age 17) fails

        # Duration validity (one row duration -1 should fail)
        cur.execute(
            """
            SELECT passed_rows, failed_rows
            FROM audit.data_quality_results
            WHERE batch_id = %s AND check_name = 'duration_negative'
            """,
            (batch_id,),
        )
        passed, failed = cur.fetchone()
        assert passed == 2  # two rows have duration >= 0
        assert failed == 1  # one row (duration -1) fails


def test_data_quality_uniqueness(test_batch):
    """
    Run uniqueness checks and verify duplicate detection.
    """
    batch_id = test_batch

    # Execute uniqueness checks
    checker = DataQualityChecker(batch_id)
    checker.check_uniqueness()

    # Verify audit rows
    with get_cursor() as cur:
        # Uniqueness (duplicate row should be counted as 1 failed row)
        cur.execute(
            """
            SELECT passed_rows, failed_rows
            FROM audit.data_quality_results
            WHERE batch_id = %s AND check_name = 'duplicate_rows'
            """,
            (batch_id,),
        )
        passed, failed = cur.fetchone()
        assert failed == 1  # there is exactly one duplicate instance
        assert passed == 2  # 3 total rows – 1 duplicate = 2 unique rows


def test_data_quality_referential_integrity(test_batch):
    """
    Run referential integrity check (placeholder).
    """
    batch_id = test_batch

    # Execute referential integrity check
    checker = DataQualityChecker(batch_id)
    checker.check_referential_integrity()

    # Verify audit rows
    with get_cursor() as cur:
        # Referential-integrity placeholder (should pass all rows)
        cur.execute(
            """
            SELECT passed_rows, failed_rows
            FROM audit.data_quality_results
            WHERE batch_id = %s AND check_name = 'referential_integrity_stub'
            """,
            (batch_id,),
        )
        result = cur.fetchone()
        if result:
            passed, failed = result
            assert passed == 3  # all rows pass (it's a stub)
            assert failed == 0


def test_data_quality_all_checks(test_batch):
    """
    Run the complete suite of checks and assert that the audit results match expectations.
    """
    batch_id = test_batch

    # ---------- Execute all checks ----------
    checker = DataQualityChecker(batch_id)
    checker.run_all_checks()

    # ---------- Verify audit rows ----------
    with get_cursor() as cur:
        # 1️⃣ Data-quality results count
        cur.execute(
            """
            SELECT COUNT(*) FROM audit.data_quality_results
            WHERE batch_id = %s
            """,
            (batch_id,),
        )
        total_checks = cur.fetchone()[0]
        # Expected rows:
        #   – 5 completeness checks (age, job, education, balance, y)
        #   – 4 validity checks (age, balance, duration, campaign)
        #   – 1 uniqueness check
        #   – 1 referential-integrity stub
        assert total_checks == 5 + 4 + 1 + 1

        # 2️⃣ Check that all results have proper structure
        cur.execute(
            """
            SELECT COUNT(*)
            FROM audit.data_quality_results
            WHERE batch_id = %s
              AND (passed_rows IS NULL OR failed_rows IS NULL OR pass_rate IS NULL)
            """,
            (batch_id,),
        )
        null_count = cur.fetchone()[0]
        assert null_count == 0  # No NULL values in required columns


def test_audit_batch_log_entry(test_batch):
    """
    Verify that the batch is logged in audit.etl_batch_log.
    """
    batch_id = test_batch

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT batch_id, table_name, rows_processed, status
            FROM audit.etl_batch_log
            WHERE batch_id = %s
            """,
            (batch_id,),
        )
        result = cur.fetchone()
        assert result is not None
        assert result[0] == batch_id
        assert result[1] == "bronze.bank_marketing_raw"
        assert result[2] == 3  # 3 rows loaded
        assert result[3] == "SUCCESS"
