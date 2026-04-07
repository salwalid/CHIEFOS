import imaplib
import email
from email.header import decode_header
import os

def get_email_body(msg_id):
    username = os.environ.get("GMAIL_USER", "your@gmail.com")
    password = os.environ.get("GMAIL_PASS", "")
    imap_url = "imap.gmail.com"

    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(username, password)
        mail.select("inbox")

        status, response = mail.fetch(str(msg_id), "(RFC822)")
        if status != "OK":
            print(f"Error fetching email {msg_id}")
            return

        for response_part in response:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            payload = part.get_payload(decode=True)
                            print(payload.decode())
                            return
                else:
                    payload = msg.get_payload(decode=True)
                    print(payload.decode())
                    return
        mail.logout()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        get_email_body(sys.argv[1])
