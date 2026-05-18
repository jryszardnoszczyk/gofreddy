---
date: 2026-05-18 v1
type: judge-design Step 1 — geo (generative engine optimization / AEO) optimal-output spec
status: DRAFT v1 — 4 deep-research deliverables synthesized; ready for redundancy check + fixture validation
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
pattern_reference: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI v3.3 gold standard)
companions:
  - docs/research/2026-05-15-judges-domain-geo.md (generalist GEO domain research)
  - docs/research/2026-05-18-geo-vertical-conventions.md (vertical-specific evidence-substrate research)
  - docs/research/2026-05-18-geo-artifact-taxonomy.md (10 form-factor taxonomy)
  - docs/research/2026-05-18-geo-ai-failure-modes.md (LLM-specific GEO failure surfaces)
  - docs/research/2026-05-18-geo-dual-audience-tension.md (Aggarwal-method-by-domain + AND-conjunction rationale)
revision_history:
  - 2026-05-18 v0 — initial skeleton, 5 criteria, dual-audience reader framed but AND-conjunction implicit
  - 2026-05-18 v1 — synthesis of 4 deep-research deliverables. Added §1.5 per-fixture geo_format enum
    (10 form factors — NOT one LOCKED hybrid, GEO routes per-fixture). Rewrote §1 reader with substitute-
    readers list and concrete-anchor-not-architectural-target note (mirrors CI v3.3 first-cohort discipline).
    Rewrote §2 success with cross-industry exemplars (Stripe / Linear / Anthropic / Mayo Clinic / Backlinko).
    Rewrote §3 failure with mediocre modes + Phase-4-Goodhart-collapse + 5 AI-specific failure surfaces
    (entity confab 19.9% GPT-4o; source confab 37% Perplexity / 78% OpenAI / 94% Claude; recency cutoff
    23-35% NAACL; inverted citation 27% Partial Attribute Corruption; competitive injection). Rewrote
    GEO-1..GEO-5 with explicit AND-conjunction language in score-1 anchors (the load-bearing Goodhart
    defense per dual-audience-tension research). Generalized GEO-5 freshness from 12-18 months (healthcare-
    only cadence) to vertical-conditioned windows. Added 3 vertical anchors per example-bearing criterion
    (legal / healthcare / B2B SaaS load-bearing; fintech / AI-lab alternates). Added GEO-6 "Evidence chain
    survives tracing" as documented ≤5-ceiling exception per design-guide §5 — mirrors CI-6 precedent;
    AI-failure-class surface with measured effect sizes the other 5 can't catch. §6 Goodhart-resistance
    expanded with 7 per-vertical collapse modes (legal: attorney-bio theater; healthcare: guideline slot-
    fill; B2B SaaS: comparison-where-we-win; fintech: disclaimer density; AI-labs: vendor-benchmark; DTC:
    schema + Reddit-pull-quote fab; professional services: head-to-head template repetition).
    structural_gate expanded to 8 AI-failure-routing checks (URL HEAD, quote-grep, entity-existence
    Wikidata-lookup, "as of" date, recency floor ≥1 source <90 days, schema.org validity, FAQPage rich-
    results JSON-LD, broken-link detection). §8 open questions broadened beyond v0's 4 to cover redundancy
    pairs, site_engine boundary, YMYL 6th-criterion exception status, Wikidata coverage tiering for SMB,
    cosine threshold tuning, first-cohort overfit re-validation triggers, March/April 2026 Google AI
    Overview algorithm updates, engine-side downstream monitoring deferred to monitoring lane.
---

# GEO (Generative Engine Optimization / AEO) — Optimal-Output Spec (DRAFT v1)

Conforms to `docs/rubrics/judge-design-guide.md` with one documented exception (§7). Frameworks
(Aggarwal KDD 2024, Volpini, Shepard, Kalicube Entity SEO, AEO, BLUF, Matryoshka Paragraph) inform
the reader/success/failure spec and are the judge's reasoning toolkit. They do NOT appear by name
in criterion prose.

This v1 supersedes the v0 skeleton by synthesizing four deep-research deliverables. Each elaboration
here is anchored in one of those four: §1.5 per-fixture `geo_format` enum (artifact-taxonomy research —
10 form factors with empirically dominant 4 in 2026; shape-drift Goodhart is documented in evolution-
loop literature); 3 vertical anchors per criterion (vertical-conventions research — first-cohort
overfit documented across legal/AI-lab/healthcare verticals); structural_gate 8 AI-failure-routing
checks (AI-failure-modes research — 19.9-37% documented citation-fab rates require deterministic
verification the judge structurally cannot do because all three frontier families share the
hallucination class); §3 AI-specific failure surface awareness; GEO-6 evidence-chain (the documented
≤5-ceiling exception); AND-conjunction at every criterion (dual-audience-tension research — weighted
blends create tuning surfaces workflows learn to game).

The v0 skeleton's wrapper prose ("AI engine is the gating reader") was correct and is preserved.
What v1 adds is the architectural rigor underneath: per-fixture form-factor routing, vertical-divergent
anchors, AND-conjunction language explicit, and one documented 6th-criterion breach for the AI-failure
surface the other 5 cannot catch.

The dual-audience asymmetry is load-bearing — GEO is alone among the autoresearch lanes in serving
TWO distinct primary readers (a human researcher AND an AI engine that fans out, reranks, and
synthesizes) and the artifact must satisfy both AT EACH CRITERION via AND-conjunction, not via
weighted blend or audience toggle. "Looks elaborate" ≠ "over-engineered" — GEO-6 elaboration is
justified per documented AI-failure surfaces with measured effect sizes; the same lesson CI v3.1's
over-correction taught applies here.

---

## 1. Reader (LOCKED 2026-05-18)

GEO content serves TWO readers simultaneously, both primary. The judge must score for both via
AND-conjunction at each criterion (§5 wrapper makes this explicit).

**Primary human reader.** A researcher or evaluator querying ChatGPT, Perplexity, Claude, or Google
AI Mode about a category gofreddy clients operate in. They ask a question in natural language, the
engine answers with cited sources, and they decide whether to click through, copy the answer, file
the source as reference, or commit to an action (book a demo, request a quote, file for procurement
review). Specifically, the load-bearing personas are:

- **Head of marketing at a mid-market B2B SaaS** doing vendor diligence ahead of a Q3 procurement
  cycle. They have 40-second skim budget per source; they will quote one sentence to a peer if the
  page survives the skim; they convert at ~14% (AI-referred traffic vs ~2.8% on Google organic per
  Adobe / RankScience Q1-Q2 2026 data) when the page reads as reference, not as marketing.
- **In-house counsel comparing legal-services providers** for a specific upcoming matter (litigation,
  restructuring, regulatory). They need jurisdiction-scoped, statute-anchored, attorney-attributed
  content; their skepticism is calibrated against YMYL gating norms.
- **Clinic operations lead** evaluating aesthetic-dermatology brands ahead of a vendor contract,
  partnership, or competitive-positioning decision. They need clinician-attributed, guideline-
  referenced, last-medically-reviewed content; their skepticism is calibrated against healthcare
  YMYL norms.

The human reader is smart, time-poor, and skeptical. They've been pitched enough SEO-pivoted-to-AEO
content to recognize slot-fills. They have authority to act on what they read: route a procurement
decision, brief a partner, escalate to a senior buyer, file for diligence. They will not re-read
the page; they get one extraction pass.

**Primary machine reader.** The AI search engine itself — ChatGPT, Perplexity, Claude, Gemini,
Google AI Mode, Copilot — deciding whether to retrieve this page into the candidate set AND whether
to cite it in the final answer. The engine operates a four-stage pipeline (Volpini's breakdown):
lexical-candidate-generation → dense retrieval → reranking → synthesis-with-citation. It fans out
the user's query into multiple sub-queries, retrieves candidates across the fan-out set, reranks
by passage relevance and authority, and synthesizes with citation footnotes.

The engine's behavior is empirically measured: ChatGPT cites Wikipedia (#1 source, 7.8% of all
citations) and Reddit most; Perplexity cites sources with visible publication or update dates within
12-18 months 70% of the time, 78% of complex-research answers tie every claim to a specific source;
90% of top-cited Perplexity sources answer the core question within the first 100 words. Google AI
Overviews now pull only 38% of citations from Google's organic top 10 (down from 76% in July 2025)
and only 12% of all AI-cited URLs overlap with Google's top 10 on the original prompt — AI citation
is diverging from organic ranking. Listicles account for 43.8% of all ChatGPT citations; tables get
4.2× the citation rate of equivalent prose; 40-75-word passages get 3.1× the citation rate of longer
passages.

The page must be citation-worthy on its own merits, not on link-graph inheritance — and it must be
citation-RESILIENT to the engine's own hallucination tendencies (entity confabulation, source confab,
recency distortion — see §3).

**Substitute readers the same page should also serve.** Founder-CEO doing competitive landscape
research before a quarterly off-site; corp-dev / strategy lead evaluating a category for acquisition;
owner-operator at a small-to-mid local-market business (healthcare, hospitality, retail, professional
services) doing vendor selection; decision-maker at a B2B SaaS at any scale evaluating channel /
pricing / positioning; fintech or regulated-finance operator evaluating compliance-context content
sources; DTC e-commerce buyer doing product-discovery via agentic-commerce protocols (ACP / UCP)
where the AI engine is the literal point-of-sale interface.

