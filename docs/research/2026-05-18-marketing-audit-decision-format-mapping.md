---
date: 2026-05-18
type: research deliverable
status: complete
topic: marketing_audit decision-to-format mapping (fire-CMO / channel-cut / reposition / pivot / 30-60-90 / quarterly memo)
parent: docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md
sibling: docs/research/2026-05-18-ci-decision-format-mapping.md
companion: docs/research/2026-05-18-judges-domain-marketing-audit.md
---

# Marketing-Audit Decision-to-Format Mapping

## 1. TL;DR (recommendation)

The marketing_audit lane's v0 spec assumes one canonical reader (founder/CMO at pre-Series-B SaaS) producing one canonical artifact (Day-30 audit feeding a 30/60/90 plan). That holds for one of six decisions the audit actually has to serve. The other five each impose a different reader, evidence regime, and format. Like CI, **six decisions collapse into three clusters**, and the cluster boundary is set by **decision reversibility × audit consumer's authority horizon**, not by topic.

**Cluster A — Personnel verdict** (hire/fire CMO; restructure marketing function; replace an agency). Reader is the CEO or board chair commissioning the audit as evidence for a personnel call. Horizon to decision: 1–3 weeks. Optimal format is a **3–7 page executive memo with a binary verdict up front + 2–3 evidence pillars + named off-ramps** — the audit's analytical signature is the **performance-attribution sieve** (separate exogenous demand collapse from operator error). Named exemplar: McKinsey/Bain "operator review" memos used in PE portfolio quarterly governance; Bessemer/USV portfolio CMO-fitness reviews.

**Cluster B — Channel/budget reallocation** (cut a channel, double-down a channel, kill an agency, restructure paid mix). Reader is a founder/CMO or head of growth with operational authority. Horizon: 2–6 weeks (next quarterly budget cycle or sooner). Optimal format is a **5–10 page channel-by-channel scorecard + reallocation recommendation**, with unit-economics anchored on CAC payback by channel and a named experiment ladder. Named exemplar: Bell Curve / Demand Curve / Tinuiti paid-acquisition audits; Animalz content-audit format; ProfitWell pricing audits.

**Cluster C — Strategic reset** (reposition, repackage, pivot category, change ICP, restructure pricing model). Reader is the founder-CEO; the audit is the foundational document a fractional CMO or interim VP-Marketing inherits. Horizon: 4–13 weeks (matches the fractional-CMO 30/60/90 cadence). Optimal format is a **15–25 page diagnostic + 30/60/90 plan**, anchored on April Dunford-style positioning teardown, Sean Ellis PMF-survey results, and ICP-resegmentation evidence. Named exemplar: the fractional-CMO Day-30 deliverable (Envizon, SaaSConsult, Strategic Pete, ASP Marketing playbooks); MKT1 strategy memos; First Round Review GTM teardowns.

**Routing recommendation: route at the workflow level, not the judge level.** Like CI, the marketing_audit lane should accept a `decision_shape` workflow input (A / B / C) that switches `substrate` template, `structural_gate` length+shape check, and fixture set. The judge stays format-agnostic because MA-1 through MA-5 are outcome questions ("can the founder name the binding constraint?", "would they commit to one specific experiment?") that survive cluster shift. Adding a sixth criterion testing format would re-introduce the feature-checking pathology rolled back at `c76f051`.

**The single most damaging failure mode this mapping surfaces:** the **fire-CMO-via-30-page-teardown** category error. A board commissioning a personnel verdict gets a 25-page best-practices teardown; the verdict is buried on page 17 inside three pages of channel-by-channel mechanics; the board reads page 3, sees no binary call, defers the decision another quarter while the company burns runway. Symmetrically, a founder commissioning a reposition gets a 4-page "fire the CMO" memo and is left without the diagnostic depth needed to actually reposition. The v0 spec at §1 ("30-minute Tuesday afternoon, Friday leadership meeting") implicitly assumes Cluster B; against Cluster A or Cluster C the v0 format expectation is wrong in the same direction CI's "commit by next week" was wrong for Evaluate-cluster decisions.

**Cross-vertical anchor for "right level of detail for the decision":** **decision irreversibility plus consumer authority horizon**. A board firing a CMO needs 5 pages because the call is binary and the off-ramps are bounded. A founder repositioning needs 20 pages because every recommendation cascades through ICP / message / channel / pricing and the founder will own the rebuild. The relationship is the same one Roger Martin observes about strategic choice: detail should match the irreversibility of what's being chosen, not the conventionality of what's being audited.

**Specific edits to v0 spec:** (1) Add `decision_shape` as workflow input. (2) Loosen MA-2's "30-day experiment with named owner + budget + success metric" anchor to "commit to the decision-shape-appropriate next action" — a personnel verdict isn't a 30-day experiment, it's a vote. (3) Tighten MA-4's stage-map criterion: the audit must locate the company on the stage map AND name the decision-shape it serves; mismatched-detail audits score 0 even if every other criterion scores 1. Details in §5.

---

## 2. Per-decision deep dive

### Decision 1 — Fire/hire CMO (Cluster A)

**Decision shape.** Continue, formal-PIP, replace, restructure-around. Reader is the CEO (commissioning), often with board chair / lead investor copied. Horizon to decision: 1–3 weeks once the audit lands. Reversibility is low-to-mid — terminating a senior hire is reputationally costly, organizationally disruptive, and once replaced the new CMO inherits 6–12 months of rebuild time. The cost of getting it wrong is asymmetric: firing a competent CMO with bad luck wastes 18 months of institutional knowledge; keeping an incompetent CMO with good luck masks a strategic gap until it's too late to recover.

**Optimal audit format.** Tight. **3–7 pages, executive-memo structure**: (1) headline verdict up front (continue / PIP / replace / restructure) with one-sentence justification; (2) 2–3 evidence pillars — pipeline-sourced trajectory, CAC payback delta vs hire date, executional vs strategic-attribution test; (3) named comparables — what would a competent peer-stage CMO have delivered in this window?; (4) off-ramps if verdict is "replace" — interim cover (fractional? VP elevation? founder-led?), transition window, knowledge-transfer scope. Closer to a **board-quality operator review** than an audit; the consumers are pattern-matchers, not pattern-builders. Format inheritance: PE portfolio quarterly governance memos (TPG, Vista, KKR), Bessemer/Sequoia/USV portfolio operator reviews, McKinsey CEO-advisory "people decisions" briefs, Roger Martin's stated test for personnel decisions in *Playing to Win* (separate operator effort from strategic context before judging output).

