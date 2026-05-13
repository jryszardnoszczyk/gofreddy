---
date: 2026-05-13
type: retune playbook (judge-design)
status: active reference
companion: 2026-05-13-judge-rewrites-for-evolution-resume.md
---

# Retune playbook — what to do when evolution generations return σ data

After the evolution-running agent applies the 14 rewrites and 1-2 generations complete, we'll have empirical σ data on the rewritten criteria. This doc says what to do based on what comes back.

## How to read the signal

Two sources of post-generation σ data:

1. **`scripts/validate_rubric_rewrites.py --per-lane 5`** — calls judge against archived artifacts using new rubric; outputs per-criterion σ + delta vs old cached σ
2. **`/tmp/discrimination_analysis.py`** — walks post-2026-05-11-modified `.last_eval_cache.json` files, computes per-criterion σ from emergent evolution-run data

Decision should rest on (2) when available — it's emergent data from actual evolution, not synthetic re-scoring.

## Scenario decision tree

### Scenario A: σ widens as expected on rewritten criteria

**Signal:** Each rewritten criterion's σ moves from < 0.15 to > 0.20 (preferably > 0.25). Score distributions show 3-level differentiation across artifacts.

**Action:** No retune needed. Rewrites worked. Two follow-ups:
1. Capture the new σ baseline in `docs/brainstorms/2026-05-12-judge-design-deep-research/audit-findings-2026-05-13.md` as "VERIFIED" status
2. Decide whether to apply the same pattern to LinkedIn / MA criteria. Currently skipped because of "no post-fix data" — but if the pattern works, expanding makes sense.

### Scenario B: σ widens on SOME criteria, stays flat on others

**Signal:** Mixed — e.g., MON-1/3/4 widen but MON-5/6 stay flat. Or one lane responds, another doesn't.

**Diagnosis:**
- **Flat-rewritten criteria** = the new prose hasn't sufficiently raised the Score-5 bar. Common cause: the anti-gaming clause or substitution test isn't operationalizable enough for the judge to apply.
- **Specific lane flat** = the lane's artifacts may not exhibit the failure mode the rewrite targets (e.g., MON-5 about compound narratives may be flat because the lane's outputs lack cross-story signal at all).

**Action by-criterion:**

For each flat criterion, examine 2-3 sample judge `feedback` strings from the new post-fix caches:
- If feedback says "passes 4/4" or "scores 5" uniformly → bar still too low; tighten further
- If feedback says "fails on sub-question N" consistently → check whether the artifacts even contain the substance the criterion measures (substrate-level problem, not rubric problem)
- If feedback says "ambiguous" / "partially" → operational definition is judge-fuzzy; add a concrete example

**Concrete retune moves per criterion** (apply only to flat ones):

| Criterion | If flat, do |
|---|---|
| MON-1 | Tighten "named baseline" further: require a specific calendar date OR a metric-name (e.g., "Q4 2025" or "Buffer 2026 baseline"). Anti-gaming clause may need expansion. |
| MON-3 | If feedback says "names runner-up but doesn't argue why" → require an explicit "alternatives considered" paragraph naming what could have been the lede |
| MON-4 | If "specific individual" passes when it shouldn't → require named individual to be ROLE+NAME, not just title |
| MON-5 | If lane has no cross-story signal at all → substrate issue, not rubric. Surface back to evolution agent. |
| MON-6 | Tighten "falsifiable next-period condition" → require an explicit date AND a specific number/range, not just direction |
| CI-1 | If client-substitution test passes when shouldn't → require explicit naming of "what makes THIS client different" in the thesis itself |
| CI-5 | Same as CI-1 substitution issue |
| CI-6 | If "stakeholder could veto" doesn't discriminate → ask for explicit statement of what the brief is asking the client to accept that they'd previously rejected |
| CI-7 | If priority axes get gamed → require explicit "if you only do ONE thing" sentence naming the single top action |
| SB-1 | If 3 references concentrate in one section → require references to span at least 3 different story sections (hook + climax + denouement) |
| SB-2 | If hooks pass substitution test cosmetically → require the unique element to be NAMED in the hook itself, not just present |
| SB-3 | If diegetic cause vs narrative assertion is fuzzy → require the cause to be a specific line/action in story_beats, with cross-reference |
| SB-5 | If audio doesn't add information → require an explicit list of "audio decisions" with a column for "what story info this carries" |
| X-9 | If markdown links / disguised redirects don't get caught → expand regex to include common shortener domains explicitly (bit.ly, tinyurl, etc.) |

**My role:** retune the specific flat criteria; deliver updated brief prose to the evolution agent (same handoff format as before).

### Scenario C: Scores collapse to floor

**Signal:** Rewritten criteria show mean < 0.30, σ < 0.10. Everything fails the new bar.

**Diagnosis:** Bars set too harsh. The Score 5 prose requires substance that current substrate doesn't produce at all.

