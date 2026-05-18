---
date: 2026-05-18 v1
type: judge-design Step 1 — monitoring (MON) optimal-output spec
status: DRAFT v1 — research-grounded redesign of v0; ready for redundancy check + fixture validation + ops-integration verification
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
ci_precedent: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI v3.3 — pattern for decision_shape-aware reader + §5 documented-exception breach of ≤5 ceiling)
companions:
  - docs/research/2026-05-15-judges-domain-monitoring.md (generalist MON domain research)
  - docs/research/2026-05-18-monitoring-vertical-conventions.md (vertical-specific cadence + reader conventions)
  - docs/research/2026-05-18-monitoring-artifact-taxonomy.md (six form factors; weekly digest LOCKED)
  - docs/research/2026-05-18-monitoring-ai-failure-modes.md (LLM-specific failure surfaces — event/source confab, recency, tier inflation, compound-claim fabrication)
  - docs/research/2026-05-18-monitoring-compound-narrative-absence.md (apophenia defense; MON-COMPOUND + MON-ABSENCE criterion shape)
revision_history:
  - 2026-05-18 v0 — initial 5-criterion draft (MON-1..MON-5), Monday-8:55am single-reader, MON-5 bundling compound + projection + silence
  - 2026-05-18 v1 — research-grounded redesign:
      MON-5 split (per compound-narrative-absence research): drop forward-projection (covered by MON-2 + MON-4); rename remainder MON-5 ABSENCE-as-signal + add MON-6 COMPOUND-claim evidence-chain;
      Reader spec made decision_shape-aware (per vertical-conventions research): standard / event-driven / incident-driven cadences;
      §1.5 LOCKED form factor added (per artifact-taxonomy research): weekly digest hybrid, FullIntel/PDB skeleton + Cision dual-axis severity + FAA-AD action items;
      §3 mediocre + Goodhart catalog expanded (per AI-failure-modes research): apophenia, compound fabrication, alert-fatigue from over-promotion, tier-inflation, silence fabrication;
      structural_gate expanded to 5+ deterministic AI-failure checks (event existence / quote-grep / URL HEAD / entity allowlist / as-of date / evidence_dates / tier-distribution floor);
      §7 verification: 6-criterion count IS the §5 documented exception — TWO documented exceptions (MON-5 ABSENCE + MON-6 COMPOUND) both backed by 2024–2026 literature with measured effect sizes;
      §8 open questions: redundancy check predictions (MON-1 ↔ MON-5 ABSENCE absorption likely; MON-5 ↔ MON-6 keep separate or merge), multi-week corpus prerequisite, low-volume + crisis-trigger handling, multi-client agency variant, cross-lane shape coordination with CI, first-cohort revalidation when financial-services/healthcare fixtures land
---

# Monitoring Digest — Optimal-Output Spec (DRAFT v1)

Conforms to `docs/rubrics/judge-design-guide.md` with two documented exceptions (§7). Frameworks (Cision React Score, Coombs SCCT, Benoit, Edelman Trust Barometer, Sandman Hazard+Outrage, FAA AD format, PDB precedent, AMEC, Dezenhall Glass Jaw, Wohlstetter signals-to-noise, Heuer ACH, FM 34-2 PIR→Indicator→SIR, Ansoff weak signals, Tetlock calibration) inform the reader/success/failure spec and are the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

This v1 supersedes v0's single-archetype reader and bundled MON-5. Each elaboration is anchored in one of the four deep-research deliverables and follows the CI v3.3 pattern: §1.5 LOCKED (artifact-taxonomy research — shape-drift Goodhart is documented in evolution loops); decision_shape-aware reader (vertical-conventions research — 3/7 verticals operate on event-driven cadences, not weekly); structural_gate AI-failure plumbing (AI-failure-modes research — 19.9–37% citation-fab rates, 23–35% temporal-relative accuracy drop, 59% forecast-error inflation on AI-assisted reports); MON-5 ABSENCE + MON-6 COMPOUND with apophenia defenses (compound-narrative-absence research).

The "looks elaborate ≠ over-engineered" lesson from CI v3.1 applies here too: each defense below is anchored in a documented failure rate. Cutting them shifts brittleness from a testable layer (`structural_gate`) to a layer that can't do the work (the semantic judge).

---

## 1. Reader (LOCKED 2026-05-18)

**Primary archetype.** A senior communications director or PR lead at a Series-B-or-later company ($30M+ ARR), reading the digest as preparation for a leadership-cadence-appropriate briefing. They have 5–7 minutes. They need to walk into the room knowing (a) the single most-consequential development of the week, (b) what they personally need to do this week, (c) what gets worse if they don't act, and (d) anything conspicuously absent that their team probably missed.

They've subscribed to monitoring vendors before and unsubscribed because every email was 800 words of "230 mentions this week" with no interpretation. They want the digest to tell them something they don't already know — including silences, absences, and developments their team probably missed. They will forward 1–2 sentences to their CEO if challenged. They have the authority to act on the brief: assign a comms-team task, place a call to a journalist or partner, escalate to legal or to the CEO.

**Decision_shape-aware extension (per `docs/research/2026-05-18-monitoring-vertical-conventions.md`).** The Monday-8:55am framing is first-cohort overfitting: 3 of 7 surveyed verticals operate on event-driven or regulator-clock cadences, not weekly. The judge accommodates three decision shapes:

- **Standard cadence (routine-weekly).** B2B SaaS, founder-led startups, legal services, professional services, agency. Monday-morning leadership-briefing prep is the modal use case.
- **Event-driven (regulator-clock-anchored).** Financial services (SEC Reg S-K, FRB SR 11-7/13-19, FINRA, EU DORA, GDPR Art. 33–34); healthcare (HIPAA, FDA, Joint Commission, CMS). Cadence is materiality-driven (SEC SAB 99) or regulatory-clock-driven (HIPAA 60-day, GDPR 72-hour, FDA Warning Letter 48–72h).
- **Incident-driven (regulated industries).** Utilities (NERC CIP), nuclear (NRC 10 CFR 50.72), telecom (FCC NORS 120-min), defense (CMMC/DFARS 72-hour), pharma, aviation (FAA AD). Same-day briefing is routine.

