---
date: 2026-05-19
type: adversarial spot-check — SITE v2 spec
target: docs/handoffs/2026-05-18-judge-design-step1-site-engine.md (v2, restructured 2026-05-19)
reviewer-mode: adversarial — falsify premises, surface assumptions, stress-test decisions
companion: docs/research/2026-05-19-site-engine-comprehensive-scope.md
sibling-precedent: CI v3.5 spot-check (2026-05-19-competitive-v2-spot-check.md); MON v2 / SB v2 spot-checks
verdict-summary: NEEDS-EDIT. Judge layer (SE-A..SE-E criterion prose, 5-criterion ceiling, structural_gate routing, AND-conjunction wrapper) is taste-clean and largely defensible. The 3-phase staged lane scope is research-derived with zero client validation, mixes design-document into product-roadmap, and quietly imports a 90-day delivery timeline as if it were a judge concern. Same pathology CI/MON/SB peers flagged: the spec is doing two jobs, and the second job (lane roadmap) is the weakly-evidenced one.
depth: deep (>11k words, 30 deliverables, multi-vertical, regulated-domain interactions, three sibling-fork triggers)
---

# §1. Reader and scope

The reader is JR holding SITE v2 to the same gate CI v3.4 / MON v2 / SB v2 cleared before evolution-loop promotion. The question is whether the v2 restructure earns the surface area it adds, or whether ~7,000 words of new prose (§1 expansion, §1.5b 3-phase deliverable list, §2 program success, §3 14-cuts/15-adds, §6b per-component Goodhart, §8b-e sibling-forks/cross-lane/retainer) constitutes scope creep into product roadmap territory.

The judge layer (SE-A..SE-E, the wrapper, the structural_gate split, the dual-audience AND-conjunction) is **explicitly unchanged from v1**. So the v2 review is overwhelmingly a review of **lane-scope creep**, not judge-criterion drift. The right adversarial frame: which parts of the v2 expansion are load-bearing for the judge, which are load-bearing for the lane's production work, and which are speculative product-roadmap material that should not be sitting in a judge spec at all.

---

# §1.5. The two-jobs problem (load-bearing concern, same as CI/MON/SB peers)

The peer spot-checks for CI v3.5, MON v2, and SB v2 all flagged the same structural pathology: **the v2 spec is doing two jobs (judge spec + lane-scope spec) in one document, and the second job is weakly evidenced.** SITE v2 imports the same pathology and arguably the most extreme instance of it.

Quantify the split. The v1 spec was ~4,700 words and was a judge spec. The v2 spec is ~11,500 words. The criterion prose at the judge layer is unchanged. So roughly **6,800 net-new words are about lane scope, not judge design.** That is 1.4x the original judge spec's word budget added in a document whose subject is criterion design. The expansion lives in:

- §1 readers: ~700 words expanding 7 substitute readers to 10 categories with named exemplars per category.
- §1.5b lane scope: ~1,800 words enumerating 30+ deliverables across three 30-day phases with size envelopes.
- §2b/c program success + exemplars: ~1,500 words on what the client commits to + exemplars across 10 verticals.
- §3a/b 14 cuts + 15 adds: ~1,400 words on the modern-lever bias catalog applied across the program.
- §6b per-component Goodhart: ~400 words on Phase 2-3 deliverable failure modes.
- §8b-e sibling-fork triggers + cross-lane consistency + retainer revenue model: ~900 words.

The judge layer (SE-A..SE-E prose + wrapper + structural_gate routing) is intact and competent. The lane-scope material is the v2 delta. **Most of the v2 delta is research-derived without a single client-validation point, and would more honestly live in `docs/plans/` or `docs/research/` than in a judge-design spec.** The spec is straddling judge-design discipline and product-roadmap-pitch genres simultaneously.

This matters epistemologically because the two genres warrant different evidence standards. A judge criterion needs: literature citation, fixture testbed, redundancy check against peers, anti-Goodhart anchor. A lane scope claim ("the lane must produce comparison pages in Phase 2") needs: client-stated demand, business-model fit, capacity check, sequencing logic, opportunity-cost framing against the 7 other lanes. The v2 spec applies judge-discipline evidence standards to the lane-scope material it adds — citing research §6 EL2 and SOTA exemplars as if those were sufficient validation that a *gofreddy client* wants this in the next 90 days. They are not.

---

# §2. Premise challenging

## §2.1 The 90-day staged program is research-derived with no client validation

The single most load-bearing premise of v2 is that gofreddy's modern AI-native agency engagement is a 30/60/90-day staged program with ~30 deliverables. The spec asserts this as fact (§1.5b: *"The lane's full deliverable scope is the comprehensive site program a 2026 AI-native agency must produce"*; §2b: *"site_engine engagement is a multi-component compounding program, not a one-shot landing-page rebuild"*). The research companion (`comprehensive-scope.md` §H1) asserts the same.

The premise rests on **zero validation from actual gofreddy clients.** Klinika Melitus (Polish aesthetic dermatology, b2c-aesthetics) and DWF Poland (b2b-regulated-services) are the only signed first-cohort clients per project memory; both are characterized in the spec as "current first-cohort fixtures." Neither has been observed committing to a 30-day audit + IA + 12-deliverable Phase 1, then a 31-60 day comparison-page + use-case + blog-architecture expansion, then a 61-90+ CRO + Knowledge Panel + retainer transition. The spec is **predicting client behavior from SOTA exemplar analysis** (Linear, Stripe, Mercury, Anthropic ship 30-surface programs; therefore gofreddy clients will commission and complete 30-surface programs). That's a 2-step inference where step 2 is the load-bearing one and isn't evidenced.

