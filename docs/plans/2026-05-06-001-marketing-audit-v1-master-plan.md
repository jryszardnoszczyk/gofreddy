# Marketing Audit v1 — Master Plan

**Status:** Active 2026-05-06. All 7 sections drafted + locked.

**Supersedes** (header notes will be added to source docs; no deletions):
- `docs/plans/2026-04-30-001-marketing-audit-v1-pipeline-plan.md` (framework-only)
- `docs/plans/2026-04-23-002-marketing-audit-lhr-design.md` (LHR design)
- `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` (original product spec)
- `docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md` (dormant v3 — absorbed; full autoresearch ships in v1)

**Canonical references (NOT superseded):**
- `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` — lens content authority (149 always-on + 25 vertical + 10 geo + 5 segment bundles + 9 Phase-0 meta-frames)

**Consultation pattern:** every load-bearing decision in this plan carries an inline source citation back to the originating plan + section/line. The four superseded plans are read deeply for every section; this master plan is the consolidation, not a replacement of their research.

---

## Section 1 — Goals, Non-Goals, North Star

### North Star

First-runnable pipeline that produces a marketing audit deliverable JR would proudly send to a paying client at $1–3K, generated end-to-end by an automated run — no manual prose-writing.

### Goals (in v1)

1. **Productized funnel from day 1:** free AI Visibility Scan → sales call → invoice → paid audit → walkthrough call. *[source: `2026-04-20-002` R10, R14, R15, R16]*
2. **All 149 always-on lenses preserved** + 25 vertical / 10 geo / 5 segment bundles + 9 Phase-0 meta-frames. Lens catalog v2 is canonical content; nothing reduced. *[source: `2026-04-22-005` §Locked Final Recommendations]*
3. **4 broad Stage-2 agents:** Findability, Narrative, Acquisition, Experience. SubSignal → ParentFinding aggregation, target ~25–32 ParentFindings per audit. *[source: `2026-04-23-002` §v1 line 56-62; `2026-04-22-005` §Architectural Patterns]*
4. **Autoresearch IS the engine — full implementation in v1.** `marketing_audit` registered as `LaneSpec` in `autoresearch/lane_registry.LANES`; `audits/lineage.jsonl` shape-compatible with `autoresearch/archive/lineage.jsonl`; MA-1..MA-8 rubric SHA256-frozen via `lane_registry.compute_manifest`; evolve loop runs from day 1 (variant rotation, mutation, fitness scoring); pre-promotion smoke gate fail-closed; promotion judges enabled. *[source: `2026-04-24-005` Units 15, 17, 18; JR override on prior "v3-defer" stance]*
5. **Tool access via autoresearch's existing multi-provider CLI dispatch:** claude code CLI / codex CLI / opencode CLI, with retry on transient errors. **No `claude-agent-sdk`, ever.** *[source: JR direction; verified `pyproject.toml` confirms SDK not installed]*
6. **Cost observability without a cap in v1:** `cost_actual.json` written per stage; first 5 real audits calibrate empirical baseline. High costs at the beginning are explicitly accepted; caps deferred until post-audit-5 once realized data informs where to set them. *[source: JR direction 2026-05-06 — caps dropped after second-pass review of `docs/plans/2026-05-06-001-autoresearch-evolution-fixes-phase-a-b.md` context]*
7. **Storage:** local `clients/<slug>/audit/`, git-committed per stage; published deliverables at `reports.gofreddy.ai/<uuid4>/` via Cloudflare Worker; `X-Robots-Tag: noindex`. *[source: `2026-04-20-002` R6, R11; §Architecture diagram + Worker spec]*

### Non-goals (in v1)

1. **Inner-loop critique iteration** (3-pass critic from original R5) — single-pass agents only. *[source: `2026-04-23-002` §v1 line 76]*
2. **arq queue + auto-fire on payment webhook** — manual JR-fire policy; only free scan auto-runs. *[source: `2026-04-23-002` D1; `2026-04-20-002` R14]*
3. **5 of 9 attach-\* commands:** `attach-esp`, `attach-survey`, `attach-assets`, `attach-demo`, `attach-crm` — deferred. v1 ships `attach-gsc`, `attach-ads`, `attach-winloss`, `attach-budget`. *[source: `2026-04-24-005` §Scope Boundaries]*
4. **Web UI / dashboard** — CLI-only. *[source: `2026-04-23-002` D1]*
5. **R29 subscription-window SLA** — fusion-only construct, removed. *[source: `2026-04-30-001` O6]*
6. **Imposed per-audit cost cap** — instrumented via `cost_actual.json` but NOT enforced in v1; deferred to post-audit-5 calibration. *[source: JR direction 2026-05-06]*

### Operating principles

- **Owned-provider-first.** Stage 1a deterministic pre-pass uses ~17 wired Python providers (DataForSEO, GSC, PageSpeed, Cloro, Foreplay, Adyntel, 12 monitoring adapters). Free public APIs (~75) are agent-driven via WebFetch instructions in agent prompts + a thin `cli/scripts/fetch_api.sh` retry helper (Phase 1 work; does not currently exist on disk). *[source: `2026-04-20-002` §Stage 1a + provider inventory; verified repo scan]*
- **Three permanent gates:** intake review, payment gate, mandatory ship gate. No audit publishes without JR sign-off. *[source: `2026-04-20-002` R8; `2026-04-23-002` D2]*
- **Provider truth wins over plan claim.** When prior plans assumed infra that doesn't exist (`claude-agent-sdk`, `cli/scripts/fetch_api.sh`, `phase-1-foundation-snapshot` 127 tests on main), this plan treats them as Phase 1 work to create or surface, not as assumed.
- **Each phase calibrates the next.** First 5 real audits replace estimated cost / time / quality figures with empirical ones; second 5 inform the evolve loop's first variant rotation.

### What "first-runnable" means concretely

`freddy audit run https://prospect.com` completes end-to-end → produces `report.md` + `report.json` + `findings.md` (rough quality acceptable) → JR edits and publishes via `freddy audit publish`. Client #1 may need heavy editing; that editing surfaces what to harden. By client #3 the editing should be light. Each audit feeds the autoresearch evolve loop with labeled data; thin labels at first, accepted explicitly.

---

## Section 2 — Deliverable Shape

### 2.1 Customer-facing artifacts

| Product | Where it lives | Form | Cost target |
|---|---|---|---|
| **Free AI Visibility Scan** | `reports.gofreddy.ai/scan/<slug>/scan.html` + markdown email to prospect | 1-page teaser highlighting 2–3 specific AI-search findings | ~$1–2 *[source: `2026-04-20-002` R16]* |
| **Paid audit** | `reports.gofreddy.ai/<ulid>/` (Cloudflare Worker, `X-Robots-Tag: noindex`) | Hosted HTML + downloadable PDF | No cap in v1; observability via `cost_actual.json` (Section 1 Goal 6) |
| **Source artifacts** | `clients/<slug>/audit/synthesis/{findings.md, surprises.md, report.md, report.json, gap_report.md}` + `deliverable/{report.html, report.pdf, assets/}` | Git-committed per stage | n/a |

### 2.2 Information architecture — 9 deliverable sections (CAD-2 lock = "Both")

Lifted from current `src/audit/agent_models.py:44-51` (already on main, correct shape):

| # | Section ID | Display name | What it covers |
|---|---|---|---|
| 1 | `seo` | SEO | Findability via traditional search |
| 2 | `geo` | **AI Visibility (GEO)** *[rename]* | Findability via AI answer engines |
| 3 | `competitive` | Competitive | Position vs named competitors |
| 4 | `monitoring` | Monitoring | Mention velocity, sentiment, brand-health observability |
| 5 | `conversion` | Conversion | Visitor → lead → customer mechanics |
| 6 | `distribution` | Distribution | Where prospect gets discovered / evaluated |
| 7 | `lifecycle` | Lifecycle | Post-acquisition retention, churn, CX |
| 8 | `martech_attribution` | **MarTech, Measurement & Compliance** *[rename]* | Stack + attribution + compliance |
| 9 | `brand_narrative` | Brand & Narrative | Positioning, voice, thought leadership, trust |

Plus Hero TL;DR opener: 0-100 health score + 9-axis radar + ≤120-word Opus rationale. *[source: `2026-04-20-002:1326`; `agent_models.py` `compute_health_score`]*

### 2.3 Tag taxonomy — 11 marketing areas

The catalog organizes the 149 lenses into 11 marketing areas. The deliverable IA stays at 9 sections; the 11-area structure rides as a **`marketing_area`** tag on SubSignal — content-authority traceability without changing report shape.

| # | Marketing area | Lens count | Primary agent owner |
|---|---|---|---|
| 1 | Discoverability & Organic Search | 28 | Findability |
| 2 | Content Assets & Authority Plays | 6 | Narrative |
| 3 | Paid Media | 6 | Acquisition |
| 4 | Earned Media & PR | 6 | Narrative |
| 5 | Distribution, Community & Listings | 13 | Acquisition |
| 6 | Conversion Architecture | 16 | Experience |
| 7 | Activation & Product-Led | 12 | Experience |
| 8 | Lifecycle, Retention & CX | 13 | Experience |
| 9 | Brand & Authority | 16 | Narrative |
| 10 | Sales / GTM / Enablement | 14 | Acquisition |
| 11 | MarTech, Measurement & Compliance | 28 | Findability + Experience (split per CAD-3) |

*[source: `2026-04-22-005` §Marketing-Areas View lines 146-394]*

### 2.4 Phase-0 meta-frames — hybrid execution (CAD-4 lock = Hybrid)

The 9 Phase-0 meta-frames *[verbatim from `2026-04-22-005:153-161`]*:

1. Traffic-mix ratio (direct/organic/paid/social/referral/email)
2. Channel-model fit (Balfour Four Fits)
3. Traffic trajectory 12-month delta
4. Growth loops vs funnel inventory (Reforge)
5. Marketing-maturity tier (Kotler/Forrester 6-axis)
6. Share-of-voice vs named competitors
7. Geo / country mix (ICP-channel mismatch detector)
8. North-star metric / vanity-metric tell
9. Engagement tier proxies (bounce / session duration / pages-per-session)

**Hybrid execution:**
- **Woven into agent prompts as background:** each Stage-2 agent receives the relevant Phase-0 frames pre-computed in Stage 1c brief as structured input + ~150-token reading guide tailored to that agent. *[source: `2026-04-23-002:62`]*
- **Cross-cutting deliverable pass:** Stage 3 emits 1–3 dedicated **Phase-0 ParentFindings** carrying `phase0_frame` tag. These open the deliverable as a "State of the Business" framing before tactical sections. *[source: `2026-04-30-001` §CAD-4 Hybrid]*

### 2.5 Schema additions (NOT a redo)

`src/audit/agent_models.py` is correctly shaped — 9-value `ReportSection` Literal, SubSignal/ParentFinding/AgentOutput/HealthScore/computed-rollup-validators all sound. The framework plan's "redo from scratch" was a misread. Concrete v1 diff is **additive only** (~6 LOC):

```python
# SubSignal additions
marketing_area: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] = Field(
    description="Catalog 005 area assignment — content-authority tag"
)
phase0_frame: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9] | None = Field(
    default=None,
    description="Set on SubSignals derived from Phase-0 meta-frames"
)

# AgentOutput addition (per-agent synthesis simplification — Section 3.5)
parent_findings: list[ParentFinding] = Field(
    default_factory=list,
    description="Agent-rolled-up ParentFindings — Stage 3 merges across agents instead of synthesizing from scratch"
)
```

ParentFinding aggregates `marketing_area` via most-common-area win in Stage 3. No deletions, no `EffortBand`/`ProposalTier` rewrites — those remain load-bearing. *[source: verified read of `src/audit/agent_models.py` lines 1-291]*

### 2.6 What a finished audit reads like

Top-to-bottom render order:

