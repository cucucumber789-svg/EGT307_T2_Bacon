"""Backend API configuration.

Secrets (DATABASE_URL, etc.) come from environment variables (.env).
Non-sensitive tuning values come from config.yaml at the repo root.
"""

import os

import yaml
from dotenv import load_dotenv

load_dotenv()  # auto-load .env from repo root for standalone mode


def _load_yaml():
    """Load config.yaml — in Docker it's mounted at /app/config.yaml,
    standalone we search upward to the repo root."""
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in [
        os.path.join(here, "..", "config.yaml"),      # Docker: /app/config.yaml
        os.path.join(here, "..", "..", "config.yaml"), # Standalone: repo root
        "config.yaml",                                  # Running from repo root
    ]:
        if os.path.isfile(candidate):
            with open(candidate) as f:
                return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml()


class Config:
    # --- Secrets (from .env) ---
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/env_monitor")
    ML_SERVICE_URL = os.environ.get("ML_SERVICE_URL", "http://localhost:5001")
    NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5002")

    # --- Non-sensitive (from config.yaml) ---
    # Anomaly score threshold for Telegram notifications.  The IsolationForest
    # score is negative for anomalies; we fire when score < -threshold, so only
    # genuinely anomalous readings notify — mild anomalies are stored but do
    # not alert, reducing alert fatigue.
    ANOMALY_SCORE_THRESHOLD = float(_yaml.get("anomaly_score_threshold", 0.05))
