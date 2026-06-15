#!/usr/bin/env bash
#
# Container entrypoint for the Holly web service.
# Runs database migrations, collects static assets, then serves the ASGI app.
set -euo pipefail

# Resolve repo root relative to this script and run from the Django project dir.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../backend"

PORT="${PORT:-8181}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-2}"

echo "Running database migrations..."
uv run python manage.py migrate --noinput

# Static collection is best-effort: in production static is served from object
# storage/CDN, so a failure here should not prevent the service from starting.
echo "Collecting static files..."
uv run python manage.py collectstatic --noinput || echo "WARNING: collectstatic failed; continuing"

echo "Starting ASGI server on 0.0.0.0:${PORT} (${WEB_CONCURRENCY} workers)..."
exec uv run uvicorn config.asgi:application \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers "${WEB_CONCURRENCY}"
