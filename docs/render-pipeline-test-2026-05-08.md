# Render-pipeline data-completeness audit — 2026-05-08

**Branch:** `feat/render-pipeline-test` (worktree at `.worktrees/render-pipeline-feature`)
**Author:** rendering-pipeline agent
**Vision under test:** *radical data transparency* — every rendered report
should let a reviewer answer "what did the agent do, what did it consider,
what did it decide?" without opening a single file in `session_dir/`.

This document is structured as a per-lane gap analysis. It is the foundation
of every code change that follows in this branch: each composer extension /
new composer is justified by a numbered finding here.

---

## 1 · Headline numbers (before)

Total bytes rendered per session vs total session_dir bytes:

| Fixture                     | session_dir | report.html | % surfaced |
|-----------------------------|-------------|-------------|------------|
| geo/ahrefs                  | 9.1 MB      | 144 KB      | ~1.6%      |
| competitive/figma           | 2.6 MB      | 119 KB      | ~4.6%      |
| monitoring/Lululemon        | 3.1 MB      | 135 KB      | ~4.4%      |
| storyboard/Gossip.Goblin    | 944 KB      | 33 KB       | ~3.5%      |
| marketing_audit/Anthropic   | 2.7 MB      | 122 KB      | ~4.5%      |

**~95–98% of the bytes the agent produced are not in the rendered report.**
Most of the unsurfaced material is the agent's own conversation — codex /
claude transcripts in `logs/iteration_*.log.err` or `logs/multiturn_session.log.err`.

The current `build_transcripts_appendix` (render_report.py:235) caps each
log file at **12 KB** (head-half + tail-half). Real iteration logs run
40 KB → 1.1 MB; the truncation throws away **>99%** of the largest files.

---

## 2 · Per-lane gap analysis

For each lane I open one fixture, list what's in the report, list what's
in `session_dir/` but NOT in the report, then call out the conversation gap.

### 2.1 GEO · `geo/ahrefs`

session_dir contents (top-level):
```
competitors/  evals/  findings.md  gap_allocation.json  logs/
optimized/    pages/  report.json  report.md  results.jsonl
session.md    session_summary.json verification-schedule.json
```

**Currently surfaced** (`compose_geo`, render_report.py:248):
- Hero + meta strip + 4-tile stat grid
- gap_allocation.json first allocation only
- report.json: rec_blocks (top 8), top_questions (10), top_headings (10),
  offsite_domains (8)
