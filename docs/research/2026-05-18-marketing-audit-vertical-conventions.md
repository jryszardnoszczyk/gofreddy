---
date: 2026-05-18
type: research deliverable
status: complete
topic: marketing-audit vertical conventions — industry × stage
parent: docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md
guide: docs/rubrics/judge-design-guide.md
companions:
  - docs/research/2026-05-18-judges-domain-marketing-audit.md (generalist MA domain research — DEEPENED here)
  - docs/research/2026-05-18-ci-vertical-conventions.md (sibling pattern for CI lane)
  - docs/handoffs/2026-05-17-judge-design-step1-competitive.md (vertical-anchor pattern reference)
---

# Marketing Audit — Vertical Conventions (Industry × Stage)
## What changes by industry × stage, and what the MA v1 spec must accommodate

**Why this exists.** The generalist domain research treats the MA reader as "founder/CMO at pre-Series-B-to-Series-C B2B SaaS." That archetype maps cleanly onto roughly 35–50% of plausible fixtures. Klinika (Polish aesthetic dermatology), DWF (UK legal services), plus future fixtures from DTC, fintech, marketplaces, dev-tools, services, or hospitality have different binding-constraint surfaces, evidence substrates, stage maps, and readers. A 50-generation evolution loop with a single-archetype rubric will learn to produce SaaS-shaped audits and grade non-SaaS audits down for failing to fit. This deliverable goes vertical × stage so the MA judge does not silently optimize for one archetype.

---

## TL;DR

**The stage axis is more load-bearing than the industry axis.** A Seed audit and a Series-C audit are structurally different artifacts regardless of vertical — Seed pressure-tests positioning, ICP, and the single channel that might compound; Series-C pressure-tests CAC payback, cohort retention curves, expansion motion, multi-channel attribution. Stage mismatch is the single most-burning failure mode: Series-C playbook on a Seed startup burns runway; Seed playbook on Series-C misses the unit-economics layer entirely.

**The industry axis matters where it changes the metric set, the channel-mix space, and the upstream-vs-marketing diagnostic.** B2B SaaS uses CAC payback + NRR + trial-to-paid + pipeline-sourced. Local healthcare uses CAC-by-channel + capacity utilization + review velocity + referral-rate. Marketplaces use take rate + liquidity + cohort-retention by side. DTC uses contribution margin + CAC:LTV-by-cohort + repeat-purchase rate. Regulated B2B uses pipeline + win-rate + referral-source-mix.

**For v1, three concrete recommendations:** (1) three vertical-anchored score-1 examples per criterion (SaaS / consumer-or-marketplace / services-or-regulated), pattern from CI v3.3; (2) generalize MA-4's stage-map criterion away from ARR-band-only anchors; (3) add explicit stage-mismatch Goodhart failure mode to §3b.

---

## Key questions

(1) MA shape across STAGE (Pre-seed / Seed / Series A / B / C / Late / IPO); (2) MA shape across INDUSTRY (B2B SaaS, DTC, healthcare, fintech, dev-tools, marketplace, services); (3) per-cell "passing" vs "failing"; (4) divergent vertical anchors to avoid first-cohort overfit; (5) the stage-mismatched-framework failure mode and how the judge resists rewarding it.

---

## 1. Stage Axis — what changes Pre-seed → IPO

The stage axis is more load-bearing than the industry axis. Industry changes metric names and channel space; stage changes which dimensions are even examinable, what the binding constraint can be, and what a defensible recommendation looks like.

### Pre-seed / Pre-PMF (<$200K ARR or pre-revenue)

Most of the standard audit toolkit is inapplicable: no cohort curves, trial-to-paid noise dominated by 5–20 customers, CAC payback undefined without LTV. The audit's job is an upstream diagnostic: is this pre-PMF and the founder needs to fix product/positioning/ICP first?

**Passing:** names ICP confusion or PMF gaps; recommends a PMF survey, messaging-resonance tests, or best-fit-customer interviews before channel work. Refuses paid acquisition. **Failing:** recommends "increase paid spend on LinkedIn" or "build a content engine"; names "lead generation" as the constraint when the artifact gives no evidence retention works.

### Seed ($200K–$2M ARR; founder-led sales or one working channel)