**Counter-construction.** What if the realistic gofreddy client (Klinika, DWF, future tech-savvy founder/early-co) buys a Phase 1 (home + 2-3 landing pages + pricing + about + first customer story + AEO infra), uses it for 60-120 days, judges whether it's working, and only THEN decides whether to commission Phase 2-3? The 90-day staged program assumes continuous client buy-in through three sequential commitments. Realistic agency engagements have ONE buy-in moment and one renewal moment. If 50% of clients don't renew after Phase 1 (industry-typical agency churn), the lane has just optimized 27 of its 30 deliverables for clients who never asked for them.

This isn't a hypothetical — DWF and Klinika are signed but neither has shipped a site rebuild yet (per memory, both are in plan-002 scope). The 90-day timeline has no precedent in gofreddy operations. **CONFIDENCE: HIGH (0.85).** I can cite the spec's own assertion-without-citation and the memory note that no client has run this loop.

**Consequence if wrong.** Phases 2-3 become deliverable templates the lane is judged against, structural_gate validates them, evolution generations are spent making them pass — and no client engagement actually executes them in production. The lane produces a beautiful 30-deliverable artifact-bundle for a client who would have signed and paid for Phase 1 alone. This is the same failure mode CI v3.5 spot-check flagged with the modular package: optimize for an organizational shape the client never asked for.

## §2.2 The "what a 2026 AI-native agency must deliver" framing is normative, not descriptive

§1.5b opens with *"The lane's full deliverable scope is the comprehensive site program a 2026 AI-native agency must produce"* (emphasis added). The "must" is doing all the work. The companion research §TL;DR makes the same move: *"A modern AI-native agency in 2026 does not sell 'one landing page redesign.' It sells website transformation across 30+ surfaces."* This is **normative industry-trend language masquerading as a deliverable scope.**

The actual evidence base for the "must" is: (a) SOTA exemplar inventory (Stripe / Linear / Mercury / Anthropic run 30-surface programs), (b) Ahrefs / CXL / Wynter trend research showing comparison pages and AEO architecture matter, (c) research §6 EL2 recommendation. None of this evidence shows that **the agency-buyer side of the market is commissioning 30-surface engagements at the cadence the spec assumes.** Stripe ships 30 surfaces because Stripe is a 12-year-old infrastructure company with engineering investment in their own marketing surface. They did not commission an agency to ship 30 surfaces in 90 days. The exemplar set is a category error for the production-shape question.

**Reframe test.** Replace "must" with "could" throughout §1.5b and §2b. Does the spec still justify itself? *"The lane could produce ~30 deliverables across three phases over 90 days when a client commissions that scope."* That reads as a reasonable agency-capability statement. The lane's evolution loop and judge-design layer no longer need to be sized to that ceiling — they only need to be sized to Component A (Phase 1 judge core) plus structural_gate validation of whatever the actual client engagement happens to produce.

**Consequence.** The "must" framing forces v2 to define structural_gate validation surface for 25 Phase 2-3 deliverables that may or may not be produced. Every one of those is a future engineering cost, a future Goodhart attack surface, and a future variance-instrumentation slot. **CONFIDENCE: HIGH (0.80).** The normative-vs-descriptive slip is right there in the prose.

## §2.3 The judge-vs-product-roadmap conflation is structural

§8e (retainer-shape revenue model implications) is the smoking gun. The section starts: *"This is business-model commentary outside the lane's design scope but worth surfacing as a product question for plan-002 next iteration"* — and then the section continues to surface it inside the spec. Either it's outside the lane's design scope (in which case delete it from the judge spec) or it's inside (in which case "outside the lane's design scope" is wrong).

Same shape in §8d (cross-lane consistency enforcement): proposes a new `ClientConfig.entity_anchor` infrastructure surface, defers concrete design to plan-002. That's infrastructure design, not judge design. Same in §8b sibling-fork triggers: comparison_engine prioritization is a plan-002 sequencing decision, not a SITE judge decision. These sections are **plan-002 input notes parked inside the judge spec.**

The clean separation a peer designer would impose: the spec splits into (a) `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` containing v1's judge-design content unchanged + the structural_gate routing list expansion + the modern-lever bias additions in §3 cuts/adds + §6b per-component Goodhart modes (because those route to structural_gate from a judge-design concern about Goodhart-resistance), and (b) `docs/plans/2026-05-19-XXX-site-engine-lane-scope-roadmap.md` containing the 3-phase staged deliverable list, the sibling-fork triggers, the cross-lane consistency design, the retainer revenue model commentary, the 10-vertical exemplar matrix.

That split would be ~5,500 words in the judge spec (already 800 over v1, which is fine — the §3 cuts/adds and per-component Goodhart additions earn it) and ~6,000 words in the plan roadmap (where they belong). **CONFIDENCE: HIGH (0.85).** The conflation is mechanical — every section that does product-roadmap work is identifiable, and CI/MON/SB peers have all flagged variants of this exact pathology.

---

# §3. Assumption surfacing

## §3.1 Assumption: structural_gate can validate 25+ Phase 2-3 deliverables on the timeline the spec implies

The §3e routing list expands from 8 verifiables to 8 verifiables + "additional checks for Phases 2-3 deliverables" enumerated parenthetically: URL HEAD resolution on customer-story / comparison-page external references, quote-grep on customer quotes, entity-existence lookup, schema-vs-body cross-validation, llms.txt-entry resolution, CRO test sample-size + significance validation, comparison-page "at least one row favors competitor" check. §8a-3 marks structural_gate expansion as DEFERRED — same posture as CI v3.4.

