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
        recall_class = r.get("recall_class", "")
        severity = {"Class 1": "HIGH", "Class 2": "MEDIUM", "Class 3": "LOW"}.get(recall_class, "UNKNOWN")
        repeat_warning = "<br><strong>Repeat Recall — same product recalled within 30 days</strong>" if r.get("is_repeat_recall") else ""
        summary_block = f"<p><em>{r['ai_summary']}</em></p>" if r.get("ai_summary") else ""

        body += f"""
        <hr>
        <p><strong>{r['title']}</strong></p>
        <p>Severity: <strong>{severity}</strong></p>
        <p>Issue: {r.get('issue', 'N/A')}</p>
        <p>Category: {r.get('food_category', 'N/A')}</p>
        {summary_block}
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

def send_confirmation_email(recipient: str, confirm_url: str):
    subject = "Confirm your Food Recall Alert subscription"

    body = f"""
    <h2>Confirm Your Subscription</h2>
    <p>Thank you for signing up for Food Recall Alerts.</p>
    <p>Click the button below to confirm your email and activate your subscription:</p>
    <p>
        <a href="{confirm_url}" style="
            background-color: #e53e3e;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
        ">Confirm Subscription</a>
    </p>
    <p>If you did not sign up, ignore this email.</p>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = recipient
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, recipient, msg.as_string())