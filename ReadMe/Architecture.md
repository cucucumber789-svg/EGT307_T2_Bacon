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
├── components/                 # All services live under this folder
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
│   │   │   │   └── prediction.py  # Predict + predictions routes
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
    │   ├── configmap.yaml          # thresholds (non-secret)
    │   └── secret.example.yaml     # Telegram credentials template (placeholder)
    ├── data-ingestion-service/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── database/                  # shared dataset PersistentVolumeClaim
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

### File-by-File Explanation

Paths below are relative to the repo root unless marked `(relative to service)`,
in which case they are relative to the service folder inside `components/`.

| File                                                                  | Purpose |
|-----------------------------------------------------------------------|---------|
| `docker-compose.yml`                                                  | Defines all services (backend, ML, notification, ingestion, database) and how they run together locally. One command starts everything. The Sensor Simulator and Frontend are not yet defined here. |
| `sensor_data.csv`                                                     | Raw sensor dataset (ground truth) that the Sensor Simulator replays. |
| `components/backend-api/app/main.py`                               | Flask app entry point. Creates the app, registers blueprints (routers), and starts the server. This is the first file that runs. |
| `components/backend-api/app/config.py`                             | Stores all configuration (database URL, ML service URL, etc.) loaded from environment variables. Keeps secrets out of code. |
| `components/backend-api/app/database.py`                           | Creates the SQLAlchemy engine and session. Other files import `SessionLocal` to query or insert data into PostgreSQL. |
| `components/backend-api/app/spark_session.py`                      | Creates and returns a PySpark `SparkSession`. Services import this to run Spark data processing operations. (TBD) |
| `components/backend-api/app/routers/sensor.py`                     | Defines Flask Blueprint with sensor endpoints (`GET /api/sensors`, `GET /api/sensors/count`, `POST /api/sensors`, `POST /api/sensors/batch`). Receives HTTP requests and queries/inserts directly into the DB. |
| `components/backend-api/app/routers/prediction.py`                 | Defines Flask Blueprint with prediction endpoints (`POST /api/predict`, `GET /api/predictions`). Calls the ML service, persists results via `prediction_service.py`, and passes ML errors (e.g. 503 not trained) through to the caller. |
| `components/backend-api/app/models/sensor.py`                      | SQLAlchemy model defining the `sensor_readings` table schema (`SensorReading`). Used by database.py and imported by routes to query/insert data. |
| `components/backend-api/app/models/prediction.py`                  | SQLAlchemy model defining the `predictions` table schema (`Prediction`). Stores ML anomaly results so they survive ML restarts and are queryable by the dashboard. |
| `components/backend-api/app/schemas/sensor.py`                     | Request/response schemas for validating JSON payloads and serialising responses. (TBD) |
| `components/backend-api/app/services/sensor_service.py`            | Business logic for sensor data. May use PySpark for data transformations and aggregations. (TBD) |
| `components/backend-api/app/services/ml_client.py`                 | HTTP client that sends readings to the ML microservice (`/api/predict`, `/api/predict/batch`) and returns the prediction results. |
| `components/backend-api/app/services/notification_client.py`       | HTTP client that POSTs anomalous readings to the Notification microservice (`/api/notify`). Best-effort: never raises, so an unavailable notification service cannot break prediction storage. |
| `components/backend-api/app/services/prediction_service.py`        | Persists a prediction result into the `predictions` table (`store_prediction`) and serialises rows for API responses (`prediction_to_json`). When a stored prediction is an anomaly, it triggers the Notification Service (best-effort). |
| `components/backend-api/Dockerfile`                                | Tells Docker how to build the backend container — installs dependencies, copies code, runs the app. |
| `components/backend-api/requirements.txt`                          | Lists all Python packages the project needs (Flask, SQLAlchemy, etc.). |
| `components/ml-service/app/main.py`                                | Flask app entry point for ML Service. Trains the IsolationForest model at startup when the cleaned dataset exists, otherwise starts idle and reports `model_ready: false`; registers the prediction blueprint. |
| `components/ml-service/app/config.py`                              | Stores dataset path, IsolationForest hyperparameters, and alert thresholds. All values overridable via environment variables (e.g. `DATASET_PATH`). |
| `components/ml-service/app/routers/prediction.py`                  | Defines Flask Blueprint with prediction endpoints (`POST /api/predict`, `POST /api/predict/batch`). Retries lazy training on demand and returns 503 with an actionable message when no dataset is available yet. |
| `components/ml-service/app/services/model_service.py`              | Contains the scikit-learn **IsolationForest** anomaly-detection logic: `load_dataset()` reads the cleaned CSV, `train_model()` fits the forest, `check_thresholds()` flags readings, and `predict()` returns anomaly score, severity, and alerts. |
| `components/ml-service/Dockerfile`                                 | Container definition for ML Service. |
| `components/ml-service/requirements.txt`                           | Python dependencies for ML Service (Flask + ML framework TBD). |
| `components/notification-service/app/main.py`                      | Single-file Flask app for the Notification Service. Accepts readings via `POST /api/notify`: when the payload includes the ML model's `alerts` list it sends those verbatim, otherwise it derives them from the 3 env-configurable thresholds (`TEMP_THRESHOLD` 39, `HUMIDITY_THRESHOLD` 55, `AQ_THRESHOLD` 2). Sends Telegram alerts via the Telegram Bot API using `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` env vars, and keeps the 50 most recent alerts in memory for the dashboard (`GET /api/alerts`). |
| `components/notification-service/Dockerfile`                       | Container definition for Notification Service. |
| `components/notification-service/requirements.txt`                 | Python dependencies for Notification Service (Flask, requests). |
| `components/data-ingestion-service/app/main.py`                    | Flask app entry point for Data Ingestion Service. Registers ingestion blueprints. |
| `components/data-ingestion-service/app/config.py`                  | Stores Backend API URL, `DATA_DIR`, and allowed file formats loaded from environment variables. |
| `components/data-ingestion-service/app/routers/ingestion.py`       | Defines Flask Blueprint with data intake endpoints (`POST /api/ingest/file`). Accepts CSV/JSON sensor data. |
| `components/data-ingestion-service/app/services/data_ingestion.py` | Parses raw CSV sensor data (drop columns, rename, coerce types, drop NaN), saves cleaned output to `sensor_data_cleaned.csv`, and forwards records to the Backend API. Also runnable standalone (`python -m app.services.data_ingestion`). |
| `components/data-ingestion-service/Dockerfile`                     | Container definition for Data Ingestion Service. |
| `components/data-ingestion-service/requirements.txt`               | Python dependencies for Data Ingestion Service (Flask, requests, pandas). |
| `components/database/init.sql`                                     | SQL script that runs when PostgreSQL starts. Creates tables. |
| `components/database/Dockerfile`                                   | Builds the `dataset-seed` image used by a Kubernetes init container to copy `sensor_data.example.csv` into the shared dataset PVC. Build with `docker build -t dataset-seed:latest components/database`. |
| `components/database/sensor_data.example.csv`                      | Raw sensor data (ground truth) used by the ingestion pipeline. |
| `components/frontend/html/dashboard.html`                          | Dashboard page markup. |
| `components/frontend/css/styles.css`                               | Dashboard styling. |
| `components/frontend/js/dashboard.js`                              | Dashboard logic. Polls the Backend API for sensor readings and predictions (coloring anomalous points red) and the Notification Service's `GET /api/alerts` for the alert panel, renders charts with Chart.js. |
| `components/sensor/sensor_simulator.py`                            | Simulates an IoT sensor by replaying `sensor_data.csv` row by row and posting each reading to the Data Ingestion Service via REST, one record every few seconds. |
| `components/sensor/Dockerfile`                                     | Container definition for the Sensor Simulator. No exposed port — it only makes outgoing requests. |
| `components/sensor/requirements.txt`                               | Python dependencies for the Sensor Simulator (pandas, requests). |
| `k8s/*.yaml`                                                          | Kubernetes deployment manifests. Define how each microservice is deployed, exposed, and configured in a cluster. `k8s/database/pvc.yaml` declares the shared dataset volume both ingestion and ML mount. |

