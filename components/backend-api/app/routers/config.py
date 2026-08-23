"""Config routes blueprint.

Routes:
- GET /api/config  non-sensitive config values for the frontend dashboard
"""

from flask import Blueprint, jsonify

from app.config import Config, _yaml

config_bp = Blueprint("config", __name__)


@config_bp.route("/config", methods=["GET"])
def get_config():
    """Return non-sensitive config values used by the frontend."""
    ml = _yaml.get("ml_service", {})
    sensor = _yaml.get("sensor_simulator", {})
    return jsonify({
        "notification_threshold": Config.ANOMALY_SCORE_THRESHOLD,
        "model_contamination": float(ml.get("contamination", 0.02)),
        "severity_steepness": float(ml.get("severity_steepness", 10.0)),
        "sensor_send_interval_seconds": max(
            0.1,
            float(sensor.get("send_interval_seconds", 3)),
        ),
    })
