---
date: 2026-05-19
type: research deliverable — comprehensive scope mapping
status: complete
topic: full competitive-intelligence surface for a 2026 modern AI-native agency
parent: docs/handoffs/2026-05-17-judge-design-step1-competitive.md
companions:
  - docs/research/2026-05-15-judges-domain-competitive.md
  - docs/research/2026-05-18-ci-vertical-conventions.md
  - docs/research/2026-05-18-ci-artifact-taxonomy.md
  - docs/research/2026-05-18-ci-ai-failure-modes.md
  - docs/research/2026-05-18-ci-decision-format-mapping.md
scope-posture: comprehensive (do NOT scope-reduce); modern-lever bias; multi-vertical (SaaS / AI / agency / service firm / finance / e-commerce); US-primary with Polish first-cohort
---

# Competitive Intelligence — Full Comprehensive Scope for a 2026 Modern Agency Client

## TL;DR

This deliverable maps the **full surface area** of competitive intelligence gofreddy should be able to deliver to a 2026 modern AI-native agency client. The CI v3.4 spec scopes the lane to a single React-cluster hybrid brief (800–2,000 words). That artifact-shape lock is correct as a **judge-stability** decision. It is **wrong as a description of the comprehensive value surface** the agency must be able to deliver. The two are not in conflict: the judge stays narrow; the lane's deliverable can grow much wider; the workflow gains capability without the judge losing discriminating power.

Five claims:

1. **CI is at least 24 axes wide for a 2026 client**, not the 5 (competitor / mechanism / trajectory / trade-off / evidence) that v3.4 surfaces. §1.1–§1.24 below enumerate. Each axis ties to a practitioner-grade source.
2. **Modern CI cuts more than it adds.** Largest leverage is killing late-1990s deliverables — generic SWOTs, Porter Five Forces fill-ins, surface-level feature comparison matrices, Gartner-quadrant theater, 60-page BCG/McKinsey deck shapes, single-source trajectory extrapolations, framework-name slot-fill, benchmark-table-as-strategy. The v3.4 `CI_BANNED_PHRASES` list is a floor; cut surface is much larger.
3. **Modern CI adds 2026-specific axes** that pre-2023 frameworks could not see: AEO presence across engines; distribution-moat comparison; talent-flow inference; 90-day pricing sprints; comparison-page warfare; founder-as-CEO-of-narrative tracking; AI-native competitor anatomy; asymmetric-opportunity identification.
4. **Vertical adjustments are real but bounded.** SaaS / AI-lab / agency / service-firm / finance / e-commerce share the 24-axis surface; they differ in which axes are load-bearing, which evidence sources are CI-grade, what counts as a concrete action, and what time horizons matter. The biggest adjustment is *decision-shape mapping*, not axis selection.
5. **Deliverable architecture should be modular, not monolithic.** Judge-stable hybrid brief stays at 800–2,000 words. The comprehensive deliverable wraps it: executive brief + per-competitor profile cards + trajectory matrix + comparison matrix + watchlist + evidence appendix. The brief is the forcing function; the wrapping is the depth.

**Strongest single recommendation:** the CI lane's evolution-loop judge stays at v3.4's 6 criteria. The lane's deliverable grows to a 5–8 component modular package, with wrap-around components evaluated by `structural_gate` checks (presence, freshness, traceability), not judge criteria. Preserves v3.4 judge-stability work; unlocks comprehensive scope. The two design goals stop fighting.

---

## §1. Full CI surface — 24 axes

This is the comprehensive surface of competitive intelligence that a serious modern agency should be able to deliver. Not all 24 axes appear in every engagement — engagement scoping selects 10–18 of these per client. The point of enumeration is that the lane (and the agency) must be **capable** of all 24, not that the lane should slot-fill all 24 in every output.

### §1.1 Competitor identification + tier ranking

Direct, indirect, and replacement competitors named explicitly, with the **rationale for inclusion** specified. Practitioner standard: Klue's "ranked battlecards" and Crayon's "competitive landscape map" both require the analyst to name *why* each competitor is on the list, distinguishing primary-direct (head-to-head in deals), secondary-direct (same category, different segment), indirect (different category, same buyer JTBD), and replacement (the do-nothing or workaround alternative). Cody Schneider's framing: "your real competitor is what they were doing before you existed" — replacement-competitor analysis is dropped from most CI in practice and is the modern lever.

For 2026, an additional tier: **AI-native disruptors** that didn't exist in the buyer's mental map 18 months ago. Especially load-bearing for agency clients, SaaS, and finance — Anthropic vs Copilot vs Cursor vs Windsurf vs Cline didn't exist as a competitive set in 2023. Klinika-style local-market clients have a different cut: an AI-native disruptor in aesthetic dermatology might be a remote-Rx GLP-1 service vertically intruding on local-injector pricing.

### §1.2 Per-competitor deep profile

For the 3–5 most consequential competitors: product, pricing, positioning, traction signals, funding, hiring, M&A, partnerships, public statements. Practitioner standards: CB Insights "Strategy Teardown" depth on the dominant competitor; Klue "competitor profile cards" lighter touch for tier-2; Crayon's running-profile model for tier-3 (auto-updated, lower depth). For agency clients specifically: a 2026 modern profile must include AI-native attributes (model surface, AEO presence, agent capability, technical-credibility surface).

### §1.3 Trajectory analysis (6–18 months out)

Where each competitor is heading. Forward call backed by ≥2 independent signals — the v3.4 CI-2 criterion. Sources: M&A patterns, hiring patterns (Levels.fyi, LinkedIn, Paraform), product-roadmap inference (changelogs, GitHub commit cadence), earnings-call language analysis, partnership patterns, regulatory positioning, lateral-hire flow. Cody Schneider's distinction: trajectory is not "what they say their roadmap is" — it's "what their hiring + commits + customer-conversation patterns demand they will build next."

Vertical adjustment on time horizon: 6–18 months for B2B SaaS / agency / service / finance; 6–18 weeks for frontier AI (model-release cadence); 12–24 months for legal-services partnership cycles; 4–12 weeks for local healthcare (treatment-cycle, season).

### §1.4 Structural mechanism diagnosis (moat analysis)

For each named competitor advantage: the underlying structural reason it's hard to copy. Hamilton Helmer's 7 Powers — Scale Economies, Network Economies, Counter-Positioning, Switching Costs, Branding, Cornered Resource, Process Power — is the practitioner framework. Used **as a reasoning toolkit**, never named in the deliverable (the framework-name-checking pathology from `c76f051`).

