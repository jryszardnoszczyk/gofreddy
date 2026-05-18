---
date: 2026-05-18
type: research deliverable
status: complete
topic: Monitoring artifact taxonomy (pager alert / weekly digest / scorecard / deep-dive memo / board-prep deck / incident-postmortem)
parent: docs/handoffs/2026-05-18-judge-design-step1-monitoring.md
sibling: docs/research/2026-05-15-judges-domain-monitoring.md
companion-to: docs/research/2026-05-18-ci-artifact-taxonomy.md
guide: docs/rubrics/judge-design-guide.md
---

# Executive-Monitoring Artifact Taxonomy

## 1. TL;DR + artifact-shape recommendation

Executive brand-and-reputation monitoring is not one artifact, the same way competitive intelligence is not one artifact. The MON lane's v0 spec at `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` implicitly nominates the **weekly executive digest** shape (FullIntel + PDB-style, 200–400 words, "what happened / why it matters / recommended action") but never says so out loud. That ambiguity is the same shape-drift Goodhart attack surface the CI lane catalogued at `docs/research/2026-05-18-ci-artifact-taxonomy.md` — under 50-generation selection pressure, the workflow will learn that an output looking like a pager alert scores well on MON-3 (highest-stakes lede) while one looking like a deep-dive memo scores well on MON-5 (cross-story compound), producing a Frankenstein digest fixture-to-fixture.

The six canonical executive-monitoring form factors are:

1. **Real-time pager alert** — single-incident, <100 words, oncall action in <1hr (PagerDuty-style for reputation events; Brandwatch / Talkwalker crisis-room alerts).
2. **Daily executive brief** — 1 page, 5–7 minutes, 3–6 items, PDB / FullIntel daily / ArchIntel 6am newsletter.
3. **Weekly executive digest** — 1–2 pages, 200–500 words, Monday-morning leadership prep, FullIntel weekly / PRWeek Weekender / Bulldog Reporter Friday.
4. **Monthly scorecard** — 2–4 pages with charts, KPI-tracked, AMEC framework + Barcelona Principles, board-adjacent.
5. **Quarterly deep-dive memo** — 5–15 pages, narrative + trend, Edelman Trust Barometer-grade decomposition, McKinsey/Bain strategy-monitoring briefs.
6. **Board-prep deck** — 8–15 slides quarterly, governance-grade summary, IR + ESG + reputation roll-up, Edelman + AMEC outcomes layer.
7. **Incident postmortem** — 3–5 pages, retrospective, NTSB / CISA / SRE postmortem traditions translated to comms.

**Recommendation: option (c), one hybrid shape — the weekly executive digest skeleton (FullIntel 200–400 words per spine item) with daily-pager severity discipline applied to lede selection (MON-3) and quarterly-memo evidence depth applied to cross-story compound + silence-as-signal (MON-5).** Specifically: the lane produces a weekly digest in length (≈ 600–1,400 words for the full digest, 3–6 items each 80–200 words) with FAA-AD-grade action items (MON-4) and Cision React Score + Sandman + Edelman-decomposed severity classification (MON-2). It does NOT produce a real-time pager alert (different cadence, different reader), NOT a board-prep deck (different governance audience), NOT a quarterly deep-dive (different decision velocity), NOT an incident postmortem (different temporal orientation — backward not forward).

The top failure mode this taxonomy surfaces that the v0 MON spec does not catch: **cadence-shape drift** — the workflow learning to inflate a digest into deep-dive length to score on MON-5 (cross-story + silence) while losing the 5-minute-read forcing function that makes the digest useful Monday morning. The fix is naming the shape AND the cadence explicitly in the spec, AND routing length-band + section-presence enforcement to `structural_gate` not to judge criteria.

---

## 2. Per-shape deep dive

### 2.1 Real-time pager alert — single-incident, oncall-driven

