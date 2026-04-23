---
title: "design: Marketing audit LHR (long-horizon-running) layer"
type: design
status: active
date: 2026-04-23
revision: 2026-04-23 (honest pressure-test revision — see §"First-pass lessons")
extends: 2026-04-20-002-feat-automated-audit-pipeline-plan.md
related:
  - 2026-04-22-005-marketing-audit-lens-catalog.md
  - 2026-04-22-006-marketing-audit-lens-ranking.md
---

# Marketing audit LHR layer — phased design with judges + evolution

## Premise

The existing implementation plan (`2026-04-20-002-feat-automated-audit-pipeline-plan.md`, 1534 lines) describes a 6-stage marketing audit pipeline that JR fires manually. This design doc adds the **LHR primitive layer** (autonomy, resume, cost control), the **judges** (quality gating inside the pipeline), the **cross-audit signal capture** (so quality can be measured over time), and the **evolution loop** (so the system actually improves itself).

It is phased across three versions because **designing the full system before running any audits is a guess**. v1 is the minimum viable autonomous pipeline that ships fast and produces real audit data. v2 adds the quality gates + signal capture. v3 closes the self-improvement loop via the autoresearch evolution engine that already exists in the repo.

## First-pass lessons (what the 2026-04-23 initial draft got wrong)

Pressure-test of the first draft surfaced four material problems:

1. **"Self-improving" was aspirational, not architectural.** The Layer-3 cross-audit memory described as "Opus proposes lessons monthly, JR reviews" is a manual feedback loop dressed up as automation. A self-improving system needs automatic quality signal + a knob to turn based on signal + something that turns the knob without JR. The first draft had none of that.

2. **The v1 architecture was over-specified before any audit has run.** 9 agents, asyncio.TaskGroup + Semaphore + tenacity, per-lens checkpointing, section-level Stage-3 atomicity, three-tier cost control, 13 new modules — committed on zero empirical data. The locked 149-lens *scope* is content (JR locked it across 4 reshuffle passes); the derived 9-agent *architecture* was a guess.

3. **Cost estimates were fiction.** $60 for Stage 2, $10 for Stage 3, $98 total — made-up numbers dressed in spreadsheet authority. Real figures could be 0.5x or 2x, and we have no calibration baseline.

4. **Judges were omitted entirely.** The harness and autoresearch both have judge layers (verifier agents, outer-loop evaluator, layer1 validators). Pretending marketing audits don't need them was wrong. ~$3-5/audit of judge overhead is cheap insurance at the $1K price point.

This revision replaces the monolithic first-draft with **phased v1 → v2 → v3** where each phase's design triggers off signal from the previous phase.

## Decisions locked (unchanged from first draft)

Three open decisions surfaced during research synthesis. These stand.

- **D1 Trigger:** CLI-only for v1 dogfood (5 audits); arq queue + webhook deferred to v2
- **D2 Ship gate:** Mandatory `freddy audit ship` preserved through v1 (revisit after 20 paid audits with zero veto-on-defect)
- **D3 Isolation:** Serialize at worker level (one audit per process); no per-audit git worktrees

## v1 — Dogfood pipeline (ships first, 4-6 weeks)

### v1 goals

- Ship an autonomous-enough pipeline that can run 5 paid audits end-to-end
- Capture structured signal for v2 quality instrumentation (every JR ship-gate edit, every cost event, every agent session transcript)
- Validate the locked 149-lens scope against real prospect audits
- Measure actual cost envelope (replace fiction with empirical baselines)

### v1 architecture — deliberately simpler than first draft

**4 broad-scope agents, not 9 narrow ones.** The 9-agent split over-partitions shared context (Paid Media + Earned PR + Distribution Community all share the same media landscape and should share a session). Starting broader lets the right boundaries fall out of real audits.

