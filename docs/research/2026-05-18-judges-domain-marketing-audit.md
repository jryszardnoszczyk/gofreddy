---
date: 2026-05-18
type: research deliverable
status: complete
topic: domain research — marketing audit lane
parent: docs/rubrics/judge-design-guide.md
sibling: docs/research/2026-05-15-judges-domain-competitive.md
---

# Domain Research: What Makes an Excellent Marketing Audit + Remediation Roadmap

**Purpose:** Ground the `marketing_audit` lane judge in published practitioner methodology, named consultancy exemplars, and founder/CMO heuristics — not statistical properties, not transferred meta-patterns from other lanes, and not framework-checking prose. Outcome questions about reader behaviour, anchored in concrete behavioural descriptions.

**Scope:** Synthesis of practitioner methodology from Sean Ellis (ICE, North Star, PMF survey), Brian Balfour / Reforge (Four Fits, growth loops), Andrew Chen (a16z growth essays), Lenny Rachitsky (growth loops, channel lanes), Peep Laja (CXL ResearchXL, Wynter messaging-resonance), Ross Simmonds / Foundation Inc (content audits), Patrick Campbell (pricing audits), Tomasz Tunguz and Bessemer (cloud benchmarks), Eric Ries (vanity-vs-actionable metrics), Dave McClure (AARRR), Animalz (editorial-first audits), Demand Curve / Bell Curve (paid-acquisition audits), Kalungi (B2B SaaS audit scorecard), and the fractional-CMO 30/60/90 pattern documented across multiple SaaS advisory shops. Anti-patterns drawn from the same sources where named explicitly.

---

## 1. What Makes a Marketing Audit Actionable

### Who actually reads it

Marketing audits are NOT consumed by "marketers" as a generic class. The deliverable is consumed by one of four sharply different personas, and the criteria a great audit must satisfy diverge sharply by reader.

**Founder-CEO at pre-Series-B SaaS ($0–$5M ARR).** Reads it during a runway-tight quarter when the marketing line item is the largest discretionary spend and conversion is uncertain. After reading, they answer one question: *which one or two bets do I fund for the next 90 days, and which do I cut?* The fractional-CMO scope-of-work literature (ASP Marketing, ThinkCap Advisors, Strategic Pete, Envizon, SaaS Hero, SaaSConsult) converges on a Day-30 deliverable of "clear ICP doc, audit findings, prioritized roadmap" precisely because the founder cannot consume more than that without the deliverable losing its purpose.

**Fractional or interim CMO at $5M–$50M ARR.** Reads it as the input to their first 90-day plan. They will run the audit as the discovery phase of their own engagement. After reading, they answer: *what foundation work happens in days 0–30, what experiments in days 31–60, what scaling moves in days 61–90?* Envizon's playbook and the SaaSConsult 30/60/90 template are the dominant industry references; both make the audit the gate, not a deliverable in itself.

**Head of Growth or in-house Director of Marketing at Series-B-or-later.** Reads it as ammunition. They already have a theory of the bottleneck; the audit either supports their case to the CEO/board or doesn't. After reading, they answer: *which slide do I bring into the next exec meeting, and what budget reallocation does it justify?* The Klue executive-briefing pattern (point-of-view-at-top, then evidence) maps directly: the in-house Head of Growth needs a headline that can survive a board slide, not a research dump.

**Founder-CMO hybrid at $1M–$10M ARR.** Reads it when their pipeline has stalled and they cannot tell whether the issue is messaging, channel mix, ICP, or product-market fit itself. After reading, they answer: *is the problem upstream of marketing (PMF, ICP), inside marketing (channel mix, message), or downstream (sales motion)?* Sean Ellis's PMF survey ("how would you feel if you could no longer use this product?", 40%-very-disappointed threshold) is the canonical instrument for separating these layers; an audit that doesn't help the founder distinguish them is recommending into the wrong layer.

### Empirical patterns from audits that produced action

**Pattern 1 — Diagnosis before prescription.** The strongest convergence across Kalungi, Bell Curve, Demand Curve, and the fractional-CMO playbooks is that the audit MUST identify the binding constraint before recommending. Bell Curve's stated methodology starts every engagement with audit-then-strategy precisely because fixing foundational issues before scaling spend is non-negotiable. Kalungi's 95-point inspection produces a "5-point-scale marketing report card" across brand, SEO, positioning, messaging, website, paid channels — the scorecard exists so the next-action recommendation is locatable to a specific weakness.

