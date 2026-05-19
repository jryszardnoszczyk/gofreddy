---
date: 2026-05-19
type: adversarial spot-check — MON v2 spec
target: docs/handoffs/2026-05-18-judge-design-step1-monitoring.md (v2)
reviewer-mode: adversarial — falsify premises, surface assumptions, stress-test decisions
companion: docs/research/2026-05-19-monitoring-comprehensive-scope.md
sibling-precedent: docs/handoffs/2026-05-19-monitoring-v1-spot-check.md (if any), CI v3.4 spot-check pattern
verdict-summary: MOSTLY-SOUND with three load-bearing risks. v2's School-B expansion is defensible but the spec is doing two jobs (judge spec + lane-scope spec) in one document and the second job is weakly evidenced.
depth: standard (medium-complexity document, ~10k words, moderate risk signals — multi-component lane scope, AEO/AI-engine novelty, regulated-vertical compliance surfaces)
---

# §1. Reader

The reader is a human designer (JR) holding the MON lane spec to the same standard as CI v3.4 before promoting it into the v006 evolution loop, AND deciding whether to enforce the multi-component lane scope on the next branch of `session_eval_monitoring.py` / `structural_gate` work. They are reading to decide whether v2's expansion from "single-artifact judge spec" to "multi-component lane scope" earns the surface area it adds, or whether some of the new surface is speculative complexity the substrate cannot yet support.

Secondary reader: any future engineer/agent who picks up the spec and has to operationalize the structural_gate checks for Components B–E. They will read this spot-check to understand which load-bearing claims are evidenced vs hopeful, and which sibling-fork thresholds are real vs round-number heuristics.

# §1.5. Artifact under review

`docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` at v2 (2026-05-19 revision). ~10,400 words. Six judge criteria (MON-1..MON-6), two of which (MON-5, MON-6) breach the ≤5 ceiling under the §5 documented-exception clause. Multi-component lane scope: Component A (weekly digest, judge-scoped), Components B (watchlist), C (AI engine citation report), D (cross-lane handoff manifest) as structural_gate-validated, Component E (optional quarterly synthesis) as conditional.

Companion research load-bearing: `docs/research/2026-05-19-monitoring-comprehensive-scope.md` (22 axes × 8 form-factors × 3 cadence shapes) — the source for the v2 multi-component expansion and the 22 CUTS / 22 ADDS catalog.

The spec is doing two jobs simultaneously: (a) a judge-criterion spec for Component A in the v006 evolution loop, and (b) a lane-scope spec for the broader MON program. These have different epistemic requirements, and v2 does not consistently distinguish which evidence supports which.

---

# §4. Per-criterion stress-tests

## MON-1..MON-4 (criterion prose unchanged from v1.1)

The spot-check does not re-litigate v1.1's criterion prose; the v1 cross-check pass concluded MINOR-DRIFT with surgical restoration applied. MON-1..MON-4 are LOCKED for the purpose of v2 review.

## MON-5 (ABSENCE-as-signal)

**Premise being claimed:** absence-as-evidence is an LLM-specific failure surface that MON-1..MON-4 + MON-6 cannot catch.

**Stress-test 1 — does MON-1 actually fail to catch fabricated absences?** v2 §7 claims "MON-1..MON-4 + MON-6 cannot catch fabricated absences — they test present-signal interpretation, not missing-signal reasoning." This is not obviously true. MON-1's outcome question already requires every quantitative claim to be framed as a delta with a *named-source* baseline. A fabricated absence claim ("competitor's expected tier-1 trade-press coverage did not materialize") is structurally identical in evidence requirements: it needs a named-source baseline (the analyst-tracker corpus). MON-1's "Step 2: identify whether a baseline / comparator / delta is named with its source" CoT step would catch a fabricated absence the same way it catches a fabricated delta — the source either resolves or it doesn't.

The spec itself, in §8 #2, predicts: *"MON-1 ↔ MON-5 most likely to merge (both require named-baseline-with-source reasoning)."* This is the same critique. v2 doubles down on MON-5 as a documented exception while predicting its redundancy. That's epistemically incoherent — you either have evidence the criterion is structurally distinct (in which case it earns the breach), or you predict it'll absorb (in which case the breach is provisional and probably wrong). Pick one.

