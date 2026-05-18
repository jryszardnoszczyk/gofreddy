---
date: 2026-05-18
type: judge-design Step 2 — geo domain-deepening research
status: living document; feeds the v1 GEO judge spec
parent: docs/handoffs/2026-05-18-judge-design-step1-geo.md
companions:
  - docs/research/2026-05-15-judges-domain-geo.md (do not restate — this deepens)
  - docs/rubrics/judge-design-guide.md
axis: dual-audience tension (human researcher vs AI engine) + Aggarwal domain variance
constraints:
  - outcome-questions, not feature-checks
  - reference-free, no framework-name embedding in criterion prose
  - behavioral binary anchors
  - first-cohort overfitting watch (≥3 divergent verticals)
---

# GEO — Dual-Audience Tension and Aggarwal-Method-by-Domain

## TL;DR

GEO content serves two readers whose preferences are NOT redundant and NOT identical. The AI engine rewards extraction-friendly surfaces (front-loaded declarative answer, dense statistic/quote/citation injection, self-contained 40-75-word passages, format-intent match). The human researcher arriving via that engine rewards proof of expertise (depth, named experience, traceable evidence chain, acknowledged trade-offs, voice that isn't pure declarative-document register). The two preferences overlap on roughly half the GEO levers — verifiable evidence, entity stability, freshness, third-party validation — and CONFLICT on three: (1) summary density vs. depth-of-proof, (2) unambiguous answer vs. nuanced trade-off discussion, (3) declarative-document register vs. human voice / story / metaphor.

Aggarwal KDD 2024's load-bearing finding is NOT that "stats + quotes + citations win." That's true but it's the summary headline. The load-bearing finding is that **the optimal-method MIX shifts by domain**: Statistics Addition dominates Law & Government and factual / Opinion domains; Quotation Addition dominates People & Society, Explanation, and History; Fluency dominates Health and Business. Single-formula GEO is wrong by construction. 2025-2026 follow-up work (Schulte et al. "Don't Measure Once" 2604.07585, Bagga et al. E-GEO 2511.20867, Profound / Ahrefs citation-pattern studies) confirms the variance axis while adding two new findings: visibility is a distribution not a point (must be measured n>1), and within a single homogeneous domain (e-commerce product listings) a stable domain-agnostic optimization pattern DOES emerge. The two findings reconcile: Aggarwal's variance was across very-heterogeneous domains (Law vs Health vs Opinion); Bagga's stability was within one. The judge has to operate across heterogeneity, so domain-sensitivity is load-bearing.

For the v1 GEO judge: do NOT add a separate "human-first AEO" vs "AI-first AEO" criterion (creates a new feature-checking surface). Instead, every criterion's score-1 anchor must require BOTH the AI-engine-extractable form AND a human-trust-survivable substance. If a passage is extractable but a human would not trust the claim (vendor-vacuum stat without source), score 0. If a passage is trustworthy but not extractable (depth buried below the fold, no canonical entity name, no standalone passage structure), score 0. The dual-audience requirement is an AND, not a weighted blend or a client-intent toggle.

---

## Key questions answered

**Q1. When do human and AI-engine interests conflict?** Three measurable conflicts: summary density (AI wants 40-75-word extractable passages with one claim each; humans want depth that lets them assess credibility); unambiguous answers (AI rewards a single declarative claim; humans reward nuanced trade-off discussion that survives the "but actually" follow-up); and declarative-document register (AI penalizes query-echo and conversational register per Volpini; humans tire of pure declarative prose without voice, story, or metaphor). The conflicts are real but bounded — they live on roughly one-third of the GEO levers, not the whole surface.

**Q2. Aggarwal's domain-variance finding restated.** The KDD 2024 paper does NOT find a universal optimization recipe. It finds that the +30-40% visibility lifts from Statistics Addition, Quotation Addition, and Cite Sources are domain-conditional. Statistics Addition wins biggest in Law & Government and Opinion domains; Quotation Addition wins biggest in People & Society, Explanation, and History; Fluency Optimization wins biggest in Health and Business (where authority-tone signals matter more than raw evidence density). This is THE load-bearing finding for cross-vertical judges. 2025-2026 follow-up (E-GEO Bagga et al. 2511.20867) finds domain-agnostic stability WITHIN one narrow domain (e-commerce product listings) but does not contradict Aggarwal; e-commerce-listing surface is one node in the Aggarwal domain-space, not a counter-example to the variance finding.

**Q3. How does the judge score content that is optimal for human but sub-optimal for AI engine, or vice versa?** Neither weighted blend nor dominant-audience toggle. The judge requires AND-conjunction at the criterion level: each criterion's score-1 anchor names the AI-engine-extractable form AND the human-trust-survivable substance. A passage scoring 1 must satisfy both. Vendor-vacuum stats fail the human side; floating-pronoun depth fails the AI side; both score 0. The reason for AND-over-weighted-blend: weighted blends are tunable, which means under selection pressure the workflow learns to maximize the cheaper side and pay only the floor on the expensive side. AND-conjunction is Goodhart-resistant — both sides must hold or the criterion fails.

**Q4. What measurable signals distinguish human-first AEO, AI-first AEO, and balanced?** AI-first AEO is identifiable by surface-marker density without substantive proof: citation count high but sources sibling-domain; stats present but unsourced; declarative-register prose without examples / metaphors / named experience; "last updated" date current-year but body content stale; entity name repeated 12+ times per section with no canonical disambiguation. Human-first AEO (essentially: pre-GEO content-marketing prose) is identifiable by buried answer, query-echo lead, prose where a table would do, depth without passage self-containment, brand storytelling before claim. Balanced GEO is identifiable by the dual conjunction at every level: front-loaded declarative answer that is ALSO a substantive claim a domain expert would defend; statistics that are ALSO sourced; passages that ALSO carry voice; trade-offs that ALSO compress to extractable form.

**Q5. The over-optimization failure mode.** Content optimizes for AI engines so hard it becomes useless to humans. Measurable shape: AI-citation rate stays high or rises, but human bounce rate rises 18-25% over baseline, time-on-page drops by 30%+, conversion-from-AI-traffic drops despite the AI-traffic baseline 5x higher than organic. This is the Goodhart-collapse mode for the GEO lane specifically. Detection: track AI-citation rate AND human-engagement metrics; the divergence between them is the early-warning signal. (For the judge: not directly observable, but the score-0 anchors must catch the surface signatures — slot-filled citations, citation stuffing, surface-marker compliance without substantive claim.)

---

## Research synthesis

### 1. The dual-audience is a real architectural feature, not a framing flourish

The GEO lane is alone among the autoresearch lanes in serving two distinct primary readers. Competitive intelligence serves one (the founder-CEO / VP); monitoring serves one (the comms director); marketing audit serves one (the marketing leader). GEO serves two simultaneously, and they consume the artifact differently.

The AI engine consumes the artifact as **passage candidates for a retrieval-and-citation pipeline**. Its operations: lexical-candidate-generation, dense-retrieval, reranking, synthesis-with-citation (Volpini's architectural breakdown). It cares about: passage standalone-coherence (40-75 words), declarative-document register (because asymmetric retrievers project documents and queries into different vector spaces), citation-worthiness signals (named source, dated claim, third-party validation), entity stability (so the engine can confidently associate the page with one canonical entity across query variants), and format-intent fit (table for comparison queries, ordered steps for how-to, definition + structured detail for what-is).

The human researcher consumes the artifact as **proof that the source is worth trusting and the action is worth taking**. Their operations: 40-second skim of the answer the AI engine surfaced + a check on whether the answer holds under scrutiny + a decision to click through, copy, file, or act. They care about: depth that survives a 90-second look (does the claim hold up?), traceable evidence chain (could I defend this to a colleague?), trade-off acknowledgment (real strategy costs something; if the page hides the cost, the page is marketing not reference), and voice + named experience (which marks expertise versus generic AI-assisted summary).

The conversion data confirms the dual-reader posture is load-bearing, not theoretical. AI-referred visitors convert at 14.2% vs Google organic 2.8% (a 5x lift), spend 48% longer per visit, browse 13% more pages, and show 23% lower bounce rates (Adobe / Ahrefs / RankScience studies, Q1-Q2 2026). The conversion gap exists because AI users arrived with intent already refined through engine-mediated research — they are NOT casual browsers. This means the human-reader side of GEO is HIGH-stakes, not low-stakes. A page that wins AI citation but loses human trust converts at a fraction of the achievable rate. The judge cannot afford to optimize one side at the expense of the other.

### 2. Where the two preferences align (roughly half the GEO surface)

The Aggarwal +30-40% levers (Statistics Addition, Quotation Addition, Cite Sources) all reward AI-citability AND human-trust simultaneously. A statistic with a named source and date is more extractable by an AI engine AND more credible to a human researcher than the same claim without attribution. Direct quotes from a named credible third party (analyst, journalist, named customer with role + employer) earn AI-citation lift AND survive the human "is this just marketing?" check.

Entity stability is dual-aligned: canonical brand naming and consistent semantic triples help knowledge-graph ingestion for AI engines AND signal professionalism / coherent positioning to humans. Inconsistent naming reads as sloppy to both audiences.

Freshness signals are dual-aligned within bounds: a visible publication date in the last 12-18 months helps Perplexity's 70%-recent-source preference AND helps humans confirm the page reflects current reality. The bound is that freshness-as-a-stamp ("Last updated 2026-05-15" with no current-year body content) signals AI-optimization-theater to humans even though it nominally passes the AI engine's date check.

Third-party validation is dual-aligned: AI engines weight off-domain mentions (Ahrefs r=0.664 brand-mention correlation vs r=0.218 backlinks) AND humans treat the presence of off-domain validation as the difference between reference and marketing.

These dual-aligned levers cover roughly half the GEO surface. The judge can score them without worrying about audience-conflict.

### 3. Where the two preferences conflict (the three load-bearing tensions)

**Tension 1: Summary density vs depth-of-proof.** AI engines reward the 40-75-word passage that compresses one substantive claim into extractable form (Profound's 3.1x citation multiplier on 40-75-word passages, 4.2x on tabular comparison content). Humans, particularly in regulated verticals like legal and healthcare, reward the depth that lets them assess whether the claim is credible — case-fact patterns, methodology details, clinical evidence chains, the careful "in patients meeting X criteria, treatment Y showed Z effect" qualifications that legal and healthcare audiences are trained to look for. A page that ships only 40-75-word passages reads as marketing-bait to a clinician or attorney; a page that ships only the full depth fails the AI-engine extraction layer.

The resolution that works in practice (per Stripe.com developer pages, Mayo Clinic / Cleveland Clinic content, Anthropic research pages) is to nest BOTH: each substantive passage is extractable as a standalone 40-75-word claim, AND a structured deeper section directly below sustains the claim with the proof a domain expert needs. The AI engine extracts the top; the human-clicking-through reads the bottom. The judge has to check both layers exist; an artifact with only the top layer fails the human-trust side; an artifact with only the bottom layer fails the AI-engine side.

**Tension 2: Unambiguous answer vs nuanced trade-off discussion.** AI engines reward content that gives a single declarative answer (Perplexity's 90/100-words BLUF finding; ChatGPT extracts the top-passage as the answer). Humans, especially sophisticated B2B buyers and regulated-vertical decision-makers, reward content that engages the trade-offs they actually face. A page that says "Freddy is the best content engine for regulated B2B" answers cleanly for the AI engine but reads as vendor-puffery to the buyer who is comparing real alternatives. A page that says "Freddy is one of three viable approaches for regulated B2B content, optimal when [specific conditions]; if [other conditions] hold, Acme or in-house teams may fit better" satisfies the human's trade-off literacy but fragments the AI engine's extractable claim.

The resolution that works: declarative claim at the top with named conditions / domain ("Freddy is an AI-native content engine for regulated B2B clients in legal, financial, and medical verticals"); the conditional / comparative depth in a clearly-marked section below, where humans look for it and AI engines treat it as supporting context. The conditional surface lives in extractable form too — "When Freddy fits best: [3 conditions]. When alternatives may fit better: [2 conditions]" — but in a section the AI engine will not extract as the top-line answer. Critically, the unambiguous top-line and the trade-off depth must agree; if they contradict, both readers lose trust.

**Tension 3: Declarative-document register vs human voice and named experience.** AI engines penalize query-echo register and conversational opening register; they reward declarative-document register that reads like a reference (Volpini's asymmetric-retrieval argument). Humans tire of pure declarative-document register; they reward voice, story, metaphor, named human experience. A page written entirely in declarative-document register passes the AI engine's retrieval-document classifier but reads as generic AI-assisted summary to a human — exactly the failure mode the 2025-2026 "AI-content-hurts-SEO" studies measure (18% higher bounce rate on AI content without human editing).

The resolution that works in practice: declarative-document register at the top (the 40-75-word extracted passages, the definitions, the structured comparisons), human voice in the middle (named author or expert quote, specific worked example, story or case study with attribution), declarative-document register at the bottom (the structured detail, the FAQs, the third-party citation block). The voice is bracketed inside the declarative surface, not opposed to it. Both Mayo Clinic explainers and Stripe developer pages follow this pattern — declarative entity-definition lead, named clinician or named engineer in the middle, structured reference detail at the bottom.

### 4. Aggarwal's domain-variance finding — deepened

The headline summary of Aggarwal et al. (arxiv 2311.09735, KDD 2024) is "Statistics Addition, Quotation Addition, and Cite Sources each lift visibility by 30-40%." This is correct but misleading as a basis for cross-vertical judge design. The paper's §6.3 (Domain-Specific Analysis) reports method-effectiveness per domain class, and the variance is large.

**Reported domain-by-method ranking (Aggarwal §6.3, restated from the paper):**

- Statistics Addition wins biggest in **Law & Government** and **Opinion** domains. The pattern fits: legal and opinion content is contested, and the addition of a defensible numeric anchor materially changes whether the AI engine treats the source as authoritative.
- Quotation Addition wins biggest in **People & Society, Explanation, and History** domains. The pattern fits: these domains lean on named human voices for authority (historian, sociologist, named expert), and direct attribution is the strongest authority signal.
- Fluency Optimization wins biggest in **Health and Business** domains. The pattern fits more subtly: health and business content is already evidence-dense (clinical trials, market data); the marginal lift from adding more evidence is small. The lift comes from how well the existing evidence reads — Fluency Optimization makes domain-expert content accessible to the AI engine's retrieval layer.

**Why this is load-bearing for the autoresearch judge:** the GEO lane serves clients across all of these domain classes simultaneously. First-cohort fixtures include legal (DWF — Law & Government), AI-lab tech (Anthropic, Perplexity — likely Computers & Electronics in Aggarwal's taxonomy, or Business depending on framing), and aesthetic dermatology (Klinika — Health). A judge that bakes Statistics-Addition-bias into score-1 anchors will mis-score Health-domain content (where Fluency dominates) and over-score Law-domain content (where Statistics dominates). A judge that bakes Quotation-Addition-bias into anchors will mis-score Business content (where Fluency dominates).

The right response is NOT to add a per-vertical criterion (creates new feature-check surface and domain overfitting). The right response is to write the evidence-density criterion (GEO-2 in the current draft) at a level of abstraction that admits ALL three Aggarwal levers as evidence: "verifiable evidence — quantitative figures with sources, direct quotations from credible third parties, inline citations to first-party data or external authority." The judge then scores presence of dual-aligned evidence, agnostic to which Aggarwal lever the artifact picked. The vertical-fit comes from the workflow's mutation choosing the appropriate evidence type for the domain, not from the judge encoding domain-preference.

**2025-2026 follow-up — confirms and bounds the variance finding:**

Schulte et al. "Don't Measure Once: Measuring Visibility in AI Search (GEO)" (arxiv 2604.07585, April 2026) confirms Aggarwal's variance axis empirically with a different framing. Their headline: AI-search visibility is a DISTRIBUTION across runs, prompts, and time — not a point estimate. The implication is that a single fixture run gives an unreliable visibility score; the judge sees one rendering and cannot itself measure visibility, but the variance finding reinforces why domain-specific optimization patterns matter: in high-variance domains, the marginal evidence lift has to be large enough to clear noise.

Bagga et al. "E-GEO: A Testbed for Generative Engine Optimization in E-Commerce" (arxiv 2511.20867, November 2025) finds the opposite of Aggarwal's variance: WITHIN the narrow domain of e-commerce product listings, a stable domain-agnostic optimization pattern emerges. The reconciliation is straightforward: Aggarwal's domain space spans heterogeneous query intents (Law vs Health vs Opinion vs History); Bagga's space is one node (product-listing content for shopping queries). The "universally effective" pattern Bagga reports is universal within that node, not across Aggarwal's nodes. For the autoresearch judge serving clients across legal / AI-lab / aesthetic-dermatology / B2B-SaaS / fintech verticals, the operating regime is Aggarwal's heterogeneity, not Bagga's homogeneity. Domain-variance is load-bearing.

Profound's 2025 10K-citation passage study and Ahrefs' 17M-citation freshness study layer onto this: the passage-as-unit-of-competition finding (40-75 words = 3.1x citation rate) and the freshness preference (70% of Perplexity-cited sources within 12-18 months) are domain-stable surface signals. The domain-VARYING dimension is the substantive evidence type (stats vs quotes vs fluency-driven authority) that fills the passage. Surface signals are universal; evidence-type-for-domain is conditional.

### 5. Scoring shape — the AND-conjunction at every criterion

The current v0 GEO spec (`docs/handoffs/2026-05-18-judge-design-step1-geo.md`) names the dual audience in §1 and §2 (Primary reader = human; Secondary reader = AI engine) and §3 (Success for both). The five criteria in §4 each have implicit dual-audience structure but the score-1 anchors don't always make the AND-conjunction explicit. v1 should tighten this.

**Specifically, each criterion's score-1 anchor must require both:**

- **GEO-1 (BLUF compliance):** the first 40-75 words must be (a) declarative-document register extractable by an AI engine AND (b) a substantive claim a domain expert in the target vertical would defend. "Freddy is the best content engine" passes the AI side, fails the human side. "Freddy is an AI-native content engine for regulated B2B clients in legal, financial, and medical verticals" passes both.
- **GEO-2 (evidence density):** evidence must be (a) extractable / inline-citable AND (b) off-domain verifiable. A stat with sibling-domain self-citation passes the surface count, fails the human-trust check. A stat with named third-party attribution + date passes both.
- **GEO-3 (passage self-containment):** passages must be (a) standalone-extractable AND (b) substantive enough that a human reading the standalone passage learns something. "Freddy ships content for regulated B2B" repeated three times passes mechanical self-containment, fails the human-substance check.
- **GEO-4 (entity stability + third-party validation):** entity (a) canonically named in retrieval-document register AND (b) externally validated by named off-domain sources. Logo wall without attribution passes the surface signal, fails the human-trust check.
- **GEO-5 (format-intent match + freshness):** format must (a) match likely query class for AI-engine extraction AND (b) carry substantive currency in body content. "Last updated YYYY-MM-DD" with no current-year body passes the surface date, fails the human check.

The AND-conjunction is the structural defense against AI-first-AEO Goodhart collapse. A workflow that learns to slot-fill the AI surface only (citation stuffing, schema-only optimization, date-stamping) cannot score 1 because the human-trust side fails. A workflow that learns to write deep human content only cannot score 1 because the AI-engine-extraction side fails. The workflow has to produce both, which means the dual-audience artifact is the only path to a high score.

### 6. The over-optimization failure mode

The empirical signature of GEO over-optimization (content optimized for AI engines to the point of harming human reception) is now measurable in 2025-2026 data:

- **AI-citation rate stays high or rises**, because the workflow has learned the surface markers.
- **Human bounce rate rises 18-25% over baseline** for AI-content-without-human-editing (multiple 2025-2026 SEO studies, summarized in Position.digital's 150+ AI SEO Statistics for 2026).
- **Time-on-page drops 30%+** as the human skim-bounces off generic declarative-document prose.
- **Conversion-from-AI-traffic drops** even as AI-traffic baseline rises, because the high-intent AI-referred visitor (14.2% conversion baseline) finds the page is not the depth they expected.

The Goodhart-collapse pattern is well-documented in the GEO-specific literature: pages that "look AEO-optimized" get de-ranked by AI engines within 1-2 indexing cycles (per Profound and Ahrefs Q1 2026 citation-pattern studies — the citation share from "obviously optimized" pages is declining as engines tune their authority signals).

The judge cannot directly observe bounce rate or conversion. The judge can catch the surface signatures of over-optimization: citation count high but sources sibling-domain; entity name repeated 12+ times per section without canonical disambiguation in the lead; "last updated" current-year on stale body content; declarative-document register without any human voice or named experience; passages extractable but substantively empty. Each of these is in scope for GEO-1 through GEO-5's score-0 anchors. The Goodhart-resistance pattern from §6 of the v0 spec must be tightened: each score-0 anchor must name the surface-marker-without-substance shape specifically, not just the absence of the surface marker.

### 7. Three-vertical example anchoring (first-cohort overfitting watch)

Per design guide §16 first-cohort-overfitting watch, the judge spec must be validated against ≥3 divergent verticals. The current v0 spec leans on regulated B2B examples (legal, healthcare, AI-lab). v1 should anchor each criterion's score-1 example with three concrete divergent-vertical illustrations. NOT to be quoted as criterion prose (anti-pattern: framework-name-embedding equivalent), but to be used as fixture-validation anchors:

- **Legal (DWF-style):** "Slaughter & May's RES practice is one of three UK Tier-1 RES practices specializing in international tax structuring for FTSE-100 clients; Pinsent Masons and Linklaters are the comparable alternatives." Passes AI-extraction (declarative entity + category + comparison). Passes human-trust (named comparables + verifiable specifics).
- **AI-lab tech (Anthropic / Perplexity-style):** "Claude 4.7 is Anthropic's frontier model for agentic tool use; primary alternatives are GPT-5.5 (OpenAI), Gemini 3 Pro (Google), and DeepSeek V3 for cost-sensitive deployments." Passes both sides.
- **Aesthetic dermatology (Klinika-style):** "Klinika Melitus is a Warsaw aesthetic-dermatology practice specializing in non-surgical anti-aging treatment for women aged 35-55; clinically directed by Dr. Maria Noszczyk, board-certified dermatologist with 18 years of practice." Passes both sides.

A v1 GEO score-1 anchor that fits all three of these without modification — and would fit a DTC e-commerce vertical (lipstick brand) and a B2B SaaS vertical (BambooHR-class) without modification — is the right level of abstraction. If the anchor requires per-vertical adjustment, the criterion is over-specified.

### 8. Site Engine boundary

GEO and site_engine overlap (per v0 §8 Open Questions). The boundary: GEO judges ONE landing-page surface optimized for AI engine citation. site_engine judges the FULL site as a coherent set of pages each playing a role in the fan-out coverage. For dual-audience purposes, the GEO judge tests dual-audience fit AT PASSAGE / PAGE LEVEL. site_engine will test dual-audience fit AT SITE LEVEL (does the site cover the human-research journey AND the AI-engine fan-out simultaneously). The dual-audience axis lives in both lanes; the scope differs. The two judges should NOT have identical criteria; the GEO judge's GEO-1 through GEO-5 must be page-scoped, and site_engine's analogues must be site-scoped.

---

## Recommendations for v1

1. **Keep the 5-criterion shape** (GEO-1 through GEO-5). The dual-audience tension does not require a 6th criterion; it requires tightening the AND-conjunction inside each existing criterion's score-1 anchor.

2. **Rewrite each score-1 anchor to require dual-audience AND-conjunction explicitly.** Concrete pattern: "Passes when [AI-engine-extractable form] AND [human-trust-survivable substance]." Score 0 when either side fails. Score 0.5 only when one side is met and the other is ambiguous in the artifact alone.

3. **GEO-2 evidence density: keep agnostic to which Aggarwal lever** (stats, quotes, citations). The score-1 anchor should accept ANY of the three with proper attribution. Do NOT bias toward stats (would mis-score Health and Business per Aggarwal §6.3); do not bias toward quotes (would mis-score Law & Government); do not bias toward citations alone (would mis-score domains where fluency-driven authority dominates). The Aggarwal domain-variance finding is the load-bearing reason to keep the criterion abstract.

4. **GEO-5 format-intent match: lean on URL / title / H1 to infer query class.** This is the cheapest signal the judge has for matching format to likely fan-out coverage. Score-1 anchor should accept any of: comparison table for /best-X-for-Y, ordered steps for /how-to-X, definition + structured detail for /what-is-X, side-by-side comparison for /X-vs-Y. Do NOT embed a per-vertical template.

5. **Add a Goodhart-collapse score-0 anchor to each criterion.** Per design guide §11.1. The score-0 anchor must name the surface-marker-without-substance shape specifically:

   - GEO-1 score 0: query-echo lead OR declarative-shaped first sentence that is generic across categories (templated answer with vertical-specific terms swapped in).
   - GEO-2 score 0: citation count high but all sources sibling-domain OR stats present but unsourced OR quotes from un-named "industry experts."
   - GEO-3 score 0: passages mechanically self-contained via entity-repetition but substantively empty.
   - GEO-4 score 0: logo wall without per-logo attribution OR external sources all undated / unverifiable.
   - GEO-5 score 0: "Last updated" current-year stamp on body content with no current-year references OR table on a page where the underlying data is mismatched / stale.

6. **structural_gate hardening for AI-failure surfaces.** Per the CI spec's structural_gate pattern (`docs/handoffs/2026-05-17-judge-design-step1-competitive.md` §3b), add the GEO-specific deterministic checks:

   - URL HEAD resolution on all external citations.
   - "Last updated" or visible-publication-date presence check.
   - Entity-name canonicalization check (count of variant spellings of the primary entity; fail if > 1 canonical + plausible-acronym).
   - At least one off-domain citation present (not sibling-domain).
   - Word-count band for primary passage (40-75 words) and total page (band TBD per vertical fixture work).
   - Schema.org markup validation (if claimed).
   - Mobile / a11y / image alt-text deterministic checks (existing v006 structural_gate).

7. **Open question to fixture validation:** Build at least one fixture per Aggarwal domain class represented in first-cohort clients (Law & Government → DWF; Health → Klinika; Computers & Electronics → Anthropic / Perplexity), plus at least one new-vertical fixture (DTC e-commerce or B2B SaaS) before locking v1 criteria via the redundancy check.

8. **Do NOT add a "dual-audience" criterion as a separate criterion.** That would create a meta-feature-check surface. The dual-audience requirement lives INSIDE each of GEO-1 through GEO-5 via the AND-conjunction pattern.

9. **Do NOT add a per-vertical / per-domain criterion.** First-cohort overfitting risk. The Aggarwal variance is handled by keeping evidence-type abstract (any of stats / quotes / citations counts), not by tagging the criterion with a vertical.

10. **Watch GEO-1 ↔ GEO-3 correlation in the redundancy check.** Both touch passage structure (front-passage extractability and per-passage self-containment). If they correlate > 0.7 in fixture re-runs, fold one into the other. Most likely fold: GEO-3 absorbs into GEO-1's anchor as "and at least 2 additional passages downstream also work standalone."

---

## Open questions for JR

1. **Dominant-audience-by-client-intent toggle: explicitly REJECTED here. Confirm or push back.** The brief asked whether the judge should weight audiences by client intent. The synthesis argues against: a toggle adds a tuning surface that workflows learn to game (set the toggle low on the side the workflow is bad at). AND-conjunction is the Goodhart-resistant alternative. JR call: keep AND-conjunction or admit a controlled toggle?

2. **Site Engine boundary.** v0 §8 names this as open. Recommendation: defer to site_engine spec work; v1 GEO stays page-scoped. JR confirm or override.

3. **Schema markup as structural_gate vs judge.** Currently routed to structural_gate per v0 §4 GEO-5 "Do not score". Confirm; if structural_gate doesn't currently validate schema, that's a structural_gate expansion task.

4. **Per-vertical fixture coverage.** Build the Law / Health / Computers&Electronics + new-vertical fixture set before locking criteria, or accept that v1 ships with legal + AI-lab + healthcare coverage and gets re-validated against new-vertical fixtures as they appear?

5. **Format-intent inference from URL alone vs URL + title + H1.** Score-1 anchor needs to be specific about what signals the judge uses to infer likely query class. URL is the cheapest; URL + title + H1 is more robust but adds CoT length. Trade-off worth committing on before v1 lock.

6. **The Aggarwal domain taxonomy.** Aggarwal's 25 domain classes don't map 1:1 to gofreddy's client verticals. Worth a one-time mapping pass: for each first-cohort vertical, which Aggarwal class is the closest match, and which Aggarwal-method-lift therefore applies? This becomes the fixture-validation reference set.

7. **Variance instrumentation per the design guide §11.5.** GEO is a likely candidate for early Goodhart drift because the AI-engine-extraction surface is so heavily described in the literature that workflows have many templates to copy. Schedule the variance-per-criterion-per-generation telemetry for GEO from generation 1, not on a delayed cadence.

---

## Citations

Academic:

- Aggarwal, Murahari, Rajpurohit, Kalyan, Narasimhan, Deshpande. "GEO: Generative Engine Optimization." arXiv:2311.09735, KDD 2024. Section 6.3 (Domain-Specific Analysis) is the load-bearing source for domain-variance.
- Bagga, Farias, et al. "E-GEO: A Testbed for Generative Engine Optimization in E-Commerce." arXiv:2511.20867, November 2025. Finds stable domain-agnostic optimization pattern within e-commerce listings; reconciles with Aggarwal as within-node vs cross-node.
- Schulte et al. "Don't Measure Once: Measuring Visibility in AI Search (GEO)." arXiv:2604.07585, April 2026. Confirms visibility-as-distribution; reinforces variance axis.
- "Reasoning about Intent for Ambiguous Requests." arXiv:2511.10453, 2025. Background on the unambiguous-answer vs nuanced-interpretation tradeoff in AI systems.

Practitioner / industry research:

- Cyrus Shepard, "AI Citation Ranking Factors Analysis," Zyppy Signal — 54-experiment meta-analysis.
- Andrea Volpini (WordLift), "Why AI Cites Some Pages and Ignores Others," "Retrieval Evolution For Large Language Models," "Query Fan-Out: A Data-Driven Approach to AI Search Visibility." Asymmetric-retrieval and declarative-document register arguments.
- Profound, "AI Platform Citation Patterns" + "How ChatGPT Sources the Web." 40-75-word passage finding, 4.2x tabular-comparison finding.
- Ahrefs, 75K-brand mention-correlation study (Patel Long, 2025): r=0.664 brand mentions vs r=0.218 backlinks.
- Ahrefs, "AI Assistants Prefer to Cite Fresher Content (17M Citations)."
- Ahrefs, "76% → 38% AI Overview Citations Pull From the Top 10" Q1 2026 update.
- Skywork, "Perplexity Accuracy Tests 2025: Sources & Citations." 78% claim-source attachment; 70% sources within 12-18 months.
- Search Engine Land, "AI Overviews drive 61% drop in organic CTR, 68% in paid." Seer Interactive Sept 2025 study.
- Adobe / RankScience / IAMedia Q1-Q2 2026 conversion studies: AI traffic 14.2% conversion vs Google 2.8%; AI visitors 23% lower bounce, 48% longer per visit, 13% more pages.
- Position.digital, "150+ AI SEO Statistics for 2026 (April 2026)." Compiled bounce-rate and AI-content-quality findings.
- Mersel AI, "Why Is Organic Traffic Declining in 2026? AI Search & Recovery Plan." Overall traffic-shift framing.
- WebFX / Authority Tech, "AI Search Traffic Converts 4-23x Better Than Organic." Conversion-multiplier confirmation.

Project context:

- `docs/research/2026-05-15-judges-domain-geo.md` — generalist GEO domain research (do not restate; this deepens).
- `docs/handoffs/2026-05-18-judge-design-step1-geo.md` — v0 GEO judge spec being deepened here.
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` §3b — structural_gate pattern for AI-failure surfaces; transferable to GEO.
- `docs/rubrics/judge-design-guide.md` — design constraints and anti-patterns referenced throughout.
