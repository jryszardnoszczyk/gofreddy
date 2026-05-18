---
date: 2026-05-18 v3.4
type: judge-design Step 1 — competitive (CI) optimal-output spec
status: DRAFT v3.4 — surgical restoration from live code (ce386b8) applied to v3.3; ready for redundancy check + fixture validation + propagation
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
companions:
  - docs/research/2026-05-15-judges-domain-competitive.md (generalist CI domain research)
  - docs/research/2026-05-18-ci-vertical-conventions.md (vertical-specific CI conventions)
  - docs/research/2026-05-18-ci-artifact-taxonomy.md (CI artifact shape taxonomy)
  - docs/research/2026-05-18-ci-ai-failure-modes.md (LLM-specific CI failure modes)
  - docs/research/2026-05-18-ci-decision-format-mapping.md (CI decision-to-format mapping)
revision_history:
  - 2026-05-17 v0 — initial draft, 6 criteria, before design guide locked
  - 2026-05-18 v1 — dropped to 5 criteria, added CoT, added 0.5=unknown, added shared wrapper, hedged score-1 examples
  - 2026-05-18 v2 — Path-A iteration with JR (Reader / Success / Failure / Criteria locked)
  - 2026-05-18 v3 — 4 deep-research passes added §1.5 Artifact-shape LOCKED, 4th mediocre mode, AI-specific failures in §3b, 3 vertical examples per criterion, NEW CI-6 evidence-chain
  - 2026-05-18 v3.1 — simplified in place per JR push-back on over-engineering (later determined to be over-correction)
  - 2026-05-18 v3.2 — restored v3's research-backed defenses after honest reassessment:
      Restored §1.5 Artifact shape (LOCKED) — defends against shape-drift Goodhart documented as a real failure mode in evolution-loop literature (artifact-taxonomy research);
      Restored healthcare vertical examples (3 per criterion on CI-1, CI-2, CI-3, CI-5) — defends Klinika and other healthcare fixtures from Pinsent-shape Goodhart (vertical-conventions research);
      Restored structural_gate to 9 checks (5 anti-hallucination + 4 shape-conformance) — each defends a specific documented failure rate; deterministic verification belongs in structural_gate per OpenRubrics design principle, NOT in the judge;
      Kept cut from v3.1: §3a's 4th mediocre mode header (folded into §1.5's rationale; the failure mode is named there) + §6 closing line about shape-drift caught upstream (redundant);
      Net: spec back to ~4400 words; aligns with the research-backed defense layer.
  - 2026-05-18 v3.3 — first-cohort overfitting reduction:
      Reader spec → substitute-readers list broadened beyond DWF/Klinika first-cohort (added DTC e-commerce, B2B SaaS at any scale, fintech, hospitality, retail) + explicit note that legal/AI-lab/healthcare reference set is concrete-anchor not architectural-target;
      §1.5 → added "Empirical validation scope" note acknowledging form factor is research-grounded against first-cohort fixtures only and may need adjustment when new-vertical fixtures appear;
      CI-2 Example C → DermaCenter healthcare → Stripe fintech (rotates 3rd vertical away from Klinika-shape);
      CI-5 Example C → DermaCenter healthcare → BambooHR-vs-SOC2 B2B SaaS (rotates 3rd vertical);
      KEPT: CI-1 + CI-3 retain DermaCenter healthcare Example C (Klinika is a real first-cohort client; healthcare anchor still defends specifically against legal/AI-lab-only Goodhart on those criteria);
      Net: 5 verticals represented across the 4 example-bearing criteria (legal / AI-lab / healthcare / fintech / B2B SaaS); first-cohort references kept as concrete fixtures but no longer architectural-default.
  - 2026-05-18 v3.4 — surgical restoration of load-bearing live-code prose (cross-check audit `docs/handoffs/2026-05-18-judge-design-v1-cross-check.md`, baseline `ce386b8`):
      CI-1 restored live CI-4 "capacity-to-act" good-vs-better pair (llms.txt by Mar 26 / your dev can do this in a half-day) as an inline capacity-sizing note;
      CI-1 restored live CI-7 "not everything is Priority 1 / 2-3 actions drive disproportionate impact" prioritization discipline as an explicit score-1 extension;
      CI-1 restored live CI-5 asymmetric-opportunity framing ("not just what no one is doing, but what no one is doing that this client is uniquely positioned to own") as an explicit target-naming consideration — folded into CI-1 rather than reintroduced as CI-7 to preserve the 6-criterion ceiling exception;
      CI-6 restored live CI-8 "gap itself is treated as an intelligence finding" reframe in score-1 prose;
      §8 restored explicit 12-phrase `CI_BANNED_PHRASES` list (preserved as the consulting-slop blocklist; the AI-slop tells extension stays as an addition, not a replacement);
      §8 restored explicit SOV-negation-filter structural_gate check (run #2 bug — "would be misleading" / "would be" / "not a" excluded).
      Net: live CI-4/CI-5/CI-7/CI-8 load-bearing prose now survives in v3.4; v3.3 architecture (6 criteria, decision-shape-aware reader, AND-anchors, structural_gate 9-check list, AI-failure surfaces) preserved without change.
---

# Competitive Intelligence — Optimal-Output Spec (DRAFT v3.4)

Conforms to `docs/rubrics/judge-design-guide.md` with one documented exception (§7). Frameworks (Helmer, Porter, Martin, Christensen, Dunford, etc.) inform the reader/success/failure spec and are the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

This v3.2 supersedes the v3.1 over-correction and restores v3's research-backed defenses. Each elaboration here is anchored in one of the 4 deep-research deliverables: §1.5 LOCKED (artifact-taxonomy research — shape-drift Goodhart is a documented failure mode in evolution loops); 3 vertical examples per criterion (vertical-conventions research — Pinsent-shape Goodhart documented across legal/AI-lab/healthcare verticals); structural_gate 5 anti-hallucination checks (AI-failure-modes research — 19.9–37% documented citation-fab rates require deterministic verification, which judges can't do); §3b AI-specific failure surface awareness; CI-6 evidence-chain.

