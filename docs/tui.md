# Holly TUI — Developer Reference

> High-signal reference for building, debugging, and extending the Rust terminal interface and API client library.

## Repository layout

```
holly/
├── holly-client/          # Rust API client library (crate: holly_client)
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs         # Public re-exports
│       ├── error.rs       # HollyError enum + Result<T> alias
│       ├── auth/
│       │   ├── mod.rs
│       │   ├── token_store.rs   # Arc<RwLock<Tokens>> — thread-safe JWT store
│       │   └── jwt.rs           # JWT exp decoder (no sig verification)
│       ├── api/
│       │   ├── mod.rs
│       │   ├── client.rs        # ApiClient — HTTP + 401→refresh→retry
│       │   └── sse.rs           # SseStream — async SSE byte parser
│       ├── models/              # serde structs derived from openapi.json
│       │   ├── auth.rs          # TokenObtainPairInput/Output, UserDetail, …
│       │   ├── missions.rs      # MissionSummary, MissionDetail, MissionCreate, …
│       │   ├── conversations.rs # Conversation, Message, SseEvent, …
│       │   ├── llm.rs           # LlmSchema, UserLlmApiKey, …
│       │   ├── github.rs        # GitRepositoryResponse, OAuth types
│       │   ├── knowledge.rs     # KnowledgeSchema
│       │   ├── tools.rs         # ToolSchema
│       │   ├── notifications.rs # NotificationSchema, NotificationListResponse
│       │   └── git.rs           # WorktreeRequest, BranchesResponse, …
│       └── services/            # One service per domain
│           ├── mod.rs           # HollyClient — top-level entry point
│           ├── auth_service.rs
│           ├── mission_service.rs
│           ├── conversation_service.rs
│           ├── github_service.rs
│           ├── llm_service.rs
│           ├── knowledge_service.rs
│           ├── tools_service.rs
│           └── notification_service.rs
│
└── tui/                   # Ratatui terminal application (binary: holly-tui)
    ├── Cargo.toml
    ├── Makefile
    ├── scripts/
    │   └── build-api.sh   # api:full equivalent
    └── src/
        ├── main.rs        # Terminal setup, event loop
        ├── config/mod.rs  # Config — persisted to ~/.config/holly-tui/config.json
        ├── events/mod.rs  # AppEvent (Key, Tick, Resize) + EventHandler
        ├── app/
        │   ├── mod.rs
        │   ├── state.rs   # App struct — all state; Screen enum
        │   └── handlers.rs # handle_event() dispatch + async data loaders
        └── ui/
            ├── mod.rs     # draw() dispatch
            ├── helpers.rs # centered_rect, status_bar, render_tabs, …
            ├── login.rs
            ├── dashboard.rs
            ├── missions.rs
            ├── chat.rs
            ├── github.rs
            ├── llms.rs
            ├── settings.rs
            ├── notifications.rs
            └── wizard.rs
```

---

## Build commands

```bash
# From repo root
cd holly-client && cargo build       # build library
cd holly-client && cargo test        # run 45 unit tests

cd tui && cargo build                # build TUI binary
cd tui && cargo test                 # run 23 unit tests
cd tui && cargo run                  # launch TUI

# Full rebuild (equivalent of npm run api:full)
cd tui && make api-full              # or: ./tui/scripts/build-api.sh [SERVER_URL]

# All make targets
make run        # cargo run
make build      # cargo build --release
make test       # both crates
make api-full   # full rebuild from OpenAPI spec
make check      # cargo check (no codegen)
make fmt        # cargo fmt
make clean      # cargo clean
```

The `build-api.sh` script:
1. Fetches `openapi.json` from `SERVER_URL/_api/openapi.json` (falls back to `frontend/openapi/openapi.json`)
2. Optionally runs `npx @openapitools/openapi-generator-cli generate -g rust` to produce a skeleton in `holly-client-gen/` (reference only — the hand-written client takes precedence)
3. Builds `holly-client --release`
4. Runs all tests in both crates
5. Builds `holly-tui --release`

