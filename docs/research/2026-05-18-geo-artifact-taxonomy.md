---
date: 2026-05-18
type: research deliverable
status: complete
topic: GEO artifact taxonomy (page-type form factors for AEO/GEO surfaces)
parent: docs/handoffs/2026-05-18-judge-design-step1-geo.md
sibling: docs/research/2026-05-15-judges-domain-geo.md
pattern_reference: docs/research/2026-05-18-ci-artifact-taxonomy.md
---

# GEO Artifact Taxonomy — AEO Page-Type Form Factors

## 1. TL;DR + artifact-shape recommendation

Generative Engine Optimization is not one artifact. It is a portfolio of at least **ten canonical page-type form factors**, each with a distinct query class, locked structural shape, evidence convention, and citation behavior in 2026 AI engines. The current `geo` lane fixtures (`docs/handoffs/2026-05-18-judge-design-step1-geo.md`, v0) treat GEO as "single optimized landing-page surface" — a useful first-cohort approximation but one that flattens a real taxonomy and risks shape-drift Goodhart under 50-generation selection pressure.

The ten form factors are:

1. **"What is X" definition page** — entity-grounding surface, 600–1,500 words, declarative lead in 40–75 words.
2. **"How to X" instructional page** — process surface, 800–2,500 words, numbered/ordered steps with HowTo schema.
3. **"X vs Y" head-to-head comparison** — 1,200–2,500 words, mandatory comparison table, dual-entity symmetry.
4. **"Best of X" listicle / "Alternatives to Y"** — 2,000–4,500 words, ranked items with criteria disclosed, individual entry passages 100–200 words.
5. **FAQ page** (standalone or embedded) — question-as-heading + 40–75 word answer, FAQPage schema (now schema-only after Google killed FAQ rich results May 7 2026).
6. **Glossary entry / category hub child** — 200–500 word atomic definitions, DefinedTerm schema, cross-linked into a glossary index.
7. **Pillar / topic hub page** — orchestration surface, 1,500–3,500 words, narrative overview + structured sub-question outlets.
8. **Integration page** — "Tool X + Tool Y", 600–1,400 words, workflow + setup + limits + supported APIs.
9. **Pricing page** — public tier matrix, server-rendered (HTML), with SoftwareApplication/Offer schema.
10. **Product / category landing page** — brand-anchored entity definition + category placement + third-party validation block.

**Recommendation for v1: declare the artifact shape per fixture via a `query_class` workflow input, lock the form factor, and route shape-conformance into `structural_gate` per OpenRubrics design principle (Hard Rules → gate, Principles → judge).** Concretely: extend GEO's v0 spec with a §1.5 "Artifact shape (LOCKED)" block, scoped initially to the four highest-citation-volume form factors (listicle, comparison, definition, how-to), and add a `geo_format` enum to the fixture brief. Defer integration / pricing / product pages to a `geo_v1.1` fast-follow once first-cohort fixtures land. Do NOT collapse all ten shapes into one judge or one workflow — the divergent evidence conventions and divergent citation behaviors mean the same five outcome questions would produce different reward gradients across shapes and the workflow would drift the artifact toward whichever shape happens to be easiest to slot-fill against the current rubric.

The top failure mode the taxonomy surfaces that the v0 GEO spec does not catch: **shape-drift Goodhart** — workflow learning that "passages of 134–167 words score well on GEO-3 self-containment" while "tables get cited 4.2× more" produces a Frankenstein output that's a definition-shaped page with a forced-in comparison table and bolted-on FAQ section, none of which serve the page's actual query class. The fix is naming the shape per fixture, not designing a shape-agnostic judge.

---

## 2. Key questions answered (executive summary)

- **Canonical AEO page-type form factors:** ten identified above; the four with empirically dominant citation share in 2026 are listicle, comparison, definition, and how-to.
- **What makes each LOCKED shape:** form-specific word-count bands, structural conventions, schema markup type, citation conventions, freshness signals, and internal-link topology — detailed in §3.
- **Convergence across verticals:** declarative-lead + passage self-containment + named entity stability converge across legal / healthcare / SaaS / DTC. Divergent: evidence type (citations-to-statute in legal, citations-to-clinical-guideline in healthcare, citations-to-G2/Capterra in SaaS, citations-to-original-research in DTC), required schema (MedicalEntity in healthcare, SoftwareApplication in SaaS, Product in DTC), and freshness cadence (90-day in legal/healthcare, 30-day in SaaS, weekly in DTC).
- **Shape-drift Goodhart surfaces:** length bloat, keyword stuffing, FAQ-question gaming, schema-without-substance, hub-bloat, listicle-without-criteria, fake-table padding, freshness-stamp gaming (date-only updates).
- **Form factors losing citation share in 2026:** thin glossary entries (Google March 2026 update demoted), templated AI-generated roundups (April 2026 update), pure-FAQ pages without underlying article context (FAQ rich results killed May 7 2026, schema still useful for AI Overviews but rich snippet feature gone), and thin pillar/hub pages built for ad revenue (March 2026 "intermediary" demotion).

---

## 3. Per-form-factor deep dive

### 3.1 "What is X" definition page

**Query class.** Definitional / informational. "What is GEO," "What is GS1 Digital Link," "What is constitutional AI."

