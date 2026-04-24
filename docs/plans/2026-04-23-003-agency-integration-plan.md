---
title: Agency integration plan — freddy → gofreddy
date: 2026-04-23
status: partially-superseded
superseded_by:
  - docs/plans/2026-04-24-003-audit-engine-implementation-design.md (replaces §6 Bundle 9 + §7 Bundle 10)
still_valid:
  - §3 Bundle 0 pre-flight (prerequisite for audit engine)
  - §4 Bundle 1 analytical uplift (prerequisite)
  - §5 Bundle 2 client platform lite (prerequisite)
future_scope:
  - §8 Bundle 3 CI triangle
  - §9 Bundle 4 creator ops
  - §10 Bundle 5 content factory
  - §11 Bundle 6 video studio
  - §12 Bundle 7 workers
  - §13 Bundle 8 workspace + skills infra
companion: docs/plans/2026-04-23-002-agency-integration-research-record.md
scope: Port agency capability from the `freddy` repo into `gofreddy` so gofreddy can ship as a real agency product. Ordered bundles, locked decisions, executable next steps.
---

> **NOTICE (2026-04-24):** This plan was over-scoped for the audit-engine-first product decision. Active execution scope is now Bundles 0+1+2 as prerequisites, then `docs/plans/2026-04-24-003-audit-engine-implementation-design.md` for the audit engine + marketing_audit LHR lane. Bundles 3–8 are future scope — not abandoned, not planned now.


# Agency integration plan — freddy → gofreddy

## 0. Executive summary

`gofreddy` is a conscious lean rebuild with architectural wins (Sonnet judges, fixture infra, agent-first autoresearch, Claude+Codex harness, multi-tenant memberships, portal, 11 references library) but a large unbuilt center: the 6-stage audit pipeline designed in `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`, hooked to the 149-lens marketing-audit catalog locked v2 2026-04-23.

This plan ships the audit engine first (differentiated product), bolts on just enough agency ops to make it sellable, then adds capability from `freddy` as paying customers ask. **~6–8 weeks to first revenue-producing audit**, then incremental bundles.

Full research inventory lives in the companion doc at `docs/plans/2026-04-23-002-agency-integration-research-record.md`. This plan is the executable shape.

---

## 1. Locked decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Orchestrator architecture | **Path B: programs-only extension** | gofreddy's programs-as-skills already beats freddy's orchestrator for autoresearch use case. Saves 6–8 weeks. Audit pipeline ships via program, not agent tool call. |
| 2 | Hosting | **Stay on Fly.io** (Fly Cron + Fly Redis) | Already deployed there. Cloud Tasks isn't worth the migration tax. |
| 3 | UI strategy | **CLI-first** | Defer 50+ canvas-section port. Ship web UI only when paying customer demands it. |
| 4 | Billing | **Skip Stripe in phase 1** | Manual invoicing for first 5 audits. Add Stripe when free-scan→paid conversion rate is real data, not a guess. |
| 5 | Orphaned tests (33 files) | **xfail, don't delete** | They are the roadmap. Delete destroys institutional memory of what was planned. |
| 6 | 005 lens registry shape | **Single `configs/audit/lenses.yaml`** | 325 lenses × per-lens files = filesystem noise. One YAML with clear sectioning is greppable and editable. |
| 7 | LHR agent placement | **Autoresearch `marketing_audit` lane** | Autoresearch already solves every LHR primitive (SIGALRM ceilings, critique manifest, resume, evolution judges). Separate runtime duplicates infrastructure for no benefit. |
| 8 | Large repository ports | **Regenerate, don't copy** | `video_projects/repository.py` is 17k LOC mostly SQL. When we reach video studio, write fresh against current schema. |
| 9 | Workers MVP | **MonitorWorker + PublishDispatcher only** | Defer JobWorker, BatchWorker, GenerationWorker until their bundles land. |
| 10 | Build order | **Audit engine before weekly brief** | Weekly brief is commodity; every agency platform has it. Audit engine + LHR is the differentiated product. Ship the moat first. |

Unlocking these requires re-planning; changing one locks any in-flight bundle work.

---

## 2. Bundle sequence + dependency graph

```
Bundle 0 (pre-flight, 3–4 days)
        ↓
    ┌───┴───┐
Bundle 1    Bundle 2         ← parallel, 1 week combined
(analytical) (client-lite)
    └───┬───┘
        ↓
Bundle 9 (audit engine, 5–6 weeks)     ← the product
        ↓
Bundle 10 (LHR marketing_audit lane, 2 weeks)  ← the moat
        ↓
Bundle 7 (workers MVP, 2–3 weeks)      ← unblocks async
        ↓
Bundle 3 (CI triangle, 3–4 weeks)      ← first commodity deliverable
        ↓
Bundle 4 (creator ops, 3 weeks)        ← IC + AQS + deepfake
        ↓
Bundle 5 (content factory, 5 weeks)    ← publishing + OAuth + adapters
        ↓
[deferred indefinitely]
Bundle 6 (video studio)
Bundle 8 (full workspace + orchestrator Path A)
```

Total to last executed bundle (5): ~22–26 weeks sequential, ~14–18 weeks with one backend-heavy and one integration-heavy track in parallel.

First revenue-producing audit: after Bundle 9 (~6–8 weeks from start).

---

## 3. Bundle 0 — Pre-flight

**Status:** not-started
**Depends on:** none
**Duration:** 3–4 days
**Goal:** CI reflects reality. Planning assumptions hold.

### 3.1 Orphaned test xfail pass

33+ test files import modules absent from `gofreddy/src/`. xfail them with a reason pointing to the bundle that will restore them.

Affected test files and the bundle that will un-xfail each:

| Test file | Imports | Bundle that restores |
|---|---|---|
| `tests/test_brands.py` | `src.brands.service` | Bundle 3 (partial) / Bundle 9 |
| `tests/test_brands_exposure.py` | `src.brands.service` | Bundle 3 (partial) / Bundle 9 |
| `tests/test_clients_service.py` | `src.clients.service` | Bundle 2 |
| `tests/test_manage_client_tool.py` | `src.orchestrator`, `src.clients` | Bundle 2 (client only), Bundle 8 (tool) |
| `tests/test_demographics.py` | `src.demographics`, `src.schemas` | Bundle 4 |
| `tests/test_job_worker.py` | `src.jobs.config`, worker | Bundle 7 (deferred beyond MVP) |
| `tests/test_job_service.py` | `src.jobs.service` | Bundle 7 |
| `tests/test_pr067_scheduled_monitoring.py` | `src.jobs`, `src.monitoring.worker` | Bundle 7 |
| `tests/test_pr025_durability.py` | `src.jobs`, `src.stories` | Bundles 6 + 7 |
| `tests/test_newsletter_service.py` | `src.newsletter.service` | Bundle 3 |
| `tests/orchestrator/test_*.py` (14 files) | `src.orchestrator` | Bundle 8 (skip since Path B) — mark xfail permanent |
| `tests/test_schemas.py` and 12 others | `src.schemas` top-level | Bundle 1 (schemas move) |
| `tests/test_instagram_stories.py` | `src.stories` | Bundle 6 |
| `tests/test_pr057_ssrf_path_traversal.py` | `src.stories`, `src.common.url_validation` | Bundle 6 (partial; url_validation already present) |
| `tests/test_pr052_resume_cache.py` | `src.prompts` | Bundle 1 |
| `tests/test_fraud_ic_enrichment.py` | `src.api.routers.fraud` | Bundle 4 |
| `tests/test_pr082_ic_search.py` | `src.search.service` | Bundle 4 |

Use this decorator pattern at file top:

```python
pytestmark = pytest.mark.xfail(
    reason="Pending Bundle <N>: see docs/plans/2026-04-23-003-agency-integration-plan.md",
    strict=False,
)
```

Adding `strict=False` lets a file pass if the module returns before deletion — catches accidental early restores.

### 3.2 Root `tests/conftest.py`

Create at `tests/conftest.py` with the minimum fixture set the existing (non-orphaned) tests need:

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_adyntel():
    ...

@pytest.fixture
def mock_ic_backend():
    ...

@pytest.fixture
def mock_xpoz():
    ...

@pytest.fixture
def mock_gemini():
    ...

@pytest.fixture
def mock_r2():
    ...

# Database pool fixture — use testcontainers or docker-compose
@pytest.fixture(scope="session")
async def db_pool():
    ...
```

Port each fixture from `/Users/jryszardnoszczyk/Documents/GitHub/freddy/tests/conftest.py` (539 LOC) — prune to the 6 above for phase 1.

### 3.3 Dependencies

Add to `pyproject.toml` `[project.dependencies]`:

```toml
"resend>=2.0,<3.0",       # Bundle 3 digest delivery
"weasyprint>=62.0",       # Bundle 9 PDF export
"mistune>=3.0.0",         # Bundle 9 markdown rendering
"nh3>=0.2.14",            # Bundle 9 HTML sanitization
"jinja2>=3.1.0",          # Bundle 9 template rendering (likely already transitive, pin explicit)
```

Not yet: `stripe`, `google-cloud-tasks`, `redis`, `dspy`, `supabase`, `svix`. Add when bundles that need them land.

### 3.4 pytest marker

Restore `db` marker in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "db: marks tests requiring a database (deselect with '-m \"not db\"')",
    # ... existing markers
]
```

