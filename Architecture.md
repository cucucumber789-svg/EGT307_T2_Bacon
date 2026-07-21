# Architecture — Smart Environmental Monitoring System

## Overview

This document outlines the overall system architecture, repository structure,
technology decisions, and deployment strategy for the Smart Environmental
Monitoring System. The system uses a **microservices architecture** orchestrated
by **Docker** and **Kubernetes**.

---

## System Architecture (High-Level)

```
┌─────────────────────┐
│  Frontend Dashboard │
│   (TBD)             │
└────────┬────────────┘
         │ REST API
         ▼
┌─────────────────────┐        ┌─────────────────────┐
│   Backend API       │◄──────►│   ML Service        │
│   (Flask + PySpark) │        │   (TBD)             │
└────────┬────────────┘        └─────────────────────┘
         │
    ┌────┴────────────────────┐
    ▼                         ▼
┌──────────────────┐   ┌──────────────────┐
│Data Ingestion    │   │ Notification     │
│   Service        │   │   Service        │
│(CSV/JSON intake) │   │ (email/SMS)      │
└──────────────────┘   └──────────────────┘
         │                         ▲
         ▼                         │
┌──────────────────┐               │
│  PostgreSQL DB   │◄──────────────┘
└──────────────────┘
```

All components are containerised with Docker and deployed via Kubernetes.

---

## Repository File Structure

```
EGT307_T2_Bacon/
├── README.md
├── Architecture.md
├── docker-compose.yml
│
├── backend-api/                  # BACKEND API — Flask + PySpark
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Flask app entry point
│   │   ├── config.py            # Environment-based configuration
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── spark_session.py     # Spark session initialisation
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── sensor.py        # Sensor data model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── sensor.py        # Request/response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── sensor.py        # Sensor CRUD routes
│   │   │   └── prediction.py    # Prediction routes
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── sensor_service.py  # Sensor business logic
│   │       └── ml_client.py       # ML service HTTP client
│   ├── tests/
│   │   └── __init__.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── ml-service/                   # ML SERVICE — TBD
│
├── notification-service/         # NOTIFICATION SERVICE — alerts (email/SMS)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Flask app entry point
│   │   ├── config.py            # SMTP and alert configuration
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── notification.py  # Alert endpoints
│   │   └── services/
│   │       ├── __init__.py
│   │       └── alert_service.py # Email/SMS sending logic
│   ├── Dockerfile
│   └── requirements.txt
│
├── data-ingestion-service/       # DATA INGESTION SERVICE — sensor data intake
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Flask app entry point
│   │   ├── config.py            # Backend API URL configuration
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── ingestion.py     # Data intake endpoints
│   │   └── services/
│   │       ├── __init__.py
│   │       └── data_loader.py   # CSV/JSON parsing logic
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                     # FRONTEND — TBD
│
├── database/                     # DATABASE — PostgreSQL init
│   └── init.sql
│
└── k8s/                          # KUBERNETES — deployment manifests
    ├── backend-api/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── ml-service/
    ├── notification-service/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── data-ingestion-service/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── database/
    └── frontend/
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
from app.models.sensor import Sensor

# With __init__.py — this works:
from app.models.sensor import Sensor
```

The file can be **empty** (just acts as a marker) or used to expose commonly
imported items for convenience.

### How the Files Connect

```
main.py  (entry point — starts the app)
  ├── imports config.py          (reads environment variables)
  ├── imports database.py        (connects to PostgreSQL)
  ├── imports spark_session.py   (creates Spark session)
  ├── registers routers/sensor.py      (adds /api/sensors routes)
  └── registers routers/prediction.py  (adds /api/predict routes)

routers/sensor.py  (handles HTTP requests)
  ├── imports models/sensor.py   (to read/write sensor data in DB)
  ├── imports schemas/sensor.py  (to validate incoming JSON)
  └── imports services/sensor_service.py (to process data)

routers/prediction.py  (handles prediction requests)
  ├── imports services/ml_client.py (to call ML microservice)
  └── imports services/sensor_service.py (to fetch sensor data)
```

### File-by-File Explanation

