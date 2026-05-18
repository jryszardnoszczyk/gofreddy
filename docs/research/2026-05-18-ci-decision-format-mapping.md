---
date: 2026-05-18
type: research deliverable
status: complete
topic: CI decision-to-format mapping (acquisition / retention / pricing / roadmap / market-entry / partner)
parent: docs/handoffs/2026-05-17-judge-design-step1-competitive.md
sibling: docs/research/2026-05-15-judges-domain-competitive.md
---

# CI Decision-to-Format Mapping

## 1. TL;DR (recommendation)

The CI v2 spec's implicit "one universal brief format" assumption is **partially right and dangerously partially wrong**. Six competitive decisions split cleanly into **three formal clusters**, not six bespoke formats and not one universal — and the cluster boundary is set by **decision irreversibility × time-to-act**, not by topic.

**Cluster A — Long-form Evaluate** (acquisition target, market entry / segment expansion): irreversible high-capital commitments with 4–13 week horizons. Optimal format is **20–60 page narrative-plus-data dossier** modelled on IB pitch books, McKinsey market-entry studies, and CB Insights teardowns. Financial-and-strategic evidence dominate; recommendation is **contingent and price/option banded** ("acquire if EBITDA-multiple ≤ 8.5x and integration confidence ≥ X").

**Cluster B — Tight-form React** (retention threat, pricing response, product roadmap pivot): time-pressured reactions with 1–4 week horizons where the cost of getting it wrong is bounded and reversible-ish. Optimal format is a **1–2 page Amazon-six-pager-style decision memo** (Klue executive briefing for retention/pricing; product strategy memo for roadmap). Operational + unit-economic + capability evidence; **quantified action with explicit trade-off** is the recommendation shape.

**Cluster C — Structural Choose** (partner / channel selection vs competitor): boundary-defining decisions where the cost is mostly opportunity cost and the trade-off is between mutually exclusive structural positions. Optimal format is a **1–2 page relationship-matrix brief** with co-opetition assessment + channel-conflict map; recommendation is **a structural commitment to a quadrant**, not a quantified delta.

**Routing recommendation: Yes, route — at the workflow level, not the judge level.** The CI lane should detect or be told which cluster the brief is being commissioned for and switch its **substrate / fixture / structural_gate** accordingly. The **judge stays format-agnostic** because CI-1 through CI-5 are outcome questions, not format checks. The CI v2 criteria already survive cluster shift because they ask whether the reader can commit, not whether the brief is short.

**Most damaging failure mode the mapping surfaces:** **abstraction-mismatch** between the brief format and the decision irreversibility. A 60-page acquisition dossier delivered against a retention threat decays into ignored deck; a 1-page executive briefing delivered against a $500M acquisition decision masks integration risk and gets the deal done at the wrong price. The CI v2 spec at §3c explicitly waves this away ("CI-1 disqualifies abstraction-mismatch automatically") — that's wrong. CI-1 catches abstraction *level* (strategic vs tactical), not abstraction *depth* (one-page reaction vs dossier). Add a workflow-level decision-shape input; do not add a sixth meta-criterion to the rubric.

**Specific edit to CI v2:** add `decision_shape` as a workflow input variable (Cluster A / B / C), route to corresponding `structural_gate` and `substrate`, and add to CI-1 score-1 anchor that the action's *time-to-commit* and *reversibility* match the decision shape — not as a separate criterion, as a tightening of CI-1's existing "commit by next week" anchor.

---

## 2. Per-decision deep dive

### Decision 1 — Acquisition target evaluation (Cluster A)