**Pattern 2 — Stage-appropriate recommendations.** A recommendation tuned to a $20M-ARR company is wrong for a $2M-ARR company; the Kalungi SaaS-growth-stages literature names this directly. "Applying earlier-stage logic as you scale is the most common strategic mistake" — and the inverse, applying late-stage best practices to an early-stage company, is the audit failure mode that burns the most runway. A great audit names the company's current stage (pre-traction, traction, scaling, expansion) and only then names what fits.

**Pattern 3 — Revenue chain, not activity chain.** Every observation must trace to a revenue mechanism. The fractional-CMO playbooks converge on five metrics that define success: pipeline sourced, MQL→SQL conversion, CAC payback, organic traffic to product/comparison pages, trial-to-paid. An audit that observes "blog traffic is up" without tracing the chain to revenue is reporting, not auditing.

**Pattern 4 — Prioritisation by impact AND speed-to-impact.** TripleDart, ByDefaultCMO, and Kalungi all use a two-axis prioritisation: revenue impact potential × speed to impact. Founders need to see what they can ship in 30 days that moves a needle, and which slower bets justify their longer payback. A flat list of 12 recommendations of equal weight is a failure; a 2×2 of "quick wins / foundational bets / long-horizon / cut" is the discipline.

**Pattern 5 — Time-bound, scoped, owner-named.** Recommendations must say what gets done by when, with what budget, by whom. The fractional-CMO Day-30/60/90 cadence is the industry template for this — and audits that lack the cadence default to "consider exploring" verbs that no founder can commit to. The Lean Startup distinction between vanity metrics ("page views are up") and actionable metrics ("trial-to-paid moved from 2% to 3.4% after the onboarding change") applies recursively to recommendations: a vanity recommendation is one a founder cannot commit to executing.

**Pattern 6 — Surfaces the upstream problem when it's the real one.** The hardest audit to write is the one that concludes "the bottleneck isn't marketing." Sean Ellis's PMF survey exists for exactly this case. Kalungi publishes a one-page "marketing readiness audit" whose only purpose is to tell a founder whether marketing CAN succeed at the company's current state — gaps in ICP, positioning, or product cannot be patched by demand-gen budget. An audit that always recommends more marketing has failed the discipline.

### Dimensions practitioners cite

Synthesising across the named practitioner sources, the dimensions a senior reader actually evaluates are:

1. **Names the binding constraint** (vs. surveying all dimensions equally)
2. **Locates the company on a stage map** before recommending stage-appropriate moves
3. **Traces every recommendation to a revenue mechanism**, not an activity metric
4. **Prioritises hard** (top 2–3 quick wins, 1–2 foundational bets, explicit cuts)
5. **Time-bounds, scopes, and owners every recommendation**
6. **Tells the founder when the problem is upstream of marketing** (PMF, ICP, product, sales)
7. **Degrades gracefully when evidence is partial** — names what it would need to commit further

---

## 2. What Separates Great Audits from Mediocre

Named practitioners identify specific, recurring failure modes — not abstract criticisms.

**The "ten-page PDF of generic recommendations" failure** (McKee Creative, Helen Cox Marketing, Apiary Digital, Umbrex). The dominant audit failure mode in the SMB and early-stage SaaS market is recommendations that "could apply to any business in any category." The diagnostic test: if the same recommendations would land for a competitor in a different vertical with different ARR, the audit is not an audit — it is a checklist.

**The "checklist vs. effectiveness" failure** (Growth Syndicate, ThinkCap, Kalungi). "Checklists measure presence, not effectiveness — having a content calendar does not mean your content strategy is working." The Kalungi 95-point inspection mitigates this specifically by requiring a 5-point quality score on each dimension, not a boolean has/doesn't-have. A great audit asks "is the marketing function producing a return on this dimension?" — never "does the marketing function HAVE this dimension?"

