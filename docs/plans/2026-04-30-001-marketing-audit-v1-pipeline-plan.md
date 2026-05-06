---
title: "feat: Marketing Audit v1 — dogfood pipeline (LHR-locked, FRAMEWORK ONLY)"
type: feat
status: superseded-by-2026-05-06-001
date: 2026-04-30
superseded: 2026-05-06
authoritative-overrides: docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md
composes-from:
  - docs/plans/2026-04-23-002-marketing-audit-lhr-design.md
  - docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md
  - docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md
---

> **🔖 SUPERSEDED 2026-05-06.** Consolidated into [`2026-05-06-001-marketing-audit-v1-master-plan.md`](2026-05-06-001-marketing-audit-v1-master-plan.md). The 5 CADs flagged here are all resolved in the master plan. Retained as historical reference; do not implement against this doc.

# Marketing Audit v1 — dogfood pipeline

> **⚠ STATUS — FRAMEWORK ONLY (2026-04-30 self-audit).**
>
> This file correctly identifies the v1/v2/v3 phasing, the LHR
> reversions, the locked overrides, and the deferred-fusion bookkeeping.
> It is **NOT yet implementable.** Self-audit on 2026-04-30 found:
>
> - **Q-Tools is misframed.** Claude Agent SDK is NOT installed in this
>   codebase (zero hits for `claude_agent_sdk` / `ClaudeSDKClient` /
>   `create_sdk_mcp_server` / `SdkMcpServer` in src/, autoresearch/,
>   harness/, pyproject.toml, uv.lock). The original plan PRESCRIBED
>   it; never landed. So "re-adopt SDK + MCP cached tools per original
>   plan" is **prescribing net-new work**, not composing from existing.
>   Real Q-Tools is a 3-way structural decision (see §Critical
>   Architectural Decisions).
> - **Q-Schema is a source-doc conflict, not a pick-one.** Catalog says
>   11 Marketing Areas IS the deliverable view; LHR uses 9 sections.
>   Two locked sources disagree.
> - **LHR's 4-to-11 mapping accounts for ~139 lenses.** Catalog locks
>   149 always-on. ~10 Area-11 lenses unmapped between Findability +
>   Experience subset boundaries.
> - **Phase-0 execution model is 3-way ambiguous.** Original plan has
>   no mention; LHR says "woven into agent prompts"; catalog says
>   "above tactical lenses." Not reconciled.
> - **Module list is incomplete** (missing capability_registry,
>   Stripe webhook, free-scan flow, agent_runner, Cloudflare Worker,
>   risk register, success metrics, v2/v3 trigger criteria).
> - **Reusability claim "70%" is optimistic** — agent_models.py needs
>   rework regardless of Q-Schema; honest reusability is ~55-65%.
> - **"4-6 weeks" estimate** copy-pasted from LHR which predates the
>   SDK-availability question. Realistic estimate is **6-9 weeks**.
>
> **Do not start Phase 1 from this plan.** The 4 critical structural
> decisions (Q-Tools, Q-Schema, LHR mapping gap, Phase-0 execution)
> need lock first. See §Critical Architectural Decisions below.

## Status

- **Framework for v1** — establishes phasing + locked overrides + deferred
  fusion. Implementation-ready spec requires resolving §Critical
  Architectural Decisions first.
- Replaces `docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md` (deferred
  to v3 per LHR pressure-test review on 2026-04-30).
- Composes from already-locked design docs rather than re-specifying. Read
  the source docs for the bulk of the spec; this file holds the v1 frame
  + the locked overrides + the unresolved structural decisions.

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
- **LFS strategy from day 1** (added 2026-04-30 per cross-plan review
  with harness_fixer K-4): `.gitattributes` rule for
  `tests/fixtures/audit/**/*.tar.gz` lands in Phase 1 — prospect-NDA'd
  fixture content (HTML snapshots, lighthouse JSON, screenshots,
  response captures) MUST NOT land in normal git history. Same
  policy harness_fixer mandates for `harness/fixtures/archive/*.tar.gz`.

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
- **Bernoulli replay variance for self-scoring honesty** (added
  2026-04-30 per harness_fixer K-9 cross-pollination): 2-replay mean
  per fixture for MA-1..MA-8 to detect single-shot self-report bias.
  Adopt at v2 judge ship; cost ~2× per fixture.

### NOT in v1 (deferred to v3 per LHR)

