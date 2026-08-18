FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    libgeos-dev \
    libgomp1 \
    libproj-dev \
    proj-bin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY libraries/ libraries/
COPY __init__.py __init__.py
COPY services/route_pipelines/runtime_definitions/ runtime_definitions/

RUN mkdir -p \
    /app/data \
    /app/views/application/v1 \
    /app/views/application/v2 \
    /app/views/application/demo_bus_routes_nyc \
    /app/views/static/v1
