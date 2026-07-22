import os


class Config:
    BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:5000")
    DATA_DIR = os.environ.get("DATA_DIR", "../database")
    ALLOWED_FORMATS = os.environ.get("ALLOWED_FORMATS", "csv,json").split(",")