The v3.1 simplification taught a real lesson: looks-elaborate ≠ over-engineered. Each deterministic check is a thin defense against a measured failure rate. Cutting them shifts brittleness from a testable layer (`structural_gate`) to a layer that can't do the work (the semantic judge).

---

## 1. Reader (LOCKED 2026-05-18)

A founder-CEO or VP of Strategy at a tech-savvy company that has commissioned competitive intelligence to inform an upcoming decision. The reader may be:

- **Reading reactively** after a competitive signal (customer-evaluating-competitor, lateral hire, regulator letter, partnership announcement) with leadership-meeting pressure to commit by next week
- **Reading proactively** before a planning meeting (quarterly off-site, board prep, annual strategy) where they will allocate next quarter's roadmap / budget / market focus
- **Reading on-demand** because someone asked "what's happening with X" and the answer affects a near-term call

They are smart, time-poor, and skeptical — they've been pitched enough strategic frameworks to recognize slot-fills. They have the authority to act on the brief: reroute a roadmap, re-price a tier, commit a budget envelope, call a customer or partner. They will quote one or two sentences from the brief if challenged later.

**Decision-making shape varies by vertical** (per `docs/research/2026-05-18-ci-vertical-conventions.md`):
- **Tech / AI-lab style** — solo founder or small exec team; fast unilateral decisions; founder reads the brief and acts within the week
- **Professional-services style** — partner committee or executive committee; mediated consensus build; brief gets quoted into a partner-vote conversation 1–4 weeks out
- **Healthcare-practice style** — practice owner solo or with one medical director; local-market focus; decision tied to a specific upcoming patient-acquisition window or vendor-contract renewal

The brief still has to drive concrete action regardless of which decision-making shape the reader operates in — but the "commit by" timeline scales to the decision-shape-appropriate gate (next week for fast reactive, next quarter-end for evaluate-class decisions, next vendor-cycle for healthcare).

**Reading time budget is not load-bearing.** They read until they have what they need, then stop. Length guidelines route to `structural_gate`, not the judge.

Substitute readers the same brief should also serve: Head of Product evaluating a roadmap pivot; Corp Dev / strategy lead at later stage evaluating an acquisition; decision-maker at a small-to-mid B2B services firm (legal, accounting, consulting, agency, financial advisory) evaluating lateral-flight or competitive moves; owner-operator at a small-to-mid local-market business (healthcare, hospitality, retail, professional services) evaluating market entry / pricing / referral patterns; Head of Marketing or Strategy at a DTC e-commerce platform or B2B SaaS at any scale evaluating channel / pricing / positioning shifts; fintech or regulated-finance operator evaluating regulatory or competitor-product threats.

The legal-services + AI-lab + healthcare reference set in this spec exists because those are gofreddy's current first-cohort fixture clients (DWF, Anthropic, Perplexity, Klinika). They are **not** the architectural target — they are concrete anchors. The spec is designed to generalize to tech-savvy-founder / early-co clients across verticals; first-cohort overfitting is an explicit risk to monitor (see §8).

NOT the reader: comms director (different decision shape — see monitoring lane); consulting partner reading for entertainment; researcher cataloging the market; investor doing diligence.

---

## 1.5. Artifact shape (LOCKED 2026-05-18)

**The lane produces ONE hybrid CI brief format**, per `docs/research/2026-05-18-ci-artifact-taxonomy.md`. Locked because shape-drift Goodhart is a documented failure mode in evolution loops: under 50-generation selection pressure, the workflow learns that teardown-shaped outputs score well on CI-3 (mechanism) while war-game-shaped outputs score well on CI-2 (trajectory), producing Frankenstein artifacts that don't serve any coherent reader. The lock prevents this.

**Form factor:**
- 800–2,000 words total
- **Klue 5-section spine:** headline-as-claim → rationale → comparison → implications → recommendations
- **CB Insights triple as Implications scaffolding:** for the dominant threat, "what they're doing now / where they're going next / why this is a priority"
- **War-game-flavored trade-off rigor on the recommendation:** explicit pairing of bet ↔ cost ↔ contingency

**Out of scope shapes (the lane will NOT produce these):**
- 30-page strategic teardown (CB Insights / Stratechery deep dive)
- 1-page sales battlecard (Klue / Crayon / Kompyte format)
- Weekly monitoring digest (handled by `monitoring` lane)
- Multi-scenario war-game memo (multi-branch contingency planning)

**Why one shape:** the v2 Reader spec (founder/VP archetype) and Success spec (commits to single concrete action) point unambiguously to executive-briefing form. CI-3 (structural mechanism) and CI-2 (trajectory with 2+ independent signals) presume teardown-grade evidence depth that pure Klue briefings don't carry — so the hybrid blends Klue's actionability skeleton with CB Insights' evidence depth and war-game-style trade-off framing.

