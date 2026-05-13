# v2 Spec Audit — Findings (2026-05-13)

5 parallel agents audited the v2 master spec. The audit invalidates v2's premise. v3 reframe required.

## CORRECTION (post-investigation 2026-05-13 evening)

After writing the audit, follow-up investigation discovered that the headline pathology "broadcast-feedback across 8 criteria" was already substantially fixed:

- **PR #60 (commit `3b97b3d`) on 2026-05-11** shipped the Stream A axis-collapse fix
- Fix is on by default (`AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on`)
- CLI side reads `per_criterion` array from judge response (`cli/freddy/commands/evaluate.py:215-285`)
- Judge prompt explicitly instructs "do not back-fill identical verdicts across rubrics" (`judges/session/prompts/critique.md:29`)
- **Verified working:** post-fix geo cache (2026-05-12) shows 8/8 unique feedback strings + 2 distinct scores
- The audit agent's broadcast finding came from May 8 caches generated **3 days before** the fix shipped

**What this means for the audit's findings:**

1. **Broadcast pathology** — RESOLVED. Verify-only work remains (regression test + lane coverage check). Phase 0.1 reduces from 3-5 days to ~1 day.
2. **Ceiling-bound rubrics** — POTENTIALLY STALE. The discrimination analysis was over pre-fix data; post-fix variance may be different. Re-run before declaring kernel criteria load-bearing.
3. **`rubric_version` not in archive** — STILL TRUE. The DB schema has the column; autoresearch `scores.json` doesn't write it. Phase 0.2 still needed.
4. **3-level scoring grain** — STILL TRUE. Documentation work in Phase 0.3 still needed.
5. **Empty `dimension_scores` in archive** — STILL TRUE. Per-criterion data lives in `.last_eval_cache.json` only. Phase 0.2 covers this.

The rest of the audit (paper verification, adversarial review, scope-guardian review, Phase C re-rating) stands unchanged. Only the substrate-pathology severity reframes downward.

The rest of this document was written PRE-correction and reflects the original audit findings. The plan at `docs/plans/2026-05-13-001-judge-substrate-fix-and-kernel-plan.md` reflects the corrected scope.

---

---

## Headline: v2 is treating a rubric problem; the actual problem is the substrate

The audit's biggest discovery — from the empirical score-distribution agent — is that the existing judges **do not behave as designed**. Adding +14 criteria on top of a substrate that doesn't use the existing 52 per-criterion is solving the wrong problem.

**Substrate pathologies found:**

1. **Scores are 3-level (0.0 / 0.5 / 1.0), not 1-10 gradient.** All rubrics in `src/evaluation/rubrics.py` declare `"gradient"` scoring. The session-judge collapses to 3 levels. Every "mean > 8.5 / mean < 3.5 ceiling/floor" analysis in v2 is moot against this dataset — there's no 1-10 data to analyze.

2. **66% of sessions emit identical feedback strings across all 8 criteria.** The judge isn't scoring per-criterion — it produces one global verdict and stamps it onto every criterion. Per-criterion independence is an illusion at the data layer.

3. **Cross-criterion variance is fictional outside GEO.** Mean and σ across all 8 criteria in MON, CI, SB are near-identical:
   - Monitoring (MON-1..MON-8): mean 0.932-0.937, σ 0.097-0.099 — ceiling-bound across the board
   - Storyboard (SB-1..SB-8): mean 0.980, σ 0.027 — pure decoration; entire rubric never separates variants
   - Competitive (CI-1..CI-8): mean 0.900-0.950, σ 0.112-0.137 — same uniform-σ pattern
   - **Only GEO produces criterion-level variance** (σ 0.18-0.28 across criteria, range 0.41-0.81)

4. **`rubric_version` field is not persisted alongside scores.** The `RUBRIC_VERSION` constant at `rubrics.py:1516` exists but doesn't ship with score rows. Cross-version comparison from archive is impossible. Phase 1.3 of v2 ("RUBRIC_VERSION hash extension") presumes a baseline that isn't there.

