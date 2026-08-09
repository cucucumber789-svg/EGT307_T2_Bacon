# Architecture — Smart Environmental Monitoring System

## Overview

This document outlines the overall system architecture, repository structure,
technology decisions, and deployment strategy for the Smart Environmental
Monitoring System. The system uses a **microservices architecture** orchestrated
by **Docker** and **Kubernetes**.

---

## System Architecture (High-Level)

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

## Repository File Structure

```
EGT307_T2_Bacon/
├── docker-compose.yml             # Local multi-service development
├── sensor_data.csv                # Raw sensor dataset (ground truth)
├── EGT307 PRESENTATION.pptx       # Project presentation
├── EGT307_Contribution.docx       # Individual contribution breakdown
│
├── ReadMe/                        # Project documentation
│   ├── README.md
│   └── Architecture.md
│
├── microservices/                 # All services live under this folder
│   ├── backend-api/               # BACKEND API — Flask + PySpark
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py            # Flask app entry point (create_app)
│   │   │   ├── config.py          # Environment-based configuration
│   │   │   ├── database.py        # SQLAlchemy engine + session
│   │   │   ├── spark_session.py   # Spark session initialisation (TBD)
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── sensor.py      # SensorReading SQLAlchemy model
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   └── sensor.py      # Request/response schemas (TBD)
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sensor.py      # Sensor CRUD routes (implemented)
│   │   │   │   └── prediction.py  # Prediction routes (TBD)
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       ├── sensor_service.py  # Sensor business logic (TBD)
│   │   │       └── ml_client.py       # ML service HTTP client (TBD)
│   │   ├── tests/
│   │   │   └── __init__.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── ml-service/                # ML SERVICE — anomaly detection
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py            # Flask app entry point (TBD)
│   │   │   ├── config.py          # Model path and ML settings (TBD)
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   └── prediction.py  # Prediction endpoints (TBD)
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       └── model_service.py # IsolationForest prototype (notebook-style)
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
│   │   └── sensor_data.example.csv   # Raw sensor data (ground truth)
│   │
│   ├── frontend/                  # FRONTEND — dashboard (HTML/CSS/JS + Chart.js)
│   │   ├── css/
│   │   │   └── styles.css
│   │   ├── html/
│   │   │   └── dashboard.html
│   │   └── js/
│   │       └── dashboard.js
│   │
│   └── sensor/                    # SENSOR SIMULATOR — replays dataset as IoT stream
│       ├── sensor_simulator.py
│       ├── Dockerfile
│       └── requirements.txt
│
└── k8s/                          # KUBERNETES — deployment manifests
    ├── backend-api/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── ml-service/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── notification-service/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── data-ingestion-service/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── database/                  # (empty placeholder)
    └── frontend/                  # (empty placeholder)
```

---

## File Structure Guide

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

### How the Files Connect

All services live under `microservices/`. The Backend API is the largest
service and still uses the full `app/` split:

```
microservices/backend-api/app/main.py  (entry point — starts the app)
  ├── imports config.py          (reads environment variables)
  ├── imports database.py        (connects to PostgreSQL)
  ├── imports spark_session.py   (creates Spark session)   (TBD)
  └── registers routers/sensor.py      (adds /api/sensors routes)

routers/sensor.py  (handles HTTP requests)
  ├── imports models/sensor.py   (to read/write sensor data in DB)
  ├── imports schemas/sensor.py  (to validate incoming JSON)   (TBD)
  └── imports services/sensor_service.py (to process data)     (TBD)

routers/prediction.py  (handles prediction requests)            (TBD)
  ├── imports services/ml_client.py (to call ML microservice)   (TBD)
  └── imports services/sensor_service.py (to fetch sensor data) (TBD)
```

The Notification Service takes a simpler shape: it is a **single-file app** —
`app/main.py` contains the Flask routes, the threshold checks, and the
Telegram sending logic all in one place. The Data Ingestion Service keeps the
`app/` split but is smaller than the Backend API. The ML Service entry points
(`main.py`, `config.py`, `routers/prediction.py`) are stubs; the working
anomaly-detection prototype lives in `app/services/model_service.py`.

### File-by-File Explanation