**Canonical exemplars.**
- **Brandwatch Vizia / Iris alerts** — crisis-room dashboards configured to push named-event alerts to mobile / Slack / PagerDuty when threshold conditions breach (sustained volume rise, sentiment cliff, traditional-media amplification per Brandwatch's published five-warning-indicator model).
- **Talkwalker Quick Search alerts** — sub-minute latency on social signal spikes, used by Deutsche Telekom's documented situation room.
- **Cision Komo / Onclusive crisis push** — analyst-curated breaking-event alerts to a duty roster.
- **PagerDuty for reputation events** — increasingly common 2024-2026 pattern of routing brand-monitoring alerts through SRE-grade pager infrastructure with named oncall.
- **AP / Reuters newsroom flash** — the journalism-side analogue: <50 words, "URGENT," delivered to terminals in <60 seconds of confirmation.

**Length convention.** **Under 100 words.** Subject line + 2–3 sentences. Mobile-first; must be readable on a phone lockscreen.

**Structure / sections in order.** Headline-as-claim (the specific incident, not a category) → one-line evidence anchor (named source, timestamp) → recommended response action (call X / hold Y / escalate to Z). No baseline framing, no severity classification beyond binary fire-or-not, no cross-story analysis. The alert presupposes the reader will pull deeper context from a dashboard.

**Signal density.** One signal, named. Citation: one source URL. The discipline is the inverse of the digest — the alert is the inverse of synthesis.

**Cadence.** Event-triggered, 24/7. Volume target: 0–3 per week in a healthy state. Above 5/week = alert-fatigue threshold per the 2025 SANS Detection and Response Survey (73% of security teams name false positives as their top detection challenge); social-listening practice has imported the SRE tuning discipline of "identifying the noisiest detection rules and disabling or refining rules with false-positive rates above 50%" (Motadata, "What Is Alert Noise Reduction?").

**Reader persona.** Communications director on oncall rotation, agency duty officer, or in-house counsel for reputational-legal events. Time budget: 30 seconds to read; 1 hour to act. Decision shape: binary — escalate to the war room, or stand down. The reader's success criterion: the alert fires only for events that would have woken them up anyway if they'd been watching live.

**Recommendation specificity.** Single named action with a single named owner. No trade-off discussion. No alternative hypotheses. The pager alert is the inverse of analytic depth: it commits to one read of the situation, accepts the false-positive risk, and routes to an owner.

**Failure modes.** (a) Alert fatigue — cried-wolf alerts train the reader to ignore the channel. Brandwatch explicitly warns: "if it's the former [a non-issue], releasing a knee-jerk public apology could draw attention to a non-issue." (b) Latency-killing length — alerts that try to be digests delay the oncall response. (c) Auto-generated alerts without analyst-in-the-loop confirmation — the Bloomberg "fat-finger flash" pattern where false positives reach decision-makers before the analyst can intercept. (d) Missing the escalation surface — alert fires to a dashboard nobody is watching at 2am.

**AI-generation difficulty.** Hard at quality. The compression discipline is real; the latency requirement is real; the confidence requirement is high (false-positive cost is alert-fatigue compounding, not just one bad email). LLM value is supporting (drafting the alert text once the human analyst confirms the incident) rather than originating (firing the alert autonomously). The MON lane does NOT and should NOT produce this artifact — it requires a separate oncall-grade infrastructure layer.

**Shape-drift Goodhart risk for MON lane.** Low — the MON lane's weekly cadence cannot accidentally produce a pager alert (different cadence forces different shape). But the inverse risk exists: under selection pressure, the workflow might learn that putting a pager-flavored "URGENT" stanza at the top of the weekly digest scores well on MON-3 (highest-stakes lede). Defensible if substance is real; performative if the urgent stanza is templated.

### 2.2 Daily executive brief — 1 page, PDB-style

**Canonical exemplars.**
- **President's Daily Brief (PDB)** — declassified Kennedy/Johnson/Nixon/Ford PDBs (CIA Reading Room, archives.gov 2015–2016 releases) confirm the shape: "rarely longer than 25 pages total," 6–7 articles "usually one paragraph to one page long," plus 2 deep-dive pieces, highest-stakes first. Bush PDB ran 6 articles + 2 deep-dives.
- **FullIntel Daily Executive Briefing** — analyst-written next-morning brief delivered by email, optimized for mobile, "200–400 words total, structured per item as (a) what happened — one sentence, no background; (b) why it matters — 1–2 sentences; (c) recommended action — one sentence" (fullintel.com).
- **ArchIntel Daily Intelligence Brief** — 6am delivery newsletter format, "1–3 pages" explicit length convention.
- **Axios PM** and **Punchbowl AM** — journalism-side analogues; "smart brevity" format with named-source anchors.
- **Bloomberg First Word** — terminal-delivered analyst summary, 200-word ceiling per item.

**Length convention.** **1–2 pages. 300–800 words total. 3–7 items.** PDB convention has been imported wholesale into PR practice; FullIntel's executive briefings are explicit about the "long briefings don't signal thoroughness — they signal poor judgment" discipline.

**Structure / sections in order.** Per-item: lead claim → 2–4 bullet evidence → optional "implications" close. No section headers across items — the digest is a sequence of compressed articles, not a slotted template. Highest-stakes article opens; second-highest follows; routine reporting compressed into a tail "also noted" stanza.

**Signal density.** 3–7 items per brief, each 1 named source minimum. Total citation count: 5–15. Mixed primary and secondary; primary preferred (named entity, dated event, specific document) — secondary acceptable when primary is restricted-access. The PDB convention is "single-source items get a confidence hedge" — applicable to comms via "per single trade-press report" or "per one named industry analyst."

**Cadence.** Daily, weekday mornings, 6–8am local. Latency: same-day for previous-day events; analyst overnight cycle assumed. Weekend handling varies — PDB ran 6 days/week historically; commercial daily briefs typically 5 days/week.

**Reader persona.** C-level or chief-of-staff, reading on phone or desktop before first meeting. Time budget: 5–10 minutes. Decision shape: triage — which items get raised in today's meetings, which get assigned, which get monitored. Action commitment is downstream of the brief, not in it.

**Recommendation specificity.** Per-item watch-status or recommended-action one-liner. Not strategic posture. Compares to the monitoring-digest shape in §2.4 below at lower cadence — the daily brief is the digest's faster cousin.

**Failure modes.** (a) Length creep — drift from 1 page toward 3–5 pages as the analyst hedges. (b) Item-count creep — drift from 5 items toward 12+ items, none individually load-bearing. (c) Verbatim repetition of yesterday's items without acknowledgment ("Day 4 of the Pinsent partner-pull aftermath, no new signal" is information; restating Monday's brief on Tuesday with no delta is noise). (d) Missing the action-status convention — items lacking a watch/escalate/stand-down tag force the reader to do the classification.

**AI-generation difficulty.** Medium. The compression discipline is the hardest part (LLMs default toward verbose). The daily cadence is operationally heavy — requires analyst-in-the-loop QA on a tight cycle. The MON lane does NOT produce this artifact today (cadence mismatch with current weekly workflow), but the daily shape is the closest cousin to the weekly digest in §2.3 and informs the per-item compression discipline.

**Shape-drift Goodhart risk for MON lane.** Medium — under selection pressure, the workflow might learn that the daily-brief shape (5–7 short items, no synthesis stanza) scores well on MON-3 (clean lede placement) while losing the weekly-cadence requirement of cross-story compound (MON-5). The fix is `structural_gate` enforcing both the length band AND the synthesis-section presence.

### 2.3 Weekly executive digest — 1–2 pages, leadership-prep

**Canonical exemplars.**
- **FullIntel Executive Weekly Briefing** — "200–400 words total, executive-briefing template targeting senior comms teams at Fortune 500" (fullintel.com/blog/executive-briefing-that-leadership-actually-reads). The MON lane's v0 Reader spec maps directly to FullIntel's stated audience.
- **PRWeek Weekender** — Friday newsletter for in-house comms leads; longer than FullIntel (typically 800–1,200 words) but with the same "synthesis over collation" discipline.
- **Bulldog Reporter Friday Roundup** — Agility PR Solutions' weekly summary; "what advanced, what resolved, what stalled" structure across continuing storylines.
- **Edelman client digests (internal)** — agency-grade weekly briefs delivered to retainer clients; structure published in Edelman's Trust Barometer methodology materials.
- **Meltwater Mira AI weekly summary** — automated weekly synthesis from collected social + earned + broadcast signal.
- **CB Insights State of (X) weekly** — adjacent shape, market-intel-flavored but same cadence.

**Length convention.** **600–1,400 words for the full digest. 3–6 items, each 80–200 words.** The MON v0 spec implicit target (5–7 minute read, leadership-briefing prep) maps to roughly 1,000 words at typical executive read speed.

**Structure / sections in order.** Highest-stakes lede (MON-3, 100–300 words with proportional structural emphasis) → 2–4 supporting items (each 80–200 words, FullIntel "what / why / action" triple) → cross-story compound + forward projection stanza (MON-5, 100–200 words) → 1–3 action items with named owner + deadline + consequence (MON-4, FAA-AD format).

The Klue 5-section spine (Headline / Rationale / Comparison / Implications / Recommendations) used in the CI lane does NOT translate directly to MON — the monitoring digest is multi-item by construction, while CI is single-development. The PDB multi-article-then-deep-dive structure is the better fit.