**Action:**
1. Don't roll back. The floor-collapse signal is real — it means current substrate doesn't meet the new bar.
2. Decide per-criterion: is the bar too high, or is the substrate broken?
3. If bar too high: soften specific sub-questions or anchors. Replace "ALL material claims" with "at least 3 material claims" for criteria where the universal quantifier is too aggressive.
4. If substrate broken: the rubric is correctly diagnosing a real gap. Pair the rewrite with a substrate hint in the lane's `meta.md` so evolution can learn the new behavior (similar to GEO-9 substrate hint pattern we'd planned but rejected).

**Concrete softening moves** for each criterion if needed:

| Criterion | Soften by |
|---|---|
| MON-1 | "ALL material claims" → "EVERY major claim (top 3-5 in the digest)" |
| MON-4 | "specific named individual with single decision-making authority" → "specific named role or named individual" |
| MON-6 | "specific client decision it would change" → "decision-relevant interpretation" |
| CI-1 | "client-substitution test" → "the thesis includes at least one client-specific qualifier" |
| CI-5 | Same softening — "competitor-substitution" → "client-specific qualifier" |
| CI-6 | "real strategic decision" → "non-cosmetic challenge to the client's plans" |
| CI-7 | Drop the "stakeholder could rebut" test; keep the "explain what's lost / gained" requirement |
| SB-1 | "at least 3 distinct creator-specific" → "at least 2 distinct creator-specific" |
| SB-2 | Drop substitution test entirely; keep "irreplaceable element named in hook" |
| SB-3 | "diegetic cause" requirement → "story-content cause (revelation, action, or juxtaposition)" |
| SB-5 | "specific story-event tie" → "stated reason this delivery serves this beat" |
| X-9 | (Already a deterministic check; no softening needed.) |

### Scenario D: Mixed effects in unexpected directions

**Signal:** Some criteria score HIGHER than before (mean increases), or σ moves but in a way that suggests calibration drift (e.g., everything bunches at 0.5).

**Diagnosis:** The rewrite changed not just discrimination but the absolute scale.

**Action:** Surface to JR. Don't unilaterally retune. The scale shift may reflect a real change in what "good" means under the new rubric, which is a product decision, not a calibration one.

### Scenario E: Evolution agent reports the patches didn't apply correctly

**Signal:** Agent comes back saying it couldn't find the resume-target variant, or the CRITERIA dict doesn't match the handoff's "current prose" exactly.

**Diagnosis:** Variant evolution has moved on since 2026-05-08 v006 archive. The current.json head may point at a v189+ variant whose workflows/ has different prose.

**Action:**
1. Get the agent to provide the actual current.json paths + the variant's current CRITERIA prose for each affected criterion
2. Re-draft the brief-form rewrites against the actual current prose (the v2 patterns transfer; the exact "replace this string" instructions don't)
3. New handoff doc supersedes the 2026-05-13 one

## Pre-thinking the lane-by-lane expected response

Based on the failure modes the rewrites target, I expect:

**Monitoring** — high response. The brief prose was the most permissive; the new bars are dramatically tighter on named baselines + falsifiable predictions. Expect σ widening on MON-1/3/4/6; MON-5 may stay flat if cross-story signal isn't in the artifacts.

**Competitive** — moderate response. CI-1 / CI-5 should respond clearly because the substitution tests are concrete. CI-6 / CI-7 are more judge-fuzzy and may need anchor tuning.

**Storyboard** — high response on SB-1 / SB-2 (substitution tests are crisp). SB-3 may be substrate-limited (emotional_map quality depends on the substrate writing it well). SB-5 may need iteration if audio specifications are underspecified in current artifacts.

**X_engine** — X-9 should fire on 3/3 current archived drafts (Phase C of original audit confirmed this). Expect immediate discrimination once it ships.

## What I (judge design) do vs what evolution agent does

| Action | Owner |
|---|---|
| Determine if σ data shows pattern works | Judge-design (me) |
| Retune specific criterion prose | Judge-design (me) |
| Apply retuned prose to variant | Evolution agent |
| Run evolution generations | Evolution agent |
| Decide whether to expand pattern to LI/MA | Judge-design (me) + JR |
| Decide whether substrate hints are needed | Judge-design (me) + Evolution agent |
| Decide to roll back | JR only |

## When to escalate to JR

- Scenario D (unexpected scale shifts) — product decision, not calibration
- Scenario E (handoff doesn't apply) — needs operator context on which variants are live
- Any retune that touches >3 criteria in one round — sign that the pattern itself needs rethinking, not individual criterion tuning
- Cost overrun on validation runs > $200
- Any case where σ moves in a direction that surfaces a substrate problem (not a rubric problem)

## File index for retune

- This playbook
- Handoff: `docs/handoffs/2026-05-13-judge-rewrites-for-evolution-resume.md`
- Validation script: `scripts/validate_rubric_rewrites.py`
- Discrimination analysis: `/tmp/discrimination_analysis.py`
- v3 spec (rejected alternatives source): `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-master-spec-v2.md`
- Audit findings: `docs/brainstorms/2026-05-12-judge-design-deep-research/audit-findings-2026-05-13.md`
- Long-form prose (HTTP API path): `src/evaluation/rubrics.py` (commit 896f366)
