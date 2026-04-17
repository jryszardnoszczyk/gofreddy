# Monitoring + Agent Dashboard Transfer Plan

**Date:** 2026-04-17
**Scope:** Transfer the full monitoring + session telemetry + agent engine + transcript/R2 + frontend dashboard from `freddy/` into `gofreddy/`.
**Rule:** **COPY, DON'T REWRITE.** Where a file needs a delta, edit in-place — don't reimplement.

---

## Why this is large

A 6-agent comprehensive audit (backend modules + CLI + frontend/infra + adapters + router graph + tests + orchestrator) surfaced scope that a surface read misses:

- The **agent engine** (`src/orchestrator/` + 20 tool handlers + tool catalog) has to come across too — the "stream transcripts and updates" feature requires the agent that *produces* those transcripts.
- **20 API routers copied + 1 explicitly deleted (webhooks)**. 26 of freddy's 47 routers are skipped entirely.
- **6+ CLI commands** are missing that the dashboard workflow depends on (`auth`, `session`, `monitor`, `query_monitor`, `search_mentions`, `digest`).
- gofreddy's `cli/freddy/api.py` is **incompatible** with freddy's — gofreddy has a provider factory, freddy has an httpx REST client. **Must replace**, not merge.
- Frontend has 42 canvas sections; we need 4 of them (`MonitorMentionsSection`, `MonitorSection`, `MonitorAnalyticsSection`, `MonitorWorkbench`). The other 38 have to be deleted to get the build green.
- **Tool-provider modules** (`src/brands`, `src/creative`, `src/demographics`, `src/evolution`, `src/stories`, `src/trends`, `src/search`) are orchestrator dependencies — they cascade in when we copy the agent.
- **`src/content_gen/` (9 files) is an orchestrator dependency** — `generate_content` tool handler hard-depends on `ContentGenerationService`. Plan v1 omitted this. Copy in M2.
- **`src/policies/` (4 files) is referenced by `analysis.py` router and `analyze_video.py` handler.** gofreddy does NOT already have it. Copy in M2.
- **13 monitoring adapters** ship with `src/monitoring/adapters/` (cp -r lands them automatically), but **7 env vars** are missing from the plan's master list.
- **pyproject.toml deps delta** — 3 packages needed (`sse-starlette`, `slowapi`, `PyJWT[crypto]` upgrade from `pyjwt`). `uv.lock` must regenerate.

Honest effort estimate: **5-7 days** for a wholesale clone + selective trim + deploy. Most of that time is (a) additive merge of freddy's service init blocks into gofreddy's Phase 1 `dependencies.py`, (b) frontend page-by-page trim + build fixup, (c) M6 import surgery on analysis/deepfake/usage/manage_client/manage_policy. **Tests are out of scope** — Phase 1's 22 integration tests stay as regression check; no new tests written or ported.

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
| Modules to copy (Phase B1 core) | `sessions`, `conversations`, `workspace`, `preferences`, `extraction`, **`content_gen`**, **`policies`** | **cp -r** | ~3,200 |
| Modules to copy (Phase B2 agent engine) | `orchestrator` (+ tool_handlers/ + tool_catalog/ + strategies/), `brands`, `creative`, `demographics`, `evolution`, `stories`, `trends`, `search` | **cp -r** | ~8,000 |
| Routers to copy (Phase B1 core — 9) | `sessions`, `monitoring`, `conversations`, `workspace`, `preferences`, `health`, `usage`, `media`, `api_keys` | **cp + trim** | ~2,000 |
| Routers to copy (Phase B2 agent+tools — 11) | `agent` (deferred from B1 — imports orchestrator), `analysis`, `batch`, `competitive`, `deepfake`, `evaluation`, `generation`, `geo`, `publishing`, `seo`, `video_projects` | **cp + trim** | ~2,900 |
| Routers to **DELETE** (was in v1 plan) | ~~`webhooks`~~ — Stripe billing core, defer to M9 | — | — |
| Schemas + support | `src/api/schemas.py`, `schemas_discover.py`, `schemas_monitoring.py`, `src/api/logging.py`, `src/api/fake_externals.py` | **cp** | ~800 |
| Root-level helpers | `src/feedback.py`, `src/feedback_loop_config.py` | **cp** | ~200 |
| Billing tier enum only | `src/billing/tiers.py` (enum imported by orchestrator + monitoring) — everything else in `billing/` skipped | **cp + trim** | ~50 |
| Lifespan | `src/api/dependencies.py` — **additive merge** (keep gofreddy's Phase 1 file; paste freddy's service init blocks from L1060-1561 into existing lifespan). Less surgery than cp+trim. | **edit** | additive |
| Router registration | `src/api/main.py` — append 20 new router registrations to gofreddy's Phase 1 file; keep login/portal + middleware untouched. | **edit** | additive |
| Logging helper | `src/api/logging.py` | **cp** (new file in gofreddy) | cp |

**SKIP entirely:** `billing/` except `tiers.py`, `clients/` (SaaS multi-tenant — gofreddy has its own), `jobs/` (Cloud Tasks — defer), `newsletter/`, `optimization/`, 26 routers (billing, SaaS-only, video-analysis-only) + **`webhooks.py` explicitly dropped** (imports `billing.config.StripeSettings` and `billing.credits.*`; rewrite in M9 when/if needed).

