#!/bin/bash
# =============================================================
# CHIEFOS HQ — Phase 1 Database Migration
# Run as: bash $CHIEFOS_HOME/phase1_migration.sh
# Pre-req: backup already done at alpha_backup_20260330_1022.sql
# =============================================================

DB="$CHIEFOS_HOME/chiefos.db"

echo ""
echo "============================================================"
echo "  CHIEFOS HQ — PHASE 1 DATABASE MIGRATION"
echo "  $(date)"
echo "============================================================"
echo ""

# ============================================================
echo "--- STEP 1: Drop junk tables ---"
# ============================================================
sqlite3 "$DB" "DROP TABLE IF EXISTS to_be_deleted_table_Social_Posts;"
echo "  ✓ Dropped to_be_deleted_table_Social_Posts (36 rows — all duplicates of social_posts)"

sqlite3 "$DB" "DROP TABLE IF EXISTS AUDIT_LOG_2026_temporary;"
echo "  ✓ Dropped AUDIT_LOG_2026_temporary (0 rows)"

sqlite3 "$DB" "DROP TABLE IF EXISTS table_Recurring_Vulnerabilities;"
echo "  ✓ Dropped table_Recurring_Vulnerabilities (0 rows — replaced by subscriptions)"

echo ""

# ============================================================
echo "--- STEP 2: Create financial_transactions + migrate Financial Ledger ---"
# ============================================================
sqlite3 "$DB" "
CREATE TABLE IF NOT EXISTS financial_transactions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  property_id INTEGER,
  category    TEXT,
  amount      REAL,
  type        TEXT DEFAULT 'expense',
  date        TEXT,
  vendor      TEXT,
  description TEXT,
  notes       TEXT
);

INSERT INTO financial_transactions (property_id, category, amount, type, date, vendor, notes)
SELECT
  CAST(asset_id AS INTEGER),
  'bill',
  amount,
  'expense',
  due_date,
  bill_name,
  status
FROM table_Financial_Ledger;

DROP TABLE table_Financial_Ledger;
"
COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM financial_transactions;")
echo "  ✓ Created financial_transactions — migrated $COUNT rows from table_Financial_Ledger"

echo ""

# ============================================================
echo "--- STEP 3: Create subscriptions ---"
# ============================================================
sqlite3 "$DB" "
CREATE TABLE IF NOT EXISTS subscriptions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  amount        REAL,
  frequency     TEXT,
  category      TEXT,
  next_due_date TEXT,
  status        TEXT DEFAULT 'active',
  notes         TEXT
);
"
echo "  ✓ Created subscriptions table (ready to populate)"

echo ""

# ============================================================
echo "--- STEP 4: Rename 9 tables ---"
# ============================================================
sqlite3 "$DB" "ALTER TABLE project_metadata RENAME TO projects;"
echo "  ✓ project_metadata → projects"

sqlite3 "$DB" "ALTER TABLE table_Context_Vault RENAME TO context_vault;"
echo "  ✓ table_Context_Vault → context_vault"

sqlite3 "$DB" "ALTER TABLE table_Perimeter_Logs RENAME TO security_events;"
echo "  ✓ table_Perimeter_Logs → security_events"

sqlite3 "$DB" "ALTER TABLE table_Asset_Registry RENAME TO properties;"
echo "  ✓ table_Asset_Registry → properties"

sqlite3 "$DB" "ALTER TABLE table_Alpha_Routines RENAME TO routines;"
echo "  ✓ table_Alpha_Routines → routines"

sqlite3 "$DB" "ALTER TABLE table_Alpha_Chronicles RENAME TO chronicles;"
echo "  ✓ table_Alpha_Chronicles → chronicles"

sqlite3 "$DB" "ALTER TABLE table_Contractor_Network RENAME TO contacts;"
echo "  ✓ table_Contractor_Network → contacts"

sqlite3 "$DB" "ALTER TABLE table_Asset_Utilities RENAME TO property_utilities;"
echo "  ✓ table_Asset_Utilities → property_utilities"

echo ""

