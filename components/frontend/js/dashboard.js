/**
 * Dashboard logic - Bacon.Inc Environmental Monitoring Station
 *
 * Talks to Backend API for sensor data and predictions, and to the
 * Notification Service for the alert panel.
 *
 * Endpoints used:
 *   GET  {API_BASE}/sensors?limit=N      -> sensor readings
 *   GET  {API_BASE}/predictions?limit=N  -> ML predictions (anomaly point coloring)
 *   GET  {NOTIFICATION_BASE}/alerts      -> recent alerts, shown in the alert panel
 *
 * The Backend API triggers the Notification Service when the ML model flags
 * an anomaly; this page only reads the resulting alerts (POSTing /api/notify
 * from here would re-send Telegram messages on every poll).
 */

// Non-sensitive tuning values. Defaults only — overridden by GET /api/config on load.
const CONFIG = {
    API_BASE: "http://localhost:5000/api",           // where Backend API is running
    NOTIFICATION_BASE: "http://localhost:5002/api",  // where Notification Service is running
    POLL_INTERVAL_MS: 8000,                          // how often to refresh the page, in milliseconds
    HISTORY_POINTS: 20,                              // how many past readings to plot on each chart
    ANOMALY_THRESHOLD: 0.8,                          // score above this colors a point red when predictions lack is_anomaly
    AQ_LABELS: { 1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Hazardous" }, // turns the air_quality number into a word
    NOTIFICATION_THRESHOLD: 0.05,                    // fires Telegram alert when anomaly_score < -this (source: config.yaml)
    MODEL_CONTAMINATION: 0.02,                       // expected anomaly fraction in training data (source: config.yaml)
    SEVERITY_STEEPNESS: 10,                          // sigmoid steepness for severity bar (source: config.yaml)
};

// ---------- element references ----------
// Look up each HTML element once here, instead of searching for it again on every refresh.
const noteEl = document.getElementById("note");                 // the alert panel box; its color depends on the alert state
const alertTitleEl = document.getElementById("alert");          // the alert panel's bold title line
const alertDetailEl = document.getElementById("alert-detail");  // the alert panel's smaller detail line
const connEl = document.getElementById("conn-status");          // small text showing "Live" or "Offline"

const tempValueEl = document.getElementById("temp-value");          // big number showing the latest temperature
const humidityValueEl = document.getElementById("humidity-value");  // big number showing the latest humidity
const aqValueEl = document.getElementById("aq-value");               // big number showing the latest air quality level
const aqUnitEl = document.getElementById("aq-unit");                 // word next to it, e.g. "Good" or "Poor"

// ---------- ML status elements ----------
const severityFillEl = document.getElementById("severity-fill");     // severity bar fill
const severityValueEl = document.getElementById("severity-value");   // severity number
const anomalyScoreEl = document.getElementById("anomaly-score");     // anomaly score number
const anomalyBufferEl = document.getElementById("anomaly-buffer");   // buffer distance to notification threshold
const mlStatusTextEl = document.getElementById("ml-status-text");    // "Normal" or "Anomaly" text
const thresholdMarkerModelEl = document.getElementById("threshold-marker-model");   // model boundary marker on severity bar
const thresholdMarkerNotifyEl = document.getElementById("threshold-marker-notify"); // notification trigger marker on severity bar
const notifyThresholdValEl = document.getElementById("notify-threshold-val");       // notification threshold value
const modelContaminationValEl = document.getElementById("model-contamination-val"); // model contamination value

// ---------- charts ----------

// Creates one small line chart in the given canvas, starting empty.
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
                pointRadius: 4,   // slightly bigger dots so they're easy to see
                borderWidth: 2,   // slightly thicker line
                tension: 0.25,
            }],
        },
        options: {
            maintainAspectRatio: false,
            animation: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    display: true,                                     // show the time under the chart
                    ticks: { maxTicksLimit: 6, font: { size: 11 } },    // don't cram in every label, keep text readable
                },
                y: {
                    beginAtZero: false,
                    ticks: { font: { size: 12 } },
                },
            },
        },
    });
}

const tempChart = makeChart("temp-chart", "Temperature", "#e0526b");       // line chart of temperature over time
const humidityChart = makeChart("humidity-chart", "Humidity", "#2f7fd1");  // line chart of humidity over time
const aqChart = makeChart("aq-chart", "Air Quality", "#2e9e5b");           // line chart of air quality over time

