FROM python:3.12-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Define volume for logs to persist outside the container
VOLUME ["/app/logs"]

CMD ["python", "main.py"]