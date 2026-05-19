---
date: 2026-05-18
type: deep-research deliverable (monitoring lane, axis: compound-narrative + absence-as-signal)
parent: docs/handoffs/2026-05-18-judge-design-step1-monitoring.md
guide: docs/rubrics/judge-design-guide.md
sibling: docs/research/2026-05-15-judges-domain-monitoring.md (deepens §3 + §4 — proposed MON-E and MON-F)
status: research-only (no rubric prose; criterion proposals are outcome-question shaped, NOT prose drafts)
---

# Compound-narrative detection and absence-as-signal for the monitoring judge

## TL;DR

A weekly brand-monitoring digest scored only on this-week deltas is structurally blind to two of the most consequential signal classes a senior comms director cares about:

1. **Compound narratives** — patterns that exist across multi-week threads but read as routine inside any single week's window. (Example: quiet leadership churn at competitor X across 4 weeks + slowing product velocity + recent funding round = strategic distress; week-by-week each item is a 1-line clip.)
2. **Absences** — what conspicuously did NOT happen. (Competitor silent on a major industry event; founder absent from earnings call; expected product launch missed; expected analyst coverage didn't materialize.)

The intelligence-community tradition has 80+ years of named precedent for both — Wohlstetter's *Pearl Harbor: Warning and Decision*, Heuer's *Psychology of Intelligence Analysis*, the FM 34-2 PIR→Indicator→SIR crosswalk, the "dog that didn't bark" pattern, and Tetlock's superforecaster calibration findings on apophenia avoidance. None of this literature appears in the current MON spec.

The criterion-design move is to test **two specific reader-effects** without naming any source framework in rubric prose:

- **MON-COMPOUND** (proposed addition or replacement of current MON-5): *would the comms director walk into the briefing with a multi-week narrative their team probably didn't connect themselves, anchored in 3+ named signals across distinct time-points that point to a single underlying claim, with at least one disconfirming reading engaged?*
- **MON-ABSENCE** (proposed addition or replacement of current MON-5's silence component): *did the digest flag at least one specific expected signal that did not materialize this week, naming the signal that was missing, the baseline expectation that made it noteworthy, and the strategic implication of its absence?*

Each binary anchor has a structural defense against apophenia: the compound criterion requires named signals across distinct time-points (week-1 signal A, week-2 signal B, week-4 signal C → claim) — single-week three-headed restatements fail. The absence criterion requires the missing-signal's baseline expectation to be named — pure inventions ("Competitor did not announce a Mars program") have no baseline backing and fail.

These additions are NOT distinct from the existing MON-1..MON-5 work — they sharpen and partially replace MON-5, which currently bundles cross-story compound + forward projection + silence into one criterion and is therefore vulnerable to slot-fill Goodhart (workflow learns to add a token forward bullet, a token compound, a token absence, satisfying all three under a single criterion).

The whole proposal sits inside the design-guide §5 ceiling: net live count after a redundancy check is likely 5, not 7 — MON-3 (lede position) may absorb the most-consequential test that COMPOUND embeds; MON-1 (baseline-relative framing) supports ABSENCE rather than competing with it.

---

## Key questions answered (concise)

**Q1. How does the judge reward a digest that recognizes the COMPOUND pattern vs one that lists 3 disconnected events?**

By testing whether the multi-week thread carries (a) 3+ named signals across distinct time-points, (b) a single underlying claim the signals jointly support, and (c) at least one disconfirming reading explicitly engaged. The "across distinct time-points" requirement is the load-bearing structural defense: a workflow trying to slot-fill a compound has to surface real prior-week material; a single-week three-paragraph restatement can't pass.

**Q2. How does the judge reward absence-as-signal without inviting apophenia or hallucination?**

By requiring the absent signal to be named with its **baseline expectation** — what would normally have happened, drawn from a prior-week digest, a public calendar, an industry-standard cadence, or a named precedent. Pure inventions have no baseline anchor and fail. The judge tests for traceability ("Why did you expect this?"), not for the absence itself.

**Q3. What's the literature on "what's missing" as analytical signal?**

Three traditions converge:
- **CIA / Kent / Heuer tradecraft** — *Analysis of Competing Hypotheses* makes disconfirming evidence and "evidence we'd expect to see if H were true but don't" first-class. The CIA *Tradecraft Primer* and Sherman Kent School institutionalize "absence of expected reporting" as a tradecraft check.
- **PIR doctrine (FM 34-2)** — Priority Intelligence Requirements decompose to **Indicators**, then to **Specific Information Requirements (SIRs)**, with explicit acknowledgment that "no observation on indicator X" is itself reportable.
- **Wohlstetter signals-to-noise** — *Pearl Harbor: Warning and Decision* (1962). The signals were present; noise obscured them. The post-mortem turns on "weak signals against background noise" with explicit attention to non-occurrence of expected diplomatic traffic.

The classic literary anchor is Conan Doyle's "Silver Blaze" — the dog that didn't bark — adopted as a tradecraft mnemonic across CIA, MITRE, FBI, and corporate strategic-warning frameworks.

**Q4. How do you anchor a binary on "did the digest catch the compound narrative" or "did the digest flag the meaningful absence" without overfitting to specific events?**

The binary is on the reader-effect, not the artifact-feature. The behavioral score-1 anchor describes what the comms director walks into the briefing knowing that they didn't know before — a multi-week thread with named signals across distinct weeks, OR a specific absence with its baseline expectation. The binary tests whether the reader-effect was produced for the artifact's actual signal set, not whether the artifact contains specific named events.

This is the same construction as CI-2 (trajectory backed by 2+ independent signals): the criterion tests structure of evidence, not which evidence. A workflow can satisfy the criterion on this week's Pinsent-pull, on next week's regulator letter, on a 4-week-old leadership-churn thread — the prose doesn't name any of those, only the structural test.

**Q5. What's the failure mode where a digest invents a compound narrative from random events (apophenia)?**

This is the load-bearing failure mode and the primary risk of pursuing this axis. Three names from the literature:

- **Apophenia** (Conrad 1958; Shermer "patternicity") — perception of structure where none exists. Stress-amplified. Asymmetric: false positives are cheap in evolutionary terms but expensive in analytical ones.
- **Data dredging / p-hacking** — Tukey's term in the statistical tradition for finding any pattern in any dataset given enough degrees of freedom.
- **Confabulation under pressure** — Tetlock's *Superforecasting* documents that hedgehogs (single-narrative thinkers) over-pattern; foxes under-pattern. Superforecasters routinely flag absence-of-pattern even when stakeholders want a story.

**Structural defenses adopted in the proposed criteria below:**

1. The compound criterion requires named signals across **distinct time-points** (multi-week timestamps), not three readings of the same signal — this defeats "one event spun three ways."
2. The compound criterion requires explicit engagement with at least one **disconfirming reading** — this is Heuer's ACH discipline imported as a structural requirement.
3. The absence criterion requires a **baseline expectation** for the missing signal — fabrications fail because they can't supply one.
4. The shared judge wrapper tests for **traceability** to source corpus, not just plausibility of the narrative — connects to CI-6's "evidence chain survives tracing" pattern.

---

## Synthesis

### 1. The structural problem: single-week framing is reader-blind to multi-week patterns

The current monitoring spec (`docs/handoffs/2026-05-18-judge-design-step1-monitoring.md`) has five criteria. Four of them — MON-1 (baseline framing), MON-2 (severity), MON-3 (lede), MON-4 (action items) — are single-week-scoped. MON-5 bundles cross-story compound + forward projection + silence into one criterion, which makes it the single highest-risk criterion for slot-fill Goodhart: the workflow can earn the criterion by including one token cross-story sentence, one token forward bullet, one token "we did not see X" line.

The reader the spec defines — a senior comms director Monday 8:55am — is the canonical recipient of multi-week sense-making. The President's Daily Brief precedent named in the §1.5 domain research carries multi-week threads explicitly; FullIntel's executive briefing format implicitly assumes the comms director is a continuing reader; the AMEC framework's "outcomes" vs "outputs" distinction is fundamentally a multi-week metric.

The mismatch is structural. The artifact is weekly. The reader is continuing. The judge currently scores only the weekly artifact in isolation, which means the digest can earn a perfect score across MON-1..MON-4 while leaving the comms director under-served on the dimension the literature unanimously names as the practitioner's distinguishing skill: connecting threads across time.

The current MON-5 was an attempt to address this but bundled three semantically distinct concerns (compound, projection, silence) into one binary — making it both vulnerable to surface-marker satisfaction and ambiguous on what specifically failed when it does fail.

### 2. The compound-narrative case: what the intelligence community knows

Wohlstetter's *Pearl Harbor: Warning and Decision* (1962) is the canonical study of signal-against-noise failure. The signals of imminent attack existed across many weeks: changed Japanese diplomatic-traffic patterns, the recall of fleet personnel from leave, the relocation of carriers from home ports, the unusual silence of certain radio circuits. No single week's signal was unambiguous; the multi-week pattern was. The intelligence apparatus failed because no analytic surface promoted the cross-week pattern over the daily-volume noise.

This is structurally the same problem a monitoring digest faces. Each week's signal is plausibly noise. The compound exists in the integral across time.

Wohlstetter's framework was operationalized in the FM 34-2 *Intelligence Production* doctrine into the **PIR → Indicator → SIR crosswalk**:

- **PIR** (Priority Intelligence Requirement): the question the principal needs answered.
- **Indicator**: an observable proxy that, if true, suggests one PIR-answer over another.
- **SIR** (Specific Information Requirement): a collection task pinned to time, place, and detail.

The doctrine explicitly treats **indicator-not-observed** as collection product. In Army practice, "no observation on indicator X at SIR time Y" is reported and counted toward the PIR's resolution. The corporate-strategic-warning literature (Ansoff 1975 "Managing Strategic Surprise"; Day & Schoemaker *Peripheral Vision*; Karl Weick's sensemaking) imports this directly: a strategic-early-warning system (SEWS) treats both observations and non-observations as data.

For monitoring-judge design, the operational translation is:

**A compound is not "three events listed together." A compound is three signals across distinct time-points that converge on a single underlying claim, with the alternative readings explicitly considered.**

This is the Heuer Analysis of Competing Hypotheses discipline. The score-1 anchor on the compound criterion has to test for the discipline, not the cosmetics.

### 3. The absence case: "the dog that didn't bark"

Conan Doyle's "Silver Blaze" (1892) is the literary anchor. Holmes solves the case because the stable dog didn't bark — meaning the intruder was someone the dog knew. The absence of an expected reaction is the load-bearing clue.

The intelligence-tradecraft adoption is direct and longstanding:
- Heuer's *Psychology of Intelligence Analysis* (1999) lists "absence of evidence" as a recurring analytic blind spot — analysts under-weight non-observations because they have no salience.
- The CIA *Tradecraft Primer* (2009) lists "key assumptions check" and "indicators of change" as structured techniques that explicitly include absent expected indicators.
- The DOD JP 2-0 *Joint Intelligence* doctrine treats absence-of-expected-activity as a reportable indicator state.

For monitoring, three operationally useful absence classes:

**(a) Competitor silent on a major industry event.** Expected reaction would have generated trade-press coverage, a positioning statement, a partnership announcement. None materialized. The baseline expectation: "competitors at this size typically respond to category-defining events within 5 business days." Implication: under-resourced comms function, internal disagreement on positioning, or strategic decision to abstain — each of which is signal.

**(b) Founder absent from earnings call.** Baseline expectation: founders of public companies attend earnings calls unless explicitly announced otherwise. Implication: health, legal exposure, internal power shift, or impending departure.

**(c) Expected product launch missed.** Baseline expectation: a previously announced launch window or a pattern of quarterly product cadence. Implication: technical problems, strategic redirect, regulator pressure, or financial constraint.

In all three, the analytical move is the same:
1. Name the missing signal.
2. Name the baseline expectation that made it noteworthy (with reasoning, not vibes).
3. Name the strategic implication of its absence.

The baseline-expectation requirement is the load-bearing apophenia defense. A workflow that fabricates an absence ("Competitor X did not announce a Mars program") cannot supply a baseline expectation — the absence has no anchor. The judge tests the trace: where does this baseline come from? Prior-week digest? Public earnings calendar? Industry-standard cadence? Named historical pattern? If the answer is "no anchor," the absence claim fails on traceability, not on its specific content.

### 4. The apophenia failure mode (and why this axis is the hardest of the five criteria to harden)

Pursuing compound-narrative + absence-as-signal creates the largest Goodhart risk in the lane because the criterion structurally rewards storytelling. The risk surface:

- **Surface marker:** workflow generates a 3-bullet "multi-week thread" section with token references to prior weeks.
- **Surface marker:** workflow generates a 2-bullet "what did not happen" section with confidently-toned absences that have no baseline anchor.
- **Surface marker:** workflow generates one-disconfirming-strawman + one-favored-reading, satisfying the ACH-discipline requirement cosmetically.

This is exactly the Phase 4 pathology pattern the design guide § 11 catalogues as the recurring trap: feature-shaped criterion → workflow learns slot-fill → cosmetic compliance → analytic emptiness. The CI lane's `698e658` rollback was triggered by precisely this on a sibling axis (Helmer name-drops, ACH strawman alternative-hypothesis sections).

The defense pattern is the same as CI-6 (evidence chain survives tracing) and CI-2 (trajectory backed by 2+ independent signals):

**Defense 1 — Distinct time-points required.** The compound criterion requires named signals dated to distinct weeks. A single-event-spun-three-ways fails on the structural test. Workflow can't satisfy by adding prose; it has to surface real prior-week material.

**Defense 2 — Baseline expectation required for absence.** The absence criterion requires a named baseline source (prior-week digest, public calendar, named precedent, industry-standard cadence). Inventions fail because they can't supply one. Workflow can't satisfy by adding prose; it has to anchor in a corpus or context.

**Defense 3 — Disconfirming-reading discipline.** Per Heuer ACH, the compound criterion requires at least one engaged alternative reading. The judge tests whether the disconfirming reading would actually fit the evidence (strawman-detection): does the alternative have to wave away signals, or does it explain them? This is the same test CI-4 applies for "uncomfortable truth surfaced" — push against the actual organizational prior, not a manufactured strawman.

**Defense 4 — Structural ban on compound + projection + absence in the same criterion.** The current MON-5 bundle is the Goodhart attack surface; splitting it into one compound criterion + one absence criterion + projection routed elsewhere (or dropped) is the structural fix.

### 5. The Tetlock calibration finding (load-bearing for the whole axis)

Tetlock's Good Judgment Project (Mellers et al. 2014; *Superforecasting* 2015) documents that the most-calibrated forecasters (top 2% over multi-year tournaments) share three habits relevant here:

- They **flag absence-of-pattern** explicitly when stakeholders want a story but the evidence doesn't support one. Hedgehogs over-pattern; superforecasters under-pattern when warranted.
- They **calibrate confidence to evidence depth**, not to narrative coherence. A confident-sounding narrative with 1 supporting signal gets the same confidence as a tentative narrative with 1 signal — the prose doesn't earn confidence the evidence doesn't supply.
- They **engage disconfirming evidence as primary**, not as throat-clearing. The Heuer ACH discipline is baseline practice, not virtue-signaling.

These three findings map directly onto the score-1 anchor design for the compound criterion. The criterion isn't testing whether the digest finds a compound; it's testing whether the digest **earns** the compound — by named signals across distinct time-points, by calibrated confidence, by engaged disconfirming readings.

**Operational implication:** the score-0.5 ("unknown") anchor is load-bearing here. If the week genuinely has no compound to report, the digest should say so plainly and earn a 1 — not invent a compound to satisfy the criterion. This is the "no major developments" path from the existing MON-3 logic, extended to MON-COMPOUND.

The shared judge wrapper should reinforce this: **a digest that correctly reports "no compound thread this week, all developments stand alone" earns score 1 on MON-COMPOUND.** The score-1 anchor must include this branch explicitly, otherwise the workflow will infer that finding-a-compound is the only path to a positive score.

### 6. The reader-effect framing (per design guide §11.2)

Per the guide's §11.2: "the judge's job is to imagine the reader, not check the artifact." The criteria below frame the compound and absence outcomes as reader-effects:

- **MON-COMPOUND outcome question:** would the comms director walk into the briefing with a multi-week narrative their team probably didn't connect themselves?
- **MON-ABSENCE outcome question:** would the comms director walk in aware of a specific expected signal that did not materialize, with the framing to defend "why this absence matters" if challenged?

This phrasing carries the work the design-guide §11.2 requires: it forces the judge to reason about the reader's epistemic state, not about which artifact-features were checked off.

### 7. Compatibility with the design-guide §5 ceiling

The design guide caps lanes at ≤5 criteria with a documented exception for AI-specific failure surfaces (CI-6 precedent). Adding both MON-COMPOUND and MON-ABSENCE would push monitoring to 6 — possibly 7 if MON-5's forward-projection clause survives as a separate criterion.

The right move is **not** "add criteria" — it is **replace MON-5 with two sharper criteria + redundancy-check the result.**

Proposed restructure:

| Current | Proposed |
|---|---|
| MON-1 baseline framing | MON-1 unchanged |
| MON-2 severity classification | MON-2 unchanged |
| MON-3 highest-stakes lede | MON-3 unchanged |
| MON-4 action items | MON-4 unchanged |
| MON-5 (compound + projection + silence bundled) | MON-COMPOUND multi-week thread + MON-ABSENCE flagged missing signal |

Net live count: 6 criteria, awaiting redundancy-check. Most-likely-to-merge pairs:
- MON-1 (baseline framing) ↔ MON-ABSENCE (baseline expectation for absent signal) — both require named baselines, may correlate.
- MON-3 (lede position) ↔ MON-COMPOUND (would the comms director leave with a compound) — both test "the most consequential thing was surfaced."

After empirical redundancy-check on 5 fixtures × 6 criteria × 3 panel models, expected live floor: 4–5 criteria.

If a 6th criterion survives the redundancy check, the design-guide §5 exception requires the criterion to address a documented LLM-specific failure surface with 2024–2026 literature citations. MON-COMPOUND meets this (apophenia is documented as an LLM failure mode in Galileo Luna-2 + Patronus Lynx hallucination benchmarks; Tetlock-grade calibration is documented as an LLM weakness in HalluLens / FAITH). MON-ABSENCE meets this (absence-of-evidence reasoning is documented as a systematic LLM weakness in *Forecasting Bench* arXiv 2502.02145 and the LLMLagBench recency-cutoff literature). Both criteria qualify for the §5 documented-exception path if the redundancy check leaves both standing.

### 8. What this axis does NOT propose

To keep this research deliverable on-axis and not bleed into the rest of the spec:

- **No framework-name embedding.** The criterion prose must not name Wohlstetter, Heuer, ACH, PIR, FM 34-2, Ansoff, Weick, Sandman, Tetlock, or Conan Doyle. These shape the judge's reasoning toolkit; they do not appear in rubric prose. Per design guide §12 anti-pattern #2.
- **No anti-gaming clauses.** The prose must not say "do not invent compound narratives" or "do not fabricate absences." Per anti-pattern #3. The structural defenses (named signals across distinct time-points; named baseline expectation; engaged disconfirming reading) do the work that anti-gaming clauses cannot.
- **No σ-widening.** The prose must not widen variance to accommodate apophenia — that is the `2ce99bb` trap. Per anti-pattern #7. The 0.5 anchor handles the "can't tell" case.
- **No calibration via prose tweaks.** If the criteria show variance growth across generations, the response is redesign, not prose-tuning. Per design guide §11.5.
- **No reference exemplars.** The score-1 examples (if any) get the "do not optimize toward this" hedge. Per anti-pattern #9.
- **No first-cohort overfit.** The monitoring fixtures today are Anthropic / Perplexity / DWF / Klinika; the compound + absence pattern must work for tech-savvy founder/early-co clients across verticals. The literature anchors are cross-vertical (intelligence community + corporate-strategic-warning); the criteria prose should not embed legal-specific or AI-lab-specific examples.

---

## Recommendations (criterion-shape only — NOT rubric prose)

### Recommendation 1 — Replace MON-5 with two sharper criteria

Current MON-5 bundles cross-story compound + forward projection + silence-as-signal into one binary. This makes MON-5 the single highest-risk criterion in the lane for slot-fill Goodhart. Split:

**MON-COMPOUND** (compound-narrative outcome question):
- Outcome question: would the reader walk into the briefing with a multi-week pattern their team probably didn't connect themselves — anchored in 3+ named signals across distinct weeks that point to a single underlying claim — with at least one disconfirming reading engaged?
- Score 1 (yes): multi-week thread named, 3+ signals dated to distinct time-points, single underlying claim articulated, disconfirming reading explicitly considered. OR digest correctly reports "no compound thread this week, all developments stand alone" with reasoning.
- Score 0 (no): single-event prose spun three ways; or "compound" assembled from cosmetic prior-week mentions without distinct-time signals; or strawman alternative-reading; or confident-toned pattern with no signal-trace.
- Score 0.5 (unknown): compound named but one of the three required components (distinct time-points, single underlying claim, engaged disconfirming reading) is too thin to evaluate from the digest alone.
- Required CoT: list multi-week threads; for each, verify 3+ dated signals + single claim + engaged alternative; emit verdict.

**MON-ABSENCE** (absence-as-signal outcome question):
- Outcome question: would the reader walk in aware of at least one specific expected signal that did not materialize this week, with a named baseline expectation and a named strategic implication?
- Score 1 (yes): missing signal named specifically, baseline expectation named with source (prior-week digest, public calendar, named precedent, industry-standard cadence), strategic implication named. OR digest correctly reports "no flagged absences this week — all expected signals materialized" with reasoning.
- Score 0 (no): generic "we'll keep watching" with no specific absence; OR specific absence without named baseline expectation (fabrication risk); OR baseline expectation that doesn't bear scrutiny (vibe-anchored not corpus-anchored).
- Score 0.5 (unknown): absence flagged but the baseline expectation is implicit or the strategic implication is too generic.
- Required CoT: list flagged absences; for each, verify named-signal + named-baseline + named-implication; emit verdict.

### Recommendation 2 — Keep MON-1 unchanged; expect correlation with MON-ABSENCE

The redundancy-check (per design guide §5) is likely to show MON-1 (baseline-relative framing of what changed) and MON-ABSENCE (baseline expectation for missing signal) correlating > 0.7. If they do, MON-ABSENCE absorbs into MON-1 — the merged criterion tests both delta-framing of what happened AND baseline-framing of what didn't.

This is fine. The merged criterion still encodes the absence-as-signal discipline. Don't fight the absorption.

### Recommendation 3 — Drop forward projection from the criterion set

The current MON-5 includes forward projection ("next 1–2 weeks: monitor exit interviews"). The proposal here drops this from the criterion set entirely. Three reasons:

- **Forward projection is hard to falsify in a binary frame.** A workflow can produce a forward bullet that's neither right nor wrong over the relevant horizon; the judge cannot distinguish from the artifact alone.
- **Forward projection is covered structurally elsewhere.** MON-2 severity classification with the "alt-hypothesis contradicted by N-source pattern" anchor implies forward-projection reasoning. MON-4 action items with consequence-of-inaction implies forward-projection reasoning.
- **Three concerns in one criterion is the Goodhart attack surface.** Splitting MON-5 to two criteria + dropping the third is cleaner than splitting to three. The literature on action-item structure (FAA AD format) and forward-state inference (signal detection theory base-rate reasoning) supports routing forward-projection through MON-4 rather than making it a standalone criterion.

If JR wants forward projection retained as a first-class criterion, it should be a separate MON-FORWARD criterion with its own outcome question and binary anchor — not bundled into MON-COMPOUND or MON-ABSENCE.

### Recommendation 4 — Structural defense plumbing

Two non-judge changes route absence-checking to the deterministic layer:

**`structural_gate` additions** for the monitoring lane:
- A `prior_week_corpus` reference must be readable from the workflow context; the digest can reference last-week's digest by ID. If the corpus is not available, MON-COMPOUND cannot score 1 (distinct-time-points anchoring requires a corpus). This is the OpenRubrics Hard-Rules-vs-Principles split: corpus availability is structurally verifiable.
- A `baseline_sources_list` enumerated in the digest's metadata (prior-week digest IDs, public calendar URLs, named historical precedents) — present-or-absent is a structural check; baseline-quality is a judge check.

**Shared judge wrapper additions:**
- "When evaluating multi-week claims, verify each signal is dated to a distinct week with a named source. If any signal in the compound is not so anchored, the compound fails the distinct-time-points test regardless of how plausible the synthesis reads."
- "When evaluating absences, verify each absence names (a) the specific signal that did not materialize, (b) the baseline expectation that made it noteworthy with a named source, and (c) the strategic implication. Absences without all three fail."

These are NOT criterion prose; they are wrapper conditions that apply across the compound and absence criteria.

### Recommendation 5 — Apophenia variance instrumentation

Per design guide §11.5, the variance-per-criterion-per-generation telemetry is the Goodhart early-warning surface. For MON-COMPOUND and MON-ABSENCE specifically, the lane's variance instrumentation should track:

- **Compound criterion variance** — if growing monotonically across 3 generations, the workflow is learning to slot-fill compounds without earning them. Redesign the criterion, not the prose.
- **Absence criterion variance** — if growing, the workflow is learning to fabricate absences. Redesign.
- **Absence vs MON-1 correlation across generations** — if drift apart, the lane is treating them as separate dimensions; if convergent at > 0.7, merge per the redundancy check.

This is the same instrumentation pattern the design guide prescribes for all criteria; the recommendation here is to **flag MON-COMPOUND and MON-ABSENCE as the highest-priority criteria to instrument first**, because they carry the largest apophenia risk surface in the lane.

---

## Open questions

1. **Does the lane have prior-week corpus available at judgment time?** The compound criterion's distinct-time-points anchoring requires the judge to reference last week's (and 2/3/4-week-ago) digest. The current `evaluate_variant.py` pipeline may not pass multi-week context into the judge call. If not, MON-COMPOUND cannot score 1 — the criterion is non-functional. This is an ops integration question, not a design question, but it blocks the criterion.

2. **How many monitoring fixtures cover multi-week threads vs single-week-only?** If the fixture set is biased to single-week sessions (the easier shape to generate), MON-COMPOUND will score 0.5 ("unknown — no prior context") on most fixtures and provide no separation. Fixture-coverage audit needed before redundancy check.

3. **Does the absence criterion's "named baseline expectation" requirement bottom out at the workflow level or the corpus level?** If the workflow has to surface the baseline (because the corpus doesn't carry one), the workflow is doing the analytic work the judge then verifies — fine. If the corpus has to carry baselines (public calendars, prior-week digests, industry-cadence tables), `structural_gate` and lane infra both need extension.

