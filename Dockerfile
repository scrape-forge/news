# ==========================================
# STAGE 1: Builder (compile & install dependencies for Prod)
# ==========================================
FROM python:3.11-alpine AS builder

WORKDIR /build

# Install temporary build headers for C-extensions
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    libxml2-dev \
    libxslt-dev \
    postgresql-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================================
# STAGE 2: Development Stage (Loads local .venv)
# ==========================================
FROM python:3.13-slim AS dev

WORKDIR /app

# Install runtime C libraries for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Activate local mounted virtualenv (.venv)
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Jakarta

CMD ["python", "runner.py"]

# ==========================================
# STAGE 3: Production Base Runtime (Clean, ~45MB)
# ==========================================
FROM python:3.11-alpine AS prod-base

WORKDIR /app

# Install runtime C libraries only (no compiler tools)
RUN apk add --no-cache \
    libpq \
    libxml2 \
    libxslt \
    libffi \
    tzdata

# Copy pre-built site-packages from builder
COPY --from=builder /install /usr/local

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Jakarta

# ==========================================
# STAGE 4: Production Stage (Built-in code)
# ==========================================
FROM prod-base AS prod

# Copy application source code directly into image
COPY . /app

CMD ["python", "runner.py"]
