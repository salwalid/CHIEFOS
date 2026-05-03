#!/usr/bin/env python3
"""
todo_alert.py — Daily Briefing for ChiefOS todos.

Modes:
  --block briefing   Full briefing: Overdue + Today + Horizon (default; cron 5:30am)
  --block today      Only the Today block (cron 2:00pm midday pulse)

Flags:
  --only-if-nonempty  Suppress send if there's nothing to report
  --dry-run           Print to stdout instead of sending Telegram
"""
import argparse
import os
import sqlite3
import subprocess
import tempfile
from datetime import date, timedelta

import chiefos_config as cfg


def fetch_todos():
    today = date.today()
    horizon_end = (today + timedelta(days=cfg.HORIZON_DAYS)).isoformat()
    conn = sqlite3.connect(cfg.DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in cfg.ACTIVE_STATUSES)
    cur.execute(f"""
        SELECT id, title, category, priority, due_date
        FROM todos
        WHERE status IN ({placeholders})
          AND due_date IS NOT NULL
          AND due_date <= ?
    """, (*cfg.ACTIVE_STATUSES, horizon_end))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows, today


def bucket(rows, today):
    today_str = today.isoformat()
    overdue, due_today, horizon = [], [], []
    for r in rows:
        d = r["due_date"]
        if d < today_str:
            overdue.append(r)
        elif d == today_str:
            due_today.append(r)
        else:
            horizon.append(r)
    return overdue, due_today, horizon


def _pri_weight(r):
    return cfg.PRIORITY_WEIGHT.get((r.get("priority") or "").lower(), 0)


def _emoji(cat):
    return cfg.CATEGORY_EMOJI.get((cat or "").lower(), "•")


def _days_between(d1_iso, d2_iso):
    d1 = date.fromisoformat(d1_iso)
    d2 = date.fromisoformat(d2_iso)
    return (d1 - d2).days


def render_overdue(items, today):
    if not items:
        return []
    today_str = today.isoformat()
    items_sorted = sorted(
        items,
        key=lambda r: (-_days_between(today_str, r["due_date"]), -_pri_weight(r)),
    )
    shown = items_sorted[: cfg.CAP_OVERDUE]
    extra = len(items_sorted) - len(shown)
    out = [f"🚨 OVERDUE ({len(items_sorted)})"]
    for r in shown:
        days = _days_between(today_str, r["due_date"])
        out.append(f"  • {_emoji(r['category'])} {r['title']} — was {r['due_date']} ({days}d)")
    if extra > 0:
        out.append(f"  +{extra} more → dashboard")
    return out


def render_today(items):
    if not items:
        return []
    items_sorted = sorted(items, key=lambda r: -_pri_weight(r))
    shown = items_sorted[: cfg.CAP_TODAY]
    extra = len(items_sorted) - len(shown)
    out = [f"📌 TODAY ({len(items_sorted)})"]
    for r in shown:
        out.append(f"  • {_emoji(r['category'])} {r['title']}")
    if extra > 0:
        out.append(f"  +{extra} more → dashboard")
    return out


def render_horizon(items, today):
    if not items:
        return []
    today_str = today.isoformat()
    items_sorted = sorted(items, key=lambda r: (r["due_date"], -_pri_weight(r)))
    shown = items_sorted[: cfg.CAP_HORIZON]
    extra = len(items_sorted) - len(shown)

    sub = {"Tomorrow": [], "In 2-3 days": [], "In 4-5 days": []}
    for r in shown:
        delta = _days_between(r["due_date"], today_str)
        if delta == 1:
            sub["Tomorrow"].append(r)
        elif delta <= 3:
            sub["In 2-3 days"].append(r)
        else:
            sub["In 4-5 days"].append(r)

    out = [f"📡 HORIZON ({len(items_sorted)})"]
    for label in ("Tomorrow", "In 2-3 days", "In 4-5 days"):
        if not sub[label]:
            continue
        out.append(f"  {label}:")
        for r in sub[label]:
            out.append(f"    • {_emoji(r['category'])} {r['title']} ({r['due_date']})")
    if extra > 0:
        out.append(f"  +{extra} more → dashboard")
    return out


def build_briefing(overdue, due_today, horizon, today):
    blocks = []
    for lines in (
        render_overdue(overdue, today),
        render_today(due_today),
        render_horizon(horizon, today),
    ):
        if lines:
            blocks.append("\n".join(lines))
    if not blocks:
        return ""
    header = "🗓 CHIEFOS — TACTICAL BRIEFING"
    return header + "\n\n" + "\n\n".join(blocks) + f"\n\n{cfg.DASHBOARD_URL}"


def build_today_only(due_today):
    if not due_today:
        return ""
    items_sorted = sorted(due_today, key=lambda r: -_pri_weight(r))
    lines = [f"📌 STILL OPEN TODAY ({len(items_sorted)})"]
    for r in items_sorted[: cfg.CAP_TODAY]:
        lines.append(f"  • {_emoji(r['category'])} {r['title']}")
    extra = len(items_sorted) - cfg.CAP_TODAY
    if extra > 0:
        lines.append(f"  +{extra} more → dashboard")
    lines.append(f"\n{cfg.DASHBOARD_URL}")
    return "\n".join(lines)


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
    p.add_argument("--block", choices=("briefing", "today"), default="briefing")
    p.add_argument("--only-if-nonempty", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    rows, today = fetch_todos()
    overdue, due_today, horizon = bucket(rows, today)

    if args.block == "today":
        msg = build_today_only(due_today)
    else:
        msg = build_briefing(overdue, due_today, horizon, today)

    if not msg:
        if args.only_if_nonempty:
            print("Nothing to report. No alert sent.")
            return
        print("No items in any bucket. No alert sent.")
        return

    if args.dry_run:
        print(msg)
        return

    send_telegram(msg)
    print(f"Alert sent — block={args.block}, overdue={len(overdue)}, today={len(due_today)}, horizon={len(horizon)}")


if __name__ == "__main__":
    main()
