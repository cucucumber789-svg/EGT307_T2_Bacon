from flask import Flask, jsonify

from app.routers.ingestion import ingestion_bp


def create_app():
    app = Flask(__name__)

    import logging
    logging.getLogger("werkzeug").setLevel("WARNING")

    # No data is cleaned at startup: the service starts "empty" so we can
    # simulate a deployment that begins with no raw data. The cleaned
    # dataset is produced on demand via POST /api/ingest/file, and the ML
    # service picks it up lazily on the next prediction request.

    app.register_blueprint(ingestion_bp, url_prefix="/api")

    @app.route("/")
    def health():
        return jsonify({"status": "ok", "service": "data-ingestion-service"})

    return app


if __name__ == "__main__":
    print("data-ingestion listening on :5003")
    app = create_app()
    app.run(host="0.0.0.0", port=5003)
