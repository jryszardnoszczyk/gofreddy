# Monitoring + Agent Dashboard Transfer Plan

**Date:** 2026-04-17
**Scope:** Transfer the full monitoring + session telemetry + agent engine + transcript/R2 + frontend dashboard from `freddy/` into `gofreddy/`.
**Rule:** **COPY, DON'T REWRITE.** Where a file needs a delta, edit in-place — don't reimplement.

---

## Why this is large

A 3-agent comprehensive audit (backend modules + CLI + frontend/infra) surfaced scope that a surface read misses:

- The **agent engine** (`src/orchestrator/` + 53 tool handlers + tool catalog) has to come across too — the "stream transcripts and updates" feature requires the agent that *produces* those transcripts.
- **20 API routers** are needed behind the dashboard. Only 27 of freddy's 48 are safe to skip.
- **6+ CLI commands** are missing that the dashboard workflow depends on (`auth`, `session`, `monitor`, `query_monitor`, `search_mentions`, `digest`).
- gofreddy's `cli/freddy/api.py` is **incompatible** with freddy's — gofreddy has a provider factory, freddy has an httpx REST client. **Must replace**, not merge.
- Frontend has ~51 canvas sections; we need ~3 of them (`Monitor*`). The rest have to be deleted to get the build green.
- **Tool-provider modules** (`src/brands`, `src/creative`, `src/demographics`, `src/evolution`, `src/stories`, `src/trends`, `src/search`) are orchestrator dependencies — they cascade in when we copy the agent.

Honest effort estimate: **7-10 days** for a wholesale clone + selective trim + integration tests + deploy. Most of that time is (a) wiring lifespan services, (b) frontend page-by-page trim + build fixup, (c) integration test port.

---

## Context

Phase 1 (committed `c5eb9da` + `f9efc86` + `dc1ff0f`) shipped: auth layer, login page, portal HTML shell (placeholder JSON), 22 integration tests. The monitoring dashboard the user actually wanted is **not** built — that's this plan.

What must work at the end of execution:

1. **Agent chat with SSE streaming** — user opens `app.gofreddy.ai/dashboard/chat`, sends a message, sees thinking/tool calls/text stream back live.
2. **Live session telemetry** — every agent run creates an `agent_sessions` row, logs `action_log` entries per tool call, optionally writes `iteration_log` with state snapshots to R2.
3. **Monitoring dashboard** — user sees list of monitors for their client, mentions with sentiment, alert history, AI-refinement changelog (approve/reject).
4. **CLI integration** — engineer on laptop runs `freddy transcript upload` / `freddy iteration push` from an autoresearch session; data appears in dashboard within 5 seconds.
5. **Auth'd + tenant-scoped** — users only see their own client's data; admins see all. API keys for CLI issued per user.

---

## Scope snapshot (revised)

### Backend Python

| Category | What | Status | Lines |
|---|---|---|---|
| Modules already in gofreddy | `analysis`, `batch`, `common`, `competitive`, `deepfake`, `evaluation`, `fetcher`, `fraud`, `generation`, `geo`, `monitoring`, `publishing`, `seo`, `storage`, `video_projects` | ✓ Verify only | — |
| Modules to copy (Phase B1 core) | `sessions`, `conversations`, `workspace`, `preferences`, `extraction` | **cp -r** | ~2,500 |
| Modules to copy (Phase B2 agent engine) | `orchestrator` (+ tool_handlers/ + tool_catalog/ + strategies/), `brands`, `creative`, `demographics`, `evolution`, `stories`, `trends`, `search` | **cp -r** | ~8,000 |
| Routers to copy (Phase B1 core — 11) | `agent`, `sessions`, `monitoring`, `conversations`, `workspace`, `webhooks`, `preferences`, `health`, `usage`, `media`, `api_keys` | **cp** | ~2,400 |
| Routers to copy (Phase B2 tools — 10) | `analysis`, `batch`, `competitive`, `deepfake`, `evaluation`, `generation`, `geo`, `publishing`, `seo`, `video_projects` | **cp** | ~2,500 |
| Schemas + support | `src/api/schemas.py`, `schemas_discover.py`, `schemas_monitoring.py`, `src/api/logging.py` | **cp** | ~700 |
| Lifespan | `src/api/dependencies.py` — merge only (not copy) | **edit** | patched |