**Signal density.** Per-item: 1–3 citations. Total digest: 8–20 citations. Mix is heavy on baseline-relative framing (Brandwatch alerts guidance: "establish benchmarks that define what a normal level of negativity online looks like") — every quantitative claim paired with a comparator. Per Cision's React Score practice: dual-axis severity (Harm + Emotionality) on the top 3–5 items. Per Edelman Trust Barometer: competence-vs-ethics decomposition on reputation-axis events.

**Cadence.** Weekly. Monday morning is the modal delivery (FullIntel default, MON v0 default) — supports the Monday leadership-briefing prep use case. Friday delivery (PRWeek, Bulldog) supports end-of-week consolidation. Mid-week delivery is anomalous and typically signals an off-cadence crisis trigger rather than a routine digest.

**Reader persona.** Senior communications director or PR lead at a Series-B-or-later company ($30M+ ARR) per the v0 spec. Substitute readers per v0: "founder/CEO of an earlier-stage company with no in-house comms; agency lead reading on behalf of multiple clients; in-house counsel monitoring reputational legal exposure." Time budget: 5–7 minutes. Decision shape: walk into the leadership briefing with (a) the single most-important development, (b) the action list for the week, (c) awareness of compound + silence.

**Recommendation specificity.** Per-week action set (1–3 items). FAA-AD format: named owner + specific deadline + consequence-of-inaction. Not strategic posture (that's deep-dive); not in-call objection response (that's CI battlecard). The week is the forcing-function horizon.

**Failure modes.** (a) Clip dump — competitor activity log with no interpretation. (b) Buried lede — position-one driven by volume rather than stakes. (c) Alert fatigue — every uptick framed as crisis. (d) Action items reduced to "should continue to monitor." (e) Cross-story compounds missed — competitor product launch + regulator letter shown separately. (f) Silence-as-signal absent. (g) Sentiment-only severity classification (single-axis, missing the Cision dual-axis Harm + Emotionality discipline). (h) Length creep beyond 1,400 words drifts the artifact toward deep-dive memo shape.

**AI-generation difficulty.** Medium. The compression discipline is real but tractable. The "so what" interpretation that FullIntel names as the digest-vs-clip-dump differentiator is the LLM-hard part — requires understanding what changes the reader's behavior, not just what changed in the data. Cross-story compound (MON-5) is the hardest dimension to fake — it requires genuinely connecting two developments that the data does not connect for you.

**This is the LOCKED shape for the MON lane.** See §4.

### 2.4 Monthly scorecard — KPI-tracked, AMEC framework

**Canonical exemplars.**
- **AMEC Integrated Evaluation Framework dashboards** (amecorg.com/amecframework) — operationalized as monthly scorecards by mid-tier agencies and larger in-house teams; tracks outputs → out-takes → outcomes → organizational impact.
- **Barcelona Principles V4.0 reporting** (amecorg.com Barcelona V4.0) — the canonical "measure outcomes, not outputs" framework; explicit warning that "AVE is not the value of public relations."
- **Cision / Meltwater monthly reports** — vendor-default tier, typically 4–8 pages, share-of-voice trend lines + sentiment trend + tier-1-coverage volume + competitive comparison.
- **PRSA Measurement Standards** — industry-association-defined monthly KPI set.
- **Edelman monthly client KPI roll-ups** — agency-grade, often delivered alongside Quarterly Deep Dive.

**Length convention.** **2–4 pages. 800–1,800 words plus 4–8 charts.** Heavier on visualization than the weekly digest. Cover-page summary common.

**Structure / sections in order.** Executive summary (1 page) → KPI scorecard with month-over-month deltas (1 page, charts-heavy) → top 3–5 narrative developments (1 page, prose) → forward-look + risk register (½ page) → methodology notes (½ page, often as appendix).

**Signal density.** Lower per word than the weekly digest — much of the page is occupied by charts, scorecard tables, methodology notes. Citations: 10–25. Heavy on aggregate metrics (SoV, sentiment trends, tier-1 coverage volume) rather than per-incident narrative.

**Cadence.** Monthly. Often delivered on the 5th–10th of the following month. Aligned to fiscal-month or comms-team-review cycle. Decision velocity: medium — input to month-end review meetings, but not the forcing function for any single action.

**Reader persona.** VP of Communications, Chief Marketing Officer, agency account director presenting to client retainer-review meetings. Substitute reader: board observer / governance lead reviewing the comms-function performance. Time budget: 15–30 minutes; often presented in a meeting rather than read solo. Decision shape: review cycle — is the comms function on-track, what gets re-resourced.

**Recommendation specificity.** Resource-allocation level. "Increase budget on X channel," "rotate the editorial focus toward Y theme," "pause investment in Z." Not weekly tactical; not quarterly strategic. The month is the resource-rebalancing horizon.

