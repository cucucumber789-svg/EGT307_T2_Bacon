"""
Application configuration for ML Service.

Design:
- The service trains on the CLEANED dataset produced by the data ingestion
  service (sensor_data_cleaned.csv), NOT raw data.
- All values are loaded from environment variables with sensible local
  defaults, so no secrets or machine-specific values live in code.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # auto-load .env from repo root for standalone mode


class Config:
    # Dataset produced by the ingestion service. Relative default resolves
    # to components/database/ when run from components/ml-service/.
    DATASET_PATH = os.environ.get(
        "DATASET_PATH",
        "../database/sensor_data_cleaned.csv",
    )

    PORT = int(os.environ.get("PORT", "5001"))

    FEATURES = ["temperature", "humidity", "air_quality"]

    # IsolationForest hyperparameters
    N_ESTIMATORS = int(os.environ.get("N_ESTIMATORS", "200"))
    CONTAMINATION = float(os.environ.get("CONTAMINATION", "0.02"))
    RANDOM_STATE = int(os.environ.get("RANDOM_STATE", "42"))

    # Alert thresholds (env-overridable)
    TEMP_LOW = float(os.environ.get("TEMP_LOW", "25.0"))
    TEMP_HIGH = float(os.environ.get("TEMP_HIGH", "30.0"))
    HUMIDITY_LOW = float(os.environ.get("HUMIDITY_LOW", "60.0"))
    HUMIDITY_HIGH = float(os.environ.get("HUMIDITY_HIGH", "77.0"))
    AIR_QUALITY_HIGH = float(os.environ.get("AIR_QUALITY_HIGH", "49.0"))

    # How sharply severity rises from 0 to 1 near the threshold
    SEVERITY_STEEPNESS = float(os.environ.get("SEVERITY_STEEPNESS", "10.0"))
