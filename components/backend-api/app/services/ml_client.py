"""HTTP client for the ML microservice."""

import requests

from app.config import Config


def predict_reading(payload):
    """Send one reading to the ML service and return the prediction."""
    resp = requests.post(
        f"{Config.ML_SERVICE_URL}/api/predict",
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def predict_batch(payload):
    """Send multiple readings to the ML service and return predictions."""
    resp = requests.post(
        f"{Config.ML_SERVICE_URL}/api/predict/batch",
        json={"readings": payload},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