| v1 Agent | Lens areas owned | Approx lens count | Report sections |
|---|---|---|---|
| **Findability** | Discoverability & Organic Search (Area 1) + MarTech-Measurement subset (Area 11 technical SEO/analytics) | ~35 | SEO + GEO |
| **Narrative** | Content Assets (Area 2) + Brand & Authority (Area 9) + Earned Media (Area 4) | ~26 | Brand/Narrative + part of Competitive |
| **Acquisition** | Paid Media (Area 3) + Distribution (Area 5) + Sales/GTM (Area 10) | ~29 | Distribution + Monitoring + part of Competitive |
| **Experience** | Conversion (Area 6) + Activation (Area 7) + Lifecycle (Area 8) + MarTech-Compliance subset (Area 11 CMP/DNT/GDPR) | ~40 | Conversion + Lifecycle + MarTech-Attribution |
| **Phase-0 meta** | 9 meta-frames (woven into all four agent prompts, not a separate session) | 9 | (woven into all report sections by Stage 3) |

Split revisited at v2 based on empirical signal: which agent's SubSignals does JR most often edit at ship-gate, which agent's findings cluster oddly across sections, which agent runs out of context window first.

### v1 LHR primitives (minimum viable)

| Primitive | v1 implementation | v2+ if signal supports |
|---|---|---|
| State + checkpointing | Per-stage JSON files in `clients/<slug>/audit/`; atomic temp+rename; state.json with `current_stage` + `cost_spent_usd` + `sessions/<role>` | Per-lens SubSignal files (only if Stage 2 has crash-resume incidents in v1) |
| Parallelism | `asyncio.gather` over the 4 Stage-2 agents; simple; no Semaphore (4 is already the cap) | TaskGroup + Semaphore(N) if agent count grows |
| Resume | SDK-native: persist `session_id` per agent; `--resume` re-dispatches missing stages | Section-level Stage-3 atomicity (only if Stage-3 crash observed) |
| Cost control | One tier: total-audit hard breaker at $150 via cumulative `ResultMessage.total_cost_usd` | Per-call `max_budget_usd` + per-stage soft caps (only if v1 blows cost budget) |
| Error handling | Skip-not-raise on malformed SubSignal (port from `harness/findings.py`); one-agent-crash doesn't kill siblings | Tenacity retries (only if we observe transient failures worth retrying) |
| Telemetry | JSONL event log at `events.jsonl`; Slack alert on cost breaker, pre-flight gate, audit complete | OpenLLMetry → Langfuse (only if debugging parallel agent waterfalls gets painful) |
| Critique loop | **Off in v1** — agents run single-pass; critique handled by v2 judges | Re-enable if judge data shows single-pass agents produce under-severity findings |

This is ~5-6 new Python modules instead of 13. Aim: ship v1 in 4-6 weeks, not 12.

### v1 locked-lens-scope integration (unchanged — this is content, not architecture)

The 149-lens scope + SubSignal → ParentFinding model + Stage-1a deterministic pre-pass + $100/$150 cost cap + conditional bundles **all land in v1**. These are the locked outputs of the 4 reshuffle passes + pressure-test. Architecture phases; content doesn't.

| Integration | v1 |
|---|---|
| Rubric inventory | ~149 rubrics across 4 agent YAML files + bundle files; one-shot Claude script parses catalog 005 → emits YAML |
| Finding model | `SubSignal` + `ParentFinding` (flat `Finding` deprecated) |
| Stage-1a pre-pass | 8 deterministic Python check modules (DNS/SPF/JSON-LD/badges/headers/social-meta/brand-assets/tooling) |
| Cost cap | $100 soft warning / $150 hard breaker |
| Conditional bundles | Vertical (25) + geo (10) + segment (5) activated by Stage-1b detection signals |

### v1 file changes (revised — smaller)

**NEW Python modules (~5-6):**
- `src/audit/orchestrator.py` — state machine, async fan-out, resume logic (~300 LOC)
- `src/audit/agent_runner.py` — SDK wrapper, cost capture, session_id persistence (~100 LOC)
- `src/audit/checkpointing.py` — atomic state read/write, stage progress (~60 LOC)
- `src/audit/telemetry.py` — events.jsonl writer, Slack notifier (~80 LOC)
- `src/audit/preflight/runner.py` + 8 check modules (~700 LOC total)

