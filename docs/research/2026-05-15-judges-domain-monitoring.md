# Domain research: what makes a weekly brand-monitoring digest excellent

**Date:** 2026-05-15
**Purpose:** Ground judge criteria for the `monitoring` lane in published methodologies, named industry exemplars, crisis-comms frameworks, and post-mortems of monitoring that did and did not catch real crises. This document does *not* propose judge prose — it identifies the dimensions practitioners actually evaluate, and surfaces failure modes drawn from named sources.

---

## 1. What makes a monitoring digest actionable

### 1.1 The "so what" turns information into intelligence

The single most consistent dimension across vendor documentation, agency practice, and intelligence-community precedent is that a digest must *interpret*, not just collate. FullIntel — a media monitoring vendor that produces executive briefings for Fortune 500 communications teams — articulates this bluntly:

> "The 'so what' that turns information into intelligence is exactly what separates a briefing from a clip dump."
> ([FullIntel, "How to Write an Executive Briefing That Leadership Actually Reads"](https://fullintel.com/blog/executive-briefing-that-leadership-actually-reads/))

FullIntel's executive-briefing template targets **200–400 words total**, with each item structured as **(a) what happened — one sentence, no background; (b) why it matters — 1–2 sentences connecting the development to what the executive owns; (c) recommended action or watch status — one sentence.** "Long briefings don't signal thoroughness — they signal poor judgment." This 4–6-sentences-per-item discipline mirrors the President's Daily Brief format described by former DNI John Negroponte: "six or seven articles, usually one paragraph to one page long, plus two longer 'deep dive' pieces" ([Wikipedia: President's Daily Brief](https://en.wikipedia.org/wiki/President%27s_Daily_Brief)).

Meltwater's own report-design guidance reaches the same conclusion via a different door: "Media monitoring reports should have an executive summary with main takeaways at the top, then add sections on media coverage volume, sentiment, and key messages" ([Meltwater, "What Is PR Monitoring?"](https://www.meltwater.com/en/blog/pr-monitoring)). The lede goes first; volume and sentiment are supporting evidence, not the message.

### 1.2 Baseline-relative framing, not absolute counts

Brandwatch's published crisis-alert guidance explicitly tells practitioners to "establish benchmarks that define what a normal level of negativity online looks like for their brand" and then alert on deviation, not on absolute volume ([Brandwatch, "How to Use Alerts for Crisis Management"](https://www.brandwatch.com/blog/use-alerts-crisis-management/)). The five named warning indicators they cite are: (1) sustained volume rise around high-risk keywords; (2) sudden spike; (3) sharp sentiment shift positive→negative; (4) traditional-media amplification; (5) mention from a high-profile or highly influential individual (celebrity, politician, journalist, key industry voice).

This is structurally important for a weekly digest: the unit of analysis is **delta from baseline**, not raw volume. A weekly digest that reports "230 mentions this week" without saying whether 230 is normal, elevated, or anomalous has failed its readers.

### 1.3 Severity tiering with a defensible scoring rubric

Cision's React Score — the most published vendor severity model — tiers content into **high / medium / low risk** by scoring two orthogonal dimensions: **Harm** (racism, sexism, hate speech, insult, obscenity, toxicity, threat) and **Emotionality** (the eight Plutchik primary emotions: joy, sadness, anger, fear, trust, disgust, surprise, anticipation) ([Brandwatch, "How to Protect Your Brand with React Score"](https://www.brandwatch.com/blog/introducing-react-score/)). The point of having two orthogonal dimensions rather than one composite "sentiment score" is that a competitor announcement may be emotionally charged (high emotionality) without being harmful, while a quiet regulatory letter may carry zero outrage but high harm potential. Single-dimension sentiment misses both.

### 1.4 The action-item structure FAA-style

The FAA Airworthiness Directive format ([14 CFR Part 39, ecfr.gov](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-39); [FAA, "AD Content & Format"](https://www.faa.gov/aircraft/air_cert/continued_operation/ad/ad_content)) is widely cited as a model in regulated-industry monitoring because every directive specifies: **unsafe condition** (what), **applicability** (who), **required action** (verb), **compliance time** (deadline), **alternative methods** (escape hatch). Translated into a monitoring digest, an action item is incomplete unless it names a specific person, a specific deadline, and the consequence of inaction. "Should be monitored" is not an action item; "Comms team must align before Friday's analyst call or the SoV gap widens to 2-week-low" is.

### 1.5 What monitoring directors actually evaluate

Synthesizing AMEC's Integrated Evaluation Framework ([amecorg.com](https://amecorg.com/amecframework/)) and the Barcelona Principles 3.0/4.0 ([Wikipedia: Barcelona Principles](https://en.wikipedia.org/wiki/Barcelona_Principles); [AMEC, "Barcelona Principles V4.0"](https://amecorg.com/wp-content/uploads/2025/06/Barcelona-Principles-V4.0-%E2%80%93-FINAL30.6-compressed.pdf)), the dimensions that have been canonized into industry standard since 2010 are: **outputs → out-takes → outcomes → organizational impact** with the explicit warning that "AVE [Advertising Value Equivalent] is not the value of public relations." Practitioners are taught to be suspicious of any monitoring report that leads with volume and stops there.

---

## 2. What separates great monitoring from noise: failure modes from named cases

### 2.1 Burying the lede (Silicon Valley Bank, US Secret Service)

The SVB collapse is now taught as a monitoring/communication failure precisely because the bank's own communications "failed on strategy and storytelling dimensions, communicating without context and neglecting to build a narrative" ([ISOC, "Case Study: SVB"](https://www.isoc.com/blog/SVB-crisis-case-study)). The US Secret Service's response to the Butler rally shooting is now a PRNews case study under the headline "Crisis of Communication: The Secret Service's Leadership Failure" — "delayed and sparse statements at the peak of the crisis created conditions for conspiracy theories and confusion, and vague answers ceded the narrative and further eroded public trust" ([PRNews, "Crisis of Communication"](https://www.prnewsonline.com/crisis-of-communication-the-secret-services-leadership-failure/)). A monitoring digest commits the same failure when the highest-stakes development of the week sits in position 6 of 9 because it scored lower on volume than three pieces of routine product chatter.

### 2.2 Missing weak signals (Wells Fargo, BP Deepwater Horizon, Boeing 737 MAX)

Three of the most-studied corporate crises of the 21st century all involved monitoring failures rooted in the same root cause: the warning signals existed, but no escalation surface promoted them above background noise.

- **Wells Fargo**: "As early as 2002, there were warning signs that the board should have caught… management missed opportunities to analyze, size and escalate sales practice issues" ([Wikipedia: Wells Fargo cross-selling scandal](https://en.wikipedia.org/wiki/Wells_Fargo_cross-selling_scandal); [Directors & Boards case study](https://www.directorsandboards.com/board-composition/education-and-orientation/singlewells-fargo-fake-accounts-scandal/)). Internal-audit and risk-management reports were running; they just didn't promote sales-integrity findings to a level the board could see.
- **BP Deepwater Horizon**: A House panel found that "during the hours leading up to the rig explosion, there were a series of missed and ignored warning signs" — abnormal cement-test results, mounting wellbore pressure spiking to 1,400 psi — and "the most damning thing we know about BP's safety culture is that nobody blew the whistle" ([PBS NewsHour, "Memo Suggests Warning Signs Were Ignored"](https://www.pbs.org/newshour/science/review-indicates-warning-signs-ignored-ahead-of-rig-explosion); [Peter Sandman, "BP's Communication Response"](https://www.psandman.com/articles/deepwater.htm)).
- **Boeing 737 MAX**: Per the Harvard Law School corporate-governance write-up, "engineers flagged concerns about MCAS, but these warnings were diluted or ignored by leadership… it is unclear whether any reporting mechanism existed for team members to report such issues to oversight resources outside of the 737 MAX's direct value chain" ([Harvard Law School Forum on Corporate Governance, "Boeing 737 MAX"](https://corpgov.law.harvard.edu/2024/06/06/boeing-737-max/)).

The transferable lesson for a brand-monitoring digest: **a digest that only surfaces what is already loud is worthless**. The Ansoff "weak signals" tradition ([Wikipedia: Strategic early warning system](https://en.wikipedia.org/wiki/Strategic_early_warning_system); Ansoff 1975, "Managing Strategic Surprise by Response to Weak Signals") explicitly defines the practitioner's job as detecting "vague, fuzzy, and difficult to interpret" signals *before* they crystalize. Corporate Foresight Initiative data cited across the literature finds firms with formal weak-signal scanning processes are 33% more likely to outperform peers financially.

### 2.3 Crying wolf (alert fatigue)

The opposite failure mode is equally documented. Per the 2025 SANS Detection and Response Survey, 73% of security teams name false positives as their top detection challenge ([Vectra, "Alert fatigue: causes, real cost, and how to fix it"](https://www.vectra.ai/topics/alert-fatigue)). Social-listening practice has imported the SRE tuning discipline: "Effective tuning starts by identifying the noisiest detection rules by alert volume, measuring the false positive rate per rule, and disabling or refining rules with rates above 50%" ([Motadata, "What Is Alert Noise Reduction?"](https://www.motadata.com/blog/alert-noise-reduction)). Brandwatch's own crisis-management guide cautions against treating every uptick as critical: "if it's the former, releasing a knee-jerk public apology could draw attention to a non-issue" ([Brandwatch, "Social Media Crisis Management"](https://www.brandwatch.com/blog/crisis-management-how-to-deal-with-a-crisis/)). A digest that flags everything as "crisis" trains the reader to ignore the digest.

### 2.4 The Tylenol counterexample: what good looks like

The 1982 Tylenol cyanide case ([PBS NewsHour, "How the Tylenol murders of 1982 changed the way we consume medication"](https://www.pbs.org/newshour/health/tylenol-murders-1982); [Wikipedia: Chicago Tylenol murders](https://en.wikipedia.org/wiki/Chicago_Tylenol_murders); [Time, "Tylenol Poison Spree 1982"](https://time.com/3423136/tylenol-deaths-1982/)) is the gold standard not because J&J's response was clever but because monitoring caught the cluster fast and information flowed up unimpeded. CEO James Burke personally contacted heads of major TV networks, J&J set up a toll-free hotline, recalled 31M bottles. The PR-relevant point for digest design: when the underlying monitoring was working, the action-item structure was unambiguous — *who* (CEO direct contact with networks), *when* (immediately), *consequence* (otherwise the information vacuum fills with speculation).

### 2.5 Dezenhall's inversion (Glass Jaw)

Eric Dezenhall, who runs an elite Washington crisis-management firm, argues in *Glass Jaw: A Manifesto for Defending Fragile Reputations in an Age of Instant Scandal* (2014, updated edition 2024) that "controversies are like icebergs — the small top above the water is all that the world sees, but most of what's really happening is happening in a place that few people see" ([Dezenhall Books, "Glass Jaw"](https://dezbooks.net/books/glass-jaw/); [Hachette Book Group](https://www.hachettebookgroup.com/titles/eric-dezenhall/glass-jaw/9781538725696/)). The implication for a monitoring digest: surface mentions are not the story. The story lives in the regulatory filings, the lawsuit dockets, the activist-investor letters, the trade-press scoop nobody amplified yet. A digest that reads only Twitter has already lost.

---

## 3. Industry frameworks the rubric should leverage

### 3.1 SCCT crisis-cluster taxonomy (Coombs, 2007)

W. Timothy Coombs's Situational Crisis Communication Theory ([Wikipedia: SCCT](https://en.wikipedia.org/wiki/Situational_crisis_communication_theory); [Coombs 2007, Springer/Palgrave](https://link.springer.com/article/10.1057/palgrave.crr.1550049)) sorts crises into three clusters by attribution of responsibility:

- **Victim cluster** (weak attribution): natural disasters, workplace violence, product tampering, rumors. Organization viewed as co-victim.
- **Accidental cluster** (minimal attribution): technical-error accidents, technical-error product harm, challenges. Unintentional.
- **Intentional/Preventable cluster** (strong attribution): human-error accidents, organizational misdeed with or without injuries. Organization "knowingly placed people at risk."

Response strategies are organized as **Deny / Diminish / Rebuild / Bolster**, with mapping to attribution level. A weekly digest classifying a development as "crisis" should at minimum implicitly answer: *which cluster*? Because the response toolkit is different. A regulator-issued enforcement notice is not the same crisis-type as a viral employee-misconduct video.

### 3.2 Benoit's image-restoration typology (1995, 1997)

William Benoit's *Accounts, Excuses, and Apologies* ([Wikipedia: Image restoration theory](https://en.wikipedia.org/wiki/Image_restoration_theory); [TheCommSpot synthesis](https://thecommspot.com/communication-basics/communication-theories/image-restoration-theory/)) names five primary response strategies: **denial, evasion of responsibility, reducing offensiveness, corrective action, mortification**. The relevance to monitoring digests is the symmetry: when the digest reports on *competitors* responding to their own crises, naming which Benoit strategy they're running ("Competitor X is in mortification mode, week 3") is the kind of analytic depth that distinguishes a $50K-a-year communications director's brief from a clip dump.

### 3.3 Edelman Trust Barometer competence/ethics decomposition

The Edelman Trust Barometer ([edelman.com/trust](https://www.edelman.com/trust/trust-barometer); [2026 Global Report](https://www.edelman.com/sites/g/files/aatuss191/files/2026-01/2026%20Edelman%20Trust%20Barometer%20Global%20Report_Final.pdf); [Edelman, "Competence Is Not Enough"](https://www.edelman.com/research/competence-not-enough)) decomposes institutional trust into two dimensions — **competence** (delivering on promises) and **ethics** (doing the right thing) — with the further finding that ethics dimensions (integrity, dependability, purpose) drive ~76% of trust capital vs. ~24% for competence. A monitoring digest that classifies a competitor's misstep purely as "operational stumble" without recognizing the ethics-axis exposure is mis-sizing the reputational damage by roughly 3×.

### 3.4 Sandman's Risk = Hazard + Outrage

Peter Sandman's framework ([psandman.com/index-OM.htm](https://www.psandman.com/index-OM.htm); [AIHA Synergist, "Revisiting the Sandman Outrage Model"](https://publications.aiha.org/202403-revisiting-sandman-outrage-model)) splits perceived risk into a technical hazard component and a 12-factor outrage component (voluntary/coerced, natural/industrial, familiar/exotic, memorable, dread, chronic/catastrophic, knowable, controlled-by-me, fair, morally relevant, trust, responsiveness). "The engine of risk response is outrage." This is operationally useful for digest authors: a low-hazard, high-outrage story (a tone-deaf executive tweet) will dominate the news cycle, while a high-hazard, low-outrage story (a complex regulatory filing) will pass quietly even though long-term consequences flip. The digest should explicitly distinguish these.

### 3.5 AMEC framework and Barcelona Principles

The AMEC Integrated Evaluation Framework ([amecorg.com/amecframework](https://amecorg.com/amecframework/); [AMEC, "PR Measurement in 2026"](https://amecorg.com/2026/03/pr-measurement-meaningful-outcomes/)) and Barcelona Principles 3.0/4.0 ([Wikipedia: Barcelona Principles](https://en.wikipedia.org/wiki/Barcelona_Principles)) operationalize "measure outcomes, not outputs." Outputs = volume, reach, AVE. Outcomes = awareness change, attitude shift, behavior. Impact = revenue, retention, market cap. A weekly digest that names only outputs has, per AMEC's own line, failed the basic professional standard.

### 3.6 Cision React Score severity tiering (harm + emotionality)

As covered in §1.3 — operationally useful as a two-axis severity model that practitioners can defend without overfitting to a single composite sentiment score ([Brandwatch, "How to Protect Your Brand with React Score"](https://www.brandwatch.com/blog/introducing-react-score/)).

### 3.7 Talkwalker Crisis IQ comparative framing

Talkwalker's published crisis-dashboard template explicitly includes **competitor KPI comparison** as a first-class element: "You can check competitors' KPIs against yours in the moment or over the duration of the crisis to get a sense of how you're faring" ([Talkwalker, "Crisis Management Dashboard Template"](https://www.talkwalker.com/marketing-essentials/crisis-management-dashboard-template); [Talkwalker, "Deutsche Telekom real-time crisis management"](https://www.talkwalker.com/resource/case-studies/deutsche-telekom-real-time-crisis-management-using-a-social-listening-powered-situation-room)). The framing convention is that *every metric for the focal brand must be paired with the same metric for at least one named competitor*. Volume alone is unfalsifiable; volume vs. peer set is interpretable.

---

## 4. Proposed judge-criteria specs (grounded in this research)

The current rubric (MON-1 through MON-8) has the right instincts but lacks named-source anchoring. Six criteria below are proposed as the grounded successor set. Each names what it evaluates, why monitoring practitioners evaluate this dimension, the source backing the claim, and concrete failure modes that should pull score down.

### MON-A. Baseline-relative framing of "what changed"

**Evaluates:** Whether the digest expresses week-over-week developments as deltas from a defined baseline (prior week, 4-week trailing average, peer set), not as absolute counts.
**Why practitioners evaluate this:** Brandwatch's published crisis-alert guidance ([Brandwatch alerts guide](https://www.brandwatch.com/blog/use-alerts-crisis-management/)) and standard SoV interpretation practice ([Sprout Social, "Share of voice"](https://sproutsocial.com/insights/share-of-voice/); [Britopian, "Rethinking Share of Voice Measurement"](https://www.britopian.com/research/share-of-voice-measurement/)) both make this the entry condition: without a baseline, a number is not a signal. Excess Share of Voice (ESOV) — the gap between SoV and market share — is the practitioner-standard interpretation rule.
**Failure modes:** "230 mentions this week" with no comparator; "sentiment was 62% positive" without "vs. 78% baseline"; competitor volume reported without the focal-brand counterpart; pre-vs-post-event delta not stated when an obvious event occurred.

### MON-B. Severity tiering with defensible classification

**Evaluates:** Whether each surfaced development is explicitly tiered (e.g., crisis / opportunity / watch / noise) and whether the classification is internally defensible — anchored in a model the reader can interrogate, not vibes.
**Why practitioners evaluate this:** Cision's React Score and Brandwatch's published methodologies both tier signals into high/medium/low risk by scoring on multiple orthogonal axes ([Brandwatch, "React Score"](https://www.brandwatch.com/blog/introducing-react-score/)); the FAA AD format makes severity a structural required field ([FAA, AD Content & Format](https://www.faa.gov/aircraft/air_cert/continued_operation/ad/ad_content)). A digest that does not tier forces the reader to do the tiering.
**Failure modes:** Every item presented at the same emphasis level; "concerning" used as a tier when it could mean anything from boycott-threat to mild PR scuff; tiering implied by ordering but not stated; SCCT cluster (victim/accidental/intentional) implicit when it changes the response toolkit.

### MON-C. Highest-stakes lede in position one

**Evaluates:** Whether the development with the largest expected impact on the client's strategic interests opens the digest, with structural emphasis (length, headline weight, position) proportional to stakes — not to volume, novelty, or sentiment extremity.
**Why practitioners evaluate this:** FullIntel's executive-briefing template ([FullIntel](https://fullintel.com/blog/executive-briefing-that-leadership-actually-reads/)) makes lede placement explicit ("lead with the most important fact"); the SVB and US Secret Service post-mortems ([PRNews, Secret Service](https://www.prnewsonline.com/crisis-of-communication-the-secret-services-leadership-failure/); [ISOC, SVB](https://www.isoc.com/blog/SVB-crisis-case-study)) both name "ceding the narrative" via buried-lede framing as the defining failure mode; the President's Daily Brief format historically opens with the highest-stakes item, not the loudest ([Wikipedia: PDB](https://en.wikipedia.org/wiki/President%27s_Daily_Brief)).
**Failure modes:** Routine product chatter at the top because it had the highest volume; a regulatory letter mentioned at item six because it was quiet; visual emphasis (bold, callout) given to the most surprising item rather than the most consequential; word count proportional to drama instead of impact.

### MON-D. Action items with named owner, deadline, and consequence

**Evaluates:** Whether action items follow the FAA-directive structure: (a) specific owner (named person or role, not "the team"); (b) compliance time (specific date or window); (c) consequence-of-inaction (what gets worse if the action is skipped). Recommendations without all three are not action items, they are observations.
**Why practitioners evaluate this:** FAA Airworthiness Directive convention ([14 CFR Part 39](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-39)) is the source format for regulated-industry action items; FullIntel's "recommended action or watch status — one sentence" rule ([FullIntel](https://fullintel.com/blog/executive-briefing-that-leadership-actually-reads/)) imports the structure into PR briefings; the Tylenol case ([Time, "Tylenol Poison Spree 1982"](https://time.com/3423136/tylenol-deaths-1982/); [PBS, Tylenol murders](https://www.pbs.org/newshour/health/tylenol-murders-1982)) shows that fast effective response required owner+deadline+consequence specified to the minute.
**Failure modes:** "Continue to monitor" as an action item; "the team should consider…"; recommended response with no deadline; consequence reduced to "this could affect reputation" with no operationalized cost; "Should we respond?" left as an open question instead of a recommendation.

### MON-E. Cross-story compound narrative and forward projection

**Evaluates:** Whether the digest identifies when two or more developments interact (e.g., a competitor product launch + a regulator's comment letter on the same category = a compound narrative the focal brand is exposed to), and whether it projects forward (next 1–2 weeks) rather than only describing the present.
**Why practitioners evaluate this:** The Harvard Law School "Narrative Contradictions" framework ([Corporate Governance Forum, "Narrative Contradictions"](https://corpgov.law.harvard.edu/2025/09/13/narrative-contradictions-the-invisible-governance-risk/)) names cross-issue coherence as a board-level governance failure when missed; Ansoff weak-signal theory ([Wikipedia: SEWS](https://en.wikipedia.org/wiki/Strategic_early_warning_system)) is fundamentally a forward-projection discipline; PRovoke Media's annual Crisis Review ([provokemedia.com/focus/crisis-review](https://www.provokemedia.com/focus/crisis-review)) repeatedly diagnoses missed compounds as the proximate cause of escalation; Dezenhall's *Glass Jaw* iceberg metaphor ([Dezenhall](https://dezbooks.net/books/glass-jaw/)) is exactly this point.
**Failure modes:** Each story stands alone with no connecting analysis; "competitor launched X" and "regulator commented on category Y" reported in separate sections with no acknowledgment they're the same narrative; "what to watch" section absent or filled with generic platitudes; no implied scenario for the next 1–2 weeks.

### MON-F. "So what" interpretation, including absent expected signals

**Evaluates:** Whether numbers are interpreted (not just reported) and whether the digest flags **what should have been there but wasn't** — e.g., "Competitor X did not respond to the regulator's comment letter this week, week 2 of silence" or "Expected analyst day coverage in tier-1 trade press did not materialize."
**Why practitioners evaluate this:** FullIntel's "so what separates a briefing from a clip dump" ([FullIntel](https://fullintel.com/blog/executive-briefing-that-leadership-actually-reads/)); AMEC/Barcelona Principles' outcomes-over-outputs requirement ([AMEC framework](https://amecorg.com/amecframework/); [Barcelona V4.0](https://amecorg.com/wp-content/uploads/2025/06/Barcelona-Principles-V4.0-%E2%80%93-FINAL30.6-compressed.pdf)); the Wells Fargo / BP / Boeing 737 MAX trio all show that absence-of-expected-signal is the canonical weak-signal pattern that institutional monitoring tends to miss; declassified PDB precedent of single-subject articles with "Canada — [blank page]" as the analytic comment ([Wikipedia: PDB](https://en.wikipedia.org/wiki/President%27s_Daily_Brief)) is direct precedent for flagging silence as content.
**Failure modes:** Numbers reported with no interpretation ("SoV was 23%" with nothing after); no flagged absences; "no major developments" used when in fact a major development was conspicuously absent; sentiment scores reported without translating into trust-dimension exposure (Edelman competence vs. ethics axes — [Edelman, "Competence Is Not Enough"](https://www.edelman.com/research/competence-not-enough)); outrage-driven stories not distinguished from hazard-driven stories per Sandman ([psandman.com](https://www.psandman.com/index-OM.htm)).

### (Optional MON-G) Temporal arc continuity across digests

**Evaluates:** Whether this week's digest acknowledges prior-week storylines — what advanced, what resolved, what stalled — rather than reading as a one-shot document with no memory.
**Why practitioners evaluate this:** This is the Brandwatch "continuous rise over time" warning indicator operationalized at the digest level ([Brandwatch alerts](https://www.brandwatch.com/blog/use-alerts-crisis-management/)). Bulldog Reporter's Friday weekly roundup convention ([Bulldog Reporter, Agility PR](https://www.agilitypr.com/about-bulldog-reporter/)) and PRWeek's "Weekender" both explicitly frame their weekly product as a continuity surface, not a fresh-start daily. A reader who tracks the digest across 4 weeks should see narrative threads weave through.
**Failure modes:** Story X dominates this week with no acknowledgment it was item 3 last week; resolved storylines not closed out; stalled storylines (silence-as-signal per MON-F) not noted as still-open; the digest reads correctly in isolation but loses information when read as a sequence.

---

## 5. Sources cited

**Vendor methodologies (primary)**

- [Cision, "Unlock PR Insights with Media Monitoring Reports"](https://www.cision.com/resources/insights/media-monitoring-reports/)
- [Cision, "5 PR Crisis Metrics You Should Track"](https://www.cision.com/resources/tip-sheets/metrics-to-track-during-a-pr-crisis/)
- [Cision, "How Media Monitoring Empowers Communications Professionals in a PR Crisis"](https://www.cision.com/resources/articles/how-media-monitoring-empowers-communications-in-a-pr-crisis/)
- [Brandwatch, "How to Use Alerts for Crisis Management"](https://www.brandwatch.com/blog/use-alerts-crisis-management/)
- [Brandwatch, "How to Protect Your Brand with React Score"](https://www.brandwatch.com/blog/introducing-react-score/)
- [Brandwatch, "Social Media Crisis Management: How to Respond"](https://www.brandwatch.com/blog/crisis-management-how-to-deal-with-a-crisis/)
- [Brandwatch, "How to Prepare for and Manage a Crisis"](https://www.brandwatch.com/blog/crisis-management/)
- [Meltwater, "What Is PR Monitoring? Tools, Tips & Benefits"](https://www.meltwater.com/en/blog/pr-monitoring)
- [Meltwater, "How to Measure Share of Voice"](https://www.meltwater.com/en/blog/share-of-voice-definition-measurement)
- [Talkwalker, "Crisis Management Dashboard Template"](https://www.talkwalker.com/marketing-essentials/crisis-management-dashboard-template)
- [Talkwalker, "Deutsche Telekom Real-Time Crisis Management"](https://www.talkwalker.com/resource/case-studies/deutsche-telekom-real-time-crisis-management-using-a-social-listening-powered-situation-room)
- [Sprout Social, "Share of voice definition"](https://sproutsocial.com/insights/share-of-voice/)
- [Onclusive overview, Decide Advisory Services](https://decidesoftware.com/airpr/)
- [FullIntel, "How to Write an Executive Briefing That Leadership Actually Reads"](https://fullintel.com/blog/executive-briefing-that-leadership-actually-reads/)

**Crisis-comms theory**

- [Wikipedia: Situational crisis communication theory (Coombs 2007)](https://en.wikipedia.org/wiki/Situational_crisis_communication_theory)
- [Coombs 2007, "Protecting Organization Reputations During a Crisis", Springer/Palgrave](https://link.springer.com/article/10.1057/palgrave.crr.1550049)
- [Wikipedia: Image restoration theory (Benoit 1995, 1997)](https://en.wikipedia.org/wiki/Image_restoration_theory)
- [TheCommSpot, "Image Restoration Theory Explained"](https://thecommspot.com/communication-basics/communication-theories/image-restoration-theory/)
- [Eric Dezenhall, *Glass Jaw*, Hachette/Twelve, 2014/2024](https://www.hachettebookgroup.com/titles/eric-dezenhall/glass-jaw/9781538725696/)
- [Dezenhall Books official page](https://dezbooks.net/books/glass-jaw/)
- [Peter Sandman, Outrage Management Index](https://www.psandman.com/index-OM.htm)
- [AIHA Synergist, "Revisiting the Sandman Outrage Model"](https://publications.aiha.org/202403-revisiting-sandman-outrage-model)
- [Wikipedia: Outrage factor](https://en.wikipedia.org/wiki/Outrage_factor)

**Industry frameworks (PR measurement)**

- [AMEC, "Integrated Evaluation Framework"](https://amecorg.com/amecframework/)
- [AMEC, "PR Measurement in 2026"](https://amecorg.com/2026/03/pr-measurement-meaningful-outcomes/)
- [AMEC, "Barcelona Principles V4.0"](https://amecorg.com/wp-content/uploads/2025/06/Barcelona-Principles-V4.0-%E2%80%93-FINAL30.6-compressed.pdf)
- [Wikipedia: Barcelona Principles](https://en.wikipedia.org/wiki/Barcelona_Principles)
- [Edelman, "2026 Trust Barometer Global Report"](https://www.edelman.com/sites/g/files/aatuss191/files/2026-01/2026%20Edelman%20Trust%20Barometer%20Global%20Report_Final.pdf)
- [Edelman, "Competence Is Not Enough"](https://www.edelman.com/research/competence-not-enough)
- [Edelman, "About the Trust Barometer methodology"](https://www.edelman.com/trust/our-methodology)

**Regulatory bulletin format precedent**

- [FAA, "Airworthiness Directives"](https://www.faa.gov/regulations_policies/airworthiness_directives)
- [FAA, "AD Content & Format"](https://www.faa.gov/aircraft/air_cert/continued_operation/ad/ad_content)
- [eCFR: 14 CFR Part 39, Airworthiness Directives](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-39)
- [FAA Safety, "Understanding Airworthiness Directives"](https://www.faasafety.gov/files/notices/2022/Mar/Understanding_Airworthiness_Directives_Presentation.pdf)

**Intelligence-community precedent for digest format**

- [Wikipedia: President's Daily Brief](https://en.wikipedia.org/wiki/President%27s_Daily_Brief)
- [intelligence.gov: What is the PDB?](https://www.intelligence.gov/publics-daily-brief/presidents-daily-brief)
- [CIA Readings: "President's Daily Brief 1961-1969"](https://www.cia.gov/readingroom/collection/presidents-daily-brief-1961-1969)
- [Wikipedia: Strategic early warning system (Ansoff weak signals)](https://en.wikipedia.org/wiki/Strategic_early_warning_system)

**Trade press / practitioner**

- [PRovoke Media, "PR Crisis & Business Crisis Review"](https://www.provokemedia.com/focus/crisis-review)
- [PRovoke Media (about / Holmes Report)](https://www.provokemedia.com/agency-playbook/agency-profile/the-holmes-report)
- [Bulldog Reporter (Agility PR Solutions)](https://www.agilitypr.com/about-bulldog-reporter/)
- [PRWeek newsletters](https://www.prweek.com/us/email-bulletins)
- [PRNews, "Crisis of Communication: The Secret Service's Leadership Failure"](https://www.prnewsonline.com/crisis-of-communication-the-secret-services-leadership-failure/)
- [PRNews, "PR Finally Has a Seat at the Table—Thanks to Better Measurement"](https://www.prnewsonline.com/pr-finally-has-a-seat-at-the-table-thanks-to-better-measurement/)
- [PRSA, "Crisis Communication Lessons From Boeing's 737 MAX Tragedies"](https://www.prsa.org/article/crisis-communication-lessons-from-boeing-s-737-max-tragedies)

**Named case studies — monitoring failures and gold standards**

- [Wikipedia: Wells Fargo cross-selling scandal](https://en.wikipedia.org/wiki/Wells_Fargo_cross-selling_scandal)
- [Directors & Boards: Wells Fargo Fake-Accounts Scandal](https://www.directorsandboards.com/board-composition/education-and-orientation/singlewells-fargo-fake-accounts-scandal/)
- [NACVA, "Fake Accounts Scandal at Wells Fargo"](http://web.nacva.com/JFIA/Issues/JFIA-2022-No2-11.pdf)
- [Harvard Law School Forum on Corporate Governance, "Boeing 737 MAX"](https://corpgov.law.harvard.edu/2024/06/06/boeing-737-max/)
- [PBS NewsHour, "Memo Suggests Warning Signs Were Ignored Ahead of Rig Explosion" (Deepwater Horizon)](https://www.pbs.org/newshour/science/review-indicates-warning-signs-ignored-ahead-of-rig-explosion)
- [Peter Sandman, "BP's Communication Response to the Deepwater Horizon Spill"](https://www.psandman.com/articles/deepwater.htm)
- [Bryghtpath, "Crisis Management Case Study: Deepwater Horizon"](https://bryghtpath.com/deepwater-horizon-case-study/)
- [Wikipedia: Chicago Tylenol murders](https://en.wikipedia.org/wiki/Chicago_Tylenol_murders)
- [PBS NewsHour, "How the Tylenol murders of 1982 changed the way we consume medication"](https://www.pbs.org/newshour/health/tylenol-murders-1982)
- [Time, "Tylenol Poison Spree 1982 Becomes Crisis Management Case Study"](https://time.com/3423136/tylenol-deaths-1982/)
- [Harvard Business School: "Johnson & Johnson: The Tylenol Tragedy"](https://www.hbs.edu/faculty/Pages/item.aspx?num=17858)
- [ISOC, "Case Study: SVB — how bad communication fuelled a major bank failure"](https://www.isoc.com/blog/SVB-crisis-case-study)

**Operational supporting (signal/noise, weak-signal theory, board reporting)**

- [Vectra, "Alert fatigue: causes, real cost, and how to fix it"](https://www.vectra.ai/topics/alert-fatigue)
- [Motadata, "What Is Alert Noise Reduction? Techniques & Tools"](https://www.motadata.com/blog/alert-noise-reduction)
- [IBM, "What Is Alert Fatigue?"](https://www.ibm.com/think/topics/alert-fatigue)
- [Corporate Governance Forum (Harvard Law), "Narrative Contradictions: The Invisible Governance Risk"](https://corpgov.law.harvard.edu/2025/09/13/narrative-contradictions-the-invisible-governance-risk/)
- [Britopian, "Rethinking Share of Voice Measurement"](https://www.britopian.com/research/share-of-voice-measurement/)

---

## Notes for the next step (rubric-prose authoring)

This research deliberately stops short of judge-prose drafting. When that step happens, three usage notes:

1. **Cite the named source in the rubric anchors themselves**, not only in handoff docs. "Per Cision React Score severity tiering" or "per FAA AD action-item format" inside the rubric gives the judge a concrete reference point that's harder to drift from than abstract design principles.
2. **MON-A through MON-F map closely to existing MON-1 through MON-8**, but the proposed names are sharper about the unit-of-evaluation. The current rubric's "what changed this period" maps to MON-A; the current rubric's "highest-stakes development priority signaling" maps to MON-C; "absent expected signals" lives inside MON-F rather than being split.
3. **MON-G (temporal arc) is genuinely the lowest-confidence criterion** of the seven — it's the one most likely to reward digests that just include a "previously on…" recap section without it being load-bearing. Worth flagging for discussion before adoption.

File: `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-15-judges-domain-monitoring.md`
