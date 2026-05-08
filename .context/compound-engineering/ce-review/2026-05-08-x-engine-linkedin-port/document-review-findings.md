# document-review pass — feat/x-engine-linkedin-port content artifacts

**Mode:** autofix
**Date:** 2026-05-08
**Documents reviewed:**
- `src/evaluation/rubrics.py` — the 12 NEW prose blocks `_X_1`..`_X_6` + `_LI_1`..`_LI_6`
- `autoresearch/archive/v007-curated/programs/x_engine-session.md`
- `autoresearch/archive/v007-curated/programs/linkedin_engine-session.md`
- `autoresearch/archive/v007-curated/programs/references/voice.md`
- `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md` (companion file)

## Reviewers spawned (4)

| Reviewer | Focus |
|---|---|
| coherence-reviewer | Cross-document consistency |
| adversarial-document-reviewer | Premise + boundary challenges |
| design-lens-reviewer | AI slop in prompts + missing interaction states |
| feasibility-reviewer | LLM-judge scoring stability |

Skipped: scope-guardian (plan v13 already trimmed); product-lens (D10 dual-lane locked); security-lens (no auth surfaces in content).

## Cross-reviewer agreement (boost confidence on these)

1. **Hashtag policy [3,5] vs [1,5] mismatch** — coherence + design-lens + feasibility (P1)
2. **AUTOMATIC caps under-specified (X-1/LI-1)** — adversarial + feasibility (P1)
3. **HARD FLOOR ambiguous (X-2/LI-2)** — adversarial + feasibility (P1)
4. **Cross-item under-enumerated (X-6/LI-6)** — adversarial + feasibility + design-lens (P1, triple-agreement)

## Applied fixes (autofix queue)

| # | File | Fix | Reviewer(s) |
|---|---|---|---|
| 1 | `linkedin_engine-session.md:170` | Hashtag count gate `[3, 5]` → `[1, 5]` to match code; clarified LI-5 grading | coherence + design-lens + feasibility |
| 2 | `rubrics.py:1222-1225` (_LI_3) | "Most marketers don't realize" verbatim removed (slop self-contamination) | design-lens |
| 3 | `rubrics.py:1265-1269` (_LI_4 score-3) | "And here's the thing:" verbatim → "the 'here's the thing' pattern" | design-lens |
| 4 | `2026-05-07-001-x-engine-rubric-anchors.md` | "earns 10" → "earns 5" (1/3/5 scale fix; 3 occurrences) | coherence |
| 5 | `rubrics.py:1222` (_LI_3) | ~210-char cutoff disclaimer added | adversarial |
| 6 | `voice.md:127` | Em-dash policy contradiction resolved (X bans, LinkedIn singles OK, em-dash-heavy is LI slop) | design-lens |
| 7 | Both session.md | NEW "Handling incomplete angles" section (null source_text) | design-lens |
| 8 | Both session.md | NEW "Cohort diversity decision rule" section | adversarial + feasibility + design-lens |
| 9 | Both session.md | NEW "Structural gate" explanation section | design-lens |
| 10 | Both session.md | NEW "Cold-start exemplars (hand_drafts)" section | design-lens |

**Tests:** 615 pass + 2 skipped (no test file changes; content-only).

## Residual actionable (NOT autofix scope — JR design decisions)

### P0: Pre-loop calibration (feasibility F9)

This IS JR's deferred F4 review. Before L2 evolution kicks off:
1. Generate or pick 3-5 representative X drafts + 3-5 LinkedIn drafts.
2. Score each TWICE through the judge (independent invocations, same prompt).
3. Per criterion, record the variance.
4. **Gating criterion:** if any dimension varies > 2 points, rewrite the anchor before evolution.
5. Document as a "Judge Stability Report" in the plan.

**Why critical:** Evolution loop convergence depends on stable judge scores. ±2 variance on a single dimension produces false promotions and false rollbacks. The 14d X-dogfood is the wrong window for this — calibration must precede dogfood.

### P1 design choices

- **AUTOMATIC caps in `_X_1`/`_LI_1`** — feasibility + adversarial agree the caps are under-specified ("2+ unexplained technical terms" — what counts as unexplained? what counts as a technical term?). Two paths:
  - **Option A (safer):** Remove AUTOMATIC caps. Let the judge score 1/3/5 on the full anchor prose. Removes a known variance source.
  - **Option B (precision-preserving):** Enumerate JR's vocabulary (15-20 terms from voice.md Section 2) and specify which need plain-English follow-up.
- **HARD FLOOR triggering criteria in `_X_2`/`_LI_2`** — enumerate the 3-4 "specific lived-work claim" patterns + accept/reject examples in voice.md Section 3.
- **`_X_6`/`_LI_6` simplification** — remove the geometric-mean per-draft subscoring instruction; rewrite as direct cohort-level gradient (matches `_SB_8` working pattern).
- **Hashtag aggregation logic in `_LI_5`** — explicit aggregation order needed: structure score first, then hashtag cap.

### P2 content authoring (JR's hand)

- **Add 2-3 verified JR exemplar tweets to voice.md Section 3** — gives the judge calibration anchors for "reads like JR typed it" (X-4).
- **Hashtag list per pillar** — `linkedin_engine-session.md` says "3-5 targeted hashtags map to JR's brand pillars" but no list is provided.
- **Define "specificity"** in voice.md Section 4 — currently said but not operationalized.
- **Define "thoughtful authority"** in `_LI_1` more concretely — currently a vibe.

## Verdict

Content artifacts are **autofix-improved**. All cross-reviewer-agreed P1 fixes that don't require design decisions have landed. The remaining work is genuine F4 review territory (JR's hand) — not engineering deferrals.

**Pre-L2-evolution gates that must close (JR-side):**
1. Pre-loop calibration (3-5 drafts × 2 judge runs each; verify variance ≤ 2 per dimension).
2. F4 anchor rewrite for any dimension that fails calibration.
3. AUTOMATIC cap design choice (remove vs enumerate).
4. Voice.md Section 3 entity allowlist + exemplar tweets.

If calibration confirms anchor stability, L2 evolution can proceed with the current content. If 2+ dimensions show ≥2 variance, those need rewrites before promotion gating.
