# Competitive Lane — Calibration Corpus

Phase B of judge-design research. Inputs: phase-b-research/raw/competitive.json (Lenny/Balfour-heavy; April/Andy empty), plus targeted web research on CI vendor practice (Crayon, Klue, Kompyte), Wardley/JTBD/Dunford applied to competition, and B2B CI benchmarking. CI rubric is already the most-iterated of the gold-standard lanes; this corpus aims at surgical additions on triangulation depth, source-class diversity, and forward-signal anticipation — not a rewrite.

---

## 1. Top 9-tier signals (10-15 concrete examples)

What a CMO would describe as "the brief that paid for itself in one meeting." Each signal pairs a content move with a judge-able test against `brief.md` + `competitors/<name>.json`.

1. **Single named strategic thesis in the first 150 words.** Example: "Adyen is winning enterprise payments because their unified-commerce pitch lets a CFO retire three vendors at once; Stripe's API-first story is irrelevant in that buying committee." Source: Dunford's "competitive alternatives over competitors." Test: extract first 150 words; could a reasonable strategist hold the opposite view? If no, no thesis.

2. **Triangulated load-bearing claims (≥2 independent source classes).** "Adyen hiring 40% more enterprise AEs in EMEA" backed by LinkedIn JD delta + Glassdoor interview-volume spike + Q3 earnings transcript. Source: SCIP + Klue. Test: per claim count distinct CLASSES (pricing, review, hiring, financial, leadership, community, repo, earnings). ≥2 = triangulated; 1 = thin; 0 = assertion.

3. **Trajectory framing, not snapshot.** "Postman's team-tier price rose 35% over 18 months — harvesting, not acquiring" beats "Postman charges $29/user." Source: Wardley evolution-stage analysis. Test: each competitor section contains ≥1 dated comparison.

4. **Earnings-call or 10-K specific quote with date.** "On Stripe's Q2 2026 call, Collison spent 4 of 9 prepared paragraphs on agentic payments — they're pivoting." Source: AlphaSense / SCIP. Test: regex for date-stamped quoted phrases.

5. **Hiring-signal interpretation, not just count.** "Decagon posted 14 forward-deployed engineer roles in 60 days — abandoning self-serve for white-glove implementation." Source: Balfour's Reforge growth-signal reading. Test: each hiring observation followed by a falsifiable "implies / suggests / indicates" inference.

6. **JTBD-defined competitive set including non-obvious substitutes.** "Mercury isn't beating Brex — it's beating 'keep using Chase Business.'" Source: Dunford phantom-competitors + Christensen JTBD. Test: brief explicitly names the status-quo alternative; penalize direct-competitors-only profiling.

7. **A specific uncomfortable truth about the client.** "Your dev-docs advantage is irrelevant — the CFO signs before engineering evaluates." Source: Balfour second-order effects. Test: ≥1 self-critical statement naming a specific client weakness.

8. **Top 3 recs each carry impact / effort / owner-archetype / success-metric.** "Reroute 40% of Q3 branded-search to comparison terms. Effort: 1 sprint, paid-search lead. Impact: +180 enterprise MQLs/qtr. Metric: comparison-term CTR ≥ 4%." Source: Crayon battlecards-to-revenue + SCIP ROI. Test: regex each top-3 rec for the 4 fields.

9. **Forward signal with explicit leading indicator.** "Watch for Stripe agentic-commerce SDK by Q1 2027; leading indicator = >5 'agent payments' JDs in 90 days." Source: Wardley anticipatory + AlphaSense predictive CI. Test: each future-tense claim names an observable + window.

10. **Data-tier honesty inline, not in a footnote.** "Enterprise pricing is gated; $50K floor estimate from 2 anonymized G2 quotes — treat as directional." Source: Improvado + SCIP ethics. Test: confidence language attached to specific findings, not boilerplate.

11. **Distinctive surface area.** Earnings-call diff, JD diff, changelog cadence, GitHub commit frequency, conference-talk topics — not the same five pages every analyst reads. Source: Improvado / Klue automation. Test: ≥3 source-types beyond homepage + pricing + G2 + Crunchbase.

12. **Strategic-lens application, not recitation.** Wardley map showing Adyen at commodity stage vs Stripe pre-product, with a specific move — not a textbook description. Source: Wardley 2026 + Dunford framework-theater warning. Test: penalize any named framework not applied to a named competitor with a named consequence.

13. **Pricing-trajectory + packaging, not list price.** "Adyen quietly removed their public pricing page Feb 2026 — confirms enterprise-only repositioning seen in hiring." Source: Crayon move-detection. Test: each pricing finding includes a structural-change observation.

14. **Buying-committee mapping.** "Champion (head of payments), economic buyer (CFO), blocker (compliance) — Adyen wins champion, loses blocker." Source: Dunford sales narrative. Test: ≥3 distinct buyer roles per competitor with win/lose verdict.