**Why `content_gen/` and `policies/` moved from SKIP to COPY** (v2 correction): audit of `src/orchestrator/tools.py:475,582` shows `generate_content` handler registers with a `content_generation_service` parameter initialized from `ContentGenerationService` in lifespan. Audit of `src/api/routers/analysis.py` + `src/orchestrator/tool_handlers/analyze_video.py` shows `PolicyService` imports. Skipping them breaks the agent on the first `generate_content` or `analyze_video` call.

### CLI

| Category | Files |
|---|---|
| Rename-then-cp: `cli/freddy/api.py` | gofreddy has a provider factory; freddy has an httpx REST client. `mv gofreddy's api.py → providers.py`, then `cp freddy/cli/freddy/api.py gofreddy/cli/freddy/api.py`. No rewrite, just two copies. |
| Must **cp**: `cli/freddy/output.py`, `cli/freddy/commands/auth.py`, `session.py`, `monitor.py`, `query_monitor.py`, `search_mentions.py`, `digest.py`, `evaluate.py` | 7 new files (all `cp`) |
| Must **cp + re-add** `cli/freddy/main.py` | `cp freddy's main.py` then re-add gofreddy-unique `audit`/`auto_draft`/`client`/`save`/`setup`/`sitemap` registrations. |
| Already present (verify identical): `transcript.py`, `iteration.py` | — |
| Probably-needed (after provider verification): `seo.py`, `competitive.py` | 2 files (cp) |

### Frontend

| Category | What |
|---|---|
| Clone whole | `cp -r freddy/frontend/ gofreddy/frontend/` (~48.6K LOC) |
| Keep pages | `MonitoringPage`, `SessionsPage`, `ChatPage`, `LoginPage`, `AuthCallbackPage`, `SettingsPage` (trimmed — keep API key mgmt, drop billing) |
| Keep components | `ChatCanvasLayout`, `NavigationRail`, `ProtectedRoute`, `AuthProvider`, `ErrorBoundary`, `Toast`, `Button`, `Card`, `Badge`, `EmptyState`, `Skeleton`, `PageHeader`, `AlertBanner`, `MentionCard`, `MonitorWorkbench`, `MonitorMentionsSection`, `MonitorSection`, `MonitorAnalyticsSection`, `ConversationSidebar` (rename to `MonitorSidebar`) |
| Keep hooks | `useChat`, `useMonitors`, `useSessions`, `useMonitorDetail`, `useAuth`, `useDocumentTitle`, `useResizablePanel`, `useToast` |
| Keep lib | `lib/api.ts` (all 1796 lines — unused functions are dead code but harmless), `lib/api-types.ts` (regenerated), `lib/routes.ts`, `index.css` |
| **Delete** pages | `LibraryPage`, `PricingPage`, `UsagePage`, `LandingPage`, `pages/library/` subdir, `content/marketing.ts`. All `.test.tsx`/`.test.ts` files (no tests in scope). |
| **Delete** canvas sections (38 of 42) | All `canvas/sections/*` except `MonitorMentionsSection`, `MonitorSection`, `MonitorAnalyticsSection`, `MonitorWorkbench` |
| **Delete** studio/video-gen components | `StudioReferenceTray`, `VideoProjectStudio`, `StudioWorkspace`, everything under `studio/` and `video-gen/` |
| **Delete** hooks | `useLibraryData`, `useVideoProjects`, `useBatchProgress`, `useGenerationProgress`, `useConversations`, `useWorkspace`, `useDesktopSplitView` |

### Database schema

25 tables + indexes + triggers. Extract from freddy `scripts/setup_test_db.sql` lines 1362-1644. Add gofreddy-specific: `ALTER TABLE agent_sessions ADD COLUMN client_id UUID REFERENCES clients(id);` + RLS policies.

**Required in M1** (not optional — agent in M3 writes to them): conversations + workspace tables (freddy L857-920, 6 more tables). Include in the M1 migration file.

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
│  Preferences:/v1/preferences                                            │
│  (Webhooks router DELETED in v2 — Stripe-coupled; revisit in M9)        │
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

**Deliverable:** `supabase/migrations/20260418000001_monitoring_sessions.sql` + updated `scripts/setup_db.sql` + seed + CI bootstrap.

Steps:
1. Extract freddy `scripts/setup_test_db.sql` lines 1362-1644 (monitoring + sessions + alerts).
2. Append to gofreddy's migration file with the minimum required shape changes:
   - `ALTER TABLE agent_sessions ADD COLUMN client_id UUID REFERENCES clients(id);`
   - `ALTER TABLE monitors ADD COLUMN client_id UUID REFERENCES clients(id);`
   - Same for `alert_rules`.
3. RLS policies on `agent_sessions`, `action_log`, `iteration_log`, `monitors`, `mentions`, `alert_*` using the `user_client_memberships` table from Phase 1.
4. **Copy seed + CI bootstrap** (v2 addition — audit flagged missing):
   ```bash
   cp freddy/supabase/seed.sql   gofreddy/supabase/seed.sql    # monitor fixtures (Shopify, Lululemon, Notion) with stable UUIDs
   cp freddy/scripts/ci_bootstrap.sql gofreddy/scripts/         # CI-side DB bootstrap
   ```
   Replace user_id references in seed.sql with gofreddy's tenant model before applying.
