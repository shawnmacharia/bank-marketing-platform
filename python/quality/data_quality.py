"""
DataQualityChecker runs a suite of checks against one bronze batch
(_batch_id) and writes the outcome to audit.data_quality_results.
"""

import logging
from datetime import datetime

from python.utils.db import get_cursor

logger = logging.getLogger(__name__)

BRONZE_TABLE = "bronze.bank_marketing_raw"


class DataQualityChecker:
    """
    Executes completeness, validity, uniqueness and (placeholder) referential
    integrity checks for a single bronze batch.
    """

    def __init__(self, batch_id: str):
        self.batch_id = batch_id
        self.start_time = datetime.utcnow()

    # -----------------------------------------------------------------
    # Helper – write a single result row
    # -----------------------------------------------------------------
    def _write_result(
        self,
        table_name: str,
        check_name: str,
        check_type: str,
        passed_rows: int,
        failed_rows: int,
    ):
        total = passed_rows + failed_rows
        pass_rate = round((passed_rows / total) * 100, 2) if total else 0.0

        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO audit.data_quality_results
                    (batch_id, table_name, check_name, check_type,
                     passed_rows, failed_rows, pass_rate, run_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                """,
                (
                    self.batch_id,
                    table_name,
                    check_name,
                    check_type,
                    passed_rows,
                    failed_rows,
                    pass_rate,
                ),
            )
        logger.info(
            f"✅ {check_name} – {pass_rate}% ({passed_rows}/{total})"
        )

    # -----------------------------------------------------------------
    # Generic runner – executes a SQL fragment that returns the count of
    # *invalid* rows.
    # -----------------------------------------------------------------
    def _run_check(self, check_name: str, check_type: str, sql_invalid: str):
        """
        Returns (passed_rows, failed_rows)
        """
        with get_cursor() as cur:
            # Total rows for this batch
            cur.execute(
                f"SELECT COUNT(*) FROM {BRONZE_TABLE} WHERE _batch_id = %s",
                (self.batch_id,),
            )
            total_rows = cur.fetchone()[0]

            # Rows that violate the rule
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM {BRONZE_TABLE}
                WHERE _batch_id = %s
                  AND ({sql_invalid})
                """,
                (self.batch_id,),
            )
            failed_rows = cur.fetchone()[0]

        passed_rows = total_rows - failed_rows
        self._write_result(
            table_name=BRONZE_TABLE,
            check_name=check_name,
            check_type=check_type,
            passed_rows=passed_rows,
            failed_rows=failed_rows,
        )
        return passed_rows, failed_rows

    # -----------------------------------------------------------------
    # 1️⃣ Completeness
    # -----------------------------------------------------------------
    def check_completeness(self, columns):
        """Check that specified columns are not null or empty."""
        for col in columns:
            self._run_check(
                check_name=f"{col}_not_null",
                check_type="completeness",
                sql_invalid=f"{col} IS NULL OR {col} = ''",
            )

    # -----------------------------------------------------------------
    # 2️⃣ Validity
    # -----------------------------------------------------------------
    def check_validity(self):
        """Check data validity constraints (ranges, formats, etc)."""
        # age must be between 18 and 100 (or not null/empty)
        self._run_check(
            "age_out_of_range",
            "validity",
            "age IS NULL OR age = '' OR age::int < 18 OR age::int > 100",
        )
        # balance must not be lower than -10 000
        self._run_check(
            "balance_negative_outlier",
            "validity",
            "balance IS NULL OR balance = '' OR balance::int < -10000",
        )
        # duration cannot be negative
        self._run_check(
            "duration_negative",
            "validity",
            "duration IS NULL OR duration = '' OR duration::int < 0",
        )
        # campaign must be > 0
        self._run_check(
            "campaign_non_positive",
            "validity",
            "campaign IS NULL OR campaign = '' OR campaign::int <= 0",
        )

    # -----------------------------------------------------------------
    # 3️⃣ Uniqueness (duplicate raw rows inside the same batch)
    # -----------------------------------------------------------------
    def check_uniqueness(self):
        """Check for duplicate rows within the batch."""
        raw_cols = [
            "age", "job", "marital", "education", "default", "balance",
            "housing", "loan", "contact", "day", "month", "duration",
            "campaign", "pdays", "previous", "poutcome", "y",
        ]
        group_by = ", ".join(raw_cols)

        dup_sql = f"""
            SELECT COALESCE(SUM(cnt - 1), 0) AS duplicate_rows
            FROM (
                SELECT COUNT(*) AS cnt
                FROM {BRONZE_TABLE}
                WHERE _batch_id = %s
                GROUP BY {group_by}
            ) sub
            WHERE cnt > 1
        """

        with get_cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM {BRONZE_TABLE} WHERE _batch_id = %s",
                (self.batch_id,),
            )
            total_rows = cur.fetchone()[0]

            cur.execute(dup_sql, (self.batch_id,))
            dup_rows = cur.fetchone()[0] or 0

        passed = total_rows - dup_rows
        self._write_result(
            table_name=BRONZE_TABLE,
            check_name="duplicate_rows",
            check_type="uniqueness",
            passed_rows=passed,
            failed_rows=dup_rows,
        )

    # -----------------------------------------------------------------
    # 4️⃣ Referential integrity (stub – always passes for now)
    # -----------------------------------------------------------------
    def check_referential_integrity(self):
        """Placeholder for referential integrity checks."""
        # For now, just log a passing check
        with get_cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM {BRONZE_TABLE} WHERE _batch_id = %s",
                (self.batch_id,),
            )
            total_rows = cur.fetchone()[0]

        self._write_result(
            table_name=BRONZE_TABLE,
            check_name="referential_integrity_stub",
            check_type="referential_integrity",
            passed_rows=total_rows,
            failed_rows=0,
        )

    # -----------------------------------------------------------------
    # 5️⃣ Run all checks
    # -----------------------------------------------------------------
    def run_all_checks(self):
        """Execute all checks in order."""
        logger.info(f"Running quality checks for batch {self.batch_id}...")
        
        # Core checks
        self.check_completeness([
            "age", "job", "marital", "education", "default", "balance",
            "housing", "loan", "contact", "day", "month", "duration",
            "campaign", "pdays", "previous", "poutcome", "y"
        ])
        self.check_validity()
        self.check_uniqueness()
        self.check_referential_integrity()

        logger.info(f"✅ Quality checks complete for batch {self.batch_id}")
