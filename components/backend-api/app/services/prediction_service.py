"""Prediction persistence helpers for the Backend API."""

from datetime import datetime

from app.config import Config
from app.database import SessionLocal
from app.models.prediction import Prediction
from app.services import notification_client


def store_prediction(pred):
    """Persist one ML prediction result and return the new row id.

    Anomalies with anomaly_score < -ANOMALY_SCORE_THRESHOLD trigger the
    Notification Service (best-effort) so the team is alerted. Mild anomalies
    are still stored and visible on the dashboard but do not notify,
    reducing alert fatigue.
    """
    reading = pred["readings"]
    db = SessionLocal()
    try:
        row = Prediction(
            entry_id=pred["entry_id"],
            created_at=datetime.fromisoformat(pred["created_at"]),
            temperature=reading["temperature"],
            humidity=reading["humidity"],
            air_quality=int(reading["air_quality"]),
            is_anomaly=pred["is_anomaly"],
            anomaly_score=pred["anomaly_score"],
            severity=pred["severity"],
            alerts=", ".join(pred["alerts"]),
        )
        db.add(row)
        db.commit()
        if pred["is_anomaly"] and pred["anomaly_score"] < -Config.ANOMALY_SCORE_THRESHOLD:
            notification_client.notify_anomaly({
                **reading,
                "alerts": pred["alerts"],
            })
        return row.id
    finally:
        db.close()


def prediction_to_json(row):
    """Serialise a Prediction row for API responses."""
    return {
        "id": row.id,
        "entry_id": row.entry_id,
        "created_at": row.created_at.isoformat(),
        "temperature": float(row.temperature),
        "humidity": float(row.humidity),
        "air_quality": int(row.air_quality),
        "is_anomaly": bool(row.is_anomaly),
        "anomaly_score": float(row.anomaly_score),
        "severity": float(row.severity),
        "alerts": [a for a in row.alerts.split(", ") if a],
    }