**Stress-test 2 — effect size citation quality.** v2 §7 cites "Tetlock GJP top-2% calibrated forecasters flag absence-of-pattern explicitly when stakeholders want a story; LLMs sycophantically generate stories (arxiv 2603.16643 'Good Arguments Against the People Pleasers'; arxiv 2510.04721 BrokenMath)." Tetlock's GJP findings document a human-superforecaster *capability*, not an LLM *failure rate*. The 2603.16643 citation is about LLM sycophancy in argument-construction generally — not about absence-fabrication specifically. There's no measured "absence-fabrication rate" cited (the way CI-6's 19.9% GPT-4o citation-fab rate is measured). The effect-size standard from the design guide §5 documented-exception clause is "measured effect sizes from 2024–2026 literature." MON-5 has the lit refs but not the *measurement*. **Confidence: MODERATE (0.65)** that this would not survive a strict reading of design guide §5.

**Stress-test 3 — has the substrate evolved to test it?** v2 §8 #1 acknowledges the multi-week corpus prerequisite. The CoT for MON-5 requires comparing to "prior-period digest" (Example A), which means the judge needs prior-period context at evaluation time. The spec admits this isn't wired yet (`evaluate_variant.py` may not pass multi-week context). **MON-5 is currently not testable end-to-end.** A criterion that the substrate can't score is at best speculative. This is a real issue, not a stylistic complaint.

**Verdict on MON-5:** the breach is *weakly* documented. The prediction-of-absorption in §8 #2 is honest but should drive a posture of "draft as 5 criteria + 1 provisional pending substrate" not "ship as 6 with documented exception." Provisional 6th is fine; documented exception requires harder evidence.

## MON-6 (COMPOUND-claim evidence chain)

**Premise being claimed:** compound-claim fabrication is a documented LLM failure surface with measured effect size (59% FactSet forecast-error inflation).

**Stress-test 1 — is FactSet 2025 a valid effect-size anchor?** The cite is "FactSet 2025 retrospective measuring 59% higher forecast error on AI-assisted equity reports vs analyst-only." The 59% is a *forecast-error inflation* metric on an *equity-report* substrate. It's load-bearing for financial-services digests but is being generalized to all monitoring compound claims. This is more legitimate than MON-5's evidence base (it IS a measured effect size) but the generalization is unaudited. **Confidence: HIGH (0.80+)** that the citation is real and measured; **MODERATE (0.65)** that 59% transfers cleanly from equity reports to weekly monitoring digests.

**Stress-test 2 — does MON-6 fold into MON-2 or stay separate?** v2 §8 #2 predicts MON-5 ↔ MON-6 stay separate ("absence and compound are structurally distinct phenomena"). I agree this prediction is probably right — compound-claim chains are about *invented connective tissue between real signals*, which is structurally distinct from absence reasoning. The harder absorption question is MON-6 vs MON-2 — MON-2's "anchored on observable signal vs. confident-tone defense" CoT step 2 catches the same sycophantic-confidence-toned synthesis MON-6 also defends against. Score-0 prose in MON-2 explicitly names "confident-tone orthogonal-axis prose generated to defend a foregone classification." That IS compound-claim fabrication's narrative-coherence-without-evidence-chain shape. Run the redundancy check explicitly on MON-2 ↔ MON-6, not just MON-1 ↔ MON-5.

**Stress-test 3 — is the substrate ready?** MON-6's score-1 requires "3+ signals across distinct time-points," which means the judge needs a multi-week corpus. §8 #1 admits the substrate may not pass this in. Same problem as MON-5 — but MON-6's failure mode is more severe because the failure case is unscored compound claims (false positives), not just unscored absences. Until the substrate ships multi-week context, MON-6 score-1 is *unreachable*, which means under-promotion of legitimately strong digests.

**Verdict on MON-6:** the documented-exception breach is genuinely better-evidenced than MON-5. The FactSet 59% is a real measured effect size. But the substrate readiness gap is the same: the criterion can't score 1 until multi-week corpus retrieval is implemented at `evaluate_variant.py`. **Recommendation:** either ship the substrate change BEFORE locking MON-6 as a 6th criterion, or downgrade to provisional pending that work.

---

# §6/§8 stress-tests — multi-component lane scope (the v2 expansion)

## Component A (weekly digest, judge-scoped)

No new findings — unchanged from v1.1.

## Component B (watchlist)

**Premise being claimed:** "the watchlist IS the monitoring substrate. Without it, the workflow re-discovers what to monitor every week and overfits to whatever the prior week surfaced."

**Stress-test — is this actually a structural_gate validation problem or a fixture-design problem?** A watchlist is per-client persistent data, not per-digest output. Per design guide §1.2 (Hard Rules → `structural_gate`. Principles → judge.), structural_gate validates a per-digest deterministic check. The watchlist itself isn't an artifact the lane produces each week — it's an input that conditions the digest. The structural_gate checks listed (entity-allowlist consistency, 90-day freshness floor, required-silence calendar coverage) are reasonable but they conflate two different things: (a) "does the digest reference entities consistent with the watchlist" (per-digest, valid structural_gate check), and (b) "is the watchlist up to date" (per-client data hygiene, not a per-evaluation check).

This is a minor scope drift, not a fatal flaw. But it suggests the v2 spec is treating "lane scope" too broadly — as if everything the lane touches needs to be in this document. **Recommendation:** explicitly separate per-evaluation structural_gate checks from per-client data hygiene policies. The latter belong in client-onboarding documentation, not in the judge spec.

**Stress-test — per-vertical entity-count bands.** "5–10 SaaS / AI; 3–8 agency / professional services; 8–15 finance." These numbers are not sourced in the spec or the companion research. They look like round-number heuristics. They will become enforced bands in structural_gate per §8 #9. Where did 5–10 come from? Why not 3–7 or 8–12? **Confidence: HIGH (0.80+)** that these are unevidenced — I scanned the companion research and they don't appear there with sourcing either. Flag as speculative bands.

## Component C (AI engine citation report)

**Premise being claimed:** "the single highest-leverage 2026 modernization" — invisible to 2024-era vendors, ~9 dedicated 2026 entrants named, Gartner 50%-by-2028 search-volume migration projection.

**Stress-test 1 — is the spec actually treating it as load-bearing, or as decoration?** The companion research §3 N7 + §5 S8 names this as the highest-leverage axis. But in v2 §1.5 Component C, the form factor is "2–4 pages, 800–1,800 words + per-engine visibility tables. Monthly cadence initially." That's a smaller artifact than the weekly digest. And it's structural_gate-only, not judge-scored. If this is the *highest-leverage* modernization, why is the judge layer not testing its semantic quality? The defense in v2 is "MON owns the **measurement** (correct prompts, correct attribution, correct counting). Judge-layer scoring discipline would push the workflow toward narrative-quality optimization, which is GEO-lane work."

This is a defensible lane-boundary call but it creates a tension: the spec claims Component C is the headline modernization but treats it as a measurement substrate the judge doesn't even look at. The risk is that "highest-leverage" becomes marketing rhetoric for the lane spec rather than a load-bearing claim about judge design. **Confidence: HIGH (0.80+)** that this tension exists; **MODERATE (0.65)** that it's a real problem vs. an acceptable scope decision.

**Stress-test 2 — methodology drift.** Companion research §6.5 + §8 Q5 + v2 §8 #12 all acknowledge that AI engines change grounding behavior frequently. Standardized prompt corpora may produce different citation patterns in 6 months. The v2 defense is "quarterly methodology refresh + version-tag the methodology." OK, but if the citation tracking is itself unstable on a quarterly horizon, how do you score *citation drift week-over-week* meaningfully? Component C requires `citation_drift` as a measurement axis (§1.5 Component C list), but if the underlying engine behavior drifts faster than week-to-week, you're measuring noise. **Confidence: MODERATE (0.65)** that this is a real measurement-substrate problem the spec doesn't resolve.

**Stress-test 3 — vendor dependency / future-proofing.** Component C names ~9 vendors (Profound, AthenaHQ, Daydream, Otterly, Peec, Scrunch, Bluefish AI, Goodie) as the "2026 dedicated entrants." None of them existed 18 months ago. By the spec's own §8 #12 admission, AI-engine behavior drifts within months. The vendor tooling is even more fragile. **Recommendation:** the spec should explicitly NOT name vendors in the locked structural_gate prose. Name the *measurement axes* (per-engine citation frequency, citation tier, sentiment, drift) but treat the vendors as substitutable.

## Component D (cross-lane handoff manifest)

**Premise being claimed:** "the handoff manifest IS the moat surface" (v2 §1.5 D).

**Stress-test 1 — does cross-lane handoff actually exist in the current evolution-loop substrate?** v2 §1.5 D requires "Target-lane acknowledgment within 7 days" as a structural_gate check. This presupposes (a) CI / GEO / marketing_audit lanes are running on the same client's fixture corpus, (b) those lanes have an acknowledgment mechanism, (c) a deferred-acknowledgment timer exists. None of these are documented as shipped. The §8 #7 cross-lane coordination open question implicitly acknowledges this isn't wired. **Confidence: HIGH (0.80+)** that the handoff manifest cannot be structurally validated end-to-end today because the receiving infrastructure isn't built.

**Stress-test 2 — the moat claim.** v2 §1.5 D and v2 §8 #16 both lean on cross-lane horizontal integration as the AI-native-agency moat vs Cision / Meltwater. This is a *product* claim, not a *judge spec* claim. It belongs in product/positioning documentation, not in a judge-design handoff. The spec's job is to score Component A and validate B–E; whether the handoff manifest is the moat is downstream of whether the spec correctly scores digests.

**Stress-test 3 — Goodhart on handoff inflation.** v2 §6b correctly identifies handoff-inflation as a Goodhart mode and defends with target-lane acknowledgment requirement. But acknowledgments can themselves be gamed if they're cheap (auto-acknowledged within 24h). The spec doesn't define what "acknowledgment" means rigorously. **Recommendation:** if Component D ships, define acknowledgment as a target-lane-produced artifact with content (e.g., the next CI brief references the handoff signal), not just a status flag.

## Component E (optional quarterly synthesis)

This component is honestly scoped (optional, sibling-fork-gated, narrow size envelope). No significant findings. The 4,000-word hard ceiling + §8 #15 fork-trigger discipline is sound.

---

# §8 — open-questions completeness

The 16 open questions are reasonably comprehensive but have some gaps:

1. **Missing — substrate prerequisite count.** #1 names the multi-week corpus prerequisite for MON-6. But Component D (handoff manifest) requires cross-lane infrastructure; Component C (AI engine citation) requires a standardized prompt corpus + per-engine evidence capture pipeline; Component B requires a per-client watchlist storage layer. Each is a substrate prerequisite the spec depends on but doesn't enumerate as a single substrate-readiness checklist. **Recommendation:** add an explicit "substrate prerequisites for shipping v2" item before any rollout.

2. **Missing — what happens at v006 evolution if Components B–E don't exist?** The evolution loop selects on judge scores. Judge scope is Component A only. So the evolution-loop selection pressure on Components B–E is *zero* until they're integrated. If a workflow produces a great weekly digest but no watchlist / handoff manifest / AEO report, does it pass? The spec says structural_gate enforces, but if the gate isn't wired for B–E, the evolution loop will produce A-only workflows. **Confidence: HIGH (0.85)** this is a real shipping-order question the spec doesn't address.

3. **Sibling-fork thresholds — are 3+ clients the right gate?** §8 #5 (mon_pager), #6 (mon_aeo_citation), and Component E (mon_quarterly) all use "3+ clients" as the fork threshold. This is a round-number heuristic. For an early-stage agency with 2 active clients (Klinika + DWF), waiting for a 3rd-client demand signal could be 12+ months of latency. For a later-stage agency with 30 clients, 3 might be too low (~10% of book). **Recommendation:** convert "3+ clients" to "≥X% of retainer revenue attributed to the sibling demand" — a relative threshold scales as the agency grows. **Confidence: MODERATE (0.70)** that absolute-count thresholds will misfire one direction or the other.

4. **First-cohort overfitting check.** §8 #8 names this as a re-validation trigger. Good. But the v2 spec's substitute readers list (§1) includes 9 personas; the §3a / §3b catalogs run to 22 each; the companion research lists 22 axes × 7 verticals. The total cross-product of attempted coverage is enormous. **Falsification test:** pick one substitute reader the spec claims to serve (e.g., "Practice-owner at a small-to-mid local-market service business — aesthetic dermatology, dental, hospitality, retail, fitness") and walk through the MON-1..MON-6 criteria with their actual decision context. Would the same digest serving a Series-B comms director also serve a dental-practice owner? Almost certainly not — different decision shape, different evidence depth, different cadence. The spec acknowledges this with `cadence_class` but doesn't apply the discipline rigorously across the persona list. **Confidence: HIGH (0.80)** that the substitute-reader list is broader than the spec can defend.

5. **Modern-lever bias asymmetry.** §3a CUTS / §3b ADDS show the spec correctly rewards modern levers (multi-axis severity, trust-dimension decomposition, compound detection, absence-as-signal, FAA-AD action items, distribution-moat tracking) and penalizes classical mediocrity (clip-dumps, sentiment-only, raw volume, "continue to monitor," AVE, alert-fatigue). This part of the spec is well-executed and aligned with the companion research. **No findings here — this is the strongest part of v2.**

---

# Top 3 risks

## Risk 1 — MON-5 / MON-6 ship before the substrate supports them

**Severity: HIGH.** Both criteria require multi-week corpus context. The spec admits the substrate may not pass this in (§8 #1). Locking MON-5 and MON-6 as 6th-criterion documented exceptions before the substrate ships means the criteria are unscoreable at score 1, which causes systematic under-promotion of strong digests. **Recommendation:** sequence the ops-integration work (date-indexed retrieval per research §6.3 + §8 Q3) BEFORE locking the §5 ceiling breach. Until then, treat MON-5/MON-6 as provisional. Failure to do so risks the same Phase 4 pathology pattern (`698e658` → `c76f051` rollback) where criteria looked good in spec but produced regression in evolution-loop scoring.

## Risk 2 — multi-component lane scope outruns evolution-loop selection pressure

**Severity: HIGH.** The evolution loop selects on judge scores. Judge scope is Component A only. Components B–E are structural_gate-validated. If the structural_gate for B–E isn't fully wired (and per the spec it isn't — watchlist storage layer, cross-lane acknowledgment infrastructure, prompt-corpus checksum tooling, etc. are not documented as built), the evolution loop will systematically produce Component-A-only workflows. The spec's "multi-component program" framing presupposes B–E exist and are enforceable; if they're not, the v2 expansion is mostly aspirational and the production lane is still v1-shaped. **Recommendation:** publish a substrate-readiness checklist for Components B–E. Don't enforce v2 lane scope until that checklist clears. Otherwise the v2 spec is doing product-roadmap work in a judge-design document.

## Risk 3 — first-cohort overfit through substitute-reader proliferation

**Severity: MODERATE.** v2 broadened the reader spec from Series-B comms director to 9 substitute readers spanning founder/CEO, Head of Growth, agency lead, in-house counsel, IR head, CRO, Head of Content, practice-owner. The intent (anti-first-cohort-overfit) is sound. But adding personas without rigorously testing whether the same MON-1..MON-6 criteria serve each persona's decision shape will produce a different overfit: the spec optimizes for "looks generic enough" rather than "actually serves the modal client." The Klinika first-cohort lesson (don't overfit) applies in reverse here: don't *under*fit by claiming to serve everyone. **Recommendation:** drop substitute readers from the spec text until each has a fixture in the v006 corpus. Adding personas the validation surface doesn't cover is speculative complexity.