The legal-services + AI-lab + healthcare reference set in this spec exists because those are gofreddy's
current first-cohort fixture clients (DWF, Anthropic, Perplexity, Klinika). They are **not** the
architectural target — they are concrete anchors. The spec is designed to generalize to tech-savvy-
founder / early-co clients across verticals; first-cohort overfit is an explicit risk to monitor
(see §8). The Aggarwal KDD 2024 finding is load-bearing here: the optimal optimization method is
domain-conditioned (Statistics Addition wins for Law & Government / Opinion; Quotation Addition wins
for People & Society / History; Fluency Optimization wins for Health and Business) — single-formula
GEO is wrong by construction.

NOT the reader: a brand-loyalist already on the site looking for product detail; a journalist
sourcing a specific named expert; a developer reading API reference for an integration task; a casual
browser without query intent. These readers exist; this artifact is not for them.

---

## 1.5. Artifact shape (PER-FIXTURE `geo_format` enum)

**GEO produces ONE OF TEN canonical page-type form factors per fixture**, per
`docs/research/2026-05-18-geo-artifact-taxonomy.md`. Unlike CI / MA / MON / SITE — which each lock
ONE hybrid form factor — GEO routes the artifact shape PER FIXTURE via a `geo_format` enum declared
on the fixture brief. The judge stays format-agnostic at the criterion layer; the workflow's
`structural_gate` enforces shape-conformance per declared format.

**The 10 form factors (with empirically dominant 4 in 2026 boldfaced):**

1. **Definition page** (`definition`) — "What is X" entity-grounding surface; 600-1,500 words;
   declarative lead in first 40-75 words; Article + DefinedTerm schema.
2. **How-to page** (`how_to`) — Procedural / instructional; 800-2,500 words; numbered/ordered steps;
   prerequisites + verification + troubleshooting blocks; HowTo schema (demoted on non-primary
   content per Google March 2026 update, use only when primary purpose).
3. **Comparison page** (`comparison`) — "X vs Y" head-to-head; 1,200-2,500 words; mandatory
   comparison table with ≥3 dimensions; dual-entity symmetry; both entities cited at parity.
4. **Listicle / alternatives** (`listicle`) — "Best of X" / "Alternatives to Y"; 2,000-4,500 words;
   ranked items with disclosed methodology; per-item 100-200 words + structured row; ItemList +
   (optionally) FAQPage schema. **Dominant 2026 citation form factor — 43.8% of ChatGPT citations.**
5. **FAQ page** (`faq`) — Standalone or embedded; question-as-heading + 40-75 word answer; FAQPage
   schema (NOTE: Google killed FAQ rich-results May 7 2026 — schema is now AI-engine-only signal,
   not SERP-feature signal; pages with schema are 3.2× more likely to appear in AI Overviews).
6. **Glossary entry** (`glossary`) — Atomic 200-500 word definition; DefinedTerm in DefinedTermSet;
   cross-linked into glossary index.
7. **Pillar / topic hub** (`pillar_hub`) — Broad-category orchestration; 1,500-3,500 words; 4-8
   sub-topic sections with link-out to deeper pages; original-research / data block. **CAUTION:**
   Google March/April 2026 updates demoted hub-bloat / intermediary-content / topical-bloat — may
   sibling-fork to site_engine lane.
8. **Integration page** (`integration`) — "Tool X + Tool Y"; 600-1,400 words; workflow + setup +
   limits + supported APIs; Article + SoftwareApplication schema.
9. **Pricing page** (`pricing`) — Public tier matrix; 800-1,800 words including FAQ tail;
   server-rendered HTML with SoftwareApplication + Offer schema; concrete prices in schema.
10. **Product / category landing page** (`product_landing`) — Brand-anchored entity definition +
    category placement + third-party validation block. Closest shape to v0's "single optimized
    landing-page surface" framing.

**Why per-fixture enum, not one LOCKED hybrid:** the 10 form factors have structurally divergent
evidence conventions, citation behaviors, schema markup, freshness cadences, and word-count bands.
A LOCKED hybrid (the CI v3.3 approach for executive-briefing form) would either (a) fail half the
form factors at workflow level or (b) drift into a Frankenstein artifact under 50-generation
selection pressure — definition-shaped page with a forced-in comparison table and bolted-on FAQ
section, none of which serve the page's actual query class. Per-fixture routing isolates form-factor
choice as a workflow-input parameter, not a judge-inference task.

**Workflow routing of `structural_gate` per format.** The workflow's `structural_gate` reads
`geo_format` from the fixture brief and applies form-factor-specific shape-conformance checks IN
ADDITION to the 8 universal AI-failure-routing checks (§3 below). Per-format checks:

- `listicle`: ItemList schema; methodology block; ≥5 items each with ≥100 words; per-item structured
  row (name + price + fit + source); FAQ tail present; quarterly-or-newer date stamp.
- `comparison`: ≥1 comparison table with ≥3 dimensions; both entities cited at parity (entity-mention
  count ratio 0.7-1.3); both entities have ≥1 third-party off-domain citation; dated within 6 months.
- `definition`: word count 600-1,500; declarative-lead first sentence (no "What is X?" interrogative
  opener); Article + DefinedTerm schema (optional); ≥4 inline citations with ≥2 off-domain.
- `how_to`: ordered-list or numbered-heading structure; prerequisites block; verification block;
  HowTo schema only if primary purpose; dated within 12 months.
- `faq`: organic FAQ load (questions match actual user-query patterns); FAQPage schema with all
  on-page Q&A pairs represented in JSON-LD; no fake-FAQ-tail to game schema (§3 Goodhart mode).
- Other formats: scoped to v1.1 fast-follow (`pillar_hub` likely sibling-forks to site_engine).

**Out of scope shapes** (the lane will NOT produce these in v1):
- Multi-page sites (handled by `site_engine` lane)
- 30-page deep-dive industry reports (no AI-citation surface — wrong audience)
- 1-page sales battlecard (sales-enablement, not GEO)
- Site-wide content audit (monitoring lane handles)

**FAQ-rich-results killed May 7 2026 — implication.** Google removed FAQPage rich-results from
Search SERPs on May 7 2026. The schema is still actively useful for AI Overview retrieval (ALM Corp
2026: 3.2× more likely to appear) and ChatGPT / Perplexity citation, but the visual SERP feature is
gone. `structural_gate` validates FAQPage JSON-LD as schema, not as rich-result eligibility. Pages
that game the schema with non-organic FAQ load teach AI engines to distrust the domain — `faq`
format requires organic FAQ load per `structural_gate`.

**Empirical validation scope.** The 10-form-factor taxonomy is research-grounded against 2026 AI
engine citation data (Ahrefs 26,283-URL ChatGPT study; ALM Corp listicle-vs-article-vs-product-page
breakdown; Wix March 2026 data). When fixtures from new verticals or new emerging form factors
appear (e.g., conversational-thread-extracted pages from Reddit; model-card-anchored AI-tool pages;
ACP/UCP-protocol-anchored DTC product pages), re-validate. Bake versioning into the `geo_format`
field so the enum can extend without breaking historical fixtures.

---

## 2. Success — what each reader DOES (LOCKED 2026-05-18)

**Human reader.** Finishes a 40-second skim believing the page answers their actual question with
cite-able specifics, and either acts (clicks the CTA, books a demo, requests a quote) or files the
page as a reference they'd cite when explaining the category to a peer. They could quote one specific
sentence to that peer that captures what the brand does. **Conversion-test:** they convert at the
AI-traffic baseline rate (~14% — five times Google organic) because the page reads as reference, not
as marketing.

**AI engine.** Treats the page as a high-confidence source for the category. Cites it in answers
across multiple query variants (fan-out coverage). Recurs to it on related questions over the next
12+ months because the entity, claims, and supporting evidence are stable enough to be re-retrieved
under the engine's "citation gravity" tendency (Kalicube's term: established entity understanding
creates a self-reinforcing pull — once an engine has cited you, it returns to you across related
queries). The page survives engine-side hallucination tendencies (similar-name conflation, source
confab, recency distortion) because it forces the engine toward correct synthesis (§3, GEO-6).

**Dual-audience structural pattern that works in practice** (per dual-audience-tension research):
declarative-document register at the top (the 40-75-word extracted passages, the definitions, the
structured comparisons), human voice in the middle (named author or expert quote, specific worked
example, story or case study with attribution), declarative-document register at the bottom (the
structured detail, the FAQs, the third-party citation block). The voice is bracketed inside the
declarative surface, not opposed to it.

World-class real-world exemplars — used as quality anchors, NOT as templates to copy:

