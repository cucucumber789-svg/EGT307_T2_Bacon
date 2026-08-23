# Notification service

Sends Telegram alerts when the system detects abnormal environmental
conditions, and keeps the most recent alerts in memory for the dashboard.

## How it fits in

- The **Backend API** calls `POST /api/notify` only when a prediction has
  `is_anomaly: true` and its score is below the configured negative
  notification threshold (`store_prediction` in
  `components/backend-api/app/services/prediction_service.py`).
- The service sends a Telegram message for each alert and records it in an
  in-memory list.
- The **dashboard** reads the alerts with `GET /api/alerts`.

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

## Two ways to receive alerts

There are two supported paths. Pick the one that matches your situation.

### Path A — first-time setup (create your own bot)

For a new user running the app on their own: follow **Telegram setup →
First-time** below to create a bot, get a chat id, and put both into the
configuration. This is the default experience — until `TELEGRAM_BOT_TOKEN`
and `TELEGRAM_CHAT_ID` are set, the service starts with a notice that
Telegram is not configured and skips sends.

### Path B — join a team that already has a bot (recommended for groups)

If a teammate already runs the notification service with a bot, you don't
create anything:

1. Ask the bot owner to add the bot to your **Telegram group** (the owner
   adds the bot as a member).
2. Join the group as a normal member — the bot's messages are delivered to
   everyone in it.
3. Use the already-running service as-is. The token and the group's
   `chat_id` live in the shared deployment config (`.env` for Compose, k8s
   `Secret`), so no per-user setup is needed.

Credentials are **deployment-owned, not per-user**: they are shared by
everyone using the same deployment, and are never committed to the repo.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt` (Flask, requests)
- Docker (optional, for the containerised run modes)

## Telegram setup

### First-time: create your own bot

1. Open Telegram and message **@BotFather**.
2. Run `/newbot`, follow the prompts, and copy the **token** it gives you
   (looks like `123456789:AA...`).
3. Message your new bot once (any text) so it can reach you.
4. Find your **chat id**:

   ```bash
   # Bash
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"

   # PowerShell
   Invoke-RestMethod -Uri "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```

   In the JSON response, look for `"chat":{"id":<number>,...}` inside
   `result[0].message`. That number is your chat id.

5. Put the token and chat id into the configuration (see below), then start
   the service.

### Joining: add an existing bot to a group

1. Create (or open) the Telegram group and add the bot as a member.
2. Post a message in the group (so the bot receives an update).
3. Get the group's **chat id**:

   ```bash
   # Bash
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"

   # PowerShell
   Invoke-RestMethod -Uri "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```

   Look for `result[0].message.chat.id` — for a group this is a **negative
   number** (e.g. `-1001234567890`). The bot must be a member of the group,
   otherwise it cannot send to it.

4. The token (from `/token` in BotFather, or the one already in use) and the
   group chat id go into the configuration; everyone in the group receives
   the alerts.

## Configuration

All values come from environment variables.

| Variable                | Default | Secret? | Purpose                              |
|-------------------------|---------|---------|--------------------------------------|
| `TELEGRAM_BOT_TOKEN`    | `""`    | yes     | Telegram bot token (from BotFather)  |
| `TELEGRAM_CHAT_ID`      | `""`    | yes     | Chat/group to send alerts to         |

If the token or chat id is empty, the service skips the Telegram send and
prints `Telegram not configured, skipping send: <message>`. On startup it
also prints a notice pointing here, and the `/` health endpoint reports
`"telegram_configured": false`.

## Verify your setup

1. Start the service (see below).
2. Check the health endpoint:

   ```bash
   # Bash
   curl http://localhost:5002/

   # PowerShell
   Invoke-RestMethod -Uri http://localhost:5002/
   ```

   `telegram_configured` is `true` only when both `TELEGRAM_BOT_TOKEN` and
   `TELEGRAM_CHAT_ID` are set. If it is `false`, credentials are missing.

3. Send a test alert:

   ```bash
   # Bash
   curl -X POST http://localhost:5002/api/notify \
     -H "Content-Type: application/json" \
     -d '{"temperature":40,"humidity":80,"air_quality":3,"alerts":["Test alert"]}'

   # PowerShell
   Invoke-RestMethod -Uri http://localhost:5002/api/notify -Method Post `
     -ContentType "application/json" `
     -Body '{"temperature":40,"humidity":80,"air_quality":3,"alerts":["Test alert"]}'
   ```

   The message should appear in your chat/group, and `GET /api/alerts` shows
   the record.

## Running the service

### Local (standalone)

```bash
cd components/notification-service
pip install -r requirements.txt
python -m app.main
```

The service loads Telegram credentials from `.env` automatically via
`python-dotenv`. The service listens on port `5002`.

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
file.

### Kubernetes

Create the Secret with the real credentials (never commit them):

```
kubectl create secret generic telegram-credentials \
  --from-literal=TELEGRAM_BOT_TOKEN=<token> \
  --from-literal=TELEGRAM_CHAT_ID=<chat-id>
```

`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are the expected keys.

## Usage

### Trigger an alert directly

`POST /api/notify` with a reading and an `alerts` list. The service sends
each alert via Telegram and records it for the dashboard.

```bash
# Bash
curl -X POST http://localhost:5002/api/notify \
  -H "Content-Type: application/json" \
  -d '{"temperature":40,"humidity":80,"air_quality":3,"alerts":["High temperature detected!"]}'
# -> 200 {"triggered": ["High temperature detected!"]}
```

```powershell
# PowerShell
Invoke-RestMethod -Uri http://localhost:5002/api/notify -Method Post `
  -ContentType "application/json" `
  -Body '{"temperature":40,"humidity":80,"air_quality":3,"alerts":["High temperature detected!"]}'
```

### Read recent alerts

```bash
# Bash
curl http://localhost:5002/api/alerts

# PowerShell
Invoke-RestMethod -Uri http://localhost:5002/api/alerts
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
| `telegram_configured: false` in `/` | `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` not set at startup. Follow "First-time setup" (or the team's shared config) and restart. |
| `Telegram not configured, skipping send` | `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` not set at startup. Set them before launching the service (config is read at import). |
| `Telegram send failed: 401` | Bot token is wrong/revoked. Recreate via BotFather. |
| `Telegram send failed: 400` | Invalid chat id (e.g. bot never messaged you, or wrong group id). Re-check `getUpdates`. |
| `POST /api/notify` returns `400` | Missing/invalid fields. Requires `temperature`, `humidity`, `air_quality` (JSON body). |
| `POST /api/notify` returns `415` | Body sent with a non-JSON content type. Use `Content-Type: application/json`. |
| Alerts disappear | Expected: alerts live in memory and reset on restart. |
