# Phase 2 + Phase 3 — rubric forensics

Source data: 12 raw judge transcripts under `calibration/raw/{x_engine,linkedin_engine}/<draft>.run{1,2}.json` from the 2026-05-08 calibration v3 run with `--save-raw`.

This combines per-dim forensics on X failures (Phase 2) with the X-vs-LinkedIn asymmetry analysis (Phase 3).

---

## Headline corrections vs first calibration run

The first calibration run reported `linkedin_engine = PASS`. The second run with `--save-raw` reported `linkedin_engine = FAIL` (LI-1 max variance = 2.0). **Both runs hit the same drafts on the same fixtures.** The verdict swing came from sampling: 2 runs is below the floor needed to certify stability.

Updated picture from calibration v3:

| | x_engine v3 | linkedin v3 |
|---|---|---|
| Verdict | FAIL | FAIL |
| Failed dims (primary, max ≥ 2.0) | X-4, X-5, X-6 | LI-1 |
| Primary max swing | 3.0 (X-5 build) | 2.0 (LI-1 thought_leader) |
| Secondary max swing | 4.0 (X-2 build) | 2.0 (LI-2 case_study) |
| Cross-judge max abs Δ | 2.6 (case-study) | 1.0 (case_study) |
| Primary avg score | 3.4–4.65 | 6.80–7.35 |
| Secondary avg score | 5.95–6.50 | 6.35–6.95 |

**Both lanes have rubric instability.** X is worse on cross-judge calibration; LI is better but still tripped the threshold on a single dim. The first-run "LI PASS" was sampling noise.

---

## Phase 2 — per-dim forensics on X failures

### X-2 (codex 6→2 swing on build, 3→6 on sharp, 2→4 on case-study)

**Same draft, same body, same META — codex scores 2 then 6 then 4 across runs.** The judge bounces between two rationales depending on the run:

> run1 codex X-2 score=6: "The draft makes many specific factual claims: 149 lenses, 25 vertical bundles… **There is no apparent hard-floor violation because it…**"
>
> run2 codex X-2 score=2: "The draft contains many precise factual claims… **but no source_text is included in the artifacts, so these claims are not verifiable from what is in front of me.**"

**Mechanism:** X-2 anchor has three competing rules:
1. SOURCE/INTERPRETIVE split (SOURCE claims need source_text)
2. HARD FLOOR ≤3 for unnamed-entity lived-work claims
3. Cap at 7 for first-person specific claims that don't name the entity

The judge interprets "specific factual claim" as either (a) lived-work-from-named-entity → score on internal coherence (high) or (b) external claim needing verification (low). **Same input, two valid readings, picks one randomly per run.**