**The "do more content" failure** (Foundation Inc, Animalz). Ross Simmonds names this directly: "many teams do not have a content problem; they have a visibility and prioritization problem." Animalz's editorial-first framing of content audits is structured to surface the prioritisation gap rather than recommend volume. The Foundation Inc audit discipline starts with the *intent* of each piece — "whether meant to rank on Google, generate traction on social, or elevate corporate culture" — and only then evaluates fit. An audit that recommends "publish more" without naming which intents the existing content has under-served is the canonical failure mode in B2B SaaS content advisory.

**The vanity-metric overload failure** (Eric Ries, Lean Startup; Improvado; ProductPlan). Eric Ries's foundational distinction: vanity metrics "make you feel good but don't mean anything." Page views, total registered users, social-media followers, raw downloads — all are vanity. The audit failure mode is presenting these as headline findings rather than as the diagnostic context that precedes an actionable observation. The Marketoonist cartoon makes this concrete: an audit that leads with "impressions are up 40%" without tracing to qualified pipeline has failed the Ries test.

**The "no prioritisation" failure** (Kalungi, TripleDart, ByDefaultCMO). Flat lists of 8+ recommendations of equal weight. The Klue executive-briefing pattern's executive failure mode is "information overload" — and the marketing-audit version is the same: a senior reader will not act on the eighth recommendation. The Kalungi cap of "top 3-5 priorities" is the standard.

**The "wrong stage" failure** (Kalungi SaaS-growth-stages, Maxio, Reforge). Brian Balfour's four-fits framework names this as a *structural* failure: market-product fit, product-channel fit, channel-model fit, and model-market fit are all stage-dependent, and "you can't think about the four Fits in isolation because together they form an ecosystem." An audit that recommends product-led growth tactics to a sales-led company at $3M ARR is wrong even if the tactics are best-practice — they don't fit. The Reforge canon names "premature scaling" — going from MVP to paid acquisition before validating retention — as the dominant cause of burned early-stage runway.

**The "ignoring distribution" failure** (Foundation Inc, Lenny Rachitsky, First Round Review). Ross Simmonds's "create once, distribute forever" mantra exists because audits routinely diagnose creation problems when the actual constraint is distribution. Lenny Rachitsky and Dan Hockenmaier's customer-acquisition lanes framework on First Round Review names a related failure: "there are very few routes to scalable new customer acquisition," and an audit that doesn't locate the company in one of those lanes is recommending in the abstract.

**The "no budget/effort scoping" failure** (Demand Curve, Bell Curve, fractional-CMO playbooks). A recommendation without a budget envelope and an effort estimate is not a recommendation — it is a wish. The Bell Curve agency literature is explicit that paid-acquisition recommendations require channel-by-channel spend allocation; the Sean Ellis ICE framework (Impact, Confidence, Ease) makes effort a first-class scoring dimension. An audit that says "invest in SEO" without naming the budget, the months-to-impact, and the team capacity required is a vague verb in disguise.

**The "no revenue tie" failure** (Tomasz Tunguz, Bessemer, Patrick Campbell). Tunguz's "CAC Payback is the single best metric to evaluate the efficiency of a SaaS company's GTM" — and any audit that does not connect its recommendations to a CAC payback delta has skipped the unit-economics layer. Bessemer's State of the Cloud names CAC payback as a top-5 investing screen. Patrick Campbell's pricing audits at ProfitWell trace every recommendation to monthly recurring revenue. The audit failure mode is recommendations whose impact lives entirely above the revenue line — brand impressions, share of voice, social engagement — without the chain to a number a founder can spend against.

**The "we already do that" failure** (Wynter, Peep Laja). Audits that miss what the company actually believes about itself. Wynter's messaging-resonance audits exist because internal sense of "we have a clear ICP" routinely diverges from external buyer perception. The CXL ResearchXL framework's heuristic-analysis step (audits key pages for relevancy, motivation, friction from the buyer's perspective, not the founder's) is the discipline. An audit that uncritically inherits the founder's framing — "our positioning is sharp, we just need more leads" — has failed the Laja test.

---

## 3. Industry Frameworks the Rubric Should Leverage

These are the frameworks practitioners actually use. Each gives the judge a specific reasoning move. **None of these framework names belongs in the rubric prose** — they are the judge's reasoning toolkit, not features the audit must contain.

