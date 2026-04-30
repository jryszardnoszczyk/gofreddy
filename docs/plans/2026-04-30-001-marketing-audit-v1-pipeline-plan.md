---
title: "feat: Marketing Audit v1 — dogfood pipeline (LHR-locked)"
type: feat
status: active
date: 2026-04-30
authoritative-overrides: docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md
composes-from:
  - docs/plans/2026-04-23-002-marketing-audit-lhr-design.md
  - docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md
  - docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md
---

# Marketing Audit v1 — dogfood pipeline

## Status

- **Authoritative for v1.**
- Replaces `docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md` (deferred
  to v3 per LHR pressure-test review on 2026-04-30).
- Composes from already-locked design docs rather than re-specifying. Read
  the source docs for the bulk of the spec; this file holds only the
  v1 frame + the locked overrides + the open questions for JR.

## Why this replaces `2026-04-24-005`

The fusion plan shipped autoresearch fusion as v1 work, against the LHR
pressure-test which explicitly stages this v1 → v2 → v3:

| Phase | LHR trigger | LHR-spec'd scope |
|---|---|---|
| **v1** (4-6 weeks) | Now | Dogfood pipeline. 4 broad agents. SDK + MCP tools. Single-pass deliverable. Structured signal capture. **No judges, no evolve, no autoresearch fusion.** |
| **v2** (after 5-10 audits) | Empirical cost baselines + observable JR ship-gate edits | 4 judge layers (SubSignal validator, ParentFinding strategic-story judge, calibration judge, engagement-conversion judge). Inner-loop self-correction. Cross-audit memory. |
| **v3** (after 20+ audits + 5/week steady-state) | Engagement-conversion data + variance | Autoresearch fusion. Marketing_audit registers as 6th lane. Evolve loop mutates agent prompts. Pareto-dominant variant promotion. **LHR §v3 pre-mortem: v3 only earns its keep at >5 audits/week steady state.** |

The fusion plan's three additional reversions against LHR + the original
plan, all caught on 2026-04-30 review:

1. **9 → 7 → 4-broad → 7 reversion.** Original plan `2026-04-20-002`
   had 7 named agents. LHR pressure-test moved to **4 broad agents**
   (Findability / Narrative / Acquisition / Experience) explicitly
   addressing context-sharing across overlapping marketing areas. Fusion
   plan reverted to 7 citing "design doc 003" — which only specifies
   `Semaphore(7)` for asyncio concurrency, not 7 agents-as-units, and
   doesn't address LHR's rationale.
2. **SDK + MCP cached-tool layer dropped.** The original plan's
   `register_audit_tools(state) -> SdkMcpServer` + `@cached_tool`
   wrappers around DataForSEO / Cloro / Foreplay / Adyntel / GSC etc.
   are how ~50-80 of 149 lenses fetch their data; the fusion plan's
   `claude -p` direct subprocess has no specified tool-access path.
   This is a structural gap, not a stylistic preference.
3. **9-section `ReportSection` Literal** kept from the original plan,
   contradicts the catalog-locked **11 Marketing Areas** (`2026-04-22-005`
   §Marketing-Areas View). LHR §v1 already maps 4 broad agents to the
   11 areas (see LHR line 56-62) but the schema-side change was never
   landed.

The conformance work shipped on the fusion plan (`ff89729 + 619d716` on
this branch) is preserved at tag `plan-conformance-only` for reference
when fusion is re-considered for v3.

## Scope

### In v1

- **Pipeline.** 6-stage `claude -p` (or SDK — see Open Question §Q-Tools)
  pipeline: Stage 0 intake / Stage 1a deterministic preflight / Stage 1b
  bundle-activation signals + brief / Stage 2 lens fan-out / Stage 3
  synthesis (SubSignal → ParentFinding) / Stage 4 proposal / Stage 5
  deliverable + publish.
- **4 broad agents** per LHR §v1: Findability, Narrative, Acquisition,
  Experience. Lens-area assignments per LHR line 56-62.
- **149 always-on lenses + 25 vertical + 10 geo + 5 segment bundles +
  9 Phase-0 meta-frames** per catalog `2026-04-22-005` v2 lock.
