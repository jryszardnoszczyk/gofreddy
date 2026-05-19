---
date: 2026-05-18
type: research deliverable
status: complete
topic: CI artifact taxonomy (teardown / brief / battlecard / monitoring / war-game)
parent: docs/handoffs/2026-05-17-judge-design-step1-competitive.md
sibling: docs/research/2026-05-15-judges-domain-competitive.md
---

# Competitive-Intelligence Artifact Taxonomy

## 1. TL;DR + artifact-shape recommendation

Competitive intelligence is not one artifact. It is at least five — each with a distinct reader, length convention, evidence density, and decision shape. The gofreddy `competitive` lane currently produces an unnamed hybrid that drifts between shapes from fixture to fixture; the v2 spec at `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` implicitly nominates the **executive briefing** shape (Klue-style: headline-claim / rationale / comparison / implications / recommendations) but never says so out loud.

The five shapes are:

1. **Strategic teardown** — 20–100+ pages, CB Insights / Stratechery / sell-side initiation reports. Reader: strategist, M&A lead, board. Decision: posture for the next 12–24 months.
2. **Executive briefing** — 1–3 pages (PDB-style), Klue / FullIntel / McKinsey snapshot. Reader: CEO / VP. Decision: a concrete action this week.
3. **Sales battlecard** — 1 page max, Klue / Crayon / Kompyte. Reader: AE in or before a call. Decision: in-call objection response.
4. **Monitoring digest** — bulleted alerts plus 2–3 line "what changed / why it matters / what to do." Reader: comms / strategy ops. Decision: triage — escalate, watch, ignore.
5. **War-game memo** — 5–15 pages of if-they-do-X-we-do-Y matrices, McKinsey / Bain. Reader: CEO + exec committee. Decision: pre-commit to a contingency.

**Recommendation: option (c), one hybrid shape, executive-briefing skeleton with teardown-grade evidence depth on the single most-consequential development.** Specifically: the lane produces an executive briefing in length (≈ 1.5–3 pages of dense prose, ~ 800–2,000 words) with teardown-grade structural-mechanism reasoning on the dominant threat and war-game-flavored response logic on the recommendation. Optionally surfaces 1–2 sales-relevant talk tracks as a tail section when fixtures are deal-stage. Sibling-lane fork (option d) is the wrong move at this stage: the gofreddy `monitoring` lane already covers the digest shape, and decomposing further would multiply judge surface area before any single lane is judge-stable.

The top failure mode the taxonomy surfaces that v2 does not catch: **shape-drift Goodhart** — the workflow learning that an output looking like a teardown (long, headered, sectioned) scores well on CI-3 mechanism, while one looking like a war-game memo scores well on CI-2 trajectory, producing a Frankenstein artifact in fixture after fixture. The fix is naming the shape explicitly in the spec.

---

## 2. Per-shape deep dive

### 2.1 Strategic teardown — deep, public-facing analysis

**Canonical exemplars.**
- CB Insights' Apple, Google, Amazon, Microsoft, and Square Strategy Teardowns (cbinsights.com/research/teardown/) — the most-cited published reference for the shape.
- Stratechery deep dives (stratechery.com/category/articles/) — Ben Thompson's long-form essay form, ~ 2,500–6,000 words per piece, weekly free + thrice-weekly paywalled.
- Sell-side **initiation notes** from Bernstein, Morgan Stanley, Goldman Sachs Equity Research — 50–100+ pages on a single ticker, far longer than the routine earnings note (Wall Street Prep, Mergers & Inquisitions on equity research formats).

**Length convention.** 20 pages (Stratechery essay equivalent) to 100+ pages (sell-side initiation). CB Insights teardowns sit at 30–80 pages with embedded charts. Word counts: 5,000–25,000.

**Structure / sections in order.** CB Insights' published spine, repeated across Apple / Google / Amazon / Microsoft teardowns: priority areas identified first → then per priority area, the standardised three-part triple: **WHAT it's doing now → WHERE it's going next → WHY this is a priority.** Sell-side initiations add: investment thesis up top, financial model (DCF + comparables), risks, catalyst calendar, valuation, recommendation (Buy/Hold/Sell + price target). Stratechery's looser structure: framing observation → historical pattern → present-day instance → strategic implication.