The 2026 modern lever: **distinguish operational effectiveness from sustainable positioning** (Porter's named trap). Most "competitor advantages" identified by CI shops are actually operational-effectiveness gaps that fast-followers can close. The structural-mechanism diagnosis explicitly rejects operational-effectiveness claims unless they pass the "can't or won't replicate" test.

### §1.5 Strategic narrative monitoring (cross-competitor compounds)

Multi-week narrative threads across competitors that compound into market-shaping events. Example: the "AI agents not chat" narrative formed in late 2025 across Anthropic + Cognition + Cursor + LangChain over 8 weeks. Reading individual signals misses it; reading the compound surfaces it. This is what the gofreddy `monitoring` lane is supposed to own structurally; the CI lane references the compound as context for trajectory and recommendation. Practitioner exemplar: Ben Thompson's Stratechery — Aggregation Theory is a compound narrative thesis built across 10+ years of monitoring.

### §1.6 Talent flow tracking

Lateral hires between competitors as a leading indicator. Sources: LinkedIn job-change tracking (commercial: Pirical, Leopard Solutions for legal; Paraform for AI; Levels.fyi for tech), Departures from competitor X to Y signal strategic shifts at both. Specific patterns to track: senior-IC departures (signal organizational dysfunction at the source); cluster departures (3+ in 60 days = signal); founder/executive departures (always significant); reverse-flow (where do they come from?).

The 2026 modern lever: **talent flow predicts product roadmap** at a 6–9 month lag. Anthropic post-training hires → tool-use improvements 6 months later. Stripe vertical-SaaS-platform hires → embedded fintech launches 9 months later. Pirical and Leopard productize this for legal; nothing equivalent exists for SaaS, so the lane must hand-build the inference.

### §1.7 Funding + M&A signals

Funding rounds, valuation, investor composition; M&A activity; rumored acquisitions. Sources: Crunchbase, PitchBook (paid), CB Insights (paid), Axios Pro Rata, Information's deal-tracker, sector-specific (FOCUS Bankers for derm M&A, Citi Hildebrandt for legal). The 2026 modern lever: **investor composition tells the strategic direction**, not just the round size. A growth round led by Tiger Global (price-insensitive growth) vs Founders Fund (contrarian thesis) vs strategic CVC (M&A pipeline) signal different things even at the same dollar amount.

### §1.8 Patent + IP tracking

Patent filings as a moat-construction signal and a roadmap leak. Sources: USPTO public filings, Google Patents, Patbase. Most useful for: hardware companies, AI labs (training-architecture patents), regulated industries. Less load-bearing for SaaS where shipping outpaces patenting. For AI: Anthropic constitutional-AI patents, OpenAI tool-use patents, Google's MoE / MLA architecture work — patent filings often show what's about to ship 12–18 months before launch.

### §1.9 Public discourse tracking

Where competitors are being talked about and how. Sources: X, LinkedIn, Reddit, Hacker News (for technical), Discord/Slack communities, podcast appearances, conference keynote schedules. The 2026 modern lever: **founder X-thread strategy IS competitive positioning** for AI labs and modern SaaS. Aravind Srinivas, Sam Altman, Dario Amodei post strategic positioning publicly. Reading those posts carefully *is* competitive intelligence — both for the lab posting and the labs reading.

Sentiment + volume + topic alone is monitoring-lane territory. CI-lane work is the *strategic inference* from public discourse: what positioning is the competitor staking out? What audience is the competitor optimizing for? What's the "narrative wedge" they're trying to drive into the category?

### §1.10 Win-loss analysis integration

Where the client wins against each competitor; where they lose. Sources: client's own CRM (`won_to`, `lost_to` fields), Gong/Chorus call transcripts, sales-team interviews, post-deal customer surveys (Klue's "win-loss program" is the practitioner reference; Clozd is the dominant SaaS vendor). The 2026 modern lever: **AI-call-recording analytics + AI-driven post-loss-call extraction has dropped the cost of structured win-loss from $50K/quarter (analyst-driven) to ~$2K/quarter (Gong + Claude/Opus 4.7 extraction). Most clients haven't caught up to this** — agency opportunity.

CI deliverable integration: name the deal-level competitor encounter pattern. "We win on Y when buyer asks about Z first." Specific. The brief doesn't have to enumerate every won/lost deal; it names the pattern.

### §1.11 Customer migration tracking

Who's switching where. Sources: LinkedIn job-tracking for buyers (the new CMO who came from a competitor's customer is a buying signal); G2/TrustRadius switching-from filters; Crunchbase customer lists; press-release pattern matching ("Acme deploys Y" announcements); RealSelf review reading for healthcare. Each switch event is two signals: lost-customer at competitor + new-customer at winner.

The 2026 modern lever: **predict-the-switch using AI-extracted signal patterns** (renewal-window timing + competitor activity + buyer LinkedIn movement). Gong has shipped some of this; the agency-side opportunity is integrating across CRM + LinkedIn + competitor-changelog signals.

### §1.12 Pricing intelligence (changes, packaging, discount patterns)

Pricing-page diffs, packaging changes, discount patterns from won/lost deals, list-vs-realized pricing. Sources: Wayback Machine + Crayon for pricing-page archaeology; Visualping for change-detection; OpenView pricing-benchmark reports; ProfitWell pricing intelligence; Patrick Campbell's body of work. The 2026 modern lever: **elite SaaS has moved from annual pricing reviews to 90-day pricing sprints** (per OpenView and SaaS Factor 2025 Playbook). Pricing CI must operate at 90-day cadence, not annual.

For AI-lab pricing: per-token pricing on multiple dimensions (input / output / cached / context-length tiers / vision / audio). Artificial Analysis tracks 356 models across speed × cost × capability simultaneously and is the canonical reference.

### §1.13 Product roadmap inference

What each competitor will ship next, inferred from changelogs, hiring, public statements, partnership patterns, patent filings, conference talks, beta-program announcements. The 2026 modern lever: **AI-native competitors often telegraph roadmap through founder X/podcast appearances** because their primary audience is technical and they recruit through narrative. Listen for: "we're spending a lot of time thinking about X" = X is shipping in 4–8 months. Aravind Srinivas, Sam Altman, Dario Amodei all use this pattern.

For agency clients in legal / healthcare: roadmap inference is *headcount + practice-area + office-location* inference, not product-launch inference. The shape transfers; the substrate doesn't.

### §1.14 Messaging shifts (positioning evolution over time)

How each competitor's positioning has evolved over the last 6–18 months. Sources: home-page diffs (Wayback Machine), category-page diffs, sales-deck leakage (G2, conference recordings), founder messaging on X/LinkedIn. April Dunford's framework — Obviously Awesome / Positioning canvas — is the analytical toolkit (used as a reasoning aid, not named).

