# Architecture — Smart Environmental Monitoring System

## Overview

This document outlines the overall system architecture, repository structure,
technology decisions, and deployment strategy for the Smart Environmental
Monitoring System. The system uses a **microservices architecture** orchestrated
by **Docker** and **Kubernetes**.

---

## System architecture (high-level)

```
┌─────────────────────┐   ┌─────────────────────┐
│  Frontend Dashboard │   │   Sensor Simulator  │
│  (HTML/CSS/JS)      │   │   (replays dataset) │
└──────┬──────────────┘   └──────────┬──────────┘
       │                             │ REST/HTTP
       │ REST/HTTP                   ▼
       ▼                     ┌──────────────────┐
┌──────────────────┐   ┌────►│Data Ingestion    │
│ Notification     │   │     │   Service        │
│   Service        │   │     │(CSV/JSON intake) │
│ (Telegram alerts)│   │     └────────┬─────────┘
└──────────────────┘   │              │ REST/HTTP
                       │              ▼
┌─────────────────────┐│     ┌─────────────────────┐
│   Backend API       │◄┘     │ PostgreSQL DB       │
│   (Flask + PySpark) │◄──────►                     │
└──────────┬──────────┘       └─────────────────────┘
           │ REST/HTTP
           ▼
┌─────────────────────┐
│   ML Service        │
│ (IsolationForest)   │
└─────────────────────┘
```

All components are containerised with Docker and deployed via Kubernetes.

---

## Repository file structure

```
EGT307_T2_Bacon/
├── docker-compose.yml             # Local multi-service development
├── config.yaml                    # Centralised non-sensitive config (thresholds, tuning)
├── .env.example                   # Template for secrets (committed); .env is gitignored
├── EGT307 PRESENTATION.pptx       # Project presentation
├── EGT307_Contribution.docx       # Individual contribution breakdown
├── README.md                      # Project overview & quick start
├── Architecture.md                # System architecture & design docs
│
├── scripts/                       # Validation & utility scripts
│   ├── validate-env.sh            # Shell env validation (used by Docker)
│   └── validate-env.py            # Python env validation (standalone mode)
│
├── components/                 # All services live under this folder
│   ├── env-validator/             # ENV VALIDATOR — pre-flight env check container
│   │   └── Dockerfile
│   ├── backend-api/               # BACKEND API — Flask + PySpark
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py            # Flask app entry point (create_app)
│   │   │   ├── config.py          # Environment-based configuration
│   │   │   ├── database.py        # SQLAlchemy engine + session
│   │   │   ├── spark_session.py   # Spark session initialisation (TBD)
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sensor.py      # SensorReading SQLAlchemy model
│   │   │   │   └── prediction.py  # Prediction SQLAlchemy model (ML results)
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   └── sensor.py      # Request/response schemas (TBD)
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sensor.py      # Sensor CRUD routes
│   │   │   │   ├── prediction.py  # Predict + predictions routes
│   │   │   │   └── config.py      # GET /api/config — serves thresholds to frontend
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       ├── sensor_service.py  # Sensor business logic (TBD)
│   │   │       ├── ml_client.py       # ML service HTTP client
│   │   │       ├── notification_client.py  # Notification service HTTP client
│   │   │       └── prediction_service.py  # Prediction persistence helpers
│   │   ├── tests/
│   │   │   └── __init__.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── ml-service/                # ML SERVICE — anomaly detection
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py            # Flask app entry point (lazy training at startup)
│   │   │   ├── config.py          # Dataset path, model, and threshold settings
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   └── prediction.py  # /api/predict + /api/predict/batch
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       └── model_service.py # IsolationForest training + prediction
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── notification-service/      # NOTIFICATION SERVICE — Telegram alerts
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   └── main.py            # Single-file Flask app (thresholds + Telegram)
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── data-ingestion-service/    # DATA INGESTION SERVICE — sensor data intake
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py            # Flask app entry point
│   │   │   ├── config.py          # Backend API URL + DATA_DIR configuration
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   └── ingestion.py   # Data intake endpoints
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       └── data_ingestion.py   # CSV parsing, cleaning, and forwarding
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── database/                  # DATABASE — PostgreSQL init + sensor data
│   │   ├── init.sql
│   │   ├── Dockerfile                # Dataset seed image (k8s init container)
│   │   ├── sensor_data.example.csv   # Raw sensor data (ground truth)
│   │   ├── sensor_data_cleaned.csv   # Cleaned sensor data (output of ingestion)
│   │   └── validation_data.example.csv # Test dataset for sensor simulator
│   │
│   ├── frontend/                  # FRONTEND — dashboard (HTML/CSS/JS + Chart.js)
│   │   ├── css/
│   │   │   └── styles.css
│   │   ├── html/
│   │   │   └── dashboard.html
│   │   ├── js/
│   │   │   └── dashboard.js
│   │   ├── Dockerfile              # nginx container that serves the dashboard
│   │   └── nginx.conf              # listens on 3000, falls back to dashboard.html
│   │
│   └── sensor/                    # SENSOR SIMULATOR — replays dataset as IoT stream
│       ├── sensor_simulator.py
│       ├── Dockerfile
│       └── requirements.txt
│
└── k8s/                          # KUBERNETES — deployment manifests
    ├── backend-api/
    │   ├── deployment.yaml
    │   ├── service.yaml            # NodePort 30000 → 5000
    │   └── configmap.yaml
    ├── ml-service/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── notification-service/
    │   ├── deployment.yaml
    │   ├── service.yaml            # NodePort 30002 → 5002
    │   ├── configmap.yaml
    │   └── secret.example.yaml     # Telegram credentials template (placeholder)
    ├── data-ingestion-service/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── database/
    │   ├── pvc.yaml                # shared dataset PVC (sensor data)
    │   ├── postgres-deployment.yaml
    │   ├── postgres-service.yaml   # ClusterIP database:5432
    │   ├── postgres-secret.yaml    # POSTGRES_USER/PASSWORD/DB (placeholder)
    │   ├── postgres-pvc.yaml       # PostgreSQL data persistence
    │   ├── postgres-configmap.yaml # init.sql (creates tables)
    │   └── app-config-configmap.yaml # config.yaml shared across services
    └── frontend/
        ├── deployment.yaml
        ├── service.yaml            # NodePort 30080 → 80 → 3000
        └── configmap.yaml          # nginx proxy targets
```

