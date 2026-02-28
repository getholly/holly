---
title: Holly – Key Data Flows
scope: auth, mission-lifecycle, chat, tool-execution, sse, github-oauth
audience: llm, developer
---

# Holly – Key Data Flows

This document traces the critical paths through the system: authentication, mission creation and start, the chat/SSE cycle, and tool execution inside the Hilly container.

---

## 1. Authentication Flow

### 1a. Email / Password Login

```
Browser (Svelte)             Django                    DB
     │                          │                       │
     │─POST /auth/token/────────▶│                       │
     │  {email, password}       │─SELECT User──────────▶│
     │                          │◀─User─────────────────│
     │                          │ bcrypt verify          │
     │                          │ sign JWT (access+refresh)
     │◀─{access, refresh}───────│                       │
     │  store in js-cookie      │                       │
     │                          │                       │
     │  [subsequent requests]   │                       │
     │─GET /missions/───────────▶│                       │
     │  Authorization: Bearer   │ JWTAuth.authenticate() │
     │  <access>                │                       │
```

### 1b. GitHub OAuth Login

```
Browser          Django          GitHub          DB
  │                 │               │              │
  │─GET /auth/─────▶│               │              │
  │  github/        │──302 redirect─▶│              │
  │◀────────────────│  to github.com │              │
  │                                 │              │
  │  user approves OAuth app        │              │
  │◀────302 /auth/github/callback?──│              │
  │       code=<code>&state=...     │              │
  │─GET callback────▶│              │              │
  │                  │─POST oauth/─▶│              │
  │                  │   token      │              │
  │                  │◀─access_tok──│              │
  │                  │ create/link SocialAccount ──▶│
  │                  │ issue Holly JWT              │
  │◀─302 /dashboard──│              │              │
  │  #access=<jwt>   │              │              │
  │  store tokens    │              │              │
```

### 1c. JWT Refresh (automatic, via middleware)

```
Browser (API middleware)      Django
  │                              │
  │─GET /some/endpoint/──────────▶│  ← access token expired
  │◀─401 Unauthorized────────────│
  │                              │
  │─POST /auth/token/refresh/────▶│
  │  {refresh: <refresh_token>}  │
  │◀─{access: <new_access>}──────│
  │  update tokens store         │
  │                              │
  │─GET /some/endpoint/ (retry)──▶│  ← new access token
  │◀─200 OK──────────────────────│
```

---

## 2. Mission Creation Flow

### 2a. Wizard → Mission Record

```
Browser                           Django
  │                                  │
  │  [Wizard step 6 – submit]        │
  │─POST /_api/holly/missions/───────▶│
  │  {description, repos, llm_id,    │
  │   tools, knowledge, branch_name} │
  │                                  │ MissionService.create_mission()
  │                                  │ ├─ LLM.generate_title_and_branch()
  │                                  │ ├─ Mission.save(state=DRAFT)
  │                                  │ ├─ MissionRepos.bulk_create()
  │                                  │ └─ link tools, knowledge
  │◀─201 {id, title, branch_name}────│
  │  navigate to /sse-chat?mission=id │
```

---

## 3. Mission Start Flow (SSE)

The start endpoint is a long-lived SSE stream. The client listens until the container is READY.

```
Browser                 Django                    Docker / Hilly
  │                       │                            │
  │─GET /missions/{id}/   │                            │
  │    sse/start/         │                            │
  │    ?token=<jwt>───────▶│                            │
  │                       │ validate JWT from query    │
  │                       │ state → PROVISIONING       │
  │                       │─docker run hilly:latest────▶│
  │                       │   -e MISSION_ID=<id>        │
  │                       │   -e MISSION_REPOS=...      │
  │                       │   -e AUTH_TOKEN=<gh_token>  │
  │                       │   -e DJANGO_WEBHOOK_URL=... │
  │◀─data: container_starting│                          │
  │                       │                            │ supervisord starts
  │                       │                            │ REST MCP :8090
  │                       │                            │ AI Agent :8181
  │                       │                            │ VNC :6080
  │                       │                            │ bootstrap script:
  │                       │                            │   git clone repos
  │                       │◀─POST /webhooks/container/─│
  │                       │   {status: "ready",        │
  │                       │    mission_id: <id>}       │
  │                       │ Mission.state = READY      │
  │◀─data: container_ready│                            │
  │  EventSource.close()  │                            │
```

### SSE Event Schema

```json
{ "type": "container_starting", "data": { "container_id": "abc123" } }
{ "type": "repo_cloning",       "data": { "repo": "owner/name" } }
{ "type": "repo_cloned",        "data": { "repo": "owner/name" } }
{ "type": "container_ready",    "data": { "ip": "172.17.0.5" } }
{ "type": "error",              "data": { "message": "..." } }
```

---

## 4. Chat Cycle (Conversation + SSE Streaming)