The brief drives concrete action regardless of decision_shape; the "commit by" timeline scales to the decision-shape-appropriate gate (this Monday / same-day / sub-1hr). Required-silence vs anomalous-silence distinction is load-bearing (see MON-5).

**Reading time budget is not load-bearing.** The reader reads until they have what they need, then stops. Length guidelines route to `structural_gate`, not the judge.

**Substitute readers the same digest should also serve:** founder/CEO at earlier-stage with no in-house comms; agency lead reading on behalf of multiple clients; in-house counsel monitoring reputational legal exposure; IR head reading for analyst-call prep; Chief Reputation Officer at a regulated firm reading for board-risk-committee input; practice-owner at a small-to-mid local-market business (healthcare practice, hospitality, retail) reading for week-ahead operational decisions.

The Series-B-SaaS reference archetype exists because Anthropic, Perplexity, and similar AI-lab fixtures are gofreddy's current first-cohort. They are concrete anchors, **not** the architectural target. First-cohort overfitting is an explicit risk to monitor (see §8).

**NOT the reader:** oncall duty officer reading a pager alert (different infrastructure, sub-1hr decision velocity — separate workflow concern); board observer reading the quarterly governance roll-up (different audience, different evidence depth); crisis-team lead reading the post-incident after-action review (different orientation — backward not forward); junior analyst building a clip dump; marketing-ops person measuring share-of-voice in isolation; researcher cataloging brand mentions for a future report.

---

## 1.5. Artifact shape (LOCKED 2026-05-18)

**The lane produces ONE hybrid weekly-digest format**, per `docs/research/2026-05-18-monitoring-artifact-taxonomy.md`. Locked because shape-drift Goodhart is a documented failure mode in evolution loops: under 50-generation selection pressure, the workflow learns that pager-alert-shaped output scores well on MON-3 (highest-stakes lede), deep-dive-memo-shaped output scores well on MON-6 (compound evidence chain), and scorecard-shaped output scores well on MON-2 (severity classification) — producing Frankenstein digests that serve no coherent reader. The lock prevents this.

**Form factor:**
- 600–1,400 words total (hard ceiling 1,500, floor 400, enforced by `structural_gate`).
- 3–6 items (hard ceiling 7). Single-item digest allowed for low-volume periods when accompanied by explicit "no other developments warrant weekly-cadence treatment" stanza.
- 80–250 words per item (hard ceiling 300 — exceeding drifts toward deep-dive shape).
- FullIntel **"what happened / why it matters / recommended action"** triple per item.
- **FAA-AD-grade action items** (owner / deadline / consequence) in closing stanza — MON-4.
- **Cision dual-axis severity** (Harm + Emotionality, or Competence + Ethics for trust events) on top 3–5 items — MON-2.
- **Edelman competence-vs-ethics decomposition** on trust-impact events; **Sandman Hazard + Outrage discrimination** for lede selection — inform MON-2 and MON-3 reasoning.

**Out-of-scope shapes (the lane will NOT produce these):**
- Real-time pager alert (<100 words, sub-1hr action — separate workflow + oncall infrastructure).
- Daily executive brief (1 page, weekday-morning cadence — different operational rhythm).
- Monthly scorecard (KPI-driven AMEC framework — different cadence + data infrastructure).
- Quarterly deep-dive memo (5–15 pages — different cadence + evidence depth).
- Board-prep deck (8–15 slides quarterly — different format + audience).
- Incident postmortem (NTSB/CISA/SRE-style retrospective — backward not forward).

**Why one shape:** the v0 Reader spec points to weekly executive synthesis. The hybrid blends PDB multi-article structure with FullIntel per-item compression and FAA-AD action-item discipline. Decision-class scope: the **weekly-action cluster** (Monday briefing prep, immediate-week comms tasks, escalation surfacing). Pager-tier crisis, monthly governance, and quarterly strategy are out-of-scope.

**Shape enforcement lives in `structural_gate`, NOT in the judge criteria.** Per design guide §11.1, this preserves outcome-question-not-feature-check discipline at the judge layer.

**Empirical validation scope.** Form factor is research-grounded against current first-cohort fixtures (Anthropic, Perplexity, DWF, Klinika). When financial-services pre-market briefs, regulated-industries bulletins, or other new-vertical fixtures appear, re-validate — verticals may need shape adjustments (materiality-tier prefix; elevated compliance-time field). The lock is the weekly-cadence default; lane scope may sibling-fork as the client mix evolves.

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18)

After reading in under 7 minutes (or under the decision-shape-appropriate window), the comms director walks into the leadership context with:

- **A single specific call on the most-consequential development.** The action may be: assign a comms-team task, place a personal call, escalate to a named owner, commission deeper monitoring, or explicitly stand down ("no action this week — here's why" is valid).
- **A 1–3 item action list** with named owners (concrete person or role, not "the team"), specific deadlines (this week / by Friday 3pm / same-day), and operationalized consequence-of-inaction ("the narrative hardens for the Q3 trade-press cycle," not "reputational damage").
- **Awareness of one cross-story compound** the reader's team probably wouldn't have connected themselves — anchored in 3+ named signals across distinct time-points pointing to a single underlying claim, with at least one disconfirming reading engaged.
- **Confidence they aren't missing a quiet but high-stakes signal.** Named-absent signals come with a baseline expectation (prior-week digest, public calendar, industry cadence, named precedent) and a strategic implication.

