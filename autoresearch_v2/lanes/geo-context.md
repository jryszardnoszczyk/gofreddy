# Lane: geo — AI-search content optimization

**What this lane does:** evolves the prose at `lanes/geo.md` (this file) so that when it drives a session against a client's website, the session produces optimized page content AI search engines will quote, cite, and recommend. The output of each session is `optimized/<page>.md` deliverables that get scored by the 8 GEO judges.

**Baselines you're trying to beat:**
- v006 search-v1 composite: **7.82** (the visible/training fixture set in `autoresearch/eval_suites/search-v1.json`)
- v009 holdout-v1 composite: **4.77** (the hidden 6-fixture set in `~/.config/gofreddy/holdouts/holdout-v1.json`)

The two metrics differ because they evaluate different fixtures. Both must trend up over time for a keep to be real.

---

## Deliverable contract

The session writes `optimized/<page>.md` files under `sessions/geo/<client>/`. Each file MUST satisfy:

1. **Non-empty `optimized/<file>.md`** — at least one such file with real content (not a placeholder).
2. **`<script type="application/ld+json">` blocks parse** — every JSON-LD block in every optimized file is valid JSON. A broken schema block zeros GEO-8.
3. **`gap_allocation.json` at session root** with at least one entry.
4. **`[FAQ]` marker** OR `## FAQ` / `## Frequently Asked` heading (CQ-2 5-7 self-contained Q&As).
5. **`[INTRO]` marker — literal brackets**. `## Intro` / `## Introduction` fails the structural gate.
6. **≥ 300 words per artifact.** `[HOWTO]`, `[SCHEMA]`, `[TECHFIX]`, `[PRUNE]`, `[FILL]` markers follow the same bracket convention (read by `scripts/build_geo_report.py` when compiling the final report).

If any of these fails, the iter is `checks_failed` — log it and discard.

---

## The 8 GEO judges (your fitness function)

Composite = **geometric mean** of these 8. A zero in any one collapses the fixture; consistency across fixtures (also geometric mean) matters.

1. **GEO-1 Self-contained, quotable answers** — snippet-ready; an AI engine extracts a paragraph without surrounding context.
2. **GEO-2 Specific, verifiable facts** — concrete numbers, named entities, measurable claims. Not vague positioning.
3. **GEO-3 Honest competitive positioning** — *hardest one*. Acknowledge where the client loses. "We're better in every way" = 0. A comparison table showing where competitors genuinely win = scores.
4. **GEO-4 Voice/structure fit** — content matches the page's existing tone and structure, with mechanical placement instructions.
5. **GEO-5 Citability moat** — proprietary methodology, unique data, or depth competitors can't easily replicate. At least one such element per page.
6. **GEO-6 Cross-page coherence** — each optimized page tells a different story. No repeated differentiators, no recycled stats, no duplicate FAQ angles.
7. **GEO-7 Directly answers target queries** — first paragraph answers the primary query head-on.
8. **GEO-8 Technical fixes are real** — schema markup and infra recommendations are specific, valid, actionable. Not boilerplate.

---

## Content quality standards (CQ-1 through CQ-19) — reference, not a checklist

These are quality bars, not gates. The full content-quality reference (the original v006 prose) lives at `autoresearch/archive/v006/programs/geo-session.md` while v1 still exists. Key levers you should treat as load-bearing:

- **CQ-17 AI-tell blocklist** — strip `utilize / leverage / facilitate / streamline / robust / comprehensive / pivotal / seamless / holistic`. Strip filler `absolutely / actually / basically / clearly / really / simply / very / just`. Em-dash heuristic: >1 em-dash per page → rewrite.
- **CQ-DATA** — never include specific citation counts unless `method: 'measured'`; qualitative positioning when data unavailable.
- **Princeton GEO study (KDD 2024) levers (best-to-worst):** citing sources +40%, adding statistics +37%, quotations with attribution +30%, authoritative tone +25%, improve clarity +20%, technical terms +18%, unique vocabulary +15%. Keyword stuffing is actively penalized (−10%).
- **Per-platform citation levers:** ChatGPT content-answer fit = 55% of citation likelihood; Perplexity privileges FAQPage JSON-LD + PDFs; Copilot has a sub-2s load-time threshold; Claude (Brave Search) rewards factual density.

---

## What you CANNOT edit (`readonly_subprefixes` from v1)

- `autoresearch/archive/v006/workflows/geo.py`
- `autoresearch/archive/v006/workflows/session_eval_geo.py`

These are the structural gate functions. Editing them is a scope violation; the alert agent will flag the cross-lane mutation.

You also cannot edit any other `lanes/*.md` file — only this one. And not `tools/`, `harness/`, `judges/`, or `autoresearch.md` (the driver prompt).

---

## What you CAN edit

This file (`lanes/geo.md`). The session prompt is THIS prose. Every change you make to it changes what the session agent does.

Typical mutation surfaces that have worked in v006/v007:
- Reframing the 8 GEO judge criteria (CQ-1..19 levers, Princeton boosts, platform levers).
- Adjusting structural-doc-fact framing (bracket marker conventions).
- Adding new domain knowledge (Corey Haines skill references, schema patterns).
- Tightening the AI-tell blocklist.

Mutation surfaces that have regressed:
- Stripping the bracket-marker convention — sessions stop hitting structural gates.
- Demanding "answer in first 40 words" without the 8-judge composite framing — overfits on GEO-1, drops GEO-3 and GEO-5.
- Removing CQ-DATA → fabricated citation counts → cross-fixture penalty.

---

## Fixture coverage (no content revealed)

- Search-v1 (visible): see `autoresearch/eval_suites/search-v1.json` for fixture_ids only. **Never read the fixture content yourself** — `tools/run_experiment.py` does that under the hood.
- Holdout-v1 (hidden): 6 fixtures in `~/.config/gofreddy/holdouts/holdout-v1.json`. `tools/score_holdout.py` runs them and returns only composite + per-fixture metadata. You never see the fixture contexts.

---

## Recent history pointers (read these before mutating)

- `git log --oneline lanes/geo.md` — the lane's evolution history
- Last ~10 rows of `lanes/geo/results.tsv` — recent attempts including `asi_json` rationale
- `lanes/geo/holdout_results.tsv` — holdout composite trajectory
- `alerts.jsonl` — alert agent flags scoped to this lane
