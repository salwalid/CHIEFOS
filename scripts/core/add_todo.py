#!/usr/bin/env python3
"""
add_todo.py — Alpha's single entry point for creating todos.

Usage:
    python3 add_todo.py \
        --title "Call plumber" \
        --category personal \
        --priority high \
        --due_date 2026-04-05 \
        --reminder_date 2026-04-04 \
        --notes "Details about the job"

After inserting, immediately regenerates schedule_data.json so the
item appears on the HQ Schedule page within 60 seconds.

Categories: project / finance / property / content / personal
Priority:   high / medium / low
Status:     open / in_progress / done / snoozed
"""

import argparse
import sqlite3
import subprocess
import sys
import os
from datetime import datetime

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_NAME", "chiefos.db"))
HYDRATOR = os.path.join(BASE_DIR, "scripts/hydrate_schedule.py")

def add_todo(title, category="personal", priority="medium", status="open",
             due_date=None, reminder_date=None, linked_type=None,
             linked_id=None, notes=None):

    if not title:
        print("ERROR: title is required")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO todos
            (title, category, priority, status, due_date, reminder_date,
             linked_type, linked_id, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        category,
        priority,
        status,
        due_date,
        reminder_date,
        linked_type,
        linked_id,
        notes,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    print(f"✅ Todo #{new_id} created: {title}")
    if due_date:
        print(f"   Due: {due_date} | Priority: {priority} | Category: {category}")

    # Immediately regenerate schedule so it appears on HQ calendar
    result = subprocess.run(
        ["python3", HYDRATOR],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"   📅 Schedule updated — visible on HQ within 60 seconds")
    else:
        print(f"   ⚠️  Schedule update failed: {result.stderr.strip()}")

    return new_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a todo to ChiefOS")
    parser.add_argument("--title",         required=True)
    parser.add_argument("--category",      default="personal",
                        choices=["project","finance","property","content","personal"])
    parser.add_argument("--priority",      default="medium",
                        choices=["high","medium","low"])
    parser.add_argument("--status",        default="open")
    parser.add_argument("--due_date",      default=None, help="YYYY-MM-DD")
    parser.add_argument("--reminder_date", default=None, help="YYYY-MM-DD")
    parser.add_argument("--linked_type",   default=None)
    parser.add_argument("--linked_id",     default=None, type=int)
    parser.add_argument("--notes",         default=None)

    args = parser.parse_args()
    add_todo(
        title=args.title,
        category=args.category,
        priority=args.priority,
        status=args.status,
        due_date=args.due_date,
        reminder_date=args.reminder_date,
        linked_type=args.linked_type,
        linked_id=args.linked_id,
        notes=args.notes
    )