### Sean Ellis — PMF Survey + ICE + North Star
Sean Ellis's contribution is the **upstream-vs-marketing diagnostic**. The PMF survey ("How would you feel if you could no longer use this product?", with the 40%-very-disappointed threshold) lets a judge ask whether the audit has considered that the bottleneck might be PMF rather than marketing. ICE (Impact × Confidence × Ease, 1–10 each) is the canonical prioritisation lens — Impact alone is not enough, Confidence and Ease determine what actually ships in a 30-day window. North Star Metric methodology gives the test for whether the audit has identified a single metric that aligns the team — versus a dashboard of 14 metrics where nothing is the focus.

### Brian Balfour — Four Fits
Balfour's framework (Market-Product, Product-Channel, Channel-Model, Model-Market) tests the audit for **ecosystem coherence**. A recommendation that fixes Product-Channel without checking whether it breaks Channel-Model is the failure mode. Balfour's three load-bearing claims: all four fits must align, they form an ecosystem (cannot be optimised in isolation), and they continuously change. The judge's question: does the audit treat the marketing function as an ecosystem, or as a list of channels?

### Lenny Rachitsky + Dan Hockenmaier — Growth Loops + Customer Acquisition Lanes
The growth-loops-vs-funnels distinction is the test for whether the audit recommends compounding mechanics or linear additive ones. The First Round Review "lanes" framework names that there are *few* routes to scalable acquisition (paid, content/SEO, virality, sales, partnerships, community) and an audit must place the company in one lane and recommend deepening it, not generically recommend "diversify channels." The Rachitsky test: does the audit recommend mechanisms that compound (referral loops, content compounding, ICP-driven word-of-mouth) over mechanisms that require linear re-spend?

### Dave McClure — AARRR (Pirate Metrics)
McClure's Acquisition / Activation / Retention / Referral / Revenue funnel gives the judge a **bottleneck-locating test**. A great audit identifies which stage of the funnel is the binding constraint and why fixing earlier stages won't help. The audit failure mode is dumping observations across all five stages with no claim about which one matters most. McClure's own published prescription is to "find the weakest point of a business and focus on it" — not to optimise the whole funnel in parallel.

### Peep Laja / CXL — ResearchXL
The six-step Conversion Research model (Heuristic Analysis, Technical Analysis, Digital Analytics, Qualitative Surveys, User Testing, Mouse Tracking) tests the audit for **evidence-source triangulation**. An audit that asserts "the landing page underperforms" using only the founder's intuition has failed the Laja test. An audit that triangulates analytics, qualitative survey, and heuristic page-audit has passed. ResearchXL's value to the judge is the discipline that every claim should rest on evidence from at least two of the six sources, never just one.

### Eric Ries — Vanity vs. Actionable Metrics
The Lean Startup distinction is the **headline-finding hygiene check**. Page views, follower counts, raw impressions, downloads-without-activation are vanity. Conversion rate, activation rate, CAC payback, trial-to-paid, MQL→SQL are actionable. The judge's question: do the audit's findings lead with vanity or actionable metrics?

### Tomasz Tunguz / Bessemer — CAC Payback + Cloud Benchmarks
Tunguz's "CAC Payback is the single best metric to evaluate the efficiency of a SaaS GTM" and Bessemer's State-of-the-Cloud benchmarks (SMB CAC payback under 12 months, mid-market under 18) give the **unit-economics anchor**. The audit failure mode is recommendations that ignore CAC payback. The judge tests whether at least one recommendation in the roadmap is tied to a CAC-payback or LTV:CAC delta the founder can actually measure.

### April Dunford — Positioning + Competitive Alternatives
Dunford's framework (competitive alternatives → unique attributes → value → target market → market category) is **positioning-audit hygiene**. The named failure mode: audits that critique a company's positioning without identifying what customers would do if the product didn't exist. The judge's test: does the audit's messaging critique start from the customer's competitive alternatives, including "do nothing" and substitutes?

### Patrick Campbell / ProfitWell — Pricing as a Marketing Lever
Campbell's body of work names pricing as the marketing decision with the highest leverage. A great B2B SaaS audit considers pricing — value metric, packaging, price points, expansion paths — not just demand gen. The judge tests whether the audit has interrogated pricing at all, or treated it as out-of-scope.

