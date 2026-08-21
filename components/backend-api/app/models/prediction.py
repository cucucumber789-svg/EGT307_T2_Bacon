"""ORM model for stored ML predictions."""

from sqlalchemy import Column, Integer, Boolean, Numeric, DateTime, Text

from app.database import Base


class Prediction(Base):
    """An ML verdict for one reading, persisted so the dashboard can show it.

    Mirrors the reading fields plus the model output: is_anomaly flag,
    anomaly_score (signed distance from the IsolationForest boundary),
    severity (0..1), and the alert messages joined into one Text column.
    """

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    temperature = Column(Numeric, nullable=False)
    humidity = Column(Numeric, nullable=False)
    air_quality = Column(Integer, nullable=False)
    is_anomaly = Column(Boolean, nullable=False)
    anomaly_score = Column(Numeric, nullable=False)
    severity = Column(Numeric, nullable=False)
    alerts = Column(Text, nullable=False, default="")
