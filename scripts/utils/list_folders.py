import imaplib
import os

def list_folders():
    username = os.environ.get("GMAIL_USER", "your@gmail.com")
    password = os.environ.get("GMAIL_PASS", "")
    imap_url = "imap.gmail.com"

    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(username, password)
        status, folders = mail.list()
        if status == "OK":
            for folder in folders:
                print(folder.decode())
        mail.logout()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_folders()
