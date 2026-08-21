"""
notification-service/app/main.py

Notification Service — receives ML-flagged alerts from the Backend API and
sends them via Telegram. This service does NOT make alerting decisions;
the ML model decides what is anomalous and passes alert messages here.
"""

import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()  # auto-load .env from repo root for standalone mode

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Alerts are kept here in memory so the dashboard can GET /api/alerts and
# show them; simple on purpose, resets if the service restarts.
recent_alerts = []


def send_telegram(message):
    """Send one message to the Telegram chat bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured, skipping send:", message)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=5)
    except requests.exceptions.RequestException as e:
        print("Telegram send failed:", e)


def create_app():
    app = Flask(__name__)

    @app.after_request
    def allow_dashboard(response):
        # dashboard.js calls this service straight from the browser, on a
        # different port, so it needs these headers or the browser blocks it.
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.route("/")
    def health():
        return jsonify({
            "status": "ok",
            "service": "notification-service",
            "telegram_configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
        })

    @app.route("/api/notify", methods=["POST"])
    def notify():
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        # The Backend API passes the ML model's alert messages.
        # This service is a pure sender — it does not decide what to alert on.
        triggered = data.get("alerts", [])

        for message in triggered:
            send_telegram(message)
            recent_alerts.insert(0, {
                "message": message,
                "temperature": data.get("temperature"),
                "humidity": data.get("humidity"),
                "air_quality": data.get("air_quality"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        del recent_alerts[50:]  # keep only the 50 most recent

        return jsonify({"triggered": triggered}), 200

    @app.route("/api/alerts", methods=["GET"])
    def get_alerts():
        # This is what the dashboard polls to show alerts.
        return jsonify(recent_alerts)

    return app


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured - alerts will not be sent. See README 'First-time setup'.")
    app = create_app()
    app.run(host="0.0.0.0", port=5002)
