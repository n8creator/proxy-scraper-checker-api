# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV IS_DOCKER=1
ENV POETRY_CACHE_DIR="/var/cache/pypoetry"
ENV POETRY_VERSION=2.0.0

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cron \
    htop \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Copy the rest of the project files
COPY pyproject.toml poetry.lock ./
COPY proxy_scraper_checker/ ./proxy_scraper_checker/
COPY api/ ./api/
COPY config.toml start.sh ./

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Setup cron job
RUN echo "0 * * * * /app/start.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/proxy-scraper-cron \
    && chmod 0644 /etc/cron.d/proxy-scraper-cron \
    && crontab /etc/cron.d/proxy-scraper-cron

# Create log file
RUN touch /var/log/cron.log

# Create a directory for persistent storage
RUN mkdir -p /app/out

# Grant execute permission to start.sh
RUN chmod +x start.sh

# Start cron and FastAPI
CMD ["sh", "-c", "python -m api.main & /app/start.sh"]
