from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from app.database import SessionLocal
from app.models.sensor import SensorReading

sensor_bp = Blueprint("sensor", __name__)


@sensor_bp.route("/sensors", methods=["GET"])
def list_sensors():
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
    db = SessionLocal()
    try:
        count = db.query(func.count(SensorReading.id)).scalar()
        return jsonify({"count": count})
    finally:
        db.close()


@sensor_bp.route("/sensors", methods=["POST"])
def create_sensor():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    required = ["created_at", "entry_id", "temperature", "humidity", "air_quality"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    db = SessionLocal()
    try:
        reading = SensorReading(
            created_at=datetime.fromisoformat(data["created_at"]),
            entry_id=data["entry_id"],
            temperature=data["temperature"],
            humidity=data["humidity"],
            air_quality=data["air_quality"],
        )
        db.add(reading)
        db.commit()
        return jsonify({"message": "Reading created", "id": reading.id}), 201
    finally:
        db.close()


@sensor_bp.route("/sensors/batch", methods=["POST"])
def create_sensors_batch():
    data = request.get_json()
    if not data or "readings" not in data:
        return jsonify({"error": "Provide {\"readings\": [...]} payload"}), 400

    readings = data["readings"]
    db = SessionLocal()
    try:
        count = 0
        for r in readings:
            required = ["created_at", "entry_id", "temperature", "humidity", "air_quality"]
            if not all(f in r for f in required):
                continue
            db.add(SensorReading(
                created_at=datetime.fromisoformat(r["created_at"]),
                entry_id=r["entry_id"],
                temperature=r["temperature"],
                humidity=r["humidity"],
                air_quality=r["air_quality"],
            ))
            count += 1
        db.commit()
        return jsonify({"message": f"{count} readings created", "count": count}), 201
    finally:
        db.close()