Pressure-tests positioning, ICP sharpness, and the single channel that is or isn't compounding. Binding constraint is almost always: positioning too generic and trial-to-paid leaking; founder hasn't located the company in a single acquisition lane; or retention too weak to scale spend on the channel that works.

**Passing:** names one acquisition channel as the next-90-day bet + the prerequisite to scaling it (positioning rewrite, homepage variant, onboarding fix). Refuses to recommend a second channel until the first is proven. Max 2–3 scoped actions for the next 30 days. **Failing:** recommends ABM at $1M ARR with under 50 customers (ICP too noisy); full marketing-ops stack when 80% of revenue is founder-sourced; "diversify channels" before one channel works.

### Series A ($2M–$8M ARR; first GTM hire, first paid channel scaling)

Tests whether the company graduated from one working channel into a repeatable GTM motion. Is the founder still selling 60%+ of pipeline? Definable funnel, or fog with marketing reporting MQL volume and sales reporting only closed-won? Dominant constraint: funnel-fog.

**Passing:** names which funnel stage is the constraint with evidence from at least two sources (cohort, call transcripts, attribution, interviews). Recommends instrumentation if missing. Distinguishes founder pipeline from marketing-sourced honestly. **Failing:** scales paid spend before the funnel resolves; ABM tooling without customer-success motion; reports MQL volume as headline when MQL→SQL is unmeasured.

### Series B ($8M–$20M ARR; multi-channel motion, GTM team build-out)

Multi-channel attribution and unit-economics audit. CAC payback should be measurable; cohort retention should resolve to a 6–12-month curve; channel-by-channel CAC should be visible. Pricing becomes first-class — changes show up in expansion revenue and net retention.

**Passing:** reports CAC payback per channel against target (<12 mo SMB, <18 mid-market per Bessemer). Identifies channels above/below the payback bound. Names expansion as a separate growth engine. Surfaces pricing as a lever when expansion is below 110% NRR. May recommend pausing a channel. **Failing:** reports channel performance without unit economics ("LinkedIn delivered 280 MQLs at $42 CPL" — no CAC, no payback); "double down on best-performing" without checking payback waterline; treats expansion as out-of-scope.

### Series C / Pre-IPO ($20M–$100M ARR; multi-segment, multi-product, multi-region)

Portfolio audit. Binding constraint is usually: one segment masks weakness in another; legacy GTM no longer fits the drifted ICP; expansion hides new-logo deceleration; brand-vs-performance mix stale.

**Passing:** decomposes revenue and growth by segment (SMB/mid/enterprise; or B2C/B2B; or region). Names which segment is decelerating and the leading indicator. Distinguishes expansion-driven from new-logo growth. Surfaces brand-vs-performance mix; recommends rebalancing if brand under-invested for two cycles. Max three priorities. **Failing:** aggregate growth masks segment weakness; treats expansion and new-logo as fungible; recommends "improve content" when constraint is mid-market CAC payback over 24 months; applies SMB playbooks when company has graduated to enterprise-led GTM.

### Late stage / Public-readiness

Audits at this stage are conducted by investment banks or activist investors; founder-CMO archetype no longer fits. Largely out of scope — fixtures unlikely. If one appears, v1 needs a sibling fork.

---

## 2. Industry Axis — what changes B2B SaaS → DTC → marketplaces → services

The industry axis matters where it changes (a) the metric set, (b) the channel space, (c) the upstream-vs-marketing diagnostic, (d) the regulatory or structural ceiling on what tactics are legal/ethical.

### 2.1 B2B SaaS — the archetype the generalist research assumes

**Metric set.** CAC payback (<12 SMB, <18 mid-market, 24+ enterprise). NRR (110%+ healthy). Trial-to-paid (SaaS median ~6%). MQL→SQL→opportunity→closed-won. Pipeline-sourced ratio.

**Channel space.** Content/SEO, paid (Google, LinkedIn, programmatic), outbound, PLG, partnerships, communities, events, ABM (at maturity).

| Stage | Audit focus | Primary failure mode |
|---|---|---|
| Seed | Single-channel commitment + ICP sharpness | ABM / full-funnel attribution / paid scaling |
| Series A | Funnel-fog resolution + GTM-motion definition | Scaling spend before attribution resolves |
| Series B | Channel unit economics + pricing + expansion | CPL/MQL without CAC payback; ignores expansion |
| Series C | Segment decomposition + new-logo-vs-expansion + brand-performance | Aggregate growth as unit of analysis |

