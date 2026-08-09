"""
Prediction routes blueprint.

Routes:
- POST /api/predict      validate reading -> call ML service -> store + return
- GET  /api/predictions  most recent stored predictions (frontend dashboard)
"""

import requests
from flask import Blueprint, request, jsonify

from app.database import SessionLocal
from app.models.prediction import Prediction
from app.services import ml_client
from app.services.prediction_service import store_prediction, prediction_to_json

prediction_bp = Blueprint("prediction", __name__)

REQUIRED_FIELDS = ["entry_id", "created_at", "temperature", "humidity", "air_quality"]


@prediction_bp.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        result = ml_client.predict_reading(data)
    except requests.HTTPError as e:
        # Pass through ML-service errors as-is (e.g. 503 model not trained yet).
        if e.response is not None:
            try:
                detail = e.response.json().get("error", str(e))
            except ValueError:
                detail = str(e)
            return jsonify({"error": detail}), e.response.status_code
        return jsonify({"error": f"ML service error: {e}"}), 502
    except Exception as e:
        return jsonify({"error": f"ML service error: {e}"}), 502

    store_prediction(result)
    return jsonify(result), 201


@prediction_bp.route("/predictions", methods=["GET"])
def list_predictions():
    limit = request.args.get("limit", 100, type=int)
    db = SessionLocal()
    try:
        rows = (
            db.query(Prediction)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
            .all()
        )
        return jsonify([prediction_to_json(r) for r in rows])
    finally:
        db.close()
