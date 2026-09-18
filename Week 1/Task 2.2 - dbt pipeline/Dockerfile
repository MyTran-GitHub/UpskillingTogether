FROM python:3.11-slim

WORKDIR /app
COPY requirements-orchestrator.txt /tmp/requirements-orchestrator.txt
RUN pip install --no-cache-dir -r /tmp/requirements-orchestrator.txt

ENV PYTHONUNBUFFERED=1
ENV DAGSTER_HOME=/app/.dagster
