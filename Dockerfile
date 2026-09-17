FROM python:3.10-slim

# Automatically accept Microsoft EULA for fonts installation
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula boolean true" | debconf-set-selections

# Install LibreOffice, Java, and Microsoft Core Fonts for exact layout matching
RUN apt-get update && apt-get install -y \
    libreoffice \
    default-jre \
    fontconfig \
    ttf-mscorefonts-installer \
    fonts-liberation \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn --bind 0.0.0.0:$PORT app:app --workers 1 --threads 8 --timeout 120
