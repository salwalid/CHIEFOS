import os
import json
import sqlite3
from datetime import datetime
import re

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
VAULT_HTML = os.path.join(BASE_DIR, "www/HQ/vault/index.html")
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_NAME", "chiefos.db"))

def hydrate_vault():
    if not os.path.exists(VAULT_HTML):
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get Combat Window — high priority open todos
    cursor.execute("SELECT title as task, priority, due_date as deadline, status FROM todos WHERE LOWER(priority)='high' AND status NOT IN ('done','snoozed') ORDER BY due_date ASC")
    combat = [dict(r) for r in cursor.fetchall()]

    # Get Weekly Window — open todos ordered by due date
    cursor.execute("SELECT title as event, status FROM todos WHERE status NOT IN ('done','snoozed') ORDER BY due_date ASC LIMIT 20")
    weekly = [dict(r) for r in cursor.fetchall()]
    
    # Get Strategic Archive (LinkedIn Drafts)
    # Fixed: Schema check showed 'content' does not exist in social_posts
    cursor.execute("SELECT title, status as summary FROM social_posts WHERE platform='LinkedIn'")
    archive = [dict(r) for r in cursor.fetchall()]

    conn.close()

    with open(VAULT_HTML, 'r') as f:
        content = f.read()

    sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data_payload = {
        "combat_window": combat,
        "weekly_horizon": weekly,
        "strategic_archive": archive,
        "syncTime": sync_time
    }
    
    data_block_json = json.dumps(data_payload)
    
    # Use split/join to avoid regex escape character issues with large data
    pattern = r'const vaultData = \{.*?\};'
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        updated_content = content[:match.start()] + f"const vaultData = {data_block_json};" + content[match.end():]
        with open(VAULT_HTML, 'w') as f:
            f.write(updated_content)
        print("SUCCESS: hydrate_vault.py updated to SQL.")
    else:
        print("ERROR: Could not find vaultData pattern in HTML.")

if __name__ == "__main__":
    hydrate_vault()