# ============================================================
echo "--- STEP 5: Create tasks + migrate PROJECT rows from table_Tactical_Horizon ---"
# ============================================================
sqlite3 "$DB" "
CREATE TABLE IF NOT EXISTS tasks (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER,
  title      TEXT NOT NULL,
  status     TEXT DEFAULT 'open',
  priority   TEXT,
  due_date   TEXT,
  notes      TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

INSERT INTO tasks (title, status, priority, due_date)
SELECT
  task,
  CASE
    WHEN UPPER(status) IN ('DONE','COMPLETED') THEN 'done'
    WHEN UPPER(status) = 'IN PROGRESS'         THEN 'in_progress'
    ELSE 'open'
  END,
  LOWER(COALESCE(NULLIF(priority,''), 'medium')),
  deadline
FROM table_Tactical_Horizon
WHERE UPPER(category) = 'PROJECT';
"
COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM tasks;")
echo "  ✓ Created tasks — migrated $COUNT PROJECT rows from table_Tactical_Horizon"

echo ""

# ============================================================
echo "--- STEP 6: Create todos + migrate remaining rows from table_Tactical_Horizon ---"
# ============================================================
sqlite3 "$DB" "
CREATE TABLE IF NOT EXISTS todos (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  title         TEXT NOT NULL,
  category      TEXT,
  linked_type   TEXT,
  linked_id     INTEGER,
  priority      TEXT,
  status        TEXT DEFAULT 'open',
  due_date      TEXT,
  reminder_date TEXT,
  notes         TEXT,
  created_at    TEXT DEFAULT (datetime('now'))
);

INSERT INTO todos (title, category, priority, status, due_date)
SELECT
  task,
  CASE
    WHEN UPPER(category) = 'RENTAL'  THEN 'property'
    WHEN UPPER(category) = 'MISSION' THEN 'personal'
    ELSE 'personal'
  END,
  CASE
    WHEN UPPER(priority) = 'CRITICAL' THEN 'high'
    ELSE LOWER(COALESCE(NULLIF(priority,''), 'medium'))
  END,
  CASE
    WHEN UPPER(status) IN ('DONE','COMPLETED') THEN 'done'
    WHEN UPPER(status) = 'IN PROGRESS'         THEN 'in_progress'
    WHEN UPPER(status) = 'SNOOZED'             THEN 'snoozed'
    ELSE 'open'
  END,
  deadline
FROM table_Tactical_Horizon
WHERE UPPER(category) != 'PROJECT' OR category IS NULL OR category = '';

DROP TABLE table_Tactical_Horizon;
"
COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM todos;")
echo "  ✓ Created todos — migrated $COUNT non-PROJECT rows from table_Tactical_Horizon"
echo "  ✓ Dropped table_Tactical_Horizon"

echo ""

# ============================================================
echo "--- STEP 7: Create events + migrate Travel_Log ---"
# ============================================================
sqlite3 "$DB" "
CREATE TABLE IF NOT EXISTS events (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  title          TEXT NOT NULL,
  type           TEXT,
  start_datetime TEXT,
  end_datetime   TEXT,
  location       TEXT,
  project_id     INTEGER,
  notes          TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

INSERT INTO events (title, type, start_datetime, end_datetime, location, notes)
SELECT
  destination,
  'travel',
  departure_date,
  return_date,
  destination,
  notes
FROM table_Travel_Log;

DROP TABLE table_Travel_Log;
"
COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM events;")
echo "  ✓ Created events — migrated $COUNT rows from table_Travel_Log"
echo "  ✓ Dropped table_Travel_Log"

echo ""

# ============================================================
echo "--- STEP 8: Create maintenance_log ---"
# ============================================================
sqlite3 "$DB" "
CREATE TABLE IF NOT EXISTS maintenance_log (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  property_id    INTEGER,
  contact_id     INTEGER,
  work_type      TEXT,
  description    TEXT,
  status         TEXT DEFAULT 'open',
  scheduled_date TEXT,
  completed_date TEXT,
  cost           REAL,
  notes          TEXT,
  FOREIGN KEY (property_id) REFERENCES properties(id),
  FOREIGN KEY (contact_id)  REFERENCES contacts(id)
);
"
echo "  ✓ Created maintenance_log table (ready to populate)"

echo ""

# ============================================================
echo "--- VERIFICATION: Final table list ---"
# ============================================================
echo ""
echo "Tables now in chiefos.db:"
sqlite3 "$DB" "SELECT '  ' || name FROM sqlite_master WHERE type='table' ORDER BY name;"

echo ""
echo "============================================================"
echo "  PHASE 1 COMPLETE — $(date)"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Update hydrate_security.py  (table_Perimeter_Logs → security_events)"
echo "  2. Update hydrate_properties.py (table_Asset_Registry → properties)"
echo "  3. Update hydrate_vault.py      (table_Context_Vault + table_Tactical_Horizon refs)"
echo "  4. Update track_usage.py        (table_Usage_Ledger → already untouched, verify)"
echo "  5. Run master_hydration.sh and confirm all pages update cleanly"
echo ""
