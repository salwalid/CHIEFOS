import imaplib
import email
from email.header import decode_header
import sys
import os

def read_email_body(email_id):
    username = os.environ.get("GMAIL_USER", "your@gmail.com")
    password = os.environ.get("GMAIL_PASS", "")
    imap_url = "imap.gmail.com"

    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(username, password)
        mail.select("inbox")

        res, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                print(f"--- Email ID: {email_id} ---")
                print(f"From: {msg.get('From')}")
                print(f"Subject: {msg.get('Subject')}")
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            print(f"Body:\n{body}")
                else:
                    body = msg.get_payload(decode=True).decode()
                    print(f"Body:\n{body}")
        mail.logout()
    except Exception as e:
        print(f"Error reading email: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 read_email.py <id>")
        sys.exit(1)
    read_email_body(sys.argv[1])