**Evidence type and density.** Heavy primary + secondary. Patents searched and counted. M&A and investment patterns charted over a 5+ year window. Hiring-data telemetry (LinkedIn pulls). Earnings-call transcript phrase analysis. Patent-filing trends. Public filings (10-K, 10-Q, S-1). Citation count: dozens per section. The teardown earns its length by triangulating across signal types, not by repetition.

**Reader persona.** Corp dev / M&A analyst evaluating a target; strategy team at the directly competing company; sell-side analyst's institutional client (PM, hedge fund analyst) deciding to hold or rotate; LP / VC evaluating a thesis. Time budget: 1–3 hours, often consumed across multiple sittings. The reader expects a hand-off — they pass the doc to someone else who builds a model from it.

**Recommendation specificity.** Strategic posture across a 12–24 month horizon. Sell-side delivers a numeric price target. Stratechery delivers a thesis (often without a recommendation; analytical narrative is the deliverable). CB Insights delivers "where the priority areas are heading + what this means for the category."

**Failure modes.** (a) Length without point of view — the descriptive teardown that does not commit to a thesis; readers walk away informed, undirected. (b) Backward-looking — heavy on history, thin on trajectory. (c) Cargo-culting headers without earning them ("Mechanism of Advantage:" with two sentences underneath). (d) Confusing operational effectiveness with strategic positioning (Porter's named trap — easy to fall into at length).

**AI-generation difficulty.** Hard. Length punishes hallucination compounding — a teardown that gets a financial fact wrong on page 12 loses credibility for the entire document. Requires deep primary-source retrieval (patents, transcripts, filings). Easier with retrieval-augmented systems; harder for a context-window-only LLM. The gofreddy lane in its current form is not equipped for teardown output.

### 2.2 Executive briefing — 1–2 pages, action-oriented

**Canonical exemplars.**
- **President's Daily Brief (PDB)** — declassified Kennedy/Johnson/Nixon/Ford PDBs from CIA archives (cia.gov / archives.gov releases 2015–2016) confirm the shape: rarely longer than 25 pages total brief, "staccato, short-form" articles, typically 1–2 pages per article, bulleted, with visuals (Wikipedia entry on PDB; The Cipher Brief column "What I Learned Writing for the President's Daily Brief"). Bill Clinton's PDB ran 9–12 pages; the Bush PDB consisted of "a half dozen or so one- to two-page articles."
- **Klue executive briefing** — Headline → Rationale → Comparison → Implications → Recommendations. Klue blog "Competitive Intelligence Reporting" recommends 1–3 pages and explicitly warns against "60-page PowerPoints" as a known anti-pattern.
- **FullIntel executive news briefings** — analyst-written summaries plus social-impact analysis, delivered daily by email, optimized for mobile (fullintel.com/solutions/executive-news-briefings).
- **ArchIntel daily intelligence brief** — newsletter format, 6 a.m. delivery, "1–3 pages" explicit length convention (ArchIntel "Effective Executive Briefings").

**Length convention.** 1–3 pages. 500–1,500 words. The PDB and ArchIntel are the strongest published anchors for the upper bound; 3 pages is the ceiling, not the target.

**Structure / sections in order.** Klue's hardcoded structure is the practitioner default: **Headline (claim, not topic) → Rationale (why this matters now) → Comparison (us vs. them) → Implications (what this means for the company) → Recommendations (2–3 concrete actions, time-bound).** PDB articles use a bulleted variant: lead claim, 2–4 bullet evidence, optional "implications for the President" close.

**Evidence type and density.** Mixed primary and secondary, but compressed. Three to five citations per page; one or two charts at most. Heavy compression discipline — each evidence item must earn its line. Octopus Intelligence's "kill your darlings" rule applies hardest here.

**Reader persona.** CEO, VP of Strategy, Chief of Staff, founder. Time budget: 5–15 minutes, often read on phone before a meeting. The reader commits to action from this artifact alone, without follow-up. This is the artifact shape closest to the gofreddy CI lane's locked v2 Reader spec.

**Recommendation specificity.** Tactical-to-strategic action this week or this quarter. Klue's spec: "specific, actionable, tied to business impact." Product Marketing Alliance: rejects "vague statements like 'increase productivity.'" Concrete: "Reprice the SMB tier by 15% by Q3" beats "strengthen positioning."

**Failure modes.** (a) Headline as topic ("Acme Q3 Earnings Update") rather than claim ("Acme's Q3 earnings confirm the up-market pivot — defend mid-market this quarter"). (b) Length creep — drift toward 5–10 pages as the writer hedges. (c) Recommendations with no trade-off named (the wish-list failure). (d) The Phase-4 pathology rolled back at `c76f051`: framework-header templating that mimics consulting-deck format without earning it.

**AI-generation difficulty.** Medium. The compression discipline is real (LLMs default toward verbose). Concrete-action specificity is hard without fixture-specific grounding. But the form factor is well within LLM range. The gofreddy lane fixtures (DWF / Anthropic / Perplexity / Klinika) confirm: when the lane stays at 1.5–3 pages, output is recognizable as an executive briefing.

### 2.3 Sales battlecard — per-competitor, objection-handling

**Canonical exemplars.**
- **Klue's sales battlecards** (klue.com/blog/competitive-battlecards-101, klue.com/blog/sales-battlecard-templates-attack-defend) — the practitioner reference. Klue's audit of 150+ live battlecards found 100% of highest-retention cards include both talk tracks and proof points.
- **Crayon battlecards** — emphasize real-time signal injection (competitor pricing / job posting / press release changes flow into the card).
- **Kompyte, Apollo, Highspot** — variants of the same one-page form.
- **Public leaked / shared battlecards** — Salesforce, Snowflake, Datadog cards leak periodically and confirm the same structural skeleton.

**Length convention.** **One page.** "Scannable in 10 seconds while the prospect is still talking" (Klue). The one-screen-maximum rule is "non-negotiable for mid-call usage." 200–500 words. Compression is the entire point.

**Structure / sections in order.** Three canonical sections: **talking points → objection responses → trap-setting questions.** Klue's recommended framework is **Fact / Impact / Act (FIA)** — for each line: fact = the competitive insight, impact = why this matters now, act = the specific talk track. The **Know / Say / Show** alternative: what to know, what to say, what to show (proof point, customer quote, demo asset).

**Evidence type and density.** Talk tracks (verbatim sentences the rep can read). Customer quotes (verbatim attributable). Proof points (one stat or chart). Trap-setting questions ("ask them this — they can't answer well"). Citations are external materials referenced by URL or deck-asset ID, not embedded.

**Reader persona.** AE, BDR, SE, sales engineer — in or immediately before a call. Time budget: 10 seconds mid-call, 2 minutes pre-call. The reader's decision shape is unique: they need a sentence they can speak out loud, not an analysis they can think about.

**Recommendation specificity.** In-call objection response. Verbatim language. Klue's 2026 research: 71% of businesses using battlecards report improved win rates; 93% of those say the lift exceeds 20%. The artifact-success metric is per-deal win rate, measurable.

**Failure modes.** (a) Length creep — a 3-page battlecard is functionally a 0-page battlecard because the rep won't open it. (b) Strategic analysis instead of talk tracks (the rep does not need to know why Helmer's counter-positioning applies — they need the sentence). (c) Outdated competitor info (talk track that references a competitor product version superseded six months ago is worse than no card). (d) Tone mismatch (executive briefing language sounds wrong out loud — "leverage the strategic asymmetry" doesn't fit in a discovery call).

**AI-generation difficulty.** Medium-easy if the system has access to live talk-track ground truth (recordings, transcripts, win-loss data); hard without. The lane currently does not have access to sales-call ground truth, so producing a credible battlecard would be a stretch.

### 2.4 Monitoring digest — weekly snapshot, signal-driven

**Canonical exemplars.**
- **Meltwater Mira AI executive briefings** (meltwater.com/en/ai) — dashboards plus AI summaries of news, social, broadcast, podcasts, forums.
- **Cision media monitoring reports** (cision.com/resources/insights/media-monitoring-reports/) — PR-focused but adjacent to CI monitoring.
- **Brandwatch / Talkwalker** — social listening + sentiment, weekly digest cadence.
- **ReadLess Intelligence Digest** (readless.app/solutions/intelligence-digest) — "50+ intelligence sources into one strategic digest."
- **gofreddy's own `monitoring` lane** — already handles this artifact shape for gofreddy clients.

**Length convention.** Bulleted alerts (2–3 sentences each, per Unkover / Outreach guidance: "what changed, why it matters, what to do differently") OR weekly digest of 5–15 bullets plus 1–2 sentences of synthesis per bullet. Total: under 1 page; often a Slack message, email digest, or dashboard widget.

**Structure / sections in order.** Signal-classified bullets (competitor X did Y) → severity flag (red / yellow / green) → 1-sentence "what to do." Optional weekly synthesis: "themes this week." Heavy use of tables, dashboards, share-of-voice charts, sentiment trend lines.

**Evidence type and density.** Primary-source telemetry — competitor website diffs, pricing-page diffs, job posting counts, press releases, social-volume spikes, sentiment shifts. Auto-collected by tooling (Crayon, Brandwatch). Citation is the source URL; one per bullet.

**Reader persona.** Comms director, PR manager, CI manager, strategy ops analyst. Time budget: 2–5 minutes scanning, daily or weekly. Decision shape is triage: which bullets escalate to leadership, which get monitored, which get ignored. Almost never a direct strategic-commitment decision.

**Recommendation specificity.** Triage-level. "Watch this." "Escalate to VP Product." "Set alert if X breaches Y." Not strategic posture.

**Failure modes.** (a) Signal noise — too many bullets, no severity discrimination. (b) No "so what" — competitor activity logged without inference. (c) Same signal repeated across weeks because no synthesis layer compresses. (d) Sentiment-only dashboards with no behavioral signal layer.

**AI-generation difficulty.** Easy in principle, but quality is dominated by collection-pipeline quality, not synthesis quality. LLM value-add is small on triage, larger on synthesis.

**Boundary with `competitive` lane.** Monitoring digest answers "what changed last week?"; executive briefing answers "what should we do about the most consequential thing that changed?" The gofreddy `monitoring` lane should own the digest. The `competitive` lane should reject the digest shape and commit to executive briefing + teardown-grade depth on the single most-consequential development.

### 2.5 War-game memo — scenario-driven response prediction

**Canonical exemplars.**
- **McKinsey war games** (mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/playing-war-games-to-win, "bias-busters-war-games") — multi-round simulation. Teams of senior leaders + industry experts build "deeply researched profiles" of two-or-more competitors, then project likely actions across multiple consecutive periods.
- **Bain scenario analysis and contingency planning** (bain.com/insights/management-tools-scenario-and-contingency-planning) — explicit framework: identify critical uncertainties → big bets in primary scenario → strategic hedges + options → trigger points and signposts → contingency plans tied to signposts.
- **U.S. Army War College methodology** — the protocol most consulting war games inherit. Cyber-attack and innovation-strategy variants documented by McKinsey.

**Length convention.** 5–15 pages of memo plus appendices (competitor profiles, model output). The war game itself is multi-day; the memo is its compressed output. Bain's variant (contingency plan with signposts) often runs 10–25 pages with the trigger-table being the load-bearing section.

**Structure / sections in order.** Scenarios identified (2–4 named futures, e.g., aggressive-Acme / acquired-Acme / stalled-Acme) → competitor response patterns per scenario (what they'd do in each) → us-response in each scenario → signposts and triggers (early-warning signals that scenario N is materializing) → contingency commitments per trigger (pre-committed action library). The output is **the matrix of conditional commitments**, not a recommendation. McKinsey explicitly frames the deliverable as "strategic guidance on the industry's direction, the most promising types of moves... never a tactical playbook."

**Evidence type and density.** Researched competitor dossiers (per McKinsey: "deeply researched profiles of two competitors"). Simulation-model output (financial impact under each scenario). Industry-expert qualitative judgments. Trigger-signpost tables. The matrix is the evidence-organizing primitive, not the bullet list.

**Reader persona.** CEO + executive committee + scenario participants. Time budget: 1–2 hours initially; referenced repeatedly as signposts materialize. Often the reader is *also a participant* in the war game (the artifact memorializes a process the reader experienced). Decision shape: pre-commit to a contingency that activates when a trigger fires.

**Recommendation specificity.** Conditional commitments, not direct actions. "If Acme acquires X by Q3, we accelerate Y; if Acme raises prices by Z%, we hold; if regulator does W, we exit." The recommendation lives in the contingency table.

**Failure modes.** (a) Single-scenario analysis (defeats the purpose — the war game is the structured imagining of alternative futures). (b) Scenarios indistinguishable in implication (if every scenario triggers the same response, the war game was a strategic-planning exercise mislabeled). (c) Triggers that can never fire (no observable signpost). (d) Memo-only without process — the value is half the simulation, half the artifact; an AI-generated war-game memo without an actual senior-leader simulation has only the document.

**AI-generation difficulty.** Hard. The memo presupposes a multi-day senior-leader simulation; the artifact alone (without process) loses much of its decision value. LLMs can produce the structural skeleton (scenarios, response patterns, triggers) credibly, but the contingency-commitment binding requires real organizational authority the LLM lacks. Useful as a *pre-game preparation* aid (helping the CEO frame scenarios) rather than the deliverable itself.

---

## 3. Cross-shape synthesis

The five shapes form a 2x2-plus-one matrix on two axes: **time horizon** (this week → 12+ months) and **decision specificity** (in-call tactic → strategic commitment).

|                       | Tactical (in-call / this week)            | Strategic (this quarter / 12+ months)            |
|-----------------------|-------------------------------------------|--------------------------------------------------|
| **Reactive (signal-driven)** | Monitoring digest (triage)         | Executive briefing (commit-to-action)            |
| **Proactive (planning)**     | Sales battlecard (objection-response) | Strategic teardown (posture for 12–24 months)    |
| **Scenario (contingent)**    | —                                  | War-game memo (pre-commit by trigger)            |

Three of the five shapes (executive briefing, strategic teardown, war-game memo) all serve a strategic decision but at progressively wider horizons and progressively more contingent commitments. The executive briefing is the **forcing function** of the three — it forces a commit now on a single development; the teardown and war-game enrich the commitment context.

The battlecard and monitoring digest are different artifacts entirely — they serve operational decisions (call-level, triage-level) and have different success metrics (win rate, signal-to-noise). They belong in different lanes than the strategic `competitive` lane.

**Practitioner consensus on shape selection.** Klue's "layered approach" (klue.com guidance referenced across multiple posts): "Think of competitive content in layers, from quick-reference to deep-dive." Battlecards reference in calls; executive briefings drive weekly decisions; teardowns inform quarterly planning. The shapes are not substitutes; they are different products.

The shape collision the gofreddy lane risks is exactly the one Klue warns about: trying to do all of these at once with one artifact produces 60-page PowerPoints that get read by no one.

---

## 4. Recommendation for CI lane artifact shape with reasoning

**Recommendation: option (c) — one hybrid shape, executive-briefing skeleton with teardown-grade evidence depth on the single most-consequential development, optionally with 1–2 talk-track tail items when fixtures are deal-stage.**

**Reasoning.**

The locked v2 spec at `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` defines Reader as "founder-CEO or VP of Strategy at a tech-savvy company" with substitute readers including "senior partner at a professional-services firm" and "clinic operations lead." Success is defined as "the reader commits to a single specific concrete action on the most-consequential development surfaced in the brief." These two clauses point unambiguously to the executive-briefing shape (option a or c) and away from the other three:

- **Reject (a) pure executive briefing.** A pure 1–2 page briefing lacks the structural-mechanism depth CI-3 demands and the trajectory-rigor CI-2 demands. CI-3 ("Could the reader explain to their CTO in one sentence why this threat is structurally durable?") and CI-2 ("2+ independent signals required for trajectory") both presume teardown-grade evidence on the dominant threat. A pure Klue-style briefing typically does not carry that depth.

- **Reject (b) branch by decision type.** Branching adds workflow complexity (decision-type classifier upstream of the lane) without solving the underlying judge-stability problem. The four fixture clients (DWF / Anthropic / Perplexity / Klinika) span industries, not decision types — every fixture is reactive-to-signal at the strategic horizon.

- **Reject (d) decompose into 2–3 sibling lanes.** The gofreddy `monitoring` lane already owns the digest shape per the v2 spec's "NOT the reader: comms director (different decision shape — see monitoring lane)." A `competitive_battlecard` sibling lane is plausible but premature — no fixture client has asked for one, and the lane is not yet judge-stable on its current scope. Forking now would multiply judge surface area threefold before any one lane has validated on real fixtures, and the v2 spec's open question #3 (propagation to other 7 lanes) is already a backlog item.

- **Accept (c) hybrid shape.** The hybrid preserves the executive-briefing forcing-function (commit-to-action on the dominant development) while requiring teardown-grade evidence depth on the structural-mechanism question (CI-3) and war-game-flavored response logic on the trade-off question (CI-5). This matches the v2 Success spec's named exemplars: McKinsey/Bain war-game memos as ceiling (cross-industry rigor), Bloomberg/S&P sector briefs as quantitative anchor, Klue executive briefing as achievable floor. The v2 spec already names this hybrid implicitly — option (c) just makes it explicit.

**Operational form factor.** 800–2,000 words. Klue's 5-section spine (Headline / Rationale / Comparison / Implications / Recommendations) with the Comparison section deliberately deeper than Klue's default (carries the CI-3 mechanism analysis), and the Recommendations section deliberately tighter than Klue's default (carries CI-5's trade-off discipline). Trajectory analysis lives inside the Implications section, using CB Insights' WHAT-NOW / WHERE-NEXT / WHY-PRIORITY triple as scaffolding for the dominant-development analysis.

---

## 5. Specific edits to CI v2 spec

Based on option (c), three concrete edits to `docs/handoffs/2026-05-17-judge-design-step1-competitive.md`:

**Edit 1 — Add §1.5 "Artifact shape (LOCKED)" between §1 Reader and §2 Success.** Name the artifact shape explicitly:

> The brief is an **executive briefing** in form factor (≈ 800–2,000 words, Klue's 5-section spine: Headline-as-claim / Rationale / Comparison / Implications / Recommendations) with **teardown-grade structural-mechanism depth** on the dominant threat (CB Insights' WHAT-NOW / WHERE-NEXT / WHY-PRIORITY triple as the Implications-section scaffolding) and **war-game-flavored trade-off rigor** on the recommendation (Bain's signposts-and-triggers logic applied to the single most-consequential development). It is NOT a 30-page strategic teardown, NOT a one-page sales battlecard, NOT a weekly monitoring digest (that's the `monitoring` lane), and NOT a multi-scenario war-game memo. Outputs drifting toward any of those shapes should be penalized by `structural_gate`, not by criteria 1–5.

**Edit 2 — Add §3d "Shape-drift Goodhart" to the failure section.** Catalogue the failure mode the taxonomy surfaces:

> **Shape-drift Goodhart.** The workflow learns that outputs looking like a teardown (long, headered, sectioned) score well on CI-3, while ones looking like a war-game memo score well on CI-2, producing a Frankenstein artifact that drifts between shapes from fixture to fixture. Specifically: 8-page outputs with consulting-deck section headers (Mechanism of Advantage / Trajectory / Trade-offs / Scenarios), multi-scenario branching where the Reader spec requires a single committed action, or per-competitor battlecard-style talk tracks instead of strategic posture. The fix is `structural_gate` enforcing the 800–2,000 word band and rejecting consulting-deck headers and multi-scenario branching when not paired with a single committed action.

**Edit 3 — Add §1 substitute-readers note clarifying the cross-shape rejection.** Append to the existing §1 paragraph "NOT the reader":

> NOT the reader: AE preparing for a call (different artifact — sales battlecard, not currently in scope); comms director monitoring share-of-voice (different lane — `monitoring`); CEO running a multi-day war-game simulation (different artifact — war-game memo, requires process not present in this workflow).

These edits do not change any criterion text and preserve the v2 redundancy-check and fixture-validation work-in-progress. They lock the artifact shape so the next 50-generation evolution cannot drift across shapes between iterations.

---

## Sources

**Strategic teardown:**
- [CB Insights Strategy Teardown archive](https://www.cbinsights.com/research/teardown/) (Apple, Google, Amazon, Microsoft, Square)
- [Stratechery by Ben Thompson](https://stratechery.com/)
- [Equity Research Report Format (Wall Street Prep)](https://www.wallstreetprep.com/knowledge/sample-equity-research-report/)
- [Equity Research Report Samples (Mergers & Inquisitions)](https://mergersandinquisitions.com/equity-research-report/)

**Executive briefing:**
- [Klue Competitive Intelligence Reporting](https://klue.com/blog/competitive-intelligence-reporting)
- [Klue Competitive Intelligence 101](https://klue.com/blog/competitive-intelligence)
- [Klue CI Framework in 90 Days](https://klue.com/blog/competitive-intelligence-framework)
- [ArchIntel Effective Executive Briefings](https://archintel.com/competitive-intelligence/effective-executive-briefings/)
- [FullIntel Executive News Briefings](https://fullintel.com/solutions/executive-news-briefings/)
- [President's Daily Brief — Wikipedia](https://en.wikipedia.org/wiki/President%27s_Daily_Brief)
- [What I Learned Writing for the PDB — The Cipher Brief](https://www.thecipherbrief.com/column_article/what-i-learned-writing-for-the-presidents-daily-brief)
- [CIA PDB Project (declassified Kennedy/Johnson briefs)](https://www.cia.gov/resources/publications/presidents-daily-brief-delivering-intelligence-to-kennedy-and-johnson/)

**Sales battlecard:**
- [Klue Sales Battlecards 101](https://klue.com/blog/competitive-battlecards-101)
- [Klue Battlecard Templates Attack/Defend](https://klue.com/blog/sales-battlecard-templates-attack-defend)
- [Klue Objection Handling Battlecard](https://klue.com/blog/sales-battlecard-template-objection-handling-and-counterpoints)
- [Good Sales Battlecard Examples 2026 — Klue](https://klue.com/topics/good-sales-battlecard-examples)
- [Apollo Sales Battlecard Template](https://www.apollo.io/insights/sales-battlecard-template)
- [Highspot Sales Battlecard Examples](https://www.highspot.com/blog/sales-battlecards/)
- [Octopus Intelligence — Battle Cards](https://www.octopusintelligence.com/what-are-battle-cards-and-how-to-use-them-correctly/)

**Monitoring digest:**
- [Cision Media Monitoring Reports](https://www.cision.com/resources/insights/media-monitoring-reports/)
- [Meltwater Mira AI](https://www.meltwater.com/en/ai)
- [Meltwater Earned Media Monitoring](https://www.meltwater.com/en/blog/earned-media-monitoring)
- [ReadLess Intelligence Digest](https://www.readless.app/solutions/intelligence-digest)
- [Outreach CI Automation](https://www.outreach.io/resources/blog/competitive-intelligence-automation)
- [Unkover AI Competitive Intelligence 2026](https://unkover.com/blog/ai-competitive-intelligence/)

**War-game memo:**
- [McKinsey Playing War Games to Win](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/playing-war-games-to-win)
- [McKinsey Bias Busters: War Games](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/bias-busters-war-games-heres-what-theyre-good-for)
- [McKinsey CFOs and War Gaming](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/how-cfos-can-use-war-gaming-to-support-strategic-decisions)
- [McKinsey Battle-Test Your Innovation Strategy](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/battle-test-your-innovation-strategy)
- [Bain Scenario Analysis and Contingency Planning](https://www.bain.com/insights/management-tools-scenario-and-contingency-planning/)
- [Craig Quilkey — How to War Game a Business Strategy](https://www.craigquilkey.com/post/how-to-war-game-a-business-strategy)

**Cross-shape and taxonomy:**
- [Klue Competitive Intelligence Platform](https://klue.com/competitive-intelligence-platform)
- [Northr Competitive Intelligence Framework 2026](https://battlecard.northr.ai/blog/competitive-intelligence-framework)
- [SCIP Competitive Intelligence Foundational Tools](https://www.scip.org/page/Competitive-Intelligence-Foundational-Tools-and-Practices)
- [Competitive Intelligence Alliance — Delivery to Leadership](https://www.competitiveintelligencealliance.io/how-to-deliver-competitive-intelligence-to-leadership/)
- [Octopus Intelligence — How to Write a Compelling CI Report](https://www.octopusintelligence.com/how-to-write-a-good-competitive-intelligence-report/)
