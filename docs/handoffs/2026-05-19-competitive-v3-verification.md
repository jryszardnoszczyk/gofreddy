---
date: 2026-05-19
type: verification review
target: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (v3.6)
source: docs/handoffs/2026-05-19-competitive-v2-spot-check.md
reviewer-role: CI verification reviewer (1 of 8 parallel verifications)
status: complete
---

# CI v3.6 verification

This document verifies whether the v3.6 surgical edits actually closed the v2 spot-check findings, did not introduce new issues, and preserved the v3.4/v3.5 architecture.

## v2 findings vs v3 state (PASS / FAIL / PARTIAL per finding)

### Finding 1 — CI-4 score-1 anchor's "imagine the company's prior" CoT step (v2)

**v2 finding.** Step 1 asked the judge to "Identify the company's apparent priors from the brief's framing" — but the brief is written FOR an unknown reader at an unknown company with unknown priors. Double-imagination, high variance.

**v3 state.** CI-4 score-1 anchor now requires the brief to EXPLICITLY name the prior ("leadership currently believes X" / "our prior assumption was Y" / "we have been hedging on Z" / "the company narrative is W"). CoT Step 1 rewritten: "Identify priors the brief EXPLICITLY STATES it is challenging. ... If the brief does not explicitly name a prior it is contradicting, the criterion does not apply and emit 0.5 + 'unknown' + 'brief does not name the prior it is challenging.' Do not impute priors the brief leaves implicit." CoT Step 3 requires the rationale to quote or paraphrase the brief's own statement of the prior; absent that, score cannot be 1. Example sentence ("Our 'enterprise readiness' is the prior most likely to be wrong...") explicitly demonstrates the prior being named on the page. Score 0.5 anchor now has a split (a)/(b) — (a) for "no named prior" and (b) for "named but evidence thin."

**Verdict: PASS.** The fix is mechanically tight. The judge is forbidden from imputing priors; the brief must put the prior on the page. The example demonstrates the required shape. Step 3's "quote or paraphrase" requirement is the load-bearing closing — without it, the rewrite would still allow soft imputation. One residual concern: the burden now shifts to the workflow (the brief writer must self-disclose what prior it is challenging). If the substrate doesn't reliably emit explicit prior-statements, CI-4 will collapse to 0.5 across most generations and look broken; this is a substrate-readiness concern, not a judge-layer one, but should be tracked in §8.

### Finding 2 — CI-6 CoT Step 3 confabulation flagging (v2)

**v2 finding.** Step 3 asked the judge to "flag confabulations" — a deterministic check the judge can't reliably perform without source corpus access. The judge will hallucinate confabulation flags. Recommended: tighten to internal inconsistency only, or drop Step 3 and rely on structural_gate.

**v3 state.** CoT Step 3 now reads: "Flag any INTERNALLY-INCONSISTENT claims within the brief itself: date contradictions ... named-entity mismatches within the brief ... self-contradicting trajectory claims ... Entity/source/recency confabulation against external reality (does the cited URL resolve? does the named competitor exist? is the dated event within 90 days?) is verified by `structural_gate` (§8 anti-hallucination checks), NOT this criterion — the judge does not have source-corpus access and cannot perform those checks reliably." Three concrete examples of intra-brief inconsistency given: date contradictions, named-entity mismatches, self-contradicting trajectory claims.

**Verdict: PASS.** The fix is the right shape — the judge now does what the judge can do (internal coherence check) and routes what the judge cannot do (external verification) to `structural_gate`. The phrase "the judge does not have source-corpus access" is load-bearing and forces clarity. One small residual: §6a Goodhart-mode for CI-6 still reads "Entity confabulation / source confabulation / recency distortion (the 3 AI-specific failure surfaces) each force a score 0." That sentence is now inconsistent with the tightened CoT (CI-6 no longer detects external entity/source confabulation; structural_gate does, and structural_gate fails the artifact before the judge sees it). §6a should be tightened to say "internal inconsistency on entity / source / date references forces a score 0; external confabulation is caught upstream by structural_gate." Minor; not blocking.

### Finding 3 — CI-3 rejection-of-advantage 4th example (v2)

