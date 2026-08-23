FROM python:3.11-slim

# Intention: Multi-stage build for backend API
# - Install dependencies from requirements.txt
# - Copy application code
# - Expose Flask port and run with gunicorn

WORKDIR /app

COPY components/backend-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY components/backend-api/ .
COPY config.yaml /app/config.yaml

EXPOSE 5000

CMD ["python", "-m", "app.main"]
