import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, body):
    from_email = os.environ.get("GMAIL_USER", "your@gmail.com")
    owner_email = os.environ.get("OWNER_EMAIL", "")
    password = os.environ.get("GMAIL_PASS", "")
    agent_name = os.environ.get("AGENT_NAME", "Chief of Staff")

    msg = MIMEMultipart()
    msg["From"] = f"{agent_name} <{from_email}>"
    msg["To"] = to_email
    if owner_email:
        msg["Cc"] = f"{from_email}, {owner_email}"
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        recipients = [to_email, from_email]
        if owner_email:
            recipients.append(owner_email)
        server.sendmail(from_email, recipients, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 send_email.py <to> <subject> <body>")
        sys.exit(1)
    send_email(sys.argv[1], sys.argv[2], sys.argv[3])