Paths below are relative to the repo root unless marked `(relative to service)`,
in which case they are relative to the service folder inside `microservices/`.

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Defines all services (backend, ML, notification, ingestion, database) and how they run together locally. One command starts everything. The Sensor Simulator and Frontend are not yet defined here. |
| `sensor_data.csv` | Raw sensor dataset (ground truth) that the Sensor Simulator replays. |
| `microservices/backend-api/app/main.py` | Flask app entry point. Creates the app, registers blueprints (routers), and starts the server. This is the first file that runs. |
| `microservices/backend-api/app/config.py` | Stores all configuration (database URL, ML service URL, etc.) loaded from environment variables. Keeps secrets out of code. |
| `microservices/backend-api/app/database.py` | Creates the SQLAlchemy engine and session. Other files import `SessionLocal` to query or insert data into PostgreSQL. |
| `microservices/backend-api/app/spark_session.py` | Creates and returns a PySpark `SparkSession`. Services import this to run Spark data processing operations. (TBD) |
| `microservices/backend-api/app/routers/sensor.py` | Defines Flask Blueprint with sensor endpoints (`GET /api/sensors`, `GET /api/sensors/count`, `POST /api/sensors`, `POST /api/sensors/batch`). Receives HTTP requests and queries/inserts directly into the DB. |
| `microservices/backend-api/app/routers/prediction.py` | Defines Flask Blueprint with prediction endpoints (`POST /api/predict`). Calls ML service and returns anomaly results. (TBD) |
| `microservices/backend-api/app/models/sensor.py` | SQLAlchemy model defining the `sensor_readings` table schema (`SensorReading`). Used by database.py and imported by routes to query/insert data. |
| `microservices/backend-api/app/schemas/sensor.py` | Request/response schemas for validating JSON payloads and serialising responses. (TBD) |
| `microservices/backend-api/app/services/sensor_service.py` | Business logic for sensor data. May use PySpark for data transformations and aggregations. (TBD) |
| `microservices/backend-api/app/services/ml_client.py` | HTTP client that sends data to the ML microservice and receives prediction results back. (TBD) |
| `microservices/backend-api/Dockerfile` | Tells Docker how to build the backend container — installs dependencies, copies code, runs the app. |
| `microservices/backend-api/requirements.txt` | Lists all Python packages the project needs (Flask, SQLAlchemy, etc.). |
| `microservices/ml-service/app/main.py` | Flask app entry point for ML Service. Registers prediction blueprints. (TBD) |
| `microservices/ml-service/app/config.py` | Stores model path and ML framework settings. Loaded from environment variables. (TBD) |
| `microservices/ml-service/app/routers/prediction.py` | Defines Flask Blueprint with prediction endpoints (`POST /api/predict`, `POST /api/predict/batch`). (TBD) |
| `microservices/ml-service/app/services/model_service.py` | Contains the scikit-learn **IsolationForest** anomaly-detection prototype (training, threshold checks, and a `predict()` function) developed in a notebook style. Needs refactoring into a production Flask service. |
| `microservices/ml-service/Dockerfile` | Container definition for ML Service. |
| `microservices/ml-service/requirements.txt` | Python dependencies for ML Service (Flask + ML framework TBD). |
| `microservices/notification-service/app/main.py` | Single-file Flask app for the Notification Service. Checks readings against 3 thresholds (temperature > 39, humidity > 55, air_quality <= 2), sends Telegram alerts via the Telegram Bot API, and keeps the 50 most recent alerts in memory for the dashboard (`GET /api/alerts`). |
| `microservices/notification-service/Dockerfile` | Container definition for Notification Service. |
| `microservices/notification-service/requirements.txt` | Python dependencies for Notification Service (Flask, requests). |
| `microservices/data-ingestion-service/app/main.py` | Flask app entry point for Data Ingestion Service. Registers ingestion blueprints. |
| `microservices/data-ingestion-service/app/config.py` | Stores Backend API URL, `DATA_DIR`, and allowed file formats loaded from environment variables. |
| `microservices/data-ingestion-service/app/routers/ingestion.py` | Defines Flask Blueprint with data intake endpoints (`POST /api/ingest/file`). Accepts CSV/JSON sensor data. |
| `microservices/data-ingestion-service/app/services/data_ingestion.py` | Parses raw CSV sensor data (drop columns, rename, coerce types, drop NaN), saves cleaned output to `sensor_data_cleaned.csv`, and forwards records to the Backend API. Also runnable standalone (`python -m app.services.data_ingestion`). |
| `microservices/data-ingestion-service/Dockerfile` | Container definition for Data Ingestion Service. |
| `microservices/data-ingestion-service/requirements.txt` | Python dependencies for Data Ingestion Service (Flask, requests, pandas). |
| `microservices/database/init.sql` | SQL script that runs when PostgreSQL starts. Creates tables. |
| `microservices/database/sensor_data.example.csv` | Raw sensor data (ground truth) used by the ingestion pipeline. |
| `microservices/frontend/html/dashboard.html` | Dashboard page markup. |
| `microservices/frontend/css/styles.css` | Dashboard styling. |
| `microservices/frontend/js/dashboard.js` | Dashboard logic. Polls the Backend API for sensor readings and the Notification Service for alerts, renders charts with Chart.js. |
| `microservices/sensor/sensor_simulator.py` | Simulates an IoT sensor by replaying `sensor_data.csv` row by row and posting each reading to the Data Ingestion Service via REST, one record every few seconds. |
| `microservices/sensor/Dockerfile` | Container definition for the Sensor Simulator. No exposed port — it only makes outgoing requests. |
| `microservices/sensor/requirements.txt` | Python dependencies for the Sensor Simulator (pandas, requests). |
| `k8s/*.yaml` | Kubernetes deployment manifests. Define how each microservice is deployed, exposed, and configured in a cluster. |

