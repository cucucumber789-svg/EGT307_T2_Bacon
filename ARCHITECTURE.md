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
│   (Flask)          │◄──────►                     │
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
├── ARCHITECTURE.md              # System architecture & design docs
│
├── scripts/                       # Validation & utility scripts
│   ├── validate-env.sh            # Shell env validation (used by Docker)
│   └── validate-env.py            # Python env validation (standalone mode)
│
├── components/                 # All services live under this folder
│   ├── env-validator/             # ENV VALIDATOR — pre-flight env check container
│   │   └── Dockerfile
│   ├── backend-api/               # BACKEND API — Flask
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py            # Flask app entry point (create_app)
│   │   │   ├── config.py          # Environment-based configuration
│   │   │   ├── database.py        # SQLAlchemy engine + session
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
    └── frontend/
        ├── deployment.yaml
        ├── service.yaml            # NodePort 30080 → 80 → 3000
        └── configmap.yaml          # nginx proxy targets
```

---

## Technology decisions

| Component        | Technology             | Justification                                                     |
|------------------|------------------------|-------------------------------------------------------------------|
| Backend API      | Flask                  | Flask for lightweight HTTP; all CRUD via SQLAlchemy + PostgreSQL.  |
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
- **Isolation Forest** — Unsupervised anomaly detection: anomalies are few
  and different from normal points. 200 decision trees isolate anomalies in
  fewer splits (shorter path length). Chosen because the dataset has no
  labeled anomalies for supervised training
- **Contamination** — Sets the expected fraction of anomalies in training
  data (default 2%). Controls where the model draws its decision boundary
  (`score = 0`). Higher = more sensitive, lower = more conservative
- **Two-tier filtering** — Model flags anomalies at `score < 0`; notification
  only fires at `score < -threshold` (default 0.05). Mild anomalies are
  visible on the dashboard but do not trigger Telegram
- **Severity sigmoid** — Maps anomaly score to 0–1 for the dashboard bar:
  `severity = 1 / (1 + exp(steepness * score))`. Score `0.0` (boundary) →
  `0.50` (50% bar); score `-0.05` (notification threshold) → `0.62` (62% bar).
  Steepness configurable in `config.yaml`
- **Safety-net** — Hardcoded `ABSOLUTE_MAX_TEMP = 50°C` pins severity to 1.0
  for physically dangerous values

### Notifications
- **Backend triggers on ML anomalies** — Notification service is called only
  when the model flags a reading. One notification per anomalous reading —
  rare events in an early-warning system must not be delayed or coalesced
- **ML model is the single source of truth** — Alerting decisions driven
  entirely by IsolationForest score. Notification service is a pure sender
- **Two-tier filtering reduces alert fatigue** — `score < 0` = anomaly;
  `score < -threshold` = Telegram notification. Tunable in `config.yaml`
- **Dashboard only reads alerts** — `GET /api/alerts` drives the alert panel;
  the dashboard never POSTs `/api/notify`, so polling cannot spam Telegram
- **Credentials are secrets** — Bot token and chat ID in `.env` (Compose) or
  k8s Secret. Health endpoint exposes `telegram_configured` for verification

### Database
- **`init.sql` creates table only, no seeding** — Ingestion service handles data
  flow; DB schema stays clean and independent of data volume
- **SQLAlchemy ORM** — Decouples app logic from raw SQL; models serve as single
  source of truth for table schema

### Technology choices
- **Why PySpark was not used** — PySpark was considered for the Backend API
  but not adopted. The dataset is 51K rows (2.5 MB), and the backend performs
  only simple OLTP operations: `ORDER BY ... LIMIT 100`, `COUNT(*)`, and
  single-row INSERTs. PostgreSQL handles this workload natively. Spark's JVM
  startup overhead alone would exceed all actual compute done by the service.
  The stub files (`spark_session.py`, `sensor_service.py`) have been removed.

---

## Development conventions

For coding conventions, service structure patterns, configuration & secrets
management, API error handling, frontend patterns, database schema changes,
deployment hygiene, and adding new microservices, see
[`DEVELOPMENT.md`](./DEVELOPMENT.md).

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
- `config.yaml` baked into images — repo root is the build context; each
  Dockerfile copies both its source and `config.yaml`. Changing a threshold
  requires `docker-compose up --build`
- **`depends_on` for startup order** — Database → Backend API → Ingestion
- **Shared dataset volume** — `./components/database` bind-mounted as `/data`
  into ingestion and ML containers
- **Log suppression** — Flask services set `werkzeug` to WARNING; nginx uses
  `access_log off;`. Only errors and startup notices appear in logs

### Kubernetes
- Separate YAML manifests per service under `k8s/`
- ConfigMaps for environment configuration, Secrets for credentials
- Services for internal DNS-based communication
- **Dataset PVC** — `k8s/database/pvc.yaml` declares the shared volume.
  Apply PVC first, then service manifests
- **Startup ordering** — ML Service returns 503 until `POST /api/ingest/file`
  is called. This is by design (loose coupling), not an error

---

## Data flow

```
Sensor Simulator
  │  POST /api/ingest/reading
  ▼
Data Ingestion Service
  │  validates → POST /api/sensors → Backend API → PostgreSQL
  ▼
Backend API
  │  POST /api/predict → ML Service (anomaly scoring)
  │  stores prediction in PostgreSQL
  │  if score < -threshold:
  │    POST /api/notify → Notification Service → Telegram
  ▼
Frontend Dashboard (polls every 8s)
  │  GET /api/sensors       → charts + latest values
  │  GET /api/predictions   → anomalous points coloured red
  │  GET /api/alerts        → notification panel
  │  GET /api/config        → threshold displays in sync
```

A single sensor reading flows through validation, storage, ML analysis,
optional alerting, and dashboard display — all without manual intervention.
Threshold tuning is a config-file change (`config.yaml`), not a code change.

---
