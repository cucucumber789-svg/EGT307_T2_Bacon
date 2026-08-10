FROM python:3.11-slim

# Sensor Simulator container
# Intention: Lightweight Python image that replays recorded sensor
# readings and streams them to the Data Ingestion Service, standing in
# for real IoT hardware.

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# No EXPOSE here - this service only makes outgoing requests, it never
# accepts incoming connections, so it doesn't need a port.

CMD ["python", "sensor_simulator.py"]
