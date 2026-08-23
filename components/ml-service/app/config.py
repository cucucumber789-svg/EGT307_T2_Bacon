"""
Application configuration for ML Service.

Secrets and deployment-specific values come from environment variables.
Non-sensitive tuning values come from config.yaml at the repo root.

Design:
- The service trains on the CLEANED dataset produced by the data ingestion
  service (sensor_data_cleaned.csv), NOT raw data.
- Alerting is driven by the IsolationForest model, not hardcoded thresholds.
  The only safety net is ABSOLUTE_MAX_TEMP for physically dangerous values.
"""

import os

import yaml
from dotenv import load_dotenv

load_dotenv()  # auto-load .env from repo root for standalone mode


def _load_yaml():
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in [
        os.path.join(here, "..", "config.yaml"),
        os.path.join(here, "..", "..", "config.yaml"),
        "config.yaml",
    ]:
        if os.path.isfile(candidate):
            with open(candidate) as f:
                return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml()
_ml = _yaml.get("ml_service", {})


class Config:
    DATASET_PATH = os.environ.get(
        "DATASET_PATH",
        "../database/sensor_data_cleaned.csv",
    )

    PORT = int(os.environ.get("PORT", "5001"))

    FEATURES = ["temperature", "humidity", "air_quality"]

    # IsolationForest hyperparameters (from config.yaml)
    N_ESTIMATORS = int(_ml.get("n_estimators", 200))
    N_ESTIMATORS = max(1, N_ESTIMATORS)
    CONTAMINATION = float(_ml.get("contamination", 0.02))
    CONTAMINATION = max(0.0, min(1.0, CONTAMINATION))
    RANDOM_STATE = int(os.environ.get("RANDOM_STATE", "42"))

    # Safety-net threshold (from config.yaml)
    ABSOLUTE_MAX_TEMP = float(_ml.get("absolute_max_temp", 50.0))

    # Severity sigmoid steepness (from config.yaml)
    SEVERITY_STEEPNESS = float(_ml.get("severity_steepness", 10.0))
    SEVERITY_STEEPNESS = max(0.01, SEVERITY_STEEPNESS)
