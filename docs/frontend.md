---
title: Holly – Frontend Reference
scope: sveltekit, routes, stores, components, api-client, sse
audience: llm, developer
---

# Holly – Frontend Reference

The frontend is a **SvelteKit 2 + TypeScript** application in `frontend/`. It uses TailwindCSS + Flowbite for UI, auto-generated API clients for the Django backend, and EventSource (SSE) for real-time streaming.

---

## Directory Structure

```
frontend/src/
├── routes/                    # SvelteKit file-based routing
│   ├── (auth)/                # layout group – redirects if not authed
│   │   ├── login/
│   │   ├── register/
│   │   └── forgot-password/
│   ├── dashboard/             # home page after login
│   ├── wizard/                # 6-step mission creation
│   ├── sse-chat/              # real-time chat with LLM
│   ├── github/
│   │   ├── connect/           # OAuth connect flow
│   │   └── account/           # manage installations
│   ├── llms/                  # LLM management
│   └── settings/              # user profile + API keys
└── lib/
    ├── apis/                  # API wrapper functions
    │   ├── api.config.ts      # base URL + auth headers (reactive)
    │   ├── mission/           # mission API calls
    │   ├── conversation/      # chat API calls
    │   ├── github/            # github API calls
    │   ├── llm/               # llm API calls
    │   └── middleware/        # token-refresh interceptor
    ├── store/                 # Svelte writable stores
    │   ├── auth/              # tokens, user identity
    │   ├── mission/           # selected mission
    │   ├── chat/              # active conversation + messages
    │   └── wizard.store.ts    # wizard multi-step state
    ├── components/            # reusable UI components
    └── utils/                 # helpers (logger, formatters)
```

---

## Routes

### `(auth)/login` – Login Page

**File:** `src/routes/(auth)/login/+page.svelte`

Email + password form. On success stores JWT tokens via `tokens.store.ts` and navigates to `/dashboard`. Includes "remember me" (persists refresh token to cookie).

### `(auth)/register` – Registration

**File:** `src/routes/(auth)/register/+page.svelte`

Creates a new account via `POST /_api/auth/register/`. Auto-logs in on success.

### `dashboard` – Dashboard

**File:** `src/routes/dashboard/+page.svelte`

Shows summary stats (missions, repos, conversations). Quick-launch buttons for wizard and chat. Fetches data on mount using `loadDashboard()`.

### `wizard` – Mission Creation Wizard

**File:** `src/routes/wizard/+page.svelte`

Multi-step wizard backed by `wizard.store.ts`.

```
Step 1: Branch name (auto-suggested by LLM on description entry)
Step 2: Select repositories (from GitHub installations)
Step 3: Choose LLM model
Step 4: Select tools (MCP servers)
Step 5: Select knowledge base items
Step 6: Mission description + confirm
```

On submit: `POST /_api/holly/missions/` → navigates to `/sse-chat?mission=<id>`.

### `sse-chat` – Real-Time Chat Interface

**File:** `src/routes/sse-chat/+page.svelte`
**Component:** `src/lib/components/chat/SSEChat.svelte`

The main interaction surface. Opens an `EventSource` for streaming. See [flows.md](flows.md) for the full chat cycle.

Key responsibilities:
- Create or resume a `MissionConversation`
- Subscribe to SSE stream on `/_api/holly/conversations/{id}/sse/`
- Send user messages via `POST /_api/holly/conversations/{id}/messages/`
- Render streaming tokens as they arrive
- Display tool calls and results inline

### `github/connect` – GitHub OAuth Connect

**File:** `src/routes/github/connect/+page.svelte`

Initiates GitHub OAuth redirect via `GET /_api/auth/github/`. On return from callback, links the GitHub account and prompts user to install the GitHub App on their repos.

### `llms` – LLM Management

**File:** `src/routes/llms/+page.svelte`

Lists system LLMs and allows adding custom ones with personal API keys. CRUD for `UserLLMApiKey`.

---

## Svelte Stores

Stores are in `src/lib/store/`. All are `writable` (or derived). Persistent stores use `js-cookie` for cross-session auth.

### `auth/tokens.store.ts`

```typescript
tokens: {
  access: string | null
  refresh: string | null
}
isAuthenticated: boolean  // derived
currentUser: User | null
```

`isAuthenticated` is read in `+layout.svelte` to guard protected routes. Token refresh is handled transparently in the API middleware.

### `mission/mission.store.ts`

```typescript
selectedMission: Mission | null
missions: Mission[]
```

Set when the user opens the wizard or navigates to a mission. Used by `sse-chat` to know which mission to attach conversations to.