The unstated assumption: **structural_gate is a real callable that can support 15+ deterministic checks across the 25 Phase 2-3 deliverables.** Per memory, the existing v006 structural_gate checks are: "3+ headings, 2+ citations, ≤2000 words, banned-phrases" (per §8a-3). That's 4 checks. The v2 expansion implies a 3-4x increase in structural_gate sophistication. The spec asserts this is "DEFERRED" to plan-002 next iteration but does not size the engineering work.

**Specific load-bearing pieces that aren't really deterministic:**
- "Comparison-page at least one row favors competitor" — requires a judge call or NLI model to identify favoritism per row. Not a string match. Calling this a deterministic check is a categorization slip.
- "Schema-vs-body cross-validation" — requires semantic equivalence checking between structured-data fields and rendered body content. Not deterministic.
- "Quote-grep on customer quotes" — depends on access to source corpus. Without a corpus, this is unverifiable.
- "Brand-token compliance (color/font/spacing extracted from rendered output)" — requires headless-browser rendering pipeline. Real engineering project on its own.

**Consequence if wrong.** structural_gate cannot actually validate the 8 verifiables + Phase-2-3 checks the spec routes to it. The validation work bleeds back into the judge under selection pressure (the workflow learns to write content that looks structural_gate-passing because the gate is loose), and the judge inherits the verifiables it was supposed to be free of. **CONFIDENCE: MODERATE (0.70).** I can show the categorization slips in spec text; whether they materially break v006 substrate is something I'd have to check against the structural_gate codebase.

## §3.2 Assumption: 30/60/90 phase sequencing is universally appropriate across 10 verticals

§1.5b implicitly assumes that all 10 categories of substitute reader (B2B SaaS / AI lab / agency / professional services / fintech / e-commerce / B2C app / marketplace / dev-tool / healthcare) execute the Phase 1 → Phase 2 → Phase 3 sequence in the same order. The deliverable list is the same for every vertical, with category-appropriate trust signals and CTA framing.

This is implausible. **Specific counter-examples:**
- **Professional services (DWF, Slaughter & May).** A Magic Circle firm or a regulated practice doesn't ship "Phase 1 home + 2-3 ICP landing pages" in 30 days. Partner committees approve homepage changes on quarterly cadence. Comparison pages ("DWF vs DLA Piper Poland") are legally risky in regulated marketing and unlikely to ship in Phase 2.
- **Healthcare (Klinika).** Polish medical advertising regulations constrain customer-story content (no before-after imagery per memory). The Phase 1 "first customer-story page" deliverable may take 60+ days for legal review alone.
- **AI labs (Anthropic).** AI labs ship research papers as primary content cadence, not blog posts on a "4 initial blog posts in Phase 2" schedule. Their "blog" is research + responsible AI publication, on a different cadence.
- **Marketplace.** Two-sided dual-CTA pattern requires demand AND supply landing pages from day 1, not in Phase 2 ICP variants.

The spec acknowledges vertical adjustments (§2c, research §4) but does not flow the adjustments through to phase sequencing. The 30-day, 60-day, 90-day deliverable lists are vertical-invariant in §1.5b.

**Consequence if wrong.** The first non-b2b-SaaS client engagement that runs this spec discovers the phase sequencing doesn't match their reality, and the lane has to rebuild the deliverable architecture from scratch. **CONFIDENCE: MODERATE-HIGH (0.75).** I can point at the vertical-divergent counter-examples in the spec's own §2c exemplars.

## §3.3 Assumption: 10-vertical breadth is the right anchor

The v2 broadening from 7 substitute readers to 10 categories (B2B SaaS / AI lab / agency / services / fintech / e-commerce / B2C app / marketplace / dev-tool / healthcare) is presented as first-cohort overfitting mitigation per §8a-7. The unstated assumption: **gofreddy will plausibly serve clients across all 10 categories.** Project memory says the actual target is "tech-savvy founder/early-co" — a narrower profile than the 10-category mix suggests.

**The 10-category breadth is doing two contradictory things at once.** On one hand it broadens overfitting watch (good). On the other hand it dilutes the spec's discrimination power — when SE-A's score-1 anchor has to accommodate B2B SaaS PLG, services-firm gravitas, e-commerce product-photo, marketplace dual-search, dev-tool code-block, B2C-app emotion-led, fintech security-row, AI-lab research-led, AND healthcare LocalBusiness-schema-led all at once, the criterion's discriminating power against any single category degrades. The category-appropriate-expectations wrapper attempts to manage this, but the burden on the judge is real.

**Per the CI v3.5 peer concern about healthcare substitute reader being "out of family."** Same applies here. "Owner-operator at small-to-mid local-market business (Klinika)" and "founder-CEO of an AI lab (Anthropic)" do not commission the same agency engagement. They warrant different lanes, or a tighter substitute-reader set with documented exceptions.

**Consequence if wrong.** Either (a) the spec serves the 10-category breadth and the criteria degrade in discrimination power because they have to accommodate too many categorical exceptions, or (b) the spec implicitly favors b2b-SaaS-PLG-shaped clients (the modal vertical in the exemplar set) and the other 9 categories underperform — first-cohort overfitting at the SaaS-canonical level instead of the Klinika/DWF level. **CONFIDENCE: MODERATE (0.65).** I'd want to see the redundancy check + per-vertical fixture scores before committing higher.

## §3.4 Assumption: comparison_engine is the right first sibling-fork