**Cross-vertical rigor (the ceiling):**
- **Stripe.com developer-product pages** ("Connect is Stripe's solution for routing payments to
  third parties…") — declarative entity definition + category placement + code-example density +
  named-customer evidence. Passes both AI-extraction (BLUF declarative) and human-trust (concrete
  proof of expertise).
- **Mayo Clinic / Cleveland Clinic disease-overview pages** — clinician-attributed, guideline-
  referenced, last-medically-reviewed-stamped, structured detail with deep evidence-chain. The
  YMYL baseline that any healthcare GEO content competes against.
- **Anthropic.com research pages** — named expert quotes, dated claims, third-party authority
  signals, reproducible benchmark methodology. The AI-lab citation ceiling.

**Practitioner-grade (the achievable floor):**
- **Linear.app product / pricing pages** — BLUF declarative, sharp entity definition, named-
  customer evidence at parity with feature claims, structured comparison tables.
- **Backlinko's own SEO content pages** — heavy stats with named sources, ranked lists with
  citations, declarative-document register that earns its place because the substance is dense.

What ties these together: declarative entity-definition lead, evidence-paired claims with off-
domain attribution, passages that work standalone, freshness signaled in body content not just
stamp, vertical-appropriate evidence type (Aggarwal-aware: statistics for Law / Opinion; quotation
for People & Society / History; fluency for Health / Business).

---

## 3. Failure — mediocre and Goodhart-collapse (LOCKED 2026-05-18)

### 3a. Mediocre — failure modes the judge must discriminate against

**Query-mirroring lead.** Page opens with "What is X? X is becoming increasingly important…"
(Volpini's Matryoshka Paragraph: under Google's asymmetric embedding scheme this signals "another
query" not "an answer," and ranks behind sources that lead with a declarative definition; Aggarwal
documents keyword-stuffing as the single most consistent negative signal).

**Buried answer.** Core claim sits below the fold or in paragraph 4. Generative engines have
retrieval caps per URL — 44% of all AI citations come from the top third of a page; if the answer
isn't there, the citation isn't either.

**Prose where a table would do.** Comparison content, pricing, feature differences, spec lists
written as flowing paragraphs lose to the same data structured as a table by 4.2× (Profound).

**Unsourced specificity.** A number without a source is a marketing claim, not a fact. Aggarwal's
Statistics Addition method works ONLY when statistics are presented as verifiable.

**Floating pronouns and orphan passages.** Volpini's chunk-complete principle — if a 50-word
passage extracted standalone can't be understood without prior context ("This makes it…", "The above
shows…"), the retrieval system treats it as low-confidence material.

**Vendor self-puffery without third-party signal.** Forrester 2026: AI buyers validate vendor claims
against external sources before trusting them. Pages that don't acknowledge the competitive landscape
read as marketing not reference. The Verge documented Google AI Mode catching and de-ranking vendor-
authored "best of" lists that placed their own products first.

**Stale freshness.** No visible date, no current-year reference, no recent third-party citation.
Perplexity 70% / 12-18 month finding; Ahrefs 17M-citation freshness study.

**Entity drift.** "Acme Pay" / "Acme Payments" / "AcmePay" across sections. Embeddings cluster these
as different entities; citation signal fragments.

**Mismatch between page intent and likely query class.** A "/best-X-for-Y" URL written as flowing
marketing narrative; a "/how-to-X" page without ordered steps; a "/X-vs-Y" page that's actually a
single-sided product page. Shepard's Intent-Format Match (#6, 9.0).

### 3b. Goodhart-collapse — Phase-4 pathology + AI-specific failure surfaces

**Phase-4 pathology (the historical Goodhart trap).** 50-generation evolution against a feature-
checking judge produces exactly the pathology rolled back at HEAD `c76f051` (commit `698e658`).
The workflow learns to slot-fill the verifiable surface markers:

- **Citation stuffing.** Three citations per section regardless of relevance.
- **Stats-table cargo-cult.** A stats table dropped on every page regardless of whether the page
  shape calls for one.
- **"Last updated" date gaming.** Stamp touched daily by automation with zero body-content changes.
- **Entity-name spam.** Brand name repeated 12+ times per section without canonical disambiguation
  in the lead.
- **Exactly-40-word answer-bait passages.** Plants 40-word "answer-shaped" passages regardless of
  whether the substance supports them.
- **Schema markup slot-fill.** JSON-LD describing content the page doesn't actually carry (FAQ
  schema with no organic FAQ; Review schema with no visible reviews; HowTo schema on supplementary
  content per Google March 2026 demotion).
- **Methodology-block-without-substance.** Listicle discloses criteria with no evidence the criteria
  were applied to ranked items.

AI engines catch most of these within 1-2 indexing cycles — the page enters the "looks AEO-
optimized therefore distrust" tier. The page scores high on a feature-checking judge AND low on
actual AI citation. The judge has to test for OUTCOMES (would the engine cite, would the human act)
not for surface-marker presence.

**Per-vertical Goodhart collapse modes (from vertical-conventions research §5).** Each vertical has
its own slot-fill shape under selection pressure — the judge must defend against vertical-specific
Goodhart-collapse, not just cross-vertical surface-marker drift:

- **Legal:** "Attorney-bio + jurisdiction-scope theater." Workflow plants attorney byline + bar-number +
  jurisdiction-statement on every page regardless of whether the underlying analysis is jurisdiction-
  accurate or attorney-substantive.
- **Healthcare:** "Clinical-guideline citation slot-fill." Workflow drops NICE / USPSTF / AAD citations
  on every page regardless of whether the citation is relevant; medical-reviewer-byline is templated
  and not load-bearing.
- **B2B SaaS:** "Comparison-table-where-we-win." Workflow produces comparison pages where the home
  product wins every row — already an AI-flagged pattern (Verge / Google AI Mode), so the slot-fill is
  self-defeating but the workflow may iterate through several before learning.
- **Fintech:** "Disclaimer / risk-disclosure prose density." Workflow plants disclaimers and risk-
  disclosure language on every page regardless of whether the underlying analysis is regulator-aligned.
- **AI-labs:** "Vendor-benchmark table slot-fill." Workflow drops benchmark tables citing self-reported
  scores; AI engines have learned to preferentially cite independent-eval sources (Epoch AI, Artificial
  Analysis, LMSYS), but the workflow iterates through several before learning.
- **DTC e-commerce:** "Schema + Reddit-pull-quote fabrication." Workflow injects Product schema
  everywhere + plants Reddit-style quotes that aren't actually sourced; AI engines that detect the
  fabrication de-rank.
- **Professional services:** "Head-to-head template repetition." Workflow learns the X-vs-Y format
  and replicates it on pages where comparison is the wrong format-intent.

**AI-specific failure surfaces (load-bearing for GEO-6).** These are LLM-specific failure shapes
the judge panel structurally cannot detect because all three frontier families (Claude / OpenAI /
Gemini) share the hallucination class — deterministic verification in `structural_gate` is the only
defense. Each cited with measured effect size from 2024-2026 literature:

- **Entity confabulation.** Engine fabricates the entity being described OR conflates similarly-
  named entities ("Cursor" the IDE vs "Cursor" the cursor-tracker; "Anthropic" attributed to a
  non-existent "Anthropic Communications"). Documented: GPT-4o 19.9% citation-fabrication rate
  (Chelli et al. 2025); GhostCite / KGHaluBench 14-95% entity-existence hallucination across 13
  models × 40 domains.
- **Source confabulation.** Engine invents or distorts the source URL: sibling-URL substitution;
  section-anchor hallucination; plausible-domain hallucination; real-URL-fabricated-attribution
  (most dangerous shape). Documented: Perplexity 37% citation-fabrication rate; OpenAI Deep
  Research 78% accuracy (22% fab); Claude with search 94% accuracy (6% fab). NeurIPS 2025: 100
  AI-generated hallucinated citations in 53 published papers (Total Fabrication 66% / Partial
  Attribute Corruption 27% / Identifier Hijacking 4%).
- **Recency / training-cutoff distortion.** LLMLagBench (arxiv 2511.12116): models often have
  *behavioral* cutoffs 6-18 months before their release date — a Feb-2026-released model frequently
  behaves as if its knowledge stops in Oct 2024 for finance / regulatory / product-launch facts.
  "Is Your LLM Outdated?" NAACL 2025: accuracy drops 23-35% on relative ("recently") vs absolute
  ("in 2026") temporal framings.
- **Inverted-citation attack.** Adversary publishes a page that names the brand correctly but mis-
  attributes events/features; engine retrieves the adversary's page and synthesizes the mis-
  attribution into the answer. NeurIPS 2025 / CompoundDeception: 27% Partial Attribute Corruption
  rate; engine attributes real events to wrong sources, or wrong attributes to real entities.
- **Competitive injection.** Page satisfies all GEO surface markers — BLUF declarative lead,
  evidence density, self-contained passages, third-party validation — but the framing of those
  validations is competitor-favorable (comparison table where competitor's strengths are stated in
  equal or stronger language; fabricated-competitor-claim injection). HalluLens Nonsense sub-
  benchmark documents context-free entity-attribute hallucination as the modal shape for competitor
  descriptions.

**Deterministic AI-failure checks live in `structural_gate`.** Per OpenRubrics design principle
(Hard Rules → `structural_gate`, Principles → judge) and per the design-guide §2 split — deterministic
verification belongs in `structural_gate` because the judge structurally cannot deterministically
verify URL resolution, quote provenance, entity existence, or date freshness. The cross-family panel
is blind to these classes (§7 dual-audience-tension research). Eight AI-failure-routing checks:

