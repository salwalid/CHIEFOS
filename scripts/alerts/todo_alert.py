#!/usr/bin/env python3
"""
todo_alert.py — Daily 5:30am
Sends Telegram alert for todos due today or overdue.
"""
import sqlite3
import subprocess
import tempfile
import os
from datetime import date

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

    cur.execute("""
        SELECT title, category, priority, due_date
        FROM todos
        WHERE status NOT IN ('done','snoozed')
          AND due_date IS NOT NULL
          AND due_date <= ?
        ORDER BY due_date ASC, priority DESC
    """, (today,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No overdue or due-today todos. No alert sent.")
        return

    overdue = [r for r in rows if r['due_date'] < today]
    due_today = [r for r in rows if r['due_date'] == today]

    lines = ["🗓 CHIEFOS — DAILY TODO ALERT\n"]

    if due_today:
        lines.append(f"📌 DUE TODAY ({len(due_today)})")
        for r in due_today:
            lines.append(f"  • [{r['category'].upper()}] {r['title']}")

    if overdue:
        lines.append(f"\n🔴 OVERDUE ({len(overdue)})")
        for r in overdue:
            lines.append(f"  • [{r['category'].upper()}] {r['title']} (was {r['due_date']})")

    lines.append(f"\nReview: https://{os.environ.get("BASE_URL", "yourdomain.com")}/HQ/schedule/")

    msg = "\n".join(lines)
    send_telegram(msg)
    print(f"Alert sent — {len(due_today)} due today, {len(overdue)} overdue.")

if __name__ == "__main__":
    run()
