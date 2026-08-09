"""
Prediction routes blueprint.

Handles anomaly prediction requests. The trained model is held on the Flask
app config (set in app/main.py) and read here via current_app.config.

Routes:
- POST /api/predict       single reading -> prediction
- POST /api/predict/batch {readings:[...]} -> {predictions:[...]}
"""

from flask import Blueprint, current_app, request, jsonify

from app.services import model_service

prediction_bp = Blueprint("prediction", __name__)

REQUIRED_FIELDS = ["entry_id", "created_at", "temperature", "humidity", "air_quality"]


def _get_model():
    return current_app.config["ML_MODEL"]


def _parse_reading(data):
    """Validate a single reading and return (entry_id, created_at, temp, hum, aq)."""
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise ValueError(f"Missing fields: {missing}")
    try:
        return (
            data["entry_id"],
            data["created_at"],
            float(data["temperature"]),
            float(data["humidity"]),
            float(data["air_quality"]),
        )
    except (TypeError, ValueError):
        raise ValueError("temperature, humidity and air_quality must be numbers")


def _run_prediction(data):
    entry_id, created_at, temperature, humidity, air_quality = _parse_reading(data)
    return model_service.predict(
        _get_model(),
        entry_id=entry_id,
        created_at=created_at,
        temperature=temperature,
        humidity=humidity,
        air_quality=air_quality,
    )


@prediction_bp.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
    try:
        result = _run_prediction(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(result), 200


@prediction_bp.route("/predict/batch", methods=["POST"])
def predict_batch():
    data = request.get_json()
    if not data or "readings" not in data:
        return jsonify({"error": "Provide {\"readings\": [...]} payload"}), 400

    predictions = []
    for reading in data["readings"]:
        try:
            predictions.append(_run_prediction(reading))
        except ValueError:
            continue

    return jsonify({"predictions": predictions}), 200
