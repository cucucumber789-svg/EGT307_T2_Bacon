"""
Model service — handles loading cleaned sensor data, training the anomaly
detection model, and running predictions.

Design:
- The service trains a scikit-learn IsolationForest on startup from the
  CLEANED dataset produced by the data ingestion service
  (sensor_data_cleaned.csv). It does not do its own cleaning.
- `predict()` combines the IsolationForest anomaly flag with simple alert
  thresholds and returns a single prediction payload.

Usage:
    from app.services.model_service import load_dataset, train_model, predict
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.config import Config


def load_dataset(path):
    """Read the cleaned sensor dataset and select the model features."""
    df = pd.read_csv(path)

    needed = ["entry_id", "created_at"] + Config.FEATURES
    missing = [col for col in needed if col not in df.columns]
    if missing:
        raise ValueError(f"Cleaned dataset missing columns: {missing}")

    df = df[needed].copy()

    # Defensive only: the ingestion service already drops NaN in these
    # columns, but guard against any residual gaps in the cleaned file.
    df[Config.FEATURES] = df[Config.FEATURES].apply(pd.to_numeric, errors="coerce")
    df[Config.FEATURES] = df[Config.FEATURES].interpolate(method="linear").bfill()
    df = df.dropna(subset=Config.FEATURES)

    return df.reset_index(drop=True)


def train_model(df):
    """Train an IsolationForest on the given readings and return the model."""
    X = df[Config.FEATURES].values
    model = IsolationForest(
        n_estimators=Config.N_ESTIMATORS,
        contamination=Config.CONTAMINATION,
        random_state=Config.RANDOM_STATE,
    )
    model.fit(X)
    return model


def check_thresholds(temperature, humidity, air_quality):
    """Compare one reading against the alert thresholds and return alert messages."""
    alerts = []

    if temperature > Config.TEMP_HIGH:
        alerts.append(
            f"High Temperature detected: {temperature}\u00b0C "
            f"(threshold: {Config.TEMP_HIGH}\u00b0C)"
        )
    elif temperature < Config.TEMP_LOW:
        alerts.append(
            f"Low Temperature detected: {temperature}\u00b0C "
            f"(threshold: {Config.TEMP_LOW}\u00b0C)"
        )

    if humidity > Config.HUMIDITY_HIGH:
        alerts.append(
            f"High Humidity detected: {humidity}% "
            f"(threshold: {Config.HUMIDITY_HIGH}%)"
        )
    elif humidity < Config.HUMIDITY_LOW:
        alerts.append(
            f"Low Humidity detected: {humidity}% "
            f"(threshold: {Config.HUMIDITY_LOW}%)"
        )

    if air_quality > Config.AIR_QUALITY_HIGH:
        alerts.append(
            f"Poor Air Quality detected: {air_quality} AQI "
            f"(threshold: {Config.AIR_QUALITY_HIGH} AQI)"
        )

    return alerts


def predict(model, entry_id, created_at, temperature, humidity, air_quality):
    """Run a prediction on a single reading and return the result payload."""
    X = np.array([[temperature, humidity, air_quality]])

    raw_prediction = model.predict(X)[0]       # 1 = normal, -1 = anomaly
    raw_score = model.decision_function(X)[0]  # negative = anomaly, positive = normal
    ml_flagged = raw_prediction == -1

    alerts = check_thresholds(temperature, humidity, air_quality)
    severity = 1 / (1 + np.exp(Config.SEVERITY_STEEPNESS * raw_score))

    return {
        "entry_id": entry_id,
        "created_at": created_at,
        "is_anomaly": bool(ml_flagged or alerts),
        "anomaly_score": round(float(raw_score), 5),
        "severity": round(float(severity), 4),
        "alerts": alerts,
        "readings": {
            "temperature": temperature,
            "humidity": humidity,
            "air_quality": air_quality,
        },
    }
