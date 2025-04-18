FROM python:3.11-slim

WORKDIR /app

# Copy all files from the current directory (which is honeypots/ssh)
COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]