**NEW YAML data files:**
- `data/rubrics_findability.yaml` + 3 other agent rubrics + `rubrics_phase0_meta.yaml`
- `data/bundles_vertical.yaml` + `bundles_geo.yaml` + `bundles_segment.yaml`
- `data/preflight_lenses.yaml`
- Total ~1500 LOC YAML (mechanical one-shot Claude authoring from catalog)

**MODIFIED files:**
- Existing plan (R3 7→4 agents, R7 cost cap, U1 state schema, U4 Stage-2 spec, U6 Stage-3 spec)
- `agent_models.py` (flat Finding → SubSignal + ParentFinding)
- `stage3.py` (SubSignal grouping → ParentFinding per section)
- `state.py` (extend for v1 state layout)
- `cli.py` (add `--resume`)
- `audit_report.html.j2` (render ParentFindings + SubSignal evidence rows)
- `stage1.py` (invoke Stage-1a preflight; populate detection signals)

### v1 signal capture (the load-bearing piece)

**Every audit captures structured signal for v2/v3 learning, even though v1 doesn't act on it.**

```
clients/<slug>/audit/signals/
  pre_ship.json           # full deliverable state before JR ship-gate
  ship_gate_edits.diff    # JR's edits to findings/proposal at ship-gate
  cost_actual.json        # realized per-stage cost (replaces fiction)
  agent_turns.json        # turn count per agent per audit
  lens_firings.jsonl      # which lenses fired, which returned findings, which returned NA
```

**Across audits, append to:**
```
audits/lineage.jsonl      # one row per completed audit
                          # {audit_id, completed_at, total_cost_usd, ship_gate_edit_count,
                          #  vertical, segment, geo, finding_count, severity_distribution}
```

This is the autoresearch pattern ported. Cheap to write in v1, load-bearing for v2/v3.

## v2 — Judges + structured signal (after 5-10 v1 audits)

Triggers to start v2: 5 audits shipped, cost baselines empirical, JR ship-gate edit patterns observable.

### v2 adds: four judge layers

**Judge-1. SubSignal validator (synchronous, per lens emission)**

Runs as a post-SubSignal hook on every Stage-2 agent. ~$0.02/call.

```python
class SubSignalJudgment(BaseModel):
    subsignal_id: str
    has_evidence_urls: bool
    severity_calibrated: bool         # 0-3 matches severity_anchors for this lens_id
    observation_specific: bool        # not generic platitude
    passes: bool                      # all three above
    reason_if_fails: str | None
```

**Failure action (v2 inner-loop pattern):** judge-driven self-correction. Agent gets ONE revision shot with the failure reason fed back as a `[JUDGE FEEDBACK: <reason>]` user message. If still fails, skip-not-raise + flag in `gap_report.md`. This replaces the existing plan's fixed "critique loop ≤3 iterations" pattern: instead of always running 3 critique passes (cost: 30-50% overhead unconditionally), we run zero critique passes by default and only spend correction cost when judges actually flag a problem. Same inner/outer-loop shape as autoresearch's per-variant critique → outer fitness pattern, applied at SubSignal granularity.

**Judge-2. ParentFinding strategic-story judge (synchronous, per section post-synthesis)**

Runs once per report section after Stage-3 synthesis. ~$0.10/call × 9 sections = ~$1/audit.

```python
class ParentFindingJudgment(BaseModel):
    parent_finding_id: str
    tells_strategic_story: bool       # not just a list of sub-issues
    is_actionable: bool               # JR could scope work from it
    does_not_repeat_other_sections: bool
    severity_rollup_correct: bool     # max(children) actually
    passes: bool
```

**Failure action:** re-synthesize that section once (cost: ~$1 per re-synth). If still fails, flag with `quality_warning` in deliverable metadata; JR sees weak ParentFindings highlighted at ship-gate review.

