FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the honeypot application files
COPY main.py /app
COPY SSHServer.py /app

# Expose the port (documenting expected container port)
EXPOSE 22

# Run the honeypot application
CMD ["python", "main.py"]