---

## File structure guide

This section explains what each file does and how they connect, for developers
new to this project.

### What is `__init__.py`?

`__init__.py` is a file that marks a folder as a **Python package**, allowing you to
import modules from it. Without this file, Python treats the folder as a regular
directory and cannot import from it.

**Example:**
```python
# Without __init__.py — this fails:
from app.models.sensor import SensorReading

# With __init__.py — this works:
from app.models.sensor import SensorReading
```

The file can be **empty** (just acts as a marker) or used to expose commonly
imported items for convenience.

### How the files connect

All services live under `components/`. The Backend API is the largest
service and still uses the full `app/` split:

```
components/backend-api/app/main.py  (entry point — starts the app)
  ├── imports config.py          (reads environment variables)
  ├── imports database.py        (connects to PostgreSQL)
  ├── imports spark_session.py   (creates Spark session)   (TBD)
  └── registers routers/sensor.py      (adds /api/sensors routes)

routers/sensor.py  (handles HTTP requests)
  ├── imports models/sensor.py   (to read/write sensor data in DB)
  ├── imports schemas/sensor.py  (to validate incoming JSON)   (TBD)
  └── imports services/sensor_service.py (to process data)     (TBD)

routers/prediction.py  (handles prediction requests)
  ├── imports services/ml_client.py (to call the ML microservice)
  └── imports services/prediction_service.py (to persist results in the DB)
```

The Notification Service takes a simpler shape: it is a **single-file app** —
`app/main.py` contains the Flask routes, the threshold checks, and the
Telegram sending logic all in one place. The Data Ingestion Service keeps the
`app/` split but is smaller than the Backend API. The ML Service uses the same
`app/` split: `main.py` trains the IsolationForest model at startup when the
cleaned dataset is available (or starts idle otherwise), and
`routers/prediction.py` serves the prediction endpoints, retrying training
lazily on the first request if data appeared after startup.

### File-by-file explanation

Paths below are relative to the repo root unless marked `(relative to service)`,
in which case they are relative to the service folder inside `components/`.

