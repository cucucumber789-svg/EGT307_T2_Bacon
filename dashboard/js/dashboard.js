/**
 * Dashboard logic - Bacon.Inc Environmental Monitoring Station
 *
 * Talks ONLY to Backend API - never directly to the ML Service. Backend
 * API is responsible for calling ML Service itself and handing back
 * predictions (see Architecture.md's communication table).
 *
 * Endpoints used:
 *
 *   GET /api/sensors?limit=N
 *     -> [{ id, created_at, entry_id, temperature, humidity, air_quality }]
 *     Already implemented and working.
 *
 *   GET /api/predictions?limit=N
 *     -> [{ entry_id, anomaly_score, is_anomaly, created_at }]
 *     NOT implemented yet (backend-api/app/routers/prediction.py is still
 *     a TODO). Until it exists, this file keeps working off sensor data
 *     alone - the notification panel just says so instead of guessing.
 */

const CONFIG = {
    API_BASE: "http://localhost:5000/api",
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
    // Backend API yet, so a failure here just means "not built yet".
    let anomalyEntryIds = new Set();
    let predictionsAvailable = false;
    let latestPrediction = null;
    try {
        const predictions = await fetchJSON("/predictions?limit=" + CONFIG.HISTORY_POINTS);
        predictionsAvailable = true;
        latestPrediction = predictions[0] || null;
        anomalyEntryIds = buildAnomalySet(predictions);
    } catch (err) {
        predictionsAvailable = false;
    }

    updateCharts(readings, anomalyEntryIds);

    if (!predictionsAvailable) {
        setAlert("pending", "Notification", "ML predictions not connected yet - showing real sensor data only.");
    } else if (!latestPrediction) {
        setAlert("pending", "Notification", "Waiting for a prediction.");
    } else {
        const isAnomaly = latestPrediction.is_anomaly ?? (latestPrediction.anomaly_score >= CONFIG.ANOMALY_THRESHOLD);
        if (isAnomaly) {
            setAlert("alert", "Anomaly detected", "Entry #" + latestPrediction.entry_id + " was flagged by the ML service.");
        } else {
            setAlert("good", "All systems normal", "No anomalies in the latest reading.");
        }
    }
}

refresh();
setInterval(refresh, CONFIG.POLL_INTERVAL_MS);