---

## holly-client — Architecture

### Entry point

```rust
let client = HollyClient::new("http://localhost:8000");
client.auth().login("user@example.com", "password").await?;
let missions = client.missions().list().await?;
```

`HollyClient` holds a single `ApiClient` (cloneable) which in turn holds a `TokenStore` (Arc-wrapped). Every `.missions()`, `.llms()` etc. call clones the `ApiClient` — cheap because all fields are `Arc`-backed.

### Token flow

```
login() → POST /_api/token/pair → TokenStore.set(access, refresh, email)

every authenticated request:
  1. is_authenticated()? → else return NotAuthenticated
  2. access_token_expired()? → proactive do_refresh()
  3. send request
  4. 401? → do_refresh() → retry once
  5. else return parse_response()

do_refresh():
  - tokio::Mutex guard (one refresh at a time)
  - double-check: expired after acquiring lock? else skip
  - POST /_api/token/refresh
  - failure → tokens.clear() + TokenRefresh error
```

`is_token_expired()` decodes the JWT payload (base64 URL decode, no signature verification) and compares `exp` against `Utc::now()`. The server validates signatures; we only need the expiry hint.

### Error types

`HollyError` in `src/error.rs`:

| Variant | When |
|---|---|
| `NotAuthenticated` | Request attempted with no access token |
| `TokenRefresh(msg)` | Refresh endpoint failed or no refresh token |
| `Api { status, message }` | Non-2xx HTTP response |
| `Http(reqwest::Error)` | Network-level failure |
| `Serde(serde_json::Error)` | JSON parse failure |
| `Sse(msg)` | SSE stream protocol error |

`is_unauthorized()` → true when `status == 401`. Use `is_auth_error()` to match all auth-related variants.

### Adding a new endpoint

1. Add request/response structs to the relevant `src/models/*.rs` file with `#[derive(Serialize, Deserialize)]`. Add a unit test that round-trips the JSON.
2. Add a method to the relevant service in `src/services/*.rs`:
   ```rust
   pub async fn my_new_endpoint(&self, id: &str) -> Result<MyResponseType> {
       self.api.get(&format!("/_api/holly/my-resource/{id}")).await
   }
   ```
3. For non-standard HTTP methods (e.g. DELETE with a body), use:
   ```rust
   let resp = self.api
       .raw_request_builder(Method::DELETE, &format!("/_api/holly/res/{id}"))
       .json(&body)
       .send()
       .await
       .map_err(HollyError::Http)?;
   ApiClient::parse_response(resp).await
   ```
4. Expose from `HollyClient` in `src/services/mod.rs` if adding a new domain.

### Adding a new model domain

1. Create `src/models/my_domain.rs` with structs + tests.
2. Add `mod my_domain; pub use my_domain::*;` to `src/models/mod.rs`.
3. Create `src/services/my_domain_service.rs`.
4. Add `mod my_domain_service; pub use my_domain_service::MyDomainService;` to `src/services/mod.rs`.
5. Add `pub fn my_domain(&self) -> MyDomainService { MyDomainService::new(self.api.clone()) }` to `HollyClient`.

### SSE streaming

```rust
// Mission start (GET stream, token in query string)
client.missions().start_sse("mission-id", |event: SseEvent| {
    if let Some(msg) = event.message { println!("{msg}"); }
}).await?;

// Conversation send (POST + stream response)
client.conversations().send_message_sse("conv-id", "hello", |token: String| {
    print!("{token}");
}).await?;
```

`SseStream` parses `data: {...}\n\n` blocks. The `[DONE]` sentinel ends the stream cleanly. Malformed JSON lines produce `HollyError::Serde` per chunk rather than aborting the stream.

---

## TUI — Architecture

### Event loop

