import sqlite3
import json
import os
import subprocess
from datetime import datetime

DB_PATH = os.path.join(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"), os.environ.get("DB_NAME", "chiefos.db"))

def get_session_stats():
    # Attempt to get status via agent CLI (chiefos or compatible)
    try:
        result = subprocess.run(['chiefos', 'status', '--json']  # chiefos or your agent CLI if shutil.which('chiefos') else ['echo', '{}'], capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return None

def track_usage():
    stats = get_session_stats()
    if not stats:
        print("Could not retrieve session stats.")
        return

    # Extract data (mapping for Gemini/Anthropic)
    model = stats.get("model", "unknown")
    input_tokens = stats.get("totalTokens", 0) # Simplification for first version
    output_tokens = 0 
    
    # Cost estimates per 1M tokens (approximate)
    costs = {
        "google/gemini-3-flash-preview": 0.10,
        "anthropic/claude-sonnet-4-5": 3.00,
        "anthropic/claude-opus-4-5": 15.00
    }
    rate = costs.get(model, 1.00)
    cost_estimate = (input_tokens / 1000000) * rate

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO table_Usage_Ledger (model, input_tokens, output_tokens, cost_estimate, session_type)
        VALUES (?, ?, ?, ?, ?)
    """, (model, input_tokens, output_tokens, cost_estimate, "main"))
    conn.commit()
    conn.close()
    print(f"✅ Usage logged: {model} | {input_tokens} tokens | ${cost_estimate:.4f}")

if __name__ == "__main__":
    track_usage()
