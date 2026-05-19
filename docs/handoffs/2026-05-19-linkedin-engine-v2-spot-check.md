---
date: 2026-05-19
type: adversarial spot-check review
target: docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md (v2)
companion: docs/research/2026-05-19-linkedin-engine-comprehensive-scope.md
reviewer-role: LI lane adversarial reviewer (epistemological / taste / production-readiness)
status: complete
peer-reviews: CI v3.5 (`2026-05-19-competitive-v2-spot-check.md`), MON, SB
---

# LinkedIn Engine v2 spot-check

The v2 spec is internally coherent, conforms to the design guide §3/§4/§5/§6/§7/§10/§11, and preserves the four surgical-restoration folds verbatim. The judge layer (LI-1..LI-5 over Component A) is genuinely well-engineered — the gestalt-stack defense in LI-3, the four-mechanism families + reply-ladder CoT in LI-4, and the structural_gate hoist of author-context determinables out of LI-5 are all load-bearing improvements over the rolled-back `698e658` Phase 4 pathology. **The judge is not where the risk lives.** The risk lives in the §1.5 Components A–H multi-component restructure, which lands on this lane the same way it landed on CI v3.5 — research-derived without a single client validation point, solving a problem nobody named, shifting Goodhart surface from a place we monitor (the judge) to places we don't (seven new structural_gate layers).

Overall verdict: **NEEDS-EDIT**. Three judge-layer edits (small) plus one architectural decision (large): demote Components B–H from production-default to on-demand evidence the workflow CAN produce, until at least one real client (Klinika, DWF, or a SaaS founder pilot) has been observed actually using B–H to defend or operationalize a decision.

---

## §1 Reader spec verdict

**ALIGNED, with one taste concern and one load-bearing assumption that's never tested.**