**Decision-class scope:** the hybrid form serves the **React cluster** decisions (retention threat / pricing response / roadmap pivot / outreach decision) per `docs/research/2026-05-18-ci-decision-format-mapping.md`. Evaluate-cluster (acquisition target / market entry) and Structure-cluster (partner / channel selection) decisions may need different shapes — those are deferred to future lane work; current spec scopes to React only.

**Shape enforcement lives in `structural_gate`, NOT in the judge criteria.** The judge tests outcomes (CI-1..CI-6 below); the workflow's structural_gate tests artifact-shape conformance (word count band, section presence, comparison structure, CB Insights triple). Per design guide §11.1, this preserves the outcome-question-not-feature-check discipline at the judge layer while still defending against shape-drift.

**Empirical validation scope.** The hybrid form factor is research-grounded against legal-services / AI-lab / healthcare / B2B-SaaS fixtures (current first-cohort: DWF, Anthropic, Perplexity, Klinika). When fixtures from new verticals appear (DTC e-commerce, regulated finance, hospitality, marketplaces, etc.), re-validate the form factor — different verticals may need shape adjustments (e.g., regulated-finance briefs may need a compliance-context section; DTC briefs may need a unit-economics-by-cohort comparison instead of the standard comparison structure). The §1.5 lock is the React-cluster-default; lane scope may expand or sibling-fork as the client mix evolves.

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18)

After reading, the reader commits to a single specific concrete action on the most-consequential development surfaced in the brief. The action may be:

- A competitive **posture** (attack / defend / flank / cooperate / ignore) on a named threat
- A **budget reallocation** (pause channel X, accelerate spend on Y)
- A **roadmap change** (ship counter-feature, kill in-flight initiative, redirect engineering capacity)
- An **outreach call** (reach the prospect-customer, call a partner, engage a regulator)
- A **hiring move** (accelerate a search, defer a hire, restructure a function)
- A **follow-up intel ask** (commission specific deeper research, watch a named signal, set up a monitoring trigger)

The reader knows what they're giving up — the action has an explicit cost the reader could explain to their CFO or board. They could explain the call to a peer in 90 seconds. **Sleep test:** if they slept on it overnight, they'd make the same call tomorrow — the brief's logic survives 24h reflection, not just momentum.

The brief may also surface a *secondary* follow-up intel ask (the next question the reader should commission). Primary success is still the concrete action on what's known now; the follow-up ask is a bonus, not a substitute.

World-class real-world exemplars — used as quality anchors, NOT as templates to copy:

