# How the renderer evolves itself — end-to-end loop

**Branch context:** `feat/render-pipeline-test`. Wired across the
following commits, in order:

1. `programs/render/<lane>.md` files — agent reads these to write the
   highlights HTML dynamically per session.
2. `agent_compose_dynamic_highlights()` — the orchestrator that calls
   the agent against the prompt files.
3. `_aggregate_render_quality()` + `EVOLVE_INCLUDE_RENDER_QUALITY` env
   gate — already present pre-branch, but the gate flipped from
   default-off to default-on in this branch (existing operator
   override `=0/off/false/no/skip` still disables).
4. `render_rubric_ids` set on all 7 lanes (was 5/7 before this branch).

This document explains the loop end-to-end so a reader can predict
what the substrate does + how to nudge it.

---

## The loop

```
                 ┌───────────────────────────────────────────────┐
                 │     1. SESSION RUN (run.py iteration loop)    │
                 │     Agent produces deliverable + transcripts. │
                 └────────────────────┬──────────────────────────┘
                                      │
                                      ▼
        ┌───────────────────────────────────────────────────────────┐
        │ 2. POST-SESSION HOOKS (runtime/post_session.py)            │
        │    → summarize_session writes session_summary.json         │
        │    → render_report.py PRIMARY path:                        │
        │         agent reads programs/render/<lane>.md +            │
        │         programs/render/_base.md + payload, writes the     │
        │         report HTML dynamically. Sanitized + cached.       │
        │    → Chrome --print-to-pdf, Chrome --screenshot.           │
        │    → render_judge.py grades the PNG against RND-1..5,      │
        │         writes render_score.json.                          │
        └────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
        ┌───────────────────────────────────────────────────────────┐
        │ 3. VARIANT EVALUATION (evaluate_variant.py)                │
        │    Across all (lane, fixture) pairs in this variant:       │
        │      - per-domain composite from outer-judge scores        │
        │      - mean render_quality across render_score.json        │
        │      - Composite blend: 0.9 × deliverable + 0.1 × render   │
        │        (when EVOLVE_INCLUDE_RENDER_QUALITY != 0)           │
        └────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
        ┌───────────────────────────────────────────────────────────┐
        │ 4. EVOLUTION DECISION (evolve.py)                          │
        │    Variants with higher composite get promoted. Variants   │
        │    that mutated programs/render/<lane>.md and improved     │
        │    render_quality survive; ones that broke it get pruned.  │
        └────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼  (next iteration)
                              ◄── back to 1
```

---

## What's evolvable

Every file in `<variant>/programs/render/` is mutable by the meta-
agent. That means:

- **`_base.md`** — shared sanitizer reference + editorial principles.
  Mutating this changes what every lane's renderer can do (e.g.
  adding new chart kinds, relaxing the "200 char min" floor,
  introducing a new component class).
- **`<lane>.md` per-lane prompts** — each lane evolves its renderer
  independently. The meta-agent observing that GEO renders with weak
  charts could tweak `geo.md`'s chart guidance and that variant's
  render_quality would either rise or fall — the score signals
  whether the mutation helped.

What's NOT evolvable yet (deliberately — these are the safety floor):

- The sanitizer code (`_sanitize_agent_html` + allowlists).
- The chart-helper Python (`charts_svg.py`).
- The deterministic appendices (tool I/O timeline, evals, transcripts,
  bundle, file tree). These guarantee data transparency regardless
  of what the agent does in highlights.
- `render_judge.py` itself + the `render-rubric.md` (RND-1..5).
  These are the *measurement* — letting the meta-agent evolve the
  judge alongside the renderer would invite reward-hacking.

---

## Operator controls