### Ross Simmonds / Foundation Inc — Distribution-First Content
"Create once, distribute forever." The framework gives the judge the **distribution-vs-creation diagnostic**. A great content audit reframes "we need more content" as "we need to distribute existing content to a wider audience first." The judge tests whether the audit names distribution mechanics (newsletter, social, syndication, internal linking, repurposing) before or after recommending creation volume.

### Bell Curve / Demand Curve — Paid Acquisition Audit
The Demand Curve "Growth Guide" and Bell Curve agency methodology give the **paid-channel-readiness diagnostic**. The named pattern: fix landing-page conversion and tracking architecture before scaling spend; "fixing structural problems rather than just increasing ad spend." The judge tests whether paid-channel recommendations have a foundation-then-scale sequence or jump straight to "increase budget."

---

## 4. Proposed Judge Criteria (5 Outcome Questions, Draft)

Each criterion is an outcome question phrased per the design guide (§4). Score-1 and score-0 anchors are concrete behavioural descriptions. No framework names appear in the criterion prose. The framework citations live in the rationale for *why* this is what experts evaluate.

### MA-A — Founder Can Name the Binding Constraint
**Outcome question (binary):** After reading the audit, can the founder/CMO name in one sentence which single dimension of the marketing function is the binding constraint on growth, and why?

**Why experts evaluate this:** The strongest convergence across Bell Curve, Demand Curve, Kalungi, and the fractional-CMO playbooks is that audits must diagnose before they prescribe. Eric Ries's vanity-vs-actionable distinction, Dave McClure's "find the weakest point and focus" prescription, and Brian Balfour's four-fits ecosystem framing all anchor on the same discipline: name the binding constraint before recommending.

**Score 1 (yes):** The audit names one specific constraint (e.g., "the website converts at 0.4%, half the SaaS median; this is the binding constraint, not lead volume") with at least two evidence sources supporting the diagnosis. The constraint is locatable — a specific stage of the funnel, a specific channel, a specific message, a specific upstream gap (PMF, ICP, product).
*Example (do not optimize toward this): "Your trial-to-paid conversion is 1.8% versus the SaaS median of 6%; until that moves, paid-acquisition budget is being spent on water that leaks out before revenue."*

**Score 0 (no):** The audit surveys multiple dimensions at roughly equal weight, or names a vague constraint ("messaging could be sharper") without evidence, or names multiple constraints without ranking, or treats every channel/dimension as a parallel improvement opportunity.

### MA-B — Founder Can Commit to One Specific Experiment in the Next 30 Days
**Outcome question (binary):** After reading the audit, would the founder/CMO commit to one specific, scoped, measurable experiment in the next 30 days — with named owner, budget, and success metric?

**Why experts evaluate this:** The fractional-CMO 30/60/90 cadence is the industry template precisely because the Day-30 commit is the test of audit actionability. Sean Ellis's ICE framework (Impact × Confidence × Ease) and the Product Marketing Alliance's "specific, measurable, tied to business impact" standard converge here. The Lean Startup vanity-vs-actionable distinction applies to recommendations as well as metrics: a vanity recommendation is one a founder cannot commit to executing.

**Score 1 (yes):** At least one recommendation specifies: the action ("ship a homepage variant testing X positioning"), the owner ("marketing lead + freelance designer"), the budget envelope ("under $5k including testing tool"), the timeline ("4 weeks"), and the success metric ("primary CTA click rate, measured against current baseline").
*Example (do not optimize toward this): "Week 1: rewrite homepage hero against the buyer-language patterns from the 12 Gong calls. Week 2-3: ship A/B test. Week 4: read result against current 0.8% CTA rate baseline. Owner: head of marketing. Budget: $3k for tool + design."*

**Score 0 (no):** Recommendations use vague verbs (explore, consider, evaluate, look into, optimise, improve), lack owners or budgets, or list 8+ initiatives of equal weight with no commitment-grade specificity. A recommendation that requires the founder to make a follow-up planning meeting before they can commit has failed.

### MA-C — Each Recommendation Traces to a Revenue Mechanism
**Outcome question (binary):** Does every recommendation in the audit trace through an explicit chain to a revenue mechanism — a specific input the founder can spend against, a specific metric that would move, and a specific revenue line that would respond?