### Key Concept: Blueprints

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

## Technology Decisions

| Component        | Technology             | Justification                                                     |
|------------------|------------------------|-------------------------------------------------------------------|
| Backend API      | Flask + PySpark        | Flask for lightweight HTTP; PySpark for large-scale               |
|                  |                        | sensor data processing (Spark session TBD).                       |
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

## Key Development Decisions

### Data Pipeline
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

### Notifications
- **Backend triggers on ML anomalies** — The notification service is only
  called by the Backend API when the ML model flags a reading as anomalous
  (`store_prediction`). One notification per anomalous reading — rare events
  in an early-warning system must not be delayed or coalesced away
- **Two onboarding paths** — First-time users self-provision a bot via
  BotFather (token + chat id into `.env` / Secret). Teams can instead reuse
  one bot in a shared Telegram group: the owner adds the bot to the group and
  groupmates simply join, with credentials staying in the shared deployment
  config. The `/` health endpoint exposes `telegram_configured` so a new user
  can confirm their setup
- **ML alert messages win** — The backend passes the ML model's `alerts` list
  with the reading, so Telegram text always matches what the model flagged.
  Direct callers (e.g. the dashboard) may omit it and the notification service
  derives messages from its own thresholds
- **Defaults in code, overrides in config** — Each threshold is read as
  `os.environ.get("<NAME>", "<default>")`, so the service works standalone
  with the built-in values (39 / 55 / 2). The compose file and k8s ConfigMap
  set the same numbers explicitly to override per deployment, keeping
  behaviour identical whether or not environment variables are set
