# Data-transparency rubric proposal — DTP-1..6

**Status:** Proposal. Not implemented in the production substrate.
Awaiting JR review before wiring into `autoresearch/archive/v00X/workflows/session_eval_*.py`.

**Branch context:** `feat/render-pipeline-test`. Sibling deliverable to
`docs/render-pipeline-test-2026-05-08.md` (the gap audit).

---

## 1 · Why a rubric

The substrate already grades:

- **Per-artefact judges** (X-1..X-6 for x_engine; LI-1..LI-6 for
  linkedin_engine; MA-1..MA-9 for marketing_audit, etc.) — score the
  *deliverable*.
- **Render-quality sub-judge** (RND-1..5 in `scripts/render_judge.py`) —
  Gemini Flash grades the rendered PNG screenshot for typography,
  hierarchy, density.

Neither grades whether a reviewer can answer **"what did the agent do,
what did it consider, what did it decide?"** purely from the rendered
report. That's the data-transparency dimension. Without it, the
evolution loop optimises for cleaner final deliverables (artefact
judges) and prettier reports (render-quality judge) but rewards
*hiding* the agent's reasoning — a slick render that surfaces only the
verdict scores higher than a transparent render that shows three
retries and the cached eval JSON. That's wrong: a reviewer who needs to
distinguish "the agent thought hard" from "the agent rolled the dice
and got lucky" loses the signal.

A `data_transparency` rubric inverts that: a variant that surfaces its
reasoning, eval JSONs, retries, and source data scores higher.
Equivalent final deliverable + better transparency = stronger evolution
candidate.

---

## 2 · The 6 dimensions (DTP-1..6)

Each scored 1–10. Composite = mean. The dimensions intentionally mirror
the gap categories surfaced in the audit so a render fix maps to a
rubric improvement.

### DTP-1 · Conversation visibility

> Can a reviewer read the agent's full thinking — every reasoning beat,
> every tool call, every retry — without leaving the rendered report?

| Score | Signal |
|-------|--------|
| 1–2   | No transcripts surfaced. Just a verdict + a deliverable. |
| 3–4   | Transcript appendix exists but truncated to <20 KB total; per-iteration breakdown missing. |
| 5–6   | All `iteration_*.log.err` (or `multiturn_session.log.err`) accessible at ≥64 KB / file with per-file `<details>`; reasoning-beat preview ≥6 beats. |
| 7–8   | All beats per iteration accessible (open-by-default first 6, expandable for the rest); tool calls + reasoning labelled and grouped. |
| 9–10  | Every beat + every tool I/O visible; retries called out; pivots highlighted; agent's prompt (`session.md`) rendered alongside response. |

### DTP-2 · Evaluation visibility

> Can a reviewer see every judgement the substrate made on every artefact?

| Score | Signal |
|-------|--------|
| 1–2   | No eval JSON surfaced. Headline scores only. |
| 3–4   | Eval scores in stat tiles, no underlying critique text. |
| 5–6   | One representative eval JSON dumped; per-criterion scores visible. |
| 7–8   | Every `evals/*.json` + `*_eval.json` + `eval_feedback.json` rendered in `<details>`; per-criterion + KEEP/REVISE decisions explicit. |
| 9–10  | Above + diff against prior session's eval (when present); cached evaluator output (`.last_eval_cache.json`) labelled and shown. |

### DTP-3 · Source-data visibility

> Can a reviewer see what input the agent worked from?

| Score | Signal |
|-------|--------|
| 1–2   | No source data surfaced. |
| 3–4   | Source label only ("ran against X domain"). |
| 5–6   | First N source files surfaced inline, rest dropped silently. |
| 7–8   | All source files surfaced (inline OR `<details>` for bulk); `session.md` (the prompt) rendered. |
| 9–10  | Above + read-only invariants (e.g. `programs/references/voice.md` for x_engine) surfaced + diffed against prior runs. |

### DTP-4 · Decision-trail visibility

> Can a reviewer reconstruct every KEEP / DISCARD / REVISE decision the
> agent and substrate made, with the reasoning?

