---
date: 2026-04-18
topic: migrate-autoresearch-to-gofreddy
status: active
---

# Migrate autoresearch from freddy to gofreddy — full and complete

## Context

Autoresearch is freddy's evolutionary scoring pipeline: 4 lanes (geo, competitive, monitoring, storyboard) running agent-driven variant programs scored by a frozen external evaluator. Designed per Meta-Harness (arxiv 2603.28052) and HyperAgents (arxiv 2603.19461): variant layer evolves, evaluator layer stays frozen and externally hosted.

Goal: move autoresearch to `gofreddy/` so evolution runs happen there. Preserve the 7 recent fix commits (c199a5d → 49e87a2). Port every piece of backend autoresearch genuinely needs — and nothing more (no UI, no Stripe, no video pipeline, no newsletter).

## Approach — copy + edit-in-place, no reimplementation

**Every file in this plan is either `cp`d verbatim from freddy, or overwritten with freddy's version, or the existing gofreddy file is edited in place.** No logic is retyped or rewritten.

- Service/router/CLI files: `cp freddy/<path> gofreddy/<path>` — byte-identical
- Stale gofreddy files: `cp` to overwrite (only when freddy has newer bug fixes)
- Existing gofreddy files (main.py, cli/main.py, dependencies.py, .env.example, .gitignore, pyproject.toml): **delete specific lines** (billing imports) or **append specific lines** (router registrations, lifespan init blocks, env vars). No rewrites.
- Lifespan init blocks pasted into `gofreddy/src/api/main.py` are themselves copied from specific line ranges in `freddy/src/api/dependencies.py` (each block cites its source range).
- The Supabase migration is **extracted** from freddy's `setup_test_db.sql` — `CREATE TABLE` blocks copied verbatim, not rewritten.
- The autoresearch module is `rsync`d as a whole tree.

If this plan ever says "implement" or "write a new X", that's a bug — fix it back to "copy from freddy `<path>:<line>`".

## Two-harness finding (not a concern)

There are two Python packages both named `harness`:
- `freddy/harness/` — the QA eval-fix system. Not used by autoresearch. **Stays in freddy.**
- `freddy/autoresearch/harness/` — the session harness (agent, backend, session_evaluator, stall, telemetry, util). Lives inside autoresearch tree, comes along automatically with `cp -r autoresearch/`.

No separate harness copy step is required.

## Autoresearch module is self-contained

Verified by `grep -rE "^(from|import) " autoresearch/`:
- Zero `from src.*` imports
- Zero non-stdlib Python packages beyond `fcntl` (Unix)
- All internal imports resolve via `sys.path` setup in `autoresearch/harness/__init__.py`
- Shells out to 12 `freddy` subcommands via subprocess

The complexity is everything *outside* autoresearch: backend services, HTTP routers, CLI tool commands, and Supabase tables.

## Complete backend dependency trace

### CLI commands autoresearch invokes (12)

Verified by grepping program text + workflow code:

| CLI | Backend route(s) | Router file |
|---|---|---|
| `freddy evaluate variant/critique` | `/v1/evaluation/evaluate`, `/v1/evaluation/critique` | `evaluation.py` |
| `freddy monitor mentions/sentiment/sov/baseline` | `/v1/monitors/{id}/{mentions,sentiment,share-of-voice}` | `monitoring.py` |
| `freddy digest persist/list` | `/v1/monitors/{id}/digests` | `monitoring.py` |
| `freddy search_mentions` | `/v1/monitors/{id}/mentions` | `monitoring.py` |
| `freddy trends` | `/v1/monitors/{id}/trends-correlation` | `monitoring.py` |
| `freddy query_monitor` | `/v1/monitors/{id}/{sov,sentiment}` | `monitoring.py` |
| `freddy detect` | `/v1/geo/detect` | `geo.py` |
| `freddy visibility` | `/v1/geo/visibility` | `geo.py` |
| `freddy scrape` | `/v1/geo/scrape` | `geo.py` |
| `freddy search-ads` | `/v1/competitive/ads/search` | `competitive.py` |
| `freddy competitive brief` | `/v1/competitive/brief` — **lives in `reports.py`, not `competitive.py`** | — (CLI not called by autoresearch; skip backend wiring) |
| `freddy search_content` | Direct-to-provider (IC API) | — |
| `freddy sitemap` | In-process (`src.geo.sitemap.SitemapParser`) | — |
| `freddy seo keywords/audit` | Unused at runtime | SKIP |

Verified by `grep -hE "freddy seo" autoresearch/archive/current_runtime/{workflows,runtime,scripts}/*.py`: only mention is a table entry in a markdown program, never called. CLI file still gets copied for command registry completeness; backend wiring skipped.

### Backend files needed

**Routers** (4 files, 1,826 LOC):
| File | LOC |
|---|---|
| `src/api/routers/evaluation.py` | 221 |
| `src/api/routers/geo.py` | 565 |
| `src/api/routers/competitive.py` | 139 |
| `src/api/routers/monitoring.py` | 901 |

**Schemas** (2 files, 1,139 LOC):
| File | LOC |
|---|---|
| `src/api/schemas.py` | 802 |
| `src/api/schemas_monitoring.py` | 337 |

