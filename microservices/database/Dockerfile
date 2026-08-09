FROM busybox:1.36

# Dataset seed image
# Intention: provides the raw example dataset to the shared k8s dataset PVC.
# Used as an init container on the data-ingestion pod so /api/ingest/file
# has raw data to read. Build with:
#   docker build -t dataset-seed:latest microservices/database

WORKDIR /seed

COPY sensor_data.example.csv /seed/sensor_data.example.csv
