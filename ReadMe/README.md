# EGT307_T2_BACON

## Task Assignment

| Name     | Task                                                                                                    | Microservice                           |
|----------|---------------------------------------------------------------------------------------------------------|----------------------------------------|
| Wei Guan | Notification Service, Frontend Dashboard, Sensor Simulator, Presentation, Data Sources                   | sensor simulator, notification-service |
| Shun Wei | Backend API, System Integration, Docker & Kubernetes, System Architecture, Code Quality & Documentation | backend-api                            |
| Derek    | Data Ingestion Service, Database Setup, Machine Learning Service                                        | data-ingestion, ml service              |

## Project Overview

## Problem Statement

Many environmental monitoring systems only display sensor readings without providing intelligent analysis or early detection of abnormal conditions. This requires users to manually monitor large amounts of data, which is time-consuming and may lead to delayed responses. 

## Relevance of the problem towards the real world

In a nuclear plant, catching a sudden change in air quality is a race against an invisible hazard. Expecting a human operator to stare at screens and catch a tiny spike in gas levels or airborne particles among thousands of data points just isn't realistic—people get tired and miss things. By letting AI scan the data in the background, the plant can predict emergencies instead of just reacting to them. Smart environmental sensors sniff out tiny leaks and spot weird patterns, giving the safety team an early-warning notification hours before a real disaster hits.

## Objectives

1. Automated Analysis: Use machine learning to interpret sensor data instead of relying solely on raw readings
2. Early Detection: Identify abnormal environmental conditions (e.g., pollution spikes, temperature anomalies) before they escalate.

## Intended Benefits

1. Reduced Manual Monitoring: AI automatically monitors environmental data, reducing the need for constant human supervision.
2. Early Hazard Detection: Provides timely alerts to help prevent or minimise environmental risks.
3. Improved Accuracy: AI detects abnormal patterns that may be missed during manual monitoring.
4. Scalable and Easy to Maintain: The microservices architecture allows each service to be updated, maintained, and scaled independently.

## Data Source

Data is collected through sensors that is placed in a controlled environment. The controlled environment is meant to simulate work conditions in a dangerous environment such has a chemical or nuclear powerplants. The following features of the data are Temperature, Humidity and Air Quality.

## System Architecture

The Smart Environmental Monitoring System uses a microservices architecture to provide a flexible and reliable solution for monitoring environmental conditions. The system consists of six services: the Data Ingestion Service, which collects sensor data; the Machine Learning Service, which analyses the data and detects abnormal conditions; the Notification Service, which sends Telegram alerts when abnormal readings are detected; the Backend API, which manages communication between services; the Database, which stores sensor data and prediction results; and the Frontend Dashboard, where users can view live data, AI predictions, and notifications.

Using a microservices architecture improves modularity by giving each service a specific responsibility, making it easier to develop and maintain. It also improves scalability, as each service can be deployed or scaled independently based on demand. Since the services operate separately, the system is also more fault tolerant, as a failure in one service is less likely to affect the others, allowing the rest of the application to continue running.

### Sensor Architecture

The Sensor Architecture is responsible for simulating IoT sensors by continuously reading environmental data from the CSV dataset. Instead of collecting live sensor readings, it loops through the existing dataset and sends one record at a time to the Data Ingestion Service through REST API requests. This simulates a real-time data stream, allowing the rest of the system to process, analyse, and display sensor data as if it were coming from actual IoT devices. This approach provides a simple and reliable way to test the system without requiring physical hardware.

### Data Ingestion

The Data Ingestion Service is responsible for transferring environmental sensor data to the system for processing. It receives real-time readings such as temperature, humidity, CO2 concentration, and air quality from IoT sensors through REST APIs. The service validates and formats the incoming data before storing it in the database and forwarding it to the Machine Learning Service for analysis. By separating data collection into its own microservice, the system achieves better scalability, reliability, and maintainability, allowing new sensors or data sources to be integrated with minimal changes to the overall application.

### Database Service

The Database Service stores the imported environmental monitoring dataset, anomaly prediction results, and historical records. The Backend API retrieves data from the database for preprocessing and machine learning analysis, while prediction results are stored for future reference and visualisation. This provides persistent and centralized data storage, enabling efficient data management and historical analysis.

### Backend API Service