**Judge-3. Audit coherence judge (synchronous, post Stage-3 master merge)**

One Opus call after master merge. ~$0.30/audit.

```python
class AuditCoherenceJudgment(BaseModel):
    findings_cohere_into_narrative: bool
    surprises_are_actually_surprising: bool     # not just most-severe findings
    proposal_aligns_with_severity_distribution: bool
    no_contradictions_between_sections: bool
    passes: bool
    weak_link_list: list[str]                    # section names with issues
```

**Failure action:** Slack JR with weak-link list before ship-gate, so review focuses on flagged spots.

**Judge-4. Engagement-conversion judge (async long-loop, 60-day post-ship)**

Writes to `audits/lineage.jsonl` 60 days after audit ship, after JR updates `engagement_signed_usd` field manually (or auto via Stripe reconciliation).

```python
class EngagementConversionJudgment(BaseModel):
    audit_id: str
    shipped_at: datetime
    engagement_signed_usd: float | None          # filled in at T+60d
    engagement_signed_within_60d: bool
    retrospective_signal: dict                   # {audit_cost, agent_turns, ship_gate_edit_count,
                                                 #  finding_severity_distribution, vertical, segment}
```

**No action.** Pure signal. v3 evolution loop consumes this as fitness function.

**Judge overhead total: ~$3-5/audit** (3-5% of $100 budget). Cheap insurance.

### v2 adds: cross-audit memory layer (mechanical, not agentic)

Not "Opus proposes lessons monthly." Structured signal tables queried deterministically.

```
audits/
  lineage.jsonl                          # one row per audit (v1 already writes this)
  signals_by_agent.jsonl                 # one row per (audit, agent): cost, turns, SubSignal count,
                                         #   validator-judge pass rate, ship-gate edit count on that agent's findings
  signals_by_lens.jsonl                  # one row per (audit, lens): fired, produced_finding, severity,
                                         #   judge-validator pass, ship-gate survived
  signals_by_vertical.jsonl              # aggregate by detected vertical
  cost_baselines.json                    # rolling p50/p95 per stage per vertical per segment
```

Loaded at agent startup as a deterministic prompt prefix:

> "In prior Findability audits on PLG B2B SaaS prospects: lens L042 fires 89% but survives ship-gate only 34% (consider skeptically); lens L017 fires 12% but always produces high-severity findings that survive ship-gate (treat seriously when it fires). Rolling p95 cost for this agent in your cohort: $7.20 — flag if you're trending higher."

This is not "learning" in a deep sense — it's **carrying empirical base rates into the next audit**. But it's mechanical, verifiable, and doesn't require evolutionary machinery yet.

### v2 scope summary

- 4 judge layers
- Structured signal tables (lineage, by_agent, by_lens, by_vertical, cost_baselines)
- Base-rate prompt prefixes for v1 agents
- Slack alert on coherence judge weak-links

**Est v2 cost:** 3-4 weeks, ~6 new modules, ~$3-5/audit overhead.

## v3 — Autoresearch lane integration (after 20+ audits with judge data)

Triggers to start v3: 20 audits with full judge coverage, engagement-conversion signal on at least 10 audits, enough variance in agent prompt/rubric decisions to justify evolving them.

### Architecture: three layers sharing infrastructure deliberately

Marketing audit becomes a **new lane in the existing autoresearch evolution engine**, not a parallel system. autoresearch already has 5 lanes (`core`, `geo`, `competitive`, `monitoring`, `storyboard`); we add a 6th: `audit_agents`. Audit RUNTIME stays in `src/audit/` (different output shape, different cost envelope, different cadence); audit AGENT EVOLUTION lives in `autoresearch/archive/audit_agents/` (same archive shape as existing lanes).