- **Thresholds are config, credentials are secrets** — `TEMP_THRESHOLD`,
  `HUMIDITY_THRESHOLD`, `AQ_THRESHOLD` live in the compose file / k8s
  ConfigMap. `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are injected from a
  local `.env` for compose (git-ignored) or a k8s `Secret`
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

### Local Development vs Docker
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

### Docker & Deployment
- **`depends_on` for startup order** — Database → Backend API → Ingestion
  service ensures services connect in the right sequence
- **Shared dataset volume** — `./components/database` is bind-mounted as
  `/data` into both ingestion and ML containers, so the raw file, the cleaned
  output, and the trained model inputs all stay in one place
- **Kubernetes dataset storage** — The same shared folder is represented in
  k8s by the `dataset-pvc` (see `k8s/database/pvc.yaml`). Both deployments
  mount it at `/data`; the ingestion pod seeds the raw example file into it
  via the `dataset-seed` init container. Apply order:
  `kubectl apply -f k8s/database/pvc.yaml` first, then the service manifests

---

## Development Style & Conventions

How new code in this project should look, structured, and committed. These
conventions come from the patterns already in the codebase; when in doubt,
match the neighbouring service.

### Service Structure
- **Backend-style services** (backend-api, ml-service, data-ingestion) use the
  `app/` split: `main.py` (a `create_app()` factory), `config.py`,
  `routers/` (Flask blueprints), `services/` (business logic and HTTP
  clients), and — for the backend — `models/` (SQLAlchemy) and `database.py`.
- **Small single-purpose services** stay single-file: the notification service
  defines its routes, threshold logic, and Telegram sending all in
  `app/main.py`.
- **Blueprints** are named `name_bp = Blueprint("name", __name__)` and
  registered in `main.py` with `url_prefix="/api"`.

### Python Code Style
- 4-space indentation, `snake_case` names, `"""docstrings"""` for modules and
  public functions.
- One idea per function; keep functions small and single-purpose. Prefer plain
  functions over classes for service logic unless state is genuinely needed.

### Configuration & Secrets
- Every service reads configuration through
  `os.environ.get("KEY", "default")` (a `Config` class or module constants).
- **Secrets** (bot tokens, credentials) use empty-string defaults and are
  injected per environment — `.env` for Compose, a k8s `Secret`, or shell
  environment variables. Never hardcode a secret in code.
- **Non-secret config** (thresholds, paths, URLs) carries a real default in
  code, and the same value is set explicitly in `docker-compose.yml` / the k8s
  ConfigMap so behaviour is identical whether or not the variable is set.
- Never commit credentials, keys, or generated artifacts (the cleaned dataset
  is git-ignored for this reason).

### Service Entry Points
- Flask services expose `create_app()` and start via
  `if __name__ == "__main__": app.run(host="0.0.0.0", port=NNNN)`.
- Browser-facing services enable CORS with an `@app.after_request` handler.
- Ports are fixed per service; see the Port Assignments table.

### API Responses & Error Handling
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

### Frontend (Vanilla JS) & CSS
- Plain JavaScript with **Chart.js** for charts — no framework, no build
  step, no bundler. Files live under `html/`, `css/`, and `js/`.
- A `CONFIG` object at the top of the script holds every tunable (base URLs,
  poll interval, thresholds, labels).
- Cache DOM element references once at the top of the script; drive styling
  from `data-*` attributes (`#note[data-state]`) rather than toggling classes.
