#!/usr/bin/env python3
"""
hydrate_comms.py — Reads contacts from DB,
writes comms_data.json for the /HQ/comms/ dashboard.
"""
import os
import json
import sqlite3
from datetime import datetime

BASE_DIR = "$CHIEFOS_HOME"
DB_PATH = os.path.join(BASE_DIR, "chiefos.db")
OUTPUT = os.path.join(BASE_DIR, "www/HQ/comms/comms_data.json")

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, specialty, contact_info, last_used, rating
        FROM contacts
        ORDER BY rating DESC NULLS LAST, name ASC
    """)
    contacts = [dict(r) for r in cur.fetchall()]
    conn.close()

    rated = [c for c in contacts if c.get('rating')]
    avg_rating = round(sum(c['rating'] for c in rated) / len(rated), 1) if rated else 0

    data = {
        "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_contacts": len(contacts),
            "rated_contacts": len(rated),
            "avg_rating": avg_rating,
        },
        "contacts": contacts,
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Comms hydrated — {len(contacts)} contacts, avg rating {avg_rating}.")

if __name__ == "__main__":
    run()