§8b sets comparison_engine as the HIGHEST PRIORITY sibling-fork, ahead of cro_test_program and site_landing_variants. The argument: comparison-page warfare is the single highest-leverage 2026 AEO surface (per research §6 EL2). The trigger is "3+ clients with comparison-page demand."

**Counter-construction.** Across the existing first-cohort:
- Klinika (b2c-aesthetics-healthcare): comparison pages between aesthetic-dermatology practices are not a standard form factor. Polish medical advertising regulations make naming-the-competitor risky.
- DWF (b2b-regulated-legal): comparison pages between law firms are highly regulated; partnerships generally avoid public competitor naming.
- gofreddy itself (b2b-tech / agency): single client; not 3+ yet.

So the "3+ clients with comparison-page demand" trigger may not fire across the actual first-cohort. The comparison_engine prioritization derives from B2B SaaS market analysis (Linear vs Jira, Mercury vs Brex, Cursor vs Copilot) and applies poorly to the verticals gofreddy is actually serving. **comparison_engine may be the wrong first sibling-fork given the actual client mix.** A site_audit_engine (input to all other lanes; per research §8 OQ1) or customer_story_engine (foundational trust signal across verticals) is more obviously load-bearing across all 3 current first-cohort verticals.

**Consequence.** The first sibling-fork hits a vertical mismatch. Engineering cost is sunk on comparison_engine that doesn't apply to 2 of 3 first-cohort clients, while site_audit and customer_story sit waiting. **CONFIDENCE: MODERATE (0.65).** I'm inferring from first-cohort vertical analysis; the actual prioritization may be informed by anticipated client mix.

---

# §4. Decision stress-testing

## §4.1 Decision: keep SE-A..SE-E criterion prose unchanged from v1 — DEFENSIBLE

The v2 restructure explicitly does NOT touch criterion prose. The judge layer is treated as locked v1 (criterion-level), and only the lane-scope expansion is in scope. This is the right call for two reasons:

1. **The v1 criterion prose was iterated with care.** Three vertical-divergent score-1 anchors on SE-A / SE-B / SE-D (Linear, Slaughter & May, Allbirds for SE-A; Stripe, Slaughter & May, Allbirds for SE-B; Anthropic, DWF, Mercury for SE-D). The AND-conjunction wrapper is explicit. The structural_gate routing is clean. Changing this without strong cause violates Rule 3 (Surgical Changes) of project conventions.
2. **The criterion prose passes the design-guide §11 outcome-question test.** SE-A asks "would the human commit" not "does the hero contain X". SE-B asks "would the engine cite" not "does the page contain schema". SE-C tests claim-survival-under-credibility-interrogation. SE-D tests persona-commitment. SE-E tests substantive-recency. All are reader-side outcome questions, not artifact-feature checks.

**Falsification test.** What evidence would prove this decision wrong? (a) A redundancy check showing SE-A correlates >0.7 with SE-D (both are human-reader tests); (b) SE-B correlating >0.7 with SE-E (both touch AI-engine signals). §8a-1 already flags both pairings as likely-to-merge with live floor 3. If both pairs merge, the spec absorbs without redesign — the ceiling is preserved either way. The decision is robust under the most likely failure scenario.

**Verdict.** ALIGNED. The judge-layer decision is correct.

## §4.2 Decision: 5-criterion ceiling held — no documented exception — DEFENSIBLE BUT WORTH SCRUTINY

§5 of judge-design-guide v2.1 permits a 6th criterion under the documented-exception clause when literature documents an LLM-specific failure surface the other 5 can't catch. CI v3.4 took the exception with CI-6 (evidence chain survives tracing). SITE v2 explicitly rejects taking the exception: *"The lane's AI-failure surfaces (entity confabulation in customer-story / comparison pages, source confabulation on named third-party validation, recency / training-cutoff distortion, schema fabrication, persona-misclassification under multi-page generation, llms.txt poisoning) all route to structural_gate rather than warranting a 6th semantic criterion."*

**Stress test.** Compare CI v3.4's CI-6 to SITE v2's structural_gate routing. CI-6 tests "evidence chain survives tracing" — a semantic judgment about whether 2-3 strategic claims have named signals + verifiable sources + alternative-engaged. Is the SITE equivalent (entity confabulation in customer stories / comparison pages) also a semantic judgment? Yes. URL HEAD resolution catches some confabulation, but "the named customer at the named role gave the named outcome quote dated Q1 2026" requires more than HEAD resolution — it requires verifying the quote against a source. Quote-grep against what corpus? If the corpus is the client's own claimed customer database, quote-grep is meaningful; if the corpus is the public web, quote-grep is unreliable.

**The decision to route this to structural_gate instead of a 6th criterion is defensible IF the structural_gate validation is actually deterministic and complete.** It's questionable otherwise — see §3.1 above. The CI lane took the exception because the semantic judgment of "does this claim survive tracing" is genuinely beyond structural_gate. The same case can be made for SITE.

**Counter-argument the spec doesn't make.** A 6th criterion testing "customer-story claims survive provenance-tracing" would be the SITE analog of CI-6. The spec doesn't entertain this. The rationale would have to be: customer-story is a Phase 2 deliverable not judge-scoped, so the failure mode doesn't apply to Component A. This is defensible IF customer-story stays out of Component A scope. But §1.5a Component A includes "home + 2-3 primary landing pages" and named-customer-with-outcome appears in every score-1 anchor for SE-A. So customer-story-claim-tracing IS relevant to Component A scoring.