5. `supabase db reset` — verify no DDL errors, all tables present.

**Required concurrent with M2 (agent engine lands in M3):** conversations/workspace tables (freddy L857-920 — 6 tables). The plan v1 said "defer to M9" but M3 ships the agent that writes to those tables. Move these to M2 migration file.

### Phase B1 — Backend core (M2)

**Deliverable:** every session + monitoring + workspace + preferences API route works locally against the seed user.

Steps (all `cp`, no rewrite):
```bash
cp -r freddy/src/sessions      gofreddy/src/                      # verify, should be same
cp -r freddy/src/conversations gofreddy/src/
cp -r freddy/src/workspace     gofreddy/src/
cp -r freddy/src/preferences   gofreddy/src/
cp -r freddy/src/extraction    gofreddy/src/
cp -r freddy/src/content_gen   gofreddy/src/                      # v2 addition — orchestrator depends on ContentGenerationService
cp -r freddy/src/policies      gofreddy/src/                      # v2 addition — analysis router + analyze_video handler depend on PolicyService

cp freddy/src/api/schemas.py            gofreddy/src/api/
cp freddy/src/api/schemas_discover.py   gofreddy/src/api/
cp freddy/src/api/schemas_monitoring.py gofreddy/src/api/
cp freddy/src/api/logging.py            gofreddy/src/api/
cp freddy/src/api/fake_externals.py     gofreddy/src/api/

# Root-level helpers — referenced by feedback loop (collected in session logs)
cp freddy/src/feedback.py               gofreddy/src/
cp freddy/src/feedback_loop_config.py   gofreddy/src/

# Billing tier enum — imported by orchestrator + monitoring routers even though
# we skip the rest of billing/. Copy only the enum; delete everything else.
mkdir -p gofreddy/src/billing
cp freddy/src/billing/tiers.py          gofreddy/src/billing/
touch gofreddy/src/billing/__init__.py

# Phase B1 routers — 9 total (agent.py deferred to M3 — needs orchestrator; webhooks.py DELETED — see M6)
cp freddy/src/api/routers/sessions.py      gofreddy/src/api/routers/
cp freddy/src/api/routers/monitoring.py    gofreddy/src/api/routers/
cp freddy/src/api/routers/conversations.py gofreddy/src/api/routers/
cp freddy/src/api/routers/workspace.py     gofreddy/src/api/routers/
cp freddy/src/api/routers/preferences.py   gofreddy/src/api/routers/
cp freddy/src/api/routers/health.py        gofreddy/src/api/routers/
cp freddy/src/api/routers/usage.py         gofreddy/src/api/routers/
cp freddy/src/api/routers/media.py         gofreddy/src/api/routers/
cp freddy/src/api/routers/api_keys.py      gofreddy/src/api/routers/
```

**pyproject.toml deps update** (verified by grep — only what the ported code actually imports):
```toml
# Add to gofreddy/pyproject.toml [project.dependencies]
"sse-starlette>=2.0.0",      # agent SSE streaming (used by agent.py router)
"slowapi>=0.1.9",            # rate limiter (Phase 1 uses it)
"PyJWT[crypto]>=2.8.0",      # fix: Phase 1 has lowercase `pyjwt` without [crypto] extra
```
Then: `uv lock` (regenerates `uv.lock`).

**Explicitly NOT added** (verified via grep of freddy/src/): `redis` (zero imports), `resend` (only in skipped `newsletter/`), `supabase` SDK (no imports), `asyncpg` version bump (Phase 1's 0.29 works; no 0.30-specific feature used).

**Env var consolidation** (v2 addition):
```bash
# Merge freddy's .env.example monitoring/adapter section into gofreddy's .env.example.
# Add the 7 missing vars called out in "Env variables master list" below.
# Do not overwrite gofreddy's Phase 1 auth/R2/clients_dir vars.
```

Then **additive merge** into gofreddy's Phase 1 `src/api/dependencies.py` + `src/api/main.py` (keeps Phase 1's correctly-trimmed 305-line dependencies.py intact; adds only the specific blocks the new code needs):

**`src/api/dependencies.py`** — paste these service init blocks from freddy's lifespan into gofreddy's existing `lifespan()`:
- `ContentGenerationService` (freddy L1414-1447) — required for `generate_content` tool handler
- `SessionService`, `ConversationService`, `WorkspaceService`, `PreferenceService`, `ExtractionService`, `PolicyService` — one `app.state.<x>_service = <x>Service(...)` block each (freddy L1060-1561, pick the specific blocks by name)
- Add matching `get_<x>_service` dependency getters at module scope

**`src/api/main.py`** — append **9 M2 router registrations** now (agent + 10 tool routers deferred to M3 because they need orchestrator):
```python
# After existing login/portal registration:
app.include_router(sessions_router.router, prefix="/v1")
app.include_router(monitoring_router.router, prefix="/v1")
app.include_router(conversations_router.router, prefix="/v1")
app.include_router(workspace_router.router, prefix="/v1")
app.include_router(preferences_router.router, prefix="/v1")
app.include_router(health_router.router)
app.include_router(usage_router.router, prefix="/v1")
app.include_router(media_router.router, prefix="/v1")
app.include_router(api_keys_router.router, prefix="/v1")
```
M3 appends the remaining 11: `agent`, `analysis`, `batch`, `competitive`, `deepfake`, `evaluation`, `generation`, `geo`, `publishing`, `seo`, `video_projects`.

