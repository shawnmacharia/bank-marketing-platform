-- -------------------------------------------------
-- Silver layer: cleaned & typed version of the raw data
-- -------------------------------------------------
DROP TABLE IF EXISTS silver.customers_clean CASCADE;

CREATE TABLE silver.customers_clean (
    -- Primary key for downstream joins (generated identity)
    customer_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Cleaned / typed columns
    age                  SMALLINT,
    job                  TEXT,
    marital              TEXT,
    education            TEXT,
    default_flag         BOOLEAN,
    balance              INTEGER,
    housing_flag        BOOLEAN,
    loan_flag           BOOLEAN,
    contact_type        TEXT,
    day_of_month        SMALLINT,
    month_number        SMALLINT,
    duration_seconds    INTEGER,
    campaign_number      SMALLINT,
    pdays               INTEGER,
    previous_contacts   SMALLINT,
    poutcome            TEXT,
    subscribed          BOOLEAN,

    -- Derived / helper columns
    age_group           TEXT,
    never_contacted     BOOLEAN,
    contact_date       DATE,

    -- Load metadata (mirroring bronze)
    _loaded_at         TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    _batch_id          UUID NOT NULL,
    _source_file       TEXT NOT NULL
);

-- Indexes that help later transformations (optional but good practice)
CREATE INDEX ix_silver_customers_clean_age_group ON silver.customers_clean (age_group);
CREATE INDEX ix_silver_customers_clean_contact_date ON silver.customers_clean (contact_date);
