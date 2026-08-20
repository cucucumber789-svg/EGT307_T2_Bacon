import os

from dotenv import load_dotenv

load_dotenv()  # auto-load .env from repo root for standalone mode


class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/env_monitor")
    ML_SERVICE_URL = os.environ.get("ML_SERVICE_URL", "http://localhost:5001")
    NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5002")
