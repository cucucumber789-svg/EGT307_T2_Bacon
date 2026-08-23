# EGT307_T2_BACON

## Task assignment

| Name     | Task                                                                                                                                        | Microservice                           |
|----------|---------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| Wei Guan | Notification Service, Frontend Dashboard, Sensor Simulator, Presentation, Data Sources                                                      | sensor simulator, notification-service |
| Shun Wei | Backend API, System Integration, Docker & Kubernetes, System Architecture, Code Quality & Documentation, Centralised Config, ML Integration | backend-api                            |
| Derek    | Data Ingestion Service, Database Setup, Machine Learning Service                                                                            | data-ingestion, ml-service             |

## Project overview

The Smart Environmental Monitoring System monitors environmental conditions
such as temperature, humidity, and air quality. Sensor data is collected and processed before being analysed by the Machine Learning Service to detect abnormal conditions. The system uses a microservices architecture with a dashboard for monitoring and a Notification Service that sends alerts through Telegram when abnormal readings are detected. This helps users identify potential environmental hazards quickly and respond when needed.

## Problem statement

Many environmental monitoring systems only display sensor readings without providing intelligent analysis or early detection of abnormal conditions. This requires users to manually monitor large amounts of data, which is time-consuming and may lead to delayed responses. 

## Relevance of the problem towards the real world

In facilities such as chemical or nuclear plants, a change in air quality can
be an early sign of a hazard, and operators cannot reliably watch thousands
of readings at once. Automated analysis addresses this: sensor data is
checked continuously in the background, abnormal patterns raise an alert,
and the safety team is notified without waiting for someone to notice a
reading on a screen.

## Objectives

1. Automated Analysis: Use machine learning to interpret sensor data instead of relying solely on raw readings
2. Early Detection: Identify abnormal environmental conditions (e.g., pollution spikes, temperature anomalies) before they escalate.

## Intended benefits

1. Reduced Manual Monitoring: AI automatically monitors environmental data, reducing the need for constant human supervision.
2. Early Hazard Detection: Provides timely alerts to help prevent or minimise environmental risks.
3. Improved Accuracy: AI detects abnormal patterns that may be missed during manual monitoring.
4. Scalable and Easy to Maintain: The microservices architecture allows each service to be updated, maintained, and scaled independently.

## Data source

Data is collected through sensors placed in a controlled environment that
simulates working conditions in a dangerous facility such as a chemical or
nuclear power plant. The data features are temperature, humidity, and air
quality.

## System architecture

The Smart Environmental Monitoring System uses a microservices architecture to provide a flexible and reliable solution for monitoring environmental conditions. The system consists of six services: the Data Ingestion Service, which collects sensor data; the Machine Learning Service, which analyses the data and detects abnormal conditions; the Notification Service, which sends Telegram alerts when abnormal readings are detected; the Backend API, which manages communication between services; the Database, which stores sensor data and prediction results; and the Frontend Dashboard, where users can view live data, AI predictions, and notifications.

Using a microservices architecture improves modularity by giving each service a specific responsibility, making it easier to develop and maintain. It also improves scalability, as each service can be deployed or scaled independently based on demand. Since the services operate separately, the system is also more fault tolerant, as a failure in one service is less likely to affect the others, allowing the rest of the application to continue running.

### Sensor architecture

The Sensor Architecture is responsible for simulating IoT sensors by continuously reading environmental data from the CSV dataset. Instead of collecting live sensor readings, it loops through the existing dataset and sends one record at a time to the Data Ingestion Service through REST API requests. This simulates a real-time data stream, allowing the rest of the system to process, analyse, and display sensor data as if it were coming from actual IoT devices. This approach provides a simple and reliable way to test the system without requiring physical hardware.

### Data ingestion

The Data Ingestion Service is responsible for transferring environmental sensor data to the system for processing. It receives real-time readings such as temperature, humidity, and air quality from IoT sensors through REST APIs. The service validates and formats the incoming data before storing it in the database and forwarding it to the Machine Learning Service for analysis.

### Database service

The Database Service stores the imported environmental monitoring dataset, anomaly prediction results, and historical records. The Backend API retrieves data from the database for preprocessing and machine learning analysis, while prediction results are stored for future reference and visualisation. This provides persistent and centralised data storage, enabling efficient data management and historical analysis.

### Backend API service

The Backend API Service acts as the communication layer between all microservices. It receives requests from the Frontend Dashboard, retrieves sensor data from the database, sends data to the Machine Learning Service for prediction, stores the prediction results, and returns the processed information to the user.

### Machine learning service

