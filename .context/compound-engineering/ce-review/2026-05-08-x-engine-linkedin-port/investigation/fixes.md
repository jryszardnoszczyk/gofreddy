# Fixes — synthesis from 4-phase investigation

**Branch:** `feat/x-engine-linkedin-port` (26 commits ahead of `origin/main`, 0 pushed).

Two classes of fix. **Mechanical** = code/config changes I can land without JR design decisions. **JR-design** = rubric anchor prose rewrites that require JR's hand per the master plan.

---

## Mechanical fixes (I land these)

### M1 — calibration script: cohort-dim variance is per-cohort, not per-draft

**Source:** Phase 2 §X-6 forensics. Both claude and codex flag "single-draft cohort" → unscorable. The calibration script feeds drafts one-at-a-time, but X-6 / LI-6 are `is_cross_item=True`. Per-draft variance for those dims is structural noise, not signal.

**Change:** in `scripts/calibrate_judge_stability.py`, exclude cross-item dims from the per-dim variance roll-up. Compute their variance only against the cross-cohort axis (variance of [draft1_score, draft2_score, draft3_score], not variance of run1-vs-run2 per draft).

**Files:** `scripts/calibrate_judge_stability.py`. Update `_per_dimension_variance` callers + `dim_summary` aggregator.
**Tests:** `tests/scripts/test_calibrate_judge_stability.py` — add a test that cross-item dim with high run-to-run swing within one draft does NOT trip FAIL.

---

### M2 — `STRUCTURAL_DOC_FACTS` backfill for new lanes; drop pytest.skip carve-out

**Source:** Phase 4 Gap 4. Empty tuples → AUTOGEN block says "_no structural gates defined_" while `SessionEvalSpec.structural_gate` does real work. Misleading + carve-out hides the contradiction.

**Change:** populate `LaneSpec.structural_doc_facts` for both new lanes with prose that describes what `structural_gate` actually enforces. Same for `structural_gate_functions` (string refs to the SessionEvalSpec callable namespace).

**Files:** `autoresearch/lane_registry.py` (lines 235-285) + drop the pytest.skip carve-out in `tests/autoresearch/test_structural_doc_facts.py`.

---

### M3 — `state.db` env override

**Source:** Phase 4 Gap 2. Hardcoded module-relative DB path; worktree experiments hit empty/missing DB.

**Change:** `DB_PATH = Path(os.environ.get("X_ENGINE_DB_PATH", str(Path(__file__).parent.parent / "state.db")))`.

**Files:** `x_engine/pipeline/db.py:9`. Add unit test for env override.

---

### M4 — per-lane `random_per_domain` rotation override

**Source:** Phase 4 Gap 3. New lanes have 0 anchors; stratified rotation samples 1 fixture/cohort vs 3 for existing lanes.

**Change:** allow per-domain rotation override in `search-v1.json`. Add `domain_rotation_overrides: {x_engine: {random_per_domain: 3}, linkedin_engine: {random_per_domain: 3}}` to suite manifest. Update `_sample_fixtures` to read per-domain override before suite-level rotation.

**Files:** `autoresearch/eval_suites/search-v1.json` + `autoresearch/evaluate_variant.py:374-441` (`_sample_fixtures`). Add tests covering per-domain override behavior + fall-through.

---

### M5 — daily fixture sync CLI: `xeng search-v1-sync`

**Source:** Phase 4 Gap 1. Search-v1 fixture contexts are static `"1".."5"`; live `angles` table holds 120-127. Sessions fail at `xeng angle-show 1`.

**Change:** new CLI command `xeng search-v1-sync [--top N] [--output PATH]`:
- Query `angles ORDER BY picked_at DESC LIMIT N`.
- Rewrite `eval_suites/search-v1.json` `domains.x_engine[]` and `domains.linkedin_engine[]` with current angle IDs as fixture contexts.
- Atomic-rename via tmp file. Idempotent.

LaunchAgent fires after `linkedin-pull-search` so fresh angles → fresh fixtures → next evolve picks them up.

**Files:** new command in `x_engine/cli.py`, new LaunchAgent `.plist` `com.jryszardnoszczyk.x-engine-search-v1-sync.plist`. Tests for empty/full/partial-N angle DB cases + JSON roundtrip integrity.

---

## JR-design rewrites (your hand)

Each carries empirical evidence from the calibration transcripts. See `phase2-3-rubric-forensics.md` for full rationales.

### J1 — X-1 + LI-1: AUTOMATIC ≤6 jargon-cap

**Evidence:** doc-review residual + LI-1 instability (claude 8→6 on thought_leader, AUTOMATIC cap fires unpredictably).
**Choice:**
- (A) Enumerate exact term list that triggers the cap (15-20 terms from voice.md Section 2 — "harness", "lineage", "frontier", "evaluator", etc.) + plain-English-follow-up requirement.
- (B) Remove the cap entirely; let gradient scoring handle it.

**Recommendation:** (A) preserves the original intent at the cost of one explicit term-list maintenance.

### J2 — X-2: SOURCE/INTERPRETIVE decision tree

**Evidence:** codex X-2 swing 6→2 on build; same input, judge picks one of two valid rule-readings.
**Add to anchor prose:**
> "If the claim names a voice.md Section 3 entity AND uses first-person/operator framing → INTERPRETIVE. Score on internal coherence + cohort-fit. Source verification NOT required.
>
> If the claim references an external counterparty OR an unnamed comparator → SOURCE. Source_text required, cap fires if missing."

### J3 — X-3: SHARP-bracket bare-enumeration test

**Evidence:** sharp.md cross-judge gap of 6 points (claude 3 vs codex 9). Same opener, opposite reads.
**Add to anchor prose:**
> "A bare numeric enumeration with no claim verb scores ≤4 even if specific. SHARP earns 5+ when the first 12 words include at least one verb-bearing claim alongside the numbers."

### J4 — X-4 + X-5: pad-vs-substance enumeration

**Evidence:** claude X-5 swing 4→7 on build. "Pad" not defined; same bullets read both ways.
**Add to anchor prose:**
> "A bullet is **substance** if it carries at least one of: specific number, named entity, contrast, lived-work claim. A bullet is **pad** if it carries none. BUILD with ≥3 substance bullets earns 7+; with all-pad bullets, ≤4 hard cap fires."

### J5 — X-6 / LI-6: NO PROSE CHANGE — calibration script fix only

**Evidence:** N=1 cohort is structurally unscorable per both judges.
**Fix lands in M1.** No anchor change needed.

---

## Order of operations

1. **Land all mechanical fixes** (M1–M5). Tests green. ~3.5 hr. No anchor prose touched.
2. **JR rewrites J1–J4 anchor prose.** Half-day to full-day.
3. **Recalibrate.** Need 3 runs minimum (not 2) to escape sampling-noise verdict swings — extend `--runs 3` default. ~15 min wall.
4. **Drop pytest.skip carve-out** if M2 backfill stable.
5. **Push branch + open PR.**

---

## Open question on calibration sample size

The first calibration run reported LinkedIn = PASS; the second run reported FAIL. **2 runs is below the noise floor.** Default should be 3 runs. M1 should bump the script's `--runs` default from 2 to 3 + adjust the verdict gating accordingly.

This is a small change inside M1.
