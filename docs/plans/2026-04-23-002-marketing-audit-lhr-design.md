---
title: "design: Marketing audit LHR (long-horizon-running) layer"
type: design
status: active
date: 2026-04-23
extends: 2026-04-20-002-feat-automated-audit-pipeline-plan.md
related:
  - 2026-04-22-005-marketing-audit-lens-catalog.md
  - 2026-04-22-006-marketing-audit-lens-ranking.md
---

# Marketing audit LHR (long-horizon-running) layer

## Premise

The existing implementation plan (`2026-04-20-002-feat-automated-audit-pipeline-plan.md`, 1534 lines) describes a 6-stage marketing audit pipeline that JR fires manually via `freddy audit run`. It already has session-level resumability via the Claude Agent SDK, three operational circuit breakers, and ~7 Stage-2 agents producing 9 report sections.

This design doc adds the **LHR primitive layer** that bridges between "manually-fired pipeline" and "fully-automated long-horizon-running pipeline" — the autonomy primitives that let it run end-to-end without intervention while staying safe at the $1K customer-deliverable price point. It also specifies the **locked-lens-scope integration** (149 always-on lenses + 25 vertical + 10 geo + 5 segment bundles + 9 Phase-0 meta-frames per `2026-04-22-005-marketing-audit-lens-catalog.md`) that the existing plan doesn't yet reflect.

This is **not a rewrite**. It is a focused supplemental layer. The 6-stage pipeline shape, the 9 report sections, the 3 hard gates, the cost-telemetry-not-gating philosophy, and the manual-fire-by-default discipline (R14) all stand. What changes is: rubric inventory, finding schema, Stage-1a content, cost cap parameters, plus a thin orchestrator wrapper that adds the LHR primitives.

## Decisions locked

Three open decisions surfaced during research synthesis. Locked here with rationale; revisit if first 5 dogfood audits invalidate the assumptions.

### D1. Trigger model: CLI-only for v1, queue + webhook deferred to v2

**Decision:** Keep the existing `freddy audit run --client <slug>` CLI as the only trigger surface for v1. Defer webhook + queue (`arq` on Redis) to v2 after first 5 audits validate the pipeline.

**Rationale:**
- v1 success criterion is "5 paid audits delivered, $15K engagement-conversion measured" — not throughput. CLI is sufficient for that volume.
- Manual-fire is already the policy (R14). Adding a queue at v1 would introduce infra surface (Redis, worker process supervision) that doesn't pay back until volume justifies it.
- Webhook trigger is mostly orthogonal to the LHR question — it's about *how an audit gets queued*, not *how an audit runs autonomously*. We can add webhook → queue without touching orchestrator internals.

**v2 trigger model (deferred):** Cloudflare Worker → Fly API `/v1/audit/queue` → `arq` Redis queue → worker process consumes → audit runs in worker. One audit per worker process; horizontal scale via more workers.

### D2. Human-review gate: keep mandatory `freddy audit ship` through v1

