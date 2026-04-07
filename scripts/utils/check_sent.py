import imaplib
import email
from email.header import decode_header
import os

def check_sent_folder():
    username = os.environ.get("GMAIL_USER", "your@gmail.com")
    password = os.environ.get("GMAIL_PASS", "")
    imap_url = "imap.gmail.com"
    sent_folder = '"[Gmail]/Sent Mail"'

    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(username, password)
        
        # Select the Sent folder
        status, _ = mail.select(sent_folder)
        if status != "OK":
            print(f"Failed to select folder {sent_folder}")
            return

        # Search for all emails
        status, messages = mail.search(None, 'ALL')
        if status != "OK":
            print("Failed to search sent folder")
            return

        mail_ids = messages[0].split()
        if not mail_ids:
            print("Sent folder is empty.")
            return

        # Get the latest email ID
        latest_id = mail_ids[-1]

        res, msg_data = mail.fetch(latest_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                to_ = msg.get("To")
                date_ = msg.get("Date")
                print(f"Latest Sent Email Confirmation:")
                print(f"To: {to_}")
                print(f"Subject: {subject}")
                print(f"Date: {date_}")

        mail.logout()
    except Exception as e:
        print(f"Error checking sent folder: {e}")

if __name__ == "__main__":
    check_sent_folder()