1. **URL HEAD resolution** for every off-domain cited URL (HTTP 200 within 5s, retry-on-3xx) — catches
   dead cited links + sibling-URL substitution.
2. **Quote-grep against source corpus** — every direct quote (string in `""`) must exist in the cited
   source URL with cosine similarity > 0.85 — catches fabricated quotes from real URLs (Perplexity
   37% failure shape subset).
3. **Entity-existence Wikidata-lookup** — singleton canonical entity name across H1 + JSON-LD `@id`
   + OpenGraph + BLUF first sentence; schema.org `sameAs` to at least one canonical KG anchor
   (Wikidata > Crunchbase > LinkedIn Company Page > Google Business Profile > registry .gov, tiered
   for SMB coverage) — catches invented competitor entities (GPT-4o 19.9% citation-fab subset).
4. **"As of" date requirement** — visible `data-as-of="2026-MM-DD"` or `<time datetime=...>` element
   within last 90 days — forces freshness signaling against LLMLagBench training-cutoff drift.
5. **Recency floor** — ≥1 cited source dated within 90 days per schema.org `datePublished` or HTTP
   last-modified — defends against recency-cutoff distortion + NAACL 2025 relative-temporal-framing
   accuracy drop.
6. **Schema.org markup validity** — JSON-LD validates against schema.org vocabulary; declared schema
   types match actual page content (no FAQPage schema on pages without organic FAQ; no Review schema
   without visible reviews; no HowTo schema on supplementary content per Google March 2026 demotion).
7. **FAQPage rich-results JSON-LD validation** — for `faq` format fixtures: all on-page Q&A pairs
   represented in JSON-LD; no schema-without-substance (note: rich-results SERP feature killed
   May 7 2026 but schema remains AI-engine signal; ALM Corp 3.2× AI Overview boost).
8. **Broken-link detection** — every internal link resolves to a 200; every external link resolves
   to a 200 or 301 with valid redirect target — catches link-rot drift and prevents the page from
   becoming a stale-link citation surface.

**Banned-phrase patterns** (deterministic, structural failure if matched without disambiguating
absolute-date qualifier): "recently," "in recent months," "today's," "the latest," "current year" /
"this year" without absolute year qualifier. Catches NAACL 2025 relative-date framing distortion.

**Historical context.** This lane (or its siblings) has triggered three prior rollbacks for the
same underlying Phase-4 pathology: `2ce99bb` (σ-widening prose, J1-J4), `ca4a256` (v2 contract-
prose), `698e658` (Phase 4 feature-checking → `c76f051`). The criteria below are designed to
resist re-creating any of them AND to surface the AI-specific failure surfaces those rollbacks
didn't address. The lesson `2ce99bb` taught (σ-widening trades information for variance) and the
lesson `698e658` taught (feature-checking criteria enable 27.9 pp preference drift) both apply
here.

---

## 4. Criteria — outcome questions (6)

### GEO-1 — Answer-first BLUF compliance (AND-conjunction: extractable form AND substantive claim)

**Outcome question (binary):**
Does the page's primary claim — what the product / service / entity is, who it serves, what makes
it different — land in the first 40-75 words of meaningful body content, in declarative-document
register (not query-echo register), AND does that 40-75-word passage carry a substantive claim a
domain expert in the page's target vertical would defend? Would an AI engine extracting the top
passage emit a complete, citable answer that a sophisticated human reader would also accept as
reference-grade?

**Score 1 (yes)** — First 40-75 words contain BOTH (a) a declarative entity definition + category
placement + a differentiation claim in retrieval-document register (no interrogative opener, no
brand storytelling preamble), AND (b) a substantive claim that names the specific vertical / target
reader / non-generic differentiator that a domain expert would defend. An AI engine could emit those
75 words verbatim AND a sophisticated human reader would not classify the page as "generic AI
content" on the strength of the first passage alone.

Example A — legal (do not optimize toward this): "Section 230 of the Communications Decency Act
(47 U.S.C. § 230) is the federal statute that provides interactive computer service operators with
immunity from liability for third-party-posted content. As of May 2026, the immunity has been
narrowed by FOSTA-SESTA and is subject to two pending Supreme Court reviews; this article is
current as of May 1, 2026 and is for informational purposes only, not legal advice."

Example B — B2B SaaS (do not optimize toward this): "Linear is a project-management tool built for
software engineering teams that prefer keyboard-first interfaces, fast issue triage, and Git
integration. Used by 10,000+ teams including Cash App, Vercel, and OpenAI; consistently rated 4.7+
on G2 across 800+ reviews."

Example C — healthcare (do not optimize toward this): "Klinika Melitus is a Warsaw aesthetic
dermatology practice, founded 2008 by Dr. Maria Noszczyk, MD (board-certified equivalent to FAAD),
specializing in injectable cosmetic dermatology (Botox, fillers, biostimulators) for adult patients
in central Warsaw. Listed on RealSelf and Healthgrades; this article was last medically reviewed
May 2026."

**Score 0 (no)** — Opens with a question paraphrasing the query ("What is X?"); brand storytelling
preamble; vague positioning ("the future of marketing," "the leading platform"); buries the answer
below the fold. OR the first-75-words structure is declarative but the substance is generic — a
templated answer with vertical-specific terms swapped in that wouldn't survive a domain-expert read.

**Score 0.5 (unknown)** — Answer exists in the first 75 words but is hedged or genre-mixed (part
declarative, part interrogative) such that extracted standalone it would read as partial — OR
the substance side is ambiguous from the artifact alone. Emit 0.5 + "unknown" + one sentence on
what would clarify.

**Required CoT:**
- Step 1: Extract the first 75 words of meaningful body content (skip nav, hero-image alt text,
  cookie banners).
- Step 2: Test whether those 75 words contain a complete declarative answer to "what is this and
  who is it for?" in retrieval-document register.
- Step 3: Test whether the substance survives the domain-expert read — does it name vertical-
  specific differentiators, or is it a templated answer with terms swapped?
- Step 4: Emit verdict + one-sentence justification.

**Do not score:** visual design, page length beyond first 75 words, whether the page also contains
imagery, schema.org markup specifics. Those live in `structural_gate` or do not matter.

### GEO-2 — Evidence density (AND-conjunction: extractable form AND off-domain verifiable substance)

**Outcome question (binary):**
Does the page inject verifiable evidence — quantitative figures with sources, direct quotations
from credibly-named third parties, inline citations to first-party data or external authority — at
a density that would let an AI engine validate the claims independently, AND would a sophisticated
human researcher trust those sources as off-domain and reference-grade? Does the evidence type
match the page's vertical (the Aggarwal domain-conditioned optimum — statistics dominate Law &
Government / Opinion; quotation dominates People & Society / History; fluency-driven authority
dominates Health and Business)?

**Score 1 (yes)** — Page contains at least 3 specific claims paired with verifiable evidence BOTH
(a) extractable / inline-citable in form (named numeric figure with year + source; direct quote
with named attribution + role + employer + date; inline citation to a specific document) AND
(b) off-domain / first-party-data-anchored in substance (the source is named off the brand's own
domain — not sibling-page self-citation; OR is genuinely first-party original research the brand
owns and others can cite back). Each claim is checkable AND a domain expert in the vertical would
accept the source as appropriate (statute / case citation in legal; clinical-guideline citation
in healthcare; G2 / Gartner / TrustRadius in B2B SaaS; SEC / FINRA / FCA in fintech; arxiv /
analyst-Substack in AI-lab).

Example A — legal (do not optimize toward this): "Per 47 U.S.C. § 230(c)(1), as construed in
*Zeran v. America Online*, 129 F.3d 327 (4th Cir. 1997), and reaffirmed in *Gonzalez v. Google
LLC*, 598 U.S. 617 (2023), platforms retain immunity for third-party content even when applying
editorial-review functions."

Example B — healthcare (do not optimize toward this): "Per the American Academy of Dermatology's
2025 Clinical Practice Guideline on Botulinum Toxin Type A for cosmetic use (AAD CPG-BTX-2025),
onabotulinumtoxinA shows efficacy in glabellar lines at doses of 20U with peak effect at 14 days
post-injection; comparator studies vs Daxxify (Revance) show similar efficacy with longer duration
of action (24 weeks vs 16) — see Revance phase-3 trial RTI-001 (NCT04823300, primary endpoint
2024-05-30)."

Example C — B2B SaaS (do not optimize toward this): "Linear ranks #2 in G2's Spring 2026 Project
Management Grid (4.7 stars across 814 reviews; methodology disclosed at g2.com/grid-methodology)
and #3 in Gartner Peer Insights' Q2 2026 Voice of the Customer (4.6 stars across 1,247 reviews);
named in Forrester's 2026 Wave for Collaborative Work Management as a Strong Performer (Wave
report Q1-2026-CWM, page 14)."

