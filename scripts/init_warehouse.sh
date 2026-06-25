#!/usr/bin/env bash
set -euo pipefail

# Load environment variables (POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB)
export $(grep -v '^#' .env | xargs)

# Helper function – execute a .sql file inside the Postgres container
run_sql() {
    local file=$1
    echo "=== Executing ${file} ==="
    docker compose exec -T postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f "/sql/${file}"
}

# 1. Create schemas
run_sql create_schemas.sql

# 2. Bronze tables
run_sql bronze/create_bronze_tables.sql

# 3. Silver tables
run_sql silver/create_silver_tables.sql

# 4. Gold tables
run_sql gold/create_gold_tables.sql

# 5. Audit tables
run_sql audit/create_audit_tables.sql

echo "✅ All schemas & tables have been created successfully."