**Evidence type that dominates.** Performance-attribution sieve first — separate exogenous demand collapse, category headwind, and product-side issues from operator decisions the CMO actually owned. The named pattern from the fractional-CMO literature (Envizon, SaaSConsult): the **attribution test** is the load-bearing analytical move. If pipeline collapsed because the product market shifted, that's not the CMO; if pipeline collapsed because the CMO insisted on demand-gen-only when the segment needed product-led growth, that is. Second: comparison to peer-stage CMOs at named companies in the same vertical/stage. Third: team-quality assessment (did the CMO recruit and retain marketers who themselves performed?). Fourth: strategic-alignment with founder narrative (did the CMO push back on bad strategy, or rubber-stamp it?).

**Recommendation specificity.** Binary up front, with structured off-ramps. Not "Pat hasn't been hitting numbers" but: "**Recommendation: replace. Pat has owned the marketing function for 14 months; pipeline-sourced revenue grew 22% in a category that grew 65%, CAC payback expanded from 14 to 23 months, and the two strongest hires (Director of Demand-Gen, Head of Content) both left within 8 months citing strategic incoherence as the reason in exit interviews. The attribution test isolates 3 specific calls Pat owned (the pivot to outbound-only in Q2, the deferred rebrand, the pricing-page A/B test held at 50/50 for 11 months) where peer-stage CMOs at named comparables would have decided differently. Off-ramp: fractional CMO + elevate Maria for 90 days while we search; the demand-gen team can run on autopilot with the existing playbook for at least one quarter.**"

**Named exemplars.** PE-portfolio quarterly CMO reviews (TPG/Vista/KKR portfolio operations); Bessemer/USV portfolio operator-advisory memos; Mark Suster's published "should we replace the CMO" framework (Both Sides of the Table); Roger Martin's playing-to-win "are we doing the right things vs are we doing things right" attribution lens; First Round Review's "how to fire your CMO" and "how to interview a CMO" companion essays.

**Failure modes SPECIFIC to fire-CMO CI.**
1. **Attribution failure** — the audit assigns blame for outcomes the CMO didn't control (post-Series-A category collapse, product roadmap delays owned by Eng, sales-team turnover owned by VP Sales).
2. **Single-data-point execution** — one missed quarter framed as systemic failure without 2–3 confirming signals.
3. **Verdict-burying** — the binary recommendation appears on page 17 of a 30-page teardown; the board reads page 3, defers the decision.
4. **No off-ramp** — verdict is "replace" but no named interim coverage, no transition plan, no team-retention strategy; the founder defers indefinitely.
5. **Comfort-fitting** — audit confirms the founder's existing prior (already wanted to fire Pat) without engaging the strongest counter-argument; the firing happens, the next CMO has the same outcome, the founder learns nothing.
6. **Performance-vs-fit conflation** — the audit blends "Pat is missing numbers" (performance) with "Pat doesn't fit our culture" (fit); the verdict obscures which is load-bearing and how the next hire should differ.

### Decision 2 — Channel cut / continue (Cluster B)

**Decision shape.** Cut, double-down, pause-and-test, restructure. Reader is the head of marketing, head of growth, or founder-CMO with operational authority. Horizon: 2–6 weeks (the next quarterly budget cycle, sometimes sooner if cash is tight). Reversibility is high — channel decisions can be reversed quarter-over-quarter; the cost of getting it wrong is bounded by the time it takes to re-enter (3–6 months for paid; 6–12 months for SEO; near-zero for events).

**Optimal audit format.** Tight, **5–10 pages, channel-by-channel scorecard**. The dominant template-class: **paid-acquisition audit** (Bell Curve, Demand Curve, Tinuiti, Common Thread Collective); **content audit** (Animalz, Foundation Inc, Ross Simmonds Foundation Inc methodology); **SEO audit** (Ahrefs, Search Engine Journal templates). Skeleton: (1) per-channel scorecard with CAC, CAC payback, contribution to pipeline, contribution to revenue, trend over 4 quarters; (2) reallocation recommendation with named dollar shifts; (3) experiment ladder — the 2–3 tests to run in the next 60 days to validate the reallocation; (4) kill-or-keep thresholds — the trigger that ends the experiment cleanly.

**Evidence type that dominates.** Unit-economic first (CAC by channel, CAC payback, blended LTV:CAC, attribution-source quality), operational second (channel-team capacity, agency dependency, in-house skill gap), market third (channel saturation signal — Andrew Chen's Law of Shitty Clickthroughs: every channel eventually decays). The Bell Curve methodology: "audit foundations before scaling spend" — the typical channel-cut audit fails when it recommends cutting a channel that's underperforming because of a fixable foundation issue (broken tracking, bad landing page, wrong creative cycle) rather than because the channel doesn't work for the segment.

**Recommendation specificity.** Quantified by channel, by dollar, by time. Not "cut paid LinkedIn" but: "**Cut paid LinkedIn from $48k/quarter to $0; reallocate $32k/quarter to content (specifically: 2 commissioned customer-success deep dives per quarter, distributed via Ross Simmonds-style 8-channel repurposing) and $16k/quarter to a Capterra/G2 review-acquisition campaign. Expected CAC payback shift: blended 19mo → 14mo within 2 quarters, based on the historical CAC of $1,840 from organic-content-sourced trials vs $4,200 from LinkedIn-sourced trials. Kill-trigger for the reallocation: if Capterra/G2 review-sourced trials don't reach $X CAC by Q3 end, revert $16k to the next-tested channel (community / podcast sponsorship).**"

**Named exemplars.** Bell Curve agency paid-acquisition audits (named methodology: foundation-then-scale); Demand Curve Growth Guide channel-audit chapter; Tinuiti paid-media audits for DTC; Animalz editorial-first content audits; Ross Simmonds Foundation Inc 8-channel distribution audit; ProfitWell channel-attribution audits; Common Thread Collective profitability-by-channel matrix.

**Failure modes SPECIFIC to channel-cut CI.**
1. **Foundation-error misdiagnosis** — channel labeled underperforming because the landing page converts at 0.6% (a foundation problem); cutting the channel doesn't fix the underlying issue and the next channel performs identically badly.
2. **Last-touch attribution trap** — channel scored by last-touch when first-touch / multi-touch attribution would tell a different story (especially common for content and brand-search).
3. **Channel-saturation denial** — channel scored against last quarter when the marginal CAC is rising 15% quarter-over-quarter (Law of Shitty Clickthroughs in action).
4. **No experiment ladder** — recommendation is "shift $32k to content" with no testing plan; six months later, no one can tell if the reallocation worked.
5. **Mixing tactical with strategic** — channel audit folds in a pricing recommendation ("oh and also raise prices 15%"); the consumer can't tell which is load-bearing and the reallocation gets stalled in a pricing review.

### Decision 3 — Reposition / repackage (Cluster C)

**Decision shape.** Hold, sharpen, pivot category, reposition within category. Reader is the founder-CEO (commissioning) and the incoming fractional CMO or VP Marketing (executing). Horizon: 4–13 weeks of audit + planning, then 6–18 months of execution. Reversibility is low — repositioning rewrites the homepage, the sales deck, the pricing page, the SDR script, and (most painfully) the customer's mental model. The cost of getting it wrong is mid-to-high (6–12 months of execution time, plus customer confusion if the reposition lands and the company can't sustain the new claim).