### 3.5 Done signal

- `pytest --collect-only` succeeds with zero import errors.
- `pytest -m "not db"` runs and returns a count (pass or xfail).
- Existing passing tests still pass.
- `pyproject.toml` diff committed.

---

## 4. Bundle 1 — Analytical uplift

**Status:** not-started
**Depends on:** Bundle 0
**Duration:** 1 week (parallel with Bundle 2)
**Goal:** Every LLM call in gofreddy inherits freddy's calibrated prompts and taxonomies. Pure copy-paste work.

### 4.1 Files to port

| freddy path | gofreddy destination | LOC | Notes |
|---|---|---|---|
| `src/prompts.py` CREATIVE_PATTERN_PROMPT constant | `src/prompts.py` | ~1,200 | Scene-beat-map format `(N) BEAT_TYPE T1-T2s: shot_type camera_move — description` |
| `src/prompts.py` DEMOGRAPHICS_INFERENCE_PROMPT | `src/prompts.py` | ~1,000 | 2025–2026 slang taxonomy, gender-skew baselines |
| `src/prompts.py` BRAND_DETECTION_PROMPT + BRAND_DETECTION_SYSTEM | `src/prompts.py` | ~450 | Per-brand sentiment, `is_competitor` flag |
| `src/prompts.py` QUERY_PARSING_PROMPT | `src/prompts.py` | ~200 | NL → platform-aware filters |
| `src/prompts.py` MODERATION_PROMPT | verify parity, port if missing | 40–164 | 75-class GARM |
| `src/prompts.py` BRAND_SAFETY_PROMPT | verify parity | 261–312 | Content + moderation + sponsored combined |
| `src/prompts.py` SPONSORED_CONTENT_PROMPT | verify parity | 168–216 | FTC signals |
| `src/schemas.py` ModerationClass enum | verify parity (policies agent confirms 75 classes present) | ~400 | 11 GARM categories |
| `src/schemas.py` AudienceDemographics model | port if missing | ~30 | interests, age, gender, geography, income |
| `src/schemas.py` BrandMention + BrandExposureSummary | port if missing | ~80 | sentiment + context + competitor flag |
| `src/monitoring/intelligence/intent.py` | `src/monitoring/intelligence/intent.py` | 161 | 5-class Gemini Flash-Lite |
| `src/monitoring/intelligence/sentiment_classifier.py` | same | 173 | Lexicon + Gemini dual-pass |
| `src/monitoring/intelligence/trends_correlation.py` | same | 120 | Pearson r |
| `src/monitoring/intelligence/sentiment.py` | same | 131 | Time-series, 30min TTL |
| `src/monitoring/intelligence/metric_computations.py` | same | 73 | Aggregate utilities |
| `src/analysis/lane_selector.py` | `src/analysis/lane_selector.py` | ~100 | L1/L2 routing, ~80% cost cut |
| `src/analysis/compliance.py` | verify parity | 106 | A–F grading (40/35/25 weights) |
| `src/competitive/schemas.py` AdCreativeCore dataclass | verify parity | ~150 | 18-field unified schema |

### 4.2 Explicitly skipped

- `src/evaluation/rubrics.py` (1,001 LOC) — already at parity (verified by prior audit).
- `fuzzy_match` evidence gate — intentionally replaced by gofreddy's Sonnet paraphrase judge (R-#32).

### 4.3 Adaptations required

- Fix any `from ..schemas` imports that differ in gofreddy package layout.
- Intent + sentiment classifiers use `src/common/gemini_models.py` — verify model name matches gofreddy's version.
- Cost-recording calls use `cost_recorder` singleton — already present in gofreddy.

### 4.4 Tests

- Unxfail: `tests/test_schemas.py`, `tests/test_pr052_resume_cache.py` (after schema + prompt port).
- Add: smoke test importing each prompt constant and classifier module.

### 4.5 Done signal

- Every ported file imports cleanly.
- Smoke test passes.
- No regressions in existing pass-set.
- `pytest tests/test_schemas.py` passes.

---

## 5. Bundle 2 — Client platform (lite)

**Status:** not-started
**Depends on:** Bundle 0
**Duration:** 1 week (parallel with Bundle 1)
**Goal:** Real client entities with competitor tracking, brand context, auto-brief flag. Minimum agency data model.

**Explicitly deferred:** per-client platform_connections, OAuth flows, portal branding, PDF export, RBAC enforcement beyond current portal. Those land with the bundles that need them (Bundle 5 for connections+OAuth, Bundle 3 for branded digest delivery).

### 5.1 Database migration

New file: `supabase/migrations/20260423000001_client_platform_lite.sql`

```sql
-- Extend clients with competitor tracking + brand context
ALTER TABLE clients
  ADD COLUMN competitor_brands TEXT[] DEFAULT '{}',
  ADD COLUMN competitor_domains TEXT[] DEFAULT '{}',
  ADD COLUMN brand_context TEXT,
  ADD COLUMN auto_brief BOOLEAN DEFAULT FALSE,
  ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW(),
  ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX idx_clients_auto_brief ON clients(auto_brief) WHERE auto_brief = TRUE;
```

### 5.2 Files to create

#### `src/clients/__init__.py`

Exports: `ClientService`, `ClientRepository`, `Client`, `ClientCreate`, `ClientUpdate`.

#### `src/clients/models.py` (~80 LOC)

Port from freddy `src/clients/models.py` (51 LOC) and extend:

```python
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from typing import Optional

@dataclass
class Client:
    id: UUID
    slug: str
    name: str
    competitor_brands: list[str]
    competitor_domains: list[str]
    brand_context: Optional[str]
    auto_brief: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class ClientCreate:
    slug: str
    name: str
    competitor_brands: list[str] = None
    competitor_domains: list[str] = None
    brand_context: Optional[str] = None
    auto_brief: bool = False

@dataclass
class ClientUpdate:
    name: Optional[str] = None
    competitor_brands: Optional[list[str]] = None
    competitor_domains: Optional[list[str]] = None
    brand_context: Optional[str] = None
    auto_brief: Optional[bool] = None
```

#### `src/clients/repository.py` (~200 LOC)

Port from freddy `src/clients/repository.py` (150+ LOC) + `propagate_to_monitors` transactional update:

Key methods:
- `async create(conn, data: ClientCreate, user_id: UUID) -> Client` — create client + add user as admin membership
- `async get(conn, client_id: UUID, user_id: UUID) -> Optional[Client]` — RBAC-scoped
- `async list_for_user(conn, user_id: UUID) -> list[Client]` — via memberships
- `async list_auto_brief(conn) -> list[Client]` — for scheduler (returns all across users)
- `async update(conn, client_id: UUID, user_id: UUID, data: ClientUpdate) -> Client` — RBAC + propagate_to_monitors on competitor change
- `async delete(conn, client_id: UUID, user_id: UUID) -> None` — admin-only
- `async propagate_to_monitors(conn, client_id: UUID, competitor_brands: list[str]) -> None` — transactional update of existing monitors

#### `src/clients/service.py` (~120 LOC)

Port from freddy `src/clients/service.py` (82 LOC):

```python
class ClientService:
    def __init__(self, repo: ClientRepository):
        self._repo = repo

    async def create(self, conn, data: ClientCreate, user_id: UUID) -> Client:
        # Enforce: slug unique within memberships
        ...

    async def get(self, conn, client_id: UUID, user_id: UUID) -> Client:
        client = await self._repo.get(conn, client_id, user_id)
        if not client:
            raise ClientNotFoundError(client_id)
        return client

    async def list_for_user(self, conn, user_id: UUID) -> list[Client]:
        return await self._repo.list_for_user(conn, user_id)

    async def list_auto_brief_clients(self, conn) -> list[Client]:
        return await self._repo.list_auto_brief(conn)

    async def update(self, conn, client_id: UUID, user_id: UUID, data: ClientUpdate) -> Client:
        updated = await self._repo.update(conn, client_id, user_id, data)
        if data.competitor_brands is not None:
            await self._repo.propagate_to_monitors(conn, client_id, data.competitor_brands)
        return updated

    async def delete(self, conn, client_id: UUID, user_id: UUID) -> None:
        await self._repo.delete(conn, client_id, user_id)
```

#### `src/clients/exceptions.py` (~20 LOC)

```python
class ClientNotFoundError(Exception):
    ...

class ClientAccessDeniedError(Exception):
    ...

class DuplicateSlugError(Exception):
    ...
```

### 5.3 API endpoints

Port `src/api/routers/clients.py` (145 LOC in freddy):

| Method | Path | Purpose |
|---|---|---|
| `POST /v1/clients` | Create | Returns 201 with client |
| `GET /v1/clients` | List user's clients | Via memberships |
| `GET /v1/clients/{id}` | Fetch | RBAC-scoped |
| `PATCH /v1/clients/{id}` | Update | RBAC-scoped; propagates to monitors |
| `DELETE /v1/clients/{id}` | Delete | Admin-only |

Wire router in `src/api/main.py` alongside existing routers.

### 5.4 CLI commands

