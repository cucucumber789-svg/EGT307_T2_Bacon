"""Data ingestion service configuration.

Environment variables with localhost defaults so the service also runs
standalone during development.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # auto-load .env from repo root for standalone mode


class Config:
    # Backend API that stores the readings we forward.
    BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:5000")
    # Folder holding the raw/cleaned CSV datasets (shared volume in Docker).
    DATA_DIR = os.environ.get("DATA_DIR", "../database")
    # Dataset formats this service accepts (informational for now).
    ALLOWED_FORMATS = os.environ.get("ALLOWED_FORMATS", "csv,json").split(",")