15. **One disconfirming-evidence paragraph per major thesis.** "The Adyen-winning-enterprise thesis would be invalidated if Stripe Q4 reports >30% enterprise net-new logos." Source: SCIP rigor + falsifiability norm. Test: presence of invalidation conditions on top-level claims.

---

## 2. Top 5-tier signals — the mediocre middle

Briefs that look professional, read coherently, and contain no strategic value. The "feature comparison + framework regurgitation" zone where 70% of vendor-produced CI lives.

- **Comprehensive feature matrix with no decision.** All five competitors get green/yellow/red dots across 24 features. The reader can't tell what to do.
- **SWOT for each competitor with generic entries.** "Strengths: strong brand. Weaknesses: high pricing." Source-free, undated, interchangeable across industries.
- **Recitation of Porter's Five Forces without competitor-specific application.** "Threat of new entrants is moderate." Useless.
- **Pricing tables that mirror the competitor's marketing page.** No structural read, no trajectory, no inference.
- **Founding-year / HQ / employee-count paragraphs.** Wikipedia-grade openers.
- **"Key differentiators" sections that mirror each competitor's own positioning page** — i.e., the brief is parroting marketing copy as analysis.
- **Recommendations of the form "Monitor X closely" or "Strengthen our value proposition."** Verb-less, owner-less, metric-less.
- **One-source-confident claims.** "Customers are leaving Mercury (Reddit thread, 14 upvotes)" presented at the same confidence level as audited churn data.

These are the briefs CI teams produce when the goal is "show we did the work" rather than "change a decision."

---

## 3. Slop patterns (1-tier)

What automatic graders should flag aggressively. Most are already named in the prompt; I've added a few specific failure modes from the Crayon/Klue AI-summary patterns surfaced in research.

- **Wikipedia rehash.** Founding date, HQ, mission statement, employee count, primary investors. Found in opening paragraphs of low-tier briefs.
- **Framework theater.** Full SWOT tables, Five Forces grids, BCG matrices — populated but never operationalized. The framework is the deliverable.
- **Feature-list drift.** Bullet lists of features without pricing-tier context, GTM context, or adoption signal.
- **Single-source confidence collapse.** "They're losing customers" sourced to one Reddit thread or one G2 review, stated with the same confidence as a multi-source claim.
- **No "so what."** Findings end in periods, not implications. "Adyen raised $250M in 2024." (And?)
- **Stale citations.** Sources >18 months old presented as current state without acknowledgement.
- **Recommendation void.** "Monitor closely," "consider further analysis," "strengthen positioning." Action-shaped strings with no action.
- **Battlecard substitution.** Objection-handling tables ("If they say X, say Y") presented as strategic analysis. Distinct genre, distinct client; should not be confused with a strategic brief.
- **AI-summary slop (2026-specific).** Crayon's "Sparks" and similar features produce paragraph-form summaries that read fluently but flatten signal. Tell: every competitor section is the same length, same structure, same hedge density. No paragraph reads like a human noticed something.
- **Phantom-competitor profiling.** Per Dunford: pages dedicated to a competitor who never shows up on a real shortlist. PM's list, not sales' list.
- **Mission-statement quoting as evidence.** "Stripe's mission is to increase the GDP of the internet" presented as strategic insight.

---

## 4. What separates 9-tier from 5-tier

Six measurable dimensions. The judge should probably operationalize 3-4 of these; the rest are already captured by existing CI criteria.

**Insight density per 500 words.** Count claims that draw inferences ("X implies Y because Z") versus claims that restate facts ("X is true"). 9-tier ≥40% inference; 5-tier <15%. Operationalization: classify each declarative sentence as inferential vs. factual; report ratio.

**"So what" rate.** Per finding, is there an explicit implication for the client? 9-tier ≥80% of load-bearing findings carry a "so what." 5-tier <30%. Operationalization: per H3 section, count findings with ≥1 follow-on sentence beginning "this means," "the implication," "for [client]," etc.

**Triangulation depth.** Per load-bearing claim, count independent source CLASSES (not URLs). 9-tier averages ≥2.2; 5-tier ~1.1. Operationalization: classify each citation by class (pricing, review, hiring, financial, leadership, community, repo, earnings, regulatory), count distinct classes per claim.

**Source-class diversity (brief-wide).** Total distinct classes across the brief. 9-tier ≥5; 5-tier ≤2 (usually homepage + Crunchbase). Operationalization: pre-defined class taxonomy; count distinct classes appearing ≥1× in citations.

**Anticipation rate.** % of forward-tense claims that include a specific leading indicator. 9-tier >60% of forecasts are falsifiable with a named observable; 5-tier near 0%.