**Why experts evaluate this:** Tomasz Tunguz's "CAC Payback is the single best metric to evaluate GTM efficiency," Bessemer's CAC-payback benchmarks (SMB <12 months, mid-market <18), and Patrick Campbell's pricing-as-marketing-lever framing all anchor on the same discipline: marketing audits must operate in the unit-economics layer. The fractional-CMO playbooks' five-numbers-that-define-success (pipeline sourced, MQL→SQL, CAC payback, organic traffic to product pages, trial-to-paid) operationalise this.

**Score 1 (yes):** Each recommendation names the metric it moves (CAC payback, trial-to-paid, MQL→SQL, organic comparison-page traffic, expansion revenue) and the chain from the marketing input through to that metric. A recommendation about brand impressions specifies how brand impressions are expected to flow into a downstream conversion metric.
*Example (do not optimize toward this): "Move pricing from flat $99/mo to value-metric (per active seat) is expected to lift expansion revenue from 8% to 18% based on the cohort analysis on slide 14, with the larger top-quartile accounts adopting per-seat first."*

**Score 0 (no):** Recommendations live entirely above the revenue line (brand awareness, impressions, social engagement, follower count) without any chain to a downstream metric. The audit reports vanity metrics as headline findings. Recommendations are activity-shaped ("publish 8 blog posts per month") without specifying what business metric the activity is expected to move.

### MA-D — The Audit Locates the Company on a Stage Map
**Outcome question (binary):** Does the audit name the company's current stage of growth and tailor its recommendations to that stage, including refusing to recommend best practices that are wrong for the stage?

**Why experts evaluate this:** Kalungi's SaaS-growth-stages playbook, Brian Balfour's four-fits ecosystem (all four are stage-dependent), and the Reforge "premature scaling" pattern name this as the dominant failure mode in SaaS marketing advisory. Applying earlier-stage logic at scale burns growth potential; applying later-stage logic early burns runway. The audit's job is to refuse stage-inappropriate best practices.

**Score 1 (yes):** The audit names the company's stage (pre-traction, traction, scaling, expansion, or equivalent) with at least one observable anchor (ARR band, retention cohort signal, channel-fit signal). At least one recommendation explicitly refuses a best practice on stage grounds ("at $1.8M ARR with 88% net retention this is too early to invest in ABM tooling; the ICP signal is too noisy to target accounts at scale yet").
*Example (do not optimize toward this): "You are mid-traction (post-PMF, pre-scale) at $2.4M ARR with 91% NRR. The instinct to hire a paid-acquisition manager is wrong for this stage; the upstream constraint is sales motion clarity, and paid spend at current LTV:CAC of 1.8 will worsen unit economics."*

**Score 0 (no):** The audit applies the same playbook regardless of stage. Recommendations include best practices typical of later-stage companies (full marketing-ops stack, demand-generation programmes, ABM tooling) without checking whether the company has the foundations to deploy them. The audit reads as if the same recommendations would land for a $500k-ARR company and a $20M-ARR company.

### MA-E — The Audit Surfaces an Upstream Problem When That's the Real Constraint
**Outcome question (binary):** When the binding constraint is upstream of marketing (PMF, ICP, product, pricing, sales motion), does the audit say so plainly — even though saying so means the audit's own recommendations get smaller?

**Why experts evaluate this:** Sean Ellis's PMF survey exists for exactly this case. Kalungi publishes a one-page marketing-readiness audit whose sole purpose is to tell founders when marketing CANNOT succeed at the current state. Patrick Campbell's pricing audits routinely surface pricing as the binding constraint over demand-gen. Peep Laja / Wynter's messaging-resonance audits surface the case where the company's internal positioning is wrong before any channel-level work makes sense. The Competitive Intelligence Alliance's "kill your darlings" discipline applies recursively: an audit edited to comfort the founder by recommending more marketing has failed.

**Score 1 (yes):** Where evidence suggests the constraint is upstream (low retention, low PMF-survey scores, fundamental ICP confusion, pricing-model mismatch, sales-motion misalignment), the audit names it directly and sequences its marketing recommendations behind the upstream fix. The audit is willing to recommend pausing demand-gen spend, deferring channel diversification, or running a PMF re-test before scaling marketing.
*Example (do not optimize toward this): "Your monthly churn is 6.4%; LTV at this churn rate means CAC payback cannot work below an ACV that is 4x your current. The constraint is retention, not acquisition. Pause the SEO investment and the paid-LinkedIn pilot; the marketing budget should fund three Wynter-style messaging tests to diagnose whether the issue is positioning or product fit."*

