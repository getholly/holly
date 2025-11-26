#!/bin/bash
# Start Celery worker for the Holly project

# Load environment variables
if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Celery worker with info log level
echo "Starting Celery worker..."
celery -A config worker -l info --concurrency=4