**Distinctiveness.** Surface-area entropy. 9-tier cites earnings transcripts, JD diffs, GitHub repo activity, conference talk decks. 5-tier cites the homepage and G2. Operationalization: score by source-type rarity (homepage = common, earnings transcript = distinctive).

The first three are likely the highest-leverage additions to CI given the audit gap. Density and "so what" rate may overlap enough with CI-1 (single strategic thesis) and CI-3 (trajectory not snapshot) to skip — see §6.

---

## 5. 2026 emerging signals

**AI-summary slop in published CI reports.** Crayon's "Sparks" and Klue's automation features generate competitor summaries automatically from RSS / news ingestion. The 2026 failure mode visible in vendor demos: summaries are fluent paragraphs of equal length per competitor, no notice-worthy moment surfaces. Judge implication: penalize uniform-length per-competitor sections; reward asymmetric depth (the competitor that matters gets 2× the words).

**New competitive signal sources.** Three under-used in 2024 are now load-bearing in 9-tier briefs:
- **Levels.fyi compensation trajectories** as a proxy for talent-war intensity and team-level org structure (which functions are paying above-market = where competitor is investing).
- **Glassdoor interview-volume velocity** (review counts dated by month) as a proxy for hiring throughput and attrition.
- **GitHub commit cadence + release-tag velocity** on public competitor repos as a product-velocity proxy. Particularly load-bearing for dev-tool, infrastructure, and OSS-adjacent competitors.

**Strategic-lens evolution.** Wardley mapping is having a 2026 moment in build-vs-buy and agentic-AI contexts (Haberlah / Wardley.com). Application-to-competition is still rare; when present, it's a strong 9-tier signal because it forces evolution-stage thinking (custom → product → commodity) that snapshot analyses miss. JTBD applied to competition (Sivo / Christensen) is more mature but still under-used; the "competitive alternatives include the status quo" frame (Dunford) is the single highest-ROI addition for B2B briefs that overweight direct competitors.

**Falling-cost moves.** AI-augmented CI has dropped the floor of acceptable depth — even mid-tier briefs now include automated pricing-page diffs, JD diffs, social-velocity tracking. The ceiling has risen accordingly: 9-tier in 2026 looks like 9-tier in 2024 plus forward-signal anticipation and disconfirming-evidence paragraphs.

---

## 6. Implications for the judge — keep / strengthen / add for CI-1..8

CI is the most-iterated rubric of the gold-standard lanes. Recommendation is surgical additions, not rewrites. Three audit gaps to address: triangulation depth, source-class diversity, forward-signal anticipation. Insight density and "so what" rate are likely captured well enough by CI-1 and CI-3; see analysis below.

### Existing criteria

- **CI-1 (essential — single strategic thesis).** KEEP. This is exactly the "first 150 words commit to a thesis" signal from §1. No change needed.
- **CI-2 (pitfall — reasoning chain proportionate).** STRENGTHEN. Current rubric asks for "any source" supporting reasoning; promote to "≥2 independent source classes for load-bearing claims" (see CI-9 below). Without this, CI-2 cannot distinguish single-source confidence collapse from triangulated reasoning.
- **CI-3 (important — trajectory not snapshot).** KEEP. Maps directly to signal §1-#3. The trajectory framing already requires dated comparisons, which is what we want.
- **CI-4 (important — recommendations executable given client constraints).** STRENGTHEN. Add the impact / effort / owner-archetype / success-metric quartet from §1-#8 to the score-5 anchor. Currently the cross-reference to `_client_baseline.json` ensures the recs are *relevant*; it does not ensure they are *operational*.
- **CI-5 (essential — gaps mapped to specific client capabilities).** KEEP. Strong as written.
- **CI-6 (important — surfaces challenges to client beliefs).** KEEP. Maps to §1-#7 (uncomfortable truth). Strong as written; consider tightening score-5 anchor to require ≥1 client-specific weakness explicitly named.
- **CI-7 (essential — top 2-3 actions clearly prioritized).** KEEP. Mostly subsumed into the strengthened CI-4 if the impact/effort/owner/metric quartet is enforced; could potentially merge, but keeping separate preserves the "prioritization" signal distinct from "executability."
- **CI-8 (pitfall — data-gap honesty).** KEEP. Maps directly to §1-#10. Already cross-references `data_tier`; strong as written.

### New criteria

**CI-9 (essential — triangulation depth).** Source-class taxonomy: pricing, review, hiring, financial-filing, leadership-statement, community, repo, earnings-call, regulatory. Score-5: every load-bearing claim cites ≥2 distinct classes. Score-3: load-bearing claims average ≥1.5 classes. Score-1: load-bearing claims single-source or unsourced. Verification: extract citations, classify by taxonomy, count distinct classes per claim (load-bearing = first sentence under each H3, or sentences with causal/inferential language). Tier: pitfall-gate (<2 classes flagged) then quality scoring above the gate.

