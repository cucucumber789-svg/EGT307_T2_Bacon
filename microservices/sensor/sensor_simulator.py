"""
Sensor Simulator

This program simulates an IoT sensor by reading data from a CSV file.
It sends one reading at a time to the Data Ingestion Service every few
seconds. When it reaches the end of the dataset, it starts again from
the beginning to simulate a continuous sensor.
"""

import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests

# ======================================================
# Configuration
# Set the dataset location and Data Ingestion Service URL.
# ======================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.environ.get(
    "DATASET_PATH",
    os.path.join(SCRIPT_DIR, "sensor_data.csv")
)

DATA_INGESTION_URL = os.environ.get(
    "DATA_INGESTION_URL",
    "http://data-ingestion-service:5003/api/ingest/reading"
)

SEND_INTERVAL_SECONDS = float(
    os.environ.get("SEND_INTERVAL_SECONDS", "3")
)

# ======================================================
# Column Names
# Rename the CSV columns to meaningful names.
# ======================================================

COLUMN_MAP = {
    "field1": "temperature",
    "field2": "humidity",
    "field3": "air_quality"
}

# ======================================================
# Load Dataset
# Read and prepare the sensor dataset.
# ======================================================

def load_dataset(path):

    df = pd.read_csv(path)

    df = df.rename(columns=COLUMN_MAP)

    df = df[
        ["entry_id", "temperature", "humidity", "air_quality"]
    ]

    df = df.dropna()

    return df.reset_index(drop=True)


# ======================================================
# Create Sensor Reading
# Convert one row into a sensor reading.
# ======================================================

def build_reading(row):

    return {

        "entry_id": int(row["entry_id"]),

        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "temperature": float(row["temperature"]),

        "humidity": float(row["humidity"]),

        "air_quality": int(row["air_quality"])

    }


# ======================================================
# Send Sensor Reading
# Send one reading to the Data Ingestion Service.
# ======================================================

def send_reading(reading):

    try:

        response = requests.post(
            DATA_INGESTION_URL,
            json=reading,
            timeout=5
        )

        if response.status_code in (200, 201):
            print("Reading sent successfully.")
        else:
            print("Failed to send reading.")

    except Exception as error:

        print("Connection Error:", error)


# ======================================================
# Main Program
# Continuously send sensor readings.
# ======================================================

def main():

    print("Sensor Simulator Started")

    dataset = load_dataset(DATASET_PATH)

    while True:

        for _, row in dataset.iterrows():

            reading = build_reading(row)

            send_reading(reading)

            time.sleep(SEND_INTERVAL_SECONDS)


# ======================================================
# Start the Sensor Simulator
# Run the program.
# ======================================================

if __name__ == "__main__":

    main()