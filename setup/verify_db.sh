#!/usr/bin/env bash
# Verifies the database has all expected tables after schema init.
# Usage: bash verify_db.sh /path/to/chiefos.db

set -euo pipefail

DB_PATH="${1:-}"
if [[ -z "$DB_PATH" || ! -f "$DB_PATH" ]]; then
    echo "❌ Usage: bash verify_db.sh /path/to/chiefos.db"
    exit 1
fi

EXPECTED_TABLES=(
    properties contacts projects tasks todos events
    financial_transactions subscriptions maintenance_log property_utilities
    social_posts security_events chronicles context_vault routines
    table_principle_week_blueprint tasks routines table_Alpha_Intel table_Maat_Audit_Trail
    table_Memory_Index table_System_Agents table_System_Tools table_Usage_Ledger
    table_Latency_Tests agent_state_history system_environment
)

PASS=0
FAIL=0

echo "Verifying database: $DB_PATH"
echo ""

for table in "${EXPECTED_TABLES[@]}"; do
    EXISTS=$(sqlite3 "$DB_PATH" "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='${table}';")
    if [[ "$EXISTS" == "1" ]]; then
        echo "  ✅ $table"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $table — MISSING"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "Result: ${PASS} tables present, ${FAIL} missing"

if [[ "$FAIL" -gt 0 ]]; then
    echo "❌ Database verification failed"
    exit 1
else
    echo "✅ Database verified — all 25 tables present"
    exit 0
fi
