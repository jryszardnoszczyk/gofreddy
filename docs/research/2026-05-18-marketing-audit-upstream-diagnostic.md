---
date: 2026-05-18
type: research deliverable — deep-research axis
topic: marketing_audit lane — upstream diagnostic (marketing-symptom vs product/positioning/pricing/sales root cause)
status: complete
parent: docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md
guide: docs/rubrics/judge-design-guide.md
companion: docs/research/2026-05-18-judges-domain-marketing-audit.md
related:
  - docs/handoffs/2026-05-17-judge-design-step1-competitive.md
  - docs/rubrics/judge-design-guide.md §5, §11
deepens: MA-5 (Surfaces upstream problem when that's the real constraint)
axis: UPSTREAM DIAGNOSTIC
constraints:
  - outcome questions, not feature checks
  - binary anchors with behavioural prose
  - no framework-name embedding in criterion prose
  - reference-free (no model-authored exemplars as scoring anchors)
  - defend per failure mode
---

# Marketing Audit — Upstream Diagnostic Deep Research

## TL;DR

The marketing audit lane's highest-leverage failure mode is **misattribution**: an AI audit observing low conversion / low pipeline / high CAC, and prescribing a marketing fix when the binding constraint is actually product, positioning, pricing, ICP, or sales motion. This destroys client trust faster than any other failure mode and burns the most runway — and it is exactly the failure mode LLM-driven audits over-produce because their training distribution is saturated with marketing tactics, not product-strategy decisions.

The upstream-diagnostic axis is what separates a Dunford / Rachitsky / Balfour / Campbell-grade audit from a "ten-page PDF of generic recommendations." MA-5 in the Step-1 draft captures the right outcome question but needs sharper score-0 anchors, an expanded list of upstream-signal classes (positioning is missing as a named class), and a structural_gate complement that catches mechanically-attestable upstream-diagnostic features without becoming a feature checklist.

This deliverable proposes:

1. Sharpening MA-5's score-0 anchor catalogue with four named upstream-misdiagnosis sub-patterns plus a calibration-only fifth.
2. A structural_gate "upstream signal floor" — three deterministic presence-checks that shrink the slot-fill Goodhart surface.
3. Explicit guidance on the MA-5 ↔ MA-1 redundancy boundary, including calibration-set weighting toward upstream-evidence fixtures.
4. A scope-creep posture: the judge rewards the audit naming the upstream constraint, not solving it. The audit's job is to refuse a wrong recommendation, not to write a product roadmap.

Recommend: ship MA-5 substantially as drafted, with the score-0 sub-patterns and structural_gate complement folded in. **Hold the ≤5 ceiling** — the upstream axis does not justify a 6th criterion under §5's justified-breach standard (reserved for LLM-specific failure surfaces with measured 2024–2026 effect sizes, e.g., CI-6).

## Key questions

1. When are marketing metrics underperforming because of a non-marketing root cause? — six upstream classes (§ Synthesis 1).
2. How does a high-quality audit distinguish marketing-symptom from upstream-cause? — sequential triage (§ Synthesis 2).
3. What's the LLM-audit-specific failure mode? — training-distribution bias toward marketing tactics (§ Synthesis 3).
4. What deterministic signals can structural_gate check? — three: upstream-diagnosis presence, upstream-class lexical coverage with evidence, binding-constraint declaration (§ Synthesis 4).
5. How does the judge reward correct attribution? — binary outcome on confirm-marketing-OR-sequence-behind-upstream (§ Synthesis 5).
6. What does the literature say about misdiagnosis cost? — scope-creep into the wrong layer + compounding diagnostic-optionality loss (§ Synthesis 6).

## Synthesis

### 1. The six upstream classes

A marketing audit can be wrong in six structurally distinct ways once you accept that the binding constraint may not be marketing. Each has practitioner-named signals; each requires a different remedy.

**(a) PMF.** Sean Ellis's 40%-very-disappointed survey threshold. Below it, demand-gen produces no durable growth — leaks downstream of acquisition exceed inflow. Signals: low D7/D30 activation; logo churn at <12 months; cohort retention curves that decay to zero rather than flatten; NPS detractor concentration late-stage. Refuse demand-gen until PMF re-tests.

**(b) ICP.** Distinct from PMF — PMF can be locally strong inside a specific ICP and absent everywhere else. Signals: bimodal sales-call conversion across segments; customer-success effort variance >3× between segments; expansion revenue concentrated in one cohort; high CAC against blended LTV that resolves cleanly when segmented. Wynter's messaging-resonance audits exist for this case.

**(c) Positioning.** April Dunford's named failure mode: buyer confusion about category, value, competitive alternatives. Signals: "how would you describe what we do" responses cluster into 4+ different categories; sales-call recordings show prospects with the wrong mental model; comparison-page traffic high but conversion low; win-loss interviews surface "we thought you did X" as a recurring loss reason. Dunford's claim is load-bearing: marketing executed against bad positioning amplifies confusion, doesn't correct it.

**(d) Pricing.** Patrick Campbell at ProfitWell — pricing is the marketing decision with the highest leverage. Signals: ACV/willingness-to-pay mismatch; value-metric mismatch (per-seat when value scales with usage); flat single-tier pricing in bimodal-usage market; expansion revenue <10% of new ARR; high-touch sales required to close low-ACV deals. Treating pricing as out-of-scope when demand-gen cannot work at the current price point is misdiagnosis.

**(e) Product.** Distinct from PMF — PMF asks "do customers love this product?"; product asks "does it reliably do the job?" Signals: support-ticket density on activation path; specific features named in churn surveys; bug reports concentrated on conversion-critical surfaces; sales engineers required for basic demos. No demand-gen recovers a leaky product.

**(f) Sales motion.** Balfour's Channel–Model fit. Signals: marketing-qualified leads convert at sub-median rates to sales-accepted; sales cycle 2–4× category median; AE ramp >9 months; pipeline coverage >4× of quota; high lead volume but flat closed-won. When sales motion is the bottleneck, more pipeline makes it worse.

The Step-1 draft enumerates five (PMF, ICP, pricing, product, sales motion). **Positioning is the load-bearing addition** — Dunford's framing of positioning as upstream of marketing-execution is canonical and the audit's job is to catch positioning-buyer-mental-model divergence even when the company believes positioning is fine.

These six are not mutually exclusive — a PMF gap can exist inside ICP confusion, or a pricing model can mask a positioning failure. The audit's job is not to pick one but to name which is *binding* at the current decision point.

### 2. The triage sequence

A high-quality audit walks a sequence, stopping at the first binding constraint. The Kalungi / Bell Curve / Wynter / ProfitWell / fractional-CMO converge:

1. **Retention / PMF gate.** Cohort retention first. If retention is below category median (monthly churn >5% B2B SaaS; D30 <30% B2C), fix PMF/product first.
2. **ICP / positioning resonance.** Win/loss data, customer-language surveys. If ICP is confused or positioning mismatched with buyer mental model, intervene before channel work.
3. **Pricing audit.** Value-metric alignment, expansion revenue, sales-cycle anomalies. Often higher-leverage than acquisition-channel changes.
4. **Sales motion fit.** Marketing-to-sales handoff conversion, ramp time, pipeline coverage benchmarks.
5. **Marketing function audit.** Channel mix, messaging, content distribution, paid efficiency. Where 80% of "audits" start; should be where they end.

A great audit may stop at any step and recommend pausing marketing investment until the upstream gap is closed. The judge tests whether the audit shows evidence of having walked the triage — not section-by-section (that's a feature-check), but whether the diagnosis-of-binding-constraint engages at least one upstream class when evidence points there.

### 3. The LLM-audit-specific failure mode

LLMs are trained on a corpus saturated with marketing-tactics content (agency blogs, "10 ways to improve conversion" posts, HubSpot SEO plays) and starved of practitioner-grade product-strategy decisions (private memos, board decks, consulting deliverables that don't index publicly). Rachitsky has named this: SEO-shaped growth content is "tactic-shaped" because tactic content ranks and converts.

When asked to "audit our marketing," an unguided LLM:

- Over-indexes on channel mix, ad copy, SEO, content cadence, landing-page A/B tests.
- Under-indexes on PMF diagnostics, ICP segmentation, positioning re-statement, pricing audits, sales-motion alignment.
- Defaults to additive recommendations ("do more X") over subtractive ones ("pause marketing until Y is fixed").
- Treats upstream classes as out-of-scope rather than candidate binding constraints.

This is structural bias, not prompt engineering. It cannot be solved by adding "and consider product/positioning/pricing" to the prompt — the model will surface them mechanically without diagnostic conviction. **The mitigation lives in the judge:** the judge tests whether the audit *would refuse a marketing recommendation* when evidence points upstream. A workflow that learns to slot-fill an "upstream consideration" section gets caught by the score-0 anchor on slot-fill specifically.

### 4. Structural_gate complement — three deterministic checks

Per design guide §1.2 / §2 (Hard Rules → structural_gate, Principles → judge), the upstream-diagnostic axis has deterministic features that can be pushed out of the judge. The point isn't to make the judge cheaper — it's to shrink the slot-fill Goodhart surface. If the workflow has to pass structural_gate's upstream-presence checks AND the judge's outcome question, slot-filling structural_gate alone doesn't help.

1. **Upstream-diagnosis section presence.** The audit contains a section, sub-section, paragraph, or labeled passage engaging at least one upstream class. Presence check, not quality check.
2. **Upstream-class lexical coverage with evidence reference.** At least one of the six classes named, with at least one supporting evidence reference (cohort, survey, interview, benchmark, transcript). Catches the variant where the audit produces an "upstream considerations" header but engages nothing specific.
3. **Binding-constraint declaration.** Explicit "the binding constraint is X" or equivalent — either naming a marketing-internal constraint (defended against upstream alternatives) OR naming an upstream constraint and sequencing marketing behind it. Most load-bearing; without it, neither MA-1 nor MA-5 can be evaluated.

Cost: ~50–100 LOC in the lane's `structural_gate.py`. None of these enter the judge prose — judge sees the artifact only after structural_gate passes, and tests outcome quality, never artifact compliance.

### 5. The misdiagnosis sub-patterns

The Step-1 draft's MA-5 score-0 anchor is correct but compressed. Practitioner literature names five specific misdiagnosis sub-patterns the anchor should catch:

**(a) "Audit always recommends more marketing."** Default failure mode. Evidence might literally include 6.4% monthly churn, but the audit recommends "improve onboarding email sequence" rather than naming retention as a PMF or product gap.

**(b) "Upstream classes named but treated as out-of-scope."** The audit acknowledges that PMF/ICP/pricing exist as concepts but explicitly defers them. When the audit's own data points at an upstream constraint, this deferral is misdiagnosis.

**(c) "Slot-filled upstream section with no diagnostic conviction."** Mechanical rotation through PMF/ICP/pricing without engaging specific evidence. Reads like a template insertion. Caught by the CoT step "verify the audit either confirms marketing IS the constraint OR sequences behind the upstream fix" — slot-fill fails the sequencing test.

**(d) "Both diagnoses given equal weight."** The Goodhart-resistant form of slot-fill — audit slot-fills upstream section AND keeps the marketing recommendations, so the founder reads it and defaults to the marketing actions because those are concrete. **The judge must require sequencing, not parallel-tracking.**

**(e) "Wrong upstream class named."** The audit shows the right discipline but reaches the wrong conclusion — recommending positioning work when evidence points at pricing. Highest-skill failure; hard for a judge without ground truth. Surfaces in calibration when JR-labeled fixtures disagree with the audit's diagnosis. Judge alone cannot catch this; calibration set must.

The proposed MA-5 score-0 anchor expansion (full prose in § Synthesis 8) covers sub-patterns (a)–(d) explicitly; (e) is left to calibration.

### 6. Misdiagnosis cost in fractional / consulting work

The fractional-CMO and consulting literature frames misdiagnosis cost as **compounding loss of diagnostic optionality.** Every week spent executing against the wrong binding constraint is a week of budget burned AND a week of diagnostic data not collected on the real constraint.

Envizon and SaaSConsult Day-30/60/90 playbooks make this explicit: the Day-30 deliverable is a diagnosis-grade audit, not a tactical plan, because Days 31–60 will fund experiments against the diagnosed constraint. Diagnose wrong on Day 30 → Days 31–60 are wasted. The fractional-CMO field names the failure mode: **"scope-creep into the wrong layer."** A CMO hired for marketing growth who diagnoses a product or pricing problem must surface it and renegotiate scope — not silently execute the marketing playbook anyway. Kalungi's one-page marketing-readiness audit is the canonical "is the company ready for marketing investment at all?" instrument.

In the LLM context, the cost compounds differently. A misdiagnosed audit doesn't burn the founder's quarter — they may catch it before committing. But a misdiagnosed audit at scale (autoresearch evolution, 50 generations) trains the workflow to produce misdiagnosed audits, and the resulting Goodhart-collapsed lane produces nothing diagnostic at all. The judge's job: keep the selection signal pointed at correct attribution.

**Simmonds-style marketing-internal upstream.** Ross Simmonds names a related pattern: companies routinely diagnose a content-creation problem ("we need more content") when the actual constraint is distribution ("existing content isn't reaching anyone"). Upstream-of-default-recommendation in the same way PMF is upstream of channel choice. This is a marketing-internal upstream — caught inside the marketing function, not above it — but the judge's discipline is identical: refuse the surface recommendation when evidence supports a different framing. Likely MA-3 territory (revenue trace) more than MA-5 territory (upstream-of-marketing); confirm during fixture validation.

### 7. The redundancy boundary — MA-5 vs MA-1, and the ≤5 ceiling

The Step-1 spec's open question #3 flags possible MA-1 ↔ MA-5 correlation. Structural argument: the upstream constraint IS a binding constraint when it exists, so an audit scoring 1 on MA-5 (correctly surfaces upstream) likely also scores 1 on MA-1 (names a specific constraint with evidence).

What keeps them discriminating:

- **MA-1 tests precision of diagnosis** — does the audit name one constraint with two evidence sources? Works whether marketing-internal or upstream.
- **MA-5 tests upstream-willingness specifically** — when evidence points upstream, does the audit go there? An audit that names a marketing-internal constraint correctly but ignores upstream evidence fails MA-5 while passing MA-1.

The likely disagreement cases (named-upstream-but-not-sequenced → MA-1 = 1, MA-5 = 0) are what keep them separable. If the calibration set is dominated by marketing-internal-evidence fixtures, MA-5 under-fires and correlation goes above the §5 0.7 threshold — then the criterion gets dropped. **Remediation: weight the calibration set toward upstream-evidence fixtures. At least 30% of the 100-fixture calibration set should have upstream-evidence shape** so MA-5 has separable failure surface.

**Why this does NOT justify a 6th criterion.** CI-6 was added as a justified breach because entity confabulation (19.9% GPT-4o rate), source confabulation (37% Perplexity rate), and recency distortion (LLMLagBench) have measured 2024–2026 effect sizes for LLM-specific failure surfaces the other 5 criteria cannot catch. The upstream-diagnostic axis does not meet this bar:

- Misdiagnosis is a general analytical failure, not an LLM-specific surface. Human consultants produce upstream-misdiagnosed audits at high rates; the LLM bias is quantitative amplification, not a new kind of failure.
- No published 2024–2026 paper measures upstream-misdiagnosis rates in LLM business-analysis tasks with the specificity §5's exception requires.
- MA-5 already targets this axis; sharpening its anchors is the right remediation, not splitting it off.

The upstream-diagnostic axis is *deepened* into MA-5, not split. Structural_gate absorbs the deterministic part, keeping MA-5's prose focused on the outcome question.

### 8. Refined MA-5 — full proposed prose

```
### MA-5 — Surfaces upstream problem when that's the real constraint

Outcome question (binary):
When the binding constraint is upstream of marketing (PMF, ICP,
positioning, product, pricing, sales motion), does the audit
say so plainly — even though saying so means the audit's own
recommendations get smaller? Would the founder finish thinking
"the bottleneck isn't marketing" if that's what the evidence
points at — and would the audit's marketing recommendations be
SEQUENCED behind the upstream fix, not parallel-tracked
alongside it?

Score 1 (yes) — Where evidence in the audit suggests the
constraint is upstream (low retention, low PMF-survey scores,
ICP confusion, positioning–buyer-mental-model mismatch,
pricing-model misfit, product activation gap, sales-motion
misalignment), the audit names it directly and SEQUENCES
marketing recommendations behind the upstream fix. The audit
is willing to recommend pausing demand-gen, deferring channel
diversification, or running a PMF re-test / positioning
re-anchor / pricing audit before scaling marketing.

Example (do not optimize toward this): "Your monthly churn is
6.4%; LTV at this churn rate means CAC payback cannot work
below an ACV 4x your current. The constraint is retention,
not acquisition. Pause the SEO investment and the paid-LinkedIn
pilot; the marketing budget should fund three messaging tests
to diagnose whether the issue is positioning or product fit."

Score 0 (no) — At least one of: (a) audit always recommends
more marketing despite evidence pointing upstream;
(b) upstream classes named but treated as out-of-scope when
evidence engages them; (c) upstream section slot-filled with no
diagnostic conviction (generic mention without engaging the
specific evidence); (d) upstream constraint named but marketing
recommendations parallel-tracked rather than sequenced behind
the upstream fix. Audits with no "the bottleneck is upstream of
marketing" branch by default — implying marketing is always
the answer — score 0.

Score 0.5 (unknown) — Audit engages upstream evidence but the
artifact lacks enough detail to determine whether the upstream
naming is supported, OR the sequencing of marketing
recommendations behind the upstream fix is partial. Emit 0.5 +
"unknown" + one sentence on what's missing.

Required CoT:
- Step 1: Identify upstream signals present in the audit's
  evidence (retention cohorts, PMF-survey scores, ICP/positioning
  divergence, pricing-model mismatch, product activation gap,
  sales-motion friction).
- Step 2: Determine whether the audit (i) confirms marketing IS
  the constraint with evidence, OR (ii) names an upstream
  constraint AND sequences marketing recommendations behind it.
- Step 3: If (ii), verify the sequencing is real — marketing
  recommendations explicitly deferred, paused, or scoped behind
  the upstream fix, not parallel-tracked.
- Step 4: Emit verdict + one-sentence justification.

Do not score: number of upstream classes discussed, presence of
"upstream constraints" section header, length of the upstream
discussion, depth of upstream remediation guidance (audit names
the constraint; audit does not need to solve it).
```

Length ≈ 280 words, over the design guide's ~150 target but absorbable per the CI-1 precedent. If a redundancy check reduces live criteria to 4, the budget is available.

### 9. Scope-creep posture and anti-patterns

A judge criterion can drift into asking the audit to do more than it should. MA-5 must NOT reward audits that produce a full product-strategy roadmap (product's job), recommend specific pricing changes (a pricing audit, not a marketing audit), conduct a PMF re-test inline (a follow-on engagement), or re-state the company's positioning (a Dunford-style workshop).

**MA-5 rewards the audit for naming the upstream constraint correctly and refusing to make marketing recommendations the upstream constraint would invalidate.** Deliverable scope stays marketing; diagnostic scope expands to upstream. The audit's job is to refuse a wrong recommendation, not write a different product. This matches Kalungi's one-page marketing-readiness audit — tells the founder whether marketing is ready to invest in, then stops.

Anti-patterns the redraft avoids per design guide §12: framework-name embedding (no "does the audit apply the Sean Ellis Test?" — Phase 4 rollback `c76f051` precedent); surface-marker prose (no "does the audit have a section labeled 'upstream considerations'?" — that's a structural_gate check); anti-gaming clauses (no "don't be biased toward recommending more marketing" — theatrical per arxiv 2506.13639); implicit weight reshuffles (don't list all six upstream classes in a way that weights upstream-diagnosis more than upstream-refusal-sequencing).

## Recommendations

1. **Adopt the refined MA-5 prose** (§ Synthesis 8) — sharper score-0 anchor catalogue with four named sub-patterns (a)–(d), upstream-class enumeration expanded to include positioning explicitly, sequencing-vs-parallel-tracking made load-bearing.

2. **Add three structural_gate checks** for the marketing_audit lane: upstream-diagnosis section presence; upstream-class lexical coverage with evidence reference; binding-constraint declaration. ~50–100 LOC; shrinks slot-fill Goodhart surface.

3. **Weight the calibration set toward upstream-evidence fixtures.** At least 30% of the 100-fixture marketing_audit calibration set should have upstream-evidence shape, so MA-5 has separable failure surface. Without this, MA-1 ↔ MA-5 correlation will exceed the §5 0.7 threshold and the redundancy check drops MA-5.

4. **Hold the ≤5 ceiling.** The upstream-diagnostic axis is deepened into MA-5, not split into a 6th criterion. §5's justified-breach is reserved for LLM-specific failure surfaces with measured 2024–2026 effect sizes; upstream-misdiagnosis is a general analytical failure quantitatively amplified by LLM training bias, not a qualitatively new surface.

5. **Variance-instrumentation watch on MA-5.** Per §11.5, track MA-5 variance per generation. If variance grows monotonically over 3 generations (signaling slot-fill emergence) OR mean compresses toward middle (signaling judge ambiguity), redesign — don't calibrate.

6. **First-cohort overfitting watch.** The six upstream classes are derived from B2B SaaS practitioner literature. Healthcare-practice fixtures (Klinika-shape) will likely have practice ops / payer mix / regulatory positioning as upstream classes; legal-services fixtures (DWF-shape) will likely have practice-area-portfolio and partner-economics. Per CI v3.3's first-cohort overfitting reduction, treat the SaaS-derived list as concrete-anchor reference, not architectural-target. Re-validate when client #5+ onboards.

## Open questions

1. **Calibration weighting confirmation.** The 30%-upstream-evidence-fixture recommendation is a starting point, not literature-derived. Re-validate after first redundancy check.

2. **"Wrong upstream class named" failure (sub-pattern e).** Ground-truth-dependent; calibration-set-dependent, not judge-prose-dependent. Open: how should calibration labels handle fixtures where even practitioners disagree on the binding constraint? Likely: 3+ JR-vetted practitioner labels per fixture, disagreement → "genuinely ambiguous" flag.

3. **Vertical-specific upstream class lists.** Healthcare-practice and legal-services need their own enumeration. Open: should structural_gate's lexical coverage check be parameterised by vertical, or should the judge be vertical-aware via the shared wrapper? Defer to fixture validation.

4. **Simmonds-style marketing-internal upstream.** Distribution-vs-creation is upstream inside the marketing function. Is this MA-5 territory or MA-3 territory? Likely MA-3 (revenue trace); MA-5 stays narrowly on upstream-of-marketing.

5. **Sequencing-vs-parallel discrimination strength.** The redraft makes sequencing load-bearing. Open: can the judge reliably distinguish "sequences behind" from "lists in parallel" on compressed audit text where parallel-listing may dominate? Validate on fixtures.

## Citations

**Practitioner sources (primary):**

- Ellis, Sean. *Hacking Growth* (2017). PMF survey (40%-very-disappointed threshold), ICE, North Star Metric. Lenny's Newsletter interview: https://www.lennysnewsletter.com/p/the-original-growth-hacker-sean-ellis. PMF-survey template: https://www.zonkafeedback.com/templates/sean-ellis-product-market-fit-survey-template.
- Balfour, Brian. "Four Fits For $100M+ Growth": https://brianbalfour.com/four-fits-growth-framework. "Why Product Market Fit Isn't Enough": https://brianbalfour.com/essays/product-market-fit-isnt-enough. Reforge: https://www.reforge.com/blog/four-fits-in-action.
- Rachitsky, Lenny, and Dan Hockenmaier. "Drive Growth by Picking the Right Lane." First Round Review: https://review.firstround.com/drive-growth-by-picking-the-right-lane-a-customer-acquisition-playbook-for-consumer-startups/. Lenny's Newsletter: https://www.lennysnewsletter.com/.
- Dunford, April. *Obviously Awesome* (2019); *Sales Pitch* (2023). Positioning framework starting from competitive alternatives.
- Campbell, Patrick. ProfitWell pricing audits. Intercom interview: https://www.intercom.com/blog/podcasts/profitwells-patrick-campbell-on-the-art-and-science-of-pricing/. Acquired episode: https://www.acquired.fm/episodes/pricing-everything-you-always-wanted-to-know-but-were-afraid-to-ask-with-profitwell-ceo-patrick-campbell.
- Laja, Peep. CXL ResearchXL: https://cxl.com/conversion-rate-optimization/how-to-create-a-cro-process-by-peep-laja/. Wynter messaging-resonance: https://wynter.com/solutions/messaging-resonance-audit.
- Tunguz, Tomasz. SaaS benchmarks: https://tomtunguz.com/saas-startup-benchmarks/. CAC payback as GTM-efficiency anchor.
- Ries, Eric. *The Lean Startup* (2011). Vanity-vs-actionable, applied recursively to recommendations.
- McClure, Dave. "AARRR! Pirate Metrics": https://mcgaw.io/wp-content/uploads/2016/04/PirateMetrics_Final.pdf. "Find the weakest point and focus" — canonical bottleneck-locating prescription.
- Simmonds, Ross / Foundation Inc. Distribution-first content: https://foundationinc.co/. ContentGrip interview: https://www.contentgrip.com/foundation-digital-agency-ross-simmonds/.

**Consultancy methodology:**

- Kalungi. "How to Conduct a B2B Marketing Audit": https://www.kalungi.com/blog/how-to-b2b-saas-marketing-audit. 95-point audit: https://www.kalungi.com/audit. One-page founder readiness audit (canonical upstream-gate instrument): https://www.kalungi.com/blog/one-page-marketing-readiness-audit-for-saas-founders. SaaS growth stages: https://www.kalungi.com/blog/saas-growth-stages.
- Bell Curve / Demand Curve. Audit-then-strategy: https://www.bellcurve.com/. Growth Guide: https://www.demandcurve.com/growth/intro.
- TripleDart. B2B Marketing Audit Guide: https://www.tripledart.com/b2b-marketing/audit.
- ByDefaultCMO. Marketing audit system: https://www.bydefaultcmo.com/marketing-audit-system.

**Fractional-CMO 30/60/90 playbooks:**

- Envizon: https://www.envizon.com/blog/the-fractional-cmo-playbook-what-to-expect-in-your-first-90-days.
- SaaSConsult: https://saasconsult.co/blog/fractional-cmo-30-60-90-day-plan/.
- ASP Marketing: https://asp-marketing.com/blog/fractional-cmo-for-saas.

**Project-internal references:**

- `docs/rubrics/judge-design-guide.md` (v2.1) — §1 outcome questions, §2 structural_gate split, §5 ≤5 ceiling + justified-breach, §11 Goodhart resistance, §11.5 variance instrumentation, §12 anti-patterns.
- `docs/research/2026-05-18-judges-domain-marketing-audit.md` — generalist domain research; this deliverable deepens MA-5 / upstream-diagnostic axis.
- `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md` (DRAFT v0) — Step-1 spec; this deliverable's recommendations refine MA-5 in that spec.
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (v3.3) — CI spec; precedent for justified-breach exception (§ Synthesis 7) and first-cohort overfitting reduction (Recommendation 6).
