"""
Prediction routes blueprint.

Handles anomaly prediction requests. The trained model is held on the Flask
app config (set in app/main.py or trained lazily here) and read via
current_app.config.

Routes:
- POST /api/predict       single reading -> prediction
- POST /api/predict/batch {readings:[...]} -> {predictions:[...]}

When no cleaned dataset exists yet, the model is not trained and requests
return 503 instead of crashing, so the ML service stays decoupled from
the data-ingestion service.
"""

import threading

from flask import Blueprint, current_app, request, jsonify

from app.config import Config
from app.services import model_service

prediction_bp = Blueprint("prediction", __name__)

REQUIRED_FIELDS = ["entry_id", "created_at", "temperature", "humidity", "air_quality"]

_train_lock = threading.Lock()


def _ensure_model():
    """Return the trained model, training it lazily if data is now available.

    Returns None when the cleaned dataset still does not exist.
    """
    model = current_app.config["ML_MODEL"]
    if model is not None:
        return model

    with _train_lock:
        model = current_app.config["ML_MODEL"]
        if model is not None:
            return model
        try:
            df = model_service.load_dataset(Config.DATASET_PATH)
            model = model_service.train_model(df)
            current_app.config["ML_MODEL"] = model
            print(f"Lazily trained model on {len(df)} rows from {Config.DATASET_PATH}")
        except FileNotFoundError:
            return None
    return model


def _model_unavailable():
    return jsonify({
        "error": (
            "Model not trained: no cleaned dataset available at "
            f"{Config.DATASET_PATH}. Register data via the data-ingestion "
            "service first."
        )
    }), 503


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
        _ensure_model(),
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
    if _ensure_model() is None:
        return _model_unavailable()
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
    if _ensure_model() is None:
        return _model_unavailable()

    predictions = []
    for reading in data["readings"]:
        try:
            predictions.append(_run_prediction(reading))
        except ValueError:
            continue

    return jsonify({"predictions": predictions}), 200