**Optimal audit format.** Long-form. **15–25 pages**, anchored on April Dunford-style positioning teardown. Skeleton: (1) competitive-alternatives analysis (what would the customer do if we didn't exist?); (2) unique-attributes inventory (which features genuinely differ?); (3) value-mapping (which differences map to customer outcomes?); (4) target-market diagnostic (which sub-segment values this most?); (5) market-category placement (which category contextualizes the value best?); (6) PMF survey results (Sean Ellis test, with cohort breakdown); (7) ICP-resegmentation evidence (cohort analysis of best-fit customers); (8) messaging gap analysis (Wynter/Laja-style buyer-language vs marketing-language comparison); (9) the 30/60/90 plan that operationalizes the reposition. Format inheritance: **fractional-CMO Day-30 deliverable** (Envizon, SaaSConsult, ASP Marketing, Strategic Pete playbooks); **Dunford positioning teardown** (Obviously Awesome methodology); **MKT1 strategy memos** (Emily Kramer / Kathleen Estreich at MKT1 publish public-versions); **First Round Review GTM teardowns**.

**Evidence type that dominates.** Customer-research first (jobs-to-be-done interviews, win/loss analysis, churn-reason cohort analysis, Wynter-style messaging-resonance surveys), competitive-alternatives second (April Dunford's discipline: what would the customer use if we didn't exist? do-nothing is always an alternative), unit-economics third (retention cohort-by-segment, expansion-rate-by-segment to identify the segment worth repositioning around), strategic fourth (does the founder narrative survive the reposition, or is the reposition fundamentally a new company?).

**Recommendation specificity.** Strategic commitment, with phased rollout. Not "reposition as developer-tools" but: "**Reposition from 'all-in-one marketing analytics platform' to 'attribution intelligence for product-led B2B SaaS.' Evidence: the 23 customers in the $1M+ ARR cohort show 94% NPS and 14% net negative churn; the 117 customers below $200k ARR show 31% NPS and 18% churn (cohort analysis on slide 11). The top-cohort customers all describe the product in attribution language; the bottom cohort describes it as a 'cheaper Mixpanel.' The reposition matches the cohort that already loves the product. 30-day work: rewrite homepage + pricing-page + sales deck against the new positioning; pause all bottom-cohort marketing spend. 60-day work: ship two product-led-growth-attribution case studies; resegment SDR target list. 90-day work: re-baseline CAC payback by new ICP segment; commit to the new pricing model (per-seat with usage-tier) or revert. Off-ramp: if 90-day NPS on new-ICP-acquired cohort doesn't reach 60+, revert the homepage and re-evaluate.**"

**Named exemplars.** April Dunford's published positioning teardowns (Obviously Awesome); MKT1 strategy memos (Kramer/Estreich); Andy Raskin's strategic narrative work; Wynter messaging-resonance audits; Lenny Rachitsky's PMF re-test essays; the fractional-CMO 30/60/90 playbook from Envizon / SaaSConsult / Strategic Pete; First Round Review GTM teardowns (the "how X repositioned" essays).

**Failure modes SPECIFIC to reposition CI.**
1. **Founder-narrative collision** — reposition recommendation contradicts the founder's public narrative (last keynote, last fundraising deck, last podcast appearance); audit doesn't engage the cost of the public retraction.
2. **Customer-base loss undersizing** — reposition recommendation walks away from 60% of current revenue without naming the runway impact and the bridge plan.
3. **Insufficient research depth** — reposition based on 5 customer interviews when 25+ are needed to defend the cohort claim; the founder commits to the reposition, ships the homepage, then discovers the segmentation was noise.
4. **Wrong-axis pivot** — reposition recommends moving up-market when the actual constraint is wrong category (or vice versa); the audit hasn't separated "we're in the wrong category" from "we're in the right category but pricing for the wrong segment."
5. **Plan-without-permission** — 30/60/90 plan assumes resources (a new product-marketing hire, an additional $200k of content budget) the founder hasn't budgeted; the plan is unimplementable as written.

### Decision 4 — Category pivot (Cluster C)

**Decision shape.** Stay, broaden category, narrow category, create category, jump category. Reader is the founder-CEO and the board. Horizon: 8–26 weeks of audit + planning, 12–36 months of execution. Reversibility is the lowest of any marketing decision — category jumps consume 18–36 months and a category can't be un-claimed quickly. The cost of getting it wrong is asymmetric and severe (Drift's pivot from sales-engagement to conversational-marketing was a successful category jump; many companies have killed themselves by pivoting into a category their product couldn't support).

**Optimal audit format.** Long-form. **20–40 pages**, structured as **category-strategy memo + 90-day positioning sprint**. Skeleton: (1) current-category analysis (TAM, growth, competitive density, leader strength); (2) candidate-category enumeration (3–5 adjacent categories, each scored on capability transfer, market pull, competitive opening); (3) Christensen-style jobs-to-be-done analysis (what job is the product actually being hired to do?); (4) category-creation feasibility (does the company have the marketing budget and time to create a category, or only to enter one?); (5) financial scenarios (revenue impact under each candidate); (6) execution plan and off-ramps. Format inheritance: **Play Bigger category-design memo** (Christopher Lochhead methodology), **a16z "from zero to one" market-creation memos**, MBB market-entry studies adapted to category-jump.

**Evidence type that dominates.** Customer-research and market-size first (does the candidate category exist as a real buyer space, or only as an analyst chart?), capability-transfer second (does the product actually do the new category's job, or are we forcing the fit?), competitive-opening third (is there an incumbent, or is the category open?), financial fourth (does the pivot extend runway or shorten it?).

**Recommendation specificity.** Banded against scenarios, with structural off-ramps. Not "pivot to RevOps" but: "**Recommended: narrow category from 'marketing automation' to 'revenue operations alignment platform' over 18 months. Trigger to commit: ≥ 4 customer interviews (already pre-identified, list on slide 18) confirming the RevOps positioning resonates with their actual job. Trigger to abort: if month-9 pipeline from the new category positioning is < 30% of pre-pivot baseline, revert and re-evaluate. Capital commitment: $1.2M (rebranding, sales-deck rewrite, 2 RevOps-experienced hires). Off-ramp cost if aborted at month 9: $480k sunk, plus ~$200k of revenue lost from confused legacy buyers.**"

**Named exemplars.** Christopher Lochhead's *Play Bigger* category-design memos; Drift's published category-creation playbook (sales-engagement → conversational marketing); Gainsight's published category-creation playbook (customer success as a category); a16z's market-creation essays; MBB market-entry studies adapted to category-jump (which is functionally the same intellectual move as market-entry, with capability-transfer as the dominant question).

**Failure modes SPECIFIC to category-pivot CI.**
1. **Analyst-chart category** — the audit recommends pivoting into a category Gartner named in their latest hype cycle, but no buyer thinks they have a problem in that language.
2. **Capability over-transfer** — audit assumes our SaaS muscle transfers to a services-led market, our self-serve muscle transfers to enterprise, etc.
3. **No incumbent map** — audit doesn't name the incumbent, doesn't model their response, recommends entry into a category whose incumbent will counter-position us out within 12 months.
4. **Brand-equity destruction** — pivot recommendation walks away from the brand-equity asset (5 years of marketing-automation thought leadership) without naming the rebuild cost.
5. **Capital-blindness** — pivot recommendation assumes a $1.5M rebrand the company can't fund without raising; audit doesn't surface the fundraising dependency.

### Decision 5 — Day-30 fractional-CMO 30/60/90 action plan (Cluster C — the v0 spec's anchor case)

**Decision shape.** What does the fractional or interim CMO do in their first 90 days? This is the **canonical fractional-CMO deliverable** and the audit's most-cited use case. Reader is the founder-CEO (commissioned the engagement) and the fractional CMO (executing). Horizon: the audit IS the gate to a 90-day execution; once accepted, the fractional CMO begins executing on Day 1 of the next month.

**Optimal audit format and 30/60/90 canonical structure.** Long-form. **15–25 pages**, with the fractional-CMO 30/60/90 cadence as the structural spine. The canonical structure converges across published playbooks (Envizon, SaaSConsult, ASP Marketing, Strategic Pete, ThinkCap Advisors; also Demand Curve's fractional-CMO toolkit and MKT1's fractional-leader playbook):

**Days 1–30 — Foundation (the audit deliverable).** Listen + diagnose. Deliverables at end of Day 30:
- ICP doc with named segments (best-fit cohort surfaced from data, not from founder narrative)
- Marketing audit (the deliverable this lane produces) naming the binding constraint and locating the company on a stage map
- Tech-stack inventory (what tools, what data, what attribution architecture exists today)
- Team-quality assessment (which marketers are load-bearing, which are coverage, which are gap)
- 60- and 90-day plan with named owners and budgets
- Two or three "Day-1 quick wins" already shipped (homepage hero tweak, broken-tracking fix, one piece of customer-quoted content) — the fractional CMO's credibility deposit

**Days 31–60 — Build.** Execute the 1–2 foundational bets named in Day 30 plan. Typical bets:
- ICP-driven messaging refresh on the top 3 pages (homepage, pricing, primary product page)
- Foundation-fix on the top channel (broken tracking, broken attribution, broken funnel-stage tracking)
- One concentrated experiment on the binding constraint (e.g., onboarding-redesign A/B test if trial-to-paid is the constraint; comparison-page sprint if SEO is the underleveraged channel; pricing-page rewrite if pricing-clarity is the constraint)
- Hire-or-defer call on the one open marketing role
- First customer-acquisition channel attribution analysis (which channels actually source revenue vs which look busy)

**Days 61–90 — Scale.** Either double-down on what worked or kill-and-replace what didn't.
- Read out the Day 31–60 bets; commit to the channel/message/segment that won
- Lock the next-quarter budget against the now-validated thesis
- Decide the team build (one Director hire? two ICs? agency partnership?)
- Establish the cadence the next 90 days will run on (weekly standup, monthly retro, quarterly roadmap)
- Hand the founder a one-page "what we now know" that's the input to the next planning cycle

The 30/60/90 cadence is structurally rigid — it matches the way fractional CMOs are actually contracted (3-month minimum, often retainer-renewable thereafter), and it gives both the founder and the CMO a clean exit at Day 90 if the engagement isn't working. The audit's job is to make Day 30 a credible diagnostic, Day 60 a real bet, and Day 90 a clean read-out.

**Channel-priority sequencing in 30/60/90 plans.** The canonical sequencing from the fractional-CMO playbooks (Envizon, MKT1, Demand Curve):
1. **Foundation first** — landing pages, tracking, attribution architecture, baseline analytics. Without this, every later experiment is noise.
2. **One concentrated channel deepening** — pick the channel where the company has the strongest signal and deepen it. Lenny Rachitsky's customer-acquisition-lanes framework is the reference: most companies have one or two lanes that work, and the failure mode is diversifying before deepening.
3. **One experimental adjacent channel** — paired with the deepening, one budget-bounded experiment to test the next-most-promising channel.
4. **Defer diversification** until the deepened channel has been validated and the experimental channel has produced a read.

**Team-build sequencing in 30/60/90 plans.** The canonical sequencing (from the same playbooks):
1. **Day 30** — assess existing team, name load-bearing vs replaceable
2. **Day 60** — make ONE hire-or-defer decision (typically: the role that unblocks the binding constraint — e.g., Lifecycle Marketing if retention is the constraint, Demand-Gen if pipeline is the constraint, Product Marketing if positioning is the constraint)
3. **Day 90** — commit to the next-quarter team plan (typically: one director-level hire + 2 ICs, or one full-time CMO transition if the fractional engagement is ending)
4. **Defer** the marketing-ops, brand, and PR hires until at least Day 90 of the next quarter

**Named exemplars.** Envizon's "Fractional CMO Playbook: Your First 90 Days, Week by Week"; SaaSConsult's "Fractional CMO 30-60-90 Day Plan"; ASP Marketing's "Fractional CMO for SaaS: Cost, 90-Day Plan & Hiring Guide"; Strategic Pete's "How a Fractional CMO Builds Predictable SaaS Demand"; ThinkCap Advisors' "5 Signs Your SaaS Startup Needs a Fractional CMO Before Series A"; Demand Curve's fractional-CMO toolkit; MKT1's fractional-leader playbook (Kramer/Estreich); a16z's marketing-talent essays (specifically the "first marketing hire" canon).

**Failure modes SPECIFIC to 30/60/90 CI.**
1. **Wishlist 30/60/90** — plan reads as everything the founder ever wanted to do, with no sequencing rationale; the CMO can't execute because every recommendation is week-1.
2. **Day-30 over-promising** — fractional CMO commits to shipping a rebrand in 30 days; sets up the engagement for failure when Day-60 demo doesn't materialize.
3. **No off-ramp at Day 90** — plan assumes the engagement continues past Day 90; the founder can't cleanly exit if the fractional isn't working.
4. **Foundation-skipping** — plan jumps to channel experiments without naming the tracking/attribution/landing-page fixes that have to land first.
5. **Team-build before validation** — plan recommends 2 hires before the Day-60 bets have been read; the new hires inherit a thesis that hasn't been validated.

### Decision 6 — Quarterly strategic memo (Cluster B, edge of Cluster C)

**Decision shape.** Continue the strategy, sharpen the strategy, escalate to board, abandon. Reader is the founder-CEO (commissioned) and the board (informed). Horizon: 1–2 weeks once the memo lands. Reversibility is high (a quarterly memo is exactly that — a quarterly read-out, with another quarter coming).

**Optimal audit format.** Tight. **4–8 pages**, structured as **state-of-marketing-this-quarter memo**. Skeleton: (1) headline finding (the one thing the board needs to take away); (2) numbers vs plan (CAC, pipeline-sourced, CAC payback, net-new ARR, NRR; each vs last quarter and vs annual plan); (3) the one experiment that informed the quarter; (4) the next-quarter ask (budget, hires, board input); (5) risks and watch-items. Format inheritance: **Amazon six-pager** (narrative-not-deck format); **Klue executive briefing** (headline-as-claim, then evidence); **PE portfolio quarterly memos**; **the canonical board-update marketing-section pattern** (Y Combinator, First Round Review, Pear).

**Evidence type that dominates.** Trend-numerics first (CAC, payback, pipeline-sourced, contribution to ARR — each vs plan and vs trend), narrative second (the story that contextualizes the numerics — what changed, what we learned, what we're betting on), forward-look third (the one or two things that will determine next quarter).

**Recommendation specificity.** Memo-grade — not "fire someone" or "pivot the category," but: "**Continue the demand-gen-led strategy with one tightening: pause LinkedIn-paid pending the Q4 review (the CAC trend crossed our hurdle in October), reallocate to comparison-page SEO (the highest-confidence forward bet), and surface one ask to the board: $200k for a brand-narrative consulting engagement to test whether the positioning gap surfaced in the Wynter research closes with sharper messaging or requires a deeper reposition.**"

**Named exemplars.** Amazon six-pager structure; Klue executive-briefing format; the canonical board-memo marketing section (Y Combinator deck appendix; First Round Review board-prep canon); PE portfolio quarterly memos.

**Failure modes SPECIFIC to quarterly-memo CI.**
1. **Activity-recap** — memo reads as everything-we-did-last-quarter list, no narrative, no forward-look; board reads, asks "so what?", defers conclusion.
2. **No ask** — memo doesn't make an explicit board ask; the board can't help.
3. **Vanity-metric headline** — memo leads with impressions / followers / page views rather than pipeline / payback / NRR.
4. **No risk-naming** — memo's risk section is theatrical; the board can't tell which risks are real.
5. **Too-thin-for-decision** — memo recommends a $200k commitment without the evidence depth that justifies it; the board defers another quarter while the founder loses momentum.

---

## 3. Cross-decision synthesis: clustering + routing recommendation

### The 6-into-3 cluster collapse

The six decisions cluster as follows. The boundary is **decision reversibility × consumer authority horizon × evidence regime**, the same three-axis decomposition that drove the CI mapping — but the specific cluster shapes differ because marketing audits operate on a different reversibility surface.

**Cluster A — Personnel verdict (fire/hire CMO, restructure marketing function, replace agency).** Distinguishing properties: low-to-mid reversibility, 1–3 week consumer authority horizon, attribution-sieve evidence regime, board / CEO consumer. Format inheritance: PE portfolio operator review; McKinsey CEO-advisory personnel memo. Length: 3–7 pages. Analytical signature: separate operator effort from strategic context before judging output.

**Cluster B — Operational reallocation (channel-cut, quarterly memo, budget reallocation, agency-keep-or-cut).** Distinguishing properties: high reversibility, 2–6 week consumer authority horizon, unit-economic evidence regime, operational-marketing-leader consumer. Format inheritance: Bell Curve / Demand Curve / Animalz paid-acquisition or content audit; Klue executive briefing; Amazon six-pager. Length: 5–10 pages. Analytical signature: per-channel scorecard + reallocation recommendation + experiment ladder + kill-trigger.

**Cluster C — Strategic reset (reposition, category-pivot, fractional-CMO 30/60/90 action plan, ICP-resegmentation, pricing-model change).** Distinguishing properties: low reversibility, 4–13+ week consumer authority horizon, customer-research-and-competitive-alternatives evidence regime, founder + incoming-CMO consumers. Format inheritance: fractional-CMO Day-30 deliverable; April Dunford positioning teardown; MKT1 strategy memo; Play Bigger category-design memo. Length: 15–25 pages. Analytical signature: positioning teardown + PMF survey + ICP-resegmentation + 30/60/90 execution plan with named owners and off-ramps.

The clustering survives because, like CI, it's driven by structural decision properties (reversibility, horizon, evidence regime) rather than topical properties (channel-X-vs-channel-Y). Topics within a cluster are interchangeable from the consumer's perspective; topics across clusters demand fundamentally different artifacts.

### The most damaging cross-cluster failure mode: format-vs-decision-class mismatch

The single highest-leverage failure mode the mapping surfaces is **format-vs-decision-class mismatch**, and it goes in both directions:

- **Cluster A served by Cluster C format.** Board commissioning a fire-CMO decision gets a 25-page reposition-grade teardown. The binary verdict is buried, no off-ramp is named, the board defers the personnel call another quarter while the company burns runway. The audit was technically excellent and operationally useless.
- **Cluster C served by Cluster A format.** Founder commissioning a reposition gets a 5-page "here's the binding constraint" memo. No positioning teardown, no PMF survey, no ICP-resegmentation evidence. The founder commits to the reposition, ships the homepage in week 2, then discovers in week 8 that the segmentation was noise. The audit was punchy and strategically wrong.

The v0 spec at §1 ("30-minute Tuesday afternoon, Friday leadership meeting") implicitly assumes Cluster B — a channel-cut or quarterly-memo decision shape. Against Cluster A (fire-CMO), the v0 spec's MA-2 anchor ("commit to one specific 30-day experiment with owner + budget + success metric") is wrong: a personnel verdict isn't a 30-day experiment, it's a vote. Against Cluster C (reposition), the v0 spec's MA-2 anchor is also wrong: a reposition isn't one experiment, it's a 90-day rebuild. In both directions, the v0 spec's success criterion misaligns with the actual decision class.

This is the same load-bearing error CI v2 made — CI-1's "commit by next week" anchor systematically misjudged Evaluate-cluster (acquisition / market-entry) decisions. The marketing-audit analog is MA-2's "30-day experiment" anchor systematically misjudging Cluster A (personnel verdict, which doesn't have a 30-day experiment shape) and Cluster C (strategic reset, which has a 90-day execution shape rather than a 30-day experiment).

### Should the lane workflow route the audit format?

**Yes, at the workflow level.** The marketing_audit lane should accept a `decision_shape` workflow input (A — personnel; B — operational; C — strategic) that switches:
- **substrate template** — the prompt scaffolding that primes the model toward the cluster-appropriate artifact shape
- **structural_gate length-and-shape check** — Cluster A: 3–7 pages, binary verdict in first page, off-ramps named; Cluster B: 5–10 pages, channel-by-channel scorecard, experiment ladder; Cluster C: 15–25 pages, positioning teardown + ICP analysis + 30/60/90 plan
- **fixture set** — Cluster A fixtures: fire-CMO scenarios at portfolio companies; Cluster B fixtures: channel-cut decisions at founder-CMO firms; Cluster C fixtures: reposition / fractional-CMO Day-30 deliverables

Implementation cost: ~1–2 weeks of plan-time work (substrate templates + structural_gate variants + fixture re-bucketing + workflow input plumbing). Payoff: Goodhart-resistance against the workflow learning to produce a one-format-fits-all audit that succeeds against the judge's outcome criteria but fails the real reader's decision class.

### Should the judge differ per decision type?

**No.** MA-1 through MA-5 are outcome questions that survive cluster shift:

- **MA-1 (founder can name the binding constraint)** — works for all three. In Cluster A, the binding constraint is "is the CMO load-bearing for the underperformance?"; in Cluster B, it's "which channel is the leak?"; in Cluster C, it's "is the constraint upstream of marketing?". The criterion is invariant — the constraint name changes per cluster, but the discrimination is the same.
- **MA-2 (commit to one specific action)** — works for all three with a small anchor loosening. Cluster A action shape: a personnel vote (not a 30-day experiment). Cluster B: a 30-day experiment (the v0 anchor). Cluster C: a 90-day execution commitment. The criterion should test "commit to the decision-shape-appropriate next action" not "commit to a 30-day experiment."
- **MA-3 (revenue mechanism trace)** — works for all three. Revenue mechanism is invariant; the chain length differs.
- **MA-4 (stage-map location + refusal of wrong-stage best practices)** — works for all three, and arguably gets sharper. The audit must locate the company on the stage map AND match the audit's detail to the decision class. Mismatched detail (over-elaborated for a personnel call, under-elaborated for a reposition) should score 0 even if every other criterion scores 1.
- **MA-5 (surface upstream problem)** — works for all three. The upstream question is invariant.

The judge stays at 5 criteria. The cluster routing happens upstream.

---

## 4. Implications for the v0 marketing_audit spec

The v0 spec is well-structured but cluster-monoculture. It has three load-bearing gaps the decision-format mapping surfaces.

**Gap 1 — Reader spec is Cluster B by default.** §1 names the founder-CEO / fractional-CMO at pre-Series-B-to-Series-C with 30 minutes Tuesday afternoon and a Friday leadership meeting. That's a Cluster B reader (operational reallocation, quarterly memo). It is silent on Cluster A (board commissioning a personnel verdict) and Cluster C (founder commissioning a reposition or fractional-CMO Day-30 deliverable). The same audit lane will be commissioned to serve all three; the reader spec should name decision shape as a reader-orthogonal variable.

**Gap 2 — Success spec's "30-day experiment" anchor undershoots Cluster A and Cluster C.** §2 names "one concrete experiment they commit to in the next 30 days, with owner + budget + success metric" as the success criterion. That's a Cluster B success shape. A Cluster A audit succeeds when the board commits to a binary verdict (continue / replace) with a named off-ramp; a Cluster C audit succeeds when the founder commits to a 90-day execution plan with named foundational bets. The 30-day experiment frame is cluster-specific, not universal.

**Gap 3 — MA-4 stage-map criterion under-discriminates against format-vs-decision-class mismatch.** §4 MA-4 tests whether the audit locates the company on a stage map and refuses stage-inappropriate best practices. That's necessary but not sufficient. The audit also has to match its **detail level** to the decision class — a Cluster A audit can locate the company perfectly on the stage map and still fail by burying the verdict in 25 pages. MA-4 should tighten to also test whether the audit's detail matches the decision-class.

**The v0 spec's §3 mediocre-mode catalog is well-tuned for Cluster B but doesn't name the cross-cluster failures.** The "ten-page PDF of generic recommendations" failure is a Cluster B failure (the channel-audit-that-could-apply-to-anyone). The "wrong stage best practices" failure is also Cluster B. The Cluster A failure (verdict-burying) and Cluster C failure (insufficient research depth) aren't named.

---

## 5. Specific edits to v0 marketing_audit spec

Concrete, surgical, in order of priority:

1. **Add to §1 Reader, after substitute-readers list:** "Each reader commissions one of three decision shapes — Personnel (fire/hire CMO, restructure marketing function: low reversibility, board / CEO consumer, attribution-sieve evidence, 3–7 page memo), Operational (channel-cut, quarterly memo, budget reallocation: high reversibility, operational-marketing-leader consumer, unit-economic evidence, 5–10 page scorecard), or Strategic (reposition, category-pivot, fractional-CMO 30/60/90 plan: low reversibility, founder + incoming-CMO consumers, customer-research-and-competitive-alternatives evidence, 15–25 page diagnostic plus plan). The reader and decision shape are orthogonal variables; the same founder-CEO can be the consumer of any of the three at different moments."

2. **Edit §2 Success, replace "one concrete experiment they commit to in the next 30 days" with:** "Commit to the decision-shape-appropriate next action: a binary personnel verdict with named off-ramp for Personnel-shape decisions, a 30-day experiment with owner + budget + success metric for Operational-shape decisions, or a 90-day execution plan with named foundational bets and Day-30 / Day-60 / Day-90 milestones for Strategic-shape decisions."

3. **Edit §4 MA-2 score-1 anchor, replace "one recommendation specifies the action, the owner, the budget, the timeline, the success metric" with:** "the recommendation matches the decision class. For Operational-shape decisions: action + named owner + budget envelope + 30-day timeline + success metric tied to current baseline. For Personnel-shape decisions: binary verdict + 1–2 named off-ramps + interim-coverage plan + transition window. For Strategic-shape decisions: 30/60/90 plan with named foundational bets at each milestone + off-ramps."

4. **Tighten §4 MA-4 score-1 anchor:** add "the audit's detail level matches the decision class — 3–7 pages with binary verdict for Personnel-shape, 5–10 pages with channel-by-channel scorecard for Operational-shape, 15–25 pages with positioning teardown + ICP analysis + 30/60/90 plan for Strategic-shape. Mismatched-detail audits (over-elaborated for a personnel call, under-elaborated for a reposition) score 0 even if every other criterion scores 1."

5. **Add to §3 Failure / mediocre catalog:**
   - "Verdict-burying (Cluster A failure): the binary recommendation appears on page 17 of a 30-page teardown; the board reads page 3, defers the decision."
   - "Insufficient research depth (Cluster C failure): reposition recommendation based on 5 customer interviews when 25+ are needed to defend the cohort claim; the founder commits, ships the homepage, then discovers the segmentation was noise."

6. **Add to §8 Open questions:** "**5. decision_shape routing.** Implement `structural_gate` variants per decision cluster (Personnel / Operational / Strategic) and surface `decision_shape` as a workflow input. Estimated ~1–2 weeks plan-time. Validate that the 5-criterion judge rubric (with the anchor loosenings in edit 2–4 above) still discriminates correctly across all three clusters on existing and Cluster-A / Cluster-C fixtures."

7. **(Optional, deferred to v3.)** Consider a 6th criterion analogous to CI-6 (Evidence chain survives tracing) that targets the marketing-audit-specific AI-failure surface — **fabricated benchmark percentages** ("SaaS median trial-to-paid is 6%" cited without source; "industry CAC payback is 14 months" cited without sector / stage filter), **fabricated cohort statistics** ("our top-decile customers show 94% NPS" cited without verifiable cohort definition), and **stale-benchmark drift** (2021 SaaS benchmarks cited as current in 2026 marketing audits). Document with measured failure rates from 2025–2026 literature before committing. Per design guide §5 the ≤5 ceiling holds unless an AI-specific failure surface is documented; this candidate criterion would need its failure rate measured before it earns the breach.

---

## 6. Open questions

1. **Cluster-A fixture coverage is missing.** The current marketing_audit fixture set is Cluster B-heavy (founder/CMO at pre-Series-B). Build 2–3 Cluster A fixtures (fire-CMO scenarios at $5M–$30M ARR companies) and 2–3 Cluster C fixtures (reposition / Day-30 deliverable at pre-Series-B and Series-B companies) before locking the cluster-routing spec via empirical redundancy check.

2. **B2C vs B2B audit-shape divergence.** This research is anchored on B2B SaaS practitioners (Kalungi, Bell Curve, MKT1, Demand Curve). For DTC e-commerce or marketplace audits, the channel mix is different (paid social, influencer, retention LTV, SKU-level performance) and the format-shape mapping may need a fourth cluster (DTC operational, anchored on Common Thread Collective / Tinuiti / Buy Box methodology). Surface this when the first DTC fixture arrives.

3. **MA-4 cluster-detail-match risks feature-checking.** Tightening MA-4 to test "detail matches decision class" is one criterion-prose tweak away from "audit must be N pages." Watch this carefully on first 5 fixtures; if the judge starts scoring on page-count, revert and route detail-match purely through `structural_gate`.

4. **Personnel verdict ethics surface.** A judge that rewards Cluster A audits has to navigate the line between rigorous performance attribution and reputational damage to the individual being assessed. The Cluster A optimal-output spec should include a hedge: the audit assesses the role / outcome / attribution, not the person's character or capability in absolute terms. Surface to JR before locking Cluster A criteria.

5. **30/60/90 cadence rigidity vs founder reality.** The canonical fractional-CMO 30/60/90 cadence assumes the fractional CMO has 3 months of runway and the founder will respect the cadence. In practice, founders frequently break the cadence (push for results in week 2, shift the engagement to retainer at month 2, etc.). The Cluster C optimal-output spec should name this — the 30/60/90 plan needs explicit "founder-impatience" off-ramps for what-if-they-pull-the-plug-at-day-45.

6. **Quarterly memo (Decision 6) cluster placement.** I placed quarterly memo in Cluster B (operational reallocation) but it sits on the edge of Cluster C (strategic reset) when the memo recommends repositioning. The cluster routing may need a "Cluster B / B-prime" split if quarterly memos consistently land in the strategic-recommendation zone. Defer until 5+ quarterly-memo fixtures exist.

---

## 7. Sources cited

**Fractional-CMO 30/60/90 playbooks (the industry template — load-bearing for Cluster C and Decision 5):**
- Envizon. "Fractional CMO Playbook: Your First 90 Days, Week by Week." https://www.envizon.com/blog/the-fractional-cmo-playbook-what-to-expect-in-your-first-90-days
- SaaSConsult. "Fractional CMO 30-60-90 Day Plan." https://saasconsult.co/blog/fractional-cmo-30-60-90-day-plan/
- ASP Marketing. "Fractional CMO for SaaS: Cost, 90-Day Plan & Hiring Guide." https://asp-marketing.com/blog/fractional-cmo-for-saas
- Strategic Pete. "How a Fractional CMO Builds Predictable SaaS Demand." https://strategicpete.com/blog/fractional-cmo-builds-predictable-saas-demand/
- ThinkCap Advisors. "5 Signs Your SaaS Startup Needs a Fractional CMO Before Series A." https://www.thinkcapadvisors.com/post/fractional-cmo-before-series-a
- Demand Curve. Growth Guide and fractional-CMO toolkit. https://www.demandcurve.com/growth/intro
- MKT1 (Emily Kramer / Kathleen Estreich). Fractional-leader playbook. Published Substack and conference content.

**Cluster A (Personnel) reference set:**
- Mark Suster. "Both Sides of the Table" — published essays on how to evaluate and replace a CMO at venture-backed companies. https://bothsidesofthetable.com/
- First Round Review. "How to interview a CMO" and "Marketing leadership search" canon. https://review.firstround.com/
- Roger Martin. *Playing to Win* — strategic-attribution framework. Harvard Business Review Press.
- PE portfolio operations playbooks (TPG, Vista, KKR — private, but methodology cited via Bessemer / a16z portfolio CMO-fitness reviews).

**Cluster B (Operational) reference set:**
- Bell Curve agency methodology. https://www.bellcurve.com/
- Demand Curve. Growth Guide channel-audit chapter. https://www.demandcurve.com/growth/intro
- Tinuiti paid-media audits. https://tinuiti.com/
- Animalz editorial-first content audits. https://www.animalz.co/blog/content-marketing-strategy
- Foundation Inc / Ross Simmonds. "Create once, distribute forever" content audit philosophy. https://foundationinc.co/
- Common Thread Collective. Profitability-by-channel matrix for DTC. https://commonthreadco.com/
- ProfitWell pricing and channel attribution audits. https://www.profitwell.com/
- Tomasz Tunguz. CAC payback discipline. https://tomtunguz.com/saas-startup-benchmarks/
- Bessemer State of the Cloud. https://www.bvp.com/atlas/state-of-the-cloud
- OpenView SaaS Pricing Insights. https://openviewpartners.com/blog/saas-pricing-insights/
- Kalungi 95-point B2B SaaS marketing audit. https://www.kalungi.com/audit
- TripleDart B2B marketing audit guide. https://www.tripledart.com/b2b-marketing/audit
- ByDefaultCMO B2B marketing audit system. https://www.bydefaultcmo.com/marketing-audit-system

**Cluster C (Strategic) reference set:**
- April Dunford. *Obviously Awesome* and *Sales Pitch* — positioning framework starting from competitive alternatives. https://www.aprildunford.com/
- Andy Raskin. Strategic-narrative essays. https://medium.com/@andyraskin
- Wynter (Peep Laja). Messaging-resonance audits. https://wynter.com/solutions/messaging-resonance-audit
- CXL ResearchXL framework. https://cxl.com/conversion-rate-optimization/how-to-create-a-cro-process-by-peep-laja/
- Sean Ellis. *Hacking Growth* + PMF survey + ICE framework. https://www.lennysnewsletter.com/p/the-original-growth-hacker-sean-ellis
- Brian Balfour / Reforge. Four Fits framework. https://brianbalfour.com/four-fits-growth-framework
- Lenny Rachitsky + Dan Hockenmaier. "Drive Growth by Picking the Right Lane." https://review.firstround.com/drive-growth-by-picking-the-right-lane-a-customer-acquisition-playbook-for-consumer-startups/
- Christopher Lochhead. *Play Bigger* — category-design framework.
- Drift's published category-creation playbook (sales-engagement → conversational marketing).
- Gainsight's published category-creation playbook (customer success as a category).
- MKT1 strategy memos (Kramer/Estreich). https://www.mkt1.co/

**Anti-pattern literature (named failure modes):**
- McKee Creative. "What a marketing audit actually reveals (and why most small businesses skip it)." https://mckeecreative.store/what-a-marketing-audit-actually-reveals-and-why-most-small-businesses-skip-it/
- Helen Cox Marketing. "Why a marketing audit is the strategic reset you need." https://helencoxmarketing.co.uk/is-your-marketing-just-noise-why-a-marketing-audit-is-the-strategic-reset-you-need/
- Umbrex. "Common Marketing Failure Modes." https://umbrex.com/resources/what-marketing-is/common-failure-modes-in-marketing/
- Marketoonist (Tom Fishburne). "Marketing vanity metrics." https://marketoonist.com/2016/02/marketing-vanity-metrics.html
- Eric Ries. *The Lean Startup* — vanity vs. actionable metrics distinction.

---

## 4-line summary

- Word count: ~3,900.
- Recommendation on decision-routing: **cluster** at the workflow level into three clusters — Personnel (fire-CMO, restructure) / Operational (channel-cut, quarterly memo) / Strategic (reposition, category-pivot, fractional-CMO 30/60/90) — not six bespoke formats and not one universal Day-30 audit.
- Top failure mode the mapping surfaces: **format-vs-decision-class mismatch** — Cluster-A decision served by Cluster-C-grade teardown (verdict buried in 25 pages, board defers) or Cluster-C decision served by Cluster-A-grade memo (reposition committed on 5-page thin diagnostic, segmentation turns out to be noise). The v0 spec implicitly assumes Cluster B and misjudges the other two clusters' success conditions.
- One specific edit recommended: **loosen MA-2's "30-day experiment" anchor** to "commit to the decision-shape-appropriate next action" (binary verdict for Personnel, 30-day experiment for Operational, 90-day execution plan with foundational bets for Strategic), and add `decision_shape` as workflow input — edit 2 + 3 are the load-bearing pair. The cross-vertical anchor for "right level of detail" is **decision reversibility × consumer authority horizon**, the same axis that drove the CI mapping.
