---
date: 2026-05-18
type: research deliverable
status: complete
topic: marketing-audit artifact taxonomy (exec scorecard / mid-length audit / teardown / deck / digest / 30-60-90 roadmap)
parent: docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md
sibling: docs/research/2026-05-18-judges-domain-marketing-audit.md
companion: docs/research/2026-05-18-ci-artifact-taxonomy.md (CI taxonomy — same axis, sibling lane)
---

# Marketing-Audit Artifact Taxonomy

## 1. TL;DR + artifact-shape recommendation

The marketing audit, like the CI brief, is not one artifact — it is at least six recognisable form factors that the operator community treats as different products with different readers, length conventions, evidence density, and decision shapes. The current gofreddy `marketing_audit` lane spec (`docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md`) implicitly nominates a hybrid — Day-30-deliverable-shaped, founder-readable, but with no locked length, no locked structural skeleton, and no shape-conformance enforcement in `structural_gate`. Under 50-generation selection pressure, that under-specification is the same shape-drift Goodhart surface the CI lane closed in v3.2 of its spec.

The six canonical shapes the practitioner community produces:

1. **Exec scorecard / readiness one-pager** — 1–2 pages, 5-point dimensional scores plus a single yes/no readiness verdict. Kalungi One-Page Marketing Readiness Audit, MaRS marketing readiness assessment, B2B Marketing Audit Checklist (1pg-format). Reader: founder pre-engagement. Decision: do I hire/fire/commit budget.
2. **Mid-length founder audit + roadmap** — 8–15 pages, 2,000–4,500 words, named binding constraint plus 30/60/90 sequencing. Kalungi 95-point B2B SaaS audit + fractional-CMO 30/60/90 (Envizon, SaaSConsult, ASP, ThinkCap). Reader: founder/CEO or fractional CMO Day-30 deliverable. Decision: commit 1–2 bets for the next quarter.
3. **Domain teardown** — 15–40 pages of deep analysis of ONE marketing dimension (paid acquisition / content / pricing / positioning / SEO / website CRO). Bell Curve paid-acquisition audit, Foundation Inc content audit, ProfitWell pricing audit, Wynter messaging-resonance audit, CXL ResearchXL CRO audit. Reader: head-of-growth or specialist marketing lead. Decision: re-architect the chosen function.
4. **Slide deck / board-ready audit** — 20–40 slides, executive committee or board presentation, "marketing health check" deck. ANA/AMA assessment frameworks, agency-of-record annual reviews, McKinsey/Bain marketing-effectiveness reviews. Reader: CMO or board. Decision: organisational realignment, budget envelope shift, agency replace/retain.
5. **Notion / live-doc operating audit** — collaborative, in-platform, link-rich, often per-channel page tree. Lenny's Newsletter operating templates, Reforge teardown templates, internal Notion playbooks from MKT1, Demand Curve school templates. Reader: in-house growth team. Decision: ongoing operational reprioritisation, owned by team rather than consumed once.
6. **Audit dashboard / digest** — automated platform output (HubSpot Marketing Hub Health, Semrush Site Audit, Ahrefs Site Audit, Improvado dashboards). Reader: marketing-ops analyst. Decision: tactical fix-list triage.

The decision-format-mapping problem is sharper here than in CI. CI fixtures cluster on the React-cluster decision (commit-this-week to a posture). Marketing-audit fixtures cluster across at least three decision classes: (a) **10-minute skim by CEO** ("is marketing the problem? do I keep this engagement?"), (b) **60-minute review by CMO or fractional CMO** ("what's my 90-day plan?"), and (c) **30-day fractional engagement** ("what's the full discovery deliverable that justifies the next 60 days of work?"). Different shapes serve different decisions; the lane cannot serve all three with one form factor.

**Recommendation: option (b) — one hybrid shape, mid-length founder audit + roadmap as the spine (2,000–4,500 words, 5 sections), with exec-scorecard-style readiness verdict as the opening section and domain-teardown-grade evidence depth on the named binding constraint, optionally with a Day-30/60/90 sequencing tail when the engagement justifies it.** This mirrors the CI taxonomy's option (c) decision logic: lock the spine, raise the evidence depth on the load-bearing element, optionally tail-extend for engagement-stage fixtures.

Reject (a) pure exec scorecard — too thin for the named binding-constraint + revenue-chain criteria (MA-1, MA-3) and too thin for the upstream-problem criterion (MA-5) which needs evidence triangulation to defend a "the bottleneck isn't marketing" conclusion. Reject (c) full domain teardown — current `marketing_audit` lane fixtures span domains (paid + content + pricing + positioning), so domain-locking is wrong. Reject (d) deck — slide-format scoring is a different rubric problem (visual rhetoric, slide-density Goodhart, framework-deck templating; see Goodhart-collapse §5). Reject (e) Notion live-doc — current substrate produces single-artifact output, not a per-channel tree. Reject (f) dashboard — already covered by HubSpot/Semrush/Ahrefs SaaS, lane has no value to add.

The top failure-mode the taxonomy surfaces that the v0 spec does not explicitly close: **audit-bloat + recommendations-count-gaming** — the workflow learns that longer audits with more recommendations score higher on shallow proxies, producing 12-page audits with 8 recommendations of equal weight. The fix is shape-locking in `structural_gate` and outcome-question criteria that test a single named binding constraint and 1–3 prioritised recommendations.

---

## 2. Per-shape deep dive

### 2.1 Exec scorecard / readiness one-pager

**Canonical exemplars.**
- **Kalungi One-Page Marketing Readiness Audit** (kalungi.com/blog/one-page-marketing-readiness-audit-for-saas-founders) — the single most-referenced one-pager in the B2B SaaS founder space. Specifically designed to answer "should we hire a marketing leader yet?" with a yes/no verdict.
- **Kalungi 95-Point B2B Marketing Audit Scorecard** (kalungi.com/audit) — although the full audit is mid-length, the headline deliverable is the 5-point-scale scorecard summary across ~10 dimensions (brand, SEO, positioning, messaging, website, paid channels, content, lifecycle, ops, attribution). The scorecard alone is a defensible one-pager.
- **MaRS Marketing Readiness Assessment** (marsdd.com/mars-library/marketing-readiness/) — Canadian innovation-network template, 1-page assessment for early-stage tech companies.
- **HubSpot Marketing Grader / Website Grader** (hubspot.com/website-grader, marketing.grader.com archive) — automated single-page output with an A–F or 0–100 score. Marketing-Ops-adjacent.
- **B2B Marketing Audit Checklist templates** — TripleDart (tripledart.com/b2b-marketing/audit), ByDefaultCMO (bydefaultcmo.com/marketing-audit-system), and Growth Syndicate (thegrowthsyndicate.com/resources/marketing-audit) all publish 1-page versions sized for founder pre-engagement skim.

