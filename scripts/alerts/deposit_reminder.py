#!/usr/bin/env python3
"""
deposit_reminder.py — Daily 5:00am
Cheques to deposit and transfers due in next 7 days.
Reads finance todos where title contains deposit/transfer/cheque keywords.
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

KEYWORDS = ('deposit', 'cheque', 'check', 'transfer', 'e-transfer', 'wire')

def run():
    today = date.today()
    in_7 = (today + timedelta(days=7)).isoformat()
    today_str = today.isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT title, due_date, priority, notes
        FROM todos
        WHERE status NOT IN ('done','snoozed')
          AND category = 'finance'
          AND due_date IS NOT NULL
          AND due_date >= ? AND due_date <= ?
        ORDER BY due_date ASC
    """, (today_str, in_7))
    all_finance = cur.fetchall()
    conn.close()

    # Filter to deposit/transfer related items
    items = [r for r in all_finance
             if any(kw in r['title'].lower() for kw in KEYWORDS)]

    if not items:
        print("No deposit or transfer reminders. No alert sent.")
        return

    lines = ["🏧 CHIEFOS — DEPOSIT & TRANSFER REMINDER\n"]
    for r in items:
        days_left = (date.fromisoformat(r['due_date']) - today).days
        urgency = "TODAY" if days_left == 0 else f"in {days_left}d"
        lines.append(f"  {r['due_date']} ({urgency})  {r['title']}")
        if r['notes']:
            lines.append(f"    ↳ {r['notes']}")

    msg = "\n".join(lines)
    send_telegram(msg)
    print(f"Deposit reminder sent — {len(items)} items.")

if __name__ == "__main__":
    run()