4. **How does the projection clause from current MON-5 land if dropped?** The dropped forward-projection clause is non-trivial — comms directors do expect monitoring to project. If MON-4 action items + MON-2 severity classification together cover it, drop is fine. If not, a separate MON-FORWARD criterion is needed. Decide via fixture validation.

5. **First-cohort overfitting watch.** The literature anchors are cross-vertical (intelligence community + Heuer + Wohlstetter); the fixture set is heavily DWF / Anthropic / Perplexity / Klinika. The compound criterion may work differently on legal-services fixtures (multi-week partner-pull threads are highly visible) vs AI-lab fixtures (model-card improvement threads) vs healthcare fixtures (local-market cadence threads). Per the CI v3.3 first-cohort overfitting pattern, re-validate when fixtures from new verticals appear (DTC e-commerce, fintech, regulated finance, hospitality).

6. **Does MON-COMPOUND correlate with MON-2 severity?** Multi-week threads tend to also be severity-elevated (sustained signal > single-week spike on Brandwatch's 5 indicators). If MON-COMPOUND tracks MON-2 closely, may merge. Surface in redundancy check.

7. **Tetlock calibration as a separate criterion?** A standalone "calibrated-confidence" criterion (confident-toned claims have multi-signal backing; tentative claims are flagged as tentative) is a candidate but would push the lane to 7. Better routed as a wrapper constraint in the shared judge prompt — every criterion's rationale should reflect calibration, not just one criterion.

---

## Citations

**Intelligence-community tradecraft:**

- Wohlstetter, Roberta. *Pearl Harbor: Warning and Decision*. Stanford University Press, 1962. Canonical signals-to-noise analysis. ([National WWII Museum overview](https://www.nationalww2museum.org/war/articles/us-intelligence-failures-pearl-harbor); [SuperSummary](https://www.supersummary.com/pearl-harbor-warning-and-decision/summary/); [Calhoun reassessment](https://calhoun.nps.edu/server/api/core/bitstreams/c9895771-870e-4a9b-a5c4-6e266265462b/content))
- Heuer, Richards J. *Psychology of Intelligence Analysis*. CIA Center for the Study of Intelligence, 1999. Foundational text on analytic biases and ACH. ([SOS Intelligence ACH primer](https://sosintel.co.uk/mastering-the-analysis-of-competing-hypotheses-ach-a-practical-framework-for-clear-thinking/); [Dhami et al. 2019 Applied Cognitive Psychology](https://onlinelibrary.wiley.com/doi/full/10.1002/acp.3550); [Wikipedia: ACH](https://en.wikipedia.org/wiki/Analysis_of_competing_hypotheses))
- CIA *Tradecraft Primer: Structured Analytic Techniques for Intelligence Analysis*. 2009. Codifies ACH, key assumptions check, indicators of change.
- Sherman Kent School / Kent Center for Intelligence Analysis. Established 2000; formalizes the "literature of intelligence" and tradecraft transfer. ([CIA Kent profession-of-analysis paper](https://www.cia.gov/resources/csi/static/Kent-Profession-Intel-Analysis.pdf); [Wikipedia: Sherman Kent](https://en.wikipedia.org/wiki/Sherman_Kent))
- FM 34-2 *Intelligence Production*. US Army. PIR → Indicator → SIR doctrine. ([FAS index of Appendix D](https://irp.fas.org/doddir/army/fm34-2/Appd.htm); [Army PIR management article](https://www.army.mil/article/285410/priority_intelligence_requirement_management_in_divisions_and_corps); [CALL PIR reprint](https://www.lineofdeparture.army.mil/Portals/144/PDF/Journals/Intelligence/2024/CALL_PIR%20Reprint-UA.pdf))
- ThreatConnect, "7 Critical Elements of a Robust PIR" — corporate-CTI translation of FM 34-2. ([ThreatConnect](https://threatconnect.com/blog/the-7-critical-elements-of-a-robust-pir/))
- Cloudflare, "Introducing RFIs and PIRs for threat intelligence teams" — operational PIR + indicator practice in industry. ([Cloudflare blog](https://blog.cloudflare.com/threat-intel-rfi-pir/))
- President's Daily Brief format. Six to seven single-paragraph articles + 2 deep dives; multi-week thread continuity standard. ([Wikipedia: PDB](https://en.wikipedia.org/wiki/President%27s_Daily_Brief); [intelligence.gov](https://www.intelligence.gov/publics-daily-brief/presidents-daily-brief))

**Absence-as-signal anchors:**

- Conan Doyle, Arthur. "The Adventure of Silver Blaze." *Strand Magazine*, 1892. The "dog that didn't bark" — canonical absence-as-evidence anchor. ([Snugfam analysis](https://snugfam.com/the-sherlock-holmes-the-dog-that-didnt-bark-quote-meaning-significance/); [Briefly Writing on absence-of-expected-facts](https://brieflywriting.com/2012/07/25/the-dog-that-didnt-bark-what-we-can-learn-from-sir-arthur-conan-doyle-about-using-the-absence-of-expected-facts/); [Steve Haffner](https://www.stevehaffner.com/post/the-dog-not-barking))
- ABA Business Law Today, "The Dog That Didn't Bark and the AI Program That Is No Sherlock Holmes." Direct legal-practice application. ([ABA](https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-may/the-dog-that-didnt-bark-and-the-ai-program-that-is-no-sherlock-holmes/))
- NewMR, "The dog that didn't bark — a great way to find insight in information." Market-research application. ([NewMR](https://newmr.org/blog/the-dog-that-didnt-bark-a-great-way-to-find-insight-in-information/))
- US Patent 7,610,172 "Method and system for monitoring non-occurring events." Operationalizes absence-detection in industrial monitoring. ([USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7610172))
- Saab newsroom, "When being silent speaks louder than words." Industrial silence-detection. ([Saab](https://www.saab.com/newsroom/stories/2022/may/when-being-silent-speaks-louder-than-words))

**Apophenia and false-pattern detection:**

- Conrad, Klaus. *Die beginnende Schizophrenie*. 1958. Original apophenia coinage. ([Britannica overview](https://www.britannica.com/topic/apophenia); [Wikipedia: Apophenia](https://en.wikipedia.org/wiki/Apophenia))
- Shermer, Michael. "Patternicity: Finding Meaningful Patterns in Meaningless Noise." *Scientific American*, 2008. Evolutionary asymmetric-cost framing for false-positive pattern detection.
- Mental Health at Home, "What Is Apophenia (Finding Patterns Where None Exist)." Confirmation-bias compounding. ([MHaH](https://mentalhealthathome.org/2021/12/10/what-is-apophenia/))
- Tetlock, Philip & Gardner, Dan. *Superforecasting: The Art and Science of Prediction*. Crown, 2015. Calibration findings; superforecasters under-pattern when warranted. ([Stewart Brand summary](https://medium.com/the-long-now-foundation/all-it-takes-to-improve-forecasting-is-keep-score-289888d4d76c); [Cheslaw review](https://harry-cheslaw.medium.com/super-forecasting-dd146e441c1c))
- Mellers, Barbara et al. "Accuracy of forecasts in strategic intelligence." *PNAS* 2014. Good Judgment Project empirical findings on calibration. ([PNAS](https://www.pnas.org/doi/10.1073/pnas.1406138111); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4121776/))
- van Prooijen et al. "Connecting the dots: Illusory pattern perception predicts belief in conspiracies and the supernatural." Empirical apophenia under cognitive load. ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5900972/))
- Signal Detection Theory primers — sensitivity vs criterion, ROC curves, asymmetric-cost decision-making. ([NYU lecture](https://www.cns.nyu.edu/~david/courses/perception/lecturenotes/sdt/sdt.html); [Stanford Gardner Lab](https://gru.stanford.edu/doku.php/tutorials/sdt); [Cogn-IQ](https://www.cogn-iq.org/learn/theory/signal-detection-theory/))

**Corporate strategic warning and weak signals:**

- Ansoff, H. Igor. "Managing Strategic Surprise by Response to Weak Signals." *California Management Review*, 1975. Foundational weak-signal text. ([Ansoff 1975 PDF](https://www.creaciondeestrategia.com/wp-content/uploads/2022/02/Ansoff_1975.pdf))
- Day, George & Schoemaker, Paul. *Peripheral Vision: Detecting the Weak Signals That Will Make or Break Your Company*. Harvard Business School Press, 2006.
- Weick, Karl. *Sensemaking in Organizations*. Sage, 1995. Small disturbances + pattern-recognition + organizational signaling. ([Wikipedia: Karl Weick](https://en.wikipedia.org/wiki/Karl_E._Weick); [Springer philosophical exploration](https://link.springer.com/article/10.1007/s40926-016-0040-z))
- Wikipedia: Strategic early warning system (SEWS). ([SEWS](https://en.wikipedia.org/wiki/Strategic_early_warning_system))
- Crowdworx, "From Weak Signals to Strong Strategy" — practitioner translation of Ansoff. ([Crowdworx](https://www.crowdworx.com/en/blog/from-weak-signals-to-strong-strategy-how-to-spot-game-changing-trends-early/))
- Crayon, "The Surprising Power of the Weak Signal: Go Deep on Competitive Intel." Direct competitive-intelligence framing. ([Crayon](https://www.crayon.co/blog/competitive-intel))
- IBIMA, "Early Warning Signs Detection in Competitive Intelligence." Academic CI literature on absence-detection. ([IBIMA](https://ibima.org/accepted-paper/early-warning-signs-detection-competitive-intelligence/))
- Rohrbeck et al. "Integrating organizational networks, weak signals, strategic radars and scenario planning." *Technological Forecasting & Social Change*. ([ResearchGate](https://www.researchgate.net/publication/256859401_Integrating_organizational_networks_weak_signals_strategic_radars_and_scenario_planning))

**Narrative coherence in analysis:**

- "The role of narrative in collaborative reasoning and intelligence analysis: A case study." PMC. ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6944337/))
- Handraise, "Mastering Narrative Intelligence: From Data Signals to Strategy." Industry framing of narrative-arc analysis. ([Handraise](https://www.handraise.com/blog/mastering-narrative-intelligence-from-data-signals-to-strategy))
- Corporate Governance Forum (Harvard Law), "Narrative Contradictions: The Invisible Governance Risk." Cross-issue coherence as board-level diagnostic. ([HLS CorpGov](https://corpgov.law.harvard.edu/2025/09/13/narrative-contradictions-the-invisible-governance-risk/))

**Project-internal references:**

- `docs/rubrics/judge-design-guide.md` — design SOTA, §5 ceiling, §11 Goodhart-resistance, §11.5 variance instrumentation, §12 anti-pattern catalogue.
- `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` — v0 monitoring spec being deepened.
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` — CI v3.3 precedent for the §5 documented-exception path (CI-6).
- `docs/research/2026-05-15-judges-domain-monitoring.md` — sibling domain research (MON-A..MON-G generalist treatment); this deliverable deepens the MON-E (compound + projection) and MON-F (absent-signal) axes specifically.
