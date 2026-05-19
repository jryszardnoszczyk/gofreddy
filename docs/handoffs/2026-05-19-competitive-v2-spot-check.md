---
date: 2026-05-19
type: adversarial spot-check review
target: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (v3.5)
reviewer-role: CI lane adversarial reviewer (epistemological / taste / production-readiness)
status: complete
---

# CI v3.5 spot-check

## §1 Reader spec verdict

**ALIGNED, with a residual taste concern.** The reader spec correctly describes a 2026 modern AI-native agency client — US-primary founder/CEO or VP of Strategy, multi-vertical substitute readers, three reading postures (reactive / proactive / on-demand), authority to act. The v3.5 broadening from "founder + 2 substitute" (DWF/Klinika/legal) to seven verticals plus US-primary default is the correct correction to the first-cohort overfitting risk JR flagged.

Residual concerns. (a) **The healthcare substitute reader is now noticeably out of family.** "Owner-operator at a small-to-mid local-market business (healthcare, hospitality, retail, professional services)" sits next to "founder-CEO of an AI lab" — these readers commission CI for fundamentally different reasons (local-market price match vs. category-defining trajectory call), operate at radically different decision velocities, and use radically different evidence surfaces. Klinika is the only fixture forcing this inclusion; if the agency's real client base is "tech-savvy founder/early-co" per memory, the healthcare reader should be either downgraded to a documented exception or scoped to "AI-savvy clinic operators commissioning CI from a modern agency" — not "any owner-operator at a small-to-mid local-market business." As written, the spec is straddling two reader archetypes. (b) **"Time-poor and skeptical" is doing more work than it earns.** Every CI brief in 2026 has time-poor skeptical readers — this phrasing doesn't discriminate. Compare to v3.4's CI-1 prose carrying "could walk into their next leadership meeting and assign this action" — load-bearing. The "smart, time-poor, and skeptical" framing is decorative.

## §1.5 Artifact shape verdict

**MISALIGNED — this is the load-bearing concern of the spot-check.** The 5-component modular package is **internal organizational neatness, not a client-driven shape.** Three specific concerns:

1. **No evidence the client actually wants this.** The research deliverable §5 asserts modular packaging is right; the v3.5 spec preserves the assertion. Neither cites a single 2026 modern AI-native client (Cody Schneider's Doola, Twain, peer set) that has expressed demand for a 10-15 page modular package with 5-8 components. Klue's executive briefing is one component. CB Insights' Strategy Teardown is one document. McKinsey war-game memos are one memo. The 5-component-bundle is not how any of the SOTA exemplars §7 cites actually ship their work to readers.

2. **The architectural trick is solving the WRONG problem.** The pitch is "judge stays narrow; deliverable surface grows 5x." But the judge surface was never the problem — JR's stated constraint is *comprehensive workflow scope*, which the workflow already had at the substrate layer (24 axes don't require 5 separate deliverable components; they require the brief to be able to draw from any of 24 reasoning lenses). The modular split solves "how do we let the workflow produce more pages without expanding the judge" — but no one asked for more pages. The reader wants ONE artifact they can commit on.