**v2 finding.** The "equally valuable — explicitly rejects an apparent advantage as replicable operational effectiveness" clause is theoretical without an example. The rejection path could become a workflow trick to score 1 without positive analytical work.

**v3 state.** CI-3 now has a 4th example, "Example D — rejection-of-advantage path." The example walks through an AI-lab competitor's apparent first-mover advantage on agentic tool use; rejects it as operational, not structural (6-month head start, matched by OpenAI Responses API in March, Gemini agent runtime in April); names what would have made it structural (curated training-data moat, proprietary RLHF corpus, compute/distribution lock-in) and concludes with the operational implication ("reallocate the planned counter-positioning spend").

**Verdict: PASS.** The example is concrete, vertical-appropriate (tech-savvy AI-lab framing per the broadened reader spec), and demonstrates the rejection actually doing analytic work — naming the would-be-structural factors and concluding with a strategic-implication. It does not invite Goodhart by template (a workflow that tried to slot-fill a "rejection" claim would still need to name the structural mechanism that is absent). One minor: the example is longer than Examples A/B/C and is also more "essay" than "sentence" — slight asymmetry with the other three examples. Not a blocker.

### Finding 4 — Multi-component bundle no client validation (v2 finding); was Substrate-Readiness Gate the right resolution?

**v2 finding.** The 5-component modular package is research-derived without a single client validation point. No evidence the client wants a 10–15 page bundle. The architectural trick solves judge-surface containment but no one asked for it; reader wants ONE artifact they can commit on. Optional G + H create shape-bifurcation. Recommended: ship Component A only as production-default; B–F as on-demand evidence.

**v3 state.** v3.6 added a Substrate-Readiness Gate in §1.5: "Component A (brief.md) ships at substrate-current ... Components B–F + optional G–H ship as substrate emission catches up ... Until Components B–F substrate emits, the lane structural-gate-fails 100% of sessions if v3.6 ships against them. The comprehensive scope is the SPEC TARGET; client-side shipping is gated on substrate readiness, not spec maturity." First-cohort posture clause added to §1.

**Verdict: PARTIAL.** The Substrate-Readiness Gate is the *operationally correct* resolution — it prevents v3.6 from shipping with a 100% structural-gate-fail because the emission layer can't produce B–F yet. It also de-facto realizes the v2 recommendation: in practice, only Component A will ship until substrate catches up. **However: this is not the same resolution the v2 reviewer recommended.** v2 said "ship A only as production-default; B–F as on-demand evidence the workflow CAN produce when challenged, until a real client has been observed using B–F." v3.6 says "the spec target stays at 5-component package; ship is gated on substrate." The underlying epistemological concern — *no real client has validated that the modular package shape is what they want* — is still unaddressed. The Substrate-Readiness Gate punts the validation problem rather than answering it. Once substrate catches up, the lane will ship a 10–15 page package to clients with zero prior evidence any client wants it. §8c retains an internal validation gate ("Eyeball whether ... the modular package delivers genuinely more value than Component A alone"), but eyeballing is JR-internal, not client-observed. The v2 missing question — *would the second client open Components B–F?* — is still not on the list.

### Finding 5 — First-cohort overfitting (v2)

**v2 finding.** v3.5 broadened to US-primary + 7 verticals. Residual concern: Klinika (healthcare owner-operator) is out of family vs. founder-CEO of an AI lab — straddling two reader archetypes.

**v3 state.** v3.6 added §1 "First-cohort posture" paragraph: "Klinika + DWF are the only two onboarded clients as of 2026-05-19 (both Polish-language, both regulated-vertical). US-primary substitute readers above are the architectural target as the client base expands Q3-2026+. Polish-language fixture passes are required before any v3.6 spec lock against Klinika or DWF sessions; US-primary fixture passes are required for the architectural-target validation. The straddle is real and intentional during cohort expansion; revisit when cohort #5 onboards from an under-represented vertical."

