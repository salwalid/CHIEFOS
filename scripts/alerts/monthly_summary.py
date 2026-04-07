#!/usr/bin/env python3
"""
monthly_summary.py — Last day of month 9:00pm
Full month financial wrap-up — what went out, what's coming, subscriptions.
"""
import sqlite3
import subprocess
import tempfile
import os
from datetime import date, timedelta
import calendar

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
    month_start = today.replace(day=1).isoformat()
    month_end = today.isoformat()
    month_name = today.strftime("%B %Y")

    # Next month first day (for upcoming bills)
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    next_month_end = next_month.replace(
        day=calendar.monthrange(next_month.year, next_month.month)[1]
    ).isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Expenses this month
    cur.execute("""
        SELECT vendor, amount, category, date
        FROM financial_transactions
        WHERE type = 'expense'
          AND date >= ? AND date <= ?
        ORDER BY date ASC
    """, (month_start, month_end))
    expenses = cur.fetchall()

    # Income this month
    cur.execute("""
        SELECT vendor, amount, date
        FROM financial_transactions
        WHERE type = 'income'
          AND date >= ? AND date <= ?
        ORDER BY date ASC
    """, (month_start, month_end))
    income = cur.fetchall()

    # Active subscriptions (monthly burn)
    cur.execute("""
        SELECT name, amount, frequency
        FROM subscriptions
        WHERE status = 'active'
        ORDER BY amount DESC
    """)
    subs = cur.fetchall()

    # Bills coming next month
    cur.execute("""
        SELECT vendor, amount, date
        FROM financial_transactions
        WHERE type = 'expense'
          AND date > ? AND date <= ?
        ORDER BY date ASC
    """, (month_end, next_month_end))
    upcoming = cur.fetchall()

    conn.close()

    total_out = sum(r['amount'] or 0 for r in expenses)
    total_in = sum(r['amount'] or 0 for r in income)
    monthly_burn = sum(r['amount'] or 0 for r in subs if r['frequency'] == 'monthly')

    lines = [f"📊 CHIEFOS — MONTHLY FINANCIAL SUMMARY\n{month_name}\n"]

    lines.append(f"── THIS MONTH ──")
    lines.append(f"  💰 Income:    ${total_in:,.2f}")
    lines.append(f"  💸 Expenses:  ${total_out:,.2f}")
    lines.append(f"  📈 Net:       ${total_in - total_out:,.2f}")

    if expenses:
        lines.append(f"\n── EXPENSES ({len(expenses)}) ──")
        for r in expenses:
            lines.append(f"  {r['date']}  {r['vendor']}  ${r['amount'] or 0:.2f}")

    if subs:
        lines.append(f"\n── SUBSCRIPTIONS (monthly burn: ${monthly_burn:.2f}) ──")
        for r in subs:
            lines.append(f"  {r['name']}  ${r['amount'] or 0:.2f}  ({r['frequency']})")

    if upcoming:
        lines.append(f"\n── COMING NEXT MONTH ──")
        for r in upcoming:
            lines.append(f"  {r['date']}  {r['vendor']}  ${r['amount'] or 0:.2f}")

    lines.append(f"\nReview finances: https://{os.environ.get("BASE_URL", "yourdomain.com")}/HQ/schedule/")

    msg = "\n".join(lines)
    send_telegram(msg)
    print(f"Monthly summary sent — {len(expenses)} expenses, {len(income)} income, {len(subs)} subs.")

if __name__ == "__main__":
    run()
