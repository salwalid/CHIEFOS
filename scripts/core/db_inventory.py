import sqlite3
import os

DB_PATH = os.path.join(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"), os.environ.get("DB_NAME", "chiefos.db"))
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

report = []
for table in tables:
    # Get count
    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
    count = cursor.fetchone()[0]
    
    # Get columns
    cursor.execute(f"PRAGMA table_info([{table}])")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Get sample data (first row)
    sample = "Empty"
    if count > 0:
        cursor.execute(f"SELECT * FROM [{table}] LIMIT 1")
        sample_row = cursor.fetchone()
        sample = str(dict(zip(columns, sample_row)))[:100] + "..."

    report.append({
        "name": table,
        "count": count,
        "columns": columns,
        "sample": sample
    })

conn.close()

# Define Intended Uses (from TOOLS.md and context)
INTENDED = {
    "table_Asset_Registry": "Property and hardware asset management.",
    "table_Financial_Ledger": "Billing, amounts, and due dates across assets.",
    "table_Tactical_Horizon": "Master task list with priority and deadlines.",
    "table_Perimeter_Logs": "IP addresses and connection events for security monitoring.",
    "table_Social_Posts": "LinkedIn hooks and full content drafts.",
    "table_Contractor_Network": "Trusted contractors with ratings and specialties.",
    "table_Recurring_Vulnerabilities": "SaaS subscriptions and burn tracking.",
    "table_Alpha_Chronicles": "Lessons learned and session success/failures.",
    "table_Alpha_Intel": "Key/Value store for quick facts and persistent variables.",
    "table_Maat_Audit_Trail": "Detailed log of every tiered action and Guardian verdict.",
    "table_Context_Vault": "Strategic concepts, breakthroughs, and high-level ideas.",
    "social_posts": "Automated briefing output (v11 script).",
    "table_Alpha_Routines": "Recurring task sequences (Email watchers, etc).",
    "table_Asset_Utilities": "Vendors, accounts, and contacts per property.",
    "table_Usage_Ledger": "Token consumption and cost per session.",
    "project_metadata": "Master registry for Project Names, Status, and types.",
    "table_Memory_Index": "Master keyword-to-table mapping.",
    "table_Travel_Log": "Trip details, departures, and destinations.",
    "table_System_Agents": "Master agent roster and configuration.",
    "table_System_Tools": "Master tool catalog and safety tiers.",
    "table_Alpha_Blog_Posts": "Blog content for your domain.",
    "table_Latency_Tests": "Performance data from the MaatSpec security tests."
}

print("| Table Name | Intended Use (A) | Current Contents (B) | Usage Context (C) |")
print("| :--- | :--- | :--- | :--- |")

for r in report:
    intended = INTENDED.get(r['name'], "Operational Metadata / System Table.")
    
    # Logic for Actual Usage (C)
    usage = intended
    if r['name'] == 'social_posts':
        usage = "Primary Social Ledger. Used by v11 script for auto-drafting."
    elif r['name'] == 'table_Alpha_Intel':
        usage = "Used for session variables and 'last_seen' markers."
    elif r['name'] == 'table_Tactical_Horizon':
        usage = "Active Task Manager. Direct source for Forward Briefings."
    elif r['name'].startswith('to_be_deleted'):
        usage = "Archived data awaiting final deletion."

    contents = f"{r['count']} rows. Columns: {', '.join(r['columns'][:3])}..."
    if r['count'] == 0:
        contents = "Empty."

    print(f"| **{r['name']}** | {intended} | {contents} | {usage} |")
