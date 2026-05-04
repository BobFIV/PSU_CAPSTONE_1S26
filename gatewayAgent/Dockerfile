# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Optional: system packages if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy gateway source code
COPY . .

# WORKDIR /app/gatewayAgent

# Environment variables for the gateway app
ENV PYTHONUNBUFFERED=1
# ENV APP_NAME=gatewayAgent
# ENV ORIGINATOR=CgatewayAgent
# ENV SUBSCRIPTION_NAME=gatewaySubscription
# ENV NOTIFY_PORT=9000


# Gateway notification server port
EXPOSE 9000

# Change this if your entry file is different
CMD ["python", "main.py"]