- Access the API through small helpers (e.g. `fetchJSON`), `async/await`, and
  a `try/catch` per fetch so a downed dependency shows an "Offline" status
  instead of breaking the page.
- Polling pattern: a `refresh()` function run once on load and then on a
  timer (`setInterval`).
- Plain CSS with id-based selectors for unique components and a small media
  query for narrow screens; state styling via `[data-state=...]` selectors.

### Git Commits
- Summary line: lowercase, imperative ("add", "fix", "refactor", "document",
  "wire").
- A short body describing what changed and why, ending with a `Why:`
  paragraph when the rationale isn't obvious from the change itself.
- One logical change per commit (service code, deployment config, and docs are
  committed separately).
- Feature changes also update the relevant docs (Architecture.md tree and
  decisions, per-service READMEs) in the same commit or an accompanying docs
  commit.

### Standalone Scripts & Verification
- Build services as **importable modules first, standalone scripts second**:
  `if __name__ == "__main__"` blocks call the same functions the routes use.
- There is no committed test framework. Verify by running services
  standalone, exercising endpoints with the Flask test client / `curl`, and
  running import checks.

### Deployment Hygiene
- One Dockerfile per service; `docker-compose.yml` at the repo root; one
  `k8s/` manifest folder per service.
- Environment: `.env` (local), ConfigMap (non-secret), Secret (credentials).
- Keep generated data and build outputs out of the repository.

### Database Schema Changes
- There is no migrations framework. To change a table, update the SQLAlchemy
  model (`app/models/`) **and** `components/database/init.sql` together.
- `Base.metadata.create_all` only creates missing tables — it does **not**
  alter existing ones. For a development database, recreate it or apply the
  change manually.

### Adding a New Microservice
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

## Microservice Communication

| From             | To                   | Protocol  | Purpose                                                            |
|------------------|----------------------|-----------|--------------------------------------------------------------------|
| Sensor Simulator | Data Ingestion       | REST/HTTP | Replay one sensor reading at a time                                |
| Frontend         | Backend API          | REST/HTTP | User requests, data display                                        |
| Frontend         | Notification Service | REST/HTTP | Reads recent alerts for the alert panel (`GET /api/alerts`)        |
| Data Ingestion   | Backend API          | REST/HTTP | Send sensor data for processing                                    |
| Backend API      | PostgreSQL           | SQL       | Data persistence & retrieval                                       |
| Backend API      | ML Service           | REST/HTTP | Anomaly prediction requests (`/api/predict`, `/api/predict/batch`) |
| ML Service       | Backend API          | REST/HTTP | Prediction results returned (score, severity, alerts)              |
| Backend API      | Notification Service | REST/HTTP | Triggers `/api/notify` on ML-flagged anomalies                     |

---

## Port Assignments

| Service                | Port | Notes                                            |
|------------------------|------|--------------------------------------------------|
| Backend API            | 5000 | Flask default, central API layer                 |
| ML Service             | 5001 | Anomaly detection (lazy-trained IsolationForest) |
| Notification Service   | 5002 | Alert processing (Telegram)                      |
| Data Ingestion Service | 5003 | CSV/JSON sensor data intake                      |
| PostgreSQL             | 5432 | Database                                         |
| Frontend               | 3000 | Dashboard UI (served statically)                 |
| Sensor Simulator       | —    | No inbound port (outgoing requests only)         |

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

## Open Decisions (Pending Team Discussion)

The following items have **not yet been finalised** and are subject to change:

1. **PySpark Usage Scope** — How Spark will be used in the backend is
   undecided. Options include batch aggregation, preprocessing for ML, or
   running Spark MLlib models directly. `spark_session.py` is currently a stub.

2. **Sensor Data Input Format** — The primary flow is now the Sensor
   Simulator replaying the CSV dataset as JSON API payloads. CSV uploads and
   IoT streaming remain possible future inputs.
   I chose wk2 dataset because it shows the exact same inferential conclusion as wk 3 dataset and it is not as heavily loaded compared to wk 3 dataset.

3. **Frontend Serving** — The dashboard is built (static HTML/CSS/JS), but
   how it is served and containerised is still open.

4. **Live Sensor → Ingestion link** — The sensor simulator posts to
   `/api/ingest/reading`, but ingestion currently only exposes
   `/api/ingest/file`. Wiring the simulator to register readings live (and
   accumulate them into the dataset) is future work; today data is registered
   by posting the raw file once.

---
