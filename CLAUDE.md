# CLAUDE.md – Holly Codebase Guide

This file gives an LLM agent orientation for working in the Holly repository.

---

## What Holly Does

Holly is an AI-assisted software development platform. Users create **missions** (scoped coding tasks) that run inside isolated Docker containers called **Hilly**. A SvelteKit frontend talks to a Django backend; the backend provisions containers, proxies MCP tool calls, and streams progress to the browser via SSE.

---

## Documentation Index

| Doc | What it covers |
|---|---|
| [`docs/overview.md`](docs/overview.md) | Architecture diagram, core concepts, tech stack, repo layout, mission lifecycle states |
| [`docs/backend.md`](docs/backend.md) | Django apps, models (Mission, Conversation, LLM, Tools), services, API endpoints, auth, Celery tasks, settings |
| [`docs/frontend.md`](docs/frontend.md) | SvelteKit routes, Svelte stores, API client generation, key components, build scripts |
| [`docs/flows.md`](docs/flows.md) | Step-by-step sequence diagrams: login, GitHub OAuth, mission start SSE, chat streaming, tool execution, teardown |
| [`docs/GH_APP_SETUP.md`](docs/GH_APP_SETUP.md) | GitHub App configuration for local development |

---

## Quick Orientation

### Three-Tier Architecture

```
SvelteKit :5173  ──REST+SSE──▶  Django :8000  ──Docker──▶  Hilly container
                                     │                        :8090 MCP API
                                     │                        :8181 AI Agent
                                     ▼
                               Redis / RabbitMQ / Celery
```

### Key Directories

```
backend/holly/holly/          ← core Django app
  models/mission.py           ← Mission model (states: draft→provisioning→ready→in_progress→completed)
  models/conversations.py     ← Message model (role: user|assistant|system|tool)
  models/llms.py              ← LLM configuration
  api/views/mission.py        ← mission CRUD + SSE /sse/start/
  api/views/conversations.py  ← chat endpoints + SSE stream
  api/proxy.py                ← MCPProxyClient (Django → Hilly container)
  services/mission_service.py ← lifecycle orchestration

frontend/src/
  routes/wizard/              ← 6-step mission creation wizard
  routes/sse-chat/            ← real-time chat UI
  lib/store/auth/             ← JWT token storage
  lib/store/chat/             ← active conversation + messages
  lib/apis/                   ← auto-generated + wrapper API clients

hilly/rest_mcp_client/        ← FastAPI server inside each container (:8090)
hilly/aiagents/               ← AI agent + MCP tools (git submodule)
```

---

## Mission Lifecycle

```
DRAFT → PROVISIONING → READY → IN_PROGRESS → COMPLETED
                                           → ABORTED
                                           → ERROR
```

- **DRAFT**: created via wizard, no container yet
- **PROVISIONING**: `GET /missions/{id}/sse/start/` called; Docker container spinning up
- **READY**: container healthy, repos cloned; SSE stream closes
- **IN_PROGRESS**: conversations happening, LLM working
- **COMPLETED/ABORTED/ERROR**: container stopped

---

## Authentication

- **JWT**: access token (5 min) + refresh token (7 days)
- SSE endpoints accept `?token=<jwt>` in query string (EventSource cannot set headers)
- GitHub OAuth via django-allauth → issues Holly JWT after callback
- Token refresh is automatic (frontend middleware retries on 401)

---

## Chat & Tool Execution

1. `POST /missions/{id}/conversation/` → get `conversation_id`
2. Open `EventSource` on `/conversations/{id}/sse/?token=<jwt>`
3. `POST /conversations/{id}/messages/` with user text
4. Django's `MCPProxyClient` forwards to `http://{container_ip}:8090`
5. Container's REST MCP API calls the AI Agent which calls the LLM
6. LLM tokens streamed back → Redis pub/sub → Django SSE → browser
7. Tool calls (git, bash, files) executed inside container; results returned inline

---

## Development Commands

### Backend
```bash
uv sync                                      # install Python deps
cd backend && uv run manage.py migrate       # run migrations
uv run manage.py populate_llms               # seed LLMs
uv run manage.py runserver                   # start Django :8000
uv run pytest                                # run tests
uv run ruff check . && uv run mypy .         # lint + type check
```

### Frontend
```bash
cd frontend && npm install
npm run dev:django           # dev server pointed at Django
npm run api:gen              # regenerate API client from OpenAPI spec
npm run test:unit            # Vitest
npm run test:integration     # Playwright
npm run lint && npm run check
```

### Hilly Container
```bash
cd hilly && git submodule update --init
./build_kasm.sh              # build hilly:latest image
```

### Full Stack (Docker Compose)
```bash
docker compose -f docker-compose.develop.yml up --build
```

---

## Environment Variables (`.env` in project root)

```bash
DJANGO_SETTINGS_MODULE=config.settings.local
SECRET_KEY=<django-secret>
GITHUB_APP_ID=<id>
GITHUB_APP_NAME=<name>
GITHUB_APP_PRIVATE_KEY_PATH=<path-to-.pem>
GITHUB_CLIENT_ID=<oauth-client-id>
GITHUB_CLIENT_SECRET=<oauth-client-secret>
ANTHROPIC_API_KEY=<key>       # optional – can be set per-user in UI
OPENAI_API_KEY=<key>          # optional
STRIPE_SECRET_KEY=<key>       # optional
```

---

## Code Conventions

- **Python**: PEP 8, 120-char line limit, type hints required, ruff + mypy enforced
- **TypeScript/Svelte**: strict mode, `$store` reactive syntax, TailwindCSS for styles
- **Git commits**: conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
- **Modules**: keep under 300 lines; split via inheritance/composition
- **Tests**: pytest (backend), Vitest + Playwright (frontend), Factory Boy for fixtures

---

## Common Tasks for an LLM Agent

| Task | Where to look |
|---|---|
| Add a new API endpoint | `backend/holly/holly/api/views/` + register in `api/router.py` |
| Add a new Django model | `backend/holly/holly/models/` + create migration |
| Change mission states | `mission.py` `State` enum + `mission_service.py` |
| Add a new Svelte route | `frontend/src/routes/<name>/+page.svelte` |
| Add a new Svelte store | `frontend/src/lib/store/<domain>/` |
| Modify chat SSE events | `api/views/conversations.py` + `SSEChat.svelte` |
| Change container env vars | `container_orchestrator.py` |
| Add an MCP tool | `hilly/aiagents/` + register in `models/tools.py` |
