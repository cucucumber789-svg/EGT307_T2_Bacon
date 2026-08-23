# EGT307_T2_BACON

## Task assignment

| Name     | Task                                                                                                                                        | Microservice                           |
|----------|---------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| Wei Guan | Notification Service, Frontend Dashboard, Sensor Simulator, Presentation, Data Sources                                                      | sensor simulator, notification-service |
| Shun Wei | Backend API, System Integration, Docker & Kubernetes, System Architecture, Code Quality & Documentation, Centralised Config, ML Integration | backend-api                            |
| Derek    | Data Ingestion Service, Database Setup, Machine Learning Service                                                                            | data-ingestion, ml-service             |

## Project overview

The Smart Environmental Monitoring System monitors environmental conditions
such as temperature, humidity, and air quality. Sensor data is collected and
processed before being analysed by the Machine Learning Service to detect
abnormal conditions. The system uses a microservices architecture with a
dashboard for monitoring and a Notification Service that sends alerts through
Telegram when abnormal readings are detected. This helps users identify
potential environmental hazards quickly and respond when needed.

## Problem statement

Many environmental monitoring systems only display sensor readings without
providing intelligent analysis or early detection of abnormal conditions.
This requires users to manually monitor large amounts of data, which is
time-consuming and may lead to delayed responses.

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

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full system architecture,
repository structure, technology decisions, and data flow workflows.

## Setup & running

### Prerequisites

- Python 3.11+ (only needed to run the services standalone; not needed if you
  use Docker only)
- Docker with Docker Compose (for the full stack)
- `kubectl` and a cluster (only for the Kubernetes option)

No Node.js is required — the frontend is plain static files served by nginx.

### Option A — full stack with Docker Compose

#### 1. Environment setup (one time)

Copy the example environment file and fill in your values:

```bash
cp .env.example .env   # then edit with your secrets
```

`config.yaml` (committed) holds non-sensitive tuning values — thresholds,
ML hyperparameters, simulator intervals — and is baked into each image at
build time.

#### 2. Build and start

```bash
docker-compose up --build
```

The `env-validator` service runs automatically and blocks startup until all
values are valid. Without Telegram credentials the Notification Service
still runs and records alerts, but prints `Telegram not configured, skipping
send` instead of messaging anyone.

Once all services are running, open the dashboard:
http://localhost:3000/html/dashboard.html

#### 3. Register the dataset (one time)

The sensor simulator is already running, but the ML model cannot train until
the cleaned dataset exists. Register it once:

**Bash:**
```bash
curl -X POST http://localhost:5003/api/ingest/file
```

**PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:5003/api/ingest/file -Method Post
```

#### Optional — verify the pipeline

**Bash:**
```bash
# Confirm readings are stored
curl http://localhost:5000/api/sensors?limit=5

# Check the config thresholds (should match config.yaml)
curl http://localhost:5000/api/config
```

**PowerShell:**
```powershell
# Confirm readings are stored
Invoke-RestMethod -Uri "http://localhost:5000/api/sensors?limit=5"

# Check the config thresholds (should match config.yaml)
Invoke-RestMethod -Uri http://localhost:5000/api/config
```

#### 4. Stop

```bash
docker-compose down
```

| Service                | Host port | URL / connection                     |
|------------------------|-----------|--------------------------------------|
| Frontend Dashboard     | 3000      | http://localhost:3000                |
| Backend API            | 5000      | http://localhost:5000/api            |
| ML Service             | 5001      | http://localhost:5001                |
| Notification Service   | 5002      | http://localhost:5002                |
| Data Ingestion Service | 5003      | http://localhost:5003                |
| Database (PostgreSQL)  | 5432      | `postgresql://user:password@localhost:5432/env_monitor` |

### Option B — Kubernetes

#### 1. Start a local cluster (one time)

```bash
minikube start
```

#### 2. Build images inside minikube

Minikube has its own Docker daemon — images built with your local Docker are
not visible to minikube. Point your shell to minikube's Docker, build all
images, then point back:

```bash
& minikube docker-env --shell powershell | Invoke-Expression
docker build -t backend-api:latest -f components/backend-api/Dockerfile .
docker build -t ml-service:latest -f components/ml-service/Dockerfile .
docker build -t notification-service:latest -f components/notification-service/Dockerfile .
docker build -t data-ingestion-service:latest -f components/data-ingestion-service/Dockerfile .
docker build -t sensor-simulator:latest -f components/sensor/Dockerfile .
docker build -t frontend:latest -f components/frontend/Dockerfile components/frontend
docker build -t dataset-seed:latest -f components/database/Dockerfile components/database
```

#### 3. Create secrets (one time)

Telegram is optional — without it the Notification Service still runs and
records alerts, but prints `Telegram not configured, skipping send` in logs
instead of messaging anyone. The dashboard alert panel still works.

Fill in the postgres secret (`k8s/database/postgres-secret.yaml`) with your
values, then apply:

```bash
kubectl create secret generic telegram-credentials --from-literal=TELEGRAM_BOT_TOKEN=<token> --from-literal=TELEGRAM_CHAT_ID=<chat-id>
kubectl apply -f k8s/database/postgres-secret.yaml
```

#### 4. Apply manifests

The database PVC must exist first because every service that mounts the
shared dataset volume depends on it:

```bash
kubectl apply -f k8s/database/pvc.yaml -f k8s/database/postgres-configmap.yaml -f k8s/database/postgres-service.yaml -f k8s/database/postgres-deployment.yaml
kubectl apply -f k8s/backend-api -f k8s/ml-service -f k8s/notification-service -f k8s/data-ingestion-service -f k8s/sensor-simulator -f k8s/frontend
```

#### 5. Register the dataset (one time)

```powershell
kubectl exec -n default deployment/data-ingestion-service -- python -c "import requests; r = requests.post('http://localhost:5003/api/ingest/file'); print(r.status_code, r.text)"
```

#### 6. Open the dashboard

```powershell
minikube service frontend --url
```

### Option C — run each service standalone

See [`DEVELOPMENT.md`](./DEVELOPMENT.md) for standalone run instructions,
per-service setup, and the service quick-reference table.

## Documentation

| Document | What it covers |
|----------|---------------|
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | System design, repository structure, technology decisions, data flow workflows, and key architectural decisions |
| [`DEVELOPMENT.md`](./DEVELOPMENT.md) | Coding conventions, project structure patterns, configuration & secrets, API error handling, frontend patterns, standalone mode, and adding new microservices |
| [`components/notification-service/README.md`](./components/notification-service/README.md) | Notification Service setup, Telegram configuration, and troubleshooting |
| [`components/frontend/README.md`](./components/frontend/README.md) | Frontend Dashboard details and nginx proxy setup |

## Issues and limitations

- Limited Dataset and Simulation: The system uses a limited, static CSV dataset to simulate IoT sensors, so it may not fully represent real-world sensor behaviour or how the ML model performs on new data.

- Alert Threshold: The notification threshold buffer (`anomaly_score_threshold` in `config.yaml`) is a design choice — tuning it controls the tradeoff between alert sensitivity and noise. Too low and mild anomalies trigger Telegram; too high and genuine anomalies are missed.