**Score 0 (no)** — Vague qualitative claims only ("leading," "trusted by thousands," "industry-
best"); numbers without attribution; self-citation only — every linked source is a sibling page
on the same domain; quotes from un-named "industry experts." OR citation count is high but all
sources sibling-domain (passes surface-count, fails human-trust). OR evidence type is wrong for
the vertical (e.g., a healthcare page that cites only B2B-SaaS-style review aggregators; a legal
page that cites only blog posts and not statute / case law).

**Score 0.5 (unknown)** — Specific claims exist but attribution is ambiguous (e.g., "internal study,"
"based on customer data") such that an AI engine couldn't independently verify AND a human couldn't
defend the source to a peer. Emit 0.5 + "unknown" + one sentence on what attribution would resolve.

**Required CoT:**
- Step 1: List every specific claim on the page (numbers, named quotes, dated facts).
- Step 2: For each, identify the attribution / source / verifiability path; flag sibling-domain
  citations as failing the off-domain test.
- Step 3: Test whether the evidence type matches the page's vertical (Aggarwal-aware: statistics
  for Law / Opinion; quotation for People & Society / History; fluency-driven authority for Health
  / Business).
- Step 4: Emit verdict + one-sentence justification.

**Do not score:** number of citations as a count (routes to `structural_gate`); link-density;
presence of footnotes; URL HEAD resolution (routes to `structural_gate`); quote-grep verification
(routes to `structural_gate`).

### GEO-3 — Passage self-containment (AND-conjunction: mechanical standalone AND substantive content)

**Outcome question (binary):**
If each substantive 40-75-word block on the page is extracted standalone, does it read as a complete
claim with named entities — no floating pronouns, no "as mentioned above," no orphan context — AND
does each standalone passage carry substantive content (a domain expert reading the passage in
isolation would learn something), not mechanical entity-repetition? Would an AI engine retrieving
that single passage be able to use it directly in a citation-worthy answer?

**Score 1 (yes)** — At least 3 substantive passages on the page work standalone BOTH (a) mechanically
(headings restate the entity, pronouns resolve within the passage, lists work item-by-item without
depending on item 1 for context) AND (b) substantively (a domain expert reading the extracted
passage learns a non-trivial claim, not a repeated definition with entity-name reinforcement).

Example A — legal (do not optimize toward this, but the pattern): "Under the SHIELD Act
(N.Y. Gen. Bus. Law § 899-bb), any business that owns or licenses computerized data containing
private information of a New York resident must implement and maintain reasonable safeguards.
'Reasonable' tracks the FTC's 2022 Safeguards Rule revision: 5 administrative + 9 technical +
4 physical safeguards. Penalties accrue at $5,000 per violation."

Example B — AI-lab (do not optimize toward this, but the pattern): "Claude 4.7 supports 200K
input tokens and 64K output tokens per request, with prompt caching reducing repeated-context
cost by 90% on subsequent calls within a 5-minute TTL. Tool use latency averages 1.2s for
single-tool calls and 3.4s for multi-tool agentic loops per Anthropic's Q1 2026 latency
benchmark (anthropic.com/news/q1-2026-perf, published 2026-02-15)."

Example C — DTC e-commerce (do not optimize toward this, but the pattern): "Our 14oz cast-iron
skillet (Brand X Model Y) is pre-seasoned with grapeseed oil and ships in 3-5 business days for
$89 (current as of week of 2026-05-13; check product page for current pricing). Reddit r/castiron
discussion thread (May 2026, 247 upvotes) ranks Model Y in the top-5 of 24 cast-iron skillets
under $100 for heat retention and edge-finish."

**Score 0 (no)** — Passages depend on prior context. "This makes it…" "The above shows…" Pronouns
floating across paragraphs. Headings that don't name the entity. Lists where items 2-5 need item 1
for context. OR passages are mechanically self-contained via entity-repetition but substantively
empty — "Freddy ships content for regulated B2B" repeated three times passes mechanical self-
containment, fails the substance check.

**Score 0.5 (unknown)** — Some passages stand alone, others don't, and the failed passages are
ones an AI engine is likely to extract. Emit 0.5 + "unknown" + one sentence on which passages fail.

**Required CoT:**
- Step 1: Extract 3 substantive 40-75-word passages from the page (one near the top, one mid-page,
  one near the bottom).
- Step 2: For each, test mechanical standalone-coherence (pronouns, headings, lists).
- Step 3: For each, test substantive content (does a domain expert reading in isolation learn a
  non-trivial claim, or is it entity-repetition padding?).
- Step 4: Emit verdict + one-sentence justification.

**Do not score:** number of headings; presence of TOC; page structure beyond passages; word-count
band (routes to `structural_gate`).

### GEO-4 — Entity stability and third-party validation (AND-conjunction: canonical retrieval form AND external substance)

**Outcome question (binary):**
Does the page present the brand / product / service as a stable entity via canonical naming AND
survive a basic cross-source authority check — naming alternatives, citing third-party comparisons
or analyst coverage, quoting external voices — such that an AI engine would confidently associate
this page with one canonical entity AND a sophisticated human researcher would accept its claims
as off-domain-validated, not vendor-vacuum marketing?

**Score 1 (yes)** — BOTH (a) brand name canonically consistent across the page (no entity drift,
schema.org `sameAs` to at least one canonical KG anchor — Wikidata / Crunchbase / SEC EDGAR /
LinkedIn Company / Google Business Profile / registry .gov, tiered for SMB coverage; category
placement explicit — "an X for Y who need Z") AND (b) at least 2 external validations that are
off-domain, named, dated, and vertical-appropriate (analyst report for B2B SaaS; clinical
guideline + clinician byline for healthcare; statute + case citation for legal; SEC / FINRA /
FCA filing for fintech; arxiv / analyst-Substack for AI-lab; Reddit / community-review for DTC;
named partner / principal byline for professional services).

Example A — legal (do not optimize toward this): "DWF LLP (registered Solicitors Regulation
Authority no. 533585) is a UK-listed law firm; Restructuring and Insolvency practice ranked
Tier-2 by Chambers UK 2026 (chambers-and-partners.com/department/dwf-llp/restructuring); the
firm's Maciej Jamka was named in Legal 500's 2026 EMEA Banking & Finance hall of fame
(legal500.com/firms/dwf, 2026 edition)."

Example B — B2B SaaS (do not optimize toward this): "BambooHR (operated by BambooHR LLC, Utah,
USA, listed at bamboohr.com) is an HR information system for SMBs; ranked #1 in G2's Spring
2026 Core HR Grid (4.6 stars, 2,847 reviews; g2.com/products/bamboohr); named Leader in
Forrester's 2026 Wave for HR Service Delivery (Wave report Q1-2026-HRSD, page 9); used by
30,000+ companies per BambooHR's 2026 annual report (bamboohr.com/about, last updated 2026-04)."

Example C — AI-lab (do not optimize toward this): "Anthropic PBC (Delaware, founded 2021;
Crunchbase: crunchbase.com/organization/anthropic) is an AI safety lab whose Claude family of
models ranked #1 on the HumanEval coding benchmark Q1 2026 (papers-with-code 2026-03), #2 on
LMSYS Chatbot Arena (lmarena.ai/leaderboard, 2026-04 update); Latent Space podcast (latent.
space, 2026-02 episode) discusses Anthropic's constitutional-AI training methodology."

**Score 0 (no)** — Entity drift (multiple name variants across page). No category placement. Zero
external sources. "Trusted by [logo wall]" without per-logo attribution or context. Self-comparison
only (us-vs-old-us). All cited sources are sibling-domain. Vendor-vacuum framing. OR canonical
name is consistent but external validation is weak in vertical-appropriateness (e.g., a legal page
cites only marketing-platform reviews, not statute / case / Chambers / Legal 500).

**Score 0.5 (unknown)** — Entity is consistent but external validation is weak (one source, or all
sources are sibling-domain, or vertical-mismatched). Emit 0.5 + "unknown" + one sentence on what
would strengthen.

**Required CoT:**
- Step 1: Note the canonical entity name + category placement + canonical KG anchor (if present).
- Step 2: Identify external validation sources (must be off-domain, named, dated, vertical-
  appropriate); flag sibling-domain validations as failing.
- Step 3: Test whether the validation type matches the page's vertical (Chambers / Legal 500 for
  legal; clinical-guideline + clinician byline for healthcare; G2 / Gartner / TrustRadius for
  B2B SaaS; SEC / FINRA / FCA for fintech; arxiv / analyst-Substack for AI-lab; Reddit / Yelp /
  community-review for DTC; named partner / principal byline for professional services).
- Step 4: Emit verdict + one-sentence justification.

**Do not score:** logo wall presence; social proof aesthetics; testimonial volume; entity-existence
Wikidata lookup (routes to `structural_gate`); schema.org `sameAs` validity (routes to
`structural_gate`).

### GEO-5 — Format-intent match and vertical-conditioned freshness (AND-conjunction: format match AND substantive freshness at vertical cadence)

**Outcome question (binary):**
Does the page's structure match the format AI engines prefer for its declared query class (declared
via `geo_format` on the fixture brief, cross-checkable via URL slug / page title / H1) — comparison
→ table; how-to → ordered steps; what-is → definition + structured detail; listicle → ranked items
with methodology — AND does it carry the freshness signals AI engines weight at the vertical-
appropriate cadence (substantive currency in body content, not just date-stamp gaming)?

