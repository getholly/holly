# REST MCP Client

A REST API server that manages conversations with LLM models and Git operations for AI-powered development workflows.

## Features

### Conversation Management
- Start new conversations with optional titles
- Send messages to existing conversations
- List all conversations with metadata (ID, title, creation date, last update)
- Retrieve complete conversation history
- Store conversation history in a database
- Integration with LLM models

### Git Operations
- **Synchronous Git operations** (current mode - no Redis required)
  - Clone repositories with GitHub OAuth or GitHub App authentication
  - Create worktrees for branch isolation
  - Commit changes with customizable messages
  - Push changes to remote repositories
  - List repository branches
- **Async Git operations** (future - requires Redis + ARQ worker)
  - Job-based queue system for long-running operations
  - Webhook notifications on job completion
  - Job status tracking

### Container Self-Initialization
- Automatic repository cloning on container startup
- Environment-driven configuration via `MISSION_ID`, `MISSION_REPOS`, etc.
- Webhook integration with Django backend for status updates

## Endpoints

### Conversation API
- `GET /api/conversations`: Get a list of all conversations with metadata
- `GET /api/conversations/{conversation_id}`: Get a complete conversation by ID
- `POST /api/conversations/start`: Start a new conversation (can include title and initial message)
- `POST /api/conversations/{conversation_id}/messages`: Send a message to an existing conversation

### Git API (Synchronous)
- `POST /api/git/clone`: Clone a repository
- `POST /api/git/worktree`: Create a worktree
- `POST /api/git/commit`: Commit changes
- `POST /api/git/push`: Push changes
- `POST /api/git/pull`: Pull changes
- `POST /api/git/branches`: List repository branches

### Git API (Async - Disabled, requires Redis)
- `POST /api/repos/clone`: Queue a clone job
- `POST /api/repos/worktree`: Queue a worktree job
- `POST /api/repos/commit`: Queue a commit job
- `POST /api/repos/push`: Queue a push job
- `GET /api/repos/jobs/{job_id}`: Get job status

## Setup

### Running Locally

1. Install dependencies:
   ```bash
   cd /app/rest_mcp_client
   uv sync
   ```

2. Set environment variables:
   ```bash
   export BASE_DIR=/data
   ```

3. Run the application:
   ```bash
   uv run uvicorn rest_mcp_client.main:app --host 0.0.0.0 --port 8090
   ```

4. Access the API documentation at:
   ```
   http://localhost:8090/docs
   ```

### Running in Container

The service is automatically started via `custom_startup.sh`:
- REST API runs on port 8090
- ARQ worker is **disabled by default** (requires Redis)
- Container initialization runs if `MISSION_ID` env var is set

### Environment Variables

**Core Configuration:**
- `BASE_DIR` - Base directory for Git repositories (default: `/data`)
- `GIT_EMAIL` - Git commit email
- `GIT_USER` - Git commit username

**Mission Configuration (for auto-initialization):**
- `MISSION_ID` - Triggers container initialization
- `MISSION_REPOS` - Comma-separated "owner/repo:branch" specs
- `MISSION_BRANCH` - Branch to create (default: `main`)
- `AUTH_TOKEN` - GitHub authentication token
- `AUTH_TYPE` - Authentication type: `oauth` or `github_app` (default: `oauth`)
- `DJANGO_WEBHOOK_URL` - URL for status webhooks

**Redis Configuration (for async ARQ worker - currently disabled):**
- `REDIS_HOST` - Redis hostname (default: `localhost`)
- `REDIS_PORT` - Redis port (default: `6379`)

## Database

The application uses SQLite as its database. The database file is created in the root directory as `conversation.db`.

## LLM Integration

The current implementation contains a stub for LLM integration in `app/services/llm_service.py`. This should be replaced with an actual implementation to connect to your preferred LLM service.

## Testing

There are multiple ways to test the application:

### Running Manual Tests

To run the manual API tests:

```
uv run tests/test_api.py
```

This will test basic API functionality.

### Running Automated Tests with pytest

For comprehensive automated testing with pytest:

```
uv add pytest pytest-asyncio
uv run python -m pytest tests/
```

Or to run specific test files:

```
uv run python -m pytest tests/test_conversation_api.py
uv run python -m pytest tests/test_git_api.py
```

To run tests with coverage:

```
uv add pytest-cov
uv run python -m pytest --cov=rest_mcp_client tests/
```

For a detailed HTML coverage report:

```
uv run python -m pytest --cov=rest_mcp_client --cov-report=html tests/
```

The test suite covers all API endpoints including:
- Root endpoint validation
- Conversation management (create, list, get, send messages)
- Git operations (clone, commit, pull, push, branches)
- Server-Sent Events (SSE) endpoints

## Architecture

### Synchronous Mode (Current)
```
Container Start
    ↓
Start REST API (port 8090)
    ↓
If MISSION_ID set:
    ↓
Run init.py
    ↓
    - Wait for API ready (30 retries)
    - Parse MISSION_REPOS
    - Clone each repo via POST /api/git/clone (synchronous)
    - Send webhooks to Django
    ↓
Start AI Agent (port 8181)
```

### Async Mode (Future - Requires Redis)
```
Container Start
    ↓
Start Redis
    ↓
Start ARQ Worker
    ↓
Start REST API
    ↓
Queue clone jobs via POST /api/repos/clone
    ↓
ARQ worker processes jobs asynchronously
    ↓
Webhooks sent on completion
```

## Enabling Async Mode

To enable async job processing with ARQ worker:

1. Uncomment Redis service in `docker-compose.yml`
2. Uncomment ARQ worker lines in `custom_startup.sh`
3. Set Redis environment variables:
   ```yaml
   environment:
     - REDIS_HOST=redis
     - REDIS_PORT=6379
   ```
4. Rebuild and restart the container

The async endpoints (`/api/repos/*`) will then be available for job-based operations.