| File                                                                  | Purpose |
|-----------------------------------------------------------------------|---------|
| `config.yaml`                                                         | Centralised non-sensitive configuration — thresholds, ML hyperparameters, simulator tuning. Committed to git. Services read it at startup via `_load_yaml()`; the Backend API also serves it to the frontend via `GET /api/config`. |
| `.env.example`                                                        | Template for secrets (Telegram token, database credentials). Committed; `.env` is gitignored. |
| `docker-compose.yml`                                                  | Defines all services (backend, ML, notification, ingestion, database, frontend, sensor simulator) and how they run together locally. Mounts `config.yaml` as a read-only volume into backend-api, ml-service, and sensor-simulator. One command starts everything. |
| `scripts/validate-env.sh`                                             | Shell script for validating `.env`. Used by the `env-validator` Docker container to block startup until all secrets are set. |
| `scripts/validate-env.py`                                             | Python script for validating `.env` in standalone mode. Loads `.env` into the environment and checks all required variables. |
| `components/env-validator/Dockerfile`                                 | Minimal alpine container that runs `validate-env.sh` as a healthcheck. Other services depend on it being healthy before starting. |
| `components/backend-api/app/main.py`                               | Flask app entry point. Creates the app, registers blueprints (routers), and starts the server. Sets the `werkzeug` logger to WARNING level so routine request logs (200, 201) do not clutter terminal output. Prints `backend-api listening on :5000` at startup. |
| `components/backend-api/app/config.py`                             | Loads secrets from environment variables (`.env`) and non-sensitive tuning values from `config.yaml` via `_load_yaml()`. Exposes `Config` class and raw `_yaml` dict used by the config endpoint. |
| `components/backend-api/app/database.py`                           | Creates the SQLAlchemy engine and session. Other files import `SessionLocal` to query or insert data into PostgreSQL. |
| `components/backend-api/app/spark_session.py`                      | Creates and returns a PySpark `SparkSession`. Services import this to run Spark data processing operations. (TBD) |
| `components/backend-api/app/routers/sensor.py`                     | Defines Flask Blueprint with sensor endpoints (`GET /api/sensors`, `GET /api/sensors/count`, `POST /api/sensors`, `POST /api/sensors/batch`). Receives HTTP requests and queries/inserts directly into the DB. |
| `components/backend-api/app/routers/prediction.py`                 | Defines Flask Blueprint with prediction endpoints (`POST /api/predict`, `GET /api/predictions`). Calls the ML service, persists results via `prediction_service.py`, and passes ML errors (e.g. 503 not trained) through to the caller. |
| `components/backend-api/app/routers/config.py`                     | Defines Flask Blueprint with `GET /api/config` endpoint. Returns non-sensitive thresholds from `config.yaml` (notification threshold, model contamination, severity steepness) so the frontend dashboard stays in sync without hardcoding values. |
| `components/backend-api/app/models/sensor.py`                      | SQLAlchemy model defining the `sensor_readings` table schema (`SensorReading`). Used by database.py and imported by routes to query/insert data. |
| `components/backend-api/app/models/prediction.py`                  | SQLAlchemy model defining the `predictions` table schema (`Prediction`). Stores ML anomaly results so they survive ML restarts and are queryable by the dashboard. |
| `components/backend-api/app/schemas/sensor.py`                     | Request/response schemas for validating JSON payloads and serialising responses. (TBD) |
| `components/backend-api/app/services/sensor_service.py`            | Business logic for sensor data. May use PySpark for data transformations and aggregations. (TBD) |
| `components/backend-api/app/services/ml_client.py`                 | HTTP client that sends readings to the ML microservice (`/api/predict`, `/api/predict/batch`) and returns the prediction results. |
| `components/backend-api/app/services/notification_client.py`       | HTTP client that POSTs anomalous readings to the Notification microservice (`/api/notify`). Best-effort: never raises, so an unavailable notification service cannot break prediction storage. |
| `components/backend-api/app/services/prediction_service.py`        | Persists a prediction result into the `predictions` table (`store_prediction`) and serialises rows for API responses (`prediction_to_json`). When a stored prediction is an anomaly with `anomaly_score < -ANOMALY_SCORE_THRESHOLD`, it triggers the Notification Service (best-effort). Mild anomalies are stored but do not notify, reducing alert fatigue. |
| `components/backend-api/Dockerfile`                                | Tells Docker how to build the backend container — installs dependencies, copies code, runs the app. |
| `components/backend-api/requirements.txt`                          | Lists all Python packages the project needs (Flask, SQLAlchemy, etc.). |
| `components/ml-service/app/main.py`                                | Flask app entry point for ML Service. Trains the IsolationForest model at startup when the cleaned dataset exists, otherwise starts idle and reports `model_ready: false`; registers the prediction blueprint. Sets the `werkzeug` logger to WARNING level. Prints model readiness on startup: `ml-service listening on :5001 — model ready` or `...model idle (waiting for data)`. |
| `components/ml-service/app/config.py`                              | Loads IsolationForest hyperparameters (`n_estimators`, `contamination`), severity steepness, and safety-net threshold (`ABSOLUTE_MAX_TEMP`) from `config.yaml` via `_load_yaml()`. Dataset path and port come from environment variables. |
| `components/ml-service/app/routers/prediction.py`                  | Defines Flask Blueprint with prediction endpoints (`POST /api/predict`, `POST /api/predict/batch`). Retries lazy training on demand and returns 503 with an actionable message when no dataset is available yet. |
| `components/ml-service/app/services/model_service.py`              | Contains the scikit-learn **IsolationForest** anomaly-detection logic: `load_dataset()` reads the cleaned CSV, `train_model()` fits the forest with the configured `contamination` parameter, `predict()` returns anomaly score (negative = anomaly), severity (sigmoid mapping score to 0–1), and alerts. The `contamination` parameter controls the model's sensitivity — it determines what fraction of training data is considered anomalous, setting the decision boundary. |
| `components/ml-service/Dockerfile`                                 | Container definition for ML Service. |
| `components/ml-service/requirements.txt`                           | Python dependencies for ML Service (Flask + ML framework TBD). |
| `components/notification-service/app/main.py`                      | Single-file Flask app for the Notification Service. Pure message sender — receives ML-generated alert messages from the Backend API via `POST /api/notify` and sends them via Telegram. No alerting decisions are made here. Keeps the 50 most recent alerts in memory for the dashboard (`GET /api/alerts`). Without Telegram credentials, alerts are still recorded but not sent. Sets the `werkzeug` logger to WARNING level. Prints Telegram configuration status on startup. |
| `components/notification-service/Dockerfile`                       | Container definition for Notification Service. |
| `components/notification-service/requirements.txt`                 | Python dependencies for Notification Service (Flask, requests). |
| `components/data-ingestion-service/app/main.py`                    | Flask app entry point for Data Ingestion Service. Registers ingestion blueprints. Sets the `werkzeug` logger to WARNING level. Prints `data-ingestion listening on :5003` at startup. |
| `components/data-ingestion-service/app/config.py`                  | Stores Backend API URL, `DATA_DIR`, and allowed file formats loaded from environment variables. |
| `components/data-ingestion-service/app/routers/ingestion.py`       | Defines Flask Blueprint with data intake endpoints (`POST /api/ingest/file`, `POST /api/ingest/reading`). Accepts CSV/JSON sensor data. |
| `components/data-ingestion-service/app/services/data_ingestion.py` | Parses raw CSV sensor data (drop columns, rename, coerce types, drop NaN), saves cleaned output to `sensor_data_cleaned.csv`, and forwards records to the Backend API. Also runnable standalone (`python -m app.services.data_ingestion`). |
| `components/data-ingestion-service/Dockerfile`                     | Container definition for Data Ingestion Service. |
| `components/data-ingestion-service/requirements.txt`               | Python dependencies for Data Ingestion Service (Flask, requests, pandas). |
| `components/database/init.sql`                                     | SQL script that runs when PostgreSQL starts. Creates tables. |
| `components/database/Dockerfile`                                   | Builds the `dataset-seed` image used by a Kubernetes init container to copy `sensor_data.example.csv` into the shared dataset PVC. Build with `docker build -t dataset-seed:latest components/database`. |
| `components/database/sensor_data.example.csv`                      | Raw sensor data (ground truth) used by the ingestion pipeline. |
| `components/database/validation_data.example.csv`                  | Test dataset with entry_ids starting at 78033, used by the Sensor Simulator to stream new readings. |
| `components/frontend/html/dashboard.html`                          | Dashboard page markup. |
| `components/frontend/css/styles.css`                               | Dashboard styling. |
| `components/frontend/js/dashboard.js`                              | Dashboard logic. Fetches non-sensitive config from `GET /api/config` on load to stay in sync with `config.yaml`. Polls the Backend API for sensor readings and predictions (colouring anomalous points red) and the Notification Service's `GET /api/alerts` for the alert panel. Renders charts with Chart.js. Displays the ML Analysis panel: severity bar with threshold markers (model boundary at 50%, notification trigger at ~62%), anomaly score, and reference rows for notification threshold and model contamination. |
| `components/frontend/Dockerfile`                                   | Container definition for the dashboard: nginx serving the static files on port 3000. |
| `components/frontend/nginx.conf`                                   | nginx server config: listens on 3000, serves `html/`, `css/`, `js/`, and falls back to `dashboard.html`. Access logging is off (`access_log off;`) so routine GET/POST requests do not clutter terminal output — only errors and warnings appear. |
| `components/sensor/sensor_simulator.py`                            | Simulates an IoT sensor by replaying `validation_data.example.csv` row by row and posting each reading to the Data Ingestion Service via REST. Reads send interval and anomaly rate from `config.yaml`. Applies random jitter to values for diversity and injects ~5% synthetic anomalies (extreme readings) to trigger ML alerts for demo purposes. Loops forever to simulate a continuous sensor stream. |
| `components/sensor/Dockerfile`                                     | Container definition for the Sensor Simulator. No exposed port — it only makes outgoing requests. |
| `components/sensor/requirements.txt`                               | Python dependencies for the Sensor Simulator (pandas, requests). |
| `k8s/*.yaml`                                                          | Kubernetes deployment manifests. Define how each microservice is deployed, exposed, and configured in a cluster. `k8s/database/pvc.yaml` declares the shared dataset volume both ingestion and ML mount. |