| Env var | Default | Effect |
|---|---|---|
| `RENDER_BACKEND` | `codex` | Which CLI to spawn for synthesis. `none` / `off` / `skip` disables agent synthesis entirely → renderer falls back to static composers. |
| `AUTORESEARCH_RENDER_DYNAMIC` | unset (on) | Set to `0/off/false/no/skip` to disable the dynamic-renderer path. Falls back to multi-section synthesis. |
| `AUTORESEARCH_RENDER_MULTI_SECTION` | unset (on) | Set to `0/off/false/no/skip` to disable multi-section. Falls back to single-section. |
| `AUTORESEARCH_RENDER_REFINE` | unset (on) | Set to `0/off/false/no/skip` to disable the heuristic-gated single-pass refine. |
| `AUTORESEARCH_AUTO_RENDER` | unset (on) | Set to `0/off/false/no/skip` to disable auto-render entirely in `post_session_hooks` (e.g. for evolution sweeps that don't need to render). |
| `AUTORESEARCH_SESSION_EVENTS` | unset (on) | Set to `0/off/false/no/skip` to disable structured per-event logging (`agent_spawn`, `agent_complete`). |
| `AUTORESEARCH_RENDER_SCORE_IN_EVOLUTION` | (alias) | Same semantics as `EVOLVE_INCLUDE_RENDER_QUALITY` — see below. |
| `EVOLVE_INCLUDE_RENDER_QUALITY` | unset (on) | Set to `0/off/false/no/skip` to skip blending render quality into the variant composite. |
| `RENDER_JUDGE_LANES_ALLOWED` | `geo,competitive,monitoring,storyboard` | Comma list of lanes whose screenshots may be sent to Gemini. Add `marketing_audit` / `x_engine` / `linkedin_engine` only when their fixtures are not customer-PII data. Or set to `all` to bypass. |
| `GEMINI_API_KEY` | unset → stub scores | When unset, `render_judge.py` writes aggregate=0.0 stubs that are filtered out of `_aggregate_render_quality` so they don't dilute the signal. |

---

## How to verify the loop is working

After running an evolution sweep:

```bash
# Per-fixture render scores landed
ls autoresearch/archive/v00X/sessions/<lane>/<fixture>/render_score.json

# Variant aggregate appears in the score JSON
jq .render_quality autoresearch/archive/v00X/scores.json
jq .composite     autoresearch/archive/v00X/scores.json

# Composite difference between variants reflects render-quality delta
jq '.[] | {variant: .variant_id, composite, render_quality}' \
    autoresearch/archive/lineage.jsonl | head
```

If `render_quality` is `null` across variants, check:

1. Are screenshots being captured? (`report-screenshot.png` in
   session_dirs.)
2. Is `GEMINI_API_KEY` set in the evolve environment? (Without it,
   `render_judge.py` writes aggregate=0.0 stubs that get filtered
   out.)
3. Is the lane in `RENDER_JUDGE_LANES_ALLOWED`?
4. Does the lane have `render_rubric_ids` set in `lane_registry.py`?
   (As of this branch, all 7 lanes do.)

---

## Why blend at 10%, not 50%?

Because deliverable quality (the agent did good work) > report quality
(the report communicates the work clearly). A variant that drafts
crisp X posts but renders them through a beige template is more
valuable than a variant that produces visually stunning reports of
mediocre drafts. 10% is enough signal that the renderer-prompts
participate in evolution; not enough that an evolution rewards
"prettier" over "better."

The 10% is in `evaluate_variant.py:1457`:

```python
composite = round(0.9 * composite + 0.1 * normalized, 4)
```

Operators can dial it differently for specific sweeps (e.g. a
"renderer-evolve" sweep with the deliverable judges held constant +
the renderer-prompts as the only mutation surface) by tuning that
number. JR has not greenlit auto-tuning yet.

---

## Risks + how the design handles them

**Reward-hacking ("judge-bait" reports).** The render judge sees a
PNG screenshot, so a variant could overfit to "looks pretty in the
fold-line viewport" without surfacing real signal. Mitigations:

1. The deterministic appendices are NOT scored — they ship verbatim
   and any reviewer can verify the agent's highlights against them.
2. The 10% blend cap means a beautiful-but-empty render can lift the
   composite by at most 1.0 point (5.0 × 2.0 × 0.1 = 1.0). The
   deliverable judges (which are 0-10) can swing 9.0 points. The
   bait floor is fundamentally below the deliverable signal floor.
3. `_aggregate_render_quality` filters stub scores so a variant
   without a real Gemini call can't game the dimension by writing
   fake `render_score.json` files (the helper requires aggregate > 0).

**Prompt-evolution destabilising the renderer.** A meta-agent could
mutate `_base.md` in a way that breaks the sanitizer contract (e.g.
telling the agent to use `<style>` blocks). Mitigations:

1. The sanitizer is unchanged — anything outside the allowlist is
   silently dropped at sanitize time. A bad prompt produces empty
   output → falls back to multi-section → falls back to static
   composer. Worst case: the variant renders with the legacy static
   composer, scores low on render_quality, gets pruned.
2. The base file's allowlist reference is the *contract*; mutations
   that misrepresent it produce sanitizer-stripped output that scores
   poorly. The loop self-heals.

**Cost.** The dynamic-renderer adds 1 agent call per session
(plus optional refine = 2). At codex CLI rates (~$0.05-0.10 per call)
that's $0.10-0.20 per session. At 5 lanes × 4 fixtures = 20 sessions
per variant, that's $2-4 per variant. For typical evolutions of 4-8
variants per sweep, ~$10-30 per sweep beyond the existing baseline.
Cache hits (when payload-hash matches) reduce this to near-zero on
re-renders.

---

## Path C — the next-tier loop (NOT shipped in this branch)

A natural follow-up: per-section render judging. Right now the
RND-1..5 rubric grades the *whole* screenshot. A section-level
judge would grade each `<div class="rprt-meta-pattern">` block
independently and feed the lowest-scoring section back into the
self-refinement loop. That'd close the gap between "the report is
good overall" and "section X specifically needs work."

Plumbing-wise:

1. New rubric file: `programs/render-section-rubric.md` (DTP-1..6
   from `docs/data-transparency-rubric-proposal.md`).
2. Extend `render_judge.py` with `--per-section` mode that takes a
   list of meta-pattern blocks and grades each.
3. Feed per-section scores into the self-refinement loop's heuristic
   gate so a low-scoring section triggers refine even when the
   heuristics pass.
4. Aggregate per-section scores into a per-render rollup that
   complements RND-1..5.

Defer until JR signals — this would 2-3× the judge cost and the
current heuristic gate already catches the common shape failures.
