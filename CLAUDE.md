# Holly — Claude Code Guide

This file is the primary reference for working on this repository with Claude Code.

## Project overview

Holly is an AI-assisted software development platform. Engineers create "missions" (scoped coding tasks), which LLMs execute inside isolated Docker containers. The system streams progress back to the UI in real time via SSE.

**Three interfaces share the same Django backend:**
1. `frontend/` — Svelte/SvelteKit web app (primary UI)
2. `tui/` — Ratatui Rust terminal app (feature-equivalent TUI)
3. `holly-client/` — Rust API client library (used by the TUI)

---

## Key documentation

| Topic | File |
|---|---|
| **TUI + Rust client: build, debug, extend** | [`docs/tui.md`](docs/tui.md) |
| GitHub App setup | [`docs/GH_APP_SETUP.md`](docs/GH_APP_SETUP.md) |
| User guide | [`USER_GUIDE.md`](USER_GUIDE.md) |
| Contributing | [`CONTRIBUTING.md`](CONTRIBUTING.md) |

> **Start here for TUI work:** [`docs/tui.md`](docs/tui.md) covers repository layout, build commands, architecture decisions, debugging patterns, and extension guides for both `holly-client` and `tui/`.

---

## Quick-start by component

### Backend (Django)
```bash
uv sync
cd backend && uv run manage.py migrate
uv run manage.py runserver          # http://localhost:8000
```

### Frontend (Svelte)
```bash
cd frontend && npm install
npm run dev:django                  # http://localhost:5173
npm run api:full                    # regenerate API client from openapi.json
```

### TUI (Rust)
```bash
cd tui && cargo run                 # launch terminal interface
make test                           # run all tests (holly-client + tui)
make api-full                       # regenerate + rebuild (equiv. of npm run api:full)
```

---

## Codebase map

```
holly/
├── backend/           Django app — missions, auth, GitHub, LLMs, SSE
├── frontend/          SvelteKit — all UI, openapi.json source of truth
│   └── openapi/openapi.json   ← canonical API spec
├── holly-client/      Rust API client library (JWT auth, serde_json models)
├── tui/               Ratatui TUI binary
│   ├── scripts/build-api.sh   ← api:full equivalent
│   └── Makefile
├── docs/
│   └── tui.md         ← TUI/client architecture + developer reference
└── scripts/           Setup helpers (GitHub App, etc.)
```

---

## Common tasks

### Adding a new API endpoint
See `docs/tui.md` → "Adding a new endpoint". Short version:
1. Add serde struct to `holly-client/src/models/<domain>.rs`
2. Add method to `holly-client/src/services/<domain>_service.rs`
3. Add UI handler in `tui/src/app/handlers.rs`
4. Add UI render in `tui/src/ui/<screen>.rs`

### Running tests
```bash
cd holly-client && cargo test       # 44 unit tests
cd tui && cargo test                # 19 unit tests
cd frontend && npm run test:unit    # Vitest
```

### Updating the OpenAPI spec
The spec lives at `frontend/openapi/openapi.json`. After backend changes:
```bash
# Option 1: fetch from running server
cd tui && make api-full             # fetches + rebuilds Rust client

# Option 2: manual frontend regen
cd frontend && npm run api:full
```

### Debugging the TUI
Logs go to `~/.local/share/holly-tui/logs/holly-tui.<date>.log` (never stdout).
```bash
RUST_LOG=holly_tui=debug cargo run 2>/dev/null
tail -f ~/.local/share/holly-tui/logs/holly-tui.$(date +%Y-%m-%d).log
```

---

## Conventions

- **Rust**: edition 2021, `serde_json` for all serialization, `thiserror` for errors, `tokio` for async. No `unwrap()` in library code — propagate with `?`.
- **Models**: all optional JSON fields use `Option<T>` with `#[serde(default)]`. Fields absent in serialized output use `#[serde(skip_serializing_if = "Option::is_none")]`.
- **TUI state**: all mutable state in `App` struct. UI functions are pure (`&App` only). Async calls only in `handlers.rs`.
- **Tests**: co-located in `#[cfg(test)] mod tests` at the bottom of each file. No integration test setup required — unit tests only.
- **Branch naming**: `claude/<description>-<session-id>` for Claude Code branches.
