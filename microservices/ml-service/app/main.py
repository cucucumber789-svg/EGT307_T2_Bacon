"""
Flask application entry point for ML Service.

Intention:
- Wait for the cleaned dataset (produced by the data ingestion service)
- Train the IsolationForest model once at startup
- Register the prediction blueprint and provide a health-check endpoint
"""

import os
import time

from flask import Flask, jsonify

from app.config import Config
from app.routers.prediction import prediction_bp
from app.services import model_service


def wait_for_dataset(path, timeout=30.0):
    """Wait for the cleaned dataset to appear before training."""
    waited = 0.0
    while not os.path.exists(path):
        if waited >= timeout:
            raise FileNotFoundError(
                f"Cleaned dataset not found at {path}. "
                "Run the data ingestion service first so it can produce "
                "sensor_data_cleaned.csv."
            )
        time.sleep(0.5)
        waited += 0.5


def create_app():
    app = Flask(__name__)

    wait_for_dataset(Config.DATASET_PATH)
    df = model_service.load_dataset(Config.DATASET_PATH)
    app.config["ML_MODEL"] = model_service.train_model(df)

    app.register_blueprint(prediction_bp, url_prefix="/api")

    @app.route("/")
    def health():
        return jsonify({"status": "ok", "service": "ml-service"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT)