They would later forward one sentence to their CEO. They would NOT later regret either (a) failing to act on something the digest surfaced, or (b) chasing a noise spike the digest framed as crisis. **Sleep test:** the digest's logic survives 24h reflection, not just Monday momentum.

World-class real-world exemplars — quality anchors, NOT templates to copy:

- **President's Daily Brief** — 6–7 single-paragraph articles + 2 deep-dives, highest-stakes first; multi-week thread continuity standard; absence-of-expected-reporting treated as analytic comment.
- **FullIntel executive briefings to Fortune 500** — per-item "what happened / why it matters / recommended action" compression; "long briefings don't signal thoroughness — they signal poor judgment."
- **J&J Tylenol-era (1982) internal monitoring** — caught the cyanide cluster fast; routed actions to specific owners with named deadlines before the information vacuum filled with speculation.
- **Edelman Trust Barometer decomposition** — competence vs ethics axis, ~76/24 trust-capital split; single-axis sentiment misses ~3× of reputational damage on ethics-exposed events.
- **Bloomberg Intelligence sector briefs** — quantitative anchor, named comparable, falsifiable forward claim, dry-and-precise tone.

What ties these together: point of view at the top, severity calibrated to evidence, action items with owner + deadline + consequence, awareness of multi-week compounds AND conspicuously absent expected signals.

---

## 3. Failure — mediocre and Goodhart-collapse (LOCKED 2026-05-18)

### 3a. Mediocre — failure modes the judge must discriminate against

- **Clip dump.** Competitor activity log ("230 mentions, sentiment 62%, top sources A/B/C"). No interpretation. FullIntel's "data dump, not intelligence" failure; AMEC/Barcelona V4.0 violation.
- **Buried lede.** Highest-stakes development at position 4+ because volume was lower. SVB / Secret Service post-mortem pattern.
- **Alert fatigue.** Every uptick framed "crisis." "URGENT" tags on routine items. Trains the reader to ignore urgency signals — 73% of SOC teams cite false-positives as top detection challenge (2025 SANS).
- **Action items as "should continue to monitor."** Observations dressed as recommendations. No deadline, owner, or consequence.
- **Sentiment without trust-dimension translation.** Single-axis sentiment without competence-vs-ethics decomposition; single-axis volume without Hazard+Outrage discrimination. Mis-sizes reputational damage ~3× on ethics-exposed events.
- **Cross-story compounds missed.** Competitor product launch + regulator letter shown separately with no acknowledgment they're the same narrative. Harvard Law "Narrative Contradictions" board-level governance risk; Ansoff weak-signal blind spot; Pearl-Harbor signals-to-noise failure imported to corporate monitoring.
- **Silence-as-signal absent.** Wells Fargo / BP / Boeing 737 MAX pattern — signals existed but no escalation surface promoted them. The "dog that didn't bark" tradecraft anchor unmet.

### 3b. Goodhart-collapse — Phase 4 pathology + AI-specific failure surfaces

**Phase 4 pathology (the historical Goodhart trap).** 50-generation evolution against a feature-checking judge produced exactly the pathology rolled back at `c76f051` (commit `698e658`). The workflow learns to slot-fill named surface markers:

- Mechanical tier tagging ("TIER: HIGH/MEDIUM/LOW") with field populated but orthogonal-axis reasoning absent.
- Templated "why it matters" stanzas that add no interpretation.
- FAA-AD-templated action items with three fields populated and zero operational content ("Owner: comms team / Deadline: ongoing / Consequence: reputational damage").
- Forced "Cross-Story Patterns" section stitched from co-occurring but causally-unrelated stories to satisfy MON-6.
- Performative forward bullets ("expect continued volatility") that can't be tested.
- Single-event-spun-three-ways compound expanded across three paragraphs to satisfy MON-6's "3+ signals" requirement cosmetically.

**AI-specific failure surfaces (new in v1, per `docs/research/2026-05-18-monitoring-ai-failure-modes.md`):**

- **Event / entity / source confabulation.** Invented press coverage, fabricated quotes, blog mentions inflated to "Wall Street Journal coverage." Documented at 19.9% citation-fab for GPT-4o (Chelli et al. 2025); 37% on Perplexity; 14–95% entity hallucination across 13 LLMs × 40 domains (GhostCite). Apple News withdrew its summary feature in early 2025 over exactly this profile. MON-1's delta framing rewards the *form* — the LLM can fabricate the baseline.
- **Recency / training-cutoff distortion presented as "this week."** LLMLagBench (arxiv 2511.12116): Feb 2026 models may carry Oct 2024 behavioral cutoffs; "Is Your LLM Outdated?" NAACL 2025: 23–35% accuracy drop on relative-temporal framings.
- **False-urgency / severity-tier inflation.** Sycophantic LLM default compounds into routine items tagged "watch" or "crisis." Arxiv 2603.16643 (People Pleasers): LLMs sacrifice factual accuracy for perceived user preference — for monitoring, the "perceived preference" is *something worth flagging this week*. Arxiv 2507.10587 (Anthropomimetic Uncertainty): "HIGH" carries no internal humility signal.
- **Compound-claim fabrication — invented connective tissue.** Real-Y + real-Z + invented "in response to" / "led to." Documented in TrustJudge (arxiv 2509.21117), Structural Hallucination (arxiv 2603.01341), Eidoku (arxiv 2512.20664). **FactSet 2025: AI-assisted equity reports show 59% higher forecast error** — richness from compound-claim language, error from fabricated connective tissue. MON-6 defends against this.
- **Silence-as-signal fabrication (apophenia).** Fabricated missing-signal claims with no baseline anchor (Conrad / Shermer patternicity literature). Tetlock superforecasters flag absence-of-pattern when stakeholders want a story; hedgehog LLMs over-pattern. MON-5's named-baseline-expectation requirement is the structural defense.

