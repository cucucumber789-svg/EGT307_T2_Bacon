"""Notification API routes for sending alerts and viewing notification history."""

from flask import Blueprint, request, jsonify

from app.config import Config
from app.services.alert_service import (
    format_alert_message,
    send_email_alert,
    send_telegram_alert,
    send_sms_alert,
    log_notification,
    get_history,
)

notification_bp = Blueprint("notification", __name__)


@notification_bp.route("/notify", methods=["POST"])
def notify():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    score = data.get("anomaly_score")

    # Below-threshold readings are logged but not sent, so callers can still
    # see them in /api/notifications without triggering a real alert.
    if score is not None and score < Config.ALERT_THRESHOLD:
        record = log_notification({
            "entry_id": data.get("entry_id"),
            "anomaly_score": score,
            "status": "skipped",
            "reason": f"anomaly_score below ALERT_THRESHOLD ({Config.ALERT_THRESHOLD})",
        })
        return jsonify({"message": "Below alert threshold, no notification sent", "notification": record}), 200

    subject, body = format_alert_message(data)

    # Attempt every channel that has its config set; skip the rest.
    channels = {}
    if Config.ALERT_EMAIL_TO:
        sent, error = send_email_alert(subject, body)
        channels["email"] = {"status": "sent" if sent else "failed", "error": error}
    if Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID:
        sent, error = send_telegram_alert(f"{subject}\n\n{body}")
        channels["telegram"] = {"status": "sent" if sent else "failed", "error": error}
    if Config.SMS_API_URL:
        sent, error = send_sms_alert(body)
        channels["sms"] = {"status": "sent" if sent else "failed", "error": error}

    if not channels:
        record = log_notification({
            "entry_id": data.get("entry_id"),
            "anomaly_score": score,
            "status": "failed",
            "channels": {},
            "error": "No notification channel configured (set ALERT_EMAIL_TO, "
                     "TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID, or SMS_API_URL)",
        })
        return jsonify({"message": "No notification channel configured", "notification": record}), 502

    any_sent = any(c["status"] == "sent" for c in channels.values())
    record = log_notification({
        "entry_id": data.get("entry_id"),
        "anomaly_score": score,
        "status": "sent" if any_sent else "failed",
        "channels": channels,
    })

    if not any_sent:
        return jsonify({"message": "All configured channels failed", "notification": record}), 502

    return jsonify({"message": "Alert sent", "notification": record}), 201


@notification_bp.route("/notifications", methods=["GET"])
def notifications():
    limit = request.args.get("limit", 100, type=int)
    return jsonify(get_history(limit))
