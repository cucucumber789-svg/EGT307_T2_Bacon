/**
 * Dashboard logic - Bacon.Inc Environmental Monitoring Station
 *
 * Talks to Backend API for sensor data (and best-effort predictions), and
 * to Notification Service directly to drive the alert panel.
 *
 * Endpoints used:
 *
 *   GET {API_BASE}/sensors?limit=N
 *     -> [{ id, created_at, entry_id, temperature, humidity, air_quality }]
 *     Already implemented and working.
 *
 *   GET {API_BASE}/predictions?limit=N
 *     -> [{ entry_id, anomaly_score, is_anomaly, created_at }]
 *     NOT implemented yet (backend-api/app/routers/prediction.py is still
 *     a TODO). Only used to color anomalous points on the charts, so it
 *     fails silently until it exists.
 *
 *   POST {NOTIFICATION_BASE}/notify  { temperature, humidity, air_quality }
 *     -> { triggered: ["..."] }
 *     Notification Service checks the latest reading against its 3 rules
 *     (and messages Telegram if one fires); the alert panel just shows
 *     whatever it decided.
 */

const CONFIG = {
    API_BASE: "http://localhost:5000/api",
    NOTIFICATION_BASE: "http://localhost:5002/api",
    POLL_INTERVAL_MS: 8000,
    HISTORY_POINTS: 20,       // how many past readings to plot on each chart
    ANOMALY_THRESHOLD: 0.8,   // same convention as notification-service's ALERT_THRESHOLD
    AQ_LABELS: { 1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Hazardous" },
};

// ---------- element references ----------
const noteEl = document.getElementById("note");
const alertTitleEl = document.getElementById("alert");
const alertDetailEl = document.getElementById("alert-detail");
const connEl = document.getElementById("conn-status");

const tempValueEl = document.getElementById("temp-value");
const humidityValueEl = document.getElementById("humidity-value");
const aqValueEl = document.getElementById("aq-value");
const aqUnitEl = document.getElementById("aq-unit");

// ---------- charts ----------
// One small line chart per metric, created once, then just fed new data
// on every poll (cheaper than rebuilding the chart from scratch each time).
function makeChart(canvasId, label, color) {
    const ctx = document.getElementById(canvasId);
    return new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: color,
                backgroundColor: color,
                pointBackgroundColor: color,
                pointRadius: 3,
                tension: 0.25,
            }],
        },
        options: {
            maintainAspectRatio: false,
            animation: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { beginAtZero: false },
            },
        },
    });
}

const tempChart = makeChart("temp-chart", "Temperature", "#e0526b");
const humidityChart = makeChart("humidity-chart", "Humidity", "#2f7fd1");
const aqChart = makeChart("aq-chart", "Air Quality", "#2e9e5b");

// ---------- small pure helpers (easy to test on their own) ----------

function timeLabel(isoString) {
    return new Date(isoString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// This is "the ML prediction, turned into a graph": rather than a separate
// chart, anomalous readings just get colored red on these ones, wherever
// their entry_id was flagged by the ML service.
function pointColors(entryIds, anomalyEntryIds, defaultColor) {
    return entryIds.map((id) => (anomalyEntryIds.has(id) ? "#d6455b" : defaultColor));
}

function buildAnomalySet(predictions) {
    const set = new Set();
    predictions.forEach((p) => {
        const isAnomaly = p.is_anomaly ?? (p.anomaly_score >= CONFIG.ANOMALY_THRESHOLD);
        if (isAnomaly) set.add(p.entry_id);
    });
    return set;
}

async function fetchJSON(path) {
    const res = await fetch(CONFIG.API_BASE + path);
    if (!res.ok) throw new Error(path + " -> " + res.status);
    return res.json();
}

async function postJSON(url, body) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(url + " -> " + res.status);
    return res.json();
}

// ---------- rendering ----------

function updateCharts(readings, anomalyEntryIds) {
    // Backend returns newest-first; charts read left-to-right, oldest-first.
    const chronological = [...readings].reverse();
    const labels = chronological.map((r) => timeLabel(r.created_at));
    const entryIds = chronological.map((r) => r.entry_id);

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = chronological.map((r) => r.temperature);
    tempChart.data.datasets[0].pointBackgroundColor = pointColors(entryIds, anomalyEntryIds, "#e0526b");
    tempChart.update();

    humidityChart.data.labels = labels;
    humidityChart.data.datasets[0].data = chronological.map((r) => r.humidity);
    humidityChart.data.datasets[0].pointBackgroundColor = pointColors(entryIds, anomalyEntryIds, "#2f7fd1");
    humidityChart.update();

    aqChart.data.labels = labels;
    aqChart.data.datasets[0].data = chronological.map((r) => r.air_quality);
    aqChart.data.datasets[0].pointBackgroundColor = pointColors(entryIds, anomalyEntryIds, "#2e9e5b");
    aqChart.update();

    const latest = readings[0]; // API returns newest first
    if (latest) {
        tempValueEl.textContent = latest.temperature.toFixed(1);
        humidityValueEl.textContent = latest.humidity.toFixed(1);
        aqValueEl.textContent = latest.air_quality;
        aqUnitEl.textContent = CONFIG.AQ_LABELS[latest.air_quality] || ("Level " + latest.air_quality);
    }
}

function setAlert(state, title, detail) {
    noteEl.dataset.state = state;
    alertTitleEl.textContent = title;
    alertDetailEl.textContent = detail;
}

// ---------- main polling loop ----------

async function refresh() {
    let readings;
    try {
        readings = await fetchJSON("/sensors?limit=" + CONFIG.HISTORY_POINTS);
        connEl.textContent = "Live";
    } catch (err) {
        console.error("Could not reach Backend API:", err);
        connEl.textContent = "Offline";
        setAlert("pending", "Notification", "Can't reach Backend API - check it's running and CORS is enabled.");
        return;
    }

    // Predictions are best-effort: /api/predictions doesn't exist on
    // Backend API yet, so a failure here just means "not built yet". Only
    // used to color anomalous points red on the charts below.
    let anomalyEntryIds = new Set();
    try {
        const predictions = await fetchJSON("/predictions?limit=" + CONFIG.HISTORY_POINTS);
        anomalyEntryIds = buildAnomalySet(predictions);
    } catch (err) {
        // not built yet - charts just show uncolored points
    }

    updateCharts(readings, anomalyEntryIds);

    // Notification Service: hand it the latest reading, it checks the 3
    // threshold rules (and messages Telegram if one fires) - the alert
    // panel just shows whatever it decided.
    const latest = readings[0];
    if (!latest) {
        setAlert("pending", "Notification", "Waiting for data...");
        return;
    }
    try {
        const result = await postJSON(CONFIG.NOTIFICATION_BASE + "/notify", {
            temperature: latest.temperature,
            humidity: latest.humidity,
            air_quality: latest.air_quality,
        });
        if (result.triggered.length > 0) {
            setAlert("alert", result.triggered[0], result.triggered.join(" "));
        } else {
            setAlert("good", "All systems normal", "No alerts on the latest reading.");
        }
    } catch (err) {
        console.error("Could not reach Notification Service:", err);
        setAlert("pending", "Notification", "Can't reach Notification Service.");
    }
}

refresh();
setInterval(refresh, CONFIG.POLL_INTERVAL_MS);