**Verdict.** DEFENSIBLE BUT WORTH SCRUTINY. The 5-criterion ceiling holds correctly under the spec's stated routing, but the routing's reliability is partially load-bearing on structural_gate sophistication that isn't yet built. If structural_gate cannot reliably do customer-story claim tracing, the 6th-criterion exception is the more honest design.

## §4.3 Decision: AND-conjunction wrapper preserved — DEFENSIBLE

SE-A / SE-B / SE-D / SE-E score-1 anchors each carry explicit AND-conjunction language on the dual-audience conflict surface. The shared wrapper §5 reinforces: *"a page can convert humans and be AI-uncitable, or vice versa. World-class pages do both on the same surface. The score-1 anchors on SE-A, SE-B, SE-D, and SE-E require AND-conjunction on the conflict surface."* This is the load-bearing defense against the Goodhart-collapse where evolution-loop selection pressure pushes the workflow to AI-citable-but-human-cold or human-warm-but-AI-uncitable, both of which are documented mediocre modes (§3c).

**Stress test.** Is AND-conjunction actually testable from the artifact alone? SE-A score-1 requires evidence-element AND warmth-signals. A judge can verify both from a rendered artifact. SE-B score-1 requires extractable passage AND semantic-completeness shape AND off-domain corroboration. Verifiable. SE-D score-1 requires named persona AND named alternative AND single-decision-CTA. Verifiable. SE-E score-1 requires visible-date AND current-year body reference AND entity-consistency AND dated-third-party reference. Verifiable.

**Verdict.** ALIGNED. AND-conjunction is structurally defensible and operationally testable.

## §4.4 Decision: 8 verifiables routed to structural_gate — CLEAN AT THE LIST LEVEL, QUESTIONABLE AT EXECUTION

The 8 verifiables in §3e + §1.5c (schema validity, Lighthouse, axe-core, brand-token, alt-text, broken-link, mobile responsive, robots.txt) are clean separations from the judge's reader-outcome concerns. None of these are semantic. All can in principle be checked deterministically with the right tooling.

**Falsification test.** Do any of these belong in the judge instead? Walking the list:
- Schema validity: deterministic JSON-LD validation. Cleanly structural_gate.
- Lighthouse: requires headless browser. Operationally heavy but deterministic. Cleanly structural_gate.
- axe-core a11y: deterministic against published WCAG rules. Cleanly structural_gate.
- Brand-token compliance: requires rendered-output color/font extraction. Operationally heavy. Cleanly structural_gate (but engineering work non-trivial).
- Alt-text presence: trivially deterministic. Cleanly structural_gate.
- Broken-link check: HEAD resolution. Deterministic. Cleanly structural_gate.
- Mobile responsive: viewport meta + horizontal-scroll check. Deterministic. Cleanly structural_gate.
- robots.txt: parsing per user-agent. Deterministic. Cleanly structural_gate.

**Verdict.** CLEAN AT THE LIST LEVEL. The 8 verifiables are correctly routed. The execution-readiness concern is separate (covered in §3.1) — the list is well-designed even if the engineering work isn't built yet.

## §4.5 Decision: legacy site-quality.md deprecation-header-in-place (file unmoved) — DEFENSIBLE

§8a-4: legacy `docs/rubrics/site-quality.md` (SE-1..SE-8, authored 2026-05-13) gets a deprecation header pointing to this spec but is NOT moved. Rationale: moving the file breaks ~20 cross-references in plan-002 + 7 other doc files; historical scored variants with `rubric_version: site-quality-v1` field stay attributable.

**Stress test.** Is this the right trade-off? Moving the file is correct from a cleanliness POV — superseded rubrics shouldn't sit alongside live rubrics with similar-looking IDs (SE-1..SE-8 vs SE-A..SE-E). Not moving the file preserves cross-reference integrity and per-version calibration per design guide §15. The cost of moving is ~27 cross-reference updates across 8 files; the cost of not moving is reader confusion when picking which SE-N convention is current.

**The deprecation-header pattern is the right hedge.** A clear frontmatter banner marking the file as superseded by `2026-05-18-judge-design-step1-site-engine.md` v2, plus the new spec using SE-A..SE-E instead of SE-1..SE-8 to avoid ID collision, prevents the worst confusion. The legacy SE-8 anti-slop catalog has separate value as workflow-side meta-agent training material (§8a-11) — keeping it in place serves that purpose.

**Verdict.** DEFENSIBLE. Not the most surgical solution but the trade-off is reasonable given the cross-reference debt.

## §4.6 Decision: Phase 2-3 deliverables in this spec at all — QUESTIONABLE

This is the load-bearing decision-stress concern. The decision to include 25 Phase 2-3 deliverables in a judge-design spec (even routing them to structural_gate + program-outcome telemetry instead of the judge) is the source of the scope creep this whole spot-check is about.

**Falsification test.** What evidence would prove this decision wrong? (a) A peer reviewer pointing out it's product-roadmap-in-judge-spec genre violation (this spot-check); (b) the v006 evolution loop being unable to consume the Phase 2-3 routing because structural_gate isn't built; (c) the first sibling-fork happening before the spec needs Phase 2-3 enumeration (then Phase 2-3 would be in the sibling lane's spec, not site_engine's).

**Reversal cost.** Low. Removing §1.5b 3-phase deliverable lists from this spec and moving them to a plan-002-next-iteration roadmap doc is a documentation-side migration. No code consumes the Phase 2-3 deliverable enumeration yet (per §8a-3 "structural_gate expansion — DEFERRED"). The cost is mainly ~3000 words of cut-and-paste between docs.

