# Lane: linkedin_engine — LinkedIn content drafts

**What this lane does:** evolves the prose at `lanes/linkedin_engine.md` so each session produces `drafts/<draft_id>.md` files — single LinkedIn posts in one of three length brackets, with structured frontmatter, `[BODY]`, and `[META]` blocks. Sibling to `x_engine` — same shape, different per-platform structural rules and rubric IDs.

**Baseline you're trying to beat:**
- v007-curated baselines (post-port substrate); first holdout run post-Plan-B establishes the v2 holdout baseline.
- Engagement formula (operator-side): `(reactions × 1 + comments × 3 + shares × 5) × exp(-days/14)`. Not enforced by judges; informs holdout fixture curation.

---

## The angle_id contract (CRITICAL — substrate-level)

Same pattern as x_engine. `AUTORESEARCH_CONTEXT=<angle_id>` → `configure_env` propagates to `$LINKEDIN_ENGINE_ANGLE_ID`. Drafts go to `$LINKEDIN_ENGINE_SESSION_DIR/drafts/`.

**LinkedIn consumes the X-derived angle stream** (per master plan v13 D13) — same v1 angles table. The angle_id semantics are identical; the platform-specific structural rules differ.

---

## Deliverable contract

`drafts/<draft_id>.md` files MUST satisfy ALL of:

1. **Frontmatter is valid YAML** with required fields: `draft_id`, `angle_id`, `platform`, `length_bracket`, `char_count`, `voice_pillar`.
2. **`length_bracket`** is one of `{short_take, thought_leader, case_study}`.
3. **`[BODY]` block char_count fits the bracket** (LinkedIn allows longer posts):
   - `short_take`: 500–900 chars
   - `thought_leader`: 1500–2500 chars
   - `case_study`: 2500–3000 chars
4. **`[META]` block has all of** `hook`, `authority_anchor`, `specific_number`, `attribution`, `hashtags`.
5. **`hashtags` is non-empty and ≤ 5 hashtags** (LinkedIn algo penalises >5; X has no such limit).

Any failure → `checks_failed`. The eval pipeline writes `drafts/<draft_id>.eval.json` per draft.

---

## Platform-specific rules (vs x_engine)

- **No em-dash check** — LinkedIn prose tolerates em-dashes; x_engine bans them.
- **Different AI-tell blocklist** — `synergy`, `paradigm`, `disruptor` weighted more heavily.
- **Longer length brackets** — `short_take` is LinkedIn's smallest unit and starts where x_engine's `sharp` ends.
- **Hashtag cap of 5** — strict; algo-driven.

---

## Voice substrate (READ-ONLY shared with x_engine)

`programs/references/voice.md` is shared between both lanes. Both `linkedin_engine.py` AND `x_engine.py` claim it in `readonly_subprefixes` — dual-claim is safe because `path_is_readonly` is per-lane lookup.

---

## The 6 LI judges (your fitness function)

Composite = geometric mean across LI-1 .. LI-6. LI-axes mirror X-axes but recalibrated for LinkedIn:
- LI-1 Hook + first-line pull (LinkedIn shows ~210 chars before "see more")
- LI-2 Specific number / dated evidence
- LI-3 Authority anchor (named person + credential — LinkedIn rewards strongly)
- LI-4 Plain-language (LinkedIn-specific AI-tell list)
- LI-5 Length-bracket fit (LinkedIn-specific brackets)
- LI-6 Hashtag relevance + cap

---

## What you CANNOT edit

- `autoresearch/archive/v007-curated/workflows/linkedin_engine.py`
- `autoresearch/archive/v007-curated/workflows/session_eval_linkedin_engine.py`
- `autoresearch/archive/v007-curated/programs/references/voice.md` (shared with x_engine)

Plus the universal don't-edit rules.

---

## Mutation surfaces that worked

- Adding "use a 3-paragraph structure: hook / evidence / takeaway" for `short_take` bracket.
- Forcing hashtags to mix branded + topic + audience tags (3 categories of 5 max).
- Pre-ship checklist mirroring x_engine's cold-start fix.

## Mutation surfaces that regressed

- Demanding hashtags ALWAYS include `#AI` — overfits to a fixture subset.
- Allowing >5 hashtags — algorithmic penalty surfaces as LI-6 collapse.

---

## Fixture coverage

- Search-v1: `linkedin_engine-*` fixture_ids in `eval_suites/search-v1.json` (4 angles after the 2026-05-08 holdout parity append).
- Holdout-v1: per-lane fixtures in `~/.config/gofreddy/holdouts/holdout-v1.json`.

---

## Recent history pointers

- `git log --oneline lanes/linkedin_engine.md`
- Last ~10 rows of `lanes/linkedin_engine/results.tsv`
- `alerts.jsonl` filtered by `lane=linkedin_engine`