**Decision shape.** Yes / no / wait + price band + integration risk tier. Reader is Corp Dev lead, CFO, or CEO with board oversight. Horizon to commitment: 4–12 weeks (LOI through close), but the brief itself is often a 2–4 week artifact that triggers go/no-go on a non-binding offer. Irreversibility is high (capital committed, organizational disruption) and downside is asymmetric (overpaying compounds for years; integration failure destroys both companies' multiples).

**Optimal brief format.** Long-form. Investment-bank pitch books for M&A run **20–60 pages**, with eight canonical sections: situation overview, bank credentials (irrelevant for in-house), market analysis, company analysis, valuation, strategic recommendations, transaction comparables, and next steps ([Mergers & Inquisitions IB Pitch Books](https://mergersandinquisitions.com/investment-banking-pitch-books/)). Buy-side decks are **shorter than sell-side** but carry **longer profile lists** of candidates and tighter financials. The valuation section alone can be 1–2 slides in a short brief or 20+ slides in a long one. McKinsey corp-dev M&A blueprints emphasize that the business case must "explain how the acquiring company plans to add value to the target" — i.e., synergy thesis must be quantified and tested against industry benchmarks ([McKinsey: A blueprint for M&A success](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/a-blueprint-for-m-and-a-success)).

**Evidence type that dominates.** Financial first (DCF, comparable transactions, precedent multiples, synergy modeling), strategic second (market position, competitive moat, capability complementarity), operational/cultural third (integration risk, clean-team customer-overlap analysis, talent retention). **The dominant failure mode** is overweighting financials and underweighting cultural-integration risk: McKinsey survey finds nearly 50% of execs say cultural issues are the biggest reason deals fail post-close ([McKinsey M&A]; corroborated by [Wharton Knowledge: Why M&A Deals Fail](https://knowledge.wharton.upenn.edu/article/why-many-ma-deals-fail-and-how-to-beat-the-odds/)).

**Recommendation specificity.** Contingent and banded. Not "acquire" but "**recommend non-binding offer at $X–Y EV / 7–8.5x EBITDA, conditional on (a) clean-team validating ≥ $Z synergy, (b) tech-DD confirming no platform re-write, (c) retention package for top 12 engineers**." The reader must be able to walk into a board meeting with both the recommendation and the **explicit conditions under which the recommendation flips**.

**Named exemplars.** IB pitch books (Goldman, Morgan Stanley sell-side decks); CB Insights strategy teardowns ([CB Insights Google Teardown](https://www.cbinsights.com/research/report/google-strategy-teardown/)); McKinsey/Bain merger-integration blueprints; in-house corp-dev IC memos at the FAANGs (typically 30–60 pages including appendix).

**Failure modes SPECIFIC to acquisition CI.** (1) **Synergy overconfidence** — 35% of mid-market acquirers fall short of synergy expectations ([BDO CFO Outlook via Ansarada](https://www.ansarada.com/article/5-risks-of-a-failed-integration)). (2) **Cultural-integration blind spot** — surfaces post-close as productivity drop and top-talent flight. (3) **Integration-cost underestimate** — IT systems combination "easily cost tens of millions" that erode the financial case. (4) **Clean-team-absent customer-overlap surprise** — only post-close discovery that 30% of revenue overlap means cross-sell math collapses.

### Decision 2 — Retention threat response (Cluster B)

**Decision shape.** Posture (defend with discount / defend with feature / let go / co-develop) + budget + timeline. Reader is VP Customer Success, GM of a business unit, or in larger orgs the named account exec's manager. Horizon to commitment: 1–7 days. Reversibility is mid-to-high — a discount given can't easily be retracted but the account can be re-engaged.

**Optimal brief format.** Tight. **1–2 pages, structured as a Klue executive briefing** — Headline-as-claim → Rationale → Comparison → Implications → Recommendations ([Klue exec briefing template; Klue 7 mistakes](https://klue.com/blog/competitive-intelligence-framework-problems)). Account-level retention briefs at Salesforce and HubSpot are operationalized as **battlecards** (one-page competitor reference docs embedded in the CRM at the account or opportunity level) — see [Highspot battlecard guide](https://www.highspot.com/blog/sales-battlecards/) and [HubSpot 30-Minute Battlecard Builder](https://offers.hubspot.com/science-of-scaling-battlecard-builder). Crayon's State of Competitive Intelligence: 68% of B2B SaaS revenue comes from competitive deals; teams with active competitive enablement see 71% win rates; **programs refreshing battlecards monthly report a 59% lift over quarterly refreshers** — frequency matters more than length.

**Evidence type that dominates.** Operational (account health, usage trend, named contact's posture), competitive (the specific feature the prospect is evaluating, the competitor's known pricing on this segment), unit-economic (account LTV, defendable margin headroom). Discount-based retention is "a slow poison" per Sales Assembly and the Customer Success Collective — defenses should target value, not price ([Sales Assembly](https://www.salesassembly.com/blog/revenue-leadership/how-to-handle-competitive-deals/), [CS Collective](https://www.customersuccesscollective.com/customer-retention-playbook-that-reduces-churn/)).

**Recommendation specificity.** Quantified action with explicit trade-off. Not "defend the account" but "**execute defense play 3 (12-month renewal at flat pricing, accelerated Q3 roadmap commit on integration X); cost: $48K margin headroom + 1 sprint engineering capacity from the API team. Drop if executive sponsor leaves before Sept 30.**"

**Named exemplars.** Klue's executive briefing template ([Klue blog](https://klue.com/blog/competitive-intelligence-reporting)); HubSpot Battlecard Builder; Crayon battlecards; CS-team-owned save plays embedded in Salesforce Account 360. Box's retention playbook ([CS Collective](https://www.customersuccesscollective.com/customer-retention-playbook-that-reduces-churn/)) is the named in-house exemplar.

**Failure modes SPECIFIC to retention CI.** (1) **Discount reflex** — competitor brief recommends matching competitor price; produces revenue compression without addressing why the customer is shopping. (2) **Single-account zoom that ignores cohort signal** — brief on one at-risk account misses that 12 others in the same segment will signal next quarter. (3) **Stale battlecard** — the brief restates the May data sheet, missing that the competitor shipped two relevant features in June.

### Decision 3 — Pricing response (Cluster B)

**Decision shape.** Match / hold / counter + which tiers + timing. Reader is Head of Product Marketing, RevOps lead, or in early-stage founder-CEO. Horizon: 2–6 weeks (longer than retention because pricing changes have systemic effects). Reversibility is mid (can re-price again, but customer perception lags).

**Optimal brief format.** Tight, **data-heavy 1–2 pages plus appendix**. ProfitWell-style pricing briefs and OpenView pricing teardowns share the same skeleton: pricing-model description → unit-economic impact → segment exposure → recommendation. **Elite SaaS companies have abandoned annual pricing reviews in favor of 90-day pricing sprints** ([OpenView SaaS Pricing Insights](https://openviewpartners.com/blog/saas-pricing-insights/), [SaaS Factor 2025 Pricing Playbook](https://www.saasfactor.co/blogs/the-2025-saas-pricing-playbook-how-to-choose-the-right-model)) — which means the brief format is optimized for fast iteration, not exhaustiveness.

**Evidence type that dominates.** Unit-economic. Customer-segment elasticity (which varies 2–4x across B2B SaaS segments per [Monetizely](https://www.getmonetizely.com/articles/how-to-measure-price-elasticity-in-b2b-saas-markets)), CAC/LTV impact, cross-price elasticity between own tiers (positive cross-price = cannibalization risk; [42Signals](https://www.42signals.com/blog/product-cannibalization/)), churn elasticity at proposed price points. Patrick Campbell's signature finding: **discount magnitude correlates with churn rate** — a hidden cost in discount-based responses ([Acquired FM podcast with Campbell](https://www.acquired.fm/episodes/pricing-everything-you-always-wanted-to-know-but-were-afraid-to-ask-with-profitwell-ceo-patrick-campbell)).

**Recommendation specificity.** Quantified, segment-targeted, time-bound. Not "hold price" but "**hold list pricing on Enterprise and Mid tiers; introduce a $39/mo Solo tier in Q3 to recapture the segment Acme just opened. Expected ARR impact: +$1.2M net of estimated -$280K Pro-tier cannibalization. Trigger to revisit: ≥ 15% Acme Solo customer acquisition rate vs. our Solo by month 3.**"

**Named exemplars.** ProfitWell's pricing intelligence briefs; OpenView pricing benchmark reports and pricing-strategy memos ([State of SaaS Pricing 2023](https://openviewpartners.com/blog/state-of-saas-pricing-2023/)); SaaS Factor 2025 Playbook templates; in-house RevOps memos at Atlassian, HubSpot, Stripe.

**Failure modes SPECIFIC to pricing CI.** (1) **Elasticity over-confidence** — using aggregate elasticity to recommend uniform action when segment elasticities differ 2–4x. (2) **Cannibalization blind spot** — recommending new tier without modeling downshift. (3) **Match-the-competitor reflex** — using competitor pricing as a target rather than as a data point. OpenView's framing: "competitor pricing is a data point, not a strategy — use competitor pricing for positioning but derive your actual price from customer willingness-to-pay research." (4) **Annual-review cadence in a 90-day market** — the brief recommends an annual pricing review when elite SaaS companies are on 90-day sprints.

### Decision 4 — Product roadmap pivot (Cluster B)

**Decision shape.** Fast-follow / differentiate / ignore + scope + sprint allocation. Reader is Head of Product, Eng lead, or founder. Horizon: 2–8 weeks (next 1–2 quarterly planning cycles). Reversibility is mid (roadmap can be re-planned, but shipped features can't be un-shipped cheaply).

**Optimal brief format.** Tight. **1-page comparison + recommendation memo, with a one-table feature-capability map**. The template-class is "**product strategy memo**" or Pragmatic Marketing competitive-analysis worksheet ([Pragmatic Marketing](https://mediafiles.pragmaticmarketing.com/Framework-Files/Competitive-Analysis-Worksheet_1307.docx)). Reforge's Insight Analytics Competitor Analysis frames this as **"table-stakes features required to compete vs. differentiating capabilities that win deals"** — and the brief's job is to classify the competitor's new feature into one of those two buckets ([Reforge: Launching Competitor Analysis](https://www.reforge.com/blog/launching-competitor-analysis)).

**Evidence type that dominates.** Capability comparison (feature matrix), technical-debt assessment (cost to ship our own version), market-pull signal (are customers asking?), positioning impact (does this re-define the category?). The classic Christensen reframe: **does this feature change the customer job-to-be-done, or just the feature surface?** If the former, ignoring is dangerous; if the latter, fast-follow may be table-stakes-and-done.

**Recommendation specificity.** Sprint-level, named-team. Not "fast-follow on the Acme integration" but "**Differentiate. Ship deeper integration on the same surface (bi-directional sync) in 6 weeks, owned by Platform team. Don't replicate Acme's marketplace tab; instead, ship Trigger Library in Q4 (5 sprints) targeting the same buyer-pain. Cost: defer the BillingV2 dashboard refactor to Q1.**"

**Named exemplars.** In-house product-strategy memos (Atlassian's "PSV — Project Strategy V—" template; Spotify's bet board memos); Pragmatic Marketing competitive worksheets; Reforge Competitor Analysis output; Productboard's competitor-feedback prioritization briefs ([Productboard](https://www.productboard.com/glossary/competitor-analysis/)).

**Failure modes SPECIFIC to roadmap CI.** (1) **Fast-follow reflex** — brief recommends shipping competitor's feature without testing whether it represents table-stakes (catch up) or differentiation (compete on their terms). (2) **Underestimating internal cost** — recommends fast-follow without surfacing the deferred initiative. (3) **Mistaking demos for adoption** — competitor's feature is loud at trade shows but unused by their customers; the brief recommends responding to noise. (4) **Capability-blind ignore** — recommends ignoring when the feature is actually category-redefining (the Christensen failure mode).

### Decision 5 — Market entry / segment expansion (Cluster A)

**Decision shape.** Enter / partner-to-enter / acquire-to-enter / skip + investment band + commitment depth. Reader is CEO, Head of Strategy, or board. Horizon: 8–26 weeks to commitment, 6–24 month execution. Irreversibility is the highest of any decision on this list (capital + organizational capacity + opportunity cost of not entering elsewhere).

**Optimal brief format.** Long-form. MBB market-entry studies follow a **standard four-section structure**: market attractiveness → competitive landscape → company capabilities/entry options → financial analysis, ending with explicit recommendation + entry sequence ([Slideworks: Market Entry Report Structure](https://slideworks.io/resources/how-to-write-a-market-entry-report-the-structure-mckinsey-bcg-and-bain-use)). Engagements run **roughly 90 days (13 weeks)** with 0–15 day problem definition, 16–45 day validation including expert calls and channel tests, and 46–90 day messaging lock and rollout prep. Reports are typically **30–80 slides** (Bessemer State of the Cloud reports are 80+ slides as a reference for adjacency-rich market analysis; [BVP State of Cloud 2024](https://www.bvp.com/atlas/state-of-the-cloud-2024)).

**Evidence type that dominates.** Market-sizing first (TAM/SAM/SOM with bottom-up and top-down triangulation), competitor-strength second (incumbent position, capability moat, customer captivity), entry-barrier third (capital requirements, regulatory, distribution, IP, customer loyalty), capability-fit fourth (internal strengths transfer? what's the missing capability?), financial fifth (break-even, payback period, IRR vs corporate hurdle rate).

**Recommendation specificity.** Decision banded against scenarios. Not "enter EU mid-enterprise" but "**Recommended: Enter via reseller partnership in Q3 ($2–3M annual commitment), with re-evaluation gate at month 9 against the trigger: ≥ 8 referenced customers AND ≥ 25% gross margin retained. If trigger met, transition to direct-sales build in year 2 ($8–12M). If not met, exit; sunk cost capped at $3.2M.**" The recommendation names the **sequence**, the **trigger**, the **off-ramp**.

**Named exemplars.** McKinsey/BCG/Bain market-entry studies; BCG Advantage Matrix industry-classification reports; Bessemer State of the Cloud sector deep-dives; CB Insights industry teardowns; Bain's "go-to-market diagnostic" reports.

**Failure modes SPECIFIC to market-entry CI.** (1) **TAM inflation** — top-down sizing without bottom-up reality check, producing a defensible-on-paper market that doesn't exist at the unit level. (2) **Incumbent-strength denial** — entry recommendation that assumes the incumbent won't respond, missing the Helmer counter-positioning trap. (3) **Capability transfer over-assumption** — brief assumes our SaaS muscle transfers to a services-led market. (4) **No off-ramp** — recommendation has no kill-trigger, so the company stays in a losing market because it's committed.

### Decision 6 — Partner / channel selection vs competitor (Cluster C)

**Decision shape.** Partner / compete / both / neither + structural depth (referral, integration, deep-co-sell, white-label). Reader is Head of BD, VP Partnerships, or founder. Horizon: 2–8 weeks. Reversibility is mixed — partnerships can be exited but reputational signaling persists.

**Optimal brief format.** Tight, **1–2 page relationship-matrix brief**. The dominant analytical lens is **co-opetition** ([PARQOR Co-opetition Framework](https://parqor.com/co-opetition-framework/), [Umbrex Game Theory & Co-opetition](https://umbrex.com/resources/frameworks/strategy-frameworks/game-theory-co-opetition-framework/)) — when do platforms and complementors have more incentive to cooperate, and when to compete? The brief should specify "decision rights, IP ownership, data-sharing, exit provisions, dispute resolution, and measurement." The companion lens is **channel conflict** ([Umbrex Channel Conflict Framework](https://umbrex.com/resources/frameworks/marketing-frameworks/channel-conflict-management-framework/), [Magentrix](https://www.magentrix.com/blog/channel-conflict-what-it-is-how-to-prevent-and-resolve-it)) — horizontal (partner-vs-partner) and vertical (vendor-vs-partner) conflict mapping.

**Evidence type that dominates.** Partnership economics (revenue share, take rate, attributable lift), channel-conflict assessment (does our direct GTM compete with this partner's channel?), strategic-positioning (does this partnership cement or weaken our differentiation?), exit-cost (what's the switching cost if the partnership fails?). The classic build-buy-partner test: **"a collaborator accelerates speed to market, unlocks distribution, or provides specialized capability that would be slow or costly to replicate"** ([TheCodev Build-Buy-Partner](https://thecodev.co.uk/build-vs-buy-framework/), [Sedulo Build-Buy-Partner](https://sedulogroup.com/build-buy-partner-framework/)).

**Recommendation specificity.** A structural commitment to a quadrant. Not "partner with AWS" but "**Partner with AWS Marketplace at Channel Partner level (not ISV-direct). Accept the 3% AWS take + co-sell motion. Conflict with our direct EMEA sales team is bounded — exclude AWS Marketplace from the EMEA enterprise compensation plan via swim-lane rule. Re-evaluate in 12 months against the trigger: ≥ 20% of pipeline sourced via AWS by Q4. Decline simultaneous Stripe Connect — overlapping merchant-acquiring channel-conflict is structural, not bounded.**"

**Named exemplars.** In-house BD memos at Twilio, Stripe, Snowflake (these companies publish little externally but the format is standardized internally); McKinsey ecosystem-strategy briefs; BCG channel-strategy diagnostics; AWS Partner Network case studies of channel decisions ([AWS Marketplace Channel Programs 2026](https://aws.amazon.com/blogs/apn/updates-to-aws-channel-programs-to-drive-growth-in-2026/)).

**Failure modes SPECIFIC to partner CI.** (1) **Channel-conflict denial** — recommends partnership without naming the segments where partner overlaps direct sales. (2) **Take-rate-myopia** — focuses on revenue share, misses strategic-positioning cost (e.g., becoming dependent on a partner that will eventually compete). (3) **No exit clause** — partnership recommendation with no specification of off-ramp triggers. (4) **Vertical-conflict undersizing** — discounts the most damaging form of channel conflict (vendor competing with own partner) because it's politically uncomfortable.

---

## 3. Cross-decision synthesis: clustering + routing recommendation

### The 6-into-3 cluster collapse holds

The clustering hypothesis in the prompt — Evaluate / React / Structure — survives the per-decision analysis with two refinements:

**Cluster A — Evaluate (acquisition, market entry).** Distinguishing properties: irreversible high-capital, 4–13 week commitment horizon, contingent-banded recommendation, financial+strategic evidence, 20–60+ page narrative-plus-data format. The format inheritance is consulting-firm + investment-bank tradition; the analytical signature is **scenario sensitivity** (what happens if synergy is 60% of claimed?) and **kill-trigger specification**.

**Cluster B — React (retention, pricing, roadmap).** Distinguishing properties: time-pressured (1–4 week), reversible-ish, quantified-action recommendation, operational+unit-economic+capability evidence, 1–2 page Amazon-six-pager-style memo. The format inheritance is Klue executive briefing + Amazon 6-pager + product strategy memo. Analytical signature is **option specification** (which of 3–4 named actions, with cost) and **trigger-to-revisit** clauses.

**Cluster C — Structure (partner/channel).** Distinguishing properties: opportunity-cost dominant, structural commitment, 1–2 page relationship-matrix format. The format inheritance is co-opetition + channel-conflict + build-buy-partner frameworks. Analytical signature is **quadrant commitment** and **swim-lane specification**.

The clustering survives because it's driven by **decision irreversibility × time-to-act × evidence-type dependency** — three structural properties of the decision, not topical properties of the competitor.

### Should the CI lane workflow route the brief format?

**Yes, at the workflow level.** The CI lane should accept a `decision_shape` input (A / B / C, or six fine-grained types collapsed to three at the structural_gate level), and route to a corresponding **substrate template**, **structural_gate length-and-shape check**, and **fixture set**. Implementation cost: ~1–2 weeks of plan-time work (substrate templates + structural_gate variants + fixture re-bucketing + workflow input plumbing). Payoff: Goodhart-resistance against the workflow learning to produce a one-format-fits-all brief that succeeds against the judge's outcome criteria but fails the real reader's decision shape.

**Critical:** routing happens **outside the judge**. The judge stays format-agnostic because CI-1 through CI-5 are outcome questions ("would the reader commit?", "does the brief surface a structural mechanism?") that survive cluster shift. **Forcing the judge to know the cluster would re-introduce exactly the feature-checking pathology that `c76f051` rolled back.**

### Should the judge differ per decision type?

**No.** The CI v2 rubric's five outcome questions hold across all three clusters:

- **CI-1 (concrete action commitment)** — works for all three. The action shape changes (Cluster A = contingent banded, Cluster B = quantified action, Cluster C = structural commitment), but the question "could the reader commit by next week?" still discriminates.
- **CI-2 (trajectory over snapshot)** — works for all three. Cluster A trajectory is 12–24 months (acquisition target's strategic direction; market's growth curve); Cluster B is 3–9 months; Cluster C is 12–24 months again. The 2+ independent signals requirement is invariant.
- **CI-3 (structural mechanism of advantage)** — works for all three. The mechanism question is structural, not format-bound.
- **CI-4 (uncomfortable truth)** — works for all three. Different priors get challenged (Cluster A: synergy optimism; Cluster B: discount reflex; Cluster C: partner-asymmetry denial), but the criterion is invariant.
- **CI-5 (trade-off in the recommendation)** — works for all three. The cost shape differs (Cluster A: capital/option cost; Cluster B: budget/initiative cost; Cluster C: opportunity/structural-position cost), but the explicit-sacrifice requirement is invariant.

The judge stays at 5 criteria. The cluster routing happens upstream.

---

## 4. Implications for CI v2 spec

The CI v2 spec is closer to correct than wrong, but it has three load-bearing gaps the decision-format mapping surfaces.

**Gap 1 — Reader spec doesn't name the decision shape.** §1 lists three reading modes (reactive / proactive / on-demand) and four substitute readers (Head of Product, Corp Dev, senior partner, clinic ops lead). It is silent on which **decision shape** the reader is committing to. The decision shape is what determines the optimal brief format, not the reader's role or the reading mode. A founder-CEO evaluating an acquisition (Cluster A) wants a 30-page dossier; the same founder-CEO responding to a retention threat (Cluster B) wants a 1-page memo. **The Reader spec should name decision shape as a Reader-orthogonal variable.**

**Gap 2 — Success spec under-discriminates against contingent-vs-quantified action.** §2 names six action types (posture / budget / roadmap / outreach / hiring / intel ask) but treats them as substitutable. The decision-format mapping shows they are **decision-shape-bound**: Cluster A primarily produces *contingent banded* actions (recommendation + kill-trigger), Cluster B primarily produces *quantified action* (specific dollar/sprint commitment), Cluster C primarily produces *structural commitment* (quadrant choice with swim-lane rule). The six action types from §2 aren't wrong — they're under-specified. A workflow that always produces "Cluster B–shape" actions will fail against acquisition-shaped decisions even if every action it names is on the §2 list.

**Gap 3 — CI-1 anchor doesn't discriminate against format-decision mismatch.** §4 CI-1 says the reader could "commit by next week." That works for Cluster B (1–4 week reactions) but **mis-anchors Cluster A** (where the commit horizon is 4–13 weeks and "by next week" is the wrong test) and Cluster C (where commit timing is structural). The "commit by next week" test will systematically misjudge acquisition and market-entry briefs as score-0 because real acquisition decisions aren't committed-to in a week — they're conditionally banded for a longer process.

**§3c is wrong in a load-bearing way.** §3c explicitly waves off abstraction-level mismatch with "CI-1 disqualifies abstraction-mismatch automatically." That holds for *strategic-vs-tactical* abstraction mismatch (which is what §3c is reading). It does NOT hold for *format-shape mismatch* (Cluster-A decision against Cluster-B brief format, or vice versa). CI-1's "commit by next week" anchor actively *creates* format-shape mismatch error in the Cluster A direction. The cleanest fix isn't another criterion — it's routing the structural_gate based on decision shape, then loosening CI-1's "by next week" to "by the next decision-shape-appropriate gate" (next week for Cluster B, next leadership review for Cluster A, next BD-committee for Cluster C).

**The judge does NOT need a sixth criterion.** Resist the temptation to add "CI-6: brief format matches decision shape" as a meta-criterion. That re-introduces feature-checking pathology — the workflow learns to slot-fill length/format markers. Format match belongs in `structural_gate`, which is the deterministic pre-judge filter, not in the LLM judge.

---

## 5. Specific edits to CI v2 spec

Concrete, surgical, in order of priority:

1. **Add to §1 Reader, after "may be reading reactively/proactively/on-demand":** "Each reading mode commissions one of three decision shapes — Evaluate (acquisition, market entry: irreversible high-capital, contingent banded recommendation), React (retention/pricing/roadmap: time-pressured reversible, quantified action), or Structure (partner/channel: structural commitment to a quadrant). The Reader and reading mode are decision-shape-orthogonal."

2. **Edit §2 Success, action list, add bridge sentence:** "These six action types take different shapes by decision: contingent and banded for Evaluate decisions (acquisition, market entry); quantified with explicit sacrifice for React decisions (retention, pricing, roadmap); structural commitment to a quadrant with swim-lane rule for Structure decisions (partner/channel)."

3. **Edit §4 CI-1 score-1 anchor, replace "the reader could commit by next week" with:** "the reader could commit by the next decision-shape-appropriate gate — next week for a React-shape decision (retention/pricing/roadmap), next leadership review (≤ 4 weeks) for an Evaluate-shape decision (acquisition/market entry), next BD or strategy committee (≤ 4 weeks) for a Structure-shape decision (partner/channel)."

4. **Edit §3c, replace the wave-off with:** "Wrong-strategic-level mismatch is caught by CI-1's commitment test. Wrong-format-shape mismatch (Cluster-A decision served by Cluster-B brief or vice versa) is a workflow-level routing concern, addressed by `structural_gate` cluster-routing — not a judge criterion. Adding it as a judge criterion would re-introduce feature-checking pathology (`c76f051`)."

5. **Add to §8 Open questions:** "**6. decision_shape routing.** Implement `structural_gate` variants per decision cluster (Evaluate / React / Structure) and surface `decision_shape` as a workflow input. Estimated ~1–2 weeks plan-time. Validate that judge rubric (unchanged) still discriminates correctly across all three clusters on existing fixtures."

Word count: ~3850.

---

## 4-line summary

- Word count: ~3850.
- Recommendation on decision-routing: **cluster** (route at workflow / `structural_gate` level into three clusters — Evaluate / React / Structure — not six bespoke formats and not one universal).
- Top failure mode the mapping surfaces: **format-shape mismatch** — Cluster-A decision served by a Cluster-B brief format (or vice versa), invisible to the current CI v2 spec because §3c explicitly waves abstraction-mismatch away and CI-1's "by next week" anchor systematically misjudges Cluster A.
- One specific edit recommended: **replace CI-1 score-1 anchor "commit by next week" with "commit by the next decision-shape-appropriate gate"** and add `decision_shape` as a workflow input variable that routes `structural_gate` and substrate (edit #3 + #5 above are the load-bearing pair).