Already present: `freddy client` group in gofreddy.

Add subcommands if missing:

```bash
freddy client create --slug acme --name "Acme Corp" --competitor-brands "Rival Inc,BigCo"
freddy client list
freddy client show <slug>
freddy client update <slug> --auto-brief
freddy client delete <slug>
```

### 5.5 Tests

- Unxfail: `tests/test_clients_service.py`
- Add: `tests/test_api/test_clients_router.py` — CRUD endpoints with RBAC matrix
- Verify: `propagate_to_monitors` transactional correctness with existing monitor records

### 5.6 Done signal

- Migration applied cleanly against dev Supabase.
- Unxfailed tests pass.
- `freddy client create` / `list` / `show` / `update` / `delete` all work end-to-end.
- Can query `list_auto_brief_clients()` and it returns flagged clients.

---

## 6. Bundle 9 — Audit engine (the product)

**Status:** not-started
**Depends on:** Bundles 0, 1, 2
**Duration:** 5–6 weeks
**Goal:** Ship the 6-stage prospect audit pipeline from plan 2026-04-20-002, grounded in the 149-lens catalog locked v2 2026-04-23.

This bundle is why gofreddy exists. Everything else is commodity.

**Explicitly deferred from the 002 plan:**
- Stripe Checkout payment gate — manual invoice for first 5 audits
- Fireflies webhook handlers — CLI-intake only for phase 1
- Cloudflare Worker intake form — CLI intake sufficient
- All 11 attachment subcommands beyond the core 3 (attach-gsc, attach-budget, attach-winloss) — add when first paying prospect asks

**Explicitly included:**
- Free AI Visibility Scan (lead magnet) — this is also gofreddy's "does it work" sanity check
- Stages 1–6 (discovery, synthesis, findings, proposal, deliverable, publish)
- HTML + PDF rendering (WeasyPrint + Jinja2)
- Cost log + state persistence
- Lens registry codification

### 6.1 Lens registry

Create `configs/audit/lenses.yaml` — single YAML codifying the 005 catalog (locked v2 2026-04-23 per memory):

```yaml
# configs/audit/lenses.yaml
# Derived from docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md (locked v2 2026-04-23)
# Ranking from docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md

version: "2.0"
locked_at: "2026-04-23"

phase_0_meta_frames:  # 9 entries — run before Stage 1a
  - id: "P0-01"
    name: "<lens name from 005>"
    detection_signals: []
    stage: 0

always_on_lenses:  # 149 entries
  - id: "A1"
    name: "<lens name>"
    rank: 1
    tier: 1   # 1=floor, 2=foundational, 3=high-value, 4=cutoff
    providers: ["dataforseo", "cloro"]
    phase: 1  # stage-1a pre-pass | stage-1 discovery | stage-2 synthesis
    cost_est_usd: 0.50

vertical_bundles:  # 25 entries, dispatched by vertical detection
  b2b_saas:
    name: "B2B SaaS vertical bundle"
    lenses: ["V-B2B-01", "V-B2B-02", ...]
  ecommerce:
    ...

geo_bundles:  # 10 entries
  us:
    detection_signals: ["ccTLD: .com", "language: en-us"]
    lenses: [...]

segment_bundles:  # 5 entries
  enterprise:
    detection_signals: ["case_study_count >= 5", "pricing_hidden"]
    lenses: [...]
```

Total YAML size: ~1,500 lines for 149 + 25 + 10 + 5 + 9 entries with metadata.

**Task:** extract actual lens names, ranks, bundles from `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` and `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md`. This is mechanical transcription — can be done in parallel with other subsections of Bundle 9.

### 6.2 Module structure

New directory: `src/audit/`

```
src/audit/
├── __init__.py
├── run.py              # 6 stage-runner functions
├── state.py            # state.json + cost_log.jsonl
├── lenses.py           # loads lenses.yaml, dispatches per applicability
├── primitives.py       # tech fingerprinting, embedding clustering
├── rendered_fetcher.py # Playwright browser context
├── report.py           # HTML + PDF rendering
├── stages/
│   ├── __init__.py
│   ├── stage_0_phase0.py       # 9 meta-frames pre-pass
│   ├── stage_1a_prepass.py     # applicability detection
│   ├── stage_1_discovery.py    # gather data per lens
│   ├── stage_2_synthesis.py    # SubSignal → ParentFinding aggregation
│   ├── stage_3_findings.py     # findings.md generation
│   ├── stage_4_proposal.py     # recommendation synthesis
│   ├── stage_5_deliverable.py  # client-branded HTML/PDF
│   └── stage_6_publish.py      # upload + notify
├── tools/              # cache-backed provider wrappers
│   ├── __init__.py
│   ├── dataforseo_tool.py
│   ├── cloro_tool.py
│   ├── foreplay_tool.py
│   ├── adyntel_tool.py
│   ├── gsc_tool.py
│   ├── pagespeed_tool.py
│   └── monitoring_tool.py
└── data/
    ├── budget_benchmarks.yaml
    ├── crm_velocity_benchmarks.yaml
    └── rubric_thresholds.yaml
```

### 6.3 Stage contracts

Each stage implements a common interface:

```python
# src/audit/stages/_base.py
from abc import ABC, abstractmethod

class StageResult(TypedDict):
    stage: int
    outputs: dict  # stage-specific
    cost_usd: float
    duration_s: float
    error: Optional[str]

class Stage(ABC):
    @abstractmethod
    async def run(self, state: AuditState) -> StageResult: ...
```

State machine:

```
NEW → STAGE_0_DONE → STAGE_1A_DONE → STAGE_1_DONE 
    → STAGE_2_DONE → STAGE_3_DONE → STAGE_4_DONE 
    → STAGE_5_DONE → STAGE_6_DONE → COMPLETE
           ↓
         FAILED (at any stage, with error field)
         PAUSED (awaiting manual input or payment)
```

State persists to `state.json` per audit in `artifacts/audits/{audit_id}/state.json`. Cost log appends to `artifacts/audits/{audit_id}/cost_log.jsonl`.

### 6.4 Cost cap

$100 ceiling per memory (locked lens catalog state). Enforce in `run.py`:

```python
COST_CEILING_USD = 100.00

async def run_audit(audit_id: str) -> AuditResult:
    state = load_state(audit_id)
    for stage in [stage_0, stage_1a, stage_1, stage_2, stage_3, stage_4, stage_5, stage_6]:
        if state.total_cost_usd >= COST_CEILING_USD:
            state.status = "paused_cost_ceiling"
            save_state(state)
            raise CostCeilingReached(state.total_cost_usd)
        result = await stage.run(state)
        state.total_cost_usd += result.cost_usd
        state.stage_results.append(result)
        save_state(state)
```

Per-stage estimates (provisional, tune after first 5 audits):

| Stage | Est. cost | Notes |
|---|---|---|
| 0 Phase-0 meta-frames | $2 | 9 lenses, deterministic detection |
| 1a Pre-pass | $3 | Applicability detection for bundles |
| 1 Discovery | $25 | 149 always-on lenses + dispatched bundles |
| 2 Synthesis | $15 | Sonnet aggregation SubSignal → ParentFinding |
| 3 Findings | $8 | Opus for findings.md writing |
| 4 Proposal | $5 | Recommendation synthesis |
| 5 Deliverable | $2 | HTML + PDF render |
| 6 Publish | $0 | Upload only |
| **Total** | **$60** | Leaves $40 headroom under ceiling |

### 6.5 CLI

Create `cli/freddy/commands/audit.py`:

```bash
# Run a full audit for a prospect
freddy audit run --prospect "acme.com" --client-slug "agency-acme"

# Free AI Visibility Scan (lead magnet tier)
freddy audit scan --domain "acme.com"

# Inspect state
freddy audit status <audit_id>
freddy audit costs <audit_id>

# Manual attachments (subset for phase 1)
freddy audit attach-gsc <audit_id> --service-account ./creds.json
freddy audit attach-budget <audit_id> --budget-usd 50000
freddy audit attach-winloss <audit_id> --file ./interviews.md

# Resume a paused audit
freddy audit resume <audit_id>

# Publish final deliverable
freddy audit publish <audit_id>

# Manual invoice email (phase 1 billing)
freddy audit invoice <audit_id> --email prospect@example.com
```

### 6.6 Report rendering

HTML template: `src/audit/templates/deliverable.html.j2` — Jinja2 template with client branding placeholders (logo, colors). WeasyPrint for PDF.

Use existing `src/shared/reporting/report_base.py` (already in gofreddy per autoresearch cluster research).

Security: nh3 HTML sanitization, `_safe_url_fetcher` blocks external URLs except `data:` URIs.

### 6.7 Provider tools (cache-backed)

Wrap existing `src/seo`, `src/competitive`, `src/geo`, `src/monitoring` provider clients with a cache layer per plan 002. Example:

```python
# src/audit/tools/adyntel_tool.py
from src.competitive.providers.adyntel import AdyntelProvider
from src.audit.state import AuditState, record_tool_call

async def search_ads_for_audit(state: AuditState, domain: str) -> list[dict]:
    cache_key = f"adyntel:{domain}"
    if cached := state.tool_cache.get(cache_key):
        return cached
    provider = AdyntelProvider(...)
    ads = await provider.search_google_ads(domain=domain, max_pages=3)
    state.tool_cache[cache_key] = ads
    await record_tool_call(state, "adyntel", cost_usd=len(ads) * 0.0088)
    return ads
```

