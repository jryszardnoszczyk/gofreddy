# Render-pipeline live-validation report — 2026-05-08

First end-to-end validation of the dynamic-renderer pipeline against
real session_dirs. All 7 lanes verified.

**Backend:** `RENDER_BACKEND=codex` · `RENDER_MODEL=gpt-5.5` · timeout
180s. Claude backend was attempted first but the local `claude -p`
subprocess returned "Not logged in" — operator-side prereq added to
the runbook (`claude login` once per machine). The codex backend was
authenticated and produced clean output for every lane.

## Per-lane results

| Lane / fixture | Wall time | Dynamic-highlights | report.html | Components rendered |
|---|---|---|---|---|
| competitive · figma | 41 s | 7 263 chars | 2.5 MB | spotlight + stat-grid + table + bar-chart SVG + evidence-row + action-list |
| geo · ahrefs | 43 s | 6 497 chars | 7.0 MB | hero-headline + 5 sub-sections + 6 stat-tiles + bar-chart SVG + 3 actions |
| monitoring · Lululemon | 2 m 11 s | 4 021 chars | 3.5 MB | spotlight (loudest anomaly) + 5 stat-tiles + interpretation-risk + 3 actions + cross-story pattern + QA result |
| storyboard · Gossip.Goblin | 36 s | 6 005 chars | 908 KB | session-status + production-funnel + spotlight + pattern evidence + blocker + next-move + chart SVG |
| marketing_audit · Anthropic | 40 s | 7 149 chars | 3.3 MB | spotlight + pull-quote + 5 stat-tiles + bar-chart SVG + 3 actions |
| x_engine · jr | 39 s | 6 854 chars | 542 KB | session-at-a-glance + reviewer-headline + cohort-shape + draft-spread + editorial-constraint + 2 chart SVGs + draft-inventory |
| linkedin_engine · jr | 34 s | 3 926 chars | 510 KB | usable-package headline + draft-cohort + hashtag-adherence + chart SVG |

**Total wall time:** ~6 min 4 s for all 7 renders. Lululemon was the
slow outlier (rich mentions + anomalies + synthesized payload).

## Component density across lanes (in highlights body, not appendices)

| Lane | SVG charts | Spotlights | Pull-quotes | Stat-tiles | Action rows |
|---|---|---|---|---|---|
| geo / ahrefs | 1 | 1 | 0 | 6 | 3 |
| monitoring / Lululemon | 0 | 1 | 0 | 5 | 3 |
| storyboard / Gossip.Goblin | 1 | 1 | 0 | 6 | 3 |
| marketing_audit / Anthropic | 1 | 1 | 1 | 5 | 3 |
| competitive / figma | 1 | 1 | 1 | 5 | 3 |
| x_engine / jr | 2 | 1 | 0 | 5 | 0 |
| linkedin_engine / jr | 1 | 1 | 0 | 5 | 0 |

Every lane has at least one spotlight + a stat grid. 6/7 have at least
one chart. 5/7 have action rows (the 2 draft-engines correctly skip
actions — drafts ARE the deliverable). The agent dynamically picked
the right component mix per lane.

## Editorial sample — monitoring/Lululemon highlights body

> **↳ loudest anomaly** — Measurement silence is the lead story. Watchlist
> LOW confidence. For 2026-04-27 through 2026-05-03, Lululemon monitoring
> returned 0 mentions, 0 fetched records, 0 source platforms, 0 daily
> sentiment buckets, and no themes. This is not evidence of calm sentiment
> or brand stability; it is an evidence gap that must be validated before
> the digest is used for market interpretation.
>
> **↳ interpretation risk** — Suppress the displayed 100.0% SOV value. The
> SOV response reports Lululemon at 100.0%, but the underlying counts are
> Lululemon 0, Nike 0, and Athleta 0. That makes the percentage a
> zero-denominator artifact, not a competitive-advantage signal.
>
> **↳ top action this week**
>   1. Validate ingestion health within 24 hours. Monitoring Ops should
>      check source connectors, monitor configuration, API permissions,
>      pagination, date boundaries, and timezone handling for 2026-04-27
>      through 2026-05-03. If healthy, classify the week as confirmed
>      low public signal for configured coverage; if faulty, backfill
>      before distribution.
>   2. Remove zero-denominator competitive language today.
>   3. Run adjacent-window recovery checks within 48 hours of validation.

