"""
notification-service/app/main.py

Notification Service - checks each incoming sensor reading against 3
simple thresholds, and if one is crossed: sends a Telegram message and
saves the alert so the dashboard can display it.

    temperature > 39   -> "High temperature detected!"
    humidity    > 55   -> "High humidity detected!"
    air_quality <= 2   -> "Poor air quality detected!"
"""

import os
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Thresholds are config, not secrets - overridable per deployment.
TEMP_THRESHOLD = float(os.environ.get("TEMP_THRESHOLD", "39"))
HUMIDITY_THRESHOLD = float(os.environ.get("HUMIDITY_THRESHOLD", "55"))
AQ_THRESHOLD = float(os.environ.get("AQ_THRESHOLD", "2"))

# Alerts are kept here in memory so the dashboard can GET /api/alerts and
# show them; simple on purpose, resets if the service restarts.
recent_alerts = []


def check_conditions(temperature, humidity, air_quality):
    #"Compare one reading against the 3 thresholds, return the alert messages that apply."
    messages = []
    if temperature > TEMP_THRESHOLD:
        messages.append("High temperature detected!")
    if humidity > HUMIDITY_THRESHOLD:
        messages.append("High humidity detected!")
    if air_quality <= AQ_THRESHOLD:
        messages.append("Poor air quality detected!")
    return messages


def send_telegram(message):
    #"Send one message to the Telegram chat bot"
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

        required = ["temperature", "humidity", "air_quality"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        air_quality = float(data["air_quality"])

        # When the Backend API triggers us, it passes the ML model's alert
        # messages so Telegram text matches what the model flagged. A direct
        # call (e.g. the dashboard) omits them and we derive them ourselves.
        provided = data.get("alerts")
        triggered = provided if provided else check_conditions(temperature, humidity, air_quality)

        for message in triggered:
            send_telegram(message)
            recent_alerts.insert(0, {
                "message": message,
                "temperature": temperature,
                "humidity": humidity,
                "air_quality": air_quality,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        del recent_alerts[50:]  # keep only the 50 most recent, so this can't grow forever

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