The Machine Learning Service receives validated sensor data from the Backend API, analyses it using the trained model, and returns prediction results. If an abnormal condition is detected, the Backend API stores the result in the database and triggers the Notification Service to send a Telegram alert.

### Notification service

The Notification Service is used to send alerts when the system detects abnormal environmental conditions. It does not make alerting decisions: when the ML model flags a reading and its anomaly score crosses the configured threshold, the Backend API calls this service, which forwards the alert message to a Telegram bot using the Telegram Bot API and keeps it for the dashboard. This allows users to receive notifications on their phones and take action as soon as possible. Separating the notification feature into its own microservice makes it easier to maintain and update without affecting the other services in the system.

### Frontend dashboard

The Frontend Dashboard provides a user-friendly interface for monitoring environmental conditions. It displays sensor data, anomaly detection results, and historical trends by sending REST API requests to the Backend API. Users can easily view environmental status and receive alerts without directly interacting with the database.

## Setup & running

### Prerequisites

- Python 3.11+ (only needed to run the services standalone; not needed if you
  use Docker only)
- Docker with Docker Compose (for the full stack)
- `kubectl` and a cluster (only for the Kubernetes option)

No Node.js is required — the frontend is plain static files served by nginx.

### Option A — full stack with Docker Compose

Create a `.env` file in the repo root (git-ignored) before starting. The
`env-validator` service runs automatically and blocks startup until all
values are valid. `config.yaml` (committed) holds non-sensitive tuning
values — thresholds, ML hyperparameters, simulator intervals — and is
mounted into the relevant containers as a read-only volume.

```bash
cp .env.example .env   # then edit with your values
docker-compose up --build
```

If any variable is missing or still has a placeholder, startup stops with a
clear error message. Without Telegram credentials the Notification Service
still runs and records alerts, but prints `Telegram not configured, skipping
send` instead of messaging anyone.

| Service                | Host port | URL / connection                     |
|------------------------|-----------|--------------------------------------|
| Frontend Dashboard     | 3000      | http://localhost:3000                |
| Backend API            | 5000      | http://localhost:5000/api            |
| ML Service             | 5001      | http://localhost:5001                |
| Notification Service   | 5002      | http://localhost:5002                |
| Data Ingestion Service | 5003      | http://localhost:5003                |
| Database (PostgreSQL)  | 5432      | `postgresql://user:password@localhost:5432/env_monitor` |

First-run data flow:

**Bash:**
```bash
# 1. Register the raw dataset once (cleans it and forwards rows to the backend)
curl -X POST http://localhost:5003/api/ingest/file

# 2. Confirm readings are stored
curl http://localhost:5000/api/sensors?limit=5

# 3. Trigger the ML model (lazy training) and store an anomaly prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"temperature":45,"humidity":90,"air_quality":1}'

# 4. Check the config thresholds (should match config.yaml)
curl http://localhost:5000/api/config

# 5. Open the dashboard
#    http://localhost:3000/html/dashboard.html
```

**PowerShell:**
```powershell
# 1. Register the raw dataset once (cleans it and forwards rows to the backend)
Invoke-RestMethod -Uri http://localhost:5003/api/ingest/file -Method Post

# 2. Confirm readings are stored
Invoke-RestMethod -Uri "http://localhost:5000/api/sensors?limit=5"

# 3. Trigger the ML model (lazy training) and store an anomaly prediction
Invoke-RestMethod -Uri http://localhost:5000/api/predict -Method Post `
  -ContentType "application/json" `
  -Body '{"temperature":45,"humidity":90,"air_quality":1}'

# 4. Check the config thresholds (should match config.yaml)
Invoke-RestMethod -Uri http://localhost:5000/api/config

# 5. Open the dashboard
Start-Process "http://localhost:3000/html/dashboard.html"
```

Verify each service is healthy:

```powershell
Invoke-RestMethod http://localhost:3000/          # Frontend
Invoke-RestMethod http://localhost:5000/          # Backend API
Invoke-RestMethod http://localhost:5001/          # ML Service
Invoke-RestMethod http://localhost:5002/          # Notification Service
Invoke-RestMethod http://localhost:5003/          # Data Ingestion
```

### Option B — Kubernetes

Create the Telegram credentials Secret (skip if you are not using Telegram):

```bash
kubectl create secret generic telegram-credentials \
  --from-literal=TELEGRAM_BOT_TOKEN=<token> \
  --from-literal=TELEGRAM_CHAT_ID=<chat-id>
```

Apply the manifests. The database PVC must exist first because every service
that mounts the shared dataset volume depends on it:

