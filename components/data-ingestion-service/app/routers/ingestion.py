import os
import pandas as pd
import requests
from flask import Blueprint, jsonify, request
from app.config import Config
from app.services.data_ingestion import parse_csv, save_local, forward_to_backend

ingestion_bp = Blueprint("ingestion", __name__)


@ingestion_bp.route("/ingest/file", methods=["POST"])
def ingest_raw_file():
    df = parse_csv()
    save_local(df)
    result = forward_to_backend(df)
    return jsonify({"rows": len(df), **result}), 201


@ingestion_bp.route("/ingest/reading", methods=["POST"])
def ingest_reading():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    required = ["entry_id", "temperature", "humidity", "air_quality"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    reading = {
        "entry_id": int(data["entry_id"]),
        "created_at": data.get("created_at", pd.Timestamp.now(tz="UTC").isoformat()),
        "temperature": float(data["temperature"]),
        "humidity": float(data["humidity"]),
        "air_quality": int(data["air_quality"]),
    }

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
