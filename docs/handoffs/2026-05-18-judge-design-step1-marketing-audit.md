---
date: 2026-05-18 v1
type: judge-design Step 1 — marketing_audit (MA) optimal-output spec
status: DRAFT v1 — JR-locked architectural decisions applied from v0 + 5 deep-research deliverables; ready for redundancy check + fixture validation + Cluster-A fixture build
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
sibling_gold_standard: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI v3.3 — decision_shape routing pattern, first-cohort overfit reduction)
companions:
  - docs/research/2026-05-18-judges-domain-marketing-audit.md (generalist MA domain research)
  - docs/research/2026-05-18-marketing-audit-vertical-conventions.md (vertical × stage axis)
  - docs/research/2026-05-18-marketing-audit-artifact-taxonomy.md (6-shape taxonomy → Cluster B hybrid lock)
  - docs/research/2026-05-18-marketing-audit-ai-failure-modes.md (LLM-specific MA failure surfaces)
  - docs/research/2026-05-18-marketing-audit-decision-format-mapping.md (6 decisions → 3 clusters)
  - docs/research/2026-05-18-marketing-audit-upstream-diagnostic.md (6 upstream classes + sequencing-not-parallel)
revision_history:
  - 2026-05-18 v0 — initial draft, 5 criteria, single Cluster-B reader, B2B-SaaS-only anchors
  - 2026-05-18 v1 — JR-locked architectural decisions applied:
      §1 Reader split into 3 cluster-aware sub-readers (Personnel A / Operational B / Strategic C);
      §1.5 Artifact shape LOCKED for Cluster B canonical (mid-length founder audit + roadmap, 2000–4500 words, 5 sections), Clusters A/C routed via workflow `decision_shape`;
      §2 Success rewritten as cluster-conditional;
      §3 expanded with mediocre + Goodhart-collapse + stage-mismatch Goodhart + cluster-format-mismatch + AI-failure surfaces (financial-metric / channel-claim / competitor-data confab + marketing-misdiagnosis);
      §4 MA-2 anchor loosened to per-cluster action shape; MA-4 sharpened to detail-vs-decision-class match; MA-5 expanded with positioning as 6th upstream class + sequencing-not-parallel-tracking + 4 named score-0 sub-patterns;
      §5 wrapper references `decision_shape` from source_data; format-agnostic at criterion level;
      §6 Goodhart-resistance verification rewritten per-criterion + "parallel-tracked NOT sequenced" Goodhart move on MA-5;
      §7 conforms-check;
      §8 open questions with Cluster A fixture build + ≥30% upstream-evidence calibration + B2C/DTC 4th-cluster watch + quarterly-memo subcluster + personnel-verdict ethics + MA-1↔MA-4 redundancy;
      Per-criterion structured 3-step CoT preserved; 3-vertical-anchored score-1 examples per criterion (SaaS + DTC/consumer + healthcare/services); 7 structural_gate checks enumerated in §8.
---

# Marketing Audit — Optimal-Output Spec (DRAFT v1)

Conforms to `docs/rubrics/judge-design-guide.md`. Frameworks (Sean Ellis, Brian Balfour, Lenny Rachitsky + Dan Hockenmaier, Dave McClure, Peep Laja, Eric Ries, Tomasz Tunguz, April Dunford, Patrick Campbell, Ross Simmonds, Roger Martin, Christopher Lochhead) inform the reader/success/failure spec and are the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

This v1 supersedes v0's single-Cluster-B archetype. Five concrete decisions in v1 anchored in the 5 deep-research deliverables: (a) §1 Reader splits into 3 cluster-aware sub-readers because v0's "founder-CEO at pre-Series-B B2B SaaS, Tuesday afternoon, Friday leadership meeting" implicitly assumed Cluster B and misjudged Cluster A (personnel verdict) and Cluster C (strategic reset); (b) §1.5 LOCKS the Cluster B canonical artifact shape (mid-length founder audit + roadmap, 2000–4500 words, 5 sections) and routes Clusters A/C via workflow `decision_shape`, NOT by adding a 6th criterion; (c) §3 catalogues LLM-specific failure surfaces (financial-metric confabulation 17–46% per FAITH; channel-claim fabrication; competitor-data confabulation 14–95% per HalluLens; marketing-misdiagnosis bias) and routes deterministic verification to `structural_gate`; (d) MA-5 absorbs positioning as the 6th upstream class and tightens to require sequencing-not-parallel-tracking; (e) MA-4 sharpens to test detail-vs-decision-class match, with explicit cluster-format-mismatch as a score-0 condition.

The 5-criterion ceiling is preserved. Research predicted an MA-6 "diagnosis survives blame-attribution check" — it absorbs into MA-5 via the explicit sequencing requirement and the marketing-misdiagnosis bias call-out in §3b. Adding a criterion to test format would re-introduce feature-checking, per the Phase 4 rollback at `c76f051`.

---

## 1. Reader (LOCKED 2026-05-18)

The MA artifact serves three sharply different readers commissioning three sharply different decisions. Reader and decision shape are orthogonal variables; the same founder-CEO can be the consumer of any cluster at different moments. The lane routes between clusters via a workflow input `decision_shape ∈ {A, B, C}`; the judge stays format-agnostic at the criterion level.

**Primary readers across all three clusters share invariant properties.** They are smart, time-poor, runway-aware, and skeptical — they've consumed enough consultant-grade decks and "ten-page PDFs of generic recommendations" to recognise slot-fills. They have authority to act on the audit. They will quote one or two sentences from it if challenged later.

### Cluster A — Personnel verdict (decision_shape = "A")

CEO or board chair commissioning the audit as evidence for a personnel call — fire/hire CMO, restructure marketing function, replace agency-of-record. Authority horizon: 1–3 weeks from audit landing to vote. They need a binary verdict (continue / formal-PIP / replace / restructure-around) plus named off-ramps (interim coverage, transition window, knowledge-transfer scope).

The Cluster A reader DOES NOT need a 30-day experiment or a 90-day execution plan; they need a defensible attribution sieve that separates exogenous demand collapse from operator error. Format inheritance from PE portfolio operator reviews (TPG / Vista / KKR), Bessemer / USV portfolio CMO-fitness reviews, McKinsey CEO-advisory personnel memos.

### Cluster B — Operational reallocation (decision_shape = "B")

Founder-CMO hybrid at pre-Series-B B2B SaaS, head of growth at Series-B-or-later, or in-house Director of Marketing — with operational authority over channel budget and team capacity. Authority horizon: 2–6 weeks (next quarterly budget cycle, or sooner if cash is tight). They have ~30 minutes Tuesday afternoon between sales calls; by Friday they need to walk into the leadership meeting with 1–2 specific bets for the next 30 days.

The Cluster B reader needs a per-channel scorecard with CAC payback, a named reallocation recommendation, an experiment ladder with kill-triggers. Format inheritance from Bell Curve / Demand Curve paid-acquisition audits, Animalz / Foundation Inc content audits, ProfitWell pricing audits, Klue executive briefings, the Amazon six-pager pattern.

This is the cluster v0 implicitly assumed. It is one of three.

### Cluster C — Strategic reset (decision_shape = "C")

Founder-CEO (commissioning) plus incoming fractional CMO or VP Marketing (executing). The audit is the foundational document the fractional inherits at Day 30 of a 90-day engagement, or the strategic memo justifying a reposition / category-pivot / ICP-resegmentation / pricing-model change. Authority horizon: 4–13 weeks audit + planning, then 6–18 months of execution.

The Cluster C reader needs an April-Dunford-grade positioning teardown, Sean-Ellis-grade PMF survey output, ICP-resegmentation evidence (cohort-by-segment), and a 30/60/90 execution plan with named foundational bets, owners, budgets, and explicit off-ramps for Day-45 founder-impatience scenarios. Format inheritance from the fractional-CMO Day-30 deliverable (Envizon / SaaSConsult / ASP / ThinkCap / Strategic Pete), MKT1 strategy memos (Kramer / Estreich), First Round Review GTM teardowns, Play Bigger category-design memos.

