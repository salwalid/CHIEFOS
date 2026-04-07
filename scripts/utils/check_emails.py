import imaplib
import email
from email.header import decode_header
import json
import os
import sqlite3
from datetime import datetime

def get_last_id():
    try:
        db = sqlite3.connect(os.path.join(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"), os.environ.get("DB_NAME", "chiefos.db")))
        res = db.execute("SELECT value FROM table_Alpha_Intel WHERE key = 'last_email_id'").fetchone()
        db.close()
        return int(res[0]) if res else 0
    except:
        return 0

def set_last_id(msg_id):
    try:
        db = sqlite3.connect(os.path.join(os.environ.get("BASE_DIR", "/home/chiefos/chiefos"), os.environ.get("DB_NAME", "chiefos.db")))
        # Check schema to see if updated_at exists, else use standard key/value insert
        cursor = db.execute("PRAGMA table_info(table_Alpha_Intel)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'updated_at' in columns:
            db.execute("INSERT OR REPLACE INTO table_Alpha_Intel (key, value, updated_at) VALUES ('last_email_id', ?, CURRENT_TIMESTAMP)", (str(msg_id),))
        else:
            db.execute("INSERT OR REPLACE INTO table_Alpha_Intel (key, value) VALUES ('last_email_id', ?)", (str(msg_id),))
            
        db.commit()
        db.close()
    except Exception as e:
        print(f"DB Error: {e}")

def check_emails():
    username = os.environ.get("GMAIL_USER", "your@gmail.com")
    password = os.environ.get("GMAIL_PASS", "")
    imap_url = "imap.gmail.com"
    log_file = "memory/email_check_log.txt"

    last_id = get_last_id()

    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(username, password)
        mail.select("inbox")

        status, messages = mail.search(None, 'ALL')
        if status != "OK":
            print("Failed to search inbox")
            return

        mail_ids = messages[0].split()
        if not mail_ids:
            print("Inbox is empty.")
            return

        new_emails = []
        max_seen_id = last_id

        for i in mail_ids:
            msg_id = int(i)
            if msg_id > last_id:
                res, msg_data = mail.fetch(i, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        from_ = msg.get("From")
                        date_ = msg.get("Date")
                        
                        new_emails.append({
                            "id": msg_id,
                            "from": from_,
                            "subject": subject,
                            "date": date_
                        })
                if msg_id > max_seen_id:
                    max_seen_id = msg_id

        if new_emails:
            print(f"--- {len(new_emails)} New Emails Found ---")
            for e in new_emails:
                print(f"ID: {e['id']}")
                print(f"From: {e['from']}")
                print(f"Subject: {e['subject']}")
                print(f"Date: {e['date']}")
                print("-" * 30)
            
            set_last_id(max_seen_id)
        else:
            print("No new emails since last check.")

        with open(log_file, "a") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Check complete. Found {len(new_emails)} new.\n")

        mail.logout()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_emails()
