import os
import pandas as pd
import requests
from app.config import Config


def parse_csv():
    df = pd.read_csv(os.path.join(Config.DATA_DIR, "sensor_data.example.csv"))

    # drop empty columns
    df = df.drop(columns=["latitude", "longitude", "elevation", "status"])
    df = df.drop(columns=["field4"])

    # rename fields
    df = df.rename(columns={"field1": "temperature", "field2": "humidity", "field3": "air_quality"})

    # fix types
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df[["temperature", "humidity", "air_quality"]] = df[["temperature", "humidity", "air_quality"]].apply(pd.to_numeric, errors="coerce")

    # handle missing values
    df = df.dropna(subset=["created_at", "temperature", "humidity", "air_quality"])

    return df


def save_local(df):
    df.to_csv(os.path.join(Config.DATA_DIR, "sensor_data_cleaned.csv"), index=False)


def forward_to_backend(df):
    records = df.to_dict(orient="records")
    for r in records:
        r["created_at"] = r["created_at"].isoformat()
    resp = requests.post(f"{Config.BACKEND_API_URL}/api/sensors/batch", json={"readings": records})
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    df = parse_csv()
    save_local(df)
    print(f"Cleaned {len(df)} rows -> sensor_data_cleaned.csv")
