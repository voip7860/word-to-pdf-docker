FROM python:3.10-slim

# Install LibreOffice and essential fonts for proper table rendering
RUN apt-get update && apt-get install -y \
    libreoffice \
    default-jre \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn --bind 0.0.0.0:$PORT app:app --workers 1 --threads 8 --timeout 120
