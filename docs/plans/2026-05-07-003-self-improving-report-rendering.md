---
title: "feat: Self-improving HTML+PDF report rendering — dual-loop architecture across all autoresearch lanes"
type: feat
status: ready
date: 2026-05-07
supersedes: []
related:
  - docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md  # extends WorkflowSpec / LaneSpec ergonomics
  - docs/plans/2026-05-06-001-marketing-audit-v1-master-plan.md  # reuses R2 + Cloudflare publish scaffold
---

# feat: Self-improving HTML+PDF report rendering across all autoresearch lanes

> **Why this plan exists:** Today every autoresearch lane terminates in raw markdown + JSON in `sessions/<lane>/<fixture>/`. Storyboard has its own polished HTML+PDF pipeline (`configs/storyboard/scripts/generate_report.py`) but it's a one-off — geo, competitive, monitoring don't have client-presentable output. The agent (Claude Opus) is perfectly capable of authoring polished HTML at session-end; the existing evolution loop already optimizes against rubric scores. This plan adds **one** new field to `WorkflowSpec` (`render_report`), **one** new subprocess script per lane, **one** new rubric domain (`RND-1..5`), and **one** new visual sub-judge — and the same self-improvement loop that improves content choices today will improve layout choices tomorrow.

## Overview

A **dual-loop, 5-layer model** for self-improving rendering:

1. **Chrome (frozen)** — header/footer/page-grid/typography/design-tokens in `src/shared/reporting/report_base.py:BASE_CSS`. Brand-locked. Rare human edits.
2. **Section-element library (slow)** — ~16 `.rprt-*` CSS classes. Quarterly human edits. **Now includes 4 transcript-derived primitives** (see §2a): `.rprt-reasoning-trail`, `.rprt-beat-card`, `.rprt-pivot-callout`, `.rprt-meta-pattern`.
3. **Lane render seed (evolution loop)** — new file `programs/{lane}-render-seed.md`. Meta-agent edits between variants.
4. **Per-session render decisions (session loop)** — Opus picks primitives based on this run's data shape **AND the agent's transcript reasoning trail**. Two-stage LLM call: (a) cheap awk/grep extraction over `logs/iteration_*.log.err`, (b) Opus synthesis with structured artifacts + extracted reasoning beats as input.
5. **Within-render refinement (render iterations)** — screenshot → Gemini Flash judges → if RND dim < threshold, refine + re-render. Bounded to 2-3 retries.

### Critical input contract addition

The render is NOT just a transform of `report.md` + `findings.md`. **It must consume the full agent transcripts** (`logs/iteration_*.log.err`) to surface the investigation journey — reasoning beats, tool-call patterns, pivot moments where the agent adapted to failures. Validated by demo v5: 19 iteration transcripts × avg 200KB = ~1.3MB raw transcript per fixture run. Programmatic extraction (awk on `^codex$` markers, grep on `^exec$`) reduces that to ~5-10KB of structured beats per fixture before the Opus call. **See §A8 below for the extraction pipeline.**

### Per-lane deliverable shape — 4 distinct templates, not one

Validated 2026-05-08 by surveying the 4 lanes' most-recent runs (geo=v009, competitive=v010, monitoring=v006, storyboard=v006): each lane produces a structurally different report, even though all four share the same chrome + section-element library + transcript pipeline.

| Lane | Deliverable | Distinctive sections |
|---|---|---|
| **geo** | Page-by-page optimization | strategic gap from `gap_allocation.json`, cached-page facts grid, citation evidence per AI engine, current-vs-recommended copy diff, JSON-LD `@graph` summary |
| **competitive** | Strategic positioning brief | per-competitor cards (with `unclassified` status when source-limited), source-coverage matrix, verify-cycle log (structural-gate retries), budget-governance recommendations |
| **monitoring** | Weekly executive digest | period header, highest-stakes development callout, anomaly cards (Crisis / Opportunity / Watchlist × severity × confidence), SOV breakdown, sentiment delta, data appendix |
| **storyboard** | Creator analysis + ideation | creator header, ranked video selection with engagement scores, format-diversity matrix, pattern cards, derived story plans, frame-level storyboards with Gemini-scored image previews |