- **SDK + MCP cached-tool surface** per original plan §Architecture
  module layout: `src/audit/tools/` with `register_audit_tools(state)
  -> SdkMcpServer` + `@cached_tool` decorator + `scoped_tools.py` for
  safety-critical primitives. **Pending Open Question §Q-Tools:** verify
  Claude Agent SDK still works under multi-provider OpenCode (PR #28+33+34)
  before any code lands.
- **SubSignal → ParentFinding aggregation** per catalog §Architectural
  Patterns. Target ~25-32 ParentFindings per audit across deliverable
  sections.
- **Single-pass deliverable.** No critique loop in v1 (LHR §v1 line 76:
  "Critique loop OFF in v1 — agents run single-pass; critique handled by
  v2 judges").
- **Cost ceiling.** $100 soft warn / $150 hard breaker per LHR §v1 line 89.
  Wall-clock observability only (NO R29 SLA — that's a fusion-plan
  invention, the LHR design doesn't include subscription-window SLA).
- **Structured signal capture** per LHR §v1 lines 116-136:
  `clients/<slug>/audit/signals/{pre_ship.json, ship_gate_edits.diff,
  cost_actual.json, agent_turns.json, lens_firings.jsonl}` + per-audit
  row appended to `audits/lineage.jsonl`. Cheap to write in v1,
  load-bearing for v2/v3.
- **Customer flow** per original plan §Architecture diagram: form → free
  AI Visibility Scan → sales call → invoice → payment gate → audit run
  → publish gate → walkthrough call. Manual invocation per stage.
- **Mandatory ship gate** per LHR D2 lock — JR reviews deliverable
  before publish.

### NOT in v1 (deferred to v2 per LHR)

- Inner-loop critique
- Judge layers (Judge-1 SubSignal validator, Judge-2 ParentFinding
  strategic-story, Judge-3 calibration, Judge-4 engagement-conversion)
- Section-level Stage-3 atomicity
- Per-call `max_budget_usd` (single hard total cap suffices in v1)
- Tenacity retries (only if v1 observes transient failures)
- Per-lens SubSignal-file checkpointing (only if v1 has crash-resume incidents)
- OpenLLMetry/Langfuse telemetry
- arq queue + webhook-driven scan auto-fire (CLI-only per D1)

### NOT in v1 (deferred to v3 per LHR)

- Autoresearch fusion (lane registration as `audit_agents` 6th lane)
- Evolve loop / variant mutation / Pareto-dominant promotion
- MA-1..MA-8 rubric scoring as variant fitness
- Pre-promotion smoke-test infrastructure
- `marketing_audit_manifest.json` SHA256 freeze
- Holdout-fixture authoring + `marketing_audit_score` / `marketing_audit_validate` / `marketing_audit_promote` LaneSpec callables
- `evolve_lock` mutex (lives in v3)
- Engagement-judge T+60d signal aggregation

The lane-registry refactor that already shipped to main (`9549500`) is
good infrastructure; it just doesn't get a `marketing_audit` LaneSpec
entry until v3.

## Authoritative source docs

For the bulk of the spec, read:

1. **LHR design lock** at `docs/plans/2026-04-23-002-marketing-audit-lhr-design.md`,
   §"v1 — Dogfood pipeline" (lines 43-137) — the v1 architecture lock.
2. **Original plan** at `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`,
   §Architecture (lines 77-181) — the concrete file inventory + module
   layout (`src/audit/tools/`, `scoped_tools.py`, `hooks.py`,
   `agent_runner.py`, etc.).
3. **Lens catalog** at `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md`,
   §"Locked Final Recommendations" + §"Architectural Patterns" + §"Marketing-Areas View"
   (lines 12-394) — the 149-lens scope + SubSignal/ParentFinding model + 11 areas.
4. **Lens ranking** at `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md` —
   linear ranking + cutoff for the always-on 149.

## Locked overrides (where v1 plan diverges from any source doc)

| # | Source claim | v1 lock | Reason |
|---|---|---|---|
| **O1** | Original plan: 7 named agents | **4 broad agents** (LHR §v1 lock) | LHR pressure-test rationale on context-sharing across overlapping marketing areas |
| **O2** | Original plan: `ReportSection` Literal of 9 sections | **11 catalog Marketing Areas** + 9 Phase-0 meta-frames as cross-cutting tags | Catalog `2026-04-22-005` is content-authority on deliverable taxonomy |
| **O3** | Fusion plan: bare `claude -p` subprocess, no SDK | **SDK + MCP cached tools** (original plan §Architecture) | ~50-80 of 149 lenses need provider-tool access; bare CLI has no specified path |
| **O4** | Fusion plan: 13+ Bundle A modules, 20-unit phased | **~5-6 modules per LHR §v1**, simpler scope | LHR pressure-test rationale: don't over-specify before audits run |
| **O5** | Fusion plan: critique loop `≤3 iterations` per agent | **OFF in v1** (LHR §v1 line 76) | Critique handled by v2 judges; v1 single-pass with signal capture |
| **O6** | Fusion plan: R29 subscription-window SLA + duration_api_ms | **No R29 in v1** | LHR §v1 doesn't include it; total $150 hard cap suffices |
| **O7** | Fusion plan: live wrapper + evolve wrapper around shared lane program | **Single live program only** | Fusion is v3 work per LHR |

## Implementation strategy (per-phase)

### v1 Phase 1 — Foundation (~1 week)

Per LHR §v1 file changes (line 92-114). New Python modules:

- `src/audit/state.py` — `AuditState` dataclass + atomic JSON persist
- `src/audit/sessions.py` — per-role session_id tracking
- `src/audit/cost_ledger.py` — $100 soft / $150 hard total breaker
  (NOT R29; NOT MissingSubscriptionToken — both fusion-plan inventions)
- `src/audit/agent_runner.py` — SDK wrapper with cost capture, session
  persist, fallback model
- `src/audit/orchestrator.py` — state machine, async fan-out, resume
- `src/audit/checkpointing.py` — atomic state read/write
- `src/audit/telemetry.py` — events.jsonl + Slack notifier
- `src/audit/preflight/` runner + 8 deterministic checks (already ported
  via Unit 1 of fusion-plan-implementation; ~70% reusable from
  `phase-1-foundation-snapshot` tag)

### v1 Phase 2 — Stage pipeline (~2 weeks)

Per original plan §U3-U5 + LHR §v1 architecture. Stages 0-3 + 4 (proposal)
running through 4 broad agents with SDK/MCP tool access.

### v1 Phase 3 — Deliverable + CLI + commercial flow (~1-2 weeks)

Per original plan §U7 + §U8 + §U10. Stage 5 deliverable (HTML+PDF+publish);
free AI Visibility Scan; mark-paid + send-invoice CLI; Stripe webhook
state-update (no auto-fire).

### v1 done = first paying audit ships

Per LHR §v1 goals (line 45-50): 5 audits shipped, structured signal
captured, empirical cost baselines, locked-lens-scope validated.

## Open questions for JR (lock before code starts)

These need lock decisions BEFORE Phase 1 starts. Each should resolve in
~10-15 min of JR time.

- **Q-Tools:** Does the Claude Agent SDK still work under
  multi-provider OpenCode (PR #28+33+34)? If not, what's the v1 substitute
  for `register_audit_tools(state) -> SdkMcpServer`? (If SDK is broken,
  this materially affects v1 timeline — manual `claude -p` + per-tool
  wrapper subprocess is significantly more code than the SDK pattern.)
- **Q-Schema:** ReportSection Literal becomes 11 Marketing Areas, OR
  9 deliverable sections + separate `marketing_area` field on SubSignal
  with documented 11→9 mapping. Pick one. LHR §v1 line 56-62 maps the
  4 agents to 11 areas; the deliverable IA aggregation (target ~25-32
  ParentFindings) prefers the 9-section view.
- **Q-PhaseZero:** Where do the 9 Phase-0 meta-frames execute? LHR §v1
  line 62 says "woven into all four agent prompts, not a separate
  session." Confirm vs original plan's separate Stage-0-meta call.
- **Q-Cost-baseline:** LHR §v1 says cost ceiling is $100 soft / $150
  hard. Catalog §"Cost envelope lift" says "$50 → $100 with $150 hard"
  — same numbers, different framing. Both align. No conflict.
- **Q-Bundle-activation:** Stage 1b emits Phase-0 detection signals
  (vertical / geo / segment) that activate ~40 conditional bundles.
  Is the activation logic deterministic (signal → bundle map lookup) or
  LLM-judged (Stage 1b agent reasons about applicability)? LHR §v1 line
  90 implies deterministic.
- **Q-Free-scan-vs-paid:** LHR §v1 doesn't explicitly cover the free
  AI Visibility Scan (Stage 0). Original plan §U8 covers it. Confirm
  free-scan ships in v1 (it's the lead-magnet that drives the sales
  funnel) and which agent runs it (Sonnet single-pass per original
  plan §U8).

## Tag bookkeeping

- `phase-1-foundation-snapshot` (commit `cb425b6`) — Phase 1 implementation
  done under fusion plan (7 commits, 127 tests). ~70% reusable for v1
  per O3 + O5 + O6 — `state.py`, `sessions.py`, `claude_subprocess.py`,
  `events.py`, `evolve_lock.py` mostly carry; `cost_ledger.py` needs
  $100/$150-only re-tune (drop R29 + MissingSubscriptionToken); all
  preflight retrofits carry as-is.
- `plan-conformance-only` (commit `619d716`) — current branch HEAD;
  the 2 plan-conformance commits against the fusion plan. Preserved for
  reference but not authoritative.
- `checkpoint-pre-rebase` — pre-existing, unrelated.

## Estimate

Per LHR §v1: **4-6 weeks** (vs fusion plan's 7-9 weeks). Saves 2-3 weeks
of pre-validation work on autoresearch fusion infrastructure that won't
have data to drive it for ~20 audits.

## What this plan deliberately does NOT do

- It does NOT re-spec the bulk of the v1 architecture. Read LHR §v1 +
  original plan §Architecture. They are the authoritative spec for v1.
- It does NOT block Phase 1 from starting. Phase 1 modules are mostly
  taxonomy-orthogonal; the open questions above all gate Phase 2 (where
  Stage 2 lens dispatch + agent prompts encode the agent count + tool
  surface + schema choices).
- It does NOT delete `docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md`.
  That plan is correct work for v3 once 20+ audits + 5/week justifies it.
  Status banner has been added there and the v3 work resumes from that
  plan when triggers fire.

## Sources

- LHR design lock: `docs/plans/2026-04-23-002-marketing-audit-lhr-design.md`
- Original plan: `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`
- Lens catalog v2 (locked content): `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md`
- Lens ranking: `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md`
- Deferred-to-v3 fusion plan: `docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md`
- Brainstorm origin (fusion-shape): `docs/brainstorms/2026-04-24-audit-engine-fusion-requirements.md`
  — note: brainstorm framed fusion as v1 prematurely; LHR pressure-test
  is the override.
