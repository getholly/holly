# Holly — Adversarial Code Review

**Date:** 2026-06-14
**Scope:** Full repository (`backend/` Django app, `frontend/` SvelteKit SPA, `backend/static/js/` legacy Alpine/JS, `hilly/` workspace-execution subsystem, infra: `Dockerfile`, `docker-compose*.yml`, `.github/workflows`, settings & dependencies).
**Method:** Adversarial multi-agent review across security, backend correctness/architecture, data model/migrations, configuration/secrets, infrastructure/CI, frontend, and testing. Findings below are grounded in actual code with file/line references.

---

## Executive Summary

Holly is an AI-assisted development workspace: it provisions Docker containers that run autonomous LLM agents against users' GitHub repositories, with JWT auth, Stripe billing scaffolding, SSE streaming, and a Caddy reverse-proxy front. The architecture is ambitious and the feature surface is large, but the review found **a connected chain of critical security weaknesses**, several **functional bugs that are live in production paths**, and **significant structural debt** (dual frontends, SQLite-in-prod, settings sprawl, ad-hoc background threads).

### The headline security chain
An attacker can chain these into **remote-task-submission → host root**:

1. **Unauthenticated, unsigned container webhook** (`/_api/holly/webhooks/container-webhook`) lets anyone forge mission state and notifications.
2. **Unauthenticated container REST API** (FastAPI in the workspace container, CORS `*`, no auth) exposes git clone/commit/push/PR using a supplied token.
3. The user's **GitHub OAuth token with full `repo` scope** is injected into that container as an env var.
4. The workspace container runs **`privileged: true`** — a textbook container-escape to host root.
5. **JWT signing key and the field-encryption salt fall back to committed default constants** — if env vars are unset, tokens are forgeable and stored API keys are decryptable.

### Severity tally (de-duplicated)

| Severity | Count | Examples |
|---|---|---|
| **Critical** | 6 | Privileged container, unauth container API, unsigned webhook, default JWT key, default Fernet salt, Caddy SSRF |
| **High** | ~22 | IDOR on PR creation & repo-token, token-in-localStorage, data-loss migration, daemon-thread background jobs, broken `create_pull_request`, `production.py` import crash |
| **Medium** | ~45 | CORS wildcard+credentials, loguru `diagnose=True` secret leak, racing token-refresh, missing transactions, SQLite split-brain, broken loguru `%s` logging |
| **Low** | ~40 | Magic strings, dead code, missing indexes, pagination gaps, redundant settings |

### Top 10 things to fix first
1. Remove `privileged: true` from the workspace container; drop caps, add seccomp/AppArmor. (`hilly/docker-compose.yml:37`)
2. Authenticate **and** HMAC-sign the container webhook. (`backend/holly/holly/api/views/webhooks.py:45`)
3. Add auth to the in-container FastAPI REST API; stop publishing its ports to `0.0.0.0`. (`hilly/rest_mcp_client/.../main.py`)
4. Fail-fast (no defaults) for `SECRET_KEY`, `DJANGO_SECRET_KEY`, `SALT_KEY` in non-DEBUG; ensure `NINJA_JWT["SIGNING_KEY"]` resolves to the real secret. (`backend/config/settings/base.py:266,367,395`)
5. Validate/allowlist the Caddy `/caddy/map` `ip:port` to prevent SSRF/open-proxy. (`backend/holly/holly/api/views/caddy.py`)
6. Fix `production.py` import of the non-existent `.email` module (it crashes on boot). (`backend/config/settings/production.py:6`)
7. Add ownership scoping to `create_pull_request`, `get_repository_token`, `knowledge`, `tools`, and the LLM list (IDOR/data leakage).
8. Set loguru `diagnose=False` in production (it dumps local variables incl. secrets). (`backend/holly/middleware/exceptions.py:23,33`)
9. Move JWT access/refresh tokens out of `localStorage`/JS-cookies into httpOnly cookies; reconcile the two competing refresh implementations.
10. Replace SQLite-in-production with Postgres (web/celery currently point at *different* SQLite files).

---

## Severity legend
- **Critical** — Direct path to data breach, RCE, host compromise, or auth bypass; fix immediately.
- **High** — Serious security or correctness defect exploitable/observable under normal operation.
- **Medium** — Meaningful risk, reliability, or maintainability issue; should be scheduled.
- **Low** — Hygiene, hardening, performance, or consistency improvement.

---

## 1. Security — Critical

### C1. Privileged workspace container running untrusted agent code → host root
- **File:** `hilly/docker-compose.yml:37` (`privileged: true`); containers started by `backend/holly/holly/services/containers/holly_container_service.py:169-189`.
- Each mission provisions a `privileged` container in which an autonomous LLM executes model-generated shell/git commands driven by user mission text. `privileged` disables seccomp/AppArmor and grants host-device access, enabling classic escapes (mount host disk, cgroup `release_agent` / `core_pattern`). This is a direct "submit a mission → root on the Docker host" path. The README already warns about it.
- **Fix:** Remove `privileged: true`; run with `--cap-drop=ALL` + only required caps, a restrictive seccomp profile, no host devices, read-only rootfs where possible, non-root user. If VNC needs caps, grant only those. Consider rootless/sysbox DinD.

