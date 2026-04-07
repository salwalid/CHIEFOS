#!/usr/bin/env python3
"""
maintenance_tracker.py — Daily 5:00am
Overdue and upcoming maintenance jobs across all properties.
"""
import sqlite3
import subprocess
import tempfile
import os
from datetime import date, timedelta

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_NAME", "chiefos.db"))
TELEGRAM = os.path.join(BASE_DIR, "scripts/utils/send_alert.sh")

def send_telegram(message):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(message)
        tmp = f.name
    try:
        subprocess.run([TELEGRAM, tmp], check=True)
    finally:
        os.unlink(tmp)

def run():
    today = date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Overdue maintenance jobs
    cur.execute("""
        SELECT m.description, m.work_type, m.scheduled_date, m.status,
               p.name as property_name
        FROM maintenance_log m
        LEFT JOIN properties p ON m.property_id = p.id
        WHERE m.status NOT IN ('completed')
          AND m.scheduled_date IS NOT NULL
          AND m.scheduled_date < ?
        ORDER BY m.scheduled_date ASC
    """, (today,))
    overdue = cur.fetchall()

    # Property todos overdue
    cur.execute("""
        SELECT title, due_date, notes
        FROM todos
        WHERE category = 'property'
          AND status NOT IN ('done','snoozed')
          AND due_date IS NOT NULL
          AND due_date < ?
        ORDER BY due_date ASC
    """, (today,))
    overdue_todos = cur.fetchall()

    conn.close()

    if not overdue and not overdue_todos:
        print("No overdue maintenance. No alert sent.")
        return

    lines = ["🔧 CHIEFOS — MAINTENANCE ALERT\n"]

    if overdue:
        lines.append(f"🔴 OVERDUE MAINTENANCE JOBS ({len(overdue)})")
        for r in overdue:
            prop = r['property_name'] or 'Unknown property'
            lines.append(f"  [{prop}] {r['description']} (due {r['scheduled_date']})")

    if overdue_todos:
        lines.append(f"\n🔴 OVERDUE PROPERTY TODOS ({len(overdue_todos)})")
        for r in overdue_todos:
            lines.append(f"  {r['title']} (due {r['due_date']})")
            if r['notes']:
                lines.append(f"    ↳ {r['notes']}")

    lines.append(f"\nhttps://{os.environ.get("BASE_URL", "yourdomain.com")}/HQ/property/")

    msg = "\n".join(lines)
    send_telegram(msg)
    print(f"Maintenance alert sent — {len(overdue)} jobs, {len(overdue_todos)} todos.")

if __name__ == "__main__":
    run()