1. **Hero TL;DR** — health score + 9-axis radar + Opus rationale ≤120 words
2. **State of the Business** (Phase-0 ParentFindings, 1–3) — strategic framing opener
3. **9 tactical sections** — each ~2–4 ParentFindings, target ~25–32 total *[source: `2026-04-22-005:44`]*. Each ParentFinding has: strategic headline (not list-of-issues), 2–3 sentence evidence summary, ≥50-word strategic recommendation (capability-registry-tier-mapped), SubSignals rendered as evidence rows underneath
4. **Surprises** — agent-flagged unexpected positives/negatives
5. **Gap report** — rubrics that gap_flagged (insufficient signal); surfaced to JR at ship gate *[source: `2026-04-20-002:680`]*
6. **Proposal** — capability-registry-anchored tiers (`fix_it` / `build_it` / `run_it`) *[source: `2026-04-20-002` U6]*
7. **Sources** — deduplicated evidence URLs

JR reviews at the mandatory ship gate, edits, runs `freddy audit publish` → deliverable goes live.
## Section 3 — Pipeline Architecture

### 3.1 Autoresearch lane wiring

The audit pipeline registers as the **6th lane (5th workflow lane)** in `autoresearch/lane_registry.LANES`, peer to `geo` / `competitive` / `monitoring` / `storyboard`. Single `LaneSpec` entry; **2 of 5 callables wired in v1** (`custom_score` + `custom_validate`); `custom_promote` stays `None` until post-audit-3 holdout fixtures land; `custom_mutate` uses default meta-agent. *[source: `autoresearch/lane_registry.py:53-164`; `2026-04-24-005` Unit 17]*

```python
"marketing_audit": LaneSpec(
    name="marketing_audit",
    is_workflow_lane=True,
    rubric_ids=("MA-1","MA-2","MA-3","MA-4","MA-5","MA-6","MA-7","MA-8"),
    path_prefixes=(
        "marketing_audit-findings.md",
        "programs/marketing_audit-session.md",
        "programs/marketing_audit/prompts/",
        "templates/marketing_audit",
        "workflows/marketing_audit.py",
        "workflows/session_eval_marketing_audit.py",
    ),
    session_md_filename="marketing_audit-session.md",
    deliverables=("findings.md", "report.md", "report.json", "report.html", "report.pdf"),
    intermediate_artifacts=("stage2_subsignals/L*_*.json", "stage2_parent_findings/*.json"),
    structural_doc_facts=(...),       # Section 2 IA + 3-tier proposal schema
    structural_gate_functions=(...),  # validators in src/evaluation/structural.py
    custom_score=src.audit.score.marketing_audit_score,
    custom_validate=src.audit.validate.marketing_audit_validate,
    custom_promote=None,              # wired post-audit-3 when holdout fixtures exist
    custom_objective_score_from_entry=None,  # default reader works — custom_score pre-folds engagement bonus into metrics.domains.marketing_audit.score
)
```

**Two execution wrappers, one set of stages** *[source: `2026-04-24-005:173-198`]*:

| Wrapper | Entry | Adds | Stages run |
|---|---|---|---|
| **Live (paid customer)** | `freddy audit run` | Commercial flow + 3 gates + payment ledger + R2 publish + T+60d feedback | All (0–5) |
| **Evolve (variant-producer)** | `autoresearch evolve --lane marketing_audit` | Variant rotation + fitness scoring (smoke gate post-audit-3) | All (0–5), against fixtures |

Both invoke the same `run_audit(audit_id, archive_dir)` async function. Live wrapper calls `run_audit_sync()` directly in-process. Evolve wrapper subprocesses through `evaluate_variant.py:698` Popen. *[source: `2026-04-24-005:892`]*

**Manifest freeze in v1 = whole-file SHA256.** `marketing_audit_manifest.json` lists rubric / judge / stage prompts; `custom_validate` re-verifies on every variant scoring; drift fails the variant. The `[STABLE]` / `[EVOLVABLE]` section-marker pattern is **deferred to v2**. *[source: `2026-04-30-001` K-2; framework-plan deferral]*

The default substrate `_check_critique_manifest` (`evaluate_variant.py:448`) only covers autoresearch's critique infrastructure — lane-specific stage / judge / rubric prompts need `custom_validate` for drift protection during evolve runs.

**Lineage shape** in `audits/lineage.jsonl` is shape-compatible with `autoresearch/archive/lineage.jsonl` (join key = `variant_id` ↔ `audit_id`). Engagement signal at T+60d feeds back as a row update — consumed by `marketing_audit_objective_score`. *[source: `2026-04-23-002:130-136`]*

### 3.2 6-stage overview

| Stage | Inputs | Outputs | LLM | Parallelism | Cost target | Wall-clock |
|---|---|---|---|---|---|---|
| **0 — Intake** | Form / webhook | `intake/form.json`, `state.json`, `config.json` | None | n/a | $0 | <5s |
| **1a — Cache warmup** | URL + intake | `cache/<tool>_<hash>.json` × ~17 | None | `asyncio.Semaphore(12)` over Python | $2–4 | 60–120s |
| **1b — Bundle activation + free-API discovery** | Cache + intake | `signals.md`, `gaps.jsonl`, `bundles_active.json` | Sonnet | 1 multi-turn session | $2–6 | 6–12min |
| **1c — Brief synthesis (incl. phase0_meta)** | signals.md + cache | `brief.md`, `brief.json`, `phase0_meta.json`, `agent_reading_guides.json` | Opus | 1 call | $0.50–1 | <60s |
| **2 — 4-agent fan-out (with per-agent synthesis)** | brief + cache + per-agent rubric YAML + reading guide | `agents/<a>/agent_output.json` × 4 (incl. SubSignals AND ParentFindings) | Multi-provider CLI | `asyncio.gather` (4 agents, no Semaphore) | $30–80 × 4 = $120–320 | 10–20min |
| **3 — Cross-cutting synthesis & narrative** | 4× AgentOutput | `synthesis/{findings.md, report.md, report.json, surprises.md, gap_report.md}` | Opus | 1 + 1 sequential | $10–15 | 3–6min |
| **4 — Proposal** | report.json + capability_registry.yaml | `proposal/proposal.md`, `proposal.json` | Opus | 1 call | $5–10 | 1–3min |
| **5 — Deliverable render** | All above | `deliverable/{report.html, report.pdf, assets/}` | None | n/a | $0 | <30s |

**Total realistic cost**: $135–375 per audit (no cap enforced in v1; observability via `cost_actual.json`).

### 3.3 Stage 0 — Intake

**Two entry paths** *[source: `2026-04-20-002` U1, U8]*:

**Free AI Visibility Scan** (auto-fire on form submission):
```
form submit → Cloudflare Worker → POST /v1/scan/request → Supabase row
            → Fly API spawns scan worker → Stage 1a subset (cheap providers only)
            → 1 Opus call (prompts/scan_synthesis.md)
            → email markdown to prospect + upload scan.html to R2 at reports.gofreddy.ai/scan/<slug>/
```
Cost ~$1–2. Slack ping to JR with prospect details + scan URL.

**Paid audit** (manual JR-fire):
```
form submit (after sales call) → Slack notification to JR
                               → JR runs: freddy audit init <client-slug> --form-data ...
                               → workspace created at clients/<slug>/audit/{intake,cache,prediscovery,agents,synthesis,proposal,deliverable}/
                               → state.json initialized with stage=0, paid=False
```
JR runs subsequent stages manually; payment gate (§3.11) blocks Stage 2 until Stripe webhook flips `state.paid=True`.

### 3.4 Stage 1 — Pre-discovery & cache-warmup

**Stage 1a — Cache warmup (parallel Python, no LLM).** *[source: `2026-04-20-002:478`]*

`stages.py:stage_1_warmup` invokes provider methods directly via `asyncio.gather` + `Semaphore(12)` to populate per-audit cache. Always-on set:
- `DataForSeoProvider.{on_page, backlinks, historical_rank, serp_features, business_data_gbp}`
- `CloroClient.ai_visibility`
- 12 monitoring adapters
- `fingerprint_martech_stack()` (Wappalyzer-next + martech_rules.yaml — Phase 1 work)
- Playwright `RenderedFetcher` homepage fetch (Phase 1 work)

Conditional providers gated by enrichment attach (e.g. GSC only if `state.enrichments.gsc.attached==True`). Each call routes through `tools/cache.py:cache_or_call(tool_name, args, fn)`; cache files at `clients/<slug>/audit/cache/<tool>_<sha256(args)[:12]>.json` with 24h TTL.

**Stage 1b — Bundle activation + free-API discovery (Sonnet, multi-turn).** *[source: `2026-04-20-002:479`; tool-access route adapted for no-SDK]*

Sonnet session via **multi-provider CLI dispatch** (claude code / codex / opencode — same harness as autoresearch). NOT MCP+SDK as the original plan proposed — the agent reads cache via filesystem `Read` tool and reaches free public APIs via `cli/scripts/fetch_api.sh` invoked through `Bash`. *[source: JR direction; supersedes `2026-04-20-002:479` SDK+MCP design]*

System prompt (`programs/marketing_audit/prompts/stage_1b_predischarge.md`) carries:
- Warm-cache manifest (tool_name + path)
- Firmographic signals from intake form
- **URL-pattern blocks** for ~75 free public APIs (full list in Section 4)
- Rubric-oriented investigation guidance + bundle-activation detection rules (vertical / geo / segment)
- Explicit `gap_flag` instruction
- `fetch_with_retry` usage pattern

Output: `signals.md` (prose, organized by rubric headings) + `gaps.jsonl` (one row per gap_flag) + `bundles_active.json` (vertical / geo / segment activations).

**Stage 1c — Brief synthesis (Opus, 1 call).** *[source: `2026-04-20-002:480`; CAD-4 hybrid]*

ONE Opus call (`stage_1c_brief_synthesis.md`) reads `signals.md` + `gaps.jsonl` + cache manifest + form data → emits:
- `brief.md` (prose for Stage-2 agent consumption)
- `brief.json` (structured `PrediscoveryBrief` Pydantic)
- **`phase0_meta.json`** — structured Phase-0 measurements (per Section 2.4 hybrid)
- `agent_reading_guides.json` — ~150-token per-agent guidance pulling relevant Phase-0 frames

### 3.5 Stage 2 — 4-agent fan-out with per-agent synthesis

**`asyncio.gather` over 4 agents, no Semaphore** (4 is the cap). *[source: `2026-04-23-002:71-72`]*

| Agent | Lens count | Rubric YAML | Primary providers | Reading guide focus |
|---|---|---|---|---|
| **Findability** | ~35 | `data/rubrics_findability.yaml` | DataForSEO + Cloro + GSC + Playwright | traffic_mix.organic_share, trajectory, geo_mix |
| **Narrative** | ~26 | `data/rubrics_narrative.yaml` | DataForSEO + monitoring (PR/podcasts) | share_of_voice, maturity_tier, north_star_tell |
| **Acquisition** | ~32 | `data/rubrics_acquisition.yaml` | Foreplay + Adyntel + DataForSEO + monitoring | channel_model_fit, growth_loops_inventory |
| **Experience** | ~47 | `data/rubrics_experience.yaml` | Playwright + Wappalyzer + WebFetch | engagement_proxies, north_star_tell |

Each agent's run via multi-provider CLI dispatch (default: Opus via claude code, configurable per `autoresearch/agent_calls.py` retry semantics):

1. Reads cache directly (`Read clients/<slug>/audit/cache/<tool>_<hash>.json`)
2. WebFetches free public APIs via `Bash cli/scripts/fetch_api.sh <url>`
3. Multi-turns through assigned lenses (~26–47), accumulating SubSignals per `agent_models.SubSignal`
4. Emits per-lens `stage2_subsignals/L<lens_id>_<agent>.json` files (intermediate_artifacts)
5. **Per-agent synthesis (NEW vs original design):** before returning, the agent groups its SubSignals by `report_section` and rolls them into `ParentFinding` objects within its own session. Rubric YAML carries a synthesis-instruction footer: *"After all lens firings complete, group SubSignals by `report_section` and emit ParentFindings with strategic headlines, ≥50-word recommendations, and proposal-tier hints."* *[simplification per pattern alignment with peer lanes — `competitive` / `geo` / `monitoring` synthesize within their session]*
6. Writes `agents/<agent>/agent_output.json` with full `AgentOutput` containing `sub_signals[]` AND `parent_findings[]` AND `agent_summary` AND `rubric_coverage`