gofreddy-specific Phase 1 files stay untouched: `src/api/users.py`, `src/api/membership.py`, `src/api/middleware.py`, `src/api/exceptions.py`, `src/api/rate_limit.py`, `src/api/routers/login.py`, `src/api/routers/portal.py`.

**Before executing the additive merge:** run `git log --since="1 week ago" freddy/src/api/dependencies.py` to catch any freddy bug-fixes that should land in gofreddy too.

**Trim-on-copy checklist (see M6 for exhaustive):**
- `src/monitoring/workspace_bridge.py` — delete; drop import from `monitoring/service.py:L578-595`. Also remove optional `workspace_bridge` param from `MonitoringService.__init__` at L56-62.
- Billing/credit decorators in routers — strip (gofreddy has no billing).
- `agent_sessions.org_id` references — replace with `client_id`.

**Verification:**
- `docker build` succeeds.
- `docker run` + all `/v1/*` endpoints return 401/200 as expected (no import errors).
- Phase 1's 22 integration tests (`pytest tests/test_api/`) still pass — regression check only; no new tests written.

### Phase B2 — Agent engine (M3)

**Deliverable:** SSE chat works end-to-end. `/v1/agent/chat/stream` accepts a prompt, streams thinking→tool_call→tool_result→text_delta→done events, persists conversation + session.

Steps:
```bash
cp -r freddy/src/orchestrator gofreddy/src/           # ~20 tool handlers + tool_catalog/ specs + strategies/
cp -r freddy/src/brands       gofreddy/src/
cp -r freddy/src/creative     gofreddy/src/
cp -r freddy/src/demographics gofreddy/src/
cp -r freddy/src/evolution    gofreddy/src/
cp -r freddy/src/stories      gofreddy/src/
cp -r freddy/src/trends       gofreddy/src/
cp -r freddy/src/search       gofreddy/src/

# Agent router (deferred from M2 because it imports ..orchestrator which lands here in M3)
cp freddy/src/api/routers/agent.py          gofreddy/src/api/routers/

# 10 tool routers called by the orchestrator
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

**Append router registrations to `src/api/main.py`** (the 11 M3 routers M2 deferred):
```python
app.include_router(agent_router.router, prefix="/v1")
app.include_router(analysis_router.router, prefix="/v1")
app.include_router(batch_router.router, prefix="/v1")
app.include_router(competitive_router.router, prefix="/v1")
app.include_router(deepfake_router.router, prefix="/v1")
app.include_router(evaluation_router.router, prefix="/v1")
app.include_router(generation_router.router, prefix="/v1")
app.include_router(geo_router.router, prefix="/v1")
app.include_router(publishing_router.router, prefix="/v1")
app.include_router(seo_router.router, prefix="/v1")
app.include_router(video_projects_router.router, prefix="/v1")
```

Extend `lifespan()` for the new services — especially `ContentGenerationService` (deps.py L1414-1447) which is required for the `generate_content` tool handler to function. Without this, calling `generate_content` from the agent returns an error instead of generating.

**Trim-on-copy checklist (v2 — refined from audit):**
- Tool handlers that reference `billing/credits/` — audit found handlers DO NOT call credit service directly; the billing layer is above handlers (`tools.py:L345-366 with_credit_billing` wrapper). Just strip that wrapper and Tier-gate decorators; handlers themselves are clean.
- Handlers referencing `jobs/` (async dispatch) — audit found **zero** orchestrator imports of `src/jobs/`; handlers are already sync. No change needed.
- **DELETE `orchestrator/tool_handlers/manage_client.py`** — imports `ClientService` from skipped `src/clients/`. Deleted outright, no replacement.
- **DELETE `orchestrator/tool_handlers/manage_policy.py`** — SaaS brand-policy CRUD; not needed in Phase 1. Deleted outright.
- **Keep `orchestrator/tool_handlers/analyze_video.py`** — policies dependency resolved in M2 v2.
- `orchestrator/strategies/` — audit found all 3 (monitoring.py, search.py, studio.py) are neutral. Copy all three.

**Tool catalog** (`src/orchestrator/tool_catalog/`, 21 .py files) — all declarative schemas; `_base.py` imports `Tier` enum only. Copy verbatim.

**Verification:**
- `/v1/agent/chat/stream` returns valid SSE events.
- SSE event types streamed (7 total per `agent.py:L34-42`): `thinking`, `tool_call`, `tool_result`, `text_delta`, `workspace_update`, `error`, `done`.
- Each tool router responds under auth.
- Running a chat that calls a tool (e.g., "analyze competitor acme.com") triggers the right handler and logs an `action_log` row.
- `generate_content` tool returns posts (not an error) — validates `ContentGenerationService` is wired.

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

**cp + re-add pattern for `cli/freddy/main.py`** (v2 correction — cleaner than hand-editing):
```bash
# cp freddy's CLI main.py wholesale (94 lines)
cp freddy/cli/freddy/main.py gofreddy/cli/freddy/main.py
```
Then add the gofreddy-unique command registrations back into the copied file:
```python
# After cp, re-add these lines to cli/freddy/main.py (these are gofreddy-only commands from the provider-factory era):
from .commands import audit, auto_draft, client, save, setup, sitemap
app.add_typer(audit.app, name="audit")
app.add_typer(auto_draft.app, name="auto-draft")
app.add_typer(client.app, name="client")
# etc. for save, setup, sitemap (trim to whatever is actually in gofreddy's current main.py)
```
The cp gives us freddy's command list (auth, session, monitor, query_monitor, search_mentions, digest, evaluate, iteration, transcript). We add back gofreddy's unique ones.

**Verification:**
- `freddy --help` shows 17+ commands.
- `freddy auth login --api-key <k> --base-url <url>` writes `~/.freddy/config.json`.
- `freddy auth whoami` → email + role + client_slugs.
- `freddy transcript upload` + `freddy iteration push` hit the API and data appears in Postgres/R2.

### Phase D — Frontend (M5)

**Deliverable:** React SPA deployed at `app.gofreddy.ai` — dashboard works end-to-end.

Steps:
1. `cp -r freddy/frontend/ gofreddy/frontend/` (whole repo, ~48.6K LOC).
2. `rm -rf gofreddy/frontend/node_modules`.
3. **Page deletion (v2 — expanded from audit):**
   ```bash
   rm gofreddy/frontend/src/pages/LibraryPage.tsx       # library feature out of scope
   rm gofreddy/frontend/src/pages/PricingPage.tsx       # no billing
   rm gofreddy/frontend/src/pages/UsagePage.tsx         # v2 addition — was missed in v1
   rm gofreddy/frontend/src/pages/LandingPage.tsx       # v2 decision — gofreddy.ai is separate marketing site; avoid double entry point
   rm -rf gofreddy/frontend/src/pages/library/           # whole subdir (5 files)
   rm gofreddy/frontend/src/content/marketing.ts        # PricingPage copy
   ```
4. **Canvas section deletion — keep 4, delete 38 (v2 corrected count):**
   Keep: `MonitorMentionsSection.tsx`, `MonitorSection.tsx`, `MonitorAnalyticsSection.tsx`, `MonitorWorkbench.tsx`.
   ```bash
   # All other files under canvas/sections/ must be deleted. 42 total → delete 38.
   # Then: Canvas.tsx line 28-65 has ~42 direct + lazy() imports. Second pass required:
   # grep Canvas.tsx for deleted names; remove import + switch/case references until build green.
   ```
5. **Component deletion:**
   ```bash
   rm -rf gofreddy/frontend/src/components/studio
   rm -rf gofreddy/frontend/src/components/video-gen
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
7. **SettingsPage trim — delete UsageBillingSection** (clean boundary; verified at `frontend/src/components/settings/UsageBillingSection.tsx` imported once on L12 + rendered once on L379 of SettingsPage.tsx):
   ```bash
   rm gofreddy/frontend/src/components/settings/UsageBillingSection.tsx
   ```
   Then in `SettingsPage.tsx`: delete the `import { UsageBillingSection }` line + the one `<UsageBillingSection />` render. That's the entire billing UI gone.