**Score 1 (yes)** — BOTH (a) page format matches its `geo_format` declaration and likely query
class (visible from URL slug, page title, or H1 — a `/best-X-for-Y` listicle page is structured
as a ranked list with at least one comparison table and disclosed methodology; a `/how-to-X` page
is structured as ordered steps with prerequisites + verification + troubleshooting blocks; a
`/what-is-X` definition page leads with a declarative entity definition) AND (b) freshness signal
is substantive at the vertical-appropriate cadence:

- **DTC pricing / shopping queries** — current-week date stamp; pricing visible in initial server-
  rendered HTML (not JS-only per Similarweb 2026 case study); inventory / availability dated.
- **Fintech rates / yields / regulatory** — current-month date stamp; rate / fee / APY data dated
  within 30 days; regulator-reference cited with current version.
- **B2B SaaS feature / pricing / comparison** — current-quarter date stamp; feature claims dated
  within 90 days; pricing visible server-rendered HTML.
- **Healthcare evidence-based explainer** — last-medically-reviewed within 24 months on stable
  conditions, within 90 days on emerging treatments; named-guideline citation with current version.
- **Legal statute / case citation** — last-reviewed within 12 months; statute-version-bound (a 1998
  statute citation with a 2026 last-reviewed stamp is correct, not stale); case citation with
  current Shepard / KeyCite-equivalent reliability check.
- **AI-lab API / SDK documentation** — per-release date stamp; version-pinned code examples; dated
  changelog; benchmark cards with reproduction methodology + date.
- **Evergreen explainer content (general)** — visible publication or update date within last 12-18
  months (the Perplexity 70% / 12-18 month finding holds as default).

**Score 0 (no)** — Format mismatch (a comparison page written as flowing narrative; a how-to page
without ordered steps; a listicle without disclosed methodology). No visible date anywhere. Stats
without years. OR "Last updated YYYY-MM-DD" current-year stamp on body content with no current-
year references, named-current-version-citation, or substantive freshness signal (the workflow has
gamed the stamp). OR freshness window is wrong for the vertical (a DTC pricing page with a 12-
month stamp; a fintech rate page with a quarterly stamp).

**Score 0.5 (unknown)** — Format matches but freshness signal is ambiguous (e.g., date present but
more than the vertical-appropriate window stale on a page making current-state claims; OR cadence
ambiguous from the artifact alone). Emit 0.5 + "unknown" + one sentence on which dimension is weak.

**Required CoT:**
- Step 1: Identify the page's declared `geo_format` (from fixture brief, cross-checked against URL
  / title / H1 query class).
- Step 2: Verify format matches that declared class (comparison → table; how-to → ordered steps;
  listicle → ranked items + methodology; definition → declarative lead + structured detail).
- Step 3: Identify freshness signals (publication date, last-updated, current-year refs, dated
  third-party citations) and test against the vertical-appropriate cadence.
- Step 4: Test whether freshness is substantive (body content matches stamp) or stamped-only
  (gaming).
- Step 5: Emit verdict + one-sentence justification.

**Do not score:** page-load speed; image-alt-text completeness; structured-data schema markup
specifics; mobile responsiveness; a11y (those route to `structural_gate`).

### GEO-6 — Evidence chain survives engine-side re-citation (NEW — documented ≤5-ceiling exception)

**Outcome question (binary):**
If an AI engine were to retrieve a passage from this page and synthesize an answer with one or two
of the documented LLM failure modes — similar-name conflation, source-anchor hallucination, partial-
attribute corruption, recency-cutoff distortion, or competitor-favorable reframing — would the brand
still come out correctly identified, correctly attributed, correctly time-framed, and not out-framed
by a competitor? Does the page's structure FORCE the engine toward correct synthesis rather than
relying on the engine to figure it out? Are the top-3 strategic claims on the page each backed by
named signals, verifiable sources, and acknowledged alternative interpretations?

**Score 1 (yes)** — Page contains ALL of:
(a) **Disambiguation against similar-name confusables** — explicit disambiguation block early when
the entity has a most-confusable similar-name target ("Anthropic, the AI safety lab founded 2021 —
not Anthropic Communications LLC"; "Cursor, the AI-native IDE — not Cursor Inc. the eye-tracking
device"). Singleton canonical name across H1 + schema.org `@id` + OpenGraph + BLUF.
(b) **KG anchor for inverted-citation-attack prophylaxis** — schema.org `sameAs` to at least one
canonical KG entry (Wikidata > Crunchbase > LinkedIn Company > Google Business Profile > registry
.gov, tiered for SMB).
(c) **Top-3 claims with named signals + verifiable sources + acknowledged alternatives** — the
headline, the dominant-positioning claim, and the strongest differentiation claim each (i) name the
specific signals they rest on, (ii) cite verifiable off-domain sources, AND (iii) acknowledge at
least one alternative interpretation the evidence does NOT rule out. Confidence is calibrated to
evidence depth.
(d) **Absolute-date framing for all temporal claims** so engines reasoning about "recent" don't
conflate with training-cutoff "recent" — no "recently," "in recent months," "today's," "the latest"
without absolute-date qualifier.
(e) **Comparison-claim symmetry where competitors are named** — every competitor claim (numeric,
dated, quoted) backed by off-domain citation; no asymmetry where brand claims are supported and
competitor claims are unsupported (or vice versa); no fabricated-competitor-claim injection.

Example (do not optimize toward this): "Klinika Melitus (Warsaw aesthetic dermatology, founded 2008
by Dr. Maria Noszczyk MD — not Klinika Mielitus the unrelated Krakow practice; sameAs:
crunchbase.com/organization/klinika-melitus) is one of three Warsaw clinics offering Daxxify (per
RealSelf's Warsaw provider directory, 2026-05-01; DermaCenter West and Beauty Klinik are the
comparable alternatives, also listed). Per AAD 2025 Clinical Practice Guideline, Daxxify shows
~24-week duration vs onabotulinumtoxinA's ~16 weeks at equivalent doses; tradeoff (per Revance
phase-3 NCT04823300): higher cost per treatment, similar efficacy. As of May 2026, our Daxxify
membership pricing is $1,200 / treatment; DermaCenter West's published rate (per their pricing
page, last reviewed 2026-04-15) is $1,150. Alternative reading: pricing differential reflects
operator-experience premium more than treatment cost; we cannot yet distinguish from 1 month of
data."

**Score 0 (no)** — Any of: similar-name conflation surface exposed (no disambiguation block when
one is needed); no KG anchor; top-3 claims confident-toned but evidence chain breaks under
inspection (unnamed signals, fabricated sources, single-source extrapolation, no disconfirming
alternative); relative-date framing on current-state claims; competitor-comparison framing
asymmetry; OR brief contains entity confabulations (competitors that don't exist, fabricated
quotes), source confabulations (404 URLs, unverifiable cited reports), or recency-cutoff
distortions (months-old "recent" announcements, training-cutoff landscape projected into present).

**Score 0.5 (unknown)** — Page is structurally clean but the disambiguation / anchoring / claim-
backing is too thin to evaluate engine resilience from the page alone. Emit 0.5 + "unknown" + one
sentence on what's missing.

**Required CoT:**
- Step 1: Identify the entity's most-confusable similar-name target (from page context); check for
  disambiguation block.
- Step 2: Identify the top 3 strategic claims on the page (headline + dominant-positioning + key
  differentiation); for each, walk the evidence chain — signals named, sources verifiable + off-
  domain, disconfirming alternative acknowledged.
- Step 3: For any competitor comparison, check claim-citation symmetry (no brand-supported-
  competitor-unsupported asymmetry); flag any fabricated-competitor-claim injection.
- Step 4: Check temporal framing — absolute-date for all current-state claims; flag relative-date
  drift.
- Step 5: Flag any entity confabulation (made-up entity, conflated similar-name), source
  confabulation (cited URL/paper/quote that doesn't exist), or recency distortion (months-old
  "recent" claim, post-cutoff event missed).
- Step 6: Emit verdict + one-sentence justification.

**Do not score:** URL HEAD resolution (routes to `structural_gate`); quote-grep cosine similarity
(routes to `structural_gate`); schema.org JSON-LD validity (routes to `structural_gate`); Wikidata-
entity-existence lookup (routes to `structural_gate`); date-stamp presence (routes to
`structural_gate`).

**Note on the ≤5 ceiling.** GEO-6 is a justified breach of design-guide §5's ≤5 criterion ceiling.
Rationale documented in §7 below. The redundancy check (§8) will tell us empirically if GEO-6
correlates with another criterion >0.7; if so, the redundant criterion gets dropped to restore 5.
Most-likely-to-merge: GEO-2 (evidence density) ↔ GEO-6 (evidence chain) — both test for traceable
evidence; CI parallel found CI-2 ↔ CI-6 absorption likely.

---

## 5. Shared judge-prompt wrapper