- Autoresearch fusion (lane registration as `audit_agents` 6th lane)
- Evolve loop / variant mutation / Pareto-dominant promotion
- MA-1..MA-8 rubric scoring as variant fitness
- Pre-promotion smoke-test infrastructure
- `marketing_audit_manifest.json` SHA256 freeze
- Holdout-fixture authoring + `marketing_audit_score` / `marketing_audit_validate` / `marketing_audit_promote` LaneSpec callables
- `evolve_lock` mutex (lives in v3)
- Engagement-judge T+60d signal aggregation
- **Section-marker (`[STABLE]` / `[EVOLVABLE]`) finer-grain freeze of
  MA-1..MA-8 rubric prompts** (added 2026-04-30 per harness_fixer K-2
  cross-pollination): allows rubric exemplar-block evolution while
  keeping anchor blocks frozen. Decide at v3 design whether full-file
  manifest is sufficient or section markers are needed. See fusion
  plan §"Cross-pollination from harness_fixer (2026-04-30)" item 6.

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

## Critical Architectural Decisions (LOCK BEFORE PHASE 1)

These four are NOT 10-min "deferred verification" questions. They are
real structural decisions where source docs disagree or prescribe
net-new work. Each blocks implementation until resolved.

### CAD-1 — Stage 2 tool-access model (CRITICAL, blocks ~80-130 lenses)

The Claude Agent SDK is not installed in this codebase. Empirical:
zero hits for `claude_agent_sdk`, `ClaudeSDKClient`,
`create_sdk_mcp_server`, `SdkMcpServer` across `src/`, `autoresearch/`,
`harness/`, `pyproject.toml`, `uv.lock`. The repo uses bare `claude -p`
subprocesses uniformly at 4 sites (`harness/engine.py:240`,
`autoresearch/compute_metrics.py:280`, `autoresearch/evolve.py:632`,
`autoresearch/program_prescription_critic.py:167`).

The original plan §Architecture (line 132) prescribed
`register_audit_tools(state) -> SdkMcpServer` + `@cached_tool` decorator
+ `scoped_tools.py` — but that prescription never landed. Adopting it
in v1 is net-new infrastructure, not a port.

Three real options:

| Option | Mechanism | Lenses supported | Est. additional v1 weeks |
|---|---|---|---|
| **(a) SDK route** | Install `claude_agent_sdk` dep + build `register_audit_tools` MCP server + `@cached_tool` wrappers per original plan | All 149 + conditional bundles | +2-3 weeks |
| **(b) Cache-warmup route** | Pre-fetch all owned-provider data via Python before each Stage 2 agent; agent reads cache via filesystem `Read` tool + WebFetch for free APIs | All 149 (cache-warmup overhead $) | +1 week |
| **(c) WebFetch-only** | Bare `claude -p` with WebFetch only; no provider-tool access | ~40-60 web-investigation lenses; 50-80 silently fail | +0 weeks but produces an incomplete deliverable |

JR decision needed. Recommendation per the LHR §v1 "deliberately simpler"
principle: option **(b)** — pre-warmup gives provider-tool access without
SDK adoption cost; cache becomes both runtime data + eval-harness fixture
(per original plan line 131). This also matches what the original plan's
Stage 1 already does for pre-discovery (line 107: "parallel cache-warmup
fires all owned-provider tool handlers unconditionally").

### CAD-2 — Deliverable taxonomy (catalog vs LHR conflict)

Catalog `2026-04-22-005` line 148 says:
> "Marketing-Areas view (11 areas) — **deliverable-oriented grouping
> for report sections**"

LHR `2026-04-23-002` line 56-62 maps 4 agents to "Report sections"
using the 9-section taxonomy from original plan
(SEO/GEO/Brand-Narrative/Distribution/Monitoring/Conversion/Lifecycle/
MarTech-Attribution/Competitive).

Two locked sources disagree. LHR was written 1 day after catalog v2
locked; appears to have not adopted the 11-area framing. JR-decision
required:

| Option | Effect |
|---|---|
| **11 areas** authoritative | Catalog wins; rewrite LHR §v1 4-agent mapping to use 11 areas; agent_models.py `ReportSection` → 11-value Literal |
| **9 sections** authoritative | LHR wins; catalog 11-area "view" becomes a tagging/grouping concept not a deliverable structure; agent_models.py keeps current 9-value Literal |
| **Both** (9 deliverable sections + 11-area `marketing_area` field on SubSignal with documented 11→9 mapping) | Most flexible; ~5-10 lines of mapping config; allows v2 to flip the deliverable view based on prospect feedback without schema rework |

Recommendation: **Both (option 3).** Schema cost is minimal; preserves
LHR's 9-section deliverable IA (which is what affects Stage 3 grouping
and ~25-32 ParentFinding target) while keeping catalog content
authority via the 11-area tag.