8. **Test file cleanup** — all `.test.tsx`/`.test.ts` files get deleted wholesale (no tests in scope):
   ```bash
   find gofreddy/frontend/src -name "*.test.ts" -delete
   find gofreddy/frontend/src -name "*.test.tsx" -delete
   ```
9. **Router update:** `src/main.tsx` — remove routes for `/library`, `/pricing`, `/usage`, `/` (LandingPage deleted; make `/` redirect to `/dashboard` or `/login`).
10. `npm install` — expect ~3 rounds of "fix compile errors" from dead imports.
11. `npm run generate-api` (or `npm run api:generate`) — regenerate types from local `openapi.json`.
12. **Env:**
    ```
    VITE_SUPABASE_URL=https://<project>.supabase.co
    VITE_SUPABASE_ANON_KEY=...
    VITE_API_BASE_URL=https://api.gofreddy.ai
    ```
13. `npm run build` → `dist/`. Deploy to Vercel or Fly static.

**Verification:**
- `npm run dev` at localhost:5173 → sign in → dashboard loads.
- Create a monitor via CLI → refresh dashboard → monitor appears.
- Open `/dashboard/chat` → send message → see SSE stream live.
- `/dashboard/settings` → create an API key → copy it, use in CLI.

### Phase E — Trim + deploy (M6, M8) — M7 tests skipped

**M6 — Trim pass** (in parallel with B1/B2, consolidate at end).

**Router-level surgery (v2 — exact imports from audit):**

| File | Surgery | Reason |
|---|---|---|
**Committed rule (no "if unused, verify" language):** strip every `billing.service`, `billing.repository`, `billing.credits.*` import and call-site. **Keep** `billing.models.BillingContext` reads (read-only tier gate). **Keep** `billing.tiers.Tier` + `TIER_CONFIGS` (enum/config).