Seven tools to wrap: dataforseo, cloro, foreplay, adyntel, gsc, pagespeed, monitoring (aggregate).

### 6.8 Free AI Visibility Scan

Subset of stages 0+1 only, narrow to GEO visibility + brand presence. Cost ≤ $2 per plan 002. Run via:

```bash
freddy audit scan --domain example.com
```

Returns public URL to summary HTML (no PDF). Lead capture via email in scan output.

### 6.9 Tests

- `tests/test_audit/test_lenses_yaml.py` — valid YAML, all 149+25+10+5+9 entries present, no duplicate IDs
- `tests/test_audit/test_stage_contracts.py` — each stage implements Stage ABC
- `tests/test_audit/test_cost_cap.py` — ceiling enforcement
- `tests/test_audit/test_state_machine.py` — valid transitions, resume correctness
- `tests/test_audit/test_free_scan.py` — end-to-end scan on fixture domain
- Smoke test: one full audit run on a fixture prospect (mocked providers)

### 6.10 Done signal

- `freddy audit scan --domain <fixture>` produces a real HTML summary under $2.
- `freddy audit run --prospect <fixture> --client-slug <fixture>` completes all 6 stages under $100.
- PDF renders correctly with client branding.
- Cost log captures every provider call.
- State persists across restart (kill process, `freddy audit resume`, stages continue from where they stopped).

### 6.11 Open questions

- Where do audit artifacts live? Local filesystem for phase 1 (`artifacts/audits/{id}/`), R2 for phase 2 when remote artifact storage needed for multi-machine workers.
- Should Phase-0 meta-frames cache across audits? Probably yes — same prospect domain shouldn't re-detect vertical on second audit. Defer cache-sharing decision until Bundle 10 shapes the audit lane.

---

## 7. Bundle 10 — LHR marketing_audit autoresearch lane

**Status:** not-started
**Depends on:** Bundle 9
**Duration:** 2 weeks
**Goal:** Make audits self-improving. Every prospect becomes training data for the next audit.

This is the moat. The audit engine from Bundle 9 runs end-to-end; this bundle wraps it in autoresearch so the pipeline mutates over generations.

### 7.1 New program files

#### `autoresearch/archive/current_runtime/programs/marketing_audit-session.md`

Follow the pattern of existing domain programs (competitive-session.md, geo-session.md):

```markdown
# Marketing audit program

You are running a 6-stage marketing audit against a prospect domain. Your goal is
to produce a deliverable that a paying agency client would accept as justifying
$X/month in strategy fees.

## Operational reality

- Budget: $100/audit ceiling (`src/audit/run.py:COST_CEILING_USD`)
- Duration: 30–60min per prospect on happy path
- Deliverable: HTML + PDF report in client-branded template
- Source data: prospect domain + attached enrichments (GSC / budget / winloss)

## Quality criteria

1. Every finding cites a specific observation (URL, screenshot, metric)
2. Recommendations are ranked by cost-of-delay × effort-ratio
3. Competitive honesty: prospect's losses to competitors are named
4. No generic boilerplate — if a lens produces generic output, the lens failed
5. Total cost tracked per stage, visible in state.json

## Workspace layout

audits/{prospect_id}/
├── state.json
├── cost_log.jsonl
├── findings.md
├── deliverable.html
├── deliverable.pdf
└── artifacts/
    ├── stage_1_discovery/
    ├── stage_2_synthesis/
    └── ...

## Iteration patterns

- Mutate: tune stage-1a applicability thresholds if bundles mis-dispatch
- Mutate: adjust lens ordering if cost ceiling hits before stage 3
- Mutate: rewrite synthesis prompt if ParentFindings are generic
- Don't mutate: lens definitions themselves (locked v2 2026-04-23)
```

#### `autoresearch/archive/current_runtime/programs/marketing_audit-evaluation-scope.yaml`

```yaml
domain: marketing_audit

outputs:
  - "audits/{prospect_id}/findings.md"
  - "audits/{prospect_id}/deliverable.html"
  - "audits/{prospect_id}/deliverable.pdf"
  - "audits/{prospect_id}/state.json"

source_data:
  - "prospects/{prospect_id}/intake.json"
  - "prospects/{prospect_id}/crawl/*"

transient:
  - "audits/{prospect_id}/artifacts/**/*"
  - "audits/{prospect_id}/cost_log.jsonl"
  - "logs/**/*"

notes: |
  Variants mutate stage prompts + stage-1a thresholds + lens dispatch logic.
  Lens definitions in configs/audit/lenses.yaml are OUT OF SCOPE for mutation
  (locked v2 2026-04-23). Scorer evaluates deliverable quality against 8-point
  MA-1..MA-8 rubric (to be defined).
```

### 7.2 Evaluation rubric

Extend `src/evaluation/rubrics.py` with MA-1..MA-8 (marketing audit):

| Criterion | Type | Focus |
|---|---|---|
| MA-1 Observational grounding | Gradient | Every finding ties to specific cited observation |
| MA-2 Recommendation actionability | Checklist | Named action + target + effort sizing + timeframe |
| MA-3 Competitive honesty | Gradient | Prospect's losses named, not softened |
| MA-4 Cost discipline | Checklist | Hit under ceiling? Per-stage within estimate? |
| MA-5 Bundle applicability | Gradient | Dispatched bundles match detection signals |
| MA-6 Deliverable polish | Gradient | HTML/PDF render cleanly with client branding |
| MA-7 Prioritization | Gradient | Top 3 actions unmistakably separated |
| MA-8 Data gap recalibration | Checklist | Failed enrichments named, confidence lowered accordingly |

