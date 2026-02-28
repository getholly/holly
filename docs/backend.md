---
title: Holly – Backend Reference
scope: django, models, services, api, auth, celery, containers
audience: llm, developer
---

# Holly – Backend Reference

The backend is a Django 5 project in `backend/`. It exposes a REST API via **Django Ninja**, manages mission/container lifecycle, proxies MCP calls to Hilly containers, and handles GitHub OAuth and Stripe payments.

---

## Django App Map

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py        # shared settings
│   │   ├── local.py       # dev overrides
│   │   ├── develop.py     # docker-compose dev
│   │   └── production.py  # prod
│   ├── urls.py            # root URL router
│   └── wsgi.py / asgi.py
└── holly/
    ├── holly/             # core app  ← missions, conversations, llms, tools
    ├── github_ext/        # GitHub OAuth, App, repo management
    ├── users/             # custom User model (email-based)
    ├── payments/          # Stripe subscriptions
    ├── analytics/         # usage tracking
    ├── home/              # repository analysis / diagramming
    └── search_app/        # cross-entity search
```

---

## Models

### Mission (`holly/holly/models/mission.py`)

The central entity. UUID primary key.

```
Mission
├── id          UUID (PK)
├── title       CharField
├── description TextField
├── state       TextChoices → DRAFT | PROVISIONING | READY |
│                             IN_PROGRESS | COMPLETED | ABORTED | ERROR
├── owner       FK → User
├── collaborators  M2M → User
├── branch_name CharField  (shared across all repos)
├── repositories   M2M → MissionRepos
├── llm         FK → LLM
├── tools       M2M → Tools
├── knowledge_items M2M → Knowledge
├── container_id          CharField (Docker container ID)
├── container_ip_address  CharField
├── container_status      CharField (starting|ready|error|stopped)
├── container_started_at  DateTimeField
├── init_job_id           CharField (async bootstrap job)
├── active_jobs           JSONField
└── requirements          JSONField
```

**MissionRepos** – pivot between Mission and RepositoryDetail, also stores `branch_name`.

Key methods:
- `can_be_accessed_by(user)` – async permission check
- `is_container_ready()` – polls `GET /api/health` on container
- `get_tools()` – merges all tool configs into one dict
- `get_container_url(user)` – calls `mission_service.ensure_mission_container()`

### Conversation & Message (`holly/holly/models/conversations.py`, `mission_conversation.py`)

```
MissionConversation
├── mission     FK → Mission
└── conversation FK → Conversation

Conversation
└── id  UUID

Message
├── conversation  FK → Conversation
├── role          TextChoices → user | assistant | system | tool
├── content       TextField
├── tool_calls    JSONField
└── created_at    DateTimeField
```

### LLM (`holly/holly/models/llms.py`)

```
LLM
├── name        CharField
├── provider    TextChoices → openai | anthropic | google | local
├── model_id    CharField  (e.g. "claude-opus-4-6")
├── is_system   BooleanField  (pre-seeded vs user-defined)
├── api_key     encrypted field (optional – overridden by UserLLMApiKey)
└── config      JSONField  (extra params, temperature etc.)
```

`UserLLMApiKey` stores per-user API keys linked to a provider.

### Tools (`holly/holly/models/tools.py`)

```
Tools
├── name    CharField
├── config  JSONField  (MCP server config merged into agent tool list)
└── is_system BooleanField
```

### Knowledge (`holly/holly/models/knowledge.py`)

```
Knowledge
├── title   CharField
├── content TextField  (injected into LLM system prompt)
└── owner   FK → User
```

### GitHub models (`holly/github_ext/models.py`)

```
RepositoryDetail
├── repo_name   CharField
├── owner       CharField
├── github_url  URLField
└── installation FK → GitHubAppInstallation

GitHubAppInstallation
├── installation_id  IntegerField
├── account_login    CharField
└── user  FK → User
```

---

## Services

### MissionService (`holly/holly/services/mission_service.py`)

Singleton `mission_service`. All mission lifecycle operations.

```python
mission_service.create_mission(user, data)     # → Mission (DRAFT)
mission_service.start_mission(mission)         # DRAFT → PROVISIONING
mission_service.stop_mission(mission)          # any → ABORTED
mission_service.ensure_mission_container(id, user)  # idempotent start
```

### ContainerOrchestrator / HollyContainerService

```
ContainerOrchestrator
  └── HollyContainerService
        ├── create_container(mission)   → docker run hilly:latest
        ├── start_container(id)
        ├── stop_container(id)
        ├── get_container_ip(id)
        └── wait_for_health(ip, port, timeout)
```

Container is created with environment variables:

```
MISSION_ID=<uuid>
MISSION_REPOS=owner/repo:branch,...
AUTH_TOKEN=<github_token>
DJANGO_WEBHOOK_URL=http://host:8000/_api/holly/webhooks/container/
```

### CaddyManager (`holly/holly/services/caddy_manager.py`)

Dynamically manages Caddy reverse proxy routes to expose per-container web UIs (noVNC) on dynamic subdomains.

### SummaryService (`holly/holly/services/summary_service.py`)

Calls an LLM to generate a `title` and `branch_name` from the mission description before the container starts.

### MCPProxyClient (`holly/holly/api/proxy.py`)

Forwards REST calls from Django → Hilly container REST MCP API.

```python
class MCPProxyClient:
    base_url: str  # http://{container_ip}:8090

    async def send_message(conversation_id, message, tools, llm_config)
    async def create_conversation(mission_id)
    async def get_conversation(conversation_id)
    async def stream_response(conversation_id) → AsyncGenerator[SSE chunks]
