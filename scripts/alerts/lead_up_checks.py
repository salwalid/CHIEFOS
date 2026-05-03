#!/usr/bin/env python3
"""
lead_up_checks.py — Targeted deadline pings for high-priority todos.

Runs once daily at 9:00 AM (configurable in cron). Fires a Telegram alert
when an open high-priority todo is exactly LEAD_UP_DAYS away from its
due_date (default: T-3 and T-1).

Idempotency comes from date math + once-per-day cron — no checkpoint table.
If the cron skips a day, the morning briefing's Horizon block still surfaces
the item.

Flags:
  --dry-run   Print to stdout instead of sending Telegram
"""
import argparse
import os
import sqlite3
import subprocess
import tempfile
from datetime import date, timedelta

import chiefos_config as cfg


T3_LABEL = "⏰ T-3 (72H OUT)"
T1_LABEL = "🚨 T-1 (TOMORROW)"
T3_SUFFIX = "got everything you need?"
T1_SUFFIX = "pre-flight check"


def fetch_lead_up_targets():
    today = date.today()
    target_dates = [(today + timedelta(days=d)).isoformat() for d in cfg.LEAD_UP_DAYS]

    conn = sqlite3.connect(cfg.DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    status_ph = ",".join("?" for _ in cfg.ACTIVE_STATUSES)
    pri_ph = ",".join("?" for _ in cfg.LEAD_UP_PRIORITIES)
    date_ph = ",".join("?" for _ in target_dates)

    cur.execute(f"""
        SELECT id, title, category, priority, due_date
        FROM todos
        WHERE status IN ({status_ph})
          AND priority IN ({pri_ph})
          AND due_date IN ({date_ph})
    """, (*cfg.ACTIVE_STATUSES, *cfg.LEAD_UP_PRIORITIES, *target_dates))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows, today


def emoji(cat):
    return cfg.CATEGORY_EMOJI.get((cat or "").lower(), "•")


def build_message(rows, today):
    if not rows:
        return ""

    t3, t1 = [], []
    for r in rows:
        delta = (date.fromisoformat(r["due_date"]) - today).days
        if delta == 3:
            t3.append(r)
        elif delta == 1:
            t1.append(r)

    if not t3 and not t1:
        return ""

    lines = ["🔔 CHIEFOS — DEADLINE CHECK\n"]

    if t1:
        lines.append(T1_LABEL)
        for r in t1:
            lines.append(f"  • {emoji(r['category'])} {r['title']} ({r['due_date']}) — {T1_SUFFIX}")
        lines.append("")

    if t3:
        lines.append(T3_LABEL)
        for r in t3:
            lines.append(f"  • {emoji(r['category'])} {r['title']} ({r['due_date']}) — {T3_SUFFIX}")
        lines.append("")

    lines.append(cfg.DASHBOARD_URL)
    return "\n".join(lines).rstrip() + "\n"


def send_telegram(message):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(message)
        tmp = f.name
    try:
        subprocess.run([cfg.ALERT_SCRIPT, tmp], check=True)
    finally:
        os.unlink(tmp)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    rows, today = fetch_lead_up_targets()
    msg = build_message(rows, today)

    if not msg:
        print("No lead-up checkpoints firing today.")
        return

    if args.dry_run:
        print(msg)
        return

    send_telegram(msg)
    print(f"Lead-up alert sent — {len(rows)} items.")


if __name__ == "__main__":
    main()
