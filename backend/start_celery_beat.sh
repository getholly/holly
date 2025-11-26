#!/bin/bash
# Start Celery Beat scheduler for the GitHubMe project

# Load environment variables
if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Celery Beat
echo "Starting Celery Beat scheduler..."
celery -A config beat -l info
