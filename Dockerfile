FROM python:3.10-slim

# Install wkhtmltopdf and system dependencies for perfect rendering
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    fontconfig \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn --bind 0.0.0.0:$PORT app:app --workers 1 --threads 8 --timeout 120
