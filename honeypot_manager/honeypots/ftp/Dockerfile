FROM python:3.12-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

# Create malware directory with proper permissions
RUN mkdir -p /app/malware && chmod 755 /app/malware

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Define volumes for malware files and logs to persist outside the container
VOLUME ["/app/malware", "/app/logs"]

# Expose FTP port
EXPOSE 21 60000-65535

CMD ["python", "main.py"]