Use existing Sonnet paraphrase judge (R-#32) + calibration judge (R-#33) for scoring.

### 7.3 Fixture integration

New fixture file: `autoresearch/eval_suites/marketing-audit-v1.json`

```json
{
  "suite_id": "marketing-audit",
  "version": "1.0",
  "domains": {
    "marketing_audit": {
      "fixtures": [
        {
          "fixture_id": "demo_saas_prospect",
          "client": "demo-agency",
          "context": {
            "prospect_domain": "example-saas.com",
            "vertical": "b2b_saas",
            "geo": "us",
            "segment": "enterprise"
          },
          "version": "1.0",
          "max_iter": 3,
          "timeout": 3600,
          "env": {}
        }
        // ... 3–5 more fixtures covering different verticals + geos
      ]
    }
  }
}
```

### 7.4 Lane integration

Update `autoresearch/lane_runtime.py` if marketing_audit needs lane-specific behavior — likely minimal, the existing 4 domains (geo, competitive, monitoring, storyboard) all flow through the same materialized runtime pattern.

### 7.5 Done signal

- `evolve.py --lane marketing_audit --session-dir ./sessions/ma-gen-001 --max-iterations 3` runs end-to-end.
- Variant scorer returns scores for MA-1..MA-8 per variant.
- At least one variant promotes to lane head after generation.
- events.jsonl captures generation + promotion mutations.
- `autoresearch/archive/v001/programs/marketing_audit-session.md` is reachable from current_runtime.

### 7.6 Open questions

- Should marketing_audit share the same search-suite as geo, or have its own? Leaning: own (audit quality diverges from SEO quality).
- Holdout suite for phase 1: collect 5 hand-curated audit artifacts as gold standard, use as `holdout-marketing-audit-v1.json`. Defer until we have 5 real audits.

---

## 8. Bundle 7 — Workers MVP

**Status:** not-started
**Depends on:** Bundle 2 (clients for auto-brief trigger)
**Duration:** 2–3 weeks
**Goal:** Two workers that unblock weekly-brief delivery and scheduled publishing. Defer all others.

**Included:**
- MonitorWorker — runs mention fetchers on schedule, computes analytics, triggers alerts
- PublishDispatcher — claims scheduled publish_queue items, fans out to adapters

**Explicitly deferred:**
- JobWorker (video analysis async) — needed only for Bundle 6
- BatchWorker (workspace batch analysis) — needed only for Bundle 8
- GenerationWorker (video render) — needed only for Bundle 6
- CommentSyncWorker — phase 2 when comment inbox ships
- OAuth token refresh cron — phase 2 when Bundle 5 publishing OAuth lands

### 8.1 Infrastructure decision: Fly Cron + Fly Redis

Not Cloud Tasks. Locked decision #2.

`fly.toml` additions:

```toml
[processes]
web = "uvicorn src.api.main:app --host 0.0.0.0 --port 8080"
monitor_worker = "python -m src.monitoring.worker"
publish_dispatcher = "python -m src.publishing.dispatcher"

[[services]]
internal_port = 8080
protocol = "tcp"
# ... existing web service config

# Schedulers via Fly Cron (configured via fly.io dashboard or fly-cron.toml)
```

Fly Redis attached via `fly redis create`:

```
REDIS_URL=redis://...  # injected by Fly
```

Used for:
- Distributed locks on `claim_scheduled_items()` and `claim_monitor_runs()`
- Cache coherence across instances (replacing in-memory TTLCache for hot paths)

### 8.2 MonitorWorker

New file: `src/monitoring/worker.py` (~300 LOC)

Port patterns from freddy `src/monitoring/worker.py` (302 LOC). Structure:

```python
class MonitorWorker:
    def __init__(self, pool, adapters, settings):
        self._pool = pool
        self._adapters = adapters
        self._settings = settings
        self._dispatch_deadline = settings.dispatch_deadline_seconds  # 900s

    async def run(self):
        """Main loop: poll for due monitors, dispatch runs."""
        while True:
            async with self._pool.acquire() as conn:
                due_monitors = await self._claim_due_monitors(conn)
            for monitor in due_monitors:
                try:
                    await asyncio.wait_for(
                        self._process_monitor(monitor),
                        timeout=self._dispatch_deadline,
                    )
                except TimeoutError:
                    logger.error(f"Monitor {monitor.id} timed out at {self._dispatch_deadline}s")
            await asyncio.sleep(self._settings.poll_interval_seconds)

    async def _claim_due_monitors(self, conn) -> list[Monitor]:
        # FOR UPDATE SKIP LOCKED + cooldown check
        ...

    async def _process_monitor(self, monitor: Monitor):
        # Parallel fetch from all adapters
        tasks = [
            adapter.fetch_mentions(monitor.query, since=monitor.last_ran_at)
            for adapter in self._adapters.get(monitor)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Ingest
        await self._ingest_mentions(monitor, results)
        # Analytics pipeline
        await self._run_analytics(monitor)
        # Alert evaluation
        await self._evaluate_alerts(monitor)
```

Dependencies:
- `src/monitoring/adapters/*` (already in gofreddy)
- `src/monitoring/intelligence/*` (ported in Bundle 1)
- `src/monitoring/alerts/*` (port in this bundle — 261 LOC from freddy)
- `src/monitoring/dispatcher.py` (port in this bundle — 86 LOC)

### 8.3 Alert system

Port from freddy:
- `src/monitoring/alerts/models.py` (50 LOC) — AlertRule, AlertEvent
- `src/monitoring/alerts/evaluator.py` (125 LOC) — spike detection, baseline calculation
- `src/monitoring/alerts/delivery.py` (136 LOC) — webhook dispatch, HMAC signing, retry 3× on 5xx

DB migration for alert tables: already present in gofreddy via `20260418000002_autoresearch_tables.sql`.

### 8.4 PublishDispatcher

New file: `src/publishing/dispatcher.py` (~100 LOC)

Port from freddy. Structure:

```python
class PublishDispatcher:
    def __init__(self, pool, adapters, settings):
        self._pool = pool
        self._adapters = adapters  # {platform: adapter}
        self._batch_size = settings.dispatch_batch_size  # 10
        self._deadline = settings.dispatch_deadline_seconds  # 200

    async def run(self):
        while True:
            async with self._pool.acquire() as conn:
                items = await self._claim_scheduled_items(conn, limit=self._batch_size)
            if not items:
                await asyncio.sleep(self._settings.poll_interval_seconds)
                continue
            tasks = [self._publish_item(item) for item in items]
            await asyncio.gather(*tasks, return_exceptions=True)
            async with self._pool.acquire() as conn:
                await self._reap_stale_publishing_items(conn)

    async def _claim_scheduled_items(self, conn, limit: int) -> list[QueueItem]:
        # FOR UPDATE SKIP LOCKED, scheduled_at <= NOW(), retry_count <= 2
        ...

    async def _publish_item(self, item: QueueItem):
        adapter = self._adapters.get(item.platform)
        try:
            result = await asyncio.wait_for(
                adapter.publish(item),
                timeout=self._deadline,
            )
            await self._mark_published(item, result)
        except Exception as e:
            await self._mark_failed(item, e)
            # Retry with [5min, 10min, 20min] backoff
            next_at = datetime.utcnow() + RETRY_DELAYS[item.retry_count]
            await self._reschedule(item, next_at)
```

**Caveat:** this worker is skeleton-only until Bundle 5 provides the `publish_queue` table + adapters. For phase 1, deploy the worker but set `enabled: False` in config. Wires up infra without blocking.

### 8.5 Auto-brief trigger (hooked to MonitorWorker)

After MonitorWorker processes each monitor, check if the monitor's `client_id` has `auto_brief=True` and a weekly digest is due:

```python
async def _maybe_trigger_weekly_brief(self, conn, monitor: Monitor):
    if not monitor.client_id:
        return
    client = await self._client_repo.get_raw(conn, monitor.client_id)
    if not client or not client.auto_brief:
        return
    last_digest = await self._digest_repo.get_latest_for_monitor(conn, monitor.id)
    if last_digest and (datetime.utcnow() - last_digest.generated_at).days < 7:
        return
    # Enqueue digest generation (via Bundle 3 service)
    ...
```

This hooks Bundle 3's weekly-brief generation into the monitor run loop. Without it, we'd need a separate weekly cron.

### 8.6 Tests

- Unxfail: `tests/test_pr067_scheduled_monitoring.py`, `tests/test_pr068_alerting.py` (rename if needed)
- Add: `tests/test_monitor_worker.py` — claim + dispatch + alert flow
- Add: `tests/test_publish_dispatcher.py` — claim + adapter call + retry
- Add: `tests/test_fly_cron_integration.py` — verify workers can run as separate Fly processes

### 8.7 Done signal

- `fly.toml` has 3 processes: web, monitor_worker, publish_dispatcher.
- Redis URL resolves on all processes.
- Deploy to staging. MonitorWorker claims a test monitor, fetches mentions from at least 3 adapters, ingests to DB, emits sentiment+intent classifications.
- PublishDispatcher deployed with `enabled: False` — idle process, doesn't crash.

---

## 9. Bundle 3 — CI triangle (weekly brief + VOC + newsletter)

**Status:** not-started
**Depends on:** Bundles 2, 7
**Duration:** 3–4 weeks
**Goal:** First commodity agency deliverable. Weekly client brief shipped via email.

### 9.1 Monitoring intelligence ports (beyond Bundle 1)

Port from freddy:

| File | LOC | Purpose |
|---|---|---|
| `src/monitoring/analytics_service.py` | 314 | Topic clustering, performance patterns, engagement prediction orchestration |
| `src/monitoring/repository_analytics.py` | 280 | Topic cluster persistence |
| `src/monitoring/workspace_bridge.py` | 80 | `save_mentions_to_workspace` (500 max; stub if workspace not ported) |
| `src/monitoring/intelligence/share_of_voice.py` | 112 | SQL-based competitor ranking |
| `src/monitoring/intelligence/commodity_baseline.py` | 356 | Weekly markdown baseline report |
| `src/monitoring/intelligence/post_ingestion.py` | 335 | **Agency differentiator** — auto-refine monitor via Gemini |
| `src/monitoring/intelligence/performance_patterns.py` | 251 | Anomaly detection |
| `src/monitoring/intelligence/engagement_predictor.py` | 210 | Reach impact scoring |

### 9.2 Competitive brief generator

Port `src/competitive/brief.py` (~400 LOC) and `src/competitive/markdown.py` (146 LOC) from freddy.

Six sections in parallel (Gemini Flash, 160s deadline):
1. Share of Voice (via intelligence/share_of_voice.py)
2. Sentiment analysis (via intelligence/sentiment.py)
3. Competitor ads (via competitive/service.py — Adyntel already wired end-to-end)
4. Competitor content (via monitoring adapters)
5. Creative patterns (via competitive/vision.py — 162 LOC Gemini vision analysis)
6. Partnerships (via competitive/intelligence/partnerships.py)

Rendered via markdown.py. Graded against CI-1..CI-8 rubrics (already in gofreddy `src/evaluation/rubrics.py`).

### 9.3 Database migration

New file: `supabase/migrations/20260423000002_ci_triangle.sql`

```sql
CREATE TABLE competitive_briefs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  date_range TEXT CHECK (date_range IN ('7d','14d','30d')),
  schema_version INT DEFAULT 1,
  brief_data JSONB NOT NULL,
  idempotency_key TEXT UNIQUE,
  dqs_score DOUBLE PRECISION,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_competitive_briefs_client_id ON competitive_briefs(client_id);
CREATE INDEX idx_competitive_briefs_idempotency ON competitive_briefs(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Monitor changelog for auto-refinement approval workflow
-- (monitor_changelog table already exists per 20260418000002)
```

### 9.4 Newsletter service

Port `src/newsletter/` from freddy (~700 LOC total):
- `service.py` (333) — Resend integration, double opt-in, broadcast, webhook handlers
- `repository.py` (213) — newsletter_sends, consent_log
- `models.py` (76) — NewsletterSend, ConsentLogEntry
- `config.py` (42) — Resend API key, confirmation flow

DB migration addendum:

```sql
CREATE TABLE newsletter_sends (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  subject TEXT NOT NULL,
  segment TEXT,
  status TEXT CHECK (status IN ('pending','sent','failed')),
  recipient_count INT,
  sent_at TIMESTAMPTZ,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE newsletter_consent_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  action TEXT CHECK (action IN ('subscribed','confirmed','unsubscribed','bounced','complained')),
  consent_token TEXT,
  ip_address INET,
  user_agent TEXT,
  confirmed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_newsletter_consent_email ON newsletter_consent_log(email);
```

Env vars: `RESEND_API_KEY`, `RESEND_AUDIENCE_ID`, `RESEND_WEBHOOK_SECRET`.

### 9.5 Weekly digest rendering

Use `src/shared/reporting/report_base.py` (already in gofreddy) + WeasyPrint + Jinja2.

Digest template: `src/monitoring/templates/weekly_digest.html.j2` — client logo, primary color, executive summary, top stories, action items, SOV chart.

### 9.6 API endpoints

Port from freddy `src/api/routers/monitoring.py`:

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/competitive/brief` | Generate brief (client_id, date_range) |
| GET | `/v1/competitive/briefs/{id}` | Fetch brief JSON |
| GET | `/v1/reports/competitive-brief/{id}.pdf` | PDF export |
| POST | `/v1/monitors/{id}/digests` | Create weekly digest |
| GET | `/v1/monitors/{id}/digests` | List digests (10-item default) |
| GET | `/v1/monitors/{id}/sentiment` | Time-series window + granularity |
| POST | `/v1/monitors/{id}/classify-intent` | On-demand intent (1000/day cap) |
| GET | `/v1/monitors/{id}/share-of-voice` | 7d–90d window |
| GET | `/v1/monitors/{id}/trends-correlation` | Pearson r |
| POST | `/v1/monitors/{id}/alerts` + 4 more | Alert lifecycle |
| POST | `/v1/monitors/{id}/changelog/{entry}/approve` + reject | Auto-refinement workflow |
| POST | `/v1/newsletter/subscribe` + confirm + broadcast + webhooks | Newsletter CRUD |

### 9.7 CLI

Extend `cli/freddy/commands/monitor.py` and add `cli/freddy/commands/digest.py`:

```bash
freddy digest generate --monitor-id <uuid> --date-range 7d
freddy digest list --client-slug acme
freddy digest send --digest-id <uuid>

freddy competitive brief --client-slug acme --date-range 14d
```

### 9.8 Tests

- Unxfail: `tests/test_newsletter_service.py`
- Add: `tests/test_competitive_brief.py` — 6-section parallel generation
- Add: `tests/test_weekly_digest.py` — end-to-end from monitor → digest → Resend delivery (mocked)
- Add: `tests/test_post_ingestion.py` — auto-refinement changelog emission

### 9.9 Done signal

- `freddy digest generate --monitor-id <fixture>` produces markdown + HTML + PDF digest.
- `freddy competitive brief --client-slug <fixture>` produces brief JSON + markdown.
- Newsletter subscribe → confirm → broadcast → webhook delivery verification works end-to-end (staging Resend).
- MonitorWorker auto-triggers weekly digest for clients with `auto_brief=True` on 7-day cadence.

---

## 10. Bundle 4 — Creator ops (wire IC + AQS + deepfake)

**Status:** not-started
**Depends on:** Bundle 2
**Duration:** 3 weeks
**Goal:** Influencers.club client is wired but unreachable. Make it reachable. Add creator fraud + deepfake vetting.

### 10.1 Orchestrator tool handlers (Path B adaptation)

Locked decision #1 says Path B (programs-only). So we don't port the full freddy orchestrator. Instead, expose IC capabilities as direct CLI commands + thin service wrappers.

New files:

#### `src/creators/service.py` (~200 LOC)

```python
class CreatorService:
    def __init__(self, ic_backend, fraud_service, deepfake_service):
        self._ic = ic_backend
        self._fraud = fraud_service
        self._deepfake = deepfake_service

    async def discover(self, query: str, platform: str, filters: dict) -> list[Creator]:
        return await self._ic.discover(query=query, platform=platform, filters=filters)

    async def get_profile(self, username: str, platform: str, enrich: bool = True) -> CreatorProfile:
        profile = await self._ic.enrich_full(username, platform)
        if enrich:
            fraud = await self._fraud.analyze(profile)
            profile.aqs_score = fraud.aqs_score
            profile.fraud_risk_level = fraud.risk_level
        return profile

    async def similar(self, username: str, platform: str, limit: int = 20) -> list[Creator]:
        return await self._ic.similar(username, platform, limit)

    async def evaluate_campaign_fit(self, usernames: list[str], platform: str, brand_context: str) -> CampaignFitReport:
        overlap = await self._ic.audience_overlap(usernames, platform)
        # Brand safety check per creator (via deepfake + fraud)
        ...

    async def check_deepfake(self, video_url: str) -> DeepfakeResult:
        return await self._deepfake.analyze(video_url)
```

### 10.2 Fraud service ensemble

gofreddy has `src/fraud/analyzers.py` (222 LOC), `config.py` (149), `models.py` (275). Missing: `service.py` — the parallel analyzer orchestrator.

Port from freddy `src/fraud/service.py` (369 LOC):

```python
class FraudService:
    def __init__(self, follower_analyzer, engagement_analyzer, comment_analyzer, ic_backend):
        ...

    async def analyze(self, username: str, platform: str) -> AQSResult:
        """Runs 3 analyzers in parallel, combines into AQS."""
        followers = await self._ic.get_followers_sample(username, platform, limit=150)
        engagement = await self._ic.get_engagement_stats(username, platform)
        comments = await self._ic.get_recent_comments(username, platform, limit=100)
        
        results = await asyncio.gather(
            self._follower_analyzer.analyze(followers),
            self._engagement_analyzer.analyze(engagement, platform),
            self._comment_analyzer.analyze(comments),
            return_exceptions=True,
        )
        
        # AQS = engagement × 0.30 + audience_quality × 0.35 + comment_auth × 0.35
        return AQSResult.combine(results)
```

### 10.3 Deepfake service orchestration

gofreddy has `src/deepfake/lipinc.py` (199) + `reality_defender.py` (166). Missing: `service.py` ensemble orchestrator.

New file: `src/deepfake/service.py` (~150 LOC)

```python
LIPINC_WEIGHT = 0.4
RD_WEIGHT = 0.6

class DeepfakeService:
    def __init__(self, lipinc, rd_client):
        ...

    async def analyze(self, video_url: str) -> DeepfakeResult:
        try:
            lipinc_task = self._lipinc.analyze(video_url)
            rd_task = self._rd.analyze(video_url)
            lipinc, rd = await asyncio.gather(lipinc_task, rd_task, return_exceptions=True)
            
            if isinstance(lipinc, Exception) and not isinstance(rd, Exception):
                return DeepfakeResult.from_rd_only(rd)
            if isinstance(rd, Exception) and not isinstance(lipinc, Exception):
                return DeepfakeResult.from_lipinc_only(lipinc)
            
            combined = (1.0 - lipinc.score) * LIPINC_WEIGHT + rd.score * RD_WEIGHT
            risk = self._risk_level(combined)
            return DeepfakeResult(
                combined_score=combined,
                risk_level=risk,
                detection_method="ensemble",
                lipinc_score=lipinc.score,
                reality_defender_score=rd.score,
            )
        except Exception as e:
            raise DeepfakeAnalysisError(str(e))

    def _risk_level(self, score: float) -> str:
        # Critical ≥0.85, High 0.70-0.84, Medium 0.50-0.69, Low 0.30-0.49, None <0.30
        ...
```

### 10.4 Fraud API router

Port from freddy `src/api/routers/fraud.py`:
- `_fetch_ic_engagement(ic_backend, platform, username)` — 15s timeout, `enrich_full` call
- `_parse_ic_engagement(data)` — `engagement_percent → avg_likes/comments`
- POST /v1/fraud/analyze — orchestrates fraud + optional IC fallback

### 10.5 Search scope routing

Port from freddy `src/search/service.py` and `src/search/ic_helpers.py`:

```python
from enum import Enum

class SearchScope(Enum):
    GENERAL = "general"
    INFLUENCERS = "influencers"

class SearchService:
    async def search(self, query: str, scope: SearchScope, filters: dict):
        if scope == SearchScope.INFLUENCERS:
            return await self._route_to_ic(query, filters)
        # Default: existing xpoz + news path
        ...
```

### 10.6 Database migration

New file: `supabase/migrations/20260423000003_creator_ops.sql`

```sql
CREATE TABLE creator_fraud_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform TEXT NOT NULL,
  username TEXT NOT NULL,
  aqs_score DOUBLE PRECISION,
  aqs_grade TEXT CHECK (aqs_grade IN ('excellent','very_good','good','poor','critical')),
  fraud_risk_level TEXT CHECK (fraud_risk_level IN ('low','medium','high','critical')),
  fraud_risk_score INT,
  bot_patterns_detected JSONB,
  engagement_tier TEXT,
  engagement_anomaly TEXT,
  analyzed_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
  UNIQUE (platform, username)
);