The Backend API Service acts as the communication layer between all microservices. It receives requests from the Frontend Dashboard, retrieves sensor data from the database, sends data to the Machine Learning Service for prediction, stores the prediction results, and returns the processed information to the user.

### Machine Learning Service

The Machine Learning Service receives validated sensor data from the Backend API, analyses it using the trained model, and returns prediction results. If an abnormal condition is detected, the Backend API stores the result in the database and triggers the Notification Service to send a Telegram alert.

### Notification Service

The Notification Service is used to send alerts when the system detects abnormal environmental conditions. After the AI model analyses the sensor data, the service checks whether any readings, such as temperature, humidity, CO2, or air quality, exceed the predefined threshold. If an abnormal condition is detected, an alert is automatically sent to a Telegram bot using the Telegram Bot API. This allows users to receive notifications instantly on their phones and take action as soon as possible. Separating the notification feature into its own microservice also makes it easier to maintain, update, and scale without affecting the other services in the system.

### Frontend Dashboard

The Frontend Dashboard provides a user-friendly interface for monitoring environmental conditions. It displays sensor data, anomaly detection results, and historical trends by sending REST API requests to the Backend API. Users can easily view environmental status and receive alerts without directly interacting with the database.

## Setup & Running

### Prerequisites

- Python 3.11+ (only needed to run the services standalone; not needed if you
  use Docker only)
- Docker with Docker Compose (for the full stack)
- `kubectl` and a cluster (only for the Kubernetes option)

No Node.js is required — the frontend is plain static files served by nginx.

### Option A — Full stack with Docker Compose

Create a `.env` file in the repo root (git-ignored) before starting. The
`env-validator` service runs automatically and blocks startup until all
values are valid:

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

# 4. Open the dashboard
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

# 4. Open the dashboard
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

### Option C — Run each service standalone (no Docker)

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

#### 3. Notification Service

```bash
cd components/notification-service
pip install -r requirements.txt
python -m app.main
```

Listens on port 5002. The Telegram credentials are loaded from `.env`
automatically. The alert thresholds default in code (`TEMP_THRESHOLD`
39, `HUMIDITY_THRESHOLD` 55, `AQ_THRESHOLD` 2). Full Telegram setup and
troubleshooting: `components/notification-service/README.md`.

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

#### 4. Data Ingestion Service

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

#### 5. ML Service

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

#### 6. Sensor Simulator

```bash
cd components/sensor
pip install -r requirements.txt
python sensor_simulator.py
```

| Variable | Default | Note |
|----------|---------|------|
| `DATASET_PATH` | `components/database/validation_data.example.csv` | Default for the Sensor Simulator. Override with `DATASET_PATH` env var. |
| `DATA_INGESTION_URL` | `http://data-ingestion-service:5003/api/ingest/reading` | A Docker-internal DNS name. For local runs set `http://localhost:5003/api/ingest/reading`. |
| `SEND_INTERVAL_SECONDS` | `3` | How long to wait between readings. |

#### 7. Frontend Dashboard

```bash
cd components/frontend
python -m http.server 3000
```

Open `http://localhost:3000/html/dashboard.html`. The dashboard is static —
it needs the Backend API (5000) and Notification Service (5002) running, and
loads Chart.js from a CDN (internet required). Opening the file directly with
`file://` will not work. See `components/frontend/README.md` for details.

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
[`components/notification-service/README.md`](../components/notification-service/README.md),
[`components/frontend/README.md`](../components/frontend/README.md), and the
system-level design notes in
[`Architecture.md`](./Architecture.md).

### Known limitations

- The ML model trains on the limited cleaned dataset, so its accuracy may
  differ on new or unseen data.

## Docker Containerization

Each application component is packaged as a Docker container to provide a lightweight, portable, and consistent runtime environment across development, testing, and production. Docker eliminates dependency conflicts and ensures that the application behaves consistently regardless of the deployment platform.

## Kubernates Deployment

The containers are orchestrated using Kubernetes, which automates deployment, scaling, load balancing, and recovery of application services. Kubernetes continuously monitors the desired state of the system and automatically replaces failed Pods, ensuring high availability and fault tolerance. The orchestration platform also enables the application to scale horizontally by creating additional Pods when system workload increases.

## Issues and Limitations

The system uses a CSV dataset to simulate IoT sensor data instead of real sensors, so it may not fully represent real-world conditions. The machine learning model is also trained on a limited dataset, which may affect its accuracy when new or different data is used.