| File | Surgery |
|---|---|
| **DELETE `src/api/routers/webhooks.py`** | Remove from `main.py` router registration; delete file. Stripe webhook handler. |
| `src/api/routers/analysis.py` | Strip `...jobs.*` imports and job-tracking endpoints (make sync). Keep `policies` usage (copied in M2). |
| `src/api/routers/deepfake.py` | Strip `...billing.credits.exceptions`, `...billing.service`. |
| `src/api/routers/usage.py` | Strip `...billing.credits.*`, `...billing.service.BillingService`. Keep `...billing.tiers.TIER_CONFIGS`. |
| `src/api/routers/preferences.py` | Strip `BillingService` import. Keep `Tier` enum. |
| `src/api/routers/api_keys.py` | Use Phase 1's `UserRepo.get_user_by_api_key` (verified at `gofreddy/src/api/users.py:L73`) in router directly. 2-3 line edit. No new repo class. |
| `src/api/routers/agent.py`, `conversations.py`, `monitoring.py`, `evolution.py`, `generation.py`, `video_projects.py` | Strip `billing.service` writes. Keep `billing.models.BillingContext` reads. |
| `src/api/dependencies.py` (after additive merge) | Don't add `get_policy_service` / `get_job_service` dep getters at all. Don't add `stripe_client` init. Do add `get_content_generation_service`. Keep `get_billing_context` (read-only). |

**Orchestrator tool handler surgery:**
- **DELETE `src/orchestrator/tool_handlers/manage_client.py`** — imports `ClientService` from skipped `src/clients/`. Multi-tenant SaaS feature.
- **DELETE `src/orchestrator/tool_handlers/manage_policy.py`** — imports `PolicyService`; audit says "likely not needed Phase 1" (brand-policy CRUD).
- Remove the deleted handlers from `src/orchestrator/tools.py` registration.

**Background workers + SaaS tooling:**
- `src/monitoring/intelligence/sentiment.py` — **no action needed**. It's pure SQL aggregation (cachetools-only, no ML deps). The plan previously claimed a 1.2GB HuggingFace model — that was wrong; freddy uses Gemini for sentiment classification (see `sentiment_classifier.py`) and has zero `transformers`/`torch` deps.
- `src/monitoring/worker.py` — don't wire into lifespan. Use sync `POST /v1/monitors/{id}/run` for now.
- `src/monitoring/alerts/delivery.py` — alerts go to `alert_events` table; webhook delivery deferred.
- `src/monitoring/workspace_bridge.py` — delete; drop optional `workspace_bridge` param from `monitoring/service.py:L56-62`.

**M7 — Tests: SKIPPED.** Phase 1's 22 integration tests (`tests/test_api/test_auth.py`, `test_membership.py`, `test_portal.py`) stay as regression check. No new tests written; no freddy tests ported. Manual smoke-test per phase via `docker run` + hitting `/v1/*` endpoints is the verification bar. If a specific CRUD path warrants coverage later, port the single relevant freddy test then — not now.

**Frontend test cleanup happens in M5** (`find gofreddy/frontend/src -name "*.test.*" -delete`).

**M8 — Cloud deploy:**