**Verdict.** QUESTIONABLE. The decision passes if the v2 spec is also the operational roadmap document. It fails if the judge-design discipline is supposed to be cleanly separated from product-roadmap discipline (which the design guide implies and the CI/MON/SB peer spot-checks all argue).

---

# §5. Simplification pressure

## §5.1 Subtraction test on §1.5b 3-phase staged deliverable list

What would happen if §1.5b were removed? Specifically: keep §1.5a Component A judge artifact locked at landing-page surface, keep §1.5c shape-enforcement-split routing 8 verifiables to structural_gate, but delete the entire 1.5b enumeration of Phase 1 (12 deliverables) + Phase 2 (7 cumulative) + Phase 3 (8 cumulative).

**What would be lost.** The reader of the judge spec wouldn't see the full lane-scope context. They'd have to navigate to a separate roadmap document to see the comprehensive site program structure.

**What would be retained.** The judge layer (SE-A..SE-E, wrapper, structural_gate routing for Component A's 8 verifiables) is intact. The criterion-level Goodhart-resistance defenses are intact. The first-cohort overfitting watch (§8a-7) is intact. The judge is fully designable from what remains.

**Subtraction verdict.** Significant subtraction is possible without harming the judge spec. ~1,800 words of §1.5b can move to a separate roadmap document. This is the most concrete simplification opportunity in v2.

## §5.2 Subtraction test on §3a 14 cuts + §3b 15 modern-lever adds

What if §3a/b were replaced with a single short paragraph: *"The lane removes 14 mediocre patterns (logo-wall theatre, vague benefits, generic SaaS hero, AI-slop, classical-SEO stuffing, freshness stickers, generic CTAs, hidden pricing, junk FAQ, faceless brand, defensive silence on competitors, contact-form-only, stock-photo team pages, one-home-page-for-all-channels) and adds 15 modern levers (AEO-native architecture, comparison warfare, demo-direct CTAs, founder visibility, named-customer outcomes, per-ICP variants, pricing transparency, llms.txt/Schema/robots, current-year cohort data, Knowledge Panel + Wikipedia + Wikidata, CRO test program, scroll-aware CTA, live chat, onboarding integration, compounding cadence). These are program-level lane outputs validated by structural_gate + program-outcome telemetry, not judge criteria"*?

**What would be lost.** The detailed prose justifying each cut and add. The named-replacement-per-cut framing. The specific named exemplars per add.

**What would be retained.** The judge-layer relevance is the §3c-d Component A failure modes (AI-slop, dated-but-AI-uncitable, AI-citable-but-human-cold, "We help X do Y" template convergence, 50-generation slot-fill) which are the actual Goodhart-resistance concerns and ARE load-bearing for the judge. These can stay; the 14/15 catalog can compress.

**Subtraction verdict.** Significant subtraction possible. The detailed 14/15 catalog earns more keep in the companion research doc than in the judge spec. ~1,400 words can move to research §2/§3 (which already has the catalog) and the spec can reference rather than reproduce.

## §5.3 Subtraction test on §8b-e sibling-fork triggers + cross-lane consistency + retainer commentary

§8b (sibling-fork triggers, ~500 words), §8c (multi-deliverable evolution-loop architecture, ~400 words), §8d (cross-lane consistency, ~150 words), §8e (retainer-shape revenue model, ~150 words). Total ~1,200 words.

**What would be lost if subtracted.** The first-pass sequencing recommendation for sibling-forks (comparison_engine first, cro_test_program second, site_landing_variants third). The cross-lane infrastructure-design hint (`ClientConfig.entity_anchor`).

**What would be retained.** All of these are explicit "DEFERRED to plan-002 next iteration" or "outside the lane's design scope but worth surfacing" notes. They are roadmap input, not judge design. Moving them to a plan-002 input doc loses nothing operationally.

**Subtraction verdict.** Significant subtraction possible. All 4 subsections belong in a plan-002 roadmap input doc, not the judge spec.

## §5.4 Total subtraction opportunity

§1.5b (~1,800w) + §3a/b detailed catalog (~1,400w) + §8b-e (~1,200w) = ~4,400 words of subtraction possible without harming the judge layer. v2 would compress from ~11,500 to ~7,100 words. Still meaningfully longer than v1's ~4,700, but the additions (§3c-d Component-A failure modes, modern-lever bias in §3 framing, §6b per-component Goodhart routed to structural_gate) all earn their keep.

This is the most concrete simplification pressure outcome: **half the v2 net-new prose is subtractable without judge-layer harm.**

---

# §6. Alternative blindness

## §6.1 Omitted alternative: stage the v2 expansion incrementally rather than all-at-once

The v2 spec is a one-shot restructure that broadens lane scope from "single landing page" to "30-deliverable 3-phase staged program." An alternative not considered: **stage the v2 expansion incrementally.** Specifically:

- v2.0 (now): broaden §1 substitute readers from 7 to 10 categories. Add §3 modern-lever bias to Component-A judge criteria. Hold §1.5b lane-scope expansion until first sibling-fork is needed.
- v2.1 (after first sibling-fork lands): document the sibling-fork lane in its own spec; document site_engine as continuing to iterate on Component A.
- v2.2 (after second sibling-fork lands): add cross-lane consistency design once 2+ sibling lanes exist and the consistency problem is real.
- v2.3 (after 3-month retainer transition observed in at least 1 client): document the 30/60/90 staged program shape from actual observed engagement.

The incremental alternative preserves the judge spec's discipline (one spec = one lane's judge design) while letting roadmap material accumulate where roadmap material belongs (plan-002 iterations).