**Evaluation backend** (2 files, 716 LOC):
| File | LOC |
|---|---|
| `src/evaluation/service.py` | 564 |
| `src/evaluation/repository.py` | 152 |

**Evaluation overwrites** (newer freddy versions have our recent fixes):
- `src/evaluation/structural.py` — commits 92f6e3a, 49e87a2, 6e3c7e8
- `src/evaluation/judges/__init__.py` — commit c4d1066 (fuzzy_match threshold 0.5)

### Billing decision: STRIP, don't port

The 4 routers import `require_pro_geo / require_pro_competitive / require_pro_geo_keywords` + `get_billing_context` + `BillingContext` to gate endpoints by tier. Autoresearch is internal tooling — no tier gating needed.

**Approach**: edit the 4 routers in place to remove billing dependencies. No billing/ module ported to gofreddy.

Specific edits per router (~30 in-place changes total):
- Delete `from ..dependencies import require_pro_geo` (and competitive variant)
- Delete `from ...billing.models import BillingContext`
- Delete `from ...billing.tiers import Tier, get_tier_config` (monitoring only)
- Delete `billing: BillingContext = Depends(require_pro_geo)` arguments from endpoint signatures
- Delete `billing: BillingContext = Depends(get_billing_context)` arguments
- Delete any `billing.tier` checks inside endpoint bodies (replace with unconditional allow)

### Lifespan service initialization (gofreddy `src/api/main.py::lifespan`)

Port 4 service init blocks to gofreddy's existing lifespan function. Gofreddy puts lifespan in `main.py`, not `dependencies.py` like freddy — insert each block after existing `app.state.session_service = SessionService(session_repo)` line.

**EvaluationService** — copy from freddy `src/api/dependencies.py:530-601` verbatim. Approximately 60 LOC covering: EvaluationSettings init → per-provider judge construction loop (GeminiJudge / OpenAIJudge, skipping OpenAI when key missing) → degraded-ensemble warnings → `EvaluationService(...)` construction. Paste into gofreddy's `main.py::lifespan` after the `app.state.session_service = SessionService(session_repo)` line. Only adapt indentation if needed.

**GeoService** — copy pattern from freddy `src/api/dependencies.py:1388-1400` (the `if geo_settings.enable_geo: geo_repo = PostgresGeoRepository(...); app.state.geo_service = GeoService(...)` block). Approximately 10 LOC. The pasted block should be identical to freddy's lines, only fix up indentation if gofreddy's lifespan indents differently.

**CompetitiveAdService** — copy pattern from freddy `src/api/dependencies.py:1353-1398` (the competitive-ad-intelligence block: ForeplayProvider + AdyntelProvider + CompetitiveAdService construction wrapped in try/except). Approximately 25 LOC. Paste verbatim — only fix indentation for gofreddy's lifespan structure.

