#!/usr/bin/env python3
"""
hydrate_projects.py — Reads projects + tasks from DB,
writes projects_data.json for the /HQ/projects/ dashboard.
"""
import os
import json
import sqlite3
from datetime import datetime, date

BASE_DIR = "$CHIEFOS_HOME"
DB_PATH = os.path.join(BASE_DIR, "chiefos.db")
OUTPUT = os.path.join(BASE_DIR, "www/HQ/projects/projects_data.json")

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM projects ORDER BY status, project_name")
    projects = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM tasks ORDER BY priority DESC, due_date ASC")
    tasks = [dict(r) for r in cur.fetchall()]

    conn.close()

    # Group tasks by project_id
    tasks_by_project = {}
    orphaned = []
    for t in tasks:
        pid = t.get('project_id')
        if pid:
            tasks_by_project.setdefault(pid, []).append(t)
        else:
            orphaned.append(t)

    today = date.today().isoformat()
    total_tasks = len(tasks)
    open_tasks = sum(1 for t in tasks if (t.get('status') or 'open') == 'open')
    overdue = sum(1 for t in tasks if t.get('due_date') and t['due_date'] < today and (t.get('status') or 'open') == 'open')

    data = {
        "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_projects": len(projects),
            "active_projects": sum(1 for p in projects if (p.get('status') or '').lower() == 'active'),
            "total_tasks": total_tasks,
            "open_tasks": open_tasks,
            "overdue_tasks": overdue
        },
        "projects": projects,
        "tasks_by_project": tasks_by_project,
        "orphaned_tasks": orphaned
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Projects hydrated — {len(projects)} projects, {total_tasks} tasks, {overdue} overdue.")

if __name__ == "__main__":
    run()