```
┌─ LAYER 1: Audit runtime (per-prospect, transactional) ───────────────┐
│  src/audit/                                                           │
│  freddy audit run --client <slug>                                     │
│  Stages 0-5, judges, ship gate                                        │
│  At boot: reads autoresearch/archive/audit_agents/current.json        │
│           materializes per-agent variant config into runtime          │
│  At end: appends audit-id row to audits/lineage.jsonl                 │
│          (same JSONL shape as autoresearch/archive/lineage.jsonl)     │
└───────────────────────────────────────────────────────────────────────┘
                          │  resolves active variants from
                          ▼
┌─ LAYER 2: Agent variant archive (autoresearch lane: audit_agents) ───┐
│  autoresearch/archive/audit_agents/                                   │
│    vNNN/                                                              │
│      variant.json   {agent_role, system_prompt, rubric_weights,       │
│                      inner_loop_enabled, max_turns, parent_id}        │
│      scores.json    {judge_1_pass_rate, judge_2_pass_rate, ...}       │
│      changed_files.json                                               │
│    current.json     {findability: vNNN, narrative: vMMM, ...}         │
│    lineage.jsonl    parent/child + scores + promotion timestamps      │
│  Same archive shape, lineage format, atomic-write pattern as          │
│  existing autoresearch lanes — reuses lane_runtime.py + archive_index │
└───────────────────────────────────────────────────────────────────────┘
                          ▲  promotes winners to current.json via
                          │
┌─ LAYER 3: Evolution loop (autoresearch evolve.py, audit_agents lane) ┐
│  ./autoresearch/evolve.sh --lane audit_agents --iterations 1          │
│                            --candidates-per-iteration 3               │
│  Per generation per agent_role:                                       │
│   1. Parent selection: TOP_K_CANDIDATES from frontier per fitness     │
│   2. Meta-agent mutation: rewords system prompt, adjusts rubric       │
│      weights, toggles inner_loop_enabled, etc.                        │
│   3. Layer1 validation: critique-manifest hash + py_compile +         │
│      schema check (cheap, before expensive replay)                    │
│   4. Holdout replay: re-run 3-5 past audits with new variant via      │
│      audit_runtime in --holdout mode (writes to scratch dir)          │
│   5. Score against fitness function (see below)                       │
│   6. Promote if Pareto-dominant on lane objectives                    │
│   7. Append to lineage.jsonl + update current.json                    │
│  Runs offline (weekly cron). Acquires global state.evolve_lock so     │
│  it never competes with live customer audits for rate limits.         │
└───────────────────────────────────────────────────────────────────────┘
```

### What's reused from autoresearch (no reinvention)

| Component | Source | Reused as-is for audit_agents lane |
|---|---|---|
| Variant archive `vNNN/` shape | `autoresearch/archive/` + `lane_runtime.py` | yes |
| `current.json` lane manifest + atomic promotion | `lane_runtime.py:223-228` | yes (extended for per-agent-role variants: one current per role) |
| `lineage.jsonl` append-only history | `autoresearch/archive/lineage.jsonl` | yes (same JSON shape; namespaced via `lane: "audit_agents"`) |
| Parent selection policy | `evolve.py:848-850` + `select_parent.py` | yes |
| Meta-agent mutation subprocess | `evolve.py:855-898` | yes (1800s timeout sufficient for one-agent-role mutation; v3 mutates one role per generation, not all 4 at once) |
| Layer1 validation gating | `evaluate_variant.py:544-594` (manifest hash + py_compile + bash -n + import check) | yes (extended to validate variant.json schema before replay) |
| Wall-clock cohort flushing | `evolve.py:825,988-1000` SIGALRM + `_sigalrm_handler` | yes (cohort = one generation × N candidates × M agent roles) |
| Telemetry blindness (proposer can't see metrics) | `compute_metrics.py` outside variant workspace | yes (judge scores + engagement-conversion never in proposer's view) |
| `evolve.sh promote` + autonomous promotion | `evolve.py:1014` + `_do_finalize_step` | yes (operates per agent_role) |
| `evolve.sh rollback` | existing | yes |

### What's lane-specific (built new for audit_agents)