The four primary audience types (founder/decision-maker, mid-career B2B IC, recruiter/talent, industry peer) are the right cuts for 2026 LinkedIn — the Edelman/LinkedIn 2025 + Van Der Blom data both support founder + IC as the dominant comment-generating segments, recruiter as a credibility-trust segment, and industry peer as the stance-taking comment-generator. **The comment-length characterization (30–60 / 50–80 / 30–50 / 60–80 words) is too precise for the evidence available.** Van Der Blom and LinkBoost both report a 30–80-word ideal band as a single number, not segmented by reader type. The per-segment word-band ranges look like they were assigned post hoc to add credibility without being measured. This is a low-stakes problem (the judge doesn't score against these specific bands — LI-4 just uses "30–80 words" as the comment-substance threshold) but it's evidence of the spec reaching past what the literature supports. Recommend: collapse to a single "30–80 words across all four primary audiences" with one sentence on why recruiters trend shorter and peers longer, OR drop the per-segment numbers and keep "30–80-word substantive comment" as a single threshold.

**The "Secondary reader — the algorithm" paragraph is doing the work it earns.** Topic Authority 78% distribution-lift framing is correctly preserved from the Step 0 research and correctly framed as platform physics, not a Goodhart-able feature. The judge does NOT test for Topic Authority signal presence (it would collapse to "did the post mention the pillar?" which is exactly Phase 4 pathology); instead, Topic Authority validation lives in Component C structural_gate (pillar coherence with voice substrate, Jaccard ≥0.2). This is the correct routing per design guide §1.2.

**Substitute reader list (SaaS / AI lab / agency / service firm / finance / e-commerce / mid-career B2B IC, US-primary):** The breadth correction from v1 is right. The Welsh/Acosta/Alić/Denning reference set is acknowledged as creator-archetype anchors, not architectural targets — better than CI v3.5, which left similar exemplar-vs-target tension only partially resolved. **But:** the spec inherits from CI v3.5 the same straddle problem. The healthcare-practice substitute reader from CI (Klinika) is implicit in Polish first-cohort scoping (§8.5 mentions Klinika) but the substitute-reader list itself doesn't include healthcare-practice operators or local-market service businesses. Either fix the substitute-reader list to be honest about what the first-cohort actually requires (Polish aesthetic dermatology + Polish legal services are NOT in "SaaS / AI lab / agency / service firm / finance / e-commerce") OR move Klinika and DWF to documented exceptions and ship US-primary clean. The current state asserts US-primary but ships against a first cohort that's Polish-primary. That's a real reader-vs-fixture mismatch the spec does not name.

**The load-bearing untested assumption:** the spec assumes the four primary audience types comment in 30–80-word substantive ranges *because the post invited them to*. The four mechanism families in LI-4 (debatable claim / genuine question / enumerated frame / honest disagreement) are derived from WikiDisputes / Graham's hierarchy / Welsh playbook. But: **what fraction of 2026 LinkedIn comments are actually 30–80 words?** Van Der Blom reports the ideal band; he does not report the prevalence. If 90% of real LinkedIn comments are <10 words (which would not surprise anyone who has scrolled LinkedIn in 2026), then LI-4 is asking the judge to predict reader behavior that is empirically rare. The judge would be calibrated to a counterfactual reader, and the rubric's anchor would be aspirational rather than predictive. This is not fatal — designing toward the ideal-band reader is defensible — but the spec should name the assumption: *the judge is testing whether the post would earn a 30–80-word comment from the ~10–20% of readers who comment in that band*, not from the median reader.

---

## §1.5 Artifact shape verdict

**MISALIGNED — this is the load-bearing concern of the spot-check, identical in shape to CI v3.5's §1.5 concern.** The Components A–H multi-component program is research-derived without client validation; the v2 restructure imports the same architectural pathology that the CI peer review flagged six paragraphs into its §1.5 verdict. Four specific concerns:

**1. No evidence any real client wants Components B–H as a single delivered package.** The Step 0 research §5 asserts the 11K-word multi-part program is the right deliverable shape — but §8.10 of the same research deliverable explicitly acknowledges "Most agency clients will pay for the program deliverable at engagement-opening (high WTP at start; degrades) — meaning shipping the program lane fast is the highest commercial-leverage move." This is a commercial-strategy assertion, not a reader-validated claim. **There is no fixture, no observed real-client engagement, no quoted client feedback, and no Klinika/DWF/SaaS-pilot pattern in any of the project memory entries that demonstrates a real 2026 LinkedIn client actually opening Component G (the 12-month Topic Authority arc) or Component F (30/60/90 roadmap) after receiving Component A.** The Welsh/Acosta/Bloom exemplars cited as program-level anchors (§2 v2 spec) publish their funnel mechanics but they do not ship 11K-word multi-component packages to their own clients — they ship newsletters and courses. The "agency program" shape is a research synthesis, not an observed deliverable shape.

**2. The architectural trick solves a problem nobody named.** The pitch is "judge stays narrow on Component A; lane scope grows 8x to Components A–H." But the judge scope was never the binding constraint — the constraint was *time-to-Goodhart-collapse under selection pressure*, which is a judge-design problem the v1 spec already solved by binary anchors + outcome questions + 5-criterion ceiling. The v2 restructure adds Components B–H so the lane can produce a comprehensive agency deliverable — but no one asked for this. JR memory explicitly says: "production-grade v1 posture (no demo deadline)... generalize when value crosses next 2-3 clients." The Components B–H expansion does the opposite — it generalizes pre-emptively against research-derived hypothetical clients, not against the 2–3 real clients (Klinika, DWF, plus a SaaS founder pilot) who would actually inform the shape.

**3. The "judge narrow / lane wide" elegance creates seven new Goodhart surfaces, each unmonitored.** Per design guide §11.5, judge variance per criterion per generation is the Goodhart early-warning. The variance instrumentation is being designed for the judge layer (LI-1..LI-5). **Components B–H structural_gate validation has no equivalent variance-monitoring telemetry.** §6 v2 spec ("Per-component Goodhart resistance") names the modes (workflow generates plausible-sounding profile copy hitting ceilings without ICP alignment; pillar names not anchored on voice substrate; fabricated LinkedIn URLs; DM templates without persona anchors; calendar-shaped milestones without capacity sizing; quarterly milestones paste-mirrored from industry-standard; syndication rules naming surfaces without translation moves) but the defense is structural-gate token-overlap and presence checks. **What happens when the workflow learns to pass Component C's Jaccard ≥0.2 pillar-vs-voice-substrate check by pillar-padding the voice substrate at generation time?** What happens when Component D's URL-resolves check passes because the workflow learns to scrape valid LinkedIn URLs from the public surface, satisfying the gate without selecting in-lane creators? Each per-component structural_gate has a Goodhart-shape mode that is *strictly easier to game than a judge criterion*, because structural_gate is deterministic and the workflow can probe it cheaply. The spec ships seven new gameable surfaces and prescribes monitoring on zero of them.

**4. Component F capacity-sizing is honestly flagged as the AI-failure point — but the defense is "first-cohort empirical re-validation" not an actual defense.** §6 v2 explicitly says "workflow learns to generate calendar-shaped milestones without capacity sizing... remaining capacity-sizing risk flagged for first-cohort empirical re-validation." Translation: we know Component F will produce 30/60/90 roadmaps that are calendar-correct but capacity-disconnected; we don't have a defense; we'll fix it after we observe client churn around month 3 (which §1 of the Step 0 research itself names as the dominant client-churn pattern). This is shipping a known-broken component into production-default and waiting for the failure mode to validate itself. **For an agency that already has memory entries on "kick it off in a planning conversation means PLAN, not CODE" and "production-grade v1 posture (no demo deadline)," this is a violation of the team's stated discipline.**

**Per-component size envelopes look correct in isolation** (800w profile, 1,500w content strategy, 800w comment strategy, 1,200w DM templates, 1,000w roadmap, 800w 12-month arc, 400w cross-platform). But the bundle is ~10K–11K words, comparable to the marketing-audit lane — and the marketing-audit lane has documented client demand from existing engagements; the LinkedIn-program bundle does not. The collapse-to-A-only realistic reading behavior is the same as CI v3.5's collapse mode: the founder receives 11K words, reads Component A (the post draft) carefully, skims B and D, defers C/F/G/H to "later," and the agency learns nothing about whether B–H earned their production-default slot.

**Recommended posture:** ship Component A as production-default at the judge layer (LI-1..LI-5 over a single text post). Treat Components B–H as on-demand evidence the workflow CAN produce when challenged — but NOT as production-default deliverables until at least one real client has been observed using a B–H component to defend or operationalize a decision (e.g., a founder client actually executes the 30/60/90 roadmap milestones on schedule, OR a partner client actually populates 10 named target accounts in Component D and runs the daily commenting block for ≥30 days). This matches the JR-stated discipline: ship the thing that scores against real clients first, generalize against next 2–3.

---

## §4 Criteria spot-check (per criterion)

The judge layer (LI-1..LI-5) is largely good. The five criteria are outcome-questioned, behaviorally anchored, and route their AI-failure surfaces and verifiable structures to structural_gate per design guide §1.2. Per-criterion notes:

### LI-1 — Trailer earns the "...more" click

- Score-1 anchor: **GOOD.** Trailer + payoff-coherence + bait-and-switch test is the load-bearing language. The 3-line / ~210 char definition is verifiable from the artifact. Hired-Gen-Z example is well-hedged.
- Score-0 anchor: **GOOD.** Generic platitude + bait-and-switch failure both concrete.
- 3-step CoT: **GOOD.** Identify trailer → test body delivers → verdict.
- One minor concern: "the relevant professional reader cannot be inferred from the artifact + source_data" in the 0.5 anchor leans on `source_data.role / stage / employer` being present. For cold-start fixtures (per §8.3), this is acknowledged but the cold-start handling is "deferred to lane wiring." That defer is honest, but the LI-1 0.5 condition fires more often than the spec acknowledges when fixtures lack populated source_data. Spec should name "cold-start with no source_data → judge emits 0.5 by default" as the expected pattern, not as the corner case.

### LI-2 — Delivers one non-obvious insight a real reader could use

- Score-1 anchor: **GOOD.** Alić specificity test + author-specific evidence + Denning name-stripped test is the load-bearing standard. 80-word-email A/B example is well-hedged and load-bearing on the "decisions ≠ words" mechanism.
- Score-0 anchor: **GOOD.** Generic advice + customer-name-veneer-but-truism-underneath catches the subtler slot-fill mode.
- 3-step CoT: **GOOD.**
- Minor concern: "the target reader's prior knowledge level cannot be inferred from the artifact + source_data" 0.5 condition is genuinely hard to validate. A founder-stage tactical insight may be revelation to a junior IC and stale to a senior peer; the judge cannot reliably resolve "novel to whom" without explicit segmentation. Suggestion: tighten Step 3 to "verdict 1 if the insight is non-obvious for AT LEAST ONE of the four primary audiences" rather than asking the judge to identify which audience. This shifts a hard prediction to a softer existence-test.

### LI-3 — Voice is recognizably the author's, not the AI's

- Score-1 anchor: **GOOD.** Gestalt voice stack defense + three compensating-voice-marker tests is the right structure; matches the false-positive-avoidance posture in §3f.
- Score-0 anchor: **GOOD with one concern.** The HARD FLOOR voice-substrate provenance check (Step 1d) is preserved correctly from the v1 surgical-restoration fold — named entity in lived-work claim REQUIRES the entity in `voice.md`. **But:** what happens at cold-start when `voice.md` is empty or sparse? The Step 1d CoT will fire score-0 on every named entity that's not in the substrate, which means cold-start clients (no prior posts, no populated voice substrate) get systematically penalized for naming real customers/colleagues. The §8.3 cold-start mitigation (pass `source_data.author_context_known = false` flag → emit 0.5 by default) is the right answer, but it's deferred to lane wiring and the spec does not specify the interaction between the flag and Step 1d. Recommend: spell out in LI-3 score-0 prose: "Step 1d applies only when `source_data.author_context_known = true` AND voice substrate has ≥3 author-surface anchors; otherwise emit 0.5 + 'unknown' + 'voice substrate insufficient for provenance check.'"
- 4-step CoT: **GOOD.** The bait-y/Twitter-translated diagnosis in Step 1c is correctly load-bearing; preserves the v1 surgical-restoration fold from LI-1's "thoughtful authority, not contrarian punch" lever. Good integration.
- Risk: LI-3 has the highest CoT step count (1a/1b/1c/1d + Step 2 three-signal test + Step 3 verdict = effectively 6 sub-steps). Design guide §6 specifies 3-step structured CoT; LI-3 is over-budget. This raises judge cost per criterion (~150 tokens × 6 sub-steps vs ~150 × 3) and risks the judge synthesizing across the sub-steps rather than committing per-step. Recommend: collapse 1a–1d into "Step 1: Apply the four gestalt/register/Twitter-translated/substrate checks; emit per-check finding." This keeps the substantive checks while restoring 3-step structure.

### LI-4 — Gives a real reader something substantive to comment on

- Score-1 anchor: **GOOD.** Four mechanism families (debatable claim / genuine question / enumerated frame / honest disagreement) are the right cuts. Hiring-trade-off example is well-hedged.
- Score-0 anchor: **GOOD.** Cross-platform reply-ladder collapse anchor (DH3–DH5 on X → DH0–DH2 on LI) is **clean** — correctly captures the v1 surgical restoration fold from LI-3 "contrarian hot-takes that work on X." Preserves the platform-physics asymmetry without re-litigating it at the judge layer.
- 3-step CoT: **GOOD.** Predict reply-ladder ceiling → identify mechanism family → verdict. Step 1 (predict reply-ladder ceiling from opener stance) is the load-bearing innovation — anchors the judge to a counterfactual reader behavior rather than a feature checklist.
- Concern: Step 1 ("predict reply-ladder ceiling") asks the judge to imagine reader behavior. This is exactly the kind of imagination CI v3.5 reviewer flagged as failure mode for CI-4 ("imagine the company's prior") — double-imagination tends to produce high variance. LI-4 differs from CI-4 in one important way: the reply-ladder is observable on LinkedIn (the actual comments accumulate under the post), so the judge's prediction is structurally falsifiable post-publication. CI-4's "imagined prior" is not. So LI-4 Step 1 is defensible where CI-4 Step 1 was not. **But:** the judge does not see post-publication comments at evaluation time; it predicts in counterfactual. Variance instrumentation on LI-4 per §11.5 is therefore especially important. Spec should explicitly flag LI-4 for first-pass variance monitoring once instrumentation lands.

### LI-5 — Author-context coherence: credible thought leadership

- Score-1 anchor: **GOOD.** Founder-stage authors writing about founder-stage problems; IC writing from IC vantage; executive from executive vantage. Series-A hiring-trade-off example is well-hedged.
- Score-0 anchor: **GOOD.** Three concrete register-mismatch failure modes (stage-too-high / role-too-high / role-too-low) cover the AI-loop-most-likely pathology per Pornpitakpan + Edelman/LinkedIn 2025.
- 3-step CoT: **GOOD.** Read source_data → identify implied vantage from substance → compare. The "Not from explicit prefix tokens" hedge in Step 2 is load-bearing — prevents the workflow from learning to prefix-spam "as a founder."
- The hoist of three determinables to structural_gate (Role-Topic Token Overlap Gate, Employer-Mention Validity Check, Claim-vs-Recent-Activity Check) is correct per design guide §1.2. ~40% of LI-5's surface offloaded to deterministic checks.
- Concern: The register-mismatch detection is irreducibly hard without source_data. Cold-start cases (per §8.3) and clients with sparse work-history surface (many real founders only have 1–2 LinkedIn jobs visible) will trigger the 0.5 way-out frequently. Spec should name the expected 0.5 rate at cold-start as ~30–50% of fixtures, not as the rare edge case.

### LI-6 — cross-cohort at workflow CrossItemCriterion NOT 6th criterion

- **CORRECT routing.** The decision to keep LI-6 cross-cohort at the workflow-level `CrossItemCriterion` rather than promoting to a 6th judge criterion is consistent with design guide §5 (≤5 criteria; only justified breach is documented LLM-specific failure surface). Cross-cohort narrative-archetype-variance is not an AI-specific failure surface — it's a cross-draft consistency concern, which is exactly what `CrossItemCriterion` is designed for.
- v2 extension correctly threads cross-draft consistency through Component C format-fit matrix + Component G quarterly milestones. The cross-draft signal flows at the program layer, not at the per-post judge layer.

**Cross-criterion redundancy concerns:**

- LI-3 ↔ LI-5 (§8.1 predict r = 0.4–0.6): I agree, dimensions are orthogonal. Keep both.
- LI-4 ↔ LI-2 (§8.1 potential absorption): I predict r = 0.5–0.65 in practice, NOT >0.7. Insight-bearing posts trend comment-inviting, but the 2026 algorithm's NLP classifier treating comment substance as a promotion gate (not boost) means LI-4 carries a distinct signal — substantial comment seeds drive distribution independent of insight quality. Keep both.
- LI-3 ↔ LI-4 ↔ LI-5 covariance: this is the actual Goodhart early-warning surface, not the pairwise redundancy. Spec correctly names the covariance pattern in §8.1.

---

## §3 Modern-lever bias verdict

**CORRECT direction, scope conflation risk.** §3a's 20 cuts and §3 v2's 15 modern levers (from Step 0 research §3) are well-derived from 2026 evidence: Plagiarism Today em-dash dataset, LinkBoost engagement-bait classifier coverage, Socialinsider carousel benchmarks, Van Der Blom Depth Score research. The judge-level cuts (CUT-1 broetry, CUT-4 humblebrag, CUT-7 em-dash, CUT-8 "Stop X. Start Y.", CUT-9 engagement-bait, CUT-10 P.S.↓ closer, CUT-11 "Here are 7 lessons," CUT-12 symmetrical bullets, CUT-13 template-phrase openers) correctly route to structural_gate when deterministic, and correctly fold into LI-3 score-0 gestalt-stack when residual. The hoist split is clean.

**Concerns:**

- **Scope conflation between judge design and product roadmap.** CUT-14 engagement pod participation, CUT-15 third-party-app video uploads, CUT-16 "Open to work" badges, CUT-17 third-person profile bios, CUT-18 posting daily without pillar strategy, CUT-19 posting from company page as primary, CUT-20 naked reposts — **none of these are judge-layer concerns.** They are product-roadmap concerns that route to Components B–H. The judge layer should not see CUT-14 through CUT-20; only the structural_gate validation of B–H should. This conflation is exactly the issue MON and SB peer reviews flagged (per the prompt), and it's repeated here. **Recommend:** split §3a into "judge-layer cuts" (CUT-1 through CUT-13) and "program-layer cuts" (CUT-14 through CUT-20). The latter become product-roadmap concerns when Components B–H ship — and if B–H is demoted per the §1.5 recommendation above, they remain documented as agency-level operator guidance, not lane-level scoring rules.

- **Modern-lever ADD list correctly identifies platform physics.** ADD-1 Topic Authority, ADD-6 90-min golden hour, ADD-7 30–80-word comment band, ADD-8 cross-platform syndication, ADD-10 comment-magnet engineering, ADD-11 AI-slop fatigue defense, ADD-12 author-context coherence — these are platform physics, not features the judge should test for presence of. Correctly routed to structural_gate (Components C, D, F) or to background platform-physics context (the §5 wrapper paragraph).

- **ADD-2 comment strategy + ADD-3 carousels + ADD-4 newsletters + ADD-5 founder-led + ADD-13 LinkedIn Live + ADD-14 employee advocacy + ADD-15 quarterly review:** these are AGENCY-PROGRAM decisions, not lane-level scoring decisions. They drive Components D, F, G — but only if Components B–H ship as production-default. If B–H demotes to on-demand (per §1.5 recommendation), these ADDs become operator playbook items in agency documentation, not lane-level commitments. **The spec is treating product-roadmap items as judge-design items**, which is the scope conflation pattern.

---

## §1.5 Sibling-fork triggers verdict

**Carousel highest-priority: CORRECT.** Socialinsider 6.60% engagement vs 4.2% for text + 39% more reach = carousel is the dominant under-utilized format in the 2026 surface. Newsletter as second-priority is also defensible (subscriber list is the only audience-owned surface). Live and profile as lower-priority is correct.

**Trigger threshold (3+ clients): DEFENSIBLE BUT UNTESTED.** The "3+ clients" threshold is named in §8.6 but not justified. Why 3 and not 2 or 5? The Step 0 research §6 recommends sibling-lane build "spread across 6–12 months of judge-design work parallel to the other 7 lanes" — that's an effort-shaped recommendation, not a client-demand-shaped one. The 3+ threshold should be tied to a measurable indicator: e.g., "3+ clients whose Component C cadence calls for ≥1 carousel/week" is a reasonable trigger; "3+ clients" alone is not.

**Sibling-fork posture vs Components B–H production-default tension.** §1.5 says the lane stays single-lane producing Components A–H; §8.6 says sibling lanes fork at trigger. So: when does Component C's "1 carousel/week" cadence prescription get fulfilled if `linkedin_carousel` hasn't forked yet? Either (a) Component C's prescription is aspirational and operators produce carousels manually, OR (b) Component C's prescription is structural_gate-validated content the lane is committed to produce — in which case the lane needs carousel-generation capability, which is what `linkedin_carousel` would provide. The spec straddles this. Recommend: explicitly state that Component C's cadence prescriptions are aspirational operator-execution guidance, not lane-production commitments, until the corresponding sibling lane forks.

---

## §1.5 Surgical-restoration folds verdict

**ALL FOUR FOLDS PRESERVED CORRECTLY in 0/0.5/1 binary.**

- **LI-3 score-0 bait-y/Twitter-translated** (preserves v1 LI-1's "thoughtful authority, not contrarian punch" + "AUTOMATIC ≤4 if bait-y or Twitter-translated"): correctly re-expressed. The "cap at 4" semantic collapses cleanly to a score-0 anchor in the binary system because the cap was effectively saying "this fails." Binary captures that.
- **LI-3 score-0 voice.md HARD FLOOR** (preserves v1 LI-2's "lived-work claims REQUIRE the named entity in voice.md" + "score capped at 7"): correctly re-expressed. The graduated cap collapses to a score-0 condition; binary system has no cap-at-7 slot. Step 1d CoT enforces the substrate provenance check. Cold-start handling (§8.3 deferred) is the only loose thread.
- **LI-4 score-0 cross-platform reply-ladder collapse** (preserves v1 LI-3's "contrarian hot-takes that work on X (≤3 even when same hook scores 5 on X)"): correctly re-expressed. The "cap at 3 even when same hook scores 5 on X" semantic was a cross-platform-asymmetry encoding; the binary system collapses it to "scores 0 on LI even if it would score 1 on X." Same operational meaning.
- **LI-5 retired hashtag scoring** (preserves v1 LI-5 graduated hashtag-count): correctly hoisted to structural_gate as hard bounds `[1, 5]` per §8.4 Layer 1. The graduated 1-2-suboptimal-cap-at-7 / 0-cap-at-4 quality scoring is intentionally retired at the judge layer; flagged for restoration via structural_gate quality-score side-channel if first-cohort data shows the gap matters. **The trade-off is correct** — the design guide §1.2 routes verifiables to structural_gate; hashtag count is verifiable; therefore hoist. No information loss occurs as long as the side-channel restoration trigger is monitored.

All four restorations are clean. This is genuinely careful work.

---

## §8 Open questions completeness

The §8 list (8.1 redundancy, 8.2 variance, 8.3 cold-start, 8.4 structural_gate, 8.5 vertical coverage, 8.6 sibling-fork triggers, 8.7 propagation, 8.8 first-cohort overfitting, 8.9 live-code restoration) is comprehensive on internal-engineering risks but **thin on reader-validation risks**, mirroring CI v3.5. Missing questions:

1. **What evidence do we have that any real client wants the Components A–H package shape?** §8 has no question matching this. §8.10 of the Step 0 research acknowledges "commercial-leverage move" — but commercial-leverage is not the same as reader-validation. The honest answer is "none — it's research-derived." That answer should drive the §1.5 demotion recommendation.

2. **Per-component generation cost in Claude Max budget.** Mirrors CI peer's §8 missing-question 2. 11K-word program × 5 fixtures × 50-generation evolution × 3-model panel is materially different cost-shape from the v1 single-text-post lane. The v5 evolution token postmortem (memory: $2521 in 75min) is the warning sign. Spec needs an explicit per-fixture cost envelope and a kill-switch if generation cost exceeds the envelope.

3. **First-cohort overfitting at the COMPONENT level is partially addressed but undermonitored.** §8.5 watches at the criterion level + Component C/D/E vertical adjustments. §8.8 acknowledges Welsh/Acosta/Alić/Denning/Meer/Murray/Bloom is creator-archetype-anchored. **But:** Component B profile audit template optimized against the Welsh/Acosta exemplars will not transfer to a Klinika aesthetic-dermatology profile (different About-paragraph register, different Featured section, different recommendation-acquisition strategy, different headline pattern — and Polish-language). The spec does not operationalize which template variant the lane uses per fixture. The CI peer flagged this same gap; same problem here.

4. **Polish first-cohort handling in the program-level components.** §1 broadened to US-primary; Components B–H have no equivalent broadening pass. Component D's "named target accounts in-lane creators with 5K–50K followers" — what's the Polish-language equivalent of Welsh/Acosta? Component E's "ICP definition includes titles + company-size + industry + geography" — is the geography field US-default? Component F's "30/60/90 milestones" — does the cadence assume US B2B reading windows (7:30–9:00 AM and 12:00–13:00 ET) which the §1 paragraph names? Spec is US-primary at the judge layer and US-primary in implicit structural_gate defaults but ships against Polish first-cohort. Same straddle.

5. **What happens if Component A scores 1 across the panel but Components B–H structural_gate fails?** Promotion logic is not specified. Is the variant promoted (Component A is judge-scored, B–H is gate-validated, judge says ship)? Is the variant rejected (gate fails any component, lane refuses to ship)? The spec's §6 says "Slot-fill alone scores 0 at the judge layer and fails the gate at the program layer" but does not specify what happens at the intersection. Spec needs an explicit table or decision tree.

---

## Top 3 risks if shipped as-is

1. **Components B–H ship as production-default → workflow optimizes seven new gameable structural_gate surfaces while the team monitors only the judge surface → variance instrumentation per §11.5 catches drift on LI-1..LI-5 but misses Goodhart drift on Components B–H → six months in, Components B–H structural_gate pass-rates are 100% generation 1-10 and 60% generation 11+, score compression invisible because no telemetry exists at the component layer → rebuild seven structural_gate validators from scratch after burning evolution generations on now-overfit templates.** This is the same failure mode as CI v3.5's modular-architecture risk, applied to LinkedIn's larger surface area (7 components vs 5). **Mitigation: defer Components B–H to on-demand until per-component variance instrumentation is shipped AND JR has run one cost-instrumented fixture end-to-end. Same recommendation as CI peer.**

2. **§1.5 Components B–H ship → real clients receive ~11K words → read Component A (~600–2,000 chars) carefully → skim B / D → ignore C / F / G / H → judge confirms Component A is good → loop converges on Component A quality → Components C–H atrophy into Goodhart-attack vectors for components no one reads.** Same shape as Phase 4 pathology and CI v3.5 risk 2, applied at the program layer instead of criterion-prose layer. The lane learns to produce structurally-compliant B–H that no human ever opens. **Mitigation: ship Component A as production-default; B–H as on-demand evidence instrumented for client-side open-rate before promoting any to default.** This requires actual telemetry — render_judge + portal route + client-side instrumentation (the live infrastructure from the Client Portal Telemetry P1–P3 memory). Without telemetry, B–H demotion is unobservable.

3. **Component F 30/60/90 capacity-sizing failure is shipped knowingly → first cohort clients churn around month 3 → spec's own first-cohort empirical re-validation triggers fire too late → agency loses the 2–3 client relationships that would have informed Components A–H validation in the first place.** §6 v2 spec admits the capacity-sizing gap is unresolved. Shipping a known-broken Component F into production-default deliverables is a violation of the "production-grade v1 posture" memory's discipline. **Mitigation: Component F either ships with explicit capacity-sizing inputs from the client (operator hours/week available, current LinkedIn ramp, prior content cadence) OR moves to on-demand. The "we'll fix it after we observe churn" posture must not ship.**

---

## Overall verdict

**NEEDS-EDIT.**

The judge layer (LI-1 through LI-5) is largely in good shape. The five criteria are outcome-questioned, behaviorally anchored, hoist verifiables to structural_gate correctly per design guide §1.2, and preserve the four v1 surgical-restoration folds verbatim in the 0/0.5/1 binary. **Three small judge-layer edits before ship:**

(a) Collapse LI-3's six effective CoT sub-steps (1a/1b/1c/1d + Step 2 three-signal + Step 3 verdict) back to 3 structured steps per design guide §6. The substantive checks are right; the structure is over-budget.

(b) Spell out in LI-3 score-0 prose: Step 1d voice-substrate provenance check applies only when `source_data.author_context_known = true` AND voice substrate has ≥3 author-surface anchors; otherwise emit 0.5 + 'unknown'. Currently the cold-start interaction is deferred to lane wiring; spec should name it.

(c) Tighten LI-2 Step 3 to "verdict 1 if the insight is non-obvious for AT LEAST ONE of the four primary audiences" rather than asking the judge to identify which audience. Shifts a hard prediction to a softer existence-test.

**The §1.5 Components A–H multi-component restructure is the load-bearing concern.** It is research-derived without a single client validation point. It solves a problem (lane scope expansion to comprehensive agency-program shape) that wasn't binding under the JR-stated "production-grade v1 posture (no demo deadline), generalize when value crosses next 2–3 clients" discipline. It shifts complexity into seven new structural_gate Goodhart surfaces that are unmonitored by design. The "deliverable surface grows ~8x without expanding judge surface" framing is architecturally elegant but operationally inverted — same shape as CI v3.5's modular-package concern; same recommendation applies.

**The recommendation is to ship Component A only as production-default**, treat Components B–H as on-demand evidence the workflow CAN produce when challenged, and gate-flip individual components to production-default only after at least one real client (Klinika, DWF, or a SaaS founder pilot) has been observed actually using that component to defend or operationalize a decision. The §8 open-questions list is comprehensive on internal-engineering risks but thin on reader-validation risks. **The single most important missing question is the one that matches the CI peer review's missing question:** what evidence do we have that any real client wants the Components A–H program shape? Honest answer: none — it's research-derived from Welsh/Acosta/Bloom playbooks none of whom ship 11K-word agency deliverables to their own clients. That answer is the reason to gate-flip B–H to on-demand before ship.

**Scope conflation between judge design and product roadmap is real and mirrors what CI/MON/SB peers flagged.** §3a CUT-14 through CUT-20 are product-roadmap concerns, not judge-layer concerns. ADD-2, ADD-3, ADD-4, ADD-5, ADD-13, ADD-14, ADD-15 from §3 (Step 0 research) are agency-program decisions, not judge-design decisions. The v2 restructure absorbs both layers into a single document; the judge spec should focus on Component A scoring and explicitly defer Components B–H product-roadmap decisions to a separate brief.

**First-cohort overfitting is acknowledged in §8.8 but not operationalized.** US-primary + Welsh/Acosta/Alić/Denning creator-archetype anchors + Polish first-cohort (Klinika, DWF) fixtures = unresolved straddle. Same problem as CI v3.5. The substitute-reader list (SaaS / AI lab / agency / service firm / finance / e-commerce) does not include Polish aesthetic dermatology or Polish legal services. The spec asserts US-primary while shipping against a Polish-primary cohort.

The carousel-highest-priority sibling-fork ordering is **correct**. The trigger threshold (3+ clients) is defensible but should be tied to a measurable indicator (e.g., "≥3 clients with Component C cadence calling for ≥1 carousel/week") rather than a raw client count.

The four v1 surgical-restoration folds are preserved correctly in 0/0.5/1 binary. This is genuinely careful work and should not be lost in the demotion of Components B–H.
