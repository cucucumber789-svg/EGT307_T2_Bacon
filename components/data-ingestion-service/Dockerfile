FROM python:3.11-slim

# Data Ingestion Service container
# Intention: Lightweight Python image for data intake processing

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5003

CMD ["python", "app/main.py"]
