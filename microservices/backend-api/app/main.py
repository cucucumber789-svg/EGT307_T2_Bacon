from flask import Flask, jsonify

from app.database import engine, Base
from app.models import prediction, sensor
from app.routers.prediction import prediction_bp
from app.routers.sensor import sensor_bp


def create_app():
    app = Flask(__name__)

    Base.metadata.create_all(bind=engine)

    app.register_blueprint(sensor_bp, url_prefix="/api")
    app.register_blueprint(prediction_bp, url_prefix="/api")

    @app.after_request
    def allow_dashboard(response):
        # The frontend dashboard calls this service straight from the
        # browser on a different port, so it needs these headers or the
        # browser blocks the requests.
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.route("/")
    def health():
        return jsonify({"status": "ok", "service": "backend-api"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