| Component | Why it's different |
|---|---|
| Holdout replay shape | Replays past audits (~$30-60 each) instead of search fixtures (~$1-5 each); holdout size capped at 3-5 audits per generation, not 20+ |
| Variant materialization into runtime | `audit_runtime_bootstrap.py` reads `current.json` and writes per-agent config into `src/audit/data/active_agent_variants.yaml` before runtime starts (mirrors `autoresearch/runtime_bootstrap.py:14` pattern) |
| Per-agent-role parent selection | Variants are per-role (findability vs narrative vs ...), not whole-system. `current.json` has one promoted variant per role; evolve runs one role per generation |
| Holdout mode in audit runtime | `freddy audit run --holdout --replay-id <past-audit-id>` writes to scratch dir, doesn't touch customer-visible state, doesn't trigger ship gate |
| Engagement-conversion signal ingestion | 60-day async judge writes to `audits/lineage.jsonl` after JR records `engagement_signed_usd`; evolve loop reads this for fitness |
| Concurrency guard | evolve acquires `state.evolve_lock`; audit runtime checks lock before starting (prevents rate-limit competition) |

### Fitness function per variant

```python
fitness = (
    0.40 * judge_1_subsignal_validator_pass_rate     # synchronous quality
    + 0.20 * judge_2_parent_finding_pass_rate         # synchronous quality
    + 0.20 * (1.0 - normalize(ship_gate_edit_count))  # human signal
    + 0.20 * engagement_conversion_rate_60d           # business signal
)
```

Weights revisited per generation as engagement-conversion data accumulates. Pareto-dominance check on `(quality_score, ship_gate_score, engagement_score)` for promotion — variant must be no worse than parent on all three axes and strictly better on at least one.

### Variant shape

```json
{
  "variant_id": "v042",
  "lane": "audit_agents",
  "agent_role": "findability",
  "parent_variant_id": "v039",
  "system_prompt_template_path": "prompts/findability_v042.md",
  "rubric_weights": {"L042": 1.2, "L017": 0.8, "L091": 1.0},
  "inner_loop_enabled": true,
  "inner_loop_judge_threshold": 0.6,
  "max_turns": 500,
  "max_budget_usd": 12.0,
  "fallback_model": "claude-sonnet-4-5"
}
```

Each variant is a small JSON blob + a system prompt markdown file. Materialization is a thin Python that reads variant.json + writes the runtime config + symlinks the prompt template path.

### Inner loop = judge-driven self-correction (v2 pattern, evolved in v3)

The inner loop spec from §v2 Judge-1 (judge-driven SubSignal correction with one revision shot) becomes a **variant-evolvable parameter** in v3. Different agent variants can have:
- `inner_loop_enabled: false` — single-pass, cheapest
- `inner_loop_enabled: true, threshold: 0.6` — judge-gated correction
- `inner_loop_enabled: true, threshold: 0.4` — more aggressive correction
- (future) `inner_loop_strategy: "multi_candidate"` — generate N candidates, judge picks best

Evolution discovers the right inner-loop config per agent role empirically, not by guess.

### v3 cost envelope

| Operation | Cost |
|---|---|
| One holdout replay of one past audit | ~$30-60 (full audit cost) |
| One generation: 1 role × 3 candidates × 3-5 holdout audits | ~$300-900 |
| One full evolve cycle: 4 roles × 1 generation each, weekly | ~$1200-3600/week |
| Amortized per customer audit (at 5 audits/week steady state) | ~$240-720/audit overhead |
| Amortized per customer audit (at 20 audits/week steady state) | ~$60-180/audit |

Higher than I initially estimated. Implication: **v3 only earns its keep at >5 audits/week steady state**. Below that, manual prompt tuning is cheaper than evolution. Trigger to start v3 = 20 paid audits + 5/week steady-state pace, not just 20 audits absolute.

### v3 what could go wrong (honest pre-mortem)