The 2026 modern lever: **positioning has shorter half-life than ever** because AEO and AI-search are training on whatever the competitor's current positioning is. A competitor that shifts positioning quietly gets months of AI-search-trained-on-stale-positioning lift before their old position is replaced in retrieval. Watch for: subtle hero-headline shifts; new use-case page additions; testimonial-pattern changes.

### §1.15 Channel-fit analysis per competitor

Which channels each competitor actually wins on. Sources: SimilarWeb (traffic + source mix), Semrush / Ahrefs (organic + paid keyword visibility), Sparktoro (audience + influencer mapping), Tubular (YouTube), Apify-scraped LinkedIn organic reach, podcast-appearance tracking. The 2026 modern lever: **distribution moat is now a primary moat category** for AI-native and modern SaaS, not just a tactical question. Cody Schneider's framing: "every competitor advantage eventually collapses to a distribution-cost question." A competitor with 800K LinkedIn audience and a podcast network owns CAC dynamics that competitors with paid-only acquisition cannot match.

### §1.16 Distribution-moat comparison

(Tightly coupled to §1.15.) Comparing competitors across distribution surfaces explicitly: LinkedIn audience (named founder + company page), X audience, podcast presence (own podcast + frequent guest), founder visibility (speaker circuit, book, newsletter), community depth (Discord/Slack), influencer relationships, organic search dominance, viral coefficient. For agency clients specifically: this analysis is often the **single highest-value CI artifact** because most clients have under-invested in distribution and the competitor comparison forces the conversation.

### §1.17 Comp-against-comp comparison matrix

Structured side-by-side: client vs each of top-3 competitors across 10–20 specified dimensions (product depth on critical features, pricing tiers, target-segment overlap, channel mix, distribution moats, AEO presence, talent density, traction signals, public sentiment, defensible moats). Klue's "comparison matrix" template is the practitioner reference. Most useful for: pre-board strategy meetings, fund-raise prep, M&A diligence.