**Score 0 (no):** The audit always recommends more marketing. The audit treats retention, ICP, pricing, or sales motion as out-of-scope even when the evidence points at them. The audit lacks any "the bottleneck is upstream of marketing" branch — implying its own recommendations are always the answer.

---

## 5. Sources Cited

**Frameworks (primary practitioner sources):**
- Ellis, Sean. *Hacking Growth* (2017); the Sean Ellis Test for PMF (40%-very-disappointed); ICE prioritisation; North Star Metric methodology. Lenny's Newsletter interview: https://www.lennysnewsletter.com/p/the-original-growth-hacker-sean-ellis ; ICE framework: https://growthmethod.com/ice-framework/ ; PMF survey: https://www.zonkafeedback.com/templates/sean-ellis-product-market-fit-survey-template
- Balfour, Brian. "Four Fits For $100M+ Growth." https://brianbalfour.com/four-fits-growth-framework ; "Why Product Market Fit Isn't Enough." https://brianbalfour.com/essays/product-market-fit-isnt-enough ; Reforge blog: https://www.reforge.com/blog/four-fits-in-action
- Rachitsky, Lenny, and Dan Hockenmaier. "Drive Growth by Picking the Right Lane." First Round Review. https://review.firstround.com/drive-growth-by-picking-the-right-lane-a-customer-acquisition-playbook-for-consumer-startups/ ; Lenny's Newsletter (frameworks compendium): https://startupgtm.substack.com/p/the-lenny-rachitsky-playbook-prompts
- Chen, Andrew. Growth essays at https://andrewchen.com/list-of-essays/ ; "Law of Shitty Clickthroughs"; a16z growth philosophy.
- McClure, Dave. "AARRR! Pirate Metrics for Startups." https://mcgaw.io/wp-content/uploads/2016/04/PirateMetrics_Final.pdf ; in-depth analysis: https://posthog.com/product-engineers/aarrr-pirate-funnel
- Ries, Eric. *The Lean Startup* (2011). Vanity vs. actionable metrics. Tim Ferriss guest post (original): https://tim.blog/2009/05/19/vanity-metrics-vs-actionable-metrics/ ; Improvado synthesis: https://improvado.io/blog/what-is-a-vanity-metric
- Laja, Peep. CXL ResearchXL framework. https://cxl.com/conversion-rate-optimization/how-to-create-a-cro-process-by-peep-laja/ and https://cxl.com/blog/how-to-come-up-with-more-winning-tests-using-data/ ; Wynter messaging-resonance audit: https://wynter.com/solutions/messaging-resonance-audit
- Tunguz, Tomasz. SaaS startup benchmarks. https://tomtunguz.com/saas-startup-benchmarks/ ; CAC payback discipline: https://www.getmonetizely.com/articles/cac-payback-period-a-critical-metric-for-saas-growth-and-sustainability
- Bessemer Venture Partners. "The five accounting metrics for cloud companies." https://www.bvp.com/atlas/cloud-computing-metrics
- Dunford, April. *Obviously Awesome* and *Sales Pitch* — positioning framework starting from competitive alternatives.
- Campbell, Patrick. ProfitWell pricing audits. Intercom interview: https://www.intercom.com/blog/podcasts/profitwells-patrick-campbell-on-the-art-and-science-of-pricing/ ; Acquired episode: https://www.acquired.fm/episodes/pricing-everything-you-always-wanted-to-know-but-were-afraid-to-ask-with-profitwell-ceo-patrick-campbell