1. **Holdout cost sticker shock.** $300-900 per generation is real money. Mitigation: hard cap per evolve generation ($1000); rolling 3-generation "fitness actually improving?" check before continuing; pause evolve if fitness flat for 3 cycles.
2. **Goodhart on judges.** Variants over-fit to SubSignal validator while losing real strategic depth. Mitigation: judges themselves don't evolve in v3 (only agent variants do); JR manually reviews promoted variants before they ship customer audits; engagement-conversion (Judge-4) is the ground-truth check that catches Goodhart on Judges 1-3.
3. **Lineage pollution across lanes.** Adding audit_agents writes weird stuff into shared `lineage.jsonl`. Mitigation: `lineage.jsonl` already supports lane-namespaced filtering (existing autoresearch tooling filters by `lane` field); audit_agents events are just another lane.
4. **Meta-agent timeout under audit-agent context size.** 149 lenses × 4 agent roles = lot of context for the meta-agent to reason over. Existing 1800s timeout might bite. Mitigation: per-agent-role mutation (one role per generation); meta-agent gets only that role's prompt + rubrics + recent fitness scores, not the whole audit system.
5. **Cross-lane resource contention.** evolve generation runs while a customer audit fires → both compete for Claude rate limits. Mitigation: `state.evolve_lock` is a global mutex; evolve refuses to start if any audit is active (`state.active_run` set), audit runtime refuses to start if evolve is active.
6. **Engagement-conversion signal lag.** 60-day window means evolve fitness is always 2 months stale on Judge-4. Mitigation: fitness function weights synchronous judges (60% combined) higher than engagement (20%); engagement is corrective signal, not primary driver.

### v3 = genuinely self-improving (the closed loop)

```
audits produce judge scores
      ↓
judge scores feed lineage.jsonl
      ↓
evolve.sh --lane audit_agents reads lineage, mutates parent variants
      ↓
holdout replay scores new variants against past audits
      ↓
Pareto-dominant variants get promoted to current.json
      ↓
next customer audit reads current.json, materializes promoted variants
      ↓
better audits produce better judge scores
```

No human in the learning loop. JR's role: ship-gate review (which itself becomes Judge-3 signal) + 60-day engagement tracking (which becomes Judge-4 signal). Both already part of the workflow — no new ops burden.

## LHR primitives inventory (ported + native)

Unchanged from first draft in substance; simplified for v1 per phasing above.

### From `harness/` (95% reuse of LHR primitives)

- `sessions.py` SessionsFile pattern (atomic + lock) → state.sessions/<role>.json
- `engine.py` rate-limit detection from stream-json tail → adapted for SDK ResultMessage
- `findings.py` skip-not-raise on malformed YAML → skip-not-raise on malformed SubSignals
- `run.py` per-cycle directory structure → per-stage directory structure
- `run.py` graceful-stop atomic flag → SIGTERM handler in orchestrator
- `safety.py` scope allowlist + leak detection → adapted as per-stage output validation (v2+)
- `preflight.py` validation-before-launch → orchestrator pre-flight (env vars, providers reachable, cost cap sane)

### From `autoresearch/` (philosophical donor for v1, literal engine for v3)

