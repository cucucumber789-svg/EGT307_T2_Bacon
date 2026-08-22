CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    entry_id INTEGER NOT NULL,
    temperature NUMERIC NOT NULL,
    humidity NUMERIC NOT NULL,
    air_quality INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    entry_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    temperature NUMERIC NOT NULL,
    humidity NUMERIC NOT NULL,
    air_quality INTEGER NOT NULL,
    is_anomaly BOOLEAN NOT NULL,
    anomaly_score NUMERIC NOT NULL,
    severity NUMERIC NOT NULL,
    alerts TEXT NOT NULL DEFAULT ''
);
