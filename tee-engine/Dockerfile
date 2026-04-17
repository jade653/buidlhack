FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install minimal system packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files.
COPY engine ./engine
COPY docs ./docs
COPY README.md ./

# Default command for container readiness check.
# Replace with your API server/worker command in production.
CMD ["python", "-c", "from engine.runner import run_submission; print('tee-engine image is ready')"]