CREATE INDEX idx_creator_fraud_platform_username ON creator_fraud_analysis(platform, username);
CREATE INDEX idx_creator_fraud_expires ON creator_fraud_analysis(expires_at);

CREATE TABLE deepfake_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_url TEXT NOT NULL,
  lip_sync_score DECIMAL,
  reality_defender_score DECIMAL,
  combined_score DECIMAL,
  is_deepfake BOOLEAN,
  risk_level TEXT CHECK (risk_level IN ('none','low','medium','high','critical')),
  detection_method TEXT CHECK (detection_method IN ('lipinc_only','reality_defender_only','ensemble')),
  analyzed_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days')
);

CREATE INDEX idx_deepfake_video_url ON deepfake_analysis(video_url);
```

### 10.7 CLI

Add `cli/freddy/commands/creator.py`:

```bash
freddy creator discover --platform tiktok --query "sustainable fashion" --min-followers 100000
freddy creator profile @handle --platform tiktok
freddy creator fraud @handle --platform tiktok
freddy creator deepfake <video_url>
freddy creator similar @handle --platform tiktok --limit 20
freddy creator evaluate --usernames @a,@b,@c --platform tiktok --brand-context "fitness brand, B2C"
```

### 10.8 API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/creators/discover` | IC discovery |
| GET | `/v1/creators/{platform}/{username}/profile` | Enrich + AQS |
| POST | `/v1/creators/{platform}/{username}/fraud` | Fraud + AQS on demand |
| POST | `/v1/creators/deepfake` | Deepfake check |
| POST | `/v1/creators/similar` | IC similar |
| POST | `/v1/creators/evaluate` | Audience overlap + brand safety |
| POST | `/v1/search` | SearchScope routing |

