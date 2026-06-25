-- -------------------------------------------------
-- Bronze layer: raw table (exact CSV copy)
-- -------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- needed for gen_random_uuid()

DROP TABLE IF EXISTS bronze.bank_marketing_raw CASCADE;

CREATE TABLE bronze.bank_marketing_raw (
    -- Original columns exactly as in the CSV (all TEXT for safe load, later cast)
    age               TEXT,
    job               TEXT,
    marital           TEXT,
    education         TEXT,
    default_flag      TEXT,
    balance           TEXT,
    housing           TEXT,
    loan              TEXT,
    contact           TEXT,
    day               TEXT,
    month             TEXT,
    duration          TEXT,
    campaign          TEXT,
    pdays             TEXT,
    previous          TEXT,
    poutcome          TEXT,
    y                 TEXT,
    -- Ingestion metadata
    _loaded_at        TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    _batch_id         UUID NOT NULL DEFAULT gen_random_uuid(),
    _source_file      TEXT NOT NULL
);

-- Add a comment for clarity
COMMENT ON TABLE bronze.bank_marketing_raw IS
  'Raw landing table – one row per CSV record. All columns kept as TEXT to avoid load‑time cast errors.';
