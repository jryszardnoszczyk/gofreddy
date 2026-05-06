---
title: "Marketing Audit v3 fusion roadmap (autoresearch lane registration)"
type: roadmap
status: dormant-v3
date: 2026-04-24
deepened: 2026-04-24
deferred: 2026-04-30
renamed: 2026-04-30 (was `2026-04-24-005-feat-audit-engine-fusion-plan.md`)
origin: docs/brainstorms/2026-04-24-audit-engine-fusion-requirements.md
trigger: ≥20 paid audits + 5/week steady-state per LHR §v3 pre-mortem
active-counterpart: docs/plans/2026-05-06-001-marketing-audit-v1-master-plan.md
v1-content-absorbed-into: docs/plans/2026-05-06-001-marketing-audit-v1-master-plan.md
v1-content-absorbed: 2026-05-06
---

> **🔖 v1 CONTENT ABSORBED 2026-05-06.** v1-relevant content (Unit 17 LaneSpec wiring, Unit 18 manifest enforcement, fusion's lineage shape, custom_score/validate callable patterns) folded into [`2026-05-06-001-marketing-audit-v1-master-plan.md`](2026-05-06-001-marketing-audit-v1-master-plan.md). The active-counterpart pointer was updated from the old framework plan to the new master plan. This roadmap remains for v3 trigger reference (≥20 paid audits + 5/week).

> **⚠ STATUS — DEFERRED TO v3 (2026-04-30 review).**
>
> This plan ships autoresearch fusion as v1 work. Re-review against the LHR
> design lock (`docs/plans/2026-04-23-002-marketing-audit-lhr-design.md`)
> determined this **directly contradicts** the LHR pressure-test, which
> stages this work as **v1 → v2 → v3** with autoresearch fusion deferred
> until **20+ paid audits + 5/week steady-state**. LHR §v3 pre-mortem:
> "v3 only earns its keep at >5 audits/week steady state. Below that,
> manual prompt tuning is cheaper than evolution."
>
> Three additional reversions caught:
> 1. Reverts LHR's locked **4 broad agents** → 7 narrow agents (without
>    addressing LHR's pressure-test rationale).
> 2. Drops the **Claude Agent SDK + MCP cached-tool layer** from the
>    original plan (`2026-04-20-002`); the fusion plan's Stage 2 has no
>    specified tool-access path for the ~80-130 of 149 lenses that
>    require provider tools or web fetches.
> 3. Retains the original 9-section `ReportSection` Literal instead of
>    the catalog-locked **11 Marketing Areas** (`2026-04-22-005`).
>
> **This file is preserved as v3 reference** — the autoresearch fusion
> design here is correct work for v3 once 20+ audits + 5/week justifies
> it. Do not implement from this plan.
>
> **The authoritative v1 plan is** `docs/plans/2026-04-30-001-marketing-audit-v1-pipeline-plan.md`.
>
> See `docs/plans/2026-04-30-001-...` §"Why this replaces 2026-04-24-005"
> for the evidence-based decision narrative.

> **2026-04-30 cross-plan review against harness_fixer lane plan**
> (`/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.worktrees/harness-fixer-decisions/docs/plans/2026-04-30-001-feat-harness-fixer-autoresearch-lane-plan.md`)
> surfaced 10 cross-pollination items, all LOCKED 2026-04-30 by JR
> after triage of the 3 PROPOSAL items (penalty terms / Bernoulli
> replay / section markers MA-1..8). All 10 items are scheduled to
> fold into Units 16 + 17 + 18 + Operational Notes when v3 trigger
> fires (≥20 audits + 5/week steady-state). See §"Cross-pollination
> from harness_fixer (2026-04-30)" below for the itemized fold-in list.

# Marketing Audit engine + autoresearch fusion v1

## Overview

Implementation plan for gofreddy's v1 Marketing Audit engine, fused with `autoresearch/` as the **5th workflow lane** (alongside geo, competitive, monitoring, storyboard; `core` is the 6th non-workflow lane in `lane_runtime.LANES`, used for autoresearch-internal evolve targets, not customer workflows). The audit pipeline runs as **agentic multi-session** `claude -p` CLI subprocesses (≥13 distinct invocations per audit chained via filesystem state — distinct from the single-session `--max-turns` pattern the existing 4 lanes use; see Key Decision §Multi-session orchestration), subscription-billed, no Python SDK. It reads a frozen 149-lens content catalog and self-improves across generations via the autoresearch evolve loop mutating orchestration (stage prompts, lens dispatch, batching, skip conditions). V1 ships as a thin cut — paid audit core + free AI Visibility Scan + 4 attach commands + manual invoicing — optimized for validating conversion (≥2/10 paid audits convert to $15K+ engagements in 60d) before expanding.

**Target ship time:** ~7–9 weeks foundation through first paying audit, ~9–11 weeks including full Bundle E autoresearch loop. (Updated +1 week from prior estimate after rolling back Worker / Unit 16 / attach-ads simplifications and adding R2DocumentStorage, INPUT_HASH plumbing, --gate-status + verify-lineage flags, audit-start preflight.)

## Problem Frame

JR runs a boutique marketing agency. The bottleneck on closing $15K+/mo retainer engagements is a credible opening pitch — prospects need to see depth before trusting the next sales conversation. Hand-producing that depth doesn't scale; generic audits are commodity and don't differentiate.

The bet: a paid $1,000 marketing audit serves as the engagement-anchor lead magnet for $15K+ retainers (credited back on signing within 60 days). A free AI Visibility Scan serves as top-of-funnel to qualify prospects. Both are produced by the same underlying pipeline at different depth settings. Audit depth is defined by the locked 149-lens catalog; self-improvement is the moat that makes audit quality compound over time.

See origin: `docs/brainstorms/2026-04-24-audit-engine-fusion-requirements.md` §Problem Frame.

## Requirements Trace

This plan implements v1 scope against origin requirements:

- **R1–R6** — Commercial flow (free scan, $1K paid audit, two-call model, HTML+PDF deliverable, UUID4-suffix URL slugs)
- **R4, R5, R25** — Operational gates, payment ledger, walkthrough survey leading indicator
- **R7–R12, R26** — Audit pipeline (6 stages, 149-lens catalog, 4 attach commands, cost ceilings, 3-tier proposal, findings schema, deliverable IA)
- **R13–R20, R27, R28** — Self-improving loop (lane-head variant runtime, externalized prompts, offline evolution, evolve_lock mutex, MA-1..MA-8 gradient rubric, anti-Goodhart, engagement judge, evaluator pin, composite fitness, orchestration mutation space)
- **R21–R24** — Data, safety, hygiene (local-first with git-split, owned-provider first, retention, PII hygiene)
- **R29** — Subscription-window SLA (≤50% of 5h window per audit, soft-warn at 40%)

## Scope Boundaries

Per origin doc Scope Boundaries — v1 **explicitly does not ship**:

- Stripe Checkout auto-fire on webhook (payment manual via `mark-paid` + `payments.jsonl` ledger)
- Fireflies webhooks (sales + walkthrough transcripts uploaded manually if needed)
- Slack lead-notification integration
- Capability-registry pricing engine (Stage 4 uses fixed pricing anchors in prompt)
- 5 of 9 attach commands: `attach-esp`, `attach-survey`, `attach-assets`, `attach-demo`, `attach-crm`
- Web UI / dashboard (CLI-only)
- Multi-tenant / white-label
- Outbound prospecting
- Post-sign delivery execution
- Free-tier full audits (only $1–2 scan is free)
- 3-business-day SLA enforcement
- Engagement-invoice credit-note accounting (manual)
- Auto-firing the full paid audit pipeline on form submission (scan still auto-runs per R1)
- Any RAL-style generic runtime (`docs/plans/2026-04-23-004-ral-runtime-design.md` is informational only)

## Context & Research

### Relevant Code and Patterns

**Existing `src/audit/` (feat/fixture-infrastructure branch, 14 files — NOT on main):**

- `src/audit/agent_models.py` (290 lines) — Pydantic `SubSignal`, `ParentFinding`, `AgentOutput`, `HealthScore`, `SectionScoreBreakdown`, `ReportSection` Literal. Matches R12 frozen schema exactly. **Treat as near-frozen content substrate.**
- `src/audit/checkpointing.py` (102 lines) — `write_atomic`, `read_json`, `write_json`, `atomic_update`. Thin, stdlib-only, explicitly no cross-process lock (v1 serializes at worker level per LHR D3).
- `src/audit/preflight/runner.py` (136 lines) — Stage-1a scaffold with `PreflightConfig`, `PreflightResult`, asyncio fan-out with per-check timeouts.
- `src/audit/preflight/checks/{dns,wellknown,schema,badges,headers,social,assets,tooling}.py` — 8 stubs; `dns.py` (128 lines with real dnspython) + `wellknown.py` (154 lines functional) are production-ready, other 6 return `{"implemented": False}`.
- `src/audit/__init__.py` — 22 lines, docstring only.
- `tests/audit/test_agent_models.py`, `tests/audit/test_checkpointing.py` — existing test coverage.

**Autoresearch primitives for direct reuse (post-2026-04-27 lane-registry refactor):**

- `autoresearch/lane_registry.py` (243 LoC) — **single source of truth** for per-lane data + 5 divergent-behavior callable hooks (`custom_mutate / custom_score / custom_validate / custom_promote / custom_objective_score_from_entry`). Marketing_audit registers as one `LaneSpec` entry in `LANES` (Unit 17). The refactor consolidated 24 hardcoded dispatch sites; `WORKFLOW_PREFIXES`, `DELIVERABLES`, `_INTERMEDIATE_ARTIFACTS`, `DOMAIN_FILENAMES`, `STRUCTURAL_DOC_FACTS`, `STRUCTURAL_GATE_FUNCTIONS`, `_DOMAIN_CRITERIA` (and `lane_paths.WORKFLOW_PREFIXES`, `lane_runtime` lane list, `evolve.all_lane_names()`, `frontier` LANES/DOMAINS, `evaluate_variant` DELIVERABLES/_INTERMEDIATE_ARTIFACTS, `regen_program_docs.DOMAIN_FILENAMES`, `program_prescription_critic.DOMAINS`, `src/evaluation/service._DOMAIN_CRITERIA`/`_DOMAIN_PREFIXES`, `src/evaluation/structural` STRUCTURAL_*) all derive automatically from `LANES`. Adding marketing_audit's LaneSpec makes them all pick it up — **no per-substrate edit required** for any of those sites. Shared utilities at `:217-242` (`file_hash`, `compute_manifest`, `verify_manifest`) are what Unit 18's `marketing_audit_validate` calls. The `_assert_models_literal_matches()` callable at `:202-214` enforces `src/evaluation/models.py:160` Literal stays in sync with `workflow_lane_names()` (Unit 15 + 17 honor this).
- `autoresearch/events.py` — `log_event(kind, **data)` + `read_events(kind, path)`. 98-line module, per-write exclusive flock, 100 MB rotation. Raises `EventLogCorruption` on malformed JSON. **Direct-import fit**; needs `path=` param on `log_event` (currently only on `read_events`) for per-audit local log. ~10 LOC + 2 tests (thread `path` through `_ensure_parent` / `_maybe_rotate` / append-with-flock; decide rotation policy when `path=` overrides default `EVENTS_LOG`).
- `autoresearch/runtime_bootstrap.py` — 21-line execv shim. Use `lane_runtime.resolve_runtime_dir(archive_dir)` to resolve the materialized variant directory; skip the `os.execv` swap (doesn't match audit's in-process model).
- `autoresearch/lane_runtime.py` — `LANES` tuple now `_LANE_SPECS` derived from `lane_registry.LANES`; `ensure_materialized_runtime()` at `:117`, `current.json` manifest writer at `:157–159`. Per-lane file copy loop at `:147`.
- `autoresearch/evolve.py` — `_build_meta_command` (Pattern B subprocess), env sanitization (13-key allowlist), workflow lane iteration via `lane_registry.all_lane_names()` / `workflow_lane_names()`. **Custom-callable invocation sites:** `custom_validate` at `:1597` (called as `(variant_dir, parent) -> bool`, fires AFTER meta-mutate, BEFORE scoring; False discards the variant), `custom_score` at `:1609` (called as `(config, str(variant_dir), parent_id)`, return value ignored — callable owns writing scores.json + lineage updates), `custom_promote` at `:1740` (called as `(archive_dir: str, variant_id: str, lane: str) -> bool`, gates `cmd_promote`).
- `autoresearch/evaluate_variant.py` — `_has_deliverables` consumes `lane_registry.DELIVERABLES` (registry-derived; no extension needed). **Hard L1 gate at `:584`** (`program_path = variant_dir / "programs" / f"{domain}-session.md"`) iterates registry-derived `DOMAINS` and requires the marker file per workflow lane — Unit 17 ships `programs/marketing_audit-session.md` to satisfy this. `_INNER_PHASE_TAGS` frozenset at `:760` is the **closed allowlist** for inner pass-rate counting (Divergence Point #6 — Unit 17 extends this in-place with marketing_audit's stage tags). `_score_variant_search` (substrate scorer that custom_score replaces) and the suite-level aggregator at `:1180-1202` (`mean_inner_pass_rate / mean_outer_pass_rate / mean_pass_rate_delta`) are **bypassed** for marketing_audit because `custom_score` short-circuits the substrate path; Unit 16's `marketing_audit_score` must independently emit those telemetry keys into `search_metrics`.
- `autoresearch/frontier.py` — `LANES`/`DOMAINS` derived from `lane_registry` at `:21-22`; `objective_score` (`:76–86`) calls `default_objective_score_from_entry`, which delegates to `LaneSpec.custom_objective_score_from_entry(entry)` if set (Unit 16 wires marketing_audit's). `best_variant_in_lane` at `:102`.
- `autoresearch/select_parent.py:97` — `pstdev(children_deltas) < 0.01` plateau check; reads from each lane's `default_objective_score_from_entry` output. Divergence Point #1 picked option (c): Unit 16's `marketing_audit_score` normalizes `weighted_rubric_raw / 10.0` → output stays in `[0, 1]` space, threshold stays calibrated, **no select_parent.py edit**.
- `autoresearch/compute_metrics.py` — `_run_claude_json` at `:224–253` (Pattern C short-shot JSON subprocess), `compute_generation_metrics` at `:91` (lane-agnostic, takes `lane` param — works as-is for marketing_audit). **No `total_cost_usd` parsing anywhere** — new capability required (Unit 4).
- `autoresearch/program_prescription_critic.py:97–117` — Pattern C short-shot, prescription critic. (`DOMAINS` at `:46` is `workflow_lane_names()` — registry-derived; no edit needed.)
- `autoresearch/critique_manifest.py` — SHA256 hash freeze for autoresearch internals via `inspect.getsource(getattr(session_evaluator, FROZEN_SYMBOL))` symbol-introspection across `FROZEN_SYMBOLS = ('DEFAULT_PASS_THRESHOLD', 'HARD_FAIL_THRESHOLD', 'GRADIENT_CRITIQUE_TEMPLATE', 'build_critique_prompt', 'compute_decision_threshold')`. **Note:** this mechanism hashes Python symbols, NOT arbitrary file paths. R17 MA-1..MA-8 manifest uses **`lane_registry.compute_manifest` + `verify_manifest` (file-bytes hashing) at `:217-242`** instead — Unit 18 wires these via `custom_validate`. No new manifest module needed.

**Harness primitives for direct reuse** (re-anchored 2026-04-29 against current main; harness shifted post-PR-#37):

- `harness/sessions.py:56` `SessionsFile` (lines 56-103 incl. `__post_init__`/`get`/`all`/`begin`/`finish`/`_write` helpers). Frozen `SessionRecord` at `:46`. threading.Lock for atomic writes. Direct-import fit.
- `harness/sessions.py:129` `claude_session_jsonl(wt_path, session_id)` — derives claude projects path via `str(wt_path).replace("/", "-")`. Audit uses `clients/<slug>/audit/<audit_id>/` as equivalent of `wt_path`.
- `harness/run.py:197-220` — `_viable_resume_id(record, wt_path) -> str | None`. Free function, importable. Pattern handles "claude silent-hung before first token" case.
- `harness/run.py:90` flag definition `graceful_stop_requested: bool = False` + `graceful_stop_reason: str = ""` on the `RunState` dataclass. Read-checked at 9 loop points (`:523, :597, :627, :722, :744, :848, :1002, :1017`); set-True at 3 sites (`:797, :1156, :1228`). Not SIGTERM-hooked on main process (only on worktree cleanup).
- `harness/worktree.py:229-245` — `cleanup(wt)` coupled to `Worktree` dataclass. **Don't direct-import**; port the SIGTERM→5s→SIGKILL escalation pattern (`_terminate_backend:349-363`, `_kill_port:366-379`).
- `harness/worktree.py:396-414` — `_install_exit_handlers()` registers atexit + SIGTERM + SIGINT → `os._exit(143)`. Portable pattern.
- `harness/engine.py:228-272` — `_build_claude_cmd` Pattern A (long-form streaming with resume). Specifies `--output-format stream-json --include-partial-messages --verbose --resume <sid>` or `--session-id <sid>`, `--dangerously-skip-permissions`.
- `harness/engine.py:275` `parse_rate_limit(log_path) -> RateLimitHit | None` (function body extends through ~`:330`). Reads stream-json events for `"type": "rate_limit_event"`. Portable for R10/R29 subscription-window tracking.

**Customer-facing prior art:**

- `src/competitive/pdf.py:1–80` — `render_brief_pdf(brief_markdown, client_name) -> bytes` with `markdown` → HTML, `nh3.clean()` sanitization (allowed tags/attrs at `:14–30`), Jinja2 `PackageLoader`, WeasyPrint `_safe_url_fetcher` SSRF guard at `:33–40` (blocks non-data-URI URLs), `asyncio.Semaphore(2)` for CPU-bound concurrency. **Directly portable** — copy skeleton to `src/audit/render.py`, swap template path to `src/audit/templates/`.
- `src/storage/r2_storage.py` + `src/storage/r2_media_storage.py` — `aioboto3`-backed R2 upload infrastructure. `VideoStorage` Protocol is domain-specific but the client factory + key validation + upload/download/delete/list surface is reusable.
- `src/common/cost_recorder.py` (102 lines) — provider-call JSONL logger (Gemini + 3rd-party APIs). **No Claude rate table**; no `extract_claude_usage` helper. Bundle A layer's `cost_ledger.py` on top of it for Claude-specific parsing + per-stage gate.
- `src/common/url_validation.py` — URL validation primitives (exists; verify exact surface during Unit 13).

**Deps in `pyproject.toml`** (verified present): `weasyprint>=62.0`, `markdown>=3.5.0`, `nh3>=0.2.14`, `jinja2>=3.1.0`, `PyYAML>=6.0`, `typer>=0.12.0`, `pydantic>=2.6.0`, `aioboto3>=13.0.0`, `httpx`, `tenacity`, `aiolimiter`, `asyncpg`, `fastapi>=0.115.0`. **No `claude-agent-sdk` dependency** — confirmed. **Python `>=3.13,<3.14`**, uv-managed.

### Institutional Learnings

No `docs/solutions/` directory exists. Institutional knowledge lives in `docs/plans/` and `autoresearch/GAPS.md` + inline comments. Relevant findings:

- **`docs/plans/2026-04-24-001-audit-pipeline-research-record.md`** (860 lines) — yesterday's hand-off doc with file:line citations for every borrowable primitive. **Caveat: written before the CLI-subprocess decision locked**; any citation of `ClaudeSDKClient`, `max_budget_usd`, or SDK hooks needs reinterpretation.
- **`docs/plans/2026-04-23-002-marketing-audit-lhr-design.md`** (469 lines) — pressure-test-revised design. Locks D1 CLI-only v1, D2 mandatory ship gate, D3 serialize at worker (no per-audit worktrees). Recommends starting with 4 broad Stage-2 agents; R28 mutation space allows evolve loop to propose alternatives.
- **`autoresearch/GAPS.md`** — 4 P0 gaps in-flight (Gap 2: meta-agent blind to eval traces; Gap 6: `regression_floor` never enforced; Gap 18: single-run variance; Gap 30: L1 import check). Reinforces R20 pin rationale.
- **`autoresearch/deep-research/cluster-5-autoresearch.md`** F5.3 — honor-system gap in two-evaluator architecture. Mitigation: SHA256-hash-freeze MA-1..MA-8 rubric + judge prompts via existing `autoresearch/critique_manifest.py`.
- **`autoresearch/deep-research/cluster-5-autoresearch.md`** F5.4 — inner-vs-outer correlation telemetry gap. Ship ~30 LOC before first evolve run to detect evaluator drift before holdout failure.
- **`docs/plans/2026-04-23-006-holdout-v1-composition-expansion.md`** — holdout-v1 shipped as 16 fixtures (4 per existing lane) at `~/.config/gofreddy/holdouts/holdout-v1.json`. Marketing_audit holdout authoring deferred until 5+ real audits exist (Bundle 10 §7.6).

### External References

External research not run — the origin doc + design doc 003 + research record 001 + pressure-tested LHR design 2026-04-23-002 already cover the external landscape. Key explicit references:

- `docs/plans/2026-04-24-003-audit-engine-implementation-design.md` (1426 lines) — architecture reference. §2 12 locked decisions, §3 module map, §4–§8 per-bundle detail, §11 JR-owned open decisions.
- `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` (2235 lines) — 149-lens content authority (frozen v2 2026-04-23).
- `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md` (641 lines) — ranking + cutoff (selector).
- `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` (1607 lines) — original product spec; **line 416 `claude-agent-sdk>=0.1.0` explicitly retired** per origin doc Key Decision.

## Key Technical Decisions

- **Execution model: direct `claude -p` CLI subprocess, subscription-billed, no Python SDK.** Reuses the per-invocation envelope shape from 4 existing sites (`harness/engine.py:240`, `autoresearch/compute_metrics.py:280`, `autoresearch/evolve.py:632`, `autoresearch/program_prescription_critic.py:167`) — same `--output-format json`, same `total_cost_usd` parsing, same env sanitization. Subscription billing (5h usage windows) traded for no API-key management and no per-token dollar accounting at the CLI layer. **Note:** the per-invocation envelope is reused; the *orchestration* pattern (chained multi-session, see next decision) is net-new. (see origin: `docs/brainstorms/2026-04-24-audit-engine-fusion-requirements.md` Key Decision §Execution model)

- **Multi-session orchestration is a NEW pattern (not multi-turn).** "Multi-turn" describes ONE `claude -p` session with many turns (the harness's `--max-turns 100` agentic mode + autoresearch's `_build_meta_command` are both single-session multi-turn). The audit pipeline is structurally different: 6 stages × ≥7 lens agents in Stage 2 = ≥13 distinct `claude -p` invocations per audit, each with its own `session_id`, each handing context to the next via filesystem state (`brief.md`, `signals.json`, `stage2_subsignals/L*_*.json`, `synthesis.md`, `proposal.md`). This pattern does not exist in autoresearch or harness today — the audit engine is the first instance. Three derived consequences: **(a) Cross-session input fingerprints required.** Each Stage-N session's first-turn prompt must include a deterministic SHA256 of consumed inputs (e.g., Stage 2's prompt header includes `INPUT_HASH=sha256(brief.md + signals.json + lenses_assigned.yaml)`) so cross-stage poisoning (Stage 1b emits a vertical mis-classification → Stages 2–4 silently produce wrong-vertical output) is detectable post-hoc by re-deriving the hash from a known-good input. **(b) Per-lens resume granularity needs an explicit write-ahead-log primitive.** Resuming a 21-lens agent mid-flight (already 11 lenses written) has no precedent in harness (which is whole-task-granular). The atomic-per-lens write pattern (`stage2_subsignals/L<id>_<slug>.json` + `completed_lenses: list[str]` in `AuditState`, written before each lens-call returns) IS the WAL — Unit 10 owns the implementation. **(c) Stage 2's 7-parallel-sessions vs 1-long-session question is explicit.** v1 ships 7 parallel agents per the design doc (justification: per-lens resume + per-agent token-window isolation + parallel wall-clock); R28 mutation space allows the evolve loop to propose 1-long-session or N-broad-agents alternatives if Stage 2 cost dominates. Locked in v1, evolvable post-v1. (see origin: §Architecture, §Stages 0-6 contract)

- **Content/orchestration split is the fusion contract.** 149-lens catalog + SubSignal/ParentFinding Pydantic schemas are frozen content; stage prompts + lens dispatch + batching + skip conditions + synthesis logic are evolvable orchestration. Anti-Goodhart boundary: meta-agent cannot change what it's scored on, only how it produces the output. (see origin: Key Decisions §Content/orchestration split)

- **Marketing_audit is a hybrid object: a lane-tracked variant-producer AND a paid customer-facing service.** The variant-production surface (Stages 0-6 driven by `claude -p` against a frozen catalog + evolvable orchestration) IS the 5th-lane shape — peer to geo/competitive/monitoring/storyboard. The live wrapper (`freddy audit run`) is NOT a peer-of-peer-lane wrapper: it adds commercial flow + 3 human gates + payment ledger + R2 publish + T+60d feedback closure — a net-new object class that none of the 4 existing lanes have. Evolve wrapper (`autoresearch evolve --lane marketing_audit`) IS a peer to other lanes' evolve runs. Same `claude -p` subprocess + same stage prompts + same catalog drives both wrappers' variant-production. The asymmetry is named honestly here so future readers understand "5th lane" applies to the variant-production surface, not to the customer-flow surface — see line 155 fidelity-contract asymmetry for the operational consequence. (see origin: §Architecture)

- **Reuse harness + autoresearch primitives first.** Build audit-specific code only (stage runners, lens dispatch, cache-backed provider tools, preflight, render, publish, CLI). Direct-import or extend-in-place for session tracking, event logging, cost tracking, resume, cleanup, graceful-stop, prompt-loader, evolve lock, rubric scoring. Coupling risk mitigated by R20 (pin evaluator at ship). (see origin: Key Decisions §Autoresearch + harness primitives first)

- **Customer-facing lane = first of its kind.** Pre-promotion smoke-test required before any new variant becomes lane-head. Runs against one holdout fixture; MA-1..MA-8 scores must not regress vs current head. Uses Plan B MVP holdout-v1 infra. (see origin: Key Decisions §Customer-facing lane risk class)

- **Cost-weighted fitness function.** `fitness = weighted_rubric_score − cost_penalty × normalized_token_cost − latency_penalty × normalized_wall_clock`. MA-1..MA-8 contribute rubric score per individual weights (engagement weight = 0 for first 3 generations per R19, ramps up as T+60d data accumulates). Token efficiency is first-class optimization target, not a constraint. (see origin: R27)

- **Subscription-window SLA (R29).** One paid audit consumes ≤50% of a 5h window. Soft-warn at 40% (Slack-alerts JR but proceeds), hard breaker at 50% (halts Stage 2+ fan-out, sets `pause_reason=subscription_window_ceiling`, resumes next window via `freddy audit resume`). Protects multi-audit throughput on subscription billing.

- **`configs/audit/lenses.yaml` is a JR-coordinated content work-stream, not greenfield code.** ~4–6h per entry × ~198 entries = multi-day task. Python loader is trivial (~50 LOC); the content transcription is the real cost. Decouple this from Bundle B code work so Stage-2 fan-out can be tested against a small subset of lenses before the full catalog lands.

- **SubSignal failures score as `null/excluded`, not `0`.** Zero compounds through geometric mean and tanks the domain score for one bad block. `null` is excluded from the geomean, counted separately in `gap_report.md`. (institutional learning from cluster-5 F5.3)

- **`asyncio.gather(return_exceptions=True)`, not `TaskGroup`.** TaskGroup is fail-fast by default — one lens exception kills sibling lens tasks. `return_exceptions=True` preserves partial completion. (institutional learning from LHR design §v1)

- **`src/audit/claude_subprocess.py` ships three factories** for the three CLI invocation patterns already in the codebase:
  - `build_cmd_streaming(prompt, model, session_id, resume=False)` — Pattern A, Stage 2 lens agents (multi-turn, filesystem-writing)
  - `build_cmd_meta(model, max_turns, allowed_tools)` — Pattern B, Stage 1b brief-gen, Stage 3 synthesis, Stage 4 proposal (one-shot but long-form, writes files)
  - `build_cmd_short_json(prompt, model)` — Pattern C, critic calls, redaction pass per R24, MA-1..MA-8 rubric judges (short, returns JSON envelope)

- **Start Stage-2 with 7 lens agents per design doc**; let the evolve loop propose alternatives via R28 mutation space. The LHR design's "4 broad agents" advice is valid but R28 subsumes it — structure is evolvable, not a v1 lock-in.

- **Lens-dispatch coverage invariant (anti-Goodhart at dispatch level).** Frozen content (Pydantic schemas + catalog) closes the *schema* gaming surface but not the *dispatch* gaming surface. MA-5 (Bundle applicability) and MA-8 (Data-gap recalibration) could be gamed by narrowing lens dispatch — fewer lenses fire = fewer gap-flags = inflated MA-8; dispatched-bundles-match-detection is trivially true if we only dispatch easy-match bundles. Mitigation: Stage 1b emits an auditable **dispatch rationale log** alongside SubSignals; MA-5 and MA-8 judges score *the decision to skip* against that log, not just the results of lenses that fired. Minimum-coverage floor: every audit must dispatch ≥80% of always-on lenses unless Phase-0 signals justify skip per logged rule.

- **Live-wrapper contract differs from evolve-wrapper contract.** The "shared lane program" framing (marketing_audit is the 5th lane) is structurally accurate but under-states a fidelity-contract asymmetry: (a) live path requires deterministic reproducibility from a frozen variant snapshot — a promoted variant must be live-safe (no net-new tool surface, no net-new external hostname); (b) cost-penalty term in composite fitness (R27) has a floor below which it stops contributing, preventing token-optimization from cannibalizing customer-facing deliverable quality (a $5 token saving that degrades MA-6 polish is a bad trade on a $1K deliverable); (c) any variant promotion must pass a "live-safe" pre-check in addition to the pre-promotion smoke-test (Unit 18). This decision is the real content of "customer-facing lane is new risk class."

- **Payment ledger compound idempotency.** The `payments.jsonl` ledger is **operator-attested** (not cryptographically non-repudiable) in v1. Idempotency key is `(audit_id, normalized_ref)` compound — not `ref` alone. `normalized_ref = lower(trim(ref))` so typo cases collapse correctly. Empty/whitespace ref is rejected, not defaulted. Duplicate attempts append their own event type `mark-paid-duplicate-attempted` to the ledger, preserving non-repudiation of the attempt (not just the first successful write). Future Stripe integration (v2) signs each entry with HMAC keyed on server secret + chain-hash of prior entry for tamper-evidence; pre-design in v1 by including `chain_hash_sha256` field in schema but leaving null until v2 signing ships. Related: `record-engagement` requires a `--ref <invoice-id-or-contract-id>` cross-referencing payments.jsonl so engagement signal is auditable against actual commercial records.

- **Pre-promotion smoke-test fail-closed policy: X.a is the v1 default (locked).** Marketing_audit holdout fixtures do not exist at v1 ship time; Bundle 10 §7.6 defers them until "5+ real audits exist." Therefore: **No variant promotion permitted in v1.** Lane ships without evolve-loop-driven variant rotation. Manual head-selection only — JR commits a single variant before first paying audit and the lane-head stays put for the entire 10-audit measurement window. The pre-promotion smoke-test infrastructure (Unit 18) ships as plumbing for v1.5; the gate enforces nothing in v1 because no promotion happens. X.b (smoke-test on cross-lane fixtures + `--manual-promote` flag) is **rejected** as a design flaw — passes MA-5/MA-6 degenerate cases and provides false assurance on the exact regression surface we need to catch. Missing fixture or smoke-test failure → **fail-closed** (halt promotion), never silent-skip. Fixtures land post-audit-3 (with prospect consent — see Open Question §Reader-readability + holdout-fixture sourcing); v1.5 unlocks variant rotation once ≥1 fixture exists.

- **DELIVERABLES shape: flat tuple with judge-vs-publish discrimination split.** Migrate `DELIVERABLES` dict to uniform `tuple[str, ...]` (minimal blast radius — one consumer at `evaluate_variant.py:433`). Keep judge-vs-publish discrimination in the separate `_JUDGE_PRIMARY_DELIVERABLE` map (already present in `src/evaluation/service.py:49–56`). Accept that a future 3rd discriminator (e.g., analytics export, third-party distribution) forces a second migration toward a structured `{'primary', 'artifacts', 'analytics'}` dict. Deferred cost is ~half a day of one additional migration vs saving ~2 days now.

- **Execution model ResultMessage field semantics (Unit 3/4 correctness).** Claude CLI `--output-format json` envelope fields:
  - `total_cost_usd` — Anthropic's estimated API cost (populated on subscription too — no fallback-to-tokens math needed)
  - `duration_ms` — wall-clock including local tool execution (Bash, Read, Edit, WebFetch)
  - `duration_api_ms` — API-call-only time (the quantity that counts against the 5h subscription window)
  - `subtype` gates `result` field presence: `"success"` → read `result`; error subtypes → read `errors: string[]`
  - `usage.{input,output,cache_creation_input,cache_read_input}_tokens` — nested under `usage`
  - `num_turns` — top-level
  R29 subscription-window SLA uses `duration_api_ms` (not `duration_ms`) to avoid false positives on tool-heavy stages. Wall-clock `duration_ms` still logged for UX + graceful-stop wall-clock bound.

- **Claude CLI version pin.** `claude` Node binary is an external dependency not under repo version control. Unit 19 pins autoresearch but must also pin the `claude` CLI version (via a preflight assertion at audit start: fail fast if running CLI version ≠ pinned). If the CLI output format drifts (e.g., envelope field shape change), parse_result_message silently returns wrong values; pinning CLI version prevents that.

- **URL slug drops client-name prefix.** R6 origin doc specifies `reports.gofreddy.ai/<client-name>-<uuid4>/`. Competitive-confidentiality concern: the prefix advertises JR's engagement with a specific client to anyone scraping referrers or search engines. Change slug format to `reports.gofreddy.ai/<uuid4>/` (no prefix). Combined with `X-Robots-Tag: noindex` on deliverable responses + `Referrer-Policy: no-referrer` + `robots.txt` disallow-all, this closes the identity-leak surface. **This amends origin doc R1 + R6 slug specification** — a narrow, defensible deviation grounded in security review.

- **Engagement signal cross-validation.** `record-engagement` writes the sole ground-truth fitness input. Three validation rails: (a) requires `--ref <invoice-id-or-contract-id>` cross-referencing `payments.jsonl` — signal is auditable against commercial records; (b) fitness engagement judge emits `low_confidence=true` for entries recorded <24h after audit (likely test data) or >90d after audit (likely memory-based estimate); (c) amounts >$15K require separate JR-signed confirmation CLI flow (`--confirm-high-value`). `record-engagement --dry-run` prints intended lineage.jsonl change without writing.

- **Two distinct lineage files: `audits/lineage.jsonl` vs `autoresearch/archive/lineage.jsonl`.** These are SEPARATE concerns and must not be unified: (a) **`audits/lineage.jsonl`** — customer-facing audit record. One row per paying audit. Schema includes `audit_id, variant_id, client_slug, prospect_domain, published_at, engagement_recorded_at, engagement_signed_usd, ref, low_confidence, high_value_confirmed, walkthrough_survey`. Written by Stage 6 publish + `record-engagement` CLI. Consumed by engagement judge (Unit 18) at T+60d. Lives outside autoresearch tree. (b) **`autoresearch/archive/lineage.jsonl`** — variant lineage. One row per scored variant. Schema includes `id, lane, parent, scores, search_metrics, holdout_metrics, suite_versions, changed_files, campaign_ids, promotion_summary` (per existing `evaluate_variant._lineage_entry:1177-1249`). Written by autoresearch evolve loop. Consumed by frontier selection. Lives in autoresearch tree. **Join key: `audits/lineage.jsonl.variant_id == autoresearch/archive/lineage.jsonl.id`** — engagement signal flows from customer record into variant lineage via this join, computed in the engagement judge before writing the per-variant signal JSONL. Without this explicit split, the two paths drift; reviewers see "lineage.jsonl" referenced and can't tell which file is meant.

## Open Questions

### Resolved During Planning

- **Branch starting state for `src/audit/`.** Research-analyst confirmed `feat/fixture-infrastructure` has 14 files (agent_models.py, checkpointing.py, preflight scaffold); `main` is empty. Bundle A subsystem 1 (exceptions + state at commit `19a4778`) may have been reverted per working direction. **Resolution:** Unit 1 reconciles state at plan-execution start — merge `feat/fixture-infrastructure` into a new working branch, verify the 14 existing files against the plan's Bundle A file list, confirm `agent_models.py` + `checkpointing.py` + `preflight/runner.py` survive, proceed from that baseline.

- **`lane_paths.py` shim → registry derivation (resolved 2026-04-27).** The lane-registry refactor (`docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md`) replaced `lane_paths.LANES` + `WORKFLOW_PREFIXES` with derived re-exports from `autoresearch/lane_registry.LANES`. Marketing_audit's `LaneSpec.path_prefixes` field is the registration surface; no shim editing needed. Resolved.

- **4 vs 7 Stage-2 agents.** LHR design recommends 4 broad; design doc 003 specifies 7. **Resolution:** Start at 7 per design; R28 mutation space allows evolve to discover optimal batching. Not a lock-in.

- **Deliverable IA pattern.** R26 specifies consultant-memo: (1) executive summary + health score, (2) top-3 actions by cost-of-delay × effort-ratio, (3) findings by marketing area with severity weighting (collapsed HTML, expanded PDF), (4) proposal tiers, (5) methodology appendix. **Resolution:** Lock in Bundle C templates; no further product-level iteration needed.

- **Free scan implementation.** Unified with paid audit at `depth=scan` per origin Key Decisions. Same lane, same pipeline, parameterized. **Resolution:** Unit 14 CLI handles `--depth scan` vs `--depth full`.

- **DELIVERABLES dict migration.** **Superseded by lane-registry refactor (shipped 2026-04-27).** `lane_registry.DELIVERABLES` is already `dict[str, tuple[str, ...]]` derived from each `LaneSpec.deliverables` field (lane_registry.py:168). Consumer at `evaluate_variant.py:_has_deliverables` already iterates the tuple shape. Marketing_audit just sets `deliverables=("findings.md", "report.md", "report.json", "report.html", "report.pdf")` on its LaneSpec entry (Unit 17); the dict is auto-populated. No migration step needed.

- **L1 validation gate marker file.** `evaluate_variant.py:584` requires `programs/{domain}-session.md` exact path for every `DOMAINS` entry (now registry-derived from `LaneSpec.session_md_filename`). **Resolution:** Ship `autoresearch/archive/current_runtime/programs/marketing_audit-session.md` as a thin marker file pointing to `programs/marketing_audit/prompts/` subdirectory. Satisfies L1 without needing validator extension. Marker file is one of the 3 new autoresearch files in Bundle E.

### Deferred to Implementation

- **`configs/audit/lenses.yaml` transcription ownership + timeline.** Per origin doc Dependencies — ~4–6h per entry × ~198 entries = multi-day JR-coordinated task. Can partially proceed before the YAML is complete (Stage-2 fan-out can be tested against a minimal 10–20 lens subset). Full catalog required before Bundle E evolve runs have meaningful signal.

- **MA-1..MA-8 rubric prompt transcription (Unit 15 deliverable).** Each of the 8 criteria needs a ~50-100 LOC prompt template matching the quality bar of existing `_GEO_1..._GEO_8` in `src/evaluation/rubrics.py` (rubric anchors + scoring band examples per integer step + edge cases + JSON output schema). Estimate: ~2-4h per criterion × 8 = ~16-32 hours JR-coordinated content authoring. Embedded in the prompts: (a) MA-5 + MA-8 must score against Stage 1b's `dispatch_rationale.md` per anti-Goodhart Key Decision, not just dispatched-lens output; (b) MA-4 must surface token-count from variant context. The 8 prompt strings are SHA256-frozen via `marketing_audit_prompt_manifest.py` (Unit 18) so any post-ship rubric drift is caught by L1. Bundle D ships scaffolding + tests against placeholder prompts; rubric correctness is gated on the transcription, which is the v1 critical-path content dependency analogous to the 149-lens YAML. Partial transcription (e.g., MA-1+MA-3+MA-7 first, since they drive most of the deliverable quality signal) unblocks early evolve dry-runs against fixtures once fixtures exist.

- **Stage prompt + critic prompt transcription (Bundle B + Unit 18 deliverables).** Adjacent content-authoring dependency: `stage_1b_signals.md`, `stage_1c_brief.md`, `stage_2_lens_meta.md`, `stage_3_synthesis.md`, `stage_4_proposal.md`, `inner_loop_critic.md`, `stage_0_intake.md`, `stage_1a_preflight.md`. Each is ~100-200 LOC of structured agent guidance (role, objective, lens assignment for stage_2_lens_meta, rubric checklist, output contract). Estimate: ~4-8h per stage prompt × 8 = ~32-64 hours JR-coordinated. Stage prompts are also SHA256-frozen in the manifest so evolve loop mutations are explicit promotion events, not silent drift.

- **Total content-authoring critical path:** ~800-1200h (149-lens YAML) + ~16-32h (rubric prompts) + ~32-64h (stage prompts) = roughly **850-1300 hours of JR-coordinated content work** runs parallel to the ~7-9 weeks of code work. Stage-2 dev unblocks at 10-20 lenses + minimal stage prompts; Bundle E evolve runs gate on full catalog + full rubric prompts + holdout fixtures.

- **Autoresearch pin commit selection.** Per R20, pin at first ship. Planning-phase decision owned by JR; trivial to implement (add `.github/workflows/` CI check that verifies `autoresearch/` tree SHA matches the tagged commit). Target: `autoresearch-audit-stable-YYYYMMDD` tag format.

- **Fixed pricing anchors for Stage-4 proposal prompt.** Specific numbers for Fix-it / Build-it / Run-it tiers. JR-owned content decision; Stage-4 prompt file stays as a template until anchors land.

- **5 synthetic prospect fixtures for marketing_audit eval suite.** Research indicates this is deferred per Bundle 10 §7.6 until 5+ real audits exist. Bundle E can ship the lane registration + evolve_lock + engagement judge infrastructure before this lands; first evolve run waits on fixtures.

- **Cloudflare Worker deployment + R2 bucket + DNS.** Operator-side ops task. v1 ships **two Worker concerns split**: (a) **deliverable-serving Worker (v1)** — single-purpose ~20 LOC response-path mediator on reports.gofreddy.ai/* that injects `X-Robots-Tag: noindex` + `Referrer-Policy: no-referrer` + `X-Content-Type-Options: nosniff` + `Cache-Control: private, no-store`. Required because R2 cannot set arbitrary response headers at upload time; the noindex header is a security requirement (R6), not a nice-to-have. (b) **intake-form Worker (deferred to v1.5)** — handles scan form intake, rate-limits, SSRF guard, etc. Deferred because operator-fired scan via `freddy audit run --depth scan` covers v1 intake. JR-owned pre-Unit-13: R2 bucket creation, DNS for reports.gofreddy.ai, deliverable Worker deploy + R2 binding (or origin-proxy fallback). Intake-form Worker awaits 2/10 conversion gate.

- **Reader-readability + holdout-fixture sourcing (149-lens v1 ship).** Premise C from re-review: 149 always-on + 25 vertical + 10 geo + 5 segment + 9 Phase-0 = ~198 catalog entries × ~4-6h transcription = ~800-1200 hours JR-coordinated content authoring on the critical path. v1 keeps the full 149-lens scope (catalog is locked content authority — shrinking changes brand promise of "comprehensive 149-lens marketing audit"), but two open validations gate density/IA choices: (a) **Reader-readability validation** — has any human read a 30+ page marketing audit deliverable end-to-end? Decide: validate via dogfood read of fixture deliverable PDF before audit 1 ships, OR validate live with audit-1 prospect (with consent) and adjust IA between audit 1 and audit 5. (b) **Holdout-fixture sourcing** — Bundle 10 §7.6 defers fixtures until "5+ real audits exist." Decide: synthesize fixtures (faster but synthetic regression surface ≠ real-input variability) OR author fixtures from first 3 paying audits with prospect NDA + consent (slower but real-input distribution). Recommendation: live IA validation + consent-based fixture sourcing — collapses wait time and uses real-input variability the synthetic fixtures can't capture.

- **Claude subscription tier selection.** R29 50% ceiling assumes a single 5h window; if JR is on a higher tier (e.g., Team), the ceiling math scales. Defer sizing until first 5 dogfood audits produce real token-count data.

- **Exact Mermaid render strategy for HTML deliverable.** R26 mentions diagrams indirectly (severity visualization); no explicit Mermaid requirement. Defer — if Bundle C deliverable IA calls for diagrams, decide client-side JS render vs server-side PNG during implementation.

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

The audit engine is a native autoresearch lane with two wrappers around a shared lane program. The wrappers differ only in what they add around the 6-stage `claude -p` subprocess chain.

```mermaid
flowchart TB
  subgraph CONTENT["Frozen content substrate"]
    C1["docs/plans/2026-04-22-005<br/>149-lens catalog v2"]
    C2["docs/plans/2026-04-22-006<br/>lens ranking + cutoff"]
    C3["configs/audit/lenses.yaml<br/>(compiled runtime form)"]
    C4["src/audit/agent_models.py<br/>SubSignal + ParentFinding schemas"]
    C1 -. content authority .-> C3
    C2 -. selection rule .-> C3
  end

  subgraph LANE_PROGRAM["Shared lane program (src/audit/)"]
    LP["6-stage claude -p pipeline<br/>Stage 0: intake<br/>Stage 1a: deterministic preflight<br/>Stage 1b: signal detection<br/>Stage 1c: brief synthesis<br/>Stage 2: 7 parallel lens agents<br/>Stage 3: synthesis (SubSignal → ParentFinding)<br/>Stage 4: 3-tier proposal<br/>Stage 5: render HTML+PDF<br/>Stage 6: publish"]
  end

  subgraph LIVE["Live wrapper: freddy audit run"]
    L1[invoice + mark-paid + payments.jsonl]
    L2[3 human gates: intake, payment, publish]
    L3[R2 upload + Cloudflare Worker]
    L4[walkthrough-survey capture]
    L5[record-engagement at T+60d]
  end

  subgraph EVOLVE["Evolve wrapper: autoresearch evolve --lane marketing_audit"]
    E1[variant mutation per R28 mutation space]
    E2[fixture iteration]
    E3[auto-approve all gates]
    E4[MA-1..MA-8 rubric scoring]
    E5[pre-promotion smoke-test]
    E6[promote winner → lane-head]
  end

  subgraph AUTORESEARCH["autoresearch/"]
    A1["programs/marketing_audit-session.md<br/>(L1 marker file)"]
    A2["programs/marketing_audit/prompts/<br/>(stage prompts — mutated by evolve)"]
    A3["lineage.jsonl<br/>(per-audit row; fitness input)"]
    A4["state.evolve_lock<br/>(mutex between modes)"]
  end

  C3 --> LP
  C4 --> LP
  LP -- reads at runtime --> A2
  LIVE -- wraps --> LP
  EVOLVE -- wraps --> LP
  LIVE -- writes --> A3
  A3 -- engagement signal --> EVOLVE
  EVOLVE -- promotes --> A2
  A4 -. mutex .- LIVE
  A4 -. mutex .- EVOLVE

  style CONTENT fill:#e8f4f8
  style LANE_PROGRAM fill:#f0f8e8
  style LIVE fill:#fff4e8
  style EVOLVE fill:#f0e8ff
  style AUTORESEARCH fill:#f8e8e8
```

The key insight: gates and commercial side-effects live in the live wrapper, not in the lane program itself. The variant-production surface (Stages 0-6) is identical in both modes — that part DOES match the existing 4-lane pattern. **The asymmetry that "5th lane" framing hides:** existing lanes (geo/competitive/monitoring/storyboard) have NO commercial wrapper, NO payment ledger, NO human gates, NO R2 publish, NO downstream consumer outside autoresearch — their promoted variants get consumed by other autoresearch machinery (fitness scoring, fixture eval), not by paying customers. Marketing_audit's live wrapper is therefore a net-new object class, not a thin shell around a peer lane. The fidelity-contract asymmetry below (live-safe pre-check, cost-penalty floor, deterministic reproducibility from frozen variant snapshot) is the operational consequence.

## Implementation Units

### Phase 1 — Foundation (Bundle A)

- [ ] **Unit 1: Reconcile `src/audit/` branch state + verify deps**

**Goal:** Establish the working-branch baseline for v1 implementation. Merge existing `feat/fixture-infrastructure` audit files into a new working branch, verify deps, confirm no drift from the plan.

**Requirements:** Enables all subsequent units.

**Dependencies:** None.

**Files:**
- Verify: `src/audit/agent_models.py` (existing, 290 lines; R12-aligned — keep as-is)
- Verify: `src/audit/checkpointing.py` (existing, 102 lines; keep as-is)
- Verify: `src/audit/preflight/runner.py` + 8 check stubs (existing)
- Verify: `tests/audit/test_agent_models.py`, `tests/audit/test_checkpointing.py` (existing)
- Verify: `pyproject.toml` deps present (weasyprint, nh3, jinja2, markdown, PyYAML, aioboto3, typer, pydantic, tenacity, aiolimiter)
- Modify: create working branch `feat/audit-engine-v1` off `feat/fixture-infrastructure`

**Approach:**
- Survey existing `src/audit/` state; flag any drift from origin doc R8, R12, R14
- Confirm no `claude-agent-sdk` references in pyproject.toml or code (per origin Key Decision)
- If `src/audit/exceptions.py` or `src/audit/state.py` exist from reverted subsystem 1 (commit `19a4778`), delete before Unit 4 rebuilds them cleanly from the plan
- Tests pass on baseline before Unit 2 starts

**Patterns to follow:**
- Existing branch layout (single `feat/audit-engine-v1`, no per-audit worktrees per LHR D3)

**Test scenarios:**
- Test expectation: none — reconciliation unit, no behavioral change. `pytest tests/audit/` must still pass on baseline (smoke).

**Verification:**
- `pytest tests/audit/test_agent_models.py tests/audit/test_checkpointing.py` passes
- `grep -rn claude_agent_sdk src/ harness/ autoresearch/ pyproject.toml uv.lock` returns no matches
- Working branch has all 14 existing `src/audit/` files present

---

- [ ] **Unit 2: Foundation primitives batch 1 — exceptions, state, sessions**

**Goal:** Ship the three primitives every other Bundle A file imports from. Port session tracking from harness; add audit-specific exception hierarchy and state machine.

**Requirements:** R7 (per-stage checkpoints), R20 (local-first storage).

**Dependencies:** Unit 1.

**Files:**
- Create: `src/audit/exceptions.py` (typed errors: `AuditError` base + `CostCeilingReached`, `SubscriptionWindowExceeded`, `RateLimitHit`, `ViableResumeFailed`, `MalformedSubSignalError`, `LaneRegistrationError`, `EvolveLockHeld`)
- Create: `src/audit/state.py` (`AuditState` dataclass wrapping `checkpointing.atomic_update`; fields: `audit_id`, `client_slug`, `prospect_domain`, `status`, `total_cost_usd`, `graceful_stop_requested`, `graceful_stop_reason`, `completed_lenses`, `failed_lenses`, `bundles_activated`, `pause_reason`, `sessions` dict, `stage2_pids: list[int]` for Stage 2 fan-out cleanup defense per Unit 10 sync/async boundary contract)
- Create: `src/audit/sessions.py` (thin wrapper around `harness/sessions.SessionsFile` scoped to an audit directory)
- Create: `tests/audit/test_state.py`
- Create: `tests/audit/test_sessions.py`
- Test: `tests/audit/test_exceptions.py` (exception hierarchy + `isinstance` checks)

**Approach:**
- `state.py`: use `checkpointing.atomic_update` for all mutations (no new file-lock primitive); mirror the frozen-dataclass convention (`@dataclass(frozen=True)`, `replace()` for transitions)
- `sessions.py`: direct-import `harness.sessions.SessionsFile`, re-export scoped to `clients/<slug>/audit/<audit_id>/sessions.json`
- `exceptions.py`: flat hierarchy; all typed errors inherit from `AuditError`; add docstrings naming which pipeline stage raises each

**Execution note:** Start with a failing test for `AuditState.mutate()` concurrency — two threads calling `.mutate` must serialize without lost writes.

**Patterns to follow:**
- Frozen dataclass convention: `harness/sessions.py:45`, `autoresearch/evaluate_variant.py:91–113`, existing `src/audit/agent_models.py`
- `os.replace` atomic pattern: `src/audit/checkpointing.py:36–64`

**Test scenarios:**
- Happy path: AuditState init → mutate status → persist → reload → verify fields round-trip intact
- Happy path: SessionsFile `.begin(agent_key, session_id, engine="claude")` → `.finish(agent_key, "complete")` → status transitions correctly
- Edge case: concurrent `AuditState.mutate()` from 2 threads (200 increments each) — no lost writes, final count = 400
- Edge case: AuditState load from corrupt JSON → raises typed error, original file preserved
- Error path: `ViableResumeFailed` raised when session_id recorded but claude JSONL missing from `~/.claude/projects/`
- Integration: state.json + sessions.json in same audit dir; audit resume reads both

**Verification:**
- AuditState persist + reload round-trips cleanly
- Concurrent writes under threading.Lock produce no lost updates
- `isinstance(CostCeilingReached(...), AuditError)` is True; pytest confirms exception hierarchy

---

- [ ] **Unit 3: `claude_subprocess.py` — shared CLI invocation helper**

**Goal:** Consolidate the three existing claude CLI invocation patterns behind a single helper module. Everything else in Bundle A+B that invokes `claude -p` uses these factories.

**Requirements:** R7 (CLI subprocess execution), R10 (token parsing for cost enforcement).

**Dependencies:** Unit 2 (uses `AuditState`, `exceptions`).

**Files:**
- Create: `src/audit/claude_subprocess.py` (three factories + stream-json tail parser)
- Create: `tests/audit/test_claude_subprocess.py`

**Approach:**
- All three factories accept a required `cwd: Path` argument and pass it to `subprocess.Popen(..., cwd=cwd, ...)`. **`cwd` MUST be the audit directory** (`clients/<slug>/audit/<audit_id>/`) so that `harness/sessions.claude_session_jsonl(cwd, session_id)` resolves correctly to the JSONL `claude` writes at `~/.claude/projects/<cwd-encoded>/<session_id>.jsonl`. Without this, `--resume <session_id>` errors out (see `harness/sessions.py:135-137`). Add `assert cwd.is_dir()` precondition at function entry.
- `build_cmd_streaming(prompt, model, session_id, cwd, resume=False, max_turns=None)` → Pattern A for Stage 2 lens agents. Mirrors `harness/engine.py:_build_claude_cmd` shape; mirrors the `--resume`-vs-`--session-id` exclusivity convention from `harness/engine.py:_build_claude_cmd` (when `resume=True`, prepends `_RESUME_PROMPT` continue-string to `prompt`; never passes both flags).
- `build_cmd_meta(model, max_turns, cwd, allowed_tools=None)` → Pattern B for Stage 1b brief-gen + Stage 3 synthesis + Stage 4 proposal. Prompt fed via stdin. Mirrors `autoresearch/evolve.py:_build_meta_command`.
- `build_cmd_short_json(prompt, model, cwd, session_id=None)` → Pattern C for critic calls, MA-1..MA-8 rubric judges, R24 redaction pass. Mirrors `autoresearch/compute_metrics.py:_run_claude_json`.
- `parse_rate_limit(stream_json_tail)` → port `harness/engine.py:275` verbatim.
- `parse_result_message(json_envelope)` → **net-new**. Extracts (all top-level except `usage.*`): `total_cost_usd`, `duration_ms` (wall-clock including tools), **`duration_api_ms` (API-only time for R29 SLA)**, `subtype` (success/error_max_turns/error_during_execution/error_max_budget_usd/error_max_structured_output_retries), `result` (success subtype only), `errors` (error subtypes), `num_turns`, `session_id`, `is_error`, `stop_reason`, and nested `usage.{input,output,cache_creation_input,cache_read_input}_tokens`. Returns typed `ResultMessage` dataclass with subtype-based dispatch (success path populates `result`; error path populates `errors`).
- Env sanitization via **13-key allowlist** copied from `autoresearch/evolve.py:74` `_CLAUDE_ENV_KEYS`: PATH, HOME, USER, SHELL, TERM, LANG, TMPDIR, SSH_AUTH_SOCK, ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN, FREDDY_API_URL, FREDDY_API_KEY, OPENAI_API_KEY. **Subscription-only billing is the v1 default per Key Decision §Execution model.** ANTHROPIC_API_KEY retention in the allowlist is **defensive** (preserves the option to fall back to API mode if subscription is unavailable mid-run); production `freddy audit run` invocations MUST run with `ANTHROPIC_API_KEY` unset in JR's production env and `CLAUDE_CODE_OAUTH_TOKEN` set. If both happen to be set, the claude CLI prefers OAuth (verified empirically). Unit 4 cost_ledger asserts at audit-start that `CLAUDE_CODE_OAUTH_TOKEN` is set, raising `MissingSubscriptionToken` if not — this is the policy enforcement point, not the env allowlist.

**Execution note:** Test-first for `parse_result_message` — claude's envelope shape is the novel capability, write tests against captured fixture envelopes before implementing.

**Patterns to follow:**
- `harness/engine.py:228-272` for Pattern A signature
- `autoresearch/evolve.py:602` `_build_meta_command` for Pattern B (post-refactor multi-provider; the function now branches on backend, but the claude branch shape is what audit reuses)
- `autoresearch/compute_metrics.py:259-305` `_build_alert_cmd` (claude branch at `:276-285`) + `_run_alert_agent_json` at `:349` for Pattern C. **Note:** the legacy `_run_claude_json` was renamed/refactored into multi-backend dispatch (PR #28+#33+#34); the audit plan deliberately stays claude-only per Key Decision §Execution model — Unit 3's `build_cmd_short_json` mirrors only the claude branch.
- `harness/engine.py:275` for rate-limit tail parsing

**Test scenarios:**
- Happy path: Pattern A cmd has correct flag order (`-p`, `--output-format stream-json`, `--resume <sid>`, `--model`, `--dangerously-skip-permissions`)
- Happy path: Pattern C cmd includes `--session-id <uuid>` + `--output-format json`
- Happy path: `parse_result_message` extracts cost + tokens from fixture envelope; returns `ResultMessage` dataclass
- Edge case: envelope missing `total_cost_usd` (subscription-billed case) — returns 0.0, still parses tokens
- Edge case: malformed JSON envelope raises typed error
- Edge case: `parse_rate_limit` detects `"type": "rate_limit_event"` in stream-json tail
- Error path: env sanitization strips `ANTHROPIC_API_KEY`, retains `CLAUDE_CODE_OAUTH_TOKEN` (subscription auth)
- Integration: end-to-end Pattern A cmd construction + env setup for a fixture call (smoke-only, not actually invoking claude)

**Verification:**
- All 3 factories return `list[str]` commands matching the existing-site patterns byte-for-byte on fixture inputs
- `parse_result_message` round-trips all fields from a captured fixture envelope
- `parse_rate_limit` detects rate-limit events in fixture stream-json

---

- [ ] **Unit 4: `cost_ledger.py` — claude cost parsing + per-stage gate enforcement**

**Goal:** Ship the net-new capability the codebase doesn't have: parse claude's `total_cost_usd` from every `ResultMessage`, accumulate per-stage, enforce R10 soft/hard breakers, enforce R29 subscription-window SLA.

**Requirements:** R10 (cost ceilings), R29 (subscription-window SLA).

**Dependencies:** Unit 2 (state.py), Unit 3 (claude_subprocess parse_result_message).

**Files:**
- Create: `src/audit/cost_ledger.py` (`CostLedger(state_file, mode)` — `mode` in `{audit, scan}`; `.record(role, result_message, metadata)` appends to `cost_log.jsonl` + updates state + enforces breakers; soft-warn/hard-breaker thresholds from R10)
- Modify: `src/common/cost_recorder.py` — add `claude_rates(model)` helper matching existing `_gemini_rates` shape (for inferred-API-cost conversion when subscription billing produces `total_cost_usd=0`)
- Create: `tests/audit/test_cost_ledger.py`

**Approach:**
- Audit mode: soft-warn at $100 (Slack stub — deferred, emits stderr log only), hard breaker at $150
- Scan mode: $2 hard breaker
- Subscription-window tracking (R29): use **`duration_api_ms`** (NOT `duration_ms`) for SLA math — the subscription bucket is API-time, not wall-clock. Soft-warn at 40% of 5h API-time (72 min of API-time), hard at 50% (90 min); halts Stage 2+ fan-out and sets `pause_reason=subscription_window_ceiling`. Wall-clock `duration_ms` still tracked for UX + graceful-stop wall-clock bound.
- On subscription billing: `total_cost_usd` is Anthropic's *estimated* API cost for the work done — typically populated, no fallback to tokens × rates needed. Verify this assumption against a real subscription call during Unit 4 testing; if `total_cost_usd` is 0 on subscription, fall back to token-count × `claude_rates(model)` inferred cost.

**Execution note:** Test-first. The parse → ledger → gate flow is the novel capability; define expected behavior via fixture envelopes before implementing the ledger class.

**Patterns to follow:**
- `src/common/cost_recorder.py` for JSONL append pattern (aiofiles, no flock — single-process v1 per LHR D3 serialization)
- `autoresearch/events.py` per-write flock (consider adopting for multi-process safety if Bundle E evolve loop ever runs parallel to a live audit — but R16 evolve_lock mutex prevents that)

**Test scenarios:**
- Happy path: record 3 calls, total_cost_usd sums correctly, cost_log.jsonl has 3 rows
- Happy path: audit mode hard breaker at $150 raises `CostCeilingReached`, sets `state.pause_reason=cost_ceiling`
- Happy path: scan mode ceiling at $2 triggers at $2.01
- Edge case: subscription billing (envelope total_cost_usd=0) — falls back to token × rate inferred cost, ceiling math still works
- Edge case: R29 subscription-window soft-warn at 40% wall-clock budget; hard breaker at 50%
- Error path: malformed cost_log.jsonl → `CostLedger.load_history` raises typed error
- Error path: `CostCeilingReached` exception caught by pipeline runner, persists state, allows resume
- Integration: cost_ledger + state → pause_reason flows through resume path correctly

**Verification:**
- Fixture-driven test suite covering audit + scan modes, subscription + API billing, soft-warn + hard-breaker transitions
- `cost_log.jsonl` in realistic audit directory has one row per stage with tokens + cost + model + metadata

---

- [ ] **Unit 5: Foundation primitives batch 2 — graceful_stop, resume, cleanup**

**Goal:** Port the three harness primitives the audit pipeline needs for resumability and clean shutdown. Thin ports, no new functionality.

**Requirements:** R7 (resumable 6-stage pipeline), R10/R29 (graceful halt on cost/window breach).

**Dependencies:** Unit 2 (state.py).

**Files:**
- Create: `src/audit/graceful_stop.py` (dict-based flag on `AuditState`; set by cost_ledger on breach or external signal)
- Create: `src/audit/resume.py` (`_viable_resume_id(record, audit_dir) -> str | None`; `build_resume_plan(state) -> ResumePlan` listing must_restart + can_resume + completed_lenses to skip)
- Create: `src/audit/cleanup.py` (`atexit` + SIGTERM + SIGINT handlers with wait(5s) + SIGKILL escalation)
- Create: `tests/audit/test_resume.py`
- Create: `tests/audit/test_graceful_stop.py`
- Create: `tests/audit/test_cleanup.py`

**Approach:**
- `graceful_stop`: `AuditState.graceful_stop_requested: bool` + `.graceful_stop_reason: str`; checked between stages and inside Stage-2 fan-out; no SIGTERM hook on main process (the audit runs under JR's terminal)
- `resume.py`: port `harness/run.py:197-220` `_viable_resume_id` verbatim. For each recorded session in state.sessions, check the claude projects JSONL exists at `~/.claude/projects/<encoded-audit-dir>/<sid>.jsonl`. **`encoded-audit-dir` derives from the audit directory the original `claude -p` was invoked with `cwd=clients/<slug>/audit/<audit_id>/`** — Unit 3 factories assert this cwd; `resume.py` mirrors the derivation by calling `harness.sessions.claude_session_jsonl(audit_dir, sid)`. Missing JSONL → force restart of that session. **Before reaching the JSONL derivation, `build_resume_plan` validates `audit_dir.is_dir()` and raises `ViableResumeFailed(audit_id)` if missing** — this prevents Unit 3's `assert cwd.is_dir()` from firing downstream with an opaque AssertionError when JR runs `freddy audit resume <id>` against a deleted directory. `build_resume_plan` also flags `stage_2_skip` with completed lenses. Add a happy-path test that round-trips `audit_dir → encoded → existing JSONL` plus a test that `--resume <id>` against a deleted directory raises `ViableResumeFailed`, not `AssertionError`.
- `cleanup.py`: atexit + signal handlers port `harness/worktree.py:_install_exit_handlers:396–414` but simpler (no backend process group — audit has one `claude -p` subprocess per call, cleaned up by the caller's with-block). Wait-then-kill escalation pattern from `harness/worktree.py:349–363`.

**Patterns to follow:**
- `harness/run.py:197-220` for resume viability
- `harness/worktree.py:396–414` for exit handlers
- `harness/worktree.py:349–379` for wait+SIGKILL escalation

**Test scenarios:**
- Happy path: graceful_stop flag set → pipeline runner breaks between stages cleanly
- Happy path: build_resume_plan with 3 completed lenses + 1 failed → plan.can_resume lists 3 lens sessions, must_restart lists the failed one, stage_2_skip has 3 lens IDs
- Happy path: cleanup atexit handler fires on normal exit (pytest captures the handler call)
- Edge case: `_viable_resume_id` returns None when claude projects JSONL is missing (simulated by unlinking fixture file)
- Edge case: SIGTERM handler triggers graceful stop — state flushed, exit 0
- Error path: cleanup handler wait exceeds 5s → SIGKILL escalation
- Integration: graceful_stop + resume + cleanup chain during simulated mid-Stage-2 breach

**Verification:**
- Pipeline runner respects graceful_stop between stages
- Resume plan correctly identifies must_restart vs can_resume vs skip
- SIGTERM during pytest fixture leaves state.json valid

---

- [ ] **Unit 6: Foundation primitives batch 3 — events + evolve_lock** (prompts_loader inlined as Stage ABC method)

**Goal:** Port events logging + implement the `state.evolve_lock` mutex between live and evolve modes. Stage-prompt loading is inlined into the Stage ABC (Unit 9 `src/audit/stages/_base.py`) as a `_load_prompt(self, name)` method that calls `lane_runtime.resolve_runtime_dir(...)` directly — no standalone `prompts_loader.py` module needed (one consumer = no abstraction).

**Requirements:** R14 (stage prompts externalized, loaded at runtime — implemented in Stage ABC, see Unit 9), R16 (evolve_lock mutex), R21 (events logged per audit).

**Dependencies:** Unit 2.

**Files:**
- Create: `src/audit/events.py` (direct-import wrapper around `autoresearch/events.log_event` with optional `path=` param for per-audit log; extend autoresearch/events.log_event to accept path — ~10 LOC + 2 tests covering rotation behavior under `path=audit_dir/events.jsonl` and `path=None` default)
- Modify: `autoresearch/events.py` — accept optional `path=` in `log_event` (currently only `read_events` has it). **Backward-compat:** existing call sites pass no `path=` argument; add integration test in `tests/autoresearch/test_events.py` exercising both old (no path) and new (per-audit path) call paths to lock the contract before any in-tree caller migrates.
- Create: `autoresearch/evolve_lock.py` (`EvolveLock` context manager using `fcntl.flock` on `~/.local/share/gofreddy/state.evolve_lock`; ~15 LOC; lives next to `autoresearch/evolve.py` since both wrappers — live and evolve — import it). **No `ActiveRunLock(client_slug)`** — multi-tenant is out of v1 scope; single-operator pipeline doesn't need per-slug concurrency.
- Create: `tests/audit/test_events.py`
- Create: `tests/autoresearch/test_evolve_lock.py`

**Approach:**
- `events.py`: thin module. `log_event(kind, **data)` writes to per-audit `clients/<slug>/audit/<audit_id>/events.jsonl`. For global lifecycle events (audit start/end), also write to the default `autoresearch/events.jsonl`.
- Stage-prompt loading: inlined into Stage ABC `_load_prompt(self, name)` method at `src/audit/stages/_base.py` (Unit 9). Implementation = `(lane_runtime.resolve_runtime_dir(archive_dir) / "programs/marketing_audit/prompts" / f"{name}.md").read_text()`; missing prompt → raise `LaneRegistrationError`. One method, one consumer, no separate module.
- `autoresearch/evolve_lock.py`: `EvolveLock` uses `fcntl.flock` with non-blocking `LOCK_EX | LOCK_NB`; `EvolveLockHeld` raised if already held. Lives next to `autoresearch/evolve.py` — imported by both `freddy audit run` (acquires lock at start, raises if evolve active) and `autoresearch evolve --lane marketing_audit` (acquires same lock, raises if any live audit in flight). Audit-side imports as `from autoresearch.evolve_lock import EvolveLock`.

**Patterns to follow:**
- `autoresearch/events.py` for log structure + rotation (100 MB)
- `autoresearch/events.py:51` for flock pattern
- `autoresearch/lane_runtime.py` for `resolve_runtime_dir` call

**Test scenarios:**
- Happy path: `log_event("stage_start", stage="stage_1b", audit_id="x")` writes one JSON line to per-audit events.jsonl
- Happy path: Stage ABC `_load_prompt("stage_2_lens_meta")` reads from materialized variant dir; returns markdown string (test lives in `tests/audit/stages/test_base.py` once Unit 9 ships)
- Happy path: `EvolveLock()` acquires + releases cleanly
- Edge case: events.jsonl rotates at 100 MB; rotation preserves data
- Edge case: missing `programs/marketing_audit/prompts/stage_X.md` → `LaneRegistrationError` (Stage ABC test, Unit 9)
- Error path: `EvolveLock.__enter__` raises `EvolveLockHeld` when held by another process (simulated via subprocess)
- Integration: `EvolveLock` held during simulated evolve run blocks concurrent `freddy audit run`

**Verification:**
- Per-audit events.jsonl written with correct structure
- Prompts loaded from promoted variant dir
- evolve_lock mutex correctly blocks concurrent live audit vs evolve run

---

- [ ] **Unit 7: Preflight retrofit — 6 stub checks get real HTTP I/O**

**Goal:** Extend the 6 stub preflight checks (`assets`, `badges`, `headers`, `schema`, `social`, `tooling`) with real httpx-based detection, matching the `dns.py` and `wellknown.py` pattern.

**Requirements:** R7 (Stage 1a deterministic preflight), R21 (owned-provider first — use httpx directly, no new deps).

**Dependencies:** Unit 2 (exceptions).

**Files:**
- Modify: `src/audit/preflight/checks/schema.py` (parse homepage JSON-LD via httpx GET + BeautifulSoup; extract org + product schema; return structured dict)
- Modify: `src/audit/preflight/checks/trust_badges.py` (alias `badges.py`) (regex scan for trust-signal badges in page HTML: PCI, HIPAA, SOC 2, GDPR badges; security/privacy/compliance links)
- Modify: `src/audit/preflight/checks/headers.py` (evaluate response headers: CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy; grade per Mozilla Observatory rubric)
- Modify: `src/audit/preflight/checks/social.py` (extract OG + Twitter card tags; validate presence + image URLs + dimensions)
- Modify: `src/audit/preflight/checks/assets.py` (detect logo URL, favicon, apple-touch-icon, manifest.json PWA presence)
- Modify: `src/audit/preflight/checks/tooling.py` (fingerprint analytics, CDP, CRM, marketing tools from DOM script tags + HTTP headers; lightweight subset of wappalyzer-next patterns)
- Modify: `tests/audit/preflight/test_*.py` for each retrofitted check

**Approach:**
- Each check: `async def run(ctx: PreflightContext) -> dict[str, Any]`. Signature matches existing stub shape at `runner.py:91–99`.
- httpx client with 10s timeout per request; share client via `PreflightContext` to avoid connection churn
- Return `{implemented: True, signals: {...}, evidence_urls: [...]}` on success; `{implemented: False, error: "<reason>"}` on failure (preflight continues — R12 skip-not-raise)
- No external APIs — all checks use the prospect's own domain responses

**Patterns to follow:**
- `src/audit/preflight/checks/dns.py` (existing, 128 lines, real dnspython)
- `src/audit/preflight/checks/wellknown.py` (existing, 154 lines, real httpx)

**Test scenarios:**
- Happy path (schema.py): mock JSON-LD response with Organization + Product schema → parsed dict returned
- Happy path (headers.py): fixture response with strict CSP + HSTS → grade A
- Happy path (social.py): fixture OG + Twitter tags → both detected with image URLs
- Happy path (badges.py): HTML with SOC 2 badge → detected
- Edge case: 404 on homepage → `{implemented: False, error: "homepage unreachable"}` — no raise
- Edge case: timeout → graceful fallback
- Edge case: malformed JSON-LD → skip, log warning, don't raise
- Integration: `PreflightRunner.run_all` with all 8 checks → returns `PreflightResult` with 8 signal entries

**Verification:**
- All 8 preflight checks return real data on a fixture site (mocked httpx responses)
- `PreflightRunner.run_all` on fixture produces a complete result dict
- No raises on 4xx/5xx; all failures logged + counted

---

### Phase 2 — Stage pipeline (Bundle B)

- [ ] **Unit 8: `configs/audit/lenses.yaml` transcription + Python loader**

**Goal:** Transcribe the 149-lens catalog from `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` into machine-readable YAML. Ship the Python loader that feeds Stage 2 dispatch.

**Requirements:** R8 (149-lens catalog is content authority, compiled to `configs/audit/lenses.yaml`).

**Dependencies:** Unit 2 (exceptions).

**Files:**
- Create: `configs/audit/lenses.yaml` (the big content file — JR-coordinated transcription, ~198 entries, multi-day)
- Create: `src/audit/lenses.py` (YAML loader + `Lens` dataclass + `select_applicable(phase_0_signals) -> list[Lens]` dispatcher)
- Create: `src/audit/bundles.py` (conditional-bundle activation: `activate_bundles(phase_0_signals) -> list[str]` returning which of the 25 vertical + 10 geo + 5 segment bundles fire for this prospect)
- Create: `tests/audit/test_lenses.py`
- Create: `tests/audit/test_bundles.py`

**Approach:**
- **Execution split:** Python loader + schema + tests land first with a **minimal 10-lens sample YAML** so Unit 9–13 can be built against it. Full 198-entry transcription is a JR-coordinated parallel task (see Dependencies / Assumptions in origin doc).
- YAML schema per lens (one entry):
  ```yaml
  - id: "L-A-01"
    name: "Technical SEO health"
    area: "Discoverability & Organic Search"
    tier: 1
    rank: 1
    stage_phase: 2  # which 6-stage pipeline stage runs this lens. 0=Phase-0 signals, 1a=preflight, 1b=signal-det, 2=lens fan-out, 3=synthesis. (Distinct from project Phases 1-6 in §Phased Delivery — those track implementation milestones; this tracks pipeline stage at runtime.)
    providers: ["dataforseo"]
    detection_signals: []  # empty = always-on
    bundle_membership: []  # empty = always-on; else bundle-id like "v-b2b-saas"
    cost_est_usd: 0.45
    timeout_s: 45
    subsignal_schema_ref: "src.audit.agent_models.SubSignal"
    rubric_anchors:
      high: "..."
      medium: "..."
      low: "..."
  ```
- `Lens` dataclass is frozen. Loader validates schema on read; raises typed error on malformed entries.
- `bundles.py`: dispatches bundles via Phase-0 signals map (`{vertical: "b2b_saas", geo: "us", segment: "enterprise"}` → `["v-b2b-saas", "g-us", "s-enterprise"]`)

**Execution note:** Full lens transcription is JR-coordinated multi-day content work; schedule separately. Python side can proceed against the 10-lens sample.

**Patterns to follow:**
- No existing YAML-driven config in `configs/` — this is the first real YAML configuration file
- Frozen dataclass + schema validation: `src/audit/agent_models.py`

**Test scenarios:**
- Happy path: load 10-lens sample YAML → returns 10 frozen Lens dataclasses
- Happy path: `select_applicable({phase_0: always-on})` returns all 149 always-on lenses
- Happy path: `activate_bundles({vertical: "b2b_saas", geo: "us"})` returns expected 2 bundle IDs
- Edge case: malformed lens entry (missing `id`) → `LaneRegistrationError`
- Edge case: duplicate lens IDs → raise
- Edge case: conditional lens fires only when `detection_signals` match
- Integration: lenses.yaml + bundles.py + Phase-0 signals produce the expected lens dispatch set for a B2B SaaS US enterprise fixture

**Verification:**
- Loader parses a valid YAML without warnings
- `select_applicable` + `activate_bundles` together produce the expected dispatch set for each of 3 fixture prospect profiles

---

- [ ] **Unit 9: Stages 0–1 (intake + preflight + pre-discovery + brief)**

**Goal:** Implement Stages 0–1a–1b–1c per the 6-stage pipeline spec. Intake initializes workspace; 1a runs deterministic preflight; 1b detects bundle-activation signals via one Pattern-B claude session; 1c synthesizes brief via one short claude call.

**Requirements:** R7 (6 stages manual-fire), R1 (scan at `depth=scan` runs a subset).

**Dependencies:** Units 2, 3, 4, 5, 6, 7, 8.

**Files:**
- Create: `src/audit/stages/__init__.py`
- Create: `src/audit/stages/_base.py` (`Stage` ABC with `__init__(self, state: AuditState, archive_dir: Path)`; `StageResult` TypedDict with `stage`, `outputs`, `cost_usd`, `duration_s`, `error`, `input_hash`; helpers `_load_prompt(name)`, `_compute_input_hash(*paths)` for cross-session integrity per Key Decision §Multi-session orchestration)
- Create: `src/audit/stages/stage_0_intake.py` (reads intake form data; initializes state + workspace)
- Create: `src/audit/stages/stage_1a_preflight.py` (wraps `preflight/runner.run_all`)
- Create: `src/audit/stages/stage_1b_signals.py` (one Pattern-B claude session with audit MCP server; detects Phase-0 signals: vertical, geo, segment)
- Create: `src/audit/stages/stage_1c_brief.py` (one Pattern-C short claude call synthesizing stage 1a + 1b into brief.md)
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_1b_signals.md` (prompt)
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_1c_brief.md` (prompt)
- Create: `tests/audit/stages/test_stage_0_intake.py`
- Create: `tests/audit/stages/test_stage_1a_preflight.py`
- Create: `tests/audit/stages/test_stage_1b_signals.py`
- Create: `tests/audit/stages/test_stage_1c_brief.py`

**Approach:**
- Stage ABC has `__init__(self, state: AuditState, archive_dir: Path)` storing both as instance attrs (`archive_dir` defaults to `Path(os.environ['ARCHIVE_DIR'])` at lane-runner construction time, matching `autoresearch/lane_runtime.py:232` convention; lane runner constructs each stage with this value), `run() -> StageResult`, `_load_prompt(self, name) -> str` helper that calls `lane_runtime.resolve_runtime_dir(self.archive_dir)` and reads `programs/marketing_audit/prompts/<name>.md` (raises `LaneRegistrationError` if missing), and `_compute_input_hash(self, *paths) -> str` helper that returns `sha256(b"\n".join(Path(p).read_bytes() for p in paths)).hexdigest()`. Each stage loads its prompt via `self._load_prompt("stage_N_xxx")` and prepends an `INPUT_HASH=<hex>` header line to the prompt body before invoking claude — consumers can re-derive the hash post-hoc to detect cross-stage poisoning per Key Decision §Multi-session orchestration consequence (a). The hash is also persisted into `StageResult.input_hash` and into `state.sessions[stage_name].input_hash` for `freddy audit verify-lineage <id>` (Unit 14c) to recompute and compare. (Replaces the standalone `src/audit/prompts_loader.py` module previously specified in Unit 6 — one consumer, no abstraction needed.)
- Stage 0 is Python-only (no LLM). **First action: `audit_dir.mkdir(parents=True, exist_ok=True)`** — this is the precondition for Unit 3's `cwd=audit_dir` factory assertions and Unit 5's `_viable_resume_id` JSONL derivation; if Stage 0 doesn't run before any subprocess factory call, the assertions fire with opaque AssertionError. After mkdir: reads intake fields, initializes `state.sessions = {}`, `state.status = "stage_0_done"`.
- Stage 1a dispatches `preflight/runner.PreflightRunner.run_all` and persists results under `clients/<slug>/audit/<id>/stage1a/`.
- Stage 1b opens one `claude -p` Pattern-B session with `--allowedTools Bash,Read,Write,WebFetch`; reads the warm cache from 1a + intake; emits bundle-activation signals to `stage1b/signals.json` AND a structured `stage1b/dispatch_rationale.md` + `stage1b/dispatch_rationale.json` sidecar that MA-5 + MA-8 judges read at evaluation time. Session_id persisted via `sessions.begin`.

**`stage1b/dispatch_rationale.md` schema (locked):**
```markdown
# Dispatch Rationale — audit_id <id>

## Phase-0 Signals Detected
- vertical: <slug> (confidence: 0.NN)
- geo: <slug> (confidence: 0.NN)
- segment: <slug> (confidence: 0.NN)

## Bundles Activated
- v-<vertical>: <count> lenses [L###, L###, ...]
- geo-<geo>: <count> lenses
- seg-<segment>: <count> lenses

## Lenses Fired
<count>/149 always-on + <count>/<bundle-total> bundle lenses

## Lenses Skipped
| lens_id | reason_code | rationale |
|---------|-------------|-----------|
| L042    | bundle_not_active | v-b2c-ecom not detected |
| L087    | phase_0_signal_excludes | enterprise segment doesn't apply to L087 |
| L121    | enrichment_unavailable | attach-ads not provided; lens depends on creative-pull |

## Coverage Summary
- always-on: <fired>/149 (<pct>%)  — must be ≥80% per anti-Goodhart Key Decision
- vertical bundles: <fired>/<total> (<pct>%)
- geo bundles: <fired>/<total> (<pct>%)
- segment bundles: <fired>/<total> (<pct>%)
```

**`stage1b/dispatch_rationale.json` schema (machine-readable companion for judges):**
```json
{
  "audit_id": "<uuid>",
  "phase_0_signals": {"vertical": "<slug>", "geo": "<slug>", "segment": "<slug>",
                      "vertical_confidence": 0.85, "geo_confidence": 0.95, "segment_confidence": 0.70},
  "bundles_activated": ["v-b2b-saas", "geo-us", "seg-enterprise"],
  "lenses_fired": ["L001", "L002", "..."],
  "lenses_skipped": [
    {"lens_id": "L042", "reason_code": "bundle_not_active", "rationale": "v-b2c-ecom not detected"}
  ],
  "coverage": {"always_on": 0.953, "vertical": 0.48, "geo": 0.20, "segment": 0.40}
}
```

**Closed-enum reason codes** for `lenses_skipped[].reason_code`:
- `bundle_not_active` — lens belongs to a vertical/geo/segment bundle that didn't activate
- `phase_0_signal_excludes` — phase-0 signal explicitly excludes this lens
- `enrichment_unavailable` — lens depends on an attach-* enrichment that wasn't provided
- `cost_ceiling_exceeded` — cost cap reached before lens dispatched
- `evolve_skip_rule` — variant's evolve mutation specifies skip per orchestration mutation space (R28)

Any other reason → reject Stage 1b output as malformed; no implicit skip categories.
- Stage 1c loads 1a + 1b outputs; one Pattern-C short-JSON claude call synthesizes `brief.md` + `brief.json`. Cost ~$0.50-1 per R10.
- `depth=scan` mode: Stages 0 + 1a (subset) + 1c (narrow scan prompt) only — skips 1b and Stage 2+.

**Execution note:** Start with a failing integration test for `stage_1a_preflight` reading a mocked preflight runner — stage orchestration + state transitions are the novel integration, not the individual check logic.

**Patterns to follow:**
- `src/audit/preflight/runner.py` existing pattern
- Pattern B + Pattern C from `src/audit/claude_subprocess.py`
- Stage result persistence via `checkpointing.atomic_update`

**Test scenarios:**
- Happy path: Stage 0 → state.status transitions to "stage_0_done", workspace created
- Happy path: Stage 1a runs 8 preflight checks, writes 8 result files under stage1a/
- Happy path: Stage 1b detects "b2b_saas", "us", "enterprise" from mock claude response; writes signals.json
- Happy path: Stage 1c produces brief.md + brief.json with expected structure
- Edge case: intake missing required field → Stage 0 raises typed error; state unchanged
- Edge case: Stage 1a has 4 preflight checks fail → Stage 1a succeeds with partial signals, skip-not-raise
- Edge case: Stage 1b claude session fails with rate-limit → pause_reason set, resumable
- Error path: Stage 1c cost exceeds $5 ceiling → CostCeilingReached raised, state flushed
- Integration: Stage 0 → 1a → 1b → 1c chain with fixture intake produces brief.md; session_ids persisted per stage; state transitions match expected
- Integration: `depth=scan` runs Stage 0 + 1a subset + 1c in <$2 total cost

**Verification:**
- Full Stage 0-1c chain on fixture intake produces `brief.md` + state.status="stage_1c_done"
- Each stage's session_id recorded in sessions.json
- `depth=scan` produces a scan deliverable in <$2 on fixture

---

- [ ] **Unit 10: Stage 2 — parallel lens fan-out**

**Goal:** Implement Stage 2 per R28 mutation space — 7 parallel `claude -p` Pattern-A sessions, `asyncio.gather(return_exceptions=True)`, Semaphore(7), inner-loop critique optional per role. Each agent handles ~21 lenses.

**Requirements:** R7, R12 (SubSignal → ParentFinding), R27 (cost-weighted fitness makes orchestration evolvable), R28 (mutation space).

**Dependencies:** Units 2–9.

**Files:**
- Create: `src/audit/stages/stage_2_lenses.py`
- Create: `src/audit/subsignals.py` (SubSignal parsing with skip-not-raise per R12; null/excluded not zero per institutional learning)
- Create: `src/audit/inner_loop.py` (critic → revise-once-on-fail → skip-not-raise; opt-in per agent role via variant config)
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_2_lens_meta.md` (shared prompt skeleton for Stage-2 agents; includes role, objective, lens assignment, rubric checklist, output contract)
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/inner_loop_critic.md` (critic prompt for opt-in inner loop)
- Create: `tests/audit/stages/test_stage_2_lenses.py`
- Create: `tests/audit/test_subsignals.py`
- Create: `tests/audit/test_inner_loop.py`

**Approach:**
- 7 agent roles (per design doc §5.4): Findability, Brand/Narrative, Conversion-Lifecycle, Distribution, MarTech-Attribution, Monitoring, Competitive
- Each agent gets ~21 lenses from `configs/audit/lenses.yaml` via `select_applicable` + `activate_bundles` dispatch
- Per agent: one `claude -p` Pattern-A session with `tools={"type":"preset","preset":"claude_code"}` + audit MCP server (cache-backed wired providers from existing code); reads stage_2_lens_meta.md prompt + agent-specific reference file + brief.md; produces SubSignals per lens
- Fan-out: `asyncio.gather(*tasks, return_exceptions=True)` with `asyncio.Semaphore(7)`. Each agent result wrapped in try/except so one failure doesn't cascade.
- Graceful-stop check between agent dispatches (per `harness/run.py` pattern)
- SubSignals persist to `stage2_subsignals/L<id>_<slug>.json` — per-lens atomic write enables per-lens resume (R28 mutation space point)
- Inner loop (opt-in per role): after agent output, critic evaluates; if fails rubric-coverage check, agent revises once; if still fails, mark `rubric_coverage[lens_id] = "gap_flagged"` and continue

**Inner-loop critic pass/fail criteria (locked):**

```python
# Pass criteria — critic accepts agent output if BOTH hold:
COVERAGE_FLOOR = 0.80  # ≥80% of assigned lenses have valid SubSignals
                       # (matches the dispatch coverage floor at Key Decision §Lens-dispatch coverage invariant)
SCORE_FLOOR = 5.0       # mean SubSignal `quality_score` (0-10) across produced SubSignals

def critic_evaluates(agent_output: AgentOutput) -> CriticVerdict:
    """Pattern-C short-JSON claude call (~$0.10-0.30 per invocation)."""
    valid_count = sum(1 for s in agent_output.subsignals if is_valid(s))
    coverage = valid_count / len(agent_output.assigned_lenses)
    mean_quality = mean(s.quality_score for s in agent_output.subsignals if is_valid(s)) if valid_count > 0 else 0.0

    if coverage < COVERAGE_FLOOR:
        return CriticVerdict(pass_=False, reason="coverage_below_floor",
                             missing_lens_ids=[l for l in agent_output.assigned_lenses
                                                  if l not in {s.lens_id for s in agent_output.subsignals if is_valid(s)}])
    if mean_quality < SCORE_FLOOR:
        return CriticVerdict(pass_=False, reason="quality_below_floor",
                             low_quality_lens_ids=[s.lens_id for s in agent_output.subsignals
                                                       if s.quality_score < SCORE_FLOOR])
    return CriticVerdict(pass_=True)

# Revise-once shape — fed to the same agent session (--resume <session_id>)
REVISE_PROMPT = """\
Your previous output covered {valid_count}/{total} assigned lenses with mean quality {mean_quality:.1f}/10.
Critic flagged: {reason}.
{detail_block}
Revise by emitting valid SubSignals for as many of the flagged lens_ids as possible.
Output JSON only, no prose. Same SubSignal schema as before.
"""

# Final fall-back — if revise also fails:
def gap_flag_unfilled(agent_output: AgentOutput, critic_verdict: CriticVerdict) -> AgentOutput:
    """Mark missing lenses as gap_flagged in rubric_coverage; do NOT raise."""
    for lens_id in critic_verdict.missing_lens_ids or []:
        agent_output.rubric_coverage[lens_id] = "gap_flagged"
    for lens_id in critic_verdict.low_quality_lens_ids or []:
        agent_output.rubric_coverage[lens_id] = "low_quality_gap_flagged"
    return agent_output
```

**Opt-in defaults (variant config):**

```yaml
# default in v1: opt-in for high-SubSignal-density roles; opt-out for low-density
stage_2:
  inner_loop:
    Findability: true            # high lens density (~25 lenses); revise pays back
    Brand: true                  # narrative coherence benefits from critic pass
    Conversion-Lifecycle: true   # downstream of MA-2 actionability — drives conversion gate
    Distribution: false          # ~12 lenses; revise cost > benefit
    MarTech-Attribution: true    # technical accuracy critical
    Monitoring: false            # observational, lower critic-revise upside
    Competitive: false           # MA-3 honesty axis is judged at outer loop, not Stage 2
```

**Cost ceiling:** Total inner-loop critic calls ≤ 2 × 7 = 14 LLM calls per audit (one critic + one optional revise per agent). At ~$0.20 per call, max ~$2.80 of inner-loop overhead per audit. R28 mutation space lets evolve toggle which roles opt-in based on observed score deltas across generations.
- Malformed SubSignals: logged to `gap_report.md`, `score=null` in fitness (not zero per institutional learning)

**Execution note:** Test-first for `subsignals.parse` — malformed-input handling is the most error-prone path and the null-vs-zero semantics are novel.

**Technical design:** *(directional guidance, not implementation specification)*

Stage 2 has no direct asyncio-subprocess precedent in the codebase (autoresearch's evolve runs meta agents sequentially via `subprocess.Popen + select.select`; harness uses `ThreadPoolExecutor + threading.Lock` for parallel work). This is part of the multi-session orchestration pattern named in Key Tech Decisions — Stage 2's choice to fan out 7 parallel `claude -p` subprocesses (vs 1 long agentic session) is justified by per-lens resume granularity, per-agent token-window isolation, and parallel wall-clock; R28 reserves the right to evolve toward N-broad-agents or 1-long-session if Stage 2 cost dominates.

**Sync/async boundary contract:** the `marketing_audit` lane runner exposes a sync entrypoint (`run_audit_sync(audit_id, archive_dir) -> int`) that wraps `asyncio.run(run_audit(audit_id, archive_dir))`. **The actual sync caller is `autoresearch/evaluate_variant.py` (~`:698` Popen)** — that's the lane-program scoring path that evolve runs route through, not `evolve.py` directly. The live wrapper `freddy audit run` invokes `run_audit_sync` directly (no subprocess; runs in the freddy process).

**Cleanup contract** (replaces prior overstated "atomically" claim):
1. Stage 2's asyncio child spawns use **`asyncio.create_subprocess_exec(..., start_new_session=False)`** (the asyncio default) so children stay in the parent's process group. This means SIGTERM-of-parent propagates via the kernel's process-group delivery semantics — children receive SIGTERM and Stage 2's `_run_agent` wrapper catches the signal-driven cancellation, writing partial state.
2. The lane runner registers atexit + SIGTERM/SIGINT handlers per Unit 5 (`SIGTERM → wait 5s → SIGKILL` escalation borrowed from `harness/worktree.py:349-379`). Wait-and-escalate is NOT atomic — it's the explicit non-atomic pattern Unit 5 already specifies; orphan-leak risk is bounded to the 5s wait window, not silent.
3. When `evaluate_variant.py` ran the lane via `subprocess.Popen`, its `os.killpg` cleanup reaches the lane runner's process group **only** because (1) holds — children share the group. If any future Stage 2 spawn opts into `start_new_session=True`, that child becomes a session leader and `killpg(parent_pid)` does NOT propagate; track all in-flight Stage-2 PIDs in `AuditState.stage2_pids: list[int]` and explicitly killpg each on shutdown as defense-in-depth.

This contract is **consistent with Unit 5's "no backend process group" framing** — Unit 5 describes the per-call `claude -p` cleanup (one subprocess per stage call, cleaned up by the caller's with-block); Unit 10's process-group story is about Stage 2's parallel fan-out, which Unit 5 doesn't model. Both are true at their respective scopes; together they specify the full cleanup picture.

The net-new coordination pattern needs three layers beyond a naive `asyncio.gather`:

```
subscription_burst_lock  (asyncio.Lock, single-slot)
   ↓  stagger spawns by ≥10s
dispatch_semaphore       (asyncio.Semaphore, size=7)
   ↓  caps in-flight agents
agent_task wrapper       (catches exceptions + records name alongside result)

async def _run_agent(name, lens_assignment):
    async with subscription_burst_lock:
        await asyncio.sleep(STAGGER_SECONDS)  # 10s between spawns
    async with dispatch_semaphore:
        if state.pause_reason or state.graceful_stop_requested:
            return (name, _SkippedReason(state.pause_reason or "graceful_stop"))
        try:
            return (name, await agent_runner.run(agent_name=name, ...))
        except RateLimitHit as e:
            state.mutate(lambda s: setattr(s, "pause_reason", "rate_limit"))
            return (name, e)
        except Exception as e:
            return (name, e)

tasks = [_run_agent(a.name, a.lenses) for a in agents]
results = await asyncio.gather(*tasks)  # NOT return_exceptions; _run_agent catches internally
```

Re-implements the stagger-spawn idiom from `harness/run.py:661-678` (threading: `threading.Lock()` + `time.sleep(gap)`) in asyncio (`asyncio.Lock` + `await asyncio.sleep`) — distinct concurrency primitive, not a literal port. Validate cross-event-loop semantics under the single `asyncio.run()` entrypoint. (Subscription-burst avoidance — 7 concurrent claude subprocesses on 1 subscription account trip 1-allowed + 6-rejected on first-second burst.) The `_invoke`-style wrapper borrows from `src/audit/preflight/runner.py:100-110` so one agent's exception never cascades through peers. Per-lens resume uses the atomic-per-lens write pattern (`stage2_subsignals/L<id>_<slug>.json`) + a `completed_lenses: list[str]` field in `AuditState` — Stage 2 skips any lens ID already in that set when resuming.

**Patterns to follow:**
- Pattern A from `src/audit/claude_subprocess.py`
- `autoresearch/evolve.py:_build_meta_command` shape for long-form claude invocation
- `asyncio.gather(return_exceptions=True)` pattern — NOT `TaskGroup` (fail-fast)
- Skip-not-raise pattern: `harness/findings.py:68–90` if it exists (otherwise custom)

**Test scenarios:**
- Happy path: 7 agents run in parallel, each producing SubSignals for its ~21 lenses; all write to stage2_subsignals/
- Happy path: Semaphore(7) limits concurrent subprocesses
- Edge case: one agent fails with rate-limit exception → other 6 complete, partial state preserved, pause_reason set
- Edge case: one agent outputs malformed SubSignal → logged to gap_report.md, score=null, other SubSignals from same agent preserved
- Edge case: graceful_stop set mid-fan-out → remaining agents not dispatched, current agents allowed to finish
- Edge case: lens-level resume — restart Stage 2 after 14 of 147 lenses completed → only 133 dispatched
- Error path: SubSignal missing required field → `MalformedSubSignalError` logged, NOT raised
- Error path: agent exceeds per-call token cap → cost_ledger halts at threshold, state preserved
- Integration: Stage 2 end-to-end on fixture brief produces N SubSignals across 7 agents; gap_report.md has 0–K entries depending on rubric-coverage
- Integration: inner loop opt-in for role "Competitive" revises once on critic fail; persists

**Verification:**
- Fixture run produces correct SubSignal count per agent (sum ≈ 149 for always-on)
- Malformed inputs logged to gap_report.md, not in stage2_subsignals/
- `asyncio.gather(return_exceptions=True)` preserves partial completion on 1-agent failure
- Per-lens resume correctly skips completed lenses

---

- [ ] **Unit 11: Stages 3–4 — synthesis + proposal**

**Goal:** Stage 3 aggregates SubSignals → ParentFindings (~25–32 strategic findings). Stage 4 produces 3-tier proposal (Fix-it/Build-it/Run-it) with fixed pricing anchors.

**Requirements:** R7, R11 (3-tier proposal with fixed pricing), R12 (SubSignal → ParentFinding aggregation).

**Dependencies:** Units 2–10.

**Files:**
- Create: `src/audit/synthesis.py` (SubSignal → ParentFinding aggregation logic; severity rollup = max of children, confidence = floor)
- Create: `src/audit/stages/stage_3_synthesis.py` (one Pattern-B claude session producing findings.md + report.md + report.json)
- Create: `src/audit/stages/stage_4_proposal.py` (one Pattern-B claude session producing proposal.md with 3-tier structure + fixed pricing anchors)
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_3_synthesis.md`
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_4_proposal.md`
- Create: `tests/audit/test_synthesis.py`
- Create: `tests/audit/stages/test_stage_3_synthesis.py`
- Create: `tests/audit/stages/test_stage_4_proposal.py`

**Approach:**
- Synthesis: group SubSignals by `ReportSection` (9 sections from `agent_models.ReportSection` Literal); aggregate via severity=max + confidence=floor rollup already in `agent_models.py`; cluster related SubSignals into ParentFindings ranked by cost-of-delay × effort-ratio (per R26 deliverable IA)
- Stage 3 claude session reads SubSignals + brief; produces `findings.md` (structured), `report.md` (narrative), `report.json` (machine-readable schema)
- Stage 4 claude session reads findings + capability hints; produces `proposal.md` with Fix-it/Build-it/Run-it tiers + fixed pricing anchors (pricing anchors are a template variable; JR supplies specific numbers)
- Cost ~$5-10 Stage 3 + $1-2 Stage 4 per R10

**`findings.md` 9-section schema (locked; matches `agent_models.ReportSection` Literal):**

```markdown
# Marketing Audit — <prospect-domain>
**Audit ID:** <uuid> | **Generated:** <iso-timestamp> | **Variant:** <variant_id>

## 1. Executive Summary
**Health Score:** <0-100>/100 (color: <Green|Amber|Red>)

**Top-3 Actions** (ranked by cost-of-delay × effort-ratio):
1. <action title> — Section: <name>; Severity: <S0-S3>; CoD×Effort: <score>
2. <action title> — ...
3. <action title> — ...

**Audit metadata:** lenses fired: <count>/149 always-on + <count> bundle; subscription window used: <NN>%; cost: $<amount>

## 2. Findability (SEO + GEO + LLM-Optimization)
**Section health:** <Green|Amber|Red> (<score 0-10>)
### Findings (<count>)
<for each ParentFinding:>
#### <Finding title>
- **Severity:** <S0|S1|S2|S3>
- **Supporting evidence:** <count> SubSignals from lenses [L###, L###, ...]
- **Recommended action:** <one-line action>
- **Cost-of-delay × effort-ratio:** <numerical priority score>
- **Confidence:** <high|medium|low> [(if low: rationale)]
- **Detail:** <2-3 paragraphs of evidence-grounded explanation>

## 3. Brand & Narrative
[same per-section schema]

## 4. Conversion & Lifecycle
[same]

## 5. Distribution & Channels
[same]

## 6. MarTech & Attribution
[same]

## 7. Monitoring & Operational
[same]

## 8. Competitive Intelligence
[same — note: per MA-3, must name prospect's losses, not puff-piece]

## 9. Data Gaps & Confidence Calibration
**Lenses skipped:** <count> (see `dispatch_rationale.md` for full list)
**Failed enrichments:** <list of attach-* enrichments unavailable>
**Confidence-lowered findings:** <list of finding IDs where confidence was floored due to gap>

[per MA-8, this section MUST exist even if empty — explicitly state "no data gaps" rather than omit]
```

**Structural validator (Unit 15) checks:**
- All 9 H2 section headers present in exact order
- Section 1 has Health Score (0-100), Top-3 Actions (exactly 3), audit metadata
- Sections 2-8 each have at least a Section health line + Findings sub-header (zero findings is acceptable; section is not omitted)
- Section 9 always present (even if "no data gaps")
- ParentFindings cite SubSignal lens_ids; severity ∈ {S0, S1, S2, S3}; confidence ∈ {high, medium, low}
- Section names match `agent_models.ReportSection` Literal exactly (drift = structural reject)

**`proposal.md` 3-tier schema (locked):**

```markdown
# Proposed Engagement — <prospect-domain>
**Audit ID:** <uuid> | **Generated:** <iso-timestamp>

Based on the audit findings, three engagement options are sized for different commitment levels and outcomes:

## Fix-it (One-shot, 30 days)
- **Engagement:** 30-day fixed-scope sprint
- **Investment:** $<from-pricing-anchor-Fix-it>
- **Best for:** <prospect-profile-fragment, e.g., "teams with 1-2 named priorities">
- **What this tier delivers:**
  - Addresses Findings #<id>, #<id>, #<id> (typically S0/S1 highest CoD×Effort)
  - <specific outcome>
  - <specific deliverable shape>
- **What we won't do at this tier:**
  - <explicit exclusion 1 — to make Build-it differentiated>
  - <explicit exclusion 2>

## Build-it (60-90 days)
- **Engagement:** Multi-sprint engagement, named outcomes
- **Investment:** $<from-pricing-anchor-Build-it>
- **Best for:** <prospect-profile-fragment, e.g., "teams ready to invest in 3-4 systemic improvements">
- **What this tier delivers:**
  - <typically 3-5 findings spanning 2-3 sections>
  - <named integration / build outputs>
  - <named handoff to in-house team>
- **What we won't do at this tier:**
  - <exclusion 1 — to differentiate from Run-it>

## Run-it (Ongoing, 6+ months)
- **Engagement:** Embedded ongoing partnership; quarterly review cycles
- **Investment:** $<from-pricing-anchor-Run-it>/month
- **Best for:** <prospect-profile-fragment, e.g., "teams without senior in-house marketing leadership">
- **What this tier delivers:**
  - Continuous monitoring + adaptation per Section 7 findings
  - Quarterly priority resets
  - Embedded in roadmap planning
- **What we won't do at this tier:**
  - <exclusion: scope-creep guards — what does NOT belong in retainer>

---

## Notes for prospect
- Pricing reflects scope, not hourly billing. If your situation differs from these tiers, we can size a custom engagement.
- All tiers include a kickoff call and a final readout; Build-it and Run-it include named in-flight checkpoints.
```

**Pricing-anchor template variables:** Stage 4 prompt includes `<from-pricing-anchor-Fix-it>`, `<from-pricing-anchor-Build-it>`, `<from-pricing-anchor-Run-it>` placeholders. JR supplies values via `configs/audit/pricing_anchors.yaml` (per-vertical or default). If the file is missing or values are placeholders, Stage 4 fails with `MissingPricingAnchors` — never ships a proposal with `$TBD`.

**Structural validator (Unit 15) proposal.md checks:**
- 3 H2 headers in exact order: "Fix-it", "Build-it", "Run-it"
- Each tier has all 5 sub-fields (Engagement, Investment, Best for, What this tier delivers, What we won't do at this tier)
- Investment value is a parsed dollar amount, NOT `$TBD` or `$<placeholder>` (regex check)
- Each tier references at least one finding ID from `findings.md` Section 2-9 (not just Section 1 Top-3)

**Patterns to follow:**
- Pattern B from `src/audit/claude_subprocess.py`
- `src/competitive/brief.py` synthesis pattern if it exists
- Severity rollup from `src/audit/agent_models.ParentFinding.validate_rollup`

**Test scenarios:**
- Happy path: 100 SubSignals across 9 sections → ~25 ParentFindings, severity rollup correct, confidence=floor
- Happy path: Stage 3 produces findings.md with 3 sections (executive summary, findings, methodology) per R26
- Happy path: Stage 4 proposal has 3 distinct tiers with pricing anchors substituted from template
- Edge case: SubSignals with null score (from malformed inputs in Stage 2) excluded from ParentFinding aggregation
- Edge case: empty SubSignals for a section → section omitted from findings.md, not crashed
- Error path: Stage 3 claude session fails mid-synthesis → state preserved, resumable
- Integration: Stage 2 → 3 → 4 chain on fixture produces findings.md + report.md + report.json + proposal.md
- Integration: top-3 actions in findings.md ranked correctly per cost-of-delay × effort formula

**Verification:**
- Fixture synthesis produces expected ParentFinding count + severity rollup
- Proposal tiers match R11 structure
- No crashes on null-score SubSignals

---

### Phase 3 — Deliverable + publish (Bundle C; deliverable-serving Worker in v1; intake-form Worker deferred to v1.5)

- [ ] **Unit 12: `render.py` + consultant-memo templates**

**Goal:** Render HTML + PDF deliverables from Stage 3 findings.md + Stage 4 proposal.md per R26 deliverable IA (consultant-memo, not dashboard). Port the sanitization + template pattern from `src/competitive/pdf.py`.

**Requirements:** R6 (HTML+PDF deliverable with branded footer + mobile single-column + UUID4 suffix), R26 (consultant-memo deliverable IA).

**Dependencies:** Unit 11.

**Files:**
- Create: `src/audit/render.py` (port of `src/competitive/pdf.py:render_brief_pdf` for audit shape)
- Create: `src/audit/templates/deliverable.html.j2` (consultant-memo layout per R26)
- Create: `src/audit/templates/deliverable_print.css` (print-specific CSS for PDF rendering)
- Create: `src/audit/templates/free_scan.html.j2` (narrow teaser for scan depth per R1)
- Create: `tests/audit/test_render.py`

**Approach:**
- `render.py`: `render_audit_deliverable(findings_md, proposal_md, brief_json, client_name, uuid_slug) -> tuple[str, bytes]` returning HTML + PDF bytes
- Markdown → HTML via `markdown` package with `["tables", "fenced_code", "toc"]` extensions
- `nh3.clean()` sanitization with explicit allowed tags/attrs from `src/competitive/pdf.py:14–30`
- Jinja2 `PackageLoader("src.audit", "templates")` with `StrictUndefined` + `autoescape=select_autoescape(["html","j2"])`
- WeasyPrint `_safe_url_fetcher` SSRF guard from `src/competitive/pdf.py:33–40`; `base_url="about:blank"`
- `asyncio.Semaphore(2)` for CPU-bound concurrency cap
- Deliverable structure per R26:
  1. Executive summary + health score band (top)
  2. Top-3 actions by cost-of-delay × effort-ratio
  3. Findings grouped by marketing area, severity visual weight, collapsed-by-default in HTML, expanded in PDF
  4. Proposal tiers with fixed anchors
  5. Methodology appendix
- Mobile-first single-column layout per R6 (B2B shareable links opened on mobile)
- "Prepared by GoFreddy · gofreddy.ai" branded footer preserved on external share

**Patterns to follow:**
- `src/competitive/pdf.py` line-by-line — directly portable
- Jinja2 autoescape + StrictUndefined (fail loud on missing template vars)

**Test scenarios:**
- Happy path: fixture findings + proposal → HTML rendered correctly, nh3 sanitization strips script tags
- Happy path: PDF rendered via WeasyPrint, includes branded footer, mobile-friendly layout
- Edge case: findings.md with malicious inline script/iframe → stripped by nh3
- Edge case: missing template variable → `StrictUndefined` raises (fail loud, not silent blank)
- Edge case: external image URL in findings.md → `_safe_url_fetcher` blocks, fallback placeholder
- Error path: WeasyPrint render failure → propagates; does NOT silently skip PDF
- Integration: full audit fixture → HTML + PDF pair rendered, both include all 9 marketing areas
- Integration: free_scan template renders narrow teaser (2-3 findings) at depth=scan

**Verification:**
- Fixture findings produce valid HTML + PDF
- `nh3` strips unsafe tags; Jinja2 fails loud on missing vars
- PDF renders without external resource fetches

---

- [ ] **Unit 13: `publish.py` + R2 document storage + UUID slug + minimal deliverable-serving Worker**

**Goal:** Ship Stage 6 publish logic. Upload HTML+PDF to R2 via a new `R2DocumentStorage` class (existing `src/storage/r2_storage.py` is video-shape and incompatible); generate UUID4 slug; serve via a minimal Cloudflare Worker on the response path that injects `X-Robots-Tag: noindex` (R2 cannot set arbitrary response headers at upload time — `S3.upload_file ExtraArgs` only takes `ContentType`, and `Metadata={...}` only sets `x-amz-meta-*` user metadata, not the `X-Robots-Tag` response header that crawlers consume). **The intake-form Worker is deferred to v1.5** (operator-fired scan via `freddy audit run --depth scan` covers v1 intake), but the deliverable-serving Worker is v1 because R6 noindex is a security requirement, not a nice-to-have.

**Requirements:** R6 (public URL at reports.gofreddy.ai/<uuid4>/ with UUID enumeration defense + `X-Robots-Tag: noindex`; ≥122 bits entropy), R1 (scan via operator-fired `freddy audit run --depth scan`; auto-fire scan + intake-form Worker deferred to v1.5).

**Dependencies:** Unit 12.

**Files:**
- Create: `src/audit/publish.py` (UUID4 slug gen, R2 upload helpers — uploads via R2DocumentStorage; **does NOT attempt to set X-Robots-Tag at upload time** — header injection happens on the Worker response path)
- Create: `src/storage/r2_document_storage.py` (~40 LOC; `R2DocumentStorage` class with `upload(slug, filename, content_type, body) -> str` for uploading `.html` + `.pdf` to `documents/<uuid4>/<filename>` paths; aioboto3-based; sibling to existing `r2_storage.py` (video-shape) and `r2_media_storage.py`)
- Create: `src/audit/stages/stage_5_deliverable.py` (wraps render.py)
- Create: `src/audit/stages/stage_6_publish.py` (wraps publish.py + writes lineage.jsonl row)
- Create: `cloudflare-worker/wrangler.toml` (minimal Worker config — only the deliverable-serving Worker; intake-form Worker NOT included in v1)
- Create: `cloudflare-worker/src/deliverable.ts` (~20 LOC: fetches R2 object via Worker bindings or origin proxy; injects `X-Robots-Tag: noindex` + `Referrer-Policy: no-referrer` + `Cache-Control` into response headers; serves under reports.gofreddy.ai/*)
- Create: `cloudflare-worker/README.md` (deployment instructions for JR — only the deliverable Worker in v1)
- Create: `tests/audit/test_publish.py`
- Create: `tests/storage/test_r2_document_storage.py`
- Create: `tests/audit/stages/test_stage_5_deliverable.py`
- Create: `tests/audit/stages/test_stage_6_publish.py`

**Approach:**
- `R2DocumentStorage`: `upload(slug, filename, content_type, body) -> str` validates slug as UUID4, validates filename in `{report.html, report.pdf, findings.md, report.md, report.json}`, uploads to `documents/<slug>/<filename>` with `ExtraArgs={"ContentType": content_type}`. Returns `f"https://reports.gofreddy.ai/{slug}/{filename}"`. Mirrors `r2_storage.py` aioboto3 patterns but with document-shape paths.
- `publish.py`: `generate_slug() -> str` produces a bare `<uuid4>` (no client-name prefix per Key Decision security/competitive-intel reasoning); `upload_deliverable(slug, html_bytes, pdf_bytes, findings_md, report_md, report_json) -> str` uploads all 5 deliverable files to R2 via R2DocumentStorage; returns the public URL `reports.gofreddy.ai/<slug>/`. **No header-setting at upload time** — the Worker handles that.
- Stage 5 calls `render.render_audit_deliverable`, writes files to `deliverable/` (git-ignored per R21 split)
- Stage 6 uploads + writes `audits/lineage.jsonl` row with audit_id, client_slug, prospect_domain, published_at, deliverable_url, ma_scores (placeholder — filled by evolve), engagement_signal (null until T+60d)
- Cloudflare Worker (deliverable-serving only): single-purpose response-path mediator. Bound to `reports.gofreddy.ai/*` route. On every request, fetches the R2 object via Worker bindings (or via origin proxy if R2 binding unavailable in v1 setup), then mutates response headers to inject `X-Robots-Tag: noindex`, `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store`. ~20 LOC of TypeScript.
- Scan path in v1: JR fires `freddy audit run --depth scan --client <slug> --domain <host>` after Calendly intake. No public intake form in v1.

**Execution note:** R2 cannot set the `X-Robots-Tag` response header at upload time (verified against `src/storage/r2_storage.py` and S3 API surface — `ExtraArgs` only takes `ContentType`; `Metadata` sets `x-amz-meta-*` user metadata, not response headers). The deliverable-serving Worker is therefore the v1 mechanism for satisfying R6's noindex requirement. The Worker is intentionally minimal (~20 LOC, no rate-limit, no SSRF guard, no scan-form handling) — that machinery lives in the v1.5 intake-form Worker. JR ships R2 bucket + DNS + minimal deliverable Worker before Unit 13's Python code first runs end-to-end.

**Patterns to follow:**
- `src/storage/r2_storage.py` aioboto3 patterns (for R2DocumentStorage class shape)
- Cloudflare Workers + R2 binding docs for response-path header injection
- `src/common/url_validation.py` for any URL validation needed at scan-time

**Test scenarios:**
- Happy path: R2DocumentStorage uploads HTML+PDF to `documents/<uuid4>/{report.html,report.pdf}` paths, returns public URLs
- Happy path: Stage 5 render → Stage 6 upload chain; deliverable accessible at reports.gofreddy.ai/<uuid4>/
- Happy path: lineage.jsonl row written with all required fields
- Happy path: response from `reports.gofreddy.ai/<uuid4>/report.html` includes `X-Robots-Tag: noindex` (verified via curl against deployed Worker, not at upload time)
- Edge case: R2 upload fails → retried with exponential backoff via tenacity; state persisted
- Edge case: slug collision (UUID4 collision — astronomical) → regenerate
- Edge case: filename outside allowlist → `R2DocumentStorage.upload` rejects with `InvalidDeliverableFilename`
- Integration: full audit → publish chain → deliverable fetchable via public URL with correct security headers; browser renders correctly

**Verification:**
- Fixture deliverable uploaded, accessible via public URL
- UUID slug has ≥122 bits entropy, no enumeration
- Worker-mediated response headers include `X-Robots-Tag: noindex` (no search-engine indexing) + `Referrer-Policy: no-referrer`
- R2DocumentStorage rejects non-document filenames

---

- [ ] **Unit 14: `cli/freddy/commands/audit.py` full surface — split into 14a critical (5 cmds), 14b attach (4 cmds per R9), 14c hygiene (lazy)**

**Goal:** Extend the existing `cli/freddy/commands/audit.py` (111 lines, provider-call CLIs) with the marketing_audit orchestration surface, sequenced by criticality. **First paying audit needs 14a only**; 14b attach commands (all 4 v1 attach commands per R9) ship between audit 1 and audit 5 as prospects bring data; 14c hygiene commands ship lazily as operational pain warrants.

**Requirements:** R4 (invoice + mark-paid + payments.jsonl ledger), R7 (freddy audit run --client), R9 (**4 attach commands in v1: gsc + budget + winloss + ads**), R19 (record-engagement at T+60d, with optional walkthrough-survey flag at the same call), R25 (walkthrough-survey capture as `record-engagement --depth N --landed "..." --objection "..."` flag, not a separate subcommand).

**Dependencies:** Units 2–13.

**Files:**
- Modify: `cli/freddy/commands/audit.py` — three tiers, structurally:
  - **14a critical (5 commands, ~3 days, BLOCKS first paying audit):** `run`, `invoice`, `mark-paid`, `publish`, `record-engagement` (with optional `--depth N --landed "..." --objection "..."` flags for walkthrough-survey capture per R25, collapsing into one command). These 5 are the minimum surface for the audit-to-engagement loop.
  - **14b attach (4 commands, ~1.5-2 weeks, ships as prospects bring data):** `attach-gsc`, `attach-budget`, `attach-winloss`, `attach-ads` (Meta Ads Library + Google Ads Transparency ingest; ~1 week per origin R9). All 4 ship in v1 per origin R9 — no sub-deferral.
  - **14c hygiene (~7 commands, lazy ship between audit 1 and audit 5):** `verify-payments`, `verify-deliverables`, `verify-lineage` (recomputes per-stage `INPUT_HASH` from persisted inputs and compares to `state.sessions[stage].input_hash` per Key Decision §Multi-session orchestration consequence (a) — surfaces cross-stage poisoning if Stage 1b's brief.md is accidentally rewritten between Stage 1c and Stage 2), `archive-expired`, `pin-preview`, `window-budget`, `config` (with `--calibration-audits-remaining` flag), `status` (with `--engagement-due` and `--gate-status` flags — `--gate-status` computes the sequential-stop rule triggers (early-kill on first 5 zeros, early-expand on 3 conversions in trailing 5, leading-indicator gate average across walkthrough-survey ratings) so JR can run it weekly without manual spreadsheet math), `costs`, `resume` (operational; `republish` dropped — Tier 1 rollback can be a 5-line script when needed, doesn't earn a CLI command).
- Create: `src/audit/cli_entrypoints.py` (thin wrappers delegating to the stage runners + state management)
- Create: `src/audit/payments.py` (`payments.jsonl` append-only ledger, non-repudiable per R4)
- Create: `src/audit/enrichments/gsc.py` (attach-gsc: OAuth service-account credential validation + import)
- Create: `src/audit/enrichments/budget.py` (attach-budget: CSV/JSON parse into canonical `BudgetRollup` Pydantic model; validation; write to enrichments/budget.json)
- Create: `src/audit/enrichments/winloss.py` (attach-winloss: PDF/MD/CSV/DOCX parse; **mandatory Sonnet redaction pass** per R24 before persist; prompt-injection-hostile parsing)
- Create: `src/audit/enrichments/ads.py` (**attach-ads** the single v1 depth-driver: Meta Ads Library / Google Ads Transparency CSV ingest; normalize to canonical `AdCreativeSignals` schema; ~1 week of work per origin R9)
- Create: `tests/audit/test_cli.py`
- Create: `tests/audit/test_payments.py`
- Create: `tests/audit/enrichments/test_gsc.py`
- Create: `tests/audit/enrichments/test_budget.py`
- Create: `tests/audit/enrichments/test_winloss.py`
- Create: `tests/audit/enrichments/test_ads.py`

**Approach:**
- Typer subcommand group `app = typer.Typer(...)`; match existing style in `cli/freddy/commands/audit.py`
- `freddy audit run --client <slug> --domain <host> [--depth {scan,full}] [--resume <audit_id>]` — fires Stages 0–6 (scan = subset)
- `freddy audit invoice --email <addr>` — records invoice intent in state
- `freddy audit mark-paid <audit_id> --amount <n> --method {stripe,bank,wire} --ref <invoice-id>` — toggles state.paid=True + appends to `payments.jsonl` with all fields (non-repudiable)
- `freddy audit publish <audit_id>` — runs Stage 6 if not already
- `freddy audit record-engagement <audit_id> --usd <n> [--depth <1-5> --landed "<finding>" --objection "<txt>"]` — fills lineage.jsonl engagement field; if `--depth/--landed/--objection` flags supplied (R25 walkthrough-survey capture), writes `walkthrough-survey.json` in the same call. One command, two related signals — collapses what was previously a separate `walkthrough-survey` subcommand.
- 4 v1 attach commands (14b): `attach-gsc`, `attach-budget`, `attach-winloss`, `attach-ads` — each takes `--client <slug> [--file <path>]` and writes to `clients/<slug>/audit/<audit_id>/enrichments/<type>.json`
- Other deferred attach commands (per origin R9): stub commands rejecting with "deferred to v2" message

**Execution note:** Test-first for `payments.jsonl` ledger semantics — idempotency on double-mark-paid and the audit-trail schema are the non-obvious correctness requirements.

**Patterns to follow:**
- Existing typer style in `cli/freddy/commands/audit.py`
- `@handle_errors` decorator if present
- `from ..providers import emit` for output
- `autoresearch/events.py` flock pattern for `payments.jsonl` writes

**Test scenarios:**
- Happy path: `freddy audit run` end-to-end on fixture → Stages 0-6 complete, deliverable published
- Happy path: `freddy audit mark-paid` appends one row to payments.jsonl, toggles state.paid=True
- Happy path: `freddy audit record-engagement <id> --usd 15000` updates lineage.jsonl
- Happy path: `freddy audit record-engagement <id> --usd 15000 --depth 4 --landed "..." --objection "..."` writes both the lineage.jsonl engagement field AND walkthrough-survey.json (one command, two related signals per Unit 14 collapse)
- Happy path: each of 4 v1 attach commands writes structured enrichment file
- Edge case: `mark-paid` twice with same `--ref` → second call idempotent (no duplicate row, warning logged)
- Edge case: `freddy audit run --resume` on half-completed audit → resumes from `state.status`, skips completed lenses
- Edge case: `mark-paid` missing `--amount` → rejects with helpful error
- Edge case: 5 deferred attach commands → reject with "deferred to v2" message
- Edge case: attach-winloss on PDF with PII → Sonnet redaction pass strips names/companies/deal-sizes before persist
- Error path: attach-ads on malformed CSV → logs parse errors, rejects (doesn't silently accept partial)
- Integration: full scan flow — form submit → Worker → `freddy audit run --depth scan` → email sent
- Integration: full paid flow — invoice → mark-paid → run --client → publish → record-engagement (with --depth/--landed/--objection flags writing walkthrough-survey.json in same call)

**Verification:**
- All 14a + 14b commands (5 + 4 = 9) exist with help text in v1 ship; 14c hygiene commands (~7) ship lazily between audit 1 and audit 5
- payments.jsonl is valid append-only ledger (no duplicate refs, all rows parse as JSON)
- v2-deferred commands reject cleanly
- Redaction pass strips PII from win-loss before persist

---

### Phase 4 — Evaluation (Bundle D)

- [ ] **Unit 15: `src/evaluation/` extension + MA-1..MA-8 rubric + structural validator**

**Goal:** Register `marketing_audit` as an evaluation domain in `src/evaluation/`. Add the MA-1..MA-8 rubric (gradient scoring for MA-4 per R17). Ship the structural validator.

**Requirements:** R17 (MA-1..MA-8 rubric, gradient MA-4), R12 (structural validation: findings + report + proposal must exist).

**Dependencies:** Unit 1 (reconciled deps).

**Files:**
- Modify: `src/evaluation/models.py:160` — `EvaluateRequest.domain` Literal. Per the lane-registry refactor's `_assert_models_literal_matches()` runtime check (`autoresearch/lane_registry.py:202-214`), this Literal must match `lane_registry.workflow_lane_names()`. Add `"marketing_audit"` to the Literal tuple.
- Modify: `src/evaluation/service.py:_JUDGE_PRIMARY_DELIVERABLE` (`:49-56`) — add `"marketing_audit": ("findings.md",)` — **single primary deliverable, NOT a tuple-of-two**. The previous plan version specified `("findings.md", "report.md")` but `_build_judge_output_text` at `service.py:59-66` concatenates listed files via `\n\n`, and report.md is the narrative summary that cites findings.md content — concatenating both produces duplication that distorts MA-1..MA-3 judge scoring (existing monitoring lane was bitten by this exact pattern in 2026-04-17 per `service.py:43-48` comment). findings.md is the structured 9-section source; the judges score that. report.md ships in the deliverable bundle but is NOT a judge input. **Note:** `_DOMAIN_CRITERIA` is auto-derived from `lane_registry.LANES` post-refactor — Unit 17's LaneSpec entry sets `rubric_ids=("MA-1",..,"MA-8")`, which makes `lane_registry._DOMAIN_CRITERIA["marketing_audit"]` return the criteria list automatically. No separate `_DOMAIN_CRITERIA` edit needed in service.py.
- Modify: `src/evaluation/rubrics.py` — add 8 `RubricTemplate` instances MA-1..MA-8 with **8 transcribed prompt-string definitions** (`_MA_1 = """..."""` through `_MA_8 = """..."""` in the existing pattern; each ~50-100 LOC of rubric anchors + scoring band examples + edge cases + JSON output schema, matching the `_GEO_1..._GEO_8` quality bar already in the file). MA-4 has `kind="gradient"`. **Per Divergence Point #1 picked option (c) (resolved in Unit 16):** MA-4 stays band 0-10 internally; the score normalization happens at composite-fitness time (Unit 16's `marketing_audit_score` divides weighted_rubric_raw by 10.0). No RubricTemplate band extension needed; MA-4 contributes via the same gradient mechanism as MA-1..MA-3, MA-5..MA-8. **The `assert len(RUBRICS) == 40` bump lives in Unit 17** (single-source-of-truth for the registration surface).
- Create: `src/evaluation/structural.py:_validate_marketing_audit` — sync function defining the 9-section findings.md schema and 3-tier proposal.md schema locked in Unit 11. **No direct edits to `STRUCTURAL_DOC_FACTS` at `:405` or `STRUCTURAL_GATE_FUNCTIONS` at `:444` needed** — both dicts are now auto-derived from `lane_registry.LANES` post-refactor; Unit 17's LaneSpec entry sets `structural_doc_facts=(...)` and `structural_gate_functions=(...)` which makes the registry's derived re-exports populate these dicts automatically. The paired test in `tests/evaluation/test_structural.py` validates the LaneSpec fields stay in sync. **findings.md checks:** all 9 H2 headers present in exact order matching `agent_models.ReportSection`; Section 1 has Health Score (0-100) + exactly 3 Top-Actions + audit metadata; Sections 2-8 have section-health line + Findings sub-header; Section 9 always present; ParentFindings cite lens_ids; severity ∈ {S0,S1,S2,S3}; confidence ∈ {high,medium,low}. **proposal.md checks:** 3 H2 tier headers (Fix-it / Build-it / Run-it) in exact order; per-tier sub-sections (Engagement, Investment, Best-for, What-this-tier-delivers, What-we-won't-do-at-this-tier); each tier references at least one finding ID. **deliverables:** report.md exists (narrative), report.json exists + parses (machine-readable), report.html exists, report.pdf exists.
- Create: `src/evaluation/judges/marketing_audit.py` — audit-specific judge orchestration. **3-backend ensemble decision:** marketing_audit reuses the existing `GeminiJudge + OpenAIJudge + SonnetAgent` ensemble (consistency with GEO/CI/SB/MO; preserves robustness against single-backend failure modes). Cost compounds: 3 backends × 8 criteria × N variants × M fixtures per evolve generation (~$X per generation; sized empirically once first variants run). If post-calibration cost data shows ensemble dominates Bundle E budget, drop to 2-of-3 (Sonnet + one other) or single Sonnet — but DEFAULT to 3-backend in v1 ship to inherit existing infrastructure unchanged. Marketing_audit-specific handling needed: (a) MA-5 + MA-8 prompts must include explicit instruction to score "the decision to skip lenses against the dispatch rationale log written by Stage 1b, not just the results of lenses that fired" per Key Decision §Lens-dispatch coverage invariant — embed this in the `_MA_5` and `_MA_8` prompt strings, not as runtime logic; **also pass the full `configs/audit/lenses.yaml` catalog (or a compiled summary listing always-on lens IDs + bundle membership) into MA-5 and MA-8 judge context** so judges can independently flag obvious skipped-bundle cases without trusting the dispatch rationale (anti-Goodhart hardening: the rationale is written by the same agent stack producing the audit; without an independent reference, a self-justifying rationale could pass scoring); (b) MA-4 cost-discipline judge needs token-count input as part of judge context (existing GEO judges don't get this) — extend `_build_judge_output_text` for marketing_audit only.
- Create: `tests/evaluation/test_marketing_audit_rubric.py`
- Modify: `tests/evaluation/test_structural.py` — add marketing_audit cases

**Approach:**
- MA-1..MA-8 rubric criteria per R17 (one-line summaries below; **the actual ~50-100-line prompt content per criterion is JR-coordinated content authoring**, see Open Question §MA-1..MA-8 rubric prompt transcription):
  - MA-1 Observational grounding (gradient 0-10): every finding cites specific observation
  - MA-2 Recommendation actionability (gradient 0-10): named action + target + effort + timeframe
  - MA-3 Competitive honesty (gradient 0-10): prospect's losses named
  - MA-4 Cost discipline (**gradient 0-5**, distinct band — see Files for normalization): token efficiency at fixed quality
  - MA-5 Bundle applicability (gradient 0-10): dispatched bundles match detection signals — **prompt MUST instruct judge to read Stage 1b's `dispatch_rationale.md` and score the SKIP DECISIONS, not just dispatched-lens output, per anti-Goodhart Key Decision**
  - MA-6 Deliverable polish (gradient 0-10): HTML/PDF render cleanly with branding
  - MA-7 Prioritization (gradient 0-10): top-3 actions unmistakably separated by cost-of-delay × effort-ratio
  - MA-8 Data gap recalibration (gradient 0-10): failed enrichments named, confidence lowered accordingly — **prompt MUST instruct judge to score against the dispatch rationale log per anti-Goodhart Key Decision**
- 3-backend ensemble (Gemini + OpenAI + Sonnet) scores each variant: 24 LLM calls per variant × M fixtures per evolve generation; existing `_run_judges` orchestration in `service.py` handles fan-out + ensemble aggregation
- Structural validator checks file existence + parses + schema conformance; uses SubSignal/ParentFinding Pydantic schemas from `src/audit/agent_models.py`

**Execution note:** Test-first. Rubric correctness is the most-important v1 correctness property and fixtures-driven testing is the right pattern.

**Patterns to follow:**
- Existing RubricTemplate instances in `src/evaluation/rubrics.py` for GEO-1..GEO-8, etc.
- Existing structural validators in `src/evaluation/structural.py`
- Judge orchestration in `src/evaluation/judges/`

**Test scenarios:**
- Happy path: rubric scoring on fixture findings produces expected MA-1..MA-8 values
- Happy path: structural validator accepts valid marketing_audit deliverable
- Happy path: MA-4 gradient — variant with 50% token cost at 7/8 quality beats variant with 100% token cost at 8/8 under composite fitness
- Edge case: missing findings.md → structural validator rejects with specific error
- Edge case: findings.md with only 8 of 9 sections → structural warns, doesn't reject (skip-not-raise per R12)
- Edge case: proposal.md missing one of 3 tiers → structural rejects
- Error path: malformed SubSignal in findings.md → rubric scoring excludes that section (null), not zero
- Integration: end-to-end `src/evaluation/service.evaluate` on fixture audit → returns DomainResult with 8 criteria scored

**Verification:**
- Rubric produces expected scores on 3 fixture audits (ground-truth set)
- Structural validator catches 5 representative failure modes
- MA-4 gradient correctly favors token-efficient variants in composite fitness

---

- [ ] **Unit 16: Composite fitness function (R27) — implemented as LaneSpec callables**

**Goal:** Ship the composite fitness function per R27 as two callables wired into the LaneSpec contract: `marketing_audit_score` (custom_score — variant-time scoring, normalized to [0,1]) and `marketing_audit_objective_score` (custom_objective_score_from_entry — selection-time scoring, layers engagement-weighted fitness on top). Makes token efficiency first-class and catches evaluator drift pre-holdout-failure. Ships in v1 as **plumbing**: it has nothing to score against until marketing_audit holdout fixtures land (Bundle 10 §7.6, post-audit-3 with prospect consent), but shipping it in v1 means v1.5 doesn't need to ship Unit 16 + activate the evolve loop simultaneously — when fixtures land, the loop closes immediately. Cost ~3-4 days for v1; benefit = de-risked v1.5 ramp.

**Why two functions, not one:** the lane-registry contract separates variant-time scoring (`custom_score`, called once per variant during evaluate) from selection-time scoring (`custom_objective_score_from_entry`, called per lineage row during frontier ranking). marketing_audit needs both because engagement signal is time-varying — it arrives T+60d after audit publish, so it can't be folded into the variant-time score. variant-time fixed quality + selection-time engagement-weighted overlay = the right factoring.

**Requirements:** R27 (composite fitness), R17 (MA-4 gradient contributing), R29 (latency penalty in fitness), R19 (engagement-weighted time-varying fitness).

**Dependencies:** Unit 15 (rubric criteria + judges) + lane-registry refactor on `main` (provides `LaneSpec.custom_score` + `LaneSpec.custom_objective_score_from_entry` hooks + shared `lane_registry.default_objective_score_from_entry` for fallback semantics).

**Files:**
- Create: `src/audit/__init__.py` (if not present from earlier units).
- Create: `src/audit/score.py` — defines `marketing_audit_score(config, variant_dir: str, parent_id: str) -> None` (custom_score callable, signature per `evolve.py:1609`; return ignored, function owns writing `scores.json` + lineage updates) and `marketing_audit_objective_score(entry: dict[str, Any]) -> float | None` (custom_objective_score_from_entry callable, signature per `lane_registry.py:181`; lane name is bound implicitly when registered). Both wired into LaneSpec at Unit 17.
- Create: `tests/audit/test_score.py` — fixture-driven tests of both functions; verifies normalization to [0,1] and engagement-weight ramp formula.

**Approach (variant-time scoring):**
- `marketing_audit_score(config, variant_dir: str, parent_id: str) -> None` is invoked at `evolve.py:1609`. **Critical:** this callable REPLACES `_score_variant_search` wholesale for marketing_audit — the substrate scorer at `evaluate_variant.py` and the suite-level aggregator at `:1180-1202` are bypassed entirely. The callable must internally: load fixture suite from `config`, run the standard 3-judge ensemble per criterion (existing `service._run_judges` infrastructure) yielding raw MA-1..MA-8 scores in `[0, 10]` per fixture, write `scores.json` to `variant_dir`, and append the per-variant lineage entry to `archive/lineage.jsonl` with the `search_metrics` shape below populated. Return value is ignored.
- Per fixture: compute `weighted_rubric_raw` = weighted sum of MA-N scores (weights below). Range: `[0, 10]`.
- **Normalize per Divergence Point #1 (option c):** `weighted_rubric_normalized = weighted_rubric_raw / 10.0`. Range: `[0, 1]`. This brings marketing_audit's externally-visible score into the same `[0, 1]` space as existing lanes — `select_parent.py:97` plateau threshold (`pstdev < 0.01`) stays calibrated; no `select_parent.py` edit needed. **Note:** the consumer of this normalization is `marketing_audit_objective_score`, which reads `entry["search_metrics"]["domains"]["marketing_audit"]["score"]`. Add a unit test asserting `_objective_score` output stays in `[0, 1.05]` for a hand-built entry (1.0 base + max 0.05 engagement contribution). Without this, the [0,1]-space invariant the plateau check depends on is not enforced anywhere.
- **No penalty terms** (LOCKED 2026-04-30 cross-plan review item A8):
  ```
  variant_score = weighted_rubric_normalized
  ```
  Final variant-time score range: `[0, 1]`. Cost as first-class is encoded via MA-4 (cost discipline rubric criterion); separate `cost_penalty × normalized_token_cost` and `latency_penalty × normalized_wall_clock` terms double-count with MA-4 and were dead-code paths (`0.0` placeholders) in v1. Matches harness_fixer K-5 discipline. If post-Gen-3 empirical data shows MA-4 underweights cost/latency, add penalty terms back via explicit decision record.
- **Bernoulli replay variance — phased** (LOCKED 2026-04-30 cross-plan review item A9): for Generations 1-3, each fixture is replayed twice and per-fixture score is the 2-replay mean. Detects single-shot self-report bias. Cost: ~2× per-fixture spend (~$60 → ~$120) for first 3 generations. Post-Gen-3, if observed variance < 10% σ across the 30-fixture holdout, drop to single-shot single-shot per-fixture (saves ~$94K/year at 1 gen/week steady-state cadence). Engagement-conversion (Judge-4 at T+60d) remains the ground-truth honesty check; Bernoulli is the synchronous backup.
- Aggregate across fixtures: geometric mean (matches existing-lane convention) of per-fixture scores (each per-fixture score is the 2-replay mean for Gen 1-3, single-shot post-Gen-3 if variance check passes). Result: `score` field for `search_metrics.domains["marketing_audit"]`.
- **Populate the full search_metrics shape Plan B promotion agents expect:** `{score, fixture_sd, fixtures, fixtures_detail, wall_time_seconds, results, active}`. Without `fixtures_detail` populated, Plan B's `is_promotable` agent sees empty per-fixture data and cannot consume marketing_audit results consistently with existing lanes.
- **Inner-vs-outer pass-rate telemetry per Divergence Point #7 (option b):** because `custom_score` REPLACES `_score_variant_search`, the substrate suite-level aggregator at `evaluate_variant.py:1180-1202` (which emits `mean_inner_pass_rate / mean_outer_pass_rate / mean_pass_rate_delta` for the existing 4 lanes) is **bypassed**, not reused. "Untouched" therefore means "no substrate edit + we own emitting these keys ourselves." Marketing_audit's `marketing_audit_score` MUST independently compute and write `inner_pass_rate / outer_pass_rate / pass_rate_delta` (per fixture) plus the `mean_*` rollups into the lineage entry's `search_metrics` so downstream consumers (`generations.jsonl` rollup, `eval_digest.md`, `evaluator-drift` telemetry) see non-null values. Recommended: import `evaluate_variant._extract_inner_pass_rate` for parity with the 4 existing lanes, OR re-implement and pin via a parity test that compares marketing_audit's pass-rate computation to the substrate's on a shared fixture. Without this, evaluator-drift detection (cluster-5 F5.4) silently disables for marketing_audit — the bug surfaces only as null cells in `eval_digest.md`.

**Approach (selection-time scoring):**
- `marketing_audit_objective_score(entry: dict[str, Any]) -> float | None` is called by `lane_registry.default_objective_score_from_entry` (which `frontier.objective_score` delegates to) per lineage row. Signature matches `lane_registry.py:181` — single `entry` arg; lane name is bound implicitly when the LaneSpec is registered.
- Step 1: read the variant's stored variant-time score (`entry["search_metrics"]["domains"]["marketing_audit"]["score"]`). If missing, return None.
- Step 2: read engagement signal aggregated for this variant from `autoresearch/metrics/marketing_audit/engagement_signal.jsonl` (Unit 18 writes this). If no T+60d-aged audits for this variant, engagement_weight stays at 0 → return variant-time score unchanged.
- Step 3: if engagement signal exists, compute final score:
  ```
  normalized_engagement = min(1.0, mean_signed_usd_per_variant / ENGAGEMENT_TARGET_USD)
  final_score = variant_time_score + engagement_weight × normalized_engagement
  ```
  Where `engagement_weight` ramps via the formula below (max contribution `0.05` in [0,1] space, scaled down from `0.5` in the prior [0,10] space to match the score's new range — preserves the relative weighting from the prior plan).

**v1 starting weights (locked; tunable post-calibration via critique manifest):**

```python
# Variant-time scoring (custom_score):
def weighted_rubric_score(ma_scores: dict[str, float]) -> float:
    """ma_scores: {MA-1..MA-8: float in [0,10]} (MA-4 already × 2 for normalization)."""
    return (
        0.15 * ma_scores["MA-1"]   # Observational grounding
      + 0.20 * ma_scores["MA-2"]   # Recommendation actionability — drives conversion
      + 0.10 * ma_scores["MA-3"]   # Competitive honesty
      + 0.10 * (ma_scores["MA-4"] * 2)  # Cost discipline (raw 0-5 × 2 = 0-10 normalized)
      + 0.10 * ma_scores["MA-5"]   # Bundle applicability
      + 0.10 * ma_scores["MA-6"]   # Deliverable polish
      + 0.15 * ma_scores["MA-7"]   # Prioritization — top-3 actions clarity
      + 0.10 * ma_scores["MA-8"]   # Data gap recalibration
    )
    # weights sum = 1.00; max raw = 10.0

def variant_time_score(ma_scores) -> float:
    """Variant-time fitness in [0, 1] space.

    LOCKED 2026-04-30: no penalty terms. Cost discipline encoded via
    MA-4 rubric criterion; latency observability via wall_time_seconds
    in search_metrics. Matches harness_fixer K-5.
    """
    raw = weighted_rubric_score(ma_scores)
    return raw / 10.0  # → [0, 1]
```

```python
# Selection-time scoring (custom_objective_score_from_entry):
ENGAGEMENT_TARGET_USD = 5000  # median expected paid engagement; tunable via critique manifest

def marketing_audit_objective_score(entry):
    # lane_name binding is implicit — registered as the marketing_audit LaneSpec callable.
    metrics = entry.get("search_metrics", {}).get("domains", {}).get("marketing_audit", {})
    variant_score = metrics.get("score")
    if variant_score is None:
        return None
    engagement = read_engagement_signal_for_variant(entry["variant_id"])  # from Unit 18 jsonl
    if engagement is None or engagement["mean_signed_usd"] == 0:
        return variant_score
    normalized_engagement = min(1.0, engagement["mean_signed_usd"] / ENGAGEMENT_TARGET_USD)
    weight = engagement_weight(entry["generation"], engagement["audits_aged_past_60d"])
    return variant_score + weight * normalized_engagement

def engagement_weight(generation, audits_aged_past_60d):
    """0.0 in v1; ramps to 0.05 max in v1.5+ (scaled to [0,1] space)."""
    if generation < 3 or audits_aged_past_60d < 6:
        return 0.0
    gen_ramp = min(1.0, (generation - 3) / 3)
    audit_ramp = min(1.0, (audits_aged_past_60d - 6) / 14)
    return 0.05 * gen_ramp * audit_ramp  # max contribution = 0.05 (5% of variant_score range)
```

**Weight rationale (unchanged from prior plan):**
- MA-2 (0.20) is highest because recommendation actionability is what makes the deliverable VALUABLE to prospects — drives the 2/10 conversion gate
- MA-1 + MA-7 (0.15 each) — observational grounding + top-3 prioritization are the readability anchors
- MA-3 + MA-8 (0.10 each) — honesty axes (competitive losses named, data gaps recalibrated)
- MA-4 + MA-5 + MA-6 (0.10 each) — efficiency, applicability, polish (important but not differentiators against the conversion target)

**Cost / latency penalty starting values: 0.0 in v1, tunable via critique manifest.** Existing 4 autoresearch lanes (geo/competitive/monitoring/storyboard) do NOT use cost or latency in selection — `wall_time_seconds` is observability only per `frontier.py:71-73` ("NOT a selection input after Phase 2"). Marketing_audit is the first lane to bake cost+latency into fitness. Without empirical variant cost/latency variance data, the proposed coefficients are guesses. **Default `cost_penalty = 0.0` and `latency_penalty = 0.0` for first 5 generations**; ramp via critique manifest only after observing actual variance. This matches existing-lane convention.

**Cost-penalty floor:** When cost_penalty is non-zero (post-calibration), only penalize OVER-median variants — `cost_penalty_effective = max(0, normalized_token_cost − 1.0)`. Under-median variants pay zero penalty; over-median variants pay proportionally. Preserves intent ("don't reward cannibalizing quality for token savings").

**Engagement signal normalization:** Raw `engagement_signal = mean(engagement_signed_usd) × (1 − 0.5 × low_confidence_pct)` is in raw USD ($5K-$15K typical). Normalized to [0, 1] via `min(1.0, mean_signed_usd / ENGAGEMENT_TARGET_USD)` where target ≈ $5000. With `engagement_weight ≤ 0.05`, max engagement contribution is `0.05 × 1.0 = 0.05` — 5% of the [0,1] variant_score range, proportional to the prior plan's `0.5 / 10.0 = 0.05` ratio.

**Execution note:** Test-first. Fitness function correctness determines which variants promote; a bug silently produces bad variants for paying customers.

**Patterns to follow:**
- `autoresearch/lane_registry.default_objective_score_from_entry` (provides the fallback semantics; marketing_audit's `custom_objective_score_from_entry` overrides it).
- `service._run_judges` for the 3-backend ensemble per criterion.
- Existing-lane geomean aggregation across fixtures (matches the `score` field shape Plan B agents expect).

**Test scenarios:**
- Happy path: 3 variants × 3 fixtures fixture suite; `marketing_audit_score` produces variant_time_score in [0, 1] for each; ranking matches hand-calculated expected.
- Happy path: variant A (8/8 rubric all criteria, cost_penalty=0) vs variant B (7/8 rubric, cost_penalty=0) → A wins (cost penalties off in v1).
- Happy path: `marketing_audit_objective_score(entry)` returns variant_time_score unchanged when no engagement data exists for the variant.
- Happy path: with engagement data + generation=4 + audits_aged_past_60d=10, `marketing_audit_objective_score` returns variant_time_score + engagement_weight × normalized_engagement.
- Happy path: `search_metrics.domains["marketing_audit"]` shape matches Plan B promotion agent's expected fields (score, fixture_sd, fixtures, fixtures_detail, wall_time_seconds, results, active).
- Happy path: per-fixture inner_pass_rate / outer_pass_rate / pass_rate_delta included in `custom_score` output (Divergence Point #7 telemetry).
- Edge case: all variants have equal rubric score → cost-penalty (when on, post-calibration) breaks tie.
- Edge case: low_confidence_pct=1.0 → engagement contribution halved per `1 − 0.5 × low_confidence_pct` formula.
- Error path: malformed rubric output → variant_time_score returns None (excluded from frontier ranking), not zero.
- Integration: full evolve cycle with marketing_audit lane registered; promote agent consumes search_metrics shape correctly.

**Verification:**
- Fitness ranking on fixture variants matches hand-calculated expected values in [0, 1] space.
- `select_parent.py:97` plateau detection (`pstdev < 0.01`) correctly identifies plateau on marketing_audit fixture variants without lane-specific threshold (verifies Divergence Point #1 picked option (c) works).
- Unit test asserts `marketing_audit_objective_score(entry)` output ∈ [0, 1.05] for hand-built entries spanning low/high rubric × no/full engagement (locks the [0,1]-space invariant the plateau check depends on).
- `marketing_audit_score` writes `mean_inner_pass_rate / mean_outer_pass_rate / mean_pass_rate_delta` to the lineage entry's `search_metrics` (parity test against `evaluate_variant._extract_inner_pass_rate` on a shared fixture).
- `tests/audit/test_score.py` green.

---

### Phase 5 — Lane + loop (Bundle E)

- [ ] **Unit 17: Register marketing_audit as a divergent lane via LaneSpec + programs/ files + eval_suites JSON**

**Goal:** Register `marketing_audit` as the 6th lane (5th workflow lane) by adding one `LaneSpec` entry to `autoresearch/lane_registry.py:LANES` with 4 of 5 `custom_*` callables wired (custom_score, custom_validate, custom_promote, custom_objective_score_from_entry; custom_mutate stays None — uses default meta-agent). Plus 2 minimal substrate edits for divergence axes outside the LaneSpec abstraction (per `docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md` §"Known Divergence Points"), the RUBRICS assertion bump, and 6 supporting creates. **Supersedes the pre-refactor 18-op shape** — the lane-registry refactor (shipped 2026-04-27, `main` HEAD `9549500`) consolidated 14+ enumeration sites as derived re-exports from `LANES`.

**Requirements:** R13 (lane-head variant at runtime), R14 (stage prompts externalized), R15 (evolution against fixtures), R17 (marketing_audit-specific scoring), R19 (engagement judge), R27 (cost-weighted fitness).

**Dependencies:** Units 2–16 (Unit 17 wires Unit 15's structural validator + Unit 16's `custom_score` function + Unit 18's `custom_validate` + `custom_promote` callables into the LaneSpec). The lane-registry refactor on `main` provides the contract; this Unit slots into it.

**Files:** (1 LaneSpec entry + 4 callable wires + 2 substrate edits + 1 assertion bump + 6 supporting creates + 1 test create + 1 test extension ≈ 11 ops total)

- Modify: `autoresearch/lane_registry.py:LANES` — add `LaneSpec("marketing_audit", ...)` entry. Data fields: `is_workflow_lane=True`, `rubric_ids=("MA-1","MA-2","MA-3","MA-4","MA-5","MA-6","MA-7","MA-8")`, `path_prefixes=("marketing_audit-findings.md", "programs/marketing_audit-session.md", "programs/marketing_audit/prompts/", "templates/marketing_audit", "workflows/marketing_audit.py", "workflows/session_eval_marketing_audit.py")`, `session_md_filename="marketing_audit-session.md"`, `deliverables=("findings.md", "report.md", "report.json", "report.html", "report.pdf")`, `intermediate_artifacts=("stage2_subsignals/L*_*.json",)`, plus `structural_doc_facts` + `structural_gate_functions` matching the validator built in Unit 15. Callables: `custom_score=src.audit.score.marketing_audit_score` (Unit 16), `custom_validate=src.audit.validate.marketing_audit_validate` (Unit 18 — manifest verification via shared `lane_registry.verify_manifest`), `custom_promote=src.audit.promote.marketing_audit_promote` (Unit 18 — pre-promotion smoke-test), `custom_objective_score_from_entry=src.audit.score.marketing_audit_objective_score` (Unit 16 — engagement-weighted time-varying fitness). `custom_mutate` stays `None` (uses default meta-agent).
- Modify: `src/evaluation/rubrics.py:1001` — bump `assert len(RUBRICS) == 32` → `== 40`. Without this, adding 8 MA-N rubrics fires the assertion at module import.
- Modify: `src/evaluation/structural.py:38-46` — add `marketing_audit` branch to the if/if/if dispatch routing to `_validate_marketing_audit` from Unit 15 (per Divergence Point #3 picked option (a): structural validator dispatch stays explicit because async asymmetry of `_validate_monitoring` makes data-driven dispatch hairy). 1-line addition; new validator is sync, no `await` keyword.
- Modify: `autoresearch/evaluate_variant.py:760` — extend `_INNER_PHASE_TAGS` frozenset with marketing_audit's stage event tags: `stage_2_lens, inner_critic, revise, stage_3_synthesis, stage_4_proposal` (per Divergence Point #6 picked option (a): 1-line allowlist edit beats per-LaneSpec field). Single definition, single consumer at `:830`. Without this extension, marketing_audit's `results.jsonl` phase events are silently filtered → `inner_pass_rate=None` for all fixtures.
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit-session.md` (L1 marker file ≤20 lines + pointer to prompts/ subdir; satisfies L1 at `evaluate_variant.py:584` — `program_path = variant_dir / "programs" / f"{domain}-session.md"`, iterates registry-derived `DOMAINS`).
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit-evaluation-scope.yaml` — canonical schema matching all 4 existing lanes: `{domain: "marketing_audit", outputs: [<scoreable artifacts>], source_data: [<judge inputs>], transient: [<scratch ignored>], notes: "<free-text>"}`. For marketing_audit: `outputs` = findings.md + report.{md,json,html,pdf}; `source_data` = brief.md + signals.json + dispatch_rationale.md + stage2_subsignals/L*_*.json; `transient` = events.jsonl + state.json + intermediate stage logs.
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_0_intake.md` (Stage 0 agent prompt — Python-only stage, minimal).
- Create: `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_1a_preflight.md` (Stage 1a orchestrator prompt).
- Verify: stage_1b_signals.md, stage_1c_brief.md, stage_2_lens_meta.md, stage_3_synthesis.md, stage_4_proposal.md, inner_loop_critic.md exist (Units 9-11).
- Create: `autoresearch/eval_suites/marketing-audit-v1.json` (5-fixture seed suite — placeholders per origin Deferred-to-Planning item 2; JR supplies actual fixture data before first evolve run).
- Modify: `autoresearch/test_lane_ownership.py` — extend for marketing_audit (test already iterates `lane_registry.LANES`; add lane-specific assertions for path_prefixes ownership + manifest path existence).
- Create: `tests/autoresearch/test_marketing_audit_lane.py` — exercises the LaneSpec entry: rubric_ids match RUBRICS dict keys, path_prefixes resolve, deliverables glob templates parse, callables import without circular-import errors.

**What this Unit does NOT touch (auto-derived from `lane_registry.LANES`):** `autoresearch/lane_runtime.py`, `autoresearch/lane_paths.py:WORKFLOW_PREFIXES`, `autoresearch/evolve.py` lane iteration (now `lane_registry.all_lane_names()` / `workflow_lane_names()`), `autoresearch/frontier.py:DOMAINS`/`LANES`, `autoresearch/evaluate_variant.py:DELIVERABLES`/`_INTERMEDIATE_ARTIFACTS`, `autoresearch/regen_program_docs.py:DOMAIN_FILENAMES`, `autoresearch/program_prescription_critic.py:DOMAINS`, `autoresearch/archive/current_runtime/scripts/evaluate_session.py:402` argparse, `tests/autoresearch/conftest.py:43`, `src/evaluation/service.py:_DOMAIN_PREFIXES`/`_DOMAIN_CRITERIA`, `src/evaluation/structural.py:STRUCTURAL_DOC_FACTS`/`STRUCTURAL_GATE_FUNCTIONS`. The lane-registry refactor consolidated these as derived re-exports from `LANES`. Adding marketing_audit to LANES makes them all pick it up automatically. **Also NOT touched:** `autoresearch/select_parent.py:97` plateau threshold — Divergence Point #1 resolved by Unit 16's score normalization to [0,1] instead of a substrate edit.

**Approach:**
- **Single-commit scope** for the LaneSpec entry + assertion bump + 2 substrate edits (lane-list registration is now a 4-edit diff, trivially reviewable). Supporting creates land as a follow-on commit.
- The 4 callables (custom_score, custom_validate, custom_promote, custom_objective_score_from_entry) are imported at `lane_registry.py` module load — they live in `src/audit/{score,validate,promote}.py` (Units 16 + 18 own those files). If the import path breaks, LaneSpec construction fails at module load with a clear ImportError, NOT silent runtime breakage.
- L1 marker file `marketing_audit-session.md` is thin (~20 lines): docstring + pointer to prompts/ subdirectory. Stage runners never read this file at runtime; they read `programs/marketing_audit/prompts/stage_*.md` directly via `Stage._load_prompt(name)` (Unit 9).
- eval_suites/marketing-audit-v1.json initially has 5 placeholder rows; v1 fail-closed promotion lock means no evolve runs in v1 — so placeholder is fine.

**Patterns to follow:**
- Worked example at `docs/architecture/lane-registry.md:74-87` ("Adding a divergent lane") — the marketing_audit illustrative example in that doc IS the contract this Unit instantiates.
- Existing 4 lanes' LaneSpec entries at `autoresearch/lane_registry.py:47-145` for path_prefix conventions + structural_doc_facts shape.
- `autoresearch/lane_registry.py:_assert_models_literal_matches` (`:202-214`) for the `models.py:160` Literal cross-check — callable (not module-load) to avoid circular import.

**Test scenarios:**
- Happy path: `lane_registry.workflow_lane_names()` returns 5-tuple including `"marketing_audit"`; `lane_registry.LANES["marketing_audit"]` returns the LaneSpec.
- Happy path: `evaluate_variant.layer1_validate` passes for marketing_audit variant (marker file present, RUBRICS contains MA-1..MA-8, structural facts paired with gate functions).
- Happy path: `lane_registry.DELIVERABLES["marketing_audit"]` returns the 5-tuple; `_has_deliverables` accepts it via the existing tuple-shaped consumer.
- Happy path: all 4 existing lanes still pass `_has_deliverables` (registry's derived re-exports preserve their tuples).
- Happy path: `lane_registry.LANES["marketing_audit"].custom_score is not None` (and similarly for custom_validate / custom_promote / custom_objective_score_from_entry).
- Edge case: missing `marketing_audit-session.md` marker file → L1 validation fails with specific error.
- Edge case: `regen_program_docs` iterates all 5 workflow lanes from registry without crashing.
- Error path: callable import failure at `lane_registry.py` module load → ImportError with traceback (NOT silent fallback to None).
- Integration: `autoresearch evolve --lane marketing_audit --iterations 1 --candidates-per-iteration 1` on 5 placeholder fixtures runs end-to-end (smoke; will fail-closed in v1 because no real fixtures + no promotion permitted).

**Verification:**
- All 5 workflow lanes pass `lane_registry._assert_models_literal_matches()` cross-check.
- `tests/autoresearch/test_lane_registry.py` (existing 23 tests) + `test_marketing_audit_lane.py` (new) green.
- `test_lane_ownership.py` passes for marketing_audit.

---

- [ ] **Unit 18: Engagement judge + custom_validate (manifest verification) + custom_promote (smoke-test) — implemented as LaneSpec callables**

**Goal:** Ship the three evolve-loop safety rails per origin Key Decisions, all wired into the LaneSpec contract: (a) engagement judge reading `audits/lineage.jsonl` for T+60d fitness signal (separate concern, NOT a LaneSpec callable — it's a long-loop offline aggregator); (b) `marketing_audit_validate` (custom_validate callable) that uses the shared `lane_registry.compute_manifest` + `verify_manifest` utilities to lock MA-1..MA-8 rubric prompts + judge prompts + stage prompts at lane-head ship time and re-verify on every variant scoring; (c) `marketing_audit_promote` (custom_promote callable) implementing pre-promotion smoke-test against holdout fixture. **Supersedes the pre-refactor shape** that proposed a standalone `marketing_audit_prompt_manifest.py` module + explicit `_check_critique_manifest` extension at `evaluate_variant.py:442-541` — the lane-registry refactor on `main` provides shared manifest utilities AND the `custom_validate` hook fires at scoring time, eliminating both the standalone module and the substrate edit.

**Requirements:** R17 (critique manifest SHA256 frozen), R18 (anti-Goodhart telemetry blindness), R19 (engagement judge T+60d), plus Customer-Facing Lane Key Decision (pre-promotion smoke-test).

**Dependencies:** Units 15, 16, 17. Unit 18 engagement_signal.jsonl output is consumed by Unit 16's `marketing_audit_objective_score` callable once T+60d-aged audits exist; in the v1 measurement window the signal is written but read only by v1.5 evolve runs.

**Files:**
- Create: `src/audit/judges/__init__.py`
- Create: `src/audit/judges/engagement.py` (long-loop offline aggregator: reads `audits/lineage.jsonl`, filters T+60d-aged rows, aggregates by `variant_id`, writes to `autoresearch/metrics/marketing_audit/engagement_signal.jsonl`. NOT a LaneSpec callable — runs as a scheduled job per Operational Notes; produces the signal that `marketing_audit_objective_score` reads).
- Create: `src/audit/validate.py` — defines `marketing_audit_validate(variant_dir, parent) -> bool` (the custom_validate callable wired in Unit 17's LaneSpec; signature per `evolve.py:1597` — receives both the variant dir and its parent dir). Uses shared `lane_registry.verify_manifest(variant_dir / "marketing_audit_manifest.json", variant_dir)` to verify the file-bytes manifest of MA-1..MA-8 rubric prompts + judge prompts + inner-loop critic prompt + stage prompts. Returns False if any file drifted (variant is `_safe_rmtree`'d at `evolve.py:1602-1604`). **Per Divergence Point #2 picked option (c):** `custom_validate` re-runs the manifest verification at scoring time (no separate clone-time snapshot infrastructure; the baseline `marketing_audit_manifest.json` is written ONCE at lane-head ship time alongside the LaneSpec, and `custom_validate` verifies on every subsequent variant). **Manifest enumeration is part of the contract** — see Approach below for the locked file-list policy.
- Create: `src/audit/promote.py` — defines `marketing_audit_promote(archive_dir: str, variant_id: str, lane: str) -> bool` (the custom_promote callable; signature per `evolve.py:1740` — receives archive root + variant id + lane name; resolve `variant_dir = Path(archive_dir) / variant_id` internally). Runs one-fixture smoke-test: scores the proposed winner against the holdout fixture, compares MA-1..MA-8 to current head, returns True only if no criterion regresses.
- Create: `src/audit/smoke_test.py` (helper: runs one fixture audit against a variant; returns MA-1..MA-8 scores. Imported by `marketing_audit_promote`).
- Create: `marketing_audit_manifest.json` (committed alongside lane-head; written ONCE by JR via `compute_manifest` at lane-head ship time. Lists all rubric/judge/stage prompt file paths + their SHA256 baselines. The custom_validate callable verifies the live tree against this file every time evolve scores a variant — drift is caught immediately, NO substrate edit to `evaluate_variant.py:_check_critique_manifest` needed).
- Create: `tests/audit/judges/test_engagement.py`
- Create: `tests/audit/test_validate.py` (covers `marketing_audit_validate` happy path + manifest drift detection).
- Create: `tests/audit/test_promote.py` (covers `marketing_audit_promote` happy path + regression rejection).
- Create: `tests/audit/test_smoke_test.py`

**Approach:**
- `engagement.py`: reads `audits/lineage.jsonl`; filters rows where `(now - published_at).days >= 60`; for each such row, reads `engagement_signed_usd` field; aggregates by variant_id; writes per-variant engagement signal JSONL
- Per R19, engagement weight = 0 for first 3 generations; this judge writes the signal but the fitness function (Unit 16) weights it

**Engagement judge thresholds (locked):**

```python
# Aging threshold for fitness inclusion
T_PLUS_AGING_DAYS = 60   # row included only if (now - published_at).days >= 60

# Confidence flagging — set low_confidence=True in signal output
LOW_CONFIDENCE_RECORDED_TOO_EARLY_HOURS = 24   # recorded <24h after audit = likely test data
LOW_CONFIDENCE_RECORDED_TOO_LATE_DAYS = 90     # recorded >90d after audit = memory-based estimate

def compute_confidence_flag(audit_published_at: datetime, recorded_at: datetime) -> bool:
    """True = low confidence; signal still aggregated but downweighted in fitness."""
    delta_hours = (recorded_at - audit_published_at).total_seconds() / 3600
    if delta_hours < LOW_CONFIDENCE_RECORDED_TOO_EARLY_HOURS:
        return True   # likely test data — flag and aggregate at half weight
    if delta_hours > LOW_CONFIDENCE_RECORDED_TOO_LATE_DAYS * 24:
        return True   # memory-based estimate — flag and aggregate at half weight
    return False

# High-value confirm threshold
HIGH_VALUE_USD = 15000   # amounts >= this require --confirm-high-value flag at record-engagement time

# Per-variant aggregation (when engagement signal feeds fitness)
def aggregate_variant_engagement(rows: list[LineageRow]) -> dict:
    """Groups by variant_id; computes mean usd, count, low_confidence_pct."""
    by_variant = {}
    for r in rows:
        by_variant.setdefault(r.variant_id, []).append(r)
    return {
        variant_id: {
            "mean_signed_usd": mean(r.engagement_signed_usd for r in vrows),
            "count": len(vrows),
            "low_confidence_pct": sum(r.low_confidence for r in vrows) / len(vrows),
            # signal contribution to fitness = mean_signed_usd × (1 - 0.5 × low_confidence_pct)
            # — so 100% low-confidence rows = half-weighted; 0% low-confidence = full-weighted
            "fitness_signal": mean(r.engagement_signed_usd for r in vrows)
                              * (1 - 0.5 * (sum(r.low_confidence for r in vrows) / len(vrows))),
        }
        for variant_id, vrows in by_variant.items()
    }
```

**Schema for `lineage.jsonl` engagement row** (locked):

```json
{
  "audit_id": "<uuid>",
  "variant_id": "<sha-of-promoted-variant-at-publish-time>",
  "client_slug": "<slug>",
  "published_at": "<iso-timestamp>",
  "engagement_recorded_at": "<iso-timestamp or null>",
  "engagement_signed_usd": <number or null>,
  "ref": "<invoice-id or contract-id>",
  "low_confidence": <bool>,
  "high_value_confirmed": <bool, true if usd >= HIGH_VALUE_USD>,
  "walkthrough_survey": {
    "depth_rating": <1-5 or null>,
    "landed": "<short string or null>",
    "objection": "<short string or null>"
  }
}
```

`record-engagement` CLI writes this row and refuses to overwrite existing engagement_signed_usd unless `--force` flag passed; a non-null value transitioning to a different non-null value emits `engagement-amend-attempted` event for audit-trail.
- `marketing_audit_validate(variant_dir, parent)` (custom_validate callable): two-step implementation. **Step 1:** call `lane_registry.verify_manifest(variant_dir / "marketing_audit_manifest.json", variant_dir)` for whole-file freeze of stage prompts (`programs/marketing_audit/prompts/stage_*.md`) + judge prompts + inner-loop critic. **Step 2 (LOCKED 2026-04-30 cross-plan review item A10):** for MA-1..MA-8 rubric prompts ONLY, run the section-marker diff check — parse `[STABLE]` / `[EVOLVABLE]` markers; verify every `[STABLE]` block byte-equals the v0-freeze copy. ~30 LoC diff post-processor. Rubric anchors (judge instructions, scoring schema, JSON contract) live inside `[STABLE]`; rubric exemplars (good/bad score examples) live inside `[EVOLVABLE]` and can mutate freely. The `parent` arg is unused for marketing_audit but required by the registry contract (`evolve.py:1597`). Returns False if either step fails; variant is `_safe_rmtree`'d.

  **Manifest enumeration policy (locked):** the manifest MUST list every file under `programs/marketing_audit/prompts/` plus the 8 MA-N rubric prompts + judge prompts + inner-loop critic prompt — gaps in the manifest = porous anti-gaming guard (a meta-agent could mutate any unlisted file undetected). Unit 18 ships:
  1. `tests/audit/test_validate.py` enumeration test that diffs `programs/marketing_audit/prompts/` directory contents against the manifest's keyset; FAILS if any prompt file is unlisted or any manifest key has no underlying file.
  2. `marketing_audit_manifest.json` itself listed in `LaneSpec.path_prefixes` (Unit 17) so `lane_paths.path_owned_by_lane` recognizes it as marketing_audit-owned and meta-agent edits to it are blocked by tier-B safety.

  **No standalone `marketing_audit_prompt_manifest.py` module needed** — the shared utilities at `autoresearch/lane_registry.py:217-242` are all that's required. **No `evaluate_variant.py:_check_critique_manifest` extension needed** — `custom_validate` fires per-variant at scoring time (between meta-agent mutate at `evolve.py:1551` and `custom_score` at `:1609`), which is when we need verification. Including stage prompts in the manifest mechanically blocks the evolve loop from migrating content authority out of `lenses.yaml` into stage-prompt text (catalog-content drift via prompt expansion) — closes the gaming surface flagged in re-review §Premise D.
- `marketing_audit_promote(archive_dir, variant_id, lane)` (custom_promote callable): runs `src/audit/smoke_test.py` against one holdout fixture, scores both variant (resolved as `Path(archive_dir) / variant_id`) and current head, returns True only if no MA-1..MA-8 criterion regresses. Hooks into `evolve.cmd_promote` automatically per the LaneSpec contract (NO direct `evolve.py` modification needed — the lane-registry refactor's `custom_promote` callable at `:1740` is the official extension point).
- Uses Plan B MVP holdout-v1 infra. **No cross-lane placeholder fixtures** — line 161 X.a fail-closed lock means smoke-test does not run in v1 (zero promotions; nothing to gate). When marketing_audit holdout fixtures land post-audit-3 (Open Question §Reader-readability + holdout-fixture sourcing), smoke-test activates against those fixtures only. Cross-lane fixture placeholder is X.b (rejected as design flaw at line 161 — passes MA-5/MA-6 degenerate cases).

**Execution note:** Test-first. Pre-promotion smoke-test is the primary customer-facing safety rail and characterization-test it against known-bad variants early. The custom_validate callable fires on EVERY scoring event (not just promotion), so manifest drift is caught the instant a variant introduces it.

**Patterns to follow:**
- `autoresearch/lane_registry.py:217-242` (`file_hash`, `compute_manifest`, `verify_manifest` shared utilities) — `marketing_audit_validate` calls these directly.
- `docs/architecture/lane-registry.md:91-112` ("Shared file-bytes manifest utilities") — worked example of compute-then-verify pattern.
- `autoresearch/compute_metrics.py:_run_claude_json` for short-shot judge calls inside the smoke-test.

**Test scenarios:**
- Happy path: 5 audits in lineage.jsonl, 3 aged past 60d → engagement judge writes signal for each variant.
- Happy path: `marketing_audit_validate` passes when variant tree matches `marketing_audit_manifest.json` baseline; returns True.
- Happy path: `marketing_audit_promote` passes for a proposed winner with equal-or-better scores; promotion proceeds via `evolve.cmd_promote`.
- Happy path: `marketing_audit_promote` rejects a proposed winner with regressive MA-1..MA-8 scores on holdout.
- Edge case: engagement_signed_usd = null (forgot to record) → excluded from aggregation, not counted as 0.
- Edge case: variant edits a stage prompt → `marketing_audit_validate` returns False (manifest mismatch); evolve discards variant without scoring; loud log line identifying which file drifted.
- Edge case: `marketing_audit_promote` runs with missing holdout fixture → **fail-closed**: returns False with `missing_smoke_test_fixture` error reason logged to `autoresearch/evolve_log.jsonl`. JR manually resolves (add fixture back OR pass `--force-promote` flag with rationale logged). Never silent-skip.
- Error path: smoke-test claude session fails → exception caught, `marketing_audit_promote` returns False with state preserved.
- Integration: full evolve cycle — variants generated → custom_validate (manifest check) → scored → custom_promote (smoke-test) → promoted (or rejected).
- Integration: T+60d engagement signal flows from `engagement.py` → `engagement_signal.jsonl` → `marketing_audit_objective_score` → frontier ranking; variants weighted accordingly after 3rd generation.

**Verification:**
- Engagement judge correctly signals for T+60d-aged audits.
- `marketing_audit_validate` rejects variants with manifest drift; `marketing_audit_promote` rejects regressive variants.
- `lane_registry.LANES["marketing_audit"].custom_validate is marketing_audit_validate` and similar for custom_promote (tests the wire-through).
- Manifest enumeration test (per locked policy above): every file under `programs/marketing_audit/prompts/` appears as a manifest key, and every manifest key resolves to an existing file. Test FAILS if either side has an extra entry — prevents porous-guard regressions when prompts are added/renamed.
- `marketing_audit_manifest.json` is recognized as marketing_audit-owned by `lane_paths.path_owned_by_lane` (covered by lane_paths conformance test extended in Unit 17).

---

- [ ] **Unit 19: Pin autoresearch evaluator + claude CLI in CI + docs**

**Goal:** Pin autoresearch evaluator at a specific commit per R20; pin claude CLI version per Key Decision (added during deepening); add CI checks that fail on drift; ship the pin documentation. **R29 subscription-window enforcement lives in Unit 4 (cost_ledger), not here** — Unit 4's Approach already specifies `duration_api_ms`-based SLA math, soft-warn at 40%, hard at 50%, halt-and-set-pause_reason. Unit 19 ships only the CI pins + docs, not the SLA code.

**Requirements:** R20 (autoresearch evaluator pinned at first ship), claude CLI version pin (Key Decision §Pinning, added during deepening for reproducibility on subscription-billed CLI).

**Dependencies:** Unit 17 (lane registration). (Unit 4 owns R29 — see `src/audit/cost_ledger.py` for the `duration_api_ms`-based SLA enforcement code, soft-warn at 40%, hard at 50% halt logic; Unit 19 ships independently of Unit 4.)

**Files:**
- Create: `.github/workflows/pins.yml` (single workflow with two jobs: `autoresearch-pin` verifies `autoresearch/` tree SHA matches pinned tag; `claude-cli-pin` verifies `claude` CLI version matches pinned version in `pyproject.toml`. Both fail on drift; failure messages include the pin-bump runbook URL.)
- Create: `docs/version-pins.md` (running doc: what's pinned, when, why; pin-bump runbook covers both autoresearch + claude CLI)
- Modify: `pyproject.toml` — add `autoresearch_pin_tag` + `claude_cli_pin_version` project metadata fields for ops visibility

**Approach:**
- Pin tag format: `autoresearch-audit-stable-YYYYMMDD`
- Autoresearch pin CI check: computes `git rev-parse HEAD:autoresearch/`; compares to pinned tag; fails if diverged (forces manual pin bump + smoke-test)
- Claude CLI pin CI check: parses `claude --version` output via `claude --version | awk '{print $1}'` (strips the trailing ` (Claude Code)` product-name suffix — verified against installed CLI which returns `2.1.120 (Claude Code)`); compares to `claude_cli_pin_version` in `pyproject.toml` via shell `==` test; fails if diverged
- **Audit-start preflight assertion (per Key Decision line 174):** `freddy audit run` first action is to invoke `claude --version`, parse via the same `awk '{print $1}'` shape, and compare to `pyproject.toml`'s `claude_cli_pin_version`. Mismatch raises `ClaudeCLIVersionMismatch` and aborts the audit before any subprocess fires. This is what protects against silent envelope drift on JR's local machine (CI alone protects PRs, not running audits)
- Pin-bump runbook (`docs/version-pins.md`): bump tag → re-run pre-promotion smoke-test (Unit 18) on fixtures → if green, commit new pin tag → CI passes
- Subscription-window enforcement is **NOT shipped here** — see Unit 4 (cost_ledger) which owns the `duration_api_ms`-based SLA math, soft-warn at 40%, hard at 50%, halt-and-set-pause_reason logic.

**Patterns to follow:**
- Existing CI workflows in `.github/workflows/`
- Pin-pattern in `harness/runs/` if any (otherwise greenfield CI)

**Test scenarios:**
- Happy path: pin tag matches → CI green
- Edge case: autoresearch drift detected in CI → fails with clear pin-bump instructions
- Edge case: claude CLI version mismatch → fails with version-pin instructions
- Error path: pin tag malformed → CI fails, blocks merge
- Integration: pin-bump runbook executes end-to-end on a synthetic drift event

**Verification:**
- CI check catches autoresearch drift
- CI check catches claude CLI version drift
- Pin tags visible to ops team via `pyproject.toml` metadata

---

- [ ] **Unit 20: v1 smoke-test + documentation + onboarding**

**Goal:** End-to-end v1 smoke-test confirming the full pipeline ships. Update documentation for the new audit CLI. Refresh ONBOARDING.md for the new module.

**Requirements:** All.

**Dependencies:** Units 1–19.

**Files:**
- Create: `tests/audit/test_smoke_end_to_end.py` (full `freddy audit run --client test-fixture --domain example.com --depth scan` + `--depth full` integration test; mocks external providers; validates deliverable)
- Modify: `docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md` — mark units complete as they ship
- Modify: `ONBOARDING.md` (if exists) — add audit engine section
- Modify: `README.md` — add v1 marketing audit usage example
- Create: `docs/audit-engine-user-guide.md` (operator guide: run an audit end-to-end, record engagement, troubleshoot)
- Create: `docs/audit-engine-ops-guide.md` (ops guide: deploy Cloudflare Worker, rotate R2 creds, tune subscription-window ceiling, pin autoresearch)

**Approach:**
- Smoke test covers full happy path + one representative error path (cost ceiling)
- User guide is concise (1-2 pages); targets JR running audits solo
- Ops guide captures the operator-side tasks not visible in user guide (Worker deploy, creds, autoresearch pin bumps)

**Patterns to follow:**
- Existing smoke tests in the repo
- Existing ONBOARDING.md shape if present

**Test scenarios:**
- Happy path: full paid audit from `freddy audit run` to deliverable upload
- Happy path: full scan from form submit to email
- Edge case: audit hits cost ceiling mid-Stage-2 → resumable, state preserved
- Edge case: resume after rate-limit → completes successfully
- Edge case: pre-promotion smoke-test rejects a bad variant in a follow-up evolve run

**Verification:**
- Smoke test passes in CI
- User + ops guides cover the documented workflows
- ONBOARDING.md reflects new module

---

## System-Wide Impact

- **Interaction graph:** New `src/audit/` module interacts with: `autoresearch/` (lane registration, variant materialization, evolve loop, fitness function, engagement judge), `src/evaluation/` (MA-1..MA-8 rubric, structural validator, composite fitness), `src/storage/r2_storage.py` (deliverable upload), `src/common/cost_recorder.py` (layered cost tracking), `src/common/url_validation.py` (Cloudflare Worker intake), `harness/` (direct-import of sessions, resume, graceful-stop primitives). New Cloudflare Worker interacts with: R2 bucket (public-read via Worker-mediated auth), external scan form submissions (public HTTPS endpoint).

- **Error propagation:** Typed exceptions from `src/audit/exceptions.py` bubble up through stage runners; each stage catches and persists state before re-raising. Preflight checks use skip-not-raise (failures become gap-flags, don't crash pipeline). SubSignals with malformed data log to `gap_report.md` as `score=null` (not zero, to avoid geomean corruption). Stage 2 parallel fan-out uses `asyncio.gather(return_exceptions=True)` so one lens failure doesn't cascade. Cloudflare Worker returns 4xx on intake validation failures; Python side never sees those.

- **State lifecycle risks:** `state.json` atomic writes via `checkpointing.atomic_update` prevent partial writes. `state.evolve_lock` mutex prevents concurrent live audit + evolve run. Per-lens SubSignal files under `stage2_subsignals/` enable per-lens resume without clobbering completed work. `payments.jsonl` append-only ledger with idempotency on `--ref` prevents double-mark-paid. `lineage.jsonl` populated incrementally (audit start → publish → engagement record); null engagement signal distinguishable from zero conversion.

- **API surface parity:** New CLI commands on `freddy audit`: **14a critical (5):** run, invoice, mark-paid, publish, record-engagement (with optional `--depth/--landed/--objection` flags collapsing R25 walkthrough-survey capture). **14b attach (4 per R9):** attach-gsc, attach-budget, attach-winloss, attach-ads. **14c hygiene (~7, lazy):** verify-payments, verify-deliverables, verify-lineage (input-hash recompute per Key Decision §Multi-session orchestration), archive-expired, pin-preview, window-budget, config (--calibration-audits-remaining), status (--engagement-due, --gate-status), costs, resume. Existing `freddy audit seo/competitive/...` provider-call commands unchanged (different namespace semantically — these are the low-level provider wrappers). Stable Cloudflare Worker endpoints in v1: GET /<uuid4>/* (deliverable-serving Worker, response-path `X-Robots-Tag: noindex` injection). v1.5 adds intake-form Worker endpoints (POST /scan/intake, GET /scan/<slug>/). No API version bumps needed; entirely additive.

- **Integration coverage:** Cross-layer tests required:
  - `cost_ledger` + `state` + pipeline runner → cost-breaker halt is resumable
  - Stage 1b → Stage 2 bundle dispatch → expected lens count per prospect profile
  - Stage 2 → Stage 3 SubSignal → ParentFinding aggregation
  - Render → R2 upload → Worker serve → browser renders correctly
  - `mark-paid` + `record-engagement` → lineage.jsonl → engagement judge → fitness signal
  - `autoresearch evolve` → smoke-test → promote → live audit uses new variant
  - evolve_lock mutex correctly blocks concurrent live + evolve

- **Unchanged invariants:** Existing autoresearch lanes (geo, competitive, monitoring, storyboard) continue to work post-DELIVERABLES-migration (single-element tuples preserve consumer behavior). Existing `src/evaluation/` consumers unchanged for geo/competitive/monitoring/storyboard domains. Existing `harness/` untouched (audit imports but doesn't modify). Existing `src/competitive/pdf.py` unchanged (audit ports pattern to `src/audit/render.py`). Claude subscription billing model + existing token-usage patterns in harness unchanged; audit adds its own cost_ledger layer on top of existing `src/common/cost_recorder.py`.

## Risks & Dependencies

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Autoresearch P0 gaps (Gap 2/6/18/30) land mid-project and change evaluator behavior | Medium | High | R20 pin evaluator at first ship; CI check (Unit 19) catches drift; mid-project pin bumps are explicit events with smoke-test requirement |
| 5h subscription window exhausts during multi-audit day | Medium | Medium | R29 50% ceiling per audit schedules ≤2 audits per window; soft-warn at 40% gives JR reaction time; `resume` after window reset |
| Deliverable-serving Worker (~20 LOC, v1) deploy delays Unit 13 ship | Low | Medium | Worker is minimal (no rate-limit, no SSRF, no scan-form); Python can ship + test via mocked R2 + curl-verified header injection while Worker deploys; JR's ops task on critical path. Intake-form Worker (v1.5) doesn't block v1. |
| Lens YAML transcription incomplete at Bundle B ship time | High | Medium | 10-lens sample unblocks Stage-2 dev; JR-coordinated multi-day content work; audits can run against partial catalog until fully transcribed |
| Variant regresses in production before smoke-test catches it | Low | Critical | Unit 18 pre-promotion smoke-test + evolve_lock mutex + 3 human gates all defend; variant promotion is rare event, not per-audit |
| Rubric SHA256 frozen but prompt updates lose CI-pin | Low | Medium | Unit 18 CI check on manifest + Unit 19 CI check on autoresearch pin both fail loud |
| Customer-facing deliverable has rendering bug visible to prospects | Medium | High | Unit 12 test suite + Unit 20 smoke test; manual review at R5 Gate 2 per audit; templates SHA256-frozen via critique manifest |
| Engagement signal never materializes (JR forgets to record) | Medium | Low | `record-engagement --depth/--landed/--objection` flags (Unit 14a) capture R25 walkthrough-survey leading indicator immediately at the same call as engagement recording; T+60d engagement recorded lazily; missing data excluded (null), not zeroed |
| Claude `total_cost_usd` envelope shape changes upstream | Low | Medium | Unit 3 parse function is the only dependency; upstream change is a claude CLI release event, not a repo change; pin CLI version in CI |
| Prospect PII leaks via git-committed state.json | Low | High | R21 git-split + `.gitignore` entries + Unit 1 verification; state.json contains operational telemetry only (audit_id, status, costs, sessions); prospect content lives in git-ignored dirs |
| Inner-vs-outer correlation telemetry misses drift | Low | Medium | Unit 16 threshold tunable; drift events logged but not gating; JR reviews weekly (ops guide) |
| Customer-facing deliverable has defect discovered post-publish | Medium | High | 3-tier rollback plan in Operational Notes (`republish` CLI for template fixes, `resume --from-stage` for content fixes, manual refund for unrecoverable); Tier 1 command exercised in Unit 20 smoke-test |
| Promoted variant degrades in production before next smoke-test cycle | Low | High | `autoresearch lane-head revert` mechanism + revert reason logged to `evolve_log.jsonl`; variant rollback exercised once on fixture before v1 ship |
| Smoke-test silently skips due to missing holdout fixture | Medium | High | Unit 18 changed to fail-closed (not silent-skip); fixture-presence check runs in Unit 19 CI |
| Python merges but deliverable-serving Worker deploys later; deliverables miss noindex header in gap | Medium | High | Unit 13 acceptance criterion requires Worker + Python lockstep E2E test (curl -vI verifies `X-Robots-Tag: noindex` on deployed Worker before first paying audit). Deferred intake-form Worker (v1.5) is NOT in this risk — operator-fired scan covers v1 intake. |
| Claude CLI auto-updates mid-project; `parse_result_message` silently wrong | Low | High | Pin `claude` CLI version in Unit 19 CI + preflight assertion at audit start; pin documented alongside autoresearch pin |
| Subscription window exhausted with customer audit in flight | Medium | Medium | R29 50% per-audit ceiling; soft-warn at 40%; `pause_reason=subscription_window_ceiling` + `resume` after window reset; post-calibration decision matrix determines if Pro tier is sufficient |
| R2 public-read vs private-Worker-signed-URL unresolved leaves auth gap | Medium | High | **Resolved post-refinement:** Unit 13 ships with R2 origin behind the deliverable-serving Worker; UUID4 slug (≥122 bits entropy) is the access-control mechanism; Worker injects `X-Robots-Tag: noindex` + `Referrer-Policy: no-referrer` + `Cache-Control: private, no-store`. Signed-URL upgrade path documented for v1.5 if URL leakage becomes a real risk post-conversion-gate. |
| SSRF defense is single-layer (Worker only) | Medium | High | Unit 13 adds Python-side URL re-validation + IP pinning + IPv6/cloud-metadata deny list; claude Stage 1b/2 sessions run with WebFetch host allowlist + no Bash tool for prospect-content fetching |
| Prompt injection via prospect-supplied content (win-loss PDF, ad CSV) | High | High | Unit 14 adds explicit prompt-injection guards: deterministic regex redaction before LLM pass, content-isolation delimiters, output-schema validation; test suite includes known injection payloads |
| `CLAUDE_CODE_OAUTH_TOKEN` leak → arbitrary claude consumption on JR's account | Low | Critical | Token stored in OS keychain only (no repo `.env`, no shell history); 90d rotation matching Cloudflare token cadence; subscription-consumption anomaly alert tied to `cost_log.jsonl` baseline |
| Prospect PII in git-committed operational data (state.json, lineage.jsonl) | Medium | Medium | `client_slug` + `prospect_domain` are identifying; document as business decision with prospect notice (engagement letter); git-history rotation (rebase-squash post-retention) OR separate private-telemetry repo split |
| Engagement signal tampered (JR records $15K for $5K actual) | Low | High | `record-engagement` requires `--ref` cross-referencing payments.jsonl; fitness engagement judge flags `low_confidence=true` for entries recorded <24h or >90d after audit; amounts >$15K require `--confirm-high-value` flag |
| Client-name prefix in public URL leaks competitive intelligence | High | Medium | Slug format changed from `<client-name>-<uuid4>/` to `<uuid4>/` (no prefix); combined with `X-Robots-Tag: noindex` + `robots.txt` disallow-all on deliverable paths |
| Redaction pass fails silently on win-loss; PII reaches deliverable | Medium | High | Deterministic regex redaction (names, emails, phones, URLs) THEN LLM redaction — not LLM alone; human review gate before Stage 2 consumes redacted content; original + redacted diff captured for audit |
| Autoresearch pin has no security-patch escape hatch | Low | High | Ops guide documents emergency-patch process: security-tagged pin bump skips monthly cadence but still runs smoke-test; fallback strategy if smoke-test fails (halt live audits vs proceed with workaround) |

## Alternative Approaches Considered

**Alt 1: Defer autoresearch fusion (R13–R20) to v1.5, contingent on 2/10 gate pass.**

Rejected. Pressure-tested during brainstorm (see origin §Key Decisions). Short version: building the autoresearch lane machinery in v1.5 vs v1 saves ~2 weeks but loses the automated-tuning value. Manual tuning of stage prompts across 10 audits costs ~20 hours; Bundle E costs ~2 weeks; net-positive to ship Bundle E in v1. Also: operational autoresearch (internal tuning) vs customer-facing self-improving pitch are separable concerns; shipping the machinery doesn't force the external pitch until engagement data earns it.

**Alt 2: Use `claude-agent-sdk` (Python wrapper) instead of direct `claude -p` subprocess.**

Rejected. Origin doc Key Decision §Execution model. Short version: SDK doesn't exist in codebase; adding it would break the existing pattern (4 invocation sites use direct subprocess); subscription billing via SDK would require API key management; no operational benefit over direct subprocess. Plan 002 line 416 retired.

**Alt 3: Single-variant marketing_audit lane without evolve loop (content-only v1).**

Rejected. Foregoes the compounding moat. Also: the lane-registration cost is low (~1 week for Unit 17), and the evolve loop is what makes marketing_audit a first-class autoresearch lane (not just a runtime consumer). Half-shipping here would ship more technical debt than it saves.

**Alt 4: Decompose marketing_audit into 10+ fine-grained lanes (per stage).**

Rejected. Adds orchestration complexity (chaining 10+ lanes per audit), fragments lineage, and each lane evolves toward its local rubric without global coherence. Current 5-lane design preserves the coherent optimization target (one composite audit fitness).

**Alt 5: 4 broad Stage-2 agents (per LHR design pressure-test) instead of 7.**

Partially adopted. Design doc specifies 7; R28 mutation space allows evolve to propose 4 or other batchings. Start at 7 (follow the design doc baseline), let the evolve loop discover optimal batching.

**Alt 6: Build marketing_audit as a harness consumer (no autoresearch lane registration in v1).**

Rejected. Surface: rather than copying-and-adapting harness primitives (graceful_stop, resume, cleanup, sessions wrapper, evolve_lock — 5 ports per Phase 1 description), the audit pipeline could consume harness's existing multi-session orchestration capability and register as a lane only in v1.5 once first holdout fixtures land. Three reasons rejected: (a) **harness primitives are coupled to its `Worktree` dataclass + harness-specific runtime model** — refactoring them into a shared `src/shared/multi_session/` library would touch 3+ files in `harness/` and require Worktree-vs-AuditState adapters; refactor cost ≥ duplication cost. (b) **Lane registration is now cheap post-2026-04-27 lane-registry refactor** — Unit 17 collapses to ~10 ops (1 LaneSpec entry + 4 callable wires + 2 substrate edits + 6 supporting creates + tests); deferring this to v1.5 trades ~1 week now for ~3 weeks then (lane registration + activate evolve loop simultaneously, doubling v1.5 risk). (c) **The lane-frame is the right shape for the variant-production surface** even though the live wrapper is asymmetric (per Key Decision §Marketing_audit is a hybrid object) — registering as a lane in v1 means evolve can score variants the moment fixtures exist, not after a refactor. Documented as rejected so future readers see the alternative was considered, not path-dependent silence.

## Success Metrics

**V1 ship-gate (from origin R2 success criterion, with sequential-stop refinement):** Baseline target preserved — ≥2 of first 10 paid audits close $15K+ engagement within 60 calendar days of individual delivery date. **Sequential-stop rule** added to address binary-gate noise (95% CI on 2/10 is [0.025, 0.556] — equally consistent with viable business and noise):

- **Early kill:** First 5 audits with 0 conversions (T+60d aged) → **halt program** = pause new audit dispatch, retune (price/qualification/sales motion/deliverable IA), require explicit JR resume signal before audit 6 ships. Resume criterion: at least one of (a) pricing structure changed (e.g., $1K → $1.5K or tiered), (b) qualification filter changed (e.g., min-revenue threshold added), (c) sales motion changed (e.g., walkthrough format restructured), (d) deliverable IA changed (e.g., page count cut, exec-summary expanded). Saves 5 audits of effort if signal is clearly absent.
- **Early expand:** 3 conversions across any trailing 5 audits (T+60d aged) → strong signal; activate v1.5 work (intake-form Worker, full lens evolve loop with first holdout fixtures, attach-ads expansion if not yet shipped) without waiting for the full 10.
- **Default measurement:** absent early kill or early expand, measurement runs full 10. 2/10 baseline outcome = ambiguous → run 5 more. ≥4/10 = strong signal. 0/10 = clear kill.
- **Leading-indicator gate (R25 elevated):** if first 5 audits' walkthrough-survey depth rating averages <3.5/5 with ≥4 ratings collected, treat as soft kill signal even if T+60d data hasn't landed yet — the audit isn't reading well to prospects, so the conversion lag is unlikely to surprise positively. **Min-N: gate is inactive if fewer than 4 walkthrough ratings collected from first 5 audits** (B2B walkthrough completion runs 60-80%; with <4 ratings one prospect's outlier rating dominates the average). **Null-handling: prospects who didn't take the walkthrough call have null depth and are excluded from the average**, not zeroed.

**Evolutionary health indicators (telemetry, not gates):**
- MA-1..MA-8 rubric scores trend positive across generations (inner-vs-outer correlation stays high)
- Per-audit cost (inferred-API-cost) trends down as evolve optimizes orchestration
- Per-audit wall-clock trends down
- Subscription-window SLA breaches trend to zero

**Operational health indicators:**
- Pre-promotion smoke-test catches ≥1 regressive variant across evolve runs (if 0 caught, manifest/smoke-test may not be sensitive enough)
- autoresearch pin bump events are rare (<1/month) and each one passes smoke-test
- No prospect PII in git history (post-hoc audit)
- No URL enumeration events in Cloudflare logs

## Phased Delivery

**Phase 1 (Units 1–7): Foundation** — ~2 weeks
Primitives everything else imports from. Ships no user-visible functionality but unblocks all subsequent phases. Can be reviewed end-to-end via test suite without any lens execution. **Reuse-vs-port breakdown** (corrects re-review finding that "~10 of 22 Bundle A files are direct imports/extends" overstates the reuse): roughly **~3-4 direct extends** (`harness/sessions.SessionsFile` wrapped, `autoresearch/events.log_event` extended with `path=`, `autoresearch/lane_runtime.resolve_runtime_dir` imported, `src/common/cost_recorder` extended with claude rates) **+ ~5 ports** (graceful_stop, resume, cleanup, sessions wrapper, evolve_lock — all copy-and-adapt from harness patterns to AuditState dataclass shape, NOT direct imports) **+ ~14 net-new** (audit-specific exceptions, state, claude_subprocess factories, cost_ledger, preflight retrofit, etc.). Net-new ports = net-new bugs and test surface, not glue — budget the test load accordingly.

**Phase 2 (Units 8–11): Stage pipeline** — ~2 weeks
Full 6-stage pipeline executable on a fixture prospect with mocked providers. Ships the audit engine core. Bundle B in design doc terms. Lens YAML transcription runs parallel (JR-coordinated multi-day).

**Phase 3 (Units 12–14): Deliverable + CLI** — ~1–2 weeks
Renders and publishes deliverables; tiered CLI surface (14a critical → 14b attach → 14c hygiene). **Deliverable-serving Cloudflare Worker (~20 LOC) ships in v1** for `X-Robots-Tag: noindex` response-header injection (R2 cannot set this header at upload time; R6 security requirement). Intake-form Worker deferred to v1.5 — operator-fired scan covers v1 intake. End of Phase 3 = first paying audit can ship (Bundle C in design doc terms).

**Phase 4 (Units 15–16): Evaluation** — ~1 week
MA-1..MA-8 rubric + structural validator (Unit 15) for human-in-the-loop quality check on deliverables; composite fitness implemented as `marketing_audit_score` + `marketing_audit_objective_score` LaneSpec callables (Unit 16) shipped as **plumbing** for v1.5 — binds when holdout fixtures land post-audit-3. Per Divergence Point #7 picked option (b), `custom_score` independently emits inner-vs-outer pass-rate telemetry into its output (the substrate aggregator at `evaluate_variant.py:1180-1202` is bypassed because `custom_score` replaces `_score_variant_search` wholesale; see Unit 16 for the parity-test mitigation). Bundle D.

**Phase 5 (Units 17–19): LaneSpec registration + safety rails as callables** — ~1 week (down from 1-2 weeks pre-refactor)
Single LaneSpec entry in `autoresearch/lane_registry.py:LANES` with 4 callables wired (custom_score, custom_validate, custom_promote, custom_objective_score_from_entry); engagement judge as separate offline aggregator; manifest verification via shared `lane_registry.verify_manifest`; pre-promotion smoke-test as `custom_promote` callable; autoresearch + claude CLI pins (Unit 19). **End of Phase 5 = full fusion plumbing wired + unit-tested; first end-to-end variant rotation in v1.5 once ≥1 marketing_audit holdout fixture lands** (per X.a fail-closed policy at line 159, locked as v1 default). v1 ships as a hand-promoted single-variant pipeline with all evolve infrastructure as plumbing — explicitly NOT a self-improving loop until smoke-test fixtures exist (post-audit-3 with prospect consent, per Open Question §Reader-readability + holdout-fixture sourcing). **First-generation local-minimum risk** is structurally mitigated by the v1 no-promotion lock. Pre-Bundle-E ship gate: smoke-test rubric calibration on 5-10 hand-graded fixture audits to verify MA-1..MA-8 spread is at least ±2 points across "obviously good" vs "obviously weak" deliverables; if rubric collapses to 7-8/10 universally, re-author anchors before manifest freeze. Bundle E.

**Phase 6 (Unit 20): v1 ship** — ~2–3 days
Smoke-test + docs + onboarding. V1 ready for first paying customer.

**Total: 7–9 weeks foundation to first paying audit; 9–11 weeks including full Bundle E.** (Net effort unchanged after the lane-registry refactor: Phase 5 saves ~3-5 days on registration mechanics, but the `custom_*` callables in src/audit/{score,validate,promote}.py are net-new code in their own right — they were previously distributed across Unit 16's standalone module + Unit 18's standalone manifest module + Unit 18's evolve.py modification. Slightly cleaner shape; same total LoC.)

## Documentation Plan

- `docs/audit-engine-user-guide.md` — operator guide (JR)
- `docs/audit-engine-ops-guide.md` — ops tasks (Worker deploy, creds rotation, pin bumps)
- `docs/version-pins.md` — pin rationale + bump history
- `ONBOARDING.md` — updated with audit module overview
- `README.md` — v1 usage example
- `CHANGELOG.md` — v1 release notes
- Plan doc (this file) — status updates as units ship

## Go/No-Go Checklist — First Paying Audit

Pre-flight for v1 ship. Every item must be green before `freddy audit run --client <first-paying-prospect>` executes. Unit 20 ships this checklist alongside the smoke-test.

### Infrastructure — v1 (JR-ops, blocks first paying audit)
- [ ] **Deliverable-serving Cloudflare Worker** deployed to `reports.gofreddy.ai` (~20 LOC, response-path `X-Robots-Tag: noindex` injection only — no rate-limit, no SSRF guard, no scan-form handling; intake-form Worker on `scan.gofreddy.ai` is v1.5)
- [ ] DNS CNAME live for `reports.gofreddy.ai`, TLS issued + verified via `curl -vI`; response includes `X-Robots-Tag: noindex` + `Referrer-Policy: no-referrer`
- [ ] R2 bucket `gofreddy-audits` provisioned; deliverable-serving Worker has R2 binding (or origin-proxy fallback); access path tested end-to-end against fixture deliverable
- [ ] R2 API token loaded into Worker secrets; scoped to `documents/<uuid>/*` prefix (`scan/*` prefix deferred to v1.5 alongside intake-form Worker)
- [ ] Cloudflare API token for cache purge loaded; purge tested against fixture URL
- [ ] Claude subscription active + tier documented (`docs/version-pins.md` — affects R29 ceiling math)
- [ ] Python + Worker deployment locked-step — Python merge SHA recorded alongside deployed Worker version; rollback runbook pairs both
- [ ] `CLAUDE_CODE_OAUTH_TOKEN` stored in OS keychain only (not in repo `.env`, shell history, or CI)
- [ ] Audit-start preflight assertion catches CLI version drift on JR's machine (Unit 19 + Key Decision §Pinning)

### Infrastructure — v1.5 (gated on 2/10 conversion gate, NOT v1 ship-blockers)
- [ ] Intake-form Cloudflare Worker on `scan.gofreddy.ai` (rate-limit, SSRF guard, scan-form POST handling)
- [ ] DNS CNAME for `scan.gofreddy.ai`, TLS issued
- [ ] R2 token scope expanded to include `scan/*` prefix

### Code readiness (verified in CI)
- [ ] Unit 20 smoke-test green (full `--depth scan` + `--depth full` on fixture)
- [ ] `pins.yml` CI workflow green (both `autoresearch-pin` and `claude-cli-pin` jobs pass)
- [ ] Critique manifest SHA256 pinned; CI catches drift
- [ ] 149-lens YAML transcription complete; loader validates all entries parse
- [ ] **MA-1..MA-8 rubric prompts transcribed** to `src/evaluation/rubrics.py` (8 × ~50-100 LOC each); reviewed against existing `_GEO_1..._GEO_8` quality bar; SHA256-frozen via `marketing_audit_prompt_manifest.py`; MA-5 + MA-8 prompts include explicit dispatch-rationale-log scoring instruction per anti-Goodhart Key Decision; MA-4 prompt surfaces token-count from variant context
- [ ] **Stage prompts transcribed** to `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/` (8 × ~100-200 LOC: stage_0..stage_4 + stage_2_lens_meta + inner_loop_critic + stage_1a_preflight); SHA256-frozen via the same prompt manifest
- [ ] Deliverable template visual QA: render 1 fixture to HTML + PDF; JR eyeball-reviews against R26 IA
- [ ] **Reader-readability validation:** JR reads the fixture deliverable PDF end-to-end (not just visual QA scan). Rubric: page count fits stated "comprehensive but scannable" framing; exec summary lands top-3 actions in <2 minutes; severity-weighted findings are skimmable; methodology appendix collapsed by default. If JR can't finish reading the fixture in <30 minutes without losing focus, IA needs tightening before audit 1 ships
- [ ] `nh3` + `StrictUndefined` verified via malicious-fixture test
- [ ] Security headers (CSP, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex`, `Cache-Control: private, no-store`) verified on deliverable-serving Worker responses (curl -vI against fixture URL)

### Operational workflow (JR-owned)
- [ ] First-5 calibration mode flag enabled in config; transition criterion documented (see below)
- [ ] Payment ledger schema documented; `payments.jsonl` idempotency key is `(audit_id, normalized_ref)` compound
- [ ] Redaction-pass human-review checkpoint decided for `attach-winloss` — resolve before Unit 14 merges
- [ ] Human-gate workflow documented in user guide: Gate 1 (intake review), Gate 2 (deliverable review pre-publish), Gate 3 (post-publish within 1h)
- [ ] `freddy audit record-engagement` T+60d reminder mechanism chosen (iCal auto-write at publish time)

### Rollback readiness
- [ ] Rollback runbook tested on mock deliverable — Tier 1 `republish`, Tier 2 `resume --from-stage`, Tier 3 manual refund
- [ ] `autoresearch lane-head revert <lane> <prior_variant_id>` exercised once on fixture before ship
- [ ] Variant kill-switch (`autoresearch evolve --pause marketing_audit`) exercised once

### Monitoring wired
- [ ] Weekly `freddy audit verify-payments` scheduled (detects duplicate refs, missing amounts, parse errors)
- [ ] Weekly `freddy audit verify-deliverables` scheduled (detects 404/403 on published audits)
- [ ] Weekly `freddy audit status --engagement-due` scheduled (JR records aged audits)
- [ ] Monthly PII-in-git grep scheduled
- [ ] All 7 incident response playbooks exist as ≥5-line skeletons in `docs/incident-response/`

## Operational / Rollout Notes

### Rollback tiers (customer-facing deliverable)

Three rollback tiers depending on defect scope:
- **Tier 1 (seconds):** Template-only fix — `freddy audit republish <audit_id>` re-renders from persisted Stage 3 findings.md + Stage 4 proposal.md with patched template; re-uploads to same R2 UUID slug; purges Cloudflare cache.
- **Tier 2 (hours):** Prompt regression — `freddy audit resume --from-stage <n>` re-runs affected stage(s) with patched prompt. State.json preserves prior stage outputs; engagement clock + lineage row unchanged.
- **Tier 3 (ops intervention):** Unrecoverable — refund + hand-tuned deliverable. Payments ledger row with `method=refund` and `amount=-<original>`; `ref=<original-invoice-id>:refund` crosslinks. Document in incident log.

**Rollback triggers (paging):** structural validator fails post-publish; prospect reports visible rendering bug; PII leak detected in served HTML; MA-1..MA-8 score <4 on any criterion in post-publish audit.

### Variant rollback (autoresearch lane)

If a promoted variant degrades quality in production, revert lane-head via `autoresearch lane-head revert <lane> <prior_variant_id>`. Writes revert reason to `autoresearch/evolve_log.jsonl`. Variant-revert differs from template-rollback — variant-revert affects all *future* audits; template-rollback affects one past audit.

### First-5 calibration transition gate

- **Toggle:** `calibration_mode: true` in `~/.local/share/gofreddy/audit_config.json`; decrements on each completed audit; transitions to `false` when counter hits 0.
- **Manual override:** `freddy audit config --calibration-audits-remaining <n>` extends calibration.
- **Calibration artifacts:** every per-stage approval writes to `clients/<slug>/audit/<audit_id>/calibration_log.jsonl`. After audit 5, JR writes calibration debrief to `docs/audit-engine-calibration-debrief-<date>.md`.
- **Transition criteria (all must pass):** all 5 audits completed without Tier 2/3 rollback; cost burn ≤55% of R29 ceiling on every audit; MA-1..MA-8 average ≥6/10 per audit; JR explicit sign-off.
- **Failure mode:** stay in calibration +5 more audits; do not silently transition.

### Subscription-window decision matrix (post-calibration)

Based on real token burn from first 5 audits:

| Median / max window burn | Action |
|---|---|
| Median ≤40%, max ≤50% | Ship as-is; R29 ceiling stays 50% |
| Median 40–55%, max ≤60% | Tighten Stage-2 fan-out (reduce lens parallelism); re-measure after +3 audits |
| Median >55% OR max >60% | Two-audit-per-window throughput at risk; (a) upgrade Claude tier, OR (b) reduce lens count via selector cutoff, OR (c) split Stage-2 across two window boundaries by design |
| Any audit hits 100% | Immediate halt; wall-clock tracking OR stage decomposition broken; incident review before continuing |

Second-order risk: evolve loop runs add window consumption. `freddy audit window-budget` CLI shows `remaining_window_minutes / queued_audits + queued_evolve`.

### Autoresearch pin bump process

- **Cadence:** monthly (first Monday); also triggered by `autoresearch/GAPS.md` Gap-2/6/18/30 closure, `autoresearch/evolve.py` breaking change, `autoresearch/evaluate_variant.py` rubric semantics change, or a security advisory against the pinned tree.
- **Process:** `freddy audit pin-preview` diffs current tag vs HEAD → `autoresearch smoke-test --lane marketing_audit --autoresearch-ref <candidate-sha>` against holdout fixture → if pass, bump tag + update `docs/version-pins.md` with rationale + diff summary + smoke-test scores; if fail, stay on current pin + file follow-up issue.
- **Staging proxy:** v1 has no staging env; holdout-fixture smoke-test is the de facto gate. The next live audit after a bump is an implicit canary — flag this in the user guide.
- **Security patch escape hatch:** security-tagged pin bump skips monthly cadence but still runs smoke-test. If smoke-test fails on a security patch, halt live audits and decide: (a) proceed with known-vulnerable evaluator while working around, OR (b) pause the lane until patch is smoke-test-clean. Ops guide documents the decision tree.

### Worker + Python deployment lockstep

Unit 13 completion criterion: Worker deployed **and** Python deployed **and** end-to-end path `POST /scan/intake` → Worker → Python scan pipeline → email → R2-served URL works on a real submit. If Python merges first and Worker blocked, `freddy audit run --depth scan` returns `"scan intake not yet available"` rather than pretending functional.

### Engagement signal recording reminder

- At publish time (Stage 6), `freddy audit publish` writes an iCal entry to `~/Library/Calendars/` (macOS) or prints a `gcal` reminder command for JR to copy-paste. Calendar event body contains the exact `record-engagement` invocation.
- `freddy audit status --engagement-due` lists all audits where `(now - published_at).days >= 60 AND engagement_signal IS null` — runnable weekly hygiene check.
- User guide: "Weekly workflow — run `freddy audit status --engagement-due` every Monday."

### Evolve loop kill-switch (first 3 generations)

Because engagement weight = 0 for generations 1–3 (per R19), the loop optimizes against MA-1..MA-8 + cost + latency only. If real-world audit quality (JR subjective + prospect feedback) trends down while rubric scores trend up → Goodhart.

- **Detection:** JR records 1–5 subjective quality rating per audit in `clients/<slug>/audit/<audit_id>/jr_quality_rating.json`. If subjective trends down over 5+ consecutive audits while composite fitness trends up, **pause** the evolve loop.
- **Kill-switch:** `autoresearch evolve --pause marketing_audit` sets a lane-level flag preventing `run_all_lanes` from advancing marketing_audit; variant promotions halted; live audits continue on current lane-head.
- **Resume criteria:** rubric refinement in critique manifest, OR engagement signal accumulates enough to re-weight fitness, OR JR explicit resume with rationale logged.

### Post-launch monitoring (first 30 days)

| Signal | Source | Alert threshold | Cadence |
|---|---|---|---|
| Subscription window burn | `cost_log.jsonl` stderr + `freddy audit costs <id>` | Soft 40% warn; Hard 50% halt (auto) | Auto halts; JR reads warning post-audit |
| Payment ledger integrity | `payments.jsonl` | Duplicate `ref`; row without `amount`; parse error | `freddy audit verify-payments` daily |
| Deliverable URL accessibility | R2 + Worker | 404/403 on status=published audit | `freddy audit verify-deliverables` weekly |
| Cloudflare Worker rate-limit hits | Cloudflare analytics | >10/day | JR weekly |
| Autoresearch pin drift | `pins.yml` (`autoresearch-pin` job) | CI fails on PR | Blocks PR; JR resolves |
| Per-variant fitness trend | `autoresearch/metrics/marketing_audit/composite_fitness.jsonl` | Trend down across 3 consecutive generations | JR monthly; trigger kill-switch per above |
| Inner-vs-outer correlation drift | Unit 16 correlation log | Correlation <0.6 | JR monthly |
| PII leak in git history | `git log -p \| grep -E '(@\|phone\|ssn)'` | Any match | JR monthly |
| Engagement signal backfill | `freddy audit status --engagement-due` | Any 60d+ null entry | JR weekly |

### Incident response playbooks

Each is a 1-page runbook in `docs/incident-response/`. All 7 exist as ≥5-line skeletons before Unit 20 marks v1 ready:

- `pii-leak.md` — prospect PII in public R2 or git history
- `variant-regression.md` — regressive variant promoted; revert lane-head, reach out to affected audits
- `subscription-window-exhausted.md` — audit halted with customer waiting; resume schedule + customer communication template
- `claude-cli-breaking-change.md` — CLI release changes envelope; detection via smoke-test; pin-rollback command
- `r2-creds-leaked.md` — R2 token in git/log/Slack; rotation + object re-ACL verification
- `payments-ledger-integrity-breach.md` — duplicate `ref`, parse error, suspicious amount; ledger reconciliation runbook
- `deliverable-bug-post-publish.md` — rollback tier decision tree (see above)

### Infrastructure + credential lifecycle

- **Cloudflare Worker credential rotation:** every 90 days; Worker API tokens scoped to R2 write-only for scan + deliverable prefixes; rotation tested in staging.
- **`CLAUDE_CODE_OAUTH_TOKEN` lifecycle:** OS keychain only (no repo `.env`); 90d rotation matching Cloudflare cadence; subscription-consumption anomaly alert tied to cost_ledger baseline (e.g., 2× daily-median consumption triggers warning).
- **Third-party provider credentials** (DataForSEO, Cloro, Foreplay, Adyntel, GSC): 90d rotation; log-scrubbing guards prevent API keys from entering `cost_log.jsonl` or `events.jsonl` (both git-committed).
- **R2 retention policy:** per R23, active 90d → archived 1y → deleted. `freddy audit archive-expired` (see Unit 14a) runs weekly; moves R2 objects from `active/` to `archived/` prefix, deletes past 1y.

### PII incident playbook (summary; full runbook at `docs/incident-response/pii-leak.md`)

If prospect PII leaks (public URL enumeration, git-history leak, deliverable misrender):
1. Purge Cloudflare cache on affected slug(s)
2. Rotate the UUID slug (410 the old one, serve new) — purge alone doesn't clear downstream CDN/browser caches
3. Delete R2 objects under old slug
4. `git filter-repo` for history rewrite if PII reached git-committed state (operational data only — prospect content is git-ignored per R21 split)
5. Notify affected prospect per engagement-letter policy
6. Incident log entry; post-mortem within 1 week

## Cross-pollination from harness_fixer (2026-04-30)

Cross-plan review on 2026-04-30 against the harness_fixer lane plan
(`/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.worktrees/harness-fixer-decisions/docs/plans/2026-04-30-001-feat-harness-fixer-autoresearch-lane-plan.md`,
which ships first per its K-11 ordering). harness_fixer is the first
divergent LaneSpec lane against the registry contract.

This plan is **deferred to v3**; items below land when v3 trigger fires
(≥20 audits + 5/week steady-state per LHR §v3 pre-mortem). Items split
into two buckets: **(A) fold-in to Unit body** (no rationale conflict
with current plan; pointer to where the change goes) and **(B) PROPOSAL
for JR** (real architectural tradeoff; lock before v3 implementation
starts).

### A. Fold into Unit body when v3 trigger fires

| Item | Where in plan body | Change |
|---|---|---|
| **A1. Generation-3 fitness-weight sunset trigger** | Unit 16 §Approach (line ~1389-1400) | Replace vague "tunable post-calibration" language with concrete trigger: "After Gen 3, if MA-1 single-shot variance < 0.5σ across 30 fixtures → weights are degenerate, re-tune required." Mirrors harness_fixer K-5 sunset-clause discipline. |
| **A2. Test-extension specificity** | Unit 17 §Patterns to follow + §Verification (line ~1487) | Cite `tests/autoresearch/test_lane_registry.py:42-47` (lane name lists update) + `tests/autoresearch/test_lane_registry_lifecycle_wraps.py:38-119` (synthetic divergent lane try/finally pattern) + add regression test that omitting `models.py:160` Literal extension causes `_assert_models_literal_matches()` to raise. Mirrors harness_fixer plan line 53-54. |
| **A3. No-mock execution note for lane lifecycle tests** | Unit 17 §Execution note | "real subprocess + real git for lane lifecycle tests; respx mocks only for inside-claude-subprocess httpx calls." Without this guidance, mocked smoke-test claude subprocess passes while missing real failures. Mirrors harness_fixer plan line 56. |
| **A4. `src/audit/regen_marketing_audit_manifest.py` operator regen script** | Unit 18 §Files (~line 1542) | Add to file list (~20 LoC). Calls `lane_registry.compute_manifest(...)` over explicit prompt-file list; writes to `marketing_audit_manifest.json`. Without it, every legitimate rubric tuning becomes ad-hoc. Mirrors harness_fixer's `harness/regen_frozen_manifest.py`. |
| **A5. Metadata-outside-manifest-body pattern** | Unit 18 §Approach (manifest section) | `verify_manifest` iterates `manifest.items()` and treats every key as a path — `frozen_at` or `version` field would fail. Move metadata to (a) git tag `marketing-audit-v0-freeze` for label; (b) commit message for `frozen_at`; (c) optional `.about` sidecar for `manifest_format_version`. Mirrors harness_fixer Unit 9 lines 712-716. **Real correctness fix** — without this, the manifest design as currently spec'd will fail at `verify_manifest` time. |
| **A6. LFS strategy for prospect-NDA'd fixtures** | Operational Notes + Risks | `.gitattributes` rule for `tests/fixtures/audit/**/*.tar.gz` lands Phase 1, before prospect-NDA'd content (HTML snapshots, screenshots, response captures) lands. Symmetric with harness_fixer K-4 mandate. |
| **A7. evolve_lock policy → primitive shared with harness_fixer** | Risks table + cross-plan operational note | harness_fixer ships with policy-only ("operator quiesce") because single-operator dev-loop is safe. Audit's commercial flow (paying-customer audit running while evolve mutates prompts) requires the `fcntl.flock`-based primitive (Unit 6 already specs it). When v3 audit ships, harness_fixer adopts the primitive too — 15-LoC upgrade serving both lanes. |
| **A8. Drop `cost_penalty` + `latency_penalty` terms from fitness formula (LOCKED 2026-04-30)** | Unit 16 §Approach (line ~1367-1376, ~1400-1402) | **Locked: drop terms entirely.** R27 narrative is internal evolve-loop language not customer-facing; MA-4 (cost discipline) already encodes cost as first-class rubric criterion; adding `cost_penalty × normalized_token_cost` on top is double-counting + dead code paths in v1. Rewrite formula as `variant_score = weighted_rubric_normalized` (no penalty subtraction). If post-Gen-3 empirical data shows MA-4 alone underweights cost, add penalty back via explicit decision record. Matches harness_fixer K-5. |
| **A9. Bernoulli replay variance for MA-1..MA-8 — phased (LOCKED 2026-04-30)** | Unit 16 §Approach (custom_score aggregation) | **Locked: 2-replay mean for Generations 1-3, drop to single-shot if observed variance < 10% σ post-Gen-3.** ~2× per-fixture cost (~$60 → ~$120) for first 3 generations to baseline variance; then evidence-based decision on whether to maintain. Caps cost while preserving the anti-Goodhart insight. Engagement-conversion (Judge-4) remains the ground-truth check at T+60d; Bernoulli catches single-shot variance in the meantime. |
| **A10. Section-marker contract for MA-1..MA-8 rubric prompts ONLY (LOCKED 2026-04-30)** | Unit 18 §Approach (manifest section) + new sub-spec | **Locked: adopt section markers for `_MA_*` rubric prompts only. Stage prompts keep whole-file freeze (Premise D unchanged).** Rubric prompts have permanent-anchor blocks (judge instructions, scoring schema, JSON contract — must never drift) AND exemplar blocks (good/bad score examples — should evolve as JR learns from real audits). Whole-file freeze calcifies the exemplar-tuning loop. ~30 LoC for diff post-processor inside `marketing_audit_validate`. |

## Sources & References

- **Origin document:** [`docs/brainstorms/2026-04-24-audit-engine-fusion-requirements.md`](../brainstorms/2026-04-24-audit-engine-fusion-requirements.md) — 29 requirements, 13 key decisions
- **Architecture reference:** [`docs/plans/2026-04-24-003-audit-engine-implementation-design.md`](2026-04-24-003-audit-engine-implementation-design.md) — 1426-line design doc (§2 decisions, §3 module map, §4–§8 bundle detail)
- **Research record:** [`docs/plans/2026-04-24-001-audit-pipeline-research-record.md`](2026-04-24-001-audit-pipeline-research-record.md) — 860-line primitives hand-off
- **Content authority:** [`docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md`](2026-04-22-005-marketing-audit-lens-catalog.md) — 149-lens catalog v2 (frozen 2026-04-23)
- **Selector:** [`docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md`](2026-04-22-006-marketing-audit-lens-ranking.md)
- **Original product spec:** [`docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`](2026-04-20-002-feat-automated-audit-pipeline-plan.md) — 1607 lines (line 416 SDK requirement retired)
- **LHR pressure-tested design:** [`docs/plans/2026-04-23-002-marketing-audit-lhr-design.md`](2026-04-23-002-marketing-audit-lhr-design.md) — D1/D2/D3 locked decisions
- **Institutional learnings:** `autoresearch/GAPS.md`, `autoresearch/deep-research/cluster-5-autoresearch.md` (F5.3, F5.4)
- **Related prior art in repo:**
  - `src/competitive/pdf.py` — WeasyPrint + nh3 + Jinja2 pattern (directly portable to `src/audit/render.py`)
  - `src/storage/r2_storage.py` — aioboto3 R2 upload infrastructure
  - `harness/sessions.py`, `harness/run.py`, `harness/worktree.py` — session, resume, cleanup primitives
  - `autoresearch/events.py`, `autoresearch/lane_runtime.py`, `autoresearch/evaluate_variant.py`, `autoresearch/evolve.py`, `autoresearch/frontier.py`, `autoresearch/compute_metrics.py`, `autoresearch/critique_manifest.py` — lane machinery
