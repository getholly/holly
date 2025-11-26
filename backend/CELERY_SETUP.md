# Celery Background Tasks for Mission Repository Cloning

This implementation adds Celery-based background task processing for cloning repositories when a mission container is started.

## Architecture

- **Message Broker**: RabbitMQ
- **Results Backend**: Redis
- **Real-time Updates**: Server-Sent Events (SSE) via Redis Pub/Sub

## Setup Instructions

### 1. Install RabbitMQ and Redis

```bash
# Install RabbitMQ
sudo apt-get update
sudo apt-get install rabbitmq-server

# Start RabbitMQ
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 2. Environment Configuration

The `.env.local` file has been updated with:

```env
`CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/0`
```

### 3. Run Database Migrations

```bash
cd /data/holly
python manage.py migrate django_celery_results
```

### 4. Start Services

Start the services in separate terminals:

```bash
# Terminal 1: Start Django development server
cd /data/holly
python manage.py runserver

# Terminal 2: Start Celery worker
cd /data/holly
./start_celery_worker.sh

# Terminal 3: Start Celery Beat (for periodic tasks)
cd /data/holly
./start_celery_beat.sh
```

## How It Works (Git-Flow V1.1 Architecture)

1. When `start_mission_container()` is called in `MissionService`, it:
   - Starts the Docker container with environment variables (MISSION_ID, MISSION_REPOS, etc.)
   - Updates the mission with the container ID
   - Container self-initializes asynchronously

2. Container Self-Initialization (`init.py`):
   - Waits for REST API to be ready
   - Creates async clone jobs for each repository via `/api/git/repos`
   - Sends initialization webhook to Django
   - ARQ workers execute jobs in the background

3. Real-time Updates via Webhooks + SSE:
   - Container sends webhooks to Django on job completion/failure
   - Django updates mission state (PROVISIONING → READY)
   - Updates published to Redis Pub/Sub for SSE
   - Frontend connects to `/api/holly/missions/{mission_id}/clone-status/stream`
   - Frontend can also poll `/api/holly/missions/{mission_id}/jobs/{job_id}` for status

## API Endpoints

### SSE Endpoint for Clone Status
```
GET /api/holly/missions/{mission_id}/clone-status/stream
```

Returns Server-Sent Events stream with status updates:
- `started`: Clone process started
- `progress`: Repository being cloned
- `completed`: All repositories cloned successfully
- `failed`: Some or all repositories failed to clone

## Frontend Integration

Use the `CloneStatusMonitor` component:

```svelte
<script>
  import CloneStatusMonitor from '$lib/components/mission/CloneStatusMonitor.svelte';
</script>

<CloneStatusMonitor missionId={mission.id} />
```

## Monitoring

### Check Celery Worker Status
```bash
celery -A config inspect active
```

### Monitor Redis Pub/Sub
```bash
redis-cli
> SUBSCRIBE mission:*:clone_status
```

### View Celery Results
```bash
python manage.py shell
>>> from django_celery_results.models import TaskResult
>>> TaskResult.objects.all()
```

## TODO

1. **Implement actual git clone API call**: The task currently simulates cloning. Need to implement the actual HTTP request to the container's git API.

2. **Add authentication token handling**: Pass the GitHub auth token securely to the clone task.

3. **Implement retry logic**: Add intelligent retry with exponential backoff for failed clones.

4. **Add webhook support**: Allow webhook callbacks when cloning is complete.

5. **Progress persistence**: Store clone progress in database for recovery after failures.

## Troubleshooting

### RabbitMQ Connection Issues
```bash
# Check RabbitMQ status
sudo systemctl status rabbitmq-server

# Check RabbitMQ logs
sudo journalctl -u rabbitmq-server

# Reset RabbitMQ (if needed)
sudo rabbitmqctl stop_app
sudo rabbitmqctl reset
sudo rabbitmqctl start_app
```

### Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping
```

### Celery Worker Not Processing Tasks
```bash
# Check Celery logs
celery -A config worker -l debug

# Purge all pending tasks
celery -A config purge
```
