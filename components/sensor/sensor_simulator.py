"""
Sensor Simulator

This program simulates an IoT sensor by reading data from a CSV file.
It sends one reading at a time to the Data Ingestion Service every few
seconds. When it reaches the end of the dataset, it starts again from
the beginning to simulate a continuous sensor.

Each loop pass applies random jitter to values and uses unique entry_ids
so readings look diverse. Synthetic anomalies (~5% chance) inject extreme
values to trigger ML alerts for demo purposes.
"""

import os
import random
import time
from datetime import datetime, timezone

import pandas as pd
import requests
import yaml

# ======================================================
# Configuration
# Set the dataset location and Data Ingestion Service URL.
# ======================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(SCRIPT_DIR, "..", "database")


def _load_yaml():
    for candidate in [
        os.path.join(SCRIPT_DIR, "config.yaml"),
        os.path.join(SCRIPT_DIR, "..", "..", "config.yaml"),
        "config.yaml",
    ]:
        if os.path.isfile(candidate):
            with open(candidate) as f:
                return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml()
_sensor = _yaml.get("sensor_simulator", {})


DATASET_PATH = os.environ.get(
    "DATASET_PATH",
    os.path.join(DATABASE_DIR, "validation_data.example.csv")
)

DATA_INGESTION_URL = os.environ.get(
    "DATA_INGESTION_URL",
    "http://data-ingestion-service:5003/api/ingest/reading"
)

SEND_INTERVAL_SECONDS = float(
    os.environ.get("SEND_INTERVAL_SECONDS", str(_sensor.get("send_interval_seconds", 3)))
)
SEND_INTERVAL_SECONDS = max(0.1, SEND_INTERVAL_SECONDS)

# Anomaly injection rate: synthetic anomalies injected into the stream
ANOMALY_RATE = float(os.environ.get("ANOMALY_RATE", str(_sensor.get("anomaly_rate", 0.05))))
ANOMALY_RATE = max(0.0, min(1.0, ANOMALY_RATE))

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
    """Read the CSV and keep only the columns needed for a reading.

    Renames field1/2/3 to meaningful names and drops rows with missing
    values so every sent reading is complete.
    """

    df = pd.read_csv(path)

    df = df.rename(columns=COLUMN_MAP)

    df = df[
        ["entry_id", "temperature", "humidity", "air_quality"]
    ]

    df = df.dropna()

    return df.reset_index(drop=True)


# ======================================================
# Create Sensor Reading
# Convert one row into a sensor reading with jitter.
# ======================================================

def build_reading(row, entry_id_counter):
    """Convert one dataset row into the JSON payload the API expects.

    Adds random jitter to temperature (+/-2), humidity (+/-5), and
    air_quality (+/-1) so each loop pass produces diverse readings.
    Uses a counter for unique entry_ids across loop passes.
    """

    temperature = float(row["temperature"]) + random.uniform(-2.0, 2.0)
    humidity = float(row["humidity"]) + random.uniform(-5.0, 5.0)
    air_quality = int(row["air_quality"]) + random.randint(-1, 1)

    # Clamp to realistic ranges
    temperature = max(15.0, min(50.0, temperature))
    humidity = max(20.0, min(100.0, humidity))
    air_quality = max(1, min(5, air_quality))

    return {

        "entry_id": entry_id_counter,

        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "temperature": round(temperature, 2),

        "humidity": round(humidity, 2),

        "air_quality": air_quality

    }


# ======================================================
# Synthetic Anomaly Generator
# Create extreme readings to trigger ML alerts.
# ======================================================

def build_anomaly_reading(entry_id_counter):
    """Generate a synthetic anomaly with extreme values.

    Randomly picks one of three anomaly types: extreme temperature,
    extreme humidity, or extreme air quality. These are designed to
    be flagged by the IsolationForest model.
    """

    anomaly_type = random.choice(["temp", "humidity", "aq"])

    if anomaly_type == "temp":
        temperature = random.uniform(40.0, 55.0)
        humidity = random.uniform(60.0, 80.0)
        air_quality = random.randint(2, 4)
    elif anomaly_type == "humidity":
        temperature = random.uniform(25.0, 35.0)
        humidity = random.uniform(85.0, 100.0)
        air_quality = random.randint(2, 4)
    else:
        temperature = random.uniform(25.0, 35.0)
        humidity = random.uniform(60.0, 80.0)
        air_quality = random.choice([1, 5])

    return {

        "entry_id": entry_id_counter,

        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "temperature": round(temperature, 2),

        "humidity": round(humidity, 2),

        "air_quality": air_quality

    }


# ======================================================
# Send Sensor Reading
# Send one reading to the Data Ingestion Service.
# ======================================================

def send_reading(reading):
    """POST one reading to the Data Ingestion Service.

    Never raises: a simulator must keep running when the service is
    temporarily down, so failures are printed and the loop continues.
    """

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
    """Replay the dataset forever, one reading every SEND_INTERVAL_SECONDS.

    Each loop pass applies jitter and uses unique entry_ids.
    ~5% of readings are synthetic anomalies to trigger ML alerts.
    """

    print("Sensor Simulator Started")

    dataset = load_dataset(DATASET_PATH)

    entry_id_counter = 1

    while True:

        for _, row in dataset.iterrows():

            if random.random() < ANOMALY_RATE:
                reading = build_anomaly_reading(entry_id_counter)
            else:
                reading = build_reading(row, entry_id_counter)

            entry_id_counter += 1

            send_reading(reading)

            time.sleep(SEND_INTERVAL_SECONDS)


# ======================================================
# Start the Sensor Simulator
# Run the program.
# ======================================================

if __name__ == "__main__":

    main()
