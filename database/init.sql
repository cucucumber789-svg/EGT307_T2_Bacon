CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    entry_id INTEGER NOT NULL,
    temperature NUMERIC NOT NULL,
    humidity NUMERIC NOT NULL,
    air_quality INTEGER NOT NULL
);
