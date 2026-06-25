-- -------------------------------------------------
-- Create all required schemas (if they do not exist)
-- -------------------------------------------------
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS audit;

-- Optional: set a comment for documentation purposes
COMMENT ON SCHEMA bronze IS 'Raw landing zone – 1:1 copy of source CSV files';
COMMENT ON SCHEMA silver IS 'Cleaned / transformed data ready for modelling';
COMMENT ON SCHEMA gold   IS 'Star‑schema (dim + fact) for analytics & ML';
COMMENT ON SCHEMA audit  IS 'ETL observability and data‑quality tables';