`rubric_coverage` is required and strict — every rubric ID from agent's YAML must appear keyed `"covered"` or `"gap_flagged"`. Missing keys raise at Stage 3. *[source: `agent_models.AgentOutput`]*

**Crash isolation:** `asyncio.gather(..., return_exceptions=True)` captures per-agent exceptions; one agent crash doesn't kill siblings. Crashed agent's gap is flagged in `gap_report.md`. *[source: `2026-04-23-002:74`]*

### 3.6 Stage 3 — Cross-cutting synthesis & narrative

`stages.py:stage_3_synthesis` does four things in **2 Opus calls** (down from 10 in the original Section 3 draft):

1. **Read 4× AgentOutput.** Collect all SubSignals + per-agent ParentFindings. Group ParentFindings by `report_section` (most agents will already cluster correctly).
2. **Opus call #1 — Cross-cutting Phase-0 merge & dedup.** Reads `phase0_meta.json` + ALL per-agent ParentFindings → emits 1–3 dedicated **Phase-0 ParentFindings** (`phase0_frame` tag set) for the State of the Business opener; also dedupes any cross-agent ParentFinding overlap (e.g. Findability + Experience both fire Consent Mode v2 — merge into one).
3. **Python-deterministic HealthScore** via `agent_models.compute_health_score(parent_findings)` → emits `HealthScore` object.
4. **Opus call #2 — Narrative writer.** Reads merged ParentFindings + HealthScore → writes `report.md` (executive narrative summary) + `findings.md` (structured 9-section primary deliverable, judge input per `2026-04-24-005:1308`) + `surprises.md` (agent-flagged unexpected signals) + the ≤120-word HealthScore rationale.

**Outputs** (same as original draft):
- `findings.md` — primary deliverable (judge input)
- `report.md` — narrative summary
- `report.json` — machine-readable; HealthScore + ParentFindings[] + sources[]
- `surprises.md` — unexpected signals
- `gap_report.md` — every `gap_flagged` rubric across all 4 agents

**Why 2 calls instead of 9:** competitive / geo / monitoring lanes synthesize within the agent session; per-agent synthesis (§3.5) preserves per-cluster reasoning depth. Stage 3's job becomes merge + cross-cutting + narrative, not section-by-section synthesis from raw SubSignals.

### 3.7 Stage 4 — Proposal

ONE Opus call. Reads `report.json` + `data/capability_registry.yaml` (~48 capability entries) → emits 3-tier proposal:

- **Fix-it** — discrete one-off fixes mapped to `proposal_tier_mapping="fix_it"` ParentFindings
- **Build-it** — productized build engagement (typical $15K+)
- **Run-it** — ongoing retainer

Per tier: Engagement / Investment / Best-for / What-this-tier-delivers / What-we-won't-do-at-this-tier. Each tier references ≥1 ParentFinding ID. *[source: `2026-04-20-002` U6 + structural §1310]*

Outputs: `proposal/proposal.md` (3 H2 tier headers in fixed order) + `proposal.json`.

### 3.8 Stage 5 — Deliverable render

**No LLM.** Jinja2 + WeasyPrint:
- `templates/audit_report.html.j2` — single template with embedded partials
- Renders `report.json` + `proposal.json` + `phase0_meta.json` + cache screenshots
- Produces `deliverable/{report.html, report.pdf, assets/}`
- ULID slug generated; written to `state.json`

**Publish step** (separate command, after JR ship-gate review):
- `freddy audit publish <slug>` → uploads `deliverable/` to R2
- Cloudflare Worker serves at `reports.gofreddy.ai/<ulid>/` with `X-Robots-Tag: noindex` + `Referrer-Policy: no-referrer`

### 3.9 Cost observability (no cap in v1)

After each stage, `cost_ledger.write(stage, cost_usd)` updates `clients/<slug>/audit/cost_actual.json`:

```json
{
  "stage_1a_warmup": 3.42,
  "stage_1b_predischarge": 4.10,
  "stage_1c_brief": 0.85,
  "stage_2_findability": 47.20,
  "stage_2_narrative": 31.50,
  "stage_2_acquisition": 38.10,
  "stage_2_experience": 62.30,
  "stage_3_synthesis": 12.40,
  "stage_4_proposal": 7.05,
  "total_so_far": 206.92
}
```