### Substitute readers across clusters

Decision-maker at a small-to-mid B2B services firm (legal, accounting, consulting, agency, financial advisory) evaluating practice-portfolio shifts (Cluster A or C). Owner-operator at a small-to-mid local-market business (healthcare, hospitality, retail, professional services) evaluating market entry / pricing / referral patterns (Cluster B or C). Head of Marketing or VP Growth at a DTC e-commerce platform evaluating channel / pricing / positioning shifts (Cluster B or C). Fintech or regulated-finance operator evaluating compliance-bounded channel mix (Cluster B, with regulatory-constraint overlay). The B2B-SaaS reference set in this spec exists because that is gofreddy's first-cohort fixture skew (Anthropic, Perplexity); legal-services (DWF) and healthcare (Klinika) are present but underweighted, and DTC / fintech / marketplaces are not yet in fixtures. The spec is designed to generalise to tech-savvy-founder / early-co clients across verticals; first-cohort overfitting is an explicit risk to monitor (see §8).

### NOT the reader

Junior marketer looking for a checklist. MBA writing a thesis on the company. VC doing due diligence. Marketing-ops analyst triaging a HubSpot dashboard. Board member reading a deck for sport. Comms director (see monitoring lane).

---

## 1.5. Artifact shape (LOCKED 2026-05-18 for Cluster B; cluster-routed for A/C)