### Key concept: blueprints

Blueprints are the routing system used in `routers/`. Each file inside
`routers/` defines a Flask **Blueprint** — a group of related API endpoints.
This applies to the services that keep the `app/` split (Backend API, Data
Ingestion Service, and eventually the ML Service).

- `components/backend-api/app/routers/sensor.py` → Defines `sensor_bp` with sensor routes
- `components/backend-api/app/routers/prediction.py` → Defines `prediction_bp` with prediction routes

These blueprints are then **registered** onto the Flask app in `main.py`:

```python
# main.py — imports and registers blueprints
from app.routers.sensor import sensor_bp
from app.routers.prediction import prediction_bp

app.register_blueprint(sensor_bp)
app.register_blueprint(prediction_bp)
```

This keeps routes organised by feature instead of having everything in one file.

> Note: the Notification Service does **not** use blueprints — it is a
> single-file app where routes are defined directly in `app/main.py`.

---

## Technology decisions

| Component        | Technology             | Justification                                                     |
|------------------|------------------------|-------------------------------------------------------------------|
| Backend API      | Flask + PySpark        | Flask for lightweight HTTP; PySpark for large-scale               |
|                  |                        | sensor data processing (Spark session TBD).                       |
| Config           | PyYAML + config.yaml   | Centralised non-sensitive config (thresholds, tuning) read by     |
|                  |                        | services at startup; served to frontend via `GET /api/config`.    |
| Database         | PostgreSQL             | Strong relational support for structured sensor data;             |
|                  |                        | ACID compliance; mature tooling.                                  |
| ORM              | SQLAlchemy             | Standard Python ORM; decouples app logic from SQL.                |
| Containerisation | Docker                 | Consistent runtime across environments; single-command            |
|                  |                        | startup via docker-compose.                                       |
| Orchestration    | Kubernetes             | Automated deployment, scaling, self-healing, and load             |
|                  |                        | balancing across microservices.                                   |
| Frontend         | HTML/CSS/JS + Chart.js | Static dashboard served to the browser; polls the                 |
|                  |                        | Backend API and Notification Service via REST.                    |
| ML Service       | scikit-learn           | IsolationForest trained on the cleaned dataset; lazy training,    |
|                  | (IsolationForest)      | `model_ready` health flag, and 503 until data is available.       |
| Notifications    | Telegram Bot API       | Alerts pushed to a Telegram chat; configured via                  |
|                  |                        | environment variables (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`). |

---

## Key development decisions

### Data pipeline
- **Raw data as `.example.csv`** — Committed file is ground truth; cleaned output is
  git-ignored since it evolves with the cleaning process
- **Cleaning logic kept simple** — Wrapped in functions but kept minimal to avoid
  over-engineering; same code runs locally and in Docker
- **Ingestion service cleans and forwards** — Cleaning happens in the ingestion
  service, not in SQL; keeps data flow consistent with microservice architecture
- **Ingestion creates `sensor_data_cleaned.csv`** — Only exists after data is
  registered via `POST /api/ingest/file`; not committed to the repo
- **No data is cleaned at startup** — Ingestion starts "empty" to simulate a
  deployment that begins with no raw data; the cleaned dataset is produced on
  demand when data is registered
- **ML trains on the cleaned dataset** — The ML service never touches raw data;
  it reads `sensor_data_cleaned.csv`, keeping a single source of cleaning truth
- **ML trains lazily** — If no cleaned dataset exists at startup, the ML service
  starts idle (`model_ready: false`), retries training on the first prediction
  request, and returns 503 with an actionable message until data is available.
  This keeps the services loosely coupled
- **Predictions are persisted in the backend** — The ML service is stateless
  (in-memory model), so results are stored in the `predictions` table by the
  Backend API and served to the dashboard via `GET /api/predictions`

### ML model & scoring

- **Isolation Forest** — The system uses scikit-learn's Isolation Forest, an
  unsupervised anomaly detection algorithm. The core idea: anomalies are
  **few and different** from normal data points. The algorithm builds an
  ensemble of random decision trees (`n_estimators = 200`). Each tree
  recursively partitions the feature space by randomly selecting a feature
  and a split value. Anomalous points are isolated in fewer splits (shorter
  path length in the tree), while normal points require more splits to
  separate. The shorter the average path across all trees, the more
  anomalous the point

- **Training** — The model is trained on three sensor features:
  `temperature`, `humidity`, and `air_quality` from the cleaned dataset.
  The `contamination` parameter (default `0.02`, from `config.yaml`) sets
  the expected fraction of anomalies in the training data. It controls the
  decision boundary — a higher contamination makes the model more sensitive
  (flags more points as anomalous), while a lower value makes it more
  conservative. With `contamination = 0.02`, the model expects roughly 2%
  of training readings to be anomalous

- **Anomaly score** — `model.decision_function()` returns a signed distance
  to the decision boundary: **negative = anomaly, positive = normal**.
  The magnitude indicates how far the point is from the boundary — a score
  of `-0.15` is more anomalous than `-0.03`. Typical normal readings
  score between `0.0` and `0.3`; mild anomalies fall between `0.0` and
  `-0.05`; clear anomalies are below `-0.05`. The notification threshold
  (`anomaly_score_threshold: 0.05` in `config.yaml`) means Telegram
  alerts only fire when `score < -0.05`, filtering out the mild cases

- **Severity** — The raw anomaly score is mapped to a 0–1 severity value
  using a sigmoid function: `severity = 1 / (1 + exp(steepness * score))`.
  With the default steepness of 10, this produces:
  - Score `0.0` (boundary) → severity `0.50` (50% bar)
  - Score `-0.05` (notification threshold) → severity `0.62` (62% bar)
  - Score `-0.10` → severity `0.73`
  - Score `-0.20` → severity `0.88`
  - Score `-0.30` → severity `0.95`

  The steepness parameter (configurable in `config.yaml`) controls how
  sharply the bar transitions. Higher steepness means a sharper green-to-red
  shift near the boundary

- **Safety-net** — A hardcoded `ABSOLUTE_MAX_TEMP = 50°C` catches
  physically dangerous values that may fall outside the training
  distribution. If triggered, severity is pinned to `1.0` regardless of the
  model score. The Isolation Forest should catch these, but this provides a
  hard floor

### Notifications
- **Backend triggers on ML anomalies** — The notification service is only
  called by the Backend API when the ML model flags a reading as anomalous
  (`store_prediction`). One notification per anomalous reading — rare events
  in an early-warning system must not be delayed or coalesced away
- **ML model is the single source of truth** — Alerting decisions are driven
  entirely by the IsolationForest model's anomaly score. The notification
  service is a pure message sender — it does not make alerting decisions
- **Two-tier filtering reduces alert fatigue** — Not every anomaly triggers a
  Telegram notification. The model flags anomalies when `score < 0`, but the
  notification only fires when `score < -ANOMALY_SCORE_THRESHOLD` (default
  0.05, configurable in `config.yaml`). This buffer means mild anomalies are
  visible on the dashboard (red dots, severity bar) but do not spam Telegram.
  Operators can tune the threshold in `config.yaml` to control the sensitivity
  vs. noise tradeoff
- **Severity sigmoid** — The ML service maps the raw anomaly score to a 0–1
  severity value using a sigmoid function (`severity = 1/(1 + exp(steepness *
  score))`). The steepness parameter (default 10, from `config.yaml`) controls
  how sharply the bar transitions from green to red. This gives operators a
  visual sense of anomaly intensity on the dashboard
- **Safety-net threshold** — The ML service has one hardcoded safety-net
  (`ABSOLUTE_MAX_TEMP = 50°C`) for physically dangerous values that may fall
  outside the training distribution. The IsolationForest should catch these,
  but this provides a hard floor
- **Two onboarding paths** — First-time users self-provision a bot via
  BotFather (token + chat id into `.env` / Secret). Teams can instead reuse
  one bot in a shared Telegram group: the owner adds the bot to the group and
  groupmates simply join, with credentials staying in the shared deployment
  config. The `/` health endpoint exposes `telegram_configured` so a new user
  can confirm their setup
- **Credentials are secrets** — `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
  are injected from a local `.env` for compose (git-ignored) or a k8s `Secret`
  (`k8s/notification-service/secret.example.yaml` is a placeholder template;
  create the real one with `kubectl create secret generic telegram-credentials
  --from-literal=TELEGRAM_BOT_TOKEN=... --from-literal=TELEGRAM_CHAT_ID=...`)
- **Dashboard only reads alerts** — `GET /api/alerts` drives the alert panel;
  the dashboard never POSTs `/api/notify`, so polling cannot spam Telegram
  with duplicates for the same reading

### Database
- **`init.sql` creates table only, no seeding** — Ingestion service handles data
  flow; DB schema stays clean and independent of data volume
- **SQLAlchemy ORM** — Decouples app logic from raw SQL; models serve as single
  source of truth for table schema

### Local development vs Docker
The `components/database/` folder is the single source of data for both
environments. Docker's volume mount (`./components/database:/data`) maps
the host folder to the container, so both environments read and write to the
same files.

- **Local:** `Config.DATA_DIR` defaults to `../database` (relative path; from
  `components/data-ingestion-service/` this resolves to
  `components/database/`)
- **Docker:** `DATA_DIR=/data` env var overrides the default; volume mount
  makes `/data` equivalent to `./components/database/` on the host

This means cleaned output appears in `components/database/` regardless of
how you run the service. No duplication, no sync issues.

### Docker & deployment
- **`depends_on` for startup order** — Database → Backend API → Ingestion
  service ensures services connect in the right sequence
- **Shared dataset volume** — `./components/database` is bind-mounted as
  `/data` into both ingestion and ML containers, so the raw file, the cleaned
  output, and the trained model inputs all stay in one place
- **`config.yaml` volume** — Mounted as read-only into backend-api, ml-service,
  and sensor-simulator (`./config.yaml:/app/config.yaml:ro`). Changing a
  threshold in `config.yaml` and restarting the affected containers is enough
  to retune the system — no rebuild required
- **Kubernetes dataset storage** — The same shared folder is represented in
  k8s by the `dataset-pvc` (see `k8s/database/pvc.yaml`). Both deployments
  mount it at `/data`; the ingestion pod seeds the raw example file into it
  via the `dataset-seed` init container. Apply order:
  `kubectl apply -f k8s/database/pvc.yaml` first, then the service manifests
- **Log suppression** — All four Flask services set the `werkzeug` logger to
  WARNING level in `main.py`; the frontend nginx uses `access_log off;`.
  Routine 200/201 request logs are suppressed so only errors and startup
  notices appear in `docker compose logs`

---

## Development style & conventions

How new code in this project should look, structured, and committed. These
conventions come from the patterns already in the codebase; when in doubt,
match the neighbouring service.

### Service structure
- **Backend-style services** (backend-api, ml-service, data-ingestion) use the
  `app/` split: `main.py` (a `create_app()` factory), `config.py`,
  `routers/` (Flask blueprints), `services/` (business logic and HTTP
  clients), and — for the backend — `models/` (SQLAlchemy) and `database.py`.
- **Small single-purpose services** stay single-file: the notification service
  defines its routes, threshold logic, and Telegram sending all in
  `app/main.py`.
- **Blueprints** are named `name_bp = Blueprint("name", __name__)` and
  registered in `main.py` with `url_prefix="/api"`.

### Python code style
- 4-space indentation, `snake_case` names, `"""docstrings"""` for modules and
  public functions.
- One idea per function; keep functions small and single-purpose. Prefer plain
  functions over classes for service logic unless state is genuinely needed.

### Configuration & secrets
- **Two-tier configuration** — Secrets (bot tokens, database credentials) live
  in `.env` (gitignored) or a k8s `Secret`. Non-sensitive tuning values
  (thresholds, ML hyperparameters, simulator intervals) live in `config.yaml`
  at the repo root (committed). This keeps secrets out of version control
  while making tuning values visible and reviewable.
- **`config.yaml`** — Centralised config read by backend-api, ml-service, and
  sensor-simulator at startup via a `_load_yaml()` helper. Each service
  searches a few candidate paths (Docker mount, standalone relative path,
  current directory) so the same code works in both environments. In Docker,
  `config.yaml` is mounted as a read-only volume (`./config.yaml:/app/config.yaml:ro`).
- **`GET /api/config`** — The Backend API serves non-sensitive config values
  from `config.yaml` to the frontend dashboard. The dashboard fetches this on
  page load so threshold displays and severity bar markers stay in sync with
  the backend without hardcoding values in JavaScript.
- **Secrets** use empty-string defaults and are injected per environment —
  `.env` for Compose, a k8s `Secret`, or shell environment variables. Never
  hardcode a secret in code.
- **Env validation** — The `env-validator` service (Docker Compose) and
  `scripts/validate-env.py` (standalone) check that `.env` exists and all
  required variables are set before any service starts. In Docker, the
  validator runs as a healthcheck; other services depend on it being healthy.
  In standalone mode, run `python scripts/validate-env.py` before starting
  services. This is the **first layer**: it catches placeholder values and
  missing variables so misconfigured deployments fail fast.
- **Runtime confirmation** — Each service's startup print confirms the
  credentials actually reached the process. For example, the notification
  service prints `Telegram configured` when both `TELEGRAM_BOT_TOKEN` and
  `TELEGRAM_CHAT_ID` are loaded, or `Telegram not configured` when they
  are not. This is the **second layer**: the env-validator ensures the
  `.env` file is correct; the startup prints ensure the values were
  injected into the container's environment.
- **Auto-loading `.env`** — Each service calls `load_dotenv()` from
  `python-dotenv` at startup, so `.env` is automatically loaded into
  `os.environ` when running standalone. No manual variable exports needed.
- **Non-secret config in env vars** (service URLs, dataset paths) carries a
  real default in code, and the same value is set explicitly in
  `docker-compose.yml` / the k8s ConfigMap so behaviour is identical whether
  or not the variable is set.
- Never commit credentials, keys, or generated artifacts (the cleaned dataset
  is git-ignored for this reason).

### Service entry points
- Flask services expose `create_app()` and start via
  `if __name__ == "__main__": app.run(host="0.0.0.0", port=NNNN)`.
- Browser-facing services enable CORS with an `@app.after_request` handler.
- Ports are fixed per service; see the Port Assignments table.

### API responses & error handling
- JSON in, JSON out. Responses use `jsonify(...)`.
- Errors use `jsonify({"error": "..."})` with the appropriate status code:
  `400` for validation, `503` when a dependency is not ready (e.g. ML model
  not trained), and pass-through codes for informative upstream errors.
- Validate required fields at the top of a route and return a clear
  "Missing fields" message.
- Inter-service calls live in `app/services/` HTTP client modules. Use
  `raise_for_status()`; wrap in `try/except` when the call is best-effort
  (must never break the caller — e.g. `notification_client`), or pass the
  `HTTPError` through when the upstream error is useful to the caller (e.g.
  the ML 503).

### Frontend (vanilla JS) & CSS
- Plain JavaScript with **Chart.js** for charts — no framework, no build
  step, no bundler. Files live under `html/`, `css/`, and `js/`.
- A `CONFIG` object at the top of the script holds every tunable (base URLs,
  poll interval, AQ labels). Threshold values (`NOTIFICATION_THRESHOLD`,
  `MODEL_CONTAMINATION`, `SEVERITY_STEEPNESS`) have defaults that are
  overridden by `GET /api/config` on page load, keeping the dashboard in sync
  with `config.yaml` without hardcoding.
- **ML Analysis panel** — Displays the latest prediction's severity bar,
  anomaly score, and status. The severity bar has two threshold markers:
  a dark line at 50% (model boundary, `score = 0`) and a red line at ~62%
  (notification trigger, `score = -threshold`), with a small legend below
  the bar identifying each line. Below a divider, static rows show
  "Notify when: `score < -0.05`" and "Model: `contamination 2%`" so
  operators understand the tuning at a glance.
- Cache DOM element references once at the top of the script; drive styling
  from `data-*` attributes (`#note[data-state]`) rather than toggling classes.
- Access the API through small helpers (e.g. `fetchJSON`), `async/await`, and
  a `try/catch` per fetch so a downed dependency shows an "Offline" status
  instead of breaking the page.
- Polling pattern: a `loadConfig()` fetches config first, then `refresh()`
  runs once and on a timer (`setInterval`). If the config fetch fails,
  hardcoded defaults are used.
- Plain CSS with id-based selectors for unique components and a small media
  query for narrow screens; state styling via `[data-state=...]` selectors.
- **Served by nginx** — `components/frontend/Dockerfile` + `nginx.conf` serve
  the static files on port 3000. Compose wires it in as the `frontend`
  service; `k8s/frontend/` holds the deployment and the NodePort service
  (30080). The nginx container proxies `/api/*` to the Backend API and
  Notification Service, so the browser only talks to one origin. The
  frontend has no `depends_on` (it is not a microservice, just a static-file
  server with a proxy).

### Git commits
- Summary line: lowercase, imperative ("add", "fix", "refactor", "document",
  "wire").
- A short body describing what changed and why, ending with a `Why:`
  paragraph when the rationale isn't obvious from the change itself.
- One logical change per commit (service code, deployment config, and docs are
  committed separately).
- Feature changes also update the relevant docs (Architecture.md tree and
  decisions, per-service READMEs) in the same commit or an accompanying docs
  commit.

### Standalone scripts & verification
- Build services as **importable modules first, standalone scripts second**:
  `if __name__ == "__main__"` blocks call the same functions the routes use.
- There is no committed test framework. Verify by running services
  standalone, exercising endpoints with the Flask test client / `curl`, and
  running import checks.

### Deployment hygiene
- One Dockerfile per service; `docker-compose.yml` at the repo root; one
  `k8s/` manifest folder per service.
- Environment: `.env` (local), ConfigMap (non-secret), Secret (credentials).
- Keep generated data and build outputs out of the repository.
- **Log suppression** — Flask services set the `werkzeug` logger to WARNING
  level so routine request logs (200, 201) do not clutter terminal output.
  The frontend nginx disables access logging entirely (`access_log off;`).
  Only errors, warnings, and startup notices appear in `docker compose logs`.

### Database schema changes
- There is no migrations framework. To change a table, update the SQLAlchemy
  model (`app/models/`) **and** `components/database/init.sql` together.
- `Base.metadata.create_all` only creates missing tables — it does **not**
  alter existing ones. For a development database, recreate it or apply the
  change manually.

### Adding a new microservice
1. Create `components/<name>/` with the `app/` split (or a single-file app
   for small services) plus a `requirements.txt`.
2. Add a `Dockerfile`: `python:3.11-slim`, `WORKDIR /app`, install
   `requirements.txt`, `EXPOSE <port>`, `CMD ["python", "app/main.py"]`.
3. Register it in `docker-compose.yml` (`build`, `ports`, `environment`,
   `depends_on`).
4. Add `k8s/<name>/`: `deployment.yaml` (image `<name>:latest`, `envFrom`
   referencing the ConfigMap/Secret), `service.yaml` (ClusterIP,
   `port: 80` → `targetPort`), and a `configmap.yaml` for non-secret config.
5. Register it in Architecture.md (repository tree, file-by-file table,
   Microservice Communication table, Port Assignments) and add a service
   README if it has non-obvious setup or usage.
6. Wire cross-service calls through the backend `app/services/` HTTP-client
   pattern (best-effort or pass-through, per the error-handling conventions).

---

## Microservice communication

| From             | To                   | Protocol  | Purpose                                                            |
|------------------|----------------------|-----------|--------------------------------------------------------------------|
| Sensor Simulator | Data Ingestion       | REST/HTTP | Replay one sensor reading at a time                                |
| Frontend         | Backend API          | REST/HTTP | User requests, data display                                        |
| Frontend         | Backend API          | REST/HTTP | Fetches non-sensitive config thresholds on page load (`GET /api/config`) |
| Frontend         | Notification Service | REST/HTTP | Reads recent alerts for the alert panel (`GET /api/alerts`)        |
| Data Ingestion   | Backend API          | REST/HTTP | Send sensor data for processing                                    |
| Backend API      | PostgreSQL           | SQL       | Data persistence & retrieval                                       |
| Backend API      | ML Service           | REST/HTTP | Anomaly prediction requests (`/api/predict`, `/api/predict/batch`) |
| ML Service       | Backend API          | REST/HTTP | Prediction results returned (score, severity, alerts)              |
| Backend API      | Notification Service | REST/HTTP | Triggers `/api/notify` on ML-flagged anomalies                     |

---

## Port assignments

| Service                | Container Port | k8s NodePort | Notes                                           |
|------------------------|----------------|--------------|-------------------------------------------------|
| Backend API            | 5000           | 30000        | Flask default, central API layer                |
| ML Service             | 5001           | —            | Anomaly detection (lazy-trained IsolationForest)|
| Notification Service   | 5002           | 30002        | Alert processing (Telegram)                     |
| Data Ingestion Service | 5003           | —            | CSV/JSON sensor data intake                     |
| PostgreSQL             | 5432           | —            | Database                                        |
| Frontend               | 3000           | 30080        | Dashboard UI (served statically via nginx)      |
| Sensor Simulator       | —              | —            | No inbound port (outgoing requests only)        |

NodePort services (30000, 30002, 30080) are exposed for browser access in
local clusters (minikube / Docker Desktop). Use `minikube service list` or
`kubectl get svc` to confirm the assigned ports.

---

## Docker & Kubernetes strategy

### Docker
- Each microservice has its own `Dockerfile`
- `docker-compose.yml` at root for local multi-service development
- Environment variables injected via `.env` files or ConfigMaps

### Kubernetes
- Separate YAML manifests per service under `k8s/`
- ConfigMaps for environment configuration
- Services for internal DNS-based inter-service communication
- Deployments with replica counts for scalability
- **Startup ordering** — The ML Service trains on `sensor_data_cleaned.csv`,
  which only exists after someone calls `POST /api/ingest/file` on the Data
  Ingestion Service. The init container seeds the *raw* CSV into the shared
  PVC, but cleaning happens on-demand. Until that step runs, the ML Service
  returns 503 on prediction requests. The sensor simulator can start
  immediately — it will trigger predictions that get 503'd until the model
  is trained. This is by design (loose coupling), not an error

### Local development (standalone mode)

Services can be run individually for development and testing without
starting the full Docker Compose stack. Each service module includes an
`if __name__ == "__main__"` entry point for standalone execution.

**Data Ingestion (standalone):**
```bash
cd components/data-ingestion-service
python -m app.services.data_ingestion
```

This reads `sensor_data.example.csv`, cleans it, and saves
`sensor_data_cleaned.csv` to the `components/database/` folder. No Flask
server or backend API required — useful for testing the cleaning pipeline
independently.

**ML Service (standalone):**
```bash
cd components/ml-service
python -m app.services.model_service
```

This loads `sensor_data_cleaned.csv`, trains the IsolationForest, and prints
sample predictions (first 3 dataset readings plus a synthetic anomaly) so the
model can be sanity-checked without starting the server. It mirrors the
service's error handling: if no cleaned dataset exists yet, it prints the same
not-trained message the API returns as a 503 and exits instead of crashing.

**Key design principle:** Services are built as importable modules first,
standalone scripts second. The `if __name__` block is minimal (calls the
same functions the Flask router uses, including the shared
`train_if_available` helper), ensuring local and Docker behaviour stay
consistent.

---

## Data flow workflows

These end-to-end scenarios show how the microservices collaborate to deliver
product value. Each workflow traces a user-visible event through the system.

### Workflow 1: Sensor reading arrives

**Trigger:** Sensor Simulator sends a reading to the Data Ingestion Service.

```
Sensor Simulator
  │  POST /api/ingest/reading
  ▼
Data Ingestion Service
  │  validates + formats the reading
  │  POST /api/sensors  →  Backend API  →  PostgreSQL (stored)
  ▼
Backend API
  │  POST /api/predict  →  ML Service (anomaly scoring)
  │  stores prediction in PostgreSQL
  │  if anomaly_score < -0.05:
  │    POST /api/notify  →  Notification Service  →  Telegram
  ▼
Frontend Dashboard (polls every 8s)
  │  GET /api/sensors       →  updates charts + latest values
  │  GET /api/predictions   →  colours anomalous points red
  │  GET /api/alerts        →  shows alert in notification panel
  │  GET /api/config        →  keeps threshold displays in sync
```

**Product value:** A single sensor reading flows through validation, storage,
ML analysis, optional alerting, and dashboard display — all without manual
intervention. The user sees the reading on the dashboard within seconds.

### Workflow 2: Anomaly detected and alerted

**Trigger:** ML Service scores a reading and the anomaly score crosses the
notification threshold (`score < -0.05`).

```
ML Service
  │  model.decision_function() → raw_score = -0.08
  │  model.predict()           → -1 (anomaly)
  │  severity = sigmoid(-0.08) → 0.71
  │  returns: {anomaly_score: -0.08, severity: 0.71, is_anomaly: true}
  ▼
Backend API (prediction_service.py)
  │  stores prediction in PostgreSQL
  │  checks: is_anomaly AND anomaly_score < -0.05 → True
  │  calls notification_client.notify_anomaly()
  ▼
Notification Service
  │  receives alert message
  │  sends Telegram message (if configured)
  │  stores in recent_alerts for dashboard
  ▼
Frontend Dashboard
  │  red dot appears on charts at that timestamp
  │  severity bar fills to 71% (past the ~62% notification marker)
  │  anomaly score shows "ALERT" (buffer ≤ 0)
  │  notification panel shows the alert message + timestamp
```

**Product value:** The two-tier filtering ensures only genuinely anomalous
readings trigger Telegram notifications. Mild anomalies (score between 0 and
-0.05) are visible on the dashboard but do not cause alert fatigue.

### Workflow 3: Operator tunes the notification threshold

**Trigger:** Operator edits `config.yaml` to change `anomaly_score_threshold`.

```
config.yaml (anomaly_score_threshold: 0.1)
  │
  ├──▶ Backend API (restart)
  │      Config.ANOMALY_SCORE_THRESHOLD = 0.1
  │      prediction_service now only notifies when score < -0.1
  │
  ├──▶ Frontend Dashboard (page reload)
  │      GET /api/config → {notification_threshold: 0.1}
  │      severity bar notification marker shifts position
  │      "Notify when" row updates to "score < -0.1"
  │
  └──▶ ML Service (restart) — no change needed
         contamination and steepness unchanged
```

**Product value:** Threshold tuning is a config-file change, not a code change.
Operators can adjust the sensitivity vs. noise tradeoff without redeploying
or rebuilding containers — just edit `config.yaml` and restart affected services.

---

## Open decisions (pending team discussion)

The following items have **not yet been finalised** and are subject to change:

1. **PySpark Usage Scope** — How Spark will be used in the backend is
   undecided. Options include batch aggregation, preprocessing for ML, or
   running Spark MLlib models directly. `spark_session.py` is currently a stub.

2. **Sensor Data Input Format** — The primary flow is now the Sensor
   Simulator replaying the CSV dataset as JSON API payloads. CSV uploads and
   IoT streaming remain possible future inputs.

3. **Live Sensor → Ingestion link** — The sensor simulator posts to
   `/api/ingest/reading`, which is now implemented in the Data Ingestion
   Service. Each reading is validated, formatted, and forwarded to the
   Backend API for storage.

---