**Length convention.** 1–2 pages. 200–500 words of narrative plus a scorecard table. The scorecard is the load-bearing element; the prose is reading-aid only.

**Structure / sections in order.** Verdict-at-top → dimensional scorecard table (5–10 rows, 5-point or A–F scale per row) → 2–3 sentences of overall narrative → single concrete next-step recommendation ("you are not ready to hire a full-time CMO; spend the next 60 days on ICP clarity and PMF re-test"). The Kalungi readiness-audit explicitly opens with the binary readiness verdict before any dimensional analysis.

**Evidence type and density.** Sparse but disciplined. Each scorecard row is one score plus one sentence of rationale. Citations rarely embedded; the scorecard's authority comes from the methodology behind the framework, not from per-row source-traceability. Single chart or visual at most.

**Reader persona.** Founder-CEO at pre-Series-A SaaS, evaluating whether to commit to a longer engagement. Time budget: 5–10 minutes, often consumed on phone. Decision shape: gate decision — do I hire this consultant / do I keep this fractional CMO past Day 30 / do I shift budget envelope. The reader is NOT looking for a roadmap; they are looking for "are we ready for marketing investment to work?"

**Recommendation specificity.** Single next-step at most. The artifact is diagnostic, not prescriptive. Kalungi's one-pager famously ends with "you need to address [specific upstream issue] before any marketing investment will pay back" — and that is the whole recommendation, not a 30/60/90.

**Failure modes.** (a) Scorecard inflation — every dimension scored 3–4 ("solid but could improve"), no discrimination, no actionable signal. (b) Missing verdict — the one-pager shows the scorecard but never commits to the yes/no readiness call. (c) Scorecard without methodology — 5/5 on "brand" with no definition of what 5/5 means. (d) Auto-grader vanity scoring (the HubSpot Grader pattern) — every site scores in the 70s-80s, no real discrimination.

**AI-generation difficulty.** Easy structurally, hard substantively. The one-page form factor is well within LLM range, but the discrimination quality depends entirely on the methodology behind the scorecard, which is fixture-specific and hard to validate. LLM-generated readiness scorecards routinely score everything 3/5 because the model hedges.

**Why this shape doesn't fit the lane.** Too thin for MA-1's evidence-source requirement (2+ supporting sources behind the named constraint) and MA-3's revenue-mechanism chain. The verdict-at-top form is a useful element to BORROW (see §4 hybrid recommendation), but as the whole artifact, the scorecard loses too much information.

### 2.2 Mid-length founder audit + roadmap

**Canonical exemplars.**
- **Kalungi 95-Point B2B SaaS Marketing Audit** (kalungi.com/blog/how-to-b2b-saas-marketing-audit, kalungi.com/audit) — the practitioner reference for mid-length B2B SaaS audits. ~12–20 pages, scorecard plus narrative diagnostics across 10 dimensions plus prioritised next-actions list.
- **Fractional CMO Day-30 deliverable** — the dominant industry shape for engagement-stage audits. Documented across Envizon (envizon.com/blog/the-fractional-cmo-playbook-what-to-expect-in-your-first-90-days), SaaSConsult (saasconsult.co/blog/fractional-cmo-30-60-90-day-plan/), ASP Marketing (asp-marketing.com/blog/fractional-cmo-for-saas), ThinkCap Advisors (thinkcapadvisors.com/post/fractional-cmo-before-series-a), Strategic Pete (strategicpete.com/blog/fractional-cmo-builds-predictable-saas-demand/). The Day-30 deliverable converges across all of these on: ICP doc + audit findings + prioritised 60–90 day roadmap.
- **TripleDart B2B Marketing Audit** (tripledart.com/b2b-marketing/audit) — step-by-step audit template, ~10–15 pages, channel-by-channel narrative plus priority-by-impact summary.
- **ByDefaultCMO Complete Guide to Conduct a B2B Marketing Audit** (bydefaultcmo.com/marketing-audit-system) — operator-grade walk-through that produces ~3,000–4,000 word deliverable.
- **Growth Syndicate audit template** (thegrowthsyndicate.com/resources/marketing-audit) — agency methodology, similar mid-length spine.

**Length convention.** 8–15 pages. 2,000–4,500 words. The Kalungi 95-point audit sits at the upper end; the fractional-CMO Day-30 deliverable sits at the lower end (closer to 2,000–3,000 words because it is a working doc, not a marketing collateral piece). The dominant convergent length is 2,500–3,500 words.

