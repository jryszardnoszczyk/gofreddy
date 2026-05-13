---
date: 2026-05-13
phase: D-v3 (post-audit reframe — in-place update of v2)
topic: judge design master spec — reframed after 5-agent audit
status: awaiting operator approval on Phase 0 + +5 kernel
supersedes: phase-d-master-spec.md (v1) and earlier v2 framing
audit_source: audit-findings-2026-05-13.md
---

# Phase D Master Spec — Reframed Post-Audit

This file was v2 ("+14 kernel"). The 2026-05-13 5-agent audit invalidated v2's premise. v2 has been rewritten in place — v3 in spirit, same filename. **The audit findings at `audit-findings-2026-05-13.md` are the load-bearing source document. Read that first.**

## Audit headline — the load-bearing discovery

**The existing 52 criteria don't behave as 52 independent signals.**

Direct evidence from `autoresearch/archive/v006/sessions/monitoring/Shopify/.last_eval_cache.json`: all 8 MON criteria score `1.0` with **byte-identical feedback strings**. The session-judge produces one global verdict per artifact and stamps it onto every criterion. Per-criterion independence is fictional at the data layer.

Cross-lane empirical scan (~1,705 score rows across 5 lanes):

| Pathology | Evidence |
|---|---|
| **3-level scoring grain** | Rubrics declare `"gradient"` (1-10); session-judge writes only {0.0, 0.5, 1.0}. v2's σ-invariant math assumed a scale that doesn't exist. |
| **Identical-feedback broadcast** | 66% of sessions emit byte-identical `feedback` across all 8 criteria. The judge isn't scoring per-criterion. |
| **Ceiling-bound rubrics** | MON: mean 0.932-0.937, σ 0.097-0.099 (uniform across all 8 criteria); SB: mean 0.980 σ 0.027; CI: mean 0.900-0.950 σ 0.112-0.137. Only GEO has criterion-level variance. |
| **No rubric_version in archive** | `RUBRIC_VERSION` constant exists at `src/evaluation/rubrics.py:1516`; DB schema has the column; autoresearch archive (`scores.json`, `.last_eval_cache.json`) doesn't persist it. Cross-version comparison from archive is impossible. |
| **No `dimension_scores` in archive** | DB has the column; archived `scores.json` has it empty. Per-criterion data lives only in `.last_eval_cache.json` (session-keyed, easily overwritten). |

**Implication:** Adding +14 criteria on top of this substrate would change nothing measurable. The judges don't use the existing 52 per-criterion. **Phase 0 — substrate fix — is now load-bearing for the entire program.**

## TL;DR — v1 → v2 → v3 (this file)

