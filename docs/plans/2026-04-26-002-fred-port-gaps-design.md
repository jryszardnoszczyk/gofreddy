# Fred → GoFreddy Port-Gaps: Design (Bundles A + B)

> ## ⚠ SUPERSEDED — research record only
>
> **Active reference:** `docs/plans/2026-04-27-001-fred-port-gaps-checklist.md`
>
> This design was scoped around Bundle A (porting freddy's `src/orchestrator/`) and Bundle B (marketing-audit prereqs). **Bundle A was dropped on 2026-04-27 after round-5 triage surfaced two corrections:**
>
> 1. GoFreddy's `autoresearch/` IS the orchestration system. Importing freddy's `src/orchestrator/` would create a parallel agent system that conflicts with the one already built.
> 2. `docs/plans/2026-04-23-003-agency-integration-plan.md` Decision #1 explicitly locked **Path B (programs-only extension)** on 2026-04-23. The 14 `tests/orchestrator/test_*.py` files are marked xfail-permanent in that plan, not driven by a port.
>
> Bundle B was also re-scoped: B.1 (`clients/models.py` port) + B.2 (`content_extractor` port) + B.7 (docs snapshot) + B.8 (deepfake test_models port) are pure ports and ship on this branch. **B.3 (eval extensions) + B.4 (marketing-audit judge) + B.5 (autoresearch lane registration) + B.6 (programs/marketing_audit/ prompts) are greenfield extensions to the autoresearch orchestrator** — they belong to the next branch (`feat/audit-engine-implementation`) following `docs/plans/2026-04-24-003-audit-engine-implementation-design.md`, not this branch.
>
> Preserved unchanged below for institutional record. Skim, don't action.

---

**Date:** 2026-04-26
**Branch:** `feat/fred-port-gaps`
**Scope:** Active subset of `docs/plans/2026-04-26-001-fred-port-gaps-inventory.md` — Bundle A (orchestrator foundation, slim) + Bundle B (marketing-audit prereqs).
**Sequencing:** A → B on this branch. Tag `autoresearch-v1-baseline` at A→B boundary.
**Out of scope:** Bundles C/D/E/F and the full skip-list. See inventory `§Skip-list`.

---

## 1. Goal & Scope

**Goal.** Close the two highest-leverage gaps:
1. **Bundle A** — Port a slim orchestration foundation so gofreddy has unified tool registration, dynamic tool selection, ReAct loop, cost-budget enforcement, and runaway-loop protection. Unblocks "agent teams" and the broken `tests/test_tool_catalog.py`.
2. **Bundle B** — Port the marketing-audit prerequisites the audit-engine plan (`2026-04-24-003`) cites by name: MA-1..MA-8 evaluation domain, content extractor, audit-only `clients` schema subset, autoresearch lane registration, `programs/marketing_audit/` prompts.

**Success criteria.**
- `tests/test_tool_catalog.py` and `tests/test_cli_evaluate_scope.py` collect and pass.
- New tests cover ToolRegistry roundtrip, ReAct stuck-detection, CostTracker budget filtering, MA-1..MA-8 rubric registration, content-extractor smoke, deepfake `models.py` schema validation.
- One Stage-2 marketing-audit agent (Findability) runs end-to-end against a fixture client without hitting stuck-detection or budget caps.
- `scripts/build_tool_artifacts.py` runs against the ported catalog and writes a non-empty `SKILL.md`.
- CostTracker hard-cap raises `CostCapExceeded` when budget exceeded (Bundle X).
- `src/orchestrator/tool_handlers/_helpers.py` regex validators have unit-test coverage (Bundle W).
- `gofreddy/docs/from-fred/` exists with the 10 reference files + a top-level README explaining their frozen status.
- Existing flows (`freddy detect`, `freddy evaluate`, `freddy competitive`, `freddy audit *`) keep passing their tests.

**Locked decisions** (recorded in inventory `§Open decisions`):
- Bundle A scope = "C" — runtime machinery only; no `prompts.py` or `strategies/` port.
- Decouple from `Tier`/`Workspace`/`Billing` during port — replace type-hints with protocol stubs or remove.
- 4 broad-scope agents for the audit (Findability, Narrative, Acquisition, Experience) — already locked in `2026-04-23-002` §54.
- MA-1..MA-8 rubric prose: transcribe sketches now, refine in v1 dogfood.
- Tool catalog scope: port all ~20 specs (catalog is metadata only; subset = re-port debt).
- Stuck detection: full circuit-breaker port.
- Tag `autoresearch-v1-baseline` at end of Bundle A.

---

## 2. Architecture

### 2.1 Module landing (target tree under `gofreddy/`)

```
src/orchestrator/                       [Bundle A — new]
├── __init__.py
├── tool_catalog/                       # Single source of truth for ~20 tool specs
│   ├── __init__.py                     # exports: all_specs, get_spec, to_json_schema
│   ├── catalog.py                      # the spec list itself
│   └── _spec.py                        # ToolSpec dataclass + validation
├── tools.py                            # ToolRegistry, ToolDefinition (~25 handlers)
├── agent.py                            # VideoIntelligenceAgent → renamed AgentLoop
├── cost.py                             # CostTracker (extracted from freddy's agent.py)
├── stuck.py                            # detection + circuit-breaker (extracted)
├── filters.py                          # _prepare_for_llm tool-result filtering
└── compat.py                           # tool-name migration map + error allowlist

src/audit/                              [Bundle B — partial; plan 003 designs the full module]
└── enrichments/
    └── assets.py                       # ports freddy/src/extraction/content_extractor.py

src/clients/                            [Bundle B — new, narrow]
├── __init__.py
└── models.py                           # Client model, audit-only fields (no billing/membership)

src/evaluation/                         [Bundle B — extend in place]
├── service.py                          # add "marketing_audit" to Domain Literal
├── rubrics.py                          # add MA-1..MA-8 RubricTemplate instances
├── structural.py                       # add _validate_marketing_audit()
└── judges/
    └── marketing_audit.py              # MA judge orchestrator

autoresearch/                           [Bundle B — extend in place]
├── lane_runtime.py                     # register marketing_audit lane
├── lane_paths.py                       # add lane path resolution
├── evolve.py                           # register lane in evolution loop
├── evaluate_variant.py                 # route marketing_audit variants
├── critique_manifest.py                # add lane critique config
└── archive/current_runtime/programs/marketing_audit/  [new dir]
    ├── prompts/
    │   ├── findability.md
    │   ├── narrative.md
    │   ├── acquisition.md
    │   ├── experience.md
    │   ├── stage1a_pre_discovery.md
    │   ├── stage1b_brief_synthesis.md
    │   ├── stage1c_lens_routing.md
    │   ├── stage3_section_synthesis.md
    │   └── stage4_proposal.md
    ├── critique_manifest.yaml
    └── evaluation_scope.yaml

tests/                                  [both Bundles]
├── test_tool_catalog.py                # already exists, currently broken — port closes it
├── test_orchestrator_registry.py       # new
├── test_orchestrator_agent_loop.py     # new
├── test_orchestrator_cost.py           # new
├── test_orchestrator_stuck.py          # new
├── test_audit_assets_enrichment.py     # new
├── test_clients_model.py               # new
├── test_marketing_audit_rubrics.py     # new
└── test_autoresearch_marketing_audit_lane.py  # new
```

### 2.2 Decoupling strategy

Freddy's orchestrator type-hints reference `Tier`, `WorkspaceService`, and `Billing` — none of which exist in gofreddy by design. The port replaces them with **protocol stubs** (PEP 544 `Protocol`) so the runtime semantics are preserved without dragging the SaaS surface in:

```python
# src/orchestrator/_protocols.py
from typing import Protocol

class _NoTier(Protocol):
    """Stand-in for freddy Tier; gofreddy is single-tenant."""
    name: str = "agency"
    def can_use(self, tool_name: str) -> bool: return True

class _NoWorkspace(Protocol):
    """Stand-in for freddy WorkspaceService; gofreddy uses file paths."""
    async def store_result(self, *args, **kwargs) -> None: return None
```

Where freddy's agent.py calls `tier.can_use(tool)` or `await workspace.store_result(...)`, gofreddy's port calls the stub. Tier-gating becomes a no-op (everything allowed); workspace persistence becomes a no-op (file paths are owned by callers via `clients/<name>/sessions/`).

**Rationale.** This keeps the diff minimal — we don't have to rewrite control flow, just inject stubs. If we later want real tier/workspace logic, swap the protocol implementations without touching the agent loop.

### 2.3 CostTracker vs cost_recorder

- **`src/common/cost_recorder.py`** (existing) — JSONL append-only spend log per provider call. Persists.
- **`src/orchestrator/cost.py:CostTracker`** (new, ported) — *per-request* budget enforcement. In-memory token accumulator, pre-call budget filter via `_TOOL_COST_ESTIMATES`, downstream cost aggregation.

These are complementary, not redundant. The orchestrator's CostTracker calls `cost_recorder.record_*` after each LLM/tool call to persist; CostTracker itself enforces the budget envelope per agent-turn. Bundle A keeps both.

### 2.4 Tool catalog and ToolRegistry interaction

```
                       ┌────────────────────────┐
                       │  tool_catalog (specs)  │ <-- pure metadata
                       │  20 ToolSpec entries   │
                       └──────────┬─────────────┘
                                  │ all_specs() / get_spec()
                                  ▼
                       ┌────────────────────────┐
                       │  ToolRegistry          │ <-- runtime, holds handlers
                       │  build_default_registry│
                       └──────────┬─────────────┘
                                  │ tools_by_name, build_system_prompt
                                  ▼
                       ┌────────────────────────┐
                       │  AgentLoop             │ <-- ReAct + cost + stuck
                       └──────────┬─────────────┘
                                  ▼
                       (Gemini / OpenAI / etc., via existing src/* clients)
```

The catalog is metadata; the registry binds names to *Python callables* that gofreddy already has (`src/seo/providers/dataforseo.py`, `src/competitive/providers/foreplay.py`, etc.). Most existing gofreddy provider modules already match the freddy tool-handler signatures; the registry's job is to wire them up.

### 2.5 What `prompts.py` / `strategies/` get replaced with

Bundle A skips freddy's 3K-line `prompts.py` + `strategies/`. The replacement is **per-flow prompts written fresh inside each gofreddy command** (or, for the audit, inside `autoresearch/.../programs/marketing_audit/prompts/`). The ToolRegistry exposes `build_system_prompt(tools=[...])` that generates a tool-listing prefix; each command prepends its own purpose-specific prompt to that. No shared "kitchen-sink" prompt.

---

## 3. Bundle A — Units of Work

Port runs in this order. Each unit is independently shippable but all need to land before Bundle B's marketing-audit judges can use them.

### A.1 — `tool_catalog/`

Port `freddy/src/orchestrator/tool_catalog/` essentially verbatim. **Keep all ~20 specs as-is** (locked decision; catalog is metadata, no runtime cost for unused specs). The ToolRegistry (A.3) is responsible for emitting a warning at `build_default_registry()` time if a spec has no handler in gofreddy. Keep `to_json_schema()` exporter intact.

**Tests:** `test_tool_catalog.py` (existing, currently broken) starts passing. Add `test_tool_catalog_roundtrip.py` for spec→json_schema→spec.

**Port effort:** S.

### A.2 — Protocol stubs (`_protocols.py`)

Net-new file in gofreddy. Define `_NoTier`, `_NoWorkspace` as no-op stand-ins for the SaaS types referenced by `agent.py`/`tools.py`.

**Tests:** none (trivial type stubs).

**Port effort:** S.

### A.3 — `tools.py` (ToolRegistry)

Port `freddy/src/orchestrator/tools.py`. Replace `Tier` / `WorkspaceService` imports with protocol stubs (A.2). Drop `to_adk_tools()` method (Google ADK is not used). Keep `build_default_registry()`, `build_system_prompt()`, parameter-schema validation.

**Tests:** `test_orchestrator_registry.py` covering: register/lookup, system-prompt generation, parameter validation, duplicate-detection.

**Port effort:** S.

### A.4 — `cost.py` (CostTracker + hard-cap enforcement)

Extract `CostTracker` from `freddy/src/orchestrator/agent.py` into its own file `src/orchestrator/cost.py`. Port `_TOOL_COST_ESTIMATES`. Wire `record_*` calls into existing `src/common/cost_recorder` for persistence.

**Hard-cap enforcement (Bundle X folded in).** Round 4 I4 found neither freddy nor gofreddy enforces a hard cost cap — both log overruns but never halt. Extend the port:
- Add `max_budget_usd: float | None = None` to `CostTracker.__init__`.
- Add `class CostCapExceeded(Exception)` raised when accumulated cost exceeds `max_budget_usd`.
- Pre-call budget filter (existing freddy behavior) stays as the soft check; the new hard cap fires only on overrun, after the call has happened.

**Tests:** `test_orchestrator_cost.py`: budget filter rejects calls that would exceed cap; per-turn aggregation matches; `cost_recorder` writes happen; `CostCapExceeded` raised when cap exceeded; cap defaults to `None` (no enforcement) for backward-compat.

**Port effort:** S.

### A.5 — `stuck.py` (stuck detection + circuit breaker)

Extract stuck-detection logic from `freddy/src/orchestrator/agent.py` into `src/orchestrator/stuck.py`. Port `_STUCK_DETECTION_EXEMPT` allowlist. Keep the same triggering thresholds (3 repeats of same tool + same args = circuit break).

**Tests:** `test_orchestrator_stuck.py`: same-tool+same-args 3× triggers; exempt tools don't trigger; reset-on-progress behaves.

**Port effort:** S.

### A.6 — `filters.py` + `compat.py`

`filters.py` — port `_prepare_for_llm` (strip heavy payloads, fix UUID serialization).
`compat.py` — `TOOL_NAME_MIGRATION_MAP` (legacy→current name table) + `_PASSTHROUGH_ERROR_CODES` allowlist (~70 entries).

**Tests:** filter unit tests (large blob compression, UUID handling); migration-map applies.

**Port effort:** S.

### A.7 — `agent.py` (AgentLoop)

Port `freddy/src/orchestrator/agent.py:VideoIntelligenceAgent` → `gofreddy/src/orchestrator/agent.py:AgentLoop`. Renames: drop "video" prefix (gofreddy uses it for many flows). Strip references to `prompts.build_system_prompt()` and `strategies/*` — system prompts come from caller. Wire CostTracker (A.4), stuck detection (A.5), filters (A.6) as composed dependencies.

**Port-source table (cross-reference for the writing-plans phase):**

| What | Source in freddy | Notes |
|---|---|---|
| Core ReAct loop | `freddy/src/orchestrator/agent.py:VideoIntelligenceAgent` | Main port target |
| Per-request agent build | `freddy/src/api/routers/agent.py:_build_per_request_agent` (lines 184-440, ~267 LOC) | Reference only — adapt logic; gofreddy's tier filter is a no-op via `_NoTier` (§2.2) |
| Recipe-context injection | Same file as above | Optional v1; defer to follow-up if not needed for marketing-audit agents |
| Cost-budget override pattern | Same file as above (lines ~280-310) | Inform CostTracker (A.4) defaults |

API:

```python
class AgentLoop:
    def __init__(
        self,
        registry: ToolRegistry,
        cost_tracker: CostTracker,
        *,
        system_prompt: str,           # caller provides
        max_turns: int = 20,
        model: str = "gemini-2.5-pro",
        ...
    ): ...

    async def run(self, user_message: str, *, session_id: str | None = None) -> AgentResult: ...
```

**Tests:** `test_orchestrator_agent_loop.py`: happy path (1-tool ReAct), stuck-detection trip, cost-cap trip, error-passthrough.

**Port effort:** M.

### A.8 — Mark `autoresearch-v1-baseline` cut-point

After A.1–A.7 land and tests are green, **record the commit SHA** as the Bundle-A→Bundle-B cut-point. The literal tag is created on `main` at merge time (avoids tagging WIP feature-branch commits that get squashed). The marker is referenced in the merge PR description and in the inventory `§Open decisions`. No code change.

### A.9 — `scripts/build_tool_artifacts.py` (co-ship with tool catalog)

Port `freddy/scripts/build_tool_artifacts.py` to `gofreddy/scripts/build_tool_artifacts.py`. This script auto-generates `SKILL.md` + CLI documentation stubs from `src/orchestrator/tool_catalog.all_specs()`. Its only input is the catalog ported in A.1, so it co-ships naturally.

Add a CI hook (or pre-commit) only if the team wants drift-detection between `tool_catalog.py` and the generated artifacts; otherwise it's a manual run. **Lean: manual for v1**, document the run in the script's docstring.

**Tests:** smoke test that runs the script against a fixture catalog and verifies output exists. No deeper assertions.

**Port effort:** S.

### A.10 — `tool_handlers/_helpers.py` (round 4 finding — fold-in)

Round 4 I5 surfaced `freddy/src/orchestrator/tool_handlers/_helpers.py` (296 LOC) — sits adjacent to the tool handlers and provides regex validators (username, video ID, request parsing), namespace UUID, severity ordering, sanitization wrappers used across multiple handlers.

Port to `gofreddy/src/orchestrator/tool_handlers/_helpers.py`. The tool handlers themselves are already in A.3's scope (ToolRegistry binds catalog → ~25 callable handlers); this just adds the shared helpers those handlers call.

**Tests:** unit tests for the regex validators (valid/invalid inputs), namespace UUID determinism, severity ordering, sanitization roundtrip. Folded into `test_orchestrator_tool_handlers.py`.

**Port effort:** S.

---

## 4. Bundle B — Units of Work

### B.1 — `src/clients/models.py` (audit-only subset)

Net-new in gofreddy. Port `freddy/src/clients/models.py:Client` model, narrowed:
- **Keep:** `name`, `slug`, `domain`, optional `enrichments: dict`, optional `fit_signals: dict`, `created_at`.
- **Drop:** `subscription_id`, `tier`, `billing_status`, `members`, `workspace_id`, anything Stripe-touching.
- **Add:** audit-specific optional fields per `2026-04-20-002` R22 + design `2026-04-23-002` §v1.

Persistence is JSON file at `clients/<slug>/client.json` (matches existing gofreddy file-based workspace model). No DB.

**Tests:** `test_clients_model.py`: model roundtrip, validation, missing-required handling.

**Port effort:** S.

### B.2 — `src/audit/enrichments/assets.py`

Port `freddy/src/extraction/content_extractor.py` PDF/PPTX-extraction helpers into a thin wrapper at `src/audit/enrichments/assets.py`. Drop the multi-source URL/video paths (those are Bundle C).

```python
def extract_pdf(path: Path) -> str: ...
def extract_pptx(path: Path) -> str: ...
def extract_assets(client_slug: str) -> dict[str, str]:
    """Read every PDF/PPTX in clients/<slug>/assets/ → name→text dict."""
```

**Tests:** `test_audit_assets_enrichment.py` against fixtures (one PDF + one PPTX per `tests/fixtures/clients/<slug>/assets/`).

**Port effort:** S.

### B.3 — `src/evaluation/` extensions

Three in-place edits to existing files (~200 LOC net):

1. **`src/evaluation/service.py`** — add `"marketing_audit"` to the `Domain` Literal.
2. **`src/evaluation/rubrics.py`** — add 8 `RubricTemplate` instances (MA-1..MA-8). Prose transcribed from `2026-04-24-003` §7.3 sketches (locked decision: transcribe-now, refine in dogfood).
3. **`src/evaluation/structural.py`** — add `_validate_marketing_audit(deliverables: dict) -> ValidationResult` per design §7.1.

**Tests:** `test_marketing_audit_rubrics.py`: 8 templates registered, structural validator catches malformed deliverables, end-to-end domain dispatch.

**Port effort:** S.

### B.4 — `src/evaluation/judges/marketing_audit.py`

Net-new judge that orchestrates MA-1..MA-8 calls per the design `2026-04-23-002` §v2. Sketch:

```python
class MarketingAuditJudge:
    def __init__(self, registry: ToolRegistry, cost_tracker: CostTracker): ...
    async def evaluate_subsignals(self, audit_state: dict) -> list[SubSignalVerdict]: ...
    async def evaluate_parent_findings(self, audit_state: dict) -> list[ParentFindingVerdict]: ...
```

Depends on Bundle A's `ToolRegistry` and `CostTracker` (this is *the* reason A precedes B).

**Tests:** `test_marketing_audit_judge.py` against fixture audit state.

**Port effort:** M.

### B.5 — `autoresearch/` lane registration

Five-file edit in place. All registration boilerplate; no logic changes:

- `autoresearch/lane_runtime.py` — add `marketing_audit` lane.
- `autoresearch/lane_paths.py` — path resolver.
- `autoresearch/evolve.py` — register in evolution loop.
- `autoresearch/evaluate_variant.py` — route `marketing_audit` variants to MA judge.
- `autoresearch/critique_manifest.py` — add lane critique config.

**Tests:** `test_autoresearch_marketing_audit_lane.py`: lane appears in registry, paths resolve, evaluate routes correctly.

**Port effort:** M.

### B.6 — `programs/marketing_audit/` prompts + manifest

New directory at `autoresearch/archive/current_runtime/programs/marketing_audit/`. Contents:

- 4 agent prompts: `findability.md`, `narrative.md`, `acquisition.md`, `experience.md` (4-agent partition per locked decision).
- 5 stage prompts: `stage1a_pre_discovery.md`, `stage1b_brief_synthesis.md`, `stage1c_lens_routing.md`, `stage3_section_synthesis.md`, `stage4_proposal.md`.
- `critique_manifest.yaml` — per-criterion paraphrase + verifier configuration.
- `evaluation_scope.yaml` — which deliverables MA-1..MA-8 score per agent role.

Content sourced from catalog `005`, ranking `006`, plan `2026-04-20-002` R3, and design `2026-04-23-002` §v1. Prose locked at first pass; iteration happens in v1 dogfood.

**Port effort:** M (~6 KB content total).

### B.7 — `docs/from-fred/` knowledge preservation snapshot

Create `gofreddy/docs/from-fred/` with a top-level `README.md` explaining "frozen reference material from `freddy@50602a2`, not actively maintained, do not port code from these — read for context only." Copy these files (paths preserved relative to `freddy/`) into the new dir:

- `docs/research/2026-04-17-workflow-failure-root-causes.md`
- `docs/research/2026-04-13-autoresearch-session-loop-audit.md`
- `docs/research/2026-04-11-autoresearch-evaluation-infrastructure-audit.md`
- `docs/research/2026-04-11-autoresearch-prompt-audit.md`
- `docs/research/2026-04-14-autoresearch-run2-audit.md`
- `docs/research/2026-04-16-storyboard-mock-removal-and-evolution-readiness.md`
- `docs/plans/2026-04-18-001-migrate-autoresearch-to-gofreddy-plan.md`
- `docs/plans/2026-04-14-004-refactor-harness-unconstrained-loop-plan.md`
- `docs/plans/2026-04-08-001-fix-harness-round1-findings-plan.md`
- `docs/superpowers/specs/2026-04-16-freddy-distribution-engineering-agency-design.md`

The first one (`workflow-failure-root-causes.md`) is the most directly applicable — 31 documented autoresearch failure root causes with line numbers and fixes. Saves redundant debugging.

**Tests:** none (it's a doc copy).

**Port effort:** S.

### B.8 — Deepfake test parity (cheap fold-in)

`src/deepfake/` exists in gofreddy with provider adapters but **zero test coverage** (round 2 G6 finding). Port the test files that don't depend on FastAPI:

- `freddy/tests/deepfake/test_service.py` → `gofreddy/tests/deepfake/test_service.py`
- `freddy/tests/deepfake/test_models.py` → `gofreddy/tests/deepfake/test_models.py`
- *Skip* `freddy/tests/deepfake/test_router.py` (FastAPI route tests; out of scope).

Note: `test_service.py` exercises orchestration logic for the *missing* `src/deepfake/service.py` (Bundle G). On this branch, port the test against a stub or `pytest.skip` until Bundle G lands. Better: port only `test_models.py` for now (covers schema validation against existing `src/deepfake/models.py`); `test_service.py` rides with Bundle G.

**Decision:** Port `test_models.py` only on this branch. Defer `test_service.py` to Bundle G.

**Port effort:** S.

---

## 5. Sequencing & dependencies

```
A.1 tool_catalog ──┐
A.2 protocols ─────┤──> A.3 tools.py ──> A.7 agent.py ──> A.8 mark cut-point
                   │      ▲                  ▲                  │
A.4 cost.py ───────┼──────┘                  │                  ▼
A.5 stuck.py ──────┼─────────────────────────┤            A.9 build_tool_artifacts (uses A.1)
A.6 filters/compat ┘                         │
                                             ▼
                                       B.1 clients/models  (independent)
                                       B.2 audit/assets    (independent)
                                       B.3 eval/* extensions
                                       B.4 eval/judges/MA  ──> needs A.3 + A.4
                                       B.5 autoresearch lane registration ──> needs B.4
                                       B.6 programs/marketing_audit/  (independent)
                                       B.7 docs/from-fred/  (independent, tiny)
                                       B.8 deepfake/test_models.py  (independent, tiny)
```

- **A.1, A.2** parallel-safe (no deps).
- **A.4, A.5, A.6** parallel-safe with A.3 once protocols (A.2) land.
- **A.3** depends on A.1 + A.2.
- **A.7** depends on A.3, A.4, A.5, A.6.
- **A.8** is the cut-point marker. Bundle B starts.
- **A.9** depends only on A.1; can land any time after the catalog exists.
- **A.10** depends on A.3 (tool handlers are bound by ToolRegistry; helpers ride alongside).
- **B.1, B.2, B.3, B.6, B.7, B.8** are independent of each other; can land in any order or in parallel during Bundle B.
- **B.4** depends on A.3 + A.4 (must come after Bundle A).
- **B.5** depends on B.4 directly — `evaluate_variant.py` imports the MA judge to route variants to it.

**Estimate.** Bundle A ≈ 8–10 working days (including A.9). Bundle B ≈ 7–9 working days (including B.7 + B.8). Total ≈ 3.5–4 weeks calendar with normal review cycles.

---

## 6. Testing strategy

### 6.1 Pre-existing tests

- **`tests/test_tool_catalog.py`** — currently fails at collection (missing import). After A.1, must pass without modification. This is a regression-gate for the port.
- **`tests/test_cli_evaluate_scope.py`** — fails because `typer` was missing from base sync; resolved already by `uv sync --extra dev`. Confirm clean run after each unit lands.
- **All other existing tests** — must not regress. Run `pytest tests/ -q --no-header --ignore=tests/judges --ignore=tests/harness` (heavy fixtures excluded for speed) at A.1, A.3, A.7, A.8, B.4, end-of-B.

### 6.2 New tests per unit

Listed inline above. Common pattern: each unit has one focused test file. No integration / E2E except the fixture-driven Findability smoke run (see 6.3).

### 6.3 Smoke run (success criterion)

After Bundle B lands, a fixture-driven smoke test (in `tests/test_marketing_audit_smoke.py`, **not** a CLI command — Bundle B doesn't include the audit-engine CLI; that's plan `2026-04-24-003`) must complete without runtime errors. Setup: pre-staged `tests/fixtures/clients/fixture-client/assets/*.pdf`. Run path: load client → instantiate `AgentLoop` with the Findability prompt + ToolRegistry → call `loop.run()` for ≤5 turns → run MA judge over the produced state. Asserts: agent loop runs ≥1 turn, CostTracker records >0 USD, stuck-detection doesn't trigger, MA judge returns ≥1 verdict.

### 6.4 What's deliberately NOT tested

- ADK paths (we skipped the wrapper).
- `prompts.py` / `strategies/` from freddy (we replaced with per-flow prompts).
- Multi-tenant / billing paths (decoupled to no-op stubs; "tier always allows" is the contract).

---

## 7. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Freddy's `agent.py` has subtle Gemini-coupling that bleeds into the port | MED | MED | Keep the SDK call paths unchanged; only swap type imports. Don't try to multi-provider in this PR. |
| Tool catalog has specs without handlers in gofreddy (catalog/registry drift) | LOW | LOW | Catalog keeps all specs (metadata is harmless); ToolRegistry's `build_default_registry()` emits a warning at startup naming specs that have no handler. Tests assert the warning fires when expected. |
| MA-1..MA-8 rubric prose (transcribed from sketches) produces poor judge calibration in v1 dogfood | MED | LOW | Locked decision: refine in dogfood, not in spec. Add a memory entry citing this expectation. |
| Autoresearch lane registration touches files that land in main concurrently → merge conflict | LOW | LOW | Tag `autoresearch-v1-baseline` at end of A; any concurrent main work rebases against the tag, not against Bundle B in flight. |
| Decoupling stubs (`_NoTier`, `_NoWorkspace`) hide a real API expectation, causing silent miss-behavior | LOW | MED | Each stub method is a no-op that *returns the same type* freddy expects. Add asserts in tests that confirm "tier always allows" + "workspace store is no-op". |
| `tests/test_tool_catalog.py` was written against a different shape than freddy's current catalog | LOW | LOW | Open the test first at A.1; reconcile shape before porting (cheap diff). |

---

## 8. Open / deferred decisions

| # | Decision | Defer to | Note |
|---|---|---|---|
| 1 | Whether to migrate gofreddy's existing CLI commands (`detect`, `evaluate`, `competitive`, `trends`) to use AgentLoop | Follow-up branch | Out of scope here — Bundle A delivers the foundation; migration is a separate, optional pass. |
| 2 | Bundle G — service-layer ports (`src/search/service.py`, `src/seo/service.py`, `src/competitive/brief.py`, `src/fraud/service.py`, `src/deepfake/service.py`, `src/publishing/service.py`) | Next branch (`feat/service-layer-port`) | Largest deferred work from the round-2 survey. ~3K LOC. Recommend starting with `src/search/service.py` (most-impactful single port) or `src/deepfake/service.py` (smallest, fastest momentum win). |
| 3 | Bundle N — `feedback_loop/` (top-level Gemini-driven self-improvement loop) | Re-evaluate after Bundle G lands | Round 1 said skip; round 2 disagreed. Defer until we can see whether gofreddy's existing `judges/` + `events.py` + `agent_calls.py` already cover the same ground. |
| 4 | Bundle M — env-var documentation hygiene | Separate small PR (`chore/ops-hygiene`) | 25+ undocumented autoresearch env vars in gofreddy code. Touched-but-not-comprehensively during B.5. |
| 5 | Bundle K — backport freddy's harness convergence improvements (escalation tracking, frozen-judge backup, convergence logic) | Follow-up branch after current harness work stabilises | gofreddy's harness has been actively iterated since the fork; may have intentionally diverged. |
| 6 | Bundle O — extract API-route business logic incrementally | Each follow-up branch that touches the relevant surface | The single most-relevant block (`routers/agent.py:_build_per_request_agent`) is already cited in A.7's port-source table. Other extractions ride with their domains. |
| 7 | Bundle P — backport ~14 freddy fixes since fork (evaluation hardening + autoresearch pipeline repair) | Separate small `chore/freddy-fix-backport` PR | Parallel-safe with this branch; orthogonal to the port. Cherry-picks. |
| 8 | Bundle Q — harness track scope decision (6→3 was deliberate; document or restore?) | Separate `docs/harness-scope-clarification` PR | Recommended: document the reduction explicitly in `harness/README.md`. |
| 9 | Bundle R — caller-level SDK feature exposure (Gemini Batches/caching, OpenAI reasoning_effort, httpx limits per service) | `feat/sdk-feature-exposure-pass` follow-up | Performance pass; aggregate M effort. |
| 10 | Bundle S — agency-frontend deployment model (Option A: CLI-served local server + file reads, vs B: persistent backend, vs C: hybrid) | Strategic open decision; shapes future scope | Recommended: A. Affects whether `sse-starlette` + FastAPI return as deps. |
| 11 | Whether to publish a public Tool API beyond what's needed internally | Post-Bundle B | The catalog is internal-only by default. Re-evaluate after Bundle B lands. |

---

## 9. References

- **Inventory:** `docs/plans/2026-04-26-001-fred-port-gaps-inventory.md`
- **Marketing-audit design (locks 4-agent partition):** `docs/plans/2026-04-23-002-marketing-audit-lhr-design.md`
- **Audit-engine implementation design:** `docs/plans/2026-04-24-003-audit-engine-implementation-design.md`
- **Audit pipeline plan (R3, R22):** `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`
- **Source-of-truth commit:** `freddy` @ `50602a2`
- **Target base:** `gofreddy/main` @ `feaacf7`