**MonitoringService** (~100 LOC — trimmed from freddy's ~300):

Port freddy's init cascade from `src/api/dependencies.py:729-1083` WITH these exclusions:
- Skip `MonitorWorker` init (lines 1086-1093) — background alert job, autoresearch doesn't use
- Skip `WorkspaceBridge` init — drop the param from `MonitoringService.__init__` call (the monitoring-transfer plan flags the same deletion)
- Skip `AlertEvaluator` init — no alert rules in autoresearch
- Skip `CreativePatternService` + other PR-048+ additions below the MonitoringService block
- **Keep** the full adapter registry cascade (Bluesky, Xpoz, IC, NewsData, Apify ×6, PodEngine, AiSearch) — each is already guarded by `if env_var: init`, missing credentials just means that data source is unavailable
- **Keep** `IntentClassifier` init (Gemini-based) — cheap, referenced by some monitor endpoints

Cleanup block in `finally:` — port only the services we initialized:
```python
for svc_name in ("evaluation_service", "geo_service", "ad_service", "monitoring_service", "foreplay_provider", "adyntel_provider"):
    svc = getattr(app.state, svc_name, None)
    if svc:
        try:
            await svc.close()
        except Exception:
            logger.exception("Error closing %s", svc_name)
```

### Domain code gaps — minimal set after transitive-dep trace

Did a full transitive-dep trace from each router/service to find the real minimum needed. Many files originally flagged as "missing" are not actually referenced by any code autoresearch exercises — skipping them saves ~3,200 LOC.

**Required ports — verified by import trace** (11 files, ~4,121 LOC):

`src/monitoring/` core (2 files, 2,186 LOC):
| File | LOC | Why needed |
|---|---|---|
| `service.py` | 595 | MonitoringService — every `/monitors/*` endpoint calls this |
| `repository.py` | 1591 | PostgresMonitoringRepository — all monitor DB ops |

`src/monitoring/` subdirs (5 files, 624 LOC):
| File | LOC | Why needed |
|---|---|---|
| `alerts/delivery.py` | 136 | Router endpoint #14 imports `WebhookDelivery` locally. Included for completeness — autoresearch shouldn't hit it, but keeps the monitoring router 100% functional for agency use. |
| `alerts/evaluator.py` | 125 | Not directly imported by ported files, but included alongside delivery.py so the alerts subsystem is complete and future-proofed for agency alert features. |
| `intelligence/sentiment.py` | 131 | `service.sentiment_time_series()` calls `get_sentiment_time_series` from this |
| `intelligence/share_of_voice.py` | 112 | `service.get_share_of_voice()` calls `calculate_sov` from this |
| `intelligence/trends_correlation.py` | 120 | `service.get_trends_correlation()` calls `get_trends_correlation` from this |

`src/geo/` core (3 files, 1,091 LOC):
| File | LOC | Why needed |
|---|---|---|
| `service.py` | 262 | GeoService — `/geo/*` endpoints call this |
| `repository.py` | 192 | PostgresGeoRepository — imported by service.py |
| `orchestrator.py` | 637 | `run_geo_audit` — imported by service.py |

`src/competitive/` (1 file, 219 LOC):
| File | LOC | Why needed |
|---|---|---|
| `creator_search.py` | 219 | Imported by competitive/__init__.py and router; lightweight (common.cost_recorder only) |

**Minor file-level overwrites** (2 files — `__init__.py` only):
- `src/geo/__init__.py` — add `from .service import GeoService` and `"GeoService"` to `__all__`
- `src/competitive/__init__.py` — add `from .creator_search import CreatorSearchService` + `BriefGenerationError, BriefNotFoundError` to `__all__`; exceptions already in gofreddy's `exceptions.py`

**DO NOT overwrite `monitoring/exceptions.py`** — verified gofreddy's version is a superset of freddy's (has all 11 classes freddy has PLUS `ICUnavailableError`). Overwriting would delete a class gofreddy needs.

### SKIPPED from domain port — NOT referenced on any autoresearch code path

Verified by grep: these files are only imported by lifespan init blocks we're already skipping, or by features autoresearch doesn't touch.

`src/monitoring/` core (5 files, 1,061 LOC skipped):
- `worker.py` — only imported by `dependencies.py` lifespan (`MonitorWorker` init — we skip); and `internal.py` router (not ported). Has deep billing integration.
- `analytics_service.py` — not imported by `service.py` or `repository.py` or monitoring router
- `repository_analytics.py` — only referenced in a comment in `repository.py`
- `dispatcher.py` — not imported by the code paths autoresearch uses
- `workspace_bridge.py` — `service.py` imports it inside `if TYPE_CHECKING:` only. Runtime signature accepts `workspace_bridge: WorkspaceBridge | None = None` via `from __future__ import annotations`, so the class doesn't need to be importable. Passing `None` at init is sufficient.

(`alerts/delivery.py` and `alerts/evaluator.py` are now ported — see required list above. Earlier drafts of this plan skipped them based on grep coverage, but per "err toward include when uncertain" we include them. Cost: 261 LOC. Benefit: zero risk of a runtime surprise from a dynamic caller we didn't scan.)

`src/monitoring/comments/` (3 files, 617 LOC skipped):
- `repository.py`, `service.py`, `sync.py` — `monitoring/service.py` and `monitoring/repository.py` don't import any of these; monitoring router has no `/comments` endpoints. (Comments module is a separate feature for a dashboard that autoresearch doesn't use.)

`src/monitoring/crm/` (2 files, 228 LOC skipped):
- `repository.py`, `service.py` — same rationale as comments.

`src/monitoring/intelligence/post_ingestion.py` (335 LOC skipped):
- Only referenced in a docstring comment in `repository.py`; no runtime import.

`src/competitive/` (3 files, 1,000 LOC skipped):
- `brief.py` (694) — the `/competitive/brief` endpoint autoresearch would theoretically hit actually lives in `src/api/routers/reports.py` (not the competitive router), and `freddy competitive brief` is not called by any autoresearch program. Verified by `grep -rhE "freddy competitive" autoresearch/` → empty.
- `repository.py` (188) — only used by brief.py flow
- `intelligence/partnerships.py` (118) — only used by brief.py

**Total saved by trace-based trimming**: ~2,980 LOC across 12 files (vs. naive "cp everything missing"). Earlier estimate said 3,241 / 14 files; the 2 alerts/ files were added back.

### Already present in gofreddy (verified byte-identical or semantically sufficient)

- `src/common/{cost_recorder, exceptions, gemini_models, sanitize, enums}.py` — all present
- `src/monitoring/adapters/` — 13 adapters byte-identical count
- `src/monitoring/{config, models, discovery, query_builder, query_sanitizer, fetcher_protocol}.py` — present
- `src/monitoring/alerts/models.py` — present
- `src/monitoring/comments/models.py` — present (not needed but exists)
- `src/monitoring/crm/models.py` — present (not needed but exists)
- `src/monitoring/intelligence/{intent, commodity_baseline, engagement_predictor, metric_computations, models_analytics, performance_patterns, sentiment_classifier}.py` — present
- `src/geo/{config, models, exceptions, analyzer, detector, extraction, formatter, generator, http_checks, link_graph, scraper, sitemap, patterns, article_postprocess, fetcher}.py` — present
- `src/geo/providers/cloro.py` — present
- `src/competitive/{config, models, exceptions, service, providers, markdown, pdf, schemas, utils, vision}.py` — present (service.py byte-identical, has `CompetitiveAdService`)
- `src/competitive/intelligence/` — present (only `__init__.py`; partnerships.py skipped)

### Supabase tables needed

Beyond gofreddy's existing schema (sessions, action_log, iteration_log, users, api_keys, clients, user_client_memberships):

**From `freddy/scripts/setup_test_db.sql`, extract**:
- `evaluation_results` (judge cache) — mandatory
- `monitors`, `mention_runs`, `mentions` — monitoring lane
- `alert_rules`, `alert_events` — may skip if AlertEvaluator init skipped
- `weekly_digests` — digest command
- `changelog_entries` — classify-intent, approve/reject flows
- `sentiment_classifications` — sentiment endpoint cache
- `geo_audits` — geo audit (CLI doesn't hit /audit, but GeoService may persist state)
- `competitive_ad_searches` — competitive search (verify exact table name)

All fit in one migration file: `gofreddy/supabase/migrations/20260418000001_autoresearch_tables.sql`.

Skip tables tied to features autoresearch doesn't use: video_projects, creator_profiles, stripe_events, webhook_deliveries, etc.

### Env vars needed

Autoresearch adds these env vars to gofreddy (document in `.env.example`):

**CLI auth**:
- `FREDDY_API_KEY` (generated per dev user)
- `FREDDY_API_BASE_URL=http://127.0.0.1:8000`

**Judges (evaluation)**:
- `OPENAI_API_KEY`, `GEMINI_API_KEY` (gofreddy already has these)

**Geo lane**:
- `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` (optional; geo falls back if missing)

**Competitive lane**:
- `FOREPLAY_API_KEY` OR `ADYNTEL_API_KEY` (at least one required for `search-ads`)

**Monitoring lane** (all optional — each adapter gates on presence):
- `XPOZ_API_KEY`, `IC_API_KEY`, `NEWSDATA_API_KEY`, `APIFY_TOKEN`, `POD_ENGINE_API_KEY`, `AI_SEARCH_API_KEY`, `BLUESKY_APP_PASSWORD`

## Existing plan assessment

`gofreddy/docs/plans/2026-04-17-monitoring-transfer-plan.md` (764 lines) overlaps ~70% of our backend needs (updated from earlier ~40% after full trace):
- Ports `monitoring.py`, `competitive.py`, `geo.py` routers
- Ports `schemas_monitoring.py`
- Ports `billing/tiers.py` (we're stripping instead — cleaner)
- Lifespan additive merge for monitoring/geo/competitive services
- Ports `evaluate.py` CLI + `evaluation.py` router

**Decision**: this plan is self-contained and doesn't depend on monitoring-transfer plan running first. Where they overlap, this plan's `cp` is idempotent. If monitoring-transfer plan runs first, most of our Phase 2-3 becomes no-ops; we just add the missing evaluation pieces + autoresearch module + billing strip.

## Scope boundaries

- **No tests**. Autoresearch has minimal existing tests; not porting. No new tests written.
- **No billing**. Strip from routers; don't port billing/.
- **No SEO backend**. `freddy seo` referenced in program text but never called at runtime. CLI file still copied for registry completeness.
- **No MonitorWorker / WorkspaceBridge / AlertEvaluator**. Not on autoresearch's path.
- **No video_projects / newsletter / creative-patterns / deepfake / fraud** routers or services. Autoresearch doesn't touch them.
- **No autoresearch redesign**. No file-based judge cache, no inline judges. Preserve Meta-Harness invariant.
- **No session artifact migration**. Fresh archive in gofreddy.
- **No lineage.jsonl migration**. Fresh evolution history.

## Design alignment (Meta-Harness / HyperAgents)

Evaluator lives outside variant edit surface. In gofreddy after this migration:

| Evolvable (variant modifies) | Frozen (variant cannot touch) |
|---|---|
| `autoresearch/archive/v*/{programs,runtime,workflows,scripts}` | `src/evaluation/*` |
| `autoresearch/archive/v*/run.py` | `src/api/routers/*` |
| `autoresearch/{evolve,frontier,evaluate_variant,...}.py` | `cli/freddy/commands/*` |
| | `autoresearch/harness/*` (inner session harness) |

Agent working directory at runtime: `gofreddy/autoresearch/archive/v*/sessions/<session>/`. Cannot traverse up without explicit subprocess. Boundary preserved byte-for-byte.

## What gofreddy has (verified)

- `src/evaluation/{__init__,config,exceptions,models,rubrics}.py` — byte-identical to freddy
- `src/evaluation/judges/{openai,gemini}.py` — byte-identical
- `src/{geo, competitive, monitoring, seo}/` — present with differences (see domain audit)
- `src/common/exceptions.py::PoolExhaustedError` — line 4
- `src/api/dependencies.py::get_current_user_id` — line 308
- `src/api/rate_limit.py::limiter` — present
- `cli/freddy/{api,session,output,config,main}.py` — present (api.py + session.py byte-identical to freddy)
- Deps in `pyproject.toml`: `asyncpg`, `fastapi`, `uvicorn`, `httpx`, `typer`, `pydantic`, `openai`, `google-genai`
- Entry point: `freddy = "cli.freddy.main:app"`

## Migration phases

Sequential. One commit per phase. Commits to `main` (per user convention).

### Phase 1 — Supabase migration

**Create**: `gofreddy/supabase/migrations/20260418000001_autoresearch_tables.sql`

Source: `freddy/scripts/setup_test_db.sql`. Extract and concatenate `CREATE TABLE IF NOT EXISTS` blocks + their indexes for:
- `evaluation_results`
- `monitors`, `mention_runs`, `mentions`
- `weekly_digests`, `sentiment_classifications`, `changelog_entries`
- `geo_audits`
- `competitive_ad_searches` (verify name)

Strip `user_id UUID REFERENCES users(id)` only if gofreddy's users table schema differs — spot-check first.

**Verify**:
```
cd gofreddy && supabase db reset
psql $DATABASE_URL -c "\d evaluation_results"   # expect columns + indexes
psql $DATABASE_URL -c "\d monitors"             # expect monitor schema
```

**Commit**: `feat(db): add autoresearch backend tables (evaluation_results + monitors + ...)`

### Phase 2 — Backend evaluation service + router

**Copy verbatim**:
```
cp freddy/src/evaluation/service.py      gofreddy/src/evaluation/service.py
cp freddy/src/evaluation/repository.py   gofreddy/src/evaluation/repository.py
cp freddy/src/api/routers/evaluation.py  gofreddy/src/api/routers/evaluation.py
```

**Overwrite** (stale in gofreddy — missing recent fixes):
```
cp freddy/src/evaluation/structural.py        gofreddy/src/evaluation/structural.py
cp freddy/src/evaluation/judges/__init__.py   gofreddy/src/evaluation/judges/__init__.py
```

**No billing strip needed for evaluation router** — verified: `evaluation.py` imports are `rate_limit`, `evaluation.models`, `evaluation.service`, `get_current_user_id`. Zero billing deps.

**Add dep helpers to `gofreddy/src/api/dependencies.py`** — the monitoring router (ported in Phase 3) imports `get_monitoring_service` and `get_webhook_delivery`. Append these to gofreddy's dependencies.py:
```python
def get_monitoring_service(request: Request):
    """Dependency providing MonitoringService."""
    return request.app.state.monitoring_service


def get_webhook_delivery(request: Request):
    """Dependency providing WebhookDelivery for alert endpoints (None if unavailable)."""
    return getattr(request.app.state, "webhook_delivery", None)
```
Not strictly needed until Phase 3, but adding now avoids a second dependencies.py edit.

**Edit `gofreddy/src/api/main.py`**:
1. Add `from .routers import evaluation as evaluation_router`
2. In lifespan (after `app.state.session_service = ...`), insert `EvaluationService` init block (see "Lifespan service initialization" above)
3. Add cleanup for `evaluation_service` in lifespan `finally:`
4. Add `app.include_router(evaluation_router.router, prefix="/v1")` after existing registrations

**Verify**:
```
cd gofreddy && uv run uvicorn src.api.main:create_app --factory --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/v1/openapi.json | jq '.paths | keys[]' | grep evaluation
```

**Commit**: `feat(evaluation): backend service + repository + router + lifespan wiring`

### Phase 3 — Backend geo + competitive + monitoring routers

**Copy verbatim**:
```
cp freddy/src/api/routers/geo.py          gofreddy/src/api/routers/geo.py
cp freddy/src/api/routers/competitive.py  gofreddy/src/api/routers/competitive.py
cp freddy/src/api/routers/monitoring.py   gofreddy/src/api/routers/monitoring.py
cp freddy/src/api/schemas.py              gofreddy/src/api/schemas.py
cp freddy/src/api/schemas_monitoring.py   gofreddy/src/api/schemas_monitoring.py
```

**Strip billing from each router** (in-place edits):

For `geo.py`, `competitive.py`, `monitoring.py`:
- Delete `from ..dependencies import require_pro_geo` (and competitive / any other require_pro_* import)
- Delete `from ...billing.models import BillingContext`
- Delete `from ...billing.tiers import Tier, get_tier_config` (monitoring only)
- Delete `from ..dependencies import get_billing_context` if present
- For each `@router.post/@router.get` endpoint, remove parameters like `billing: BillingContext = Depends(require_pro_geo)` and `billing: BillingContext = Depends(get_billing_context)`
- Search endpoint bodies for `billing.tier` / `get_tier_config(billing.tier)` references and delete tier-check branches (replace with unconditional success path)

Expected edit count: ~30 small deletions across 3 files. Use `grep -n "billing\|require_pro" gofreddy/src/api/routers/{geo,competitive,monitoring}.py` to inventory, then edit.

**Edit `gofreddy/src/api/main.py`**:
1. Add router imports: `from .routers import geo as geo_router, competitive as competitive_router, monitoring as monitoring_router`
2. In lifespan, insert `GeoService` + `CompetitiveAdService` + `MonitoringService` (trimmed) init blocks
3. Add cleanup entries in `finally:` for `geo_service`, `ad_service`, `monitoring_service`, `foreplay_provider`, `adyntel_provider`
4. Register routers: `app.include_router(geo_router.router, prefix="/v1")` etc.

**Verify**:
```
cd gofreddy && uv run uvicorn src.api.main:create_app --factory --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/v1/openapi.json | jq '.paths | keys[]' | grep -E "(geo|monitor|competitive)"
```

Expect to see `/v1/geo/detect`, `/v1/geo/visibility`, `/v1/geo/scrape`, `/v1/competitive/ads/search`, `/v1/competitive/brief`, `/v1/monitors/{monitor_id}/mentions`, etc.

**Commit**: `feat(backend): geo + competitive + monitoring routers with billing stripped`

### Phase 4 — Port minimum domain code (~4,121 LOC across 11 files)

Post-trace list. `cp` each one:

**Monitoring core** (2 files):
```
cp src/monitoring/service.py     ~/Documents/GitHub/gofreddy/src/monitoring/
cp src/monitoring/repository.py  ~/Documents/GitHub/gofreddy/src/monitoring/
```

**Monitoring alerts** (2 files):
```
cp src/monitoring/alerts/{delivery,evaluator}.py \
   ~/Documents/GitHub/gofreddy/src/monitoring/alerts/
```

**Monitoring intelligence** (3 files):
```
cp src/monitoring/intelligence/{sentiment,share_of_voice,trends_correlation}.py \
   ~/Documents/GitHub/gofreddy/src/monitoring/intelligence/
```

**Geo** (3 files):
```
cp src/geo/{service,repository,orchestrator}.py \
   ~/Documents/GitHub/gofreddy/src/geo/
```

**Competitive** (1 file):
```
cp src/competitive/creator_search.py \
   ~/Documents/GitHub/gofreddy/src/competitive/
```

**Overwrite 2 `__init__.py` files** (add exports for newly-ported classes):
```
cp src/geo/__init__.py              ~/Documents/GitHub/gofreddy/src/geo/
cp src/competitive/__init__.py      ~/Documents/GitHub/gofreddy/src/competitive/
```

Do NOT overwrite `src/monitoring/exceptions.py` — gofreddy's version is a superset (has `ICUnavailableError` that freddy doesn't).

**No billing strip needed** in ported files — verified by grep. Clean.

**Verify**:
```
cd gofreddy
uv run python -c "from src.monitoring.service import MonitoringService; print('mon service ok')"
uv run python -c "from src.monitoring.repository import PostgresMonitoringRepository; print('mon repo ok')"
uv run python -c "from src.monitoring.intelligence.sentiment import get_sentiment_time_series; print('sentiment ok')"
uv run python -c "from src.geo import GeoService; print('geo ok')"
uv run python -c "from src.competitive import CreatorSearchService, CompetitiveAdService; print('competitive ok')"
```

If any import fails: most likely the `__init__.py` overwrite pulled in a reference to a file we intentionally skipped. Fix by editing gofreddy's `__init__.py` to drop that re-export.

**Commit**: `feat(domain): port monitoring/geo/competitive service layer from freddy (~4.1K LOC, trace-minimized)`

### Phase 5 — CLI: 13 commands

**Copy verbatim**:
```
for cmd in evaluate monitor digest search_mentions detect search_ads visibility \
           scrape search_content seo trends query_monitor competitive; do
  cp freddy/cli/freddy/commands/${cmd}.py gofreddy/cli/freddy/commands/
done
```

All 13 use `from ..api`, `from ..config`, `from ..output`, `from ..session` — verified that gofreddy's versions of these modules are byte-identical or compatible.

**Edit `gofreddy/cli/freddy/main.py`**:
- Import the 13 new command modules
- Add `app.command(name="...")` registrations
- If `sitemap` command collides with gofreddy's existing `sitemap`: `diff` both; keep whichever is byte-identical, if both exist and differ, keep freddy's (autoresearch needs this specific one)

**Verify**:
```
cd gofreddy && uv run freddy --help   # expect 23 commands total (10 gofreddy-native + 13 new)
uv run freddy evaluate --help         # expect subcommands: variant, critique, review
uv run freddy monitor --help          # expect: mentions, sentiment, sov, baseline
```

**Commit**: `feat(cli): copy evaluate + 12 tool commands from freddy`

### Phase 6 — autoresearch/ module

**Copy**:
```
cd /Users/jryszardnoszczyk/Documents/GitHub/freddy
rsync -a \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='archive/v*/sessions/' \
  --exclude='archive/v*/archived_sessions/' \
  --exclude='archive/v*/logs/' \
  --exclude='archive/v*/meta-session.log' \
  --exclude='archive/v*/runs/' \
  --exclude='archive/failures.log' \
  autoresearch/ ~/Documents/GitHub/gofreddy/autoresearch/
```

`current_runtime/` is a regular directory (not a symlink) — rsync handles it correctly.

**Edit `gofreddy/.gitignore`** — append the autoresearch block from `freddy/.gitignore:124-132`:
```
# Evolution — variant runtime data
autoresearch/archive/v*/sessions/
autoresearch/archive/v*/archived_sessions/
autoresearch/archive/v*/logs/
autoresearch/archive/v*/meta-session.log
autoresearch/archive/failures.log
autoresearch/archive/current_runtime/
autoresearch/archive/core/
autoresearch/archive/workflows/
```

**Edit `gofreddy/pyproject.toml`** — register `autoresearch` as a package so it's importable. Add to packages list in whichever build-system config gofreddy uses (verify existing section style).

No new runtime deps — autoresearch uses stdlib + `fcntl` only.

**Verify**:
```
cd gofreddy && uv sync
uv run python -c "import autoresearch; from autoresearch import frontier; print(frontier.DOMAINS)"
uv run python -c "from autoresearch.harness import agent, backend, session_evaluator; print('ok')"
uv run python autoresearch/archive/v006/run.py --help
```

**Commit**: `feat(autoresearch): copy module from freddy (inc. inner harness + archive v001-v006)`

### Phase 7 — Env + backend restart script

**Edit `gofreddy/.env.example`** — append:
```
# Autoresearch — CLI auth
FREDDY_API_KEY=
FREDDY_API_BASE_URL=http://127.0.0.1:8000

# Autoresearch — geo lane (optional)
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=

# Autoresearch — competitive lane (need at least one)
FOREPLAY_API_KEY=
ADYNTEL_API_KEY=

# Autoresearch — monitoring lane (all optional, each adapter gates on presence)
XPOZ_API_KEY=
IC_API_KEY=
NEWSDATA_API_KEY=
APIFY_TOKEN=
POD_ENGINE_API_KEY=
AI_SEARCH_API_KEY=
BLUESKY_APP_PASSWORD=
```

**Copy restart script**:
```
cp freddy/scripts/run_backend.sh gofreddy/scripts/run_backend.sh
chmod +x gofreddy/scripts/run_backend.sh
```

**Seed dev user + API key**:
```sql
INSERT INTO users (id, email, role) VALUES (gen_random_uuid(), 'dev@gofreddy.ai', 'admin')
  ON CONFLICT (email) DO NOTHING
  RETURNING id;

-- Copy returned UUID into the next query
INSERT INTO api_keys (user_id, key_hash, name, created_at)
VALUES (
  '<user-uuid>',
  encode(sha256('<pick-random-string>'::bytea), 'hex'),
  'autoresearch-dev',
  NOW()
);
```

Put `<pick-random-string>` in `.env` as `FREDDY_API_KEY` value.

**Verify**:
```
cd gofreddy && ./scripts/run_backend.sh &
uv run freddy auth login --api-key $FREDDY_API_KEY
uv run freddy evaluate --help
```

**Commit**: `chore(env): autoresearch env vars + backend restart script`

### Phase 8 — End-to-end smoke test

Launch one session per lane:
```
cd gofreddy
./scripts/run_backend.sh &
sleep 3

uv run python autoresearch/archive/v006/run.py --domain competitive figma
uv run python autoresearch/archive/v006/run.py --domain geo semrush
uv run python autoresearch/archive/v006/run.py --domain monitoring Shopify
uv run python autoresearch/archive/v006/run.py --domain storyboard <client>
```

**Expected per lane**:
- Session dir: `autoresearch/archive/v006/sessions/YYYYMMDD-HHMMSS-<lane>-<client>/`
- `results.jsonl` contains `gather`/`analyze`/`synthesize` phase events
- `uv run freddy evaluate variant <lane> <session_dir>` returns JSON with `domain_score > 0`
- New row in `evaluation_results` with `content_hash` = 64 chars

**Common failures + fixes**:
- `/v1/evaluation/*` returns 500 → judge API keys missing (`OPENAI_API_KEY`, `GEMINI_API_KEY`)
- `/v1/monitors/*` returns 500 → Supabase monitors table not seeded; or adapter env vars missing (check backend log for specific adapter)
- `/v1/geo/detect` returns 503 → `geo_service` not initialized; check Phase 3 lifespan wiring
- Variant script fails `from watchdog import ...` → verify `autoresearch/archive/current_runtime/` is a real directory with `scripts/watchdog.py`
- `ImportError: cannot import name 'BillingContext'` → Phase 3 billing-strip missed an import; grep `billing` in edited routers

**Commit**: `chore: autoresearch end-to-end smoke test — <lane>-<client> scored <N>`

## Commit summary

| Phase | Commit |
|---|---|
| 1 | `feat(db): add autoresearch backend tables` |
| 2 | `feat(evaluation): backend service + repository + router + lifespan wiring` |
| 3 | `feat(backend): geo + competitive + monitoring routers with billing stripped` |
| 4 | `feat(domain): port monitoring/geo/competitive service layer from freddy (~4.1K LOC)` |
| 5 | `feat(cli): copy evaluate + 12 tool commands from freddy` |
| 6 | `feat(autoresearch): copy module from freddy (inc. inner harness + archive)` |
| 7 | `chore(env): autoresearch env vars + backend restart script` |
| 8 | `chore: autoresearch end-to-end smoke test passed` |

Each phase commits to `main` directly. Phases 1-3 must run in order (DB → evaluation backend → other routers). Phases 4-7 can reorder if convenient. Phase 8 runs last.

## Rollback per phase

| Phase | Rollback |
|---|---|
| 1 | New migration `DROP TABLE <new tables>` |
| 2 | `git revert <sha>` — removes service/repo/router + lifespan edits |
| 3 | `git revert <sha>` — removes 3 routers + schemas + billing strips + lifespan inits |
| 4 | `git revert <sha>` — restores gofreddy's domain-code versions |
| 5 | `git revert <sha>` — removes 13 CLI commands |
| 6 | `git revert <sha>` + `rm -rf gofreddy/autoresearch/` |
| 7 | `git revert <sha>`; remove API key row + `.env` entries |
| 8 | N/A (no state changed beyond logs) |

Phases are independent within their dependency ordering.

## Estimated effort

| Phase | Effort |
|---|---|
| 1 (Supabase migration) | 30 min |
| 2 (evaluation backend + lifespan block + dep helpers) | 45 min |
| 3 (3 routers + 2 schemas + billing strip + 4 lifespan inits) | 3-4 hours |
| 4 (domain code port — ~4.1K LOC, 11 files after trace-trim) | 45 min |
| 5 (CLI: 13 command files) | 30 min |
| 6 (autoresearch module rsync) | 30 min |
| 7 (env + script) | 15 min |
| 8 (smoke test + debug) | 2-4 hours |

Total: **~1.5-2 solid days** realistic.

Saves roughly half a day vs. the pre-trace estimate (Phase 4 shrank from 2 hours / 7K LOC to 45 min / 4K LOC).

## Open questions — all resolved

1. `src/evaluation/service.py` in gofreddy? **Missing**, `ls` confirmed.
2. `cli/freddy/api.py` is freddy's httpx client? **Yes**, `diff -q` empty.
3. `PoolExhaustedError` in gofreddy? **Yes**, `src/common/exceptions.py:4`.
4. `get_current_user_id` in gofreddy? **Yes**, `src/api/dependencies.py:308`.
5. `current_runtime/` a symlink? **No**, regular directory.
6. Root `freddy/harness/` needed? **No**, separate QA system.
7. Billing layer needed? **No**, stripping from routers.
8. `freddy seo` backend wiring needed? **No**, referenced in program text but never called at runtime.
9. `MonitorWorker` / `WorkspaceBridge` / `AlertEvaluator` needed? **No**, background/cross-workspace features autoresearch doesn't use.
10. Gofreddy has `src/{geo, competitive, monitoring}/`? **Partial** — skeleton present (config, models, exceptions, adapters) but core service-layer files missing. Phase 4 ports 11 files (~4,121 LOC) after transitive-dep trace trimmed out files autoresearch doesn't exercise.
11. `build_judge_ensemble` helper exists? **No** — fictional. Real pattern is inline ~60-LOC judge construction from freddy `dependencies.py:530-601`.
12. `get_monitoring_service` / `get_webhook_delivery` helpers exist in gofreddy? **No** — need to add 2 tiny 3-line functions to gofreddy `dependencies.py`.
13. `get_evaluation_service` exists? **Yes**, defined inside `evaluation.py` router itself (line 24) — comes along with the router copy, no extra work.

## Critical file references

**Sources (freddy)**:
- `freddy/autoresearch/` — ~3,000 LOC Python + ~50 markdown programs + archive/v001-v006 + inner harness
- `freddy/src/evaluation/{service, repository, structural, judges/__init__}.py`
- `freddy/src/api/routers/{evaluation, geo, competitive, monitoring}.py`
- `freddy/src/api/{schemas, schemas_monitoring}.py`
- `freddy/src/api/dependencies.py:729-1083` (monitoring init), `:1356-1398` (geo/competitive init), `:1394` (geo service init), `:1610-1615` (cleanup pattern)
- `freddy/cli/freddy/commands/{evaluate + 12 tool commands}.py`
- `freddy/scripts/setup_test_db.sql` (table extraction source)
- `freddy/scripts/run_backend.sh`
- `freddy/.gitignore:124-132`

**Targets (gofreddy)**:
- `gofreddy/supabase/migrations/20260418000001_autoresearch_tables.sql` — new
- `gofreddy/src/evaluation/{service, repository}.py` — new
- `gofreddy/src/evaluation/{structural, judges/__init__}.py` — overwrite
- `gofreddy/src/api/routers/{evaluation, geo, competitive, monitoring}.py` — new, with billing stripped
- `gofreddy/src/api/{schemas, schemas_monitoring}.py` — new
- `gofreddy/src/api/main.py` — edit (4 router imports + registrations, 4 lifespan init blocks, cleanup handlers)
- `gofreddy/src/{geo, competitive, monitoring}/` — port 11 missing files + overwrite 2 `__init__.py` (geo + competitive)
- `gofreddy/cli/freddy/commands/*.py` — new (13 files)
- `gofreddy/cli/freddy/main.py` — edit (13 registrations)
- `gofreddy/autoresearch/` — new (entire dir via rsync)
- `gofreddy/.env.example` — edit (append autoresearch vars)
- `gofreddy/.gitignore` — edit (append autoresearch block)
- `gofreddy/pyproject.toml` — edit (register autoresearch package)
- `gofreddy/scripts/run_backend.sh` — new

**Papers (design invariants)**:
- Meta-Harness: arxiv 2603.28052
- HyperAgents: arxiv 2603.19461