| Metric | v1 (2026-05-12) | v2 (2026-05-13 morning) | v3 (post-audit) |
|---|---|---|---|
| New criteria | +55 | +14 | **+5** |
| AUTO-CAPs (deterministic only) | 11 | 5 | 2 (MON-9, X-9); 3 deferred (IMG-3, ADE-3, compliance) |
| New structural inputs | 4 | 2 | **0** (hardcode-first compliance; defer findings_brief; defer voice_persona; defer brand-style-guide) |
| Shadow-rubric mode | — | 4 weeks parallel | **One-shot archive replay** |
| Score-distribution invariant | — | σ ≥ 0.85 (1-10 grain) | DEFERRED (wrong-directional; grain doesn't match data) |
| New lanes (article/image/ad) | +24 criteria | +12 criteria | **KILLED from demo window** |
| Substrate work | — | None | **Phase 0 added — load-bearing** |
| Timeline | 6 weeks (claimed) | 4-6 weeks | **2-3 weeks** |

## What v3 ships

### Phase 0 (NEW — substrate fix; blocks everything)

The audit's discovery makes this load-bearing. Without these three fixes, every rubric change is invisible at the per-criterion level.

**0.1 — Per-criterion scoring fix.** Investigate the session-judge prompt at `EVOLUTION_JUDGE_URL` (port 7200; backend code outside this repo) and `autoresearch/archive/v*/scripts/evaluate_session.py`. The script iterates criteria + builds isolated per-criterion prompts (line 308: `_build_prompts_isolated`), but the judge response broadcasts one verdict across the results array. Either (a) the prompt asks for all criteria in one call and judge collapses, or (b) per-criterion calls return correctly but parsing replicates one response across criteria. **Determine which; fix at root.** Acceptance: re-run any archived monitoring fixture; per-criterion `feedback` strings differ for the 8 MON criteria.

**0.2 — Persist per-criterion to autoresearch archive.** Make `scores.json` write the `dimension_scores` array (currently empty) and write `rubric_version` alongside composite. Add equivalent to `metrics/<lane>.jsonl`. Without this, no cross-version analysis is possible from the archive.

**0.3 — Decide score grain explicitly.** Either (a) keep 3-level (0/0.5/1) and rewrite spec language that assumes 1-10, or (b) move to 1-10 gradient and update the judge prompt + parser. Audit says **(a) is the cheaper honest fix** — the existing rubrics work fine at 3-level; v3 spec language is rewritten for 3-level below. Acceptance: spec uses {0, 0.5, 1} consistently for criterion scores; composite is 0-10 derived from weighted mean × 10.

**Phase 0 estimate:** 3-5 days. Blocks Phase 1.

### Phase 1 — The +5 evidence-backed kernel

Per-lane PRs in priority order. Citations have been verified (see `audit-findings-2026-05-13.md` §"Research-grounding audit").

**1.1 — `monitoring + MON-9` (fabrication AUTO-CAP).** Substring-match check: every numeric/named claim in the digest must appear in `mentions/<week>.json`. AUTO-CAP to 0 (3-level grain) on violation. **Validation gap:** all archived monitoring fixtures are zero-mention; MON-9 cannot be validated against current archive. Seed at least 3 populated-mention fixtures (Lululemon, Ramp, Shopify with real mentions) before promotion. Acceptance: re-run seeded fixtures + intentional fabrication injection → cap fires on injected; doesn't fire on clean.

**1.2 — `x_engine + X-9` (algorithmic-citizenship AUTO-CAP).** Regex check for URLs in `[BODY]` / `[REPLY]` blocks. AUTO-CAP to 0. **Strongest empirical validation:** Phase C 3/3 archived drafts violate; Buffer's 18.8M-post analysis shows median engagement ~0% for non-Premium link posts since March 2025 (paper-verification agent confirmed; numbers stronger than v2 framing claimed). Acceptance: re-run current 3 archived drafts → all cap; clean drafts (no external links) score normally.

**1.3 — `geo + GEO-9` (named-expert quoted attribution).** Named individual cited in `"..."` form with explicit credential or institutional role nearby. Gradient (0 / 0.5 / 1), no AUTO-CAP. **Evidence:** KDD 2024 GEO paper (arXiv 2311.09735) — verified; +41% Position-Adjusted Word Count from Quotation tactic on LLM-citation systems (ChatGPT/Perplexity/SGE), NOT classical SEO. **Expected behavior:** every archived geo variant currently fails this criterion (institutional cites only); GEO-9 will produce floor-stuck scores for ~10 evolution generations until substrate learns named-expert citation. Accept this as the intended cliff or pair with substrate hint in `geo-session.md` mentioning named-expert pattern. **Free upgrade available:** KDD paper also shows "Source Emphasis" tactic at +115% (stronger than Quotation). Consider adding "Source Emphasis" sub-question to GEO-9 prompt: does the artifact name + emphasize the institutional source in the leading sentence?

**1.4 — `competitive + CI-9` (triangulation depth).** Each insight must rest on ≥2 independent source classes (e.g., scraped landing page + public earnings call ≠ same class; two landing pages = same class). Gradient. Strengthens existing CI-2 sub-question rather than replacing it. **Evidence:** N=4 audit sample σ=2.2 across triangulation levels — DISCRIMINATES. Partial CI-2 overlap accepted; CI-9 adds yield on partial-data variants (v018 vs v095 in audit). Acceptance: re-rate the 4 surveyed competitive variants; CI-9 ranks differently than CI-2 alone.

**1.5 — `marketing_audit + MA-9` (decision-changing insight density).** Fraction of findings that would change a marketing decision vs descriptive observations or governance recommendations. Gradient. **Evidence:** N=4 audit sample σ≈1.0 — discriminates but tracks completion more than the deeper "decision-changing" axis. **Mandatory before promotion:** write explicit rubric anchors distinguishing decision-changing from governance. Anchor examples:
- DECISION-CHANGING: "Stripe should split state-of-business messaging by buyer stage" (action-forcing, owner-implied, budget-impacting)
- GOVERNANCE: "Create a canonical proof register before claims are reused" (process recommendation, no decision flip)
- DESCRIPTIVE: "Anthropic's homepage emphasizes safety" (observation, not action)

Acceptance: re-rate the 4 v006 audit variants (Stripe, DWF, Anthropic, Perplexity) with anchors; σ holds or grows.

**Phase 1 estimate:** 5-7 days.

### Phase 2 — One-shot archive replay (not 4-week shadow mode)

Replay the +5 kernel against existing archived artifacts in `autoresearch/archive/v*/`. Compare composite distributions across the archive with vs without the kernel. Single execution, single judge spend.

This replaces v2's Principle 2 (4-week parallel shadow mode). Audit caught: cache-key collision under two-version mode, no v007 baseline for new lanes, 4 weeks of 2× judge cost doesn't fit demo window.

**Phase 2 estimate:** 1-2 days.

### Phase 3 — KILLED from demo window

article_engine, image_engine, ad_engine REJECTED. Zero archived artifacts to calibrate against; 4 criteria × 4 variants × 30 generations × 5 fixtures is the same calibration-sparsity v2 inherited from v1. Revive lane-by-lane when first 5 client deliverables produce ground truth.

Klinika + DWF demos run through monitoring + marketing_audit + geo (+ possibly storyboard + x_engine + linkedin_engine). They do not need new lanes.

### Compliance regime — hardcode-first, not YAML

Replaces v2's `configs/compliance/{medical_pl,legal_pl}/rules.yaml` schema work. When Klinika storyboard ships:

```python
# storyboard/scripts/evaluate_session.py (or equivalent)
MEDICAL_PL_TRIGGERS: list[str] = [
    # hand-curated by JR + legal review, ~10 phrases
    "100% bezpieczne",
    "gwarantujemy efekt",
    # ...
]

def check_medical_pl_compliance(artifact_text: str) -> bool:
    return not any(t in artifact_text.lower() for t in MEDICAL_PL_TRIGGERS)
```

~30 LOC. No `configs/compliance/` directory. No YAML schema. Promote to YAML when (a) a second lane needs the same rules, OR (b) the trigger list grows past ~25 entries.

This is YAGNI applied to compliance. v2's abstraction was correct architecture for steady-state but premature for demo window.

## Principles — kept / revised / deferred

| Principle | v2 status | v3 verdict | Rationale |
|---|---|---|---|
| 1 — Negative controls in V-tests | new | **KEEP** | Cheap; prevents silent false-positive caps |
| 2 — Shadow-rubric mode 4 weeks | new | **REPLACE with one-shot replay** | Cache collision; 2× judge cost doesn't fit window; can't compute for new lanes |
| 3 — Cross-family Cohen's κ per criterion | new | **KEEP (corrected citation)** | Cite Rating Roulette (arXiv 2510.27106) + Preference Leakage (arXiv 2502.01534), NOT J/ΔJ (arXiv 2605.06939 — paper actually supports calibration-drift, not cross-family agreement) |
| 4 — Cap precedence rules | new | **KEEP** | Pure documentation + ~20 LOC; resolves real ambiguity |
| 5 — σ(v008) ≥ 0.85 × σ(v007) invariant | new | **DEFER** | Wrong-directional (successful AUTO-CAPs *raise* σ); 1-10 grain doesn't exist; threshold has no derivation |
| 6 — Substrate gates first, judge criteria second | new | **KEEP** (architecture only) | Inline trigger lists ARE the substrate gate; criterion shells don't exist until rules ship |
| 7 — Cost projection up-front | new | **KEEP** | Already inline; zero ongoing cost |
| **NEW: Policy Invariance Score + Judge Card** | — | **KEEP** | Free upgrade from arXiv 2605.06161 (verified). 9.1% of judge verdicts flip on meaning-preserving rewording; 18-43% of flips on unambiguous cases. Adopt as evolution telemetry. |
| **NEW: Substrate-fix-first** | — | **KEEP** | Phase 0 is load-bearing per audit |

## Architectural decisions — revised

### Decision 1: Compliance regime → hardcode-first inline lists (REVISED)
Was: shared YAML rule files. Now: inline `MEDICAL_PL_TRIGGERS` / `LEGAL_PL_TRIGGERS` lists at the evaluate_session.py call-site for each lane that needs them. Abstract to YAML on the 2nd lane or 25th rule.

### Decision 2: AUTO-CAP applied selectively (REVISED FURTHER)
v1 had 11 AUTO-CAPs; v2 had 5; v3 ships 2:
- **MON-9** (fabrication — substring match)
- **X-9** (external links — regex)

3 deterministic AUTO-CAPs deferred until lanes need them:
- IMG-3 (Pillow canvas measurement) — defers with image_engine
- ADE-3 (Meta 20% text overlay) — defers with ad_engine
- Compliance triggers (medical_pl, legal_pl) — inline regex check per lane, deterministic when phrases ship

### Decision 3: New structural inputs — ALL deferred
- voice_persona/ — defer to v1.5 (gated on 2+ lanes needing it)
- findings_brief schema — defer (no +5 kernel criterion references it)
- compliance YAML — replaced with hardcode-first
- brand-style-guide YAML — defer to v1.5 (gated on first Klinika brand-stamped artifact)

Phase 0's persistence work is the only structural fix in v3.

### Decision 4: Mode-conditional firing in storyboard — STILL DEFERRED
Single 8-criterion rubric. SB-12 / SB-15 compliance criteria not added; medical_pl/legal_pl triggers inline at evaluator call when fixture metadata indicates Klinika or DWF.

### Decision 5: Vision-judge architecture — DEFERRED with image_engine
No vision-judge work in demo window. `render_judge.py` (Gemini 2.5 Flash, shipped 2026-05-12) continues handling HTML/PDF reports; that's a separate code path.

### Decision 6: Voice fidelity — STILL DEFERRED
Same v2 verdict; corpus < 50K words.

## Citation fixes from paper-verification audit

Audit found 4/5 v2 citations hold up, 1 misapplied, 2 stronger than v2 claimed. Updates for v3:

**GEO-9 citation rewrite:**
> +41% Position-Adjusted Word Count from Quotation tactic on LLM-citation systems (Aggarwal et al., "GEO: Generative Engine Optimization," KDD 2024 / arXiv 2311.09735). Mechanism is LLM citation patterns (ChatGPT, Perplexity, SGE), not classical Google SEO. Source Emphasis tactic in same paper shows +115% — stronger lever, optional sub-question in GEO-9 prompt.

**X-9 citation rewrite:**
> Median engagement ~0% for non-Premium link posts since March 2025 (Buffer 2026, 18.8M-post analysis across 71K accounts). Open-sourced X recommender shows 30-50% multiplier penalty in `TweetUrlMultiplier`. Empirical impact: closer to 100% suppression than 30-50%.

**Cross-family principle citation rewrite (Principle 3):**
> Rating Roulette (Haldar & Hockenmaier, EMNLP Findings 2025 / arXiv 2510.27106) shows intra-rater Krippendorff's α < 0.8 across LLM judges — "almost arbitrary in the worst case." Preference Leakage (Li et al., arXiv 2502.01534) shows judges biased toward training-data-sharing models. **Distinguish intra-rater (same judge repeated, Rating Roulette) from inter-rater (different judges, Cohen's κ).** v2 conflated them. The cross-family check uses inter-rater κ across Claude/Gemini/GPT families.

