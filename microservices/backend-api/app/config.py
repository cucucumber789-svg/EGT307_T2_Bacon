import os


class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/env_monitor")
    ML_SERVICE_URL = os.environ.get("ML_SERVICE_URL", "http://localhost:5001")
    NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5002")
