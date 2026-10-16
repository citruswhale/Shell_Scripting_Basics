#!/bin/sh
# Container start-up: bring the database schema up to date, then start the API.
# alembic/env.py holds a Postgres advisory lock while migrating, so several
# replicas starting at once won't run the same migration twice.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting GearLoan API (version ${APP_VERSION:-unknown})..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --no-access-log