**Failure modes.** (a) AVE-leading reports (Barcelona Principles' canonical violation — "AVE is not the value of public relations"). (b) Output-only reporting without out-take / outcome layers. (c) Chart-junk — visualizations that obscure rather than reveal. (d) Methodology-drift — undocumented changes to KPI definitions month-over-month making trend lines meaningless. (e) Scorecard becomes performative — the same green ticks every month regardless of underlying state. (f) Backward-looking — heavy on last month, thin on forward-look.

**AI-generation difficulty.** Medium-hard. Chart-generation requires structured data infrastructure beyond raw LLM. KPI methodology consistency requires a fixed measurement spec the LLM doesn't get to mutate. AMEC-grade outcome translation (from out-take to outcome) requires linking comms signal to organizational impact data the LLM typically lacks. The MON lane does NOT produce this artifact today — different cadence, different data infrastructure, different reader.

**Shape-drift Goodhart risk for MON lane.** Low-medium — under selection pressure, the workflow might learn that adding a "KPI snapshot" stanza to the weekly digest scores well on MON-2 (severity classification) by performing AMEC-grade rigor without actually carrying it. The fix is `structural_gate` rejecting chart-stanzas in the weekly digest (different artifact, different lane scope), and the judge resisting the "this stanza looks rigorous, score 1" temptation.

### 2.5 Quarterly deep-dive memo — narrative + trend

**Canonical exemplars.**
- **Edelman Trust Barometer quarterly slice reports** (edelman.com/trust) — annual flagship + quarterly slice deliverables decomposing competence vs ethics across 28-country panel.
- **McKinsey/Bain monitoring-into-strategy briefs** — quarterly cadence; often delivered as part of strategic retainer.
- **Bloomberg Intelligence sector briefs** — quarterly cross-company analysis (industry-monitoring flavored, but reputation/competitive-position adjacent).
- **PRovoke Media Crisis Review** (provokemedia.com/focus/crisis-review) — annual but with quarterly slice analyses; named-case post-mortem tradition.
- **CB Insights State of (Industry) reports** — quarterly cadence, longer-form synthesis of weekly-cadence signal.
- **Gartner / Forrester analyst monitoring briefs** — quarterly cadence, vendor + market-position assessment.

**Length convention.** **5–15 pages. 3,000–8,000 words. Charts + tables + named-case anchors.**

**Structure / sections in order.** Executive summary (1 page) → quarter-in-review narrative (2–4 pages, prose-heavy, named developments) → trend analysis (2–4 pages, chart-supported) → forward-look + risk register (1–2 pages) → appendix (methodology, source list).

**Signal density.** High per page on synthesis, lower per page on raw signal. Citations: 30–100+. Heavy on primary research (proprietary surveys, panel data, structured interviews). Edelman Trust Barometer's 28-country, 32,000-respondent panel is the canonical example of evidence depth the quarterly format expects.

**Cadence.** Quarterly. Delivered 4–8 weeks after quarter-end. Decision velocity: low — input to quarterly strategy review, board-prep cycle. The quarterly is the strategic-rebalancing horizon.

**Reader persona.** C-level executive committee, board, retainer-client senior team. Time budget: 1–2 hours, often consumed across sittings. Often presented in a multi-hour quarterly review meeting; the memo is the artifact participants reference during and after.

**Recommendation specificity.** Strategic posture. "Reposition the brand voice on X theme," "rebuild the regulator-relations function," "exit the Y narrative." Not tactical, not weekly. The quarter is the strategic-pivot horizon.

**Failure modes.** (a) Length without point of view — the descriptive trend report that doesn't commit to a thesis. (b) Backward-looking — heavy on last quarter, thin on next quarter. (c) Synthesis without primary evidence — the LLM-prone failure where prose claims rest on no traceable signal chain. (d) Confusing narrative description with strategic recommendation (Porter's "operational effectiveness vs strategic positioning" trap, imported to comms). (e) Citation density without verification — fabricated quote attributions, dead URLs (the AI-specific failure surface documented at `docs/research/2026-05-18-ci-ai-failure-modes.md`).

**AI-generation difficulty.** Hard. Length punishes hallucination compounding the same way teardown-shape does for CI. Requires deep primary-source retrieval (named-case research, panel-data analysis, primary interview synthesis). LLM value is supporting (drafting structure, surfacing patterns across collected signal) rather than originating end-to-end. The MON lane does NOT produce this artifact today — different cadence, different evidence-depth requirement.

**Shape-drift Goodhart risk for MON lane.** Medium-high — under selection pressure, the workflow might learn that expanding a digest item into deep-dive-flavored 800-word prose stanzas scores well on MON-5 (cross-story compound depth) while losing the 5-minute-read forcing function. This is the inverse of the CI lane's "Frankenstein hybrid" risk. The fix is `structural_gate` enforcing the 600–1,400 word total band on the weekly digest, and rejecting per-item lengths over 250 words.

### 2.6 Board-prep deck — governance-grade summary

**Canonical exemplars.**
- **Corporate board reputation/ESG roll-ups** — quarterly cadence, 8–15 slides, presented by Chief Communications Officer to the audit / governance committee.
- **Harvard Law School Forum on Corporate Governance — Narrative Contradictions framework** (corpgov.law.harvard.edu/2025/09/13/narrative-contradictions-the-invisible-governance-risk/) — the canonical reference for what board-level reputation monitoring is supposed to surface.
- **Edelman Trust Barometer board materials** — agency-grade board-prep slides distilled from the quarterly Trust Barometer.
- **Major-bank ESG / reputation board reports** — public-disclosure-adjacent versions visible in proxy filings and ESG appendices.
- **Investor Relations reputation roll-ups** — IR teams' quarterly deck variants, blending sell-side perception with reputation-monitoring signal.

**Length convention.** **8–15 slides. ~400–800 words on the deck itself; 1–2 pages of speaker notes per slide.** The deck is companion to a live presentation, not standalone reading material.

**Structure / sections in order.** Cover + agenda (1 slide) → quarter executive summary (1 slide) → KPI scorecard (1–2 slides, chart-heavy) → top 3 reputation events with governance implications (3–4 slides) → forward risk register (1–2 slides) → recommendations to the board (1 slide) → appendix (methodology, source list, full data).

**Signal density.** Low per slide (presentation-grade compression); high per speaker-notes block. The deck-vs-speaker-notes ratio is load-bearing — the deck is for the room, the speaker notes are for the prepared briefing.

**Cadence.** Quarterly, aligned to board meeting cycle. Decision velocity: very low — input to governance oversight; rarely the forcing function for an immediate action. When it IS the forcing function, the trigger is typically a Narrative Contradictions-style "the board has been missing a structural reputation risk" surface event.

**Reader persona.** Board of directors, audit / governance committee, executive committee. Time budget: 15–30 minutes presentation + 30 minutes Q+A. Decision shape: governance oversight — accept the comms function's read of the quarter, request follow-up, escalate.

**Recommendation specificity.** Board-decision level. "Ratify the reputation-risk register," "approve the crisis-comms playbook update," "commission a specific deeper review." Not operational.

**Failure modes.** (a) Slide-count creep — 25-slide decks become 60-slide decks become "appendices nobody reads." (b) Chart-junk — visualizations that obscure rather than reveal at presentation distance. (c) Single-axis severity (Cision dual-axis discipline lost in board-deck simplification). (d) Narrative Contradictions blind spots — the board-level governance risk where reputation signal contradicts a publicly-stated narrative and the deck doesn't surface it. (e) Performative scorecards — every quarter green-tick regardless of state (the comms-function-self-protection failure mode).

**AI-generation difficulty.** Hard. The deck format requires presentation-grade compression different from prose compression. The speaker-notes layer requires deep understanding of which board members care about which dimensions. Board-decision-shape recommendations require organizational context the LLM lacks. The MON lane does NOT produce this artifact — different audience, different cadence, different governance shape.

**Shape-drift Goodhart risk for MON lane.** Low — different format (slide-shaped vs prose-shaped); the workflow can't accidentally produce a slide deck from the digest skeleton.

### 2.7 Incident postmortem — retrospective, NTSB-style