### 10.9 Tests

- Unxfail: `tests/test_fraud_ic_enrichment.py`, `tests/test_pr082_ic_search.py`
- Add: `tests/test_fraud_service_ensemble.py` — parallel 3-analyzer orchestration
- Add: `tests/test_deepfake_ensemble.py` — LIPINC+RD combination, fallback paths

### 10.10 Env vars

New: `IC_API_KEY` (already defined in gofreddy config; verify loaded in app.state).

### 10.11 Done signal

- `freddy creator fraud @fixture_handle --platform tiktok` returns AQS + grade + risk level.
- `freddy creator deepfake <fixture_video_url>` returns ensemble result.
- IC subscription credentials enable real `freddy creator discover`.
- Can gate when to buy IC subscription — until this bundle ships, IC is drawer money.

---

## 11. Bundle 5 — Content factory

**Status:** not-started
**Depends on:** Bundles 2, 7
**Duration:** 5 weeks
**Goal:** Multi-platform content production for clients. Draft → approve → schedule → publish → track.

### 11.1 Content generation service

Port from freddy `src/content_gen/` (~900 LOC):

| File | LOC | Purpose |
|---|---|---|
| `service.py` | 511 | 8 content types (social_posts, blog_article, newsletter, video_script, ad_copy, rewrite, synthesize, from-digest) |
| `output_models.py` | 65 | SocialPost, NewsletterContent, VideoScript, AdCopyVariant, RewriteVariant |
| `voice_repository.py` | 178 | PostgresVoiceRepository |
| `voice_service.py` | 312 | Voice profile creation + analysis |
| `voice_models.py` | 64 | TextVoiceMetrics + Qualitative |
| `config.py` | 40 | ContentGenSettings |

### 11.2 Publishing service + adapters

Port from freddy `src/publishing/` (~3,500 LOC):

| File | LOC | Purpose |
|---|---|---|
| `service.py` | 455 | Queue state machine (DRAFT → SCHEDULED → PUBLISHING → PUBLISHED/FAILED/CANCELLED) |
| `dispatcher.py` | 78 | Already stubbed in Bundle 7 — wire enabled=True |
| `repository.py` | 718 | Persistence (platform_connections, publish_queue) |
| `rss_monitor.py` | 165 | RSS feed → queue |
| `encryption.py` | ~100 | AES-256-GCM v2 with HKDF-SHA256 |
| `oauth_manager.py` | 366 | Device flow (YouTube, TikTok), Auth Code (LinkedIn), token refresh |

Adapters (~2,000 LOC total):

| Adapter | LOC | Platform specifics |
|---|---|---|
| `linkedin.py` | 308 | POST /rest/posts restli 2.0, carousel PDF, first_comment |
| `tiktok.py` | 269 | PULL_FROM_URL 4GB, photo carousel 4–35 images |
| `youtube.py` | 317 | Resumable upload, 10K units/day quota, scheduling |
| `wordpress.py` | 142 | Application Passwords, Yoast SEO, SSRF pre-flight |
| `bluesky.py` | 247 | AT Protocol, facet building, app password |
| `webhook.py` | 153 | HMAC-SHA256, SSRF pre-flight |
| `_carousel.py` | 101 | PDF render utility |
| `instagram.py` | stub | Not in phase 1 |

### 11.3 Article generation + tracking

Port from freddy:
- `src/articles/service.py` (~200 LOC) — AI article generation with SEO optimization
- `src/seo/article_repository.py` — content_articles table
- `src/seo/article_tracking_service.py` (88 LOC) — GSC-driven performance tracking

### 11.4 Database migrations

New file: `supabase/migrations/20260423000004_content_factory.sql`

```sql
-- Platform connections with encrypted credentials
CREATE TABLE platform_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  platform TEXT NOT NULL CHECK (platform IN ('linkedin','tiktok','youtube','wordpress','bluesky','webhook','instagram')),
  auth_type TEXT CHECK (auth_type IN ('oauth2','api_key','app_password')),
  account_id TEXT,
  account_name TEXT,
  credential_enc JSONB,
  access_token_enc TEXT,
  refresh_token_enc TEXT,
  key_version INT DEFAULT 1,
  scopes TEXT[],
  token_expires_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_platform_connections_client ON platform_connections(client_id);
CREATE INDEX idx_platform_connections_active ON platform_connections(is_active) WHERE is_active = TRUE;

-- Publish queue with state machine
CREATE TABLE publish_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  connection_id UUID REFERENCES platform_connections(id),
  content_parts JSONB NOT NULL,
  media JSONB DEFAULT '[]',
  first_comment TEXT,
  og_title TEXT,
  og_description TEXT,
  og_image_url TEXT,
  canonical_url TEXT,
  slug TEXT,
  labels TEXT[] DEFAULT '{}',
  group_id UUID,
  newsletter_subject TEXT,
  newsletter_segment TEXT,
  status TEXT CHECK (status IN ('draft','scheduled','publishing','published','failed','cancelled')),
  approved_at TIMESTAMPTZ,
  approved_by UUID REFERENCES users(id),
  scheduled_at TIMESTAMPTZ,
  external_id TEXT,
  external_url TEXT,
  error_message TEXT,
  retry_count INT DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_publish_queue_status_scheduled ON publish_queue(status, scheduled_at) WHERE status IN ('scheduled','publishing');
CREATE INDEX idx_publish_queue_client ON publish_queue(client_id);
CREATE INDEX idx_publish_queue_group ON publish_queue(group_id);

-- Voice profiles
CREATE TABLE voice_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  platform TEXT,
  username TEXT,
  profile_type TEXT DEFAULT 'text',
  text_voice_json JSONB,
  video_voice_json JSONB,
  system_instruction TEXT,
  is_self BOOLEAN DEFAULT FALSE,
  posts_analyzed INT DEFAULT 0,
  generation_model TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Content articles
CREATE TABLE content_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  title TEXT,
  article_result JSONB,
  article_md TEXT,
  word_count INT,
  generation_cost_usd DECIMAL,
  site_link_graph_snapshot JSONB,
  generation_model TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE article_performance_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id UUID REFERENCES content_articles(id) ON DELETE CASCADE,
  snapshot_date DATE,
  clicks INT,
  impressions INT,
  ctr DECIMAL,
  position DECIMAL,
  UNIQUE (article_id, snapshot_date)
);
```

### 11.5 API endpoints

Port `src/api/routers/{publishing,articles,generation,newsletters}.py` from freddy:

| Router | Endpoints | Notes |
|---|---|---|
| publishing | 8 routes (draft CRUD + approve + schedule + cancel + list) | |
| articles | 5 routes (generate, list, get, performance, update) | |
| generation | 5 routes (submit job, status, list, cancel) | video_generate stub for Bundle 6 |
| newsletters | 6 routes (subscribe, confirm, broadcast, segments, sends, webhooks) | |

### 11.6 CLI

```bash
freddy write social --topic "Q2 launch" --platforms linkedin,x --voice-profile-id <uuid>
freddy write article --topic "how to X" --keywords "a,b,c" --word-count 1500
freddy write brief --collection-id <uuid> --vertical b2b_saas
freddy write rewrite --content "..." --tones "formal,casual"

freddy publish draft --platform linkedin --content "..." --connection-id <uuid>
freddy publish approve <draft_id>
freddy publish schedule <draft_id> --at 2026-05-01T10:00:00
freddy publish cancel <queue_item_id>

freddy accounts connect linkedin  # OAuth2 device flow
freddy accounts list
freddy accounts disconnect <connection_id>

freddy newsletter subscribe --email x@y.com --segment creators
freddy newsletter broadcast --subject "..." --html @body.html --segment all
```

### 11.7 Env vars

- `ENCRYPTION_SECRET` + optional `ENCRYPTION_SECRET_V2` (HKDF master)
- LinkedIn, TikTok, YouTube client IDs / secrets
- `RSS_FEEDS` (optional, for RSS monitor)

