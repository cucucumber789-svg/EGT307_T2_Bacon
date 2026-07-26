"""
Alert service - handles sending notifications.

Intention:
- Send email alerts via SMTP
- Send SMS alerts via API (if configured)
- Log notification history
- Handle retry logic for failed sends
"""

import smtplib
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from itertools import count

import requests

from app.config import Config

# In-memory notification history. Simple by design (matches the "keep it
# simple" approach used elsewhere in this repo) - history resets if the
# service restarts. Swap for a database table later if that becomes a problem.
_history = []
_next_id = count(1)


def format_alert_message(data):
    """Build an email subject/body from an incoming /api/notify payload."""
    entry_id = data.get("entry_id", "unknown")
    score = data.get("anomaly_score")

    subject = f"[ALERT] Anomaly detected - sensor entry {entry_id}"

    lines = [f"An anomaly was detected for sensor entry {entry_id}."]
    if score is not None:
        lines.append(f"Anomaly score: {score}")
    for field in ("temperature", "humidity", "air_quality"):
        if field in data:
            lines.append(f"{field.replace('_', ' ').title()}: {data[field]}")
    if data.get("message"):
        lines.append(f"Note: {data['message']}")

    return subject, "\n".join(lines)


def _with_retries(send_fn):
    """
    Call send_fn() up to MAX_RETRIES times, retrying on any exception.
    send_fn takes no arguments, performs the network call, and raises on
    failure. Shared by every channel below so they all retry the same way.

    Returns (success: bool, error: str | None).
    """
    last_error = None
    for attempt in range(1, Config.MAX_RETRIES + 1):
        try:
            send_fn()
            return True, None
        except Exception as exc:
            last_error = str(exc)
            if attempt < Config.MAX_RETRIES:
                time.sleep(Config.RETRY_DELAY_SECONDS)

    return False, last_error


def send_email_alert(subject, body, to=None):
    """
    Send an email alert via SMTP, retrying on transient failures.

    Returns (success: bool, error: str | None).
    """
    recipients = to or Config.ALERT_EMAIL_TO
    if not recipients:
        return False, "No recipients configured (set ALERT_EMAIL_TO)"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = Config.ALERT_EMAIL_FROM
    msg["To"] = ", ".join(recipients)

    def _send():
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if Config.SMTP_USERNAME:
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.sendmail(Config.ALERT_EMAIL_FROM, recipients, msg.as_string())

    return _with_retries(_send)


def send_telegram_alert(message, chat_id=None):
    """
    Send an alert via a Telegram bot, using the Bot API's sendMessage
    method (https://core.telegram.org/bots/api#sendmessage) - a plain
    HTTP POST, so no extra dependency beyond `requests`.

    Skipped entirely unless TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are
    both set. Retries the same way as email.

    Returns (success: bool, error: str | None).
    """
    if not Config.TELEGRAM_BOT_TOKEN:
        return False, "Telegram not configured (TELEGRAM_BOT_TOKEN is empty)"

    chat_id = chat_id or Config.TELEGRAM_CHAT_ID
    if not chat_id:
        return False, "Telegram not configured (TELEGRAM_CHAT_ID is empty)"

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"

    def _send():
        resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            # Telegram returns HTTP 200 with ok=false for some errors
            # (e.g. bad chat_id), so this isn't caught by raise_for_status.
            raise RuntimeError(data.get("description", "Telegram API returned ok=false"))

    return _with_retries(_send)


def send_sms_alert(message, to=None):
    """
    Send an SMS alert via a generic HTTP API.

    Skipped entirely unless SMS_API_URL is set - no SMS provider has been
    chosen yet (see Architecture.md open decisions). Adjust the payload
    shape below to match whichever provider (Twilio, Vonage, etc.) the
    team ends up using.

    Returns (success: bool, error: str | None).
    """
    if not Config.SMS_API_URL:
        return False, "SMS not configured (SMS_API_URL is empty)"

    try:
        resp = requests.post(
            Config.SMS_API_URL,
            json={"to": to, "message": message},
            headers={"Authorization": f"Bearer {Config.SMS_API_KEY}"},
            timeout=10,
        )
        resp.raise_for_status()
        return True, None
    except Exception as exc:
        return False, str(exc)


def log_notification(entry):
    """Append a record to the in-memory history and return it."""
    record = dict(entry)
    record["id"] = next(_next_id)
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    _history.append(record)
    return record


def get_history(limit=100):
    """Most recent notifications first."""
    return list(reversed(_history))[:limit]