**Canonical exemplars.**
- **NTSB accident reports** (ntsb.gov) — the canonical incident-postmortem format imported into multiple industries; sections: factual narrative, analysis, probable cause, recommendations.
- **CISA cybersecurity incident reports** (cisa.gov) — adjacent format for security incidents; published findings shape the corporate-postmortem template.
- **Google SRE postmortem template** (sre.google/sre-book/postmortem-culture) — the operational tech-industry import: blameless postmortem, what-happened, impact, root cause, action items, learnings.
- **Crisis-comms after-action reviews** — internal-circulation post-mortems following named incidents. Tylenol (1982), Tylenol-revisited (2026 retrospectives), BP Deepwater Horizon, Wells Fargo, Boeing 737 MAX, SVB — each generated an after-action document tradition.
- **PRovoke Media annual Crisis Review** — public-facing post-mortem tradition; serves as a teaching corpus for the genre.

**Length convention.** **3–5 pages. 1,500–3,500 words.** Plus appendices for the deeper-dive cases (timeline, source-document index, supporting interviews).

**Structure / sections in order.** Incident summary (½ page) → factual narrative timeline (1 page) → analysis: what worked, what failed (1 page) → root-cause attribution (½ page) → recommendations for prevention / detection / response (½ page) → appendices (timeline, sources, contributors).

**Signal density.** High on primary signal (interviews, internal logs, dated communications). Citations: 20–50+. Heavy on timeline anchoring — every claim pinned to a dated event.

**Cadence.** Event-triggered, 2–8 weeks post-incident. Not a routine cadence. Decision velocity: medium — feeds into preventive-controls update, playbook revision, training refresh.

**Reader persona.** Crisis team, executive committee, sometimes board (escalated cases). Time budget: 30–60 minutes. Decision shape: extract learnings, update preventive infrastructure, close out the incident formally.

**Recommendation specificity.** Process / playbook / training updates. "Update the crisis-team escalation tree to include legal-counsel direct contact," "add the social-volume-spike trigger to the alert configuration," "train the duty roster on the new template." Not strategic posture.

**Failure modes.** (a) Blame-driven narrative (defeats the SRE blameless-postmortem discipline). (b) Action items without owners — same FAA-AD failure as in the weekly digest, but with longer-horizon consequences. (c) Closed-out incidents that didn't actually close (the BP Deepwater Horizon pattern where the engineering postmortem missed the cultural root cause). (d) Postmortem-as-self-protection — the document that absolves the comms function regardless of underlying performance.

**AI-generation difficulty.** Medium-hard. Timeline construction from raw signal is LLM-tractable. Root-cause analysis requires organizational context. Recommendation specificity requires playbook-state knowledge. The MON lane does NOT produce this artifact — different orientation (backward not forward), different trigger (event not cadence), different decision shape.

**Shape-drift Goodhart risk for MON lane.** Low-medium — under selection pressure, the workflow might learn that adding "lessons from last week" retrospective stanzas to the weekly digest scores well on MON-5 (cross-story arc) while losing the forward-projection forcing function. The fix is `structural_gate` enforcing forward-projection presence (MON-5 requirement) and the judge resisting "this stanza looks reflective, score 1" temptation.

---

## 3. Cross-shape synthesis — decision velocity × signal density matrix

The seven shapes form a 3x3 matrix on two axes: **decision velocity** (hours → quarters) and **signal density per word** (compressed-headline → full-evidence-depth).

|                              | <1hr action | Weekly action | Quarterly strategy |
|------------------------------|-------------|---------------|--------------------|
| **Headline-only compression** | Pager alert (§2.1) | — | — |
| **Multi-item brief**         | Daily exec brief (§2.2) | Weekly digest (§2.3) | Monthly scorecard (§2.4) |
| **Narrative depth**          | — | — | Quarterly deep-dive (§2.5) / Board-prep deck (§2.6) |
| **Retrospective**            | — | — | Incident postmortem (§2.7) |

The weekly digest sits in the matrix's center — fast enough to be the action-forcing function for a Monday meeting, dense enough to carry interpretation that a pager alert cannot. It is the shape the MON v0 spec implicitly nominates.

**Practitioner consensus on cadence selection.** FullIntel's stated taxonomy: daily for monitoring teams in active-watch mode; weekly for senior comms leadership; monthly for board governance. Brandwatch and Talkwalker offer all three cadences as configurable in their dashboards but treat the weekly as the modal executive deliverable. AMEC Barcelona Principles V4.0 explicitly recommends "fit cadence to decision rhythm" — daily for ops, weekly for leadership, monthly for governance, quarterly for strategy.

**The shape-collision risk for the MON lane** is exactly the Klue 60-page-PowerPoint warning translated to monitoring: trying to do all of these at once with one artifact produces an 1,800-word "weekly digest" that nobody reads Monday morning, nobody references quarterly, nobody escalates from when a pager alert was needed.

---

## 4. LOCKED form-factor recommendation for MON lane

**Recommendation: option (c) — hybrid shape, weekly executive digest skeleton with pager-grade severity discipline on lede selection and quarterly-grade evidence depth on cross-story compound + silence-as-signal.**

**Operational form factor.**

- **Total length:** 600–1,400 words. Hard ceiling 1,500 words enforced by `structural_gate`. Hard floor 400 words — below this, the digest is operating in pager-alert mode and should be flagged as off-cadence.
- **Item count:** 3–6 items. Hard ceiling 7. The pager-alert escape valve (single-item digest with explicit "no other developments warrant weekly-cadence treatment") is allowed and should be supported, not penalized.
- **Per-item length:** 80–250 words. Hard ceiling 300 words enforced — exceeding this drifts toward deep-dive shape.
- **Cadence:** Weekly. Monday-morning delivery (8am local) is the modal target. Cadence-drift (mid-week off-cycle digest without explicit crisis-trigger justification) is a `structural_gate` rejection.

**Structural skeleton (enforced by `structural_gate`, not by judge):**

1. **Highest-stakes lede** (MON-3). 100–300 words. Proportional structural emphasis. Position 1, no exception. If nothing extraordinary happened, position 1 says so plainly.
2. **2–4 supporting items.** FullIntel "what happened / why it matters / recommended action" triple per item.
3. **Cross-story compound + silence-as-signal stanza** (MON-5). 100–200 words. At least one named compound, at least one forward projection, at least one absence flagged.
4. **Action item set** (MON-4). 1–3 items, each with named owner + specific deadline + consequence-of-inaction in FAA-AD format.