**Cluster B canonical (this lane's default if `decision_shape` is unset or "B"):** mid-length founder audit + 30/60/90 roadmap, **2,000–4,500 words**, 5-section spine. Locked because shape-drift Goodhart is a documented failure mode in evolution loops (per `docs/research/2026-05-18-marketing-audit-artifact-taxonomy.md` §5): under 50-generation selection pressure, the workflow learns that longer audits with more recommendations score higher on shallow proxies, drifting toward 8,000+ word "ten-page PDF of generic recommendations" artifacts; OR drifts toward Klue-thin executive briefings that fail MA-1's 2-source evidence requirement and MA-3's revenue-chain trace. The lock prevents both.

**Cluster B form factor:**
- **Length: 2,000–4,500 words.** Hard floor at 2,000 (below this, evidence triangulation against MA-1 becomes infeasible). Hard ceiling at 4,500 (above this, audit-bloat Goodhart sets in; founder can't consume in the 30-minute Tuesday window). Word-count enforcement lives in `structural_gate`, NOT in criterion prose.
- **5 sections, in order:** (1) Readiness verdict + named binding constraint — exec-scorecard-style opening, ~150–300 words, borrows Kalungi One-Page format's verdict-at-top discipline; (2) Stage diagnostic + ecosystem-fit analysis — ~400–700 words, names the stage with at least one observable anchor (ARR band, retention cohort, channel-fit signal, capacity utilization, location count, regulatory licensing — vertical-appropriate), refuses at least one stage-inappropriate best practice; (3) Current-state diagnostic with domain-teardown-grade evidence depth on the binding constraint specifically — ~600–1,500 words, NOT exhaustive scorecard across every dimension; CXL-ResearchXL-style triangulation (≥2 sources per claim) applied only to the binding-constraint section; (4) Upstream-vs-marketing check — ~200–500 words, explicit branch; if evidence points at PMF / ICP / positioning / pricing / product / sales motion, name it directly and SEQUENCE marketing recommendations behind the upstream fix (not parallel-tracked); if marketing IS the constraint, defend with evidence; (5) Prioritised 30/60/90 sequencing — ~400–800 words, 1–3 Day-30 commitments with action + owner + budget envelope + timeline + success metric tied to baseline; Day-60 and Day-90 lighter (sequenced, not over-specified); optional explicit "cuts" section.

**Cluster A canonical (decision_shape = "A"):** 3–7 page executive memo, ~800–2,000 words, binary verdict in the first page (continue / formal-PIP / replace / restructure-around) + 2–3 evidence pillars from attribution sieve + named off-ramps + interim-coverage plan. NOT a 30-day experiment, NOT a 90-day execution plan. Format inheritance from PE-portfolio operator reviews.

**Cluster C canonical (decision_shape = "C"):** 15–25 page positioning teardown + PMF-survey output + ICP-resegmentation + 30/60/90 execution plan, ~4,500–9,000 words. Foundational research depth on the strategic-reset axis (positioning / category / ICP / pricing model). Format inheritance from fractional-CMO Day-30 deliverables and Dunford-style positioning teardowns.

**Out-of-scope shapes (the lane will NOT produce these regardless of cluster):**
- Pure 1-page readiness scorecard (too thin for MA-1's 2-source evidence requirement)
- Pure single-domain teardown (e.g., 30-page paid-acquisition audit only) — fixture clients span domains; locking the lane to one domain is wrong
- 20–40 slide board-ready deck (different reader, different visual-rhetoric rubric problem, different fixture format)
- Notion / live-doc operating audit (different substrate — link tree, not single artifact)
- Automated dashboard digest (already SaaS-commodified by HubSpot / Semrush / Ahrefs)

**Why workflow-level routing not criterion-level routing.** Adding a 6th criterion "audit format matches decision class" would re-introduce the feature-checking pathology rolled back at `c76f051`. The workflow's `decision_shape` input switches substrate template, `structural_gate` length-and-shape check, and fixture set. The judge tests outcomes (MA-1..MA-5) that survive cluster shift. This is the CI v3.3 routing pattern — proven and load-bearing.

**Empirical validation scope.** The Cluster B canonical form is research-grounded against B2B SaaS practitioner conventions (Kalungi, Bell Curve, Demand Curve, ProfitWell, Wynter, CXL, fractional-CMO playbooks). When fixtures from new verticals appear (DTC e-commerce, regulated finance, hospitality, marketplaces, dev-tools), re-validate — different verticals may need shape adjustments (e.g., DTC may need a contribution-margin-by-cohort comparison instead of CAC payback; healthcare may need a capacity-utilization section; regulated finance may need a regulatory-clearance overlay). The §1.5 lock is the React-cluster-equivalent default; lane scope may expand or sibling-fork as the client mix evolves.

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18)

After reading, the reader commits to the **decision-shape-appropriate next action** on the most consequential finding the audit surfaces. The action class varies by cluster; the discipline (commit to one specific thing with evidence-defended trade-off they could explain to their CFO / board / partnership) is invariant.

**Cluster A — Personnel verdict.** Board or CEO commits to a binary verdict (continue / formal-PIP / replace / restructure-around) with a named off-ramp the audit makes legible: interim coverage (fractional? VP elevation? founder-led?), transition window, knowledge-transfer scope. They could walk into the next board call and assign the call. **Sleep test:** if they slept on it overnight, they'd make the same call tomorrow — the attribution sieve's logic survives 24h reflection, not just board-meeting momentum.

**Cluster B — Operational reallocation.** Founder-CMO or head of growth commits to 1–3 specific bets for the next 30 days, each with action + named owner + budget envelope + timeline + success metric tied to a current baseline. They could walk into Friday's leadership meeting and assign them. They could explain to their CFO what budget line moves and what initiative pauses.

**Cluster C — Strategic reset.** Founder commits to a 90-day execution plan with named foundational bets at Day-30 / Day-60 / Day-90, plus explicit off-ramps if Day-45 or Day-60 reads don't materialise. The incoming fractional CMO inherits this as the engagement contract.

In all three clusters: the brief may surface a *secondary* follow-up intel ask (the next question the reader should commission). Primary success is the committed action; the follow-up ask is bonus, not substitute.

### World-class real-world exemplars — quality anchors, NOT templates to copy

**Cross-industry rigour ceiling (Cluster A):** McKinsey / Bain CEO-advisory operator-review memos; PE portfolio quarterly CMO-fitness reviews (TPG / Vista / KKR methodology); Roger Martin's *Playing to Win* attribution discipline (separate operator effort from strategic context before judging output); Mark Suster's published "should we replace the CMO" framework.

**Practitioner ceiling (Cluster B):** Bell Curve / Demand Curve paid-acquisition audits with foundation-then-scale sequencing; Animalz editorial-first content audits; ProfitWell pricing audits at Patrick-Campbell-grade rigour; Wynter messaging-resonance audits with ICP-panel research; Kalungi's 95-point inspection scorecard with named-stage prescription; the Amazon six-pager narrative discipline.

**Strategic-reset ceiling (Cluster C):** April Dunford's published positioning teardowns (*Obviously Awesome* methodology); MKT1 strategy memos (Kramer / Estreich); Andy Raskin's strategic-narrative work; Drift's published category-creation playbook (sales-engagement → conversational marketing); the fractional-CMO Day-30 deliverable as documented across Envizon / SaaSConsult / ASP / ThinkCap / Strategic Pete; Lenny Rachitsky's PMF re-test essays.

What ties these together across all three clusters: point of view at the top, structural reasoning, evidence triangulation, one or two calls the reader could commit to before the next decision gate.

---

## 3. Failure — mediocre, Goodhart-collapse, AI-specific (LOCKED 2026-05-18)

### 3a. Mediocre — five failure modes the judge must discriminate against

**Ten-page PDF of generic recommendations.** Reads as a competent strategy memo but every recommendation is one level too abstract ("strengthen positioning" instead of "reprice the SMB tier by 15% by Q3 to defend against BambooHR's bundled compliance push"). Same audit would land for a competitor in a different vertical with different ARR. Named directly by McKee Creative and Helen Cox Marketing as the dominant SMB-audit failure mode.

**Vanity-metric overload.** "Impressions up 40%" / "social engagement at 14%" / "follower count crossed 12k" as headline findings. Eric Ries / Marketoonist named this. Founder reads, nothing is the unit of action.

**Flat list of equal-weight recommendations.** 5+ recommendations with no prioritisation, no kill-triggers, no sequencing rationale. The Kalungi cap of "top 3–5 priorities" is the practitioner standard for a reason: senior readers will not act on the eighth recommendation.

**Single-hypothesis confirmation bias.** Audit reinforces the reader's existing prior. No disconfirming evidence engaged. Founder nods through, commits to nothing they weren't already going to do. Comfortable rather than uncomfortable.

**Stage-mismatched framework application.** Audit applies a stage-inappropriate framework regardless of evidence: ABM stack for $1.8M ARR; PLG tactics for a sales-led company with named SDR/AE motion; "trial-to-paid optimization" for a DTC brand with no trial; "MQL nurture" for a derm practice whose patients book directly through GBP. The recommendation may be best-practice in some other context but is wrong for THIS company's stage and vertical. Score 0 even if every other surface marker (named constraint, owner, budget, timeline) is present.

### 3b. Goodhart-collapse — slot-fill drift under selection pressure

**Phase 4 pathology (the historical Goodhart trap precedent).** 50-generation evolution against a feature-checking judge produced the pathology rolled back at `c76f051` (commit `698e658`). The workflow learns to slot-fill named surface markers — framework headlines, mechanical stage-rotations, ACH-strawman alternative hypotheses, fabricated quantified outcomes. Structurally compliant, strategically empty.

**MA-specific Goodhart modes:**

- **Audit-bloat.** Workflow learns longer audits score higher on perceived comprehensiveness. Drift 3,000 → 8,000+ words across generations. Founder can't consume in the 30-minute window. Caught by §1.5 word-count band in `structural_gate`.
- **Recommendations-count-gaming.** Workflow learns more recommendations look like more value. Drift 2–3 prioritised → 8+ of equal weight. Caught by `structural_gate` ceiling on Day-30 recommendations + MA-2's outcome question discriminating against templated owner/budget/timeline boilerplate.
- **Framework-citation as substitute for analysis.** Workflow learns naming Sean Ellis / AARRR / Four Fits / ICE / North Star / CAC payback / ResearchXL signals expertise. Drift from analysis-with-frameworks-as-toolkit → framework-name-drops-with-shallow-analysis. Caught by design-guide constraint (no framework names in rubric prose) + `structural_gate` banned-phrase grep extension.
- **Stage-mechanical-rotation.** Workflow learns mentioning "you are at stage X" scores well on MA-4. Drift: every audit mechanically rotates pre-traction → traction → scaling → expansion regardless of fixture. Caught by MA-4's anchor requirement (at least one observable anchor + at least one explicit refusal on stage grounds).
- **Upstream-default-no.** Workflow learns the upstream branch is high-cost (makes its own recommendations smaller) and defaults to "no, it's marketing." Drift: every audit's upstream-vs-marketing section concludes "marketing is the constraint" by default, sometimes with the upstream signal confabulated away. Caught by MA-5's sequencing-not-parallel requirement + `structural_gate` upstream-signal presence check.
- **Parallel-tracking instead of sequencing (Goodhart-resistant slot-fill on MA-5).** Workflow learns to slot-fill an "upstream considerations" section AND keep the marketing recommendations parallel — so the founder reads it and defaults to the concrete marketing actions. MA-5 explicitly requires sequencing (marketing recommendations explicitly deferred, paused, or scoped behind the upstream fix), NOT parallel-tracking.

### 3c. Cluster-format-mismatch (the highest-leverage cross-cluster failure)

Per `docs/research/2026-05-18-marketing-audit-decision-format-mapping.md` §3, the single highest-leverage MA failure mode is format-vs-decision-class mismatch, in both directions:

- **Cluster A served by Cluster C format.** Board commissioning a fire-CMO decision gets a 25-page reposition-grade teardown. The binary verdict is buried on page 17. The board reads page 3, sees no binary call, defers the personnel call another quarter while the company burns runway. The audit was technically excellent and operationally useless.
- **Cluster C served by Cluster A format.** Founder commissioning a reposition gets a 5-page "fire the CMO"-style memo. No positioning teardown, no PMF survey, no ICP-resegmentation evidence. The founder commits to the reposition, ships the homepage in week 2, then discovers in week 8 that the segmentation was noise. The audit was punchy and strategically wrong.

MA-4 score-0 explicitly covers cluster-format-mismatch — an audit whose detail level is wrong for the commissioned decision class scores 0 even if every other criterion scores 1.

### 3d. AI-specific failure surfaces (new in v1, per ai-failure-modes research)

Marketing audits are quantitative-by-construction in a way CI briefs are not — CAC, LTV, payback, churn, NRR, trial-to-paid are the dominant claim shape. Each cited metric is a fabrication surface. Five LLM-specific failure modes the v0 spec did not catch:

- **Financial-metric confabulation.** Audit invents CAC, LTV, NRR, MRR, ARR, payback, churn, trial-to-paid numbers that do not exist in source data. Documented at 17–46% intrinsic hallucination rates on financial-entity numerical statements (FAITH, arxiv 2508.05201). FactSet 2025 retrospective: AI-assisted equity research exhibits 59% higher forecast error specifically from un-vetted plausible-sounding signal.
- **Channel-claim fabrication.** LLM asserts "LinkedIn ads are working" / "their SEO is the dominant channel" / "they ran a six-figure paid-LinkedIn pilot in Q3" without analytics / Gong / campaign-report evidence — driven by marketing-blog training-corpus priors (modal B2B-SaaS = content+SEO; modal B2C = paid social+influencer; both fire regardless of actual data).
- **Competitor-data confabulation.** Pricing tiers, positioning claims, customer logos, executive moves on competitors that don't exist or are misattributed. HalluLens / HalluEntity / KGHaluBench document 14–95% across 13 LLMs × 40 domains. NeurIPS 2025 100-citation incident: 66% Total Fabrication, 27% Partial Attribute Corruption.
- **Marketing-misdiagnosis bias.** LLM over-attributes problems to marketing causes because training-corpus is dominated by marketing-blog content where marketing is *always* the answer. Sycophancy + CoT-rationalization compound (arxiv 2603.16643, 2510.04721). The LLM bias is structurally stronger than the human consultant bias because LLMs don't have the Bell-Curve / Kalungi / Sean-Ellis explicit anti-marketing-bias literature in their priors, only the marketing-blog corpus where marketing is the answer by survivorship.
- **Recommendation hallucination.** Wrong-stage / wrong-vertical / wrong-sales-motion tactic recommendations driven by latent-space gradient toward modal B2B-SaaS playbook regardless of input specifics. LLMLagBench (arxiv 2511.12116) plus the practitioner-named "wrong-stage best-practices" failure compound.

**Deterministic AI-failure checks live in `structural_gate`** — metric-citation grep (any %/dollar/multiple/ratio must have inline citation within 200 chars), source-corpus numerical match (cited metric must appear in named source ±5% tolerance), channel-claim source check, competitor URL HEAD-check, entity-existence lookup, stage-applicability denylist, forbidden-formulation grep ("industry-standard," "typical SaaS," "reportedly," "according to industry sources" without inline citation). Per the OpenRubrics design principle (Hard Rules → `structural_gate`, Principles → judge), the judge cannot deterministically verify URL resolution, quote provenance, entity existence, or numerical match — those are factual checks, not semantic judgments. **Semantic marketing-misdiagnosis-bias check lives in MA-5** below; the explicit sequencing requirement and upstream-engaged-on-the-merits CoT absorb the research-predicted MA-6 "Diagnosis survives blame-attribution check" candidate.

---

## 4. Criteria — outcome questions (5)

### MA-1 — Founder can name the binding constraint

**Outcome question (binary):**
After reading the audit, can the reader name in one sentence which single dimension is the binding constraint on growth, and why — with at least two evidence sources behind the diagnosis? Could they walk into their next decision gate (board call / leadership meeting / planning offsite) and defend the named constraint?

**Score 1 (yes)** — Audit names one specific constraint with at least two evidence sources supporting it. The constraint is locatable — not "marketing in general," but a specific funnel stage, a specific channel, a specific message, a specific upstream gap, a specific operator decision (Cluster A), or a specific positioning axis (Cluster C). The two evidence sources are independent and named (cohort analysis on slide N, Gong calls dated X, Wynter messaging survey, win-loss interviews, benchmark from named primary source).

Example A — SaaS Cluster B (do not optimize toward this): "Your trial-to-paid conversion is 1.8% versus the SaaS median of 6%; until that moves, paid-acquisition budget is being spent on water that leaks out before revenue. Evidence: cohort data on slide 8 (12 monthly cohorts, Stripe export); 12 Gong calls where prospects bounced at the onboarding step (transcripts attached, themes coded)."

Example B — DTC / consumer (do not optimize toward this): "Your repeat-purchase rate at 90 days is 11% versus the DTC apparel median of 28%; until that moves, Meta CAC at $42 doesn't pay back at your $58 first-purchase contribution margin. Evidence: cohort retention curves on slide 14 (Northbeam export, last 6 cohorts); 47 post-purchase survey responses citing 'didn't fit / didn't like fabric' as the dominant non-return reason (Klaviyo flow data)."

Example C — Healthcare / local services (do not optimize toward this): "Your top constraint is reputation, not lead volume — your 4.2 Google rating and 19 reviews-mentioning-wait-times are choking the funnel before paid acquisition can pay back. Evidence: GBP review velocity (47 reviews in 90 days, 8 below 3 stars citing wait times); RealSelf comment-thread analysis showing 22 'considered but did not book' patients citing reputation (slide 11)."

**Score 0 (no)** — Multiple dimensions surveyed at equal weight. Vague constraint named without evidence ("messaging could be sharper"). Multiple constraints named without ranking. Single-source extrapolation presented as multi-source (one Gong call, one cohort point). Confabulated metric used as evidence (caught upstream by `structural_gate`; if it slips through, MA-1 scores 0 on the evidence-traceability test in CoT Step 2). Severity-inflation failure also scores 0: every signal severity=3, every finding maxed out, no credible severity distribution. Severity (0-3) on SubSignals + ParentFindings must be anchored to lens-specific `severity_anchors` from rubric YAML, and ParentFinding severity = max of children (rollup rule); a "sea of 3's" defeats the diagnostic discipline that lets the reader name ONE binding constraint with conviction.

**Score 0.5 (unknown)** — Constraint named but the second evidence source is absent or too thin to defend in the decision gate. Emit 0.5 + "unknown" + one sentence on what evidence would have to be present.

**Required CoT:**
- Step 1: Identify the constraint the audit names + locate it (funnel stage, channel, message, upstream class, operator decision for Cluster A, positioning axis for Cluster C).
- Step 2: Verify at least 2 independent named evidence sources support the diagnosis (not slot-filled, not confabulated, not single-source restated).
- Step 3: Emit verdict + one-sentence justification citing the named constraint and the two evidence sources.

Do not score: number of dimensions surveyed, presence of "binding constraint" header, total audit length, framework-name density. Those live in `structural_gate` or do not matter.

### MA-2 — Reader commits to the decision-shape-appropriate next action

**Outcome question (binary):**
After reading, would the reader commit to the next action appropriate to the commissioned decision class — and could they walk into their next decision gate and assign it? The action class varies by cluster; the discipline (specificity + named target + named cost + decision-shape-appropriate timeline) is invariant.

**Score 1 (yes)** — Recommendation matches the decision class:

- **Cluster A (Personnel):** Binary verdict (continue / formal-PIP / replace / restructure-around) + 1–2 named off-ramps + interim coverage plan + transition window + knowledge-transfer scope. NOT a 30-day experiment.
- **Cluster B (Operational):** 1–3 Day-30 commitments, each with action + named owner (specific person or role, NOT "the team") + budget envelope (specific dollar amount or shape) + timeline (specific weeks) + success metric tied to a current baseline. Action shape maps cleanly to a `capability_registry` tier (`fix_it` / `build_it` / `run_it`) — recommendations describe the work the agency would do, NOT DIY execution guides. When `proposal.md` is produced alongside `findings.md`, it carries the 3 tier headers (`fix_it`, `build_it`, `run_it`) in fixed order, structurally enforced by `structural_gate`. The action shape is sized for an agency engagement of $15K+ scope, not a $1K one-off artifact: the audit IS pitching a credible agency engagement vs. reading like a one-off audit report, and capability_registry tier-mapping serves the pitch.
- **Cluster C (Strategic):** 30/60/90 plan with named foundational bets at each milestone + named owners + budgets + explicit off-ramps (e.g., "if Day-60 NPS on new-ICP cohort doesn't reach 60+, revert the homepage and re-evaluate").

Example A — SaaS Cluster B (do not optimize toward this): "Week 1: rewrite homepage hero against the buyer-language patterns from the 12 Gong calls. Week 2–3: ship A/B test against current 0.8% primary-CTA-click baseline. Week 4: read result, decide kill-or-scale. Owner: head of marketing + freelance designer Maria. Budget: $3k for VWO + design. Kill-trigger: if variant doesn't lift to ≥1.4% by week 4 reading, revert and pursue the pricing-page rewrite as the next-priority Day-30 bet."

Example B — DTC / consumer (do not optimize toward this): "Day 0–14: launch post-purchase fit-survey via Klaviyo to last 1,000 buyers. Day 14–30: redesign size-chart + fabric-detail copy on top-5 SKU PDPs against survey responses. Owner: ecom manager + product team. Budget: $5k (no agency; in-house copy + photoshoot re-use). Success metric: repeat-purchase rate at 90 days for buyers post-launch, target ≥18% (vs current 11%). Kill-trigger: if 30-day return rate doesn't shift in either direction by Day 60, pause and run a deeper jobs-to-be-done sprint."

Example C — Healthcare / local services Cluster A (do not optimize toward this): "Recommendation: replace marketing lead. Pat has owned marketing for 11 months at the practice; new-patient bookings flat across that window while a comparable practice 3 blocks away grew bookings 38% in the same period (data on slide 9). Pat owned three calls peer-stage local-marketing leads would have decided differently: deferring the GBP review-response system through summer despite seeing wait-time complaints, holding the RealSelf profile incomplete for 8 months, and signing the $4k/mo paid-Meta contract before the GBP rating crossed 4.5. Off-ramp: bring in fractional medspa marketing consultant for 90 days while we search; elevate front-desk lead Maria to operations-marketing-coordinator for tactical execution; defer the laser-skin investment by one quarter to free $30k for the search."

**Score 0 (no)** — Recommendations use vague verbs (explore, consider, evaluate, look into, optimise, improve). No named owner / budget / metric / off-ramp. Cluster-mismatched recommendation shape (30-day experiment for a personnel verdict; 5-page memo for a reposition). 5+ recommendations of equal weight with no prioritisation. Recommendation requires the reader to make a follow-up planning meeting before they can commit.

**Score 0.5 (unknown)** — Recommendation has 2–3 of the required elements for its decision class but is missing one load-bearing piece. Emit 0.5 + "unknown" + one sentence on which element is missing.

**Required CoT:**
- Step 1: Identify the commissioned decision class (Cluster A / B / C) from the audit's framing and the workflow's `decision_shape` input.
- Step 2: Identify the top recommendation(s) and verify they match the decision-class action shape: binary-verdict-plus-off-ramps for A, action+owner+budget+timeline+metric for B, 30/60/90-with-foundational-bets-and-off-ramps for C.
- Step 3: Emit verdict + one-sentence justification.

Do not score: number of recommendations beyond the 1–3 range, Gantt / timeline diagrams, formatting polish, presence of "recommendations" header.

### MA-3 — Every recommendation traces to a revenue mechanism

**Outcome question (binary):**
Does every substantive recommendation trace through an explicit chain to a revenue mechanism — a specific input the reader can spend against, a specific metric that would move, and a specific revenue line (or contribution-margin / payback / capacity-utilization line, vertical-appropriate) that would respond?

**Score 1 (yes)** — Each top recommendation names the metric it moves (CAC payback / trial-to-paid / MQL→SQL / organic-comparison-page traffic / expansion revenue for SaaS; contribution margin per cohort / repeat-purchase / return rate for DTC; capacity utilization / review velocity / referral-source mix for local services; win-rate / pipeline-sourced / sales-cycle for regulated B2B) AND the chain from input through to revenue. Brand / impressions / engagement recommendations specify how they flow into a downstream conversion metric. Vertical-appropriate evidence substrate is engaged (do not penalize evidence sources unfamiliar to a SaaS reader; do penalize sources categorically wrong for the company's vertical — e.g., "trial-to-paid" for a brand with no trial).

Example A — SaaS Cluster B (do not optimize toward this): "Move pricing from flat $99/mo to value-metric (per active seat) is expected to lift expansion revenue from 8% to 18% based on the cohort analysis on slide 14, with top-quartile accounts adopting per-seat first. Chain: per-seat pricing → top-quartile expansion → blended NRR 105% → 110%; with current ~$2M ARR, that's $100k of net-new ARR at zero acquisition cost."

Example B — DTC / consumer (do not optimize toward this): "Shift $32k/quarter from Meta to SMS retention flows. Chain: SMS-flow-recovered cart abandoners → repeat-purchase rate from 11% → 16% on the recovered cohort → contribution margin per buyer from $58 to $94 over 90 days (cohort-extrapolated from current Klaviyo abandoned-cart open rates). Net: ~$22k/quarter contribution-margin lift against the $32k reallocated."

Example C — Healthcare / local services (do not optimize toward this): "Launch GBP review-response system in week 1 + RealSelf profile completion in week 3. Chain: review velocity 6 → 14 per month → rating drift 4.2 → 4.5 over 90 days → GBP click-through-rate doubles → new-patient bookings from GBP from 8 → 16/month → capacity utilization from 71% to 86%; at the practice's $1.4k average treatment margin, that's ~$11k/month margin lift starting month 4."

**Score 0 (no)** — Recommendations live entirely above the revenue line (impressions / reach / share-of-voice / follower count as headline findings). Vanity metrics as headline. Activity-shaped recommendations ("publish 8 blog posts/month") without specifying the business metric. Recommendations recommending a vertical-inappropriate metric ("trial-to-paid" for a no-trial brand).

**Score 0.5 (unknown)** — Some recommendations trace to revenue, others don't, and the un-traced ones are load-bearing. Emit 0.5 + "unknown" + one sentence on which recommendation lacks the trace.

**Required CoT:**
- Step 1: List the top 1–3 recommendations.
- Step 2: For each, identify the metric it moves + the chain from input to revenue / contribution-margin / payback / utilization, verifying the metric is vertical-appropriate.
- Step 3: Emit verdict + one-sentence justification.

Do not score: precision of revenue forecasts, presence of "revenue impact" table, financial-model depth, ROI quantification (a CFO-recognizable chain is enough; exact ROI is not required).

### MA-4 — Audit locates company on stage map + matches detail to decision class + refuses wrong-stage best practices

**Outcome question (binary):**
Does the audit name the company's current stage with at least one observable anchor, refuse to recommend best practices that are wrong for the stage, AND match its detail level to the commissioned decision class? Would the reader finish the audit knowing why a generically-correct recommendation was deliberately omitted, AND would the audit's depth match what their decision needs?

**Score 1 (yes)** — Audit names the company's stage with at least one observable anchor — ARR band, retention cohort signal, channel-fit signal, capacity utilization, location count, regulatory licensing state, monthly revenue + margin profile, pipeline composition, or other vertical-specific stage signal. At least one recommendation is explicitly refused or sequenced on stage grounds. AND the audit's detail level matches the decision class (Cluster A: 3–7 pages with binary verdict; Cluster B: 5–10 pages with channel-by-channel scorecard; Cluster C: 15–25 pages with positioning teardown + ICP analysis + 30/60/90 plan). Mismatched-detail audits — over-elaborated for a personnel call, under-elaborated for a reposition — score 0. Stage diagnostic incorporates Phase-0 measurements from `phase0_meta.json` (the 9 meta-frames) when the workflow produces them; per-section findings color by relevant Phase-0 frames where applicable, and Phase-0 measurements that came back null surface as findings (gap-honesty), not papered over.

Example A — SaaS Cluster B (do not optimize toward this): "You are mid-traction (post-PMF, pre-scale) at $2.4M ARR with 91% NRR. The instinct to hire a paid-acquisition manager is wrong for this stage; the upstream constraint is sales-motion clarity, and paid spend at current LTV:CAC of 1.8 will worsen unit economics. Defer the ABM-tooling investment by two quarters until the SDR motion stabilises."

Example B — DTC / consumer (do not optimize toward this): "You are mid-stage DTC at ~$5M/mo with retail breaking even and digital still 78% of revenue. The recommendation to expand to TikTok Shop is wrong for this stage; the binding constraint is contribution margin at current Meta CAC, and a new platform adds creative-production cost without solving the unit-economic ceiling. Defer TikTok Shop until repeat-purchase at 90 days clears 18%."

Example C — Healthcare / local services (do not optimize toward this): "You are a healthy single-location aesthetic practice with 71% capacity utilization, 4.2 GBP rating, and an unsigned RealSelf profile. The recommendation to run Meta Ads for Botox-acquisition is wrong for this stage — the constraint is reputation and capacity, not lead volume. Defer paid Meta until GBP rating crosses 4.5 and capacity utilization reaches 85%."

**Score 0 (no)** — Same playbook regardless of stage. Recommendations include late-stage best practices (ABM tooling, full marketing-ops stack, demand-gen programmes) without checking foundations. Audit would land identically for a $500k-ARR and $20M-ARR company. **Or** detail level mismatches the decision class: 25-page positioning teardown for a fire-CMO decision; 5-page Cluster-A-style memo for a reposition; 12-page audit for a quarterly memo.

**Score 0.5 (unknown)** — Stage named but recommendations don't visibly tailor to it, OR detail level is borderline-appropriate (e.g., 12 pages for a 5–10-page Cluster B operational audit). Emit 0.5 + "unknown" + one sentence on which recommendation is stage-mismatched or which dimension of detail is off.

**Required CoT:**
- Step 1: Identify the company stage named + the observable anchor supporting it.
- Step 2: Verify at least one recommendation is explicitly refused or sequenced on stage grounds.
- Step 3: Verify the audit's detail level matches the commissioned decision class.
- Step 4: Emit verdict + one-sentence justification.

Do not score: vocabulary used for stage labels, presence of stage-map diagram, number of stages discussed, exact page count (the band-match is what matters, not 7.0 vs 7.5 pages).

### MA-5 — Surfaces upstream problem when that's the real constraint, sequenced not parallel-tracked

**Outcome question (binary):**
When the binding constraint is upstream of marketing (PMF, ICP, positioning, product, pricing, sales motion), does the audit say so plainly — even though saying so means the audit's own recommendations get smaller? Would the reader finish thinking "the bottleneck isn't marketing" if that's what the evidence points at, AND are the audit's marketing recommendations SEQUENCED behind the upstream fix (explicitly deferred, paused, or scoped behind it) rather than parallel-tracked alongside it?

**Score 1 (yes)** — Where evidence in the audit suggests the constraint is upstream — low retention, low PMF-survey scores, ICP confusion, positioning–buyer-mental-model mismatch (Dunford-territory: "how would you describe what we do" responses cluster into 4+ different categories; win-loss interviews surface "we thought you did X" as a recurring loss reason), pricing-model misfit (value-metric mismatch, expansion <10% of new ARR), product activation gap (D7/D30 activation falling off, support-ticket density on activation path), sales-motion misalignment (MQL→SQL conversion sub-median, AE ramp >9 months, pipeline coverage >4×) — the audit names it directly AND sequences marketing recommendations behind the upstream fix. The audit is willing to recommend pausing demand-gen spend, deferring channel diversification, or running a PMF re-test / positioning re-anchor / pricing audit before scaling marketing. Triage sequence walked (retention/PMF → ICP/positioning → pricing → sales motion → marketing-internal), stopping at the first binding constraint with evidence.

Example A — SaaS Cluster B (do not optimize toward this): "Your monthly churn is 6.4%; LTV at this churn rate means CAC payback cannot work below an ACV 4× your current. The constraint is retention, not acquisition. Pause the SEO investment and the paid-LinkedIn pilot; the marketing budget should fund three Wynter-style messaging tests to diagnose whether the issue is positioning or product fit. Once churn closes to <3.5%, re-evaluate SEO investment in Q3."

Example B — DTC / consumer (do not optimize toward this): "Your 11% 90-day repeat-purchase rate against the DTC-apparel 28% median means contribution margin at current Meta CAC ($42) cannot work — first-purchase margin is $58, repeat-purchases at this rate barely double it. The constraint is product-fit (returns data shows 38% sizing-driven), not channel mix. Pause the TikTok Shop expansion and the influencer pilot; reallocate to the sizing-redesign and post-purchase fit-survey work for 90 days. Re-evaluate paid expansion after Day 90 cohort retention reads."

Example C — Healthcare / local services (do not optimize toward this): "Your dominant constraint is reputation and capacity, not lead volume — Meta Ads spend on Botox at $4k/mo cannot pay back at your 4.2 GBP rating and 71% capacity. Pause the Meta spend; reallocate to GBP review-response system and RealSelf profile completion for 60 days. Re-evaluate paid Meta after GBP rating closes to 4.5 and capacity utilization hits 85%. Marketing budget should fund the reputation work directly."

**Score 0 (no)** — At least one of: (a) audit always recommends more marketing despite evidence pointing upstream; (b) upstream classes named but treated as out-of-scope when evidence engages them; (c) upstream section slot-filled with no diagnostic conviction (generic mention without engaging the specific evidence — mechanical rotation through PMF/ICP/pricing); (d) upstream constraint named but marketing recommendations PARALLEL-TRACKED rather than sequenced behind the upstream fix (the Goodhart-resistant slot-fill form: founder reads, defaults to concrete marketing actions because those aren't deferred); (e) invented-signals failure — missing data papered over with fabricated specifics, provider-blocked lenses presented as honest findings rather than honest gaps. `gap_flagged` rubrics from per-agent rubric_coverage maps must surface in `gap_report.md`; Phase-0 nulls and provider-blocked lenses are findings, not synthesis material. Audits with no "the bottleneck is upstream of marketing" branch by default — implying marketing is always the answer — score 0.

**Score 0.5 (unknown)** — Audit engages upstream evidence but the artifact lacks enough detail to determine whether the upstream naming is supported, OR the sequencing of marketing recommendations behind the upstream fix is partial (some sequenced, some parallel). Emit 0.5 + "unknown" + one sentence on what's missing.

**Required CoT:**
- Step 1: Identify upstream signals present in the audit's evidence (retention cohorts, PMF-survey scores, ICP / positioning divergence, pricing-model mismatch, product activation gap, sales-motion friction).
- Step 2: Determine whether the audit (i) confirms marketing IS the constraint with evidence on the merits, OR (ii) names an upstream constraint AND sequences marketing behind it.
- Step 3: If (ii), verify the sequencing is real — marketing recommendations explicitly deferred, paused, or scoped behind the upstream fix, NOT parallel-tracked alongside it.
- Step 4: Emit verdict + one-sentence justification.

Do not score: number of upstream classes discussed, presence of "upstream constraints" section header, length of the upstream discussion, depth of upstream remediation guidance (audit names the constraint; audit does not need to solve it — that's product's / pricing's / sales's job).

---

## 5. Shared judge-prompt wrapper

```
You are scoring a marketing audit + roadmap. The artifact's
decision_shape is provided in source_data and is one of:
  A — Personnel verdict (3–7 page exec memo; CEO/board reader;
      attribution-sieve evidence; 1–3 week horizon; binary
      verdict + named off-ramps).
  B — Operational reallocation (5–10 page channel scorecard +
      reallocation; founder-CMO or head-of-growth reader;
      unit-economic evidence; 2–6 week horizon; 1–3 Day-30
      experiments with named owner/budget/timeline/metric).
  C — Strategic reset (15–25 page positioning teardown + PMF
      survey + ICP analysis + 30/60/90 plan; founder +
      incoming-CMO readers; customer-research-and-competitive-
      alternatives evidence; 4–13 week horizon; named
      foundational bets with off-ramps).

The reader (cluster-appropriate) is smart, time-poor, runway-
aware, and skeptical — they recognise generic "best-practices"
slot-fills. They will commit to the decision-shape-appropriate
next action based on this audit.

Evidence sources vary by vertical and stage — cohort retention
and CAC payback in B2B SaaS; contribution margin per cohort
and repeat-purchase in DTC; review velocity and capacity
utilization in local healthcare; win-rate and referral-source
mix in services; liquidity and side-specific retention in
marketplaces. Do not penalize evidence sources unfamiliar to a
SaaS reader; do penalize sources categorically wrong for the
company's vertical (e.g., "trial-to-paid" for a brand with no
trial; "MQL nurture" for a derm practice).

Score each criterion independently with 0, 0.5, or 1 plus a
one-sentence rationale following the per-criterion CoT steps.
Do not blend criteria. Do not infer criteria not stated. If a
criterion's condition is ambiguous from the artifact alone,
emit 0.5 + "unknown" + one sentence on what would have to be
present to commit to 1.

Test whether the audit would actually change what the reader
commits to next — not whether it follows a specific template,
names named frameworks, or covers all conventional dimensions.

Voice discipline applies across all three clusters: prose has
the voice quality of a customer-facing $1K-$15K agency artifact.
Voice is consistent across sections (one author, not five). Em-
dash density is restrained. Headings are parallel; no section-
level voice drift. The audit is a sales artifact, not a planning
document — score against that posture, not against the polish
of an internal-strategy memo.

Emit per-criterion JSON:
{"criterion_id": "MA-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 6. Goodhart-resistance verification

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **MA-1**: "Templated 'binding constraint' assertion at top" doesn't pass — must have 2+ independent named evidence sources behind the diagnosis. Confabulated metric used as evidence is caught upstream by `structural_gate` source-corpus numerical match; if it slips through, MA-1's CoT Step 2 evidence-traceability check fails it.
- **MA-2**: "Templated owner/budget/deadline boilerplate" doesn't pass — must match the decision-class action shape (binary-verdict-plus-off-ramps for A, action+owner+budget+timeline+metric for B, 30/60/90-with-off-ramps for C) AND tie to a specific current baseline metric (B) or named attribution evidence (A) or named cohort-by-segment data (C).
- **MA-3**: "Activity-shaped recommendations with no revenue chain" doesn't pass — must specify the metric and the chain. Vanity-metric headlines (impressions / reach / followers / raw pageviews) score 0 unless paired with downstream conversion-metric chain.
- **MA-4**: "Mechanical stage label without recommendations actually tailored to it" doesn't pass — at least one explicit refusal or sequencing required + detail level must match the commissioned decision class. Cluster-format-mismatch (25-page reposition served as fire-CMO memo, or vice versa) scores 0 even if every other criterion scores 1.
- **MA-5**: "Marketing is the constraint" default doesn't pass — must engage upstream evidence on the merits. **AND "parallel-tracked NOT sequenced" Goodhart move** explicitly scored 0: an audit that names the upstream constraint AND keeps the marketing recommendations parallel — so the founder defaults to the concrete marketing actions — fails the sequencing test in CoT Step 3. This is the Goodhart-resistant slot-fill form that the v0 spec did not catch.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0.

---

## 7. Verification — conforms to design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (3 vertical examples per criterion: SaaS + DTC/consumer + healthcare/services) ✓
- §5 criterion count: **5 (at ceiling, no breach)**. Research predicted MA-6 "Diagnosis survives blame-attribution check" — absorbed into MA-5 via the explicit sequencing-not-parallel requirement and the marketing-misdiagnosis bias call-out in §3d. Adding a 6th criterion to test format would re-introduce feature-checking (routing belongs at workflow level via `decision_shape`).
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3–4 steps each, evidence before score) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §10 input sanitization: structural_gate strips non-printable + prompt-injection markers ✓ (operationalised in §8)
- §11 Goodhart-resistance verification ✓ (§6 above + "parallel-tracked NOT sequenced" move on MA-5)
- §13 specimen criterion template followed ✓

Length per criterion ≈ 250–280 words (above the 150-word target due to 3 vertical examples + per-cluster anchor specificity on MA-2 and MA-4; absorbable per the CI v3.3 precedent on CI-1 / CI-2 / CI-3). Total spec body ≈ 4800 words.

---

## 8. Open questions

Reader / Artifact-shape / Success / Failure / 5 Criteria are LOCKED at v1. Remaining:

1. **Cluster A has ZERO existing fixture coverage (urgent before propagation).** Build 2–3 portfolio-company fire-CMO archetype fixtures at $5M–$30M ARR (Bessemer / USV portfolio shape) before locking Cluster A routing via empirical redundancy check. Without these fixtures, MA-2's per-cluster anchor for Cluster A is theoretically motivated but empirically unvalidated. Risk: the binary-verdict-plus-off-ramps anchor may need tightening (or loosening) when concrete Cluster A audits exist to evaluate.

2. **Calibration set must be weighted toward upstream-evidence fixtures.** Per the upstream-diagnostic research §7 redundancy-boundary argument, **at least 30% of the 100-fixture calibration set** must have upstream-evidence shape (low retention + clear PMF/positioning/pricing/product/sales-motion signal). Without this weighting, MA-1 ↔ MA-5 correlation will exceed the design-guide §5 0.7 threshold (audits that locate stage tend to also name the constraint) and the redundancy check drops MA-5 — losing the only criterion specifically targeting marketing-misdiagnosis bias.

3. **B2C / DTC may need a 4th cluster.** The current 3-cluster taxonomy (A Personnel / B Operational / C Strategic) is research-grounded against B2B SaaS practitioner conventions. DTC e-commerce operations differ structurally — Common Thread Collective / Tinuiti / Buy Box methodology converges on a DTC-Operational pattern that has its own metric set (contribution margin per cohort, repeat-purchase at 30/60/90, channel CAC + incrementality post-iOS-14.5) and channel space (Meta + TikTok + Google Shopping + influencer + email/SMS + retail/wholesale). **Defer the 4th-cluster decision** to first 5 DTC fixtures landing; if those fixtures consistently fail MA-2's Cluster B anchor on metric-vertical-appropriateness, fork DTC-Operational off Cluster B.

4. **Quarterly-memo subcluster may need splitting from Cluster B.** Decision 6 in the decision-format-mapping research (quarterly strategic memo: 4–8 page state-of-marketing memo with board ask) sits at the edge of Cluster B (operational) and Cluster C (strategic). When the recommendation is "continue + sharpen + escalate one ask to the board," it's Cluster B; when the recommendation slides into "reposition / restructure / pivot," it's Cluster C. **Defer the B/B-prime split** until 5+ quarterly-memo fixtures exist and consistently behave one way or the other.

5. **Personnel-verdict ethics surface (Cluster A) needs explicit hedging.** A judge that rewards Cluster A audits must navigate the line between rigorous performance attribution and reputational damage to the assessed individual. The Cluster A optimal-output spec MUST include a hedge: the audit assesses the role / outcome / attribution against the strategic context, NOT the person's character or capability in absolute terms. The score-1 example for Cluster A in MA-2 above intentionally frames around "Pat owned three calls peer-stage CMOs would have decided differently" (decision-attribution), not "Pat is a bad CMO" (character-attribution). Surface to JR for sign-off before locking Cluster A criteria.

6. **MA-1 ↔ MA-4 pairwise redundancy check (run before propagation).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 5 criteria × 3 panel models = ~75 calls (~$30). Most-likely-to-merge pair: MA-1 (binding constraint named with 2 evidence sources) ↔ MA-4 (stage located with observable anchor + recommendation refused on stage grounds). Both criteria reward "diagnosis with evidence and locatability"; they may collapse on the calibration set. Secondary watch: MA-3 (revenue chain) ↔ MA-5 (upstream constraint sequenced) — both reward layer-appropriate analysis, but the upstream-evidence-weighted calibration set should keep them separable.

7. **`structural_gate` expansion (before spec ships to v006/workflows).** Add 7 anti-hallucination + shape-conformance checks. Per OpenRubrics design principle (Hard Rules → `structural_gate`, Principles → judge), deterministic verification lives here because the judge cannot deterministically check URL resolution, quote provenance, entity existence, or numerical match.

   **The 7 checks (each defends a documented LLM failure rate or shape-drift Goodhart surface):**
   - **Metric-citation grep.** Any number formatted as `\d+(\.\d+)?%`, `\$\d`, `\d+x`, `\d+ months`, or `\d+:\d+ ratio` in the audit body must be followed within 200 chars by an inline citation (URL, "(source: ...)", or footnote marker). Bare numbers fail. Defends Q1 financial-metric confabulation (FAITH 17–46% rate).
   - **Source-corpus numerical match (±5% tolerance).** For each cited metric with a source attribution, verify the exact number (with ±5% rounding tolerance) appears in the named source document. Defends Q1 financial-metric confabulation at the source-substitution sub-shape.
   - **Channel-claim source check.** Any channel-performance claim ("X is your dominant channel," "Y is working," "Z has stalled," "they ran a six-figure paid-LinkedIn pilot") must cite a specific source artifact (analytics screenshot, Gong call transcript ID, campaign report, ad-platform export). Bare channel claims fail. Defends Q2 channel-claim fabrication.
   - **Competitor URL HEAD-check.** Any cited competitor URL must resolve (HTTP 200/301/302). Any competitor named without a URL or supporting source fails. Defends Q3 competitor-data confabulation (HalluLens 14–95%).
   - **Entity-existence lookup on competitors (Wikidata / Crunchbase / SEC EDGAR / OpenCorporates).** Defends Q3 at the "Partial Attribute Corruption" sub-shape (real competitor + fabricated attribute).
   - **Stage-applicability denylist.** Maintain `docs/rubrics/ma-stage-denylist.yaml` mapping (ARR-band × vertical × sales-motion) → denied tactics list. Reject audits that hit the denylist (e.g., ABM tooling for sub-$5M ARR; B2C influencer playbook for B2B SaaS; "trial-to-paid optimization" for a no-trial brand). Defends Q5 wrong-stage tactic at surface level; MA-4 handles the subtler cases semantically.
   - **Forbidden-formulation grep.** "Industry-standard," "typical SaaS," "reportedly," "according to industry sources," "we see this often" without inline citation = structural failure. Banned-phrase list extended with AI-slop tells (em-dash density, "let me explain why," "moreover," "furthermore") and framework-name-without-supporting-analysis tells. Defends both Q1/Q2 confabulation surfaces and the "framework-citation as substitute for analysis" Goodhart mode.
   - **`MA_BANNED_PHRASES` corporate-jargon blocklist (marketing-audit-specific, JR-iterated, ADDITIVE to the AI-slop list above — NOT a replacement).** Any of the following 12 phrases appearing anywhere in the audit body = structural failure: "in today's fast-paced world," "in the ever-evolving landscape," "leverage synergies," "drive impact," "unlock value," "best practices," "key takeaways," "deep dive," "moving forward," "going forward," "circle back," "low-hanging fruit." These target the corporate-jargon-as-AI-tell surface that drops the deliverable's customer-facing-$1K-$15K-agency-artifact quality bar (parallels MA-6 voice discipline in the wrapper).

   **Shape-conformance checks (enforce §1.5 LOCKED):**
   - Word-count band per cluster: 800–2,000 for A, 2,000–4,500 for B, 4,500–9,000 for C.
   - Cluster B 5-section findings spine presence check (verdict / stage-diagnostic / current-state / upstream-vs-marketing / 30-60-90).
   - Cluster A binary-verdict-in-first-page check.
   - Cluster C 30/60/90 milestone presence + off-ramp check.
   - Top-3-recommendations vs full-list separation in Cluster B section 5.
   - Stage anchor present (vertical-appropriate observable anchor).
   - Upstream-vs-marketing section present and reasoned (not skipped).
   - **9-section deliverable-shell presence check** (live-code-inherited, agency-deliverable-substrate): `findability` / `narrative` / `acquisition` / `experience` / `competitive` / `monitoring` / `geo` (display: AI Visibility) / `state_of_business` / `martech_compliance`. The Cluster B 5-section findings spine is the FINDINGS structure INSIDE the 9-section deliverable shell; both structures coexist (the spine organizes the strategic argument; the shell organizes the deliverable surface area the agency engagement covers). When `proposal.md` is produced, structural_gate enforces the 3 capability-registry tier headers in fixed order: `fix_it`, `build_it`, `run_it`.
   - **`lens_id` + `evidence_url` mechanical traceability (live-code-inherited).** Every claim cites a `lens_id` AND ≥1 `evidence_url`; numbers are source-attributed (no naked stats); `ParentFinding.addresses_rubrics` arrays match the lens IDs cited in evidence. Persists as long as the rubric YAML / lens_id substrate persists in workflow.

8. **First-cohort overfitting watch.** v1 broadened §1 Reader / §1.5 form-factor / per-criterion examples to reduce SaaS-only anchoring, but the underlying research (vertical-conventions, artifact-taxonomy, decision-format-mapping, upstream-diagnostic) was still done predominantly against B2B SaaS verticals with legal-services (DWF) and healthcare (Klinika) as the legible non-SaaS anchors. Monitor: when client #5+ onboards (DTC e-commerce, fintech, hospitality, regulated finance, marketplaces, dev-tools), check whether the substitute-readers + §1.5 form factors + criterion anchors generalise OR whether per-vertical adjustment is needed. **Re-validation trigger:** any fixture from a vertical not in {B2B SaaS, AI-lab, legal-services, healthcare-aesthetic} should prompt a quick re-validation pass on the affected criteria — especially MA-1's 2-evidence-source requirement (vertical-appropriate evidence substrate must be engaged) and MA-3's revenue-mechanism chain (vertical-appropriate metric must be cited).

9. **Propagation to other 6 lanes after MA v1 validates.** GEO → MON → SB → X → LI → site_engine. Each lane gets its own Path-A iteration + (optionally) lane-customized deep-research pattern — NOT a mechanical CI/MA template repeat. The CI and MA deep-research question sets weren't equally relevant to all lanes (CI's first-cohort-overfit problem is sharper than MA's per-fixture metric-confabulation problem); per-lane question scoping needed.

10. **Live-code surgical restoration applied (2026-05-18, OPTION C-RESTRICTED).** v1 originally lost 7 of 8 JR-iterated live-code criteria during research-driven re-architecture. MA is a SHIPPED production lane (DWF, Perplexity, Anthropic clients); live code architecture (`phase0_meta.json`, `capability_registry`, `lens_id`, `severity_anchors`, `proposal.md` 3-tier headers, 9-section deliverable shell) is workflow substrate that MUST persist alongside v1's research-driven Cluster A/B/C decision-shape routing. The 9 folds applied surgically — no new criteria added (5-criterion ceiling preserved); no §4 architectural restructuring:
    - F1 — `MA_BANNED_PHRASES` 12-phrase corporate-jargon blocklist restored verbatim in §8 structural_gate (ADDITIVE to v1's existing AI-slop list, not a substitute).
    - F2 — Phase-0 9-meta-frames framing folded into MA-4 score-1 anchor (stage diagnostic incorporates `phase0_meta.json` measurements; nulls surface as findings).
    - F3 — `capability_registry` tier-mapping (`fix_it`/`build_it`/`run_it`) folded into MA-2 score-1 anchor for Cluster B; `proposal.md` 3-tier-header structural enforcement preserved in §8.
    - F4 — Severity-calibration ("not a sea of 3's" anti-inflation + rollup rule + `severity_anchors` YAML anchoring) folded into MA-1 score-0 anchor.
    - F5 — MA-6 voice quality / $1K-$15K agency artifact discipline folded into §5 SHARED JUDGE-PROMPT WRAPPER (parallels MON's editorial-restraint wrapper restoration).
    - F6 — Gap honesty / "invented signals" anti-pattern (`gap_flagged` → `gap_report.md`; provider-blocked-lenses-as-honest-gaps) folded into MA-5 score-0 anchor.
    - F7 — Engagement-fit / $15K+ pitching credibility / audit-as-sales-artifact framing folded into MA-2 score-1 anchor for Cluster B (paired with F3 tier-mapping).
    - F8 — 9-section deliverable-shell structural_gate requirement preserved (findability / narrative / acquisition / experience / competitive / monitoring / geo / state_of_business / martech_compliance), with explicit coexistence clarification: Cluster B 5-section FINDINGS spine lives INSIDE the 9-section deliverable shell.
    - F9 — `lens_id` + `evidence_url` mechanical traceability (`ParentFinding.addresses_rubrics` matches lens IDs cited) preserved in §8 structural_gate.
    **Both architectures now coexist intentionally**: v1 research-driven Cluster A/B/C decision-shape routing organizes the audit's STRATEGIC ARGUMENT and DECISION-CLASS ACTION shape (the judge's outcome questions); live agency-deliverable substrate (`phase0_meta.json`, `capability_registry`, `lens_id`/`severity_anchors`/`gap_flagged`, 9 sections, `proposal.md` 3 tier headers) organizes the DELIVERABLE SURFACE AREA and MECHANICAL TRACEABILITY (the workflow's structural_gate + criterion score-1/score-0 anchors). The Cluster routing tells the audit WHAT decision the reader is making; the deliverable substrate tells the audit WHAT SECTIONS / EVIDENCE / TIER MAPPINGS the agency engagement covers. Neither replaces the other.