| File | Purpose |
|------|---------|
| `main.py` | Flask app entry point. Creates the app, registers blueprints (routers), and starts the server. This is the first file that runs. |
| `config.py` | Stores all configuration (database URL, ML service URL, etc.) loaded from environment variables. Keeps secrets out of code. |
| `database.py` | Creates the SQLAlchemy engine and session. Other files import `SessionLocal` to query or insert data into PostgreSQL. |
| `spark_session.py` | Creates and returns a PySpark `SparkSession`. Services import this to run Spark data processing operations. |
| `routers/sensor.py` | Defines Flask Blueprint with sensor endpoints (`GET /api/sensors`, `POST /api/sensors`). Receives HTTP requests and delegates logic to services. |
| `routers/prediction.py` | Defines Flask Blueprint with prediction endpoints (`POST /api/predict`). Calls ML service and returns anomaly results. |
| `models/sensor.py` | SQLAlchemy model defining the `sensors` table schema. Used by database.py and imported by routes to query/insert data. |
| `schemas/sensor.py` | Pydantic schemas for validating request bodies and formatting responses. Ensures API input/output is consistent. |
| `services/sensor_service.py` | Business logic for sensor data. May use PySpark for data transformations and aggregations. |
| `services/ml_client.py` | HTTP client that sends data to the ML microservice and receives prediction results back. |
| `Dockerfile` | Tells Docker how to build the backend container — installs dependencies, copies code, runs the app. |
| `requirements.txt` | Lists all Python packages the project needs (Flask, SQLAlchemy, PySpark, etc.). |
| `docker-compose.yml` | Defines all services (backend, database) and how they run together locally. One command starts everything. |
| `database/init.sql` | SQL script that runs when PostgreSQL starts. Creates tables and seeds initial data. |
| `k8s/*.yaml` | Kubernetes deployment manifests. Define how each microservice is deployed, exposed, and configured in a cluster. |
| `notification-service/app/main.py` | Flask app entry point for Notification Service. Registers alert blueprints. |
| `notification-service/app/config.py` | Stores SMTP email settings and alert configuration loaded from environment variables. |
| `notification-service/app/routers/notification.py` | Defines Flask Blueprint with alert endpoints (`POST /api/notify`). Called by Backend API when anomalies detected. |
| `notification-service/app/services/alert_service.py` | Handles sending email/SMS alerts. Includes retry logic for failed sends. |
| `notification-service/Dockerfile` | Container definition for Notification Service. |
| `notification-service/requirements.txt` | Python dependencies for Notification Service (Flask, requests). |
| `data-ingestion-service/app/main.py` | Flask app entry point for Data Ingestion Service. Registers ingestion blueprints. |
| `data-ingestion-service/app/config.py` | Stores Backend API URL and allowed file formats loaded from environment variables. |
| `data-ingestion-service/app/routers/ingestion.py` | Defines Flask Blueprint with data intake endpoints (`POST /api/ingest`). Accepts CSV/JSON sensor data. |
| `data-ingestion-service/app/services/data_loader.py` | Handles parsing CSV files and JSON payloads into structured records before forwarding to Backend API. |
| `data-ingestion-service/Dockerfile` | Container definition for Data Ingestion Service. |
| `data-ingestion-service/requirements.txt` | Python dependencies for Data Ingestion Service (Flask, requests, pandas). |

### Key Concept: Blueprints

Blueprints are the routing system used in `routers/`. Each file inside
`routers/` defines a Flask **Blueprint** — a group of related API endpoints.

- `routers/sensor.py` → Defines `sensor_bp` with sensor routes
- `routers/prediction.py` → Defines `prediction_bp` with prediction routes

These blueprints are then **registered** onto the Flask app in `main.py`:

```python
# main.py — imports and registers blueprints
from app.routers.sensor import sensor_bp
from app.routers.prediction import prediction_bp

app.register_blueprint(sensor_bp)
app.register_blueprint(prediction_bp)
```

This keeps routes organised by feature instead of having everything in one file.

---

## Technology Decisions

| Component        | Technology      | Justification                                            |
|------------------|-----------------|----------------------------------------------------------|
| Backend API      | Flask + PySpark | Flask for lightweight HTTP; PySpark for large-scale      |
|                  |                 | sensor data processing.                                  |
| Database         | PostgreSQL      | Strong relational support for structured sensor data;    |
|                  |                 | ACID compliance; mature tooling.                         |
| ORM              | SQLAlchemy      | Standard Python ORM; decouples app logic from SQL.       |
| Containerisation | Docker          | Consistent runtime across environments; single-command   |
|                  |                 | startup via docker-compose.                              |
| Orchestration    | Kubernetes      | Automated deployment, scaling, self-healing, and load    |
|                  |                 | balancing across microservices.                          |
| Frontend         | (TBD)           | To be decided by the frontend team member.               |
| ML Service       | (TBD)           | To be co-developed; framework and model approach pending. |

---

## Microservice Communication

| From                | To                | Protocol  | Purpose                          |
|---------------------|-------------------|-----------|----------------------------------|
| Frontend            | Backend API       | REST/HTTP | User requests, data display      |
| Data Ingestion      | Backend API       | REST/HTTP | Send sensor data for processing  |
| Backend API         | PostgreSQL        | SQL       | Data persistence & retrieval     |
| Backend API         | ML Service        | REST/HTTP | Anomaly prediction requests      |
| ML Service          | Backend API       | REST/HTTP | Prediction results returned      |
| Backend API         | Notification Service | REST/HTTP | Trigger alerts on anomalies   |

---

## Port Assignments

| Service                | Port | Notes                              |
|------------------------|------|------------------------------------|
| Backend API            | 5000 | Flask default, central API layer   |
| ML Service             | 5001 | Anomaly detection (TBD)            |
| Notification Service   | 5002 | Alert processing (email/SMS)       |
| Data Ingestion Service | 5003 | CSV/JSON sensor data intake        |
| PostgreSQL             | 5432 | Database                           |
| Frontend               | 3000 | Dashboard UI (TBD)                 |

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

---

## Open Decisions (Pending Team Discussion)

The following items have **not yet been finalised** and are subject to change:

1. **PySpark Usage Scope** — How Spark will be used in the backend is
   undecided. Options include batch aggregation, preprocessing for ML, or
   running Spark MLlib models directly.

2. **Sensor Data Input Format** — The format in which sensor data arrives
   (CSV uploads, JSON API payloads, or IoT streaming) has not been determined.

3. **ML Service API Contract** — The interface between Backend API and ML
   Service needs to be defined collaboratively before integration.

4. **ML Service Technology Stack** — The ML microservice's framework, model
   format, and serving approach are yet to be decided.

5. **Frontend Framework** — The frontend dashboard framework is pending team decision.

---