### 11.8 Tests

- Add: per-adapter unit tests (mock HTTP)
- Add: `tests/test_publish_dispatcher_full.py` — end-to-end claim → publish → retry
- Add: `tests/test_content_generation.py` — all 8 content types
- Add: `tests/test_oauth_device_flow.py` — LinkedIn + YouTube + TikTok
- Add: `tests/test_encryption_rotation.py` — v1 → v2 key rotation

### 11.9 Done signal

- Connect a real LinkedIn account via `freddy accounts connect linkedin`.
- `freddy publish draft → approve → schedule` ends up published on LinkedIn at scheduled time.
- Voice profile analyzed from 100+ real posts captures tone consistently.
- `freddy write article` produces 1,500-word article with SEO metadata, saves to content_articles.
- GSC article performance tracking pulls clicks/impressions weekly.

---

## 12. Bundle 6 — Video studio (deferred)

**Status:** deferred (plan exists, not slated until post-Bundle 5)
**Depends on:** Bundles 2, 5, 7
**Duration:** 8–10 weeks when taken up

### 12.1 Short scope

Full storyboard + generation pipeline per research record section 11 (Bundle 6).

Key files if we take this up:
- `src/video_projects/{service,models,exceptions}.py` — port service (1,468 LOC), regenerate repository (17k LOC → probably fits in 2k lean rewrite)
- `src/generation/{service,worker,composition,*_client,idea_service,storyboard_evaluator,image_preview_service}.py` — full port (~5,000 LOC)
- `src/creative/service.py` + repository
- `src/stories/` — optional Instagram story capture
- 4 new DB tables: video_projects, video_project_scenes, video_project_references, video_project_generation_jobs
- API routers: video_projects, voice_profiles, media
- Frontend: VideoProjectStudio.tsx + hooks (requires UI port — another deferred decision)

### 12.2 When to reconsider

If a paying client asks for white-label video ad production. Not before.

Until then: gofreddy users can produce video via other tools and hand off to Bundle 5 for publishing.

---

## 13. Bundle 8 — Workspace + skills infrastructure (deferred)

**Status:** deferred (Path B decision already locked)
**Depends on:** Bundles 2, 4, 5
**Duration:** 3–4 weeks if we take the minimal workspace path; 8 weeks if we go Path A full orchestrator

### 13.1 If we take this up

**Workspace + collections + batch + library + SSE** (~2,200 LOC):

| File | LOC | Purpose |
|---|---|---|
| `src/workspace/service.py` | 288 | Collection CRUD, dedup, filter-in-place |
| `src/workspace/repository.py` | 692 | Atomic CTEs (create, set_active, aggregate) |
| `src/workspace/models.py` | 116 | Collection, Item, ToolResult, Summary |
| `src/batch/service.py` | 164 | Batch state machine, tier limits, idempotency |
| `src/batch/repository.py` | 345 | Atomic claim (FOR UPDATE SKIP LOCKED), retry CTE |
| `src/batch/worker.py` | 412 | 50-worker pool, rate limiting, transient vs permanent errors |

API routers: workspace (5 routes), batch (4 routes incl SSE progress), library (3 routes).

DB tables: workspace_collections, workspace_items, workspace_events, workspace_tool_results, batch_jobs, batch_items.

### 13.2 Path A re-evaluation gate

If a paying client demands a chat UI with capability pills + tool invocation, re-evaluate Path A. Port estimate: 6–8 weeks for orchestrator + 20 tool catalog specs + 20 handler modules + dynamic system prompt builder + frontend capability framework.

Until that demand exists: Path B remains locked.

---

## 14. Execution checkpoints

| Checkpoint | Bundle completion | What we know after |
|---|---|---|
| C1 — Honest CI | Bundle 0 | How many tests actually pass, what real coverage looks like |
| C2 — Agency data model | Bundles 1 + 2 | Can create real client entities; prompts/taxonomies land in audit flow |
| C3 — First audit | Bundle 9 | $/audit real cost, per-lens cost breakdown, deliverable quality |
| C4 — Self-improvement loop | Bundle 10 | Whether autoresearch variants meaningfully improve audit quality over 3 generations |
| C5 — Async operations | Bundle 7 | Worker reliability, Fly Redis latency, scheduled-job drift |
| C6 — First commodity deliverable | Bundle 3 | First weekly brief sent to a real client; is the digest actually useful |
| C7 — Creator vetting | Bundle 4 | IC subscription ROI; AQS accuracy on real creators |
| C8 — Content scaling | Bundle 5 | Can one operator ship 50+ posts/week across clients |

---

## 15. Appendix A — Database migrations summary

All migrations go under `supabase/migrations/` with the prefix pattern `20260423NNNNNN_bundle_N_description.sql`.

| Bundle | Migration file | Tables affected |
|---|---|---|
| 2 | `20260423000001_client_platform_lite.sql` | clients (ALTER) |
| 3 | `20260423000002_ci_triangle.sql` | competitive_briefs, newsletter_sends, newsletter_consent_log |
| 4 | `20260423000003_creator_ops.sql` | creator_fraud_analysis, deepfake_analysis |
| 5 | `20260423000004_content_factory.sql` | platform_connections, publish_queue, voice_profiles, content_articles, article_performance_snapshots |
| 9 | (no migration — audit state lives in filesystem for phase 1) | — |
| 6 (deferred) | `20260423000005_video_studio.sql` | video_projects, video_project_scenes, video_project_references, video_project_generation_jobs |
| 8 (deferred) | `20260423000006_workspace.sql` | workspace_collections, workspace_items, workspace_events, workspace_tool_results, batch_jobs, batch_items |

---

## 16. Appendix B — Environment variables by bundle

| Bundle | Variables added |
|---|---|
| 0 (preflight) | none |
| 1 | none (prompts + classifiers use existing GEMINI_API_KEY) |
| 2 | none |
| 3 | `RESEND_API_KEY`, `RESEND_AUDIENCE_ID`, `RESEND_WEBHOOK_SECRET` |
| 4 | `IC_API_KEY` (verify loaded), `REPLICATE_API_KEY` (LIPINC), `REALITY_DEFENDER_API_KEY` |
| 5 | `ENCRYPTION_SECRET`, `ENCRYPTION_SECRET_V2` (optional rotation), `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `TIKTOK_CLIENT_ID`, `TIKTOK_CLIENT_SECRET`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` |
| 7 | `REDIS_URL` (from Fly Redis), `MONITOR_WORKER_POLL_INTERVAL_SECONDS`, `PUBLISH_DISPATCHER_POLL_INTERVAL_SECONDS` |
| 9 | `GEMINI_API_KEY` (already present), `ANTHROPIC_API_KEY` (for audit synthesis agents) |

---

## 17. Appendix C — Python dependencies by bundle

| Bundle | Added to pyproject.toml |
|---|---|
| 0 (preflight) | `resend>=2.0,<3.0`, `weasyprint>=62.0`, `mistune>=3.0.0`, `nh3>=0.2.14`, `jinja2>=3.1.0` |
| 3 | none beyond Bundle 0 |
| 4 | none (IC + Replicate use existing httpx) |
| 5 | none (adapters use existing httpx) |
| 6 (deferred) | `ffmpeg-python>=0.2.0`, `librosa>=0.10.0` |
| 7 | `redis>=5.0.0` |
| 9 | `playwright>=1.40.0` (rendered_fetcher) |

Explicitly skipped packages (not added until needed):
- `stripe[async]` — Bundle 3/9 billing if/when we adopt Stripe
- `google-cloud-tasks` — not using Cloud Tasks per decision #2
- `dspy` — not using DSPy, Path B
- `supabase` — asyncpg sufficient
- `svix` — not porting Stripe webhook Svix verification in phase 1

---

## 18. Appendix D — Risk register

| Risk | Bundle | Mitigation |
|---|---|---|
| Audit cost ceiling hit on real prospect | 9 | Per-stage estimates, pause-and-email operator for approval, adjust lens dispatch |
| IC subscription cost > value | 4 | Don't subscribe until Bundle 4 ships; run 3 real creator-discovery flows before committing |
| OAuth flows break on platform policy changes | 5 | Adapter tests against real sandbox accounts monthly |
| Fly Redis single-region latency | 7 | Stay in same region as web process; measure P99 on staging |
| Autoresearch variants degrade rather than improve audit quality | 10 | Evolution judges emit collapse/plateau alerts; rollback agent reverts; holdout suite catches regression |
| Lens catalog shifts (unlocks v3) | 9 | `lenses.yaml` is single-file diff-friendly; regenerate when unlocked |
| Orphaned test xfail becomes permanent graveyard | 0 | Every xfail references the bundle that unblocks it; Bundle N completion unxfails specific files |

---

## 19. End of plan

Next actions:
1. Execute Bundle 0 today/tomorrow.
2. Start Bundle 1 + Bundle 2 in parallel next week.
3. Write revised Bundle 9 detail as we approach its start — much of it is greenfield and will benefit from 1–2 weeks of living with Bundles 1 + 2 before solidifying.
4. Revisit this plan's checkpoints after each bundle ships and update status fields.

Revision history:
- 2026-04-23: initial plan committed.