**Decision:** The existing PUBLISH gate (R8 #3, line 36 of the plan) is preserved. JR reviews the rendered deliverable locally before publishing. No auto-publish in v1.

**Rationale:**
- At $1K/audit with reputational risk against a $15K engagement pitch, the marginal value of full autonomy is negative. One bad auto-shipped audit costs more than 100 manual ship-gate clicks.
- External research consensus (Anthropic, LangChain, multiple production write-ups): mandatory human gate before customer-facing $$$ deliverables is the durable pattern. "Long-horizon agents are here. Full autopilot isn't." (DEV.to 2026)
- Removing the gate is a one-line config change later, once empirical failure rates support it. Adding it back after a public bad-ship is much more expensive.

**Trigger to revisit:** After 20 paid audits with zero ship-gate vetoes that catch real defects, lift the gate to a "post-ship review" pattern (auto-ship + flag-and-rollback if anomaly).

### D3. Concurrent audit isolation: serialize at worker level

**Decision:** One audit per worker process. No git worktrees per audit. Each audit uses `clients/<slug>/audit/` as its scoped working directory; in-process state isolation by passing `state` explicitly into orchestrator functions.

**Rationale:**
- Audits produce artifacts; they don't mutate the repo. Worktrees solve a code-mutation isolation problem (the bug-fixing harness does that), not an artifact-production problem.
- Per-audit working dir + explicit state argument is sufficient isolation. The concurrency bug surface (shared module state in `src/audit/`) is avoided by *not running two audits in the same process*.
- Horizontal scale = more worker processes (each consumes one audit at a time from the v2 queue). Linear scaling, no shared-state contention.

**Implication:** v1 CLI invocation is single-audit-at-a-time per laptop. If JR wants to run 2 audits in parallel during dogfood, run two terminal sessions (each acquires its own `state.active_run` lock for the relevant client).

## LHR primitive layer (ported from `harness/`, native to Claude Agent SDK)

The harness already ships 95% of the LHR primitives we need. The audit pipeline borrows the patterns, adapts them to async (vs the harness's threading), and uses the SDK's native session/checkpoint primitives where they exist.

### LHR-1. State + checkpointing

**Pattern:** File-per-stage JSON checkpoints + per-lens SubSignal files. Atomic writes via temp file + rename. No database.

**Why this and not Temporal / LangGraph:** A $1K transactional audit running in minutes-to-hours doesn't need a workflow engine. File-system checkpointing is sufficient for resume; SDK gives us `session_id` + `resume="<id>"` + `enable_file_checkpointing=True` natively. Temporal pays back at >100 audits/day or multi-process workflows.

**State layout per audit (extends existing `state.json` spec from plan U1):**

```
clients/<slug>/audit/
  state.json                              # orchestrator state (atomic write)
  cost_log.jsonl                          # per-call cost events (append-only)
  events.jsonl                            # per-stage telemetry events (append-only)
  sessions/                               # SDK session checkpoints
    pre_discovery.json                    # {session_id, last_turn, last_cost_usd, status}
    agent_findability.json
    agent_brand_narrative.json
    ...
  stage1a_preflight/                      # NEW — deterministic pre-pass results
    dns_spf_dkim_dmarc.json
    well_known_files.json
    json_ld.json
    badge_regex.json
    tooling_fingerprint.json
  stage2_subsignals/                      # NEW — per-lens SubSignal files
    L001_organic_keyword_overlap.json     # {lens_id, agent, evidence_urls, observation, severity, confidence}
    L002_branded_query_share.json
    ...
  stage3_sections/                        # NEW — per-section synthesis checkpoints
    seo.json                              # ParentFindings for SEO section (intermediate)
    geo.json
    ...
  stage3_synthesis/                       # final synthesis output
    findings.md
    surprises.md
    report.md
    report.json
    gap_report.md
```

**Resume behavior:**
- On `freddy audit run --resume`, orchestrator inspects `state.current_stage` + checks which files exist
- Stage 2: skip lens checks whose `stage2_subsignals/L<id>_*.json` already exists
- Stage 3: skip sections whose `stage3_sections/<section>.json` already exists
- Skipped work costs $0; only missing pieces re-run

**Files affected:** `src/audit/state.py` (extend with stage_progress index), `src/audit/orchestrator.py` (NEW; resume logic).

### LHR-2. Parallelism: `asyncio.TaskGroup` + `Semaphore(9)`

**Pattern:** Stage 2 fan-out uses `asyncio.TaskGroup` (structured concurrency, fail-fast cleanup) over 9 lens-checker agents. `Semaphore(9)` caps concurrency at the agent boundary. `tenacity` provides exponential-jitter retries on transient failures (rate limits, malformed JSON).

**Why TaskGroup not gather:** `asyncio.gather(return_exceptions=True)` swallows exceptions silently; debugging is painful. `TaskGroup` (Python 3.11+) cleans up sibling tasks on first failure, which matches the harness's graceful-stop semantics.

**Why 9 not 7 agents:** The locked lens scope (`2026-04-22-005-marketing-audit-lens-catalog.md`) maps 149 always-on lenses to 11 marketing areas. Mapping 11 areas onto 7 agents requires uncomfortable bundling (e.g., Conversion + Lifecycle + CX into one agent). Going to 9 agents lets each agent own ~16 lenses on average and aligns 1:1 with most report sections.

**Concrete agent set (revised from existing plan's 7):**

| Agent | Lens areas owned | Approx lens count | Output report section |
|---|---|---|---|
| 1. Findability | Discoverability & Organic Search (Area 1) | 24 | SEO + GEO |
| 2. Content & Authority | Content Assets (Area 2) + Brand & Authority (Area 9) | 20 | Brand/Narrative |
| 3. Paid Media | Paid Media (Area 3) | 6 | Distribution |
| 4. Earned & PR | Earned Media & PR (Area 4) | 6 | Distribution |
| 5. Distribution & Community | Distribution, Community & Listings (Area 5) | 13 | Distribution |
| 6. Conversion | Conversion Architecture (Area 6) | 12 | Conversion |
| 7. Activation & Lifecycle | Activation (Area 7) + Lifecycle (Area 8) | 22 | Lifecycle |
| 8. Sales/GTM | Sales / GTM / Enablement (Area 10) | 10 | MarTech-Attribution |
| 9. MarTech & Compliance | MarTech, Measurement & Compliance (Area 11) | 27 | MarTech-Attribution + Compliance |
| Phase 0 (meta) | 9 meta-frames | 9 | woven into all sections by Stage 3 |

Stage 3 Opus synthesis still produces 9 report sections (Competitive + Monitoring + Phase-0 woven in), so the agent↔section map is many-to-one as before.

**Per-agent ClaudeAgentOptions (extends plan U4 line 602):**
```python
ClaudeAgentOptions(
    tools={"type": "preset", "preset": "claude_code"},
    mcp_servers={"audit": register_audit_tools(state)},
    permission_mode="bypassPermissions",
    enable_file_checkpointing=True,
    max_turns=500,
    max_budget_usd=12.0,                    # NEW — per-agent hard cap
    model="claude-sonnet-4-6",
    fallback_model="claude-sonnet-4-5",     # NEW — graceful model degrade
)
```

**Retry / timeout wrapper (NEW pattern):**
```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=1, max=60),
    retry=retry_if_exception_type((CLIConnectionError, RateLimitError)),
)
async def run_lens_agent(agent_cfg, state):
    async with asyncio.timeout(600):       # 10-min per-agent ceiling
        async with ClaudeSDKClient(options=...) as client:
            ...
```

**Files affected:** `src/audit/orchestrator.py` (NEW), `src/audit/agent_runner.py` (NEW; wraps SDK with retries + timeout + cost capture).

### LHR-3. Cost control (three tiers)

**Pattern (from external best-practices research):**
1. **Per-call:** `ClaudeAgentOptions(max_budget_usd=...)` per agent — SDK enforces, raises on overrun
2. **Per-stage soft cap:** orchestrator logs warning + Slack ping when stage spend exceeds soft threshold (does NOT abort — telemetry, not gating, per R7)
3. **Per-audit hard breaker:** `state.cost_spent_usd` accumulates from every `ResultMessage.total_cost_usd`. Cross $150 → raise `CostBreakerExceeded` and halt subsequent stages. Default soft cap raised from $50 → $100 (per locked lens scope; existing plan U1 line 324 still defaults to $50).

**Per-stage budget allocation (revised; replaces R7 line 26-34 estimates):**

| Stage | Soft budget | Notes |
|---|---|---|
| 0 Intake | $0 | Python only |
| 1a Preflight (deterministic) | $0 | Python only — DNS/SPF/JSON-LD/badge-regex saves ~$10/audit vs current plan |
| 1b Pre-discovery (Sonnet) | $25 | reduced from $30 (some surface moved to 1a) |
| 1c Brief synthesis (Opus) | $1 | unchanged |
| 2 Lens agents (9 × Sonnet × critique loop) | $60 | 9 × ~$5 + critique loop overhead |
| 3 Synthesis (9 sections + master + critique + rationale) | $10 | unchanged |
| 4 Proposal (Opus) | $2 | unchanged |
| 5 Deliverable | $0 | Jinja + WeasyPrint |
| **Total soft cap** | **$98** | rounds to $100 |
| **Hard breaker** | **$150** | 50% headroom for adversarial / large-prospect cases |

**Telemetry source:** every `ResultMessage` from every SDK session streams `total_cost_usd` and `session_id`. Orchestrator's cost ledger appends to `cost_log.jsonl` per call.

**Files affected:** `src/audit/orchestrator.py` (cost accumulator + soft/hard checks), `src/audit/state.py` (extend `cost_spent_usd` semantics), `src/audit/data/cost_caps.yaml` (NEW — per-stage soft caps configurable).

### LHR-4. Recovery: skip-not-raise + per-lens checkpoints + section-level Stage-3 atomicity

**Three failure modes addressed:**

**(a) Malformed lens output (skip-not-raise — already adopted in commit `ff2f2e4`):**
- Lens agent emits a SubSignal that fails Pydantic validation
- Caught at `MalformedSubSignal` boundary, logged to `events.jsonl` with `severity=warning`
- Audit continues; Stage 3 reports the affected lens as `gap_flagged` in `gap_report.md`

**(b) Mid-Stage-2 agent crash:**
- If crash AFTER first `ResultMessage` (session_id persisted to `state.sessions/<agent>.json`): `--resume` continues via `resume=<session_id>`
- If crash BEFORE first `ResultMessage`: restart that agent from scratch; cost is one extra agent-startup (~$0.50)
- Other 8 agents in TaskGroup are *not* canceled — TaskGroup's fail-fast is bypassed by per-agent exception handlers; we want partial completion, not all-or-nothing

**(c) Mid-Stage-3 orchestrator crash (the previously-unaddressed gap):**
- Stage 3 fans out 9 section LLM calls + master merge + critique + rationale
- Each section result is written to `stage3_sections/<section>.json` *before* moving to master merge
- On `--resume` after Stage-3 crash: orchestrator inspects `stage3_sections/`, re-runs only missing sections, then resumes from master merge
- Avoids the $5-10 of duplicate synthesis cost identified as a gap in research

**Files affected:** `src/audit/stage3.py` (refactor to write per-section files atomically before merge), `src/audit/orchestrator.py` (resume logic).

### LHR-5. Telemetry: structured JSONL events + cost ledger

**Pattern (v1):** Per-audit JSONL event log at `clients/<slug>/audit/events.jsonl`. Schema:
```json
{"ts": "2026-04-23T20:30:00Z", "stage": "stage_2", "event": "agent_started",
 "agent": "findability", "session_id": "..."}
{"ts": "...", "stage": "stage_2", "event": "subsignal_emitted",
 "agent": "findability", "lens_id": "L042", "severity": 2, "cost_usd": 0.12}
{"ts": "...", "stage": "stage_2", "event": "agent_completed",
 "agent": "findability", "subsignal_count": 24, "cost_usd": 5.34, "duration_ms": 287000}
```

**Pattern (v2 deferred):** OpenLLMetry → self-hosted Langfuse via OTLP endpoint. Auto-instruments Anthropic SDK calls; gives waterfall traces across 9 parallel agents. Skip until v1 dogfood reveals what queries we actually need.

**Slack alerts (existing pattern, unchanged):**
- Cost anomaly (3σ above rolling p95)
- Pre-flight gate triggered
- Cost breaker triggered ($150)
- Audit completed (success path)

**Files affected:** `src/audit/telemetry.py` (NEW — thin event-log writer + Slack notifier).

## Locked lens scope integration (the BLOCKING gap)

The existing plan ships ~50 rubrics across 7 agents. The locked scope is 149 always-on rubrics across 9 agents. Until this gap closes, the LHR can't actually produce the locked-scope deliverable. This is the largest pre-implementation work item.

### Lens-1. Rubric inventory expansion: ~50 → ~149

**Pattern:** Per-agent `data/rubrics_<agent>.yaml` files. Each entry maps a lens_id to: report_section, severity_anchors, evidence_requirements, prompt_text_excerpt, conditional_bundle (if applicable).

**Source of truth:** `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` §A-W super-section detail (engineering view) lists every lens with sub-signals. One YAML entry per lens.

**Estimated size:** ~149 entries × ~10 lines/entry = ~1500 LOC across 9 YAML files. Bounded, mechanical work — but cannot be deferred (rubrics are inline-loaded into agent prompts at render time per existing plan U4 line 551).

**Files affected (NEW):**
- `src/audit/data/rubrics_findability.yaml`
- `src/audit/data/rubrics_content_authority.yaml`
- `src/audit/data/rubrics_paid_media.yaml`
- `src/audit/data/rubrics_earned_pr.yaml`
- `src/audit/data/rubrics_distribution_community.yaml`
- `src/audit/data/rubrics_conversion.yaml`
- `src/audit/data/rubrics_activation_lifecycle.yaml`
- `src/audit/data/rubrics_sales_gtm.yaml`
- `src/audit/data/rubrics_martech_compliance.yaml`
- `src/audit/data/rubrics_phase0_meta.yaml`
- `src/audit/data/bundles_vertical.yaml` — 25 conditional bundles
- `src/audit/data/bundles_geo.yaml` — 10 conditional bundles
- `src/audit/data/bundles_segment.yaml` — 5 conditional bundles

### Lens-2. Finding model: SubSignal → ParentFinding aggregation

**Pattern (from `2026-04-22-005-marketing-audit-lens-catalog.md` §Architectural Patterns):**
- Each lens emits a `SubSignal` (lens_id + evidence_urls + one-line observation + severity 0-3 + confidence)
- Stage-3 synthesis groups SubSignals by `report_section` into `ParentFinding` objects
- Deliverable shows ~25-32 `ParentFinding`s; SubSignals render as evidence rows underneath
- Severity rolls up as `max(child severities)`; confidence as `floor(child confidences)`

**Schema (NEW; replaces flat Finding from existing plan U4 line 549-550):**
```python
class SubSignal(BaseModel):
    lens_id: str                           # e.g. "L042"
    agent: str                             # which Stage-2 agent produced it
    report_section: Literal[...]           # routing key for Stage 3
    evidence_urls: list[HttpUrl]
    observation: str                       # one-line finding
    severity: Literal[0, 1, 2, 3]
    confidence: Literal[0, 1, 2, 3]
    rubric_coverage: Literal["covered", "gap_flagged"]

class ParentFinding(BaseModel):
    finding_id: str                        # synthesized in Stage 3
    report_section: Literal[...]
    headline: str                          # Opus-synthesized strategic statement
    severity: Literal[0, 1, 2, 3]          # max(children)
    confidence: Literal[0, 1, 2, 3]        # floor(children)
    children: list[SubSignal]              # 1-N SubSignals from Stage 2
    proposal_tier_mapping: Literal["fix-it", "build-it", "run-it"] | None  # back-filled by Stage 3
```

**Stage 3 refactor (concrete):**
- Existing plan: Stage 3 calls 9 section Opus calls, each receives raw findings for its section
- New: Stage 3 (a) loads all SubSignals from `stage2_subsignals/`, (b) groups by `report_section`, (c) one Opus call per section receives the SubSignal list + emits `ParentFinding[]`, (d) writes per-section file to `stage3_sections/<section>.json`, (e) master merge composes `report.md` from ParentFindings, (f) critique + rationale unchanged.

**Files affected:**
- `src/audit/agent_models.py` (replace Finding with SubSignal + ParentFinding)
- `src/audit/stage3.py` (refactor to group SubSignals → ParentFindings)
- `src/audit/templates/audit_report.html.j2` (render ParentFindings as headline + SubSignals as evidence rows)

### Lens-3. Stage-1a deterministic pre-pass

**Pattern:** ~25 cheap, deterministic lens checks moved out of LLM agents into pure Python. Saves ~$10/audit, runs in <30s, deterministic for testing.

**Lenses to move (sourced from `2026-04-22-005-marketing-audit-lens-catalog.md` §Architectural Patterns):**
- DNS resolution + SPF/DKIM/DMARC presence
- `/.well-known/security.txt`, `/.well-known/ai.txt`, `/robots.txt`, `/sitemap.xml` existence
- JSON-LD schema parsing (Organization, BreadcrumbList, Product, Article, FAQPage)
- Trust badge regex (G2, Capterra, TrustPilot, BBB, SOC2, ISO27001, GDPR)
- Tooling fingerprint (Wappalyzer-next + martech_rules.yaml — already exists per existing plan)
- URL probes (HTTPS, redirect chain length, HSTS header, CSP header presence, X-Frame-Options)
- Open Graph + Twitter Card meta tag presence
- favicon + apple-touch-icon presence
- `humans.txt`, `contact.txt`, status-page link presence

**Module shape (NEW):**
```python
# src/audit/preflight/runner.py
async def run_stage1a_preflight(state: AuditState) -> Stage1aResult:
    """Run all deterministic pre-pass checks in parallel.
    Each check is a pure function returning structured data + emit SubSignal-shaped findings."""
    results = await asyncio.gather(
        check_dns_email_security(state.target_url),
        check_well_known_files(state.target_url),
        check_json_ld_schemas(state.target_url),
        check_trust_badges(state.target_url),
        check_tooling_fingerprint(state.target_url),
        check_security_headers(state.target_url),
        check_social_meta_tags(state.target_url),
        check_brand_assets(state.target_url),
        return_exceptions=True,
    )
    # Each check writes its own SubSignal to stage2_subsignals/L<id>_*.json
    # Stage 2 agents skip these lenses (rubric_coverage="covered" pre-set)
    return Stage1aResult(checks_completed=len([r for r in results if not isinstance(r, Exception)]))
```

**Files affected (NEW):**
- `src/audit/preflight/runner.py` — orchestrator
- `src/audit/preflight/dns_email_security.py`
- `src/audit/preflight/well_known.py`
- `src/audit/preflight/json_ld.py`
- `src/audit/preflight/trust_badges.py`
- `src/audit/preflight/security_headers.py`
- `src/audit/preflight/social_meta.py`
- `src/audit/preflight/brand_assets.py`
- `src/audit/data/preflight_lenses.yaml` — lens_id → check function mapping

### Lens-4. Cost cap parameter tune: $50 → $100 / $150 hard breaker

**One-line change:** existing plan U1 line 324 defaults `max_audit_cost_usd=50`. Update to:
```python
max_audit_cost_usd: float = 100.0       # soft cap (warning + Slack ping)
hard_breaker_cost_usd: float = 150.0    # hard halt (raises CostBreakerExceeded)
```

Per-client override remains via state.json (`state.max_audit_cost_usd`). Default applies to all dogfood audits.

### Lens-5. Conditional bundle activation

**Pattern:** Bundles (vertical / geo / segment) activate based on Stage-1 detection signals. Only bundles whose conditions match fire; rest are skipped. Avoids audit bloat for prospects outside a given vertical/geo/segment.

**Detection signals (Stage-1b adds these to `brief.json`):**
```python
class AuditBrief(BaseModel):
    # ... existing fields ...
    detected_verticals: list[str]          # ["e-commerce", "fintech"] — match against bundles_vertical.yaml
    detected_geos: list[str]               # ["EU", "UK"] — match against bundles_geo.yaml
    detected_segments: list[str]           # ["PLG"] — match against bundles_segment.yaml
```

**Stage 2 fan-out becomes:**
```python
always_on_lens_ids = load_always_on_lens_ids()  # 149 lenses
bundle_lens_ids = (
    load_vertical_bundle_lenses(brief.detected_verticals) +
    load_geo_bundle_lenses(brief.detected_geos) +
    load_segment_bundle_lenses(brief.detected_segments)
)
all_lens_ids = always_on_lens_ids + bundle_lens_ids
# Distribute across 9 agents based on rubrics_<agent>.yaml ownership
```

**Typical audit firing:** 149 always-on + 18-28 bundle hits = ~167-177 total lenses (per `2026-04-22-005-marketing-audit-lens-catalog.md`).

## Concrete file changes summary

### NEW files (create)
| File | Purpose | Approx LOC |
|---|---|---|
| `src/audit/orchestrator.py` | LHR orchestrator: state machine, async fan-out, cost ledger, resume logic | ~400 |
| `src/audit/agent_runner.py` | SDK wrapper: retries (tenacity), timeout, cost capture | ~120 |
| `src/audit/checkpointing.py` | Atomic write/read for state files; per-stage progress tracking | ~80 |
| `src/audit/telemetry.py` | JSONL event writer + Slack notifier | ~100 |
| `src/audit/preflight/runner.py` | Stage-1a deterministic pre-pass orchestrator | ~80 |
| `src/audit/preflight/{8 check modules}.py` | Individual deterministic checks | ~80 each = 640 |
| `src/audit/data/rubrics_{9 agent files}.yaml` | 149 lens definitions across 9 agents | ~1500 total |
| `src/audit/data/rubrics_phase0_meta.yaml` | 9 meta-frame definitions | ~150 |
| `src/audit/data/bundles_vertical.yaml` | 25 vertical conditional bundles | ~400 |
| `src/audit/data/bundles_geo.yaml` | 10 geo conditional bundles | ~200 |
| `src/audit/data/bundles_segment.yaml` | 5 segment conditional bundles | ~100 |
| `src/audit/data/cost_caps.yaml` | Per-stage soft caps (configurable) | ~30 |
| `src/audit/data/preflight_lenses.yaml` | lens_id → preflight check function mapping | ~60 |

### MODIFIED files
| File | Change | Source |
|---|---|---|
| `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` | Update R3 (7→9 agents), R7 (cost cap $50→$100/$150), U1 (state.json schema), U4 (Stage-2 spec), U6 (Stage-3 spec); reference this LHR design doc | source-of-truth update |
| `src/audit/agent_models.py` | Replace flat `Finding` with `SubSignal` + `ParentFinding`; deprecate Finding | Lens-2 |
| `src/audit/stage3.py` | Refactor to group SubSignals into ParentFindings; section-level checkpointing | LHR-4, Lens-2 |
| `src/audit/state.py` | Add `cost_spent_usd` accumulator semantics, `stage_progress` index, `sessions/` directory | LHR-1, LHR-3 |
| `src/audit/cli.py` | Add `freddy audit run --resume`, surface `freddy audit ship` (already in plan) | LHR-1, D2 |
| `src/audit/templates/audit_report.html.j2` | Render ParentFindings as headlines + SubSignals as evidence rows | Lens-2 |
| `src/audit/stage1.py` | Add Stage-1a preflight invocation before Stage-1b Sonnet pre-discovery; populate `brief.detected_verticals/geos/segments` | Lens-3, Lens-5 |

### TEST files (NEW)
| File | Purpose |
|---|---|
| `tests/audit/test_orchestrator_resume.py` | Resume from each stage; skip-not-raise on malformed SubSignal; section-level Stage-3 recovery |
| `tests/audit/test_cost_breaker.py` | Per-call cap enforcement, per-stage soft warning, hard breaker halt at $150 |
| `tests/audit/test_preflight_pre_pass.py` | Each of 8 deterministic checks (mock HTTP); SubSignal output schema |
| `tests/audit/test_subsignal_aggregation.py` | Stage-3 SubSignal → ParentFinding grouping; severity/confidence rollup |
| `tests/audit/test_bundle_activation.py` | Vertical/geo/segment detection → bundle activation; non-matching bundles skipped |
| `tests/audit/test_taskgroup_fanout.py` | 9-agent parallel fan-out; one-agent-fail doesn't kill others; per-agent cost capture |

## Out of scope (deferred to v2)

- **Webhook + queue trigger** (`arq` on Redis, Cloudflare Worker → Fly API → queue)
- **OpenLLMetry → Langfuse** observability (v1 uses JSONL event log only)
- **Multi-worker horizontal scale** (v1 is single-worker per laptop)
- **Auto-ship without human gate** (revisit after 20 paid audits with zero veto-on-defect)
- **Per-audit git worktrees** (not needed — audits don't mutate repo)
- **Cross-audit deduplication / caching** (each audit is independent; cache is per-audit only)
- **Predictive cost estimation per prospect** (defer until empirical baselines from first 5 audits)

## Open follow-ups (need decision before implementation begins)

1. **Rubric authoring source-of-truth.** The 149 rubric YAML entries can be authored from `2026-04-22-005-marketing-audit-lens-catalog.md` §A-W super-section detail by either (a) JR + Claude paired authoring, (b) a one-shot Claude script that parses the catalog markdown and emits YAML, (c) per-agent dedicated Claude session. Recommendation: **(b) one-shot script** — bounded mechanical work with clear input→output, easy to re-run if catalog updates. Decision needed on script approval.

2. **Existing plan update strategy.** This LHR design doc references the existing 1534-line plan. Two options: (i) leave both docs; existing plan is the implementation spec, this doc is the LHR layer overlay; (ii) merge LHR design INTO existing plan as new sections, keep this doc as the design rationale. Recommendation: **(i)** — keeps the existing plan stable as a contract, new LHR work lives in its own design doc with clear traceability.

3. **First implementation unit.** The work splits naturally into: (A) rubric YAML authoring (mechanical, ~1500 LOC YAML), (B) SubSignal model + Stage-3 refactor (schema migration), (C) preflight pre-pass module (8 checkers + orchestrator), (D) orchestrator + checkpointing + cost ledger (the LHR core), (E) test coverage. Recommendation: **start with (A) rubric YAML authoring** — it unblocks everything else and surfaces lens-definition gaps fast. Then (C) preflight (independent, deployable standalone), then (B) schema, then (D) orchestrator, finally (E) tests woven throughout.

4. **Dogfood audit selection.** First 5 audits validate the pipeline + cost envelope + ship-gate value. Need 5 prospect URLs from JR's pipeline (B2B SaaS preferred for vertical-bundle activation testing). Decision needed on which prospects.

5. **Active harness branch reconciliation.** `feat/fixture-infrastructure` is ahead of main with bugs #15-#19 + fixture work + this LHR design. Decision: merge to main first (clean base for LHR implementation), or implement LHR on the feat branch (faster, riskier — feat branch is also where active harness resume is running)? Recommendation: **merge to main first**, then start LHR implementation from main. Keeps LHR commits separable from harness/fixture commits.

## Validation against decisions log

This design honors prior locked decisions:
- ✅ Manual-fire policy preserved (R14)
- ✅ Telemetry-not-gating philosophy preserved (R7) — cost soft cap is warning, not abort
- ✅ Three-permanent-gate model preserved (R8) — payment, pre-discovery review, ship
- ✅ Local storage only (R6) — no DB, no Temporal
- ✅ Owned-provider-first (R17) — preflight uses existing fingerprint_martech_stack + adds bounded HTTP probes
- ✅ Locked lens scope honored (`2026-04-22-005-marketing-audit-lens-catalog.md`) — 149 always-on + bundles + Phase 0 meta-frames
- ✅ SubSignal→ParentFinding aggregation locked (catalog §Architectural Patterns)
- ✅ Stage-1a deterministic pre-pass locked (catalog §Architectural Patterns)
- ✅ Cost cap lift to $100/$150 locked (catalog §Architectural Patterns)

## Sources

- `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` — existing implementation plan (1534 lines, untouched until this design lands)
- `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` — locked lens catalog (149 + 25 + 10 + 5 + 9)
- `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md` — linear ranking + cutoff
- `harness/` — LHR primitives source (state machine, parallel queues, graceful-stop+resume, skip-not-raise, telemetry, safety)
- `autoresearch/` — alternative LHR shape reference (variant evolution loop) — *not* the pattern we're porting; included to document why we keep separate
- Claude Agent SDK Python docs (via ctx7) — `ClaudeSDKClient`, `ClaudeAgentOptions`, `ResultMessage.total_cost_usd`, `enable_file_checkpointing`, `resume`, `fork_session`, `max_budget_usd`, `fallback_model`, `hooks`
- External best-practices research synthesis (durable execution, async parallelism, cost attribution, observability, long-horizon agent autonomy patterns) — see commit message of this doc for source URLs
