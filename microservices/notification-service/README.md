# Notification Service

Sends Telegram alerts when the system detects abnormal environmental
conditions, and keeps the most recent alerts in memory for the dashboard.

## How it fits in

- The **Backend API** calls `POST /api/notify` whenever the ML model flags a
  sensor reading as anomalous (`store_prediction` in
  `microservices/backend-api/app/services/prediction_service.py`).
- The service sends a Telegram message for each alert and records it in an
  in-memory list.
- The **dashboard** reads the alerts with `GET /api/alerts`.
- The endpoint also works standalone: POST a reading directly and the service
  checks it against its own thresholds.

## Flow

```
Backend API (ML anomaly)
        │  POST /api/notify   { temperature, humidity, air_quality, alerts? }
        ▼
Notification Service
        ├─► Telegram Bot API  (sendMessage)
        └─► recent_alerts (in memory, last 50)
                │  GET /api/alerts
                ▼
           Dashboard
```

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt` (Flask, requests)
- Docker (optional, for the containerised run modes)

## Telegram setup

1. Open Telegram and message **@BotFather**.
2. Run `/newbot`, follow the prompts, and copy the **token** it gives you
   (looks like `123456789:AA...`).
3. Message your new bot once (any text) so it can reach you.
4. Find your **chat id**:

   ```
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```

   In the JSON response, look for `"chat":{"id":<number>,...}` inside
   `result[0].message`. That number is your chat id.

## Configuration

All values come from environment variables. The threshold defaults also live
in code (`app/main.py`) and the same numbers are set explicitly in
`docker-compose.yml` and the k8s ConfigMap, so behaviour is identical whether
or not the variables are set.

| Variable                | Default | Secret? | Purpose                              |
|-------------------------|---------|---------|--------------------------------------|
| `TELEGRAM_BOT_TOKEN`    | `""`    | yes     | Telegram bot token (from BotFather)  |
| `TELEGRAM_CHAT_ID`      | `""`    | yes     | Chat/group to send alerts to         |
| `TEMP_THRESHOLD`        | `39`    | no      | Temperature above this triggers alert|
| `HUMIDITY_THRESHOLD`    | `55`    | no      | Humidity above this triggers alert   |
| `AQ_THRESHOLD`          | `2`     | no      | Air quality at/below this triggers alert |

If the token or chat id is empty, the service skips the Telegram send and
prints `Telegram not configured, skipping send: <message>`.

## Running the service

### Local (standalone)

Set the environment variables **before** starting the service (they are read
once at import time):

```powershell
$env:TELEGRAM_BOT_TOKEN = "<token>"
$env:TELEGRAM_CHAT_ID = "<chat-id>"
cd microservices/notification-service
python app/main.py
```

The service listens on port `5002`.

### Docker Compose

Create a `.env` file in the repo root (git-ignored):

```
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat-id>
```

Then start the stack:

```
docker-compose up --build
```

Compose interpolates `${TELEGRAM_BOT_TOKEN}` / `${TELEGRAM_CHAT_ID}` from that
file. Thresholds are already set in the `notification-service` environment.

### Kubernetes

The ConfigMap (`k8s/notification-service/configmap.yaml`) holds the
thresholds. Create the Secret with the real credentials (never commit them):

```
kubectl create secret generic telegram-credentials \
  --from-literal=TELEGRAM_BOT_TOKEN=<token> \
  --from-literal=TELEGRAM_CHAT_ID=<chat-id>
```

`k8s/notification-service/secret.example.yaml` is a placeholder template
showing the expected keys.

## Usage

### Trigger a check / alert directly

`POST /api/notify` with a reading. When the `alerts` list is provided it is
sent verbatim (this is how the backend forwards the ML model's messages);
otherwise the service derives the messages from its thresholds.

```bash
# Backend-style call: use the ML model's messages
curl -X POST http://localhost:5002/api/notify \
  -H "Content-Type: application/json" \
  -d '{"temperature":40,"humidity":80,"air_quality":3,"alerts":["High temperature detected!"]}'
# -> 200 {"triggered": ["High temperature detected!"]}

# Direct call: derive from thresholds
curl -X POST http://localhost:5002/api/notify \
  -H "Content-Type: application/json" \
  -d '{"temperature":40,"humidity":80,"air_quality":3}'
# -> 200 {"triggered": ["High temperature detected!", "High humidity detected!"]}
```

### Read recent alerts

```bash
curl http://localhost:5002/api/alerts
# -> [{"message": "...", "temperature": ..., "humidity": ..., "air_quality": ..., "created_at": "..."}]
```

Alerts are kept in memory only (last 50) and reset when the service restarts.

### Through the Backend API

Send an anomalous reading to `POST /api/predict` on the backend (port 5000).
If the ML model flags it, the backend calls `/api/notify` automatically and
the alert appears in `GET /api/alerts` and Telegram.

## Verifying Telegram delivery

- Credentials set: a message should arrive in your chat when an alert fires.
- Credentials empty: the service prints
  `Telegram not configured, skipping send: ...` and still records the alert
  for `/api/alerts`.
- Telegram rejects the send: the service prints `Telegram send failed: ...`
  but does not crash.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `Telegram not configured, skipping send` | `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` not set at startup. Set them before launching the service (config is read at import). |
| `Telegram send failed: 401` | Bot token is wrong/revoked. Recreate via BotFather. |
| `Telegram send failed: 400` | Invalid chat id (e.g. bot never messaged you, or wrong group id). Re-check `getUpdates`. |
| `POST /api/notify` returns `400` | Missing/invalid fields. Requires `temperature`, `humidity`, `air_quality` (JSON body). |
| `POST /api/notify` returns `415` | Body sent with a non-JSON content type. Use `Content-Type: application/json`. |
| Alerts disappear | Expected: alerts live in memory and reset on restart. |
