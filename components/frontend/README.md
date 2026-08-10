# Frontend Dashboard

Static dashboard (HTML/CSS/JS + Chart.js) for the Environmental Monitoring
Station. It shows live sensor readings, colors anomalous points red, and
displays the most recent alert from the Notification Service.

## How it fits in

- The page is **static** — no build step, no bundler. Files live under
  `html/`, `css/`, and `js/`.
- The browser talks **directly** to the Backend API (`GET /api/sensors`,
  `GET /api/predictions`) and the Notification Service (`GET /api/alerts`).
  The frontend is not a microservice: it never talks to the database or the
  other services.
- Alerts are created by the Backend API when the ML model flags an anomaly;
  the dashboard only reads them. It never POSTs `/api/notify` itself, so a
  page refresh cannot re-send Telegram messages.

```
                    ┌──────────────┐
                    │    Browser   │
                    └──────┬───────┘
             ┌─────────────┼─────────────┐
             ▼                            ▼
   Backend API (5000)          Notification Service (5002)
   GET /api/sensors            GET /api/alerts
   GET /api/predictions
```

## Prerequisites

- A web browser. No Python or Node is needed to serve the page.

## Running the service

### Docker Compose (part of the full stack)

The `frontend` service in `docker-compose.yml` builds the image from this
folder's `Dockerfile` and serves it on port `3000`. Start everything from the
repo root:

```
docker-compose up --build
```

Then open `http://localhost:3000/`.

### Kubernetes

`k8s/frontend/deployment.yaml` runs the same nginx image and
`k8s/frontend/service.yaml` exposes it internally (ClusterIP). A LoadBalancer
service is future work for external access.

### Local (standalone)

Serve the folder with any static file server, e.g. Python's built-in one:

```powershell
cd components/frontend
python -m http.server 3000
```

Then open `http://localhost:3000/html/dashboard.html`. For the dashboard to
show data, the Backend API (5000) and Notification Service (5002) must be
running, and the browser must be able to reach them (CORS enabled).

> Opening `dashboard.html` directly with `file://` will not work — the page
> fetches the API and Chart.js over HTTP.

## Configuration

The tunables live in the `CONFIG` object at the top of `js/dashboard.js`:

| Setting                 | Default | Purpose                                |
|-------------------------|---------|----------------------------------------|
| `API_BASE`              | `http://localhost:5000/api` | Backend API base URL        |
| `NOTIFICATION_BASE`     | `http://localhost:5002/api` | Notification Service base URL |
| `POLL_INTERVAL_MS`      | `8000`  | How often to refresh, in milliseconds |
| `HISTORY_POINTS`        | `20`    | How many past readings to plot        |
| `ANOMALY_THRESHOLD`     | `0.8`   | Score above this colors a point red when `is_anomaly` is missing |
| `AQ_LABELS`             | `{1..5}`| Maps the `air_quality` number to a word |

## Verify your setup

1. Start the Backend API and Notification Service (see their READMEs).
2. Register the sensor dataset once: `POST http://localhost:5003/api/ingest/file`
   (Data Ingestion Service), so the backend has readings to serve.
3. Open `http://localhost:3000/html/dashboard.html`. The connection indicator
   shows **Live**, the three charts fill with readings, and the alert panel
   reflects the latest alert.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Page shows "Can't reach Backend API" | Backend API not running or CORS not enabled. Check `API_BASE` in `js/dashboard.js`. |
| Charts stay empty | No readings registered yet. POST `/api/ingest/file` to the Data Ingestion Service, or add readings via `POST /api/sensors`. |
| Points are never red | Predictions lookup failed or the ML model isn't trained yet. Check the Backend API logs and that the ML Service is running. |
| Alerts panel stuck on "pending" | Notification Service not running, or no alerts recorded yet. Check `GET http://localhost:5002/api/alerts`. |
| `file://` page is blank | Open the page over HTTP (`python -m http.server` or the Docker container), not from the filesystem. |
