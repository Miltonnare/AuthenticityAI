FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for compiling certs/builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy small English model
RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8000
