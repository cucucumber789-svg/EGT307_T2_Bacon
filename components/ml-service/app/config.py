"""
Application configuration for ML Service.

Design:
- The service trains on the CLEANED dataset produced by the data ingestion
  service (sensor_data_cleaned.csv), NOT raw data.
- All values are loaded from environment variables with sensible local
  defaults, so no secrets or machine-specific values live in code.
- Alerting is driven by the IsolationForest model, not hardcoded thresholds.
  The only safety net is ABSOLUTE_MAX_TEMP for physically dangerous values.
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

    # Safety-net threshold: absolute maximum for physically dangerous values.
    # The IsolationForest should catch these, but this is a hard floor.
    ABSOLUTE_MAX_TEMP = float(os.environ.get("ABSOLUTE_MAX_TEMP", "50.0"))

    # How sharply severity rises from 0 to 1 near the decision boundary
    SEVERITY_STEEPNESS = float(os.environ.get("SEVERITY_STEEPNESS", "10.0"))