**Verdict: PARTIAL.** v3.6 *acknowledges* the straddle explicitly — "the straddle is real and intentional during cohort expansion" — but acknowledging is not resolving. The healthcare-owner-operator reader is still on the substitute-reader list with founder-CEO of an AI lab. The two readers commission CI for fundamentally different reasons; a single criterion set (especially CI-3 structural mechanism, CI-4 uncomfortable truth, CI-6 evidence chain) will under-discriminate one or the other in practice. v3.6's posture is "monitor, revisit at cohort #5" — defensible operationally, but it does NOT close the v2 finding. The honest reading: v3.6 has accepted the straddle as a known risk rather than removing it.

### Finding 6 — Per-component first-cohort overfitting on Component B (v2)

**v2 finding.** Component B (profile cards) likely overfits hardest. A profile-card template optimized against DWF (legal partnership profile) will not transfer to Anthropic (AI-lab founder profile) without different fact-classes, hiring signals, and AEO presence sections. The spec acknowledges vertical-template-variants in §6.4 of research but doesn't operationalize how the lane picks which variant to instantiate per fixture.

**v3 state.** No targeted edit in v3.6 for this finding. §1.5 Component B section still says: "AI-native attributes section present when the competitor is AI-adjacent (model surface named, AEO presence reported)" — vertical-conditional but no operationalization of vertical-variant routing. §8c retroactive validation against the 4 Phase-3 fixtures is the closest thing to a mitigation. Substrate-Readiness Gate defers the problem until B substrate emits.

**Verdict: FAIL.** The Substrate-Readiness Gate masks this issue rather than addressing it — once B substrate emits, the vertical-template routing problem will resurface at the structural_gate layer with no design for resolution. Component B's structural_gate checks (≥3 cards, ≥10 facts per card, AEO when AI-adjacent) are necessary but not sufficient — they don't constrain *which* facts get emitted, and a workflow optimized against DWF profile-card facts will emit those same fact-classes for Anthropic. The "vertical-conditional dimension selection" promised in §1.5 D component is not specified for B. This is a known unresolved problem deferred to a future date.

### Finding 7 — Polish first-cohort handling in modular layer (v2)

**v2 finding.** §1 broadened US-primary, but Components B–F have no equivalent broadening pass — the deep-profile-card format implicitly carries Polish-legal / Polish-medical first-cohort substrate assumptions (named sources like Pirical for legal, RealSelf for healthcare). If the spec is US-primary, per-component primary-source defaults per vertical need to be US-anchored (Leopard Solutions for US legal, Glassdoor + LinkedIn for US healthcare).

**v3 state.** §3d "modern levers" lever 5 names both "Pirical / Leopard Solutions for legal" (UK + US side-by-side) and acknowledges "Levels.fyi / Paraform for AI; manual LinkedIn elsewhere." No equivalent US-primary anchoring pass on Components B–F per-component primary sources. First-cohort posture clause in §1 doesn't propagate to the per-component check sets. AEO Component G names US-anchored engines (ChatGPT, Perplexity, Claude search, Gemini, Brave, You.com) — good, but that's Component G only.

**Verdict: FAIL.** v3.6 did not propagate the §1 US-primary broadening to per-component source defaults. Components B–F will inherit Polish-first-cohort source assumptions from the substrate as it currently exists, and the Substrate-Readiness Gate will gate the *shape* but not the *source-vertical-alignment*. When Component B substrate emits for a US AI-lab fixture, the workflow will likely default to Polish-legal-substrate hiring-source patterns unless the substrate itself is US-anchored.

## New issues introduced by v3 edits

**Issue 1 — CI-4 score-0.5 split has a coverage gap.** The new score-0.5 anchor distinguishes (a) "brief does not name the prior" from (b) "named but evidence thin." But the CoT Step 1 mandates emitting 0.5 + "brief does not name the prior it is challenging" *whenever the brief doesn't name a prior* — which means CI-4 will return 0.5 on every brief that doesn't happen to name a prior, even when the brief contains genuine uncomfortable findings. This forces a structural floor of 0.5 on a likely majority of generations, which compresses the criterion's discriminative range (the mean shifts toward 0.5 instead of being binary-distributed). Per design guide §11.5, mean compression toward the middle is a redesign signal, not a calibration one. **The v3.6 fix may have replaced a high-variance bug with a mean-compression bug.** Track CI-4's mean and variance from generation 1; if mean compresses toward 0.5 within 3 generations, the fix needs another pass — likely making the "explicit prior" requirement softer (e.g., "either explicit OR derivable from a clearly-stated client engagement context").

