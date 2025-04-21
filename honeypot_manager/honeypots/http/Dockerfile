FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirement and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy honeypot code into container
COPY . /app

# Expose the port (use 8080 or your config setting)
EXPOSE 8080

# Run the HTTP honeypot
CMD ["python", "main.py"]
