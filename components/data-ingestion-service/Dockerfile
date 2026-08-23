FROM python:3.11-slim

# Data Ingestion Service container
# Intention: Lightweight Python image for data intake processing

WORKDIR /app

COPY components/data-ingestion-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY components/data-ingestion-service/ .
COPY config.yaml /app/config.yaml

EXPOSE 5003

CMD ["python", "-m", "app.main"]