**Issue 2 — §6a Goodhart-mode for CI-6 is now inconsistent with the tightened CoT.** §6a still says external entity/source/recency confabulation forces a score 0, but the CoT now routes those to structural_gate. Either §6a's CI-6 bullet needs updating ("internal inconsistency on entity/source/date references forces a score 0") or §6a needs a note that the CoT preempts. Minor; not blocking ship.

**Issue 3 — Substrate-Readiness Gate creates an evaluation paradox.** §1.5 says "Until Components B–F substrate emits, the lane structural-gate-fails 100% of sessions if v3.6 ships against them." This means: until substrate catches up, the lane cannot use v3.6 at all (it would 100% fail). But the validation gate at §8c says: "run Components B–F retroactively against the current 4 Phase-3 fixtures." Those fixtures cannot produce Components B–F (because substrate doesn't emit them yet), so the §8c gate cannot fire. v3.6 has created a chicken-and-egg: cannot ship without §8c validation, cannot validate without substrate emission, cannot get substrate emission without shipping the spec that defines the components. The resolution path is implied (build substrate emission first, validate retroactively, then ship), but the dependency order is not spelled out anywhere.

**Issue 4 — v3.6 revision_history entry is mis-numbered.** Frontmatter lists "2026-05-19 v3.6" first, then "2026-05-19 v3.5" second — but v3.5 chronologically precedes v3.6. Minor cosmetic issue.

## Architecture preservation check

- 6 criteria preserved? **YES.** CI-1 through CI-6 all present; CI-6 documented exception clause preserved.
- CI-1 / CI-2 / CI-3 (other than 4th example) / CI-5 prose unchanged? **YES.** Spot-checked CI-1 (capacity-sized recommendation, prioritization discipline, asymmetric-opportunity test all preserved verbatim); CI-2 (3 vertical examples preserved); CI-3 (Examples A/B/C preserved, Example D added); CI-5 (3 vertical examples and CFO-recognizable-cost language preserved).
- v3.4 surgical restorations preserved? **YES.** CI_BANNED_PHRASES 12-phrase list present in §8; SOV-negation-filter check present; capacity-sized recommendation, prioritization discipline, asymmetric-opportunity test, gap-as-intelligence reframe all preserved.
- 5-component modular package preserved? **YES.** Components A–F + optional G/H still defined with all size envelopes and structural_gate check sets preserved. Substrate-Readiness Gate is additive, not subtractive.
- §5 wrapper unchanged? **YES.** Verbatim from v3.5.

## Overall verdict — NEEDS-MORE-EDIT

The three judge-layer edits (CI-4 CoT, CI-6 Step 3, CI-3 Example D) are well-executed and close the v2 judge-layer findings cleanly — **PASS on findings 1, 2, 3**. The Substrate-Readiness Gate is operationally sound but does not address the underlying v2 epistemological concern (no client validation of the modular-package shape) — **PARTIAL on finding 4**. The first-cohort posture clause acknowledges the healthcare-vs-AI-lab straddle but does not resolve it — **PARTIAL on finding 5**. Per-component first-cohort overfitting and Polish first-cohort source-anchoring in B–F are **FAIL** — v3.6 did not edit them.

The v3.6 edits also introduced a likely new mean-compression risk in CI-4 (score 0.5 floor on every brief lacking an explicit prior statement) that warrants monitoring from generation 1, and a §6a/CoT inconsistency in CI-6 that should be cleaned up before ship.

**Recommendation:** Ship the judge-layer edits (CI-4, CI-6, CI-3 Example D) as v3.7. Defer the modular-package edits (B–F vertical-template routing, US-primary source-anchoring) to a v3.8 pass that does the per-component broadening §1 already received. Add a CI-4 mean-compression watch to §8 open questions. Reconcile §6a's CI-6 bullet with the new CoT routing.

## Relevant file paths

- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (v3.6 target)
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/handoffs/2026-05-19-competitive-v2-spot-check.md` (v2 findings)
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/rubrics/judge-design-guide.md` (design guide)
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/handoffs/2026-05-19-competitive-v3-verification.md` (this file)
