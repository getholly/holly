---
title: Holly – System Overview
scope: architecture, concepts, stack, deployment
audience: llm, developer
---

# Holly – System Overview

Holly is an AI-assisted software development workspace. Engineers hand off scoped coding **missions** to LLMs. Each mission runs inside an isolated Docker container (**Hilly**) where the model can clone repositories, edit code, run tests, and push changes – all without touching the host machine.

The UI streams real-time progress back via Server-Sent Events (SSE). Any frontier or local LLM can be used, and the container image can be swapped for a hardened alternative.

> **Security warning:** The default Hilly image runs with `privileged: true` to support VNC. Do not expose this on a publicly accessible host without hardening the container.

---

## High-Level Architecture

```mermaid
graph TB
    User["User (browser)"]

    subgraph "Frontend – SvelteKit :5173"
        FE[Pages / Wizard / Chat]
        STORES[Svelte Stores]
        API_CLIENT[Auto-gen API Client]
    end

    subgraph "Backend – Django :8000"
        NINJA[Django Ninja REST API]
        AUTH[JWT Auth]
        SERVICES[Mission / Container Services]
        DB[(SQLite / PostgreSQL)]
        REDIS[(Redis)]
        CELERY[Celery Worker]
    end

    subgraph "Hilly Container (per mission)"
        REST_MCP[REST MCP API :8090]
        AI_AGENT[AI Agent API :8181]
        VNC[KasmVNC :6080]
        GIT[Git Operations]
    end

    subgraph "External"
        GITHUB[GitHub API]
        LLM_CLOUD[LLM Providers\nClaude / GPT / Gemini]
        STRIPE[Stripe]
    end

    User --> FE
    FE --> STORES --> API_CLIENT
    API_CLIENT -->|REST + SSE| NINJA
    NINJA --> AUTH
    NINJA --> SERVICES
    SERVICES --> DB
    SERVICES --> REDIS
    SERVICES --> CELERY
    SERVICES -->|Docker SDK| Hilly Container
    REST_MCP --> GIT --> GITHUB
    AI_AGENT --> LLM_CLOUD
    NINJA -->|proxy MCP calls| REST_MCP
    NINJA --> GITHUB
    NINJA --> STRIPE
```

---

## ASCII Deployment View

```
┌─────────────────────────────────────────────────────────────┐
│  Host Machine                                               │
│                                                             │
│  ┌──────────────┐   ┌───────────────────────────────────┐  │
│  │  Caddy :80   │   │  Django :8000  +  SvelteKit :5173 │  │
│  │  Reverse     │──▶│  Redis  :6379  +  RabbitMQ :5672  │  │
│  │  Proxy       │   └──────────────────┬────────────────┘  │
│  └──────────────┘                      │ Docker SDK         │
│                                        ▼                    │
│                          ┌────────────────────────┐         │
│                          │  Hilly Container        │         │
│                          │  (per mission)          │         │
│                          │  :8090 REST MCP         │         │
│                          │  :8181 AI Agent         │         │
│                          │  :6080 noVNC            │         │
│                          └────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

| Concept | Description |
|---|---|
| **Mission** | A scoped coding task (feature, bugfix, refactor). Has state, repos, LLM, tools, knowledge. |
| **Hilly** | Per-mission Docker container. Ubuntu + Xfce + VNC + REST API + AI agent. |
| **MCP (Model Context Protocol)** | Protocol used by the AI agent inside Hilly to invoke tools (git, shell, file ops). |
| **MCP Proxy** | Django's `MCPProxyClient` forwards tool calls from the LLM to the running container. |
| **SSE** | Server-Sent Events used for real-time streaming (mission boot progress, chat tokens). |
| **Conversation** | A chat thread linked to a mission. Many conversations per mission are allowed. |
| **Knowledge** | User-defined context snippets fed to the LLM system prompt. |
| **Tools** | MCP server configurations (git, shell, file system) made available per mission. |

---

## Mission Lifecycle

```
DRAFT
  │  wizard complete, POST /missions/
  ▼
PROVISIONING
  │  Docker container starting, repos cloning
  ▼
READY
  │  container healthy, repos on disk
  ▼
IN_PROGRESS
  │  user chatting, LLM writing code
  ▼
COMPLETED ─── or ─── ABORTED ─── or ─── ERROR
```

---

## Technology Stack

### Backend
| Layer | Technology |
|---|---|
| Web framework | Django 5.1.5 |
| REST API | Django Ninja (OpenAPI auto-docs) |
| Authentication | django-allauth + simplejwt |
| Background tasks | Celery + RabbitMQ |
| Cache / pub-sub | Redis |
| Container mgmt | Docker SDK for Python |
| Reverse proxy | Caddy |
| DB | SQLite (dev) / PostgreSQL (prod) |
| HTTP client (async) | httpx |
| Payments | Stripe |

### Frontend
| Layer | Technology |
|---|---|
| Framework | SvelteKit 2 + TypeScript |
| Styling | TailwindCSS + Flowbite |
| API client | Auto-generated from OpenAPI spec |
| Real-time | EventSource (SSE) |
| Unit tests | Vitest |
| E2E tests | Playwright |
| Build | Vite |

### Hilly Container
| Layer | Technology |
|---|---|
| Base image | Ubuntu 22.04 + KasmVNC |
| REST API | FastAPI (port 8090) |
| AI Agent | Custom agent + MCP tools (port 8181) |
| Runtime | Python 3.11 (uv), Node.js, Git |

---

## Repository Layout

```
holly/
├── backend/              # Django project
│   ├── config/           #   settings, URLs, WSGI
│   └── holly/            #   Django apps
│       ├── holly/        #     missions, conversations, LLMs, tools
│       ├── github_ext/   #     GitHub OAuth & app integration
│       ├── users/        #     custom User model
│       └── payments/     #     Stripe subscriptions
├── frontend/             # SvelteKit app
│   └── src/
│       ├── routes/       #   pages
│       └── lib/          #   stores, components, API wrappers
├── hilly/                # AI agent Docker image
│   ├── rest_mcp_client/  #   FastAPI REST MCP server
│   └── aiagents/         #   AI agent + MCP tooling (git submodule)
├── docs/                 # LLM-optimised documentation (this folder)
├── scripts/              # Setup helpers (GitHub app, secrets)
└── tests/                # Top-level integration tests
```

---

## Related Docs

- [`docs/backend.md`](backend.md) – Django apps, models, services, API endpoints
- [`docs/frontend.md`](frontend.md) – SvelteKit routes, stores, components
- [`docs/flows.md`](flows.md) – Auth, mission start, chat, tool execution flows
- [`docs/GH_APP_SETUP.md`](GH_APP_SETUP.md) – GitHub App configuration
