from flask import Flask, jsonify

from app.routers.ingestion import ingestion_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(ingestion_bp, url_prefix="/api")

    @app.route("/")
    def health():
        return jsonify({"status": "ok", "service": "data-ingestion-service"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5003)
