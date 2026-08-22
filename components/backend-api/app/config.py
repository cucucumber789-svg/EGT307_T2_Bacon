"""Backend API configuration.

All values come from environment variables (docker-compose / k8s) with
localhost defaults so the service also runs standalone during development.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # auto-load .env from repo root for standalone mode


class Config:
    # Postgres connection string used by SQLAlchemy.
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/env_monitor")
    # Base URL of the ML microservice that produces anomaly predictions.
    ML_SERVICE_URL = os.environ.get("ML_SERVICE_URL", "http://localhost:5001")
    # Base URL of the Notification microservice used to send anomaly alerts.
    NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5002")

    # Minimum severity for an anomaly to trigger a Telegram notification.
    # Anomalies below this threshold are still stored in the DB and shown
    # on the dashboard, but do not notify — reducing alert fatigue.
    SEVERITY_NOTIFY_THRESHOLD = float(os.environ.get("SEVERITY_NOTIFY_THRESHOLD", "0.3"))