5. **Per-criterion scores aren't persisted to `scores.json`.** They live only in per-session `.last_eval_cache.json` files, which are easily overwritten. ~50% of archived variants have no eval cache at all.

**Implication:** The substrate has to be fixed before any rubric work matters. A pre-rubric Phase 0 is now load-bearing for the entire program.

---

## Convergent findings across all 5 agents

All 5 agents independently arrived at: **the kernel should be +5, not +14.**

Evidence-backed kernel survivors:
- **MON-9** (fabrication AUTO-CAP) — deterministic substring check; needs non-empty-mention fixture for validation (current corpus is degenerate; every archived monitoring artifact is zero-mention)
- **MA-9** (decision-changing insight density) — discriminates at completion-margin, but needs explicit rubric anchors distinguishing "decision-changing" from "governance recommendation"
- **GEO-9** (named-expert quoted attribution) — corpus-wide gap; no archived geo variant cites a named individual in `"..."` form; produces floor-compression for ~10 generations until substrate learns
- **CI-9** (triangulation depth) — discriminates (σ ≈ 2.2 on 4-variant sample); partially redundant with CI-2 but adds signal on partial-data triangulation
- **X-9** (algorithmic-citizenship AUTO-CAP) — strongest empirical validation; Phase C 3/3 violation; X penalty actually stronger than spec claimed (~100% suppression for non-Premium, not 30-50%)

The remaining 9 of v2's "+14 with compliance" are:
- 9 criteria for 3 new lanes (article/image/ad) — **zero archived artifacts to calibrate against**. Premature.
- 6 compliance preconditions (SB-12, SB-15, ART-8, IMG-8, LI-11, ADE-compliance) — **rule content is gated on legal-review owner**. Shipping criterion shells while gating content is shape-only-mode renamed.

---

## Research-grounding audit (paper verification agent)

4 of 5 cited claims hold up; 1 is misapplied; details matter:

| Claim | Verdict | Action |
|---|---|---|
| KDD 2024 +41% citation lift | **VERIFIED w/ nuance** | Paper is real (arXiv 2311.09735). The +41% is *Position-Adjusted Word Count from Quotation tactic*, not raw citation count. Mechanism IS LLM-citation (correct for our use case), NOT classical SEO. **Source Emphasis** is actually the strongest tactic (+115%), unaccounted for in GEO-9. Rewrite the citation precisely; consider adding "Source Emphasis" as a GEO-9 sub-question. |
| arXiv 2605.06161 Policy Invariance | **VERIFIED** | Paper directly supports shadow-rubric mode (LLM judges flip verdicts on 9.1% of cases under meaning-preserving rewordings; 18-43% of flips on unambiguous cases). Free upgrade: adopt the paper's "Policy Invariance Score" + "Judge Card" output as evolution telemetry. |
| arXiv 2605.06939 J/ΔJ | **PARTIALLY VERIFIED — misapplied** | Paper supports *calibration-drift detection* (J vs ΔJ across model versions), NOT cross-family κ. Cross-family κ is a different lever. **Either revise framing or find correct citation for cross-family κ** (Rating Roulette is closer). |
| X 30-50% reach penalty | **VERIFIED, stronger than claimed** | Buffer 18.8M-post analysis: median engagement ~0% for non-Premium link posts since March 2025. 30-50% is from open-sourced X algorithm code (`TweetUrlMultiplier`); empirical impact is closer to 100% suppression for non-Premium. Two independent sources confirmed. |
| Rating Roulette α<0.8 | **VERIFIED** | Krippendorff's α<0.8 is the standard bar (not paper-specific). Confirms judges are the bottleneck. Also identifies key distinction: intra-rater (same judge, repeated runs) vs inter-rater (different judges) — v2 conflates them. |

