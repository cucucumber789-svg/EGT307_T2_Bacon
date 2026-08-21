"""CSV cleaning and forwarding logic.

Turns the raw example dataset into the cleaned schema used everywhere else
(temperature / humidity / air_quality), saves the cleaned copy for the ML
service, and pushes the rows to the Backend API.
"""

import os
import pandas as pd
import requests
from app.config import Config


def parse_csv():
    """Read the raw CSV from DATA_DIR and return a cleaned DataFrame.

    Drops unused columns, renames field1/2/3 to meaningful names, coerces
    types, and drops any row that is unusable (missing timestamp or values).
    """
    df = pd.read_csv(os.path.join(Config.DATA_DIR, "sensor_data.example.csv"))

    # drop empty columns
    df = df.drop(columns=["latitude", "longitude", "elevation", "status"])
    df = df.drop(columns=["field4"])

    # rename fields
    df = df.rename(columns={"field1": "temperature", "field2": "humidity", "field3": "air_quality"})

    # fix types; errors="coerce" turns bad cells into NaN so dropna removes them
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df[["temperature", "humidity", "air_quality"]] = df[["temperature", "humidity", "air_quality"]].apply(pd.to_numeric, errors="coerce")

    # handle missing values
    df = df.dropna(subset=["created_at", "temperature", "humidity", "air_quality"])

    return df


def save_local(df):
    """Write the cleaned dataset next to the raw one.

    The ML service reads this file (DATASET_PATH) to train its model.
    """
    df.to_csv(os.path.join(Config.DATA_DIR, "sensor_data_cleaned.csv"), index=False)


def forward_to_backend(df):
    """POST all cleaned rows to the Backend API batch endpoint; returns its JSON reply."""
    records = df.to_dict(orient="records")
    for r in records:
        r["created_at"] = r["created_at"].isoformat()
    resp = requests.post(f"{Config.BACKEND_API_URL}/api/sensors/batch", json={"readings": records})
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    # CLI mode: clean the dataset locally without calling the Backend API.
    df = parse_csv()
    save_local(df)
    print(f"Cleaned {len(df)} rows -> sensor_data_cleaned.csv")