**Fix prose:** explicit decision tree:
> "If the claim names a voice.md entity AND uses first-person/operator framing ('we ran X on our pipeline', 'gofreddy ships Y') → score on internal coherence + cohort-fit only. Source verification is NOT required.
>
> If the claim references an external counterparty ('our client X's revenue grew Y%') OR an unnamed comparator ('Most agencies do Z') → SOURCE bar applies; require source_text or the cap fires."

### X-3 (cross-judge gap of 6 points on sharp; claude 3-4 vs codex 9)

**Same SHARP opener** — `21 priority creators, 50 search queries, 22 GitHub repos, 7 RSS feeds.`

> claude: "specific-number enumeration without context — the rubric explicitly anchors that pattern at 3 ('a specific number without context')." → score 3-4
>
> codex: "compressed and specific opener earns attention quickly with concrete scale instead of a generic hook." → score 9

**Mechanism:** claude treats bare enumerations as failing the "claim + support pair in first 12 words" rule (caps low). Codex treats specificity itself as the claim. Both readings are reasonable; the rubric doesn't disambiguate.

**Fix prose:** explicit test for SHARP openers:
> "A bare numeric enumeration with no claim verb scores ≤4 even if specific. SHARP earns 5+ when the first 12 words include at least one verb-bearing claim alongside the numbers ('We pull 375 tweets/day from 21 creators' — verb 'pull' carries the claim; `21 priority creators, 50 search queries…` does not)."

### X-4 + X-5 (claude variance on build: X-4 4→6, X-5 4→7)

Same draft. Same bullets. Same closer.

> X-5 run1 claude=4: "Loses a point because the bullets are essentially a flat enumeration of categories"
>
> X-5 run2 claude=7: "Bullets are uniformly numeric and the closer carries genuine weight"

**Mechanism:** "Pad-to-length = ≤4 hard cap" without an explicit definition of "pad". Same bullets read as "flat enumeration" (pad) or "uniformly numeric" (substance). The judge picks per-run.

**Fix prose:** enumerate the pad/substance test:
> "A bullet is pad if it carries none of: specific number, named entity, contrast, lived-work claim. A bullet is substance if it carries at least one. BUILD with ≥3 substance bullets earns 7+; with all-pad bullets, ≤4 hard cap fires."

### X-6 (single-draft cohort scoring is broken)

Both judges flag the structural mismatch:

> claude run1 X-6=3: "Cohort consists of a single draft (cal-x-build only). With N=1 the geometric-mean construction reduces to a single point — no concentration violation possible"
>
> codex run1 X-6=9 (case-study): "Only one draft is present, so there are no observable duplicate hooks… cannot demonstrate intentional full-range diversity"

**Mechanism:** The calibration script feeds each draft as its own one-fixture session. X-6 is `is_cross_item=True` and is meant to score the cohort, not individual drafts. With N=1 the rubric is structurally unscoreable.

**Fix:** This is **not a rubric anchor problem**. The calibration script sends drafts one-at-a-time. Two paths:
- **A (cleanest):** modify calibration to send all 3 drafts as one multi-artifact request for X-6 / LI-6 specifically (per-criterion request batching).
- **B (simpler):** drop X-6 / LI-6 from per-draft variance, only assess them at cross-cohort level (compute variance across the 3-draft scores, not per-draft swings).

**Recommendation:** B. The cross-item dim is meaningful only at session-level. Per-draft variance is structurally noise.

### X-1 (mostly stable: max claude swing 1, max codex swing 2 once)

X-1 is actually the most stable X dim in this sample. Document-review residuals flagged "AUTOMATIC caps under-specified" — the data here is consistent with that prediction (variance is small but cap-trigger drift exists in codex case-study 3→5). When the rubric cap fires it's deterministic; the variance comes from whether the cap fires.

**Fix:** same as document-review residual — enumerate the exact term list that triggers AUTOMATIC ≤6 jargon cap, OR remove the cap and rely on gradient scoring.

---

## Phase 3 — Why LinkedIn was less bad

Run-to-run instability is **roughly comparable** between lanes:

| | x_engine | linkedin_engine |
|---|---|---|
| dims with primary swing ≥2 | 3 | 1 |
| dims with secondary swing ≥2 | 3 | 3 |
| total cells (across 3 drafts × 6 dims) with swing ≥2 | 7 | 7 |

So the within-judge noise is similar. The asymmetry is in **cross-judge calibration**:

| metric | x_engine | linkedin_engine |
|---|---|---|
| primary avg score | 3.4–4.65 | 6.8–7.35 |
| cross-judge abs Δ avg | ~2.1 | ~0.6 |

**Claude scores X drafts ~2 points lower than codex; scores LI drafts equally.** That's not draft-quality — it's how each judge interprets the X rubric vs the LI rubric.

### Hypothesis test 1 — Are LI rubrics structurally different?

Read the prose blocks side-by-side. Findings:

| Mechanism | X usage | LI usage |
|---|---|---|
| AUTOMATIC ≤4 / ≤6 caps | X-1, X-3, X-4 | LI-1 only |
| HARD FLOOR ≤3 | X-2 | LI-2 |
| Cap-at-7 (for partial-violation) | X-2 | LI-2, LI-5 |
| Pure gradient (no caps) | X-5, X-6 | LI-3, LI-4, LI-6 |

**X uses caps in 4 of 6 dims; LI uses caps in 2 of 6.** Caps are the unstable mechanism — when the cap triggers the score drops 3-4 points; when it doesn't trigger the score is full gradient. Cross-judge cap-trigger consistency is poor (claude triggers more aggressively than codex).

This is the **structural cause of the X-LI asymmetry**: X rubric prose leans harder on AUTOMATIC caps that fire inconsistently across judge families. LI rubric prose uses gradients which scale smoothly.

### Hypothesis test 2 — Did the document-review autofix favor LI?

Yes. The autofix run (commit `9083e69`) landed:
- 6 LI-side fixes (hashtag policy, slop self-contamination ×2, em-dash policy, structural-gate explanation, cohort decision rule)
- 2 X-side fixes (em-dash policy ×1, cold-start exemplars)

The LI prose got more pre-calibration polish. X-1 / X-2 / X-3 / X-4 / X-5 anchor prose is largely unchanged from the v13 plan companion file.

### Hypothesis test 3 — Does draft length smooth variance?

LinkedIn drafts: short_take 785 chars, thought_leader 1647 chars, case_study 2634 chars (avg ~1700).
X drafts: sharp 265, build 786, case-study 1347 (avg ~800).

LI drafts are 2× longer on average. More substrate for judges to score against → individual sentence-level interpretation matters less → variance smooths. But this is a draft-length effect, not a rubric-fidelity argument. Real X drafts in production will span the same brackets, so this advantage doesn't carry.

### Phase 3 verdict

The X-vs-LI asymmetry has **two structural causes** + **one noise effect**:
1. **X rubric uses AUTOMATIC caps in 4 of 6 dims; LI uses 2 of 6.** Caps fire inconsistently → cross-judge calibration drift. This is the load-bearing cause.
2. **LI prose got more autofix polish.** Document-review landed 6 LI fixes vs 2 X fixes pre-calibration.
3. (Minor) LI drafts are 2× longer; smooths within-judge variance somewhat.

Fixing X requires reducing or operationalizing the AUTOMATIC caps (matches document-review residual recommendation), not just rewriting prose generically.

---

## Recommended X anchor rewrites (JR's hand)

These are the design-decision items. Each carries the empirical evidence above.

| Anchor | Fix | Owner | Evidence |
|---|---|---|---|
| **X-1** | Enumerate the AUTOMATIC ≤6 jargon-cap term list (15-20 terms from voice.md Section 2) OR remove the cap | JR | doc-review residual + LI-1 instability shows same mechanism is fragile |
| **X-2** | Add explicit decision tree: lived-work-from-voice.md-entity vs external claim; only the latter requires source_text | JR | codex 6→2 swing on build = same input, two valid rule-readings |
| **X-3** | Add SHARP-bracket test: bare enumeration ≤4 unless verb-bearing claim accompanies | JR | claude 3-4 vs codex 9 cross-judge gap = rule ambiguous on enumerations |
| **X-4** | Enumerate the pad-vs-substance bullet test (specific number / named entity / contrast / lived-work claim) | JR | claude 4→6 swing = "pad" not defined |
| **X-5** | Same enumeration as X-4 but for structural elements (hook, pivot, bullets, anchor, metric) | JR | claude 4→7 swing = same mechanism as X-4 |
| **X-6** | NO PROSE CHANGE — fix calibration script to score cohort-level only | me (mechanical) | both judges flag N=1 unscoreable |

LI-1 is the only LI dim that tripped; same fix as X-1 (enumerate or drop AUTOMATIC ≤6 cap).

---

## What this means for the merge timeline

- **Mechanical fixes available to land now:** X-6 calibration scoring fix (+ all 4 Phase 4 plumbing gaps).
- **JR-design rewrites required before recalibration:** X-1, X-2, X-3, X-4, X-5 + LI-1 anchor prose (5 X dims + 1 LI dim).
- **After recalibration passes:** branch is mergeable.

Realistic estimate: half-day to full day of JR's hand on rubric prose, then recalibration (~10 min wall) to verify.