// ---------- small helper functions ----------

// Turns a timestamp into a short "HH:MM" label for the chart's x-axis.
function timeLabel(isoString) {
    return new Date(isoString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Builds one color per point: red if that reading was flagged as an anomaly, otherwise the normal color.
function pointColors(entryIds, anomalyEntryIds, defaultColor) {
    const colors = [];
    for (let i = 0; i < entryIds.length; i++) {
        if (anomalyEntryIds.has(entryIds[i])) {
            colors.push("#d6455b");
        } else {
            colors.push(defaultColor);
        }
    }
    return colors;
}

// Collects the entry_id of every reading the ML service flagged as an anomaly.
function buildAnomalySet(predictions) {
    const set = new Set();
    for (let i = 0; i < predictions.length; i++) {
        const p = predictions[i];
        // Fall back to the score threshold when is_anomaly is missing.
        const isAnomaly = p.is_anomaly ?? p.anomaly_score >= CONFIG.ANOMALY_THRESHOLD;
        if (isAnomaly) {
            set.add(p.entry_id);
        }
    }
    return set;
}

// Sends a GET request and returns the parsed JSON.
// Relative paths (e.g. "/sensors") are resolved against the Backend API;
// absolute URLs (e.g. the Notification Service /alerts endpoint) are used as-is.
async function fetchJSON(path) {
    const url = path.startsWith("http") ? path : CONFIG.API_BASE + path;
    const res = await fetch(url);
    if (!res.ok) throw new Error(path + " -> " + res.status);
    return res.json();
}

// ---------- rendering ----------

// Redraws all 3 charts and the latest-value boxes from a fresh batch of readings.
function updateCharts(readings, anomalyEntryIds) {
    // Backend returns newest-first; charts read left-to-right, oldest-first.
    const chronological = readings.slice();
    chronological.reverse();

    const labels = [];        // x-axis labels, one per reading (e.g. "10:15")
    const entryIds = [];      // entry_id per reading, used to look up anomaly colors
    const temperatures = [];  // y-axis values for the temperature chart
    const humidities = [];    // y-axis values for the humidity chart
    const airQualities = [];  // y-axis values for the air quality chart
    for (let i = 0; i < chronological.length; i++) {
        const r = chronological[i];
        labels.push(timeLabel(r.created_at));
        entryIds.push(r.entry_id);
        temperatures.push(r.temperature);
        humidities.push(r.humidity);
        airQualities.push(r.air_quality);
    }

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = temperatures;
    tempChart.data.datasets[0].pointBackgroundColor = pointColors(entryIds, anomalyEntryIds, "#e0526b");
    tempChart.update();

    humidityChart.data.labels = labels;
    humidityChart.data.datasets[0].data = humidities;
    humidityChart.data.datasets[0].pointBackgroundColor = pointColors(entryIds, anomalyEntryIds, "#2f7fd1");
    humidityChart.update();

    aqChart.data.labels = labels;
    aqChart.data.datasets[0].data = airQualities;
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

// Updates the note panel's color, title, and detail text.
function setAlert(state, title, detail) {
    noteEl.dataset.state = state;   // "pending" | "alert" | "good" - CSS uses this to pick the color
    alertTitleEl.textContent = title;
    alertDetailEl.textContent = detail;
}

// Updates the ML Analysis panel with severity, anomaly score, and status.
function updateMLStatus(prediction) {
    if (!prediction) {
        severityFillEl.style.width = "0%";
        severityValueEl.textContent = "\u2014";
        anomalyScoreEl.textContent = "\u2014";
        anomalyBufferEl.textContent = "\u2014";
        mlStatusTextEl.textContent = "\u2014";
        mlStatusTextEl.className = "ml-value";
        return;
    }

    const severity = prediction.severity || 0;
    const score = prediction.anomaly_score || 0;
    const isAnomaly = prediction.is_anomaly;

    // Update severity bar width and color
    const severityPercent = Math.round(severity * 100);
    severityFillEl.style.width = severityPercent + "%";

    if (severity < 0.3) {
        severityFillEl.style.backgroundColor = "#2e9e5b";  // green
    } else if (severity < 0.7) {
        severityFillEl.style.backgroundColor = "#f0ad4e";  // yellow
    } else {
        severityFillEl.style.backgroundColor = "#d6455b";  // red
    }

    // Update severity value
    severityValueEl.textContent = severity.toFixed(2);

    // Update anomaly score and buffer to notification threshold
    anomalyScoreEl.textContent = score.toFixed(4);
    const buffer = CONFIG.NOTIFICATION_THRESHOLD - Math.abs(score);
    if (isAnomaly && buffer <= 0) {
        anomalyBufferEl.textContent = "ALERT";
        anomalyBufferEl.className = "ml-hint ml-hint-alert";
    } else {
        anomalyBufferEl.textContent = "buffer " + buffer.toFixed(4);
        anomalyBufferEl.className = "ml-hint";
    }

    // Update status text
    if (isAnomaly) {
        mlStatusTextEl.textContent = "Anomaly";
        mlStatusTextEl.className = "ml-value anomaly";
    } else {
        mlStatusTextEl.textContent = "Normal";
        mlStatusTextEl.className = "ml-value normal";
    }
}

// Place the threshold markers on the severity bar at the correct positions.
// severity = 1 / (1 + exp(SEVERITY_STEEPNESS * raw_score))
// Model boundary at score=0 → severity=0.5 → 50%
// Notification threshold at score=-threshold → severity depends on steepness
function placeThresholdMarkers() {
    const steepness = CONFIG.SEVERITY_STEEPNESS;
    const modelSeverity = 1 / (1 + Math.exp(steepness * 0));               // score=0 → 50%
    const notifySeverity = 1 / (1 + Math.exp(steepness * -CONFIG.NOTIFICATION_THRESHOLD));
    thresholdMarkerModelEl.style.left = (modelSeverity * 100) + "%";
    thresholdMarkerNotifyEl.style.left = (notifySeverity * 100) + "%";
}

// Populate the static threshold reference rows once at load.
function setThresholdInfo() {
    notifyThresholdValEl.textContent = CONFIG.NOTIFICATION_THRESHOLD;
    modelContaminationValEl.textContent = (CONFIG.MODEL_CONTAMINATION * 100) + "%";
}

// ---------- main polling loop ----------

// Runs on a timer: fetches sensor data, updates the charts, then checks and shows alerts.
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

    // Predictions are best-effort: a failure here just leaves the points
    // uncolored. Only used to color anomalous points red on the charts below.
    let anomalyEntryIds = new Set();
    let latestPrediction = null;
    try {
        const predictions = await fetchJSON("/predictions?limit=" + CONFIG.HISTORY_POINTS);
        anomalyEntryIds = buildAnomalySet(predictions);
        if (predictions.length > 0) {
            latestPrediction = predictions[0]; // newest first
        }
    } catch (err) {
        // prediction lookup failed - charts just show uncolored points
    }

    updateCharts(readings, anomalyEntryIds);
    updateMLStatus(latestPrediction);

    // Notification Service: the Backend API sends alerts here when the ML
    // model flags an anomaly, so the panel just shows the most recent one.
    const latest = readings[0];
    if (!latest) {
        setAlert("pending", "Notification", "Waiting for data...");
        return;
    }
    try {
        const alerts = await fetchJSON(CONFIG.NOTIFICATION_BASE + "/alerts");
        if (alerts.length > 0) {
            setAlert("alert", alerts[0].message, alerts[0].created_at.slice(11, 16) + " " + alerts[0].created_at.slice(0, 10));
        } else {
            setAlert("good", "All systems normal", "No alerts on the latest reading.");
        }
    } catch (err) {
        console.error("Could not reach Notification Service:", err);
        setAlert("pending", "Notification", "Can't reach Notification Service.");
    }
}

// ---------- startup ----------

// Fetch config from the backend API first, then start the polling loop.
// If the config fetch fails, the hardcoded defaults in CONFIG are used.
async function loadConfig() {
    try {
        const cfg = await fetchJSON("/config");
        CONFIG.NOTIFICATION_THRESHOLD = cfg.notification_threshold;
        CONFIG.MODEL_CONTAMINATION = cfg.model_contamination;
        CONFIG.SEVERITY_STEEPNESS = cfg.severity_steepness;
    } catch (err) {
        console.warn("Could not load /api/config, using defaults:", err);
    }
    placeThresholdMarkers();
    setThresholdInfo();
    refresh();
    setInterval(refresh, CONFIG.POLL_INTERVAL_MS);
}

loadConfig();
