FROM python:3.11-slim

# Notification Service container
# Intention: Lightweight Python image that checks sensor readings and
# sends Telegram alerts

WORKDIR /app

COPY components/notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY components/notification-service/ .
COPY config.yaml /app/config.yaml

EXPOSE 5002

CMD ["python", "-m", "app.main"]