This is editorial-quality writing the agent produced from the raw
session data. Specific numbers, specific timeframes, specific
operational owners — not generic prose.

## Data-transparency appendices verified present in every render

| Section | Present in all 7? | Notes |
|---|---|---|
| Findings (parsed from findings.md) | yes | |
| Investigation trail (reasoning beats) | yes | |
| Phase ledger (results.jsonl) | yes | |
| Per-artefact decisions | yes (when eval_summary or results.jsonl has decision fields) | |
| Session evaluator outputs (every *_eval.json) | yes (when evals exist) | |
| Tool I/O timeline | yes | per-iteration table with kind badges + expandable full output |
| Files the agent read | yes | dedup'd path list with on-disk previews |
| Prompt the agent received (session.md) | yes | |
| Intermediate state (.last_eval_cache, .progress_snapshot) | yes (when present) | |
| Agent transcripts (.log.err full) | yes | 5 MB safety valve only — full files inline otherwise |
| Phase persistence summary (.log) | yes | |
| Session bundle (tar.gz) + per-file download tree | yes | |
| Session event timeline (events.jsonl) | only on sessions newer than the events.jsonl wiring | expected |

## Issues surfaced + addressed inline

1. **Claude CLI "Not logged in" in subprocess** — caught on first live
   render attempt with `RENDER_BACKEND=claude`. Operator prereq
   documented; flag pattern updated to match the proven
   `src/evaluation/judges/sonnet_agent.py` shape (`--bare
   --dangerously-skip-permissions --output-format text`). After the
   user runs `claude login` once on their machine, the claude backend
   will work in subprocess context.

2. **Stale .render_synthesis_cache entries** — two of the existing
   session_dirs (Lululemon, Anthropic) had pre-existing 0-byte cache
   files that triggered a "could not load" warning. Non-fatal; the
   cache miss caused a fresh agent call and the new output cached
   over the stale entry. Addressed in commit `f892a6b` already (silent
   on empty JSON).

3. **No issues with the dynamic-renderer prompts** — every lane's
   `programs/render/<lane>.md` produced rich, lane-appropriate output
   on the first try. The exemplars and editorial principles from
   `_base.md` carried through as expected.

## What's NOT yet verified in this run

- **`claude` backend end-to-end** — blocked on the operator running
  `claude login`. The flag pattern is now correct; once authenticated,
  it should produce equivalent output to codex.
- **Live evolution sweep with `EVOLVE_INCLUDE_RENDER_QUALITY=1`** —
  not run; would require a real evolve cycle. The wiring is in place
  and the per-fixture render scores aggregate correctly per the unit
  tests in `tests/autoresearch/test_render_quality_in_evolution.py`.
- **PDF visual quality** — the 7 PDFs landed at ~150-500 KB each
  (slim-PDF policy holds; full-data HTML carries 0.5-7 MB). Visual
  inspection in a PDF viewer was not part of this loop — the HTML
  structural checks passed and the print CSS rules were unchanged.

## Conclusion

The dynamic-renderer pipeline is production-ready for codex backend.
Claude backend is one operator command (`claude login`) away. Every
lane's renderer-prompt produced informative output that surfaces
specific numbers, lane-appropriate component mix, and inline charts
where quantitative signal warranted them.

The deterministic appendices (~15 transparency sections including the
session bundle + per-file file tree) shipped on every render alongside
the agent-authored highlights, so "all the raw data we got" is
exposed in every report.
