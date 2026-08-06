from flask import Flask, jsonify

from app.database import engine, Base
from app.routers.sensor import sensor_bp


def create_app():
    app = Flask(__name__)

    Base.metadata.create_all(bind=engine)

    app.register_blueprint(sensor_bp, url_prefix="/api")

    @app.route("/")
    def health():
        return jsonify({"status": "ok", "service": "backend-api"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
