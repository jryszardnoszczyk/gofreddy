# Competitor Teardown & Pricing Analysis Framework

Sources (Corey Haines marketingskills repo):
- `sales-enablement`: https://github.com/coreyhaines31/marketingskills/tree/main/skills/sales-enablement
- `pricing-strategy`: https://github.com/coreyhaines31/marketingskills/tree/main/skills/pricing-strategy
- `content-strategy` (keyword-by-stage mapping)

Use this when producing analyses under `analyses/{competitor}.md` and when synthesizing cross-competitor patterns for the brief. Adds a standardized objection taxonomy, buyer-type tagging, and pricing-page teardown layer to the existing angle/mechanism/cadence framework (`ad-creative-analysis-framework.md`).

---

## The 15-objection gap taxonomy

Every competitor's pages, ads, and sales motion answer (or don't) a standardized set of buyer objections. Search each competitor's site for their response pattern to all 15; absences are positioning holes the client can exploit.

| # | Objection | What to look for on their site |
|---|-----------|-------------------------------|
| 1 | "Too expensive" | Pricing page clarity, ROI calculator, TCO comparison |
| 2 | "Competitor X is cheaper" | Direct comparison page, switcher stories, value-over-price argument |
| 3 | "We already use X" | Migration guide, coexistence story, integration stack |
| 4 | "What makes you different" | Differentiator page, manifesto, or founder post |
| 5 | "Security concerns" | SOC2/ISO/HIPAA badges, security whitepaper, data-residency page |
| 6 | "Can it scale" | Enterprise-tier details, published throughput/latency numbers, case studies at scale |
| 7 | "Need to check with my boss" | Boss-convincing template, business-case builder, printable one-pager |
| 8 | "Not the right time" | Implementation-timeline page, cost-of-delay framing, waitlist for later |
| 9 | "We build in-house" | Build-vs-buy calculator, engineering-hours comparison |
| 10 | "Support isn't reliable" | SLA page, support-hour coverage, named CSMs in case studies |
| 11 | "Lock-in / can't migrate out" | Data-export docs, open-format support, no-contract option |
| 12 | "Integrations we need" | Integration catalog, API docs, named partner logos |
| 13 | "Small team / not our stage" | Startup tier, "for teams of N" positioning, founder/SMB case studies |
| 14 | "Just starting / too early" | Free tier, 30-day trial, self-serve onboarding |
| 15 | "Not a priority this quarter" | Quick-win case studies, 30-day ROI proofs |

**Use in CI analyses:** for each competitor, record which objections they address strongly, weakly, or not at all. Clustered absences are structural gaps. A competitor missing responses to #3 (already-use-X), #5 (security), and #11 (lock-in) is under-built for enterprise evaluators — an asymmetric opportunity for a client that IS built for those.

Feeds CI-5 (asymmetric opportunities) and CI-6 (uncomfortable truths — what competitors handle better than the client).

---

## Buyer-type matrix (Technical / Economic / Champion)

Every page and ad is written for one of three buyer personas. Tag each competitor asset:

| Type | Motivation | Language markers | Asset types they optimize for |
|------|-----------|------------------|-------------------------------|
| **Technical buyer** | Will this work / integrate / scale? | Architecture diagrams, API docs, benchmarks, code samples, "built by engineers for engineers" | Docs, changelogs, technical blog posts |
| **Economic buyer** | What's the ROI / cost / risk? | $ savings, payback period, TCO, compliance badges, named enterprise logos | Pricing pages, ROI calculators, case studies with numbers |
| **Champion buyer** | Will this make me look smart to my boss? | "Used by [impressive peer]", social proof, transformation stories | Customer-story video, founder posts, community content |

**CI use:** a competitor targeting exclusively Technical buyers on their homepage but Champion buyers in their ads is either running multi-persona motion deliberately OR misaligned. Both are findings. Directly upgrades CI-3 (competitor trajectory).

---

## 10-12 slide storytelling arc (competitor deck / landing page teardown)

Corey's strong-deck structure. Use as a checklist when reading a competitor's sales deck or long-form landing page. Missing stages = argument gaps to exploit.

1. **Problem** — what pain is the buyer feeling?
2. **Cost of the problem** — what happens if unsolved?
3. **Shift in the world** — why the old way is breaking now.
4. **Approach** — the mental model / philosophy.
5. **Walkthrough** — how the product works concretely.
6. **Proof** — numbers, outcomes, named customers.
7. **Case study** — one narrative showing transformation.
8. **Implementation** — how fast, how hard.
9. **ROI** — named return on investment.
10. **Pricing** — tiers, limits, what's included.
11. **Next steps** — clear CTA, risk reversal.
12. **(Optional) FAQ / objection handling** — pre-emptive answers.

**CI use:** a competitor landing page missing stages 2 (cost of problem), 7 (case study), or 9 (ROI) is running a weak argument; reinforces CI-2 (evidence-traced claims).

---

## One-pager proof-point test

Competitor pages with 3+ differentiator bullets but no quantified proof behind them are running a weak argument the client can directly undercut. Test: for each "we are faster / better / easier" claim on a competitor page, is there a paired number or source?

