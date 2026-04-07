#!/usr/bin/env python3
"""
project_status.py — Monday 9:00am
Project health report — stalled projects, overdue tasks, this week's deadlines.
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

    # All active projects with task counts
    cur.execute("""
        SELECT p.id, p.project_name as name, p.status,
               COUNT(t.id) as open_tasks,
               MIN(t.due_date) as next_deadline
        FROM projects p
        LEFT JOIN tasks t ON t.project_id = p.id AND t.status NOT IN ('done')
        WHERE p.status NOT IN ('completed','cancelled')
        GROUP BY p.id
        ORDER BY open_tasks DESC
    """)
    projects = cur.fetchall()

    # Overdue tasks
    cur.execute("""
        SELECT t.title, t.due_date, p.project_name as project
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.status NOT IN ('done')
          AND t.due_date IS NOT NULL
          AND t.due_date < ?
        ORDER BY t.due_date ASC
    """, (today_str,))
    overdue = cur.fetchall()

    # Tasks due this week
    cur.execute("""
        SELECT t.title, t.due_date, p.project_name as project
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.status NOT IN ('done')
          AND t.due_date IS NOT NULL
          AND t.due_date >= ? AND t.due_date <= ?
        ORDER BY t.due_date ASC
    """, (today_str, in_7))
    this_week = cur.fetchall()

    conn.close()

    lines = [f"📊 CHIEFOS — WEEKLY PROJECT REPORT\n{today_str}\n"]

    if projects:
        lines.append("── PROJECTS ──")
        for p in projects:
            tasks_str = f"{p['open_tasks']} open tasks" if p['open_tasks'] else "no open tasks"
            deadline = f" | next: {p['next_deadline']}" if p['next_deadline'] else ""
            lines.append(f"  {p['name']}  [{p['status']}]  {tasks_str}{deadline}")

    if overdue:
        lines.append(f"\n🔴 OVERDUE TASKS ({len(overdue)})")
        for r in overdue:
            proj = f"[{r['project']}] " if r['project'] else ""
            lines.append(f"  {r['due_date']}  {proj}{r['title']}")

    if this_week:
        lines.append(f"\n📌 DUE THIS WEEK ({len(this_week)})")
        for r in this_week:
            proj = f"[{r['project']}] " if r['project'] else ""
            lines.append(f"  {r['due_date']}  {proj}{r['title']}")

    if not overdue and not this_week:
        lines.append("\n✅ No overdue tasks or deadlines this week.")

    lines.append(f"\nhttps://{os.environ.get("BASE_URL", "yourdomain.com")}/HQ/schedule/")

    msg = "\n".join(lines)
    send_telegram(msg)
    print(f"Project status sent — {len(projects)} projects, {len(overdue)} overdue, {len(this_week)} due this week.")

if __name__ == "__main__":
    run()