This means production `render_report.py` is NOT one function — it's a dispatcher with a base composer (chrome + section-element library + transcript pipeline) and 4 lane-specific composers that pick the appropriate sections for the lane's deliverable shape.

**Cross-variant data sourcing:** when a lane's most recent run lives in a different variant from the active one (e.g., monitoring's last run was v006 even though the current variant is v009), `render_report.py` must walk the archive (`autoresearch/archive/v*/sessions/<lane>/`) and pick the most recent variant per lane that has data — not assume all 4 lanes ran in the same variant.

Two loops drive optimization:
- **Session loop** converges this run on a render that scores well (Layer 5 within Layer 4).
- **Evolution loop** captures what's stable across runs by mutating Layer 3 between variants; the existing variant-promotion machinery propagates rendering-improving variants forward.

The output (`report.html` + `report.pdf` + `report-screenshot.png`) lands in `session_dir/` alongside today's deliverables. The `screenshot.png` feeds a vision sub-judge that reuses the existing `verify_preview()` Gemini Flash pattern at `src/generation/image_preview_service.py:373-464`.

## Problem Frame

Six surfaces today disagree on what a "report" is:
- `geo`: glob `optimized/*.md` + `analyses/*.{json,txt}` (`workflows/geo.py:38-51`)
- `competitive`: `brief.md` + `analyses/*` (`workflows/competitive.py:38-51`)
- `monitoring`: `digest.md` + `recommendations/*` (implicit)
- `storyboard`: `stories/*.json` + a separate Python→Chrome→PDF renderer at `configs/storyboard/scripts/generate_report.py`
- `marketing-audit`: Jinja2 → WeasyPrint → R2 (PR #45, separate codepath at `src/competitive/pdf.py:43-52`)
- Frontend: React+Vite SPA at `frontend/`, but no API endpoint that serves HTML reports

All of them reach the same human eventually. None of them share a render layer. Storyboard's pipeline is the simplest precedent that actually works in production — this plan generalizes it.

## What's already there (verified by 4 research agents)

| Surface | File:line | Reusable as-is |
|---|---|---|
| `build_html_document(title, sections=[(label, html), ...], css_extra="")` | `src/shared/reporting/report_base.py:531-561` | yes — lane-agnostic primitive |
| `html_to_pdf()` via headless Chrome `--print-to-pdf` | `src/shared/reporting/report_base.py:593-633` | yes |
| Chrome `--screenshot=...` for HTML→PNG | tested working: 1.68s @ 1280×1600 on this machine | new helper, mirrors `html_to_pdf()` |
| `WorkflowSpec` dataclass | `autoresearch/archive/v009/workflows/specs.py:33-44` | extend with one optional field |
| `post_session_hooks()` runs `pre_summary_hooks` → `enforce_completion_guard` → `summarize_session.py` | `autoresearch/archive/v009/runtime/post_session.py:110-135` | extend with one new step |
| Subprocess pattern for post-session artifact gen | `workflows/geo.py:13-18` runs `build_geo_report.py` via `run_script()` | mirror exactly |
| Variant scorer accepts arbitrary `dimension_scores[]` | `judges/evolution/agents/variant_scorer.py:103-153` | additive — no schema migration |
| `verify_preview()` Gemini-Flash multimodal QA | `src/generation/image_preview_service.py:373-464` | adapt prompt for layout grading |
| RUBRICS registry pattern | `src/evaluation/rubrics.py:687-712` (MON case) | add new `rendering` domain |
| Templated-domain rubric injection | `judges/evolution/agents/variant_scorer.py:46-72` (`_render_criteria_for_domain`) | reuse for rendering domain |
| R2 + Cloudflare publish scaffold | marketing-audit (PR #45) — `cloudflare-workers/audit-hosting/` | reuse for `freddy autoresearch publish --public` |

## Locked decisions

| # | Decision | Pick | Reasoning |
|---|---|---|---|
| **D1** | Generation strategy | **Hybrid** — templated chrome + LLM-authored section bodies using a constrained primitive library | Section-level layout choices are the right unit of self-improvement. Full LLM-authored is too unbounded; full templated gives up the agent's leverage. |
| **D2** | Rubric placement | **Cross-lane "rendering" rubric domain, opt-in per lane** via new `render_rubric_ids` field on LaneSpec | One source of truth for `RND-1..5`. Reuses templated-domain pattern. Storyboard opts out (it has its own renderer). |
| **D3** | Promotion gate | **Phase 1 recorded-but-ungated; Phase 2 gate after 3+ variants of empirical calibration data** | Calibration unknown at day 1. Same plan, two phases — boundary is empirical not dated. |
| **D4** | Distribution | **Both — R2 public-slug + portal-gated**, single `freddy autoresearch publish` command with `--public` flag | Different jobs (one-time deliverable vs ongoing dashboard). Both reuse the same HTML output. R2 path inherits marketing-audit's PR #45 scaffold. |
| **D5** | Section-element library form | **CSS classes** (`<div class="rprt-callout">…</div>`), NOT web components or custom markdown | Zero new infrastructure. mistune passes raw HTML through. Aligns with how `render_findings()` works today (`src/shared/reporting/report_base.py:297-418`). |
| **D6** | Visual judge placement | **Inside the existing judge service** — extend `variant_scorer.py` to accept screenshot, call Gemini Flash, append RND dimensions to `per_criterion[]` | Keeps a single source-of-truth for scoring. Schema is purely additive. |
| **D7** | Rendering instruction injection | **Post-session subprocess, NOT iterative session prompt** | Iterative sessions run 30-50 turns; embedding render instructions inline causes prompt bloat and turn-saturation. Render is one-shot at session end. |
| **D8** | Print readiness | **Add `@media print` rules to `BASE_CSS` (currently absent)** + Chrome `--print-to-pdf` | `BASE_CSS` has no print rules today; Chrome handles paged media via `--print-to-pdf`. Explicit print CSS gives us page-break control. |
| **D9** | Anthropic SDK call site | **In-process inside the new `render_report.py` subprocess** | `run.py:139` strips `ANTHROPIC_API_KEY` from the runner env. Render subprocess re-instantiates its own client without polluting the runner. |

## Build sequence

> **Note:** Layer A/B/C/D below are **implementation phases**, not the same as the 5 conceptual variability layers (Chrome / Element-Library / Lane-Render-Seed / Per-Session / Within-Render) in the Overview. The conceptual layers describe *what changes at what cadence*; the implementation phases describe *what to build in what order*. Both are useful framings for different audiences.

### Layer A — shared infrastructure (one-shot, no per-lane code)

**A1. Section-element CSS library** — `src/shared/reporting/report_base.py:497-523`
Append to existing `BASE_CSS` — ~16 primitives in two groups:

*Group 1 — content primitives (12)*: `.rprt-prose`, `.rprt-callout` (info/warn/critical/success), `.rprt-key-table`, `.rprt-stat-tile`, `.rprt-stat-grid`, `.rprt-comparison`, `.rprt-evidence-quote`, `.rprt-action-list`, `.rprt-finding-card`, `.rprt-pull-quote`, `.rprt-page-screenshot`, `.rprt-faq-accordion`, `.rprt-citation-card`

*Group 2 — transcript primitives (4, NEW)*: `.rprt-reasoning-trail` (vertical timeline container), `.rprt-beat-card` (single agent-reasoning quote with status: first-move / decide / adapt / hit-failure / recover / ship), `.rprt-pivot-callout` (highlighted moment where the agent changed approach), `.rprt-meta-pattern` (cross-fixture pattern banner — e.g., "this quote appeared in 19/19 iterations")

Plus `@media print { … }` block (page-break-inside, table reflow, hidden-on-print classes).
Effort: **4 hr** design + CSS authoring (was 3 hr; +1 hr for transcript primitives).

**A2. `html_to_screenshot()` helper** — `src/shared/reporting/report_base.py`, sibling to `html_to_pdf()` at line 593+
Mirror `html_to_pdf()` exactly. Default viewport `1280×1600`. Tested working at **1.68s** on this machine.
- Effort: **30 min** copy-paste-modify.

**A3. `WorkflowSpec` field** — `autoresearch/archive/v009/workflows/specs.py:33-44`
One optional field: `render_report: Callable[[Path, str], None] | None = None`. Default `None` = lane opts out.
- Effort: **5 min**.

**A4. Hook wiring** — `autoresearch/archive/v009/runtime/post_session.py:110-135`
Insert 3 lines after `enforce_completion_guard()` on line 121:
```python
render = get_workflow_spec(domain).render_report
if render: render(session_dir, client)
```
- Effort: **10 min**.

**A5. `LaneSpec.render_rubric_ids` field** — `autoresearch/lane_registry.py`
New optional field: `render_rubric_ids: tuple[str, ...] = ()`. Default empty = lane opts out of rendering rubric scoring.
- Effort: **5 min**.

**A6. `RND-1..5` rubric prose** — `src/evaluation/rubrics.py`
Author 5 gradient-anchored prompts (1/3/5 calibration), matching the GEO-1 / CI-1 style:
- `RND-1`: typography & visual hierarchy
- `RND-2`: information density & breathing room
- `RND-3`: print/PDF readiness
- `RND-4`: design-token consistency / no off-brand drift
- `RND-5`: interactivity & evidence linkability (clickable URLs, sortable tables, expandable detail)

Register as `rendering` domain in RUBRICS dict (mirror MON-1..8 pattern at `rubrics.py:969-976`).
- Effort: **1 day** real authoring + calibration loop with sample renders.

**A7. Vision sub-judge** — `judges/evolution/agents/render_judge.py` (new) + integration in `evaluate_variant.py:~1200`
- Read `session_dir/report-screenshot.png`
- Call Gemini Flash with `RND-1..5` prompt (reuse `verify_preview()` pattern from `image_preview_service.py:373-464`)
- Return `[{criterion: "RND-1", score: N, rationale: "…"}, ...]`
- Merge into existing `per_criterion[]` array before aggregation
- Effort: **3 hr** (~80 LOC).

**A8. Transcript extraction pipeline** — `autoresearch/archive/v009/scripts/extract_reasoning.py` (NEW)

Two-stage extraction over `session_dir/logs/iteration_*.log.err`:

*Stage 1 — programmatic (awk/grep, ~10ms per iteration file):*
```python
def extract_beats(log_err_path: Path) -> list[dict]:
    """Returns ordered list of {kind, phase, quote, exec_count, tokens}."""
    # awk pattern: lines after '^codex$' marker, until blank
    # grep pattern: '^exec$' followed by next line for tool name
    # tail: 'tokens used' footer
```

Output schema per iteration: `{iteration: int, phase: str, status: ok|degraded|fail, reasoning_beats: list[str], tool_calls: list[str] (truncated to 200 chars each), token_count: int, pivots: list[{kind, before, after, quote}]}`

*Stage 2 — Opus synthesis:*
Input bundle for the render call:
- All `report.md`, `findings.md`, `session.md`, `report.json` (the structured artifacts, ~50-100KB total)
- Stage-1 extracted beats (~5-10KB structured JSON per fixture)
- Lane render seed prompt
- Section-element library spec
- Output: HTML body fragment using both content primitives AND transcript primitives

**Why two stages:** raw transcripts are 1.3MB+ per fixture run. Sending them whole to Opus is wasteful (most lines are tool result echoes, file paths, system prompt repetitions). Stage 1 distills the substance; Stage 2 composes the report.

Effort: **4 hr** Stage 1 extraction script (~120 LOC) + Stage 2 prompt template integration with existing render_report.py.

**A8.1 Calibration requirements** — surfaced by the 2026-05-08 dry-run on `archive/v009/sessions/geo/nubank/` (full pipeline executed end-to-end in ~5 seconds; rendered artifact at `.superpowers/brainstorm/.../demo/nubank-dryrun.{html,pdf,png}`):

1. **Pivot detection is conservative without a calibration set.** First-pass heuristic (`adapt`-tagged beat preceded by `hit_failure`-tagged beat) found 1 of ~4-5 actual pivots. Production must include: (a) frozen sample transcripts in `tests/fixtures/extract_reasoning/` covering at least one example of each pivot kind, (b) a recall threshold (≥80% of human-marked pivots) the script must hit before merging, and (c) a fallback "always emit `hit_failure → ship` transitions" rule for the cases the primary heuristic misses.

2. **Classifier must classify on the first verb, not on substring matches.** Current heuristic mislabels recovery beats containing the word "failed" (referring to past tense / recorded failures). Example seen in nubank iter 3: *"I have enough for a degraded but real baseline: confirmed cached metadata, confirmed static schema absence, failed rendered/robots/PageSpeed checks"* — classified `hit_failure`, should be `ship`. Production must lead with first-verb / first-clause analysis: *"I have enough"* → `ship`; *"X failed"* → `hit_failure`.

3. **`visibility.json` reads need a typed schema or a single source of truth.** Dry-run script expected `by_engine.chatgpt` but actual key is `summary.chatgpt_citations`. Silent fallback to hardcoded numbers happened to match nubank's session but would corrupt other fixtures. Production must either: (a) declare a Pydantic schema for `visibility.json` and validate at extraction time, OR (b) read citation data through `session.md`'s already-distilled "Evidence Summary" / "Competitive Intel" sections — they're authored by the agent and stable across runs.

4. **Tool-call list must collapse repeated invocations.** Showing all 21 raw exec lines per iteration in the rendered report is too verbose. Production must group by distinct command (e.g., `freddy visibility` shown once with `× 3 calls`), then truncate to the most-recent-N or top-by-novelty.

5. **Stage 1 latency is non-issue.** Measured 30ms total for 5 iterations on this machine. The "~10ms/iteration" estimate from the spec stands. Stage 2 Opus call dominates wall time, not extraction. No action needed — recorded as confirmation.

These 5 calibration requirements ARE the test plan for `extract_reasoning.py`. Acceptance test (§Acceptance below) updates accordingly.

**A9. Cross-fixture AND cross-lane meta-pattern detection** — small post-processing pass in `render_report.py`

Find quotes that appear with high similarity across all fixtures' beats AND across lanes. Cross-fixture candidates within a lane: "I'll read the persisted session state first" (19/19 iterations), "rejected the artifact on structural labels, not content quality" (3/3 GEO fixtures). Cross-lane candidates (validated 2026-05-08): `prompt_builder_failed: sys.modules allowlist violation for ipaddress, urllib, urllib.parse` appears in **at least 3 of 4 lanes** (GEO + COMPETITIVE + MONITORING) — this is an architecture-level finding that the per-lane reports would miss in isolation.

Surface these as `.rprt-meta-pattern` callouts in two places: per-lane cross-fixture synthesis (within one lane's report), AND per-variant cross-lane synthesis (in a higher-level "all 4 lanes" report). They are higher-leverage than per-fixture details because they reveal architectural patterns that apply to every variant.

**Two output modes** for `render_report.py`:
1. **Single-lane mode**: `render_report.py <session_dir> <domain> <client>` → produces one fixture's report (existing contract from C1)
2. **Cross-lane mode (NEW)**: `render_report.py --all-lanes` → walks `archive/v*/sessions/<lane>/` for each of the 4 lanes, picks most recent variant per lane, produces cross-lane synthesis report

Effort: **2 hr** (~50 LOC, simple Jaccard or normalized-edit-distance similarity over beat texts; no embedding model needed) + **1 hr** for the cross-lane walker.

### Layer B — per-lane wiring (4 lanes × ~30 min each)

For each of `geo`, `competitive`, `monitoring`:

**B1. Lane-specific `render_report` callable** in `workflows/{lane}.py`
Add one line to `SPEC = WorkflowSpec(...)`:
```python
render_report=lambda d, c: run_script("render_report.py", str(d), "geo", c),
```

**B2. `render_rubric_ids` on the lane** in `lane_registry.py`
Set to `("RND-1", "RND-2", "RND-3", "RND-4", "RND-5")` per lane.

**B3. `programs/{lane}-render-seed.md`** (new)
Initial seed prompt: section-element library spec + design tokens + lane-specific layout preferences. Meta-agent will edit this between variants.

Storyboard skips Layer B — its existing renderer (`configs/storyboard/scripts/generate_report.py`) is preserved; storyboard's `render_report` field stays `None`.

### Layer C — the render subprocess (one new script, all lanes use it)

**C1. `autoresearch/archive/v009/scripts/render_report.py`** (new, ~250-350 LOC — was 150-200; transcript pipeline grew it)

Contract:
```python
def render_report(session_dir: Path, domain: str, client: str) -> None:
    """Read deliverables + transcripts, call Opus, write report.html + report.pdf + report-screenshot.png."""
```

Steps:
1. Read deliverables: `report.md`, `findings.md`, `*.json`, lane-specific patterns from `LaneSpec.deliverables`
2. **Read agent transcripts**: `extract_reasoning.extract_beats(p)` for each `logs/iteration_*.log.err` (A8 above). Reduces ~1.3MB raw transcript per fixture to ~5-10KB structured JSON.
3. **Detect meta-patterns** across fixtures (A9): cross-fixture quote similarity → `.rprt-meta-pattern` callouts.
4. Read `programs/{lane}-render-seed.md` (if present)
5. Optionally screenshot the analyzed page(s) via Chrome `--screenshot` for embedding
6. Compose the render prompt: data + transcript-extracted beats + meta-patterns + library spec + design tokens + lane render seed
7. Call Anthropic SDK: `Anthropic().messages.create(model="claude-opus-4-7", ...)` — get back HTML body fragment using both content + transcript primitives
8. Wrap with `build_html_document(title, sections=[(name, body)], css_extra=lane_css)`
9. Write `session_dir/report.html`
10. Run `html_to_pdf(html_path, session_dir/"report.pdf")`
11. Run `html_to_screenshot(html_path, session_dir/"report-screenshot.png")`
12. (Optional within-render refinement loop): screenshot → Gemini Flash inline judge → if RND < threshold, refine + retry. Bounded to 2-3 iterations.

Subprocess invocation pattern — mirrors `build_geo_report.py:1-30`. Anthropic client lives entirely inside this script.

- Effort: **5-6 hr** code + render seed prompt v0 (was 3-4 hr; transcript pipeline integration adds ~2 hr).

### Layer D — distribution (D4)

**D1. R2 publish path** — extend marketing-audit's `freddy audit publish` scaffold
- New CLI: `freddy autoresearch publish <variant> <lane> <fixture> [--public]`
- Default: portal-gated. `--public` writes to R2 + returns slug URL.
- Reuses `cloudflare-workers/audit-hosting/` (PR #45)
- Effort: **2 hr**.

**D2. Portal route** — new FastAPI route in `src/api/routers/portal.py`
- `GET /v1/portal/{slug}/reports/{lane}/{variant}/{fixture}` → returns HTML
- Gated by existing `resolve_client_access()` at `portal.py:51-53`
- Effort: **2 hr**.

## Out of scope (explicit deferrals)

- **Phase 2 promotion gate** — D3 phase-2 ships in a separate plan once we have empirical RND distributions across 3+ variants
- **Per-lane `ParallelismProfile` for parallel rendering** — Phase 1 renders serially per lane; if multi-fixture rendering becomes a bottleneck, hook into the existing parallelism framework (plan 2026-05-07-002)
- **Custom markdown plugins for `<rprt-*>` tags** — D5 chose CSS classes; if a constrained-markdown DSL ever proves easier for the agent, that's a separate plan
- **Lane render seed initial authoring beyond v0** — the meta-agent will iterate it from variant 2 onward; v0 is hand-authored once per lane during Layer B
- **Replacing storyboard's existing renderer** — it works, it ships, it stays. Storyboard opts out via `render_report=None`. Future migration is a separate plan if we ever consolidate.

## Risk register

| # | Risk | Mitigation |
|---|---|---|
| R1 | Anthropic API call inside post-session subprocess inflates wall time | Bounded to one Opus call + max 3 refinement retries; cost **~$0.10-0.20 per render** (was ~$0.03 — transcript-extracted beats add ~5-10KB structured input × 3 fixtures = 15-30KB; output is one HTML body ~30-50KB); 8-15s wall time per render |
| R2 | Visual judge becomes flaky if Gemini Flash latency spikes | Cache by HTML hash (32-bit hex); skip vision dimension on Gemini timeout (>20s) and log warning; rendering-quality scores are advisory in Phase 1 anyway |
| R3 | Section-element library bloats over time as agent invents new primitives | Library is human-edited (Layer 2). Agent must compose with what exists; new primitives require deliberate human PRs to `BASE_CSS` |
| R4 | Lane render seed prompt accumulates contradictions across many evolution cycles | Mitigated by the same archive/lineage mechanisms that prevent session-prompt drift today; meta-agent reads frontier-best variant before mutating |
| R5 | Print CSS divergence from screen CSS produces broken PDFs | A2's `html_to_screenshot` runs against the same HTML at the same viewport as PDF; explicit print rules tested with at least 2 fixtures per lane in Layer B |
| R6 | DNS/network unavailability blocks fixture page screenshots inside `render_report.py` | Page screenshots are optional embedded evidence; if Chrome can't reach the URL, the render proceeds without that section. Already observed in v009 (3/3 fixtures lost some live tooling). |
| R7 | **Transcript files (`logs/iteration_*.log.err`) get cleaned up before render runs** | Render must run BEFORE any log-pruning step in `post_session_hooks()`. Validate at A4 wiring time. If log retention policy ever changes, render needs to run synchronously inside the iteration runner instead of post-session — escape hatch documented but not implemented. |
| R8 | **awk/grep extraction breaks if Codex CLI changes its output format** | Stage 1 extraction script is small (~120 LOC) and version-pinned to the Codex CLI version recorded in transcript headers (`OpenAI Codex v0.125.0` line). Add unit tests against frozen sample transcripts. If Codex ever changes its `^codex$` / `^exec$` line markers, Stage 1 returns empty beats and Stage 2 falls back to deliverable-only render with a logged warning. |
| R9 | **Other agent backends (claude-code, opencode) don't store transcripts in the same format** | Multi-provider transcript adapter is out of scope for Phase 1 (Codex CLI only). When other backends become production-active, write per-backend `extract_beats_*` adapters under the same Stage-1 contract. Captured in lineage memory: x-engine port lane will hit this first (D9). |

## Acceptance test (Layer A + Layer B for `geo` only)

The first-runnable test for this plan: re-render v009 mayoclinic GEO session through the production pipeline.

```sh
# 1. Stage 1 extraction must clear the calibration bar (§A8.1)
pytest autoresearch/archive/v009/scripts/tests/test_extract_reasoning.py
# Expected: pivot recall ≥80% on fixtures, classifier first-verb rule passes,
# visibility.json schema validates on all 3 fixtures.

# 2. Run render against existing session artifacts
python autoresearch/archive/v009/scripts/render_report.py \
    autoresearch/archive/v009/sessions/geo/mayoclinic geo mayoclinic

# 3. Verify outputs
test -f autoresearch/archive/v009/sessions/geo/mayoclinic/report.html
test -f autoresearch/archive/v009/sessions/geo/mayoclinic/report.pdf
test -f autoresearch/archive/v009/sessions/geo/mayoclinic/report-screenshot.png

# 4. Visual sub-judge sanity check
curl -X POST http://localhost:7100/invoke/score \
    -H "Content-Type: application/json" \
    -d @<(jq -n --arg sd "autoresearch/archive/v009/sessions/geo/mayoclinic" \
        '{session_ref: $sd, domain: "geo", fixture: {fixture_id: "geo-mayoclinic-atrial-fibrillation"}}')
# Expected: per_criterion[] includes RND-1..5 entries with float scores 0-10
```

**Pre-existing dry-run artifact** (already executed 2026-05-08): `.superpowers/brainstorm/44038-1778186170/demo/nubank-dryrun.{html,pdf,png}`. Generated by `render_dryrun.py` from `extract_reasoning.py` output + nubank session artifacts in ~5 seconds wall time, no Opus call. Use this as the regression baseline for the production pipeline — Stage 2 (Opus) output should be strictly richer than this hand-coded composition, not strictly different.

If this passes for `geo/mayoclinic` AND `nubank` AND `semrush`, Layer B is complete for the GEO lane. Then repeat for `competitive` and `monitoring`.

## Effort summary

| Layer | Subject | Effort |
|---|---|---|
| A1 | CSS section-element library (16 primitives) | 4 hr |
| A2 | `html_to_screenshot()` | 30 min |
| A3 | WorkflowSpec field | 5 min |
| A4 | Post-session hook wiring | 10 min |
| A5 | LaneSpec render_rubric_ids field | 5 min |
| A6 | RND-1..5 rubric prose | **1 day** (intellectual work) |
| A7 | Vision sub-judge | 3 hr |
| **A8** | **Transcript extraction pipeline (NEW)** | **4 hr** |
| **A9** | **Cross-fixture + cross-lane meta-pattern detection (NEW)** | **3 hr** |
| **A10** | **Per-lane composer dispatcher (NEW)** | **2 hr** + 4× per-lane templates ≈ **6 hr** |
| B (×3 lanes) | Per-lane render_report wiring + seed v0 | 1.5 hr/lane = 4.5 hr |
| C1 | render_report.py subprocess (transcript-aware) | 5-6 hr |
| D1 | R2 publish | 2 hr |
| D2 | Portal route | 2 hr |
| **Total** | | **~28 hr code (≈3.5 days) + ~1 day rubric authoring** |

Realistic with review/test cycles: **~4 days engineer time + ~1 day rubric calibration loop = ~5 working days end-to-end.** (Was ~4 days; transcript pipeline added ~6 hr code.)

## References

- `src/shared/reporting/report_base.py:497-633` — chrome + helpers (existing)
- `configs/storyboard/scripts/generate_report.py` — simplest existing precedent
- `src/competitive/pdf.py:43-52` — Jinja2/WeasyPrint sibling pattern
- `autoresearch/archive/v009/runtime/post_session.py:110-135` — hook insertion point
- `autoresearch/archive/v009/workflows/{geo,competitive,monitoring,storyboard}.py` — per-lane spec sites
- `judges/evolution/agents/variant_scorer.py:46-72,103-153` — judge dispatch + templated-domain pattern
- `src/evaluation/rubrics.py` — RUBRICS registry
- `src/generation/image_preview_service.py:373-464` — `verify_preview()` reuse target
- `marketing-audit` PR #45 — Cloudflare/R2 publish scaffold

## Sources

- 4 research agents (2026-05-07) verified all file:line refs against live repo state
- Demo v3 at `.superpowers/brainstorm/44038-1778186170/content/08-demo-v3.html` proves end-to-end feasibility on real v009 data with section-element library v0 (10 primitives, 92KB HTML, 1.92s screenshot, 1.79s PDF)
- Cost estimate (~$0.005/cycle) measured against `verify_preview()` Gemini Flash baseline at 40 calls/cycle
