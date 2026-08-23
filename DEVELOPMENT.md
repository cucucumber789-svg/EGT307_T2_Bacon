# Contributing Guide

Development conventions and how-to guides for the Smart Environmental Monitoring System.

---

## Python basics

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

### Blueprints

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

## Frontend conventions (vanilla JS & CSS)

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
  the bar identifying each line: "model boundary (anomaly)" and
  "notification trigger (alert)". Below a divider, static rows show
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

---

## Git commits

- Summary line: lowercase, imperative ("add", "fix", "refactor", "document",
  "wire").
- A short body describing what changed and why, ending with a `Why:`
  paragraph when the rationale isn't obvious from the change itself.
- One logical change per commit (service code, deployment config, and docs are
  committed separately).
- Feature changes also update the relevant docs (ARCHITECTURE.md tree and
  decisions, per-service READMEs) in the same commit or an accompanying docs
  commit.

---

## Standalone mode

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

## Adding a new microservice

1. Create `components/<name>/` with the `app/` split (or a single-file app
   for small services) plus a `requirements.txt`.
2. Add a `Dockerfile`: `python:3.11-slim`, `WORKDIR /app`, install
   `requirements.txt`, `EXPOSE <port>`, `CMD ["python", "app/main.py"]`.
3. Register it in `docker-compose.yml` (`build`, `ports`, `environment`,
   `depends_on`).
4. Add `k8s/<name>/`: `deployment.yaml` (image `<name>:latest`, `envFrom`
   referencing the ConfigMap/Secret), `service.yaml` (ClusterIP,
   `port: 80` → `targetPort`), and a `configmap.yaml` for non-secret config.
5. Register it in ARCHITECTURE.md (repository tree, file-by-file table,
   Microservice Communication table, Port Assignments) and add a service
   README if it has non-obvious setup or usage.
6. Wire cross-service calls through the backend `app/services/` HTTP-client
   pattern (best-effort or pass-through, per the error-handling conventions).