**Cross-industry rigor (the ceiling):**
- **McKinsey / Bain war-game memos** — output is competitor *response pattern* prediction (what they'd do in 2–3 likely scenarios), not competitor position description. Works across SaaS / legal / healthcare / finance.
- **Bloomberg Intelligence / S&P sector briefs** — quantitative anchor, named comparable, falsifiable forward claim. Most rigorous of the reference set.

**Practitioner-grade (the achievable floor):**
- **Klue executive-briefing template** — headline-as-claim, rationale, comparison, implications, recommendations. Workmanlike, closer to what real fixture briefs look like, earns its place when executed well.

What ties these together: point of view at the top, structural reasoning, trajectory not snapshot, one or two calls the reader could commit to before the next meeting.

---

## 3. Failure — mediocre and Goodhart-collapse (LOCKED 2026-05-18)

### 3a. Mediocre — three failure modes the judge must discriminate against

**Catalogue / clip dump.** Reads as competitor activity log ("Acme launched X on May 1, priced $99, includes A/B/C"). No claim, no implication. Reader stays on current path. Octopus Intelligence's named "data dump, not intelligence" failure.

**Plausible strategy memo with no actionable specifics.** Reads as a competent strategy memo — has a narrative, a trajectory section, recommendations — but every recommendation is one level too abstract ("strengthen positioning" instead of "reprice the SMB tier by 15% by Q3"). Looks competent in slide-deck view. Doesn't survive the test of "what would the reader actually do?"

**Single-hypothesis confirmation bias.** Brief reinforces the reader's existing prior. No disconfirming evidence engaged, no alternative hypothesis surfaced. Reader nods through, commits to nothing they weren't already going to do. Comfortable rather than uncomfortable.

### 3b. Goodhart-collapse — Phase 4 pathology + AI-specific failure surfaces

**Phase 4 pathology (the historical Goodhart trap):** 50-generation evolution against a feature-checking judge produced exactly the pathology rolled back at `c76f051` (commit `698e658`). The workflow learns to slot-fill named surface markers:

- **Helmer-power name-drops.** Every competitor advantage gets tagged with a 7 Powers name (Scale Economies / Process Power / Counter-Positioning / Switching Costs / Branding / Cornered Resource / Network Economies), with or without the structural mechanism behind it. Surface marker present, analytical rigor absent.
- **Framework-headline templating.** Every section opens with "Mechanism of Advantage:", "Trajectory:", "Trade-offs:" — section structure mimics consulting-deck format regardless of whether the section earns its name.
- **ACH / Heuer alternative-hypothesis strawmen.** "Alternative Hypotheses Considered" section with two visibly weak strawmen + the favored hypothesis. Looks like analytic rigor, performs zero disconfirmation.
- **Hard Prioritization fabricated percentages.** Closing recommendations carry fabricated quantified outcomes ("18% ARR loss if delayed") without supporting analysis.
- **Trajectory by single-signal restated three ways.** "Where they're going next" section populated by one underlying signal expanded into three paragraphs.

**AI-specific failure surfaces (new in v3, per `docs/research/2026-05-18-ci-ai-failure-modes.md`):**

- **Entity confabulation.** Workflow invents competitors that don't exist, fabricates press-release excerpts, conflates similarly-named entities ("Cursor" the IDE vs "Cursor" the cursor-tracker, "Anthropic" vs "Anthropic Communications"). Documented at 19.9% citation-fabrication rate for GPT-4o; 37% failure rate in Perplexity production retrospectives.
- **Source confabulation.** Cited URLs that 404, papers that don't exist, analyst reports never published, quotes attributed to plausible-sounding executives who never said them, "internal data" with no provenance. Per HalluLens / FAITH / CompoundDeception benchmarks.
- **Recency / training-cutoff distortion.** "Recent" announcements that are months/years old; competitive landscape shifts that happened post-training-cutoff missed entirely; 2024 strategic environment projected into 2026. Per LLMLagBench + "Is Your LLM Outdated?" NAACL 2025.

Every surface marker present, structurally compliant, strategically empty — and now structurally invalid via confabulated entities / sources / dates. The judge that rewards these gets the workflow that learns to produce them.

**Historical context.** This lane (or its siblings) has triggered three prior rollbacks for the same underlying Phase-4 pathology: `2ce99bb` (σ-widening prose, J1–J4), `ca4a256` (v2 contract-prose), `698e658` (Phase 4 feature-checking → `c76f051`). The criteria below are designed to resist re-creating any of them AND to surface the new AI-specific failure surface that those rollbacks didn't address.

**Deterministic AI-failure checks live in `structural_gate`** — URL HEAD resolution (catches dead cited links), quote-grep against source corpus (catches fabricated quotes from real URLs), entity-existence lookup (catches invented competitor entities), "as of" date requirement (forces freshness signaling), ≥1 cited source dated within 90 days (defends against recency-cutoff distortion). Per the OpenRubrics design principle (Hard Rules → structural_gate, Principles → judge), deterministic verification belongs in `structural_gate` because the judge cannot deterministically verify URL resolution, quote provenance, entity existence, or date freshness — those are factual checks, not semantic judgments. **Semantic evidence-chain integrity lives in CI-6** below.

---

## 4. Criteria — outcome questions (6)

### CI-1 — Forces a concrete action commitment

**Outcome question (binary):**
After reading, would the reader commit to a single specific concrete action — a competitive posture, budget reallocation, roadmap change, outreach call, hiring move, or follow-up intel ask — on the most consequential development surfaced by the brief? Could they walk into their next leadership meeting and assign this action by the next decision-shape-appropriate gate?

**Score 1 (yes)** — Brief makes the single most-consequential call so concretely that disagreeing requires a counter-argument, not a shrug. The recommended action names BOTH a specific action type AND a specific target: posture toward a named competitor, budget shift in a named category, roadmap change to a named initiative, outreach to a named person, hiring move for a named role, or intel ask on a named question. The reader could commit by the next decision-shape-appropriate gate (next week for reactive, next quarter-end for evaluate-class, next vendor-cycle for healthcare-style).

Example A (do not optimize toward this): "The 6-partner Pinsent Masons RES lateral pull is the dominant Q3 retention risk; defend, by accelerating the senior associate equity-vesting conversation we already deferred. Costs: ~$1.4M ahead-of-plan; we lose the option to use that capital on the Birmingham office plan."

Example B (do not optimize toward this): "Claude 4.7 Computer Use 2.0 rollout October 15 is the dominant Q4 differentiation risk for our agent platform; flank, by shipping our MCP-native tool-orchestration patch and signing exclusive partnerships with two vertical-SaaS dev-tools companies by end of October. Costs: 8 engineer-weeks pulled from the v3 orchestrator team; defer enterprise compliance certification by one quarter."

Example C (do not optimize toward this): "DermaCenter West opened a 2-injector medspa within 0.8 miles of our location and is offering $30K-off membership pricing through April; defend our top-decile Botox cohort by escalating the loyalty-program-V2 launch from Q3 to next month and offering matching $30K bundles to the 47 highest-LTV patients we'd most lose. Costs: ~$94K margin against current Q1 spend; defer the laser-skin-resurfacing investment by one quarter."

**Capacity-sized recommendation note.** A score-1 recommendation is also sized to the client's *actual* capacity to act. "Deploy llms.txt by Mar 26" is good. "Deploy llms.txt by Mar 26, your dev can do this in a half-day" is better. Recommendations the client can't execute — because the named timeline, headcount, or budget envelope doesn't fit their actual operating reality — are decoration, not action.

**Prioritization discipline.** When the brief surfaces multiple findings, not everything is Priority 1. A score-1 brief makes the hard call about which 2–3 actions drive disproportionate impact and which findings are interesting but not urgent. The single most-consequential call still anchors the brief; secondary priorities, where present, are explicitly de-ranked rather than presented as parallel.

**Asymmetric-opportunity test.** Where the brief identifies an opportunity rather than a defensive move, the named target reflects an asymmetry — not just a gap in the landscape, but a gap this specific client is uniquely positioned to own (a strength, channel, relationship, dataset, or capability the competition can't or won't bring). Generic "no one is doing X" gaps that any competent operator could fill are not asymmetric and do not earn score 1 on their own.

**Score 0 (no)** — Brief gives a competitor activity update. No implied next move. Or recommendation is one level too abstract ("strengthen positioning," "explore the segment"). Or recommendation is wrong-timeline-shape for the decision (recommends "by next week" for an acquisition evaluation that has a 12-week horizon, or vice versa). Or recommendation is not sized to the client's actual capacity to act. Or everything is Priority 1 with no hard call about which 2–3 actions drive disproportionate impact. Reader finishes informed but uncommitted.

**Score 0.5 (unknown)** — Brief makes a concrete call but the reader could not commit without one additional piece of information explicitly named in the brief as missing. Emit 0.5 + "unknown" + one sentence on what's missing.

**Required CoT:**
- Step 1: Identify the single most consequential development the brief surfaces.
- Step 2: Find the brief's recommended action on that development; verify it names BOTH a specific action type AND a specific target the reader could act on by the decision-shape-appropriate gate.
- Step 3: Emit verdict + one-sentence justification.

Do not score: word count, presence of framework headers, executive-summary structure. Those live in structural_gate or do not matter.

### CI-2 — Trajectory over snapshot

**Outcome question (binary):**
Does the analysis project where the competitive threat is heading 6–18 months out using more than one independent signal, or does it describe where it is today? If the reader re-read this brief in 90 days, would they see most of its forward calls starting to materialize?

**Score 1 (yes)** — At least one falsifiable claim about where the competitor is heading, backed by 2–3 convergent independent signals (M&A, hiring, product roadmap, earnings language, partnership pattern, regulatory positioning, lateral hires, model-card improvements, location density, vendor relationships). Reader could check in 90 days whether the call held.

Example A (do not optimize toward this): "Slaughter & May's Q1 lateral data shows 4 partner moves into financial-services-regulatory + their newly-published policy positions emphasize MiFID III readiness + their training-contract intake is FS-regulatory-heavy — they're rebuilding their FS practice depth to defend against incoming CMS / Latham hires through FY26."

Example B (do not optimize toward this): "Anthropic's Q3 model-card showed 12pp improvement on agentic tool use + their last 8 hires are post-training researchers from RL labs + their CEO podcast appearances all emphasized 'agents not chat' — they're reorienting around agentic capabilities through 2026."

Example C (do not optimize toward this): "Stripe's last 3 product launches all target vertical-SaaS platforms (Connect Embedded, Issuing-for-platforms, Tax-as-a-service) + their Q3 earnings call emphasized 'embedded fintech' 11 times + their reseller-network growth doubled YoY — they're moving up-market into vertical-SaaS-platform PSP positioning through 2026, away from the original developer-API base."

**Score 0 (no)** — Descriptive snapshot only. Or forward call by linear extrapolation from one signal ("they raised $40M, so they're going up-market").

**Score 0.5 (unknown)** — Forward call exists but the supporting signals are ambiguous or unverifiable from the brief alone. Emit 0.5 + "unknown" + one sentence on what would have to be in the brief to commit to 1.

**Required CoT:**
- Step 1: List every forward-looking claim in the brief.
- Step 2: For each, identify the supporting signals (must be 2+ independent for score 1).
- Step 3: Emit verdict + one-sentence justification.

Do not score: number of competitors covered, presence of trajectory headers, exhaustiveness.

### CI-3 — Structural mechanism of advantage

**Outcome question (binary):**
When the brief attributes an advantage to a competitor, does it identify the specific structural mechanism that advantage rests on — and pass the test that a competitor can't or won't replicate it? Could the reader explain to their CTO / managing partner / medical director in one sentence why this threat is structurally durable, or specifically why it isn't?

**Score 1 (yes)** — For at least one competitor advantage named, the brief identifies the source of the advantage AND the structural reason it's hard to copy. Or — equally valuable — explicitly rejects an apparent advantage as replicable operational effectiveness rather than sustainable positioning.

Example A (do not optimize toward this): "Slaughter & May's senior-associate retention advantage looks like cultural moat, but it's actually a structural compensation premium of ~12% above market that they fund from partner-comp — replicable in principle but not without partner-comp restructuring we won't do."

Example B (do not optimize toward this): "Anthropic's tool-use advantage looks like model architecture, but it's actually a curated training-data moat from their constitutional-AI work + a documented red-team-prompt corpus — not replicable without 18+ months of safety-research investment we won't make."

Example C (do not optimize toward this): "DermaCenter's patient-acquisition advantage looks like marketing spend, but it's actually a board-certified-injector hiring pipeline they've cultivated via residency partnerships at 3 Warsaw medical schools — not replicable in the next 24 months without similar relationship-building."

**Score 0 (no)** — Asserts an advantage ("they have scale," "their brand is strong") without the structural reason it's hard to copy. Or the named mechanism doesn't fit what the brief describes.

**Score 0.5 (unknown)** — Mechanism named but evidence in the brief is insufficient to confirm whether the advantage is sustainable or replicable. Emit 0.5 + "unknown" + one sentence on what would resolve it.

**Required CoT:**
- Step 1: List every advantage attributed to a competitor.
- Step 2: For each, identify the brief's claim about the underlying mechanism + whether it passes the "can't or won't replicate" test.
- Step 3: Emit verdict + one-sentence justification.

Do not score: number of frameworks invoked, presence of "Mechanism of Advantage" section header.

### CI-4 — Uncomfortable truth surfaced

**Outcome question (binary):**
Does the brief surface at least one finding the reader's organization probably doesn't want to hear — and stand by it with enough evidence to defend in a leadership meeting? If the reader read this aloud at their next leadership offsite, would at least one person be visibly uncomfortable?

**Score 1 (yes)** — At least one finding pushes against the company's prior — about a customer segment that's eroding, a product strength that's actually replicable, a competitor that's stronger than leadership admits, a market trajectory the company is misreading. The finding earns its weight with evidence, not provocation.

Example (do not optimize toward this): "Our 'enterprise readiness' is the prior most likely to be wrong. The Pinsent move signals the senior-RES tier — our claimed strength — is the actual lateral-flight risk, not the junior tier we've been hedging on."

**Score 0 (no)** — All findings confirm the reader's existing narrative. No disconfirming evidence engaged.

**Score 0.5 (unknown)** — Uncomfortable claim made but the supporting evidence is too thin to defend in a leadership meeting. Emit 0.5 + "unknown" + one sentence on what evidence is missing.

**Required CoT:**
- Step 1: Identify the company's apparent priors from the brief's framing (what does the brief assume the reader believes?).
- Step 2: Find any finding that contradicts those priors with supporting evidence.
- Step 3: Emit verdict + one-sentence justification.

Do not score: confrontational tone, presence of "uncomfortable truths" section header, number of priors challenged.

### CI-5 — Trade-off in the recommendation

**Outcome question (binary):**
Does the recommended action name what the company gives up by committing — the budget, scope, market, capability, or initiative that has to be sacrificed? Real strategy always costs something; a recommendation that's free is a wish.

**Score 1 (yes)** — 1–3 specific recommendations, each pairing the bet with the explicit thing being sacrificed. The reader could explain to their CFO / partnership / medical director what budget line moves, what initiative pauses, what segment de-prioritizes. The cost is specific enough to be uncomfortable.

Example A (do not optimize toward this): "Defend senior RES tier via accelerated equity vesting. Cost: ~$1.4M ahead of plan, which means deferring the Birmingham office launch by 6 months."

Example B (do not optimize toward this): "Flank with MCP-native tool-orchestration shipped by end October. Cost: 8 engineer-weeks pulled from the v3 orchestrator team, which means deferring the enterprise compliance certification by Q1."

Example C (do not optimize toward this): "Defend our 50-employee SMB tier from BambooHR's compliance-bundle expansion by accelerating SOC2-prep-as-a-service launch from Q4 to next month. Cost: 4 engineering weeks pulled from custom-roles work, which means deferring that feature by one quarter."

**Score 0 (no)** — Recommendation is a wish ("improve," "double down on," "explore"). Or pairs gains with no costs. Or 5+ recommendations of equal weight with no acknowledged trade-off.

**Score 0.5 (unknown)** — Trade-off named but quantification absent, leaving the CFO unable to evaluate the cost. Emit 0.5 + "unknown" + one sentence on what would need quantifying.

**Required CoT:**
- Step 1: List every recommendation in the brief.
- Step 2: For each, identify the explicit cost / sacrifice named.
- Step 3: Emit verdict + one-sentence justification (must reference the largest-stakes recommendation).

Do not score: number of recommendations, presence of "Trade-offs" section header, quantification precision (a CFO-recognizable cost is enough, exact ROI is not required).

### CI-6 — Evidence chain survives tracing (NEW in v3)

**Outcome question (binary):**
For each major strategic claim in the brief, does the evidence chain survive tracing — i.e., are the underlying signals named, the cited sources verifiable, and disconfirming alternatives engaged? Or does the brief collapse into plausible-tone synthesis where confident-sounding strategic claims rest on no traceable chain?

**Score 1 (yes)** — At least the top-3 strategic claims in the brief (the headline, the dominant-threat trajectory call, the structural-mechanism diagnosis) each (a) name the specific signals they rest on, (b) cite verifiable sources (named entity / dated event / specific document / quoted attribution), AND (c) acknowledge at least one alternative interpretation the evidence does NOT rule out. Confidence is calibrated to evidence depth — strong claims have multi-source backing; tentative claims are flagged as tentative. When data sources failed or returned partial coverage, the brief recalibrates rather than speculates: it names what is missing, what analysis became impossible, and how the remaining data changes what can be concluded — **the gap itself is treated as an intelligence finding**, not silently omitted or papered over with inferred data presented at unearned confidence.

Example (do not optimize toward this): "Pinsent's senior-RES expansion (per their Sept 23 partner-promotion announcement + Chambers Tier-2 → Tier-1 RES shift in 2026 + 3 lateral RES partner moves in Q3 per ALM lateral tracker) suggests they're rebuilding RES practice depth. Alternative reading: this is a 1-year build, not a 3-year strategic shift — we can't yet distinguish from one round of opportunistic hiring. Confidence: medium, will firm up if Q1 2027 promotions also skew RES."

**Score 0 (no)** — Claims are confident-toned but evidence chain breaks under inspection: unnamed signals, fabricated sources, single-source extrapolation presented as multi-signal, no disconfirming alternative engaged. OR brief contains entity confabulations (competitors that don't exist, fabricated quotes, conflated similarly-named entities), source confabulations (404 URLs, unverifiable cited reports), or recency-cutoff distortions (months-old "recent" announcements, training-cutoff landscape projected into present).

**Score 0.5 (unknown)** — Evidence chain partially traces, but one of the top-3 claims has insufficient supporting detail in the brief itself to evaluate verifiability. Emit 0.5 + "unknown" + one sentence on which claim's evidence chain is unclear.

**Required CoT:**
- Step 1: Identify the top 3 strategic claims in the brief (headline + dominant-threat trajectory + structural-mechanism diagnosis).
- Step 2: For each, walk the evidence chain: are signals named? Are sources verifiable (named-entity / dated-event / specific-document / quoted-attribution)? Is at least one disconfirming alternative acknowledged?
- Step 3: Flag any entity confabulation (made-up competitor, conflated similar-name), source confabulation (cited URL/paper/quote that doesn't exist), or recency distortion (months-old "recent" claim, post-cutoff event missed).
- Step 4: Emit verdict + one-sentence justification.

Do not score: citation count or footnote density (those route to structural_gate), presence of "Sources" or "Evidence" section header, comprehensiveness of citation lists.

**Note on the ≤5 ceiling:** CI-6 is a justified breach of design guide §5's ≤5 criterion ceiling. Rationale documented in §7 below. The redundancy check (§8) will tell us empirically if CI-6 correlates with another criterion >0.7; if so, the redundant criterion gets dropped to restore 5.

---

## 5. Shared judge-prompt wrapper

```
You are scoring a competitive-intelligence brief written for a
tech-savvy founder/CEO or VP of Strategy. The reader may be at a
tech company, a professional-services firm (legal, accounting,
consulting), or a healthcare practice. Their decision-making
shape varies (solo founder fast / partner committee mediated /
practice owner local-market) but the brief still has to drive
concrete action by the next decision-shape-appropriate gate.

The brief is the lane's locked artifact shape: 800–2,000 words,
Klue 5-section spine (headline-as-claim / rationale / comparison
/ implications / recommendations), with CB Insights triple
scaffolding (what-now / where-next / why-priority) in the
Implications section.

Score each criterion independently with 0, 0.5, or 1 plus a
one-sentence rationale that follows the per-criterion CoT steps.
Do not blend criteria. Do not infer criteria not stated. If a
criterion's condition is ambiguous from the brief alone, emit
0.5 + "unknown" + one sentence on what would have to be present
to commit to 1.

The reader is time-poor and skeptical. They've been pitched
enough strategic frameworks to recognize slot-fills. Test for
whether the brief would actually change a decision the reader
makes — not for whether it mentions named frameworks, contains
specific section headers, or follows a consulting-deck format.

Emit per-criterion JSON:
{"criterion_id": "CI-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 6. Goodhart-resistance verification

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **CI-1**: "Action templated by rotating through posture/budget/roadmap/outreach/hiring/intel-ask" doesn't pass — must name a specific target (named competitor / category / initiative / person / role / question) at the decision-shape-appropriate gate.
- **CI-2**: "Trajectory header populated by 1 signal restated 3 ways" doesn't pass — 2+ INDEPENDENT signals required.
- **CI-3**: "Helmer-power name-drop" doesn't pass — must include the structural reason a competitor can't or won't replicate.
- **CI-4**: "ACH-style alternative-hypothesis section with 2 strawmen + favored" doesn't pass — must push against the reader's actual organizational prior, not a manufactured strawman.
- **CI-5**: "Generic 'deprioritize other initiatives'" doesn't pass — CFO-recognizable cost required (named budget line, paused initiative, deferred segment).
- **CI-6**: "Confident strategic synthesis without underlying source chain" doesn't pass — top-3 claims must have named signals + verifiable sources + acknowledged alternative interpretation. Entity confabulation / source confabulation / recency distortion (the 3 AI-specific failure surfaces) each force a score 0.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0.

---

## 7. Verification — does the v3 spec conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (3 vertical examples per criterion where applicable: legal / AI-lab / healthcare) ✓
- §5 criterion count: **6 (documented exception to ≤5 ceiling)** — see note below
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3–4 steps each) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §11 Goodhart-resistance verification ✓
- §13 specimen criterion template followed ✓

**Note on the ceiling exception:** CI-6 (Evidence chain survives tracing) is a 6th criterion justified by the AI-specific failure surface documented in `docs/research/2026-05-18-ci-ai-failure-modes.md` — entity confabulation (19.9% GPT-4o citation-fab rate), source confabulation (Perplexity 37% failure shape), and recency-cutoff distortion. Subject to the same redundancy check as the rest: **the live count is probably 5 after the check runs** — CI-6 most likely absorbs into CI-2 (trajectory backed by 2+ signals) since both test for traceable evidence chains. Don't fight the absorption when it happens.

Length per criterion ≈ 200 words (longer than the design guide's 150-word target due to 3 vertical examples per criterion; absorbable). Total spec body ≈ 4400 words including §1.5 and §3b expansions.

---

## 8. Open questions (after Path-A iteration + 4 deep-research passes + v3.4 live-code restoration)

**v3.4 surgical restoration note.** Cross-check against live code `ce386b8` (the 14 judge rewrites baseline) recovered six load-bearing prose items that did not survive v0→v3.3: live CI-4 "capacity-to-act" good-vs-better example pair (folded into CI-1 as the capacity-sized recommendation note); live CI-5 asymmetric-opportunity framing (folded into CI-1 as the asymmetric-opportunity test); live CI-7 prioritization discipline ("not everything is Priority 1," 2–3 actions drive disproportionate impact — folded into CI-1 as the prioritization discipline note); live CI-8 "gap itself is treated as an intelligence finding" reframe (folded into CI-6 score-1 prose); the 12-phrase `CI_BANNED_PHRASES` consulting-slop blocklist (restored verbatim to §8 structural_gate, with AI-slop tells now layered on top rather than substituted in); SOV-negation-filter check (restored verbatim to §8). v3.3 architecture (6 criteria, decision-shape-aware reader, AND-conjunction-style anchors, structural_gate 9-check list, §3b AI-failure surfaces) unchanged. Intentionally NOT restored: live CI-5 as a 7th standalone criterion (would breach the documented ≤5 ceiling exception twice; asymmetric-opportunity is more parsimonious as a CI-1 target-naming consideration); live CI-3's "what each competitor is abandoning" phrasing (drift to v1 CI-2 trajectory framing flagged as DRIFTED in audit but not LOST — JR signal needed on whether to surface the abandonment dimension explicitly); live CI-6 "not optimized to make the client feel good" internal-posture phrasing (v1 CI-4's "at least one person visibly uncomfortable" external-test surface was an intentional drift, kept).

Reader / Artifact-shape / Success / Failure / 6 Criteria are LOCKED at v3. Remaining:

1. **Redundancy check pending (urgent).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 6 criteria × 3 panel models = ~90 calls (~$35). Drop any criterion correlating >0.7 with another. Expected live floor 3–5 (CI-6 may absorb into CI-2 if evidence-chain ends up correlating tightly with trajectory-source-traceability). Most-likely-to-merge pairs: CI-2 (trajectory) ↔ CI-6 (evidence chain); CI-3 (mechanism) ↔ CI-5 (trade-off).

2. **Fixture validation.** Run 5 existing CI fixtures (current Phase-3 Anthropic / DWF / Perplexity outputs + at least 1 Klinika-class healthcare fixture if available) through the locked criteria; eyeball judge rationales. If the rationales don't match human reasoning about quality, the prose is wrong, not the design. Surface findings before propagating.

3. **`structural_gate` expansion (before spec ships to v006/workflows):** add 5 anti-hallucination checks + 4 shape-conformance checks. The existing v006 checks (3+ headings, 2+ citations, ≤2000 words, banned-phrases) stay.

   **Anti-hallucination checks (each defends a documented LLM failure rate):**
   - URL HEAD resolution — catches dead cited links
   - "as of" date requirement — forces freshness signaling
   - ≥1 cited source dated within 90 days — defends against recency-cutoff distortion (per LLMLagBench)
   - quote-grep against source corpus — catches fabricated quotes from real URLs (subset of Perplexity 37% failure)
   - entity-existence lookup (RapidAPI / OpenCorporates) — catches invented competitor entities (subset of 19.9% GPT-4o citation-fab rate); most operationally expensive of the set — can be implemented last, but skipping leaves a specific failure surface open

   **Shape-conformance checks (enforce §1.5 LOCKED):**
   - Word-count band (800–2,000)
   - Klue 5-section presence check (headline / rationale / comparison / implications / recommendations)
   - CB Insights triple presence in Implications (what-now / where-next / why-priority)
   - Comparison-structure check (at least one comparison element vs named competitor)
   - **SOV-negation-filtered check** (preserved from live code, run #2 bug fix): if the brief mentions "share of voice / share of observed / SOV," require at least one such sentence to also contain a numeric percentage AND not be negation-phrased ("would be misleading," "would be," "not a"). Prevents passing on phrasing like "A 0% SOV label would be misleading."

   **Banned-phrase list — consulting-slop blocklist (preserved verbatim from live code `CI_BANNED_PHRASES`, 12 phrases JR-iterated for CI specifically):**
   - "leverage social media"
   - "stay ahead"
   - "consider exploring"
   - "it's clear that"
   - "no doubt"
   - "it goes without saying"
   - "needless to say"
   - "at the end of the day"
   - "game-changer"
   - "best-in-class"
   - "synergy"
   - "low-hanging fruit"

   **Banned-phrase list extension** with AI-slop tells (em-dash density, "let me explain why," "moreover," "furthermore") — added on top of, not in place of, the 12-phrase consulting-slop blocklist above.

4. **Vertical fixture coverage.** Currently have legal (DWF) + AI-lab (Anthropic, Perplexity) coverage in fixtures; healthcare (Klinika) coverage is thin. Build 2–3 Klinika-style fixtures before locking the criteria via empirical redundancy check.

5. **Evaluate / Structure cluster decisions: deferred.** Current v3 spec is React-cluster only. When Evaluate-class fixtures appear (acquisition target, market entry), revisit `decision_shape` workflow input and possibly sibling-lane treatment per `docs/research/2026-05-18-ci-decision-format-mapping.md` §3-4.

6. **Propagation to other 7 lanes.** Once CI v3.3 validates on real fixtures, propagate the iterated pattern: GEO → MON → MA → SB → X → LI → site_engine. Each lane gets its own Path-A iteration + (optionally) lane-customized deep-research pattern — NOT a mechanical 4-question repeat. The 4 CI deep-research questions weren't equally relevant to all lanes; per-lane question scoping needed.

7. **First-cohort overfitting watch.** v3.3 broadened Reader / Example C / §1.5 to reduce DWF/Klinika-only anchoring, but the underlying research (vertical-conventions, artifact-taxonomy, decision-format-mapping) was still done against legal/AI-lab/healthcare verticals. Monitor: when client #5+ onboards (DTC e-commerce, fintech, hospitality, regulated finance, marketplaces), check whether the spec's substitute-readers + §1.5 form factor + criteria anchors generalize OR whether per-vertical adjustment is needed. Re-validation trigger: any fixture from a vertical not in {legal-services, AI-lab, healthcare, B2B-SaaS, fintech} should prompt a quick re-validation pass on the affected criteria.