```

---

## API Endpoints (Django Ninja)

All routes under `/_api/`. JWT required on all except auth endpoints.

### Auth (`/_api/auth/`)

| Method | Path | Description |
|---|---|---|
| POST | `/token/` | Email + password → access + refresh tokens |
| POST | `/token/refresh/` | Rotate access token |
| POST | `/register/` | Create account |
| GET | `/github/` | Redirect to GitHub OAuth |
| GET | `/github/callback/` | Handle OAuth callback, issue JWT |

### Missions (`/_api/holly/missions/`)

| Method | Path | Description |
|---|---|---|
| GET | `/` | List user's missions |
| POST | `/` | Create mission (DRAFT) |
| GET | `/{id}/` | Get mission detail |
| PATCH | `/{id}/` | Update mission |
| DELETE | `/{id}/` | Delete mission |
| GET | `/{id}/sse/start/` | **SSE** – start container, stream boot events |
| POST | `/{id}/stop/` | Stop container |
| POST | `/{id}/conversation/` | Create new conversation on this mission |

### Conversations (`/_api/holly/conversations/`)

| Method | Path | Description |
|---|---|---|
| GET | `/{id}/` | Get conversation + messages |
| GET | `/{id}/sse/` | **SSE** – subscribe to streaming response |
| POST | `/{id}/messages/` | Send user message → proxied to container |
| DELETE | `/{id}/` | Delete conversation |

### LLMs (`/_api/holly/llms/`)

| Method | Path | Description |
|---|---|---|
| GET | `/` | List available LLMs |
| POST | `/` | Create custom LLM |
| GET | `/{id}/` | LLM detail |
| DELETE | `/{id}/` | Delete |
| GET | `/api-keys/` | List user API keys |
| POST | `/api-keys/` | Store API key for provider |

### GitHub (`/_api/github/`)

| Method | Path | Description |
|---|---|---|
| GET | `/status/` | Connection status |
| GET | `/installations/` | App installations |
| GET | `/repositories/` | Repos accessible via app |
| POST | `/webhooks/` | Receive GitHub webhooks |

### Webhooks (`/_api/holly/webhooks/`)

| Method | Path | Description |
|---|---|---|
| POST | `/container/` | Hilly container status callbacks |

---

## Authentication Flow (JWT + GitHub OAuth)

```
Browser                     Django                      GitHub
  │                            │                            │
  │──POST /auth/token/─────────▶│                            │
  │   {email, password}        │ validate → issue JWT       │
  │◀──{access, refresh}────────│                            │
  │                            │                            │
  │── GET /auth/github/ ───────▶│                            │
  │◀──302 redirect─────────────│──────────────────────────▶│
  │                            │                            │ user approves
  │                            │◀── callback + code ───────│
  │                            │ exchange code for token    │
  │                            │ create/link SocialAccount  │
  │◀── 302 /dashboard #token ──│                            │
```

JWT tokens:
- Access token: short-lived (default 5 min)
- Refresh token: long-lived (default 7 days)
- Stored in frontend via `js-cookie`
- SSE endpoints accept token as query param `?token=<jwt>` (EventSource doesn't support headers)

---

## SSE Streaming Pattern

Mission start and conversation reply both use the same pattern:

```python
# backend/holly/holly/api/views/mission.py (simplified)
@router.get("/{id}/sse/start/", auth=None)
async def start_mission_sse(request, id: UUID, token: str):
    user = await validate_jwt_token(token)
    mission = await get_mission(id, user)

    async def event_stream():
        # 1. publish events to Redis channel
        await mission_service.start_mission(mission)
        # 2. subscribe and yield to client
        async for event in redis.subscribe(f"mission:{id}:events"):
            yield f"data: {event}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
```

Redis channel naming:
- Mission events: `mission:{uuid}:events`
- Conversation streaming: `conversation:{uuid}:stream`

---

## Background Tasks (Celery)

Celery workers connect to RabbitMQ. Key tasks:

| Task | Trigger |
|---|---|
| `clone_repository` | Mission start – clone each repo into container |
| `generate_mission_title` | Post-creation – LLM summary |
| `cleanup_stopped_containers` | Scheduled – remove stale containers |
| `process_github_webhook` | GitHub webhook received |

---

## Settings Reference

Key settings in `config/settings/base.py`:

```python
REST_MCP_SERVER_PORT = 8090       # port inside Hilly container
AI_AGENT_PORT = 8181              # AI agent port in container
HILLY_IMAGE = "hilly:latest"      # Docker image name
HILLY_NETWORK = "holly_network"   # Docker network
CADDY_API_URL = "http://caddy:2019"

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}
```

---

## Management Commands

```bash
uv run manage.py populate_llms      # seed default LLM configurations
uv run manage.py populate_tools     # seed default MCP tool configurations
uv run manage.py populate_knowledge # seed example knowledge entries
uv run manage.py createsuperuser    # create admin account
```

---

## Key File Index

| File | Purpose |
|---|---|
| `config/settings/base.py` | All shared Django settings |
| `config/urls.py` | Root URL router, mounts Ninja API |
| `holly/holly/models/mission.py` | Mission + MissionRepos models |
| `holly/holly/models/conversations.py` | Message model |
| `holly/holly/models/llms.py` | LLM configuration model |
| `holly/holly/api/views/mission.py` | Mission CRUD + SSE start |
| `holly/holly/api/views/conversations.py` | Chat + SSE streaming |
| `holly/holly/api/proxy.py` | MCPProxyClient |
| `holly/holly/services/mission_service.py` | Mission lifecycle |
| `holly/holly/services/containers/holly_container_service.py` | Docker management |
| `holly/holly/services/caddy_manager.py` | Reverse proxy routes |
| `holly/github_ext/models.py` | GitHub App + repo models |
| `holly/users/models.py` | Custom User model |
