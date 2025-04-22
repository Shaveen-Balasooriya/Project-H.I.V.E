FROM python:3.11-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Define volume for logs to persist outside the container
VOLUME ["/app/logs"]

ENV NATS_URL="nats://host.containers.internal:4222"

CMD ["python", "main.py"]