- Filesystem-as-source-of-truth (v1)
- Append-only `lineage.jsonl` pattern → `audits/lineage.jsonl` (v1; same JSON shape so v3 evolve loop reads it without migration)
- Atomic write (temp + rename) (v1)
- Wall-clock cohort flushing (v1 telemetry)
- Layer1 validation gating → Stage-1a deterministic pre-pass (v1; in v3 also gates variant validation before holdout replay)
- **NEW lane integration (v3)** — `audit_agents` becomes the 6th lane alongside `core`, `geo`, `competitive`, `monitoring`, `storyboard`. Reuses: `lane_runtime.py` (current.json + materialization), `archive_index.py`, `evolve.py` (parent selection + meta-agent mutation + cohort flush), `evaluate_variant.py` (layer1 validation pattern; per-audit-replay scoring is lane-specific), `select_parent.py` (TOP_K_CANDIDATES + TRAJECTORY_WINDOW), `compute_metrics.py` (telemetry-blindness pattern; metrics outside variant workspace), `evolve.sh` operator commands (`score-current`, `seed-baseline`, `--lane audit_agents`, `finalize`, `promote`, `rollback`)
- Variant archive `vNNN/` shape + `current.json` per-lane manifest → `autoresearch/archive/audit_agents/` (v3)
- Per-lane wall-clock budget + cost-cap discipline (v3 — hard cap per evolve generation, fitness-flat-3-cycles pause)
- Telemetry blindness (proposer can't see metrics it might game) (v3 — judges + engagement-conversion never visible to meta-agent)

### From Claude Agent SDK (native, don't reinvent)

- `ClaudeSDKClient` multi-turn (not `query()`)
- `ClaudeAgentOptions(max_budget_usd, max_turns, session_id, resume, fork_session, enable_file_checkpointing, hooks, mcp_servers, fallback_model)`
- `ResultMessage.total_cost_usd` + `session_id` for cost ledger
- Hooks (PreToolUse, PostToolUse, PreCompact, Stop)
- `fork_session` (v2 judges can fork agent sessions to critique without mutation)

## Open follow-ups (need decision before v1 implementation begins)

1. **Rubric authoring approach.** Recommendation: one-shot Claude script parses catalog 005 → emits 4 agent YAML files (bounded mechanical work).
2. **First implementation unit for v1.** Recommendation: (A) rubric YAML authoring → (C) preflight pre-pass → (B) SubSignal schema migration → (D) orchestrator → tests woven throughout.
3. **Dogfood prospect selection.** Need 5 prospect URLs from JR's pipeline (B2B SaaS preferred for vertical-bundle activation testing).
4. **Branch reconciliation.** Recommendation: merge `feat/fixture-infrastructure` → main first, then start v1 implementation from clean main.
5. **v2 trigger discipline.** Resist adding judges to v1. They belong in v2 after v1 produces ship-gate signal. Revisit only if v1 audits consistently ship with quality issues JR catches at gate.

## What this design is NOT

- Not a guess at the perfect architecture. v1 is deliberately under-specified; architecture hardens as real audit data accumulates.
- Not a rewrite of the existing 1534-line plan. Plan is the implementation contract; this doc is the autonomy + phasing overlay.
- Not an assertion that 4 agents is right. Might be 3, might be 6 — first 5 audits tell us.
- Not a commitment to build judges + evolution now. They're specified so we capture the right v1 signal *for them*, not so we build them in parallel.
- **Not a parallel system to autoresearch.** v3 audit_agents is a NEW LANE inside the existing autoresearch evolution engine. The runtime stays in `src/audit/`; the variant evolution lives in `autoresearch/archive/audit_agents/`. Reuses 95%+ of autoresearch's machinery (variant archive, lineage, evolve.py, promotion, layer1 validation).
- **Not coupled in v1 or v2.** Coupling pays back at v3 when there's actual variant signal to evolve on. v1+v2 keep `audits/lineage.jsonl` in autoresearch-compatible shape so v3 can pick it up without migration.

## Validation against decisions log (unchanged from first draft)

- ✅ Manual-fire policy preserved (R14)
- ✅ Telemetry-not-gating preserved (R7)
- ✅ Three-gate model preserved (R8)
- ✅ Local storage only (R6)
- ✅ Owned-provider-first (R17)
- ✅ Locked lens scope honored (`2026-04-22-005-marketing-audit-lens-catalog.md`)
- ✅ SubSignal→ParentFinding aggregation locked
- ✅ Stage-1a deterministic pre-pass locked
- ✅ Cost cap lift to $100/$150 locked

## Sources

- `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` — existing implementation plan
- `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` — locked lens catalog
- `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md` — linear ranking + cutoff
- `harness/` — LHR primitives source
- `autoresearch/` — v3 evolution engine source (uses as-is)
- Claude Agent SDK Python docs (via ctx7)
