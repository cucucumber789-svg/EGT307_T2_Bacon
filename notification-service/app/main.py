"""Flask application entry point."""

from flask import Flask, jsonify

from app.routers.notification import notification_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(notification_bp, url_prefix="/api")

    @app.route("/")
    def health():
        return jsonify({"status": "ok", "service": "notification-service"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5002)
