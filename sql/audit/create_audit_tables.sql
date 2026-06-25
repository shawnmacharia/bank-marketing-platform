-- -------------------------------------------------
-- Audit layer – tracking ETL runs, data quality and pipeline metrics
-- -------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ETL batch log
DROP TABLE IF EXISTS audit.etl_batch_log CASCADE;
CREATE TABLE audit.etl_batch_log (
    batch_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name        TEXT NOT NULL,
    load_date         TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    rows_processed    BIGINT,
    status            TEXT CHECK (status IN ('SUCCESS','FAILURE')),
    duration_secs     NUMERIC(10,2)
);

-- Data quality results
DROP TABLE IF EXISTS audit.data_quality_results CASCADE;
CREATE TABLE audit.data_quality_results (
    result_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id          UUID NOT NULL,
    table_name        TEXT NOT NULL,
    check_name        TEXT NOT NULL,
    check_type        TEXT NOT NULL,                      -- e.g. completeness, validity, uniqueness
    passed_rows       BIGINT,
    failed_rows       BIGINT,
    pass_rate         NUMERIC(5,2),                       -- percentage 0-100
    run_at            TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    CONSTRAINT fk_dq_batch FOREIGN KEY (batch_id) REFERENCES audit.etl_batch_log (batch_id)
);

-- Pipeline metrics (per Airflow task)
DROP TABLE IF EXISTS audit.pipeline_metrics CASCADE;
CREATE TABLE audit.pipeline_metrics (
    metric_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dag_id            TEXT NOT NULL,
    run_date          DATE NOT NULL,
    task_name         TEXT NOT NULL,
    status            TEXT CHECK (status IN ('success','failed','upstream_failed','skipped')),
    runtime_secs      NUMERIC(10,2),
    rows_in           BIGINT,
    rows_out          BIGINT,
    recorded_at       TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);
