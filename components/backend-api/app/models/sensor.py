"""ORM model for raw sensor readings."""

from sqlalchemy import Column, Integer, Numeric, DateTime

from app.database import Base


class SensorReading(Base):
    """One measurement from an environmental sensor.

    entry_id identifies the source reading in the original dataset;
    created_at is when the reading was taken (tz-aware).
    """

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    entry_id = Column(Integer, nullable=False)
    temperature = Column(Numeric, nullable=False)   # degrees Celsius
    humidity = Column(Numeric, nullable=False)      # percent
    air_quality = Column(Integer, nullable=False)   # 1 (Good) .. 5 (Hazardous)