**Adopt as new principle (free upgrade):**
> Policy Invariance (Weng et al., arXiv 2605.06161): LLM safety judges flip verdicts on 9.1% of cases under meaning-preserving rewording; 18-43% of flips on unambiguous cases. Adopt the paper's Policy Invariance Score + Judge Card protocol as evolution telemetry. Score every kernel criterion under 2-3 meaning-preserving rubric-prose rewordings monthly; flag criteria with verdict-flip rate > 10%.

**Removed citation (misapplied):**
> J/ΔJ (arXiv 2605.06939) — paper supports calibration-drift detection across model versions, NOT cross-family inter-rater κ. v2 referenced this incorrectly. Removed from v3.

## Implementation order

### Phase 0 — Substrate fix (3-5 days, blocks everything)
0.1 Per-criterion scoring fix (investigate prompt → fix at root)
0.2 Persist `dimension_scores` + `rubric_version` to `scores.json` + `metrics/<lane>.jsonl`
0.3 Decide score grain explicitly (3-level vs 1-10; recommend 3-level)

### Phase 1 — +5 kernel (5-7 days)
1.1 monitoring + MON-9 (seed populated-mention fixtures first)
1.2 x_engine + X-9 (validate against archived drafts)
1.3 geo + GEO-9 (with anchor prose + optional Source Emphasis sub-question)
1.4 competitive + CI-9 (re-rate audit's 4 variants)
1.5 marketing_audit + MA-9 (write explicit anchors before promotion)

### Phase 2 — Validation (1-2 days)
2.1 One-shot archive replay (kernel vs no-kernel composite distributions)
2.2 Negative controls for MON-9 and X-9 (clean fixtures → no cap)
2.3 Cross-family κ on +5 only (extend `judge_calibration.py`)

### Phase 3 — KILLED from demo window
article_engine, image_engine, ad_engine REJECTED.

### Phase 4 — Real-world validation (post-demo)
4.1 First 5 Klinika deliverables — what does the kernel catch vs miss?
4.2 First 5 DWF deliverables — same.
4.3 On observed kernel-miss: ship a single new criterion targeting the observed failure. Not a v1.5 batch revival; one criterion per observed failure mode.

## What's REJECTED (cut for cause, not deferred)

v3 rejects the "defer to v1.5" framing. Each item below is rejected for a specific cause. None re-enters scope without **new evidence** (not new arguments, not new research, not new aspirations).

### REJECTED — design failures or judge-fuzzy

| Item | Reason for rejection |
|---|---|
| MON-10..13 | Phase C confirmed monitoring rubric at ceiling; more criteria compress further |
| GEO-7a/7b/8a/8b splits, GEO-10/11/12 | Geo evolution issue is substrate-side (gpt-5.5 cybersecurity filter, per `project-geo-regression-root-cause-2026-05-12.md`), not rubric-side |
| CI-10 (source-class diversity), CI-11 (forward-signal) | Gold-plating per adversarial review §1; CI-11 high-risk to grade |
| MA-10, MA-11 | Overlap with existing MA-1 + MA-2; double-counting |
| X-7, X-8, X-10 | Judge-fuzzy; X-7 overlaps X-2; X-8 reply-worthiness un-gradable; X-10 aesthetic |
| LI-3 split + LI-7..10 | Inferred-from-research without empirical validation; principle: no inferred-from-research |
| ART-4 voice-fidelity rolling-window | Design theater per adversarial review §3: 2σ threshold has no calibration source; corpus < 50K words guarantees noise; components not independent |
| ART-5, ART-6, ART-7 | Inferred-from-research; no archived artifacts to validate |
| IMG-2, IMG-4, IMG-6, IMG-7 | Inferred-from-research; vision-judge cost compounds across 4 criteria |
| ADE-2, ADE-5, ADE-6 | Judge-fuzzy + judge-inflatable; ADE-5 variant diversity tuple-tag is gameable |
| Rolling-window voice fidelity (any lane) | Design theater per adversarial review |
| σ ≥ 0.85 invariant (Principle 5) | Wrong-directional (successful AUTO-CAPs raise σ); grain doesn't match data |
| Shadow-rubric mode 4-week (Principle 2) | Cache-key collision; 2× judge cost not justified; can't compute for new lanes; replaced by one-shot replay in Phase 2 |
| voice_persona shared abstraction | No lane currently needs it; YAGNI |
| findings_brief schema | No +5 kernel criterion references it |
| brand-style-guide YAML schema | No client onboarded; build inline when first Klinika brand-stamped artifact needs it |
| Compliance YAML schema | Hardcoded inline lists are simpler at 1-lane scale; abstract only if 2+ lanes ever need it |
| SB-12, SB-15, LI-11, ART-8, IMG-8, ADE-compliance criterion shells | Replaced architecturally with inline `MEDICAL_PL_TRIGGERS` / `LEGAL_PL_TRIGGERS` checks at evaluator call-site |

### NOT IN SCOPE — would be a fresh build, not a deferral

These don't exist and aren't planned. If/when client work makes one necessary, that's a new program with its own design pass — not a continuation of this one.

| Item | What would trigger a fresh build |
|---|---|
| article_engine lane | A Klinika or DWF client deliverable specifically requires long-form articles through autoresearch (not landing-page copy, not LinkedIn posts) |
| image_engine lane | Either client commits to image-led campaigns where autoresearch composes visuals |
| ad_engine lane | Either client commits paid-ads spend through autoresearch-generated cohorts |
| Vision-judge architecture | image_engine lane gets fresh-built (above) |
| Storyboard mode-conditional firing | Both Klinika educational AND DWF brand_authority storyboard fixtures get authored and evaluated |

## Cost projection (revised)

Per audit's verified Phase 0 + +5 kernel:

- **Current rubric eval**: 52 criteria × 2 families × N × M × G — baseline
- **v3 kernel eval**: 57 criteria (current 52 + 5) × 2 families × N × M × G — **~10% increase** (was v2's claimed 27%)
- **Phase 0 work**: substrate fix has no ongoing eval cost; one-time engineering
- **Phase 2 replay**: single archive sweep at archive variant count; ~$50-100 one-time
- **Vision-judge**: $0 (deferred with image_engine)

Total ongoing eval cost increase: ~10%. One-time validation cost: ~$100.

## Realistic timeline (revised)

- **Phase 0 (substrate fix)**: 3-5 days — blocks everything
- **Phase 1 (+5 kernel)**: 5-7 days
- **Phase 2 (one-shot replay + cross-family κ)**: 1-2 days
- **Total to client-demo-ready**: **2-3 weeks** (was v2: 4-6)
- **v1.5 (deferred lanes + criteria on observed-failure trigger)**: post-demo

Saves 2-3 weeks against v2; leaves slack in 1-2 month window for legal-review work and the actual client deliverables.

## Open questions still requiring operator input

1. **Legal-review owner + budget for medical_pl + legal_pl trigger phrases** (Resolve-Before-Planning #2). ~10 phrases per regime; ~4 hours of JR + lawyer time. Lanes don't enforce compliance on Klinika/DWF until this lands. Highest-priority operator task.

2. **Dr. Maria + DWF partner corpus consent** (Resolve-Before-Planning #1). Gates voice_persona (already deferred). Not blocking +5 kernel.

3. **Score grain decision** — confirm 3-level (0/0.5/1) is acceptable or push to 1-10 gradient. v3 recommends 3-level (it's what the substrate actually produces; rewriting the prompt + parser for 1-10 is a separate program). Operator call.

4. **Klinika/DWF demo route confirmation** — assumed monitoring + marketing_audit + geo + maybe storyboard. If JR plans to ship articles, images, or ads through autoresearch for these specific demos, Phase 3 reactivates lane-by-lane on that signal.

## What v3 explicitly does not do

- Doesn't write trigger-phrase content for compliance (gated on legal review; ~10 phrases per regime)
- Doesn't change MA's JSON-envelope architecture
- Doesn't ship voice_persona, findings_brief, brand-style-guide, or compliance YAML
- Doesn't add criteria for article/image/ad lanes (KILLED from demo window)
- Doesn't run shadow-rubric mode (replaced with one-shot replay)
- Doesn't track score-distribution σ invariant (deferred — wrong-directional)
- Doesn't fix the judge-service backend prompt itself directly (Phase 0 investigates; root-cause fix may be in the port-7200 service code outside this repo)

## Next step

**Operator decision required:** approve Phase 0 + +5 kernel + revised principles, or push back. On approval, `/ce:plan` for Phase 0 → Phase 1 → Phase 2.

## Files to read for full context

### v3 canonical (read these for current state)
- `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-master-spec-v2.md` (this file — v3 in place)
- `docs/brainstorms/2026-05-12-judge-design-deep-research/audit-findings-2026-05-13.md` (load-bearing)
- `docs/brainstorms/2026-05-12-judge-design-deep-research/HANDOFF.md`

### Earlier versions (preserved for history)
- `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-master-spec.md` (v1)
- `docs/brainstorms/2026-05-12-judge-design-deep-research/adversarial-review.md` (v1 → v2 critique)
- `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-rubrics/<lane>.md` × 10 (per-lane v1 specs)

### Supporting (still load-bearing)
- `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-a-lane-purposes.md`
- `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-b-research/<lane>.md` × 10
- `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-c-variant-ratings.md`
- `docs/brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md`

### Code touchpoints
- `src/evaluation/rubrics.py:1391-1502` — rubric definitions (kernel additions land here)
- `src/evaluation/rubrics.py:1516` — `RUBRIC_VERSION` constant
- `src/evaluation/judges/` — subprocess runners (sonnet_agent.py, claude.py, openai.py)
- `autoresearch/judges/quality_judge.py` — thin HTTP client to `EVOLUTION_JUDGE_URL:7200`
- `autoresearch/judge_calibration.py` — extend for Principle 3 (cross-family κ)
- `autoresearch/archive/v*/scripts/evaluate_session.py` — per-criterion prompt builder (Phase 0.1 investigation)
- `autoresearch/archive/v*/sessions/<lane>/<fixture>/.last_eval_cache.json` — empirical evidence of broadcast pathology
