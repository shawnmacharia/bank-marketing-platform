-- -------------------------------------------------
-- Gold layer: star schema (dimensions + fact)
-- -------------------------------------------------
-- Dimension: Date (calendar)
DROP TABLE IF EXISTS gold.dim_date CASCADE;
CREATE TABLE gold.dim_date (
    date_key        INTEGER PRIMARY KEY,               -- YYYYMMDD
    date_val        DATE   NOT NULL,
    day            SMALLINT NOT NULL,
    month          SMALLINT NOT NULL,
    quarter        SMALLINT NOT NULL,
    year           SMALLINT NOT NULL,
    day_name       TEXT    NOT NULL,
    is_weekend     BOOLEAN NOT NULL
);

-- Dimension: Campaign
DROP TABLE IF EXISTS gold.dim_campaign CASCADE;
CREATE TABLE gold.dim_campaign (
    campaign_key   SERIAL PRIMARY KEY,
    campaign_number SMALLINT NOT NULL,
    contact_type   TEXT,
    month_number   SMALLINT,
    poutcome       TEXT
);

-- Dimension: Customer (SCD-2)
DROP TABLE IF EXISTS gold.dim_customer CASCADE;
CREATE TABLE gold.dim_customer (
    customer_key        SERIAL PRIMARY KEY,
    -- Natural key – a deterministic hash of the customer’s immutable attributes.
    -- We will fill this column in the ETL (e.g. MD5 of age|job|marital|education|default|housing|loan)
    customer_nk         TEXT NOT NULL,
    age                SMALLINT,
    job                TEXT,
    marital            TEXT,
    education          TEXT,
    default_flag       BOOLEAN,
    housing_flag       BOOLEAN,
    loan_flag          BOOLEAN,
    age_group          TEXT,
    effective_date     DATE    NOT NULL,                -- start of this version
    expiration_date    DATE,                           -- end of this version; NULL = current
    is_current         BOOLEAN NOT NULL DEFAULT TRUE,

    -- Uniqueness on natural key + effective_date for SCD-2
    CONSTRAINT uq_dim_customer_nk_eff UNIQUE (customer_nk, effective_date)
);

-- Add indexes commonly used for SCD-2 lookups
CREATE INDEX ix_dim_customer_nk_current ON gold.dim_customer (customer_nk) WHERE is_current = TRUE;

-- Fact: Campaign Interactions
DROP TABLE IF EXISTS gold.fact_campaign_interactions CASCADE;
CREATE TABLE gold.fact_campaign_interactions (
    interaction_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_key       INTEGER NOT NULL,
    campaign_key       INTEGER NOT NULL,
    date_key           INTEGER NOT NULL,
    duration_seconds  INTEGER,
    campaign_contacts  SMALLINT,
    previous_contacts  SMALLINT,
    balance_eur        INTEGER,
    subscribed         BOOLEAN,

    -- FK constraints for referential integrity
    CONSTRAINT fk_fact_customer FOREIGN KEY (customer_key) REFERENCES gold.dim_customer (customer_key),
    CONSTRAINT fk_fact_campaign FOREIGN KEY (campaign_key) REFERENCES gold.dim_campaign (campaign_key),
    CONSTRAINT fk_fact_date      FOREIGN KEY (date_key)     REFERENCES gold.dim_date (date_key)
);