| Score | Signal |
|-------|--------|
| 1–2   | Final verdict only. |
| 3–4   | Status transitions in results.jsonl rendered as a flat ledger. |
| 5–6   | Per-iteration phase + status table; pivots called out. |
| 7–8   | Above + per-artefact decision (KEEP/REVISE) + completion-guard output explicit; `eval_summary.draft_decisions` rendered when present. |
| 9–10  | Above + cross-iteration decision diff (what changed in the agent's plan between iter N and N+1). |

### DTP-5 · Intermediate-artefact visibility

> Can a reviewer see things the agent considered but didn't ship?

| Score | Signal |
|-------|--------|
| 1–2   | Final deliverable only. |
| 3–4   | Some subdir contents inline (typically top 3–8 files; rest dropped). |
| 5–6   | All subdir files accessible (inline + `<details>`); content truncated but every file's existence is visible. |
| 7–8   | Above + content cap raised so the typical file fits without truncation; cached subprocess output (`.render_synthesis_cache/`) surfaced when present. |
| 9–10  | Above + dot-prefixed cache/state files (`.last_eval_cache.json`, `.progress_snapshot`) explicitly listed in an "intermediate state" appendix. |

### DTP-6 · Navigation + signposting

> Once everything is rendered, can a reviewer actually find the thing
> they're looking for?

| Score | Signal |
|-------|--------|
| 1–2   | Wall-of-text dump; no headers; no structure. |
| 3–4   | Top-level sections exist but no in-page TOC; `<details>` summaries unlabelled. |
| 5–6   | Per-section headings; `<details>` summaries include file names; counts present. |
| 7–8   | Every `<details>` summary includes name + size in KB so a reviewer knows whether expansion is small or huge before clicking. |
| 9–10  | Above + a top-level "Map of this report" section that lists every panel with a page-anchor link; per-section anchor IDs stable across re-renders. |

---

## 3 · Composite scoring

```
data_transparency = mean(DTP-1, DTP-2, DTP-3, DTP-4, DTP-5, DTP-6)
```

Hard floor: a variant scores **0** on data_transparency if the report
fails to render at all (no `report.html` produced). A render that
crashes mid-way and produces partial HTML scores against the rubric
normally — the goal is to surface failure modes, not to gate them.

---

## 4 · Where this fits in evolution

Three integration shapes, ranked by how invasive:

### 4a · Sub-judge (preferred)

Add `scripts/data_transparency_judge.py` — mirrors `render_judge.py` but
takes `report.html` (not the screenshot PNG) and a copy of `session_dir/`
on disk. Issues a single Gemini / Claude call with:

- the rendered HTML
- a summary of what's in `session_dir/` (file tree + sizes)
- the DTP-1..6 rubric prose

Returns one JSON: `{DTP-1: 7, ...rationale_per_criterion: ...}`.

post_session_hooks runs it after `render_report.py`. Lane registry
opt-in via `data_transparency_rubric=True` so lanes that don't want the
judge skip it.

### 4b · Evolution-loop input

`evaluate_session.py` (the canonical session evaluator) already aggregates
per-criterion judge scores into a composite. Adding `data_transparency`
as one more dimension lets the evolution loop reward variants that
render their reasoning more completely. Weighting can be tuned per-lane.

### 4c · Direct rubric in artefact judges (NOT recommended)

Could fold "did the deliverable expose its reasoning" into the existing
X-1..X-6 / MA-1..MA-9 / etc. rubrics. Don't: it conflates *deliverable
quality* with *substrate transparency*. A great X-engine draft is
laconic; a great rendered report is verbose. The two rubrics need to
score independently.

---

## 5 · Risks + mitigations

| Risk | Mitigation |
|------|------------|
| Judge-bait: variants surface huge logs to score high without adding signal | DTP-6 (signposting) penalises wall-of-text. The rubric prose explicitly says "all bytes accessible" — accessible ≠ defaulting to open. A 5 MB transcript dumped inline scores poorly on DTP-6 even if DTP-1 is 10. |
| Cost: an extra judge call per session | Sub-judge runs once per session (post-hook), not per-iteration. ~$0.05–0.20 / session at Gemini Flash rates. Gated per-lane via `data_transparency_rubric=True` so evolution sweeps that don't need it can skip. |
| Render bytes balloon: HTML grows to 5–10 MB per session | `<details>` defaulted-closed on transcripts; PDF only prints opened sections; HTML carries everything. Chrome's PDF backend tolerates this shape. |
| Judge instability: same render scores 6 vs 8 across runs | Cache the judge output by sha256 of rendered HTML — same HTML, same score. Already the cache pattern used elsewhere in render_report.py for the Stage-2 synthesis cache. |

---

## 6 · Reviewer instructions (when JR reads this)

The decision JR needs to make:

1. **Greenlight the rubric prose** above? Or revise dimensions?
2. **Greenlight integration shape 4a** (sub-judge), 4b (evolution input),
   or both?
3. **Lane opt-in**: which lanes ship with `data_transparency_rubric=True`
   first? Recommend: x_engine + linkedin_engine first (smallest sessions,
   tightest signal), then geo, then the rest.
4. **Composite weight in evolution scoring**: should data_transparency
   weight 1× the per-artefact rubric, 0.5×, 0.2×? Recommend starting at
   0.2× so a variant with a marginally better deliverable still beats a
   variant with a great render but worse work.

The implementation cost is small (one new judge script + lane registry
flag + evaluate_session aggregation). The substrate change is large
because it changes what evolution rewards. Hence: review before wiring.