### Key Concept: Blueprints

Blueprints are the routing system used in `routers/`. Each file inside
`routers/` defines a Flask **Blueprint** — a group of related API endpoints.
This applies to the services that keep the `app/` split (Backend API, Data
Ingestion Service, and eventually the ML Service).

- `microservices/backend-api/app/routers/sensor.py` → Defines `sensor_bp` with sensor routes
- `microservices/backend-api/app/routers/prediction.py` → Defines `prediction_bp` with prediction routes (TBD)

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

## Technology Decisions

| Component        | Technology      | Justification                                            |
|------------------|-----------------|----------------------------------------------------------|
| Backend API      | Flask + PySpark | Flask for lightweight HTTP; PySpark for large-scale      |
|                  |                 | sensor data processing (Spark session TBD).              |
| Database         | PostgreSQL      | Strong relational support for structured sensor data;    |
|                  |                 | ACID compliance; mature tooling.                         |
| ORM              | SQLAlchemy      | Standard Python ORM; decouples app logic from SQL.       |
| Containerisation | Docker          | Consistent runtime across environments; single-command   |
|                  |                 | startup via docker-compose.                              |
| Orchestration    | Kubernetes      | Automated deployment, scaling, self-healing, and load    |
|                  |                 | balancing across microservices.                          |
| Frontend         | HTML/CSS/JS + Chart.js | Static dashboard served to the browser; polls the |
|                  |                 | Backend API and Notification Service via REST.           |
| ML Service       | scikit-learn    | IsolationForest prototype implemented; needs            |
|                  | (IsolationForest)| production refactor and serving approach decision.       |
| Notifications    | Telegram Bot API | Alerts pushed to a Telegram chat; configured via         |
|                  |                 | environment variables (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`). |

---

## Key Development Decisions

### Data Pipeline
- **Raw data as `.example.csv`** — Committed file is ground truth; cleaned output is
  git-ignored since it evolves with the cleaning process
- **Cleaning logic kept simple** — Wrapped in functions but kept minimal to avoid
  over-engineering; same code runs locally and in Docker
- **Ingestion service cleans and forwards** — Cleaning happens in the ingestion
  service, not in SQL; keeps data flow consistent with microservice architecture
- **Ingestion creates `sensor_data_cleaned.csv`** — Only exists after running the
  ingestion service; not committed to the repo

### Database
- **`init.sql` creates table only, no seeding** — Ingestion service handles data
  flow; DB schema stays clean and independent of data volume
- **SQLAlchemy ORM** — Decouples app logic from raw SQL; models serve as single
  source of truth for table schema

### Local Development vs Docker
The `microservices/database/` folder is the single source of data for both
environments. Docker's volume mount (`./microservices/database:/data`) maps
the host folder to the container, so both environments read and write to the
same files.

- **Local:** `Config.DATA_DIR` defaults to `../database` (relative path; from
  `microservices/data-ingestion-service/` this resolves to
  `microservices/database/`)
- **Docker:** `DATA_DIR=/data` env var overrides the default; volume mount
  makes `/data` equivalent to `./microservices/database/` on the host

This means cleaned output appears in `microservices/database/` regardless of
how you run the service. No duplication, no sync issues.

### Docker & Deployment
- **`depends_on` for startup order** — Database → Backend API → Ingestion
  service ensures services connect in the right sequence

---

## Microservice Communication

| From                | To                | Protocol  | Purpose                          |
|---------------------|-------------------|-----------|----------------------------------|
| Sensor Simulator    | Data Ingestion    | REST/HTTP | Replay one sensor reading at a time |
| Frontend            | Backend API       | REST/HTTP | User requests, data display      |
| Frontend            | Notification Service | REST/HTTP | Checks latest reading against thresholds, shows alerts |
| Data Ingestion      | Backend API       | REST/HTTP | Send sensor data for processing  |
| Backend API         | PostgreSQL        | SQL       | Data persistence & retrieval     |
| Backend API         | ML Service        | REST/HTTP | Anomaly prediction requests (TBD)|
| ML Service          | Backend API       | REST/HTTP | Prediction results returned (TBD)|
| Backend API         | Notification Service | REST/HTTP | Trigger alerts on anomalies (TBD) |

---

## Port Assignments

| Service                | Port | Notes                              |
|------------------------|------|------------------------------------|
| Backend API            | 5000 | Flask default, central API layer   |
| ML Service             | 5001 | Anomaly detection (TBD)            |
| Notification Service   | 5002 | Alert processing (Telegram)        |
| Data Ingestion Service | 5003 | CSV/JSON sensor data intake        |
| PostgreSQL             | 5432 | Database                           |
| Frontend               | 3000 | Dashboard UI (served statically)   |
| Sensor Simulator       | —    | No inbound port (outgoing requests only) |

---

## Docker & Kubernetes Strategy

### Docker
- Each microservice has its own `Dockerfile`
- `docker-compose.yml` at root for local multi-service development
- Environment variables injected via `.env` files or ConfigMaps

### Kubernetes
- Separate YAML manifests per service under `k8s/`
- ConfigMaps for environment configuration
- Services for internal DNS-based inter-service communication
- Deployments with replica counts for scalability

### Local Development (Standalone Mode)

Services can be run individually for development and testing without
starting the full Docker Compose stack. Each service module includes an
`if __name__ == "__main__"` entry point for standalone execution.

**Data Ingestion (standalone):**
```bash
cd microservices/data-ingestion-service
python -m app.services.data_ingestion
```

This reads `sensor_data.example.csv`, cleans it, and saves
`sensor_data_cleaned.csv` to the `microservices/database/` folder. No Flask
server or backend API required — useful for testing the cleaning pipeline
independently.

**Key design principle:** Services are built as importable modules first,
standalone scripts second. The `if __name__` block is minimal (calls the
same functions the Flask router uses), ensuring local and Docker behaviour
stay consistent.

---

## Open Decisions (Pending Team Discussion)

The following items have **not yet been finalised** and are subject to change:

1. **PySpark Usage Scope** — How Spark will be used in the backend is
   undecided. Options include batch aggregation, preprocessing for ML, or
   running Spark MLlib models directly. `spark_session.py` is currently a stub.

2. **Sensor Data Input Format** — The primary flow is now the Sensor
   Simulator replaying the CSV dataset as JSON API payloads. CSV uploads and
   IoT streaming remain possible future inputs.
   I chose wk2 dataset because it shows the exact same inferential conclusion as wk 3 dataset and it is not as heavily loaded compared to wk 3 dataset.

3. **ML Service API Contract** — The interface between Backend API and ML
   Service needs to be defined collaboratively before integration. The
   `routers/prediction.py` files on both sides are stubs.

4. **ML Service Productionisation** — The IsolationForest prototype in
   `model_service.py` is notebook-style (trains at import time, runs an
   embedded server). It needs refactoring into a proper Flask blueprint that
   loads a persisted model and serves predictions.

5. **Frontend Serving** — The dashboard is built (static HTML/CSS/JS), but
   how it is served and containerised is still open.

---