**SKIP entirely:** `billing/` (stripe/tiers), `clients/` (SaaS multi-tenant — gofreddy has its own), `jobs/` (Cloud Tasks — defer), `newsletter/`, `policies/`, `optimization/`, 27 routers (billing, SaaS-only, video-analysis-only).

### CLI

| Category | Files |
|---|---|
| Must **replace**: `cli/freddy/api.py` | gofreddy has a provider factory; freddy has an httpx REST client. These do different things — swap, don't merge. |
| Must **copy**: `cli/freddy/output.py`, `cli/freddy/commands/auth.py`, `session.py`, `monitor.py`, `query_monitor.py`, `search_mentions.py`, `digest.py`, `evaluate.py` | 7 new files |
| Already present (verify identical): `transcript.py`, `iteration.py` | — |
| Probably-needed (after provider verification): `seo.py`, `competitive.py` | 2 files |

### Frontend

| Category | What |
|---|---|
| Clone whole | `cp -r freddy/frontend/ gofreddy/frontend/` (~48.6K LOC) |
| Keep pages | `MonitoringPage`, `SessionsPage`, `ChatPage`, `LoginPage`, `AuthCallbackPage`, `SettingsPage` (trimmed — keep API key mgmt, drop billing) |
| Keep components | `ChatCanvasLayout`, `NavigationRail`, `ProtectedRoute`, `AuthProvider`, `ErrorBoundary`, `Toast`, `Button`, `Card`, `Badge`, `EmptyState`, `Skeleton`, `PageHeader`, `AlertBanner`, `MentionCard`, `MonitorWorkbench`, `MonitorMentionsSection`, `MonitorSection`, `MonitorAnalyticsSection`, `ConversationSidebar` (rename to `MonitorSidebar`) |
| Keep hooks | `useChat`, `useMonitors`, `useSessions`, `useMonitorDetail`, `useAuth`, `useDocumentTitle`, `useResizablePanel`, `useToast` |
| Keep lib | `lib/api.ts` (all 1796 lines — unused functions are dead code but harmless), `lib/api-types.ts` (regenerated), `lib/routes.ts`, `index.css` |
| **Delete** pages | `LibraryPage`, `PricingPage`, landing page if present (gofreddy.ai is separate) |
| **Delete** canvas sections (~45 of 51) | All `canvas/sections/*` except `MonitorMentionsSection`, `MonitorSection`, `MonitorAnalyticsSection`, `MonitorWorkbench` |
| **Delete** studio/video-gen components | `StudioReferenceTray`, `VideoProjectStudio`, `StudioWorkspace`, everything under `studio/` and `video-gen/` |
| **Delete** hooks | `useLibraryData`, `useVideoProjects`, `useBatchProgress`, `useGenerationProgress`, `useConversations`, `useWorkspace`, `useDesktopSplitView` |

### Database schema

25 tables + indexes + triggers. Extract from freddy `scripts/setup_test_db.sql` lines 1362-1644. Add gofreddy-specific: `ALTER TABLE agent_sessions ADD COLUMN client_id UUID REFERENCES clients(id);` + RLS policies.

Optional Phase B2 additions: conversations + workspace tables (freddy L857-920, 6 more tables).

---

## Target architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Static landing     gofreddy.ai  (GitHub Pages, already shipped)        │
└──────────────────────────────────────────────────────────────────────────┘
              │ CTA "go to app" →
              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  React SPA                app.gofreddy.ai     (Vite build)              │
