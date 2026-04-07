#!/usr/bin/env python3
"""
bill_reminder.py — Daily 5:00am
Bills and subscriptions due in the next 14 days.
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
    in_14 = (today + timedelta(days=14)).isoformat()
    today_str = today.isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Bills from financial_transactions due soon
    cur.execute("""
        SELECT vendor, amount, date, notes, property_id
        FROM financial_transactions
        WHERE type = 'expense'
          AND date IS NOT NULL
          AND date >= ? AND date <= ?
        ORDER BY date ASC
    """, (today_str, in_14))
    bills = cur.fetchall()

    # Subscriptions due soon
    cur.execute("""
        SELECT name, amount, frequency, next_due_date
        FROM subscriptions
        WHERE status = 'active'
          AND next_due_date IS NOT NULL
          AND next_due_date >= ? AND next_due_date <= ?
        ORDER BY next_due_date ASC
    """, (today_str, in_14))
    subs = cur.fetchall()

    conn.close()

    if not bills and not subs:
        print("No bills or subscriptions due in next 14 days. No alert sent.")
        return

    lines = ["💳 CHIEFOS — BILL REMINDER\n"]

    if bills:
        lines.append(f"🏦 BILLS DUE ({len(bills)})")
        for r in bills:
            amount = f"${r['amount']:.2f}" if r['amount'] else "?"
            lines.append(f"  {r['date']}  {r['vendor']}  {amount}")
            if r['notes']:
                lines.append(f"           ↳ {r['notes']}")

    if subs:
        lines.append(f"\n🔄 SUBSCRIPTIONS DUE ({len(subs)})")
        for r in subs:
            amount = f"${r['amount']:.2f}" if r['amount'] else "?"
            lines.append(f"  {r['next_due_date']}  {r['name']}  {amount}  ({r['frequency']})")

    total = sum(r['amount'] or 0 for r in bills) + sum(r['amount'] or 0 for r in subs)
    lines.append(f"\nTotal due: ${total:.2f}")

    msg = "\n".join(lines)
    send_telegram(msg)
    print(f"Bill reminder sent — {len(bills)} bills, {len(subs)} subscriptions.")

if __name__ == "__main__":
    run()