**Canonical exemplars.** Wikipedia introductory paragraphs (ChatGPT's #1 cited source globally, 7.8% of all citations, 47.9% of top-10 share); Mayo Clinic disease-overview pages; Stripe.com developer-product definition pages ("Connect is Stripe's solution for routing payments to third parties"); the introductory paragraphs of NIH MedlinePlus topic pages.

**Length convention.** 600–1,500 words. Tight on the upper bound — definition pages that exceed 1,500 are usually pillar-hub shapes mislabeled.

**Structural sections (in order).** Declarative-lead first sentence (40–75 words containing entity + category + differentiation) → expanded definition (paragraph 2, 150–250 words, mechanism / how-it-works) → who-it's-for / category-placement → key facts box (often a 4–6 row data block) → 2–3 named examples in the wild → optional related-concept disambiguation block → optional FAQ tail. Volpini's "Matryoshka paragraph" finding pins the load-bearing weight on the first paragraph; the rest of the page provides supporting passages an engine can fan out to retrieve.

**Citation density.** 4–8 inline citations, 2+ of which are off-domain authority. For regulated domains (legal, healthcare, finance), at least one citation to a primary source (statute, regulation, clinical guideline, FAQ rich-results killed May 7 2026 means schema-only signal now, no SERP feature).

**Schema markup.** Article + Organization + DefinedTerm (if entity is a term). Avoid stacking unrelated schema; Google's March 2026 update demoted HowTo schema on non-primary content.

**Internal-link topology.** Definition page receives links from all glossary children and from related how-to / comparison / pillar pages. It does NOT need to link out broadly — it's a destination, not a hub.

**Freshness signal.** Visible "Last updated" date within 12–18 months on stable concepts; within 90 days when the concept is itself in flux (e.g., evolving regulation, new product category). Profound 2025: 70% of top-cited Perplexity sources have a visible publication-or-update date within 12–18 months.

**Shape-drift Goodhart surfaces specific to this form.** "What is X? X is becoming increasingly important..." (query-mirroring lead, Aggarwal-documented negative signal); padding the definition with three paragraphs of brand storytelling before the actual answer; inserting an FAQ block of 8 questions just to claim FAQPage schema with no organic FAQ load.

### 3.2 "How to X" instructional page

**Query class.** Procedural / instructional. "How to set up SAML SSO," "How to file a defamation claim in Poland," "How to inject lip filler safely."

**Canonical exemplars.** Stack Overflow accepted-answer-derived "how to" pages (Stack Overflow is one of the top cited domains globally on technical queries); MDN web-platform tutorials; AWS/Stripe step-by-step API integration guides; Mayo Clinic patient-procedure pages; Indeed Career Guide procedural articles.

**Length convention.** 800–2,500 words. Process complexity drives length — a 5-step UI walkthrough is 800 words; a regulatory-filing procedure is 2,500.

**Structural sections (in order).** Outcome statement (what you'll have at the end) → prerequisites block (tools, accounts, prior knowledge, time required) → numbered steps (each step = heading + 1–3 paragraphs OR ordered-list items) → verification block (how to confirm it worked) → troubleshooting / common errors → next-step / related-procedure links. Each step must read as self-contained — passage-self-containment matters MORE on how-to pages because engines often extract a single step for a fan-out sub-query.

**Citation density.** Sparser than definition pages — 2–5 citations on the page, usually to authoritative docs (RFCs, vendor official docs, regulatory text). Step screenshots and inline code blocks substitute for citation density.

**Schema markup.** HowTo schema is the canonical fit, but post-March-2026 update Google demotes HowTo schema on non-primary content. Use HowTo only when the page IS a how-to as its primary purpose; if it's a how-to embedded in a broader article, omit. Article + Breadcrumb stays.

**Internal-link topology.** Links out to definition pages for terms used (entity grounding); links out to troubleshooting pages and related procedures (next-action surface). Linked from category hubs and from FAQ pages whose questions resolve to "you do this procedure."

**Freshness signal.** Critical. Procedural content rots faster than definitional. UI screenshots tied to product version; API endpoints tied to API version; regulatory steps tied to current regulation. Pages older than 12 months in fast-moving categories (SaaS, AI tooling) lose citation share at 3× normal rate.

**Shape-drift Goodhart surfaces.** Step-padding ("step 1: open your browser," "step 2: navigate to the URL," "step 3: log in") to inflate procedural rigor; mandatory inclusion of a screenshot in every step regardless of clarity; insertion of fake prerequisites to game the "complete-answer" signal; substituting marketing copy for steps ("step 1: choose Acme because it's the easiest").

### 3.3 "X vs Y" head-to-head comparison

**Query class.** Comparative / evaluative. "Stripe vs Square," "DWF vs Pinsent Masons," "Botox vs Dysport for forehead lines."

**Canonical exemplars.** G2 / Capterra / TrustRadius head-to-head pages; PCMag head-to-head reviews; CNET comparison articles; Healthline drug-vs-drug comparison pages; CompareTheMarket-style insurance comparisons.

**Length convention.** 1,200–2,500 words. The comparison table is the load-bearing surface; the prose around it earns its space by explaining trade-offs the table can't carry.

**Structural sections (in order).** Headline as claim (NOT "X vs Y" — "X vs Y: Choose X if you need A; choose Y if you need B") → at-a-glance summary table (5–10 dimensions) → per-dimension comparison sections (each 150–300 words, naming both entities, with a verdict per dimension) → use-case-fit block ("Choose X if..." / "Choose Y if...") → mention of any third option not in the head-to-head → fairness disclosure (who wrote this, methodology, when last updated).

**Citation density.** 6–12 citations. Both entities must be cited at parity — asymmetric citation (10 sources praising X, 1 source on Y) is a documented Goodhart signal that AI engines de-rank. Required citations: third-party reviews (G2, Capterra, TrustRadius, Gartner Peer Insights), original product docs from BOTH vendors, at least one neutral third-party comparison (analyst, journalist).

**Schema markup.** Article + (optionally) ItemList listing both entities + (where applicable) Product schema for each entity. Avoid Review schema unless the page is genuinely a review with a single subject; comparisons aren't reviews.

**Internal-link topology.** Receives links from "best of X" listicles featuring both entities; from each entity's product page; from category hubs. Links out to each entity's pricing page and integration page if SaaS.

**Freshness signal.** Hard requirement: any feature-table comparison must be dated within 6 months — product feature surfaces move fast enough that stale tables actively mislead. Last-updated date visible in the page header AND in the table header.

**Shape-drift Goodhart surfaces.** **Vendor-self-comparison** (the Verge documented Google AI Mode catching and flagging vendor-authored "best of" lists that placed their own products first — same dynamic applies to vendor-authored "X vs Y" comparisons where X is the vendor); **asymmetric depth** (X gets 4 paragraphs, Y gets 1); **fake-table padding** (a table with 30 rows where 20 are trivial dimensions like "supports email"); **conclusion-rigged-to-X** (every dimension verdict swings to X regardless of evidence).

### 3.4 "Best of X" listicle / "Alternatives to Y"

**Query class.** Commercial-investigational. "Best CRM for B2B SaaS," "Top aesthetic dermatology clinics in Warsaw," "Best LLM observability tools," "Notion alternatives."

**Canonical exemplars.** Wirecutter category guides; PCMag's "best [thing] for [purpose]" lists; NerdWallet's best-credit-cards pages; G2's best-of-category pages; The Verge's annual buyer's guides; healthcare's "Top 10 Cardiologists in City" sites (US News + Castle Connolly).

**Length convention.** 2,000–4,500 words. The longest of the canonical form factors. Each listed item earns 100–200 words of dedicated explanation + a structured at-a-glance row.

**Structural sections (in order).** Methodology / how we ranked block UPFRONT (criteria disclosed, sources reviewed, freshness window) → at-a-glance comparison table → per-item sections (each: item name as H2 + 1-line pitch + structured details: price / fit / pros / cons / proof point / link) → "honorable mentions" tail → "how we chose" expanded methodology → FAQ tail (mandatory on listicles per 2026 AI engine convention).

**Citation density.** Highest of any form factor. 15–30+ citations. Each listed item should cite to its product page AND to one external third-party validation (G2 / analyst / journalist). The methodology block itself cites to the data sources used.

**Schema markup.** ItemList is the canonical fit. Per Ahrefs 2026: triple stacking Article + ItemList + FAQPage is the practitioner-default for ranking-list pages. Each item can optionally carry Product schema if appropriate.

**Internal-link topology.** Receives links from FAQ pages, category hubs, and from comparison pages featuring 2 of the listed items. Links out to every listed item's product / category page AND to relevant comparison pages ("see also: X vs Y").

**Freshness signal.** Quarterly refresh minimum. Ahrefs 2026 ChatGPT-citation analysis: 79.1% of cited listicles were updated within the last year. Pages older than 6 months in competitive listicle categories lose citation share at 3× normal rate.

**Citation share in 2026.** **Dominant form factor.** Listicles account for 43.8% of all ChatGPT citations (Ahrefs 26,283-URL study, 750 search terms); 45.3% of ChatGPT and 47.0% of Google AI Mode classifiable citations. For commercial queries specifically, 40.86% of citations go to listicles. Network analysis from OpenPR 2026: 73% of B2B buyers now find vendors through AI-cited rankings, and AI engines preferentially cite listicles over brand-owned sites for "best of" queries.

**Shape-drift Goodhart surfaces.** **Methodology-block-without-substance** (criteria disclosed but no evidence they were applied); **rotating self-feature into #1 slot** (vendor-authored, vendor-wins-every-list); **stuffed-listicle** (15 items where only 5 fit the category); **fake-honorable-mentions** padding to inflate breadth; **criteria-section gaming** (criteria written to favor a predetermined winner). Specific to AI engines: **listicle-on-thin-domain** (Google April 2026 update: "thin listicles, templated roundups, and AI-assisted content with no original input were demoted at scale").

### 3.5 FAQ page (standalone or embedded)

**Query class.** Question-form. "Why does X happen," "Can I do Y," "Does X integrate with Y."

**Canonical exemplars.** Stripe.com developer FAQ; HubSpot Knowledge Base; Mayo Clinic patient FAQ; healthcare drug-FAQ pages; vendor product-FAQ pages.

**Length convention.** 600–2,000 words for a standalone FAQ page; embedded FAQ sections are 200–600 words appended to definition / how-to / comparison pages.

**Structural sections (in order).** No introduction — go straight to questions. Each Q+A pair: question as H2 or H3 (verbatim conversational question, not keyword-stuffed) + 40–75 word direct answer + optional link to deeper resource. Group questions thematically (e.g., "Getting started," "Pricing & billing," "Integrations").

**Citation density.** Light. 1–3 citations per Q+A pair; many Q+A pairs have zero inline citation (the answer IS the citation). External authority comes from the page's domain reputation, not from in-page citation depth.

**Schema markup.** FAQPage. **CRITICAL 2026 CHANGE:** Google deprecated FAQ rich results on May 7 2026 — the visual SERP feature is gone. FAQPage schema is still actively useful for AI Overviews (pages with FAQ schema are 3.2× more likely to appear in Google AI Overviews per ALM Corp 2026) and for ChatGPT / Perplexity citation retrieval. The schema is now an AI-engine signal, not a SERP-feature signal. Adding FAQPage schema with no underlying organic FAQ load violates Google guidelines and teaches AI engines to distrust the domain.

**Internal-link topology.** Linked from every commerce / pricing / product page (the "still have questions" tail); links out to definition pages for terms used and how-to pages for procedural answers.

**Freshness signal.** Per-question rather than per-page. Each Q+A should carry an implicit freshness anchor — if the answer references "current pricing" it must date-stamp; if it references a regulation it must cite the version.

**Shape-drift Goodhart surfaces.** **FAQ-question gaming** (inventing questions nobody asks to slot-fill FAQPage schema); **answer-padding** (the 40–75-word answer expanded to 300 words to game evidence-density signals); **non-organic FAQ** (FAQ section on a page where users have demonstrably no FAQ load — vendor product pages with 12 FAQ items where the product is a one-feature SaaS); **schema-without-substance** (FAQPage JSON-LD describing questions that don't appear visibly on the page).

### 3.6 Glossary entry / category hub child

**Query class.** Atomic-definitional. Within a category-glossary site or a brand glossary section.

**Canonical exemplars.** Investopedia term entries; HubSpot Marketing Glossary; G2 SaaS Glossary; legal-term glossaries (Cornell LII); medical term glossaries (MedlinePlus). Animalz's own AEO glossary is a working example of the form.

**Length convention.** 200–500 words per entry. Atomic. The discipline is to stay short — a glossary entry that exceeds 500 words has drifted into definition-page shape and should be promoted.

**Structural sections (in order).** Term as H1 → 1-sentence definition (the elevator definition) → 2–3 paragraph expansion → key example or use case → related terms cross-links → optional "deeper dive" link to parent definition page.

**Citation density.** Light. 1–3 citations. The glossary entry's authority comes from the parent glossary's overall reputation, not from per-entry citation stacking.

**Schema markup.** DefinedTerm within a DefinedTermSet. Article + Breadcrumb for the entry; the parent glossary index page carries the DefinedTermSet.

**Internal-link topology.** Receives links from every page that uses the term; links out to 3–5 related terms in the same glossary. This is where the form factor most resembles a knowledge graph — dense intra-glossary cross-linking is the value-add over a flat dictionary.

**Freshness signal.** Glossary entries are often evergreen; freshness signal is the parent glossary's "last updated" stamp on the index page, not the per-entry stamp.

**Shape-drift Goodhart surfaces.** **Glossary bloat** (hundreds of thin entries created to inflate site size — Google March 2026 update specifically demoted "intermediary websites" that "exist mainly to capture traffic"); **circular cross-linking** (every entry links to every other entry to game internal-link topology); **near-duplicate entries** (the same definition written 5 ways to capture keyword variants); **entries-with-no-traffic-intent** (glossary entries for terms nobody searches).

### 3.7 Pillar / topic hub page

**Query class.** Broad-category orchestration. "Marketing analytics," "Aesthetic dermatology," "Restructuring law."

**Canonical exemplars.** HubSpot pillar pages (the practitioner-canonical example, originally invented by HubSpot); Salesforce's "Customer 360" topic hub; Mayo Clinic's "Diseases & Conditions" category landing pages; Cleveland Clinic Health Hubs.

**Length convention.** 1,500–3,500 words. Long enough to carry narrative; short enough that the page's job is orchestration, not exhaustion.

**Structural sections (in order).** Headline + 1-paragraph topic framing → table of contents linking to sub-question outlets → 4–8 sub-topic sections (each 200–500 words with link out to deeper page) → original research / data block (the unique contribution that earns the hub's authority) → related-resources / further-reading block.

**Citation density.** 10–20 citations. The pillar earns its citation authority by serving as a category-defining synthesis; thin pillars get demoted.

**Schema markup.** Article + BreadcrumbList. Optionally CollectionPage if the page is genuinely a curated collection.

**Internal-link topology.** Links OUT to 8–20 cluster pages in deep cluster topology. Receives links FROM cluster children and (ideally) from external authority sites. The link-out topology is the load-bearing GEO signal — pillars without children are functionally orphan content.

**Freshness signal.** Quarterly refresh; pillar pages are evergreen-narrative but should be dated.

**Shape-drift Goodhart surfaces.** **Hub bloat** (overbuilt pillar with 30 sub-section stubs that don't have real children) — Google March/April 2026 updates specifically demoted "topic hubs built primarily around ad revenue" and "topical bloat"; **narrative-without-substance** (a 3000-word pillar that says nothing the cluster children don't already say better); **thin-content classifier hits** (pages with index bloat across thin children reflect badly across the entire domain per Google's Helpful Content system sitewide classifier).

### 3.8 Integration page

**Query class.** Workflow-specific. "Does Slack integrate with HubSpot," "Stripe + Shopify setup."

**Canonical exemplars.** Stripe's integration partner pages; HubSpot's app marketplace pages; Salesforce AppExchange entries; vendor-specific "Acme + Bravo" co-marketing pages.

**Length convention.** 600–1,400 words. Tight — the integration page's job is concrete workflow + technical specificity, not narrative.

**Structural sections (in order).** Title naming both tools → 1-paragraph "what this integration does" → "who it's for" → common workflows (3–5 concrete examples) → setup steps (link out to full setup how-to) → supported APIs / data flow / sync direction → known limitations → pricing / tier requirements → related integrations.

**Citation density.** Light. 2–5 citations to official docs from both vendors.

**Schema markup.** Article + SoftwareApplication (for the primary tool). The integration itself is not its own schema entity.

**Internal-link topology.** Receives links from listing-of-integrations pages, from category hubs, and from "best of X integrations" listicles. Links out to setup how-to, troubleshooting FAQ, and the partner vendor's reciprocal integration page.

**Freshness signal.** Critical — APIs change. Dated within 90 days at minimum.

**Shape-drift Goodhart surfaces.** **Integration-logo-wall pages** (visual-only, no structured content — Similarweb 2026: "Most SaaS companies underperform in AEO because they rely only on integration logo walls instead of creating structured integration landing pages"); **fake integrations** (page describes an integration that doesn't actually exist or is one-way only when described as bidirectional); **stub pages** that score on schema but have 50 words of content.

### 3.9 Pricing page

**Query class.** Bottom-funnel commercial. "Acme pricing," "Acme cost," "Acme alternatives by price."

**Canonical exemplars.** Stripe.com/pricing; Linear.app/pricing; Notion.com/pricing; Asana.com/pricing. The form is well-converged across SaaS.

**Length convention.** 800–1,800 words including FAQ tail.

**Structural sections (in order).** Tier matrix (3–5 tiers, server-rendered HTML, all prices visible) → per-tier feature lists → usage-based pricing breakdown (if applicable) → at-a-glance comparison of what changes between tiers → enterprise contact-sales block → FAQ tail (pricing-specific Q&A) → fairness / methodology disclosure if applicable.

**Citation density.** Zero. Pricing pages don't cite — they ARE primary source.

**Schema markup.** SoftwareApplication + Offer for each tier. Concrete prices in schema (not "Contact us").

**Internal-link topology.** Linked from product / category landing pages, comparison pages, and "best of X" listicles. Links out to feature pages, integration pages, FAQ pages.

**Freshness signal.** Whenever pricing changes. Dated stamp critical because pricing rots in days, not months.

**Shape-drift Goodhart surfaces.** **JS-rendered pricing** that AI engines can't extract — Similarweb 2026 case study: "A market leader in CRM recommendations appeared in only 23% of AI responses across eight AI systems, while a competitor with smaller market share but better-structured content appeared in 78% of responses. The market leader's pricing page was behind JavaScript while the competitor's site was plain HTML with pricing visible in the initial render." The lesson: pricing must be in the initial server-rendered HTML to be citation-eligible. **Hidden-tier games** (high-end tier "contact sales" only, no anchor price) reduce citation rate vs. competitors who publish anchor pricing.

### 3.10 Product / category landing page

**Query class.** Branded-entity + category. The shape closest to the v0 GEO spec.

**Canonical exemplars.** Stripe Connect product page; Linear product pages; Anthropic Claude product pages; Klinika Melitus's primary services-category pages; DWF's restructuring-practice landing page.

Already comprehensively covered in `docs/research/2026-05-15-judges-domain-geo.md` and `docs/handoffs/2026-05-18-judge-design-step1-geo.md`. The artifact-shape findings there map onto this single form factor. Notable: this is the form factor with the broadest variance across verticals — see §4 below.

---

## 4. Convergence vs divergence across verticals

**Convergent across legal / healthcare / B2B SaaS / DTC / AI-lab:**

- Declarative-lead in first 40–75 words (Volpini retrieval-document register; Perplexity 90/100-words finding holds across domains)
- Passage self-containment at 40–75 word block level (Profound 3.1× citation lift)
- Named entity stability (Kalicube entity SEO holds independent of domain)
- Third-party validation outside the brand's own domain (Forrester 2026 cross-domain pattern)
- Visible date stamping with current-year refresh
- Format-intent match (Shepard #6, holds independent of domain)

**Divergent across verticals (the parts that resist a one-judge approach):**

- **Evidence type required.** Legal: citation to statute / case law / regulator publication. Healthcare: citation to clinical guideline (NICE, NHS, AAD), peer-reviewed study, professional body. B2B SaaS: G2 / Capterra / TrustRadius / Gartner Peer Insights review aggregates. DTC: original research, customer-survey data, named user testimonials with dated context. AI-lab: arxiv preprints, named-researcher attribution, model-card-style benchmarks.
- **Schema markup mix.** Legal: minimal beyond Article. Healthcare: MedicalEntity, MedicalCondition, MedicalProcedure schema where applicable. B2B SaaS: SoftwareApplication, Offer. DTC: Product, Review, AggregateRating. AI-lab: ScholarlyArticle.
- **Freshness cadence.** Legal: 6–12 months (regulation moves slowly). Healthcare: 12–18 months on stable conditions, 90 days on emerging treatments. B2B SaaS: 30–90 days (feature parity moves weekly). DTC: weekly on price/promo, quarterly on category positioning. AI-lab: monthly (model versions iterate fast).
- **Authority tier expected.** Healthcare's exemplar authority bar is brutally high (Mayo, Cleveland, NIH, NHS — anything below this tier struggles to citation-compete). SaaS has a more permissive bar (G2 + a thoughtful first-party doc is enough). DTC's bar is more about review-volume than expert authority.
- **Listicle conventions.** B2B SaaS: methodology block expected and scrutinized. DTC: rated-by-customer-survey methodology dominant. Healthcare: licensed-clinician-rated listicles required (US News + Castle Connolly style). Legal: directory-style listicles (Chambers, Legal 500) are the genre default — vendor-authored "best of" listicles are rare and distrusted.

**Implication for v1 judge design.** The convergent items belong in lane-wide criteria (the current v0 criteria GEO-1 through GEO-5 cover most of these). The divergent items belong either (a) in `structural_gate` parameterized by `vertical`, or (b) in a per-vertical sub-rubric only invoked when the fixture's `vertical` field is set. Trying to absorb the vertical-divergence into the judge's outcome questions creates a prompt-bloat problem (the rubric grows to encompass every vertical's evidence convention) without a corresponding accuracy gain.

---

## 5. Shape-drift Goodhart surfaces — catalogue

Cataloguing the failure modes the taxonomy surfaces. Each is a specific way a 50-generation evolution loop would learn to slot-fill against the v0 judge:

1. **Length bloat.** Workflow learns that longer pages with more passages have more "extractable" passages to score against GEO-3 (passage self-containment). Result: 4,000-word product-landing pages where 2,000 of those words are filler that dilutes the actual answer.
2. **Keyword stuffing.** Aggarwal-documented negative signal — but a Goodhart workflow that's NOT scored on keyword stuffing might still drift toward it as it learns that repeated entity mentions strengthen GEO-4 (entity stability). The hedge is GEO-4's behavioral anchor must require entity stability via *canonical naming* and not via repetition.
3. **FAQ-question gaming.** Inventing questions nobody asks to claim FAQPage schema and score against any GEO criterion that rewards Q&A structure. ALM Corp / Google: schema-without-substance teaches AI engines to distrust the domain.
4. **Schema-markup-without-substance.** JSON-LD describing content the page doesn't actually carry. Per Frase.io 2026: "A 5-star rating schema on a page with no visible reviews is one of the fastest ways to erode AI trust in your site." Currently routed to `structural_gate` in v0 spec — must stay there.
5. **Hub bloat.** Pillar pages stuffed with stub sub-section links that have no real children. Demoted by Google March/April 2026 updates as "intermediary websites" / "topical bloat."
6. **Listicle-without-criteria.** "Best of X" rankings published with no disclosed methodology, no comparison criteria, no fairness disclosure. AI engines increasingly cross-reference listicle methodology blocks against vendor identity to catch self-puffery — vendor-authored "best of" lists placing their own product first get caught and de-ranked (the Verge documented Google AI Mode doing this).
7. **Fake-table padding.** Comparison tables with 30 dimensions where 25 are trivial. Inflates apparent comparison rigor; degrades actual decision-utility for the reader.
8. **Freshness-stamp gaming.** "Last updated YYYY-MM-DD" header touched daily by automation with zero body-content changes. Currently routed to `structural_gate` via the v0 spec's "current-year body content" requirement on GEO-5 — must require *substantive* freshness, not stamped freshness.
9. **Methodology-block-without-substance.** Listicles disclose criteria but the criteria are unmeasurable or unreviewed. The disclosure mimics methodological rigor; the underlying selection was vendor-driven.
10. **Asymmetric depth in comparisons.** "X vs Y" page with 70% of words devoted to X (when the vendor is X), 30% to Y. Catches as bias to AI engines via cross-source authority check.
11. **Methodology-block-with-zero-data-source-citations.** Listicle methodology says "we analyzed 200 platforms" with no data file, no link, no audit trail. Workflow learns this slots in cheap.
12. **Glossary bloat / near-duplicate entries.** Hundreds of glossary entries with marginal-utility coverage. Helpful Content classifier hits sitewide.

---

## 6. Form factors LOSING citation share in 2026

Tracking the citation-share trajectory specifically:

- **Pure FAQ pages (without underlying article context).** Google killed FAQ rich results May 7 2026; while FAQPage schema is still useful for AI Overview retrieval, standalone FAQ-only pages without surrounding contextual content are increasingly de-ranked relative to FAQ-sections-within-articles. The trend: FAQ as appendix, not as standalone page.
- **Thin glossary entries / hub-and-spoke pages with no spoke depth.** Google March 2026 update narrowed FAQ rich result eligibility AND demoted HowTo schema on supplementary content; April 2026 update demoted "thin listicles, templated roundups, and AI-assisted content with no original input." Glossary sites built for SEO scale alone are losing ground.
- **Templated AI-generated roundups.** "Top 10 X" pages produced at scale via generic AI without human curation. Danny Goodwin April 2026 analysis: 25–35% ranking decline in competitive niches for sites with "a high proportion of thin, unoriginal, or poorly structured AI content."
- **JavaScript-only pricing pages.** Server-rendered HTML is increasingly load-bearing. Pricing behind JS lost 55-point citation gap in the Similarweb 2026 CRM case study.
- **Vendor-authored "best of" listicles where vendor is #1.** Google AI Mode catches and demotes; the Verge documented the pattern.
- **Logo-wall integration pages.** Similarweb 2026: structured integration landing pages with workflows / setup / APIs are gaining citation share at the expense of logo-wall pages.

Form factors GAINING citation share in 2026:

- **Listicles with disclosed methodology + recent freshness.** 43.8% of all ChatGPT citations (Ahrefs); 79.1% of cited listicles updated within the year.
- **Comparison pages ("X vs Y") with parity in evidence depth.** Especially for commercial-investigational queries.
- **Definition pages with declarative-lead BLUF compliance.** Perplexity 90/100-words finding holds.
- **Structured integration landing pages.** Replacing the logo-wall.
- **Original-research-backed pillar pages.** Yext 4.31× citation multiplier for first-party data.

---

## 7. Recommendations for v1 GEO lane (concrete edits)

**Recommendation 1 — extend GEO v0 spec with §1.5 "Artifact shape (LOCKED)" block.** Mirror the CI v3.3 pattern. Name the shape per fixture via a `geo_format` enum: {`definition`, `how_to`, `comparison`, `listicle`, `product_landing`, `pillar_hub`, `pricing`, `integration`, `glossary`, `faq`}. Lock the form factor at the workflow input level, not via judge-prompt inference.

**Recommendation 2 — scope v1 to four highest-citation-share shapes.** Listicle, comparison, definition, how-to. These four account for the dominant share of 2026 AI citations and have the most stable structural conventions across verticals. Defer integration / pricing / glossary / FAQ / pillar / product-landing to v1.1 (or scope to `structural_gate`-only if they're not first-class judge targets).

**Recommendation 3 — extend `structural_gate` with shape-conformance checks per `geo_format`.** Following the CI v3.3 pattern of routing deterministic verification out of the judge:

- All formats: declarative-lead first-75-words check (regex / sentence-classifier); visible publication-or-update date; canonical entity-name consistency; HTML server-rendering check (no critical content behind JS).
- `listicle`: ItemList schema present; methodology block present; ≥5 items each with ≥100 words; per-item structured row (name + price + fit); FAQ tail present; quarterly-or-newer date stamp.
- `comparison`: at-least-one comparison table with ≥3 dimensions; both entities cited at parity (entity-mention count ratio between 0.7 and 1.3); both entities have at least one third-party citation; dated within 6 months.
- `definition`: word count 600–1,500; declarative-lead first sentence (no "What is X?" interrogative opener); Article + (optionally) DefinedTerm schema; ≥4 inline citations with ≥2 off-domain.
- `how_to`: ordered-list or numbered-heading structure; prerequisites block; verification block; HowTo schema (only if the page IS a how-to as primary purpose); dated within 12 months.

**Recommendation 4 — preserve v0's 5 outcome criteria as form-factor-agnostic.** GEO-1 (BLUF) / GEO-2 (evidence density) / GEO-3 (passage self-containment) / GEO-4 (entity stability + third-party validation) / GEO-5 (format-intent match + freshness) are the convergent items across §4 — they're correctly designed as form-factor-agnostic outcome questions. The form-factor-specific items belong in `structural_gate` (per OpenRubrics design principle), not as 6th-7th-8th judge criteria.

**Recommendation 5 — do not add a 6th criterion for shape-conformance.** §5 of the design guide caps at 5 with documented exceptions; shape-conformance is verifiable, not principled, and therefore belongs in `structural_gate`. Adding a "GEO-6: Form matches its locked shape" criterion would replicate the CI-6 justified-breach pattern but without the AI-specific failure surface justification CI-6 carries (CI-6 catches semantic evidence-chain integrity that no deterministic check can; shape-conformance IS deterministically checkable).

**Recommendation 6 — vertical parameterization is a v1.1 concern, not v1.** Convergent criteria cover most of the value. Per-vertical evidence convention divergence (legal vs healthcare vs SaaS vs DTC) is real but not blocking — current first-cohort fixtures (DWF / Klinika / Anthropic / Perplexity / hypothetical SaaS / DTC) can use the convergent criteria with vertical-specific `structural_gate` parameterization if needed. Don't fork the judge.

---

## 8. Open questions

1. **Empirical citation-share by form factor at gofreddy fixture scope.** All cited per-form-factor citation-share data above is from large-scale third-party studies (Ahrefs 26K-URL, Wix data, ALM Corp). gofreddy's first-cohort fixtures (DWF, Klinika, Anthropic, Perplexity) may have different distributions because they're domain-specialist clients with narrow query surfaces. Worth running a small fixture-level pilot to confirm the form-factor distribution matches expectations before locking the v1.1 scope.
2. **Pillar / hub orchestration handled by `geo` lane or `site_engine` lane?** The boundary identified in v0 GEO spec open question #3 sharpens here. Pillar / hub pages are explicitly site-architecture concerns and may belong in `site_engine` rather than `geo`. Recommend drawing the boundary as: `geo` owns single-page form factors (definition, how-to, comparison, listicle, product-landing, pricing, integration, glossary entry, FAQ); `site_engine` owns multi-page orchestration including pillar/hub topology and internal-link graph structure.
3. **Per-vertical `structural_gate` parameterization timing.** Whether to ship vertical parameters at v1 (legal / healthcare / SaaS / DTC parameters) or defer to v1.1. Risk of deferring: first-cohort fixtures may produce gaffes (e.g., a legal-services product page that fails healthcare's evidence-convention test by accident). Risk of including: adds workflow surface area before the convergent criteria have been validated.
4. **How to handle FAQ-tail-embedded-in-other-shape.** Most listicles and definitions in 2026 carry an FAQ tail. Should the gate require it on every page (current Ahrefs convention) or treat it as optional? Recommend optional-but-rewarded — required-FAQ-tail would push the workflow toward FAQ-question gaming.
5. **`geo_format` enum stability.** The 10-shape taxonomy here is the 2026 working set; adjacent shapes likely emerge as AI engines evolve (e.g., conversational-thread-extracted pages from Reddit, model-card-anchored AI-tool pages). Bake versioning into the `geo_format` field so the enum can extend without breaking historical fixtures.
6. **Multi-page artifact handling (carried forward from v0 spec open question #1).** If a future fixture produces a full site rather than one page, GEO judge needs an aggregate-mode that scores across the page set. Recommend deferring to `site_engine` lane rather than expanding GEO's scope.
7. **First-cohort overfitting watch (mirrors CI v3.3 §1.5 pattern).** The form-factor distributions and the per-vertical evidence conventions above are research-grounded against legal / AI-lab / healthcare / B2B-SaaS / DTC fixtures — gofreddy's first-cohort + nearest-adjacent verticals. When fixtures from new verticals appear (hospitality, marketplaces, regulated finance, education, government), re-validate. Specifically: form-factor distribution may shift (e.g., government's FAQ:listicle ratio is materially different from B2B SaaS's); per-vertical evidence convention may need parameter additions (e.g., financial regulation requires SEC/FCA citation conventions not in the current set).

---

## 9. Citations (graded by authority tier)

**Tier 1 — peer-reviewed / canonical academic:**
- Aggarwal et al., "GEO: Generative Engine Optimization," [arXiv:2311.09735](https://arxiv.org/abs/2311.09735) (KDD 2024). GitHub: [GEO-optim/GEO](https://github.com/GEO-optim/GEO). Cited throughout; foundational empirical work on GEO methods and visibility lift.

**Tier 2 — large-scale industry data analyses:**
- Ahrefs, ChatGPT 26,283-URL citation analysis (750 search terms), reported via [Linkbuilding Journal listicle-placement analysis](https://linkbuildingjournal.co.uk/listicle-placements-ai-citation-tactic/) and aggregated in [ALM Corp's listicle/article/product-page citation breakdown](https://almcorp.com/blog/ai-citations-listicles-articles-product-pages/) — 43.8% of ChatGPT citations to listicles; 79.1% updated within the year.
- Ahrefs Q1 2026 AI Overview top-10 study (863K SERPs), [ALM Corp summary](https://almcorp.com/blog/google-ai-overview-citations-drop-top-ranking-pages-2026/) — 38% AI Overview citations from top-10 (down from 76% in 2025).
- Yext, 17.2M-citation analysis (cited via Patel-Long brand-mention work) — first-party data → 4.31× citation occurrences.
- Profound, "AI Platform Citation Patterns," [tryprofound.com](https://www.tryprofound.com/blog/ai-platform-citation-patterns) — passage-length and table citation findings.
- Wix March 2026 AI citation data via [ALM Corp](https://almcorp.com/blog/ai-citations-listicles-articles-product-pages/) — listicle 21.9%, article 16.7%, product page 13.7% citation share.

**Tier 3 — practitioner / industry analyst:**
- Cyrus Shepard, "AI Citation Ranking Factors Analysis," [Zyppy Signal](https://signal.zyppy.com/p/ai-citation-ranking-factors) — meta-analysis of 54 experiments; ranking-factor weights informed multi-form-factor design.
- Andrea Volpini (WordLift), retrieval / fan-out / Matryoshka paragraph analyses on [wordlift.io/blog/en](https://wordlift.io/blog/en/) — declarative-document register rationale.
- Jason Barnard / Kalicube — Entity SEO and AEO origin coinage on [kalicube.com](https://kalicube.com/).
- Animalz, "Glossary of AEO and AI Search Terms," [animalz.co/blog/aeo-glossary](https://www.animalz.co/blog/aeo-glossary) — working glossary-entry form-factor example.
- Klue, [klue.com/blog/competitive-intelligence-reporting](https://klue.com/blog/competitive-intelligence-reporting) — pattern reference for executive-briefing-shape locking (used as taxonomy parallel from CI lane).

**Tier 4 — search engine / platform updates (2026):**
- Google FAQ rich results deprecation May 7 2026 — [ALM Corp summary](https://almcorp.com/blog/google-faq-rich-results-no-longer-supported/), [Workfx blog](https://blogs.workfx.ai/2026/05/13/google-canceled-faq-rich-results-faq-schema-ai-search-importance/), [NO-BS Marketplace blog](https://nobsmarketplace.com/blog/google-officially-kills-faq-rich-results).
- Google March 2026 core update / April 2026 update — analyzed in [Eclipse Marketing](https://eclipsemarketing.io/google-core-algorithm-update/), [Clickrank algorithm updates 2026](https://www.clickrank.ai/google-algorithm-updates/); covered hub-bloat, thin-listicle, and intermediary-content demotion.
- HowTo schema demotion on non-primary content — [Digital Applied schema-after-March-2026](https://www.digitalapplied.com/blog/schema-markup-after-march-2026-structured-data-strategies).

**Tier 5 — practitioner-domain references:**
- Similarweb SaaS-AEO product-pages analysis 2026 — [similarweb.com/blog/marketing/geo/aeo-for-saas-product-pages](https://www.similarweb.com/blog/marketing/geo/aeo-for-saas-product-pages/) — CRM market-leader case study (23% vs 78% citation rate from JS-rendered vs HTML pricing).
- SEM Nexus "AEO for SaaS: Dominate AI Search 2026" — [semnexus.com/aeo-for-saas](https://semnexus.com/aeo-for-saas/) — integration page anti-patterns.
- Search Engine Land "Mastering GEO 2026" — [searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142](https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142) — page-template practitioner consensus.
- The Verge documentation of Google AI Mode catching vendor-authored "best of" lists (referenced in GEO domain research deliverable; original Verge URL via that sibling document).
- Frase.io "FAQ Schema for AI Search," [frase.io/blog/faq-schema-ai-search-geo-aeo](https://www.frase.io/blog/faq-schema-ai-search-geo-aeo) — 3.2× AI Overview rate for FAQ-schema pages.

**Cross-reference — gofreddy internal documents:**
- `docs/research/2026-05-15-judges-domain-geo.md` — sibling domain research; this taxonomy deepens §2 (failure modes) and §4 (proposed judge criteria) by adding the form-factor dimension.
- `docs/research/2026-05-18-ci-artifact-taxonomy.md` — pattern reference; this document mirrors its structure (taxonomy → per-shape deep dive → cross-shape synthesis → recommendation → open questions).
- `docs/handoffs/2026-05-18-judge-design-step1-geo.md` v0 — the spec this research informs.
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` v3.3 — the §1.5 LOCKED pattern this research recommends mirroring.
- `docs/rubrics/judge-design-guide.md` v2.1 — the OpenRubrics Hard Rules → `structural_gate` / Principles → judge split this research preserves.
