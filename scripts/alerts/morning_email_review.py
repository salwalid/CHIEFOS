#!/usr/bin/env python3
"""
morning_email_review.py — Daily 5:00am
Overnight email digest — counts, senders, anything flagged urgent.
"""
import imaplib
import email
from email.header import decode_header
import subprocess
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta, timezone

BASE_DIR = os.environ.get("BASE_DIR", "/home/chiefos/chiefos")
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_NAME", "chiefos.db"))
TELEGRAM = os.path.join(BASE_DIR, "scripts/utils/send_alert.sh")

URGENT_KEYWORDS = ['urgent', 'action required', 'overdue', 'final notice',
                   'reminder', 'payment', 'invoice', 'past due', 'eviction']

def send_telegram(message):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(message)
        tmp = f.name
    try:
        subprocess.run([TELEGRAM, tmp], check=True)
    finally:
        os.unlink(tmp)

def decode_str(s):
    if s is None:
        return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            result.append(part)
    return " ".join(result)

def get_credentials():
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT value FROM table_Alpha_Intel WHERE key = 'gmail_user'"
        ).fetchone()
        conn.close()
        if row:
            return row[0]
    except:
        pass
    return os.environ.get("GMAIL_USER", "your@gmail.com")

def run():
    username = os.environ.get("GMAIL_USER", "your@gmail.com")
    password = os.environ.get("GMAIL_PASS", "")

    # Look at emails from the last 24 hours
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%d-%b-%Y")

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")

        _, msgs = mail.search(None, f'(SINCE "{since}")')
        mail_ids = msgs[0].split() if msgs[0] else []

        overnight = []
        urgent = []

        for mid in mail_ids[-50:]:  # cap at 50
            _, data = mail.fetch(mid, "(RFC822.HEADER)")
            msg = email.message_from_bytes(data[0][1])
            subject = decode_str(msg.get("Subject", "(no subject)"))
            sender = decode_str(msg.get("From", ""))
            date_str = msg.get("Date", "")

            overnight.append({"from": sender, "subject": subject})

            if any(kw in subject.lower() for kw in URGENT_KEYWORDS):
                urgent.append({"from": sender, "subject": subject})

        mail.logout()

    except Exception as e:
        print(f"Email check failed: {e}")
        return

    lines = [f"📧 CHIEFOS — OVERNIGHT EMAIL DIGEST\n"]
    lines.append(f"  {len(overnight)} emails in the last 24 hours")

    if urgent:
        lines.append(f"\n🔴 FLAGGED URGENT ({len(urgent)})")
        for e in urgent[:5]:
            lines.append(f"  From: {e['from'][:40]}")
            lines.append(f"  Re:   {e['subject'][:60]}")

    if overnight:
        # Show unique senders
        senders = list(dict.fromkeys(e['from'].split('<')[0].strip() for e in overnight))[:8]
        lines.append(f"\n── Recent senders ──")
        for s in senders:
            lines.append(f"  • {s[:50]}")

    lines.append(f"\nCheck email: https://{os.environ.get("BASE_URL", "yourdomain.com")}/HQ/")

    msg = "\n".join(lines)
    send_telegram(msg)
    print(f"Morning email digest sent — {len(overnight)} emails, {len(urgent)} urgent.")

if __name__ == "__main__":
    run()