### CAD-3 — LHR 4-to-11 mapping completeness gap

LHR line 56-62 maps:
- Findability: 35 lenses
- Narrative: 26
- Acquisition: 29
- Experience: 40
- Phase-0: 9
- **Total: 139**

Catalog locks **149 always-on.** The 10-lens gap lives in Area 11
(MarTech-Measurement-Compliance, 28 lenses). LHR splits "technical
SEO/analytics → Findability" + "CMP/DNT/GDPR → Experience" but doesn't
define the boundary. ~10 Area-11 lenses are unassigned.

JR decision needed: walk through the 28-lens Area 11 list and assign
each to Findability OR Experience, OR decide ≤10 lenses get duplicated
across both agents (acceptable for cross-cutting MarTech concerns), OR
spawn a 5th agent for MarTech-only.

### CAD-4 — Phase-0 meta-frame execution model

Three sources, three different framings, no resolution:

| Source | Framing |
|---|---|
| **Original plan `2026-04-20-002`** | No mention. Plan predates catalog v2's Phase-0 introduction. |
| **LHR `2026-04-23-002` line 62** | "9 meta-frames woven into all four agent prompts, not a separate session" |
| **Catalog `2026-04-22-005` line 151** | "Sit above tactical lenses and shape interpretation of every finding" — implies a separate cross-cutting analysis pass, possibly Stage 3 not Stage 2 |

JR decision needed:

| Option | Implementation |
|---|---|
| **Woven** (LHR) | 9 meta-frames added to every Stage-2 agent prompt's preamble; agent reasons about meta-frames AND its tactical lenses in the same session |
| **Separate Stage** | 9 meta-frames executed as a dedicated stage (between 1c brief and Stage 2 fan-out, OR after Stage 3 synthesis) by 1 broad agent |
| **Hybrid** | Woven into Stage 2 prompts AS BACKGROUND CONTEXT (not lens-firings) + a Stage 3 cross-cutting "meta-frame ParentFinding" pass that creates 1-3 deliverable findings purely from Phase-0 dimensions |

