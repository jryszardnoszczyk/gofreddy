---
date: 2026-05-19 v3.7
type: judge-design Step 1 — competitive (CI) optimal-output spec — 5-component modular package
status: DRAFT v3.7 — post-verification surgical fixes per `docs/handoffs/2026-05-19-competitive-v3-verification.md`; judge layer preserved verbatim from v3.4 except CI-4 CoT Step 1 + CI-4 score-0.5/0 anchor split + CI-6 CoT Step 3 tightening + CI-3 4th example; §6a CI-6 Goodhart-mode bullet reconciled with CI-6 CoT; §8c rewritten as 3-phase pipeline (substrate-readiness → research validation → optional production observation); revision history reordered chronologically; deliverable surface preserved at 5-component modular package (Components A–F + optional G/H); substrate-readiness gate at §1.5 + first-cohort posture clause at §1 preserved from v3.6
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
companions:
  - docs/research/2026-05-19-competitive-comprehensive-scope.md (load-bearing — 24 axes, modular package architecture, modern-lever bias)
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
  - 2026-05-18 v3.2 — restored v3's research-backed defenses after honest reassessment
  - 2026-05-18 v3.3 — first-cohort overfitting reduction; broadened substitute-readers; rotated Example C verticals (Stripe fintech, BambooHR B2B SaaS)
  - 2026-05-18 v3.4 — surgical restoration of load-bearing live-code prose from baseline `ce386b8`:
      CI-1 restored capacity-sized recommendation note, prioritization discipline, asymmetric-opportunity test;
      CI-6 restored gap-as-intelligence reframe in score-1 prose;
      §8 restored 12-phrase `CI_BANNED_PHRASES` list + SOV-negation-filter check.
  - 2026-05-19 v3.5 — comprehensive-scope restructure per `2026-05-19-competitive-comprehensive-scope.md`:
      Judge layer (Criteria CI-1..CI-6, anchors, CoT, examples, Goodhart-resistance verification, banned-phrase list, SOV check, structural_gate anti-hallucination checks) preserved VERBATIM from v3.4 — no changes to criterion prose, no relaxation of discipline;
      Deliverable surface EXPANDED from "single comprehensive brief" to "5-component modular package" (Component A = brief.md / Component B = per-competitor profile cards / Component C = trajectory matrix / Component D = comparison-matrix narrative / Component E = watchlist + MON handoff / Component F = evidence appendix) with optional G (AEO presence comparison) and optional H (win-loss program integration);
      Judge scopes Component A only; Components B–F validated by structural_gate deterministic checks (presence, freshness, traceability, evidence-chain integrity);
      §1 substitute-reader list broadened to SaaS / AI lab / agency / service firm / finance / e-commerce; US-primary defaults made explicit; Polish first-cohort reframed as concrete-anchor not architectural-target;
      §3 cuts list expanded with 18 modern-lever bias items from research §2 (generic SWOT, Porter five-forces template, surface feature comparison, "they're a leader" without mechanism, recency-distorted claims, BCG/McKinsey deck shapes, framework-name slot-fill, single-hypothesis confirmation, benchmark-table-as-strategy, self-reported-score-trust, directory-rank theater, national-market-size opener, treatment-mix-as-feature-comparison, vague action prose, consulting-slop, AI-slop tells, confident-tone synthesis without evidence chain, length without point of view);
      §3 adds modern-lever bias coverage (15 levers from research §3: AI-native anatomy, AEO presence comparison, founder-visibility comparison, distribution-moat comparison, talent-flow inference, 90-day pricing sprints, comparison-page warfare intel, AI-call-recording win-loss, change-detection forensics, Sparktoro audience-intersection, founder X-thread reads, asymmetric-opportunity maps, Dunford counter-positioning, real-time signal injection, structured win-loss program);
      §6 Goodhart-resistance verification extended with per-component Goodhart modes (template-rigidity Goodhart on B–F; evidence-pointer Goodhart on D/F);
      §8 sibling-fork triggers added (Component B → competitor_profile lane if variance decouples; Component G → AEO-comparison lane if AEO load-bearing across cohorts; Component H → win-loss program lane if structured tooling matures);
      Net: judge surface area unchanged from v3.4; deliverable surface area ~5x; structural_gate surface area expanded to validate B–F per-component checks alongside existing Component-A shape-conformance + anti-hallucination set.
  - 2026-05-19 v3.6 — Option D surgical edits per spot-check audit (`docs/handoffs/2026-05-19-competitive-v2-spot-check.md`):
      CI-4 CoT Step 1 rewritten to score brief-stated priors only (not judge-imagined — high-variance under selection pressure per audit); CI-4 score-1 anchor tightened to require the brief to EXPLICITLY name the prior it's contradicting;
      CI-6 CoT Step 3 tightened to internal-inconsistency only (external entity/source/recency confabulation routes to structural_gate, which has corpus access; judge can't reliably verify those without it);
      CI-3 4th example added showing rejection-of-advantage scoring path in a tech-savvy founder context (AI-lab competitor's first-mover advantage explicitly rejected as operational, not structural);
      §1.5 Substrate-Readiness Gate clause added (Components B–F + optional G/H ship as substrate emission catches up; comprehensive scope remains the spec target; lane structural-gate-fails 100% of sessions if v3.6 ships against not-yet-emitting components);
      §1 first-cohort posture clause added (Klinika + DWF are the only two onboarded clients as of 2026-05-19; US-primary substitute readers are the architectural target as cohort expands; Polish-language fixture passes required before any v3.6 spec lock against Klinika/DWF; US-primary fixture passes required for architectural-target validation; straddle is intentional during cohort expansion);
      All v3.4/v3.5 architecture preserved: 5-component modular package unchanged, 6 criteria unchanged (CI-6 documented exception holds), CI_BANNED_PHRASES preserved, SOV-negation-filter preserved, capacity-sized recommendation / prioritization discipline / asymmetric-opportunity / gap-as-intelligence preserved, modern-lever CUTS/ADDS lists preserved, §5 wrapper unchanged.
  - 2026-05-19 v3.7 — post-verification surgical fixes per `docs/handoffs/2026-05-19-competitive-v3-verification.md`:
      CI-4 score-0.5 (a) condition rephrased to score 0 (preserves discrimination, fixes mean-floor compression risk from design guide §11.5 — under selection pressure with reference-free briefs, score-0.5 on every missing-prior brief would compress the mean toward 0.5; the missing-prior case is now "criterion does not apply → score 0" while the 0.5 anchor is reserved for briefs that ARE doing the uncomfortable-truth work but with thin evidence or implicit prior);
      §6a CI-6 Goodhart-mode bullet reconciled with the v3.6 CI-6 CoT tightening (internal-inconsistency-only at the judge layer; explicit cross-reference to structural_gate §3b URL HEAD-check + quote-grep + entity-existence lookup for external confabulation verification);
      §8c rewritten as 3-phase pipeline breaking the chicken-and-egg with §1.5 substrate-readiness gate (Phase 1 = substrate readiness per §1.5; Phase 2 = research validation via 3 holdout fixtures with ≥2/3 judge/human concordance, replaces original v3.6 retroactive-fixture gate; Phase 3 = optional production observation across ≥5 client engagements with <30% reference-back rate over 2 quarters demoting to optional);
      Revision history reordered chronologically (v3.5 entry now precedes v3.6 entry; v3.7 appended at end);
      All v3.4 / v3.5 / v3.6 architecture preserved: 5-component modular package unchanged, 6 criteria unchanged (CI-6 documented exception holds), CI_BANNED_PHRASES preserved, SOV-negation-filter preserved, capacity-sized recommendation / prioritization discipline / asymmetric-opportunity / gap-as-intelligence preserved, modern-lever CUTS/ADDS lists preserved, §5 wrapper unchanged, CI-1 / CI-2 / CI-3 / CI-5 / CI-6 prose unchanged (only CI-4 score-0.5/0 anchor split + §6a CI-6 Goodhart bullet + §8c rewritten).
---

# Competitive Intelligence — Optimal-Output Spec (DRAFT v3.7)

Conforms to `docs/rubrics/judge-design-guide.md` with one documented exception (§7). Frameworks (Helmer, Porter, Martin, Christensen, Dunford, etc.) inform the reader/success/failure spec and are the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

**v3.5 restructure summary.** v3.4 was correct as a judge-stability spec. It was incomplete as a description of the deliverable surface a 2026 modern AI-native agency must be capable of producing. The fix is **modular packaging**, per `docs/research/2026-05-19-competitive-comprehensive-scope.md`:

- The **judge layer** (criteria CI-1 through CI-6, anchors, CoT, examples, Goodhart-resistance, structural_gate anti-hallucination + shape-conformance set) is preserved **verbatim** from v3.4. No relaxation of discipline. The judge still tests a single 800–2,000-word executive brief against six outcome questions.
- The **deliverable surface** expands from "the brief" to a **5-component modular package**: Component A is the v3.4 brief (judge-scoped); Components B through F wrap the brief with depth that the judge does not see and `structural_gate` evaluates deterministically. Optional Components G and H extend the package where engagement scoping calls for them.
- **The judge surface stays constant; the deliverable surface grows roughly 5x.** This is the architectural trick that lets the lane be capable of all 24 axes of competitive intelligence (per the comprehensive scope research) without bloating the judge surface or expanding the Goodhart attack surface.

Each elaboration is anchored in one of the six prior research deliverables (generalist domain, vertical conventions, artifact taxonomy, AI failure modes, decision-format mapping, comprehensive scope). The v3.1 simplification lesson still applies: looks-elaborate ≠ over-engineered. Each deterministic check is a thin defense against a measured failure rate. Cutting them shifts brittleness from a testable layer (`structural_gate`) to a layer that can't do the work (the semantic judge).

---

## 1. Reader (LOCKED 2026-05-18; broadened 2026-05-19)

A founder-CEO or VP of Strategy at a tech-savvy company that has commissioned competitive intelligence to inform an upcoming decision. The reader may be:

- **Reading reactively** after a competitive signal (customer-evaluating-competitor, lateral hire, regulator letter, partnership announcement) with leadership-meeting pressure to commit by next week
- **Reading proactively** before a planning meeting (quarterly off-site, board prep, annual strategy) where they will allocate next quarter's roadmap / budget / market focus
- **Reading on-demand** because someone asked "what's happening with X" and the answer affects a near-term call

They are smart, time-poor, and skeptical — they've been pitched enough strategic frameworks to recognize slot-fills. They have the authority to act on the brief: reroute a roadmap, re-price a tier, commit a budget envelope, call a customer or partner. They will quote one or two sentences from the brief if challenged later.

**Decision-making shape varies by vertical** (per `docs/research/2026-05-18-ci-vertical-conventions.md`):

- **Tech / AI-lab style** — solo founder or small exec team; fast unilateral decisions; founder reads the brief and acts within the week
- **Modern-agency style** — founder + 1–3 senior operators; fast decisions on positioning, distribution, hiring; commit by next sprint review
- **B2B SaaS style** — VP of Product / VP of Strategy + CEO; medium-cadence; commit by next planning cycle (4–13 weeks)
- **Professional-services style** — partner committee or executive committee; mediated consensus build; brief gets quoted into a partner-vote conversation 1–4 weeks out
- **Healthcare-practice style** — practice owner solo or with one medical director; local-market focus; decision tied to a specific upcoming patient-acquisition window or vendor-contract renewal
- **Regulated-finance style** — exec team + compliance / legal; slow-cadence regulatory-aware decisions; commit by next compliance review cycle (12–24 weeks)
- **DTC / e-commerce style** — founder + head of growth + head of brand; fast-cadence (2–6 weeks) channel + pricing + promo decisions

The brief still has to drive concrete action regardless of which decision-making shape the reader operates in — but the "commit by" timeline scales to the decision-shape-appropriate gate (next week for fast reactive, next quarter-end for evaluate-class decisions, next vendor-cycle for healthcare, next compliance-cycle for regulated finance, next sprint for DTC).

**Reading time budget is not load-bearing.** They read until they have what they need, then stop. Length guidelines route to `structural_gate`, not the judge.

**Default geography is US-primary.** The 2026 modern AI-native agency client base is dominantly US-headquartered, with operations across North America, EMEA, and APAC. Polish-market clients (Klinika, DWF Poland) are concrete first-cohort fixtures, not the architectural target. Spec must generalize from US-primary baseline; vertical-specific local-market behaviors (e.g., Polish aesthetic dermatology, German legal partnership conventions) are accommodated per `docs/research/2026-05-18-ci-vertical-conventions.md` but are not the design center.

Substitute readers the same brief should also serve, drawn from the gofreddy peer-set of 2026 modern AI-native agency clients:

- Head of Product at a B2B SaaS company (any scale) evaluating a roadmap pivot in response to a competitor signal
- Founder or CEO of an AI lab or dev-tools company evaluating a model-release positioning decision or a partnership go/no-go
- Founder or operator at a modern AI-native agency (Cody Schneider's Doola, Twain, brand-strategy AI tooling peer set) evaluating distribution play, agency-vs-agency positioning, or founder-content production decisions
- Corp Dev / strategy lead at a later-stage company evaluating an acquisition or market-entry decision
- Managing partner or executive committee chair at a B2B services firm (legal, accounting, consulting, financial advisory) evaluating lateral-flight defense or competitive moves
- Owner-operator at a small-to-mid local-market business (healthcare, hospitality, retail, professional services) evaluating market entry / pricing / referral patterns
- Head of Marketing or Strategy at a DTC e-commerce brand evaluating channel reallocation, promo response, or creator-partnership decisions
- Head of Strategy or compliance lead at a fintech or regulated-finance operator evaluating regulatory positioning, competitor-product threats, or partnership-distribution moves

The legal-services + AI-lab + healthcare reference set in this spec exists because those are gofreddy's current first-cohort fixture clients (DWF, Anthropic, Perplexity, Klinika). They are **not** the architectural target — they are concrete anchors. The spec is designed to generalize across the substitute-reader set above; first-cohort overfitting is an explicit risk to monitor (see §8).

NOT the reader: comms director (different decision shape — see monitoring lane); consulting partner reading for entertainment; researcher cataloging the market; investor doing diligence (different artifact — diligence memo, not brief).

**First-cohort posture.** Klinika + DWF are the only two onboarded clients as of 2026-05-19 (both Polish-language, both regulated-vertical). US-primary substitute readers above are the architectural target as the client base expands Q3-2026+. Polish-language fixture passes are required before any v3.6 spec lock against Klinika or DWF sessions; US-primary fixture passes are required for the architectural-target validation. The straddle is real and intentional during cohort expansion; revisit when cohort #5 onboards from an under-represented vertical.

---

## 1.5. Artifact shape — 5-COMPONENT MODULAR PACKAGE (LOCKED 2026-05-19)

**The lane produces a 5-component modular package**, per `docs/research/2026-05-19-competitive-comprehensive-scope.md` §5. Component A is the judge-scoped executive narrative brief (the v3.4 hybrid form factor, unchanged). Components B through F are wrap-around deliverables that the judge does not score and `structural_gate` validates deterministically. Optional Components G and H extend the package where engagement scoping calls for them. Locked because (a) shape-drift Goodhart is a documented failure mode in evolution loops (see §3b), and (b) the modular split is what lets the judge surface stay narrow while the deliverable surface grows — preserving v3.4 judge-stability work while unlocking comprehensive scope. The two design goals stop fighting.

**Why modular, not monolithic.** A single 60-page consulting-deck deliverable is the failure mode the agency is explicitly cutting (see §3, item 5). A single 800–2,000-word executive brief is the right forcing-function for the reader's commit-to-action decision, but it cannot carry the full surface of competitive intelligence a 2026 modern agency client expects (24 axes per research §1). The modular package keeps Component A as the forcing-function front-end and wraps it with depth components the reader can drill into when defending the action, evidencing the call to a board or partner, or commissioning follow-on intel.

**Substrate-readiness gate.** The 5-component modular package (Components A–F + optional G–H) describes the COMPREHENSIVE workflow target. Component A (brief.md) ships at substrate-current — `session_eval_competitive.py` reliably emits brief.md across all Phase-3 fixtures. Components B–F + optional G–H ship as substrate emission catches up: profile cards (B) when `competitors/<n>.json` deepens to per-competitor profile fields beyond shape-only; trajectory matrix (C) when `trajectory_matrix.md` workflow emission exists; comparison matrix (D) when `comparison_matrix.md` emission exists; watchlist (E) when MON-lane handoff schema is locked; evidence appendix (F) when `evidence_appendix.md` emission exists; optional G–H when scoped per-engagement. Until Components B–F substrate emits, the lane structural-gate-fails 100% of sessions if v3.6 ships against them. The comprehensive scope is the SPEC TARGET; client-side shipping is gated on substrate readiness, not spec maturity.

### Component A — Executive narrative brief (judge-scoped, v3.4 unchanged)

The judge-scoped artifact: 800–2,000 words, **Klue 5-section spine** (headline-as-claim → rationale → comparison → implications → recommendations), with **CB Insights triple** scaffolding in Implications (what-now / where-next / why-priority), and **war-game-flavored trade-off rigor** on the recommendation (explicit bet ↔ cost ↔ contingency pairing). This is the forcing function. The reader can read this alone and commit to action; the rest of the package backs the decision.

**Judge-scored against CI-1 through CI-6** (the v3.4 criteria, preserved verbatim in §4). Length, section presence, CB Insights triple presence, comparison structure, banned-phrase list, and SOV-negation-filter check route to `structural_gate` (§8); the judge tests outcome quality only.

### Component B — Per-competitor deep profile cards

For the 3–5 most consequential competitors named in Component A: a one-page card per competitor covering product, pricing, positioning, traction signals, funding, hiring, M&A, partnerships, AI-native attributes (model surface, AEO presence where relevant), distribution moats (LinkedIn / X / podcast / founder visibility), and the strategic narrative each competitor is driving. Klue-style profile-card format. Per-competitor depth grows with consequence: dominant threat gets the longest card; tier-3 competitors get the lightest touch.

**Size envelope:** 250–600 words per competitor card. 3–5 cards per package. Total 1–3 pages.

**Not judge-scored at criterion level.** `structural_gate` validates: (a) ≥3 profile cards present, (b) each card carries ≥10 named-and-dated facts, (c) each card carries ≥1 source URL per major claim, (d) each card cites at least one signal dated within 90 days, (e) AI-native attributes section present when the competitor is AI-adjacent (model surface named, AEO presence reported), (f) distribution-moat section present (LinkedIn / X / podcast / founder visibility quantified where data available).

### Component C — Trajectory matrix

A structured table: each tracked competitor × 6–18 month forward call × 2+ independent signals × confidence level (high / medium / low) × falsifiability marker (what would prove the call wrong by when). Single page, primarily evidence-organizing. The trajectory matrix is the depth substrate behind Component A's CI-2 claims — the brief names the dominant trajectory; the matrix shows the trajectories the brief did NOT make headline because of consequence ranking, plus the supporting signals.

**Size envelope:** 1 page. ~5–8 rows. Compact tabular layout.

**Not judge-scored.** `structural_gate` validates: (a) ≥3 rows present, (b) each forward call carries ≥2 named independent signals, (c) each row carries an "as of" date stamp, (d) each row carries a falsifiability marker (what observable event by when would prove the call wrong), (e) confidence levels are explicit (no implied confidence).

### Component D — Comparison matrix (dimension-by-dimension narrative)

Not a checkmark feature grid (cut per §3, item 3). A 10–20 dimension matrix where each cell carries one sentence of narrative claim with one supporting evidence pointer. Dimensions selected per vertical (per `docs/research/2026-05-18-ci-vertical-conventions.md` §4) but always include: product depth on critical features, pricing structure, target-segment overlap, channel mix, distribution moats, AEO presence, talent density, traction signals, public sentiment, defensible structural mechanism.

**Size envelope:** 1–2 pages. 10–20 dimensions × 3–5 competitors compared. Each cell ≤30 words.

**Not judge-scored.** `structural_gate` validates: (a) ≥3 competitors compared on ≥10 dimensions, (b) each cell carries one sentence + one evidence pointer, (c) no checkmark-only cells (every cell must carry a narrative claim with evidence), (d) dimensions selected match the vertical-conditional dimension set (per §4 vertical adjustments — selection routing lives in workflow substrate, not judge).

### Component E — Watchlist + MON-lane handoff

The named handoff to the gofreddy `monitoring` lane: which signals to track on which competitors, with named threshold conditions, escalation rules, and decision-shape triggers ("if X happens, reassess CI"). Mirrors `docs/research/2026-05-19-competitive-comprehensive-scope.md` §1.24. Makes the CI brief a *commission* of follow-on intel, not a one-shot. The reader doesn't have to re-commission; they've automated the next watch.

**Size envelope:** 1 page. ~5–10 watchlist items.

**Not judge-scored.** `structural_gate` validates: (a) ≥3 watchlist items present, (b) each carries a named signal (specific observable event or metric), (c) each carries a named threshold (what value or pattern triggers reassessment), (d) each carries a named action rule (what reassessment cadence or escalation fires), (e) MON-lane handoff schema conformance check (item structure matches `monitoring` lane's ingestion schema once defined — see §8 open question on MON-lane coordination).

### Component F — Evidence appendix

Source registry. Every claim made in Components A through D maps to a source row in F: source URL (or specific document identifier), retrieval date, claim ID, alternative interpretation engaged (or explicit "none — single source" marker). Defends against the 6 LLM-specific failure modes from `docs/research/2026-05-18-ci-ai-failure-modes.md`.

**Size envelope:** 2–4 pages. Variable with package depth.

**Not judge-scored.** `structural_gate` validates the full anti-hallucination check set from §8 (preserved from v3.4): URL HEAD resolution, "as of" date requirement, ≥1 cited source dated within 90 days per forward-looking claim, quote-grep against source corpus, entity-existence lookup, alternative-interpretation column populated for every top-3 strategic claim from Component A. Per the OpenRubrics design principle (Hard Rules → structural_gate, Principles → judge), deterministic verification belongs here because the judge cannot deterministically verify URL resolution, quote provenance, entity existence, or date freshness — those are factual checks, not semantic judgments. **Semantic evidence-chain integrity at the Component-A layer lives in CI-6** (§4 below).

### Optional Component G — AEO presence comparison

For agency clients in B2B SaaS, AI-tooling, modern-agency, DTC e-commerce verticals where AEO has become load-bearing. Detail table: 10–30 category-defining queries × 4–6 AI engines (ChatGPT, Perplexity, Claude search, Gemini, Brave Search, You.com) × per-competitor citation pattern, citation frequency, citation position, and brand-mention-without-link (phantom mention) tracking. From Profound / Athena AI / Otterly / Peec AI / Goodie AI runs.

**Size envelope:** 1–2 pages.

**Optional because** not all clients have AEO yet as a load-bearing surface in 2026; engagement scoping selects in or out at start. For B2B SaaS and AI-tooling, G is required by default. For legal-services / healthcare / regulated finance, G is optional through 2026 (AEO is still emergent in those verticals). For modern-agency clients, G is required when the engagement's CI scope includes the client's own AEO positioning. Default-required by 2026-Q4 across all verticals where AEO becomes load-bearing — see §8 open question on AEO timing.

**Not judge-scored.** `structural_gate` validates (when present): (a) ≥10 queries × ≥4 engines covered, (b) per-cell citation pattern explicit (citation, no-citation, phantom-mention), (c) primary AEO measurement source declared with one corroborating source (per §8 open question on AEO primary-source).

### Optional Component H — Win-loss analysis integration

For clients with existing win-loss data (Clozd / Klue program) or Gong / Chorus call recordings the agency can analyze. Structured extract: top-3 win patterns by competitor encounter; top-3 loss patterns by competitor encounter; named buyer-segment patterns; deal-cycle-stage encounter patterns. Integrates AI-extracted analysis (Gong + Claude/Opus pattern extraction — drops cost from $50K/quarter analyst-driven to ~$2K/quarter per `docs/research/2026-05-19-competitive-comprehensive-scope.md` §3.8).

**Size envelope:** 1–2 pages.

**Optional because** not all clients have win-loss data or call-recording infrastructure. When client has no win-loss program, the CI engagement may recommend scoping one as a follow-on engagement (workflow flag for "win-loss-data-absent" cases emits a follow-on-engagement recommendation in Component A — see §8 open question on win-loss scoping).

**Not judge-scored.** `structural_gate` validates (when present): (a) ≥3 win patterns + ≥3 loss patterns named, (b) each pattern carries a specific buyer-segment qualifier (not "we win on enterprise" but "we win on regulated-vertical enterprise with ≥3 stakeholders"), (c) each pattern carries an evidence pointer to underlying call recordings or CRM stages, (d) call-recording provenance metadata present (call ID, recording date, deal stage).

### Component scope summary

**Production-default deliverable: Components A + B + C + D + E + F.** Size envelope 8–15 pages total. Component A is 3–6 pages (the 800–2,000-word brief in print); B is 1–3 pages (one card per competitor); C and D each 1–2 pages; E is 1 page; F is ~2–4 pages typical. This is a 10–15 page modular package — **dramatically more comprehensive than a standalone executive brief, dramatically less bloated than a 60-page consulting deck**.

**Optional extensions: G (AEO) and H (win-loss)** added by engagement scoping. Full package with G + H: 12–19 pages.

### The architectural trick

**The judge sees Component A only. Components B–F + optional G/H route to `structural_gate`.** The judge (CI-1 through CI-6) is calibrated against the 800–2,000-word executive-brief form factor. The wrap-around components are validated by deterministic checks (presence, freshness, traceability, evidence-chain integrity). This preserves the v3.4 judge-stability work — the judge sees an artifact it has been calibrated against — while the lane delivers comprehensive scope.

**The deliverable surface area grows ~5x; the judge surface area stays constant.**

**Why one Component-A shape:** the v3.4 Reader spec (founder/VP archetype) and Success spec (commits to single concrete action) point unambiguously to executive-briefing form. CI-3 (structural mechanism) and CI-2 (trajectory with 2+ independent signals) presume teardown-grade evidence depth that pure Klue briefings don't carry — so the hybrid blends Klue's actionability skeleton with CB Insights' evidence depth and war-game-style trade-off framing. The depth that doesn't fit into 800–2,000 words moves to Components B–F.

**Out of scope shapes (the lane will NOT produce these):**

- 30-page strategic teardown as standalone (CB Insights / Stratechery deep dive) — depth lives in Components B + D + F instead
- 1-page sales battlecard (Klue / Crayon / Kompyte format) — wrong reader; battlecards serve account executives in deals, not founders/VPs in strategic-commit decisions
- Weekly monitoring digest (handled by `monitoring` lane via Component E handoff)
- Multi-scenario war-game memo (multi-branch contingency planning) — out of scope for React-cluster decisions; may sibling-fork for Evaluate-cluster

**Decision-class scope:** the modular package serves the **React cluster** decisions (retention threat / pricing response / roadmap pivot / outreach decision) per `docs/research/2026-05-18-ci-decision-format-mapping.md`. Evaluate-cluster (acquisition target / market entry) and Structure-cluster (partner / channel selection) decisions may need different shapes — those are deferred to future lane work; current spec scopes to React only.

**Shape enforcement lives in `structural_gate`, NOT in the judge criteria.** The judge tests outcomes (CI-1..CI-6 below); the workflow's `structural_gate` tests artifact-shape conformance for Component A (word count band, Klue 5-section presence, CB Insights triple presence, comparison structure, banned-phrase list, SOV-negation-filter) AND validates Components B–F per the per-component check sets above. Per design guide §11.1, this preserves the outcome-question-not-feature-check discipline at the judge layer while still defending against shape-drift.

**Empirical validation scope.** The 5-component modular package is research-grounded (per `docs/research/2026-05-19-competitive-comprehensive-scope.md`) against legal-services / AI-lab / healthcare / B2B-SaaS / modern-agency fixtures. When fixtures from new verticals appear (DTC e-commerce, regulated finance, hospitality, marketplaces), re-validate the package shape — some components may need vertical-specific template variants (e.g., regulated-finance briefs may need a compliance-context section in Component A; DTC briefs may need a unit-economics-by-cohort comparison in Component D instead of the standard comparison structure). The §1.5 lock is the React-cluster-default; lane scope may expand or sibling-fork as the client mix evolves (see §8 sibling-fork triggers).

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18; reframed 2026-05-19 for modular package)

After reading **Component A**, the reader commits to a single specific concrete action on the most-consequential development surfaced in the brief. The action may be:

- A competitive **posture** (attack / defend / flank / cooperate / ignore) on a named threat
- A **budget reallocation** (pause channel X, accelerate spend on Y)
- A **roadmap change** (ship counter-feature, kill in-flight initiative, redirect engineering capacity)
- An **outreach call** (reach the prospect-customer, call a partner, engage a regulator)
- A **hiring move** (accelerate a search, defer a hire, restructure a function)
- A **follow-up intel ask** (commission specific deeper research, watch a named signal, set up a monitoring trigger)

The reader knows what they're giving up — the action has an explicit cost the reader could explain to their CFO or board. They could explain the call to a peer in 90 seconds. **Sleep test:** if they slept on it overnight, they'd make the same call tomorrow — the brief's logic survives 24h reflection, not just momentum.

**Components B through F (and optional G/H) serve as evidence backing for the action.** The reader uses Component B to defend the call to a co-founder ("here's the full profile on the dominant threat"); Component C to defend the trajectory call to a board member ("here are all the forward calls we considered and why this one was the headline"); Component D to defend the comparison framing to a head of product ("here's how we score against all named competitors on 14 dimensions, not just the 3 in the brief"); Component E to operationalize the follow-on watch into the monitoring lane; Component F to defend the evidence chain to a skeptical investor or partner. Optional G defends the AEO call; optional H defends the win-loss narrative.

The brief may also surface a *secondary* follow-up intel ask (the next question the reader should commission). Primary success is still the concrete action on what's known now; the follow-up ask is a bonus, not a substitute.

World-class real-world exemplars — used as quality anchors, NOT as templates to copy:

**Cross-industry rigor (the ceiling):**
- **McKinsey / Bain war-game memos** — output is competitor *response pattern* prediction (what they'd do in 2–3 likely scenarios), not competitor position description. Works across SaaS / legal / healthcare / finance / DTC.
- **Bloomberg Intelligence / S&P sector briefs** — quantitative anchor, named comparable, falsifiable forward claim. Most rigorous of the reference set.
- **CB Insights Strategy Teardowns** — WHAT-NOW / WHERE-NEXT / WHY-PRIORITY triple structure; the CB Insights triple is the Component A Implications-section scaffolding.

**Practitioner-grade (the achievable floor):**
- **Klue executive-briefing template** — headline-as-claim, rationale, comparison, implications, recommendations. The Component A spine.
- **Crayon Spark + State of CI annual** — real-time signal injection (per §3 modern levers below) plus practitioner state-of-the-practice benchmarks.

**Modern founder-led CI thinkers (the 2026 lever set, reasoning toolkit not deliverable templates):**
- **Cody Schneider** on asymmetric distribution moats and replacement-competitor framing ("real competitor is the workaround")
- **April Dunford** positioning canvas + counter-positioning methodology (Component A CI-1 asymmetric-opportunity anchor)
- **Hamilton Helmer** 7 Powers as reasoning toolkit for CI-3 mechanism diagnosis (never named in deliverable — Phase-4 pathology surface)
- **Patrick Campbell (ProfitWell)** on 90-day pricing-sprint cadence (Component D pricing-dimension routing)
- **Rand Fishkin (Sparktoro)** for §3.10 audience-intersection (Component D channel-mix dimension)

What ties these together: point of view at the top, structural reasoning, trajectory not snapshot, one or two calls the reader could commit to before the next meeting, evidence chain that survives tracing, modular packaging so the executive read is short and the depth is appendix-grade.

---

## 3. Failure — mediocre, Goodhart-collapse, modern-lever cuts (LOCKED 2026-05-18; modern-lever bias added 2026-05-19)

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

**AI-specific failure surfaces** (per `docs/research/2026-05-18-ci-ai-failure-modes.md`):

- **Entity confabulation.** Workflow invents competitors that don't exist, fabricates press-release excerpts, conflates similarly-named entities ("Cursor" the IDE vs "Cursor" the cursor-tracker, "Anthropic" vs "Anthropic Communications"). Documented at 19.9% citation-fabrication rate for GPT-4o; 37% failure rate in Perplexity production retrospectives.
- **Source confabulation.** Cited URLs that 404, papers that don't exist, analyst reports never published, quotes attributed to plausible-sounding executives who never said them, "internal data" with no provenance. Per HalluLens / FAITH / CompoundDeception benchmarks.
- **Recency / training-cutoff distortion.** "Recent" announcements that are months/years old; competitive landscape shifts that happened post-training-cutoff missed entirely; 2024 strategic environment projected into 2026. Per LLMLagBench + "Is Your LLM Outdated?" NAACL 2025.

Every surface marker present, structurally compliant, strategically empty — and now structurally invalid via confabulated entities / sources / dates. The judge that rewards these gets the workflow that learns to produce them.

**Historical context.** This lane (or its siblings) has triggered three prior rollbacks for the same underlying Phase-4 pathology: `2ce99bb` (σ-widening prose, J1–J4), `ca4a256` (v2 contract-prose), `698e658` (Phase 4 feature-checking → `c76f051`). The criteria below are designed to resist re-creating any of them AND to surface the new AI-specific failure surface that those rollbacks didn't address.

**Deterministic AI-failure checks live in `structural_gate`** — URL HEAD resolution (catches dead cited links), quote-grep against source corpus (catches fabricated quotes from real URLs), entity-existence lookup (catches invented competitor entities), "as of" date requirement (forces freshness signaling), ≥1 cited source dated within 90 days (defends against recency-cutoff distortion). Per the OpenRubrics design principle (Hard Rules → structural_gate, Principles → judge), deterministic verification belongs in `structural_gate` because the judge cannot deterministically verify URL resolution, quote provenance, entity existence, or date freshness — those are factual checks, not semantic judgments. **Semantic evidence-chain integrity at the Component-A layer lives in CI-6** below.

### 3c. Modern-lever cuts — what the 2026 deliverable does NOT do (added 2026-05-19)

The agency has explicit license to **kill** the following deliverable shapes (per `docs/research/2026-05-19-competitive-comprehensive-scope.md` §2). Each appears in legacy McKinsey / Bain / Deloitte / Big-4 CI work and in legacy in-house CI shops. None serve a 2026 modern client. These are *deliverable-level* cuts: even when these failure shapes pass the judge's CI-1..CI-6, the workflow's `structural_gate` should kill them.

1. **Generic SWOT.** 4 quadrants of plausible-sounding boilerplate. Private reasoning aid only; never in deliverable.
2. **Porter Five Forces fill-in.** Reasoning toolkit, never deliverable shape.
3. **Surface-level feature comparison matrix (checkmark grid).** Features are easily copied (operational effectiveness, not strategic positioning); the grid format defeats the analytical work. Replace with dimension-by-dimension narrative cells (Component D format).
4. **"They're a leader / we're a challenger" Gartner-quadrant theater.** Quadrant placement is a paid marketing artifact, not a strategic signal.
5. **60-page BCG/McKinsey deck shapes that don't earn their pages.** Read by no one. Klue's explicit anti-pattern. The modular package (8–15 pages total) is the deliberate alternative.
6. **Recency-distorted single-signal trajectory.** "They raised $X so they're going up-market." CI-2 catches at judge layer; Component C trajectory-matrix structural_gate (≥2 independent signals per row) catches at deliverable layer.
7. **Framework-name slot-fill.** "Counter-positioning play." "Process power." "Network economies." Framework asserted without mechanism. The Phase-4 pathology from `c76f051`.
8. **Single-hypothesis confirmation bias.** Briefs reinforcing existing prior with no disconfirming evidence. Cut: every Component-A brief engages ≥1 alternative interpretation; Component F evidence appendix requires alternative-interpretation column for top-3 claims.
9. **Benchmark-table-as-strategy (AI-lab).** MMLU / HumanEval / GSM8K aggregate scores. Saturated above 88% in 2026; differences statistically meaningless. Replace with independent evaluation citations (Epoch ECI, Artificial Analysis, LMSYS) plus 2+ signal trajectory.
10. **Self-reported-score-trust (AI-lab).** Kimi K2 reported 50% on HLE; independent retesting 29.4%. Always cite independent corroboration in Component F.
11. **Directory-rank theater (legal).** Chambers tier without underlying matter-mix / partner / client-feedback driver. The tier is output, not strategy.
12. **National-market-size citation as opener (healthcare).** "$23B → $42B market" is irrelevant to a practice owner deciding pricing match. Market-size data moves to Component F evidence appendix only.
13. **Treatment-mix-as-feature-comparison (healthcare).** "Botox vs Daxxify" pricing without JTBD framing ("I want to look less tired"). JTBD required in Component A.
14. **Vague action prose** ("strengthen positioning," "double down on," "explore the segment"). CI-1 catches; recommendation must name action type AND specific target.
15. **Consulting-slop blocklist** (preserved verbatim from live code `CI_BANNED_PHRASES`, 12 phrases JR-iterated for CI specifically — see §8).
16. **AI-slop tells** layered on top: em-dash density, "let me explain why," "moreover," "furthermore," "in conclusion." Per `2026-05-18-ci-ai-failure-modes.md` §3. Blocked by `structural_gate`.
17. **Confident-tone synthesis without traceable evidence chain.** CI-6 catches at judge layer; Component F evidence-appendix structural_gate (URL HEAD resolution + quote-grep + entity-existence lookup) catches at deliverable layer.
18. **Length without point of view.** Descriptive teardown not committing to a thesis. Cut: every Component A section ends on a claim or implication, not description; Component B profile cards end on a strategic-narrative claim, not a fact dump.

### 3d. Modern levers the 2026 deliverable explicitly ADDS (added 2026-05-19)

Axes that distinguish a 2026 modern AI-native agency from a legacy CI shop. Some are 2026-original; some are pre-AI levers consistently under-weighted by legacy CI. These are *deliverable-surface additions* — they expand what the modular package covers, particularly in Components B / D / E / G. They do not modify the judge layer's criterion prose; instead they appear as scored content within Component A's CI-1..CI-6 anchors when the engagement scope makes them load-bearing.

The 15 modern levers (per `docs/research/2026-05-19-competitive-comprehensive-scope.md` §3):

1. **AI-native competitor anatomy.** Model surface, latency, cost-per-token, agent depth (single-call → multi-call → agentic tool-use → multi-agent), evaluation methodology, safety/compliance positioning, on-prem option for regulated finance / legal. Component B section for AI-adjacent competitors.
2. **AEO presence comparison.** §1.19 from comprehensive scope research. Component G (optional, increasingly required).
3. **Founder-visibility comparison.** Per founder per surface: LinkedIn / X / podcast / conference / newsletter / book / media. Component B distribution-moat section.
4. **Distribution-moat comparison.** §1.16. The single highest-value CI artifact for many modern-agency clients. Component D dimension.
5. **Talent-flow inference.** Pirical / Leopard Solutions for legal; Levels.fyi / Paraform for AI; manual LinkedIn elsewhere. Predicts product roadmap at 6–9 month lag. Component B hiring section + Component C trajectory signals.
6. **90-day pricing-sprint cadence (SaaS).** Annual pricing review is legacy. Elite SaaS on 90-day sprints (OpenView, SaaS Factor 2025 Playbook). Component D pricing dimension + Component E watchlist.
7. **Comparison-page warfare.** Their "vs"-pages and "alternative-to"-pages. Primary SEO+AEO substrate for bottom-funnel buyer queries. Component A recommendation surface + Component G AEO presence detail.
8. **AI-call-recording win-loss integration.** Gong / Chorus + Claude/Opus extraction drops win-loss cost from $50K/quarter to ~$2K/quarter. Optional Component H.
9. **Visualping + Wayback + change-detection forensics.** Continuous change-detection on pricing pages, "vs"-pages, customer-list pages, hero headlines, careers pages. Component E watchlist triggers.
10. **Sparktoro audience-intersection.** Where client and competitor audiences overlap vs diverge. Component D channel-mix dimension.
11. **Founder X-thread strategic positioning reads.** For AI labs and modern SaaS. Modern CI cites founder posts as primary evidence in Component F.
12. **Asymmetric-opportunity gap maps.** §1.20 from comprehensive scope research. Component A CI-1 asymmetric-opportunity test (preserved from v3.4); Component D distribution + mechanism + talent-flow intersection.
13. **Counter-positioning per Dunford methodology.** §1.23 from comprehensive scope research. Reasoning toolkit for CI-3 mechanism diagnosis (never named in Component A); explicit counter-positioning recommendations in Component A recommendations.
14. **Crayon-style real-time signal injection.** Brief carries "as of [date]" stamp; last-14-days signals are flagged in Component E; last-48-hours signals route to recommendation directly.
15. **Structured win-loss program handoff.** When client has no win-loss program, CI engagement may recommend scoping one as follow-on. Component A follow-on-intel-ask + optional Component H integration when data exists.

**Where these levers land in the criteria.** None of these levers modify CI-1..CI-6 prose. They show up as **score-1-anchor content** when the engagement scope makes them load-bearing — e.g., a Component-A recommendation that names a comparison-page-warfare action (lever 7) satisfies CI-1 (concrete action with specific target) regardless of whether the underlying lever is the Helmer-mechanism or a Dunford-counter-positioning move. The criterion tests the outcome (concrete action with named target); the lever is one of many concrete substrates the recommendation can rest on.

---

## 4. Criteria — outcome questions (6) — PRESERVED VERBATIM FROM v3.4

**The judge layer is unchanged from v3.4.** All six criteria, all score anchors, all CoT prose, all examples, all "do not score" lists are preserved verbatim. The modular-package expansion in §1.5 does not modify the judge's surface. The judge scopes Component A only.

### CI-1 — Forces a concrete action commitment

**Outcome question (binary):**
After reading, would the reader commit to a single specific concrete action — a competitive posture, budget reallocation, roadmap change, outreach call, hiring move, or follow-up intel ask — on the most consequential development surfaced by the brief? Could they walk into their next leadership meeting and assign this action by the next decision-shape-appropriate gate?

**Score 1 (yes)** — Brief makes the single most-consequential call so concretely that disagreeing requires a counter-argument, not a shrug. The recommended action names BOTH a specific action type AND a specific target: posture toward a named competitor, budget shift in a named category, roadmap change to a named initiative, outreach to a named person, hiring move for a named role, or intel ask on a named question. The reader could commit by the next decision-shape-appropriate gate (next week for reactive, next quarter-end for evaluate-class, next vendor-cycle for healthcare-style, next sprint for DTC, next compliance-cycle for regulated finance).

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

Example D — rejection-of-advantage path (do not optimize toward this): "The competing AI lab's apparent first-mover advantage on agentic tool use is replicable operational effectiveness, not sustainable positioning. They had ~6 months of head start on the multi-step tool-use surface; OpenAI matched the capability in their March release with the new Responses API; Google followed in April with Gemini's agent runtime. The advantage was execution timing, not a structural mechanism — no curated training-data moat, no proprietary RLHF corpus on tool use, no compute or distribution lock-in we can't reach. Treat as a non-durable lead, not a defensible moat; reallocate the planned counter-positioning spend to the agentic-evaluation surface where the structural-mechanism case is still open."

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

**Score 1 (yes)** — At least one finding pushes against a prior the brief EXPLICITLY NAMES as belonging to the reader's organization — e.g., "leadership currently believes X," "our prior assumption was Y," "we have been hedging on Z," "the company narrative is W." The finding contradicts that explicitly-stated prior with supporting evidence. The prior cannot be imagined or inferred by the judge — it must be on the page. The finding earns its weight with evidence, not provocation.

Example (do not optimize toward this): "Our 'enterprise readiness' is the prior most likely to be wrong. The Pinsent move signals the senior-RES tier — our claimed strength — is the actual lateral-flight risk, not the junior tier we've been hedging on." (Note: the brief names "enterprise readiness" as the prior AND "the junior tier we've been hedging on" as the related assumption being contradicted; the prior is on the page.)

**Score 0 (no)** — All findings confirm the reader's existing narrative. No disconfirming evidence engaged. OR the brief makes no finding that contradicts the company's evident strategic posture (i.e., it is not surfacing an uncomfortable truth at all) — CI-4 does not apply and scores 0, not 0.5. The 0-vs-0.5 distinction matters: a brief that simply isn't doing the uncomfortable-truth work scores 0 (criterion not satisfied), preserving the criterion's discriminative range; the 0.5 anchor is reserved for the case where the brief IS doing the work but with thin evidence (see below).

**Score 0.5 (unknown)** — The brief surfaces a finding that contradicts an inferable prior of the reader's organization, but does not quote or paraphrase the prior explicitly — so the uncomfortable-truth work is happening on the page but the prior is implicit rather than named. Emit 0.5 + "unknown" + one sentence on what prior the brief appears to be contradicting AND what evidence in the finding is too thin to defend in a leadership meeting.

**Required CoT:**
- Step 1: Identify priors the brief EXPLICITLY STATES it is challenging (e.g., "leadership currently believes X" / "our prior assumption was Y" / "we have been hedging on Z" / "the company narrative is W"). If the brief does not name a prior AND makes no finding that contradicts the company's evident strategic posture (no uncomfortable-truth work is being attempted), score 0 (criterion does not apply — not 0.5). If the brief surfaces a finding contradicting an inferable prior but does not quote or paraphrase the prior explicitly, emit 0.5 + "unknown" + one sentence on the implicit prior + what evidence is thin. Do not impute priors the brief leaves implicit at score 1; score 1 requires the prior on the page.
- Step 2: For each brief-stated prior identified in Step 1, find the finding in the brief that contradicts it. Verify the finding carries supporting evidence (named signal, dated event, cited source) sufficient to defend in a leadership meeting.
- Step 3: Emit verdict + one-sentence justification. The justification must quote or paraphrase the brief's own statement of the prior; if no quoted/paraphrased prior is available, the score is not 1.

Do not score: confrontational tone, presence of "uncomfortable truths" section header, number of priors challenged. Do not impute priors the brief does not state.

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

### CI-6 — Evidence chain survives tracing (≤5-ceiling documented exception)

**Outcome question (binary):**
For each major strategic claim in the brief, does the evidence chain survive tracing — i.e., are the underlying signals named, the cited sources verifiable, and disconfirming alternatives engaged? Or does the brief collapse into plausible-tone synthesis where confident-sounding strategic claims rest on no traceable chain?

**Score 1 (yes)** — At least the top-3 strategic claims in the brief (the headline, the dominant-threat trajectory call, the structural-mechanism diagnosis) each (a) name the specific signals they rest on, (b) cite verifiable sources (named entity / dated event / specific document / quoted attribution), AND (c) acknowledge at least one alternative interpretation the evidence does NOT rule out. Confidence is calibrated to evidence depth — strong claims have multi-source backing; tentative claims are flagged as tentative. When data sources failed or returned partial coverage, the brief recalibrates rather than speculates: it names what is missing, what analysis became impossible, and how the remaining data changes what can be concluded — **the gap itself is treated as an intelligence finding**, not silently omitted or papered over with inferred data presented at unearned confidence.

Example (do not optimize toward this): "Pinsent's senior-RES expansion (per their Sept 23 partner-promotion announcement + Chambers Tier-2 → Tier-1 RES shift in 2026 + 3 lateral RES partner moves in Q3 per ALM lateral tracker) suggests they're rebuilding RES practice depth. Alternative reading: this is a 1-year build, not a 3-year strategic shift — we can't yet distinguish from one round of opportunistic hiring. Confidence: medium, will firm up if Q1 2027 promotions also skew RES."

**Score 0 (no)** — Claims are confident-toned but evidence chain breaks under inspection: unnamed signals, fabricated sources, single-source extrapolation presented as multi-signal, no disconfirming alternative engaged. OR brief contains entity confabulations (competitors that don't exist, fabricated quotes, conflated similarly-named entities), source confabulations (404 URLs, unverifiable cited reports), or recency-cutoff distortions (months-old "recent" announcements, training-cutoff landscape projected into present).

**Score 0.5 (unknown)** — Evidence chain partially traces, but one of the top-3 claims has insufficient supporting detail in the brief itself to evaluate verifiability. Emit 0.5 + "unknown" + one sentence on which claim's evidence chain is unclear.

**Required CoT:**
- Step 1: Identify the top 3 strategic claims in the brief (headline + dominant-threat trajectory + structural-mechanism diagnosis).
- Step 2: For each, walk the evidence chain: are signals named? Are sources verifiable (named-entity / dated-event / specific-document / quoted-attribution)? Is at least one disconfirming alternative acknowledged?
- Step 3: Flag any INTERNALLY-INCONSISTENT claims within the brief itself: date contradictions (one section says "last quarter," another says "3 months ago" for the same event), named-entity mismatches within the brief (one section says "Pinsent Masons," another says "Pinsents"; one section says "Anthropic," another says "Anthropic Communications" for the same referent), or self-contradicting trajectory claims (e.g., one section says "moving up-market," another says "doubling down on the developer-API base" without reconciliation). Entity/source/recency confabulation against external reality (does the cited URL resolve? does the named competitor exist? is the dated event within 90 days?) is verified by `structural_gate` (§8 anti-hallucination checks), NOT this criterion — the judge does not have source-corpus access and cannot perform those checks reliably.
- Step 4: Emit verdict + one-sentence justification.

Do not score: citation count or footnote density (those route to structural_gate at Component A AND Component F), presence of "Sources" or "Evidence" section header, comprehensiveness of citation lists.

**Note on the ≤5 ceiling:** CI-6 is a justified breach of design guide §5's ≤5 criterion ceiling, documented in design guide §5 as the first formal exception. Rationale documented in §7 below. The redundancy check (§8) will tell us empirically if CI-6 correlates with another criterion >0.7; if so, the redundant criterion gets dropped to restore 5.

---

## 5. Shared judge-prompt wrapper

```
You are scoring a competitive-intelligence brief written for a
tech-savvy founder/CEO or VP of Strategy. The reader may be at
a US-headquartered tech company (B2B SaaS, AI lab, modern
AI-native agency), a professional-services firm (legal,
accounting, consulting), a healthcare practice, a regulated-
finance operator, or a DTC e-commerce brand. Their decision-
making shape varies (solo founder fast / partner committee
mediated / practice owner local-market / VP-product medium-
cadence / compliance-aware slow-cadence / DTC sprint-cadence)
but the brief still has to drive concrete action by the next
decision-shape-appropriate gate.

The brief is Component A of a 5-component modular package:
800–2,000 words, Klue 5-section spine (headline-as-claim /
rationale / comparison / implications / recommendations), with
CB Insights triple scaffolding (what-now / where-next /
why-priority) in the Implications section. Components B–F
(per-competitor profile cards, trajectory matrix, comparison
matrix, watchlist + MON handoff, evidence appendix) and
optional Components G (AEO presence) and H (win-loss) wrap
Component A as evidence backing for the reader's commit-to-
action decision. You see Component A only — the wrap-around
components are validated by the workflow's structural_gate,
not by you.

Score each criterion independently with 0, 0.5, or 1 plus a
one-sentence rationale that follows the per-criterion CoT
steps. Do not blend criteria. Do not infer criteria not stated.
If a criterion's condition is ambiguous from the brief alone,
emit 0.5 + "unknown" + one sentence on what would have to be
present to commit to 1.

If the brief references content that "lives in" or is "covered
by" Component B / C / D / E / F / G / H, do not score positively
on the basis of those references — those components are
validated by structural_gate elsewhere, not by you. Score
Component A on what it carries itself.

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

### 6a. Per-criterion Goodhart modes (Component A — judge layer; preserved from v3.4)

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **CI-1**: "Action templated by rotating through posture/budget/roadmap/outreach/hiring/intel-ask" doesn't pass — must name a specific target (named competitor / category / initiative / person / role / question) at the decision-shape-appropriate gate.
- **CI-2**: "Trajectory header populated by 1 signal restated 3 ways" doesn't pass — 2+ INDEPENDENT signals required.
- **CI-3**: "Helmer-power name-drop" doesn't pass — must include the structural reason a competitor can't or won't replicate.
- **CI-4**: "ACH-style alternative-hypothesis section with 2 strawmen + favored" doesn't pass — must push against the reader's actual organizational prior, not a manufactured strawman.
- **CI-5**: "Generic 'deprioritize other initiatives'" doesn't pass — CFO-recognizable cost required (named budget line, paused initiative, deferred segment).
- **CI-6**: "Confident strategic synthesis without underlying source chain" doesn't pass — top-3 claims must have named signals + verifiable sources + acknowledged alternative interpretation. Date contradictions within the brief, named-entity mismatches within the brief, and self-contradicting trajectory claims within the brief each force a score 0 (internal inconsistency is what the judge can verify against the artifact in front of it). External entity/source/recency confabulation is verified by `structural_gate` (§3b URL HEAD-check + quote-grep + entity-existence Wikidata lookup); CI-6 scores against internal consistency only — the judge does not have source-corpus access and cannot reliably verify external reality.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0.

### 6b. Per-component Goodhart modes (Components B–F + optional G/H — structural_gate layer; added 2026-05-19)

The modular-package expansion introduces a **parallel Goodhart risk at the deliverable layer**: under 50-generation selection pressure, the workflow can learn to slot-fill the per-component `structural_gate` checks without producing actual evidence quality. Each per-component check below is designed to resist a specific predictable slot-fill mode.

- **Component B (profile cards) — template-rigidity Goodhart.** Risk: workflow generates 3 profile cards with the right section headers (product / pricing / hiring / etc.) and ≥10 facts each, but the facts are surface-snapshot rather than strategic. Mitigation: `structural_gate` requires each card to end on a strategic-narrative-claim sentence (not a fact dump); cards lacking a strategic-narrative-claim closing fail the check even if all fact-count requirements pass. The closing sentence ties the card to Component A's strategic frame — what makes this competitor consequential for the reader's decision.

- **Component C (trajectory matrix) — single-signal-restated Goodhart.** Risk: workflow generates ≥3 rows where each "2+ independent signals" column lists 2 signals that are actually one underlying signal restated. Mitigation: `structural_gate` requires each row's signals to be tagged with distinct signal-class identifiers from a fixed enumeration (M&A / hiring / product / earnings / partnership / regulatory / lateral-hire / model-card / location / vendor). Two signals from the same class count as one for the check.

- **Component D (comparison matrix) — checkmark-grid-collapse Goodhart.** Risk: workflow generates dimension-by-dimension matrix but every cell collapses to a checkmark or rating ("strong" / "medium" / "weak") rather than a one-sentence narrative claim with evidence pointer. Mitigation: `structural_gate` validates that every non-empty cell contains a sentence with subject-verb structure AND an evidence pointer (URL or document identifier). Cells with only ratings, checkmarks, or labels fail the check.

- **Component E (watchlist) — vague-trigger Goodhart.** Risk: workflow generates ≥3 watchlist items where named-threshold and named-action-rule are vague enough to be unfalsifiable ("watch for major changes in pricing" with action "reassess"). Mitigation: `structural_gate` validates each item carries (a) named signal from a fixed enumeration, (b) named threshold expressed as a specific quantitative or categorical condition (number, date, named event), (c) named action rule expressed as a specific reassessment cadence or escalation step. Vague qualifiers fail the check.

- **Component F (evidence appendix) — citation-count-without-coverage Goodhart.** Risk: workflow generates ≥N source rows that satisfy URL HEAD resolution but cover only a subset of Component A's claims; claims-without-source proliferate. Mitigation: `structural_gate` validates that every top-3 strategic claim from Component A (identified by claim ID from the CI-6 CoT walk) has at least one source row in F, every forward-looking claim has at least one source dated within 90 days, every quoted attribution has a corresponding quote-grep match. Coverage is the check, not citation count alone.

- **Component G (AEO presence — optional) — single-engine Goodhart.** Risk: workflow generates AEO comparison citing one engine (Profound only, or Athena only) and presents it as a comprehensive picture. Mitigation: `structural_gate` validates ≥4 engines covered, with at least one corroborating-source declaration for the primary source.

- **Component H (win-loss — optional) — segment-generic Goodhart.** Risk: workflow generates "we win on enterprise / we lose on SMB" without specific buyer-segment qualifiers. Mitigation: `structural_gate` validates each pattern carries a specific buyer-segment qualifier (regulated-vertical / stakeholder-count / deal-size band / etc.).

**Per-component variance instrumentation** (per design guide §11.5): per `docs/research/2026-05-19-competitive-comprehensive-scope.md` §6.3, extend the existing variance-per-criterion-per-generation instrumentation to **variance per `structural_gate` check per generation**. If "comparison-matrix evidence-pointer present" passes 100% generations 1–5 then drops to 60% in generation 6, that's a Goodhart-warning — the loop is finding ways to game the check. Watch the variance curves alongside the judge-criterion curves.

---

## 7. Verification — does v3.5 conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓ (unchanged from v3.4)
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (3 vertical examples per criterion where applicable: legal / AI-lab / healthcare / fintech / B2B SaaS) ✓ (unchanged from v3.4)
- §5 criterion count: **6 (documented exception to ≤5 ceiling)** — see note below; unchanged from v3.4
- §5 isolation: per-criterion rationale, no blending ✓ (unchanged from v3.4)
- §6 structured per-criterion CoT (3–4 steps each) ✓ (unchanged from v3.4)
- §7 reference-free: examples hedged with "do not optimize toward this" ✓ (unchanged from v3.4)
- §11 Goodhart-resistance verification ✓ (extended in §6b with per-component Goodhart modes; judge-layer §6a unchanged from v3.4)
- §13 specimen criterion template followed ✓ (unchanged from v3.4)
- §1.2 Hard Rules → `structural_gate` / Principles → judge: ✓ **strengthened in v3.5.** The modular-package expansion deepens the split: the judge sees Component A only and tests outcome quality; Components B–F + optional G/H are validated by `structural_gate` deterministic checks. This is the OpenRubrics "Hard Rules vs Principles" formalization applied at the deliverable-package layer, not just the artifact-conformance layer.

**Note on the ceiling exception:** CI-6 (Evidence chain survives tracing) is a 6th criterion justified by the AI-specific failure surface documented in `docs/research/2026-05-18-ci-ai-failure-modes.md` — entity confabulation (19.9% GPT-4o citation-fab rate), source confabulation (Perplexity 37% failure shape), and recency-cutoff distortion. Subject to the same redundancy check as the rest: **the live count is probably 5 after the check runs** — CI-6 most likely absorbs into CI-2 (trajectory backed by 2+ signals) since both test for traceable evidence chains. Don't fight the absorption when it happens.

Length per criterion ≈ 200 words (longer than the design guide's 150-word target due to 3 vertical examples per criterion; absorbable). Total spec body ≈ 9000 words including §1.5 5-component expansion, §3c modern-lever cuts, §3d modern-lever adds, §6b per-component Goodhart-resistance. Net length increase from v3.4 driven by deliverable-surface expansion, not judge-surface expansion.

---

## 8. Open questions + sibling-fork triggers

### 8a. Pre-existing open questions (preserved from v3.4)

**v3.4 surgical restoration note.** Cross-check against live code `ce386b8` (the 14 judge rewrites baseline) recovered six load-bearing prose items that did not survive v0→v3.3: live CI-4 "capacity-to-act" good-vs-better example pair (folded into CI-1 as the capacity-sized recommendation note); live CI-5 asymmetric-opportunity framing (folded into CI-1 as the asymmetric-opportunity test); live CI-7 prioritization discipline ("not everything is Priority 1," 2–3 actions drive disproportionate impact — folded into CI-1 as the prioritization discipline note); live CI-8 "gap itself is treated as an intelligence finding" reframe (folded into CI-6 score-1 prose); the 12-phrase `CI_BANNED_PHRASES` consulting-slop blocklist (restored verbatim to §8 structural_gate, with AI-slop tells now layered on top rather than substituted in); SOV-negation-filter check (restored verbatim to §8). v3.3 architecture (6 criteria, decision-shape-aware reader, AND-conjunction-style anchors, structural_gate 9-check list, §3b AI-failure surfaces) unchanged in v3.4. v3.5 preserves all of v3.4 verbatim at the judge layer and expands at the deliverable layer only.

Reader / Component A artifact-shape / Success / Failure / 6 Criteria are LOCKED at v3.4. Modular package / Components B–F / optional G/H are LOCKED at v3.5. Remaining:

1. **Redundancy check pending (urgent).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 6 criteria × 3 panel models = ~90 calls (~$35). Drop any criterion correlating >0.7 with another. Expected live floor 3–5 (CI-6 may absorb into CI-2 if evidence-chain ends up correlating tightly with trajectory-source-traceability). Most-likely-to-merge pairs: CI-2 (trajectory) ↔ CI-6 (evidence chain); CI-3 (mechanism) ↔ CI-5 (trade-off).

2. **Fixture validation.** Run 5 existing CI fixtures (current Phase-3 Anthropic / DWF / Perplexity outputs + at least 1 Klinika-class healthcare fixture if available) through the locked criteria; eyeball judge rationales. If the rationales don't match human reasoning about quality, the prose is wrong, not the design. Surface findings before propagating.

3. **`structural_gate` expansion for Component A (preserved from v3.4):** add 5 anti-hallucination checks + 4 shape-conformance checks. The existing v006 checks (3+ headings, 2+ citations, ≤2000 words, banned-phrases) stay.

   **Anti-hallucination checks** (each defends a documented LLM failure rate — preserved verbatim from v3.4):
   - URL HEAD resolution — catches dead cited links
   - "as of" date requirement — forces freshness signaling
   - ≥1 cited source dated within 90 days — defends against recency-cutoff distortion (per LLMLagBench)
   - quote-grep against source corpus — catches fabricated quotes from real URLs (subset of Perplexity 37% failure)
   - entity-existence lookup (RapidAPI / OpenCorporates) — catches invented competitor entities (subset of 19.9% GPT-4o citation-fab rate); most operationally expensive of the set — can be implemented last, but skipping leaves a specific failure surface open

   **Shape-conformance checks** (enforce Component A §1.5 LOCKED — preserved verbatim from v3.4):
   - Word-count band (800–2,000)
   - Klue 5-section presence check (headline / rationale / comparison / implications / recommendations)
   - CB Insights triple presence in Implications (what-now / where-next / why-priority)
   - Comparison-structure check (at least one comparison element vs named competitor)
   - **SOV-negation-filtered check** (preserved from live code, run #2 bug fix): if the brief mentions "share of voice / share of observed / SOV," require at least one such sentence to also contain a numeric percentage AND not be negation-phrased ("would be misleading," "would be," "not a"). Prevents passing on phrasing like "A 0% SOV label would be misleading."

   **Banned-phrase list — consulting-slop blocklist** (preserved verbatim from live code `CI_BANNED_PHRASES`, 12 phrases JR-iterated for CI specifically):
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

4. **`structural_gate` expansion for Components B–F + optional G/H (added 2026-05-19):** new per-component check sets per §1.5 component definitions. Implementation order: A's anti-hallucination + shape-conformance set first (already partially live in v006); F's URL HEAD + quote-grep + entity-existence + alternative-interpretation column second (depends on retrieval substrate); B's profile-card checks third; C's trajectory-row checks fourth; D's dimension-cell checks fifth; E's watchlist-item checks sixth; G's AEO-coverage check seventh (only when G is engagement-scoped in); H's win-loss-pattern check eighth (only when H is engagement-scoped in). Component F is the most operationally expensive (URL HEAD resolution across full claim-set; entity-existence lookup for all named competitors) and may need a tiered implementation (fast checks first, expensive checks gated on suspect-only). Cost-instrument on 1 fixture before propagating; budget envelope: per `docs/research/2026-05-19-competitive-comprehensive-scope.md` §8.10, watch for per-fixture cost exceeding $15–25; if so, trim F's expensive checks first.

5. **Vertical fixture coverage.** Currently have legal (DWF) + AI-lab (Anthropic, Perplexity) + healthcare (Klinika) coverage in fixtures. Build 2–3 fixtures in each of: B2B SaaS, modern AI-native agency, DTC e-commerce, regulated finance — before locking the criteria via empirical redundancy check. Each new vertical fixture also tests whether the modular-package per-component template generalizes or needs a vertical-specific variant (per §1.5 empirical-validation-scope note).

6. **Evaluate / Structure cluster decisions: deferred.** Current v3.5 spec is React-cluster only. When Evaluate-class fixtures appear (acquisition target, market entry), revisit `decision_shape` workflow input and possibly sibling-lane treatment per `docs/research/2026-05-18-ci-decision-format-mapping.md` §3-4. Modular-package architecture is hypothesis-compatible with Evaluate cluster (Components B–F serve diligence depth well), but Component A's forcing-function form factor (Klue 5-section spine + CB Insights triple + war-game trade-off) is React-specific and would need a parallel Evaluate-cluster Component-A variant.

7. **Propagation to other 7 lanes.** Once CI v3.5 validates on real fixtures, propagate the iterated pattern: GEO → MON → MA → SB → X → LI → site_engine. Each lane gets its own Path-A iteration + (optionally) lane-customized deep-research pattern — NOT a mechanical 4-question repeat. The CI deep-research questions weren't equally relevant to all lanes; per-lane question scoping needed. The modular-package architecture per §1.5 also propagates conceptually — each lane should evaluate whether a wrap-around deliverable-component set adds value beyond its primary judge-scoped artifact.

8. **First-cohort overfitting watch.** v3.3 broadened Reader / Example C / §1.5 to reduce DWF/Klinika-only anchoring; v3.5 further broadens substitute-readers and adds US-primary default + 5 verticals' decision-shapes (Modern-agency, DTC, regulated-finance) explicitly. Monitor: when client #5+ onboards (DTC e-commerce, fintech, hospitality, regulated finance, marketplaces), check whether the spec's substitute-readers + §1.5 modular package + criteria anchors generalize OR whether per-vertical adjustment is needed. Re-validation trigger: any fixture from a vertical not in {legal-services, AI-lab, healthcare, B2B-SaaS, modern-agency} should prompt a quick re-validation pass on the affected criteria AND on the affected components' `structural_gate` check sets.

### 8b. Sibling-fork triggers (added 2026-05-19)

The modular-package architecture deliberately keeps Components B–F + optional G/H **in the `competitive` lane for v1**. Sibling-forking is premature until the lane is judge-stable on Component A. Triggers below specify when forking is warranted:

**Trigger 1 — Component B → `competitor_profile` sibling lane.** When per-component variance instrumentation (§6b) shows Component B's structural_gate-check variance is high and **decoupled** from Component A's CI-1..CI-6 variance over ≥10 stable generations, fork Component B to a `competitor_profile` sibling lane. Indicates the profile-card surface is mutation-active independent of the brief's strategic-claim surface — i.e., the lane is doing two different things and a sibling-fork lets each evolve on its own loop. Until then, hold the component in `competitive` lane.

**Trigger 2 — Component G → `aeo_competitive` sibling lane.** When AEO presence comparison becomes load-bearing across ≥3 cohort verticals (e.g., B2B SaaS + AI-tooling + modern-agency all routinely engagement-scope G in), demand for G grows beyond what the `competitive` lane can carry as an optional component. Fork to `aeo_competitive` sibling lane with its own optimal-output spec, judge layer, and `structural_gate` check set. AEO measurement is methodologically distinct enough (engine-prompt sampling, citation aggregation, phantom-mention tracking) that a dedicated judge surface is warranted. Trigger watch: AEO-default-required by 2026-Q4 across B2B SaaS / AI-tooling / modern-agency / DTC per §1.5 component definition.

**Trigger 3 — Component H → `win_loss_program` sibling lane.** When structured win-loss tooling matures — e.g., AI-call-recording analytics integrated with CRM stages and AI-extraction infrastructure becomes operationally robust at the agency level — Component H grows from "optional extract when client has data" to "full structured win-loss program as a recurring deliverable." Fork to `win_loss_program` sibling lane with its own optimal-output spec and judge layer. Indicator: when ≥3 cohort clients have active win-loss programs the agency is analyzing, and the analysis pattern shows multi-quarter trajectory continuity that the snapshot Component H format can't carry.

**Trigger 4 — Component E → MON-lane handoff schema lock.** Not a sibling-fork; a coordination trigger. When the `monitoring` lane reaches v3-equivalent maturity (its own judge-stable optimal-output spec, structural_gate check set, and ingestion schema for cross-lane handoffs), define the formal handoff schema between CI Component E and MON ingestion. Until MON-lane maturity, Component E's `structural_gate` validates internal structure (named signal + threshold + action rule + escalation cadence) without enforcing schema-conformance with MON's not-yet-defined ingestion API.

**Trigger 5 — Evaluate-cluster Component-A variant.** When ≥3 Evaluate-class fixtures appear (acquisition target / market entry / structural alliance decisions), build a parallel Evaluate-cluster Component-A spec. Maintain `competitive` lane as React-cluster default; Evaluate-cluster routing lives in workflow-input `decision_shape` flag. Not a sibling-lane fork — same lane, different Component-A form factor selected by input flag. Components B–F generalize across both clusters; Component A's forcing-function form is cluster-specific.

### 8c. Comprehensive-deliverable validation gate — 3-phase pipeline (added 2026-05-19; rewritten 2026-05-19 v3.7 to break chicken-and-egg with §1.5 substrate-readiness gate)

The original v3.6 validation gate ("run Components B–F retroactively against the current 4 Phase-3 fixtures before shipping") collided with §1.5's substrate-readiness gate: substrate doesn't yet emit B–F, so retroactive validation can't fire, so v3.6 can't promote — but without promotion, substrate has no spec to build to. v3.7 splits the gate into three sequential phases. The phases are NOT independent decision points; they are gates a component must pass through in order.

**Phase 1 — Substrate readiness (gate 1; per §1.5).** A component is substrate-ready when `session_eval_competitive.py` reliably emits the component artifact (`brief.md` for A; `competitors/<n>.json` with per-competitor profile fields for B; `trajectory_matrix.md` for C; `comparison_matrix.md` for D; MON-handoff schema for E; `evidence_appendix.md` for F; optional G/H per engagement scoping). Component A is substrate-ready at v3.6 ship. Components B–F + optional G/H are substrate-readiness-gated until their substrate emission lands. Until Phase 1 passes for a given component, it does not progress.

**Phase 2 — Research validation (gate 2; replaces the original §8c retroactive-fixture gate).** Once Phase 1 passes for Component X (substrate emits X), run 3 holdout fixtures through the judge against Component X. If judge rationales match human-reviewer judgment on at least 2 of 3 fixtures (≥66% concordance on score directionality and rationale quality), Component X graduates from substrate-readiness-gated to production-default. **This is a research validation, not a production-traffic validation** — it tests whether the judge layer + structural_gate check set behaves as designed on the new component, not whether real clients use the component. Phase-3 fixtures (DWF, Anthropic, Perplexity, Klinika) plus any new vertical fixtures backfilled per §8.5 form the holdout pool; 3 fixtures per component is the minimum for the concordance check. If <2/3 concordance, the spec for that component needs another edit pass before re-validation.

**Phase 3 — Production observation (gate 3; optional demotion path).** After Component X has shipped as production-default to ≥5 client engagements, observe two client-side metrics: (a) **open-rate** (does the client open the component artifact when delivered?), (b) **reference-back rate** (does the client quote or reference the component when defending the resulting decision in follow-on conversations with the agency?). If <30% of clients reference Component X in defending decisions over 2 consecutive quarters, demote Component X back to optional via a §1.5 spec edit — i.e., Component X stays available on engagement-scope opt-in, but is no longer in the production-default package. This is a *demotion-only* gate; Components that pass Phase 2 ship by default and only retreat to optional if Phase 3 evidence accumulates against them.

**Gate separation rationale.** Three gates exist because three different questions are being asked: gate 1 asks "can the workflow produce this component at all?" (substrate engineering); gate 2 asks "does the judge correctly score this component when produced?" (research validation, judge-quality concern); gate 3 asks "do real clients use this component once shipped?" (production observation, deliverable-value concern). Collapsing them into a single gate — as v3.6's original §8c did — creates the chicken-and-egg: gate 2 can't fire without gate 1; gate 1 has no spec target without gate 2 promotion; gate 3 needs gate 2 promotion + production traffic. Separating them means each component progresses through gates 1 → 2 → 3 independently, and the spec is not blocked on either substrate engineering OR client-validation evidence that doesn't yet exist.

**Cost instrumentation (preserved from v3.6).** Cost-instrument the modular architecture on 1 fixture before propagating; per `docs/research/2026-05-19-competitive-comprehensive-scope.md` §8.10, watch for per-fixture cost exceeding $15–25 (rough envelope). Components B–F add ~3–5x compute cost per fixture (more retrievals, more substrate, more `structural_gate` checks). If cost overshoots, trim Component F first (most expensive: URL HEAD resolution + quote-grep + entity-existence lookup).

---

## Closing note

v3.5 is a **deliverable-surface restructure**, not a judge-layer redesign. The judge layer (criteria CI-1 through CI-6, anchors, CoT, examples, Goodhart-resistance, structural_gate Component-A check set) is preserved verbatim from v3.4. The deliverable surface expands from "the brief" to a 5-component modular package: Component A is the brief (judge-scoped); Components B through F wrap the brief with depth that the judge does not see and `structural_gate` evaluates deterministically. Optional Components G and H extend the package where engagement scoping calls for them.

The single most important architectural recommendation: **modularize. Keep the judge narrow. Grow the deliverable wide. Use `structural_gate` for the wrap-around components. Preserve all the v3.4 judge work.**

The judge surface area stays constant; the deliverable surface area grows ~5x. The lane becomes capable of the 24-axis competitive-intelligence surface a 2026 modern AI-native agency client expects, without expanding the Goodhart attack surface at the judge layer.
