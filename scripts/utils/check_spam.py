import imaplib
import email
from email.header import decode_header
import sys
import os

def check_spam():
    username = os.environ.get("GMAIL_USER", "your@gmail.com")
    password = os.environ.get("GMAIL_PASS", "")
    imap_url = "imap.gmail.com"

    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(username, password)
        # Gmail spam folder is usually "[Gmail]/Spam"
        status, folders = mail.list()
        spam_folder = None
        for f in folders:
            if b"Spam" in f:
                spam_folder = f.decode().split(' "/" ')[1].strip('"')
        
        if not spam_folder:
            print("Spam folder not found.")
            return

        mail.select(spam_folder)
        status, messages = mail.search(None, 'ALL')
        mail_ids = messages[0].split()
        if not mail_ids:
            print("Spam folder is empty.")
        else:
            print(f"--- Latest Spam Emails ---")
            for i in mail_ids[-3:]:
                res, msg_data = mail.fetch(i, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        print(f"From: {msg.get('From')}")
                        print(f"Subject: {msg.get('Subject')}")
        mail.logout()
    except Exception as e:
        print(f"Error checking spam: {e}")

if __name__ == "__main__":
    check_spam()
