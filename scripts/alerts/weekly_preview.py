#!/usr/bin/env python3
"""
weekly_preview.py — Daily 5:45am + Sunday 8pm
Everything due in the next 7 days across all domains.
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
    today = date.today()
    in_7 = (today + timedelta(days=7)).isoformat()
    today_str = today.isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Todos due this week
    cur.execute("""
        SELECT title, category, due_date, priority
        FROM todos
        WHERE status NOT IN ('done','snoozed')
          AND due_date IS NOT NULL
          AND due_date >= ? AND due_date <= ?
        ORDER BY due_date ASC
    """, (today_str, in_7))
    todos = cur.fetchall()

    # Tasks due this week
    cur.execute("""
        SELECT t.title, p.project_name as project, t.due_date
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.status NOT IN ('done')
          AND t.due_date IS NOT NULL
          AND t.due_date >= ? AND t.due_date <= ?
        ORDER BY t.due_date ASC
    """, (today_str, in_7))
    tasks = cur.fetchall()

    # Events this week
    cur.execute("""
        SELECT title, type, start_datetime
        FROM events
        WHERE start_datetime >= ? AND start_datetime <= ?
        ORDER BY start_datetime ASC
    """, (today_str, in_7))
    events = cur.fetchall()

    conn.close()

    if not todos and not tasks and not events:
        print("Nothing due this week. No alert sent.")
        return

    lines = [f"📅 CHIEFOS — WEEK AHEAD ({today_str} → {in_7})\n"]

    if todos:
        by_cat = {}
        for r in todos:
            cat = r['category'].title() if r['category'] else 'Personal'
            by_cat.setdefault(cat, []).append(r)

        for cat, items in by_cat.items():
            lines.append(f"── {cat} ──")
            for r in items:
                lines.append(f"  {r['due_date']}  {r['title']}")

    if tasks:
        lines.append(f"\n── Projects ──")
        for r in tasks:
            proj = f"[{r['project']}] " if r['project'] else ""
            lines.append(f"  {r['due_date']}  {proj}{r['title']}")

    if events:
        lines.append(f"\n── Events ──")
        for r in events:
            lines.append(f"  {r['start_datetime'][:10]}  {r['title']}")

    lines.append(f"\nhttps://{os.environ.get("BASE_URL", "yourdomain.com")}/HQ/schedule/")

    msg = "\n".join(lines)
    send_telegram(msg)
    print(f"Weekly preview sent — {len(todos)} todos, {len(tasks)} tasks, {len(events)} events.")

if __name__ == "__main__":
    run()