**Historical context.** This lane (or siblings) has triggered three prior rollbacks for Phase-4 pathology: `2ce99bb` (σ-widening, J1–J4), `ca4a256` (v2 contract-prose), `698e658` (Phase 4 feature-checking → `c76f051`). The criteria below resist re-creating these AND surface the AI-specific failure surfaces those rollbacks didn't address.

**Deterministic AI-failure checks live in `structural_gate`** (URL HEAD, quote-grep, entity allowlist, as-of date, evidence_dates, tier-distribution floor — see §8 #8) — per OpenRubrics, deterministic verification belongs in `structural_gate`, not in the judge. **Semantic compound-evidence-chain integrity lives in MON-6 below.**

---

## 4. Criteria — outcome questions (6)

### MON-1 — Baseline-relative framing of what changed

**Outcome question (binary):**
Does the digest express period-over-period developments as deltas from a defined baseline (prior week, 4-week trailing average, peer set, expected-given-event, regulator-clock-anchored expectation), not as absolute counts? If the reader stopped reading after the first 200 words, would they know what *changed* versus what's just current state?

**Score 1 (yes)** — Every quantitative claim is framed as a delta with an explicit comparator. Volume reported as "X vs Y-week average." Sentiment reported as "X% vs baseline Y%." Material events benchmarked against historical precedent or regulator-clock expectation. The baseline source is named, not implied.

Example (do not optimize toward this): "Brand mention volume 47% above 4-week baseline driven entirely by the Pinsent partner-pull aftermath; brand sentiment 12pt softer (62%→50%) — concentrated on legacy-firm-loyalty narrative, not on Pinsent's positioning. Comparable: when CMS pulled 6 partners from Dentons in 2024, sentiment softened 8pt over 3 weeks."

**Score 0 (no)** — Numbers reported as absolute values with no comparator. "230 mentions this week." "Sentiment was 62% positive." Or comparator is named but vibe-anchored not corpus-anchored ("higher than usual" without specifying usual).

**Score 0.5 (unknown)** — Some metrics are baseline-framed, others are not, and the un-framed metrics include one that's load-bearing for the period's lede. Emit 0.5 + "unknown" + one sentence on which framing is missing.

**Required CoT:**
- Step 1: List every quantitative claim in the first 400 words.
- Step 2: For each, identify whether a baseline / comparator / delta is named with its source.
- Step 3: Emit verdict + one-sentence justification, referencing the load-bearing metric.

Do not score: precision of the baseline math, choice of baseline window (vendor-default OK if named), formatting of the comparator, baseline-source verifiability (routed to `structural_gate`).

### MON-2 — Severity classification with defensible reasoning

**Outcome question (binary):**
Is each surfaced development explicitly classified by severity (crisis / opportunity / watch / noise — or equivalent) with reasoning the reader can interrogate, anchored on at least one orthogonal axis pair? Would the reader's CEO / managing partner / Chief Compliance Officer, challenging the classification, find the underlying logic defensible — not vibes, not sycophantic confidence?

**Score 1 (yes)** — Top 3–5 items each carry an explicit severity classification with reasoning that names at least one orthogonal dimension pair (harm potential AND emotional charge; competence exposure AND ethics exposure; materiality AND velocity; hazard AND outrage). Coverage gaps modify classification (a "crisis" call on single-source data is flagged as provisional). For event-driven readers, materiality thresholds (SEC SAB 99-style "would a reasonable investor consider this important") inform the call.

Example (do not optimize toward this): "Pinsent partner-pull — CRISIS (high harm to senior RES retention; moderate emotionality; alt-hypothesis 'isolated incident, no retention contagion' contradicted by 4-firm Q3 lateral-flight pattern; tier elevated despite below-average mention volume because lateral signal is the leading indicator). Provisional pending Friday's confirmed-versus-rumored Above the Law count."

**Score 0 (no)** — Every item presented at the same emphasis. "Concerning" used as a tier with no anchor. Classification implied by ordering but not stated. Single-axis sentiment driving severity (high outrage = high crisis, regardless of hazard). Confident-tone orthogonal-axis prose generated to defend a foregone classification (sycophancy tell).

**Score 0.5 (unknown)** — Classification given but the reasoning collapses to a single axis when an orthogonal axis is load-bearing. Emit 0.5 + "unknown" + one sentence on what dimension is missing.

**Required CoT:**
- Step 1: List the top 3–5 items in the digest.
- Step 2: For each, identify the severity classification + the orthogonal-dimension reasoning + whether the reasoning is anchored on observable signal vs. confident-tone defense.
- Step 3: Emit verdict + one-sentence justification.

Do not score: number of severity tiers used, vocabulary choice, presence of color-coding, tier-distribution floor (routed to `structural_gate`).

### MON-3 — Highest-stakes lede in position one

**Outcome question (binary):**
Does the development with the largest expected impact on the reader's strategic interests open the digest, with structural emphasis (length, headline weight, position) proportional to stakes — not to volume, novelty, or sentiment extremity? If the reader stops after position one, do they have the most-consequential information? If nothing extraordinary happened, does the digest say so plainly in position one?

**Score 1 (yes)** — The first substantive item in the digest is the highest-stakes development of the period, with the largest word allocation. Routine high-volume chatter is deprioritized or omitted. Lede selection demonstrates Sandman-style discrimination (low-hazard-high-outrage vs high-hazard-low-outrage; the latter wins position one when both are present). For event-driven readers, materiality drives lede placement. For low-volume periods, position one explicitly states "nothing extraordinary happened — here's what we tracked and why none of it warrants leadership escalation."

**Score 0 (no)** — Position one driven by volume or sentiment extremity rather than stakes. Highest-stakes development buried at item 4+ because something else was louder. Visual emphasis (callout, bold) given to most-surprising rather than most-consequential. Pager-style "URGENT" framing on a routine item to satisfy the lede requirement cosmetically.

**Score 0.5 (unknown)** — Position one is reasonable but a second item later in the digest has comparable or higher stakes and was poorly placed. Emit 0.5 + "unknown" + one sentence on the misplaced item.

**Required CoT:**
- Step 1: Identify the highest-stakes development of the period (largest expected impact on reader's strategic interests, by materiality / hazard / customer-revenue-exposure / regulator-clock-proximity).
- Step 2: Check whether it opens the digest with proportional weight, OR whether the digest correctly reports a low-volume period with explicit reasoning.
- Step 3: Emit verdict + one-sentence justification.

Do not score: section-ordering conventions, presence of executive-summary block, hierarchical headings, word count of lede (routed to `structural_gate`).

### MON-4 — Action items with owner, deadline, consequence

**Outcome question (binary):**
Does the digest end with 1–3 action items each naming a specific owner (named person or role, not "the team"), a specific deadline (date or window appropriate to the decision_shape), and the consequence of inaction (what gets worse)? Could the reader walk into the leadership-cadence-appropriate context and assign these without further interpretation?

**Score 1 (yes)** — 1–3 specific action items. Each names owner + deadline + consequence. The owner is concrete (CEO, Head of Comms, Head of Legal, Chief Compliance Officer, IR lead, founder themselves, named agency contact, regulator-relations lead — not "the team"). The deadline is specific and decision-shape-appropriate (this week / by Friday / same-day for event-driven / sub-1hr-escalation-trigger for incident-driven — not "ongoing"). The consequence is operationalized ("widens SoV gap to 2-week-low," "loses defensibility on partner-RES narrative," "creates Reg-FD-disclosure exposure if internal action precedes external statement" — not "could affect reputation").

Example A (do not optimize toward this) [standard cadence]: "Head of Comms drafts named-partner-context briefing by Wednesday 3pm; offer to Bloomberg reporter before Friday's analyst-call coverage cycle locks in. Otherwise, legacy-firm-loyalty narrative hardens for Q3 trade press."

Example B (do not optimize toward this) [event-driven]: "CFO + IR Head review the Hindenburg short report this morning; commit to Reg-FD-compliant response posture (engage / decline / delay) by 2pm market close. Otherwise, the silence increases probability of an analyst-downgrade in Friday's note cycle."

Example C (do not optimize toward this) [founder-led]: "Founder DMs the Latent Space podcast host within 24 hours to engage on the developer-tools comparison; otherwise, the framing locks in for next week's episode, which is the highest-distribution channel in our category right now."

**Score 0 (no)** — Recommendations are "continue to monitor," "the team should consider," "we should think about" — observations, not action items. No deadline. Consequence reduced to "reputational damage" or absent. Owner is "the team" / "leadership" / unnamed.

**Score 0.5 (unknown)** — Action items present but one or more of owner/deadline/consequence is too vague to act on. Emit 0.5 + "unknown" + one sentence on which dimension is missing.

**Required CoT:**
- Step 1: Identify the action items at the end of the digest.
- Step 2: For each, verify owner is concrete + deadline is decision-shape-appropriate + consequence is operationalized.
- Step 3: Emit verdict + one-sentence justification.

Do not score: number of action items beyond the 1–3 range, formatting (bullets vs prose), use of imperatives.

### MON-5 — Absence-as-signal (NEW in v1)

**Outcome question (binary):**
Did the digest flag at least one specific expected signal that did not materialize this period — naming the missing signal, the baseline expectation with source (prior-period digest, public calendar, industry cadence, named precedent), and the strategic implication? Or, when no flagged absence exists, did the digest correctly report "all expected signals materialized — no anomalous silences this period" with reasoning?

**Score 1 (yes)** — At least one named missing signal + named baseline expectation with corpus source + named strategic implication. OR digest correctly reports "no flagged absences — all expected signals materialized" with reasoning. The baseline is corpus-anchored (prior-period digest, public earnings calendar, FDA Warning Letter cadence, NRC event-reporting window, named historical pattern), not vibe-anchored.

Example A (do not optimize toward this) [standard cadence]: "Expected tier-1 trade-press coverage of competitor's Q3 launch did not materialize. Baseline: their Q1/Q2 launches each generated 8+ tier-1 mentions within 5 business days per the analyst-tracker corpus; this week's count is 1. Implication: under-resourced GTM, internal disagreement, or strategic abstention — each changes our flanking-vs-defending posture."

Example B (do not optimize toward this) [event-driven]: "Competitor CFO absent from Tuesday earnings call. Baseline: she has attended every quarterly call since 2024 per public transcripts; no pre-announced absence in the Q3 IR calendar. Implication: health, legal exposure, internal power shift, or impending departure — track if she's absent from the next off-cycle update."

**Score 0 (no)** — Generic "we'll keep watching"; OR specific absence without corpus-anchored baseline (apophenia risk); OR fabricated absence ("competitor did not announce a Mars program") with no baseline; OR digest claims comprehensive silence-coverage in a high-volume period without identifying any anomalous-silence candidate.

**Score 0.5 (unknown)** — Absence flagged but the baseline expectation is implicit or the strategic implication too generic. Emit 0.5 + "unknown" + one sentence on what's missing.

**Required CoT:**
- Step 1: List flagged absences.
- Step 2: For each, verify (a) named missing signal, (b) corpus-anchored baseline expectation, (c) named strategic implication.
- Step 3: For each, verify the absence is NOT a required-silence phase (FDA pre-approval / SEC quiet period / NRC classified investigation / Joint Commission sentinel-event confidential phase / DoD classified). Required silence is not a missed signal; recommending response during required-silence is a rule-violation.
- Step 4: Emit verdict + one-sentence justification.

Do not score: number of absences beyond 1+ (weak absences are penalty), framework-name in baseline prose, citation-format of baseline source (verifiability routed to `structural_gate`).

**Note on the ≤5 ceiling:** MON-5 is the first documented exception, justified by the apophenia / absence-fabrication AI-failure surface. Rationale in §7. Predicted: MON-5 most likely to absorb into MON-1 (both require named-baseline reasoning).

### MON-6 — Compound-claim evidence chain survives tracing (NEW in v1)

**Outcome question (binary):**
For each cross-story compound and multi-week pattern in the digest, does the evidence chain survive tracing — components named with dated signals across **distinct time-points**, connective tissue source-grounded (not generated), and at least one disconfirming reading engaged? Would the reader walk into the leadership briefing with a multi-week narrative their team probably didn't connect themselves, anchored in 3+ named signals across distinct time-points converging on a single underlying claim?

**Score 1 (yes)** — At least one cross-story compound anchored in 3+ signals across **distinct time-points** (e.g., week-1 signal A, week-2 signal B, week-4 signal C — not one week's signal restated three ways), converging on a single underlying claim, with at least one disconfirming reading explicitly engaged at weight comparable to the favored reading. Connective tissue ("led to," "in response to," "driven by") is source-grounded — components share a named entity or cited source. Confidence calibrated to evidence depth. OR digest correctly reports "no compound thread this period — all developments stand alone" with reasoning.

Example (do not optimize toward this): "Pinsent's senior-RES expansion (Sept 23 partner-promotion announcement) + Slaughter & May's October FS-regulatory lateral cluster (4 partners Q3 per ALM tracker) + the Sept 30 CMS comment letter on FS-regulatory disclosure form a compound: top-tier London firms are rebuilding FS-regulatory depth ahead of MiFID III enforcement. Three signals dated to distinct weeks across three named source-corpora. Alternative: opportunistic hiring tied to a single bonus-cycle window, not strategic shift — can't yet distinguish from one quarter of lateral data. Confidence: medium; firms up if Q1 2027 promotions also skew FS-regulatory."

**Score 0 (no)** — Compound rests on signals from a single week restated three ways. OR distinct-time signals but no single underlying claim (decorative not analytic). OR connective tissue is generated, not source-grounded (no shared entity / no causal mechanism). OR strawman alternative-reading (visibly weaker than favored). OR digest contains compound-claim fabrications (real events stitched with invented connective tissue), entity/source confabulations, or recency distortions.

**Score 0.5 (unknown)** — Compound partially traces but one required component (distinct time-points / single claim / engaged disconfirming reading / source-grounded connective tissue) is too thin to evaluate. Emit 0.5 + "unknown" + one sentence on which is unclear.

**Required CoT:**
- Step 1: Identify cross-story compounds and multi-week patterns.
- Step 2: For each, walk the evidence chain — 3+ signals across distinct time-points? Single underlying claim? Source-grounded connective tissue (shared entity / shared source / named causal mechanism)? Disconfirming reading engaged at weight comparable to favored?
- Step 3: Flag any event confabulation, recency distortion, or compound-claim fabrication — force score 0 if `structural_gate` has not already gated them.
- Step 4: Emit verdict + one-sentence justification.

Do not score: number of compounds beyond 1+, citation density (routed to `structural_gate`), section-header presence.

**Note on the ≤5 ceiling:** MON-6 is the second documented exception, justified by the compound-claim fabrication AI-failure surface (FactSet 2025 59% forecast-error inflation). Rationale in §7. Predicted: MON-5 ↔ MON-6 stay separate (absence and compound are structurally distinct); MON-1 ↔ MON-5 is the more likely absorption.

---

## 5. Shared judge-prompt wrapper

```
You are scoring a weekly monitoring digest written for a senior
communications director or PR lead. The reader may operate on:
(a) standard weekly cadence — B2B SaaS, founder-led startup,
legal services, professional services, agency multi-client; OR
(b) event-driven cadence — financial services (SEC/FRB/OCC/FINRA/
DORA), healthcare (HIPAA/FDA/Joint Commission/CMS); OR
(c) incident-driven cadence — regulated industries (NRC/FERC/
FCC/FAA/DoD/pharma). Their decision-making shape varies but the
digest still has to drive concrete action by the decision-shape-
appropriate gate (this Monday for standard / same-day for event-
driven / sub-1hr-escalation for incident-driven).

The digest is the lane's locked artifact shape: 600–1,400 words
total, 3–6 items, 80–250 words per item, weekly cadence with
Monday-morning modal delivery. Each item carries the FullIntel
"what happened / why it matters / recommended action" triple.
Action items follow FAA-AD format (named owner / specific
deadline / operationalized consequence).

Score each criterion independently with 0, 0.5, or 1 plus a
one-sentence rationale that follows the per-criterion CoT steps.
Do not blend criteria. Do not infer criteria not stated. If a
criterion's condition is ambiguous from the digest alone, emit
0.5 + "unknown" + one sentence on what would have to be present
to commit to 1.

The reader has unsubscribed from monitoring services that send
800-word clip dumps. They want interpretation, not collation.
They want silence flagged as signal with named baseline anchors,
not invented. They want compounds anchored in 3+ named signals
across distinct time-points, not single events spun three ways.
They want action items they can assign without further translation.

When evaluating multi-week claims, verify each signal is dated
to a distinct time-point with a named source. When evaluating
absences, verify each absence names (a) the specific missing
signal, (b) the baseline expectation with named source, (c) the
strategic implication. Required-silence phases (FDA pre-approval,
SEC quiet period, classified-investigation phases) are NOT missed
signals; recommending response during required-silence is a rule-
violation.

Score for whether the digest would actually change what the
reader does in the decision-shape-appropriate context — not for
whether it contains specific section headers, classification
tiers, or template fields.

Emit per-criterion JSON:
{"criterion_id": "MON-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 6. Goodhart-resistance verification

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **MON-1**: "Templated X% vs Y% framing" doesn't pass if Y is unnamed or vibe-anchored — corpus-named baseline required. Fabricated-baseline pathway is routed to `structural_gate` event-existence check.
- **MON-2**: "Mechanical TIER: HIGH tag" doesn't pass — orthogonal-axis reasoning anchored on observable signal required. Sycophantic-confidence-toned orthogonal-axis prose (defending foregone classification) is the v0 gap MON-6 also defends against on the compound side.
- **MON-3**: "Pager-style URGENT framing on routine item" doesn't pass — judge tests Sandman-style hazard-vs-outrage discrimination; low-volume periods earning score-1 via explicit "nothing extraordinary" is the documented branch.
- **MON-4**: "Owner: team / Deadline: ongoing / Consequence: reputation" doesn't pass — concrete owner + decision-shape-appropriate deadline + operationalized consequence required.
- **MON-5**: "Generic continue-to-watch" doesn't pass; fabricated absence with no baseline anchor doesn't pass (apophenia defense); required-silence misread as missed-signal doesn't pass (forces score 0). Baseline-expectation requirement IS the apophenia structural defense — fabrications fail because they can't supply a corpus-anchored baseline.
- **MON-6**: "Cross-story compound from co-occurring but unconnected stories" doesn't pass — 3+ signals across distinct time-points required (structural defense against single-event-spun-three-ways). "Confident strategic synthesis without underlying source chain" doesn't pass — top compounds must have shared entity or shared source on connective tissue (structural defense against fabricated connective tissue). Strawman alternative-reading doesn't pass — disconfirming reading must be weight-comparable to favored reading. Entity confabulation / event confabulation / recency distortion each force score 0 if `structural_gate` has not already gated them.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0.

**Note on AI-specific defenses:** MON-5's baseline-expectation requirement defends apophenia (fabrications can't supply named corpus-anchored baselines). MON-6's distinct-time-points + source-grounded-connective-tissue requirements defend compound-claim fabrication (real-Y + real-Z + invented-because pattern documented at FactSet 59% forecast-error rate). Entity/source/recency confabulation defenses live in `structural_gate` (URL HEAD, quote-grep, entity allowlist, as-of date, evidence_dates) — the judge assumes structurally-verified events and tests reasoning on top.

---

## 7. Verification — does the v1 spec conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (3 decision-shape examples on MON-4; single representative example elsewhere, with cross-shape coverage in §1 reader spec) ✓
- §5 criterion count: **6 (TWO documented exceptions to ≤5 ceiling)** — see note below
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3–4 steps each) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §11 Goodhart-resistance verification ✓
- §13 specimen criterion template followed ✓

**Note on the ceiling exception (TWO documented exceptions):**

Per design guide §5.documented-exception clause, a 6th criterion is permitted when (a) the literature documents an LLM-specific failure surface, (b) the other 5 criteria cannot catch it, and (c) the failure mode has measured effect sizes from 2024–2026 literature. The MON lane meets these conditions TWICE — one exception per AI-failure surface that prior criteria can't catch:

- **MON-5 (ABSENCE-as-signal)** — absence-as-evidence reasoning is documented as an LLM weakness in the apophenia literature (Conrad 1958; Shermer 2008 "patternicity"; Tetlock superforecaster calibration findings — hedgehogs over-pattern, foxes under-pattern when warranted) and in the absence-of-evidence reasoning literature (Heuer ACH analytic blind spots; intelligence-tradecraft "dog that didn't bark" canon). Effect size: Tetlock GJP top-2% calibrated forecasters flag absence-of-pattern explicitly when stakeholders want a story; LLMs sycophantically generate stories (arxiv 2603.16643 "Good Arguments Against the People Pleasers"; arxiv 2510.04721 BrokenMath). MON-1..MON-4 + MON-6 cannot catch fabricated absences — they test present-signal interpretation, not missing-signal reasoning. MON-5's named-baseline-expectation requirement is the load-bearing apophenia structural defense.
- **MON-6 (COMPOUND-claim evidence-chain)** — compound-claim fabrication is documented as an LLM failure surface in TrustJudge (arxiv 2509.21117 Score-Comparison Inconsistency + Pairwise Transitivity Inconsistency), Structural Hallucination (arxiv 2603.01341 90% of valid references in top-10% most-cited — popularity bias transfers to narrative-connection generation), Eidoku (arxiv 2512.20664 hallucination as structural-consistency failure), and the FactSet 2025 retrospective measuring **59% higher forecast error on AI-assisted equity reports vs analyst-only**. Apple News withdrew its summary feature in early 2025 over compound-claim fabrication (real events + invented narrative arcs). MON-1..MON-5 cannot catch this — MON-5 rewards absence-as-signal; without MON-6, MON-5's cross-period reasoning compound-fabrication surface is unprotected. MON-6's distinct-time-points + source-grounded-connective-tissue requirements are the load-bearing structural defenses.

Both criteria mirror the CI-6 evidence-chain pattern established at `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` §7. Subject to the same redundancy check as the rest: **the live count is most likely 4–5 after the check runs** — MON-5 (ABSENCE baseline expectation) is most likely to absorb into MON-1 (baseline-relative framing) since both require named-baseline-with-source reasoning. MON-6 less likely to absorb into MON-5 (compound and absence are structurally distinct phenomena: compound = real-but-unconnected; absence = expected-but-missing). Don't fight the MON-1 ↔ MON-5 absorption when it happens.

Length per criterion ≈ 250 words on average (longer than the design guide's 150-word target on MON-4 due to 3 decision-shape examples and on MON-5/MON-6 due to apophenia + compound-fabrication defense prose; absorbable). Total spec body ≈ 4500 words including §1.5 and §3b expansions.

---

## 8. Open questions

Reader / Artifact-shape / Success / Failure / 6 Criteria are LOCKED at v1. Remaining:

1. **Multi-week corpus context — ops-integration prerequisite (highest priority).** MON-6's distinct-time-points anchoring requires the judge to reference prior-period digests at judgment time. The current `evaluate_variant.py` pipeline may not pass multi-week context into the judge call. If not, MON-6 cannot score 1. Same constraint applies to MON-5's "prior-period digest reference" baseline-expectation pathway. Verify against current monitoring lane's data flow before locking the 6-criterion exception.

2. **Redundancy check pending.** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 6 criteria × 3 panel models (~90 calls, ~$35). **Predicted absorptions:** MON-1 ↔ MON-5 most likely to merge (both require named-baseline-with-source reasoning; the merged criterion would test both delta-framing of what happened AND baseline-framing of what didn't). MON-5 ↔ MON-6 predicted to stay separate (absence and compound are structurally distinct phenomena). Run before locking; restore live count to 5 if any pair absorbs.

3. **Low-volume week handling.** v1 resolves: MON-3 earns score 1 via explicit "nothing extraordinary happened" branch; MON-5 earns score 1 via "all expected signals materialized — no anomalous silences" branch. Confirm via fixture validation that the judge handles low-volume digests correctly on both criteria without penalizing the explicit low-volume statement.

4. **Multi-client agency variant scope.** Substitute reader #2 ("agency lead on behalf of multiple clients") may need different cadence. Recommendation: one-client-per-digest as modal case (preserves lede-discipline forcing function); multi-client roll-up explicitly out-of-scope. Confirm via fixture validation if agency-shape fixtures land.

5. **Crisis-trigger off-cadence stance.** Does the lane support emergency mid-week digests? Recommendation: (a) crisis triggers a separate pager-tier workflow, not the MON lane (keeps MON scope clean). Confirm with JR before locking.

6. **Cross-lane shape coordination with CI lane.** CI-6 and MON-6 both implement evidence-chain-survives-tracing at different cadences (single-development for CI, multi-period for MON). Cross-pollination risk: workflows learn each other's compound reasoning, drifting both lanes' criteria toward a shared median shape. Defense: each lane's `structural_gate` tests for its own out-of-scope shapes (CI rejects digest-shape; MON rejects single-development executive-briefing-shape). Surface for cross-lane review after both lanes ship to fixture validation.

7. **First-cohort overfit re-validation.** v1 broadened decision_shape but the underlying research is primarily anchored on legal-services / AI-lab / B2B-SaaS / healthcare-practice first-cohort. Re-validation trigger: any fixture from financial-services (CCO/CRO pre-market brief), regulated-industries (FAA-AD-style bulletin), DTC e-commerce, fintech, hospitality, or regulated-finance IR. Particular concern: MON-2's orthogonal-axis pair (Harm + Emotionality) may need substitution per vertical (Materiality + Velocity for financial services; Hazard + Outrage for regulated industries) — verify orthogonal-pair flexibility holds.

8. **`structural_gate` expansion (before spec ships to v006/workflows).** Existing checks (file presence, results.jsonl shape, banned-phrases) stay. Add 5+ AI-failure checks, each defending a documented LLM failure rate:

   *Anti-hallucination:*
   - Event-existence lookup against news APIs / vendor-feed corpus — defends 19.9% GPT-4o citation-fab rate.
   - Quote-grep against vendor-feed corpus (cosine ≥ 0.85) — defends Apple News mention-to-quote escalation pattern.
   - URL HEAD-check — defends 3–13% URL hallucination in web-grounded systems (arxiv 2604.03173).
   - Entity-existence allowlist (RapidAPI / OpenCorporates / Wikidata fallback) — defends 14–95% entity hallucination (GhostCite).
   - "As of [YYYY-MM-DD]" date requirement — defends recency-cutoff distortion (LLMLagBench).
   - Per-story `evidence_dates` array — every "this week"-framed claim points to ≥1 source within 7 days; defends 23–35% relative-temporal-framing accuracy drop (NAACL 2025).
   - Tier-distribution floor (≥1 "noise" per 5 stories; 4-week rolling 2σ shift flagged) — fights alert-fatigue / sycophantic tier inflation; defends 73% SOC false-positive rate transferred to brand monitoring.

   *Shape-conformance:* word band (600–1,400, ceiling 1,500, floor 400), item count (3–6, ceiling 7, single-item permitted with explicit low-volume statement), per-item ceiling (300), FullIntel triple presence per item, FAA-AD action-item structure in closing stanza, severity-classification presence on top 3–5 items.

   Banned-phrase list extended with AI-slop tells ("should continue to monitor," "the team should consider," em-dash density). Pager-tier promotion grep ("URGENT" / "CRISIS" capitalized): require orthogonal-axis justification sentence in same paragraph; flag >2/digest as suspicious.

9. **Tetlock calibration as wrapper constraint vs separate criterion.** Calibrated-confidence (confident-toned claims have multi-signal backing; tentative claims flagged tentative) is a candidate but would push to 7. Better routed as wrapper constraint — every criterion's rationale should reflect calibration. Confirm via fixture validation if calibration failures surface independent of MON-2/MON-6.

10. **Propagation to other 6 lanes.** Once MON v1 validates (+ redundancy check + ops-integration on multi-week corpus), propagate to GEO → MA → SB → X → LI → site_engine. Per-lane question scoping needed — the 4 MON deep-research questions don't transfer mechanically. CI v3.3 + MON v1 establishes the §5-documented-exception precedent for AI-failure-surface 6th-criterion breaches across the lane portfolio.
