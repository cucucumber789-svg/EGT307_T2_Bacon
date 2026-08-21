"""Ingestion routes.

Entry point for sensor data:
- POST /api/ingest/reading  one live reading (used by the sensor simulator)
- POST /api/ingest/file     clean the raw CSV dataset and register it
"""

import pandas as pd
import requests
from flask import Blueprint, jsonify, request

from app.config import Config
from app.services.data_ingestion import parse_csv, save_local, forward_to_backend

ingestion_bp = Blueprint("ingestion", __name__)


@ingestion_bp.route("/ingest/file", methods=["POST"])
def ingest_raw_file():
    """Clean the raw CSV in DATA_DIR, save the cleaned copy, and push it to the Backend API."""
    df = parse_csv()
    save_local(df)
    result = forward_to_backend(df)
    return jsonify({"rows": len(df), **result}), 201


@ingestion_bp.route("/ingest/reading", methods=["POST"])
def ingest_reading():
    """Validate one reading and forward it to the Backend API batch endpoint.

    Coerces fields to their storage types and stamps created_at when the
    sender omitted it. Malformed values are a client error (400), not a crash.
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    required = ["entry_id", "temperature", "humidity", "air_quality"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        reading = {
            "entry_id": int(data["entry_id"]),
            "created_at": data.get("created_at", pd.Timestamp.now(tz="UTC").isoformat()),
            "temperature": float(data["temperature"]),
            "humidity": float(data["humidity"]),
            "air_quality": int(data["air_quality"]),
        }
    except (TypeError, ValueError) as e:
        # Non-numeric or unparseable values are client errors, not crashes.
        return jsonify({"error": f"Invalid field value: {e}"}), 400

    try:
        resp = requests.post(
            f"{Config.BACKEND_API_URL}/api/sensors/batch",
            json={"readings": [reading]},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"Backend API error: {str(e)}"}), 502

    return jsonify({"status": "ok", "reading": reading}), 201
