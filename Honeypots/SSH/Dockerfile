FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install paramiko

# Copy the honeypot script
COPY ssh.py /app/

# Expose the SSH port
EXPOSE 2222

# Run the honeypot
CMD ["python", "ssh.py"]