```
Browser (SSEChat)         Django (Ninja)         MCPProxy        Hilly Container
  │                           │                      │                 │
  │─POST /missions/{id}/      │                      │                 │
  │    conversation/──────────▶│                      │                 │
  │◀─{conversation_id}────────│                      │                 │
  │                           │                      │                 │
  │─GET /conversations/{cid}/ │                      │                 │
  │    sse/?token=<jwt>────────▶│                      │                 │
  │  [EventSource open]       │─subscribe Redis──────────────────────────
  │                           │  channel             │                 │
  │                           │                      │                 │
  │─POST /conversations/{cid}/│                      │                 │
  │    messages/──────────────▶│                      │                 │
  │  {role:"user",            │ save Message         │                 │
  │   content:"..."}          │                      │                 │
  │                           │─MCPProxyClient.send──▶│                 │
  │                           │                      │─POST /api/conv/─▶│
  │                           │                      │  {message,llm,  │
  │                           │                      │   tools}        │
  │                           │                      │                 │ LLM API call
  │                           │                      │                 │ stream tokens
  │                           │                      │◀─token chunks───│
  │                           │ publish Redis events │                 │
  │◀─data:{type:"token",...}──│                      │                 │
  │◀─data:{type:"token",...}──│                      │                 │
  │  [append to message]      │                      │                 │
  │                           │                      │◀─message_done───│
  │◀─data:{type:"message_complete"}                  │                 │
  │  save to DB               │                      │                 │
```

---

## 5. Tool Execution Cycle (MCP)

When the LLM decides to call a tool (e.g., run a shell command, git commit):

```
LLM (inside Hilly)       AI Agent :8181       REST MCP :8090      Host / GitHub
  │                           │                     │                   │
  │─tool_call: git_commit─────▶│                     │                   │
  │   {message: "feat: ..."}  │                     │                   │
  │                           │─POST /api/git/      │                   │
  │                           │    commit/──────────▶│                   │
  │                           │                     │ git commit -m ...  │
  │                           │                     │─git push origin───▶│
  │                           │                     │◀─push ok──────────│
  │                           │◀─{status:"ok",      │                   │
  │                           │   sha:"abc123"}──────│                   │
  │◀─tool_result──────────────│                     │                   │
  │   {sha: "abc123"}         │                     │                   │
  │                           │                     │                   │
  │  [continue generation]    │                     │                   │
```

The Django backend is also a proxy path for tool calls that come from conversations:

```
Django /conversations/{id}/messages/
  └─ MCPProxyClient.send_message()
       └─ POST http://{container_ip}:8090/api/conversations/{cid}/messages/
            └─ REST MCP forwards to AI Agent :8181
                 └─ AI Agent calls LLM API
                      └─ LLM emits tool_calls
                           └─ MCP server executes locally (git/shell/files)
```

### Tool Call SSE Events (visible in frontend)

```
data: {"type":"tool_call",  "name":"bash",   "args":{"cmd":"pytest -x"}}
data: {"type":"token",      "content":"Running tests...\n"}
data: {"type":"tool_result","name":"bash",   "output":"5 passed","exit_code":0}
data: {"type":"token",      "content":"All tests pass. "}
data: {"type":"message_complete"}
```

---

## 6. GitHub App Installation Flow

After OAuth login the user must install the Holly GitHub App on their repos before creating a mission.

```
Browser                Django              GitHub App        GitHub API
  │                       │                    │                 │
  │─GET /github/status/───▶│                    │                 │
  │◀─{installed: false}───│                    │                 │
  │                       │                    │                 │
  │  [click Install App]  │                    │                 │
  │─redirect to────────────────────────────────▶│                 │
  │  github.com/apps/holly-app/installations   │                 │
  │                       │                    │ user selects repos
  │◀─callback to ─────────────────────────────│                 │
  │  /github/callback?    │                    │                 │
  │  installation_id=<n>  │                    │                 │
  │                       │ save GitHubAppInstallation          │
  │                       │─GET /installations/{n}/repos────────▶│
  │                       │◀─repo list──────────────────────────│
  │                       │ save RepositoryDetail records        │
  │◀─redirect /dashboard──│                    │                 │
```

---

## 7. Mission Stop / Teardown

```
Browser            Django                  Docker
  │                   │                       │
  │─POST /missions/   │                       │
  │    {id}/stop/─────▶│                       │
  │                   │ mission.state=ABORTED  │
  │                   │─docker stop <cid>─────▶│
  │                   │─docker rm <cid>────────▶│
  │                   │ CaddyManager.remove_route(id)
  │◀─200 {state:"aborted"}                    │
```

---

## Redis Channel Reference

| Channel | Publisher | Subscriber | Events |
|---|---|---|---|
| `mission:{uuid}:events` | Django (mission_service) | Django SSE handler | container_starting, repo_cloning, container_ready, error |
| `conversation:{uuid}:stream` | MCPProxyClient | Django SSE handler | token, tool_call, tool_result, message_complete |

---

## Port Reference

| Service | Port | Notes |
|---|---|---|
| Django dev server | 8000 | REST API + admin |
| SvelteKit dev | 5173 | Vite HMR |
| Caddy | 80 / 443 | reverse proxy |
| Redis | 6379 | pub/sub + cache |
| RabbitMQ | 5672 | Celery broker |
| Hilly REST MCP | 8090 | per-container |
| Hilly AI Agent | 8181 | per-container |
| Hilly noVNC | 6080 | per-container |
| Hilly VNC | 5901 | per-container |
