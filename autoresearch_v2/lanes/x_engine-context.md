# Lane: x_engine — X (Twitter) content drafts

**What this lane does:** evolves the prose at `lanes/x_engine.md` so each session produces `drafts/<draft_id>.md` files — single X (Twitter) posts in one of three length brackets, with structured frontmatter and bracketed `[BODY]` / `[META]` blocks.

**Baseline you're trying to beat:**
- Ship-rate from x_engine v1: 5 ship-eligible drafts in 80-130s wall time at $0/run via codex CLI (dogfood).
- v007-curated baselines are the post-port substrate; first holdout run post-Plan-B establishes the v2 holdout baseline.

---

## The angle_id contract (CRITICAL — substrate-level)

This lane runs **one session per angle_id**. The harness passes `AUTORESEARCH_CONTEXT=<angle_id>` to `run_experiment.py`; the v007-curated workflow's `configure_env` propagates it to `$X_ENGINE_ANGLE_ID` env var (shipped as `775de6a` on 2026-05-08).

**The session prompt MUST read `$X_ENGINE_ANGLE_ID` and fail loudly if unset.** Pre-fix bug: agents fell back to `xeng angle-list` and picked the latest angle, ignoring fixture context.

**Working directory:** sessions write to `$X_ENGINE_SESSION_DIR` (set by configure_env). Drafts go to `$X_ENGINE_SESSION_DIR/drafts/`, NOT the variant root. Pre-fix bug: codex sandbox launched with `cwd=variant_root`, drafts overwritten across runs.

---

## Deliverable contract

`drafts/<draft_id>.md` files MUST satisfy ALL of:

1. **Frontmatter is valid YAML** with required fields: `draft_id`, `angle_id`, `platform`, `length_bracket`, `char_count`, `voice_pillar`.
2. **`length_bracket`** is one of `{sharp, build, case_study}`.
3. **`[BODY]` block char_count fits the bracket**:
   - `sharp`: 250–300 chars
   - `build`: 500–900 chars
   - `case_study`: 1000–1500 chars
4. **`[META]` block has all of** `hook`, `authority_anchor`, `specific_number`, `attribution`.
5. **`xeng slop-check --platform x` passes** against the `[BODY]` text (no AI-tells, em-dash limit, banned-word check).

Any failure → `checks_failed`. The eval pipeline writes `drafts/<draft_id>.eval.json` per draft.

---

## Voice substrate (READ-ONLY across BOTH lanes)

`programs/references/voice.md` is **the shared voice substrate** for both x_engine AND linkedin_engine. It is in `readonly_subprefixes` for both lanes — both meta-agents read it, neither mutates it.

Pre-fix bug (`P0 NEW: x_engine + linkedin voice.md materialization gap`): voice.md wasn't being materialized into the variant clone. Now fixed; v2 inherits the fix via the v006 workflow.

---

## The 6 X judges (your fitness function)

Composite = geometric mean across X-1 .. X-6 (note: only 6, not 8 — `_rubric_ids("X")` would over-shoot to 8 IDs, so the lane uses an explicit 6-tuple).

X-judge axes emphasise:
- Hook quality + first-7-words pull
- Specific number / dated claim
- Authority anchor (name + credential)
- Plain-language constraint (no jargon thicket)
- Length-bracket fit (filler-free at the high end)
- Factual veto split (claims that survive a basic fact check)

---

## What you CANNOT edit

- `autoresearch/archive/v007-curated/workflows/x_engine.py`
- `autoresearch/archive/v007-curated/workflows/session_eval_x_engine.py`
- `autoresearch/archive/v007-curated/programs/references/voice.md` (shared with linkedin_engine)

Plus the universal don't-edit rules.

---

## Mutation surfaces that worked

- Pre-ship checklist for the 4 structural-fail bracket (the `templates/x_engine/skeleton-short_take.md` was added in v040 to fix 0/4 structural-fail on cold start).
- Pillar diversity constraint (3+ pillars across the day's 5 drafts).
- "Authority anchor must be a named person + credential, not a brand."

## Mutation surfaces that regressed

- Demanding all 3 length-brackets per session — fixture-time-budget collapse.
- Stripping the slop-check — banned words bypass the eval and tank X-4.

---

## Pull cadence (external — operator concern)

- Daily 06:35 keyword pull, `--max-cu 50` Apify budget.
- Weekly Sun 07:00 creator pull, `--max-cu 200`.

These produce the angle_id stream the lane consumes. JR triggers them via cron; v2 doesn't manage Apify pulls.

---

## Fixture coverage

- Search-v1: `x_engine-*` fixture_ids in `eval_suites/search-v1.json` (4 angles after the 2026-05-08 holdout parity append).
- Holdout-v1: per-lane fixtures in `~/.config/gofreddy/holdouts/holdout-v1.json`.

---

## Recent history pointers

- `git log --oneline lanes/x_engine.md`
- Last ~10 rows of `lanes/x_engine/results.tsv`
- `alerts.jsonl` filtered by `lane=x_engine`
