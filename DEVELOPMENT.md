# Contributing Guide

Development conventions and how-to guides for the Smart Environmental
Monitoring System.

---

## Project structure

All services live under `components/`. The Backend API is the largest
service and uses the full `app/` split:

```
components/backend-api/app/main.py  (entry point — starts the app)
  ├── imports config.py          (reads environment variables)
  ├── imports database.py        (connects to PostgreSQL)
  └── registers routers/sensor.py      (adds /api/sensors routes)

routers/sensor.py  (handles HTTP requests)
  ├── imports models/sensor.py   (to read/write sensor data in DB)
  └── imports schemas/sensor.py  (to validate incoming JSON)   (TBD)

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
Ingestion Service, and ML Service).

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

## Service structure

- **Backend-style services** (backend-api, ml-service, data-ingestion) use the
  `app/` split: `main.py` (a `create_app()` factory), `config.py`,
  `routers/` (Flask blueprints), `services/` (business logic and HTTP
  clients), and — for the backend — `models/` (SQLAlchemy) and `database.py`.
- **Small single-purpose services** stay single-file: the notification service
  defines its routes, threshold logic, and Telegram sending all in
  `app/main.py`.
- **Blueprints** are named `name_bp = Blueprint("name", __name__)` and
  registered in `main.py` with `url_prefix="/api"`.

### Service entry points

- Flask services expose `create_app()` and start via
  `if __name__ == "__main__": app.run(host="0.0.0.0", port=NNNN)`.
- Browser-facing services enable CORS with an `@app.after_request` handler.
- Ports are fixed per service; see the Port Assignments table in
  [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Python code style

- 4-space indentation, `snake_case` names, `"""docstrings"""` for modules and
  public functions.
- One idea per function; keep functions small and single-purpose. Prefer plain
  functions over classes for service logic unless state is genuinely needed.

---

## API responses & error handling

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

---

## Configuration & secrets

### Two-tier configuration

Secrets (bot tokens, database credentials) live in `.env` (gitignored) or a
k8s `Secret`. Non-sensitive tuning values (thresholds, ML hyperparameters,
simulator intervals) live in `config.yaml` at the repo root (committed). This
keeps secrets out of version control while making tuning values visible and
reviewable.

### `config.yaml`

Centralised config read by backend-api, ml-service, and sensor-simulator at
startup via a `_load_yaml()` helper. Each service searches a few candidate
paths (Docker image, standalone relative path, current directory) so the same
code works in both environments. In Docker, `config.yaml` is baked into the
image at build time (repo root is the build context; each Dockerfile copies
both its source and `config.yaml`).

### `GET /api/config`

The Backend API serves non-sensitive config values from `config.yaml` to the
frontend dashboard. The dashboard fetches this on page load so threshold
displays and severity bar markers stay in sync with the backend without
hardcoding values in JavaScript.

### Secrets

Use empty-string defaults and are injected per environment — `.env` for
Compose, a k8s `Secret`, or shell environment variables. Never hardcode a
secret in code.

### Env validation

The `env-validator` service (Docker Compose) and `scripts/validate-env.py`
(standalone) check that `.env` exists and all required variables are set
before any service starts. In Docker, the validator runs as a healthcheck;
other services depend on it being healthy. In standalone mode, run
`python scripts/validate-env.py` before starting services. This is the
**first layer**: it catches placeholder values and missing variables so
misconfigured deployments fail fast.

### Runtime confirmation

Each service's startup print confirms the credentials actually reached the
process. For example, the notification service prints `Telegram configured`
when both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are loaded, or
`Telegram not configured` when they are not. This is the **second layer**:
the env-validator ensures the `.env` file is correct; the startup prints
ensure the values were injected into the container's environment.

### Auto-loading `.env`

Each service calls `load_dotenv()` from `python-dotenv` at startup, so `.env`
is automatically loaded into `os.environ` when running standalone. No manual
variable exports needed.

### Non-secret config in env vars

Service URLs, dataset paths carry a real default in code, and the same value
is set explicitly in `docker-compose.yml` / the k8s ConfigMap so behaviour is
identical whether or not the variable is set.

### Config error handling

`config.yaml` values are clamped to valid bounds at startup so typos or
out-of-range values degrade gracefully instead of crashing or silently
misbehaving. Missing keys fall back to hardcoded defaults. Invalid YAML
(malformed syntax) causes a startup crash with a clear traceback — this is
intentional, as a broken config should not run. The valid ranges are:

| Value | Valid range | Default | Effect of clamping |
|---|---|---|---|
| `anomaly_score_threshold` | `0.0`–`0.3` | `0.05` | `0.0` = every anomaly notifies; `0.3` = only extreme anomalies |
| `contamination` | `0.0`–`1.0` | `0.02` | Fraction of training data flagged anomalous |
| `n_estimators` | `≥ 1` | `200` | Number of IsolationForest trees |
| `severity_steepness` | `≥ 0.01` | `10.0` | Sigmoid sharpness; higher = sharper green-to-red transition |
| `send_interval_seconds` | `≥ 0.1` | `3` | Delay between sensor readings (seconds) |
| `anomaly_rate` | `0.0`–`1.0` | `0.05` | Fraction of synthetic anomalies injected |

Values outside their range are silently corrected to the nearest bound. This
means `anomaly_score_threshold: 0.5` becomes `0.3`, and
`contamination: -0.1` becomes `0.0` — no crash, no warning, just safe
defaults. The `config.yaml` file includes valid ranges in its comments for
operator reference.

---

## Database schema changes

- There is no migrations framework. To change a table, update the SQLAlchemy
  model (`app/models/`) **and** `components/database/init.sql` together.
- `Base.metadata.create_all` only creates missing tables — it does **not**
  alter existing ones. For a development database, recreate it or apply the
  change manually.

---

## Deployment hygiene

- One Dockerfile per service; `docker-compose.yml` at the repo root; one
  `k8s/` manifest folder per service.
- Environment: `.env` (local), ConfigMap (non-secret), Secret (credentials).
- Keep generated data and build outputs out of the repository.
- **Log suppression** — Flask services set the `werkzeug` logger to WARNING
  level so routine request logs (200, 201) do not clutter terminal output.
  The frontend nginx disables access logging entirely (`access_log off;`).
  Only errors, warnings, and startup notices appear in `docker compose logs`.

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

Each service runs independently for troubleshooting and testing without the
full stack. Each module includes an `if __name__ == "__main__"` entry point
for standalone execution.

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