**CI-10 (important — source-class diversity, brief-wide).** Score-5: ≥5 distinct classes used across the brief. Score-3: 3-4. Score-1: ≤2 (typically homepage + Crunchbase). Verification: same taxonomy as CI-9; count distinct classes appearing ≥1× across all citations. Distinct from CI-9 because a brief can hit class-diversity globally while keeping individual claims thin; both signals needed.

**CI-11 (important — forward signal with leading indicators).** Score-5: ≥1 forward-tense prediction per major competitor, each with an observable + window that could confirm or falsify. Score-3: forward claims present but lack indicators. Score-1: snapshot-only. Verification: regex for "will likely / expect / anticipate / watch for"; per match check next sentence for falsifiability cue (named observable, time window). Tier: ceiling-raising, not pitfall-class.

### Skipped additions (analyzed, judged redundant)

- **Insight density (inference vs. fact ratio).** Considered but redundant with CI-1 (a real strategic thesis forces inferential writing throughout) and CI-3 (trajectory framing requires inference). Adding would create scoring noise without adding signal.
- **"So what" rate.** Considered but redundant with CI-4 (executable recommendations imply each finding leads somewhere) and CI-6 (challenging client beliefs requires implication-drawing). Adding would over-weight the same dimension.
- **Distinctiveness / source-rarity scoring.** Considered as CI-12 but judged operationally fragile — rarity rankings drift, and CI-10 (source-class diversity) captures most of the same signal more robustly. Park for v2 if CI-10 proves insufficient.

### Sequence of impact

If only one criterion ships: **CI-9 (triangulation depth)**. The single highest-leverage gap in the current CI rubric is that "evidence_confidence" rolls up qualitatively without enforcing per-claim source counting. Single-source confidence is the most common failure mode in mid-tier briefs.

If two: add **CI-11 (forward signal)**. Lifts the ceiling on briefs that already pass CI-1/CI-3/CI-9.

If three: add **CI-10 (source-class diversity)**. Catches the brief that triangulates well on a few claims but leans on homepage+Crunchbase everywhere else.

All three are score-able with simple structural extraction (citations, regex, taxonomy lookup) plus one LLM call per claim for "is this load-bearing?" classification. No new ground-truth infrastructure required beyond the taxonomy file.

---

## Sources

- [10 Competitive Intelligence Best Practices to Dominate in 2026 — TrySight](https://www.trysight.ai/blog/competitive-intelligence-best-practices)
- [A Practitioner's Complete Guide to Competitive Intelligence — CI Alliance](https://www.competitiveintelligencealliance.io/competitive-intelligence-complete-guide/)
- [Competitive Intelligence Automation: The 2026 Playbook — AriseGTM](https://arisegtm.com/blog/competitive-intelligence-automation-2026-playbook)
- [Competitive Intelligence: 32 Best Tools for 2026 — Improvado](https://improvado.io/blog/32-best-competitive-intelligence-companies)
- [Competitive Intelligence Foundational Tools and Practices — SCIP](https://www.scip.org/page/Competitive-Intelligence-Foundational-Tools-and-Practices)
- [How to Automate Competitor Insights with AI — Klue](https://klue.com/topics/automated-competitor-insights)
- [Crayon AI Toolkit / Sparks — Crayon](https://www.crayon.co/ai-toolkit)
- [Kompyte vs Crayon vs Klue comparison — Kompyte](https://www.kompyte.com/kompyte-klue-crayon-comparison)
- [B2B Competitor Analysis: A Data-Backed Guide (2026) — Prospeo](https://prospeo.io/s/b2b-competitor-analysis)
- [Competitor analysis framework — Growth Syndicate](https://www.thegrowthsyndicate.com/resources/competitor-analysis-framework)
- [Build vs Buy in 2026: Using Wardley Mapping — David Haberlah](https://medium.com/@haberlah/build-vs-buy-in-2026-using-wardley-mapping-to-navigate-the-agentic-ai-shift-be24d534b054)
- [Wardley Mapping 101 — wardleymaps.com](https://www.wardleymaps.com/guides/wardley-mapping-101)
- [Jobs to Be Done: How to Identify Your Real Competitors — Sivo](https://mrx.sivoinsights.com/blog/who-are-your-real-competitors-jobs-to-be-done-shifts-the-lens)
- [Competitive Analysis using Jobs To Be Done — Lean Startup Circle](https://medium.com/lean-startup-circle/competitive-analysis-using-jobs-to-be-done-aa2687379649)
- [Positioning and Competition — April Dunford](https://www.aprildunford.com/post/positioning-and-competition)
- [Sales-First Storytelling — Positioning with April Dunford](https://aprildunford.substack.com/p/sales-first-storytelling)
- [Levels.fyi — compensation trajectories as competitive signal](https://www.levels.fyi/)