Recommendation: **Hybrid (option 3).** Pure-woven loses the
deliverable surface (where do the 9 meta-frame insights show up if
they're just background context?); pure-separate-stage doubles agent
count. Hybrid preserves LHR's "no separate session" cost discipline
while giving Phase-0 a deliverable footprint.

### CAD-5 — Phase-1 reusability pick-list (added 2026-04-30 per cross-plan review)

§"Honest reusability of `phase-1-foundation-snapshot`" gives the
module-by-module table but does NOT lock which modules to cherry-pick
vs redo. This decision IS a CAD: it determines what code Phase 1 starts
from. JR-decision required:

| Module | Suggestion (JR-lock TBD) | Rationale |
|---|---|---|
| `agent_models.py` | **Redo** | 9-section ReportSection; flat-Finding/SubSignal/ParentFinding mix. Net-new work for CAD-2 regardless of which CAD-2 option JR picks. |
| `checkpointing.py` | Cherry-pick | Pure stdlib, taxonomy-orthogonal |
| `preflight/*` (8 retrofitted checks) | Cherry-pick | Detection logic is taxonomy-orthogonal; matches LHR §v1 line 99 |
| `state.py` | Cherry-pick | `total_duration_api_ms` is unused in v1 but ports cleanly |
| `exceptions.py` | Cherry-pick + drop 3 | Drop `MissingSubscriptionToken` + `EvolveLockHeld` + `SubscriptionWindowExceeded` |
| `sessions.py` | Cherry-pick | Direct harness wrapper |
| `claude_subprocess.py` | Cherry-pick if CAD-1 = (b) or (c); redo if (a) | Bare claude -p factories valid for cache-warmup + WebFetch routes |
| `cost_ledger.py` | Cherry-pick + simplify | Drop R29 SLA logic + `MissingSubscriptionToken` assertion; keep base tracking |
| `graceful_stop / resume / cleanup` | Cherry-pick | Generic primitives |
| `events.py` + autoresearch path= extension | Cherry-pick | Generic |
| `autoresearch/evolve_lock.py` | Skip | v3-only |
| Tests for fusion-only features | Skip | R29, MissingSubscriptionToken, evolve_lock — don't carry |

These are my suggestions per cross-plan review on 2026-04-30; JR locks
the final pick-list before Phase 1 starts. Without locking, the
implementing agent will either over-port (carrying fusion-only fields)
or under-port (rebuilding what carries cleanly).

### CAD-1 sub-decision — cache-warmup smoke gate (added 2026-04-30)

If CAD-1 resolves to option (b) cache-warmup, Stage 2 needs a smoke
gate that verifies the cache covers all 50-80 provider-tool lenses
BEFORE fan-out. Without it, Stage 2 silently degrades to (c) WebFetch-
only on cache misses. Sub-decision:

- **Strict gate:** Stage 1c emits `cache_coverage.json` listing
  per-lens cache hit/miss; Stage 2 refuses to start if any expected
  lens missing. Fail-closed.
- **Soft gate:** Stage 2 starts; missing-cache lenses produce a
  failure SubSignal with `reason: "cache_miss"`; Stage 3 surfaces in
  `gap_report.md`.

Suggested default (JR-lock TBD): **Strict gate for v1** — coverage
gaps should surface loud during initial calibration. Loosen to soft
gate post-calibration if coverage is reliably ≥95%.

## Lower-priority open questions (resolvable during Phase 1)

- **Q-Cost-baseline:** $100 soft / $150 hard confirmed (LHR §v1 +
  catalog §"Cost envelope lift" agree).
- **Q-Bundle-activation:** Stage 1b activates bundles. Deterministic
  (signal → map lookup) per LHR §v1 line 90, OR LLM-judged. Recommend
  deterministic for v1 — simpler + lower cost.
- **Q-Free-scan-execution:** Confirmed in-v1 per original §U8 (Stage 0
  Sonnet single-pass, ~$1-2). Specific agent role + prompt deferred to
  Phase 2 spec.

## Missing from this plan (must be added during Phase 1 spec)

These are concrete v1 modules / specs that LHR §v1 + original plan
collectively require but I dropped from the v1 module list:

| Item | Source spec | v1 status |
|---|---|---|
| `capability_registry.py` + `capability_registry.yaml` (~48 entries) | Original §U6 (lines 705-722) | Required for Stage 4 proposal — pricing engine. **Add to Phase 3.** |
| Stripe webhook + payment-state stub | Original §U10 + line 100 | Required for payment gate (`state.paid = True` before Stage 2 fires). **Add to Phase 3.** |
| Free AI Visibility Scan flow (Stage 0 specific impl) | Original §U8 | Required — lead-magnet drives sales funnel. **Add to Phase 2.** |
| `agent_runner.py` (SDK wrapper OR claude -p wrapper) | Original §Architecture line 145 | Required regardless; shape depends on CAD-1. **Add to Phase 1.** |
| Cloudflare Worker spec | Original + fusion both have it | Required for `reports.gofreddy.ai` hosting + `X-Robots-Tag: noindex` injection. **Add to Phase 3.** |
| Risk register | LHR + original both have one | Required at plan-completion — ports forward from those two docs with v1 scope filter. **Add at Phase 3 ship.** |
| Success metrics + kill/expand thresholds | Original R10 | **Add immediately** — kill rule "0 conversions in first 5 → halt + retune" needs to be in v1 plan, not just original. |
| v2 trigger logic | LHR §v2 has triggers but not start-criteria | **Add at Phase 3 ship** — when does v2 design start? Immediately after audit 5 ships? After 60d aging? |
| v3 rejoin path | None | **Add at v1 ship** — fusion plan as-written may need re-conformance after main-branch drift; document fresh-eye review requirement. |

## Honest reusability of `phase-1-foundation-snapshot` (commit `cb425b6`)

Earlier claim of "~70%" was optimistic. Module-by-module:

| Module | Reusable for v1? | Notes |
|---|---|---|
| `agent_models.py` (Unit 1 port) | **No** | 9-section ReportSection conflicts with CAD-2; flat-Finding/SubSignal/ParentFinding mix needs rework regardless of CAD-2 outcome |
| `checkpointing.py` (Unit 1) | **Yes** | Pure stdlib, taxonomy-orthogonal |
| `preflight/*` (Unit 7 retrofit) | **Yes** | Detection logic taxonomy-orthogonal; matches LHR §v1 line 99 (8 deterministic checks) |
| `state.py` (Unit 2) | **Yes** | `total_duration_api_ms` field is unused in v1 but ports cleanly |
| `exceptions.py` (Unit 2) | **Partial** | Drop `MissingSubscriptionToken`, `EvolveLockHeld`, `SubscriptionWindowExceeded` (fusion-only) |
| `sessions.py` (Unit 2) | **Yes** | Direct harness wrapper |
| `claude_subprocess.py` (Unit 3) | **Yes if CAD-1=(b) or (c); No if CAD-1=(a)** | Bare claude -p factories valid for cache-warmup + WebFetch routes; SDK route would replace this |
| `cost_ledger.py` (Unit 4) | **Partial** | Drop R29 SLA logic + `MissingSubscriptionToken` assertion; keep base tracking |
| `graceful_stop.py + resume.py + cleanup.py` (Unit 5) | **Yes** | Generic primitives |
| `events.py` + `autoresearch/events.py` `path=` extension (Unit 6) | **Yes** | Generic |
| `autoresearch/evolve_lock.py` (Unit 6) | **No** | v3-only |
| Tests for fusion-only features | **No** | Drop R29, MissingSubscriptionToken, evolve_lock tests |

Honest reusability: **~55-65%** by module weight. Worst-case is
agent_models.py (load-bearing, needs net-new work for CAD-2).

## Estimate (honest)

LHR §v1 says 4-6 weeks. That estimate predates the SDK-availability
question (CAD-1) and assumes SDK is available. Realistic v1 estimate:

| Scenario | Estimate |
|---|---|
| CAD-1 = (a) SDK route | **8-10 weeks** (+SDK adoption + MCP server build) |
| CAD-1 = (b) Cache-warmup route | **6-8 weeks** (cache-warmup is ~1 week net-new) |
| CAD-1 = (c) WebFetch-only route | **5-7 weeks** but produces incomplete deliverable for ~50-80 lenses |

Add: 1 week for the 4 CAD lock decisions + spec rewrite, 1 week for
the missing-modules spec (capability registry, Stripe, free scan,
Cloudflare Worker).

**Realistic range: 7-10 weeks** depending on CAD-1.

## Path to implementable plan

1. Lock CAD-1 + CAD-2 + CAD-3 + CAD-4 with JR (2-3 hr session)
2. Update this plan to spec the resolved decisions concretely
3. Add the missing modules (capability registry, Stripe, free scan,
   Cloudflare Worker, risk register, success metrics, v2/v3 triggers)
4. Honest reusability table → which Phase 1 modules to cherry-pick from
   `phase-1-foundation-snapshot` vs which to redo
5. Re-honest estimate based on CAD-1 outcome
6. Promote status from `framework-only` to `active`
7. Then Phase 1 can start

## Tag bookkeeping

- `phase-1-foundation-snapshot` (commit `cb425b6`) — Phase 1 implementation
  done under fusion plan (7 commits, 127 tests). **Honest reusability
  ~55-65%** per the table above; agent_models.py needs net-new work for
  CAD-2.
- `plan-conformance-only` (commit `619d716`) — pre-banner branch state.
  Preserved but not authoritative.
- `checkpoint-pre-rebase` — pre-existing, unrelated.

## What this plan deliberately does NOT do

- It does NOT re-spec the bulk of the v1 architecture. Read LHR §v1 +
  original plan §Architecture. They are the authoritative spec for v1
  *modulo* the unresolved CAD decisions above.
- It does NOT delete `docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md`.
  That plan is correct work for v3 once 20+ audits + 5/week justifies it.
  Status banner has been added there and the v3 work resumes from that
  plan when triggers fire.
- It does NOT pretend Phase 1 is unblocked. Earlier draft of this plan
  claimed Phase 1 modules are taxonomy-orthogonal so Phase 1 could
  start before CADs are locked — false. agent_models.py (a Phase 1
  module via Unit 1 port) is the fault line for CAD-2; Stage 2 module
  shape depends on CAD-1; etc.

## Sources

- LHR design lock: `docs/plans/2026-04-23-002-marketing-audit-lhr-design.md`
- Original plan: `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`
- Lens catalog v2 (locked content): `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md`
- Lens ranking: `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md`
- Deferred-to-v3 fusion plan: `docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md`
- Brainstorm origin (fusion-shape): `docs/brainstorms/2026-04-24-audit-engine-fusion-requirements.md`
  — note: brainstorm framed fusion as v1 prematurely; LHR pressure-test
  is the override.
- **Sister lane plan** (ships first per K-11): `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.worktrees/harness-fixer-decisions/docs/plans/2026-04-30-001-feat-harness-fixer-autoresearch-lane-plan.md`
  — first divergent LaneSpec lane shipped against the registry contract.
  Self-scoring honesty mechanism stack (K-2 section markers + orchestrator
  gates + `golden_outcome` cross-check + Bernoulli replay) is the reference
  pattern audit v3 should adopt. See deferred fusion plan §"Cross-pollination
  from harness_fixer (2026-04-30)" for the 10-item itemized list.
