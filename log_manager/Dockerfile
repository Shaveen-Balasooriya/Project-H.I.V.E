# Use a slim Python base
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Install NATS client library
RUN pip install nats-py

# Copy publisher code
COPY publisher.py .

# Entry point
CMD ["python", "publisher.py"]