3. **Optional G + H create a quiet shape-bifurcation.** "Production-default A+B+C+D+E+F" plus "engagement-scoped G+H" means the lane produces ≥4 different artifact shapes depending on engagement-start flags. v3.4 had one shape (the brief) and v3.5 has anywhere from 6 to 8 components based on engagement scope. This is exactly the kind of decision-routing complexity that creates per-vertical overfitting risk (§8 question 8 acknowledges but doesn't resolve).

**Per-component size envelopes look right in isolation** (250-600w per profile card, 1-page trajectory matrix, etc.) but the *bundle* of envelopes is what's miscalibrated. A 10-15 page package read by a "time-poor and skeptical" founder collapses to "read Component A, skim B, ignore C-F unless challenged." If that's the realistic reader behavior, the lane is producing C-F for organizational appearance, not reader value.

Recommended posture: ship Component A. Treat B-F as evidence the workflow CAN produce on demand (for defending the call later) but do NOT ship them as production-default deliverables until at least one real client has been observed using them.

## §4 Criteria spot-check (per criterion)

### CI-1 — Forces a concrete action commitment

- Score-1 anchor: **GOOD.** "Specific action type AND specific target" + "decision-shape-appropriate gate" + capacity-sized note + asymmetric-opportunity test + prioritization discipline all carry. The three vertical examples (Pinsent / Claude 4.7 / DermaCenter) cover different velocity bands and decision shapes. The "Costs:" suffix on each example is load-bearing — it actually couples CI-1 to CI-5.
- Score-0 anchor: **GOOD.** "Strengthen positioning" / "explore" / wrong-timeline-shape / not-sized-to-capacity / everything-priority-1 — each names a specific failure mode JR has seen.
- 3-step CoT: **GOOD.** Single most consequential dev → recommended action → verify both halves named.

### CI-2 — Trajectory over snapshot

- Score-1 anchor: **GOOD.** "2-3 convergent independent signals" with named signal classes (M&A / hiring / product roadmap / earnings language / partnership pattern / regulatory / lateral hires / model-card / location density / vendor relationships) gives the judge specific things to count. "Reader could check in 90 days" is a falsifiability test.
- Score-0 anchor: **GOOD.** "Descriptive snapshot" + linear-extrapolation example ("they raised $40M, so they're going up-market") names the failure shape concretely.
- 3-step CoT: **GOOD.** List forward claims → identify supporting signals → verdict.

### CI-3 — Structural mechanism of advantage

- Score-1 anchor: **GOOD with drift.** "Can't or won't replicate" test is the load-bearing language. Each vertical example correctly identifies the surface advantage AND the structural reason. **However:** the "equally valuable — explicitly rejects an apparent advantage as replicable operational effectiveness" clause is theoretical — give me a 4th example of a rejection that scored 1. As written, the rejection-of-advantage path could be a way for the workflow to score 1 without doing positive analytical work.
- Score-0 anchor: **GOOD.** "Asserts an advantage without the structural reason" + "named mechanism doesn't fit what the brief describes" — names the slot-fill failure precisely.
- 3-step CoT: **GOOD.**

### CI-4 — Uncomfortable truth surfaced

- Score-1 anchor: **DRIFT.** The "if read aloud at offsite, would at least one person be visibly uncomfortable" test is unfalsifiable from the artifact alone. The CoT Step 1 asks the judge to "Identify the company's apparent priors from the brief's framing" — but the brief is written FOR an unknown reader at an unknown company with unknown priors. The judge is being asked to imagine the prior, then check if the brief contradicts the imagined prior. This is double-imagination and likely produces high variance.
- Score-0 anchor: **GOOD.** "All findings confirm the reader's existing narrative" is concrete enough to discriminate.
- 3-step CoT: **WRONG.** Step 1 cannot be reliably executed from a reference-free brief. Suggest: rewrite Step 1 to "Identify what the brief explicitly states is the prior assumption" — only score 1 when the brief itself names the prior it's contradicting.

### CI-5 — Trade-off in the recommendation

- Score-1 anchor: **GOOD.** "Bet ↔ explicit thing being sacrificed" + "specific enough to be uncomfortable" + "CFO-recognizable cost" is the load-bearing standard. Each vertical example correctly pairs the move with a named sacrifice.
- Score-0 anchor: **GOOD.** "Wish" framing + "5+ recommendations of equal weight" catches dilution.
- 3-step CoT: **GOOD.**

### CI-6 — Evidence chain survives tracing

- Score-1 anchor: **GOOD.** "Top-3 strategic claims" scope is right; (a) signals named (b) sources verifiable (c) alternative engaged is the three-leg test. "Gap itself is treated as an intelligence finding" reframe restored from live MA-7/CI-8 surgical restoration. Confidence calibration phrasing carries.
- Score-0 anchor: **GOOD.** Names the three AI-specific failure surfaces concretely (entity confab, source confab, recency distortion).
- 4-step CoT: **GOOD.** Worth noting: Step 3 (flag confabulations) is a deterministic check the judge can't reliably perform without source corpus access. The spec acknowledges this — §3b routes URL HEAD / quote-grep / entity-existence to structural_gate — but CI-6 still asks the judge to "flag" confabulations. The judge will hallucinate confabulation flags. Either tighten the CoT to "flag confabulations only when the brief itself contains internally-inconsistent claims (date contradictions, named-entity-mismatches within the brief)" or drop Step 3 and rely on structural_gate.

**Cross-criterion concern:** CI-2 (trajectory with 2+ signals) and CI-6 (evidence chain) are likely to correlate >0.7 in the redundancy check — both test for signal-multiplicity and verifiability. §8 question 1 already flags this. The spec is honest about the absorption likelihood.

## §8 Open questions completeness

The §8 list has 8 pre-existing items + 5 sibling-fork triggers + 1 validation gate. Mostly thoughtful. **What's MISSING:**

1. **Is the modular-package architecture validated against any real reader, or only research-derived?** §8c is a self-validation gate ("run Components B-F retroactively against 4 Phase-3 fixtures; eyeball value") — but eyeballing is JR-internal. The genuine load-bearing missing question: *what happens if we ship A only to one client and B-F on demand to a second client; does the second client actually open B-F?* The answer determines whether the modular architecture is real or organizational.

2. **What is the per-component generation cost in Claude Max budget?** §8c mentions $15-25 per fixture envelope but doesn't tie to the v5 evolution token postmortem (1.46-7.83 $/call meta/inner/critique). 50-generation evolution × 5 fixtures × 6-component package × 3-model panel is materially different cost-shape from 50 × 5 × 1 × 3. Could repeat the $2521-in-75min burn pattern if not gated.

3. **Does structural_gate-driven Component E (watchlist) actually reach the MON lane?** Trigger 4 in §8b acknowledges MON lane hasn't matured. But Component E is "production-default" per the §1.5 lock. The spec ships a deliverable component whose downstream consumer doesn't exist yet. Either Component E moves to optional (matching G/H) until MON is judge-stable, or the spec needs to acknowledge the orphan.

4. **First-cohort overfitting at the COMPONENT level is unaddressed.** §6.4 of research notes per-component template-variant risk; §8 question 8 watches at the criterion level. But Component B (profile cards) likely overfits hardest — the profile-card template optimized against DWF (legal partnership profile) will not transfer to Anthropic (AI-lab founder profile) without different fact-classes, hiring signals, and AEO presence sections. The spec acknowledges vertical-template-variants in §6.4 of research but doesn't operationalize how the lane picks which variant to instantiate per fixture.

5. **Polish first-cohort handling in the modular layer.** §1 broadened US-primary, but Components B-F have no equivalent broadening pass — the deep-profile-card format implicitly carries Polish-legal / Polish-medical first-cohort substrate assumptions (named sources like Pirical for legal, RealSelf for healthcare). If the spec is US-primary, the per-component primary-source default per vertical needs to be US-anchored (Leopard Solutions for US legal vs. Pirical for UK legal; Glassdoor + LinkedIn for US healthcare vs. Polish-language local-review platforms for Klinika).

## Top 3 risks if shipped as-is

1. **Modular architecture ships → workflow optimizes for component count, not strategic insight.** Goodhart attack-surface at the structural_gate layer is described in §6b but not measured. The spec describes the *mode* of template-rigidity Goodhart on each component; it does NOT describe the variance-instrumentation TELEMETRY needed to detect when the mode is firing. If Component B's structural_gate passes 100% generations 1-5 and 60% generation 6, no one will notice until generation 7-10 when scores compress. Result: rebuild structural_gate for B-F from scratch after burning evolution generations on a now-overfit template. **Mitigation: defer Components B-F until per-component variance instrumentation is shipped AND JR has run one cost-instrumented fixture end-to-end.**

2. **§1.5 modular package ships → real clients receive 10-15 pages → read 3-6 pages of A → judge confirms A is good → loop converges on A-only quality → B-F atrophy into Goodhart-attack vectors for components no one reads.** This is the same failure mode as Phase-4 (workflow optimizes a surface marker disconnected from reader value), just at the deliverable-package layer instead of the criterion-prose layer. The lane learns to produce structurally-compliant B-F that no human ever opens. **Mitigation: ship A only as production-default; B-F as optional deliverables instrumented for actual client-side open-rate before promoting to default.**

3. **CI-4 score-1 anchor's "imagine the company's prior" CoT step ships → judge variance per generation becomes the highest of any criterion → CI-4 gets flagged for redesign per design-guide §11.5 → 6-criterion ceiling becomes 5-criterion by force, but the wrong criterion gets dropped (CI-4 instead of CI-6's redundancy with CI-2).** Result: the lane loses the uncomfortable-truth criterion (which IS load-bearing for "does this brief actually change a decision") instead of pruning the easier CI-2/CI-6 redundancy. **Mitigation: rewrite CI-4 CoT Step 1 to score on the brief's *self-stated* prior contradiction, not the judge's *imagined* prior contradiction. Then run the redundancy check, and let CI-2 ↔ CI-6 absorb.**

## Overall verdict

**NEEDS-EDIT.**

The judge layer (CI-1 through CI-6) is largely in good shape — v3.4 surgical restoration recovered the load-bearing prose JR iterated, anchors are concrete, vertical examples discriminate, Goodhart-modes are named. **Three judge-layer edits before ship:** (a) rewrite CI-4 CoT Step 1 to score against brief-stated priors, not judge-imagined ones; (b) tighten CI-6 Step 3 confabulation-flagging to internally-inconsistent claims only; (c) add a 4th CI-3 example demonstrating the rejection-of-advantage scoring path.

The §1.5 modular package architecture is the load-bearing concern. It is research-derived without a single client validation point. It solves a problem (judge-surface containment) that wasn't binding, and shifts complexity into a deliverable-layer Goodhart surface (Components B-F) that is unmeasured and uninstrumented. **The recommendation is to ship Component A only as production-default**, treat B-F as on-demand evidence the workflow CAN produce when challenged, and revisit promotion to production-default after one real client has been observed using B-F to defend a decision. The "deliverable surface grows ~5x without expanding judge surface" framing is architecturally elegant but operationally inverted — clients commission CI to *commit to an action*, not to *receive a package*.

The §8 open-questions list is comprehensive on internal-engineering risks (redundancy, vertical fixture coverage, sibling-fork triggers, cost envelope) but thin on reader-validation risks. The most important missing question: *what evidence do we have that any real client wants the modular package shape?* If the honest answer is "none — it's research-derived," that's a reason to gate-flip B-F to optional before ship.