No breaker. No cost-driven aborts. **Slack notification** at total $200 + $400 thresholds (informational, audit continues). After first 5 audits ship, JR reviews realized cost distribution and decides where to set caps in v2 (informed by the autoresearch fix plan's findings on uncapped runaway). *[source: JR direction 2026-05-06]*

### 3.10 Error semantics

| Failure mode | Behavior |
|---|---|
| Per-agent Stage-2 crash | `asyncio.gather(..., return_exceptions=True)` captures; siblings continue; gap_report flags |
| Malformed SubSignal | skip-not-raise; logged; counted in `agent.metadata.partial=True` |
| Stage-3 Opus call crash | Retry per `autoresearch/agent_retry.py` (exponential backoff, max 3); if final retry fails, write partial state and abort with non-zero exit |
| Stripe webhook missing | Stage 2 raises `PaymentRequired` until `state.paid=True` |
| Cache TTL expired | Tool re-fires; cost re-incurred (correctness > cost) |
| Multi-provider CLI transient error | Retry per `autoresearch/agent_retry.py` (exponential backoff, max 3) |
| Catastrophic failure | Partial state preserved at `state.json`; `freddy audit resume <slug>` reads state, skips completed stages |

### 3.11 Three permanent gates

*[source: `2026-04-20-002` R8; `2026-04-23-002` D2]*

| Gate | When | Action | Block until |
|---|---|---|---|
| **Intake review** | After Stage 1c | JR reads `brief.md` + `gaps.jsonl` | JR runs `freddy audit confirm-brief <slug>` |
| **Payment gate** | Before Stage 2 | Stripe webhook updates `state.paid=True` | `state.paid==True` |
| **Ship gate** | After Stage 5 (before publish) | JR reviews `deliverable/report.html` locally; edits if needed | JR runs `freddy audit publish <slug>` |

### 3.12 Wall-clock total

Best case (cache hits, no retries): ~22 min. Realistic: ~30–40 min. Worst case (retries + cache misses + slow agents): ~55–70 min. Per-audit human time: ~10–30 min (intake review + ship-gate edits). Costs are observed, not capped — high early-audit costs are explicitly accepted to gather empirical data before setting caps in v2.
## Section 4 — Provider Infrastructure

### 4.1 Three-tier hybrid architecture

The audit pipeline reads from three structurally distinct provider tiers, each with its own access pattern, cost shape, and ownership model. Tier choice is determined by the data type, not the agent. *[source: CAD-1 lock per JR direction; refines `2026-04-20-002` §"agentic data fetching philosophy"]*

| Tier | What it covers | Access pattern | Why this tier |
|---|---|---|---|
| **1 — Owned paid/rate-limited** | DataForSEO, Cloro, Foreplay, Adyntel, GSC, 11 monitoring adapters | Stage 1a Python `cache-warmup`, agents read via filesystem | Hash-dedup cache (24h TTL), per-call cost, doubles as eval-harness fixture, rate-limit-aware |
| **2 — Free public APIs (~75)** | GitHub, Wikipedia, SEC EDGAR, HuggingFace, Reddit, Product Hunt, crt.sh, GDELT, etc. | Agent-driven: `Bash cli/scripts/fetch_api.sh <url>` + `WebFetch` per URL-pattern instructions in agent prompts | No brittle Python wrapper; agent decides what to fetch based on prospect context; auth env-var injection in shell helper |
| **3 — Local detection infrastructure** | Wappalyzer-next + martech_rules.yaml; Playwright `RenderedFetcher` | Stage 1a Python helpers, no network call | No-network signals (martech fingerprint, rendered DOM); seeds cache for Stage 2 reads |

**Live-vs-indexed pattern.** Tier 1 indexed providers (Xpoz pre-indexed Twitter/Instagram/Reddit; Adyntel maintained Google Ads Transparency index) are used when **historical depth or comprehensive coverage matters** — share-of-voice over 12 months, exhaustive ad-corpus analysis, named-person mention graphs. Live fallbacks (Apify Twitter actors, SerpAPI Google Ads Transparency) are used when **a one-off lookup is sufficient** and live data is enough — quick competitor sanity check, single-page scrape, latest mentions only. Agent decides per query based on what the lens needs. Live fallbacks are 20×–43× cheaper per call but cannot reproduce the index's depth — quality always wins when historical/comprehensive coverage is required. *[source: JR direction 2026-05-06; Agent C live pricing comparison]*

### 4.2 Tier 1 — Owned paid/rate-limited providers (17 wired)

Verified by repo scan. *[source: `src/seo/providers/`, `src/geo/providers/`, `src/competitive/providers/`, `src/monitoring/adapters/`; Agent A inventory 2026-05-06]*

| # | Provider class | Path | Role | Cost per call |
|---|---|---|---|---|
| 1 | `DataForSeoProvider` | `src/seo/providers/dataforseo.py` | On-page audit, keywords, backlinks, SERP, Labs (5 methods) | $0.0006–0.05 |
| 2 | `GSCClient` | `src/seo/providers/gsc.py` | Search Console clicks/impr/CTR (conditional on R18 attach) | Free, gated |
| 3 | `PageSpeed` | `src/seo/providers/pagespeed.py` | Core Web Vitals | Free (25K/day) |
| 4 | `CloroClient` | `src/geo/providers/cloro.py` | AI-citation tracking (ChatGPT/Perplexity/Gemini/Claude/Grok/Copilot) | $0.0012–0.0028/query |
| 5 | `ForeplayProvider` | `src/competitive/providers/foreplay.py` | Meta + TikTok + LinkedIn paid creative corpus (indexed) | $49–99/mo subscription |
| 6 | `AdyntelProvider` | `src/competitive/providers/adyntel.py` | Google Ads transparency (indexed, paginated) | $0.006–0.009/page |
| 7 | `XpozAdapter` | `src/monitoring/adapters/xpoz.py` (1231 LOC) | Twitter + Instagram + Reddit (indexed pre-search) | Per-call $ |
| 8 | `ReviewsAdapter` | `src/monitoring/adapters/reviews.py` (320 LOC) | Trustpilot + AppStore + PlayStore (Apify-backed) | Per-call $ |
| 9 | `IcContentAdapter` | `src/monitoring/adapters/ic_content.py` (283 LOC) | Influencers.club TikTok+YouTube discovery | Per-call $ |
| 10 | `TiktokAdapter` | `src/monitoring/adapters/tiktok.py` (222 LOC) | TikTok via Apify (interim — Xpoz handles in production) | Per-call $ |
| 11 | `NewsAdapter` | `src/monitoring/adapters/news.py` (195 LOC) | NewsData.io REST | Per-call $ |
| 12 | `BlueskyAdapter` | `src/monitoring/adapters/bluesky.py` (197 LOC) | Bluesky AT Protocol public-search | Free + scrape |
| 13 | `FacebookAdapter` | `src/monitoring/adapters/facebook.py` (197 LOC) | Facebook mention scraper via Apify | Per-call $ |
| 14 | `PodcastsAdapter` | `src/monitoring/adapters/podcasts.py` (168 LOC) | Pod Engine + Podchaser GraphQL | Per-call $ |
| 15 | `LinkedinAdapter` | `src/monitoring/adapters/linkedin.py` (158 LOC) | LinkedIn mention scraper via Apify | Per-call $ |
| 16 | `GoogleTrendsAdapter` | `src/monitoring/adapters/google_trends.py` (153 LOC) | Google Trends scraper via Apify | Free |
| 17 | `AiSearchAdapter` | `src/monitoring/adapters/ai_search.py` (121 LOC) | AI-search visibility (wraps Cloro) | Per-call $ |

Plus `_common.py` helper (51 LOC) for shared Apify/sentiment scaffolding.

**All 17 are wired and functional today.** Stage 1a's `stage_1_warmup(state)` invokes provider methods directly via `asyncio.gather` + `Semaphore(12)`. Each call routes through `tools/cache.py:cache_or_call(tool_name, args, fn)` (Phase 1 build — does not exist yet), writing to `clients/<slug>/audit/cache/<tool>_<sha256(args)[:12]>.json` with 24h TTL.

**Live-fallback wiring.** Apify is already a wired substrate — `src/monitoring/adapters/{reviews, tiktok, facebook, linkedin, google_trends}.py` use it under the hood (via `_common.py` helpers). The **Apify-as-X-fallback** pattern routes within `XpozAdapter` when a query is one-off + live-sufficient: `xpoz.search(...)` falls through to `apify.run_actor("twitter-scraper", ...)` if `query.live_only=True`. **SerpAPI Google Ads Transparency** is net-new wiring — proposed Phase 1.5 wrapper (~1 day) used by `AdyntelProvider` as fallback for one-off advertiser lookups. Index providers (Xpoz / Adyntel) remain primary; live providers serve cheap one-offs. *[source: JR direction 2026-05-06]*

**Cross-cutting modules in repo (production-wired but not part of marketing_audit's primary fetcher tier).** Agent A's full repo scan surfaced ~25 additional production-wired data-fetching modules. Most are scoped to other lanes (geo article generation, video creator search, publishing) and don't feed marketing_audit lenses. Three are reusable for marketing_audit if a future lens demands it: `src/competitive/vision.py` (Gemini vision enrichment for ad creatives — could supplement Foreplay/Adyntel ad analysis), `src/fetcher/{instagram, tiktok, youtube}.py` (Apify wrappers — could supplement monitoring adapters for creator-side coverage), and `src/audit/preflight/checks/{wellknown, dns}.py` (functional but unwired — see §4.8 wiring debt). *[source: Agent A inventory 2026-05-06]*

### 4.3 Tier 2 — Free public APIs (~75 via WebFetch + `fetch_api.sh`)

Reached agent-side via shell helper or direct WebFetch. URL patterns + auth env vars + polite-pace + pagination notes are embedded in agent prompts (`programs/marketing_audit/prompts/stage_1b_predischarge.md` + the 4 Stage-2 agent prompts). *[source: `2026-04-20-002` §Free public APIs lines 212-260]*

Concrete inventory (subset, illustrative — full list lives in agent prompts):

| API | URL pattern | Role | Auth env | Rate / cost |
|---|---|---|---|---|
| GitHub REST + GraphQL | `api.github.com/orgs/{org}` | Repo enum, stars, contributors, releases, OSS footprint | `GITHUB_TOKEN` | 5K req/hr |
| Wikipedia REST + MediaWiki + Lift Wing | `en.wikipedia.org/api/rest_v1/page/summary/{slug}` + `api.wikimedia.org/service/lw/...` | Brand page existence + article quality scoring | optional `WIKIMEDIA_API_KEY` | Free |
| Product Hunt GraphQL | `api.producthunt.com/v2/api/graphql` | Launch history, upvotes, badges | OAuth client-credentials | ~6250 complexity pts/15min |
| crt.sh + Certspotter | `crt.sh/?q=%25.{domain}&output=json` | Subdomain enumeration via TLS cert logs | None | ~1 req/sec |
| Mozilla HTTP Observatory v2 | `observatory-api.mdn.mozilla.net/api/v2/scan` | Security headers grade (replaces SecurityHeaders.com) | None | 1 scan/host/min |
| GDELT DOC 2.0 | `api.gdeltproject.org/api/v2/doc/doc` | Global news-graph themes + tone | None | Free |
| Reddit OAuth | `reddit.com/api/v1/access_token` → `reddit.com/r/<sub>/about.json` | Subreddit subs + active users + IAmA history | `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` | Free w/ OAuth |
| SEC EDGAR | `data.sec.gov/submissions/CIK<10-digit>.json` | Public-firmographic, filings | User-Agent w/ contact email | 10 req/sec |
| HuggingFace | `huggingface.co/api/{org}` | Model/dataset publication footprint | optional `HUGGINGFACE_TOKEN` | Free |
| Mailinator | `api.mailinator.com/v2/domains/public/inboxes/<inbox>` | Welcome-email capture (DKIM/SPF/DMARC parse) | optional `MAILINATOR_API_TOKEN` | Free public / $99/mo private |
| Wayback Machine CDX | `web.archive.org/cdx/search/cdx` | Historical homepage / pricing snapshots | None | Free |
| Firefox AMO + Atlassian Marketplace + Chrome Web Store | per-marketplace | Extension/app marketplace presence | None | Free |
| APIs.guru | `api.apis.guru/v2/list.json` | Public-API directory (dev-tool indexing) | None | Free |
| Discord Invite API | `discord.com/api/v8/invites/{code}` | Owned-community size signal | None | Free |
| Podchaser GraphQL | `api.podchaser.com/graphql` | Podcast guesting graph | OAuth | Free tier |
| HackerNews Firebase | `hacker-news.firebaseio.com/v0/...` | Show HN history, hackathon detection | None | Free |
| npm registry + PyPI JSON | `registry.npmjs.org/{pkg}` + `pypi.org/pypi/{pkg}/json` | Open-source package presence | None | Free |
| Bluesky | `public.api.bsky.app/xrpc/...` | Bluesky mentions / starter packs | None | Free |
| ATS endpoints | Greenhouse / Lever / Ashby / Workable | Employer-brand + careers signal | None | Free |
| mail-tester | `mail-tester.com/...` | Email deliverability score | None | Free w/ pacing |

**~75 total endpoints across these categories** — exact roster gets locked in the reconfirmation TODO (§4.10) before Phase 1.5 build starts.

### 4.4 Tier 3 — Local detection infrastructure (Phase 1 build)

Two pieces of infrastructure the prior plans assumed exist but **do not exist on disk today**. Required for ~40 lenses across Areas 1, 6, 9, 11.

**(1) MarTech fingerprinting** — `src/audit/tools/martech.py` + `data/martech_rules.yaml`
- Port `wappalyzer-next` *[source: `2026-04-20-002:274`]* — Python lib that detects ~2500 web technologies from headers + DOM + cookie patterns
- Author `martech_rules.yaml` — domain-specific overrides + 20+ category groupings (analytics, attribution, CMP, CRM, ESP, product analytics, session replay, A/B test, CDP, AI-chat, etc.)
- Used by Stage 1a `fingerprint_martech_stack()` → produces `cache/martech_<hash>.json`
- **~14 Area-11 MarTech lenses dead without this**
- Estimate: 3–5 days

**(2) Rendered-DOM fetching** — `src/audit/tools/rendered_fetcher.py`
- Playwright Chromium headless wrapper with shared browser context across audit
- Captures rendered DOM + screenshots + console errors + network log
- Required for: paywall UX detection, popup CRO, demo-flow probes, accessibility scans, AI-chat handoff timing, signup-flow CRO
- Used by Stage 1a homepage seed + Stage 2 Experience agent's per-page checks
- **~25 lenses across Areas 1, 6, 9 dead without this** (specifically anything requiring post-JS-execution DOM)
- Estimate: 3–4 days

**Tier-3 risk concentration.** Wappalyzer + Playwright together carry **~70+ lenses across Areas 6/7/8/10/11 + Phase-0 frames + most vertical/segment bundles**. If Phase 1.5 build slips on either piece, ~40+ lenses degrade simultaneously — single biggest implementation-risk concentration in the audit pipeline. Should be top-priority within Phase 1.5 with budgeted contingency time. *[source: Agent B coverage map 2026-05-06]*

### 4.5 Cache layer (Phase 1 build)

**`src/audit/tools/cache.py`** + **`src/audit/tools/cached_tool.py`** — both Phase 1 work; do not exist on disk today.

```python
# tools/cache.py
def cache_or_call(tool_name: str, args: dict, fn: Callable, ttl_hours: int = 24) -> Any:
    """Hash-dedup wrapper. Cache key = sha256(json.dumps(args, sort_keys=True))[:12].
    Hit: read JSON from clients/<slug>/audit/cache/<tool>_<key>.json.
    Miss: call fn(**args), write result, return."""

def write_cache(tool: str, args: dict, result: Any) -> Path: ...
def read_cache(tool: str, args: dict) -> Any | None: ...

# tools/cached_tool.py
def cached_tool(tool_name: str):
    """Decorator: wraps a provider method so all calls go through cache_or_call."""
```

Used by Stage 1a (Python-side) AND by Stage 2 agents (filesystem `Read` of cache files). Bit-identical writes — agent cache-hits look the same as Python cache-hits.

### 4.6 `cli/scripts/fetch_api.sh` (Phase 1 build)

~30-LOC shell helper. Curl wrapper with:
- Exponential backoff (3 retries, 2s/4s/8s)
- Auth header injection from env vars (`Authorization: Bearer $GITHUB_TOKEN`, etc.)
- Required `User-Agent: GoFreddy-Audit/1.0 (contact: jryszardn@gmail.com)`
- Pagination follow (Link header for GitHub, cursor for GraphQL)
- Polite-pace delays per host (configurable defaults)
- JSON output to stdout; errors to stderr with HTTP status

Invoked by Stage 1b Sonnet pre-discovery and Stage 2 agents through `Bash cli/scripts/fetch_api.sh <url>`. Single source of truth for retry / auth / pacing across all ~75 free public APIs. Estimate: 1 day. *[source: `2026-04-20-002:187, 380, 478, 490`; verified does not exist via repo scan]*

### 4.7 Provider gaps requiring NEW capability

Agent B's 192-entry coverage map surfaced 4 hard gaps where neither Tier-1 wired providers nor the ~75 free public APIs deliver the lens's required signal. *[source: Agent B coverage analysis 2026-05-06]*

| Gap | Lens(es) affected | What's missing | Resolution |
|---|---|---|---|
| **Phase-0 panel data** | W5 / #1 Traffic-mix ratio + W9 / #52 Engagement tier proxies | Cross-channel session attribution + off-prospect engagement panel (bounce / session duration / pages-per-session). Phase-0 frames feed every Stage-2 agent's reading guide — load-bearing | **NEW: SimilarWeb Digital Marketing API** (or Semrush .Trends as alternative). One subscription typically covers both. Estimate: 2–3 days wiring + ongoing subscription cost |
| **Brave Search visibility** | #157 | Brave Search index ranking — Claude-citation prerequisite. DataForSEO doesn't shard Brave; Cloro tracks AI citations not Brave SERPs | **NEW: Brave Search API** wrapper (free tier 2K queries/mo). Estimate: 1 day, fits in `fetch_api.sh` URL-pattern style |
| **Hyperscaler marketplaces (partial)** | #19 — SF AppExchange / HubSpot / Shopify / Slack / AWS / Azure / GCP | No clean public APIs available. Atlassian + Firefox AMO + Chrome Web Store DO have APIs (already in Tier 2) | **Accept SERP-only fallback** via DataForSEO `site:` queries. Depth limited to listing-presence + name match, not install counts. Documented as known limitation |

**Coverage after gap resolution:** ~99% of catalog (149 always-on + 9 Phase-0 + 25 vertical + 10 geo + 5 segment) — only the hyperscaler-marketplace install-count signal degraded.

### 4.8 Wiring debt — preflight infrastructure

`src/audit/preflight/runner.py` exists but is NOT called by any production code path (orphan per Agent A scan). Two real check modules (`dns.py`, `wellknown.py`) function correctly but inherit the orphan status. Six other check modules (`assets.py`, `badges.py`, `headers.py`, `schema.py`, `social.py`, `tooling.py`) ship as STUBS returning `{"implemented": False}`. *[source: Agent A inventory 2026-05-06]*

| Action | When | Estimate |
|---|---|---|
| Wire `preflight/runner.py` into Stage 1a (`stages.py:stage_1_warmup`) | Phase 1 | 1 day |
| Fill 6 stub checks (`assets`, `badges`, `headers`, `schema`, `social`, `tooling`) — port from fusion-plan Unit 7 (~1300 LOC + tests) | Phase 1.5 | 5–7 days |
| Promote `dns.py` from stub-fills to full SPF/DKIM/DMARC/BIMI/MTA-STS interpretation | Phase 1.5 | 1 day |

This is regression-fix work. The 6 stubs landed on main without their real implementations; the runner can't fan out useful work until either the stubs are filled or removed from `stage_1_warmup`'s expected check set.

### 4.9 Phase 1.5 — Provider build sub-phase (verified + expanded)

Sequenced AFTER Phase 1 (foundation + lane wiring) and BEFORE Phase 2 (stage pipeline). **~4–5 weeks total** — revised from the original 3–4 weeks after Agent A/B/C verified additional work items. *[source: synthesized from CAD-1 lock + Agent A/B/C findings 2026-05-06]*

| Work item | Estimate | Blocks | Source |
|---|---|---|---|
| **Wappalyzer-next port + `data/martech_rules.yaml`** | 3–5 days | ~14 Area-11 lenses + Tier-3 concentration | §4.4 + Agent B |
| **Playwright `RenderedFetcher`** | 3–4 days | ~25 lenses across Areas 1/6/9 + Tier-3 concentration | §4.4 + Agent B |
| `tools/cache.py` + `cached_tool` decorator | 2 days | All 17 wired providers | §4.5 |
| `cli/scripts/fetch_api.sh` | 1 day | All ~75 free public API lenses + Brave Search wrapper | §4.6 |
| DataForSEO method extensions (whichever methods underspec'd) | 2–3 days | Findability + Acquisition agents | original plan |
| **DNS hygiene full interpretation** (SPF/DKIM/DMARC/BIMI/MTA-STS) | 1 day | Stage 1a | §4.8 |
| **6 preflight stub fills** (assets/badges/headers/schema/social/tooling) | 5–7 days | ~10 lenses across Areas 1/6/9 | §4.8 |
| **NEW: SimilarWeb Digital Marketing API wrapper** | 2–3 days | W5 + W9 Phase-0 frames | §4.7 |
| **NEW: Brave Search API wrapper** (URL-pattern via fetch_api.sh) | 1 day | #157 | §4.7 |
| **NEW: SerpAPI Google Ads Transparency wrapper** (live fallback for Adyntel) | 1 day | One-off advertiser lookups | §4.2 |
| **NEW: Apify-as-X-fallback routing within `XpozAdapter`** | 1–2 days | Live-sufficient X queries | §4.2 |
| 13 free-API URL-pattern wrappers in agent prompts (no Python; prompt authoring + auth env-var documentation) | 5–7 days (parallel-friendly) | Stage 1b + Stage 2 agents | original plan |
| Provider integration tests (1 happy path per Tier-1 provider; ~3 fixtures per Tier-2 category) | 2–3 days | Confidence to ship Phase 2 | original plan |

**Total: 27–35 working days ≈ 4–5 weeks.** Single dev. Some items parallelize within a week. **Tier-3 work (Wappalyzer + RenderedFetcher) is the critical path** — start day 1, finish before week 3 to avoid bottlenecking 40+ lenses.

### 4.10 Provider list reconfirmation TODO (before Phase 1.5 starts)

JR direction earlier in this conversation: *"as next steps we will still need to confirm again the actual list of sources and providers, leave that as an important Todo that we can address a little later in the plan."*

**Status update 2026-05-06:** Agent B already completed Pass 1 (lens-coverage audit) — produced a 192-entry mapping with 4 hard gaps surfaced (§4.7). Passes 2 and 3 remain.

**Remaining action** before Phase 1.5 build kicks off — JR + Claude reconfirm in two more passes:

1. ~~Lens-coverage audit.~~ ✅ Done by Agent B 2026-05-06.
2. **Tier reassignment review.** Walk the ~75 free-public-API list end-to-end — some endpoints may have moved (Reddit OAuth requirement is recent), some may be deprecated (SecurityHeaders.com → Mozilla HTTP Observatory v2 already done). Confirm current endpoints + auth requirements + rate limits + 2026-current pricing where applicable.
3. **Owned-provider gap check.** Confirm the 17 wired providers cover all lenses Agent B mapped to them (no agent-mapping errors); spot-check a few Tier-3 lens assignments (Wappalyzer + Playwright) for execution feasibility.

Output: `docs/plans/2026-05-06-001-marketing-audit-v1-master-plan-providers-list.md` — a flat reference table mapping lens_id → primary_provider + secondary_providers + tier + cost_per_call + auth_env_var. Becomes the Phase 1.5 source-of-truth.

Estimate: ~0.5–1 day remaining, JR + Claude collaborative (Pass 1 already done).
## Section 5 — Commerce + Funnel

### 5.1 End-to-end customer journey

```
1. Prospect lands on gofreddy.ai → reads pitch → submits form (URL + email + firmographics)
   ↓
2. Cloudflare Worker → POST /v1/scan/request → Supabase row + Slack ping to JR
   ↓
3. Fly API spawns scan worker → runs Stage 0 + 1a-subset → 1 Opus call
   ↓
4. Email markdown to prospect + scan.html uploaded to reports.gofreddy.ai/scan/<slug>/
   ↓
5. JR follows up (or prospect replies) → schedules SALES CALL (Fireflies-captured)
   ↓
6. Sales call → JR sends Stripe Checkout link for $1K paid audit
   ↓
7. Prospect pays → Stripe webhook → state.paid=True → Slack ping to JR
   ↓
8. JR runs `freddy audit init <slug>` → workspace + state.json initialized
   ↓
9. JR fires Stage 1 → reviews brief at INTAKE GATE → confirms → Stage 2 fires
   ↓
10. JR reviews deliverable at SHIP GATE → edits → runs publish
    ↓
11. WALKTHROUGH CALL (Fireflies-captured) → deliverable presented + $15K+ engagement pitched
    ↓
12. T+60d: engagement-converted? signal recorded in audits/lineage.jsonl (R10 fitness signal)
```

**Auto vs manual** *[source: `2026-04-20-002` R14]*: free scan auto-runs end-to-end; **all paid stages require manual JR-fire**. No arq queue, no auto-trigger on payment webhook.

### 5.2 Free AI Visibility Scan (lead magnet)

*[source: `2026-04-20-002` R16]*

**Architecture:**
```
gofreddy.ai form → Cloudflare Worker (cloudflare-workers/intake/) →
  POST https://api.gofreddy.ai/v1/scan/request
  → Fly API handler (src/api/routers/scan.py — Phase 1 build)
  → INSERT INTO audit_pending (audit_id, url, email, firmographics, scan_status='running')
  → Slack lead-notification to JR
  → spawn scan worker (asyncio task) →
      stage_0_intake() → stage_1_warmup_subset(["dataforseo.serp_features", "cloro.ai_visibility"]) →
      ONE Opus call (prompts/scan_synthesis.md) → produce 1-page note (markdown + HTML)
  → Send email markdown to prospect via Resend / Postmark / SES (Phase 1 pick)
  → Upload scan.html to R2 via src/storage/r2_storage.py (already wired)
  → Cloudflare Worker serves at reports.gofreddy.ai/scan/<slug>/
```

**What the scan delivers:** narrow teaser highlighting **2–3 specific AI-search findings** ("You're cited by Perplexity for 8/10 queries but by Claude for only 2 — costing you enterprise buyers"). Deliberately narrow — shows the problem on one dimension, doesn't give away the full diagnosis. Creates FOMO for the $1K audit. *[source: `2026-04-20-002` R16]*

**Cost target:** ~$1–2 per scan. **Wall-clock target:** <5 min from form submission to email delivery.

**State row at scan-time:**
```python
class AuditPending(BaseModel):
    audit_id: str         # ULID
    url: str
    email: str
    firmographics: dict   # vertical/segment/geo/employee_count guesses from form
    scan_status: Literal["pending", "running", "delivered", "failed"]
    scan_url: str | None  # reports.gofreddy.ai/scan/<slug>/
    paid: bool = False
    created_at: datetime
```

### 5.3 Two-call model (sales call + walkthrough call)

*[source: `2026-04-20-002` R15]*

| Call | When | Purpose | Capture | Schema |
|---|---|---|---|---|
| **Sales call** | After scan delivery, before $1K payment | Qualify prospect; pitch $1K audit value; collect ICP/competitor/pain-point details | Fireflies webhook → `clients/<slug>/sales_call/transcript.txt` + `fit_signals.json` | `SalesCallSignals` Pydantic — ICP refinement, named competitors, top-3 pain points, budget signal, decision-timeline |
| **Walkthrough call** | After paid audit ships | Present deliverable; pitch $15K+ engagement; capture objections | Fireflies webhook → `clients/<slug>/walkthrough_call/transcript.txt` + `fit_signals.json` | `WalkthroughCallSignals` Pydantic — finding resonance per ParentFinding, engagement-tier interest, blocker objections, T+60d-conversion-likely-Y/N |

**Two distinct webhook endpoints:**
- `POST /v1/audit/sales-call-transcript` (Fireflies → Fly API)
- `POST /v1/audit/walkthrough-call-transcript` (Fireflies → Fly API)

Each fires:
1. Webhook signature verification (Fireflies HMAC)
2. Idempotency check (transcript_id deduped)
3. Sonnet pass to extract structured fit signals from transcript
4. Write to `clients/<slug>/{sales_call,walkthrough_call}/{transcript.txt, fit_signals.json}`
5. Slack ping to JR with summary

`fit_signals.json` from the sales call feeds Stage 1c brief synthesis (refines ICP + competitor list before Stage 2 runs). From the walkthrough call, feeds T+60d engagement signal in `audits/lineage.jsonl`.

### 5.4 Stripe Checkout + payment webhook

*[source: `2026-04-20-002` R10]*

**Phase 1 build** — `cloudflare-workers/stripe-webhook/` + `src/api/routers/stripe.py`.

**Flow:**
```
JR sends Stripe Checkout link to prospect (manual)
  ↓
Prospect pays $1,000
  ↓
Stripe → POST cloudflare-workers/stripe-webhook (or directly to Fly API /v1/audit/stripe)
  ↓
1. Verify signature (Stripe-Signature header + endpoint secret)
2. Idempotency check (event.id deduped against stripe_events table)
3. Match metadata.audit_id to audit_pending row
4. UPDATE audit_pending SET paid=True, paid_at=NOW() WHERE audit_id=...
5. UPDATE state.json (in workspace) — state.paid=True
6. Slack ping to JR: "Audit <slug> paid — ready to fire Stage 2"
```

**Idempotency strategy** — `stripe_events` table keyed by `event.id`; webhook returns 200 on duplicate (Stripe retries on non-200). No double-charging the audit, no double-firing Stage 2.

**Webhook signature verification non-negotiable** — Stripe webhook calls without valid signatures are rejected before any DB write.

**Manual fire policy:** Stripe webhook flips `state.paid=True` but does NOT auto-fire Stage 2. JR sees Slack ping, manually runs `freddy audit run <slug>`. *[source: `2026-04-23-002` D1; `2026-04-20-002` R14]*

### 5.5 Cloudflare Worker (intake + scan hosting + audit hosting)

*[source: `2026-04-20-002` §Architecture diagram]*

**Three Worker entry points** — Phase 1 build:

| Worker | Path | Role |
|---|---|---|
| `cloudflare-workers/intake/` | `gofreddy.ai/api/scan-request` | Receives form submission → POST to Fly API `/v1/scan/request` → returns 200 + tracking ID |
| `cloudflare-workers/scan-hosting/` | `reports.gofreddy.ai/scan/<slug>/` | Serves free-scan HTML from R2; `X-Robots-Tag: noindex`, `Referrer-Policy: no-referrer` |
| `cloudflare-workers/audit-hosting/` | `reports.gofreddy.ai/<ulid>/` | Serves paid-audit HTML+PDF from R2; same headers; URL slug drops client-name prefix (security) |

**Stripe webhook** can live in a 4th Worker OR directly on Fly API — Phase 1 picks based on cold-start tradeoffs. Worker route benefits from Cloudflare's signature-verification middleware; Fly route co-locates with the rest of `/v1/audit/*` handlers.

R2 storage already wired via `src/storage/r2_storage.py` + `r2_media_storage.py` (per Agent A inventory). Workers read from R2; no new storage primitive needed.

### 5.6 Three permanent gates (commerce-side detail)

*[source: `2026-04-20-002` R8; `2026-04-23-002` D2]*

| Gate | Backed by | Block mechanism | What JR does |
|---|---|---|---|
| **Intake review** | `state.intake_confirmed: bool` | Stage 1c writes brief → CLI exits with "Run `freddy audit confirm-brief <slug>` to proceed"; Stage 2 raises `IntakeNotConfirmed` until set | Read `clients/<slug>/audit/prediscovery/{brief.md, gaps.jsonl}` → run confirm command |
| **Payment gate** | `state.paid: bool` | Set by Stripe webhook; Stage 2 raises `PaymentRequired` until True | Wait for Stripe webhook (or set manually via `freddy audit mark-paid <slug>` for fallback when webhook fails) |
| **Ship gate** | `state.published: bool` | Stage 5 produces deliverable; `freddy audit publish <slug>` is the only path that flips this and uploads to R2 | Read `clients/<slug>/audit/deliverable/report.html` locally → edit if needed → run publish |

**Manual override commands:**
- `freddy audit mark-paid <slug>` — for fallback if Stripe webhook misses
- `freddy audit confirm-brief <slug>` — explicit intake-confirmation flag flip
- `freddy audit publish <slug>` — final publish (uploads R2 + tags lineage)

### 5.7 Slack lead-notification

*[source: `2026-04-20-002` §"Lead capture only via Cloudflare Worker → Fly API → Supabase row → Slack ping to JR"]*

Two notification types:

```python
# Free-scan delivered
{
    "channel": "#gofreddy-leads",
    "text": "🆓 New free scan delivered to {email} for {url}",
    "fields": {
        "scan_url": "https://reports.gofreddy.ai/scan/{slug}/",
        "firmographics": {...},
        "ai_visibility_headline": "Cited by 3/6 engines"
    }
}

# Paid audit ready to fire
{
    "channel": "#gofreddy-paid",
    "text": "💰 Audit {slug} paid ($1K) — ready to run Stage 2",
    "fields": {
        "client": "{client_name}",
        "url": "{url}",
        "next_command": "freddy audit run {slug}"
    }
}
```

Phase 1 build — Slack webhook URL in `SLACK_WEBHOOK_LEADS` + `SLACK_WEBHOOK_PAID` env vars.

### 5.8 First-5 calibration mode (deferred to v1.5)

Approval prompts after every stage (beyond the 3 permanent gates) was originally proposed for audits 1-5 to catch early-pipeline shape errors. **Deferred to v1.5** — the 3 permanent gates + manual-fire policy cover most of what calibration mode adds; the 1-2 day Phase 4 work item isn't justified by what's left over. Add back if first 3 audits expose shape errors the gates miss. *[source: self-review pressure-test 2026-05-06]*

### 5.9 Data retention + R10 kill-rule

*[source: `2026-04-20-002` R10, R11]*

**Retention:**
- Workspace `clients/<slug>/audit/` — kept active 90d post-delivery
- Compressed archive — retained 1y after 90d active
- Deliverable at `reports.gofreddy.ai/<ulid>/` — preserved full 1y
- Pre-paid leads (Stage 1 complete, never paid) — same retention

**R10 success-metric kill rule:** if **<2 of first 10 paid audits convert to $15K+ engagement within 60d**, halt new audit ingestion + retune. The audit-pipeline thesis is that paid audits anchor engagement conversion; if conversion rate is too low, the pipeline doesn't earn its keep regardless of audit quality. Recorded in `audits/lineage.jsonl` per audit and rolled up monthly.

### 5.10 LFS strategy for prospect-NDA fixtures

*[source: `2026-04-30-001` §Scope; `2026-04-22-005` LFS plan]*

`tests/fixtures/audit/**/*.tar.gz` — gitignored from normal git via `.gitattributes` LFS rule. Prospect-NDA cache content (real cache JSON from real audits) stays out of normal git history; only tarred-up fixture bundles sit in LFS for eval-harness use. Phase 1 work — add LFS rule to `.gitattributes` + document `git lfs install` requirement in `docs/CONTRIBUTING.md`.
## Section 6 — Autoresearch Self-Improvement Loop

### 6.1 v1 evolve-loop activation timeline

JR direction: full autoresearch implementation in v1. But "implemented" ≠ "actively rotating variants every day." Activation has prerequisites that gate execution, even though the lane registration + scoring infrastructure ships day 1.

| Phase | What's wired | What runs | What's gated |
|---|---|---|---|
| **Day 1** | LaneSpec entry + `custom_score` + `custom_validate` + lineage shape + manifest freeze | Lineage row written per live audit; manifest validated at every variant-clone | Variant generation (no MA-1..MA-8 rubrics frozen yet); promotion gate (no holdout fixtures) |
| **After MA-1..MA-8 rubrics authored + frozen** (~3-5 weeks of JR-coordinated content authoring; can start parallel to Phase 1) | Variant rotation enabled; meta-agent mutates evolvable prompts | First variants generated + scored against existing live audits | Promotion still gated on smoke-test |
| **After audit-3** (~3 paid audits shipped) | First holdout fixtures captured (with prospect consent) | `custom_promote` wired to smoke-gate | Engagement signal still thin — wait for audit-5 to T+60d-mature |
| **After audit-5 + 60d** | Engagement signal mature in lineage | Full evolve-loop economics: variants promote on (rubric-improved + engagement-positive); pre-promotion smoke-test fail-closed | None (steady-state) |

So **v1 ships full structural integration** (everything autoresearch needs to recognize marketing_audit as a peer lane), but the **evolve loop's variant rotation only kicks in when content + fixtures are ready**. This is honest activation, not deferred capability. *[source: synthesized from `2026-04-24-005` Units 15-18 + JR direction 2026-05-06]*

### 6.2 The 2 custom callables in v1 (others use defaults)

LaneSpec wires only what genuinely diverges from peer-lane defaults. *[source: `autoresearch/lane_registry.py:42-46`; pressure-tested 2026-05-06]*

| Callable | Status | Module | Why this status |
|---|---|---|---|
| `custom_score` | **Wired** | `src/audit/score.py:marketing_audit_score(config, variant_dir, parent_id)` | Default `_score_variant_search` at `evaluate_variant.py:1180-1202` emits `mean_inner_pass_rate / mean_outer_pass_rate / mean_pass_rate_delta` assuming an inner critique loop. v1 has no inner critique loop (LHR D2). Default would emit null/wrong metrics. Required to emit lane-appropriate scoring. **Pre-folds engagement bonus (+0.05 max) into `metrics.domains.marketing_audit.score` so default reader picks it up.** |
| `custom_validate` | **Wired** | `src/audit/validate.py:marketing_audit_validate(variant_dir, parent)` | Substrate's `compute_expected_hashes()` (`autoresearch/critique_manifest.py`) is symbol-based, not file-based. Adding marketing_audit's stage/judge/rubric file paths is a structural substrate redesign. The lane callable using shared `lane_registry.verify_manifest()` is self-contained and proven. |
| `custom_objective_score_from_entry` | **None (default)** | n/a | Default at `lane_registry.py:218-241` reads `entry.search_metrics.domains[lane_name].score`. Since `custom_score` pre-folds engagement bonus into that field, no separate reader needed. **Simplified per JR pressure-test 2026-05-06.** |
| `custom_promote` | **None (until post-audit-3)** | (`src/audit/promote.py` lands when holdout fixtures exist) | No holdout fixtures in v1 — callable would do nothing. Wired post-audit-3 with first-3 paid audits' consent-captured fixtures. |
| `custom_mutate` | **None (default meta-agent)** | n/a | No marketing-audit-specific mutation logic. Default meta-agent (claude-code/codex/opencode subprocess) mutates evolvable prompts. *[source: `2026-04-24-005:1499`]* |

**Net: 2 custom callables wired in v1** — fewer than fusion plan's 4, more than peer lanes' 0. Each has a justified reason; none are inherited "we always did it this way."

### 6.3 What evolves, what stays frozen

The marketing_audit lane has **content/orchestration split** — catalog content is frozen authority; orchestration prompts are evolvable. *[source: `2026-04-24-005:173, 198`]*

| Frozen (manifest-enforced) | Evolvable (meta-agent mutates) |
|---|---|
| 149 lens definitions in catalog `2026-04-22-005` | Stage 1b agent's URL-pattern-fetching tactics (which APIs to hit first, retry strategies in the prompt) |
| MA-1..MA-8 rubric judge prompts | Stage 1c brief synthesis prompt (how Phase-0 frames are surfaced; what reading guides emphasize per agent) |
| MA-1..MA-8 judge instructions + scoring schema (`[STABLE]` section markers deferred to v2; v1 freezes whole files) | Stage 2 agent prompts for Findability/Narrative/Acquisition/Experience (rubric-checking heuristics, evidence-strength thresholds) |
| 9-section deliverable IA (Section 2.2) | Stage 3 synthesis prompt (cross-cutting Phase-0 framing, ParentFinding consolidation prose) |
| 11-area marketing taxonomy | Stage 4 proposal prompt (capability_registry tier mapping logic) |
| `agent_models.py` schema | Per-agent rubric YAML files (lens-firing decision logic) |

**Manifest verification at scoring time** (`custom_validate` fires per-variant): if the meta-agent mutates a frozen file, manifest hash check fails, variant is rejected. This blocks the evolve loop from migrating content authority out of `lenses.yaml` into stage-prompt text (catalog-content drift via prompt expansion). *[source: `2026-04-24-005:1637`]*

### 6.4 MA-1..MA-8 rubrics (the 8 judges)

8 LLM judges score each audit's `findings.md` (the structured 9-section primary deliverable, NOT report.md — see §3.6 + `2026-04-24-005:1308`). Geometric mean across 8 = fixture-level fitness; geometric mean across fixtures = lane domain score. *[source: `_rubric_ids("MA")` pattern matching peer lanes; `2026-04-24-005` Unit 15]*

Working titles (content authoring is JR-coordinated, ~16-32h per fusion plan §Unit 18; locked when manifest freezes):

| Rubric | Working title | What it scores |
|---|---|---|
| **MA-1** | Strategic-narrative coherence | Does each section have a unifying argument, not a list-of-issues? |
| **MA-2** | Evidence traceability | Every claim cites lens_id + ≥1 evidence URL; estimates labeled "estimated"; numbers source-attributed |
| **MA-3** | Phase-0 framing applied | "State of the Business" opener pulls measurements from phase0_meta.json; per-section findings color by relevant frame |
| **MA-4** | Actionable + capability-mapped | Each ParentFinding's recommendation maps to capability_registry tier; ≥50-word strategic substance; not DIY execution guide |
| **MA-5** | Severity calibration | severity 0-3 anchored to lens-specific anchors; no severity inflation; max-of-children rollup correct |
| **MA-6** | Polish + voice consistency | No AI-tells (em-dash density, "leverage/utilize/robust"); customer-facing prose quality |
| **MA-7** | Gap honesty | gap_flagged rubrics surfaced; missing-data analyzed not papered over; data-gaps treated as findings |
| **MA-8** | Engagement-fit | Findings + proposal align with capability_registry; tier-mapping serves a $15K+ engagement pitch (T+60d signal corroborates) |

**Rubric authoring path** (Phase 1 work, parallel to code build):
1. JR drafts MA-1..MA-8 working titles + scoring schemas (each ~150-250 words)
2. JR + Claude iterate on judge prompts against 1-2 hand-built example findings.md
3. SHA256-freeze when JR satisfied → `marketing_audit_manifest.json` written by `regen_marketing_audit_manifest.py` operator script *[source: `2026-04-24-005:2054` A4]*
4. Estimate: 16-32h JR time spread over Phase 1

### 6.5 Fitness composition + engagement-weighted T+60d signal

Inside `custom_score`:

```python
weighted_rubric_raw = geometric_mean([MA_1, MA_2, ..., MA_8])  # in [0, 10]
weighted_rubric_normalized = weighted_rubric_raw / 10.0          # in [0, 1]
engagement_bonus = 0.0
if entry.audit_id has T+60d engagement-converted-Y:
    engagement_bonus = 0.05  # max contribution
score = weighted_rubric_normalized + engagement_bonus            # in [0, 1.05]

# Write to standard location so default selector picks it up
search_metrics["domains"]["marketing_audit"]["score"] = score
```

**No separate `custom_objective_score_from_entry`** — default `default_objective_score_from_entry` (`lane_registry.py:218-241`) reads this `score` field directly. Engagement bonus is pre-folded; selection works without customization.

Normalization to `[0, 1]` (with `[0, 1.05]` ceiling for engagement bonus) keeps marketing_audit's externally-visible score in the same space as existing 4 lanes — `select_parent.py:97` plateau threshold (`pstdev < 0.01`) stays calibrated; no per-lane edit needed. *[source: `2026-04-24-005:1370`]*

**Engagement signal closure (T+60d):**
- Walkthrough call captures `T+60d-conversion-likely` flag (see §5.3)
- Manual JR confirmation at T+60d: `freddy audit close-engagement <slug> --converted=Y/N`
- Updates `audits/lineage.jsonl` row in-place with `engagement_converted_60d: bool`
- Next variant scoring run reads this flag; engagement_bonus reflected in next score calculation

**Cost-penalty term:** included in composite fitness with a floor below which it stops contributing — prevents token-optimization from cannibalizing customer-facing deliverable quality (a $5 token saving that degrades MA-6 polish is a bad trade on a $1K deliverable). *[source: `2026-04-24-005:198` (b)]*

### 6.6 Manifest enforcement (whole-file SHA256 in v1)

`marketing_audit_manifest.json` lives at lane-head; written ONCE by JR via the operator script `regen_marketing_audit_manifest.py` when MA-1..MA-8 rubrics + judge/stage prompts are frozen. `custom_validate` re-verifies on every variant scoring (between meta-agent mutate at `evolve.py:1551` and `custom_score` at `:1609`).

**Manifest covers:**
- All 8 MA-1..MA-8 rubric prompts (`programs/marketing_audit/prompts/rubrics/MA-*.md`)
- 8 judge prompts (`programs/marketing_audit/prompts/judges/MA-*-judge.md`)
- Stage prompts (`programs/marketing_audit/prompts/stage_*.md`)
- Inner-loop critic prompts (if v2 adds them — current v1 has no critic)

**Drift = variant rejected** (`_safe_rmtree`'d at `evolve.py:1602-1604`). No silent acceptance. The `[STABLE]` / `[EVOLVABLE]` section-marker pattern is **deferred to v2** — v1 freezes whole files. *[source: `2026-04-30-001` K-2]*

**Operator script** `autoresearch/scripts/regen_marketing_audit_manifest.py` (Phase 1 build, ~20 LOC):
```python
# Calls lane_registry.compute_manifest(...) over the explicit prompt-file list;
# writes to marketing_audit_manifest.json. Mirrors harness_fixer's regen pattern.
```

### 6.7 Pre-promotion smoke gate (`custom_promote`, post-audit-3)

When holdout fixtures exist, `custom_promote` runs one-fixture smoke-test before promoting a variant:

```python
def marketing_audit_promote(archive_dir, variant_id, lane):
    variant_dir = Path(archive_dir) / variant_id
    fixture = next(HOLDOUT_FIXTURES_DIR.iterdir())  # one fixture
    variant_score = score_against_fixture(variant_dir, fixture)
    head_score = score_against_fixture(LANE_HEAD_DIR, fixture)
    return all(
        variant_score[criterion] >= head_score[criterion]
        for criterion in ("MA-1", "MA-2", "MA-3", "MA-4", "MA-5", "MA-6", "MA-7", "MA-8")
    )
```

**Holdout fixtures** are created from real paid audits (with prospect consent) — first 3 audits inform fixture composition; a fixture bundles cache-state + brief + reference deliverable + ground-truth expected scores. Until 3+ paid audits ship, `custom_promote=None` and the substrate falls through to default behavior (no smoke gate).

**Cross-lane placeholder fixtures = REJECTED design.** Marketing_audit-specific fixtures only; passing MA-5/MA-6 against geo or competitive fixtures is degenerate. *[source: `2026-04-24-005:1639`]*

### 6.8 Lineage join (audits/lineage.jsonl ↔ autoresearch/archive/lineage.jsonl)

Two parallel lineage files; **same shape, joined by `audit_id == variant_id`** *[source: `2026-04-23-002:130-136`; `2026-04-24-005`]*:

| File | Owner | Row written | What it captures |
|---|---|---|---|
| `audits/lineage.jsonl` | live audits (`freddy audit run`) | One per completed paid audit | `{audit_id, completed_at, total_cost_usd, ship_gate_edit_count, vertical, segment, geo, finding_count, severity_distribution, engagement_converted_60d, search_metrics: {domains: {marketing_audit: {score, MA-1..MA-8, fixtures_detail, mean_inner_pass_rate, mean_outer_pass_rate}}}}` |
| `autoresearch/archive/lineage.jsonl` | evolve runs (`autoresearch evolve --lane marketing_audit`) | One per variant evaluation | Same shape |

Join key: `audit_id` (live) ≡ `variant_id` (evolve). T+60d engagement updates write back to the live file; evolve's score reads both files via the standard substrate readers.

### 6.9 Kill switch + halt commands

**Lane-level pause** *[source: `2026-04-24-005:1987`]*:
```
autoresearch evolve --pause marketing_audit
```
Sets a flag preventing `run_all_lanes` from advancing marketing_audit. Variant promotions halt; live audits continue running on current lane-head (no impact on customer-facing pipeline).

**Operator escape hatches:**
- `freddy audit run <slug> --override-manifest` — JR can run a live audit even if manifest verification fails (escape hatch for emergency client delivery if a prompt was hand-edited mid-flight)
- `freddy audit run <slug> --pin-variant <variant_id>` — force live audit to use a specific frozen variant snapshot (audit reproducibility for legal/audit trail)

### 6.10 Dependency on autoresearch substrate fixes

**Update 2026-05-06 (later same day):** autoresearch substrate fixes **SHIPPED to origin/main** — Phase A+B + 5 review-fix groups, commits `cbf01f5..d84ab2a`, 413 tests pass (+18 net new). The "approved but not implemented" note from earlier this same day is stale.

**Pre-shipment baseline** was $240–680/run with 0 validated promotions (per `docs/plans/2026-05-06-001-autoresearch-evolution-fixes-phase-a-b.md`). **Post-fix dry-run is currently blocked** on judge services not running on `:7100/:7200`. PI runs abandoned per memory; Mac-only from here.

**Implication for marketing_audit v1:** the substrate is fixed; the gating concern is now *operational* (judge services up + dry-run validates the post-fix loop) rather than architectural. Sequencing remains:

1. **Marketing-audit Phase 1** (lane registration + custom_score + custom_validate + lineage) — ships independently of substrate state
2. **Autoresearch substrate fixes** — SHIPPED ✓
3. **Judge services running on :7100/:7200 + post-fix dry-run validates loop economics** — blocker
4. **MA-1..MA-8 rubric authoring** — ships independently (JR-coordinated content)
5. **First marketing_audit variant rotation** — gates on (1) + (3) + (4)

Marketing_audit doesn't block on the operational blocker either — lane registration + manifest enforcement land regardless. The evolve-loop *value* gates on judge services + post-fix dry-run validation, not on the substrate code itself anymore.
## Section 7 — Phase Plan, First-Runnable Milestone, Risk Register

### 7.1 Phase overview

| Phase | Delivers | Estimate | Calendar parallelizable with |
|---|---|---|---|
| **Phase 1** — Foundation + lane wiring | LaneSpec registered + agent_models.py extended + cherry-picks from snapshot tag + custom_score/validate stubs + preflight runner wired | 2-3 weeks | Phase 1.5 (start week 1) |
| **Phase 1.5** — Provider build | Wappalyzer-next + RenderedFetcher + cache layer + fetch_api.sh + 6 preflight stub fills + SimilarWeb + Brave + SerpAPI + Apify-X-route | 4-5 weeks | Phase 1, MA rubric authoring |
| **Phase 2** — Stage pipeline + agents | 6-stage pipeline complete (`stages.py`, `agent_runner.py`); 4 agent prompts; Stage 3 synthesis; capability_registry; Jinja+WeasyPrint render | 2-3 weeks | MA rubric authoring; autoresearch fix plan |
| **Phase 3** — Commerce + funnel | 3 Cloudflare Workers; Stripe webhook; free scan worker; Slack notifications; Fireflies webhooks; full `freddy audit` CLI surface | 2 weeks | — |
| **Phase 4** — Polish + first-runnable | Cost observability; resume-by-session-id; deterministic HealthScore; events.jsonl; first-runnable end-to-end test | ~1 week | — |
| **MA-1..MA-8 rubric authoring** (parallel content track) | 8 rubric prompts + 8 judge prompts + manifest freeze | 16-32h JR time | All phases |
| **Autoresearch fix plan A12→A7** (parallel substrate track) | Substrate fixes from `2026-05-06-001-autoresearch-evolution-fixes-phase-a-b.md` | (separate plan) | All phases |

**Total: ~10-13 weeks** to first-runnable. **Critical path** = Phase 1 → Phase 1.5 → Phase 2 → Phase 3 → Phase 4. **Tier-3 work (Wappalyzer + RenderedFetcher) is the long pole within Phase 1.5** — start day 1, finish before week 3 of Phase 1.5.

### 7.2 Phase 1 — Foundation + lane wiring (2-3 weeks)

| Work item | Source | Estimate |
|---|---|---|
| `agent_models.py` additions (marketing_area + phase0_frame on SubSignal; parent_findings on AgentOutput) — ~6 LOC additive | §2.5 | 0.5 day |
| Cherry-pick `state.py` + `sessions.py` + `cost_ledger.py` + `graceful_stop.py` + `resume.py` + `cleanup.py` + `events.py` from `phase-1-foundation-snapshot` (`cb425b6`) with fusion-only cleanup (~80 LOC removals) | §2.5 + plan history | 2-3 days |
| Cherry-pick Unit 7's 6 real preflight check implementations (~1300 LOC + tests) — replaces stubs on main | §4.8 + fusion plan Unit 7 | 2-3 days |
| Wire `src/audit/preflight/runner.py` into `stage_1_warmup` | §4.8 | 1 day |
| Register `marketing_audit` LaneSpec in `autoresearch/lane_registry.LANES` (data fields only — callables stub-wired for v1.0) | §3.1 | 0.5 day |
| Stub `src/audit/score.py:marketing_audit_score` + `src/audit/validate.py:marketing_audit_validate` (returning sane defaults; full implementation in Phase 2) | §6.2 | 1 day |
| Create `programs/marketing_audit-session.md` marker (`evaluate_variant.py:584` L1 gate requirement) | §3.1 | 0.5 day |
| Create `src/evaluation/structural.py:_validate_marketing_audit` — 9-section findings.md schema + 3-tier proposal.md schema validators | `2026-04-24-005:1310` | 1 day |
| Create `marketing_audit_manifest.json` operator script `autoresearch/scripts/regen_marketing_audit_manifest.py` | §6.6 | 0.5 day |
| Add LFS rule to `.gitattributes` for `tests/fixtures/audit/**/*.tar.gz` | §5.10 | 0.5 day |
| Tests: lane registration, schema additions, preflight runner wiring | — | 2-3 days |

**Total Phase 1: ~12-16 working days ≈ 2-3 weeks.** Most cherry-picks are well-scoped + tested in `phase-1-foundation-snapshot` already.

### 7.3 Phase 1.5 — Provider build (4-5 weeks)

See §4.9 for full detail. Sequenced AFTER Phase 1's foundation but can start week 1 in parallel:

- **Week 1-2:** Wappalyzer-next + martech_rules.yaml (start day 1; critical path)
- **Week 1-2:** Cache layer (`tools/cache.py` + `cached_tool` decorator) — needed by every Tier-1 provider
- **Week 2-3:** Playwright RenderedFetcher (parallel with Wappalyzer finalization)
- **Week 2-3:** `cli/scripts/fetch_api.sh` + 6 preflight stub fills + DNS interpretation
- **Week 3-4:** SimilarWeb wrapper (W5+W9 panel data — load-bearing for Phase-0)
- **Week 3-4:** SerpAPI Google Ads + Apify-X-fallback wiring within existing adapters
- **Week 4:** 13 free-API URL-pattern wrappers in agent prompts (parallel-friendly)
- **Week 5:** Provider integration tests + Brave Search wrapper

### 7.4 Phase 2 — Stage pipeline + agents (2-3 weeks)

| Work item | Source | Estimate |
|---|---|---|
| `src/audit/stages.py` — `stage_0_intake`, `stage_1_warmup`, `stage_1b_predischarge`, `stage_1c_brief_synthesis`, `stage_2_agents`, `stage_3_synthesis`, `stage_4_proposal`, `stage_5_deliverable` | §3.3-3.8 | 5-7 days |
| `src/audit/agent_runner.py` — multi-provider CLI dispatch wrapper using `autoresearch/agent_calls.py` + `agent_retry.py`; session_id persistence; per-call cost capture | §3.5 | 2-3 days |
| 4 Stage-2 agent prompts (`programs/marketing_audit/prompts/stage_2_{findability,narrative,acquisition,experience}.md`) including per-agent rubric YAML synthesis instructions | §3.5 | 4-5 days (parallel with each other) |
| Stage 1c brief synthesis prompt (with phase0_meta block) + agent reading guides | §3.4 | 1-2 days |
| Stage 1b pre-discovery prompt with ~75 free-API URL-pattern blocks | §3.4 + §4.3 | 2-3 days |
| Stage 3 cross-cutting Phase-0 + narrative writer prompts | §3.6 | 2 days |
| Stage 4 proposal prompt + `data/capability_registry.yaml` (~48 entries) | §3.7 | 2-3 days |
| Stage 5 Jinja2 template (`templates/audit_report.html.j2`) + WeasyPrint render + ULID slug | §3.8 | 2-3 days |
| `data/rubrics_<agent>.yaml` files (~149 lens-entry YAML rows distributed across 4 agents) — mechanical Claude-authored from catalog | §3.5 | 3-4 days |
| Tests: orchestration smoke tests, error semantics, schema validators | — | 2-3 days |

**Total Phase 2: ~15-22 working days ≈ 2-3 weeks.** Some agent-prompt work parallelizes; rubric YAML authoring is mechanical.

### 7.5 Phase 3 — Commerce + funnel (2 weeks)

| Work item | Source | Estimate |
|---|---|---|
| Cloudflare Worker `intake/` (form submission → Fly API) | §5.5 | 1-2 days |
| Cloudflare Worker `scan-hosting/` (R2 → reports.gofreddy.ai/scan/<slug>/) | §5.5 | 0.5 day |
| Cloudflare Worker `audit-hosting/` (R2 → reports.gofreddy.ai/<ulid>/) | §5.5 | 0.5 day |
| Stripe webhook handler (`src/api/routers/stripe.py` + signature verification + idempotency table) | §5.4 | 2 days |
| Free scan worker (`src/api/routers/scan.py` — runs Stage 0 + 1a-subset + 1 Opus call → email + R2 upload) | §5.2 | 2-3 days |
| Email delivery integration (Resend / Postmark / SES — pick one) | §5.2 | 1 day |
| Slack lead-notification webhooks (`SLACK_WEBHOOK_LEADS` + `SLACK_WEBHOOK_PAID`) | §5.7 | 0.5 day |
| Fireflies sales-call webhook (`POST /v1/audit/sales-call-transcript`) + walkthrough webhook | §5.3 | 2 days |
| `freddy audit` CLI surface — `run`, `publish`, `mark-paid`, `send-invoice`, `ingest-transcript`, `init`, `confirm-brief`, `close-engagement`, `attach-{gsc, ads, winloss, budget}` | §3.3, §3.11, §5.6 | 2-3 days |
| Tests: webhook signature, idempotency, scan worker end-to-end | — | 1-2 days |

**Total Phase 3: ~12-15 working days ≈ 2 weeks.**

### 7.6 Phase 4 — Polish + first-runnable validation (~1 week)

| Work item | Source | Estimate |
|---|---|---|
| Cost observability — `cost_actual.json` per stage; Slack at $200/$400 thresholds | §3.9 + §5.7 | 1 day |
| Resume-by-session-id (per-agent session_id persistence, `freddy audit run --resume`) | §3.10 | 1 day |
| Deterministic HealthScore arithmetic + Opus rationale call | §3.6 | 1 day |
| Events.jsonl observability sink | §1 operating principles | 0.5 day |
| **First-runnable end-to-end test** — run against test prospect URL; verify all 8 stages, 3 gates, deliverable shape, lineage row | §7.7 | 1-2 days |

**Total Phase 4: ~4-5 working days ≈ 1 week.** Calibration mode deferred to v1.5 (§7.9).

### 7.7 First-runnable milestone definition (acceptance criteria)

The pipeline is first-runnable when ALL of the following pass against a single test prospect URL (test, not paying customer):

| Criterion | How to verify |
|---|---|
| `freddy audit init <slug>` creates workspace + state.json | `ls clients/<slug>/audit/` shows expected dirs |
| `freddy audit run <slug>` runs Stage 1a → 1b → 1c → confirms intake gate | CLI exits with "confirm-brief" message; brief.md + gaps.jsonl + phase0_meta.json populated |
| `freddy audit confirm-brief <slug>` flips `state.intake_confirmed=True` | state.json updated |
| `freddy audit mark-paid <slug>` (skipping Stripe for test) flips `state.paid=True` | state.json updated |
| `freddy audit run <slug>` continues Stage 2 → 3 → 4 → 5 | All stages complete; deliverable directory populated |
| Stage 2: 4 agents return AgentOutput with sub_signals + parent_findings + rubric_coverage strict | Each `agents/<a>/agent_output.json` validates against schema |
| Stage 3: synthesis produces findings.md + report.md + report.json + surprises.md + gap_report.md | Files exist; report.json contains HealthScore |
| Stage 5: deliverable/report.html + report.pdf + assets/ produced | `ls deliverable/` shows expected files |
| `freddy audit publish <slug>` uploads to R2 + Cloudflare Worker serves | `curl reports.gofreddy.ai/<ulid>/` returns 200 |
| Lineage row written to `audits/lineage.jsonl` | `tail audits/lineage.jsonl` shows the run |
| Manifest validation passes (no drift) | `custom_validate` returned True |
| Total cost recorded in `cost_actual.json` per stage | All stages have realized cost > 0 |

Quality bar at first-runnable is **"deliverable shape is correct, content is editable to client-quality"** — not yet "deliverable is shippable as-is." The first 1-2 client audits use the first-runnable pipeline + heavy JR ship-gate editing.

### 7.8 Risk register (top 5 + minor risks)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R1** | Tier-3 build (Wappalyzer + RenderedFetcher) slips in Phase 1.5 → ~70+ lenses degrade simultaneously | Medium | Critical | Prioritize as Phase 1.5 day-1 work; budget contingency time; Wappalyzer-next has clear OSS port path |
| **R2** | SimilarWeb subscription cost surprises ($1K-3K/mo enterprise tier) | Medium | High | Investigate Semrush .Trends as alternative; budget pricing reconciliation in §4.10 reconfirmation TODO |
| **R3** | Autoresearch substrate fixes (A12→A7) slip past Phase 1 → marketing_audit evolve loop generates wrong scores | Medium | High | Lane registration is independent of substrate fixes; only evolve-loop *value* gates on it. Schedule first variant rotation for after substrate fixes ship |
| **R4** | MA-1..MA-8 rubric authoring takes >32h JR time → Phase 1 calendar slip | Medium | Medium | Start parallel at Phase 1 week 1; iterate against 1-2 hand-built example findings.md; defer perfect tuning to v2 |
| **R5** | First 10 paid audits don't convert at ≥2/10 to $15K+ engagements (R10 kill rule trip) | Unknown | Critical | This IS the v1 commercial hypothesis. Halt + retune if kill rule trips. Not mitigatable — it's the commercial test |

**Minor risks** (smaller scope or more mitigatable; listed without table for visual weight):
- Cost runaway without caps in v1 — observability ships in v1; Slack thresholds at $200/$400; recalibrate cap floor after audit-5
- Stage 2 multi-turn cost overrun — per-agent `cost_actual.json`; v2 considers per-call `max_budget_usd` if pattern shows runaway
- Cloudflare Worker / Stripe webhook signature edge cases — idempotency via `stripe_events` table; manual `freddy audit mark-paid` fallback
- SimilarWeb panel data signal quality is too coarse — pilot with 1-2 test prospects pre-Phase-2; fall back to "data unavailable" gracefully
- JR ship-gate review bandwidth past ~5 audits/month — manual-fire policy explicitly accepts; v2 considers automated quality gates
- Multi-provider CLI rate limits during 4-agent fan-out — `autoresearch/agent_retry.py` already wired
- First 3 paid audits don't yield consent-able holdout fixtures — fall back to synthetic fixtures (lower fidelity, same shape)

### 7.9 What's NOT in v1 (deferred to v2/v3)

*[source: §1 Non-goals + plan history + self-review 2026-05-06]*

| Item | Where deferred | Trigger to revisit |
|---|---|---|
| 4 judge layers (SubSignal validator + ParentFinding strategic + coherence + engagement) | v2 | After 5 audits ship + ship-gate-edit patterns observable |
| Inner critique loop (3-pass critic → judge-driven correction) | v2 | After judges land |
| arq queue + auto-fire on payment webhook | v2 | After JR ship-gate bandwidth pressure |
| 5 of 9 attach-* commands (`esp`, `survey`, `assets`, `demo`, `crm`) | v2/v3 | When customer demand surfaces |
| Web UI / dashboard | v2 | When CLI-only friction observable |
| `[STABLE]` / `[EVOLVABLE]` rubric section markers | v2 | After whole-file freeze proves too coarse |
| Pre-promotion smoke gate (`custom_promote`) | post-audit-3 | First 3 paid audits with consent → fixtures land |
| Holdout fixtures | post-audit-3 | Same trigger as above |
| Cross-lane placeholder fixtures | Rejected as design flaw | Not revisited |
| Bernoulli replay variance | v2 | If non-determinism causes scoring drift |
| Per-call `max_budget_usd` enforcement | v2 | If cost runaway observed in v1 |
| Imposed per-audit cost cap | post-audit-5 | After empirical baselines |
| OpenLLMetry / Langfuse observability | v2 | If parallel-agent debugging becomes painful |
| Section-marker rubric drift detector | v2 | When section markers themselves added |
| Tenacity retries beyond `agent_retry.py` | v2 | If transient errors cluster |
| 5th MarTech agent | Rejected per CAD-3 | Not revisited |
| R29 subscription-window SLA | Removed (fusion-only construct) | Not revisited |
| **First-5 calibration mode** (approval prompts after every stage) | **v1.5** | If first 3 audits expose early-pipeline shape errors the 3 permanent gates miss |
| **8-stage pipeline collapse to 4 stages** (peer-lane-aligned shape) | **v1.5 (revisit)** | If 8-stage architecture feels heavy in practice; collapse 1a/1b/1c → 1, 2/3/4 → 2 |
