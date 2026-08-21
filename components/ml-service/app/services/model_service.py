"""
Model service — handles loading cleaned sensor data, training the anomaly
detection model, and running predictions.

Design:
- The service trains a scikit-learn IsolationForest on startup from the
  CLEANED dataset produced by the data ingestion service
  (sensor_data_cleaned.csv). It does not do its own cleaning.
- `predict()` uses the IsolationForest anomaly score as the sole alerting
  decision, with an optional safety-net threshold for extreme values.

Usage:
    from app.services.model_service import load_dataset, train_model, predict
"""

import sys

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


def train_if_available(path):
    """Load the cleaned dataset and train, or return None if it does not exist."""
    try:
        df = load_dataset(path)
    except FileNotFoundError:
        return None
    model = train_model(df)
    print(f"Trained model on {len(df)} rows from {path}")
    return model


def predict(model, entry_id, created_at, temperature, humidity, air_quality):
    """Run a prediction on a single reading and return the result payload.

    Alerting is driven entirely by the IsolationForest model score:
    - model.predict() returns -1 for anomalies, 1 for normal
    - model.decision_function() returns the signed distance to the boundary
      (negative = anomaly, positive = normal)

    The only hardcoded check is a safety-net for physically dangerous values
    (e.g. temperature > 50C) that may fall outside the training distribution.
    """
    X = np.array([[temperature, humidity, air_quality]])

    raw_prediction = model.predict(X)[0]       # 1 = normal, -1 = anomaly
    raw_score = model.decision_function(X)[0]  # negative = anomaly

    alerts = []
    if raw_prediction == -1:
        alerts.append(
            f"Anomaly detected: {temperature}\u00b0C / {humidity}% / AQI {air_quality} "
            f"(score: {raw_score:.3f})"
        )

    # Safety-net: absolute maximum for physically dangerous values
    if temperature > Config.ABSOLUTE_MAX_TEMP:
        alerts.append(
            f"CRITICAL: Temperature {temperature}\u00b0C exceeds "
            f"absolute maximum ({Config.ABSOLUTE_MAX_TEMP}\u00b0C)"
        )

    severity = 1 / (1 + np.exp(Config.SEVERITY_STEEPNESS * raw_score))

    return {
        "entry_id": entry_id,
        "created_at": created_at,
        "is_anomaly": bool(alerts),
        "anomaly_score": round(float(raw_score), 5),
        "severity": round(float(severity), 4),
        "alerts": alerts,
        "readings": {
            "temperature": temperature,
            "humidity": humidity,
            "air_quality": air_quality,
        },
    }


def _print_prediction(result):
    print(
        f"  entry_id={result['entry_id']} "
        f"anomaly={result['is_anomaly']} "
        f"score={result['anomaly_score']} "
        f"severity={result['severity']} "
        f"alerts={result['alerts']}"
    )


if __name__ == "__main__":
    path = Config.DATASET_PATH
    model = train_if_available(path)
    if model is None:
        print(
            "Model not trained: no cleaned dataset available at "
            f"{path}. Register data via the data-ingestion service first."
        )
        sys.exit(1)

    df = load_dataset(path)
    print("Sample predictions (first 3 dataset readings):")
    for row in df.head(3).to_dict(orient="records"):
        _print_prediction(predict(
            model,
            entry_id=row["entry_id"],
            created_at=row["created_at"],
            temperature=row["temperature"],
            humidity=row["humidity"],
            air_quality=row["air_quality"],
        ))

    print("\nSynthetic anomaly (40C / 80% / AQI 5):")
    _print_prediction(predict(
        model,
        entry_id=-1,
        created_at="2026-01-01T00:00:00+00:00",
        temperature=40.0,
        humidity=80.0,
        air_quality=5,
    ))