**Why this alternative isn't in the spec.** v2 was written under pressure to "broaden lane scope per JR 2026-05-19 School-B restructure" (per frontmatter). The incremental alternative wasn't explored because the restructure was framed as one-shot. **CONFIDENCE: MODERATE (0.70).** I'm inferring from frontmatter; JR may have explicitly asked for one-shot.

## §6.2 Omitted alternative: defer Phase 2-3 deliverable enumeration entirely to plan-002

The spec acknowledges that no source code consumes the Phase 2-3 deliverable enumeration yet (§8a-3 + §8a-5). The 8-doc cross-reference cleanup is deferred. structural_gate expansion for Phase 2-3 verifiables is deferred. The sibling-fork triggers are deferred. **Everything Phase-2-3-related is deferred** to plan-002.

If everything is deferred, **the right place for it is plan-002**, not the judge spec. The spec should reference plan-002 for the Phase 2-3 work and stay focused on Component A judge design. This is the cleanest version of the incremental alternative above.

**Why this alternative isn't in the spec.** Probably because the research deliverable (`comprehensive-scope.md`) already exists at ~12,000 words and presents the full lane scope. The spec then absorbs the scope to make it operational. The cleaner move would be: keep `comprehensive-scope.md` as the source of truth for lane scope; have the judge spec reference it once and stay focused on judge design.

## §6.3 Omitted alternative: site_audit_engine as first sibling-fork instead of comparison_engine

Per §3.4 above. Site audit is the input to all other lanes (per research §8 OQ1 explicit recommendation), generalizes across all 10 verticals (regulated services need an audit too; healthcare needs an audit; B2B SaaS needs an audit), and the gofreddy first-cohort has obvious audit demand (Klinika and DWF both need site audits as the first deliverable). comparison_engine is highly category-conditional (poorly fits regulated verticals + healthcare).

The spec considers site_audit as a sibling-fork candidate in §8b but defers it explicitly: *"`site_audit_engine` (input to all other lanes; may live as a shared cross-lane infrastructure piece)"* — and explicitly elevates comparison_engine to "HIGHEST PRIORITY" instead. The prioritization argument rests on the 2026 AEO leverage theme. **The argument doesn't engage with which first-cohort vertical actually demands comparison pages first.** The omitted alternative (lead with site_audit) is more defensible.

## §6.4 Do-nothing baseline

If v2 isn't adopted (v1 stays as the locked spec), what happens? The judge layer is intact (SE-A..SE-E unchanged). The 8 verifiables routing list is in v1's §1.5b. The Component A landing-page surface is judge-tested in v006 evolution loop. The lane produces landing-page artifacts only. Phases 2-3 deliverables happen organically as gofreddy clients commission them, with no enforcement of a 30/60/90 structure.

**What's lost.** The 14-cuts/15-adds modern-lever bias additions to §3 cuts/adds. The first-cohort overfitting broadening to 10 categories. The §6b per-component Goodhart modes. The §8b sibling-fork triggers.

**What's retained.** The judge layer that was iterated carefully. The structural_gate routing. The AND-conjunction wrapper. The Component A artifact lock.

**The do-nothing baseline is genuinely viable as a path.** v1 is a competent judge spec. The v2 additions improve modern-lever bias awareness but don't fix anything broken in v1. The judge spec is in good shape either way. **The case for v2 has to clear the bar: do the additions earn their keep at the judge-design layer?** A subset earn it (§3 modern-lever bias additions to mediocre catalog; §6b per-component Goodhart modes); most don't (§1.5b 3-phase deliverable list; §8b-e roadmap inputs).

---

# §7. Top 3 risks if shipped as v2 as-is

## Risk 1 — Scope creep normalizes in subsequent lane specs

If SITE v2 ships with 30-deliverable lane-scope enumeration in a judge-design spec, the precedent is set: judge-design specs are also lane-scope specs. The remaining 5 lane specs (GEO, MA, X, LI not-yet-restructured) will then accumulate the same 3x-word-budget growth. Each spec will carry: judge-layer (~5000w) + lane-scope expansion (~5000w) + sibling-fork triggers (~1000w) + cross-lane consistency notes (~500w) = ~11,500w per lane. Across 8 lanes that's ~92,000 words of judge-design specs, of which roughly half is non-judge material misfiled.

**Mitigation.** Either accept the precedent (and rename the document genre from "judge-design specs" to "lane-design specs"), or refactor v2 to extract Phase 2-3 + sibling-fork material to a parallel `docs/plans/` or `docs/roadmaps/` doc structure. The refactor is ~2-3 hours of editorial work per lane. Doing it now on SITE before the 5 remaining lanes restructure avoids 5x more cleanup later.

## Risk 2 — Phase 2-3 deliverable list becomes a hard expectation the lane underdelivers against

§1.5b reads as a commitment to ship 30 deliverables across 90 days. The companion research §H1 reinforces. §2b "what the reader DOES across the engagement" enumerates client commitments. If the first real client engagement (Klinika or DWF) doesn't ship 25 Phase 2-3 deliverables in 90 days (which is the realistic outcome — both are first-cohort, both have regulated-marketing constraints, neither has committed to a 30/60/90 cadence), the lane has documented underdelivery against its own scope.