**Upstream diagnostic toolkit (strong).** PMF survey, retention cohorts, ICP-fit interviews, call transcripts. Can credibly diagnose PMF / pricing / sales motion / onboarding / marketing.

### 2.2 B2C / DTC e-commerce — next-most-likely fixture

**Metric set.** Contribution margin per unit. CAC:LTV by cohort. Repeat-purchase at 30/60/90/180/365 days. First-purchase AOV vs LTV AOV. Channel CAC (Meta, TikTok, Google Shopping, retail, organic, influencer). Payback-by-cohort. Returns rate.

**Channel space.** Meta Ads, TikTok Ads, Google Shopping, influencer (paid + seeded), affiliate, retail/wholesale, email/SMS, organic social, referral, podcasts, OOH at scale.

**Stages don't map to ARR.** $500K/mo is early; $5M/mo is mid-stage; $20M+/mo is late-stage and usually has a retail layer.

**Stage-specific failure modes:** Early DTC audit treats first-purchase CAC as the success metric and ignores contribution margin at the second purchase — the actual question is whether the repeat-purchase engine makes unprofitable first acquisition pay back. Mid DTC recommends scaling the best-CPA channel without checking incrementality (Meta and Google attribution systematically over-credit themselves; post-iOS-14.5 requires geo-holdout / Haus / Northbeam-style measurement). Mature DTC treats digital channels as the only growth surface when the company has graduated into retail / wholesale / international.

**Upstream gates differ from SaaS:** (a) product-margin economics; (b) repeat-purchase / retention; (c) supply-chain or unit-economics ceilings. PMF is replaced by "do customers come back at a rate that makes CAC pay back?"

**Failing shape:** "expand to TikTok Shop" or "test new creative angles" when the actual constraint is contribution margin not supporting paid acquisition at current CAC.

### 2.3 Healthcare / aesthetic dermatology / local services — Klinika archetype

**Metric set.** CAC-by-channel (referral $50–150; RealSelf $200–400; Google paid $400–800; cold paid $600+). Capacity utilization (chair-time / room-time as % of available). Review velocity and rating (Google, RealSelf, Healthgrades). Patient LTV (varies by treatment-mix). Referral rate and source-mix.

**Channel space.** Referrals (highest-LTV, lowest-CAC), Google Business Profile + reviews, RealSelf / Healthgrades, Instagram + TikTok (aesthetic), local SEO, geo-targeted paid, email/SMS retention, partner referrals.

**Stage is about capacity and brand, not funding.** Pre-PMF = new opening; "Series A" = high-utilization single location; "Series B" = multi-location or strong waitlist; "Series C" = regional brand or PE-roll-up candidate.

| Stage | Audit focus | Failure mode |
|---|---|---|
| New / underutilized | Local presence + reviews + referral seed | National PR / brand campaigns |
| Healthy single-location | Treatment-mix margin + capacity + retention | Scaling paid spend before capacity is full |
| Multi-location or waitlist | Capacity expansion + brand + channel diversification | Treating local signals as transferable across markets |
| Regional brand | Practice economics + PE-readiness + brand-vs-local-trust | National-brand playbook when local trust is the moat |

**Upstream gates:** (a) clinical reputation; (b) capacity (no recommending more leads if appointments are 6 weeks out); (c) treatment-mix margin.

**Failing shape:** "Run Meta Ads for Botox patients" when the practice has a 4.2 Google rating, no RealSelf profile, and reviews mentioning long wait times. Constraint is reputation + capacity, not lead volume. SaaS-shaped audit here diagnoses "low conversion" and recommends "tighten messaging" — wrong layer.

### 2.4 Other verticals — condensed (fintech, dev-tools, marketplaces, services)

Lower-probability fixtures in the near term, but each matters for first-cohort overfit defense:

**Fintech / regulated B2B.** Metric set: pipeline + win-rate + sales cycle + cost-per-qualified-meeting. Channel space regulatory-constrained — cold outbound partially/wholly illegal under UK FCA financial-promotions, US attorney-advertising, anti-spam laws. Upstream gates: regulatory clearance, reference / case-study generation, analyst positioning. Failing shape: recommends paid acquisition before regulatory clearance to legally convert leads.

