-- ============================================================
-- ChiefOS Database Schema
-- Version: 1.0 (2026-04-06)
-- Tables: 25
-- Run: sqlite3 $DB_PATH < schema.sql
-- ============================================================

-- Core operational tables

CREATE TABLE IF NOT EXISTS properties (
    id TEXT PRIMARY KEY,
    name TEXT,
    type TEXT,
    status TEXT,
    cleaning_status TEXT,
    last_maintenance TEXT,
    next_tax_due TEXT,
    critical_notes TEXT
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    specialty TEXT,
    contact_info TEXT,
    last_used TEXT,
    rating INTEGER
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    priority TEXT DEFAULT 'medium',
    owner TEXT,
    due_date TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    priority TEXT,
    due_date TEXT,
    notes TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT,
    linked_type TEXT,
    linked_id INTEGER,
    priority TEXT,
    status TEXT DEFAULT 'open',
    due_date TEXT,
    reminder_date TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    type TEXT,
    start_datetime TEXT,
    end_datetime TEXT,
    location TEXT,
    project_id INTEGER,
    notes TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS financial_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    category TEXT,
    amount REAL,
    type TEXT DEFAULT 'expense',
    date TEXT,
    vendor TEXT,
    description TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amount REAL,
    frequency TEXT,
    category TEXT,
    next_due_date TEXT,
    status TEXT DEFAULT 'active',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS maintenance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    contact_id INTEGER,
    work_type TEXT,
    description TEXT,
    status TEXT DEFAULT 'open',
    scheduled_date TEXT,
    completed_date TEXT,
    cost REAL,
    notes TEXT,
    FOREIGN KEY (property_id) REFERENCES properties(id),
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS property_utilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER,
    vendor TEXT,
    account_number TEXT,
    contact_info TEXT,
    notes TEXT,
    FOREIGN KEY (asset_id) REFERENCES properties(id)
);

CREATE TABLE IF NOT EXISTS social_posts (
    id TEXT PRIMARY KEY,
    title TEXT,
    platform TEXT,
    status TEXT,
    post_date TEXT,
    opening TEXT,
    body TEXT,
    takeaway TEXT,
    hashtags TEXT,
    post_type TEXT,
    engine TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    event_type TEXT,
    ip_address TEXT,
    isp TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS chronicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    component TEXT,
    event TEXT,
    error_log TEXT,
    lesson_learned TEXT,
    context_id INTEGER,
    session_date TEXT
);

CREATE TABLE IF NOT EXISTS context_vault (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT,
    concept TEXT,
    breakthrough TEXT,
    implementation_link TEXT,
    horizon TEXT,
    principal_sentiment TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    related_mission_id INTEGER,
    tags TEXT
);

CREATE TABLE IF NOT EXISTS routines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    routine_name TEXT,
    sequence_id INTEGER,
    component_name TEXT,
    action_requirement TEXT,
    time_window TEXT,
    status TEXT,
    principal_note TEXT
);

CREATE TABLE IF NOT EXISTS table_principle_week_blueprint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    activity_name TEXT NOT NULL,
    focus_type TEXT,
    alpha_protocol TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- System / governance tables (read-only for the AI)

CREATE TABLE IF NOT EXISTS table_Alpha_Intel (
    key TEXT PRIMARY KEY,
    value TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS table_Maat_Audit_Trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    tier INTEGER,
    action TEXT,
    rationale TEXT,
    verdict TEXT,
    principal_override TEXT
);

CREATE TABLE IF NOT EXISTS table_Memory_Index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    table_name TEXT NOT NULL,
    row_id INTEGER NOT NULL,
    last_accessed TEXT
);

CREATE TABLE IF NOT EXISTS table_System_Agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT UNIQUE,
    name TEXT,
    domain TEXT,
    model TEXT,
    agent_dir TEXT,
    allow_agents TEXT
);

CREATE TABLE IF NOT EXISTS table_System_Tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT UNIQUE,
    description TEXT,
    tier INTEGER,
    restricted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS table_Usage_Ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_estimate REAL,
    session_type TEXT
);

CREATE TABLE IF NOT EXISTS table_Latency_Tests (
    id INTEGER PRIMARY KEY,
    test_id TEXT,
    test_case TEXT,
    tier INTEGER,
    mode TEXT,
    total_time_ms INTEGER,
    guardian_time_ms INTEGER,
    est_tokens INTEGER,
    cost_usd REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_environment (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