**Mitigation.** Reframe §1.5b from prescription to capability: *"The lane is capable of producing up to 30 deliverables across three phases when client engagement scopes that work; Component A is the judge-tested core and the minimum viable engagement."* This is closer to v2's intent but removes the implicit timeline commitment. The §2b client-commitment language similarly compresses to "primary success is Component A judge-passing; broader-program success is the engagement-scoped subset of Phase 2-3 deliverables the client actually commissions."

## Risk 3 — comparison_engine sibling-fork triggers on the wrong evidence

§8b sets comparison_engine as the first sibling-fork target with a "3+ clients with comparison-page demand" trigger. The risk is the trigger fires on the wrong evidence — for example, on the SaaS-vertical exemplar inventory (Linear vs Jira, Mercury vs Brex) rather than on actual gofreddy first-cohort demand. Engineering then ships comparison_engine for a vertical mix (B2B SaaS PLG) that doesn't match the actual client mix (Klinika healthcare + DWF regulated services).

**Mitigation.** Reframe the sibling-fork trigger to: *"`comparison_engine` forks when at least 2 of the active first-cohort clients have shipped 1+ comparison page through site_engine and demand exceeds site_engine retainer capacity for comparison-page production."* This forces the trigger to ride on actual production data, not on industry-trend inference. Also reorder the sibling-fork priority list so `site_audit_engine` (cross-vertical applicability) sits at HIGHEST PRIORITY and `comparison_engine` second.

---

# §8. Overall verdict

**NEEDS-EDIT.** The judge layer (SE-A..SE-E criterion prose, wrapper, structural_gate routing, AND-conjunction discipline, 5-criterion ceiling) is taste-clean and largely defensible. The v1→v2 additions that earn their keep at the judge-design layer are: §3c-d Component A failure modes (AI-slop / dated-but-uncitable / AI-citable-but-cold / "We help X do Y" template convergence); §6b per-component Goodhart modes routed to structural_gate; the modern-lever bias absorbed into score-1 anchors where the research-adds apply.

The v2 additions that should move out of the judge spec into a plan-002-next-iteration roadmap document: §1.5b 3-phase staged deliverable enumeration (~1,800 words); §3a/b detailed 14-cuts + 15-adds catalog (compress to 1 paragraph referencing research, ~1,400 words saved); §8b sibling-fork triggers; §8c multi-deliverable evolution-loop architecture; §8d cross-lane consistency design; §8e retainer-shape revenue model commentary (~1,200 words combined). Total subtraction opportunity: ~4,400 words, compressing v2 from ~11,500 to ~7,100.

**Three edits before ship:**

1. **Extract §1.5b 3-phase staged deliverable list + §8b-e roadmap content to a parallel plan-002 input doc.** Have the judge spec reference it once and stay focused on judge design. This addresses the "two-jobs problem" peer pattern.
2. **Reframe §1.5b's "must produce" normative language to "is capable of producing under scope-appropriate engagement" capability language.** Removes the implicit timeline commitment and the false-precision of "30 deliverables in 90 days" sized to a client mix that hasn't validated the cadence.
3. **Reorder §8b sibling-fork priority: site_audit_engine HIGHEST (cross-vertical applicability, all first-cohort demand obvious), comparison_engine SECOND (only fires when first-cohort production volume crosses threshold, not on industry-trend inference), cro_test_program/site_landing_variants tied THIRD (per their actual deferral conditions).** Add a falsifiable trigger to comparison_engine: "fork when ≥2 active first-cohort clients have shipped 1+ comparison page through site_engine."

The judge layer doesn't need edits at the criterion-prose level. The §3 modern-lever bias additions are absorbable as v1's §3 was already the right shape. The §6b per-component Goodhart routing is correct.

**What this spot-check does NOT recommend.** Reverting the 10-category substitute-reader broadening (§1) — that's a defensible first-cohort overfitting mitigation. Reverting the 8-verifiables structural_gate routing list (§3e + §1.5c) — that's clean separation. Adding a 6th criterion for customer-story claim-tracing — the structural_gate routing is defensible IF the gate is actually built; otherwise the 6th-criterion exception is the more honest move and that's a structural_gate engineering question, not a judge-design question.

The shape of the recommended edits is: **preserve the judge-design discipline; move the lane-scope and roadmap material to where it belongs**. The peer pattern (CI / MON / SB all flagging variants of "two-jobs problem") suggests this is now the canonical v2 review finding across the 8-lane restructure. The cheapest fix is now, before the 5 remaining lanes import the same pathology.

---

# §9. What is NOT my territory (deferred to other reviewers)

- **Coherence / terminology drift** across SE-A..SE-E vs legacy SE-1..SE-8 nomenclature → coherence-reviewer.
- **Technical feasibility of structural_gate engineering work** for 15+ Phase 2-3 verifiables → feasibility-reviewer.
- **Scope-goal alignment** of plan-002 next iteration prioritization → scope-guardian-reviewer.
- **UI/UX quality** of the lane's produced landing-page artifacts → design-lens-reviewer (the lane's outputs, not the spec).
- **Security implications** of Knowledge Panel / Wikipedia / Wikidata strategy → security-lens-reviewer.
- **Product framing** quality of the agency-engagement business model → product-lens-reviewer.

My territory was the epistemological quality of the v2 spec — whether the premises (30/60/90 staged program shape, 10-vertical breadth, comparison_engine prioritization), assumptions (structural_gate sophistication, 10-vertical sequence universality, client willingness to commission 30 deliverables), and decisions (criterion prose locked, 5-ceiling held, AND-conjunction preserved, Phase 2-3 enumeration included) are warranted. The judge layer holds. The lane-scope expansion is the load-bearing concern, and the recommended fix is to move it where lane-scope material belongs.
