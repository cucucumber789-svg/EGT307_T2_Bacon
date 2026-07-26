"""Configuration for the Notification Service."""

import os


class Config:
    # SMTP / email settings
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

    # Alert email settings
    ALERT_EMAIL_FROM = os.environ.get("ALERT_EMAIL_FROM", SMTP_USERNAME)
    ALERT_EMAIL_TO = [
        addr.strip()
        for addr in os.environ.get("ALERT_EMAIL_TO", "").split(",")
        if addr.strip()
    ]

    # SMS settings (optional - only used if SMS_API_URL is set)
    SMS_API_URL = os.environ.get("SMS_API_URL", "")
    SMS_API_KEY = os.environ.get("SMS_API_KEY", "")

    # Telegram bot settings (optional - only used if both are set)
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

    # Alerting behaviour
    ALERT_THRESHOLD = float(os.environ.get("ALERT_THRESHOLD", 0.8))
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
    RETRY_DELAY_SECONDS = float(os.environ.get("RETRY_DELAY_SECONDS", 2))
