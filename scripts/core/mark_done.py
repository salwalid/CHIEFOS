#!/usr/bin/env python3
"""
mark_done.py — Mark a todo as done by id and refresh the HQ Schedule.

Usage:
    python3 mark_done.py --id 47

Designed to be called when the Principal sends `/done <id>` on Telegram.
"""
import argparse
import os
import sqlite3
import subprocess
import sys

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_NAME", "chiefos.db"))
HYDRATOR = os.path.join(BASE_DIR, "scripts/core/hydrate_schedule.py")


def mark_done(todo_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, title, status FROM todos WHERE id = ?", (todo_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        print(f"❌ No todo with id {todo_id}")
        sys.exit(1)

    _, title, current_status = row
    if current_status == "done":
        conn.close()
        print(f"ℹ️  Todo #{todo_id} already done: {title}")
        return

    cur.execute("UPDATE todos SET status = 'done' WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()

    print(f"✅ Todo #{todo_id} marked done: {title}")

    result = subprocess.run(
        ["python3", HYDRATOR],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("   📅 Schedule updated")
    else:
        print(f"   ⚠️  Schedule update failed: {result.stderr.strip()}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--id", type=int, required=True)
    args = p.parse_args()
    mark_done(args.id)
