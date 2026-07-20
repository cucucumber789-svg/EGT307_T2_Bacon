FROM python:3.11-slim

# Intention: Multi-stage build for backend API
# - Install dependencies from requirements.txt
# - Copy application code
# - Expose Flask port and run with gunicorn

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app/main.py"]