```
main() → enable_raw_mode → Terminal::new → App::new → EventHandler::new
  loop:
    terminal.draw(|f| ui::draw(f, &app))   ← pure, synchronous render
    events.next().await                     ← yields Key | Tick | Resize
    app.handle_event(event).await           ← mutates state, calls API
    if app.should_quit() → break
```

`EventHandler` spawns two background tasks: a `spawn_blocking` crossterm reader (polls every 50ms) and a Tokio interval for `Tick` events (200ms default).

### Screen enum

```rust
pub enum Screen {
    Login, Register, ForgotPassword,
    Dashboard,
    Missions, MissionDetail(String),   // String = mission UUID
    Chat(String),                       // String = conversation UUID
    Github,
    Llms,
    Settings,
    Notifications,
    Wizard,
    Loading(String, Box<Screen>),       // message, destination
}
```

`navigate_to(screen)` clears error/status messages and sets `current_screen`. `handle_escape()` pops one level (e.g. `MissionDetail → Missions`, `Missions → Dashboard`).

### State

All mutable state lives in `App` (`src/app/state.rs`). There is no separate store or channel — state is owned by the main task and mutated synchronously in `handle_event`. The `HollyClient` is `Clone` (Arc-backed), so service handles can be cheaply created per-call without cloning data.

`App` is composed of domain sub-structs rather than a flat list of fields:

```rust
pub struct App {
    pub config: Config,
    pub client: HollyClient,
    pub quit: bool,
    pub current_screen: Screen,
    pub status_msg: Option<String>,
    pub error_msg: Option<String>,

    pub auth: AuthState,          // login form fields, focused field
    pub dashboard: DashboardState,// counts, recent conversations
    pub missions: MissionsState,  // list, selected_idx, action, current
    pub chat: ChatState,          // phase, messages, input, streaming_buffer, conversations, token_rx
    pub github: GithubState,      // repositories, selected_idx
    pub llm: LlmState,            // llms, api_keys, selected_idx
    pub settings: SettingsState,  // tab, server_url
    pub notifications: NotificationState, // notifications, unread_count
}
```

**Chat streaming** uses a non-blocking channel pattern. `ChatPhase` (`Idle` | `Streaming`) tracks state:

```rust
// Sending a message — spawns task, never awaits in the render loop
let (tx, rx) = mpsc::unbounded_channel::<String>();
self.chat.token_rx = Some(rx);
self.chat.phase = ChatPhase::Streaming;
tokio::spawn(async move {
    client.conversations().send_message_sse(&conv_id, &msg, |t| { let _ = tx.send(t); }).await.ok();
    let _ = tx.send("\x00DONE\x00".into());
});

// on_tick() — drains channel without blocking, called every 200ms
fn drain_streaming_tokens(&mut self) {
    loop {
        match rx.try_recv() {
            Ok(token) if token == "\x00DONE\x00" => { /* commit buffer, set Idle */ break; }
            Ok(token) => self.chat.streaming_buffer.push_str(&token),
            Err(_) => break,
        }
    }
}
```

`chat.streaming_buffer` is rendered live in a yellow-bordered "Streaming…" panel directly above the input box.

### Adding a new screen

1. Add a variant to `Screen` in `src/app/state.rs`.
2. Add a new domain sub-struct (e.g. `MyDomainState`) to `state.rs` and a field on `App`. Update `App::new`.
3. Add a `handle_<screen>_key` method in `src/app/handlers.rs` and match it in `handle_event`.
4. Add `handle_escape` logic for the new screen.
5. Create `src/ui/<screen>.rs` with a `render_<screen>(f: &mut Frame, app: &App)` function.
6. Add `mod <screen>;` and the arm to `draw()` in `src/ui/mod.rs`.

### UI conventions

All render functions take `(f: &mut Frame, app: &App)`. They never mutate state.

Helper functions in `src/ui/helpers.rs`:

| Function | Purpose |
|---|---|
| `page_layout(area)` | Returns `(content_rect, status_bar_rect)` — 2-line status bar at bottom |
| `centered_rect(pct_x, pct_y, area)` | Modal-style centered rectangle |
| `status_bar(status, error)` | Green status or red error paragraph |
| `render_tabs(titles: &[&str], selected)` | Ratatui Tabs widget — slice, no Vec allocation |
| `titled_block(title)` | Blue-border Block |
| `focused_block(title)` | Cyan-border Block for active input |
| `selected_style()` | Black-on-cyan highlight |
| `normal_style()` | White text |
| `muted_style()` | DarkGray text |

For lists with keyboard selection, use `ListState` + `StatefulWidget::render`:

```rust
let mut state = ListState::default();
state.select(Some(app.selected_idx));
let _ = ratatui::widgets::StatefulWidget::render(
    List::new(items).block(titled_block(" Title ")),
    area,
    f.buffer_mut(),
    &mut state,
);
```

### Keyboard bindings (global)

| Key | Action |
|---|---|
| `q` | Quit |
| `Ctrl+C` | Quit |
| `Esc` | Back one level |
| `↑` / `k` | List up |
| `↓` / `j` | List down |
| `Enter` | Confirm / open |
| `Tab` | Switch field / tab |
| `r` | Refresh (on list screens) |

### Config persistence

`Config` lives at `~/.config/holly-tui/config.json`:

```json
{ "server_url": "http://localhost:8000", "theme": "dark", "saved_email": "u@example.com" }
```

`Config::load()` returns `Default` on any error (missing file, parse error). `Config::save()` creates parent dirs. Mutate `app.config` then call `app.config.save()` to persist.

### Logging

Logs write to `~/.local/share/holly-tui/logs/holly-tui.YYYY-MM-DD.log` (rolling daily). They never go to stdout/stderr to avoid breaking the TUI. Set `RUST_LOG=holly_tui=trace` before launching to get verbose output.

---

## Debugging

### Compile errors

```bash
cargo check          # fast type check, no codegen
cargo check 2>&1 | grep "^error" | head -20
```

Common issues:
- **`temporary value dropped while borrowed` in `tokio::join!`**: the service object (`.missions()`, `.llms()`) returns a temporary. Either bind it to a `let` before the `join!`, or use a combined method on the service (e.g. `llms().list_with_keys()` fetches LLMs + API keys concurrently via `tokio::join!` internally, avoiding the lifetime issue):
  ```rust
  // Option A: bind the temporary
  let svc = self.client.missions();
  let (a, b) = tokio::join!(svc.list(), svc.get("id"));
  // Option B: combined service method (preferred for common pairs)
  let (llms, keys) = self.client.llms().list_with_keys().await?;
  ```
- **`module state is private`**: submodules used in `ui/` must be `pub mod state` in `app/mod.rs`.
- **`cannot infer type`**: Rust needs a type hint for `execute_authed::<_B, T>` — always call via the typed wrappers (`get<T>`, `post<B, T>`).

### Runtime debugging

Add `tracing::debug!("...")` calls — they write to the log file, not the terminal.

```bash
RUST_LOG=holly_tui=debug,holly_client=debug cargo run
tail -f ~/.local/share/holly-tui/logs/holly-tui.$(date +%Y-%m-%d).log
```

### API errors

`HollyError::Api { status, message }` wraps the raw HTTP body. The `message` field contains the server's JSON error. To see it in the TUI, it surfaces via `app.set_error(format!("{e}"))` which renders in the red status bar at the bottom of each screen.

For 401 loops: check `TokenStore::access_token_expired()` — if it always returns true, the JWT `exp` claim may be missing or the system clock is wrong.

### Testing

```bash
cargo test                          # all tests in current crate
cargo test models::                 # run all model tests
cargo test token_store              # run matching test names
cargo test -- --nocapture           # show println! output
```

Tests are co-located with source (`#[cfg(test)] mod tests { ... }` at bottom of each file). No external services required — all tests are unit tests operating on in-process data.