**Severity-classification scaffolding (judge tests, structural_gate doesn't):**

- **Cision React Score dual-axis** (Harm + Emotionality) on top 3–5 items — MON-2.
- **SCCT cluster** (Coombs victim / accidental / intentional) when classifying competitor crises — informs the analytic reasoning, never named in prose.
- **Edelman Trust Barometer decomposition** (competence vs ethics axis) on trust-impact events — informs the analytic reasoning.
- **Sandman Risk = Hazard + Outrage** when distinguishing high-volume-low-stakes from low-volume-high-stakes — informs the lede-selection reasoning at MON-3.

**Baseline-relative framing (MON-1):** every quantitative claim paired with explicit comparator (4-week trailing average, peer set, expected-given-event).

**Out-of-scope shapes (the MON lane will NOT produce these):**

- Real-time pager alert (different cadence, different oncall infrastructure, different reader)
- Daily executive brief (different cadence, different operational rhythm)
- Monthly scorecard (different cadence, different chart-data infrastructure)
- Quarterly deep-dive memo (different cadence, different evidence-depth requirement)
- Board-prep deck (different format, different governance audience)
- Incident postmortem (different orientation — backward not forward, different trigger — event not cadence)

**Decision-class scope:** the hybrid serves the **weekly-action cluster** — comms director walking into the Monday leadership briefing with the week's actions assigned. Sibling shapes (daily, monthly, quarterly, board, postmortem) are deferred to future lane work; current spec scopes to weekly only.

**Empirical validation scope.** The hybrid form factor is research-grounded against the v0 Reader spec (senior comms director at Series-B-or-later, $30M+ ARR) and the v0 substitute readers (founder/CEO at earlier-stage with no in-house comms, agency lead, in-house counsel). When fixtures from new reader segments appear (governance lead reading for the board, IR lead reading for investor day, regulatory-affairs lead reading for filings), re-validate the form factor — different reader segments may need shape adjustments analogous to the CI lane's vertical re-validation pattern.

---

## 5. Shape-drift Goodhart surfaces specific to MON

Each shape adjacent to the locked weekly digest creates a specific shape-drift attack surface under 50-generation selection pressure. Catalogue:

**Drift toward pager alert (§2.1).** Workflow learns that a 50-word "URGENT" stanza at top of digest scores well on MON-3 (highest-stakes lede). Defensible if substance is real; performative if templated. **Defense:** judge tests whether the urgent-stanza substance survives the "would the reader actually have wanted to be paged on this" sleep test; `structural_gate` enforces minimum first-item length of 100 words to prevent pager-style headline-only items.

**Drift toward daily exec brief (§2.2).** Workflow learns that 5–7 short items with no synthesis stanza scores well on MON-3 (clean lede placement) while shortcutting MON-5 (cross-story compound). **Defense:** `structural_gate` enforces synthesis-stanza presence; judge MON-5 tests substance not presence.

**Drift toward monthly scorecard (§2.4).** Workflow learns that adding a "KPI snapshot" stanza with charts/tables (or chart-emulating ASCII) scores well on MON-2 (severity classification) by performing AMEC-grade rigor without carrying it. **Defense:** `structural_gate` rejects table-heavy formatting; judge MON-2 tests dual-axis reasoning substance.

**Drift toward quarterly deep-dive (§2.5).** Workflow learns that expanding 2–3 items to 600-word each scores well on MON-5 (cross-story compound depth). This is the highest-risk drift surface — the inverse of the CI lane's Frankenstein-hybrid risk. **Defense:** `structural_gate` enforces total word band (600–1,400) AND per-item ceiling (300 words); judge MON-5 tests connection substance not stanza length.

**Drift toward incident postmortem (§2.7).** Workflow learns that "lessons from last week" retrospective stanzas score well on MON-5 (cross-story arc continuity) while losing forward-projection (MON-5's forward dimension). **Defense:** `structural_gate` enforces forward-projection presence within the cross-story stanza; judge MON-5 tests projection is falsifiable in 1–2 weeks.

**Additional MON-specific drift surfaces (not shape-adjacent):**

- **Digest bloat.** Workflow learns that longer = more rigorous. Hard length cap in `structural_gate` (1,500 words ceiling, 250 per-item ceiling) defends.
- **Alert-fatigue from over-promotion to pager-style.** Workflow learns that "CRISIS" / "URGENT" tags score well on MON-2 even when reasoning doesn't carry. Judge MON-2 tests orthogonal-dimension reasoning substance; structural_gate counts "URGENT"-style tags and flags >2/digest as suspicious.
- **Scorecard that becomes performative.** Workflow learns that every-item-tagged-MEDIUM scores well on MON-2 by performing severity discipline without carrying it. Judge MON-2 tests reasoning is interrogable, not just present.
- **Forced cross-story compound.** Workflow learns that adding a "Cross-Story Patterns" section scores well on MON-5 even with weak connections. Judge MON-5 tests substance.
- **Silence-as-signal performance.** Workflow learns that adding "expected X did not materialize" lines scores well on MON-5 even with fabricated expected-Xs. Judge MON-5 tests the named-absent signal was actually expected (defensible reasoning, not fabricated).

---

## 6. Specific edits to MON v0 spec

Based on the LOCKED form-factor recommendation, three concrete edits to `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md`:

**Edit 1 — Add §1.5 "Artifact shape (LOCKED)" between §1 Reader and §2 Success.** Name the artifact shape explicitly, parallel to the CI lane's §1.5:

> The lane produces ONE hybrid monitoring-digest format. Locked because shape-drift Goodhart is a documented failure mode in evolution loops: under 50-generation selection pressure, the workflow learns that an output looking like a pager alert scores well on MON-3 while one looking like a deep-dive memo scores well on MON-5, producing a Frankenstein digest. The lock prevents this.
>
> **Form factor:** 600–1,400 words total. 3–6 items, 80–250 words each. Weekly cadence, Monday-morning delivery. Structural skeleton: highest-stakes lede (100–300 words) → 2–4 supporting items (FullIntel what/why/action triple) → cross-story compound + silence-as-signal stanza (100–200 words) → 1–3 action items in FAA-AD format.
>
> **Out of scope shapes:** real-time pager alert (different cadence + infrastructure), daily executive brief (different cadence), monthly scorecard (different cadence + data infrastructure), quarterly deep-dive memo (different cadence + evidence depth), board-prep deck (different format + audience), incident postmortem (different orientation — backward not forward).

**Edit 2 — Add §3c "Shape-drift Goodhart" to the failure section.** Catalogue the failure modes this taxonomy surfaces:

> **Shape-drift Goodhart.** Under selection pressure the workflow learns: 50-word "URGENT" stanzas score on MON-3 (pager-alert drift); 5-item-no-synthesis structure scores on MON-3 while shortcutting MON-5 (daily-brief drift); table-heavy "KPI snapshot" stanzas score on MON-2 (scorecard drift); 600-word-per-item depth scores on MON-5 (deep-dive drift, highest-risk); retrospective "lessons from last week" stanzas score on MON-5 while losing forward-projection (postmortem drift). Defense: `structural_gate` enforces total word band, per-item ceiling, structural skeleton; judges test substance not presence at MON-2 and MON-5.

**Edit 3 — Append to §1 substitute-readers note:**

> NOT the reader at this cadence: oncall duty officer reading a pager alert (different infrastructure, different decision velocity — sub-1hr); board observer reading the quarterly governance roll-up (different audience, different evidence depth); crisis-team lead reading the post-incident after-action review (different orientation — backward not forward).

These edits do not change any criterion text (MON-1 through MON-5 stay locked at v0 prose). They lock the artifact shape so the next 50-generation evolution cannot drift across shapes between iterations, matching the CI lane's pattern.

---

## 7. Open questions

1. **Cadence-fixture coverage.** Current fixtures cover the weekly cadence well; daily / monthly / quarterly cadences are not represented in fixture data. If MON lane scope ever expands to additional cadences, sibling-lane treatment (separate lanes per cadence) is the more honest expansion than per-cadence flag on the same lane. Defer until fixture demand surfaces.

2. **Low-volume week handling.** v0 spec flags this as open question #2. The taxonomy provides a defensible answer: low-volume weeks should produce a single-item-pager-style digest with explicit "no other developments warrant weekly-cadence treatment," and `structural_gate` should permit (not penalize) the off-floor word count when accompanied by that explicit statement. This is the inverse of cadence-drift toward pager-alert — it's an explicit operator escape valve, not a workflow drift.

3. **Crisis-trigger off-cadence digest.** Adjacent to low-volume handling: when a genuine crisis triggers a Tuesday-afternoon digest (not Monday-morning), how does the lane handle the cadence-drift? Two options: (a) crisis-trigger drops the off-cadence digest entirely into pager-alert territory and the MON lane refuses (different artifact); (b) MON lane supports crisis-trigger digests with explicit justification stanza. Recommend (a) — keeps the MON lane scope clean; crisis-pager work is a separate workflow concern.

4. **Multi-client agency digest variant.** v0 substitute reader #2 ("agency lead reading on behalf of multiple clients"). Does the digest cover one client per digest, or multiple-clients-per-digest? Recommend one-client-per-digest as the modal case (preserves the lede-discipline forcing function), with multi-client roll-up explicitly out-of-scope (would require separate aggregation layer).

5. **Cross-lane shape coordination with CI.** The CI lane's hybrid shape and the MON lane's hybrid shape are both Frankenstein-by-design at different cadences. As both lanes evolve, cross-pollination risk: CI workflow learns from MON's "what happened / why it matters / recommended action" triple structure or vice versa, drifting both lanes' outputs toward a shared median shape. Defense: each lane's `structural_gate` should test for its own out-of-scope shapes explicitly (CI rejects digest-shape outputs; MON rejects single-development executive-briefing-shape outputs).

6. **Propagation to other 6 lanes.** Once MON v0+§1.5 validates on real fixtures, propagate the artifact-taxonomy pattern: GEO → MA → SB → X → LI → site_engine. Each lane gets its own taxonomy research (different reference exemplars, different shape-drift surfaces). The 6 monitoring-cadence shapes here are not directly transferable to other lanes — they're domain-specific to brand/reputation monitoring.

7. **First-cohort overfitting watch.** The Reader / Success / Failure spec for MON is grounded against gofreddy first-cohort clients (DWF legal, Klinika healthcare, Anthropic / Perplexity AI-lab). Cadence and shape expectations may not generalize to verticals not yet in the fixture set (DTC e-commerce comms, fintech regulator-monitoring, hospitality reputation-monitoring, regulated-finance investor-relations). Re-validation trigger: any fixture from a vertical not in {legal-services, AI-lab, healthcare, B2B-SaaS} should prompt a quick re-validation pass on the locked form factor.

---

## 8. Citations

**Real-time pager alert:**
- [Brandwatch Vizia / Iris alerts](https://www.brandwatch.com/blog/use-alerts-crisis-management/)
- [Talkwalker Deutsche Telekom situation room case study](https://www.talkwalker.com/resource/case-studies/deutsche-telekom-real-time-crisis-management-using-a-social-listening-powered-situation-room)
- [Cision Komo / Onclusive crisis push (Onclusive overview, Decide)](https://decidesoftware.com/airpr/)
- [SANS 2025 Detection and Response Survey (via Vectra)](https://www.vectra.ai/topics/alert-fatigue)
- [Motadata, "What Is Alert Noise Reduction?"](https://www.motadata.com/blog/alert-noise-reduction)
- [IBM, "What Is Alert Fatigue?"](https://www.ibm.com/think/topics/alert-fatigue)

**Daily executive brief:**
- [President's Daily Brief — Wikipedia](https://en.wikipedia.org/wiki/President%27s_Daily_Brief)
- [CIA Reading Room — PDB 1961-1969](https://www.cia.gov/readingroom/collection/presidents-daily-brief-1961-1969)
- [intelligence.gov — What is the PDB?](https://www.intelligence.gov/publics-daily-brief/presidents-daily-brief)
- [FullIntel Daily Executive Briefing](https://fullintel.com/solutions/executive-news-briefings/)
- [FullIntel — How to Write an Executive Briefing That Leadership Actually Reads](https://fullintel.com/blog/executive-briefing-that-leadership-actually-reads/)
- [ArchIntel Effective Executive Briefings](https://archintel.com/competitive-intelligence/effective-executive-briefings/)

**Weekly executive digest:**
- [FullIntel Executive Weekly Briefing](https://fullintel.com/blog/executive-briefing-that-leadership-actually-reads/)
- [PRWeek US newsletters](https://www.prweek.com/us/email-bulletins)
- [Bulldog Reporter — Agility PR Solutions](https://www.agilitypr.com/about-bulldog-reporter/)
- [Meltwater Mira AI](https://www.meltwater.com/en/ai)
- [Meltwater PR Monitoring guide](https://www.meltwater.com/en/blog/pr-monitoring)
- [Brandwatch crisis management dashboard](https://www.brandwatch.com/blog/crisis-management-how-to-deal-with-a-crisis/)

**Monthly scorecard + AMEC framework:**
- [AMEC Integrated Evaluation Framework](https://amecorg.com/amecframework/)
- [AMEC Barcelona Principles V4.0](https://amecorg.com/wp-content/uploads/2025/06/Barcelona-Principles-V4.0-%E2%80%93-FINAL30.6-compressed.pdf)
- [AMEC, PR Measurement in 2026](https://amecorg.com/2026/03/pr-measurement-meaningful-outcomes/)
- [Wikipedia — Barcelona Principles](https://en.wikipedia.org/wiki/Barcelona_Principles)
- [Cision Media Monitoring Reports](https://www.cision.com/resources/insights/media-monitoring-reports/)
- [PRSA — Crisis Communication Lessons from Boeing 737 MAX](https://www.prsa.org/article/crisis-communication-lessons-from-boeing-s-737-max-tragedies)

**Quarterly deep-dive memo:**
- [Edelman Trust Barometer](https://www.edelman.com/trust/trust-barometer)
- [Edelman 2026 Trust Barometer Global Report](https://www.edelman.com/sites/g/files/aatuss191/files/2026-01/2026%20Edelman%20Trust%20Barometer%20Global%20Report_Final.pdf)
- [Edelman — Competence Is Not Enough](https://www.edelman.com/research/competence-not-enough)
- [PRovoke Media — PR Crisis & Business Crisis Review](https://www.provokemedia.com/focus/crisis-review)
- [PRovoke / Holmes Report agency profile](https://www.provokemedia.com/agency-playbook/agency-profile/the-holmes-report)
- [Bloomberg Intelligence (general reference)](https://www.bloomberg.com/professional/products/bloomberg-intelligence/)
- [Gartner — Magic Quadrant methodology](https://www.gartner.com/en/research/methodologies/magic-quadrants-research)

**Board-prep deck:**
- [Harvard Law School Forum on Corporate Governance — Narrative Contradictions](https://corpgov.law.harvard.edu/2025/09/13/narrative-contradictions-the-invisible-governance-risk/)
- [Harvard Law School Forum — Boeing 737 MAX governance review](https://corpgov.law.harvard.edu/2024/06/06/boeing-737-max/)
- [Edelman Trust Barometer methodology page](https://www.edelman.com/trust/our-methodology)
- [Directors & Boards — Wells Fargo Fake-Accounts Scandal](https://www.directorsandboards.com/board-composition/education-and-orientation/singlewells-fargo-fake-accounts-scandal/)
- [NACVA — Fake Accounts Scandal at Wells Fargo](http://web.nacva.com/JFIA/Issues/JFIA-2022-No2-11.pdf)

**Incident postmortem:**
- [NTSB accident reports](https://www.ntsb.gov/investigations/Pages/AviationReports.aspx)
- [CISA cybersecurity advisories](https://www.cisa.gov/news-events/cybersecurity-advisories)
- [Google SRE Book — Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)
- [PBS NewsHour — Tylenol murders 1982](https://www.pbs.org/newshour/health/tylenol-murders-1982)
- [Time — Tylenol Poison Spree 1982 case study](https://time.com/3423136/tylenol-deaths-1982/)
- [Wikipedia — Chicago Tylenol murders](https://en.wikipedia.org/wiki/Chicago_Tylenol_murders)
- [HBS — Johnson & Johnson Tylenol Tragedy](https://www.hbs.edu/faculty/Pages/item.aspx?num=17858)
- [PBS — Deepwater Horizon warning signs ignored](https://www.pbs.org/newshour/science/review-indicates-warning-signs-ignored-ahead-of-rig-explosion)
- [Peter Sandman — BP Deepwater Horizon communication response](https://www.psandman.com/articles/deepwater.htm)
- [Bryghtpath — Deepwater Horizon case study](https://bryghtpath.com/deepwater-horizon-case-study/)
- [ISOC — SVB case study](https://www.isoc.com/blog/SVB-crisis-case-study)
- [PRNews — Secret Service crisis of communication](https://www.prnewsonline.com/crisis-of-communication-the-secret-services-leadership-failure/)

**Crisis-comms theory (severity classification, decomposition):**
- [Wikipedia — Situational Crisis Communication Theory (Coombs 2007)](https://en.wikipedia.org/wiki/Situational_crisis_communication_theory)
- [Coombs 2007 — Protecting Organization Reputations During a Crisis, Springer/Palgrave](https://link.springer.com/article/10.1057/palgrave.crr.1550049)
- [Wikipedia — Image Restoration Theory (Benoit 1995, 1997)](https://en.wikipedia.org/wiki/Image_restoration_theory)
- [TheCommSpot — Image Restoration Theory explained](https://thecommspot.com/communication-basics/communication-theories/image-restoration-theory/)
- [Peter Sandman — Outrage Management Index](https://www.psandman.com/index-OM.htm)
- [AIHA Synergist — Revisiting the Sandman Outrage Model](https://publications.aiha.org/202403-revisiting-sandman-outrage-model)
- [Wikipedia — Outrage factor](https://en.wikipedia.org/wiki/Outrage_factor)
- [Brandwatch — How to Protect Your Brand with React Score](https://www.brandwatch.com/blog/introducing-react-score/)
- [Dezenhall Books — Glass Jaw](https://dezbooks.net/books/glass-jaw/)
- [Hachette — Glass Jaw](https://www.hachettebookgroup.com/titles/eric-dezenhall/glass-jaw/9781538725696/)

**FAA action-item format precedent:**
- [FAA — Airworthiness Directives](https://www.faa.gov/regulations_policies/airworthiness_directives)
- [FAA — AD Content & Format](https://www.faa.gov/aircraft/air_cert/continued_operation/ad/ad_content)
- [eCFR — 14 CFR Part 39 Airworthiness Directives](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-39)

**Weak-signal theory:**
- [Wikipedia — Strategic Early Warning System (Ansoff)](https://en.wikipedia.org/wiki/Strategic_early_warning_system)
- [Britopian — Rethinking Share of Voice Measurement](https://www.britopian.com/research/share-of-voice-measurement/)
- [Sprout Social — Share of Voice](https://sproutsocial.com/insights/share-of-voice/)

**Cross-shape monitoring taxonomy:**
- [Cision — 5 PR Crisis Metrics You Should Track](https://www.cision.com/resources/tip-sheets/metrics-to-track-during-a-pr-crisis/)
- [Cision — How Media Monitoring Empowers Communications](https://www.cision.com/resources/articles/how-media-monitoring-empowers-communications-in-a-pr-crisis/)
- [Talkwalker Crisis Management Dashboard Template](https://www.talkwalker.com/marketing-essentials/crisis-management-dashboard-template)
- [Meltwater — How to Measure Share of Voice](https://www.meltwater.com/en/blog/share-of-voice-definition-measurement)
- [ReadLess Intelligence Digest](https://www.readless.app/solutions/intelligence-digest)
- [PRNews — PR Finally Has a Seat at the Table](https://www.prnewsonline.com/pr-finally-has-a-seat-at-the-table-thanks-to-better-measurement/)

---

File: `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-monitoring-artifact-taxonomy.md`
