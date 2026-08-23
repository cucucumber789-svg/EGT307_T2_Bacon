"""
Flask application entry point for ML Service.

Intention:
- Start regardless of whether the cleaned dataset exists yet
- Train the IsolationForest model at startup when data is available,
  otherwise start idle and train lazily on the first predict request
- Register the prediction blueprint and provide a health-check endpoint
"""

from flask import Flask, jsonify

from app.config import Config
from app.routers.prediction import prediction_bp
from app.services import model_service


def create_app():
    app = Flask(__name__)

    import logging
    logging.getLogger("werkzeug").setLevel("WARNING")

    # Best-effort initial training: if the cleaned dataset already exists
    # (e.g. produced by the data-ingestion service), be ready immediately.
    # If not, start with ML_MODEL = None; the prediction routes retry
    # loading and training on demand instead of the service failing.
    app.config["ML_MODEL"] = model_service.train_if_available(Config.DATASET_PATH)
    if app.config["ML_MODEL"] is None:
        print(f"No cleaned dataset at {Config.DATASET_PATH} yet - starting idle.")

    app.register_blueprint(prediction_bp, url_prefix="/api")

    @app.route("/")
    def health():
        # Liveness probe; model_ready tells callers whether predictions work yet.
        return jsonify({
            "status": "ok",
            "service": "ml-service",
            "model_ready": app.config["ML_MODEL"] is not None,
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT)
