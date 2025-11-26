# Holly

Holly is an AI-assisted software development workspace that lets engineers hand off scoped coding "missions" to large language models (LLMs). 

You can spin this up as a webserver with the ultimate goal to be able to send coding tasks on your mobile. 

The product combines a Svelte front end with a Django-based application layer that provisions isolated Docker workspaces, connects to GitHub(Gitlab and others in the pipeline), and streams mission progress back to the UI. LLMs operate inside hardened containers where they can edit, run, and test code. 

Swap out the backend docker container with your own setup and work safe in the knowledge that your LLM will be safely contained away from your main OS. 

Use any open source or frontier model, on cloud or locally deployed. 

---

## Quick Start

### 1. Backend

```bash
uv sync
cd backend
uv run manage.py migrate
uv run manage.py populate_llms  
uv run manage.py populate_tools # optional
uv run manage.py populate knowledge # optional
uv run manage.py runserver
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev:django  # or npm run dev:django:bash
```

Copy `frontend/env.example` to `frontend/.env`; it already references the correct local URLs.

### 3. GitHub App Configuration

With the backend and frontend running, run the setup script to create your GitHub App (it uses the callback URL which requires the servers):

```bash
Setup a GitHub App that will allow django/llm to clone repos: 

# Linux/macOS
./scripts/setup_github_app.sh

# Cross-platform (Python)
uv run scripts/setup_github_app.py
```

The script will:
1. Create a GitHub App for local development
2. Generate a private key (saved to `.github-app-keys/`)
3. Output environment variables to add to your `.env` file

Copy the output to `holly/.env` (the backend reads `.env` from the **project root**):
```bash
# GitHub App Settings (from setup script output)
GITHUB_APP_ID=123456
GITHUB_APP_NAME=holly-local-dev-username-20251109
GITHUB_APP_PRIVATE_KEY_PATH=/path/to/holly/.github-app-keys/app-name.pem

# OAuth Settings (from setup script output)
GITHUB_CLIENT_ID=Iv1.abc123def456
GITHUB_CLIENT_SECRET=abc123def456ghi789jkl012

# Django Settings
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
```

Restart the backend after updating `.env`, then visit the GitHub App installations page to connect your account and authorize the app on your repositories.

### 4. Hilly Container (AI Agent Workspace)

The Hilly container provides the isolated environment where AI agents clone repositories and execute code. Django creates these containers on demand when missions start—you just need to build the image so it's ready.

**Initialize the git submodule** (required for the `aiagents` code):

```bash
cd hilly
git submodule init
git submodule update
```

**Build the Docker image:**

```bash
cd hilly
./build_kasm.sh
# Or directly: docker build -t hilly:latest .
```

That's it! The Django backend will spin up Hilly containers automatically when you start a mission.

### 5. Mission Creation (Coding Agent)

1. Ensure Docker is running and the Hilly image is built.
2. Configure an LLM and add its API keys (unless you are using a local model).
3. Open the dashboard, launch the wizard, and select the repository, model, and any additional tools or knowledge sources for the mission.
4. Write a clear mission description, e.g., "Build the basic layout and functionality of a calculator app."
5. The system will create a container, clone the repo, and start an agent dedicated to that mission.
6. Begin a conversation with the agent and assign a task such as "Create the layout and functionality of the calculator app."
7. The agent works inside the container and reports back as soon as the task is complete.

---

## High-Level Architecture

### Frontend (Svelte + Vite)
- SvelteKit application styled with TailwindCSS and Flowbite components lives in [`frontend/`](frontend/). Authentication, repo browsing, and mission orchestration screens consume the auto-generated `holly-api` TypeScript client to call the Django REST/Ninja endpoints.
- Real-time updates rely on server-sent events (SSE). Mission start requests subscribe to `/_api/holly/missions/sse/start/{mission_id}` so the UI can render container boot progress and Git operations without a page refresh.
- The project ships with Vite tooling, linting, Playwright integration tests, and Vitest unit tests. Convenience scripts keep the generated OpenAPI client in sync with the backend.