### `chat/chat.store.ts`

```typescript
activeConversation: Conversation | null
messages: Message[]
isStreaming: boolean
```

Updated by the SSE event handler in `SSEChat.svelte`.

### `wizard.store.ts`

```typescript
currentStep: number  (1–6)
branchName: string
selectedRepos: RepositoryDetail[]
selectedLLM: LLM | null
selectedTools: Tools[]
selectedKnowledge: Knowledge[]
description: string
```

Cleared on wizard completion or cancel.

---

## API Client

### Auto-generation

```bash
cd frontend
npm run api:gen          # generate TS client from backend OpenAPI spec
npm run api:full         # generate + sync (requires Django to be running)
```

Generated files live in `frontend/gen/openapi/`. Do not edit by hand.

### API Config (`src/lib/apis/api.config.ts`)

Provides a reactive configuration object that injects the current `Authorization: Bearer <token>` header on every request, and hooks into the token-refresh middleware.

```typescript
export const apiConfig = derived(tokens, ($tokens) => ({
  baseUrl: API_BASE_URL,
  headers: $tokens.access
    ? { Authorization: `Bearer ${$tokens.access}` }
    : {}
}))
```

### Mission API (`src/lib/apis/mission/api.mission.ts`)

```typescript
createMission(data: MissionCreate): Promise<Mission>
getMission(id: string): Promise<Mission>
listMissions(): Promise<Mission[]>
deleteMission(id: string): Promise<void>
createConversation(missionId: string): Promise<Conversation>
```

### Conversation API (`src/lib/apis/conversation/api.conversation.ts`)

```typescript
sendMessage(conversationId: string, content: string): Promise<void>
getConversation(id: string): Promise<Conversation>
openSSEStream(conversationId: string, token: string): EventSource
```

### Token Refresh Middleware (`src/lib/apis/middleware/token-refresh.middleware.ts`)

Wraps every fetch. On HTTP 401:
1. Calls `POST /auth/token/refresh/` with stored refresh token
2. Stores new access token
3. Retries the original request once
4. If refresh also fails → clears tokens → redirects to `/login`

---

## Key Components

### `SSEChat.svelte`

Core chat UI. Maintains an `EventSource` for streaming. Parses SSE event types:

| Event type | Action |
|---|---|
| `token` | Append to current assistant message bubble |
| `message_complete` | Finalise message, re-enable input |
| `tool_call` | Show tool call card (name + args) |
| `tool_result` | Update tool call card with result |
| `error` | Show error toast, re-enable input |
| `mission_status` | Update mission state badge |

### `MissionCard.svelte`

Summary card on dashboard. Shows title, state badge, repo names, last activity.

### `WizardStep.svelte`

Wraps each wizard step with back/next navigation and validation guard.

### `LLMSelector.svelte`

Dropdown with LLM name, provider badge, and model ID. Reflects `selectedLLM` store.

---

## Environment Variables

`frontend/.env` (copy from `frontend/env.example`):

```bash
PUBLIC_API_BASE_URL=http://localhost:8000   # Django backend URL
PUBLIC_GITHUB_CONNECT_URL=/api/auth/github/ # OAuth entry point
```

---

## Build & Dev Scripts

```bash
npm run dev           # Vite dev server :5173 (standalone)
npm run dev:django    # dev server pointed at local Django
npm run build         # production build → dist/
npm run preview       # preview production build locally
npm run test:unit     # Vitest unit tests
npm run test:integration  # Playwright E2E
npm run lint          # ESLint + Svelte check
npm run format        # Prettier
npm run check         # svelte-check type validation
npm run api:gen       # regenerate API client
```

---

## Key File Index

| File | Purpose |
|---|---|
| `src/routes/(auth)/login/+page.svelte` | Login form + JWT storage |
| `src/routes/wizard/+page.svelte` | Mission creation wizard |
| `src/routes/sse-chat/+page.svelte` | Chat page shell |
| `src/lib/components/chat/SSEChat.svelte` | Streaming chat UI |
| `src/lib/store/auth/tokens.store.ts` | JWT token state |
| `src/lib/store/mission/mission.store.ts` | Selected mission state |
| `src/lib/store/chat/chat.store.ts` | Conversation + messages |
| `src/lib/store/wizard.store.ts` | Wizard multi-step state |
| `src/lib/apis/api.config.ts` | Auth header injection |
| `src/lib/apis/mission/api.mission.ts` | Mission API calls |
| `src/lib/apis/conversation/api.conversation.ts` | Chat API calls |
| `src/lib/apis/middleware/token-refresh.middleware.ts` | Auto JWT refresh |