- visibility.json summary (3 engines)
- pages/ — top **5** of N pages, per-page small fields
- optimized/*.md — first **2** files, **1500 chars** each
- findings.md (parsed)
- reasoning trail — capped at **6 reasoning beats / iteration**
- phase ledger from results.jsonl (notes truncated to 300 chars)
- transcripts appendix — `*.log.err` files capped at 12 KB each

**Present in session_dir but NOT in report:**
- `evals/optimized-*.json` (3 files) — judge per-file critiques. **DROPPED**.
- All pages beyond 5 (none in this fixture, but composer caps at 5 silently)
- All optimized/*.md beyond 2; the truncated content of the 2 it does include
- `verification-schedule.json` — never opened
- `competitors/*` (~150 KB of HTML/JS samples) — never surfaced
- `report.md` (raw deliverable) — never surfaced
- `session.md` — never surfaced (this is the *prompt* the agent ran against;
  highest-signal context)
- **The agent transcripts:** `logs/iteration_005.log.err` is 1.1 MB; the
  appendix renders 12 KB of it. ≥98% of the agent's reasoning + tool I/O
  is silently dropped.
- The reasoning-trail extractor finds (typically) **30–80 beats per iteration**;
  the renderer caps the display at **6 per iteration**. ≥85% of beats
  silently dropped.

### 2.2 COMPETITIVE · `competitive/figma`

session_dir contents:
```
analyses/  brief.md  competitors/  eval_feedback.json  findings.md
logs/  results.jsonl  session.md  session_summary.json
```

**Currently surfaced** (`compose_competitive`, render_report.py:411):
- Hero + 4-tile stats
- `brief.md` (first 4000 chars)
- competitors/*.json — top **8** files, top 6 fields each
- analyses/* — top **6** files, **2400 chars** each, in `<details>`
- findings + reasoning trail + phase ledger + transcripts (same caps as GEO)

**NOT surfaced:**
- `eval_feedback.json` — completion-guard / evaluator output. **DROPPED**.
- Anything past the 8th competitor / 6th analysis
- analyses content beyond 2400 chars
- session.md (the prompt) — never surfaced
- Same 12 KB / 6-beats per iteration gaps as GEO

### 2.3 MONITORING · `monitoring/Lululemon`

session_dir contents:
```
anomalies/  digest.md  digest_eval.json  evals/  findings.md
logs/  mentions/  recommendations/  results.jsonl
session.md  session_summary.json  stories/  synthesized/
```

**Currently surfaced** (`compose_monitoring`, render_report.py:502):
- Hero + 4-tile stats
- `digest.md` (first 5000 chars)
- mentions/*.json — top **8** files, JSON pretty-print to 1200 chars per file
- anomalies/*.json — same caps
- recommendations/*.md — top **4** files, **2400 chars** each
- synthesized/*.md — same
- findings + reasoning trail + phase ledger + transcripts (same caps)

**NOT surfaced:**
- `digest_eval.json` — judge feedback. **DROPPED**.
- `evals/*.json` — per-mention judge passes. **DROPPED**.
- `stories/*.json` — clustered story bundles. **DROPPED** entirely (no
  composer branch reads `stories/`).
- session.md — never surfaced
- mentions / anomalies / recommendations content beyond the cap (whole
  files past index 8 / 4)

### 2.4 STORYBOARD · `storyboard/Gossip.Goblin`

session_dir contents (real fixture, not the stalled TechReview):
```
clips/  evals/  findings.md  frames/  logs/  patterns/
results.jsonl  session.md  session_summary.json
storyboards/  stories/  .last_eval_cache.json
.progress_snapshot
```

**Currently surfaced** (`compose_storyboard`, render_report.py:613):
- Hero + 4-tile stats
- `storyboards/*.json` — all of them, with scenes table (capped at 20 scenes/sb)
- findings + reasoning trail + phase ledger + transcripts

**NOT surfaced:**
- `stories/*.json` — story selections (5 files). **DROPPED entirely**.
- `patterns/*.json` — creator-pattern analyses (typically 5–6 files,
  including `creator_synthesis.json`). **DROPPED entirely**.
- `evals/story-*.json` — per-story judge critiques (5 files). **DROPPED**.
- `clips/`, `frames/` — agent-generated keyframes / clip metadata. **DROPPED**.
- `.last_eval_cache.json` — the canonical session-level eval. **DROPPED**.
- `.progress_snapshot` — multi-iteration progress markers. **DROPPED**.
- session.md — never surfaced
- `extract_reasoning.py` only globs `iteration_*.log.err`; storyboard sessions
  use **`multiturn_session.log.err`** → reasoning-trail extraction returns
  zero beats. The transcripts appendix DOES catch the .err file (its glob is
  `*.log.err`), but the structured beat extraction silently degrades.

### 2.5 MARKETING_AUDIT · `marketing_audit/Anthropic`

session_dir contents:
```
acquisition/  experience/  findability/  narrative/
eval_feedback.json  findings.md  lens_outputs/  logs/
phase0/  results.jsonl  session.md  session_summary.json
```

**Currently surfaced** (`compose_marketing_audit`, render_report.py:714):
- Hero + 4-tile stats incl. `Has Stage-5: yes/no` flag
- IF Stage-5 mirror present: only a pointer card. The substrate detects this
  via `.stage5_mirror` marker file; the autoresearch composer DOES NOT
  overwrite report.html in that case (defended at run() line 1244).
- IF NOT mirror: the 4 agent subdirs (findability/narrative/acquisition/
  experience), top **3** files each, JSON to **1200 chars**.
- findings + reasoning trail + phase ledger + transcripts

**NOT surfaced:**
- `eval_feedback.json` — completion guard / evaluator output. **DROPPED**.
- `phase0/` — pre-discovery artefacts (phase0_meta.json, dictionary, sources).
  **DROPPED entirely.**
- `lens_outputs/` — Stage-1 lens-pre-pass outputs (visibility_summary,
  site_evidence). **DROPPED entirely.**
- All four agent subdirs past the top-3 (typically 4–6 files each)
- session.md — never surfaced
- Same 12 KB / 6-beats transcript gaps

### 2.6 X_ENGINE — *no composer*

`autoresearch/archive/v007-curated/sessions/x_engine/jr/` contents:
```
.progress_snapshot  angles/  drafts/  logs/  results.jsonl
session_summary.json
```

**Surfaced:** nothing. `render_report.py:COMPOSERS` has no `x_engine` entry;
`cli/freddy/commands/autoresearch.py:render` rejects the lane at the
allowlist (line 73). A reviewer cannot use `freddy autoresearch render` at
all for this lane. **0% surfaced.**

Artifacts the composer needs to surface:
- `drafts/<draft_id>.md` — YAML frontmatter (draft_id, angle_id, platform,
  length_bracket ∈ {sharp, build, case_study}, char_count, voice_pillar,
  hashtags) + `[BODY]/[BODY]` + `[META]/[META]` (hook, authority_anchor,
  specific_number, attribution).
- `drafts/<draft_id>.eval.json` — per-draft judge passes (X-1..X-6,
  KEEP/REVISE decisions).
- `angles/<angle_id>.json` — the angle the agent generated drafts from.
- `logs/multiturn_session.log.err` — full agent conversation.
- The shared voice substrate (`programs/references/voice.md`) — the
  invariant the agent's lived-work claims must trace to.

### 2.7 LINKEDIN_ENGINE — *no composer*

Same shape as x_engine. Brackets: `short_take` (500–900 chars),
`thought_leader` (1500–2500), `case_study` (2500–3000). [META] requires
all X keys plus `hashtags`.

**0% surfaced.** Same wiring gap.

---

## 3 · Cross-lane gaps (apply to every composer)

These are NOT lane-specific. They affect every report.

| # | Gap | Severity | Fix |
|---|-----|----------|-----|
| C-1 | `logs/*.log.err` truncated at 12 KB (head+tail). One iter is 40 KB → 1.1 MB. ≥98% dropped on the largest files. | **HIGH** | Raise per-file cap to 64 KB; render each iteration as its own `<details>` panel (don't truncate to head+tail when displayed inside an expandable that defaults closed). Optionally split very large logs into per-codex-block sub-`<details>`. |
| C-2 | reasoning-trail capped at 6 beats/iteration (render_report.py:179); typical iteration has 30–80 beats. | **HIGH** | Show **all** beats in `<details>` per iteration; show first 6 inline (current behaviour) as summary; full list under "show all". |
| C-3 | `extract_reasoning.py` only globs `iteration_*.log.err`. Storyboard + x_engine + linkedin_engine use `multiturn_session.log.err`. | **HIGH** | Extend extractor to glob `multiturn_session.log.err` too; treat it as a synthetic single iteration with phase=`multiturn`. |
| C-4 | `session.md` (the *prompt the agent received* — system message + program + runtime context) is in every session_dir but rendered in zero composers. This is the highest-signal context for "what was the agent asked to do?". | **HIGH** | Add a top-level `<details>` "## What the agent was asked to do" with the full session.md, near the hero. |
| C-5 | `session_summary.json` is read for header stats but never rendered in full; `eval_feedback.json` and `digest_eval.json` are completely skipped. | **MED** | Add a "Session evaluator outputs" section that dumps every `*_eval.json` and `eval_feedback.json` in `<details>`. |
| C-6 | per-lane `evals/*.json` (geo, monitoring, storyboard) are skipped by every composer. These are the judge feedback per artefact — KEEP/REVISE decisions. | **MED** | Generic helper that walks `session_dir/evals/` and emits one `<details>` per file. |
| C-7 | All composers cap subdir file counts (top 5 / 6 / 8 / etc) — content past the cap is silently dropped, no `+N more not shown` indicator. | **LOW** | Replace silent-cap with footer: "showing 5 of N · expand to render rest" — and *render the rest* in a closed-by-default `<details>`. |
| C-8 | `.last_eval_cache.json`, `.progress_snapshot`, `.render_synthesis_cache/` — the agent's intermediate/cached reasoning — never surfaced. Often interesting (cache shows what the agent retried). | **LOW** | Optional appendix `<details>` for "Session intermediate state (`.dotfiles`)"; closed by default. |

The "expandable by default" pattern (`<details>` + `<summary>`) is what
makes "render everything" practical. PDF rendering preserves `<details>`
state (Chrome prints them as the page sees them; default-open `<details>`
print everything; default-closed print only the summary). For PDF we
default-open the structured sections (findings, evals) and default-close
the raw transcripts so the printed PDF stays under ~50 pages while the
HTML carries everything.

---

## 4 · After-state target

Every composer:

1. Renders **session.md** as a top-level expandable "what the agent was asked to do".
2. Renders **all reasoning beats per iteration** (current 6-beat preview as
   the open summary; full list inside `<details>`).
3. Renders **all `*.log.err` files** with per-file cap of 64 KB inside
   per-file `<details>`. Uses both `iteration_*` and `multiturn_session*`
   globs so storyboard / x_engine / linkedin_engine work.
4. Renders **every `*_eval.json` / `eval_feedback.json`** as one `<details>`
   per file.
5. Renders **every JSON / MD subdir** the lane writes — current top-N caps
   become "first N inline + rest under `<details>`" so nothing is dropped.
6. Adds **x_engine** + **linkedin_engine** composers + extends the freddy CLI
   allowlist to all 7 lanes.
7. Auto-render trigger: confirms x_engine + linkedin_engine WorkflowSpec gets
   `render_report=` set so post_session_hooks fires automatically. Adds
   `AUTORESEARCH_AUTO_RENDER=0` env-skip at the post-session-hook level so
   operators can disable for evolution sweeps.
8. Concurrent-render safety: both Chrome subprocess invocations get
   `--user-data-dir=$(mktemp -d)` so parallel renders don't collide on
   `~/Library/Application Support/Google/Chrome/Default`.

Target after-state numbers (rough projection based on per-fixture content):

| Fixture                     | report.html before | report.html projected | % surfaced |
|-----------------------------|--------------------|----------------------|------------|
| geo/ahrefs                  | 144 KB             | ~2.5 MB              | ~28%       |
| competitive/figma           | 119 KB             | ~700 KB              | ~27%       |
| monitoring/Lululemon        | 135 KB             | ~900 KB              | ~29%       |
| storyboard/Gossip.Goblin    | 33 KB              | ~600 KB              | ~63%       |
| marketing_audit/Anthropic   | 122 KB             | ~700 KB              | ~26%       |

The remaining 70% is mostly transcript bytes past the 64-KB-per-file cap
and the binary `competitors/` HTML/JS samples in geo. The full-bytes
target is 100%; the practical target is "everything important + a clear
pointer to anything elided + the elided thing one click away."

---

## 5 · Constraints surfaced during audit

- **PDF rendering practicality**: Chrome's headless PDF backend tolerates up
  to ~5–10 MB of HTML before rendering becomes painfully slow / pagination
  fragments. The render-everything goal needs `<details>` defaulted-closed
  for transcripts so the PDF stays paginated. HTML carries the full bytes;
  PDF is a print-ready subset.
- **Concurrent renders**: both `chrome --headless` calls in `report_base.py`
  (lines 851 + 895) lack `--user-data-dir` — when the v006 backfill ran
  serially this hid; the substrate runs evolutions in parallel and would
  step on each other's Chrome profile. Already in the test plan as P2.
- **Multi-turn transcript shape differs**: storyboard / x_engine /
  linkedin_engine emit `multiturn_session.log.err`; geo / competitive /
  monitoring / marketing_audit emit `iteration_*.log.err`. The transcript
  appendix glob already handles both (`*.log.err` matches both); the
  reasoning-beat extractor (`extract_reasoning.py`) does not.

---

## 6 · Implementation plan (where this audit feeds the rest of the branch)

Each follow-up commit lands one slice:

- **Commit A** (test_pdf_renderer baseline): record current 11/11 tests
  + screenshot the pre-state of one rendered report so regressions are
  caught.
- **Commit B** (cross-lane data plumbing): factor the new "expandable
  everything" sections into shared helpers in render_report.py — session.md
  block, full-beats panel, evals dump, intermediate state appendix.
  Apply to all 5 existing composers.
- **Commit C** (extract_reasoning multiturn glob): make the extractor
  pick up `multiturn_session.log.err` so storyboard / x / linkedin
  reasoning beats render at all.
- **Commit D** (x_engine + linkedin_engine composers): mirror
  compose_marketing_audit shape but read drafts/<id>.md, parse YAML
  frontmatter, surface BODY+META, render eval.json per draft. Includes
  hand-crafted test fixtures.
- **Commit E** (CLI allowlist + workflow render_report wiring): extend
  `cli/freddy/commands/autoresearch.py` to accept all 7 lanes; add
  `render_report=` to `WorkflowSpec` for x_engine + linkedin_engine.
- **Commit F** (concurrent-render safety): `--user-data-dir=$(mktemp -d)`
  on both Chrome invocations.
- **Commit G** (auto-render env gate): add `AUTORESEARCH_AUTO_RENDER`
  short-circuit in `runtime/post_session.py:post_session_hooks`.
- **Commit H** (data-quality fixes): write valid `{}` to the empty
  monitoring JSON files OR (preferred) make `_render_json_dir` tolerate
  malformed files silently with one-line "(unreadable)" placeholder.
- **Commit I** (rubric proposal): `docs/data-transparency-rubric-proposal.md`.
- **Commit J** (audit doc itself, this file): committed first so the
  later commits can reference back.

Tests:
- Existing 11/11: `pytest autoresearch/archive/v006/scripts/tests/`
- New: hand-crafted x_engine / linkedin_engine session fixtures under
  `/tmp/test-{x,linkedin}-engine-session/` rendered end-to-end.

---

## 7 · Open questions

- Should the render compose the agent's **input prompt** (session.md) AND
  the agent's **output transcript** in the same panel, side-by-side? The
  audit recommends keeping them as separate top-level sections (input is
  static; transcript is dynamic), but this is a UX call.
- Should `<details>` summaries include byte counts so a reviewer knows
  whether expansion is "small" or "huge" before clicking? Recommend: yes,
  every `<details>` shows `(KB)` in its summary for predictability.
- The data-transparency rubric (P1) — should the agent grade itself, or
  should a separate evaluator agent grade the rendered HTML? Recommend:
  separate evaluator (mirrors render_judge.py's RND-* rubric).
