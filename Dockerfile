FROM gotenberg/gotenberg:8 AS gotenberg
FROM python:3.10-slim

# Copy Gotenberg/LibreOffice binaries and dependencies from official image
COPY --from=gotenberg /usr/bin/libreoffice /usr/bin/libreoffice
COPY --from=gotenberg /usr/lib/libreoffice /usr/lib/libreoffice

RUN apt-get update && apt-get install -y \
    libreoffice \
    default-jre \
    fontconfig \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn --bind 0.0.0.0:$PORT app:app --workers 1 --threads 8 --timeout 120