Anti-pattern: feature-by-feature checkmark grid (every CI shop's worst output). Modern alternative: dimension-by-dimension narrative cells, each one sentence with a specific named claim and supporting evidence.

### §1.18 Comparison-page warfare intelligence

Their "vs"-pages and "alternative-to"-pages. What positioning do they claim against the client? What positioning do they claim against the client's other competitors? What language do they use to frame the comparison? Sources: their own marketing site, scraped via Apify/Crawlee on a cadence (Visualping for change-detection). The 2026 modern lever: **comparison pages are the SEO + AEO substrate** that buyers and AI engines reference. A competitor whose "vs"-page out-ranks the client's "vs"-page wins the bottom-funnel AI-search traffic for the comparison query.

CI deliverable: catalog all the "vs" + "alternative-to" pages competitors have built mentioning the client (or the client's category), score their visibility (Ahrefs/Semrush ranking + AEO inclusion), and recommend defensive/offensive comparison-page strategy. Lights up a specific high-ROI action.

### §1.19 AEO (AI-engine optimization) presence comparison

How each competitor appears in AI-search engines: ChatGPT, Perplexity, Claude (via search), Gemini, You.com, Brave Search. Across recommendation queries, comparison queries, problem-statement queries, and brand queries. Sources: Profound, Athena AI, Otterly, Peec AI, Goodie AI — 2024–2026 vintage tools that prompt AI engines repeatedly and aggregate citation patterns. The 2026 modern lever: **AEO presence has overtaken classical SEO as the leading indicator of bottom-funnel demand** in B2B SaaS and AI-tooling categories. A competitor who shows up in 80% of category-defining Perplexity queries owns the consideration set.

Specific patterns to surface: query × engine matrix; citation source dominance (whose content does the AI engine actually quote?); brand mention without link (the "phantom mention" pattern that drives consideration but not analytics); freshness gap (last-cited content date by engine).

### §1.20 Asymmetric opportunity identification

Gaps in the landscape this specific client is uniquely positioned to own. Not just "no one is doing X" — that's a generic gap. Asymmetric = "no one is doing X, AND this client has strength / channel / relationship / dataset / capability the competition can't or won't bring." The intersection of §1.4 (mechanism) and §1.15 (channel-fit) and §1.6 (talent flow). Practitioner exemplar: April Dunford's "competitive alternatives → unique attributes → unique value → who cares" sequence. Cody Schneider's framing of "asymmetric distribution advantage" is the modern shorthand.

This axis is the one most clients want CI to deliver and most CI shops fail to deliver. v3.4 CI-1 has this as the "asymmetric-opportunity test" embedded in the score-1 anchor.

### §1.21 Defensive scenarios (what they could do to hurt us)

What's the worst plausible move a competitor could make against the client in the next 6–18 months? Pricing attack, segment expansion into client's core, partnership that locks the client out, M&A that consolidates against the client, talent poach of named individuals, regulatory positioning that tilts the field. War-game memo logic, applied tightly. Practitioner reference: McKinsey/Bain war-game memos. Not delivered as multi-scenario contingency matrix (out of scope per v3.4 §1.5 artifact-shape lock), but as named threats with named responses inside the unified brief.

### §1.22 Offensive scenarios (what we could do to hurt them)

The mirror. What asymmetric moves could the client make that the competitor structurally cannot copy? Hamilton Helmer's counter-positioning lens: the competitor can't follow because the move cannibalizes their existing business. Sahil Bloom-style framing: "find the move only you can make and they can't copy." Specific examples: pricing-page redesign that out-AEOs the competitor; founder-led podcast launch that out-distributes; vertical-specialization that the horizontal competitor can't justify investing in.

### §1.23 Counter-positioning recommendations

Specific positioning moves that exploit competitor structural weaknesses. Distinct from §1.22 offensive scenarios — counter-positioning is **structural messaging** rather than tactical action. April Dunford's mature counter-positioning practice. Example: "Position against the legacy enterprise player by leading with `built for the AI-native team` — they cannot copy because their enterprise customer base would revolt."

### §1.24 Watchlist + monitoring triggers (handoff to MON lane)

The CI brief should explicitly hand off to the `monitoring` lane (per gofreddy's existing lane architecture) a named set of triggers: signals to watch, threshold conditions, escalation rules. "Watch competitor X for hire pattern Y; trigger reassessment if Z." This is what makes the CI brief a *commission* of follow-on intel, not a one-shot. The reader doesn't have to re-commission; they've automated the next watch.

---

## §2. CUTS — outdated CI that doesn't earn its place in a 2026 deliverable

The agency has explicit license to **kill the following deliverable shapes**. Each appears in legacy McKinsey/Bain/Deloitte/Big-4 CI work and in legacy in-house CI shops. None serve a 2026 modern client.

1. **Generic SWOT.** 4 quadrants of plausible-sounding boilerplate. Private reasoning aid only; never in deliverable.
2. **Porter Five Forces fill-in.** Reasoning toolkit, never deliverable shape. Cuts.
3. **Surface-level feature comparison matrix (checkmark grid).** Features are easily copied (operational effectiveness, not strategic positioning); the grid format defeats the analytical work. Replace with dimension-by-dimension narrative cells (§1.17).
4. **"They're a leader / we're a challenger" Gartner-quadrant theater.** Quadrant placement is a paid marketing artifact, not a strategic signal.
5. **60-page BCG/McKinsey deck shapes that don't earn their pages.** Read by no one. Klue's explicit anti-pattern.
6. **Recency-distorted single-signal trajectory.** "They raised $X so they're going up-market." v3.4 CI-2 catches it; cut at deliverable level — no extrapolation without 2+ independent signals.
7. **Framework-name slot-fill.** "Counter-positioning play." "Process power." "Network economies." Framework asserted without mechanism. The Phase-4 pathology from `c76f051`.
8. **Single-hypothesis confirmation bias.** Briefs reinforcing existing prior with no disconfirming evidence. Cut: every brief engages ≥1 alternative interpretation.
9. **Benchmark-table-as-strategy (AI-lab).** MMLU/HumanEval/GSM8K aggregate scores. Saturated above 88% in 2026; differences statistically meaningless. Replace with independent evaluation citations (Epoch ECI, Artificial Analysis, LMSYS) + 2+ signal trajectory.
10. **Self-reported-score-trust (AI-lab).** Kimi K2 reported 50% on HLE; independent retesting 29.4%. Always cite independent corroboration.
11. **Directory-rank theater (legal).** Chambers tier without underlying matter-mix / partner / client-feedback driver. The tier is output, not strategy.
12. **National-market-size citation as opener (healthcare).** "$23B → $42B market" is irrelevant to a practice owner deciding pricing match. Market-size data goes to evidence appendix only.
13. **Treatment-mix-as-feature-comparison (healthcare).** "Botox vs Daxxify" pricing without JTBD framing ("I want to look less tired"). JTBD required.
14. **Vague action prose** ("strengthen positioning," "double down on," "explore the segment"). v3.4 CI-1 catches; recommendation must name action type AND specific target.
15. **Consulting-slop blocklist** (v3.4 `CI_BANNED_PHRASES`, preserved verbatim from live code): "leverage social media," "stay ahead," "consider exploring," "it's clear that," "no doubt," "it goes without saying," "needless to say," "at the end of the day," "game-changer," "best-in-class," "synergy," "low-hanging fruit."
16. **AI-slop tells** layered on top: em-dash density, "let me explain why," "moreover," "furthermore," "in conclusion." Per `2026-05-18-ci-ai-failure-modes.md` §3. Blocked by `structural_gate`.
17. **Confident-tone synthesis without traceable evidence chain.** v3.4 CI-6 catches. Cut: top-3 strategic claims must each name signals + cite verifiable sources + acknowledge ≥1 alternative.
18. **Length without point of view.** Descriptive teardown not committing to a thesis. Cut: every section ends on a claim or implication, not description.

---

## §3. ADDS — modern levers that pre-2023 CI frameworks could not see

Axes that distinguish a 2026 modern AI-native agency from a legacy CI shop. Some are 2026-original; some are pre-AI levers consistently under-weighted by legacy CI.

**§3.1 AI-native competitor anatomy.** For AI-adjacent competitors: model surface (which models, which providers, what tier), latency, cost-per-token, agent depth (single-call → multi-call → agentic tool-use → multi-agent), evaluation methodology, safety/compliance positioning, on-prem option (regulated finance / legal). Most CI shops lack the technical depth; modern agency must.

**§3.2 AEO presence comparison.** §1.19. Existed only since 2024; matured 2025; load-bearing 2026. Manifests differently per vertical — B2B SaaS sees Perplexity/ChatGPT-search lift; DTC sees Google AI Overviews displacement; healthcare sees Google Maps + medical-LLM citation patterns.

**§3.3 Founder-visibility comparison.** Per founder per surface: LinkedIn followers + engagement; X followers + engagement; podcast appearances last 6 months; conference keynotes last 12 months; own podcast/newsletter; book published; media appearances; X-thread strategic positioning frequency. The 2026 lever: **founder-as-CEO-of-narrative is the dominant brand-strength signal for sub-$100M ARR companies** (Cody Schneider, Sahil Bloom, Jasmine Bina convergence). For agency clients, founder-visibility comparison is often the asymmetric-opportunity finding.

**§3.4 Distribution-moat comparison.** §1.16. Pre-2023 treated distribution as marketing-ops; post-2023 it's a primary moat category because paid acquisition cost has roughly doubled, AEO + organic compound asymmetrically, and AI-native competitors weaponize distribution.

**§3.5 Talent-flow inference.** §1.6. Pre-2023 CI treated hiring as curiosity. Post-2023 (especially AI), talent-flow is the load-bearing leading indicator of product roadmap. Pirical for legal; Levels.fyi + Paraform for AI; manual LinkedIn elsewhere.

**§3.6 90-day pricing-sprint cadence (SaaS).** §1.12. Annual pricing review is legacy. Elite SaaS on 90-day sprints (OpenView, SaaS Factor 2025 Playbook). Pricing CI must match cadence.

**§3.7 Comparison-page warfare.** §1.18. Pre-2023 treated as marketing-ops collateral; post-2023 it's the primary SEO+AEO substrate for bottom-funnel buyer queries. Both offensive and defensive surfaces demand attention.

**§3.8 AI-call-recording win-loss integration.** §1.10. Pre-AI win-loss: $50K/quarter analyst-driven. Gong + Chorus + Claude-extraction drops it to ~$2K/quarter. Most clients haven't caught up; agency CI delivers integrated win-loss as part of brief.

**§3.9 Visualping + Wayback + change-detection forensics.** Pre-2023 CI: manual quarterly competitor-website checks. Modern: continuous change-detection on pricing pages, "vs"-pages, customer-list pages, hero headlines, careers pages (~$50/month per competitor).

**§3.10 Sparktoro audience-intersection.** Where client and competitor audiences overlap vs diverge; which podcasts / newsletters / X / LinkedIn voices each audience attends to. Rand Fishkin's named methodology. Surfaces concrete distribution opportunities.

**§3.11 Founder X-thread strategic positioning reads.** For AI labs and modern SaaS. Aravind Srinivas, Sam Altman, Dario Amodei post strategic positioning publicly. Modern CI cites founder posts as primary evidence, not anecdote.

**§3.12 Asymmetric-opportunity gap maps.** §1.20 made deliverable-shape. 2026 brief surfaces ≥1 asymmetric-opportunity finding at the intersection of structural-mechanism + channel-fit + talent-flow analysis. v3.4 CI-1 anchors this in the "asymmetric-opportunity test."

**§3.13 Counter-positioning per April Dunford methodology.** §1.23. The lever isn't the framework name (never in deliverable); it's the disciplined sequence: competitive alternatives → unique attributes → value those attributes enable → who cares most → market category framing.

**§3.14 Crayon-style real-time signal injection.** Pre-2023 CI was a quarterly deliverable. Modern CI integrates real-time capture (Crayon Spark, Klue auto-alerts, Visualping) — high-severity signal during engagement updates deliverable before final. Brief carries "as of [date]" stamp; last-14-days signals are flagged; last-48-hours signals route to recommendation directly.

**§3.15 Structured win-loss program handoff.** §1.10. If client has no win-loss program, CI engagement recommends scoping one as a follow-on. If they do, CI integrates last 4 quarters as primary evidence source. Clozd / Klue (vendors); Gong + custom analysis (modern AI-native alternative).

---

## §4. Vertical adjustments

The 24-axis surface in §1 is universal. What varies by vertical: which axes are load-bearing, what counts as a concrete action, and what time horizon matters. Per `2026-05-18-ci-vertical-conventions.md`, extended to verticals the current first-cohort doesn't cover.

**§4.1 B2B SaaS (architectural baseline).** All 24 axes apply. Load-bearing: §1.1 (competitor identification across direct + indirect + AI-native disruptors), §1.3 (trajectory 6–18 months), §1.12 (90-day pricing sprint), §1.18 (comparison-page warfare), §1.19 (AEO presence), §1.10 (win-loss), §1.20 (asymmetric opportunity). Action: roadmap pivot, pricing tier, channel shift, comparison-page deployment. Time: 1–4 weeks React; 4–13 weeks Evaluate. Decision-shape per `2026-05-18-ci-decision-format-mapping.md`: usually React or Structure; occasionally Evaluate.

**§4.2 AI labs and dev-tools.** Load-bearing differs: §1.3 trajectory at 6–18 *weeks* (much faster), §1.6 talent flow (primary signal), §3.11 founder X-thread reads, §3.1 AI-native anatomy, §1.4 mechanism (compute / data / talent moats), §1.19 AEO presence, §1.5 strategic narrative compounds. Action: model-roadmap priority, compute commitment, partnership go/no-go, narrative positioning. Time: 6–18 weeks. Cut: §1.18 comparison-page warfare (buyer journey mediated by AI engines). Add: independent benchmark citation (Epoch ECI, Artificial Analysis, LMSYS).

**§4.3 Modern AI-native agency clients (gofreddy's peer set).** Category that didn't exist in 2022 — Cody Schneider's Doola; modern outbound agencies like Twain; brand-strategy AI tooling. Load-bearing: §1.16 distribution-moat, §3.3 founder-visibility, §3.10 Sparktoro audience-intersection, §3.7 comparison-page warfare, §1.20 asymmetric opportunity (from §3.3 + §3.10 intersection). Time: 4–12 weeks. Action: distribution play, founder-content production, podcast circuit move, agency-vs-agency positioning shift. Cut: most patent/IP. Add: ICP-fit comparison.

**§4.4 Service businesses (legal / accounting / consulting).** Load-bearing: §1.6 talent flow (3,009 lateral partner moves in 2025; dominant CI signal-class), §1.4 mechanism (directory rankings as third-party evidence), §1.2 deep profile by practice group not firm-level, §1.21 defensive scenarios for lateral-flight, §1.7 M&A. Action: equity-vesting acceleration, lateral defense, practice-area investment, office-opening, alliance/merger evaluation. Time: 12–24 months. Add: Chambers / Legal 500 / IFLR1000 directory citations as CI-grade evidence; Citi Hildebrandt benchmarks. Cut: §1.19 AEO presence less load-bearing today (rising fast).

**§4.5 Healthcare practice (aesthetic dermatology / clinic ops).** Load-bearing: §1.1 local-market 0–5km radius, §1.15 channel-fit (RealSelf / Healthgrades / Instagram), §1.12 pricing (bundles, membership, financing), §1.11 customer migration via review monitoring, §1.21 defensive scenarios for consolidator threat (Schweiger / Pinnacle / Epiphany). Action: pricing match/hold, treatment-mix expansion, marketing-channel reallocation, injector hiring, device purchase, consolidator-response. Time: 4–12 weeks. Cut: national-market-size citations; patent/IP. Add: scope-of-practice + FDA off-label compliance; vendor-rep informal intel (Allergan/Galderma reps know who's buying what locally).

**§4.6 Finance / regulated finance / fintech.** Load-bearing: §1.4 mechanism (regulatory moats), §1.7 M&A and consolidation, §1.6 talent flow (senior-IC departures), §1.21 defensive scenarios for regulatory threats, §1.5 narrative monitoring for regulatory positioning shifts. Action: product launch with compliance posture, partnership for distribution, regulatory positioning, pricing-tier rationalization. Time: 12–24 months (regulatory slow). Add: SEC filings (10-K, 10-Q, 8-K), regulator letter / enforcement tracking, Bloomberg Intelligence sector briefs. Cut: §1.18 comparison-page warfare (B2B fintech sales are relationship-driven).

**§4.7 DTC / B2C e-commerce.** Load-bearing: §1.15 channel-fit (Meta / TikTok / Google / Amazon mix), §1.12 pricing at promo cadence, §1.11 customer migration via review platforms, §3.10 Sparktoro, §3.3 founder-visibility (TikTok / Instagram). Action: channel reallocation, promo response, product-launch defense, partnership/collab, creator strategy. Time: 2–6 weeks (very fast). Add: SimilarWeb traffic mix, Jungle Scout / Helium 10 for Amazon, influencer-cap-table analysis. Cut/adapt: §1.4 mechanism is usually *unit-economics by cohort*, not Helmer-7-Powers — language has to fit.

**§4.8 Cross-vertical synthesis.** The biggest cross-vertical adjustment is **decision-shape**, not vertical category — per `2026-05-18-ci-decision-format-mapping.md`. A SaaS acquisition evaluation (Evaluate cluster) needs the same brief shape as a law firm merger evaluation (also Evaluate). A SaaS pricing response (React) needs the same shape as a healthcare pricing response (also React). Routing on decision-shape matters more than routing on vertical, though vertical determines evidence sources and load-bearing axes.

---

## §5. Deliverable architecture — modular, not monolithic

The CI v3.4 spec correctly locks the **judge-stable hybrid brief** to 800–2,000 words with the Klue 5-section spine. The comprehensive CI deliverable a 2026 modern agency client expects is **wider than that brief** without violating it. The fix is **modular packaging** — the brief is the forcing-function front-end; the comprehensive scope wraps around it with components that the judge does not score (because they are deterministic-structural in nature) but that `structural_gate` checks for presence, freshness, and traceability.

### §5.1 Component A — Executive narrative brief (v3.4 hybrid)

The unchanged v3.4 artifact: 800–2,000 words, Klue 5-section spine (headline-as-claim / rationale / comparison / implications / recommendations), CB Insights WHAT-NOW / WHERE-NEXT / WHY-PRIORITY triple in Implications, war-game-flavored trade-off rigor in Recommendations. Judge-scored against CI-1 through CI-6. **This is the forcing function.** The reader can read this alone and commit to action.

### §5.2 Component B — Per-competitor deep profile cards

For the 3–5 most consequential competitors named in Component A: a one-page card per competitor covering product, pricing, positioning, traction signals, funding, hiring, M&A, partnerships, AI-native attributes (model surface, AEO presence), distribution moats (LinkedIn / X / podcast / founder visibility), strategic narrative they're driving. Klue-style profile-card format. **Not judge-scored at criterion level; `structural_gate` checks: ≥3 profiles present, each card carries ≥10 named-and-dated facts, each card carries ≥1 source URL per major claim.**

### §5.3 Component C — Trajectory matrix

A structured table: each competitor × 6–18 month forward call × 2+ independent signals × confidence level. Single page; primarily evidence-organizing. **`structural_gate` checks: ≥3 rows; each forward call carries ≥2 independent signals named; each row carries a date stamp.**

### §5.4 Component D — Comparison matrix (dimension-by-dimension narrative)

Not a checkmark feature grid (cut per §2). A 10–20 dimension matrix where each cell carries one sentence of narrative claim with one supporting evidence pointer. Dimensions selected per vertical (§4) but always include: product depth on critical features, pricing, target-segment overlap, channel mix, distribution moats, AEO presence, talent density, traction, public sentiment, defensible structural mechanism. **`structural_gate` checks: ≥3 competitors compared on ≥10 dimensions; each cell carries one sentence + one evidence pointer; no checkmark-only cells.**

### §5.5 Component E — Watchlist + monitoring triggers (MON-lane handoff)

The named hand-off to the gofreddy `monitoring` lane: which signals to track on which competitors, with named threshold conditions, escalation rules, and decision-shape triggers ("if X happens, reassess CI"). Mirrors §1.24. **`structural_gate` checks: ≥3 watchlist items; each carries named signal + named threshold + named action rule.**

### §5.6 Component F — Evidence appendix

Source registry. Every claim made in Components A–D maps to a source row in F: source URL (or specific document identifier), retrieval date, claim ID, alternative interpretation engaged (or "none — single source"). Defends against the 6 LLM-specific failure modes from `2026-05-18-ci-ai-failure-modes.md`. **`structural_gate` checks: URL HEAD resolution; "as of" date present; ≥1 source dated within 90 days per forward-looking claim; quote-grep against source corpus; entity-existence lookup; alternative-interpretation column populated.**

### §5.7 Optional component G — AEO presence detail

For agency clients in B2B SaaS, AI-tooling, DTC e-commerce, modern services. Detail table: 10–30 category-defining queries × 4–6 AI engines × competitor citation pattern + frequency + position. From Profound / Athena AI / Otterly / Peec AI / Goodie AI runs. **Optional because not all clients have AEO yet as a load-bearing surface; scoped at engagement-start.**

### §5.8 Optional component H — Win-loss analysis integration

For clients with existing win-loss data or Gong/Chorus call recordings. Structured extract: top-3 win patterns by competitor encounter; top-3 loss patterns by competitor encounter; named buyer-segment patterns. Integrates the AI-extracted analysis from §3.8. **Optional because not all clients have call-recording data.**

### §5.9 Total deliverable size envelope

Components A + B + C + D + E + F is the production-default deliverable. Size envelope: 8–15 pages total. Component A is 3–6 pages (the 800–2,000-word brief in print). B is 3–5 pages (one per competitor card). C + D each 1 page. E is 1 page. F is variable but ~2 pages typical. Total: a 10–15 page modular package, not a 60-page consulting deck — but **dramatically more comprehensive than the standalone v3.4 brief**.

### §5.10 The architectural trick: the judge stays narrow

The judge (CI-1 through CI-6) evaluates **only Component A**. Components B–F are evaluated by `structural_gate` deterministic checks (presence, count, freshness, traceability). This preserves the v3.4 judge-stability work — the judge sees a 800–2,000-word artifact it has been calibrated against — while the lane delivers a comprehensive package. The two design goals stop fighting.

**The deliverable surface area grows by 5x; the judge surface area stays constant.**

This is the most important recommendation in this document.

---

## §6. Evolution-loop considerations

Implications for the autoresearch evolution loop. The lane mutates `competitive` workflow over 50 generations; the judge tells the loop which mutations are better. Modular architecture in §5 has specific implications.

**§6.1 Mutation surface expansion is safe; judge surface stays narrow.** Adding components B–F doesn't expand the judge surface. Judge still sees Component A against CI-1..CI-6. The loop can mutate Component A's prose; it can also mutate templates/substrate producing B–F (deep-profile generators, trajectory-matrix builder, evidence-appendix retrieval). Those mutations are governed by `structural_gate` pass/fail, not judge quality score — precisely the OpenRubrics "Hard Rules → structural_gate, Principles → judge" split from `judge-design-guide.md` §1.2.

**§6.2 Shape-drift Goodhart remains the risk.** Per `2026-05-18-ci-artifact-taxonomy.md` §3 and v3.4 §1.5: under selection pressure, the workflow can drift Component A toward teardown-shape or war-game-shape. The §1.5 LOCKED artifact shape + 9-check `structural_gate` list defends this for Component A. For Components B–F, the parallel risk is **template-rigidity Goodhart**: the workflow learns to fill specific template slots without quality. Mitigation: each component's `structural_gate` requires evidence content (one sentence narrative + one evidence pointer), not just template presence.

**§6.3 Per-component variance instrumentation.** Per `judge-design-guide.md` §11.5: variance per criterion per generation is the Goodhart-time-constant signal. For modular CI, extend to: variance per `structural_gate` check per generation. If "comparison-matrix evidence-pointer present" passes 100% generations 1-5 then drops to 60% in generation 6, that's a Goodhart-warning.

**§6.4 First-cohort overfitting at the modular layer.** v3.4 §8 names first-cohort overfitting (DWF, Anthropic, Perplexity, Klinika). Modular has the same risk per component: profile-card template optimized against legal-services may not transfer to AI-lab. Mitigation: §4 vertical adjustments are operationalized as component-template selectors at engagement start; the lane carries multiple Component-B templates per vertical.

**§6.5 Judge-design discipline holds.** The 6-criteria v3.4 judge, applied to Component A only, retains all discipline `judge-design-guide.md` prescribes: outcome questions not feature checks; binary + 0.5-unknown; structured CoT; reference-free with hedged examples; per-criterion isolation; Goodhart-resistance. Modular packaging requires relaxing none of these.

**§6.6 In-lane vs sibling-lane for Components B–F.** Per `2026-05-18-ci-artifact-taxonomy.md` §4: monitoring digest belongs in `monitoring` lane, not `competitive`. By same logic, arguments exist for `competitor_profile` sibling (Component B), `competitive_appendix` sibling (Component F). **Recommendation: keep all components in `competitive` lane for v1.** Sibling-fork premature; lane is not yet judge-stable on Component A. Revisit at evolution-loop maturity.

---

## §7. SOTA exemplars — practitioners and methodologies to anchor against

Wider exemplar set the agency should be reading and reasoning with — quality anchors, never templates. See the Sources block for full URLs / references.

**Practitioner-grade CI vendors (operational floor).** Klue (executive-briefing template; battlecards; comparison-matrix discipline; "kill your darlings"); Crayon (running profile; Spark real-time signal injection; State of CI annual); Kompyte (CRM-integrated CI).

**Cross-industry analytical rigor (ceiling).** CB Insights Strategy Teardowns — WHAT-NOW / WHERE-NEXT / WHY-PRIORITY triple structure; Bloomberg Intelligence sector briefs — quantitative anchor with falsifiable forward claim; McKinsey/Bain war-game memos — competitor response-pattern prediction; S&P / Moody's sector briefs — credit-rating-driven CI.

**Modern founder-led CI thinkers (the 2026 lever set).** Cody Schneider on asymmetric distribution moats and replacement-competitor framing ("real competitor is the workaround"); Sahil Bloom on positioning + founder visibility as moat; April Dunford's positioning canvas + sales-pitch framework (reasoning toolkit for §1.23); Hamilton Helmer's 7 Powers (reasoning toolkit for §1.4 — never named in deliverable); Jasmine Bina (Concept Bureau) for §1.5 narrative + §1.23 counter-positioning; Patrick Campbell (ProfitWell) on sprint-cadence pricing intelligence + discount-magnitude/churn-rate finding; Rand Fishkin (Sparktoro) for §3.10 audience-intersection.

**Cross-vertical analyst networks.** AI labs: Nathan Lambert (Interconnects), Ben Thompson (Stratechery), Shawn Wang/swyx (Latent Space), Nathan Benaich (State of AI Report), MindStudio AI Lab Power Rankings. Legal services: MLA Global, Citi Hildebrandt, Leopard Solutions, Pirical, Law.com Pro. Healthcare: AmSpa, ASDS Consumer Survey, RealSelf Insights Center, FOCUS Bankers, Scope Research. SaaS pricing: OpenView Partners, SaaS Factor 2025 Playbook, ProfitWell. Distribution: Sparktoro, SimilarWeb, Semrush, Ahrefs. AEO: Profound, Athena AI, Otterly, Peec AI, Goodie AI.

**In-house exemplars referenced in journalism.** Anthropic's reported competitive-positioning memos around Claude vs GPT-5; OpenAI's reported frontier-compute planning (Axios April 2026); DeepMind's internal AGI-safety framing; Stripe's partnership/M&A strategic memos; Twilio's published BD-decision case studies.

**What ties SOTA together** (the 2026 quality ceiling): point of view at the top, not description-only; structural reasoning, not framework slot-fill; trajectory with 2+ independent signals, not snapshot; one or two committed actions the reader could act on before their next meeting; evidence chain that survives tracing; modular packaging so the executive read is short and the depth is appendix-grade.

---

## §8. Open questions

The comprehensive scope mapping in §1–§7 settles much of the deliverable surface. The following remain genuinely open and should be resolved before the lane ships the modular architecture.

1. **Sibling-lane fork timing.** Component B (deep-profile cards) and Component F (evidence appendix) are large enough that they could be their own lanes. v1 keeps them in `competitive` lane; when should the fork happen? Recommendation: at evolution-loop maturity (≥10 stable generations on Component A v3.4 criteria), evaluate Component B variance separately; if it's high and decoupled from Component A variance, fork to `competitor_profile` lane. Otherwise hold.

2. **AEO measurement primary-source selection.** Profound, Athena AI, Otterly, Peec AI, Goodie AI all measure AEO presence; they disagree about 15–30% of the time on specific queries because they sample AI engines at different times with different prompts. Which becomes the lane's primary source for §1.19 / Component G? Recommendation: cross-source at engagement start; declare one primary + one corroborating; cite both. No single tool is canonical yet.

3. **Sparktoro vs SimilarWeb vs Semrush primacy for §1.15 channel-fit.** Three different methodologies (audience-intersection, traffic-source, keyword-visibility) produce overlapping but non-identical channel-fit pictures. Lane should default to which? Recommendation: vertical-conditional. Sparktoro primary for content-marketing-led categories; SimilarWeb for paid-acquisition-heavy DTC; Semrush/Ahrefs for organic-search-dominant SaaS.

4. **Vertical-template count.** §4 names 7 verticals (B2B SaaS, AI-lab, agency, service-firm, healthcare, finance, DTC). Each needs a Component-B template variant per §6.4. Building 7 from scratch is expensive. Recommendation: start with 4 templates (SaaS, AI-lab, service-firm, healthcare — matching first-cohort fixtures) + a generic fall-through. Add finance and DTC templates when client #5+ onboards from those verticals.

5. **Win-loss program scoping for clients without one.** If the client has no win-loss program, Component H is absent. Should the CI engagement recommend scoping a win-loss program (a follow-on engagement) as part of the brief? Recommendation: yes, when win-loss data would have changed the dominant claim. Add a workflow flag for "win-loss-data-absent" cases that emits a follow-on-engagement recommendation.

6. **Founder-visibility comparison primary-source.** §3.3 names LinkedIn, X, podcast, conference, newsletter. Engagement scoping has to pick top-3 surfaces per client. Default? Recommendation: LinkedIn + X + podcast for B2B; X + LinkedIn + own-newsletter for AI-lab; Instagram + TikTok + own-podcast for DTC; LinkedIn + own-podcast + legal-conference circuit for service-firm.

7. **First-cohort overfitting at modular layer.** Per §6.4: monitor for template-shape Goodhart per component as the loop runs. No mitigation prescribed beyond "watch the variance instrumentation" — but if a specific component-template variance grows monotonically over 3 generations, the prescription per `judge-design-guide.md` §11.5 is redesign, not calibration.

8. **Decision-shape input plumbing.** Per `2026-05-18-ci-decision-format-mapping.md` §3-4 recommendation: `decision_shape` should be a workflow input variable routing Component A's substrate and `structural_gate`. The modular architecture in §5 doesn't depend on this being implemented, but if it isn't, the React-cluster default scoping in v3.4 stays. Recommendation: add `decision_shape` as workflow input when client #5+ onboards from Evaluate-cluster (acquisition / market entry) use cases.

9. **Comprehensive deliverable validation against real-fixture variance.** The modular architecture has never been run against the existing 4 first-cohort fixtures (DWF, Anthropic, Perplexity, Klinika). Recommendation: build Components B–F retroactively against the current Phase-3 fixtures; eyeball whether `structural_gate` checks fire correctly and whether the modular package delivers genuinely more value than Component A alone. If not, the recommendation in §5 is wrong and we revert to standalone Component A. Validation gate before propagating.

10. **Cost envelope per engagement.** Component A is the only cost-validated component (existing v3.4 lane runs at known per-generation cost). Adding Components B–F multiplies the workflow's compute cost by ~3-5x per fixture (more retrievals, more substrate, more `structural_gate` checks). Recommendation: cost-instrument the modular architecture on 1 fixture before propagating; if per-fixture cost exceeds $15-25 (rough envelope), trim Component F first (most expensive due to URL HEAD resolution + quote-grep + entity-existence lookup).

11. **Sibling-lane coordination for §1.24 watchlist handoff.** Component E hands off to `monitoring` lane. Does the `monitoring` lane have the surface to receive a structured CI-handoff today, or does monitoring need a workflow extension to ingest CI-triggered watchlists? Per memory notes, the monitoring lane has a v0 skeleton but is not yet judge-stable. Recommendation: define the handoff schema in v1; implement monitoring-side ingestion when the monitoring lane reaches v3-equivalent maturity.

12. **Component G AEO presence — when is it required vs optional?** Currently optional. Should it become default-required for B2B SaaS, AI-tooling, modern-agency, DTC verticals? Recommendation: required by 2026-Q4 as AEO presence overtakes classical SEO as a competitive surface in those verticals; optional for legal-services / healthcare / finance through 2026 because AEO is still emergent in those verticals.

---

## Closing note on posture

This deliverable is **comprehensive scope mapping**, not a redesign of v3.4. The v3.4 criteria (CI-1 through CI-6) are correct as the judge surface. The v3.4 artifact-shape lock (§1.5) is correct as the Component-A target. What this deliverable adds is **the wider deliverable surface that wraps Component A** — Components B through H — and the modular architecture (§5) that lets the lane grow that surface without expanding the judge surface.

The single most important recommendation across the 9000 words above: **modularize. Keep the judge narrow. Grow the deliverable wide. Use `structural_gate` for the wrap-around components. Preserve all the v3.4 work.**

Per JR's framing: the agency must be capable of all 24 axes in §1, must cut everything in §2, must add everything in §3, must adjust per vertical per §4, must deliver the modular architecture per §5. The lane's evolution loop, judge, and per-component template surfaces follow from there.

---

## Sources

**Practitioner CI vendors:** Klue (klue.com), Crayon (crayon.co), Kompyte, Clozd, Gong, Chorus.

**Analytical rigor exemplars:** CB Insights Strategy Teardowns (cbinsights.com/research/teardown), Bloomberg Intelligence sector briefs, McKinsey (war games; M&A blueprint), Bain (scenario and contingency planning), S&P / Moody's sector briefs.

**Modern founder-led CI thinkers:** Cody Schneider (Doola founder); Sahil Bloom (sahilbloom.com); April Dunford (Obviously Awesome; Sales Pitch); Hamilton Helmer (7 Powers); Jasmine Bina (Concept Bureau); Patrick Campbell (ProfitWell pricing); Rand Fishkin (Sparktoro audience-intersection).

**AI-lab analyst stack:** Ben Thompson (Stratechery), Nathan Lambert (Interconnects), Shawn Wang / swyx (Latent Space), Nathan Benaich (State of AI Report; stateof.ai), MindStudio AI Lab Power Rankings, Epoch AI (epoch.ai), Artificial Analysis (artificialanalysis.ai), LMSYS Chatbot Arena (lmarena.ai), Paraform Talent Density Index, Levels.fyi.

**Legal services CI:** MLA Global (legal-services maturation), Citi Hildebrandt Client Advisory, Leopard Solutions (Firmscape), Pirical, Law.com Pro, Above the Law, Law360, Chambers, Legal 500, IFLR1000.

**Healthcare practice CI:** AmSpa (State of Industry; Aesthetic Marketing Report), ASDS Consumer Survey, RealSelf Insights Center, FOCUS Bankers, Scope Research, FTI Consulting.

**SaaS pricing CI:** OpenView Partners pricing benchmarks, SaaS Factor 2025 Pricing Playbook, ProfitWell.

**AEO measurement tools (2024-2026 vintage):** Profound, Athena AI, Otterly, Peec AI, Goodie AI.

**Distribution / channel analysis:** Sparktoro, SimilarWeb, Semrush, Ahrefs.

**Change-detection + scraping infrastructure:** Visualping, Wayback Machine, Apify, Crawlee.

**Deal tracking:** Crunchbase, PitchBook, Axios Pro Rata, The Information.

**Companion gofreddy research (preserved by reference):**
- `docs/research/2026-05-15-judges-domain-competitive.md` (generalist CI domain)
- `docs/research/2026-05-18-ci-vertical-conventions.md` (vertical-specific conventions)
- `docs/research/2026-05-18-ci-artifact-taxonomy.md` (artifact shape taxonomy)
- `docs/research/2026-05-18-ci-ai-failure-modes.md` (LLM-specific failure modes)
- `docs/research/2026-05-18-ci-decision-format-mapping.md` (decision-to-format mapping)
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (CI v3.4 optimal-output spec)
- `docs/rubrics/judge-design-guide.md` (judge design discipline)