**Consultancy methodology (named exemplars):**
- Kalungi. "How to Conduct a B2B Marketing Audit." https://www.kalungi.com/blog/how-to-b2b-saas-marketing-audit ; 95-point marketing audit: https://www.kalungi.com/audit ; one-page founder readiness audit: https://www.kalungi.com/blog/one-page-marketing-readiness-audit-for-saas-founders ; SaaS growth stages: https://www.kalungi.com/blog/saas-growth-stages
- Foundation Inc / Ross Simmonds. "Create once, distribute forever" content audit philosophy. https://foundationinc.co/ ; ContentGrip interview: https://www.contentgrip.com/foundation-digital-agency-ross-simmonds/
- Animalz. Editorial-first content marketing audits. https://www.animalz.co/blog/content-marketing-strategy
- Demand Curve. Growth Guide (intro): https://www.demandcurve.com/growth/intro ; Bell Curve agency: https://www.bellcurve.com/ (audit-then-strategy methodology)
- TripleDart. "B2B Marketing Audit: A Step-by-Step Guide." https://www.tripledart.com/b2b-marketing/audit
- ByDefaultCMO. "Your Complete Guide to Conduct a B2B Marketing Audit." https://www.bydefaultcmo.com/marketing-audit-system
- The Growth Syndicate. "Marketing audit: what it is, how to conduct one, and why it matters for growth." https://www.thegrowthsyndicate.com/resources/marketing-audit

**Fractional CMO 30/60/90 playbooks (the industry template):**
- Envizon. "Fractional CMO Playbook: Your First 90 Days, Week by Week." https://www.envizon.com/blog/the-fractional-cmo-playbook-what-to-expect-in-your-first-90-days
- SaaSConsult. "Fractional CMO 30-60-90 Day Plan." https://saasconsult.co/blog/fractional-cmo-30-60-90-day-plan/
- ASP Marketing. "Fractional CMO for SaaS: Cost, 90-Day Plan & Hiring Guide." https://asp-marketing.com/blog/fractional-cmo-for-saas
- ThinkCap Advisors. "5 Signs Your SaaS Startup Needs a Fractional CMO Before Series A." https://www.thinkcapadvisors.com/post/fractional-cmo-before-series-a
- Strategic Pete. "How a Fractional CMO Builds Predictable SaaS Demand." https://strategicpete.com/blog/fractional-cmo-builds-predictable-saas-demand/

**Failure-mode literature (named anti-patterns):**
- McKee Creative. "What a marketing audit actually reveals (and why most small businesses skip it)." https://mckeecreative.store/what-a-marketing-audit-actually-reveals-and-why-most-small-businesses-skip-it/
- Helen Cox Marketing. "Why a marketing audit is the strategic reset you need." https://helencoxmarketing.co.uk/is-your-marketing-just-noise-why-a-marketing-audit-is-the-strategic-reset-you-need/
- Umbrex. "Common Marketing Failure Modes." https://umbrex.com/resources/what-marketing-is/common-failure-modes-in-marketing/
- Marketoonist (Tom Fishburne). "Marketing vanity metrics." https://marketoonist.com/2016/02/marketing-vanity-metrics.html

---

## Notes for Rubric Authors

1. **MA-A through MA-E are five binary outcome criteria, sized per the design guide §5 ceiling.** Expect 3–4 to survive a redundancy check on real fixtures; MA-A and MA-D in particular may correlate (an audit that doesn't locate stage often also doesn't name the binding constraint). Run the §5 pairwise-correlation redundancy check on the calibration set before locking the rubric.

2. **The five criteria explicitly avoid framework names in the criterion prose.** AARRR, ICE, four-fits, ResearchXL, Sean Ellis Test, North Star, CAC payback — these are the judge's reasoning toolkit (§3) but not in the rubric body. The Phase 4 rollback pattern at `c76f051` is the precedent that drove this constraint.

3. **One axis the rubric does NOT include but practitioners use:** the *executive sponsorship and team-capacity* check. A great audit considers whether the company HAS the marketing team to execute the recommendations. This was deliberately cut because it slides too easily into a feature-check ("does the audit have a 'team capacity' section?") rather than testable as an outcome. Reconsider if MA-B turns out to underfire on real fixtures.

4. **Real exemplars to anchor judge prose later (do not optimise toward these):** Kalungi's 95-point inspection scorecard (MA-A, MA-D), the fractional-CMO Day-30 deliverable pattern (MA-B), Patrick Campbell's pricing audits at ProfitWell (MA-C, MA-E), Wynter messaging-resonance audits (MA-E), Sean Ellis's PMF re-test recommendation when the data points upstream of marketing (MA-E).

5. **What to deliberately not encode** (per design guide §11): no length thresholds, no minimum number of recommendations, no required-section list, no "the audit must use the ICE framework" prose, no calibration tweaks for σ-widening. The criteria test for the effect on the reader, not the artifact's surface features.
