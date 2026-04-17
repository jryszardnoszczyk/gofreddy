# Agency Visibility Dashboard Implementation Plan

**Date:** 2026-04-17
**Scope:** Per-client dashboard at `app.gofreddy.ai` showing each client the sessions JR runs for them — action log, iteration log, transcript. Plus the CLI gaps (`auth` + `session` commands) that make the flow work.
**Rule:** **COPY, DON'T REWRITE** — every piece exists in `/Users/jryszardnoszczyk/Documents/GitHub/freddy/`. Agent runs on JR's laptop; backend is a passive receiver.

**Phase 1 already shipped** (commits `c5eb9da` / `f9efc86` / `dc1ff0f`): Supabase auth, `/login`, `/portal/<slug>` placeholder, hardened FastAPI, 22 integration tests green, DB: `users`, `clients`, `user_client_memberships`, `api_keys`.

**Non-goals:** no brand/social monitoring, no agent chat/SSE/orchestrator, no conversations/workspace/preferences/content-gen/policies/extraction, no video/deepfake/generation/SEO/GEO routers, no billing.

---

## Architecture

| Layer | Surface | Storage |
|---|---|---|
| Landing (shipped) | `gofreddy.ai` via GitHub Pages | — |
| React SPA | `app.gofreddy.ai` — `/login`, `/dashboard/sessions` (inline detail), `/dashboard/settings` (API keys) | — |
| FastAPI on Fly | `api.gofreddy.ai` — `/v1/sessions/*`, `/v1/sessions/{id}/{actions,iterations,transcript}`, `/v1/api-keys/*`, `/v1/auth/*` (Phase 1), `/health` | — |
| Supabase Postgres | Phase 1: `users`, `clients`, `user_client_memberships`, `api_keys` · this plan: `agent_sessions` (+ `client_id` + `transcript`), `action_log`, `iteration_log` | — |
| Cloudflare R2 | Session iteration logs + state snapshots | `session-logs/{id}/iteration-NNN.txt` + `state-NNN.md`. Buckets: `gofreddy-prod`, `gofreddy-test`. Transcripts stay in Postgres. |
| CLI (JR's laptop) | `freddy auth login/whoami/logout`, `freddy session start/end/status`, `freddy iteration push`, `freddy transcript upload --from-hook` | `~/.freddy/{config,session}.json` |

Auth at backend: Bearer JWT (browser) or `X-API-Key` (CLI).

---

## Scope snapshot

### Backend Python

| Action | What |
|---|---|
| **cp -r** | `src/sessions/` — overwrites gofreddy's `FileSessionRepository` with freddy's `PostgresSessionRepository` + `R2SessionLogStorage` |
| **cp 2 routers** | `sessions.py`, `api_keys.py` |
| **drop** | `media.py` router — requires `MediaService` + `PostgresMediaAssetRepository` + `R2MediaStorage` not in scope; visibility lane doesn't upload media |
| **reuse Phase 1** | `/health` (inline `@app.get("/health")`) — skip freddy's `health.py` router (drags in `..schemas.*`) |
| **edit** | `src/api/dependencies.py` — add `get_current_user_id`, `get_api_key_repo`, `get_session_service` |
| **edit** | `src/api/main.py` — wire `ApiKeyRepo` + `aioboto3.Session` + `R2VideoStorage` + `R2SessionLogStorage` + `PostgresSessionRepository` + `SessionService` in lifespan; register 2 routers |
| **extend** | `src/api/users.py` — add `ApiKeyRecord` + `ApiKeyRepo` (port freddy `src/billing/repository.py` L214-265 verbatim) |
| **Explicitly NOT copied** | 16 routers (agent, analysis, batch, competitive, conversations, deepfake, evaluation, generation, geo, monitoring, preferences, publishing, seo, usage, video_projects, webhooks, workspace) + 14 modules (orchestrator, brands, creative, demographics, evolution, stories, trends, search, conversations, workspace, preferences, extraction, content_gen, policies, billing) |

### CLI

| Action | What |
|---|---|
| **mv** | `cli/freddy/api.py` → `providers.py` (preserves existing provider factory) |
| **cp** | `freddy/cli/freddy/api.py` → `api.py` (REST client), `output.py`, `commands/auth.py`, `commands/session.py` |
| **edit in place** | `cli/freddy/main.py` — add `auth, session` to import line + 2 `app.add_typer` calls (don't overwrite — freddy's main imports ~30 commands we don't have) |
| **merge** | `cli/freddy/config.py` — gofreddy's `Config(clients_dir)` + freddy's `Config(api_key, base_url, delete_config)` into one nullable dataclass. Snippet in M3. |
| **per-file swap** | `audit.py:13` + `client.py:10` — `from ..api import ...` → `from ..providers import ...` |
| **leave alone** | `transcript.py`, `iteration.py`, `session.py` (module), `auto_draft.py`, `save.py`, `setup.py`, `sitemap.py` — byte-identical or no `..api` imports |

### Frontend

| Action | What |
|---|---|
| **cp -r** | `freddy/frontend/` → `gofreddy/frontend/` |
| **keep** | `LoginPage`, `AuthCallbackPage`, `SessionsPage` (handles detail inline), `SettingsPage` (API keys only). Components: `NavigationRail`, `ProtectedRoute`, `AuthProvider`, `ErrorBoundary`, `Toast`, `Button`, `Card`, `Badge`, `EmptyState`, `Skeleton`, `PageHeader`, `AlertBanner`, `ApiKeysSection`, plus anything `SessionsPage` transitively needs. Hooks: `useAuth`, `useSessions`, `useDocumentTitle`, `useToast`. Lib: `api.ts`, `api-types.ts`, `routes.ts`, `index.css`, `cn.ts`, `supabase.ts`. |
| **delete pages** | `MonitoringPage`, `ChatPage`, `LibraryPage`, `PricingPage`, `UsagePage`, `LandingPage`, `pages/library/`, `content/marketing.ts` |
| **delete components** | `components/canvas/` (whole tree), `components/layout/ChatCanvasLayout.tsx`, `components/studio/`, `components/video-gen/`, `components/chat/`, `components/conversations/`, `components/landing/`, `components/monitoring/`, `components/settings/UsageBillingSection.tsx` |
| **delete hooks** | `useChat`, `useConversations`, `useWorkspace`, `useMonitors`, `useMonitorDetail`, `useLibraryData`, `useLibraryFilters`, `useLibraryGroups`, `useVideoProjects`, `useBatchProgress`, `useGenerationProgress`, `useDesktopSplitView`, `useResizablePanel`, `useStudioStaging` |
| **delete lib** | `capabilities.ts`, `platformStyles.ts`, `sanitizeUrl.ts`, `videoUrl.ts` |
| **delete tests** | `find frontend/src -name "*.test.ts*" -delete` |
| **create** | `components/layout/DashboardLayout.tsx` — thin `NavigationRail + Outlet` wrapper. Snippet in M4. |
| **edit** | `SettingsPage.tsx` — delete line 12 (`UsageBillingSection` import) and line 379 (`<UsageBillingSection id="usage-billing" />`). Trim `NavigationRail.tsx` to Sessions + Settings links only. |
| **routing** | `/dashboard/*` wraps in `<DashboardLayout />`. No `/dashboard/sessions/:id` — SessionsPage handles detail inline. |

### Database (from freddy `scripts/setup_test_db.sql` L1561-1645)

Tables: `agent_sessions` (+ inline `client_id UUID REFERENCES clients(id) ON DELETE SET NULL`), `action_log`, `iteration_log`. Keep trigger `update_agent_sessions_updated_at` + indexes + unique-constraint. Drop freddy's `DO $$ ... RENAME operator_id → org_id` block (legacy). No RLS — FastAPI-layer gating via `user_client_memberships`.

---

## Execution phases

### Preflight — reset to Phase 1

```bash
cd gofreddy
git reset --hard 1d00cfe                     # wipes v2 bloat; Phase 1 intact
supabase db reset --local
uv run pytest tests/test_api/ -q             # expect 22/22
```

### M1 — DB schema

Write `supabase/migrations/20260418000001_sessions.sql` — extract freddy L1561-1645 with two tweaks:
- `agent_sessions` gains inline `client_id UUID REFERENCES clients(id) ON DELETE SET NULL` + index `idx_sessions_client_tenant ON agent_sessions (client_id, started_at DESC) WHERE client_id IS NOT NULL`
- Drop freddy's `DO $$ RENAME operator_id → org_id` block (legacy, doesn't apply to a fresh table)

Everything else verbatim: CHECK constraints, `UNIQUE INDEX idx_sessions_one_running_per_org_client`, trigger, `action_log` + index, `iteration_log` + index.

```bash
cp /Users/jryszardnoszczyk/Documents/GitHub/freddy/scripts/ci_bootstrap.sql scripts/
supabase db reset --local
```

Commit.

### M2 — Backend

```bash
cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy
cp -r /Users/jryszardnoszczyk/Documents/GitHub/freddy/src/sessions              src/
cp /Users/jryszardnoszczyk/Documents/GitHub/freddy/src/api/routers/sessions.py  src/api/routers/
cp /Users/jryszardnoszczyk/Documents/GitHub/freddy/src/api/routers/api_keys.py  src/api/routers/
```

**Inline trims:**

| File | Surgery |
|---|---|
| `routers/sessions.py` | Tenant surgery required — patch below. |
| `sessions/models.py` | Add `client_id: UUID \| None` to `Session` dataclass. |
| `sessions/repository.py` | Add `client_id` to INSERT + SELECT SQL; add `list_sessions_for_client_ids(client_ids, ...)` method (`WHERE client_id = ANY($1::uuid[])`). |
| `sessions/service.py` | Add thin wrapper `list_sessions_for_client_ids(...)` delegating to the new repo method. |
| `routers/api_keys.py` | Swap `BillingRepository` + `get_billing_repository` → `ApiKeyRepo` + `get_api_key_repo`. |

**Sessions router patch.** Freddy filters every endpoint by `org_id = auth.user_id` (SaaS). Gofreddy needs `client_id + user_client_memberships` (agency). Add helper at top of router:

```python
from ..membership import resolve_accessible_client_ids

async def _scope(request: Request, auth: AuthPrincipal) -> list[UUID] | None:
    """Returns list of client_ids caller can see, or None for admin (all)."""
    return await resolve_accessible_client_ids(
        request.app.state.db_pool, auth.user_id
    )
```

Add `resolve_accessible_client_ids(pool, user_id) -> list[UUID] | None` to `src/api/membership.py` (Phase 1 file): returns `None` if user has any `role='admin'` membership; else list of client_ids from their non-admin memberships.

Patch every endpoint:
- **POST `/v1/sessions`** — request schema gains `client_id: UUID`. Check `client_id in (accessible or [all])`; 403 otherwise. Stamp `org_id=auth.user_id` (freddy compat) + `client_id=body.client_id`.
- **GET `/v1/sessions`** — if `_scope()` returns None, list all; else call `list_sessions_for_client_ids(client_ids, ...)`.
- **GET/PATCH `/v1/sessions/{id}`**, **POST `/v1/sessions/{id}/{actions,iterations,transcript}`** — fetch session, check `session.client_id in accessible_ids` (or admin); 403 otherwise.

`SessionsPage` stays unchanged — scope filter is server-side.

**Extend `src/api/users.py`:**
- `ApiKeyRecord` dataclass: `id, user_id, key_prefix, name, created_at, last_used_at, expires_at, revoked_at` + `is_active` property
- `ApiKeyRepo` porting freddy `src/billing/repository.py` L214-265 verbatim: `create_api_key_atomic`, `list_api_keys`, `revoke_api_key` (+ `APIKey` dataclass L22-32, `_row_to_api_key` helper L546-556)

**Additive merge into `src/api/dependencies.py`:**
```python
async def get_current_user_id(principal: AuthPrincipal = Depends(get_auth_principal)) -> UUID:
    return principal.user_id

def get_api_key_repo(request: Request) -> ApiKeyRepo:
    return request.app.state.api_key_repo

def get_session_service(request: Request):
    return request.app.state.session_service
```

**Additive merge into `src/api/main.py` lifespan** (constructors verified against freddy — do not deviate):
- `R2VideoStorage(session: aioboto3.Session, config: R2Settings)` — `freddy/src/storage/r2_storage.py:107`
- `R2SessionLogStorage(video_storage, r2_config)` — `freddy/src/sessions/log_storage.py:24`
- `SessionService(repository)` — `freddy/src/sessions/service.py:17` (no log_storage/settings kwargs)

```python
import aioboto3
from ..storage.config import R2Settings
from ..storage.r2_storage import R2VideoStorage
from ..sessions.repository import PostgresSessionRepository
from ..sessions.log_storage import R2SessionLogStorage
from ..sessions.service import SessionService
from .users import ApiKeyRepo

app.state.api_key_repo = ApiKeyRepo(pool)

try:
    r2_config = R2Settings()
    aws_session = aioboto3.Session()
    app.state.r2_storage = R2VideoStorage(aws_session, r2_config)
    app.state.session_log_storage = R2SessionLogStorage(app.state.r2_storage, r2_config)
except Exception:
    logger.warning("R2 init failed — session log uploads disabled", exc_info=True)
    app.state.r2_storage = None
    app.state.session_log_storage = None

session_repo = PostgresSessionRepository(pool)
app.state.session_service = SessionService(session_repo)

try:
    yield
finally:
    if app.state.r2_storage is not None:
        await app.state.r2_storage.close()
    await pool.close()
```

Transcripts go in `agent_sessions.transcript` (Postgres), not R2.

Register routers:
```python
app.include_router(sessions_router.router, prefix="/v1")
app.include_router(api_keys_router.router, prefix="/v1")
```

`pyproject.toml`: zero new deps. Commit.

### M3 — CLI

**Step 0 — pre-rename bug fixes** (break `freddy audit monitor` today; fix before the rename):
- `cli/freddy/api.py:60` — `NewsAdapter` → `NewsDataAdapter` (also line 62)
- `.env.example` — prefix env vars to match Settings classes:
  - `FOREPLAY_API_KEY` → `COMPETITIVE_FOREPLAY_API_KEY`
  - `ADYNTEL_API_KEY` → `COMPETITIVE_ADYNTEL_API_KEY`
  - `ADYNTEL_EMAIL` → `COMPETITIVE_ADYNTEL_EMAIL`
  - `XPOZ_API_KEY` → `MONITORING_XPOZ_API_KEY`
  - `NEWSDATA_API_KEY` → `MONITORING_NEWSDATA_API_KEY`
- `cli/freddy/commands/setup.py` — update env-var check list to prefixed names

```bash
mv cli/freddy/api.py cli/freddy/providers.py
cp /Users/jryszardnoszczyk/Documents/GitHub/freddy/cli/freddy/api.py              cli/freddy/
cp /Users/jryszardnoszczyk/Documents/GitHub/freddy/cli/freddy/output.py           cli/freddy/
cp /Users/jryszardnoszczyk/Documents/GitHub/freddy/cli/freddy/commands/auth.py    cli/freddy/commands/
cp /Users/jryszardnoszczyk/Documents/GitHub/freddy/cli/freddy/commands/session.py cli/freddy/commands/
```

**Edit `cli/freddy/main.py` in place:**
```python
from .commands import (
    audit, auto_draft, client, iteration, save, setup, sitemap, transcript,
    auth, session,
)
app.add_typer(auth.app, name="auth")
app.add_typer(session.app, name="session")
```

**Merge `cli/freddy/config.py`** (don't overwrite — schemas collide):
```python
import json, os
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_PATH = Path.home() / ".freddy" / "config.json"

@dataclass
class Config:
    clients_dir: Path | None = None
    api_key: str | None = None
    base_url: str | None = None

def load_config() -> Config | None:
    if not CONFIG_PATH.exists():
        return None
    data = json.loads(CONFIG_PATH.read_text())
    return Config(
        clients_dir=Path(data["clients_dir"]) if data.get("clients_dir") else None,
        api_key=data.get("api_key"),
        base_url=data.get("base_url"),
    )

def save_config(**kwargs) -> None:
    existing = load_config() or Config()
    for k, v in kwargs.items():
        if v is not None:
            setattr(existing, k, v)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: (str(v) if isinstance(v, Path) else v)
               for k, v in asdict(existing).items() if v is not None}
    CONFIG_PATH.write_text(json.dumps(payload))
    os.chmod(CONFIG_PATH, 0o600)

def delete_config() -> None:
    CONFIG_PATH.unlink(missing_ok=True)
```

Update every agency-command call site for `load_config() -> Config | None`:
```python
config = load_config()
if config is None or config.clients_dir is None:
    raise typer.BadParameter("Run `freddy setup` first.")
```

`grep -rn "load_config()" cli/freddy/commands/` to find all sites.

**Import swaps:**
```bash
sed -i '' 's/from \.\.api import/from ..providers import/' cli/freddy/commands/audit.py
sed -i '' 's/from \.\.api import/from ..providers import/' cli/freddy/commands/client.py
grep -rn "from \.\.api import" cli/freddy/commands/   # expect zero
```

**Test fixups:**
- `tests/test_cli_evaluate_critique.py`: `"cli.freddy.api.make_client"` → `"cli.freddy.providers.make_client"`
- `cli/tests/test_api.py`: fix or delete (broken today — wrong absolute import path)

Commit.

### M4 — Frontend

```bash
cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy
cp -r /Users/jryszardnoszczyk/Documents/GitHub/freddy/frontend/ frontend/
rm -rf frontend/node_modules

# Pages
rm frontend/src/pages/{MonitoringPage,ChatPage,LibraryPage,PricingPage,UsagePage,LandingPage}.tsx
rm -rf frontend/src/pages/library/
rm frontend/src/content/marketing.ts

# Components (drag in deleted hooks)
rm -rf frontend/src/components/{canvas,studio,video-gen,chat,conversations,landing,monitoring}
rm -f  frontend/src/components/layout/ChatCanvasLayout.tsx
rm -f  frontend/src/components/settings/UsageBillingSection.tsx

# Hooks
for h in useChat useConversations useWorkspace useMonitors useMonitorDetail \
         useLibraryData useLibraryFilters useLibraryGroups useVideoProjects \
         useBatchProgress useGenerationProgress useDesktopSplitView \
         useResizablePanel useStudioStaging; do
  rm -f frontend/src/hooks/${h}.ts
done

# Lib + tests
rm -f frontend/src/lib/{capabilities,platformStyles,sanitizeUrl,videoUrl}.ts
find frontend/src -name "*.test.ts*" -delete
```

**Create `frontend/src/components/layout/DashboardLayout.tsx`:**
```tsx
import { Outlet } from "react-router-dom";
import { NavigationRail } from "./NavigationRail";

export function DashboardLayout() {
  return (
    <div className="flex h-screen bg-background">
      <NavigationRail />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
```

Trim `NavigationRail.tsx` — drop `useConversations`-based history UI; keep Sessions + Settings links.

**Edit `SettingsPage.tsx`:** delete line 12 (`import { UsageBillingSection } ...`) and line 379 (`<UsageBillingSection id="usage-billing" />`).

**Rewire `frontend/src/main.tsx`:**
- `/` → redirect to `/login` (unauthed) or `/dashboard/sessions` (authed)
- `/login`, `/auth/callback` — top-level, no layout
- `/dashboard/*` wraps in `<DashboardLayout />`:
  - `/dashboard/sessions` → `<SessionsPage />` (inline detail, no `:id` sub-route)
  - `/dashboard/settings` → `<SettingsPage />`
- `/portal/:slug` → redirect to `/dashboard/sessions?client=<slug>`

**Env vars** (`frontend/.env`):
```
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_API_URL=http://localhost:8080        # name verified at frontend/src/lib/api.ts:62
```

```bash
cd frontend && npm install && npm run api:generate && npm run build
# npm run api:generate requires the backend running locally on VITE_API_URL
```

Expect 2-4 rounds of dead-import fixes.

**End-to-end verification** (acceptance criteria — the only explicit check that the whole pipeline works):
```bash
# Terminal 1: backend
uv run uvicorn src.api.main:app --port 8080

# Terminal 2: frontend
cd frontend && npm run dev                           # localhost:5173

# Browser: log in via Supabase → expect redirect to /dashboard/sessions (empty)

# Terminal 3: laptop CLI
freddy auth login --api-key <key> --base-url http://localhost:8080
freddy session start --client demo-clinic --purpose frontend-test
freddy iteration push --session-id <id> --iteration 1 --output 'ran fine'
freddy session end --session-id <id>

# Browser: refresh /dashboard/sessions → session appears with the iteration entry
# Settings → API Keys → generate key → confirm it works with the CLI
```

Commit.

### M5 — Deploy

1. **Supabase:** create project → capture `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL` → `supabase db push`.
2. **R2:** create buckets `gofreddy-prod` + `gofreddy-test` + API token (R2:Edit) → capture `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`.
3. **Fly:**
   ```bash
   flyctl launch --name gofreddy-api --region iad --no-deploy
   flyctl secrets set SUPABASE_URL=... SUPABASE_ANON_KEY=... SUPABASE_JWT_SECRET=... \
     DATABASE_URL=... R2_ACCOUNT_ID=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... \
     R2_BUCKET_NAME=gofreddy-prod ENVIRONMENT=production
   flyctl deploy
   flyctl certs create api.gofreddy.ai
   ```
4. **Frontend:** `npm run build` → deploy `dist/` to Vercel / Cloudflare Pages / Fly static.
5. **DNS:** CNAME `api.gofreddy.ai` → `gofreddy-api.fly.dev`; CNAME `app.gofreddy.ai` → frontend host.

End-to-end verify: laptop CLI → production API → production dashboard.

---

## Env vars

```bash
# Auth (Phase 1 already set)
SUPABASE_URL= SUPABASE_ANON_KEY= SUPABASE_JWT_SECRET= DATABASE_URL=

# R2 (session logs only — transcripts are in Postgres)
R2_ACCOUNT_ID= R2_ACCESS_KEY_ID= R2_SECRET_ACCESS_KEY= R2_BUCKET_NAME=gofreddy-prod

# Runtime
ENVIRONMENT=production
```

Backend makes no LLM/external API calls. **Agency-local (CLI only, not Fly secrets):** `DATAFORSEO_LOGIN/PASSWORD`, `COMPETITIVE_FOREPLAY_API_KEY`, `COMPETITIVE_ADYNTEL_API_KEY`, `COMPETITIVE_ADYNTEL_EMAIL`, `MONITORING_XPOZ_API_KEY`, `MONITORING_NEWSDATA_API_KEY`, `GEMINI_API_KEY` — power `freddy audit` on JR's laptop.

---

## Risks

| Risk | Mitigation |
|---|---|
| `cp -r src/sessions` overwrites gofreddy's `FileSessionRepository`. | Verified: only 3 files inside `src/sessions/` reference it; no external consumers. |
| `api_keys.py` imports `BillingRepository` not being ported. | Port 3 methods to `ApiKeyRepo` in `src/api/users.py`; swap import. |
| Frontend has dead imports after purge. | Iterative `npm run build` → fix → repeat. Biggest domino: `ChatCanvasLayout` deletion. |
| Phase 1's 22 tests regress. | `uv run pytest tests/test_api/ -q` after each phase (expect 22/22). |

---

## Open decisions

1. **Invite-only signup.** JR creates users + memberships via psql; clients log in with provided credentials.
2. **SessionEnd hook.** Plan ships no hook file. JR wires it manually via Claude Code settings: `freddy transcript upload --from-hook --session-id $(cat ~/.freddy/session.json | jq -r .id)`.

---

## Critical file references

- freddy DB (sessions tables): `scripts/setup_test_db.sql` L1561-1645
- freddy sessions module: `src/sessions/{service,repository,log_storage,models,settings,validation,exceptions}.py`
- freddy sessions router: `src/api/routers/sessions.py` (9 endpoints, schemas inline)
- freddy api_keys router: `src/api/routers/api_keys.py` (swap `BillingRepository` → `ApiKeyRepo`)
- freddy api_key port source: `src/billing/repository.py` L214-265 + `APIKey` L22-32 + `_row_to_api_key` L546-556
- freddy `SessionService` ctor: `src/sessions/service.py:17`
- freddy `R2VideoStorage` ctor: `src/storage/r2_storage.py:107`
- freddy `R2SessionLogStorage` ctor: `src/sessions/log_storage.py:24`
- freddy CLI: `cli/freddy/{api,output,config}.py`, `cli/freddy/commands/{auth,session}.py`
- freddy CI bootstrap: `scripts/ci_bootstrap.sql`
- freddy SessionsPage: `frontend/src/pages/SessionsPage.tsx` (inline detail, no separate page)
- gofreddy existing provider factory: `cli/freddy/api.py` (rename to `providers.py`)
- gofreddy existing CLI config: `cli/freddy/config.py` (merge with freddy schema)

---

**Execution order:** Preflight → M1 DB → M2 Backend → M3 CLI → M4 Frontend → M5 Deploy. Estimated ~10-12 hours.