### C2. In-container REST API has no authentication and CORS `*`
- **File:** `hilly/rest_mcp_client/rest_mcp_client/main.py:19-25` (CORS `allow_origins=["*"]`, `allow_credentials=True`, no auth dependency); routes in `hilly/rest_mcp_client/rest_mcp_client/routes/git.py`.
- The FastAPI app inside the workspace container mounts git/file/conversation routes with zero auth. Its ports (`8090`, `8181`, VNC) are published to the host (`hilly/docker-compose.yml:7-13`) on `0.0.0.0`. Anyone reaching those ports (or any container on the shared network) can clone/commit/push/create-PR with a supplied `auth_token`. `allow_origins=["*"]` + `allow_credentials=True` is itself an invalid/dangerous CORS combination.
- **Fix:** Require the per-container `SESSION_ID`/`AUTH_TOKEN` on every request; bind ports to the internal network only; restrict CORS to the known origin.

### C3. Unauthenticated, unsigned container webhook → mission/notification forgery & container control
- **File:** `backend/holly/holly/api/views/webhooks.py:45` (`auth=None`, no signature); handler `backend/holly/holly/services/webhook_handler.py:68-126`.
- Any unauthenticated caller who knows a `mission_id` (UUID) can POST arbitrary `status`/`data`: flip mission state (`init.completed`→READY, `init.failed`→ERROR), inject notifications to the victim owner, fabricate PR metadata, trigger `stop_container`, and publish attacker-controlled JSON onto the Redis SSE channel streamed to the owner's browser. Contrast with the GitHub webhook path, which *does* use a secret.
- **Fix:** HMAC-sign container→Django callbacks with a per-mission/per-container secret and verify server-side; restrict the route to the internal network. Reachability is amplified by the `host.docker.internal` callback URL (`mission_service.py:671,1006`).

### C4. Default `SECRET_KEY` is also the JWT (HS256) signing key → token forgery
- **File:** `backend/config/settings/base.py:266` (`SECRET_KEY = env.str("SECRET_KEY", default="dummy_secret_auth_key")`), `:394-395` (`ALGORITHM="HS256"`, `SIGNING_KEY=SECRET_KEY`).
- Two compounding problems: (a) the default fallbacks are publicly-known constants (`"dummy_secret_auth_key"`, and `"!!!SET DJANGO_SECRET_KEY!!!"` in prod/develop/local) with **no fail-fast** if unset; (b) `base.py` reads env var `SECRET_KEY` while prod/develop/local read `DJANGO_SECRET_KEY` — a name mismatch — and `NINJA_JWT["SIGNING_KEY"]` is bound to the **base.py** value at import time, so a prod override of `SECRET_KEY` may not propagate to the JWT signing key. If the key resolves to a default, any `AccessToken` (and SSE auth at `mission.py:567`) is forgeable → full account takeover.
- **Fix:** No secret defaults; `raise ImproperlyConfigured` in non-DEBUG when unset. Unify the env-var name. Re-derive/lazily reference `SIGNING_KEY` after the final `SECRET_KEY` is set.