```bash
kubectl apply -f k8s/database/pvc.yaml
kubectl apply -f k8s/backend-api -f k8s/ml-service -f k8s/notification-service \
              -f k8s/data-ingestion-service -f k8s/frontend
```

### Option C — run each service standalone (no Docker)

Each service installs and runs on its own, so you can develop and test one
piece without the full stack.

**First, validate your environment:**

```bash
python scripts/validate-env.py
```

This loads `.env` from the repo root and checks all required variables. Fix
any errors before proceeding.

The quick reference:

| Service                | Folder                         | Port | Run                              |
|------------------------|--------------------------------|------|----------------------------------|
| Database               | `components/database`          | 5432 | Docker (see below)               |
| Backend API            | `components/backend-api`       | 5000 | `python -m app.main`             |
| Notification Service   | `components/notification-service` | 5002 | `python -m app.main`           |
| Data Ingestion Service | `components/data-ingestion-service` | 5003 | `python -m app.main`          |
| ML Service             | `components/ml-service`        | 5001 | `python -m app.main`             |
| Sensor Simulator       | `components/sensor`            | —    | `python sensor_simulator.py`     |
| Frontend Dashboard     | `components/frontend`          | 3000 | `python -m http.server 3000`     |

#### 1. Database (PostgreSQL)

PostgreSQL is not a Python service, so it runs in Docker even in standalone
mode. The default connection is `postgresql://user:password@localhost:5432/env_monitor`.

```bash
docker run -d --name bacon-db -p 5432:5432 \
  -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=env_monitor \
  -v <absolute path>\components\database\init.sql:/docker-entrypoint-initdb.d/init.sql \
  postgres:16-alpine
```

The init.sql volume needs an absolute path on Windows. The Backend API also
creates missing tables on startup (`create_all`), so init.sql is only needed
to guarantee an identical schema.

#### 2. Backend API

```bash
cd components/backend-api
pip install -r requirements.txt
python -m app.main
```

Listens on port 5000. All settings come from environment variables with
localhost defaults:

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/env_monitor` |
| `ML_SERVICE_URL` | `http://localhost:5001` |
| `NOTIFICATION_SERVICE_URL` | `http://localhost:5002` |
| `DATA_INGESTION_SERVICE_URL` | `http://localhost:5003` |

#### 3. Notification service

```bash
cd components/notification-service
pip install -r requirements.txt
python -m app.main
```

Listens on port 5002. This service is a **pure message sender** — it does
not make alerting decisions. The Backend API calls `POST /api/notify` when the
ML model flags an anomaly with `anomaly_score < -threshold` (configured in
`config.yaml`). The notification service forwards the alert message to Telegram
and stores it in memory for the dashboard's `GET /api/alerts` endpoint.

Without Telegram credentials the service still runs and records alerts, but
prints `Telegram not configured, skipping send` instead of messaging anyone.
Full Telegram setup and troubleshooting: `components/notification-service/README.md`.

#### Test the notification service

Check the health endpoint (look for `telegram_configured: true`):

```powershell
# PowerShell
Invoke-RestMethod -Uri http://localhost:5002/

# Bash
curl http://localhost:5002/
```

Send a test alert:

```powershell
# PowerShell
Invoke-RestMethod -Uri http://localhost:5002/api/notify -Method Post `
  -ContentType "application/json" `
  -Body '{"temperature":40,"humidity":80,"air_quality":3,"alerts":["Test alert"]}'
```

```bash
# Bash
curl -X POST http://localhost:5002/api/notify \
  -H "Content-Type: application/json" \
  -d '{"temperature":40,"humidity":80,"air_quality":3,"alerts":["Test alert"]}'
```

A Telegram message should arrive. Verify with:

```powershell
Invoke-RestMethod -Uri http://localhost:5002/api/alerts
```

#### 4. Data ingestion service

Server mode (listens on port 5003):

```bash
cd components/data-ingestion-service
pip install -r requirements.txt
python -m app.main
```

| Variable | Default |
|----------|---------|
| `BACKEND_API_URL` | `http://localhost:5000` |
| `DATA_DIR` | `../database` (i.e. `components/database`) |

> The server starts "empty" by design — it does **not** clean the dataset on
> startup. Produce the cleaned dataset with the clean-only command below, or
> with `POST /api/ingest/file` while the server is running (which also
> forwards the rows to the backend).

Clean-only mode — no server or backend needed; reads
`components/database/sensor_data.example.csv` and writes
`components/database/sensor_data_cleaned.csv`:

```bash
cd components/data-ingestion-service
python -m app.services.data_ingestion
```

#### 5. ML service

```bash
cd components/ml-service
pip install -r requirements.txt
python -m app.main
```