**Structure / sections in order.** Convergent spine across Kalungi, TripleDart, ByDefaultCMO, fractional-CMO playbooks: **(1) Executive summary with named binding constraint + readiness verdict** → **(2) Current-state diagnostic** (5–10 dimensions scored or narratively assessed) → **(3) Stage and ecosystem-fit analysis** (where the company sits on a growth-stage map; what fits the stage and what doesn't) → **(4) Prioritised recommendations** (3–5 priorities, ranked by impact × speed-to-impact) → **(5) 30/60/90 sequencing** (what happens in days 0–30, 31–60, 61–90). Kalungi adds a "quick wins vs. foundational bets" 2x2; the fractional-CMO playbooks add owner + budget + success metric per recommendation.

**Evidence type and density.** Mixed primary and secondary. Cohort analyses (trial-to-paid by month, retention curves), Gong/Chorus call-transcript evidence, analytics-tool screenshots (GA4, HubSpot), heuristic page audits, benchmarks (Bessemer Cloud Index, OpenView SaaS Benchmarks, ProfitWell pricing benchmarks). 1–3 charts. 3–8 evidence citations per audit. Per Patrick Campbell at ProfitWell and Peep Laja at CXL ResearchXL, the discipline is evidence-source triangulation — each claim resting on at least two independent sources.

**Reader persona.** Founder-CEO at pre-Series-B B2B SaaS OR fractional/interim CMO Day-30 deliverable. Time budget: 30–60 minutes, often consumed Tuesday afternoon between sales calls, with the goal of committing to 1–2 bets by Friday's leadership meeting. The reader has runway pressure and skepticism — they have read generic audits before and unsubscribed. Decision shape: **commit 1–2 bets for next 30 days with named owner + budget + success metric**.

**Recommendation specificity.** The fractional-CMO playbook standard: each top recommendation specifies action + owner + budget envelope + timeline + success metric tied to current baseline. The Day-30 deliverable's recommendations are the gate to Day-60 work — they are commitments the engagement will execute.

**Failure modes.** (a) Audit-bloat — drift from 3,000 words toward 8,000+ as the writer hedges with "consider also" sections; the audit becomes unreadable in the 30-minute Tuesday window. (b) Recommendations-count-gaming — 8+ recommendations of equal weight, no prioritisation; founder can't commit, defaults to none. (c) Framework-citation-as-substitute-for-analysis — every section opens with the framework name (AARRR / Four Fits / ICE / North Star) without earning the citation. (d) Generic playbook (the "ten-page PDF that could apply to any business" failure, named directly by McKee Creative and Helen Cox Marketing). (e) Vanity-metric headlines — "impressions up 40%" as a top finding. (f) Always-recommend-more-marketing — no upstream-constraint branch even when evidence points at PMF / pricing / retention.

**AI-generation difficulty.** Medium. The length and structure are well within LLM range. The substantive challenges are: (1) producing the named binding constraint defensibly (requires fixture-specific evidence reading, not generic playbook), (2) producing recommendations with concrete owners + budgets + success metrics (requires understanding of the client's team capacity), (3) refusing best practices on stage grounds (requires the model to know what to NOT recommend, which is harder than knowing what to recommend), (4) surfacing upstream constraints (requires the model to be willing to recommend its own engagement smaller). The current `marketing_audit` lane fixtures (per project memory: VideoProjectService brief-fallback fixtures; first cohort Anthropic, DWF, Perplexity, Klinika) are within this shape's range.

### 2.3 Domain teardown (single-dimension deep audit)

**Canonical exemplars.**
- **Bell Curve / Demand Curve paid-acquisition audit** (bellcurve.com, demandcurve.com/growth/intro) — the practitioner standard for paid-channel audits. Audit-then-strategy methodology; explicitly fixes structural problems before scaling spend. Length: 15–30 pages depending on engagement scope.
- **Foundation Inc / Ross Simmonds content audit** (foundationinc.co) — "create once, distribute forever" philosophy. Content audits typically run 20–40 pages with per-piece evaluation (intent-classification, performance, distribution status, repurposing opportunity).
- **Animalz content audit** (animalz.co/blog/content-marketing-strategy) — editorial-first content audit. ~15–25 pages typically.
- **ProfitWell pricing audit (Patrick Campbell)** — Acquired podcast interview (acquired.fm/episodes/pricing-everything-you-always-wanted-to-know-but-were-afraid-to-ask-with-profitwell-ceo-patrick-campbell), Intercom interview (intercom.com/blog/podcasts/profitwells-patrick-campbell-on-the-art-and-science-of-pricing/). Pricing audits typically 20–40 pages: value-metric analysis + packaging structure + price-point research (Van Westendorp PSM, conjoint analysis) + expansion-revenue cohorts. The most rigorous of the domain teardowns.
- **Wynter messaging-resonance audit (Peep Laja)** (wynter.com/solutions/messaging-resonance-audit) — B2B messaging audit grounded in ICP panel research. 10–20 pages of resonance scoring + verbatim ICP feedback + recommended messaging directions.
- **CXL ResearchXL CRO audit (Peep Laja)** (cxl.com/conversion-rate-optimization/how-to-create-a-cro-process-by-peep-laja/) — six-step Conversion Research model (Heuristic + Technical + Digital Analytics + Qualitative Survey + User Testing + Mouse Tracking). 20–40 pages, methodologically the most rigorous CRO audit reference in the operator community.

**Length convention.** 15–40 pages depending on domain depth. 4,000–12,000 words. Pricing audits and CRO audits sit at the upper end (because they require triangulated evidence); content audits and paid-acquisition audits sit in the middle.

**Structure / sections in order.** Domain-specific but with a convergent meta-spine: methodology disclosure → current-state inventory → diagnostic analysis with multi-source triangulation → benchmark comparison → prioritised recommendations with experimental design. The CXL ResearchXL six-step model is the methodological gold standard the others all converge toward.

**Evidence type and density.** Heavy. Per-piece scoring (content), per-channel CAC analysis (paid), per-segment willingness-to-pay (pricing), per-page heuristic + analytics + qualitative + user-test triangulation (CRO), per-message ICP-panel resonance scoring (messaging). Citation count: dozens per audit. Charts: 5–15 per audit.

**Reader persona.** Head of Growth / Director of Marketing / specialist marketing lead at Series-B-or-later, OR fractional specialist engaged for a domain-specific deliverable. Time budget: 2–4 hours, read in multiple sittings, often with a follow-up workshop. Decision shape: re-architect the named function — replace the pricing model, restructure the content engine, replatform the website, replace the paid agency.

**Recommendation specificity.** Methodologically rigorous experimental designs. Each recommendation specifies hypothesis + variant + sample size + duration + success metric. The Wynter messaging audit, e.g., recommends specific message variants to test in specific channels with specific success thresholds.

**Failure modes.** (a) Domain narrowness without context — the pricing audit that ignores the company's positioning, the content audit that ignores distribution mechanics. (b) Methodology theatre — long methodology sections that don't actually triangulate. (c) Recommendations too granular for the stage — Van Westendorp PSM analysis recommended to a $500k-ARR company with no statistical-power baseline.

**AI-generation difficulty.** Hard. Each domain teardown requires specialist methodology (PSM / conjoint for pricing, Heuristic + Technical + Digital Analytics + Qualitative + User Testing + Mouse-Tracking triangulation for CRO, ICP-panel research for messaging) that LLMs cannot perform without retrieval-augmented data infrastructure. The `marketing_audit` lane in its current form is not equipped for domain-teardown output.

**Why this shape doesn't fit the lane.** Fixture clients span domains (paid + content + pricing + positioning + sales motion + retention). Locking the lane to one domain teardown forces the workflow to pick a domain per fixture, which adds upstream classification complexity and multiplies judge surface area. The mid-length founder audit (§2.2) covers the breadth at the expense of per-domain depth; that's the right trade for this lane.

### 2.4 Slide deck / board-ready audit

**Canonical exemplars.**
- **ANA Marketing Maturity Assessment** (ana.net) — Association of National Advertisers framework, board-ready deck format.
- **AMA Marketing Effectiveness frameworks** (ama.org) — American Marketing Association assessment frameworks.
- **Agency-of-record annual reviews** (e.g., AKQA, Wieden+Kennedy, R/GA template decks) — 20–40 slides reviewing the year's marketing effectiveness against the brief.
- **McKinsey marketing-effectiveness reviews** — deck format, executive-committee or board-level consumption. The McKinsey Performance Marketing benchmarks (mckinsey.com/capabilities/growth-marketing-and-sales) are the closest published anchor.
- **Bain Customer Strategy reviews** (bain.com/insights/topics/customer-strategy/) — similar deck-based pattern.
- **Marketing Profs / CMI annual benchmark decks** — content marketing benchmark decks (e.g., CMI's annual B2B Content Marketing Benchmarks at contentmarketinginstitute.com/research/).

**Length convention.** 20–40 slides. The slide-density convention is 50–150 words per slide max, with one chart or visual per slide. Total word count: 1,000–3,000 words distributed across slide bullets.

**Structure / sections in order.** Executive-deck convention: cover + agenda → 2–3 slide executive summary → state-of-marketing diagnostic (5–10 slides, one dimension per slide) → benchmark comparison (3–5 slides) → strategic recommendations (3–5 slides) → 12-month roadmap (3–5 slides) → asks/decisions required (1–2 slides). The "ask" slide at the end is the load-bearing element for board-ready decks; everything before it is context for that ask.

**Evidence type and density.** Chart-heavy. Benchmark comparisons against industry data (Bessemer, OpenView, CMI, eMarketer, Gartner CMO survey). Per-slide takeaway in bold at the top, evidence below. Citations footnoted, not inline.

**Reader persona.** CMO presenting to executive committee or board; agency CEO presenting to client CMO; consulting partner presenting marketing-effectiveness review. Time budget: 30–60 minute presentation slot, deck reviewed in advance by some readers. Decision shape: organisational realignment, budget envelope shift for the next fiscal year, agency replace/retain.

**Recommendation specificity.** Strategic-level decisions framed as asks. "Approve $X budget reallocation from channel A to channel B." "Replace agency-of-record." "Hire VP of Marketing." Not tactical 30-day experiments.

**Failure modes.** (a) Slide-density Goodhart — bullets stuffed beyond readability to compress more content per slide; deck becomes unreadable while looking impressive in a PDF view. (b) Framework-deck templating — every slide opens with a framework name (Porter's Five Forces, Four Fits, AARRR), creating consulting-deck theatre. (c) "Marketing is doing fine" deck — agency presenting its own work, no genuine diagnostic, all green scorecards. (d) Vanity-metric deck — impressions / reach / share-of-voice as headline metrics; the Marketoonist cartoon on vanity-metric decks is the canonical reference.

**AI-generation difficulty.** Medium-hard. The visual rhetoric of board decks is hard for LLMs to produce credibly without a deck-rendering layer; the prose can be generated but the slide-layout, chart-design, and visual hierarchy require either a templating system or human design. Current `marketing_audit` lane output is markdown/prose, not slide-format; producing a deck-format audit would be a substrate change, not a judge change.

**Why this shape doesn't fit the lane.** (1) Deck-format scoring is a different rubric problem (visual rhetoric, slide-density, chart quality, narrative flow under presentation constraints). Folding it into the same rubric as prose audits would force the judge to evaluate two artifact types with one rubric — central-tendency collapse. (2) The reader (CMO at Series-C+ presenting to board) is not the locked v0 spec reader (founder-CEO at pre-Series-B). (3) Existing fixtures are prose, not deck. Defer deck-format audits to a possible future sibling lane.

### 2.5 Notion / live-doc operating audit

**Canonical exemplars.**
- **Lenny's Newsletter operating templates** (lennysnewsletter.com) — Lenny Rachitsky and guest operators publish Notion templates for growth audits, ICP docs, channel reviews, OKR templates. The "growth lanes" framework with Dan Hockenmaier (First Round Review) is documented as a Notion-friendly template.
- **Reforge teardown templates** (reforge.com) — Brian Balfour's Reforge ships templates as Notion-friendly docs for member operators to adapt. The Four Fits framework lives as a working doc, not a one-off audit.
- **MKT1 playbooks** (mkt1.co, mkt1newsletter.com) — Emily Kramer and Kathleen Estreich publish their B2B SaaS marketing operating system as a series of inter-linked working docs.
- **Demand Curve school templates** (demandcurve.com) — operator-facing templates for paid channels, content, lifecycle.
- **Coda / Notion published growth-team operating systems** — emerging shape; teams publish their entire marketing-ops as a live, public-or-shared Notion workspace (e.g., Linear's published handbook, GitLab's marketing handbook at about.gitlab.com/handbook/marketing/).

**Length convention.** Variable but distributed across pages. A growth-team Notion workspace can be hundreds of pages, but each individual page is short (300–800 words). The artifact is the link tree, not any single page.

**Structure / sections in order.** Page tree typically: ICP + positioning (top-level) → channels (paid, content, lifecycle, partnerships, community, sales-marketing) → experiments-in-flight → benchmarks → playbooks → team. The CXL ResearchXL six-step model and Reforge growth-loops framework typically appear as embedded reference pages rather than load-bearing structure.

**Evidence type and density.** Link-rich, embedded-dashboard-heavy. Each page typically embeds 1–3 dashboards (Mixpanel, Amplitude, GA4, HubSpot) live, plus links to source materials (Gong calls, customer interviews, market research).

**Reader persona.** In-house growth team (head of growth + 2–10 marketers). Time budget: ongoing consumption, not single-session. Decision shape: rolling operational reprioritisation — what experiments to run this sprint, what to deprioritise, where to invest hiring.

**Recommendation specificity.** Embedded in the operating system itself — recommendations are work items, not deliverables. The audit is not a separate artifact; the audit is the ongoing state of the operating doc.

**Failure modes.** (a) Link rot — pages that reference outdated benchmarks or removed dashboards. (b) Page proliferation — too many sub-pages, no synthesis layer, team can't find what they need. (c) Aspirational templates not actually used — Notion docs that look great but the team operates from email and Slack.

**AI-generation difficulty.** Easy structurally (Notion-compatible markdown is in LLM range), hard substantively (the audit value of a Notion workspace is in the live data embedded, which requires retrieval-augmented infrastructure).

**Why this shape doesn't fit the lane.** Current substrate produces single-artifact prose output, not a multi-page link tree. Notion live-doc audits are a different product, not a different form factor of the same artifact. Defer to possible future lane / product surface.

### 2.6 Audit dashboard / digest (automated)

**Canonical exemplars.**
- **HubSpot Marketing Hub Health / Website Grader** (hubspot.com/website-grader).
- **Semrush Site Audit** (semrush.com/siteaudit/) — automated SEO + site-health digest.
- **Ahrefs Site Audit** (ahrefs.com/site-audit) — same shape.
- **Improvado dashboards** (improvado.io) — marketing-ops dashboards with auto-generated narrative summaries.
- **Google Search Console / GA4 native insights** — automated insight cards in the GA4 / GSC UI.
- **Sprout Social, Hootsuite analytics digests** — social-listening + performance automated digests.

**Length convention.** Variable, but each individual finding is bullet-format (1–2 sentences). Total length: 10–50 findings per audit run, aggregated as dashboard view or PDF export.

**Structure / sections in order.** Per-finding card: severity flag (red/yellow/green or 1–100 score) → finding statement → impact estimate → recommended fix → "learn more" link. Sometimes grouped by category (technical SEO, content, links, performance).

**Evidence type and density.** Telemetry-only. Crawler output, log analysis, third-party API data (Google Search Console, Google Ads, Meta Ads). No qualitative evidence, no benchmarks beyond automated comparison.

**Reader persona.** Marketing-ops analyst, SEO specialist, junior marketer. Time budget: 5–30 minutes scanning, daily-to-weekly cadence. Decision shape: tactical fix-list triage — which findings to fix this week, which to monitor, which to ignore.

**Recommendation specificity.** Tactical fix-instructions ("fix 47 broken links," "compress 12 images >500KB," "add meta description to 23 pages"). Operational, not strategic.

**Failure modes.** (a) Finding-count gaming (some tools intentionally generate hundreds of low-severity findings to justify the SaaS subscription value). (b) No prioritisation — every finding shown with equal weight. (c) False-positive heavy — fixing the findings doesn't materially move outcomes.

**AI-generation difficulty.** N/A — already SaaS-commodified by HubSpot, Semrush, Ahrefs, Improvado. No room for LLM-generated value here.

**Why this shape doesn't fit the lane.** Already commodified. Lane has nothing to add. Reject.

---

## 3. Cross-shape synthesis — decision-format mapping

The six shapes map across two axes the operator community recognises: **engagement depth** (one-off skim → full retainer) and **reader seniority/specialism** (founder/CEO → in-house specialist team).

|                        | Founder-CEO (10-min skim)         | CMO / fractional CMO (60-min review)         | In-house growth team (ongoing)               |
|------------------------|-----------------------------------|----------------------------------------------|----------------------------------------------|
| **Pre-engagement / diagnostic** | Exec scorecard (§2.1)   | Mid-length founder audit (§2.2)              | Notion live-doc starter (§2.5)               |
| **Mid-engagement / strategic**  | (mid-length condensed) | Mid-length audit + 30/60/90 roadmap (§2.2)   | Domain teardown (§2.3) on chosen function    |
| **Board / annual review**       | (deck condensed)       | Slide deck (§2.4)                            | (slide deck distilled)                       |
| **Ongoing ops**                 | (dashboard summary)    | (dashboard summary)                          | Dashboard / digest (§2.6)                    |

Three shapes (exec scorecard, mid-length founder audit, slide deck) all serve the strategic-decision class, ordered by reader seniority and engagement depth. Two shapes (Notion live-doc, dashboard) serve the operational-decision class. Domain teardowns are a different product entirely — single-dimension specialist deliverables, not whole-function audits.

**Practitioner consensus on shape selection.** Multiple sources converge on a layered model echoing Klue's CI layering (klue.com): the readiness one-pager is the gate, the mid-length audit is the strategic deliverable, the domain teardown is the specialist follow-up, the dashboard is the ongoing ops surface, the deck is the board-translation, and the Notion live-doc is the in-house operating system. The shapes are not substitutes; they are different products at different points in the engagement lifecycle.

The shape collision the `marketing_audit` lane risks is the same one Bell Curve, Demand Curve, and Kalungi all warn against: producing a Frankenstein artifact that is too thin for the strategic decision (scorecard-shaped) and too thick for the gate decision (audit-shaped) — landing as neither. The current v0 spec does not lock this.

**Decision-class scope for the lane: mid-engagement strategic decision** — the founder-CEO or fractional CMO needs to commit 1–2 bets for the next 30 days with named owner + budget + success metric. That maps cleanly to the mid-length founder audit + roadmap shape (§2.2). Other shapes are out of scope for v1.

---

## 4. Recommendation for marketing-audit lane artifact shape

**Recommendation: option (b) — one hybrid shape, mid-length founder audit + roadmap as the spine, with exec-scorecard verdict opening and domain-teardown-grade evidence on the named binding constraint.**

**Operational form factor:**
- **Length: 2,000–4,500 words.** Hard floor at 2,000 (below this, evidence triangulation against MA-1's 2-source requirement becomes infeasible). Hard ceiling at 4,500 (above this, audit-bloat Goodhart sets in; founder can't consume in the 30-minute Tuesday window).
- **Sections (5 locked, in order):**
  1. **Readiness verdict + named binding constraint** — scorecard-style verdict in the opening, but with named-constraint specificity (not generic readiness yes/no). "Trial-to-paid is 1.8% vs SaaS median 6%; this is the binding constraint, not lead volume." ~150–300 words. Borrows the Kalungi One-Page format's verdict-at-top discipline.
  2. **Stage diagnostic + ecosystem-fit analysis** — name the stage (pre-traction / traction / scaling / expansion) with at least one observable anchor (ARR band, retention cohort, channel-fit signal). Refuse at least one stage-inappropriate best practice. ~400–700 words. Borrows the Kalungi growth-stages framework and Brian Balfour's Four Fits.
  3. **Current-state diagnostic across relevant dimensions** — narrative, not exhaustive scorecard. Cover only the dimensions where evidence supports a real finding; skip dimensions where there's no fixture data. Triangulate evidence per CXL ResearchXL discipline (≥2 sources per claim). ~600–1,500 words. This is the section that carries domain-teardown-grade evidence depth on the named binding constraint specifically — not on every dimension.
  4. **Upstream-vs-marketing check** — explicit branch. If evidence points at PMF / pricing / retention / ICP / sales motion as the real constraint, name it directly and sequence marketing recommendations behind the upstream fix. If marketing IS the constraint, defend that claim with evidence. ~200–500 words. Borrows Sean Ellis PMF survey discipline and Kalungi's marketing-readiness audit pattern.
  5. **Prioritised 30/60/90 sequencing** — 1–3 specific Day-30 commitments with action + owner + budget envelope + timeline + success metric tied to baseline. Day 60 and Day 90 commitments lighter (sequenced, not over-specified — the Day-30 results inform what 60/90 should be). Optional explicit "cuts" (what to stop or defer). ~400–800 words. Borrows the fractional-CMO 30/60/90 cadence (Envizon, SaaSConsult, ASP, ThinkCap).

- **Evidence density:** ≥2 evidence sources per major claim (binding constraint, stage diagnostic, upstream/marketing call). 1–3 charts or tables permitted. 5–10 citations total. Citations name the source (cohort analysis on slide X, 12 Gong calls, Bessemer SMB CAC payback benchmark).

- **Recommendation count:** 1–3 Day-30 commitments. Hard ceiling at 3. Recommendations-count-gaming (8+ flat list) penalised by `structural_gate` and discriminated against by MA-2.

**Reasoning.**

The v0 spec at `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md` defines Reader as "founder-CEO or founder-CMO hybrid at pre-Series-B B2B SaaS or fractional/interim CMO at $5M–$50M ARR." Success is defined as "by Friday they walk into the leadership meeting with a named binding constraint, one concrete experiment with owner+budget+success-metric, and Day-30/60/90 sequencing." These point unambiguously to the mid-length founder audit + roadmap shape (§2.2) and away from the other five:

- **Reject pure exec scorecard (§2.1).** Too thin for MA-1's 2-source evidence requirement and MA-3's revenue-mechanism chain.
- **Reject pure domain teardown (§2.3).** Fixture clients span domains; locking to one is wrong. Domain-teardown evidence depth on the named binding constraint specifically (in section 3 of the recommended spine) preserves the depth where it matters.
- **Reject slide deck (§2.4).** Different reader (CMO presenting to board), different visual-rhetoric rubric problem, different fixture format.
- **Reject Notion live-doc (§2.5).** Different substrate (link tree, not single artifact). Defer to possible future product surface.
- **Reject dashboard (§2.6).** Already SaaS-commodified.
- **Accept hybrid mid-length founder audit + roadmap.** Preserves the founder-readable forcing-function (commit 1–2 bets by Friday) while requiring evidence depth on the binding constraint and stage analysis. Matches the v0 Success spec's named exemplars: Kalungi 95-point as quality ceiling, Bell Curve/Demand Curve audit-then-strategy as methodological floor, fractional-CMO Day-30 as practitioner template, Patrick Campbell pricing audits and Wynter messaging audits as evidence-depth anchors. The v0 spec already names this hybrid implicitly via §2's exemplar list — option (b) just makes it explicit.

---

## 5. Shape-drift Goodhart surfaces specific to marketing-audit

The CI taxonomy surfaced shape-drift Goodhart (workflow learning to look-like-teardown for CI-3, look-like-war-game for CI-2). The marketing-audit equivalent has three distinct surfaces the v0 spec does not catch:

**(a) Audit-bloat.** Workflow learns that longer audits with more sections score higher on shallow proxies (perceived comprehensiveness). Drift from 3,000 words → 8,000+ words across generations. Fix: `structural_gate` enforces 2,000–4,500 word band hard, with penalty above 5,500.

**(b) Recommendations-count-gaming.** Workflow learns that more recommendations look like more value. Drift from 2–3 prioritised recommendations → 8+ recommendations of equal weight. Founder reads, finds nothing prioritised, commits to none. Documented as the canonical failure across Kalungi, TripleDart, ByDefaultCMO. Fix: `structural_gate` enforces ≤3 Day-30 recommendations + MA-2 outcome question discriminates against templated owner/budget/timeline boilerplate.

**(c) Framework-citation as substitute for analysis.** Workflow learns that naming Sean Ellis / AARRR / Four Fits / ICE / North Star / Lenny growth loops / CAC payback / ResearchXL signals expertise. Drift from analysis-with-frameworks-as-toolkit → framework-name-drops-with-shallow-analysis. The Phase 4 pathology rolled back at `c76f051` (commit `698e658`) is the precedent. Fix: design-guide constraint already in place (no framework names in rubric prose); add `structural_gate` banned-phrase list extension (Helmer-style: "AARRR funnel," "ICE-prioritised," "Four Fits analysis," "North Star Metric" — when present without supporting analysis).

**(d) Stage-mechanical-rotation.** Workflow learns that mentioning "you are at stage X" scores well on MA-4. Drift: every audit mechanically rotates through pre-traction/traction/scaling/expansion regardless of fixture. Fix: MA-4's anchor requirement (at least one observable anchor — ARR band, retention cohort signal, channel-fit signal) and at least one explicit refusal on stage grounds.

**(e) Upstream-default-no.** Workflow learns that the upstream branch is high-cost (makes its own recommendations smaller) and defaults to "no, it's marketing." Drift: every audit's upstream-vs-marketing section concludes "marketing is the constraint" by default. Fix: MA-5's outcome-question requirement (evidence-on-the-merits, not default-answer) and `structural_gate` requirement that the upstream section is present and reasoned, not skipped.

**(f) Vanity-metric-headline drift.** Workflow learns that "impressions up 40%" sounds confident and headline-worthy. Drift: vanity metrics promoted to top-line findings. Eric Ries / Marketoonist named the pathology. Fix: MA-3 outcome-question discriminates against vanity headlines + `structural_gate` extension flagging headline findings on impressions/reach/follower-count/raw-pageviews when not paired with downstream conversion-metric chain.

**(g) Generic-playbook drift (the "ten-page-PDF-that-could-apply-to-any-business" failure).** Workflow learns that generic recommendations are safer (low-confidence-but-defensible). Drift: audits become indistinguishable across fixtures. Named directly by McKee Creative (mckeecreative.store/what-a-marketing-audit-actually-reveals-and-why-most-small-businesses-skip-it/) and Helen Cox Marketing (helencoxmarketing.co.uk). Fix: MA-1's named-constraint-with-2-evidence-sources requirement + cross-fixture variance check at evaluation time (the same audit reading identically across 3+ unrelated fixtures should drop the variance flag).

---

## 6. Specific edits to marketing-audit v0 spec

Based on the recommended hybrid shape, three concrete edits to `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md`:

**Edit 1 — Insert §1.5 "Artifact shape (LOCKED)" between §1 Reader and §2 Success.** Name the artifact shape explicitly:

> The lane produces a **mid-length founder audit + 30/60/90 roadmap** (≈ 2,000–4,500 words, 5-section spine: Readiness-verdict-plus-named-binding-constraint / Stage-diagnostic / Current-state-diagnostic / Upstream-vs-marketing-check / Prioritised-30-60-90-sequencing) with **exec-scorecard-style verdict in the opening** (Kalungi readiness-audit discipline) and **domain-teardown-grade evidence depth on the named binding constraint specifically** (CXL ResearchXL evidence-triangulation discipline applied to the binding-constraint section only — not exhaustively across every dimension) and **fractional-CMO 30/60/90 sequencing** (1–3 Day-30 commitments with action + owner + budget envelope + timeline + success metric). It is NOT a one-page readiness scorecard, NOT a full domain teardown, NOT a board-ready slide deck, NOT a Notion live-doc, NOT a tool-generated dashboard digest. Outputs drifting toward any of those shapes should be penalised by `structural_gate`, not by criteria 1–5.

**Edit 2 — Insert §3c "Shape-drift Goodhart and AI-specific failure surfaces" extending the existing §3 failure section.** Catalogue the seven failure modes the taxonomy surfaces (§5 above), with the named-source citations.

**Edit 3 — Append to §8 Open questions:** add a `structural_gate` expansion section listing the shape-conformance checks (word-count band 2,000–4,500, 5-section presence, ≤3 Day-30 recommendations, vanity-metric headline flag, framework-name banned-phrase list extension, upstream-section-present-and-reasoned check) and the empirical-validation scope note (the hybrid form is grounded in B2B SaaS practitioner conventions; non-SaaS fixtures — services, regulated industries, B2C — may need shape adjustments and trigger lane re-validation).

These edits do not change any criterion text. They lock the artifact shape so the next 50-generation evolution cannot drift across shapes between iterations. They preserve the v0 redundancy-check item already in §8 (MA-1 and MA-4 may correlate) and the existing-lane-wiring item.

---

## 7. Open questions

1. **B2B SaaS first-cohort overfit.** The hybrid shape is research-grounded against B2B SaaS practitioner conventions (Kalungi, Bell Curve, Demand Curve, ProfitWell, Wynter, CXL, fractional-CMO playbooks). First-cohort fixtures include Anthropic (AI-lab), DWF (legal services), Perplexity (AI-lab), Klinika (healthcare aesthetic dermatology). The B2B-SaaS-conventions anchor may need adjustment for the legal and healthcare fixtures. Re-validation trigger: any fixture from a non-SaaS vertical should prompt a re-validation pass on the §1.5 form-factor lock.
2. **Mid-length founder audit vs Day-30-deliverable distinction.** Both shapes converge on the same word count and section spine, but the engagement context differs (pre-engagement diagnostic vs mid-engagement working doc). Whether MA-2's 30/60/90 sequencing is hard-required or context-dependent affects whether some fixture types (pre-engagement readiness audits) get unfairly penalised. Resolve via fixture validation.
3. **MA-1 + MA-4 redundancy already flagged.** Per the v0 spec §8 open question 3, audits that locate stage often also name the constraint correctly. Empirical redundancy check needed (5 fixtures × 5 criteria × 3 panel models per design-guide §5 protocol). Most-likely-to-merge pairs after taxonomy work: MA-1 (binding constraint) ↔ MA-4 (stage map); MA-3 (revenue mechanism) ↔ MA-5 (upstream constraint).
4. **Domain-teardown depth on binding constraint section: how is it enforced?** "Domain-teardown-grade evidence depth on the named binding constraint specifically" is a structural ambition. `structural_gate` cannot enforce semantic evidence depth; that's MA-1's job. Risk: the spec ends up over-claiming on evidence depth without enforceable check. Consider adding a `structural_gate` check that the binding-constraint section names ≥2 specific evidence sources by name (named cohort analysis, named Gong/Chorus dataset, named benchmark source).
5. **Vertical-specific evidence sources.** The v0 spec's evidence sources (Gong call transcripts, cohort analyses, SaaS benchmarks) are B2B-SaaS-flavored. Legal-services fixtures (DWF) would draw on different evidence sources (Chambers rankings, lateral-flight trackers, deal-database analysis); healthcare fixtures (Klinika) on still others (local-market patient flow data, vendor-contract analytics, referral-network mapping). Vertical-specific evidence-source palettes may need documenting.
6. **Subagent / lane-fork for the other shapes.** Exec scorecard, slide deck, Notion live-doc, and domain teardown could each become sibling lanes if/when fixture clients ask for them. Not for v1. Revisit when first cohort completes and second cohort onboards.
7. **Calibration set diversity.** Per design-guide §15, the calibration set should be stratified across artifact types AND quality levels. The marketing-audit calibration set needs both founder-CEO-audience fixtures AND fractional-CMO-Day-30 fixtures, both score-1 exemplars (Kalungi-grade audits) and score-0 examples (generic ten-page-PDF failures). Build before locking the criteria via empirical redundancy check.

---

## 8. Sources

**Exec scorecard / readiness one-pager:**
- [Kalungi One-Page Marketing Readiness Audit for SaaS Founders](https://www.kalungi.com/blog/one-page-marketing-readiness-audit-for-saas-founders)
- [Kalungi 95-Point B2B Marketing Audit](https://www.kalungi.com/audit)
- [MaRS Marketing Readiness Assessment](https://www.marsdd.com/mars-library/marketing-readiness/)
- [HubSpot Website Grader](https://website.grader.com/)
- [TripleDart B2B Marketing Audit (1-page version)](https://www.tripledart.com/b2b-marketing/audit)

**Mid-length founder audit + roadmap:**
- [Kalungi How to Conduct a B2B Marketing Audit](https://www.kalungi.com/blog/how-to-b2b-saas-marketing-audit)
- [Kalungi SaaS Growth Stages](https://www.kalungi.com/blog/saas-growth-stages)
- [Envizon Fractional CMO Playbook: First 90 Days](https://www.envizon.com/blog/the-fractional-cmo-playbook-what-to-expect-in-your-first-90-days)
- [SaaSConsult Fractional CMO 30-60-90 Day Plan](https://saasconsult.co/blog/fractional-cmo-30-60-90-day-plan/)
- [ASP Marketing Fractional CMO for SaaS](https://asp-marketing.com/blog/fractional-cmo-for-saas)
- [ThinkCap Advisors Fractional CMO Before Series A](https://www.thinkcapadvisors.com/post/fractional-cmo-before-series-a)
- [Strategic Pete How a Fractional CMO Builds Predictable SaaS Demand](https://strategicpete.com/blog/fractional-cmo-builds-predictable-saas-demand/)
- [TripleDart B2B Marketing Audit Step-by-Step](https://www.tripledart.com/b2b-marketing/audit)
- [ByDefaultCMO Complete Guide to B2B Marketing Audit](https://www.bydefaultcmo.com/marketing-audit-system)
- [Growth Syndicate Marketing Audit Resource](https://www.thegrowthsyndicate.com/resources/marketing-audit)

**Domain teardown (single-dimension deep audit):**
- [Bell Curve Agency](https://www.bellcurve.com/)
- [Demand Curve Growth Guide](https://www.demandcurve.com/growth/intro)
- [Foundation Inc / Ross Simmonds](https://foundationinc.co/)
- [Animalz Content Marketing Strategy](https://www.animalz.co/blog/content-marketing-strategy)
- [ProfitWell Patrick Campbell Pricing — Intercom interview](https://www.intercom.com/blog/podcasts/profitwells-patrick-campbell-on-the-art-and-science-of-pricing/)
- [ProfitWell Patrick Campbell Pricing — Acquired episode](https://www.acquired.fm/episodes/pricing-everything-you-always-wanted-to-know-but-were-afraid-to-ask-with-profitwell-ceo-patrick-campbell)
- [Wynter Messaging Resonance Audit](https://wynter.com/solutions/messaging-resonance-audit)
- [CXL ResearchXL CRO Process by Peep Laja](https://cxl.com/conversion-rate-optimization/how-to-create-a-cro-process-by-peep-laja/)
- [CXL How to Come Up with More Winning Tests Using Data](https://cxl.com/blog/how-to-come-up-with-more-winning-tests-using-data/)

**Slide deck / board-ready audit:**
- [ANA Association of National Advertisers](https://www.ana.net/)
- [AMA American Marketing Association](https://www.ama.org/)
- [McKinsey Growth, Marketing & Sales](https://www.mckinsey.com/capabilities/growth-marketing-and-sales/)
- [Bain Customer Strategy](https://www.bain.com/insights/topics/customer-strategy/)
- [Content Marketing Institute B2B Research](https://contentmarketinginstitute.com/research/)

**Notion / live-doc operating audit:**
- [Lenny's Newsletter](https://www.lennysnewsletter.com/)
- [Brian Balfour Four Fits](https://brianbalfour.com/four-fits-growth-framework)
- [Reforge Blog](https://www.reforge.com/blog/four-fits-in-action)
- [MKT1 Newsletter (Emily Kramer / Kathleen Estreich)](https://mkt1.substack.com/)
- [GitLab Marketing Handbook](https://about.gitlab.com/handbook/marketing/)
- [Lenny + Hockenmaier Customer Acquisition Lanes](https://review.firstround.com/drive-growth-by-picking-the-right-lane-a-customer-acquisition-playbook-for-consumer-startups/)

**Audit dashboard / digest:**
- [HubSpot Website Grader](https://website.grader.com/)
- [Semrush Site Audit](https://www.semrush.com/siteaudit/)
- [Ahrefs Site Audit](https://ahrefs.com/site-audit)
- [Improvado](https://improvado.io/)

**Frameworks the judge reasons with (NOT in rubric prose):**
- [Sean Ellis PMF Survey](https://www.zonkafeedback.com/templates/sean-ellis-product-market-fit-survey-template)
- [Sean Ellis Lenny's Newsletter Interview](https://www.lennysnewsletter.com/p/the-original-growth-hacker-sean-ellis)
- [ICE Framework](https://growthmethod.com/ice-framework/)
- [Brian Balfour Four Fits](https://brianbalfour.com/four-fits-growth-framework)
- [Brian Balfour Why Product Market Fit Isn't Enough](https://brianbalfour.com/essays/product-market-fit-isnt-enough)
- [Dave McClure AARRR Pirate Metrics](https://mcgaw.io/wp-content/uploads/2016/04/PirateMetrics_Final.pdf)
- [PostHog AARRR Analysis](https://posthog.com/product-engineers/aarrr-pirate-funnel)
- [Eric Ries Vanity vs Actionable Metrics — Tim Ferriss original post](https://tim.blog/2009/05/19/vanity-metrics-vs-actionable-metrics/)
- [Improvado Vanity Metric Synthesis](https://improvado.io/blog/what-is-a-vanity-metric)
- [Tomasz Tunguz SaaS Startup Benchmarks](https://tomtunguz.com/saas-startup-benchmarks/)
- [Bessemer Cloud Computing Metrics](https://www.bvp.com/atlas/cloud-computing-metrics)
- [Andrew Chen Growth Essays](https://andrewchen.com/list-of-essays/)
- [April Dunford Obviously Awesome](https://www.aprildunford.com/obviously-awesome)

**Failure-mode literature (named anti-patterns):**
- [McKee Creative — what a marketing audit actually reveals](https://mckeecreative.store/what-a-marketing-audit-actually-reveals-and-why-most-small-businesses-skip-it/)
- [Helen Cox Marketing — strategic reset](https://helencoxmarketing.co.uk/is-your-marketing-just-noise-why-a-marketing-audit-is-the-strategic-reset-you-need/)
- [Umbrex — common marketing failure modes](https://umbrex.com/resources/what-marketing-is/common-failure-modes-in-marketing/)
- [Marketoonist — vanity metrics cartoon](https://marketoonist.com/2016/02/marketing-vanity-metrics.html)

**Sibling / cross-reference:**
- [docs/research/2026-05-18-ci-artifact-taxonomy.md](../../docs/research/2026-05-18-ci-artifact-taxonomy.md) — companion taxonomy for CI lane, same axis, drove the v3 spec lock
- [docs/research/2026-05-18-judges-domain-marketing-audit.md](../../docs/research/2026-05-18-judges-domain-marketing-audit.md) — domain research for marketing-audit lane (frameworks, anti-patterns, exemplars)
- [docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md](../../docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md) — current v0 spec, target of the §6 edits proposed above
- [docs/rubrics/judge-design-guide.md](../../docs/rubrics/judge-design-guide.md) — canonical design guide, all criteria above conform to its constraints