**Net:** zero hallucinations. Every paper exists. The KDD-2024 mechanism is correct for our use case (LLM citation, not SEO). The J/ΔJ citation is the one that needs rewriting.

---

## Adversarial review (compound-engineering review agent)

Confidence-rated production failure modes if v2 ships as-is:

1. **Shadow-rubric mode never runs** — cache layer can't hold two rubric versions; team silently switches to v008 primary without comparison data (HIGH 0.80)
2. **A Klinika carousel ships with placeholder compliance rules** because operator wrote stubs under deadline pressure to unblock substrate gate (HIGH 0.85)
3. **Article_engine converges on AI-slop** that scores 5/5 on hook + 5/5 coherence — 4 criteria can't disambiguate "competent" from "good" (HIGH 0.85)
4. **MON-9 caps a correct digest** because operator updated `mentions/*.json` mid-week and substring match staled (MODERATE 0.65)
5. **σ ≥ 0.85 invariant fails the rollout it was designed to validate** — successful AUTO-CAPs catching real violations *raise* σ; principle is wrong-directional (HIGH 0.80)
6. **v1.5 decision made at week 5-6 by operator gut**, not the spec's triggers, because none of the trigger instrumentation exists (MODERATE 0.70)

Specific re-attack the adversarial review surfaced beyond v1's: **the v2 "Principle 6: substrate refuses fixture" is the v1 shape-only-mode failure-mode in a renamed costume.** Compliance criterion shells exist in the spec; rule content is gated. Under demo deadline pressure, operator writes placeholder content to unblock. Same failure mode, one layer of indirection added.

---

## Scope-guardian review (compound-engineering review agent)

YAGNI-strict recommendation: **demo window kernel = +5 criteria, not +14.** Cut Phase 3 entirely (3 new lanes, zero fixtures). Defer compliance YAML schema; hardcode 5-10 medical_pl trigger phrases inline (~30 LOC) when needed. Replace 4-week shadow-rubric mode (2× judge cost multiplier) with one-shot archive replay. Defer findings_brief schema (no kernel criterion references it). Keep Principles 1/3/4/6/7. Defer Principles 2/5.

Revised timeline: **2-3 weeks for +5 kernel + validation**, not 4-6 weeks.

---

## Phase-C re-rating (N=4-8 per lane, vs original N=1-3)

**MON-9** — FLAT on existing corpus (σ=0.0). Every archived monitoring artifact is zero-mention and never triggers fabrication. **Cannot be validated until a populated-mention fixture exists.** Currently a cliff-guard against a hypothetical failure.

**GEO-9** — FLAT-AT-FLOOR (σ=0.4). Every variant fails the criterion (institutional citations only, no named experts in `"..."` form). Catches a real corpus-wide gap that NO existing criterion penalizes. **Will produce ~10 generations of floor-stuck scores** until substrate mutates to cite named experts. Either accept the cliff or pair with substrate hint in `geo-session.md`.

**Most interesting discovery from this agent:** v175/geo claims "GWAS Nature Genetics >140 loci" and "PITX2 1.7x AFib risk" — claims **unverifiable from the source mayoclinic.org fixture page**. v182 claims "12,000+ new AFib patients annually" and "0.5% pericardial effusion rate" — same problem. GEO-9 wouldn't catch this; a hypothetical "source-grounded claim" criterion would. **This is a real fabrication signal hiding in the archive that v2's MON-9 doesn't catch in geo lane.**

**CI-9** — DISCRIMINATES (σ=2.2 on N=4). Real signal on triangulation depth. Partially redundant with CI-2 but adds yield on partial-data variants.

**SB-12 / SB-15** — N/A. No medical_pl/legal_pl fixture exists. PROPERLY DEFERRED.

**MA-9** — DISCRIMINATES at completion-margin (σ≈1.0), but tracks completion more than "descriptive vs decision-changing." Needs explicit rubric anchors before model can rate reliably.

---

## What the audit demands of v3

### Phase 0 (NEW — substrate fix; blocks everything)