Listens on port 5001. `DATASET_PATH` defaults to
`../database/sensor_data_cleaned.csv`. The model trains lazily: the service
starts idle and trains on the first prediction request (503 until data is
available). Sanity-check the model without a server:

```bash
cd components/ml-service
python -m app.services.model_service
```

**How the scoring works:**

| Concept | What it is | Where it's set |
|---------|-----------|----------------|
| Anomaly score | IsolationForest `decision_function()` — negative = anomaly, positive = normal. Magnitude indicates distance from the decision boundary. | Model internal (trained from data) |
| Contamination | Expected fraction of anomalies in training data (default 2%). Determines where the model draws its decision boundary (`score = 0`). | `config.yaml` → `ml_service.contamination` |
| Severity | Sigmoid mapping of the anomaly score to 0–1 (`severity = 1/(1 + exp(steepness * score))`). Green (low) → yellow → red (high). | `config.yaml` → `ml_service.severity_steepness` |
| Notification threshold | Telegram only fires when `anomaly_score < -threshold` (default 0.05). Mild anomalies are stored but do not notify. | `config.yaml` → `anomaly_score_threshold` |
| Safety net | Hardcoded `ABSOLUTE_MAX_TEMP = 50°C` — physically dangerous values get pinned to severity 1.0 regardless of model score. | `config.yaml` → `ml_service.absolute_max_temp` |

#### 6. Sensor simulator

```bash
cd components/sensor
pip install -r requirements.txt
python sensor_simulator.py
```

The simulator replays `validation_data.example.csv` row by row, posting one
reading every few seconds to the Data Ingestion Service. Each loop pass
applies random jitter to values (temperature ±2, humidity ±5, air quality ±1)
for diversity. ~5% of readings are synthetic anomalies (extreme values) to
trigger ML alerts for demo purposes. Send interval and anomaly rate are
read from `config.yaml`.

| Variable | Default | Note |
|----------|---------|------|
| `DATASET_PATH` | `components/database/validation_data.example.csv` | Default for the Sensor Simulator. Override with `DATASET_PATH` env var. |
| `DATA_INGESTION_URL` | `http://data-ingestion-service:5003/api/ingest/reading` | A Docker-internal DNS name. For local runs set `http://localhost:5003/api/ingest/reading`. |
| `SEND_INTERVAL_SECONDS` | `3` | How long to wait between readings. |

#### 7. Frontend dashboard

```bash
cd components/frontend
python -m http.server 3000
```

Open `http://localhost:3000/html/dashboard.html`. The dashboard is static —
it needs the Backend API (5000) and Notification Service (5002) running, and
loads Chart.js from a CDN (internet required). Opening the file directly with
`file://` will not work. See `components/frontend/README.md` for details.

**What the dashboard shows:**

- **Sensor charts** — Temperature, humidity, and air quality over the last 20 readings. Anomalous points are coloured red.
- **Notification panel** — Most recent alert from the Notification Service, with timestamp. Green = all normal, red = alert active.
- **ML Analysis panel** — Severity bar with threshold markers (dark line at model boundary, red line at notification trigger), anomaly score with buffer-to-alert indicator, status (Normal/Anomaly), and reference rows for notification threshold and model contamination.

The dashboard fetches config from `GET /api/config` on page load so threshold
displays stay in sync with `config.yaml` — no hardcoding in JavaScript.

### Run everything locally (no Docker)

1. Validate environment variables:

```bash
python scripts/validate-env.py
```

2. Start the services in this order, each in its own terminal:

   1. Database (Docker container, see #1)
   2. Backend API (see #2)
   3. Notification Service (see #3)
   4. Data Ingestion Service, server mode (see #4)
   5. ML Service (see #5)
   6. Frontend Dashboard (see #7)

Then register data as in Option A and open the dashboard.

### Per-service documentation

Each service folder has its own README with configuration, run modes, and
troubleshooting:
[`components/notification-service/README.md`](./components/notification-service/README.md),
[`components/frontend/README.md`](./components/frontend/README.md), and the
system-level design notes in
[`ARCHITECTURE.md`](./ARCHITECTURE.md).

## Issues and limitations

- Limited Dataset and Simulation: The system uses a limited, static CSV dataset to simulate IoT sensors, so it may not fully represent real-world sensor behaviour or how the ML model performs on new data.

- Alert Threshold: The notification threshold buffer (`anomaly_score_threshold` in `config.yaml`) is a design choice — tuning it controls the tradeoff between alert sensitivity and noise. Too low and mild anomalies trigger Telegram; too high and genuine anomalies are missed.