```
You are scoring a GEO-optimized page surface intended for DUAL READERS:
a human researcher querying an AI search engine (ChatGPT, Perplexity,
Claude, Gemini, Google AI Mode) AND that AI engine itself, which fans
out the query, retrieves candidate passages, reranks, and synthesizes
with citation. The human reader is a head of marketing at a mid-market
B2B SaaS doing vendor diligence, or an in-house counsel comparing legal
services, or a clinic operations lead evaluating healthcare brands —
smart, time-poor, skeptical, with authority to act on what they read.
The engine reader is the gating reader: a page that an AI engine won't
cite reaches no human.

The page conforms to a per-fixture `geo_format` declared on the brief:
one of {definition, how_to, comparison, listicle, faq, glossary,
pillar_hub, integration, pricing, product_landing}. The fixture's
geo_format is in source_data — the structural_gate has already enforced
form-factor-specific shape conformance + 8 AI-failure-routing checks
(URL HEAD, quote-grep, entity-existence, "as of" date, recency floor,
schema.org validity, FAQPage JSON-LD, broken-link). You see the page
content and the rubric.

Score each criterion independently with 0, 0.5, or 1 plus a one-sentence
rationale that follows the per-criterion CoT steps. Do not blend criteria.
Do not infer criteria not stated. If a criterion's condition is ambiguous
from the page alone, emit 0.5 + "unknown" + one sentence on what would
have to be present to commit to 1.

CRITICAL: each criterion uses AND-conjunction language in its score-1
anchor — the page must satisfy BOTH the AI-engine-extractable form AND
the human-trust-survivable substance to score 1. A page that satisfies
only one side scores 0. AND-conjunction is the Goodhart-resistant move:
weighted blends create tuning surfaces workflows learn to game.

The citation substrate varies by vertical — do not penalize evidence
sources because they're unfamiliar; do penalize evidence sources that
are wrong for the vertical (a healthcare page citing only B2B-SaaS-
style review aggregators; a legal page citing only blog posts and not
statute / case law; an AI-lab page citing only marketing claims and
not arxiv / GitHub / analyst-Substack). Test for whether an engine in
the page's vertical would cite AND a domain expert in the page's
vertical would trust — not for the presence of generic surface markers.

The page must SURVIVE engine-side re-citation distortion (GEO-6) —
similar-name conflation, source-anchor hallucination, partial-attribute
corruption, recency-cutoff drift, competitor-favorable reframing. The
page can't fully control downstream citation; but it can take specific
actions (disambiguation block, KG anchor, claim-citation symmetry,
absolute-date framing) that reduce the rate. The criteria test for
those actions.

Emit per-criterion JSON:
{"criterion_id": "GEO-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 6. Goodhart-resistance verification

### Per-criterion (cross-vertical surface-marker drift defense):

- **GEO-1**: "Declarative-shaped first sentence templated regardless of category" doesn't pass —
  must be a complete, extracted-standalone answer for the specific entity in the specific vertical
  with vertical-appropriate differentiation substance.
- **GEO-2**: "Three citations per section" doesn't pass — claims must be checkable AND off-domain
  AND vertical-appropriate evidence type (Aggarwal-conditioned).
- **GEO-3**: Mechanical self-containment ("name the entity in every paragraph") doesn't pass —
  passages must work as standalone substantive claims AND a domain expert reading in isolation
  must learn something non-trivial.
- **GEO-4**: Logo-wall stuffing doesn't pass — external validation must be off-domain, named,
  dated, AND vertical-appropriate (Chambers / Legal 500 for legal; clinical-guideline + clinician
  byline for healthcare; G2 / Gartner / TrustRadius for B2B SaaS; SEC / FINRA / FCA for fintech;
  arxiv / analyst-Substack for AI-lab; Reddit / community-review for DTC).
- **GEO-5**: "Last updated YYYY-MM-DD" without current-year substantive body content doesn't pass —
  freshness must be substantive AND at the vertical-appropriate cadence (week for DTC, month for
  fintech, quarter for B2B SaaS, 12-18 months for evergreen explainer, statute-version-bound for
  legal).
- **GEO-6**: "Confident strategic synthesis without underlying evidence chain" doesn't pass — top-3
  claims must have named signals + verifiable sources + acknowledged alternative interpretation;
  disambiguation block + KG anchor required when entity has similar-name confusable; comparison-
  claim symmetry required; absolute-date framing required. Entity confabulation / source
  confabulation / recency distortion / inverted-citation framing / competitive-injection each
  force a score 0.

### Per-vertical (Goodhart-collapse mode defense — 7 named modes from vertical-conventions §5):

- **Legal: "Attorney-bio + jurisdiction-scope theater"** — workflow plants attorney byline + bar-
  number + jurisdiction-statement on every page regardless of substance. Defense: GEO-4 requires
  vertical-appropriate validation (statute / case / Chambers / Legal 500) AND GEO-2 requires
  off-domain evidence type matching legal (statute citation, not blog posts).
- **Healthcare: "Clinical-guideline citation slot-fill"** — workflow drops NICE / USPSTF / AAD
  citations regardless of relevance. Defense: GEO-2 requires vertical-appropriate evidence type
  (clinical-guideline) BUT GEO-6 requires top-3 claims actually backed by named signals + alternative
  interpretation; slot-filled guideline citations without claim-chain integration fail GEO-6.
- **B2B SaaS: "Comparison-table-where-we-win"** — workflow produces comparison pages where home
  product wins every row. Defense: GEO-6 requires comparison-claim symmetry; asymmetric framing
  forces score 0. Also: Google AI Mode catches this pattern (Verge documentation) — the slot-fill
  is self-defeating but workflow may iterate.
- **Fintech: "Disclaimer / risk-disclosure prose density"** — workflow plants disclaimers on every
  page regardless of regulator-alignment. Defense: GEO-2 requires regulator-aligned evidence
  (SEC / FINRA / FCA filings + license disclosure), not just disclaimer prose volume; GEO-6 top-3
  claims must be backed.
- **AI-labs: "Vendor-benchmark table slot-fill"** — workflow drops self-reported benchmark scores.
  Defense: GEO-2 requires independent-eval sources (Epoch AI, Artificial Analysis, LMSYS, papers-
  with-code) as off-domain validation; self-reported benchmarks without cross-reference fail.
- **DTC: "Schema markup + Reddit-pull-quote fabrication"** — workflow injects schema everywhere +
  plants Reddit-style quotes that aren't sourced. Defense: `structural_gate` quote-grep against
  source corpus catches fabricated quotes; schema validity check catches schema-without-substance.
- **Professional services: "Head-to-head template repetition"** — workflow replicates X-vs-Y format
  on pages where comparison is the wrong format-intent. Defense: GEO-5 requires format-intent match
  to declared `geo_format`; comparison-shape on a definitional fixture fails.

Workflow that learns to slot-fill each criterion still has to produce a page an AI engine actually
cites AND a domain expert in the vertical actually trusts. Slot-fill alone scores 0 on at least
one side of the AND-conjunction. The dual-audience AND-conjunction at every criterion is the
structural defense against AI-first-AEO Goodhart collapse documented in the dual-audience-tension
research (over-optimization measurable signature: AI-citation rate stays high or rises, human
bounce rate rises 18-25%, time-on-page drops 30%+, conversion-from-AI-traffic drops).

---

## 7. Verification — does the v1 spec conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples
  (3 vertical examples per example-bearing criterion: legal / healthcare / B2B SaaS as load-
  bearing; fintech / AI-lab / DTC as alternates) ✓
- §5 criterion count: **6 (documented exception to ≤5 ceiling)** — see note below
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3-6 steps each) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §11 Goodhart-resistance verification: per-criterion + 7 per-vertical collapse modes ✓
- §13 specimen criterion template followed ✓

**Note on the ≤5 ceiling exception (justified breach per design-guide §5).** GEO-6 (Evidence chain
survives engine-side re-citation) is a 6th criterion justified by the AI-specific failure surface
documented in `docs/research/2026-05-18-geo-ai-failure-modes.md` with measured effect sizes from
2024-2026 literature the other 5 criteria structurally cannot catch:

- **Entity confabulation** at 19.9% GPT-4o citation-fab rate (Chelli et al. 2025); 14-95% range
  across 13 models × 40 domains (GhostCite / KGHaluBench arxiv 2602.19643).
- **Source confabulation** at 37% Perplexity / 22% OpenAI / 6% Claude failure rates (2025
  retrospectives); NeurIPS 2025 100-fab-citation incident with 27% Partial Attribute Corruption.
- **Recency / training-cutoff distortion** per LLMLagBench (arxiv 2511.12116): behavioral cutoffs
  6-18 months before release date; NAACL 2025 23-35% accuracy drop on relative vs absolute temporal
  framings.
- **Inverted-citation attack** per CompoundDeception benchmark + NeurIPS 2025 Partial Attribute
  Corruption + Identifier Hijacking.
- **Competitive injection** per HalluLens Nonsense + The Verge documentation of Google AI Mode
  catching vendor "best of" lists.

These failure surfaces require deterministic verification because **all three frontier judge-panel
families share the hallucination class** — the LLM judge panel (Claude Opus 4.7 + GPT-5.5 + Gemini
3 Flash) cannot catch them via reasoning alone. The deterministic checks live in `structural_gate`
(8 AI-failure-routing checks listed §3b); GEO-6 catches the *semantic* layer on top of those
deterministic checks (evidence-chain integrity, claim-citation symmetry, disambiguation against
similar-name confusables, absolute-date framing). The breach is justified per the design guide's
documented-exception clause: "When a lane's artifact has a documented LLM-specific failure surface
that the other 5 criteria cannot catch, a 6th criterion targeting that surface is permitted as a
documented exception. Required documentation: the failure mode must be cited from 2024-2026
literature with measured effect sizes; the spec must include the citation." Done — see effect
sizes above.

CI established the pattern with CI-6 (Evidence chain). GEO is the second documented exception
under §5; the design guide's exception clause explicitly names GEO as the prototype use case
("entity confabulation at 19.9% GPT-4o citation-fab rate, source confabulation at 37% Perplexity
failure shape, recency-cutoff distortion per LLMLagBench"). Subject to the same redundancy check
as the rest: the live count is probably 5 after the check runs — GEO-6 most likely absorbs into
GEO-2 (evidence density) since both test for traceable evidence chains. Don't fight the absorption
when it happens; the criteria are designed to surface the AI-failure surface regardless of whether
the rubric structurally needs a separate criterion to do it.

Length per criterion ≈ 250-300 words (longer than the design guide's 150-word target due to
explicit AND-conjunction prose + 3 vertical examples per example-bearing criterion; absorbable
because the dual-audience structural defense is the entire point). Total spec body ≈ 4500-4800
words including §1.5 + §3b expansions — matching CI v3.3 depth, not bloating beyond it.

---

## 8. Open questions (after 4 deep-research deliverables + dual-audience synthesis)

Reader / Artifact-shape / Success / Failure / 6 Criteria are LOCKED at v1. Remaining:

1. **Pairwise redundancy check pending (urgent).** Per design-guide §5, run pairwise correlation
   across re-runs of 5 fixtures × 6 criteria × 3 panel models = ~90 calls (~$35). Drop any criterion
   correlating >0.7 with another. Most-likely-to-merge pairs:
   - **GEO-1 ↔ GEO-3** (both touch passage structure — front-passage extractability and per-passage
     self-containment; flagged in dual-audience-tension research §10 recommendation 10; most likely
     fold: GEO-3 absorbs into GEO-1's anchor as "and at least 2 additional passages downstream also
     work standalone").
   - **GEO-2 ↔ GEO-6** (evidence density and evidence chain — CI parallel suggests this may absorb;
     both test for traceable evidence; if absorption confirms, restore to 5 criteria).
   Expected live floor: 4-5.

2. **Site_engine boundary — draw explicitly.** GEO judges ONE landing-page surface optimized for AI
   engine citation (single-page artifact); site_engine judges the FULL site as a coherent set of
   pages each playing a role in fan-out coverage. The 10-form-factor enum partially overlaps with
   site_engine — `pillar_hub` is explicitly site-architecture; `glossary` lives inside a glossary
   index. Recommended boundary: GEO owns single-page form factors (definition, how-to, comparison,
   listicle, product-landing, pricing, integration, glossary entry, FAQ); site_engine owns multi-
   page orchestration including pillar/hub topology and internal-link graph structure. Confirm
   when site_engine v1 spec lands.

3. **YMYL 6th-criterion exception status — probably no per redundancy check.** Per design-guide §5,
   a justified breach of the ≤5 ceiling is permitted when literature documents an LLM-specific
   failure surface other criteria can't catch. CI took the breach with CI-6 (Evidence chain); GEO
   takes the breach with GEO-6 (same shape). The analogous question for YMYL (legal / healthcare /
   fintech): is a 7th criterion warranted for "Vertical-appropriate authority signal — for YMYL
   pages, named-clinician / named-attorney + verifiable credential present"? Research read: probably
   no — YMYL gating is already captured by GEO-2 (evidence density with vertical-appropriate type)
   + GEO-4 (entity stability + vertical-appropriate third-party validation) when the score-1 anchors
   include healthcare-clinician + legal-attorney examples. Redundancy check resolves.

4. **Wikidata coverage tiering for SMB / regional clients.** Klinika Melitus is unlikely to have a
   Wikidata entry today. Schema.org `sameAs` to Wikidata becomes a non-starter for the long tail.
   Tier-1 ranked alternative anchors (per AI-failure-modes research §10): Wikidata > Crunchbase >
   LinkedIn Company > Google Business Profile > registry .gov. `structural_gate` accepts ANY of the
   canonical KG anchors, not Wikidata exclusively. Confirm tiering.

5. **Cosine-similarity threshold tuning for entity-disambiguation + quote-grep gates.** The proposed
   0.85 threshold is borrowed from arxiv 2604.03173 ("Detecting and Correcting Reference
   Hallucinations"). For GEO content, the appropriate threshold may be tighter (citation accuracy
   matters more than paraphrase tolerance). Mitigation: start at 0.85, instrument false-positive
   / false-negative rates over first 20 GEO fixtures, tune. Track per-fixture in `structural_gate`
   metrics output.

6. **First-cohort overfit re-validation triggers.** Current fixtures cover 3 of 5 load-bearing
   verticals (legal-DWF, healthcare-Klinika, AI-lab-Anthropic + Perplexity). Per vertical-conventions
   research recommendation 5, build 1 B2B SaaS + 1 fintech fixture before locking GEO criteria via
   empirical redundancy check. When DTC / fintech / hospitality / B2C app fixtures land — or any
   fixture from a vertical not in {legal-services, AI-lab, healthcare, B2B-SaaS, fintech} — trigger
   re-validation pass on the affected criteria. Specifically: form-factor distribution may shift
   (government's FAQ:listicle ratio is materially different from B2B SaaS's); per-vertical evidence
   convention may need parameter additions.

7. **March 2026 + April 2026 Google AI Overview algorithm updates — implications.** Multiple updates
   in scope: March 2026 core update (thin-listicle / intermediary-content / topical-bloat demotion);
   April 2026 update (templated AI-generated roundups + thin content demotion); May 7 2026 FAQ
   rich-results removal (schema-only signal now). The 76% → 38% drop in AI Overview citation overlap
   with organic top-10 (Ahrefs Q1 2026) is the headline structural shift — AI citation is diverging
   from organic ranking. Implication for the spec: do not encode SEO-era ranking-factor proxies as
   GEO criteria; the citation surface is different from the ranking surface. Monitor for further
   2026 updates that might shift form-factor citation share or freshness cadences.

8. **Engine-side downstream monitoring — deferred to monitoring lane.** Engine-side citation
   distortion (similar-name conflation, source-anchor hallucination, inverted-citation attack at
   retrieval time) is not testable from the page alone — needs live engine query. Recommended split:
   page-side prophylactic checks in `structural_gate` (entity-existence Wikidata-lookup, schema.org
   `sameAs`, quote-grep, URL HEAD) catch what the page can control; engine-side monitoring (weekly
   probe against ChatGPT / Perplexity / Claude / Gemini for the brand, with diff against page's
   canonical entity attributes) lives in the monitoring lane. Confirm split when monitoring lane
   v1 spec lands.

9. **Reranker recency bias — engine-side, unfixable from page-side.** Per arxiv 2509.11353, LLM-
   based rerankers prefer most-recently-dated retrieved content with effect ≈ +0.15 cosine-
   similarity boost. The page can signal freshness (GEO-5 + `structural_gate` "as of" date + recency
   floor) but cannot control reranker behavior. Flag for monitoring lane: periodic engine query +
   compare returned date vs page's absolute-date framing.

10. **Variance instrumentation per design-guide §11.5 — GEO is a likely candidate for early
    Goodhart drift** because the AI-engine-extraction surface is so heavily described in the
    literature that workflows have many templates to copy. Schedule variance-per-criterion-per-
    generation telemetry for GEO from generation 1, not on a delayed cadence. Track judge variance
    per criterion per generation; flag any criterion whose variance grows monotonically over 3
    generations, or whose mean compresses toward the middle, for redesign (NOT calibration — the
    pathology we burned three times: `2ce99bb`, `ca4a256`, `698e658`).

11. **Aggarwal domain-class mapping to gofreddy verticals.** Aggarwal's 25 domain classes don't map
    1:1 to gofreddy's client verticals. Worth a one-time mapping pass: for each first-cohort vertical,
    which Aggarwal class is the closest match, and which Aggarwal-method-lift therefore applies?
    This becomes the fixture-validation reference set. Working mapping: DWF legal → Law & Government
    (Statistics Addition dominant); Klinika healthcare → Health (Fluency dominant); Anthropic /
    Perplexity AI-lab → Computers & Electronics (or Business depending on framing — Fluency for
    Business framing); future B2B SaaS → Business (Fluency dominant); future fintech → Business
    or Law & Government depending on framing.

12. **Propagation to other 6 lanes.** Once GEO v1 validates on real fixtures (post redundancy check
    + multi-vertical fixture validation), propagate the iterated pattern to MON → MA → SB → X →
    LI → site_engine. Each lane gets its own Path-A iteration + (optionally) lane-customized deep-
    research pattern — NOT a mechanical repeat. The 4 GEO deep-research questions (vertical-
    conventions / artifact-taxonomy / AI-failure-modes / dual-audience-tension) were uniquely
    GEO-shaped — per-lane question scoping needed.