**Dev-tools / API.** Metric set: activations, time-to-first-API-call, PLG conversion, docs engagement, self-serve-to-enterprise rate. The marketing surface IS the documentation; developers dislike paid ads. Upstream gates: DX quality, docs quality, reliability/security. Failing shape: "create more blog content" or "run Google Ads" when actual surface is docs and onboarding flow.

**Marketplaces.** Metric set: take rate + liquidity + cohort retention BY SIDE separately + CAC by side + GMV + density by geo. Imbalance is canonical failure. Upstream gates: take rate vs alternatives, trust/safety, geographic density. Failing shape: reports aggregate growth without decomposing by side (30% supply + 80% demand growth looks healthy but starves supply churn).

**Professional services / agencies.** Metric set: pipeline + win-rate + project size + repeat-client rate + referral-source-mix + utilization. Referrals drive 40–70% of pipeline. Failing shape: scales content / inbound without engaging partner-led / referral dynamic; or treats founder as a channel that scales linearly.

---

## 3. Industry × Stage failure matrix — what stage-mismatch looks like

The most-damaging failure mode the MA judge must resist is **applying a stage-mismatched or industry-mismatched framework**.

| Mismatch | Specific failure | Why it burns the reader |
|---|---|---|
| Series-C → Seed | Audit at $1.8M ARR recommends ABM stack, full marketing-ops, multi-channel attribution | Burns runway on infrastructure the company can't yet need; ICP too noisy; team capacity absent |
| Series-B → Seed | Recommends scaling paid spend before retention data exists | Acquired customers leak before payback |
| Seed → Series-C | At $30M ARR recommends "tighten ICP" when the company has 3 working ICPs across segments | Misses the segment-decomposition the analytical level requires |
| Series-A → Series-C | Recommends "fix attribution" when constraint is mid-market CAC payback exceeding 24 months | Correct in spirit, mis-located in the stack; nothing moves |
| B2B SaaS → DTC | "Fix trial-to-paid" for a brand with no trial | Category error |
| B2B SaaS → Healthcare | "MQL nurture sequences" for a derm practice whose patients book directly | Mis-applied funnel |
| B2B SaaS → Dev-tools | "Content engine" when the marketing surface is documentation quality | Wrong artifact category |
| B2B SaaS → Marketplace | "Demand-side optimization" when supply is the binding constraint | Mis-attributes the bottleneck side |

Judge's job: penalize audits that apply stage-mismatched or industry-mismatched frameworks. The audit must demonstrate it identified the company's stage and industry-specific shape before recommending; recommendations that don't tailor to either are score-0.

---

## 4. Vertical-specific evidence substrates

| Vertical | Evidence to engage | Comp-grade signal |
|---|---|---|
| B2B SaaS | Cohort retention, CAC payback by channel, call analysis, sales-cycle, pipeline-sourced, PMF responses | Trial-to-paid vs SaaS median |
| DTC | Contribution margin per cohort, repeat-purchase 30/60/90, channel CAC + incrementality | Cohort LTV at 12 months vs payback |
| Healthcare (local) | GBP review velocity + sentiment, RealSelf activity, capacity utilization, referral-source mix, treatment-mix margin | Local-market density, rating cohort movement |
| Fintech / regulated | Pipeline + win-rate + sales cycle, regulatory-clearance state, analyst positioning | Win-rate vs benchmark by deal size |
| Dev-tools | API activation, time-to-first-call, docs engagement, community activity, self-serve-to-enterprise rate | Developer NPS, stars-to-activation ratio |
| Marketplaces | Liquidity rate, retention BY SIDE, take rate vs alternatives, network density by geo | Supply LTV vs demand LTV at 6 months |
| Services | Referral-source mix, win-rate by lead source, utilization, repeat-client rate | Founder-vs-team sourced pipeline split |

The judge does NOT need to know which substrate to cite for which vertical — the audit's job is to engage the right substrate, and the judge's job is to check whether the substrate cited is appropriate for the company's vertical and stage. An audit citing "trial-to-paid conversion" for a derm practice is using the wrong substrate.

