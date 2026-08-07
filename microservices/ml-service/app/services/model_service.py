"""
Model service — handles loading and running ML predictions.

Intention:
- Load trained ML model from file
- Preprocess input data
- Run prediction and return results

Note: ML framework and model format are TBD.
Possible frameworks: scikit-learn, TensorFlow, PyTorch, Spark MLlib
Possible formats: .pkl, .h5, .pt, .onnx
"""

# TODO: Define load_model(), preprocess(), predict() functions

import os
import pandas as pd
import numpy as np
import json
from sklearn.ensemble import IsolationForest
%matplotlib inline
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify
import threading
import time
import requests

DATA_PATH = "/content/sample_data/sensor_data.csv"

if not os.path.exists(DATA_PATH):
    print("sensor_data.csv not found. Drag it into the sample_data folder, then re-run this cell.")
    print("Expected path:", DATA_PATH)
    raise FileNotFoundError("Dataset missing - see instructions above")

df = pd.read_csv(DATA_PATH)
print(df.shape)
df.head()

###Clean data
COLUMN_MAP = {
    "field1": "temperature",
    "field2": "humidity",
    "field4": "air_quality",
}

df = df.rename(columns=COLUMN_MAP)

features = ["temperature", "humidity", "air_quality"]
df = df[features].copy()

df[features] = df[features].interpolate(method="linear").bfill()

print("Missing values after cleaning:")
print(df[features].isnull().sum())
df.describe()

###Train the model
X = df[features].values

model = IsolationForest(
    n_estimators=200,
    contamination=0.02,   # assume ~2% of readings are anomalies - adjust after checking results
    random_state=42,
)
model.fit(X)

print("Model trained on", len(df), "readings")

df["is_anomaly"] = model.predict(X) == -1
df["anomaly_score"] = model.decision_function(X)

n_anom = df["is_anomaly"].sum()
print(f"Detected {n_anom} anomalies out of {len(df)} readings ({df['is_anomaly'].mean()*100:.2f}%)")

# Distribution of each feature
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, col in zip(axes, features):
    ax.hist(df[col], bins=50)
    ax.set_title(col)
plt.tight_layout()
plt.show()

# Where the flagged anomalies fall along the temperature curve over time
plt.figure(figsize=(12, 5))
plt.scatter(df.index, df["temperature"], c=df["is_anomaly"], cmap="coolwarm", s=5)
plt.title("Temperature readings \u2014 flagged anomalies in red")
plt.xlabel("Reading index (time order)")
plt.ylabel("Temperature (\u00b0C)")
plt.show()

###Anomaly score across the dataset
# Anomaly score over time - negative values are what get flagged
plt.figure(figsize=(12, 5))
plt.scatter(df.index, df["anomaly_score"], c=df["is_anomaly"], cmap="coolwarm", s=5)
plt.axhline(0, color="gray", linestyle="--", linewidth=1)
plt.title("Anomaly score over time (flagged anomalies in red)")
plt.xlabel("Reading index (time order)")
plt.ylabel("Anomaly score (negative = more anomalous)")
plt.show()

# Outliers across all three features at once, viewed as three pairs
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
pairs = [("temperature", "humidity"), ("temperature", "air_quality"), ("humidity", "air_quality")]

scatter = None
for ax, (x_col, y_col) in zip(axes, pairs):
    scatter = ax.scatter(df[x_col], df[y_col], c=df["anomaly_score"], cmap="coolwarm_r", s=5)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)

fig.suptitle("Anomaly score across sensor readings (red = more anomalous)")
fig.colorbar(scatter, ax=axes, label="anomaly score")
plt.show()

###Alert thresholds
#numbers can be changed easily
TEMP_LOW = 25.0
TEMP_HIGH = 30.0

HUMIDITY_LOW = 60.0
HUMIDITY_HIGH = 77.0

AIR_QUALITY_HIGH = 49.0   # higher number = worse air quality

SEVERITY_STEEPNESS = 10.0   # how sharply severity rises from 0 to 1 near the threshold

###Threshol check + predictive functions
def check_thresholds(temperature, humidity, air_quality):
    alerts = []

    if temperature > TEMP_HIGH:
        alerts.append(f"High Temperature detected: {temperature}\u00b0C (threshold: {TEMP_HIGH}\u00b0C)")
    elif temperature < TEMP_LOW:
        alerts.append(f"Low Temperature detected: {temperature}\u00b0C (threshold: {TEMP_LOW}\u00b0C)")

    if humidity > HUMIDITY_HIGH:
        alerts.append(f"High Humidity detected: {humidity}% (threshold: {HUMIDITY_HIGH}%)")
    elif humidity < HUMIDITY_LOW:
        alerts.append(f"Low Humidity detected: {humidity}% (threshold: {HUMIDITY_LOW}%)")

    if air_quality > AIR_QUALITY_HIGH:
        alerts.append(f"Poor Air Quality detected: {air_quality} AQI (threshold: {AIR_QUALITY_HIGH} AQI)")

    return alerts


def predict(temperature, humidity, air_quality):
    X = np.array([[temperature, humidity, air_quality]])

    raw_prediction = model.predict(X)[0]        # 1 = normal, -1 = anomaly
    raw_score = model.decision_function(X)[0]     # negative = anomaly, positive = normal
    ml_flagged = raw_prediction == -1

    alerts = check_thresholds(temperature, humidity, air_quality)
    severity = 1 / (1 + np.exp(SEVERITY_STEEPNESS * raw_score))

    return {
        "is_anomaly": bool(ml_flagged or alerts),
        "anomaly_score": round(float(raw_score), 5),
        "severity": round(float(severity), 4),
        "alerts": alerts,
        "readings": {
            "temperature": temperature,
            "humidity": humidity,
            "air_quality": air_quality,
        },
    }

###Test it
#A few made-up readings, plus a real row straight from the dataset.
print("--- normal reading ---")
print(json.dumps(predict(27.5, 68.2, 41), indent=2))

print("\n--- high temperature ---")
print(json.dumps(predict(33.0, 68.2, 41), indent=2))

print("\n--- low humidity + poor air quality ---")
print(json.dumps(predict(27.5, 45.0, 55), indent=2))

print("\n--- a real row from your dataset (row 0) ---")
row = df.iloc[0]
print(json.dumps(predict(row["temperature"], row["humidity"], row["air_quality"]), indent=2))

###Run it as a real API
app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict_route():
    data = request.get_json()
    try:
        result = predict(data["temperature"], data["humidity"], data["air_quality"])
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
    return jsonify(result)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

def run_app():
    app.run(port=5000, use_reloader=False)

threading.Thread(target=run_app, daemon=True).start()
time.sleep(2)
print("Server running on http://127.0.0.1:5000")

r = requests.post("http://127.0.0.1:5000/predict", json={"temperature": 33.0, "humidity": 68.2, "air_quality": 41})
print(r.json())