### Backend (Django + Ninja API)
- The [`backend/`](backend/) Django project powers authentication, GitHub App integration, payments, and the Holly domain models. Mission CRUD, collaboration, and conversation endpoints are exposed through Django Ninja routers secured with JWT auth.
- Mission lifecycle events stream to clients over SSE. When a mission starts, Django coordinates container provisioning and publishes cloning status via Redis, allowing the front end to react instantly.
- Long-running GitHub analysis tasks run asynchronously using a lightweight task runner that records status in Django's cache, providing polling APIs for repository diagramming and analysis jobs.
- Celery workers, Redis, and RabbitMQ support background orchestration for clone pipelines, notifications, and scheduled maintenance.

### LLM Workspaces & Mission Containers
- Mission execution happens inside [`hilly/`](hilly/), an Ubuntu-based image that bundles a VNC desktop, Claude desktop client, and two REST services: `rest_mcp_client` and `aiagents`. These services expose MCP tooling so the LLM has terminal-level access to the cloned repository while keeping each mission isolated.
- The Django API proxies MCP requests through `MCPProxyClient`, merging per-mission tool configuration and forwarding calls to the running container's REST endpoints.

---

## GitHub Integration & Authentication Flow
- GitHub OAuth is handled through Django's authentication system: users are redirected to GitHub, access tokens are exchanged, and a signed JWT cookie is issued so the Svelte app can authenticate subsequent API calls.
- The `github_ext` app (in `backend/holly/github_ext/`) manages installations, repository listings, and webhook processing required by the Holly missions. The front end consumes these endpoints to list repositories and track installation status before a mission is created.

---

## Mission Lifecycle Overview
1. **Connect GitHub** – After OAuth completes, the user can initiate a GitHub App installation and load accessible repositories straight from the UI.
2. **Define a Mission** – Mission creation captures repositories, collaborators, knowledge base entries, tooling requirements, and the preferred LLM. Django persists the mission and derives a working branch name from an LLM-generated summary.
3. **Start Execution** – Starting a mission triggers container provisioning. SSE updates report container status, clone progress, and readiness so users can monitor the mission in real time.
4. **Collaborate & Chat** – Mission conversations spin up via the MCP proxy, allowing streaming chat between users and the LLM against the live repository context.
5. **Complete & QA** – When the mission wraps, Django tears down the container and Caddy routes can be removed or repointed. QA teams can exercise web front ends hosted in the mission container via the dynamic subdomains created earlier.

---

## Prerequisites
- Python 3.11 with [uv](https://docs.astral.sh/uv/) for dependency management (installed inside the Docker image as well).
- Node.js 22.x via NVM for the Svelte workspace.
- Docker/Docker Compose for mission containers and supporting infrastructure.

---

## Running the Full Stack with Docker Compose
- Copy the appropriate `.env.develop` or `.env.production` file and update secrets or run either `setup_gh_vars.sh` or `setup_gh_vars.py`
- `docker compose -f docker-compose.develop.yml up --build` starts the Django app, Redis, RabbitMQ, Celery workers. Production deployments rely on `docker-compose.yml` which mounts persistent volumes for databases, logs, and cloned repositories.

---

## Testing & Quality Checks
- Backend: `uv run pytest` exercises the Django test suite (pytest + pytest-django) with Factory Boy and Faker fixtures enabled via project dependencies.
- Frontend: `npm run test` executes Vitest unit tests and Playwright integration tests; `npm run lint` and `npm run check` cover formatting, ESLint, and Svelte diagnostics.
- Static analysis: `uv run ruff check` and `uv run mypy` enforce the repository's linting and typing policies.

---

## Additional Resources
- [`backend/readme.md`](backend/readme.md) – backend environment setup tips.
- [`CLAUDE.md`](CLAUDE.md) – notes on the Claude-powered agent workflows.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) – contribution guidelines, architecture diagrams, and development setup.
- [`CONVENTIONS.md`](CONVENTIONS.md) – coding conventions, Svelte store patterns, and Python linting guides.
- [`USER_GUIDE.md`](USER_GUIDE.md) – comprehensive user guide for Holly.
- [`scripts/README_GITHUB_SECRETS.md`](scripts/README_GITHUB_SECRETS.md) – detailed GitHub secrets setup script documentation.