### C5. Hardcoded field-encryption salt → stored LLM API keys & OAuth tokens decryptable
- **File:** `backend/config/settings/base.py:367` (`SALT_KEY = [env.str("SALT_KEY", "f2fa786c-021c-4103-acdf-82cea504eaae")]`); used by `EncryptedTextField` in `backend/holly/holly/models/user_llm_api_key.py:22`.
- `django-fernet-encrypted-fields` derives its Fernet key from `SECRET_KEY` + `SALT_KEY`. A committed default salt, combined with C4, means encrypted-at-rest data (users' provider API keys; GitHub tokens given `SOCIALACCOUNT_STORE_TOKENS=True`) is decryptable by anyone with the repo + DB read. No CI/compose step ever sets `SALT_KEY`, so production likely runs on this default.
- **Fix:** Remove the default; require from secrets; rotate and re-encrypt existing rows.

### C6. Caddy `/caddy/map` SSRF / open-proxy via user-controlled `ip:port`
- **File:** `backend/holly/holly/api/views/caddy.py:13-18`, `backend/holly/holly/services/caddy_manager.py:39-65`, schema `caddy_schemas.py:7-9` (unvalidated `ip: str`, `port: int`).
- Any authenticated user can register a reverse-proxy upstream pointing at arbitrary internal addresses (`169.254.169.254`, `127.0.0.1`, internal services): `"upstreams":[{"dial": f"{ip}:{port}"}]`, then `requests.post(f"{caddy_api_url}/load", ...)`. Turns the shared public Caddy into an open proxy to the metadata endpoint / internal services.
- **Fix:** Allowlist `ip` to the container subnet; reject loopback/link-local/private/metadata ranges; restrict `port`; ensure the Caddy admin API is not otherwise exposed.

---

## 2. Security — High

### H1. IDOR — `create_pull_request` not scoped to the requesting user
- **File:** `backend/holly/github_ext/api/router.py:130-149`. `get_object_or_404(MissionConversation, id=mission_conversation_id)` has no user filter. Any logged-in user can target another user's mission. Contrast `conversations.py`, which filters `mission__owner=request.user`.
- **Fix:** `get_object_or_404(MissionConversation, id=..., mission__owner=request.user)` (or via `can_be_accessed_by`).

### H2. `create_pull_request` is also **broken** — reads non-existent attributes
- **File:** `backend/holly/github_ext/api/router.py:134,142-145`. `mission.repositories.first()` returns a `MissionRepos` (per `holly/models/mission.py:110`), which has `repository` (FK) + `branch_name`, **not** `username`/`repo`. `repo_detail.username` / `repo_detail.repo` raise `AttributeError` at runtime — the endpoint fails for every real call.
- **Fix:** `repo_detail.repository.username` / `.repo` with `select_related("repository")`.

### H3. IDOR + token exposure — `get_repository_token` returns a raw GitHub App installation token
- **File:** `backend/holly/github_ext/views.py:97-134`. `@login_required` but ignores `owner`/`repo`, grabs `installations.first()`, mints an installation token covering possibly *all* repos in that installation, and returns it in the JSON body. Also queries the **deprecated** `GitHubAppInstallation` model (`:103-104`), inconsistent with the migrated `GitHubAccountInstallation`.
- **Fix:** Verify the installation actually covers the requested repo; never return raw tokens to the browser — act server-side.

### H4. Cross-tenant data exposure — unfiltered list endpoints
- **Files:** `backend/holly/holly/api/views/knowledge.py:13-20` (`Knowledge.objects.all()`), `tools.py:11-20`, and `backend/holly/holly/views.py:35` (`LLM.objects.values("id","name")` returns *all* LLMs incl. other users' custom ones — the `LLM` model has a `user` FK + `is_system`).
- **Fix:** Filter by `Q(is_system=True) | Q(user=request.user)` (or ownership); add pagination. If genuinely global, document and confirm non-sensitive.

### H5. JWT access **and** refresh tokens stored in `localStorage` (and duplicated into non-httpOnly cookies)
- **Files:** `frontend/src/lib/store/auth/tokens.store.ts:4-5` (persisted to localStorage via `persistable.store.ts:31-33`); `frontend/src/routes/(auth)/reset-password-confirm/+page.svelte:82-91` (also `Cookies.set` via `js-cookie`, `secure` only in prod). Three copies with inconsistent lifetimes; logout (`tokens.store.ts:14`) clears the store but **not** the cookies → stale tokens persist after logout.
- **Impact:** Any XSS exfiltrates long-lived refresh tokens → account takeover.
- **Fix:** httpOnly+Secure+SameSite cookies set by the backend; the SPA should never see the refresh token; logout must clear every location.

### H6. GitHub OAuth token (full `repo` scope) injected into the privileged container as env var
- **Files:** `mission_service.py:671,1006` (`"AUTH_TOKEN": auth_token`); scope `["user","repo"]` in `base.py:199-202`. Visible via `docker inspect` and any in-container process; combined with C1/C2 it is trivially exfiltrated.
- **Fix:** Prefer short-lived, repo-scoped GitHub App installation tokens; pass via tmpfs/credential broker, not env; minimize scope.

### H7. GitHub token written into `.git/config` on disk
- **File:** `backend/holly/github_ext/services/git_repo_mgr.py:58-63`; helper `helpers.py:70-71`. `authenticated_github_url` builds `https://{token}@github.com/...` and `clone_from` persists it in the repo's `.git/config`, where it lingers and commonly leaks into subprocess error output/logs.
- **Fix:** Use `GIT_ASKPASS`/credential helper or `http.extraHeader` so the token is never written to disk.

### H8. loguru `diagnose=True` in all environments leaks secrets into logs
- **File:** `backend/holly/middleware/exceptions.py:23,33` (both file and stdout sinks), called unconditionally from `base.py:296`. `diagnose=True` dumps local variable *values* (API keys, tokens, JWTs) into tracebacks written to `./tmp/holly.log` and stdout.
- **Fix:** `diagnose=settings.DEBUG`, `backtrace=settings.DEBUG`.

### H9. `production.py` imports a non-existent module → settings crash on boot
- **File:** `backend/config/settings/production.py:6` `from .email import *`. There is **no** `email.py` in `backend/config/settings/` (verified). `develop.py:6` has the same. Email config is already inline (`production.py:38-49`), so the import is dead and fatal.
- **Fix:** Delete the import; add a CI smoke test that imports every settings module.

### H10. Data-destroying migration silently drops all mission↔repository links
- **File:** `backend/holly/holly/migrations/0014_missionrepos_alter_mission_repositories.py:15-60`. `RemoveField(mission, "repositories")` drops the M2M join table, then recreates a new M2M with **no `RunPython`** to migrate existing associations. Every existing mission loses its repositories irrecoverably.
- **Fix (forward):** Any future relation rebuild needs a data-migration step preserving rows.

### H11. `github_id` unique field with `default=0` → IntegrityError / migration failure
- **File:** `backend/holly/github_ext/models.py:8` (`CharField(..., default=0, unique=True)`); migrations `0015`/`0016`. The second row created without an explicit `github_id` collides on `"0"`. Applying `unique=True` over existing `0`-valued rows fails the migration with no backfill.
- **Fix:** Backfill real ids; drop `default=0`.

### H12. Background work runs in fire-and-forget daemon threads — no durability/retries
- **File:** `backend/holly/background_tasks/tasks.py:74-79` (`threading.Thread(..., daemon=True)`). Despite Celery being a dependency, "background tasks" use raw daemon threads: killed on any deploy/SIGTERM/crash, no retries, no time limits, leak DB connections, and a hung LLM call ties up a thread forever. Status lives only in cache (`tasks.py:93-120`) with read-modify-write races.
- **Fix:** Use real Celery tasks (`acks_late`, `max_retries`, `soft_time_limit`), or at minimum non-daemon threads + watchdog timeouts.

### H13. Task-status endpoint has no authorization
- **File:** `backend/holly/background_tasks/views.py:11-28`. No `@login_required`, no ownership check; returns the cached `result` (LLM output, repo data, tracebacks via `str(e)`) to anyone with the UUID.
- **Fix:** Require auth; store and verify the owning user.

### H14. Two competing token-refresh implementations race on 401
- **Files:** `frontend/src/lib/apis/middleware/token-refresh.middleware.ts` (wired into every client at `api.config.ts:43`) **and** `frontend/src/lib/apis/auth/token-manager.ts` (`withTokenRefresh`, wrapped around individual calls). On a 401 both can fire; their independent de-dup mechanisms defeat each other → multiple parallel refreshes racing to write `accessToken`.
- **Fix:** Keep the middleware; delete the wrapper (or vice-versa).

### H15. Near-zero test coverage on security-critical paths
- ~317 backend test functions exist, but **zero** tests for: container webhooks, Stripe/billing, Caddy, `background_tasks`, middleware (token refresh / exception). Frontend has 3 unit test files (one is `expect(1+2).toBe(3)`), so the dual refresh logic, open redirect, SSE leak, and markdown sanitization are untested. See §8.

---

## 3. Backend — Correctness & Architecture (High/Medium)

### B1. Webhook handler lacks a transaction boundary; Redis publish before DB commit
- **File:** `backend/holly/holly/services/webhook_handler.py:106-120`. `_create_notification` autocommits, and `_publish_update` fires, *before* `mission.save()`. A failed save leaves a "Mission Ready" notification for a still-old mission; SSE consumers observe uncommitted state.
- **Fix:** Wrap in `transaction.atomic()`; publish via `transaction.on_commit(...)`; `select_for_update()` the mission.

### B2. No webhook idempotency; duplicate delivery corrupts state
- **File:** `webhook_handler.py:68-126`. At-least-once delivery re-creates duplicate notifications, re-appends PR entries, and re-invokes `stop_container`. No event-id dedup.
- **Fix:** Container sends a unique `event_id`; record processed ids; `get_or_create` notifications on a natural key.

### B3. `_handle_pr_created` writes to non-existent model fields — PR data silently lost
- **File:** `webhook_handler.py:552-571`. `Mission` has no `metadata`, `pull_request_url`, or `pull_request_number` fields (verified). The `hasattr` guards are always false; the `metadata` branch sets a plain attribute never persisted (and not in `update_fields` at `:120`). PR info is discarded; only the transient notification survives.
- **Fix:** Add real fields and include them in `update_fields`, or persist to a related table.

### B4. State writes dropped because handlers mutate fields not in `update_fields`
- **File:** `webhook_handler.py:120`. The single `save(update_fields=[...])` silently drops any field a handler mutates outside that list. Fragile coupling.
- **Fix:** Save within a transaction without `update_fields`, or have handlers declare dirty fields.

### B5. Heavy network I/O embedded in the `Mission` model (fat model)
- **File:** `backend/holly/holly/models/mission.py:242-305`. `get_job_status()` does `requests.get`, instantiates `HollyContainerService`, resolves IPs; `is_container_ready()` does `httpx` calls. Function-local imports (`:252-254,284-285,299`) signal circular-dependency workarounds. Untestable without mocking HTTP.
- **Fix:** Move orchestration to the service layer; keep the model to data + trivial derived properties.

### B6. Redis client: broken singleton + blocking PING on every publish
- **File:** `backend/holly/holly/utils/redis_client.py`. `__init__` runs on every `RedisClient()` (`:16-41`); `publish()` calls `is_available()` (a network `ping`) then `publish()` — two round-trips, and with `socket_timeout=5` an unavailable Redis blocks the webhook thread up to 5s per publish (`:43-69`). `reconnect()` is defined but never called (`:93-115`), so after a first failure real-time features stay dead until restart.
- **Fix:** Drop pre-publish ping; handle publish exceptions; rely on redis-py pool reconnection; guard init with `_initialized`.

### B7. Caddy `_update_caddy` GET-modify-POST clobbers concurrent registrations; failure wipes all routes
- **File:** `backend/holly/holly/services/caddy_manager.py:39-65,72-74`. Full-config `/load` for incremental changes: two simultaneous registrations lose one route. `_get_config` returns `{}` on error, so a fetch failure rebuilds a near-empty config and wipes existing routes. `create_dns_record` is a no-op returning `True` (`:28-37`). loguru lines use stdlib `%s` args (`:21,24,32,36,64,73`) — **loguru does not interpolate `%s`**, so the domain/IP/error is dropped from logs.
- **Fix:** Use Caddy's granular route API; abort on fetch failure; implement or hard-fail DNS; switch logs to f-strings/brace style.

### B8. SSE generators lack disconnect/cleanup handling
- **File:** `backend/holly/holly/api/views/conversations.py:443-515,579-677`. No `try/finally`/`GeneratorExit` handling, so on client disconnect the upstream `httpx` stream may linger and partial `full_content` is never saved. Nested `async with` retry branch is fragile.
- **Fix:** Wrap generator bodies in `try/finally`; handle `CancelledError`/`GeneratorExit`; persist partial content.

### B9. Synchronous, silently-failing email on request path
- **File:** `backend/holly/utils/email_utils.py:116`. `email.send(fail_silently=False)` runs inline for welcome/password-reset; broad `except` returns `False` that callers often ignore → users silently never receive security-critical emails. Anymail tags set via `hasattr(email, "anymail_msg")` (`:108-113`) is always false, so tracking tags are dropped.
- **Fix:** Offload to Celery with retries; surface failures; set `email.tags`/`email.metadata` directly.

### B10. github_ext middleware: `MultipleObjectsReturned` 500 + logout-on-any-error
- **File:** `backend/holly/github_ext/middleware.py:31-32,44-74`. `SocialToken.objects.get(account__user_id=user.id)` only catches `DoesNotExist` — multi-account users (a supported feature) get a 500 on every request. On any refresh failure it logs the user out, so a transient GitHub outage logs everyone out; the synchronous refresh also blocks each request.
- **Fix:** Handle multiple tokens; narrow the exception; cache/short-circuit refresh attempts.

### B11. OAuth callback does not verify `state.user_id == request.user.id`
- **File:** `backend/holly/users/services/github_oauth_service.py:97-150`. The JWT-authenticated callback operates on `state_data.user_id` from cache without comparing to `request.user`. Combined with silent `SocialAccount` reassignment between users (`:284-296`, which also deletes the previous owner's installation rows), this is an account-linking/takeover surface. Whole create/update flow lacks `transaction.atomic()`/`select_for_update` (`:299-353`).
- **Fix:** Assert `state_data.user_id == request.user.id`; wrap in a transaction; add a partial unique constraint for one primary per user.

### B12. Inconsistent error contracts — failures masked as HTTP 200
- **Files:** `git.py:204,284,...`, `notifications.py:102-181`, `github_ext/api/router.py:50-149`, `users/api/router.py:110-143`. Permission denials, not-found, and server errors return `200 {success:false}` (some echo `str(e)` to the client). Monitoring on 4xx/5xx is defeated; `get_repository` even returns `None` against a declared `response=GitHubRepository`. Other modules (`llm.py`, `user_llm_api_key_views.py`) do it correctly with typed status maps.
- **Fix:** Standardize on ninja multi-status responses / `HttpError`; never echo raw exception text.

### B13. Broad `except Exception` swallowing across services
- Pervasive (`github_app_service.py`, `github_api.py:257`, `notifications.py`, `summary_service.py:86`, `analytics_service.py`, `users/models.py:56`). Converts programming errors and outages into empty/200/degraded results, hiding bugs from clients and monitoring; some log raw token-endpoint response bodies (`github_apps.py:93`, `github_app_service.py:56,98,103`).
- **Fix:** Catch specific exceptions; let unexpected ones reach a global 500 handler; never log raw token responses.

### B14. N+1 queries and missing pagination
- `conversations.py:125-133` (one `afirst()` per conversation; dead `except DoesNotExist`); `github_ext/api/router.py:98-110` (one query per account); `github_api.py:130-138` (recursive GitHub `get_contents` per dir). List endpoints without pagination: `conversations.py:104`, `knowledge.py:11`, `tools.py:11`, `llm.py:33`, `github_ext` repositories.
- **Fix:** Prefetch/`select_related`; add `@paginate`.

### B15. Client can select an arbitrary LLM; silent fallback masks bad input
- **File:** `conversations.py:571-574` (uses client-supplied `message_create.id` as the LLM id with no ownership validation), `:78-81` (`get_model_config` falls back to `aget(name="Holly")`, itself uncaught if missing/duplicated → 500).
- **Fix:** Validate the requested `llm_id` against `Q(is_system=True) | Q(user=request.user)`; guard the fallback.

### B16. `MCPProxyClient.post` mutates caller's dict and logs the api_key in plaintext
- **File:** `backend/holly/holly/api/proxy.py:205-209,238-239`. `data.update(self.model_config.model_dump())` injects the api_key into the caller's dict; `logger.info(f"POSTING {endpoint} with: {data}")` (`:208`) then logs it.
- **Fix:** Build a new dict; redact secrets in logs.

### B17. Naive datetimes, `summary_service` brittle event-loop fallback, weak self-registration
- `conversations.py:626,653` use `datetime.now()` (naive) under `USE_TZ=True`. `summary_service.py:78-82` branches on `str(ex)` substring matching and falls back to a blocking sync LLM call inside the loop; `:104` uses literal `api_key = "sk-secret"`. `custom_auth_views.py:62-84` enables email/password self-registration despite `SOCIALACCOUNT_ONLY=True`, with an 8-char-only password policy.
- **Fix:** `timezone.now()`; fix loop lifecycle / run sync work in an executor; remove the placeholder key; disable local registration or route through allauth.

---

## 4. Data Model & Migrations (Medium/Low)

- **M1.** Migration-merge churn: duplicate `0020` (`add_user_ownership_to_llm` vs `alter_notification_type`) reconciled by `0021_merge`; duplicate `0015` and **two** `0016_merge_*` files reconciled by `0017_merge`. Indicates reflexive `makemigrations --merge` instead of rebasing. (`backend/holly/holly/migrations/`)
- **M2.** `owner.username` is always `None`: the custom `User` sets `username = None` (`users/models.py:23`, email is `USERNAME_FIELD`), yet `mission.get_summary()` returns `self.owner.username` (`mission.py:227`) and `views.py:47` returns `user.username`. Use `email`/`name`.
- **M3.** Missing constraints/indexes: no `UniqueConstraint` on `MissionRepos(repository, branch_name)` (`mission.py:37-51`); no partial unique for one primary `UserGitHubAccount` per user (`github_models.py`); missing indexes on hot filters `is_primary`/`is_active`/`github_login` (`users/github_models.py`), `LLM.is_system`+`user`, `GitHubAccountInstallation.installation_id`. Redundant indexes on `MissionConversation` duplicate FK/unique indexes (`mission_conversation.py:81-84`).
- **M4.** String fields with `null=True` (two empty states) and `container_status` choices without a default (`mission.py:118-165`). Inline choice tuples instead of `TextChoices` (`mission.py:137-142`, `mission_conversation.py:41-47`). `file_tree = JSONField(blank=True)` with no `default` → `TypeError` on read when `None` (`github_ext/models.py:25`, read at `repo_persist.py:31`); use `default=list`.
- **M5.** `UserGitHubAccount.save()` override does a cross-row `update()` on every save with no atomicity/constraint (`github_models.py:88-96`); `create_from_social_account` double-writes (`:65-86`). Data migration `0005` uses `get()` (only catches `DoesNotExist`), `print()`s progress, and depends on `github_ext "__first__"` rather than the specific `0010` that creates the model it reads.
- **M6.** `Tools.config = JSONField()` has no default/validation; `Mission.get_tools()` blindly `tools.update(tool.config)` assuming dict (`tools.py:12`, `mission.py:307-311`).

---

## 5. Configuration & Secrets (Medium/Low)

- **CF1.** Heavy duplication between `production.py` and `develop.py` (~90% identical: CACHES, email, WhiteNoise, R2, the entire security block, CORS) with silent divergences. Extract a shared `deployed.py`.
- **CF2.** Duplicated/contradictory security settings in `production.py`: `SESSION_COOKIE_SECURE`/HSTS set twice (`:105-113` then `:130-136`), the later block gated on `not DEBUG` — a single `DJANGO_DEBUG=True` silently disables SSL redirect + secure cookies in "production." Make prod flags unconditional and assert `DEBUG is False`.
- **CF3.** Broken CORS regex in develop: `r"https://\+\.getholly\.ai$"` matches a literal `+` (`develop.py:123`). Production's `r"https://.*\.getholly\.ai$"` + `CORS_ALLOW_CREDENTIALS=True` (`production.py:118-121`) trusts *any* subdomain with credentials → subdomain-takeover risk. `CSRF_TRUSTED_ORIGINS` includes wildcard `https://*.getholly.ai` and a typo'd `https://app-getholly.ai` (`develop.py:20-23`).
- **CF4.** `EVENTSTREAM_ALLOW_ORIGIN = "*"` in base for all environments (`base.py:94`). Scope to known origins in prod.
- **CF5.** SQLite is the only DB backend (`base.py:134-139`), not overridden in prod/develop. See I3 for the split-brain consequence. `CACHES` uses `LocMemCache` in production (`production.py:27-32`) — not shared across workers, useless for throttling/rate-limit correctness. `STATIC_URL` is missing the `https://` scheme (`production.py:91`).
- **CF6.** `CSRF_USE_SESSIONS=True` together with `CSRF_COOKIE_*` (`base.py:245-247`) is contradictory (cookie settings inert); `CSRF_COOKIE_HTTPONLY=True` conflicts with develop exposing `X-CSRFToken` to JS. The `CSRF_TRUSTED_ORIGINS` default ternary (`base.py:248`) points the prod-ish branch at a dev URL.
- **CF7.** Inconsistent settings-module defaults across entrypoints: `celery.py:8` and `asgi.py:21` default to `config.settings.local`; `wsgi.py:14` defaults to `config.settings` → the empty `__init__.py` → boots with **no settings**. Standardize and require explicitly.
- **CF8.** Missing Celery reliability config: no `task_acks_late`, `task_reject_on_worker_lost`, `result_expires`, `broker_connection_retry_on_startup` (`base.py:343-364`); default `acks_late=False` loses tasks on worker crash. Empty `beat_schedule = {}` (`celery.py:20`). Result-backend URL builds `redis://@localhost...` (stray `@`) when password empty (`base.py:344-345`).
- **CF9.** Other defaulted secrets that don't fail-fast: GitHub OAuth `dummy_client_id`/`dummy_secret` (`base.py:205-206,317-318`), Stripe `dummy_*` (`:260-262`), `API_KEY="test_api_key"` (`:306`), VNC `NOVNC_DEFAULT_PASSWORD="vncpassword"` (`holly.py:31`, `code_editor.py:35`), test.py's committed 64-char real-looking key (`test.py:8-11`).
- **CF10.** `REST_MCP_SERVER_LOCAL = os.environ.get(..., False)` returns string `"False"` (truthy) when set (`mcp.py:21`); `holly.py`/`code_editor.py`/`mcp.py` use raw `os.environ` and ignore the `.env` that `base.py` loads — config sprawl.
- **CF11.** No error tracking anywhere (no Sentry); stdlib `LOGGING` only wires the `allauth` logger; sole error sink is an ephemeral container-local `./tmp/holly.log` (`base.py:280-296`). `/docs` Swagger is always exposed (`urls.py:42-44`); the `events/` SSE channel is hardwired to `["test"]` (`urls.py:76`).

---

## 6. Infrastructure, Docker & CI/CD (High/Medium/Low)

- **I1.** Tracked env files: `.gitignore` ignores `.env` but **not** `.env.local`/`.env.production`, both of which are committed (`.env.local` holds placeholders, `.env.production` is tracked-but-empty). A loaded gun for secret leakage. Add `.env.local`, `.env.*`, `!.env.example`; `git rm --cached` the tracked ones.
- **I2.** Dockerfile defects (`Dockerfile`): runs as **root** (no `USER`); single-stage; installs `docker.io` + full NVM/Node toolchain into a Python web image; `COPY . /app/` (`:62`) *before* `uv sync` (`:65`) busts the dependency cache every build and bakes `.git`, `.env.local`, `db.sqlite3`, `node_modules` into layers (**no root `.dockerignore`**); `LABEL BUILD_ID="$(date +%s)"` (`:3`) is a literal, not evaluated. **`CMD ["./scripts/run_server.sh"]` references a script that does not exist** in the repo — the `web` image cannot start as built.
- **I3.** SQLite in production with split-brain: `docker-compose.yml:25-28` bind-mounts `db.sqlite3` into `web` only; `celery`, `celery-beat` (and `web2` in `deploy_prd.yml:84`) run `config.settings.production` with **no DB mount**, each getting a separate ephemeral SQLite. Workers and web operate on *different databases*; SQLite's single-writer also causes `database is locked` under load. Migrate to Postgres (already used in `run_tests.yml`).
- **I4.** Weak/absent service auth: RabbitMQ `holly`/`holly` (`docker-compose.yml:57-58`), Redis with **no** `requirepass`, base defaults `amqp://guest:guest@...` (`base.py:343`). Any process on the docker network (incl. untrusted workspace containers) can inject Celery tasks (RCE via task payloads) or flush data.
- **I5.** No resource limits on any service; redis/rabbitmq volumes commented out (queue/results lost on restart); sensitive ports (`8181`, VNC `6901/5901`, `8090`) bind `0.0.0.0`. No healthchecks on `web`/`celery`. Add `mem_limit`/CPU limits, named volumes, bind sensitive ports to `127.0.0.1`, add healthchecks.
- **I6.** CI/CD: `pr_preview.yml:188-191` runs `cat .env.develop`, printing all secrets to logs; deploy workflows build `.env` via `echo "${{ secrets.X }}"`; a long-lived `*.private-key.pem` lives on the self-hosted runner. No workflow declares `permissions:` (inherits write `GITHUB_TOKEN`); actions pinned to mutable tags (mixed `@v3`/`@v4`), not SHAs; `deploy_prd.yml` deploys on every push to `main` with **no dependency on tests passing**; `run_tests.yml` uses `--continue-on-collection-errors` + `continue-on-error` so the "gate" passes while tests are broken; `provenance: false` disables SLSA attestation. `.env.test` referenced but absent.
- **I7.** Pre-commit gaps: `pre-commit.yml` sets `GITGUARDIAN_API_KEY` but `.pre-commit-config.yaml` has **no** ggshield hook (only `detect-private-key`, which missed the committed `.env.local`); no `mypy`, no `hadolint`, no `uv lock --check`.
- **I8.** Supply chain: `markdown-mermaidjs` pulled from a third-party git repo with no `rev` pin (`pyproject.toml:88`), contradicting the loose `markdown-mermaidjs>=2.0.0` (`:37`); base images use mutable tags, no digests; `node:23` is non-LTS (`.nvmrc` says 22); inconsistent submodule handling (`submodules: false`+manual vs `recursive`) across workflows.
- **I9.** Observability: `prometheus.yml` scrapes only itself + cAdvisor (no app `/metrics`, no alert rules); no compose log rotation/limits → unbounded host logs; loguru file sink has no `rotation=`.

---

## 7. Frontend (High/Medium/Low)

- **F1 (structural).** **Two parallel frontends.** A legacy server-rendered Alpine/vanilla-JS app (`backend/static/js/`, session+CSRF auth) and a SvelteKit SPA (`frontend/src/`, JWT-in-localStorage). `frontend/scripts/update-django-template.ts` builds the SPA's `index.html` and injects its script/preload tags into a Django template, copying `_app/*` into Django static. Result: **two auth models and two CSRF strategies in the same session**, doubled/divergent maintenance (voice transcription exists in *three* places; tab-manager twice). This is the single biggest structural problem — every security/UX fix must be made in 2–3 places.
- **F2.** See H5 (token storage) and H14 (dual refresh) — both High.
- **F3.** Markdown XSS surface is currently mitigated (`MarkdownRenderer.svelte:58` `{@html}` with `html:false` + DOMPurify) but fragile and untested; no `rel="noopener"` hardening. Add a regression test.
- **F4.** `innerHTML` injection in legacy JS from repo-controlled data: `backend/static/js/file_extension_filter.js:213-223` interpolates a file extension (attacker-controllable via crafted filenames) into an attribute. Build via `createElement`/`textContent`.
- **F5.** Open redirect: `frontend/src/routes/github/oauth/callback/+page.svelte:46-47,65` does `goto(response.redirect_url)`; `+layout.ts:56-58` round-trips a `?redirect=` param. Whitelist internal paths; reject absolute/`//host` URLs.
- **F6.** No CSP / security headers anywhere (`app.html`, `nginx.conf`, `svelte.config.js`). With tokens in localStorage this removes the main defense-in-depth against exfiltration.
- **F7.** SSE reconnect leaks `EventSource`s and timers: `CloneStatusMonitor.svelte:58-69` reconnects without closing the old source and never clears the retry timeout in `onDestroy`. `EventSource` can't send the `Bearer` header (`:37`), so the SSE endpoint relies on cookie auth — inconsistent with the rest of the JWT app, and 401s there are unrecoverable by the refresh middleware.
- **F8.** Client-only auth guard with global `ssr=false` (`+layout.ts:8,51`) trusting a user-controlled localStorage value; `Mic.svelte:122` reads `localStorage.token` (wrong key — tokens are under `accessToken`) so the call is broken/unauthenticated. Real enforcement must be backend-side.
- **F9.** Generated API client is a committed local `.tgz` built with `--skip-validate-spec`; `openapi.json` (146 KB) and `gen/` committed → silent drift from the live backend. 35 `any`/`ts-ignore` across 23 files; auth-error detection via `message.includes("401")` string matching; extensive emoji `console.log` of auth flow that may survive prod builds; dead/commented code (`hooks.client.ts:12-54`).
- **F10.** Accessibility: progress/connection indicators are `<div>`s with no `role`/`aria-live` (`CloneStatusMonitor.svelte:142-196`); OAuth spinner lacks `aria-busy`.

*(Positive: no embedded secrets found in the frontend bundle; LLM keys are returned masked.)*

---

## 8. Testing & Observability (High/Medium)

- **T1.** Critical paths untested (verified): **0** tests for container webhooks, Stripe/billing, Caddy, `background_tasks`, and middleware (token refresh / exception). The `users` OAuth service (`github_oauth_service.py`) has no dedicated tests. Given webhooks are unauthenticated and OAuth handles account linking, these are the highest-risk untested areas.
- **T2.** `mypy` is strict on paper but undermined: five `ignore_errors=true` overrides incl. `*.settings.*` (where the `.email` import bug lives) and `*.tests.*`; `django-stubs` is installed but the `mypy_django_plugin` is never wired up, so Django typing is inert (`pyproject.toml:165-197`). The strictness is largely cosmetic.
- **T3.** `--continue-on-collection-errors` and `continue-on-error` make the CI test gate non-blocking (see I6). A `test_create_pull_request.py` exists yet the endpoint has a runtime `AttributeError` (H2) — the test likely over-mocks; add an integration test that exercises the real `MissionRepos` relationship.
- **T4.** No error aggregation/alerting (no Sentry); ephemeral local log file is the only sink (CF11). Add Sentry (`sentry-sdk[django,celery]`) and ship logs off-host.

---

## 9. Dependencies (Medium/Low)

- **D1.** Both `google-genai` (new) **and** `google-generativeai` (deprecated) are dependencies (`pyproject.toml:36,42`) — overlapping `google.*` namespaces, conflicting `protobuf`/`grpcio`, incomplete migration. Standardize on `google-genai`.
- **D2.** `aider-chat>=0.72.2` as a runtime dependency (`:11`) drags in a very large transitive tree (multiple LLM SDKs, litellm, tree-sitter) and tight pins → resolver-conflict surface and image bloat. Isolate or move out of runtime.
- **D3.** `django>=5.1.5` listed twice (`:9,12`); `coverage`/`pytest`/`mypy`/`ruff`/`pre-commit`/`pytest-django`/`django-extensions`/`factory-boy`/`faker`/`black` appear in both `[project].dependencies` and the dev group → test/lint tooling shipped into production images. De-dupe; move dev tooling to the dev group only.
- **D4.** One anomalous hard pin `httpx==0.27.2` amid otherwise unbounded `>=` ranges (`:14`). Build with `uv sync --frozen`; add upper bounds on framework deps. `requires-python = ">=3.11, <3.12"` blocks 3.12/3.13 — document why.
- **D5.** Three API layers coexist (DRF + django-ninja + FastAPI). `INSTALLED_APPS` uses ninja, not `rest_framework` — DRF may be dead weight. `transformers>=4.40.0` is heavy; confirm it's needed at runtime.

---

## 10. Prioritized Remediation Roadmap

**Phase 0 — Stop the bleeding (security-critical, do now)**
1. C1 remove `privileged: true`; C2 auth the in-container API + stop publishing ports to `0.0.0.0`; C3 HMAC-sign + auth the webhook.
2. C4/C5 remove all secret/salt defaults, fail-fast in non-DEBUG, verify JWT `SIGNING_KEY` resolves to the real secret; rotate and re-encrypt.
3. C6 allowlist Caddy `ip:port`. H9 fix the `production.py` `.email` import (it won't boot). H8 `diagnose=False` in prod.
4. H1/H3/H4 add ownership scoping (PR creation, repo-token, knowledge/tools/LLM list). H2 fix the broken `create_pull_request`.

**Phase 1 — Correctness & data integrity**
5. H5/H14 fix token storage + dual refresh. H10/H11/B3 model/migration data-loss and field bugs. B1/B2/B4 webhook transactions + idempotency. B10/B11 multi-account 500 + OAuth state binding.
6. H12/H13 replace daemon-thread background jobs with Celery + authorize task-status. I3 move to Postgres.

**Phase 2 — Hardening & reliability**
7. CF2/CF3/CF4 CORS/cookie/eventstream tightening. I1/I2 env-file hygiene + Dockerfile (multi-stage, non-root, `.dockerignore`, fix missing CMD). I4/I5 service auth, resource limits, volumes. I6 CI gating + secret-log removal + `permissions:` + SHA pinning.
8. CF11/T4 add Sentry + centralized logging. B6/B7 Redis/Caddy concurrency. F6 add CSP.

**Phase 3 — Structural debt**
9. F1 converge on a single frontend with one auth/CSRF model. B5/B12 extract business logic from models/views into services; standardize error contracts. CF1/CF7 de-sprawl settings. M1 fix migration-merge hygiene. T2 wire up django-stubs and narrow mypy ignores. D1–D5 dependency cleanup.

---

*This document was produced by an adversarial review pass and is intended as a prioritized backlog. Findings include file/line references for direct verification. Some severities depend on deployment specifics (e.g., whether `SECRET_KEY`/`SALT_KEY` env vars are actually set in production) — those are flagged as fail-open risks that should be made fail-closed regardless.*
