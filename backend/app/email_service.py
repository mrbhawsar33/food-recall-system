import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SENDER = os.getenv("GMAIL_SENDER")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT = os.getenv("GMAIL_RECIPIENT")

def send_recall_email(recalls: list):
    if not recalls:
        return

    subject = f"Food Recall Alert — {len(recalls)} new recall(s) detected"

    body = "<h2>New Food Recalls Detected</h2>"
    for r in recalls:
        severity = {"1": "HIGH", "2": "MEDIUM", "3": "LOW"}.get(r["category"], "UNKNOWN")
        repeat_warning = "<br><strong>⚠️ Repeat Recall</strong>" if r.get("is_repeat_recall") else ""
        body += f"""
        <hr>
        <p><strong>{r['title']}</strong></p>
        <p>Severity: <strong>{severity}</strong></p>
        <p>Recall ID: {r['recall_id']}</p>
        {repeat_warning}
        """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECIPIENT, msg.as_string())