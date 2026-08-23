FROM python:3.11-slim

# ML Service container
# Intention: Python image for ML model serving
# Note: Final dependencies TBD based on ML framework choice

WORKDIR /app

COPY components/ml-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY components/ml-service/ .
COPY config.yaml /app/config.yaml

EXPOSE 5001

CMD ["python", "-m", "app.main"]