Three substrate fixes, all in `src/evaluation/judges/`:

1. **Make session-judge produce per-criterion scores, not one global verdict broadcast 8×.** Audit specific files: `sonnet_agent.py` and `claude.py`. Investigate whether prompt asks for 1-10 and parser collapses to 3-level, or whether prompt itself only asks for binary.
2. **Persist per-criterion scores to `scores.json`** (not just `.last_eval_cache.json`). Add `dimension_scores` population to the score-write path.
3. **Add `rubric_version` field to score rows** so cross-version comparison becomes possible.

Without this, every rubric change is invisible at the per-criterion level.

### Phase 1 (REVISED — the +5 kernel only)

- MON-9 (fabrication AUTO-CAP) — defer activation until non-empty-mention fixture exists; validate against it before promotion
- MA-9 (decision-changing insight density) — write explicit rubric anchors first
- GEO-9 (named-expert attribution) — accept ~10 generations of floor-stuck scores; pair with substrate hint
- CI-9 (triangulation depth) — straightforward
- X-9 (algorithmic-citizenship AUTO-CAP) — empirically strongest; ship as-is with updated reach-penalty framing

Citations to fix:
- GEO-9: "+41% Position-Adjusted Word Count from Quotation tactic (KDD 2024, arXiv 2311.09735)" — and consider adding Source Emphasis as separate criterion (+115%)
- X-9: "median engagement ~0% for non-Premium link posts since March 2025 (Buffer 2026, 18.8M-post analysis); 30-50% multiplier penalty in open-sourced X algorithm"
- Cross-family κ principle: cite Rating Roulette + Preference Leakage, NOT J/ΔJ
- Add Policy Invariance Score + Judge Card as evolution telemetry (free upgrade from paper verification)

### Phase 2 (REVISED — one-shot archive replay, not shadow mode)

Replay the +5 kernel against existing archived artifacts in `autoresearch/archive/v*/`. Compare composite distributions. Single execution, single judge spend.

### Phase 3 (KILLED from demo window)

article_engine, image_engine, ad_engine — defer entirely. Revive when first 5 client deliverables produce ground truth.

### Compliance regime (REVISED — hardcode-first)

For Klinika storyboard: inline `MEDICAL_PL_TRIGGERS` list of ~10 phrases as substring check in storyboard's existing evaluator. ~30 LOC. No YAML schema. No `configs/compliance/` abstraction. Promote when a second lane needs the same rules or list grows past ~25 entries.

### Principles to keep / defer

- KEEP: 1 (negative controls), 3 (cross-family κ on +5 only, with corrected citation), 4 (cap precedence), 6 (substrate-gates-first as architectural rule), 7 (cost projection inline)
- DEFER: 2 (4-week shadow mode → one-shot replay), 5 (σ invariant — wrong-directional)

---

## The cheapest version of v3

If we strip even further: **Phase 0 (substrate fix) + the +3 deterministic AUTO-CAPs (MON-9, X-9, and one image equivalent when image_engine actually runs).** Skip MA-9 (judge-fuzzy), GEO-9 (10-gen floor compression), CI-9 (overlaps CI-2). Wait for first 5 Klinika/DWF deliverables to surface what's actually missing.

This is the "+3 kernel" the adversarial review's §1 argued for. It's defensible. JR's call.

---

## Files referenced

- Original v2 spec: `phase-d-master-spec-v2.md` (preserved)
- Original adversarial review: `adversarial-review.md` (preserved)
- This audit: `audit-findings-2026-05-13.md` (this file)
- Per-criterion stats dump: `/tmp/per_variant_crit_stats.json`
- Rubric definitions: `src/evaluation/rubrics.py` (lines 1391-1502)
- Judge implementations: `src/evaluation/judges/sonnet_agent.py`, `claude.py`
- Archive: `autoresearch/archive/v*/sessions/*/*/`, `.last_eval_cache.json`, `scores.json`