---

## 5. Cross-vertical synthesis

**Universal across all verticals × stages:** (1) diagnosis before prescription; (2) stage-appropriate recommendations; (3) trace to revenue / contribution margin / unit economics; (4) upstream surfacing when constraint is upstream of marketing; (5) hard prioritization.

**Load-bearing variance:** metric set, channel space, upstream-diagnostic toolkit, stage map, and Goodhart-collapse target all differ structurally by vertical. SaaS slop produces MQL-volume vanity findings; DTC slop produces "creative refresh" untied to incrementality; healthcare slop produces "improve Google reviews" without engaging capacity or treatment-mix.

**Takeaway.** v0 names the reader as "founder/CMO at pre-Series-B B2B SaaS." Too narrow — the lane will also grade Klinika and may grade DTC / marketplaces / dev-tools / services / fintech. A 50-generation loop with one-archetype anchors overfits to SaaS-shaped audits. Fix: three vertical-anchored score-1 examples per criterion (SaaS / consumer-or-marketplace / services-or-regulated), hedged "do not optimize toward this," plus a generalized stage-map criterion.

---

## 6. Recommendations for the MA v1 spec

**1. Three vertical-anchored score-1 examples per criterion.** Same pattern as CI v3.3. v0 has SaaS-only examples on all 5 criteria. Add a consumer/DTC/marketplace example to MA-1, MA-2, MA-3, MA-5 (MA-5's is especially load-bearing — upstream gates differ wildly in DTC). Add a local-services/healthcare example to MA-1, MA-4, MA-5. Current SaaS example stays on MA-2, MA-3. Result: five verticals across five criteria without inflating each above ~200 words.

**2. Generalize MA-4 beyond ARR-band-only anchors.** Replace ARR-band language: "Score 1: The audit names the company's current stage with at least one observable anchor — ARR band, retention cohort signal, channel concentration, hiring trajectory, capacity utilization, monthly revenue + margin profile, pipeline composition, or industry-specific stage signal (location count for local services, regulatory licensing for fintech, network density for marketplaces)."

**3. Add explicit stage-mismatch Goodhart failure mode to §3b.** v0 §3 names ten-page-PDF / vanity-metric / no-revenue-tie / generic-recommendations. Add: "Stage-mismatched framework application. The audit applies a stage-inappropriate framework regardless of evidence: ABM stack for $1.8M ARR; PLG tactics for a sales-led company; 'trial-to-paid optimization' for a DTC brand with no trial; 'MQL nurture' for a derm practice. The recommendation may be best-practice in some other context but is wrong for THIS company's stage and industry. Score 0 even if every other surface marker (named constraint, owner, budget, timeline) is present."

**4. Vertical-evidence-substrate sentence in the wrapper.** Mirroring CI: "Evidence sources vary by vertical and stage — cohort retention and CAC payback in SaaS, contribution margin per cohort and repeat-purchase in DTC, review velocity and capacity utilization in local healthcare, win-rate and referral-source mix in services, liquidity and side-specific retention in marketplaces. Do not penalize evidence sources unfamiliar to a SaaS reader; do penalize sources categorically wrong for the company's industry."

**5. Watch for MA-1 / MA-4 redundancy.** Audits that locate stage tend to also name the binding constraint. Run pairwise correlation (design-guide §5) on 5 fixtures × 5 criteria × 3 panel models. If MA-1 and MA-4 correlate >0.7, merge into "diagnosis-with-stage-and-evidence."

**6. Defer per-vertical sub-specs.** Don't bifurcate yet. Run single-spec with three vertical-anchored examples per criterion; if rationales still skew SaaS, escalate.

---

## 7. Open questions

1. **Vertical fixture coverage.** Lane has Anthropic / Perplexity / DWF fixtures but lacks Klinika-class healthcare, DTC, marketplace, dev-tool fixtures. Build 2–3 fixtures from these verticals before fully locking criteria via empirical redundancy check.

2. **Stage-evidence anchors in MA-4.** Generalizing beyond ARR bands needs validation: which signals can the judge reliably detect? Some are observable ("we have 91% NRR"); others are not (hiring patterns). Judge should test whether stage diagnosis is defensible from the artifact, not require a specific signal type.

3. **MA-5 vertical-neutrality.** v0 names upstream constraints as PMF / ICP / product / pricing / sales motion — SaaS-shaped. For DTC: contribution margin and repeat-rate. Marketplaces: liquidity and trust/safety. Healthcare: clinical reputation and capacity. MA-5's prose should be vertical-neutral ("upstream-of-marketing constraint"); examples should span verticals.

4. **Decision-class scope.** Current spec scopes to "audit + 30-day commit" / "fractional-CMO 30/60/90." When other classes appear (strategic memo, channel teardown, scorecard-only), v1 may need sibling-lane treatment. Defer.

5. **First-cohort overfitting watch.** Same as CI v3.3 §8.7. Current first-cohort: Anthropic / Perplexity / DWF / Klinika. Re-validation trigger: any fixture from a vertical not in {SaaS, AI-lab, legal, healthcare} prompts a re-validation pass.

6. **CAC payback as load-bearing concept.** Central to SaaS, partial for DTC (payback-by-cohort) and regulated B2B (pipeline-conversion economics). For healthcare/services it transforms into CAC-by-channel without a clean payback formula. Judge should test whether the audit operates in the unit-economics layer for its vertical, not whether it cites "CAC payback" specifically. Score-1 examples should span verticals so the workflow doesn't learn that "CAC payback" is the magic phrase.

7. **Hard constraints check.** All proposed changes comply with the design-guide constraints: no σ-widening, no anti-gaming clauses, no framework-name embedding, no feature-checking (outcome-question discipline preserved), reference-free (examples hedged "do not optimize toward this"), first-cohort overfit watch explicit.

---

## 8. Citations

**B2B SaaS:** Bell Curve / Demand Curve audit-before-strategy methodology; Kalungi 95-point inspection + SaaS-growth-stages (kalungi.com/audit); Patrick Campbell / ProfitWell pricing audits; Tomasz Tunguz CAC Payback (tomtunguz.com); Bessemer State of the Cloud (bvp.com/atlas/cloud-computing-metrics); Brian Balfour Four Fits (brianbalfour.com); Lenny Rachitsky + Dan Hockenmaier Customer Acquisition Lanes (review.firstround.com); Andrew Chen a16z essays; Reforge canon on premature scaling.

**DTC:** Common Thread Collective / Taylor Holiday DTC unit-economics; Northbeam / Haus post-iOS-14.5 incrementality (northbeam.io, haus.io); Drew Sanocki / Karl Schmieder repeat-purchase economics; Andrew Faris AJF Growth.

**Healthcare / local-services:** AmSpa Medical Spa State of the Industry Report (americanmedspa.org); AmSpa 2025 Aesthetic Marketing Report; ASDS Consumer Survey (asds.net); Growth99 / Cardinal / Intrepy benchmarks; RealSelf Insights Center.

**Fintech / regulated B2B:** Gartner / Forrester analyst-positioning; Pavilion / RevGenius pipeline benchmarks; UK FCA financial-promotions reg + EU MiCA as channel constraints.

**Dev-tools:** Heavybit / DevTools-Insiders (heavybit.com); Bessemer Roadmap to a Better Developer Platform; DevRel / OSS-GTM literature (Joseph Jacks, Adam Gross, Adam Frankl).

**Marketplaces:** Bill Gurley / Sarah Tavel two-sided canon; a16z marketplace canon (Chen, Jin).

**Services / consultancy:** HubSpot Agency Partner playbooks; Win Without Pitching (Blair Enns); David C. Baker agency-economics audits.

**Cross-vertical:** Sean Ellis PMF + ICE + North Star; April Dunford positioning; Eric Ries vanity-vs-actionable; Dave McClure AARRR; Peep Laja / CXL ResearchXL; Ross Simmonds / Foundation Inc distribution-first; Fractional-CMO 30/60/90 playbooks (Envizon, SaaSConsult, ASP, ThinkCap, Strategic Pete).

**Internal siblings:** `docs/research/2026-05-18-judges-domain-marketing-audit.md`; `docs/research/2026-05-18-ci-vertical-conventions.md`; `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (CI v3.3 first-cohort overfit reduction pattern); `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md`; `docs/rubrics/judge-design-guide.md`.