**Pre-deploy:** `cd gofreddy && uv lock` (regenerates `uv.lock` after M2's pyproject edits). Current gofreddy Dockerfile (pip-based) works — no uv multi-stage rebuild needed.

1. **Supabase:** create project at supabase.com → capture URL/ANON_KEY/JWT_SECRET → `supabase db push` (applies M1 migrations + seed).
2. **R2:** create two buckets `gofreddy-prod` + `gofreddy-test` → create API token with R2:Edit scope.
3. **Fly:**
   ```bash
   flyctl launch --name gofreddy-api --region iad --no-deploy
   flyctl volumes create data --size 10 --region iad
   flyctl secrets set \
     SUPABASE_URL=... SUPABASE_ANON_KEY=... SUPABASE_JWT_SECRET=... DATABASE_URL=... \
     R2_ACCOUNT_ID=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... R2_BUCKET_NAME=gofreddy-prod \
     GEMINI_API_KEY=... OPENAI_API_KEY=... XAI_API_KEY=... \
     MONITORING_XPOZ_API_KEY=... MONITORING_NEWSDATA_API_KEY=... MONITORING_APIFY_TOKEN=... \
     MONITORING_CLORO_API_KEY=... MONITORING_POD_ENGINE_API_KEY=... \
     DATAFORSEO_LOGIN=... DATAFORSEO_PASSWORD=... \
     FOREPLAY_API_KEY=... ADYNTEL_API_KEY=... ADYNTEL_EMAIL=... \
     EXTERNALS_MODE=real TASK_CLIENT_MODE=mock
   flyctl deploy
   flyctl certs create api.gofreddy.ai
   ```
4. **Frontend:** `npm run build` in `gofreddy/frontend/` → deploy `dist/` to Vercel / Cloudflare Pages / Fly static.
5. **DNS:** CNAME `api.gofreddy.ai` → `gofreddy-api.fly.dev`; CNAME `app.gofreddy.ai` → wherever frontend is hosted.

**M9 — Deferred items (explicit list, not done in this plan):**
- Background `monitoring/worker.py` — async monitor runs via Cloud Tasks. Phase 1 uses sync endpoint.
- `src/jobs/` — Cloud Tasks queue. Enable when async needed.
- `monitoring/alerts/delivery.py` — webhook + email alert fan-out.
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

# Monitoring adapters — 13 adapters ship with src/monitoring/adapters/; wire keys as clients sign up
MONITORING_XPOZ_API_KEY=           # X/Twitter posts (xpoz.py)
MONITORING_NEWSDATA_API_KEY=       # Global news (news.py)
MONITORING_APIFY_TOKEN=            # Apify — used by tiktok/facebook/linkedin/google_trends/reviews (Trustpilot, AppStore, PlayStore)
MONITORING_BLUESKY_ENABLED=false   # Bluesky AT Protocol (no API key required; just enable flag)
MONITORING_CLORO_API_KEY=          # v2 addition — AiSearchAdapter (ChatGPT/Perplexity citations) + geo Cloro provider
MONITORING_POD_ENGINE_API_KEY=     # v2 addition — PodEngineAdapter (podcast mentions)

# SEO providers (v2 addition — GSC + PageSpeed missed in v1)
DATAFORSEO_LOGIN=                  # DataForSEO — on-page, keywords, backlinks
DATAFORSEO_PASSWORD=
GSC_SERVICE_ACCOUNT_PATH=          # v2 addition — Google Search Console service account JSON path

# Generation adapters (v2 addition — Grok/FAL/TTS ship with src/generation/)
GENERATION_XAI_API_KEY=            # Grok video gen
GENERATION_FAL_API_KEY=            # fal.ai video/image gen
GENERATION_FISH_AUDIO_API_KEY=     # Fish Audio TTS
GENERATION_SUNO_API_KEY=           # Suno music gen

# Agency audit providers (already wired)
FOREPLAY_API_KEY=
ADYNTEL_API_KEY=
ADYNTEL_EMAIL=

# Runtime mode
ENVIRONMENT=production
EXTERNALS_MODE=real    # or fake in dev
TASK_CLIENT_MODE=mock  # cloud when M9 lands
```

---

## Open decisions (surface to user before execution)

V1-inherited questions that need user input before or during execution:

1. **Invite-only vs open signup.** Phase 1 defaults to invite-only (JR manually creates user+membership). Flip to open signup later by enabling Supabase's `enable_signup=true`. **Recommendation: invite-only for now.**
2. **API key distribution mechanism.** Until the `/dashboard/settings/api-keys` UI works, JR distributes keys manually (psql insert + email to client). **Recommendation: manual out-of-band for Phase 1; build UI in Phase 2.**
3. **Slug authority.** When CLI syncs data by slug and the slug isn't in the DB, what wins? **Recommendation: DB is authoritative.** CLI validates slug exists via `/v1/auth/me` before syncing; server rejects unknown slugs.
4. **Migration-time backfill.** Existing engagements (Polish derm clinic + legal firm) have JSONL session data on JR's laptop from pre-portal days. A one-shot `freddy sync --from-jsonl` import populates Postgres + R2 with that history. **Not in scope for Phase 1**; specify as a Phase 2 task if JR needs that history visible.

V2 audit additions:

5. **`orchestrator/tool_handlers/manage_client.py` + `manage_policy.py`.** Both break on copy (`clients/` skipped, `policies/` now copied but handler is SaaS-CRUD). Plan commits: DELETE both handlers outright (no replacement).

**Resolved into plan body (no longer "open"):** publishing adapters keep as-is, fetcher modules leave as-is, `content_gen/` copied in M2, landing page deleted in M5, conversations/workspace tables included in M1.

---

## Risks + mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **orchestrator is deeply coupled to billing/credits** | Won't import without trim | M6 strip pass per committed rule (strip `billing.service` writes, keep `billing.models.BillingContext` reads) |
| **Frontend has 48K LOC with many cross-dependencies** | `npm run build` will fail 3-5 times on first try | Delete files in waves, run `npm run build` between waves, fix imports |
| **CLI `api.py` incompatibility** | Breaks existing `freddy audit` commands | Move gofreddy's to `providers.py`, import from there in `audit.py` |
| **Mention adapters cost money per call** (Xpoz, NewsData, Apify) | Unexpected bills | Wire adapters only when a client's monitor needs them. Cheapest path: `ai_search` (Gemini) + `news` (NewsData) first. |

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
4. **M3 Agent engine** (orchestrator + tools + 10 tool routers)
5. **M4 CLI** (api.py split + 7 new commands)
6. **M5 Frontend** (clone + prune + build)
7. **M8 Cloud deploy** (once all green locally)
8. **M9 Document deferred items** (ongoing)

Estimated **5-7 days** for an engineer executing the plan (M7 tests cut).

---

## Summary punch list

```bash
# === Backend (M2 + M3) ===
cp -r freddy/src/sessions      gofreddy/src/   # verify
cp -r freddy/src/conversations gofreddy/src/
cp -r freddy/src/workspace     gofreddy/src/
cp -r freddy/src/preferences   gofreddy/src/
cp -r freddy/src/extraction    gofreddy/src/
cp -r freddy/src/content_gen   gofreddy/src/   # v2 addition — orchestrator dep
cp -r freddy/src/policies      gofreddy/src/   # v2 addition — analysis router + analyze_video dep
cp -r freddy/src/orchestrator  gofreddy/src/
cp -r freddy/src/brands        gofreddy/src/
cp -r freddy/src/creative      gofreddy/src/
cp -r freddy/src/demographics  gofreddy/src/
cp -r freddy/src/evolution     gofreddy/src/
cp -r freddy/src/stories       gofreddy/src/
cp -r freddy/src/trends        gofreddy/src/
cp -r freddy/src/search        gofreddy/src/

cp freddy/src/api/schemas.py            gofreddy/src/api/
cp freddy/src/api/schemas_discover.py   gofreddy/src/api/
cp freddy/src/api/schemas_monitoring.py gofreddy/src/api/
cp freddy/src/api/logging.py            gofreddy/src/api/
cp freddy/src/api/fake_externals.py     gofreddy/src/api/

cp freddy/src/feedback.py               gofreddy/src/
cp freddy/src/feedback_loop_config.py   gofreddy/src/

mkdir -p gofreddy/src/billing
cp freddy/src/billing/tiers.py          gofreddy/src/billing/
touch gofreddy/src/billing/__init__.py

# 20 routers split by phase (webhooks DELETED; agent + 10 tool routers = M3 because they need orchestrator)
# M2 (9 CRUD routers — no orchestrator dep):
for r in sessions monitoring conversations workspace preferences health usage media api_keys; do
  cp freddy/src/api/routers/${r}.py gofreddy/src/api/routers/
done
# M3 (agent + 10 tool routers — after orchestrator lands):
for r in agent analysis batch competitive deepfake evaluation generation geo publishing seo video_projects; do
  cp freddy/src/api/routers/${r}.py gofreddy/src/api/routers/
done

# After cp: delete orchestrator handlers that import skipped modules
rm gofreddy/src/orchestrator/tool_handlers/manage_client.py
rm gofreddy/src/orchestrator/tool_handlers/manage_policy.py
# Delete their registration lines from src/orchestrator/tools.py (surgical line-delete, not rewrite).

# === API top-level files (M2) — additive merge, NOT cp+trim ===
# src/api/dependencies.py: keep gofreddy's Phase 1 file (305 lines, already correctly trimmed).
#   Paste freddy's service init blocks (L1060-1561) into existing lifespan() for:
#     ContentGenerationService, SessionService, ConversationService, WorkspaceService,
#     PreferenceService, ExtractionService, PolicyService
#   Add matching get_<x>_service dependency getters.
# src/api/main.py: append 20 router registrations to gofreddy's Phase 1 main.py.
# cp freddy/src/api/logging.py (new file, no gofreddy equivalent).
# Files untouched (Phase 1 gofreddy-only): dependencies.py base, main.py base, users.py, membership.py,
#   middleware.py, exceptions.py, rate_limit.py, routers/login.py, routers/portal.py.

# === CLI main.py (M4) — cp then re-add gofreddy-unique commands ===
cp freddy/cli/freddy/main.py gofreddy/cli/freddy/main.py
# Then re-add: app.add_typer(audit.app, ...) for audit/auto_draft/client/save/setup/sitemap.

# === CLI (M4) ===
mv gofreddy/cli/freddy/api.py gofreddy/cli/freddy/providers.py
cp freddy/cli/freddy/api.py    gofreddy/cli/freddy/
cp freddy/cli/freddy/output.py gofreddy/cli/freddy/
for c in auth session monitor query_monitor search_mentions digest evaluate; do
  cp freddy/cli/freddy/commands/${c}.py gofreddy/cli/freddy/commands/
done

# === Deps + lock refresh (M2) ===
# Edit gofreddy/pyproject.toml: add sse-starlette, slowapi, PyJWT[crypto] (upgrade from pyjwt).
# NOT added: redis/resend/supabase SDK (verified zero imports in freddy/src/), asyncpg version bump.
cd gofreddy && uv lock

# === Frontend (M5) ===
cp -r freddy/frontend/ gofreddy/frontend/
rm -rf gofreddy/frontend/node_modules
# Page deletion (5 files):
rm gofreddy/frontend/src/pages/LibraryPage.tsx
rm gofreddy/frontend/src/pages/PricingPage.tsx
rm gofreddy/frontend/src/pages/UsagePage.tsx
rm gofreddy/frontend/src/pages/LandingPage.tsx
rm -rf gofreddy/frontend/src/pages/library/             # 5 files
rm gofreddy/frontend/src/content/marketing.ts
# Canvas sections: delete 38, keep 4 (MonitorMentionsSection/MonitorSection/MonitorAnalyticsSection/MonitorWorkbench)
# SettingsPage: rm components/settings/UsageBillingSection.tsx + remove import/render in SettingsPage.tsx.
# Delete ALL .test.tsx/.test.ts files (no tests in scope):
find gofreddy/frontend/src -name "*.test.ts" -delete
find gofreddy/frontend/src -name "*.test.tsx" -delete
# npm install → fix compile errors → npm run api:generate → npm run build

# === DB (M1) ===
# Write supabase/migrations/20260418000001_monitoring_sessions.sql:
#   - Extract freddy setup_test_db.sql L1362-1644 verbatim (monitoring + sessions + alerts)
#   - Extract L857-920 (conversations + workspace tables — v2 includes these in M1, not M9)
#   - Add ALTER TABLE agent_sessions/monitors/alert_rules ADD COLUMN client_id
#   - Add RLS policies on all 25+ new tables
cp freddy/supabase/seed.sql        gofreddy/supabase/seed.sql    # v2 addition — monitor fixtures
cp freddy/scripts/ci_bootstrap.sql gofreddy/scripts/             # v2 addition — CI DB bootstrap
# supabase db reset to verify
```

When this plan ships: users log in to `app.gofreddy.ai`, see live session telemetry streaming from the CLI, see monitors updating with real mentions from 13 adapters (when clients enable them), chat with the agent via SSE stream, see alert history in-dashboard (webhook delivery deferred to M9). The portal placeholder shipped in Phase 1 is retired — everything behind the auth wall is real.