│  /login                 → Supabase auth                                  │
│  /dashboard/monitoring  → MonitoringPage    (monitors, mentions, alerts)│
│  /dashboard/sessions    → SessionsPage      (agent sessions + actions)  │
│  /dashboard/chat        → ChatPage          (SSE-streaming chat)        │
│  /dashboard/settings    → SettingsPage      (API keys, profile)         │
│  /portal/<slug>         → promoted to real dashboard                    │
└────────┬─────────────────────────────────────────────────────────────────┘
         │ Bearer JWT (or X-API-Key for CLI)
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  FastAPI              api.gofreddy.ai      (Fly.io, Dockerfile)         │
│                                                                          │
│  Auth:       /v1/auth/me + /logout                (Phase 1, done)       │
│  Sessions:   /v1/sessions/* CRUD + actions + iterations + transcript    │
│  Monitoring: /v1/monitors/* CRUD + mentions + analytics + alerts +      │
│              changelog                                                   │
│  Agent:      /v1/agent/chat/stream  (SSE)                               │
│  Convs:      /v1/conversations/*                                        │
│  Workspace:  /v1/workspace/*                                            │
│  Webhooks:   /v1/webhooks/* (alert delivery)                            │
│  Preferences:/v1/preferences                                            │
│  Media:      /v1/media/* (presigned R2 URLs)                            │
│  API Keys:   /v1/api-keys/* (CLI credentials)                           │
│  Usage:      /v1/usage                                                  │
│  Tools:      /v1/analysis, /v1/generation, /v1/evaluation, /v1/seo,     │
│              /v1/geo, /v1/competitive, /v1/publishing, /v1/batch,       │
│              /v1/deepfake, /v1/video_projects  (called by orchestrator) │
└────────┬─────────────────────────────────────────┬──────────────────────┘
         │ asyncpg                                 │ aioboto3
         ▼                                         ▼
┌────────────────────────────────┐        ┌──────────────────────────┐
│  Supabase Postgres             │        │  Cloudflare R2           │
│  (Phase 1, done)               │        │  session-logs/<sid>/     │
│   users, clients,              │        │    iteration-NNN.txt     │
│   user_client_memberships      │        │    state-NNN.md          │
│  (this plan)                   │        │  transcripts/<sid>.txt   │
│   agent_sessions, action_log,  │        │  media/<org>/<asset>/    │
│   iteration_log                │        │                          │
│   monitors, mentions,          │        │  Buckets:                │
│   monitor_runs, alert_rules,   │        │   video-intelligence     │
│   alert_events, monitor_       │        │   (prod)                 │
│   changelog, cursors           │        │   video-intelligence-    │
│  (optional, Phase B2)          │        │   test  (dev/CI)         │
│   conversations, messages,     │        └──────────────────────────┘
│   workspace_collections,       │
│   workspace_items, events,     │
│   workspace_tool_results       │
└────────────────────────────────┘
         ▲
         │ X-API-Key header
         │
┌────────┴─────────────────────────────────────────────────────────────────┐
│  CLI (freddy)                                                            │
│                                                                          │
│  freddy auth login/whoami/logout   → ~/.freddy/config.json (0600)       │
│  freddy session start/end          → /v1/sessions CRUD                   │
│  freddy transcript upload          → /v1/sessions/.../transcript         │
│  freddy iteration push             → /v1/sessions/.../iterations → R2    │
│  freddy monitor mentions           → /v1/monitors/.../mentions           │
│  freddy query-monitor              → /v1/monitors/.../{sov,sentiment}    │
│  freddy search-mentions            → /v1/monitors/.../mentions?q=...     │
│  freddy digest persist             → /v1/monitors/.../digests            │
│  freddy evaluate review            → Gemini (local, no API)              │
│  freddy audit seo/competitive      → existing (provider factory; local)  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Execution phases

### Phase A — Database (M1)

**Deliverable:** `supabase/migrations/20260418000001_monitoring_sessions.sql` + updated `scripts/setup_db.sql`.

Steps:
1. Extract freddy `scripts/setup_test_db.sql` lines 1362-1644 (monitoring + sessions + alerts).
2. Append to gofreddy's migration file with the minimum required shape changes:
   - `ALTER TABLE agent_sessions ADD COLUMN client_id UUID REFERENCES clients(id);`
   - `ALTER TABLE monitors ADD COLUMN client_id UUID REFERENCES clients(id);`
   - Same for `alert_rules`.
3. RLS policies on `agent_sessions`, `action_log`, `iteration_log`, `monitors`, `mentions`, `alert_*` using the `user_client_memberships` table from Phase 1.
4. `supabase db reset` — verify no DDL errors, all tables present.

**Defer to M9:** conversations/workspace tables (only land them when orchestrator is actually shipping).

### Phase B1 — Backend core (M2)

**Deliverable:** every session + monitoring + workspace + preferences API route works locally against the seed user.

Steps (all `cp`, no rewrite):
```bash
cp -r freddy/src/sessions     gofreddy/src/                       # verify, should be same
cp -r freddy/src/conversations gofreddy/src/
cp -r freddy/src/workspace    gofreddy/src/
cp -r freddy/src/preferences  gofreddy/src/
cp -r freddy/src/extraction   gofreddy/src/

cp freddy/src/api/schemas.py            gofreddy/src/api/
cp freddy/src/api/schemas_discover.py   gofreddy/src/api/
cp freddy/src/api/schemas_monitoring.py gofreddy/src/api/
cp freddy/src/api/logging.py            gofreddy/src/api/

cp freddy/src/api/routers/agent.py         gofreddy/src/api/routers/
cp freddy/src/api/routers/sessions.py      gofreddy/src/api/routers/
cp freddy/src/api/routers/monitoring.py    gofreddy/src/api/routers/
cp freddy/src/api/routers/conversations.py gofreddy/src/api/routers/
cp freddy/src/api/routers/workspace.py     gofreddy/src/api/routers/
cp freddy/src/api/routers/webhooks.py      gofreddy/src/api/routers/
cp freddy/src/api/routers/preferences.py   gofreddy/src/api/routers/
cp freddy/src/api/routers/health.py        gofreddy/src/api/routers/
cp freddy/src/api/routers/usage.py         gofreddy/src/api/routers/
cp freddy/src/api/routers/media.py         gofreddy/src/api/routers/
cp freddy/src/api/routers/api_keys.py      gofreddy/src/api/routers/
```

Then **merge** `src/api/dependencies.py`:
- Add imports from new modules.
- Extend `lifespan()` with service init blocks copied from freddy L1060-1561 for each new service.
- Add `get_conversation_service`, `get_workspace_service`, `get_session_service`, etc. dependency getters.
- Register new routers in `src/api/main.py`.

**Trim-on-copy checklist (see M6 for exhaustive):**
- `src/monitoring/workspace_bridge.py` — delete; drop import from `monitoring/service.py`.
- Billing/credit decorators in routers — strip (gofreddy has no billing).
- `agent_sessions.org_id` references — replace with `client_id`.

**Verification:**
- `docker build` succeeds.
- `docker run` + all `/v1/*` endpoints return 401/200 as expected (no import errors).
- All Phase 1 tests still pass + new sessions/monitoring integration tests pass.

### Phase B2 — Agent engine (M3)

**Deliverable:** SSE chat works end-to-end. `/v1/agent/chat/stream` accepts a prompt, streams thinking→tool_call→tool_result→text_delta→done events, persists conversation + session.

Steps:
```bash
cp -r freddy/src/orchestrator gofreddy/src/           # ~53 tool handlers
cp -r freddy/src/brands       gofreddy/src/
cp -r freddy/src/creative     gofreddy/src/
cp -r freddy/src/demographics gofreddy/src/
cp -r freddy/src/evolution    gofreddy/src/
cp -r freddy/src/stories      gofreddy/src/
cp -r freddy/src/trends       gofreddy/src/
cp -r freddy/src/search       gofreddy/src/

cp freddy/src/api/routers/analysis.py       gofreddy/src/api/routers/
cp freddy/src/api/routers/batch.py          gofreddy/src/api/routers/
cp freddy/src/api/routers/competitive.py    gofreddy/src/api/routers/
cp freddy/src/api/routers/deepfake.py       gofreddy/src/api/routers/
cp freddy/src/api/routers/evaluation.py     gofreddy/src/api/routers/
cp freddy/src/api/routers/generation.py     gofreddy/src/api/routers/
cp freddy/src/api/routers/geo.py            gofreddy/src/api/routers/
cp freddy/src/api/routers/publishing.py     gofreddy/src/api/routers/
cp freddy/src/api/routers/seo.py            gofreddy/src/api/routers/
cp freddy/src/api/routers/video_projects.py gofreddy/src/api/routers/
```

Extend `lifespan()` for the new services.

**Trim-on-copy checklist:**
- Tool handlers that reference `billing/credits/` — remove credit decrement calls; gofreddy has no billing layer.
- Handlers referencing `jobs/` (async dispatch) — make them synchronous (inline-execute). Don't copy `src/jobs/`.
- Tool handlers that reference `newsletter/`, `clients/` SaaS — drop the whole handler file.
- `orchestrator/strategies/` — may reference SaaS features; trim per strategy.

**Verification:**
- `/v1/agent/chat/stream` returns valid SSE events.
- Each tool router responds under auth.
- Running a chat that calls a tool (e.g., "analyze competitor acme.com") triggers the right handler and logs an `action_log` row.

### Phase C — CLI (M4)

**Deliverable:** engineer can run `freddy auth login`, `freddy session start`, `freddy transcript upload`, `freddy monitor mentions` and data flows to the API.

**The critical swap:** gofreddy's `cli/freddy/api.py` is a *provider factory* (DataForSEO, Foreplay, etc.). Freddy's is an *httpx REST client*. They do different jobs. To keep the provider factory for the existing `freddy audit` commands AND gain the REST client for new dashboard commands, split them:

```bash
# Preserve the existing provider factory
mv gofreddy/cli/freddy/api.py gofreddy/cli/freddy/providers.py

# Bring freddy's REST client as the new api.py
cp freddy/cli/freddy/api.py gofreddy/cli/freddy/api.py

# Bring shared output helpers
cp freddy/cli/freddy/output.py gofreddy/cli/freddy/output.py

# New command files
cp freddy/cli/freddy/commands/auth.py            gofreddy/cli/freddy/commands/
cp freddy/cli/freddy/commands/session.py         gofreddy/cli/freddy/commands/
cp freddy/cli/freddy/commands/monitor.py         gofreddy/cli/freddy/commands/
cp freddy/cli/freddy/commands/query_monitor.py   gofreddy/cli/freddy/commands/
cp freddy/cli/freddy/commands/search_mentions.py gofreddy/cli/freddy/commands/
cp freddy/cli/freddy/commands/digest.py          gofreddy/cli/freddy/commands/
cp freddy/cli/freddy/commands/evaluate.py        gofreddy/cli/freddy/commands/
```

Update existing `audit.py` to import from `providers` instead of `api` (where it referenced the provider factory). All new commands use `api` (REST client).

Update `cli/freddy/main.py`:
```python
from .commands import (
    audit, auto_draft, auth, client, digest, evaluate,
    iteration, monitor, query_monitor, save, search_mentions,
    session, setup, sitemap, transcript,
)
app.add_typer(auth.app, name="auth")
app.add_typer(session.app, name="session")
app.add_typer(monitor.app, name="monitor")
app.add_typer(digest.app, name="digest")
app.add_typer(evaluate.app, name="evaluate")
app.command(name="query-monitor")(query_monitor.query_monitor_command)
app.command(name="search-mentions")(search_mentions.search)
# existing commands unchanged
```

**Verification:**
- `freddy --help` shows 17+ commands.
- `freddy auth login --api-key <k> --base-url <url>` writes `~/.freddy/config.json`.
- `freddy auth whoami` → email + role + client_slugs.
- `freddy transcript upload` + `freddy iteration push` hit the API and data appears in Postgres/R2.

### Phase D — Frontend (M5)

**Deliverable:** React SPA deployed at `app.gofreddy.ai` — dashboard works end-to-end.

Steps:
1. `cp -r freddy/frontend/ gofreddy/frontend/` (whole repo).
2. `rm -rf gofreddy/frontend/node_modules`.
3. **Page deletion:**
   ```bash
   rm gofreddy/frontend/src/pages/LibraryPage.tsx
   rm gofreddy/frontend/src/pages/PricingPage.tsx
   # Keep LandingPage as-is (or delete — we have gofreddy.ai)
   ```
4. **Canvas section deletion — delete all `canvas/sections/*` except:**
   - `MonitorMentionsSection.tsx`
   - `MonitorSection.tsx`
   - `MonitorAnalyticsSection.tsx`
5. **Component deletion:**
   ```bash
   rm -rf gofreddy/frontend/src/components/studio
   rm -rf gofreddy/frontend/src/components/video-gen
   # Any "workspace" video-related components, but KEEP ChatCanvasLayout
   ```
6. **Hook deletion:**
   ```bash
   rm gofreddy/frontend/src/hooks/useLibraryData.ts
   rm gofreddy/frontend/src/hooks/useLibraryFilters.ts
   rm gofreddy/frontend/src/hooks/useVideoProjects.ts
   rm gofreddy/frontend/src/hooks/useBatchProgress.ts
   rm gofreddy/frontend/src/hooks/useGenerationProgress.ts
   rm gofreddy/frontend/src/hooks/useConversations.ts
   rm gofreddy/frontend/src/hooks/useWorkspace.ts
   rm gofreddy/frontend/src/hooks/useDesktopSplitView.ts
   ```
7. **SettingsPage trim:** open `SettingsPage.tsx`, delete billing/usage/subscription sections, keep API key management.
8. **Router update:** `src/main.tsx` — remove routes to deleted pages.
9. `npm install` — expect ~3 rounds of "fix compile errors" from dead imports.
10. `npm run generate-api` — regenerate types from local `openapi.json`.
11. **Env:**
    ```
    VITE_SUPABASE_URL=https://<project>.supabase.co
    VITE_SUPABASE_ANON_KEY=...
    VITE_API_BASE_URL=https://api.gofreddy.ai
    ```
12. `npm run build` → `dist/`. Deploy to Vercel or Fly static.

**Verification:**
- `npm run dev` at localhost:5173 → sign in → dashboard loads.
- Create a monitor via CLI → refresh dashboard → monitor appears.
- Open `/dashboard/chat` → send message → see SSE stream live.
- `/dashboard/settings` → create an API key → copy it, use in CLI.

### Phase E — Trim + tests + deploy (M6, M7, M8)

**M6 — Trim pass** (in parallel with B1/B2, consolidate at end):
- Every file that imports `src/billing/` or `src/jobs/` or `src/clients/` — surgical edit to remove the reference.
- Every router that has `@require_tier` decorator or `check_credits()` call — strip.
- `src/monitoring/intelligence/sentiment.py` — stub (return null) until M9. 1.2GB HuggingFace model otherwise ships in Docker image.
- `src/monitoring/worker.py` — don't wire into lifespan. Use sync `POST /v1/monitors/{id}/run` for now.
- `src/monitoring/alerts/delivery.py` — alerts go to `alert_events` table; webhook delivery deferred.

Document every trim in a comment at the top of the edited file: `# gofreddy-trim: removed <X> — see docs/plans/2026-04-17-monitoring-transfer-plan-v2.md M6`.

**M7 — Tests:**
- Port `tests/test_api/test_auth_router.py` — already done in Phase 1 (adapted).
- Port `tests/test_api/test_dependencies.py` — test JWT decode + user resolution.
- **NEW:** `tests/test_api/test_sessions.py` — session CRUD + action/iteration logging + R2 upload path.
- **NEW:** `tests/test_api/test_monitoring.py` — monitor CRUD + mentions (with mock adapter) + alerts.
- **NEW:** `tests/test_api/test_agent_stream.py` — SSE endpoint connects + streams events.
- **NEW:** `tests/test_api/test_conversations.py` — create conversation, append message, retrieve.
- **NEW:** `tests/test_cli/test_e2e.sh` — bash script: login, session start, transcript upload, iteration push, verify in DB + R2.

Pattern: real local Supabase + real asyncpg (per MEMORY.md: "integration tests must hit a real database, not mocks").

**M8 — Cloud deploy:**
1. **Supabase:** create project at supabase.com → capture URL/ANON_KEY/JWT_SECRET → `supabase db push`.
2. **R2:** create two buckets `gofreddy-prod` + `gofreddy-test` → create API token with R2:Edit scope.
3. **Fly:**
   ```bash
   flyctl launch --name gofreddy-api --region iad --no-deploy
   flyctl volumes create data --size 10 --region iad
   flyctl secrets set SUPABASE_URL=... SUPABASE_ANON_KEY=... SUPABASE_JWT_SECRET=... DATABASE_URL=... R2_ACCOUNT_ID=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... R2_BUCKET_NAME=gofreddy-prod GEMINI_API_KEY=... (adapter keys as applicable)
   flyctl deploy
   flyctl certs create api.gofreddy.ai
   ```
4. **Frontend:** `npm run build` in `gofreddy/frontend/` → deploy `dist/` to Vercel / Cloudflare Pages / Fly static.
5. **DNS:** CNAME `api.gofreddy.ai` → `gofreddy-api.fly.dev`; CNAME `app.gofreddy.ai` → wherever frontend is hosted.

**M9 — Deferred items (explicit list, not done in this plan):**
- Background `monitoring/worker.py` — async monitor runs via Cloud Tasks. Phase 1 uses sync endpoint.
- `src/jobs/` — Cloud Tasks queue. Enable when async needed.
- `monitoring/alerts/delivery.py` — webhook + email alert fan-out.
- `monitoring/intelligence/sentiment.py` — HuggingFace sentiment model. Currently returns null.
- `monitoring/comments/` + `monitoring/crm/` — files ship, not wired until a client needs them.
- OpenTelemetry instrumentation — nice-to-have for prod observability.
- RLS end-to-end on all monitoring/session tables — Phase 1 gates at FastAPI layer.
- Multi-VM deployment — requires Redis-backed rate limiter + token blocklist. Single-VM for now.

---

## Env variables master list

Set in `.env.example` + as Fly secrets:

```bash
# Auth (Phase 1 already configured)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_JWT_SECRET=
DATABASE_URL=

# R2 storage (this plan)
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=gofreddy-prod   # or gofreddy-test in dev

# Clients workspace (Phase 1 — local filesystem)
GOFREDDY_CLIENTS_DIR=/data/clients

# LLM — at least one required
GEMINI_API_KEY=
OPENAI_API_KEY=
XAI_API_KEY=

# Monitoring adapters (wire as clients sign up)
MONITORING_XPOZ_API_KEY=
MONITORING_NEWSDATA_API_KEY=
MONITORING_APIFY_TOKEN=
MONITORING_BLUESKY_ENABLED=false
MONITORING_PODCASTS_ENABLED=false

# Agency audit providers (already wired)
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=
FOREPLAY_API_KEY=
ADYNTEL_API_KEY=
ADYNTEL_EMAIL=

# Runtime mode
ENVIRONMENT=production
EXTERNALS_MODE=real    # or fake in dev
TASK_CLIENT_MODE=mock  # cloud when M9 lands
```

---

## Risks + mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **orchestrator is deeply coupled to billing/credits** | Won't import without trim | M6 strip pass — document every removal |
| **HuggingFace sentiment adds 1.2GB to Docker image** | Slow Fly deploy, startup time | M6: stub sentiment; activate via Gemini API if needed |
| **`agent.py` router has 803 lines of SSE orchestration** | Most fragile thing to port | Copy verbatim; fix only the specific billing decorators that break imports |
| **Frontend has 48K LOC with many cross-dependencies** | `npm run build` will fail 3-5 times on first try | Delete files in waves, run `npm run build` between waves, fix imports |
| **CLI `api.py` incompatibility** | Breaks existing `freddy audit` commands | Move gofreddy's to `providers.py`, import from there in `audit.py` |
| **Tool handlers reference `jobs/` for async** | Tool calls hang | Make tool handlers sync (inline-execute). If a handler genuinely needs async, copy `src/jobs/` — but try to avoid. |
| **Mention adapters cost money per call** (Xpoz, NewsData, Apify) | Unexpected bills | Wire adapters only when a client's monitor needs them. Cheapest path: `ai_search` (Gemini) + `news` (NewsData) first. |
| **SSE through Fly proxy** | Connections drop | Verify `Cache-Control: no-cache` + ping interval 15s < any proxy timeout. |
| **R2 presigned URL 7-day max** | UI embeds expire | Refresh on each page load; or proxy through API. |
| **Tests fail because lifespan inits services that need env vars not set in CI** | CI red | Conditional lifespan: skip service init if required env var missing, warn in log. |

---

## Critical file references

- freddy source: `/Users/jryszardnoszczyk/Documents/GitHub/freddy/`
- gofreddy target: `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/`
- freddy DB schema: `scripts/setup_test_db.sql` lines 1362-1644 (+ optional 857-920 for conversations/workspace)
- freddy lifespan: `src/api/dependencies.py` lines 1050-1561 (service init blocks to port)
- freddy agent SSE: `src/api/routers/agent.py` lines 452+ (EventSourceResponse)
- freddy frontend entry: `frontend/src/main.tsx` (route registration)
- freddy frontend API layer: `frontend/src/lib/api.ts` (all endpoint functions)

---

## Execution order (what to do in sequence)

1. **M1 DB schema** — can run in parallel with everything else (no code deps)
2. **M2 Backend core** (sessions, monitoring routers wire, conversations, workspace, preferences, schemas, logging)
3. **M6 Trim pass** (start early, consolidate at end)
4. **M7 Tests for B1** (sessions + monitoring tests green)
5. **M3 Agent engine** (orchestrator + tools + 10 tool routers)
6. **M7 Tests for B2** (agent SSE stream test, conversations, workspace)
7. **M4 CLI** (api.py split + 7 new commands)
8. **M5 Frontend** (clone + prune + build)
9. **M8 Cloud deploy** (once all green locally)
10. **M9 Document deferred items** (ongoing)

Estimated **7-10 days** for an engineer executing the plan.

---

## Summary punch list

```bash
# === Backend ===
cp -r freddy/src/sessions     gofreddy/src/  # verify
cp -r freddy/src/conversations gofreddy/src/
cp -r freddy/src/workspace    gofreddy/src/
cp -r freddy/src/preferences  gofreddy/src/
cp -r freddy/src/extraction   gofreddy/src/
cp -r freddy/src/orchestrator gofreddy/src/
cp -r freddy/src/brands       gofreddy/src/
cp -r freddy/src/creative     gofreddy/src/
cp -r freddy/src/demographics gofreddy/src/
cp -r freddy/src/evolution    gofreddy/src/
cp -r freddy/src/stories      gofreddy/src/
cp -r freddy/src/trends       gofreddy/src/
cp -r freddy/src/search       gofreddy/src/

cp freddy/src/api/schemas.py            gofreddy/src/api/
cp freddy/src/api/schemas_discover.py   gofreddy/src/api/
cp freddy/src/api/schemas_monitoring.py gofreddy/src/api/
cp freddy/src/api/logging.py            gofreddy/src/api/

for r in agent sessions monitoring conversations workspace webhooks preferences health usage media api_keys \
         analysis batch competitive deepfake evaluation generation geo publishing seo video_projects; do
  cp freddy/src/api/routers/${r}.py gofreddy/src/api/routers/
done

# === CLI ===
mv gofreddy/cli/freddy/api.py gofreddy/cli/freddy/providers.py
cp freddy/cli/freddy/api.py    gofreddy/cli/freddy/
cp freddy/cli/freddy/output.py gofreddy/cli/freddy/
for c in auth session monitor query_monitor search_mentions digest evaluate; do
  cp freddy/cli/freddy/commands/${c}.py gofreddy/cli/freddy/commands/
done

# === Frontend ===
cp -r freddy/frontend/ gofreddy/frontend/
rm -rf gofreddy/frontend/node_modules
# then prune per M5 (delete LibraryPage, PricingPage, 45 canvas sections, video-gen, studio components, 7 hooks)
# then npm install, fix compile errors, npm run generate-api, npm run build

# === DB ===
# Write supabase/migrations/20260418000001_monitoring_sessions.sql:
#   - Extract freddy setup_test_db.sql L1362-1644 verbatim
#   - Add ALTER TABLE agent_sessions/monitors/alert_rules ADD COLUMN client_id
#   - Add RLS policies
# supabase db reset to verify
```

When this plan ships: users log in to `app.gofreddy.ai`, see live session telemetry streaming from the CLI, see monitors updating with real mentions from 13 adapters (when clients enable them), chat with the agent via SSE stream, receive webhook alerts. The portal placeholder I shipped in Phase 1 is retired — everything that's behind the auth wall is real.
