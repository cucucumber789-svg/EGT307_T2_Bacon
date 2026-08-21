"""Sensor ingestion routes.

Readings enter the system here (pushed by the data-ingestion service or
posted directly) and are persisted in Postgres. Batch ingestion also asks
the ML service for anomaly predictions so the dashboard can display them.
"""

import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from app.database import SessionLocal
from app.models.sensor import SensorReading
from app.services import ml_client
from app.services.prediction_service import store_prediction

sensor_bp = Blueprint("sensor", __name__)

logger = logging.getLogger(__name__)

# Fields every reading must carry; anything else is rejected/skipped.
REQUIRED_FIELDS = ["created_at", "entry_id", "temperature", "humidity", "air_quality"]


def _parse_reading(data):
    """Convert raw JSON fields into a SensorReading, or raise ValueError.

    Coerces numeric fields to their storage types so bad values surface
    here as a client error instead of failing at database flush time.
    """
    return SensorReading(
        created_at=datetime.fromisoformat(data["created_at"]),
        entry_id=int(data["entry_id"]),
        temperature=float(data["temperature"]),
        humidity=float(data["humidity"]),
        air_quality=int(data["air_quality"]),
    )


@sensor_bp.route("/sensors", methods=["GET"])
def list_sensors():
    """Return the most recent readings, newest first (for dashboard charts)."""
    limit = request.args.get("limit", 100, type=int)
    db = SessionLocal()
    try:
        readings = db.query(SensorReading).order_by(SensorReading.created_at.desc()).limit(limit).all()
        return jsonify([{
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "entry_id": r.entry_id,
            "temperature": float(r.temperature),
            "humidity": float(r.humidity),
            "air_quality": r.air_quality,
        } for r in readings])
    finally:
        db.close()


@sensor_bp.route("/sensors/count", methods=["GET"])
def sensor_count():
    """Return the total number of stored readings."""
    db = SessionLocal()
    try:
        count = db.query(func.count(SensorReading.id)).scalar()
        return jsonify({"count": count})
    finally:
        db.close()


@sensor_bp.route("/sensors", methods=["POST"])
def create_sensor():
    """Store a single reading; 400 when the payload is missing or malformed."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        reading = _parse_reading(data)
    except (TypeError, ValueError) as e:
        # Bad timestamp or non-numeric values are client errors, not crashes.
        return jsonify({"error": f"Invalid field value: {e}"}), 400

    db = SessionLocal()
    try:
        db.add(reading)
        db.commit()
        return jsonify({"message": "Reading created", "id": reading.id}), 201
    finally:
        db.close()


@sensor_bp.route("/sensors/batch", methods=["POST"])
def create_sensors_batch():
    """Store a batch of readings, then fetch ML predictions for exactly what was stored.

    Items missing required fields or with unparseable values are skipped so one
    bad row cannot fail the whole batch. The ML call is best-effort: ingestion
    must not fail when the ML service is unavailable.
    """
    data = request.get_json()
    if not data or "readings" not in data:
        return jsonify({"error": "Provide {\"readings\": [...]} payload"}), 400

    valid_readings = []
    db = SessionLocal()
    try:
        for r in data["readings"]:
            if not all(f in r for f in REQUIRED_FIELDS):
                continue
            try:
                db.add(_parse_reading(r))
                valid_readings.append(r)
            except (TypeError, ValueError):
                continue
        db.commit()
    finally:
        db.close()

    count = len(valid_readings)

    # Best-effort: ask the ML service for anomaly predictions on the batch
    # and persist them so the dashboard can show them. Ingestion must not
    # fail if the ML service is unavailable.
    if count > 0:
        try:
            resp = ml_client.predict_batch(valid_readings)
            for pred in resp.get("predictions", []):
                store_prediction(pred)
        except Exception as e:
            # Predictions are supplementary; log and keep the ingestion result.
            logger.warning("ML prediction step failed for batch: %s", e)

    return jsonify({"message": f"{count} readings created", "count": count}), 201
