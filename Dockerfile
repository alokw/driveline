FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose Flask port
EXPOSE 5000

# Default to production mode with gunicorn
# Development mode overrides this CMD to run "python app.py" with hot-reload
CMD ["gunicorn", "--worker-class", "socketio.worker.GunicornWorker", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "app:app"]