---

## Extension patterns

### Persisting auth tokens across sessions

```rust
// On exit:
let store = client.token_store();
let tokens = serde_json::json!({
    "access": store.access_token(),
    "refresh": store.refresh_token(),
    "email": store.email(),
});
fs::write(token_path, serde_json::to_string(&tokens)?)?;

// On startup:
let loaded: serde_json::Value = serde_json::from_str(&fs::read_to_string(token_path)?)?;
let store = TokenStore::new();
store.set(&loaded["access"].as_str().unwrap_or(""), ...);
let client = HollyClient::with_tokens(server_url, store);
```

### Real-time streaming in TUI (non-blocking)

Chat SSE uses a non-blocking channel. `send_message_sse` is called in a spawned task; the render loop never awaits it. The `on_tick()` handler drains the channel via `try_recv()` and appends tokens to `chat.streaming_buffer`, which renders as a live panel:

```rust
// In handle_chat_key (Enter pressed):
let (tx, rx) = mpsc::unbounded_channel::<String>();
self.chat.token_rx = Some(rx);
self.chat.phase = ChatPhase::Streaming;
let client = self.client.clone();
tokio::spawn(async move {
    client.conversations().send_message_sse(conv_id, content, |t| { let _ = tx.send(t); }).await.ok();
    let _ = tx.send("\x00DONE\x00".into());
});

// In on_tick() → drain_streaming_tokens():
match rx.try_recv() {
    Ok(t) if t == "\x00DONE\x00" => { /* commit buffer to messages, reset to Idle */ }
    Ok(t) => self.chat.streaming_buffer.push_str(&t),
    Err(TryRecvError::Empty) => {}  // nothing yet, try next tick
    Err(TryRecvError::Disconnected) => { /* task dropped, commit buffer */ }
}
```

### Adding a webhook / background poller

In `on_tick()` in `handlers.rs`, increment a counter and poll on every N ticks:

```rust
self.tick_count += 1;
if self.tick_count % 30 == 0 {  // every 6s at 200ms tick
    if self.client.is_authenticated() {
        let count = self.client.notifications().unread_count().await.unwrap_or_default();
        self.notifications.unread_count = count.count;
    }
}
```

### Regenerating models from a new OpenAPI spec

```bash
./tui/scripts/build-api.sh http://your-server:8000
```

The script copies the spec to `tui/openapi.json`. If `npx` is available it runs `openapi-generator-cli -g rust` and outputs to `holly-client-gen/`. That generated crate is a reference — manually port new schemas to `holly-client/src/models/` and new endpoints to the relevant service, following the existing patterns.

Alternatively, diff the new `openapi.json` against `frontend/openapi/openapi.json`:

```bash
diff <(python3 -c "import json,sys; d=json.load(open('frontend/openapi/openapi.json')); [print(k) for k in d['paths']]") \
     <(python3 -c "import json,sys; d=json.load(open('tui/openapi.json')); [print(k) for k in d['paths']]")
```

---

## Relationship to the Svelte frontend

| Svelte concept | Rust equivalent |
|---|---|
| `npm run api:full` | `make api-full` / `./scripts/build-api.sh` |
| `holly-api` npm package | `holly-client` Rust crate |
| `TokenManager` class | `TokenStore` + `ApiClient::do_refresh()` |
| `withTokenRefresh()` | `ApiClient::execute_authed()` |
| `accessToken` svelte store | `TokenStore::access_token()` |
| `missionApi.hollyHollyApiViewsMissionListMissions()` | `client.missions().list()` |
| `EventSource` / SSE | `SseStream::connect()` |
| `api.config.ts` `baseURL` | `HollyClient::new(server_url)` |
| Routes (`/missions`, `/chat`) | `Screen` enum variants |
| Svelte stores | `App` struct fields |
| Component re-render | `terminal.draw(|f| ui::draw(f, app))` on every loop tick |
