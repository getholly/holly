/usr/bin/desktop_ready
echo "========= Starting services at `date`"

git config --global user.email $GIT_EMAIL
git config --global user.name $GIT_USER

echo "******************* Starting rest_mcp_client at `date`"
cd /app/rest_mcp_client
echo "BASE_DIR=/data" > /app/rest_mcp_client/.env

# Start ARQ worker for async jobs (DISABLED - requires Redis)
# Uncomment when Redis is available:
# echo "******************* Starting ARQ worker at `date`"
# uv run arq rest_mcp_client.workers.git_worker.WorkerSettings &

# Start REST API
echo "******************* Starting REST API at `date`"
uv run uvicorn rest_mcp_client.main:app --host 0.0.0.0 --port 8090 --app-dir /app/rest_mcp_client &

# Run container initialization if MISSION_ID is set
if [ ! -z "$MISSION_ID" ]; then
    echo "******************* Running container initialization at `date`"
    # Init script has built-in API wait logic (30 retries x 1 sec)
    # Configure git identity if provided
    if [ ! -z "$GIT_EMAIL" ]; then
        git config --global user.email "$GIT_EMAIL"
    fi
    if [ ! -z "$GIT_USER" ]; then
        git config --global user.name "$GIT_USER"
    fi
    uv run python -m rest_mcp_client.init
fi

echo "****************************** Starting AIAgent `date`"
cd /app/aiagents
uv run fastapi run remote_server.py --host 0.0.0.0 --port 8181

