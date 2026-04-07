#!/usr/bin/env python3
"""
hydrate_finance.py — Reads financial_transactions + subscriptions from DB,
writes finance_data.json for the /HQ/finance/ dashboard.
"""
import os
import json
import sqlite3
from datetime import date, timedelta, datetime
import calendar

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_NAME", "chiefos.db"))
OUTPUT = os.path.join(BASE_DIR, "www/HQ/finance/finance_data.json")

def run():
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    month_end = today.isoformat()
    month_name = today.strftime("%B %Y")
    in_14 = (today + timedelta(days=14)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Income this month
    cur.execute("""
        SELECT id, property_id, category, amount, date, vendor, description, notes
        FROM financial_transactions
        WHERE type = 'income' AND date >= ? AND date <= ?
        ORDER BY date DESC
    """, (month_start, month_end))
    income_rows = cur.fetchall()

    # Expenses this month
    cur.execute("""
        SELECT id, property_id, category, amount, date, vendor, description, notes
        FROM financial_transactions
        WHERE type = 'expense' AND date >= ? AND date <= ?
        ORDER BY date DESC
    """, (month_start, month_end))
    expense_rows = cur.fetchall()

    # Upcoming bills next 14 days
    cur.execute("""
        SELECT id, property_id, category, amount, date, vendor, description, notes
        FROM financial_transactions
        WHERE type = 'expense' AND date > ? AND date <= ?
        ORDER BY date ASC
    """, (month_end, in_14))
    upcoming_rows = cur.fetchall()

    # Active subscriptions
    cur.execute("""
        SELECT id, name, amount, frequency, category, next_due_date, status, notes
        FROM subscriptions
        WHERE status = 'active'
        ORDER BY next_due_date ASC
    """)
    sub_rows = cur.fetchall()

    conn.close()

    total_income = sum(r['amount'] or 0 for r in income_rows)
    total_expenses = sum(r['amount'] or 0 for r in expense_rows)
    monthly_burn = sum(r['amount'] or 0 for r in sub_rows if r['frequency'] == 'monthly')

    def row_to_dict(r):
        return {k: r[k] for k in r.keys()}

    data = {
        "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "month_name": month_name,
        "summary": {
            "income": round(total_income, 2),
            "expenses": round(total_expenses, 2),
            "net": round(total_income - total_expenses, 2),
            "monthly_burn": round(monthly_burn, 2)
        },
        "income": [row_to_dict(r) for r in income_rows],
        "expenses": [row_to_dict(r) for r in expense_rows],
        "upcoming": [row_to_dict(r) for r in upcoming_rows],
        "subscriptions": [row_to_dict(r) for r in sub_rows]
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Finance hydrated — {len(income_rows)} income, {len(expense_rows)} expenses, "
          f"{len(sub_rows)} subs, {len(upcoming_rows)} upcoming.")

if __name__ == "__main__":
    run()