- Claim + number + source = strong (citable, undercuttable only with better number).
- Claim + number, no source = moderate (verifiable but not self-anchored).
- Claim only = weak (vulnerable to any quantified counter-claim from client).

Cross-reference CI-2 (evidence-traced claims).

---

## Cost-of-delay framing (CI-4 operationalizer)

Corey's cost-of-delay frame: articulate what the buyer loses each week/month they don't act. Maps directly to CI-4's "window-closing argument" requirement. Concrete templates:

- **Revenue cost:** "Every month without X costs an avg $Y in [specific metric]."
- **Competitive cost:** "Competitor A shipped X last quarter; waiting leaves you N months further behind."
- **Compliance cost:** "Regulation Y lands in Q3 2026; non-compliant vendors face $Z fines."
- **Talent cost:** "Every sprint spent on X instead of Y is N engineer-days not reallocated."

A CI-4 recommendation missing a cost-of-delay frame is a "consider doing this" — with one, it's a "start this before N."

---

## Pricing-page teardown (competitive-session layer)

### Three pricing axes to classify

For each competitor pricing page, tag:

1. **Packaging** — what's in each tier (feature lists).
2. **Value metric** — what the buyer is charged per: `per-seat | per-usage | per-feature | per-transaction | per-contact | flat | hybrid`.
3. **Price point** — absolute numbers per tier.

### Value-metric detection rule

Value metric is the strongest pricing positioning tell. Competitors with misaligned metrics (e.g., charging per-seat for an API-driven product) have a gap a smarter-metric competitor can exploit.

Common value metrics by category:
- CRM / CRM-adjacent: per-seat (aligned with user count as scaling driver).
- API / infra: per-request, per-GB, per-transaction.
- Marketing automation: per-contact, per-send.
- Observability: per-host, per-GB-ingested, per-metric.
- Creator tools: per-creator or per-audience-size.

### Tier-count heuristic

- **2 tiers** = SMB vs Enterprise split (product-led → sales-led handoff).
- **3 tiers** = Good-Better-Best anchoring (behavioral-economics standard; middle tier gets majority pick).
- **4+ tiers** = feature proliferation signal; potential decision paralysis. Sometimes deliberate (capturing narrow segments) but often a sign of pricing-strategy drift.

A competitor shifting from 3 tiers to 4-5 between captures is reacting to specific customer segments; worth naming the archetype they added for.

### Pricing psychology signals on competitor pages

- **Anchoring** via "starts at" showing the high tier first = premium positioning.
- **Decoy middle tier** (one unattractive-seeming middle offer that makes a specific tier look best) = sophisticated pricing team.
- **Charm pricing ($49)** vs round pricing ($50) = charm tier reads "value," round tier reads "premium." Mix within one page = inconsistent positioning.
- **Inconsistent tier prices across channels** (partner pricing, affiliate pricing, direct pricing different for same features) = likely running WTP research (Van Westendorp or MaxDiff). Tag as "competitor testing pricing" — predictive signal for upcoming price change.

### "Contact sales" as a tell

Hidden pricing ("contact sales") for an otherwise self-serve product is either (a) high-touch motion by design, (b) deliberately friction-adding for BDR-first routing, or (c) a pricing team without confidence to publish. Read the surrounding pricing page for signal. See also CQ-13 (machine-readable `/pricing.md` for agent buyers).

---

## Buyer-stage query mapping (applies to competitive content audits)

When analyzing a competitor's content coverage, tag each of their pages by buyer stage (cross-references the GEO `page-structure-and-comparison-patterns.md`):

| Stage | Query patterns |
|-------|----------------|
| Awareness | "what is," "how to," "guide to" |
| Consideration | "best," "top," "vs," "alternatives" |
| Decision | "pricing," "reviews," "demo" |
| Implementation | "templates," "tutorial," "setup" |

A competitor saturating Consideration but absent on Awareness or Implementation is under-investing in either demand-gen (top of funnel) or retention (bottom). Both are asymmetric-opportunity findings (CI-5).

---

## Reporting template

For each competitor's teardown, append to `analyses/{name}.md`:

> **Objection coverage:** addresses {strong-list}, weak on {weak-list}, absent on {absent-list}.
>
> **Buyer type tagging:** homepage = {type}, ads = {type}, docs = {type}. {Aligned | Misaligned — which section reads for a different persona}.
>
> **Deck / landing-page argument gaps:** missing {1-2 of the 12 stages}.
>
> **Pricing:** value metric = {type}; {2|3|4+} tiers; {anchoring|decoy|charm} signals observed; pricing {published|contact-sales|hybrid}.
>
> **Buyer-stage coverage:** {saturated} / {under-invested}.
>
> **Angle × mechanism × cadence** (from `ad-creative-analysis-framework.md`): {…}.

This combined line feeds CI-1 (single thesis), CI-2 (evidence-traced), CI-3 (trajectory), CI-5 (asymmetric opportunities), and CI-6 (uncomfortable truths) simultaneously.