---

# Overall verdict

**MOSTLY-SOUND with three load-bearing risks.** The v2 multi-component expansion is defensible as a direction, and the §3a/§3b CUTS/ADDS catalog is the strongest modern-lever-bias execution across the lane portfolio so far. The two documented exceptions (MON-5 ABSENCE + MON-6 COMPOUND) are honestly disclosed and the redundancy-check posture is correct.

The load-bearing issues are:

1. **Substrate readiness gap.** MON-5, MON-6, Components B–E all presuppose substrate infrastructure that isn't documented as shipped. The spec should not lock until that infrastructure is either built or explicitly sequenced before lock.

2. **Scope conflation.** The spec is doing both judge-criterion design and lane-scope/product-roadmap work. These have different epistemic standards. The judge-criterion work is rigorous; the lane-scope work imports product claims (the "moat surface," the "highest-leverage modernization") that don't earn the structural-gate prose they're driving.

3. **Substitute-reader breadth without validation.** 9 personas in §1 + §3 22+22 catalog + 7 verticals in companion research = enormous cross-product. Without per-persona fixture validation, this is *aspirational generality* not *demonstrated generality*.

**Recommended actions:**

- **Before v2 lock:** explicit substrate-readiness checklist (multi-week corpus retrieval + watchlist storage + cross-lane acknowledgment infrastructure + prompt-corpus tooling).
- **Before v2 ship:** redundancy check on MON-1↔MON-5 AND MON-2↔MON-6 (not just MON-1↔MON-5 as §8 #2 currently scopes).
- **Before v2 propagation to other lanes:** narrow substitute-reader list to personas with current-cohort fixtures; defer the rest to per-vertical re-validation triggers.
- **For sibling-fork thresholds:** convert "3+ clients" to a relative-revenue threshold so the gating scales with the agency.
- **For Component C:** name the measurement axes in spec, but treat vendor tooling as substitutable; do not name vendors in locked structural_gate prose.

The spec is approximately 80% of the way to a CI v3.4-grade lock. The remaining 20% is substrate-prerequisite sequencing and scope discipline. Do not propagate to GEO / marketing_audit / SB / X / LI / site_engine until the substrate readiness gap is closed — the propagation amplifies the same gap across 7 lanes.
