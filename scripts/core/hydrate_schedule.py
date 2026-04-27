import os
import json
import sqlite3
from datetime import datetime, date

BASE_DIR = "$CHIEFOS_HOME"
SCHEDULE_JSON = os.path.join(BASE_DIR, "www/HQ/schedule/schedule_data.json")
DB_PATH = os.path.join(BASE_DIR, "chiefos.db")

# Map todo category → CSS tag type
CATEGORY_TO_TYPE = {
    "property": "property",   # green
    "finance":  "finance",    # orange
    "project":  "admin",      # blue
    "content":  "admin",      # blue
    "personal": "admin",      # blue
}

def get_tag_type(category, due_date_str):
    """Overdue items always show red regardless of category."""
    today = date.today()
    if due_date_str:
        try:
            due = datetime.strptime(due_date_str[:10], "%Y-%m-%d").date()
            if due < today:
                return "medical"  # red — overdue
        except ValueError:
            pass
    return CATEGORY_TO_TYPE.get(str(category).lower(), "admin")

def hydrate_schedule():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    events = []

    # --- Source 1: todos with a due_date, not done ---
    cursor.execute("""
        SELECT title, category, due_date
        FROM todos
        WHERE due_date IS NOT NULL
          AND due_date != ''
          AND status NOT IN ('done', 'snoozed')
        ORDER BY due_date ASC
    """)
    for row in cursor.fetchall():
        events.append({
            "date":  row["due_date"][:10],
            "title": row["title"],
            "type":  get_tag_type(row["category"], row["due_date"])
        })

    # --- Source 2: tasks with a due_date, not done ---
    cursor.execute("""
        SELECT title, due_date
        FROM tasks
        WHERE due_date IS NOT NULL
          AND due_date != ''
          AND status NOT IN ('done')
        ORDER BY due_date ASC
    """)
    for row in cursor.fetchall():
        events.append({
            "date":  row["due_date"][:10],
            "title": row["title"],
            "type":  get_tag_type("project", row["due_date"])
        })

    # --- Source 3: events table (travel, meetings, etc.) ---
    cursor.execute("""
        SELECT title, type, start_datetime, end_datetime, location, notes
        FROM events
        WHERE start_datetime IS NOT NULL
          AND start_datetime != ''
        ORDER BY start_datetime ASC
    """)
    for row in cursor.fetchall():
        loc = (row["location"] or "").strip()
        evt = {
            "date":     row["start_datetime"][:10],
            "title":    row["title"],
            "type":     row["type"] if row["type"] else "admin",
            "end_date": row["end_datetime"][:10] if row["end_datetime"] else None,
            "location": loc if loc and loc.lower() != "n/a" else None,
            "notes":    row["notes"] if row["notes"] else None,
        }
        events.append(evt)

    conn.close()

    payload = {
        "events": events,
        "syncTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(events)
    }

    with open(SCHEDULE_JSON, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: hydrate_schedule.py — {len(events)} events written to schedule_data.json")

if __name__ == "__main__":
    hydrate_schedule()
