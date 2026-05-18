---
date: 2026-05-18
type: judge-design Step 2 — site_engine domain-deepening research
status: living document; feeds the v1 site_engine judge spec
parent: docs/handoffs/2026-05-18-judge-design-step1-site-engine.md
companions:
  - docs/research/2026-05-18-judges-domain-site-engine.md (do not restate — this deepens)
  - docs/research/2026-05-18-geo-dual-audience-tension.md (parallel sibling — site is broader)
  - docs/rubrics/judge-design-guide.md
axis: dual-audience tension (human visitor conversion vs AI engine citation) on landing-page surfaces
constraints:
  - outcome-questions, not feature-checks
  - reference-free, no framework-name embedding in criterion prose
  - behavioral binary anchors
  - first-cohort overfitting watch (Klinika / DWF / Anthropic-Perplexity / b2b-tech archetypes)
boundary_to_geo_lane: GEO judges a single page optimized for AI citation; site_engine judges full landing-page surfaces serving both humans AND AI engines as co-equal readers
---

# Site Engine — Dual-Audience Tension on Landing Pages

## TL;DR

A 2026 landing page has two co-equal readers — the human visitor (founder/recruiter/diligence-prospect deciding in ~10 seconds whether to engage) and the AI search engine (deciding per-passage whether to cite the page in answers to category queries). Roughly two-thirds of the design surface is dual-aligned: clear value proposition, named-customer-with-outcome social proof, visible pricing or pricing shape, freshness signals, entity-stability, third-party validation. These levers reward both readers simultaneously, and the marketing-tech consensus in Q1-Q2 2026 (HubSpot's 27% AI-traffic-to-SQL data, Adobe-Ahrefs 14.2% AI-converting-traffic vs 2.8% organic, Tatvic's "no tradeoff" reframing) has crystallized around the claim that AEO and CRO reinforce each other on the bulk of the page.

But the marketing-tech consensus has flattened the actual structure. There IS a tradeoff — it lives on roughly one-third of the landing-page surface, and that third is where workflows under selection pressure will collapse. The four real conflict points: **(1) keyword-and-schema density vs hero scannability** (the AI engine rewards entity-rich passages with extractable claims; humans bounce off prose that reads like reference-document register at the hero); **(2) FAQ / glossary depth vs above-fold conversion path** (FAQ schema is one of the highest-impact AEO levers and humans treat a long FAQ as friction in the conversion path); **(3) declarative claim vs warmth + named customer voice** (AI engines prefer canonical-form entity statements with verifiable specifics; humans convert on warmth, story, named-human social proof); **(4) third-party-validation depth vs visual breathing room** (Q1 2026 data: 85% of brand discovery happens through external mentions, but rendering off-domain validation on-page eats viewport real estate the human conversion path needs).

The single most important 2026 AEO update for this lane: Ahrefs Q1 2026 measured AI Overview citation overlap with Google's top 10 dropped from 76% to 38% over twelve months. Citation diverges from organic ranking faster than expected. A landing page that ranks but is not citation-shaped LOSES the AI-engine reader entirely, no matter how well it converts. A landing page that's citation-shaped but un-warm LOSES the human reader. The judge must score both outcomes against the same artifact — not as a weighted blend (which is Goodhart-tunable) but as an AND-conjunction on every criterion that touches the conflict surface.

Three of the proposed site_engine criteria (SE-1 human CTA, SE-2 AI citation, SE-5 freshness/entity-stability) directly straddle the dual-audience axis. The judge's score-1 anchors on those criteria must require behavioral evidence of BOTH outcomes — not the surface markers of either. The recommended escalation for v1: keep the five outcome questions in the Step-1 spec; rewrite their score-1 anchors so each criterion that lives on the conflict surface demands the AND-conjunction explicitly in its behavioral description.

---

## Key questions answered

**Q1. When do human-visitor and AI-engine interests CONFLICT on a landing page?** Four measurable conflict surfaces, each backed by 2026 data: (a) entity / keyword density beyond the hero — AI citation lifts from entity-rich passage density (Aggarwal +30-40% Statistics/Quote/Cite injection, replicated in 2026 GEO benchmarks) but humans bounce on entity-bloated copy at +5% per "delve/leverage/synergize/optimize" usage per Digital Applied 2026 2,000-page study; (b) FAQ / glossary surface — FAQPage schema is among the highest-leverage AEO moves but a long FAQ above the conversion CTA depresses CVR per Wynter user-testing 2025-2026 data; (c) declarative-document register at the hero — AI engines reward "Linear is the modern issue tracker for high-performing software teams" canonical-form leads, humans on B2B SaaS pages convert on warmth + named-human voice + named-customer story; (d) third-party-validation rendering — AI engines weight brand mentions off-domain at r=0.664 (Ahrefs) and require visible third-party validation on-page to corroborate, but every analyst quote / press logo on-page consumes viewport real estate humans need for proposition and CTA.

**Q2. Which page elements serve HUMAN-only, AI-ENGINE-only, and BOTH?** Human-only: warm photography of named team, hand-drawn or illustrated brand artwork, manifesto / brand-narrative paragraphs, motion / micro-interactions, video testimonials with visible faces, demo embeds. AI-engine-only: schema.org markup (Organization, Product, FAQPage, BreadcrumbList), JSON-LD structured data, sitemap-discoverability signals, semantic-triple statements (subject-predicate-object) consumable by knowledge graphs, current-year reference embeddings the engine can date-stamp. BOTH: the hero proposition stated declaratively + memorably; named customer with named outcome ("Used by Dentons and Pinsent Masons since 2025" with footnote link); visible pricing or pricing shape; one primary CTA; specific dated claims; founder name surfaced; freshness signal (changelog, dated blog, current-year copy); category placement; consistent canonical entity naming. The BOTH category is the bulk of the page and the bulk of conversion + citation lift; the conflict surface is narrower than the marketing-tech "win-win" consensus admits.

**Q3. Failure mode where SEO/AEO tanks human conversion.** Three measurable shapes: (1) keyword-bloated copy — Digital Applied 2026 study of 2,000 pages found pages with "delve / leverage / synergize / optimize your experience" lose 8% CVR average; pages with > 2 em-dashes per 100 words lose 5%; pages with "amazing / innovative / cutting-edge" lose 4%. (2) FAQ-stuffing above the CTA — AEO-driven workflows pile 8-15 FAQ entries above the demo CTA to maximize FAQPage schema yield; Wynter / CXL testing shows human visitors bounce on the perception of complexity, especially founders in evaluation mode. (3) Hero replaced with declarative-document-register lead — "Acme Corp is a content engine for regulated B2B verticals serving legal, financial, and healthcare clients with AI-native research workflows" parses cleanly for an AI engine but reads as machine-generated to a human and is the exact register the 2026 AI-content-hurts-conversion studies measure as the cause of the 18% bounce-rate delta.

**Q4. Failure mode where conversion-optimized copy loses AEO citation share.** Four measurable shapes: (1) no FAQ / glossary / answer-shape content — pages converted via CRO-only optimization in 2018-2022 era frequently have hero + features + testimonials + CTA and ZERO content shaped as "Q: ... A: ..." or "What is X?" passages, costing the AEO citation channel entirely. (2) query-echo or manifesto hero — "What if your content engine could finally..." or "We believe content should..." opens parse poorly for AI engines that want declarative-document register from the first 100 words; Perplexity / ChatGPT top-cited pages answer the core question in the first 100 words 90% of the time. (3) entity-name drift across sections — "Freddy" / "freddy.ai" / "GoFreddy" / "Gofreddy Inc." inconsistently named across hero, footer, schema, FAQ fragments knowledge-graph ingestion; AI engines cite the canonical-name page over the drifting one. (4) zero off-domain validation visible on-page — Q1 2026 AirOps data: 85% of brand discovery in AI search happens through external mentions; pages without visible analyst / customer / press citation give the AI engine nothing to corroborate against.

**Q5. How does the judge score the BALANCE?** Not by weighted blend (Goodhart-tunable: workflow learns to max the cheap side and pay the floor on the expensive side). Not by page-type toggle (creates a feature-checking pre-classifier). The judge scores via AND-conjunction at the criterion level: every criterion that touches the conflict surface (SE-1, SE-2, SE-5) requires score-1 anchor evidence for BOTH the human-visitor outcome AND the AI-engine outcome on the same artifact. If a page is human-warm but AI-uncitable, SE-2 fails. If a page is AI-citable but human-cold, SE-1 fails. The score-1 anchors hedge an exemplar but require the AND-conjunction in the behavioral description. The judge does NOT score "weighted dual-audience excellence"; the judge scores whether the artifact clears both binary outcome tests.

**Q6. 2026 AEO updates: what changed in how engines cite landing pages?** The single largest delta: Ahrefs Q1 2026 measured AI Overview citation overlap with Google's top 10 dropped from 76% to 38% over twelve months. Citation has decoupled from ranking faster than the SEO industry anticipated. Three concrete shifts: (a) brand-mention weight rose — r=0.664 brand-mention correlation with citation vs r=0.218 backlinks (Ahrefs 2026); (b) external validation dominates — 85% of brand mentions that drive AI discovery come from off-domain sources; (c) semantic-completeness scoring surfaced — passages scoring 8.5/10+ on semantic completeness are 4.2× more likely to be cited (per Wellows / PPC.land 2026 analyses citing Google's apparent extraction model). Landing pages that succeeded in 2024 by ranking organically without entity-grounding and third-party validation increasingly FAIL the citation test in 2026 even when the rank position is preserved. This is the load-bearing 2026 update for the site_engine judge: a page can rank #1 and be cited 0 times.

---

## Research synthesis (2500 words)

### 1. The two readers consume the artifact differently — and the difference is not academic

The site_engine lane's artifact is a landing-page surface: a single HTML page, possibly with deep links to product / pricing / about / FAQ subpages, intended as the primary entry point for new visitors. Unlike the GEO lane (which scores a single page optimized for AI citation) or the marketing-audit lane (which scores a written audit deliverable), the site_engine artifact is consumed by both audiences in real time on the same surface. The dual-reader posture is not a theoretical complication — it is the core engineering constraint.

The human visitor in 2026 arrives with one of three intent shapes (per CXL hero-audit framework and Wynter B2B testing data): the founder evaluating a vendor for a near-term problem; the recruiter or candidate checking legitimacy; the prospective client doing diligence after a referral. All three resolve in ~10 seconds whether to commit attention to the page. The conversion path requires: a hero that answers "what / who-for / why-different" without scroll, one primary CTA, named social proof in viewport, pricing visibility, and friction-removed CTA path. CXL's 6-second test is the binding-constraint operationalization.

The AI search engine in 2026 consumes the same surface as a passage-extraction candidate. Per Profound's 2025-2026 citation-pattern work, Perplexity-cited pages answer the core question in the first 100 words 90% of the time. Per Ahrefs Q1 2026: only 38% of AI Overview citations now come from Google's top 10 — citation has decoupled from organic ranking, and the page must earn citation on its own merits. The AI engine operationalizes: passage self-containment (40-75 words, claim complete, entity named in canonical form), evidence injection (statistic + named source + dated reference), schema.org markup interpretation, semantic completeness scoring, third-party-validation cross-referencing.

The two readers AGREE on roughly two-thirds of the page surface. They DISAGREE on the remaining third, and the disagreement is the focus of this research deliverable.

### 2. Where the two readers agree (the bulk of the page)

The marketing-tech consensus in 2026 — Tatvic's "Landing Page Optimization Has Two Audiences" piece, HubSpot's AEO guide, ALM Corp's AEO-vs-SEO playbook, CXL's AEO guide, Conductor's AEO trends report — has crystallized around the claim that AEO and CRO reinforce rather than compete on the bulk of the page. This consensus is empirically defensible. HubSpot reports 27% AI-traffic-to-SQL conversion among early AEO adopters; AirOps reports 31% higher conversion from AI-pre-qualified visitors; Adobe-Ahrefs report 14.2% conversion on AI-referred traffic vs 2.8% on organic. The traffic that arrives via AI engine is pre-qualified and converts at multiples of organic baseline.

The dual-aligned levers — those that reward both readers simultaneously — cover most of the landing-page surface:

**Specific value proposition + category placement at the hero.** "Linear is the modern issue tracker for high-performing software teams" passes the CXL 6-second test for humans AND parses as a citable canonical-form entity statement for AI engines. Vague benefit copy ("save time," "increase productivity") fails both readers; specific category-placed propositions ("Stripe is payments infrastructure for the internet") succeed for both.

**Named-customer-with-named-outcome social proof.** Stripe's "Used by millions of businesses, from startups to public companies" + named-customer logos linking to case studies is the canonical pattern. Humans treat the named-customer-with-outcome quote as more credible than logo walls (Marketing Examples / Pencil Pages teardown vocabulary). AI engines extract the named-customer assertion as an evidence-injection passage (Aggarwal's +30-40% citation lift on Quotation Addition + Cite Sources). Same line, both readers win.

**Visible pricing or pricing shape.** April Dunford and Brian Balfour treat pricing opacity as a positioning failure — humans interpret "contact sales" as evasion. AI engines extract per-seat / per-usage / custom-enterprise pricing-shape signals as semantic-triple data the knowledge graph ingests. A pricing page that lists tier and one anchor price-point converts the human AND grounds the AI engine's entity profile.

**Single primary CTA.** Single-CTA pages convert at 13.5% vs 10.5% for multi-CTA pages (B2B SaaS benchmark studies, 2026). A single dominant CTA also reduces parse ambiguity for AI engines that infer the page's intent from CTA structure (the same engine that interprets multiple competing CTAs as multiple intents and discounts the page's citation-worthiness on any single intent).

**Freshness signals.** Visible date / changelog / current-year reference / recent updates. Humans use freshness to confirm the page reflects current reality; AI engines explicitly prefer recent content (Search Engine Land 8K-citation study: 44% of AI Overview citations come from current-year content). The pattern only fails when freshness becomes a stamp ("Last updated 2026-05-15" with stale body content) — which signals AI-optimization-theater to humans even while nominally passing the engine's date heuristic.

**Entity-stability + canonical naming.** "Freddy" / "freddy.ai" / "Gofreddy Inc." consistently used across hero, footer, FAQ, schema. Knowledge-graph ingestion succeeds when entity-name is canonical; humans interpret consistent naming as professionalism. Inconsistent naming reads as sloppy to both readers.

**Third-party validation visible on-page.** Q1 2026 AirOps data: 85% of brand discovery in AI search happens via off-domain mentions. Pages without analyst quotes, named customer voices, or visible press citations give AI engines nothing to corroborate. Humans treat the same external validation as evidence the company exists outside its own marketing surface. AI citation correlation r=0.664 with brand mentions vs r=0.218 with backlinks (Ahrefs 2026) confirms the channel-shift.

The dual-aligned levers above cover roughly two-thirds of the page surface. The judge can score these without dual-audience tension — a page that does them well wins both readers.

### 3. Where the two readers conflict (the load-bearing third)

The remaining one-third of the landing-page surface is where the two readers' preferences genuinely diverge. Four conflict surfaces, each backed by 2026 measurement:

**Conflict 1: keyword + entity density beyond the hero.** AI engines reward entity-rich passages with extractable claims at the hero AND in subsequent sections. Aggarwal et al. (Princeton, KDD 2024, replicated in 2026 GEO benchmarks) measured Statistics Addition / Quotation Addition / Cite Sources at +30-40% citation visibility lift each. Workflows under AEO selection pressure will pile entity mentions, statistics, quotes, and citations into every section. But Digital Applied's 2026 2,000-page conversion study measured the human-side cost: pages using "delve / leverage / synergize / optimize your experience" lose 8% CVR average; pages with > 2 em-dashes per 100 words lose 5%; pages with generic adjectives "amazing / innovative / cutting-edge" lose 4%. The AI-content-shape penalty on conversion is real and measurable. Beyond the hero, dense entity / statistic / citation prose can clear the AI-citation bar and tank the human conversion bar simultaneously.

**Resolution that works in practice:** keep declarative entity-rich passages in dedicated sections (FAQ block, glossary section, case-study block, the footer "About" passage) where the structure signals "reference content" to both readers. Keep the hero, the primary feature block, and the CTA section in human-conversion-optimized prose with low entity-bloat. The judge's score-1 anchor for SE-2 should require evidence-injected passages to exist on the page WITHOUT requiring them in the conversion-critical hero / CTA path.

**Conflict 2: FAQ / glossary depth vs above-fold conversion path.** FAQPage schema is one of the highest-leverage AEO moves — it maps question-shaped content directly to how users query AI engines. The 2026 AEO playbook (Cubitrek, GenOptima, Frase.io, AirOps, LLMrefs) all rank FAQPage schema as top-three AEO leverage. Workflows under AEO selection pressure will pile 8-15 FAQ entries on every page. But Wynter user-testing data and the broader CRO consensus (CXL, Pencil Pages, Marketing Examples) flag a long FAQ above the conversion CTA as a friction signal — humans, especially founders evaluating in 10-second windows, treat a 15-question FAQ as "this product is complicated enough to require an FAQ." Conversion drops measurably when FAQ is rendered above the demo CTA.

**Resolution that works in practice:** FAQ section lives BELOW the primary CTA in the page flow, with a tight 3-5 question initial render + "see all questions" expansion. The schema.org FAQPage markup captures all 15 entries for AI extraction; humans see the compact 5-question summary above the fold of the FAQ section, with the demo CTA already passed in scroll position. The judge's score-1 anchor for SE-1 should require the conversion path to clear the FAQ surface; the score-1 anchor for SE-2 should require sufficient FAQ depth that an AI engine extracting from FAQPage schema finds canonical Q-A pairs in the company's category.

**Conflict 3: declarative-document register vs warmth + named-human voice.** AI engines reward declarative-document register that reads like a reference document. Volpini's asymmetric-retriever argument: dense retrievers project documents and queries into different vector spaces; documents in declarative register (entity + attribute + value statements) score higher in retrieval than documents in conversational register (query-echo, manifesto, brand-narrative). Workflows under AEO selection pressure will write every hero in declarative-document register: "Freddy is an AI-native content engine for regulated B2B verticals serving legal, financial, and healthcare clients." Parses cleanly for AI engines. Reads as generic AI-assisted copy to humans — exactly the failure mode the 2025-2026 "AI-content-hurts-SEO" studies measure as the 18% bounce-rate cause on AI-written content.

**Resolution that works in practice:** declarative-document register at the hero proposition + the top of the FAQ; human voice + named-customer story + specific worked example in the middle of the page (the "social proof" block, the case-study section, the founder-quote block); declarative-document register at the bottom (structured comparison tables, the third-party-citation block, the footer entity description). The voice is bracketed inside the declarative surface, not opposed to it. Stripe.com, Linear.app, Anthropic.com, and Vercel.com all follow this pattern: declarative entity-definition lead, named human voice in the middle, structured reference detail at the bottom. The judge's score-1 anchor for SE-1 (human CTA) should require evidence of warmth + named-human voice somewhere in the visible viewport; the score-1 anchor for SE-2 (AI citation) should require declarative-register passages somewhere on the page. Both can hold on the same artifact.

**Conflict 4: third-party-validation rendering on a viewport budget.** Q1 2026 AirOps data: 85% of brand discovery in AI search happens via off-domain mentions; brands with on-page third-party validation are 6.5× more likely to earn AI citation than brands relying solely on owned content. AI engines need visible third-party validation to corroborate the page's claims. But every analyst quote / press logo / customer testimonial rendered on-page consumes viewport real estate the human conversion path needs. A page with 8 analyst logos, 4 customer quotes, 3 press features, and a "trusted by 500+ companies" counter has paid 4-6 viewport slots to AI engine corroboration that could have gone to the proposition + CTA + named-customer story humans actually convert on.

**Resolution that works in practice:** one named-customer-with-named-outcome quote in the hero viewport (dual-aligned — both readers win on this single rendering); a tight 4-6 logo strip immediately below the hero (low viewport cost, sufficient AI-engine corroboration); a single dedicated "press / analyst coverage" block in the footer area for deeper external validation. The judge's score-1 anchor for SE-2 (AI citation) should require some named third-party validation visible on-page; the score-1 anchor for SE-1 (human CTA) should require the hero viewport to commit to a primary CTA without third-party-validation real-estate over-spending.

### 4. The 2026 AEO update — citation has decoupled from ranking faster than expected

Three concrete shifts since the 2026-05-15 site_engine domain research:

**Shift 1: Ahrefs Q1 2026 measured AI Overview citation overlap with Google's top 10 dropped from 76% to 38% over twelve months.** The original 2026-05-15 GEO research cited the 12% figure (from late-2025 measurement of overall AI citation, not specifically AI Overview citation). The 38% Ahrefs Q1 2026 figure is the more recent benchmark and specifically targets Google AI Overview. The direction of travel is consistent: citation is decoupling from organic ranking, faster than the SEO industry anticipated, and the gap is widening. A landing page that ranks #1 organically can be cited 0 times by AI engines if it is not citation-shaped — and the inverse is increasingly true (pages cited heavily but not ranking organically). The judge cannot rely on rank-as-proxy-for-citation; the page must be scored on citation-shape directly.

**Shift 2: brand-mention weight rose; backlink weight fell.** Ahrefs 2026: r=0.664 brand-mention correlation with AI citation vs r=0.218 backlink correlation. The classical SEO playbook (build backlinks; rank pages; collect organic traffic) does not transfer cleanly to the AEO channel. Off-domain brand mentions — analyst Substacks, podcast transcripts, press articles, YouTube descriptions — drive AI citation more than backlinks do. For the site_engine judge, the implication is that on-page surface alone cannot solve for AI-citation share. The page must be designed to MIRROR the off-domain brand mention surface (consistent entity naming, canonical category placement, named-customer outcomes) so that when AI engines cross-reference the page against off-domain sources, the corroboration succeeds.

**Shift 3: semantic-completeness scoring surfaced as a measurable feature.** Per Wellows / PPC.land 2026 analyses: passages scoring 8.5/10+ on semantic-completeness measures are 4.2× more likely to be cited. The semantic-completeness signal favors passages that fully answer a query in 134-167 word self-contained units. The original Profound 40-75-word finding remains valid for hero-extraction citation; the newer 134-167-word semantic-completeness band applies to FAQ / glossary / explainer passages where the engine wants a complete answer rather than a hero-shaped excerpt. The site_engine judge should not optimize for either length specifically — but the score-1 anchor for SE-2 should require AT LEAST one extractable passage that answers a category question completely (semantic-completeness shape) AND AT LEAST one hero-shaped passage that compresses the proposition (40-75-word shape).

### 5. Goodhart-collapse on the dual-audience surface

The lane's specific Goodhart-collapse mode under 50 generations of selection pressure: the workflow learns to slot-fill BOTH the human-conversion surface AND the AI-citation surface as templated patterns rather than substantive content. Every hero gets a "X is Y for Z" canonical-form template; every page stuffs 3 named-customer-with-outcome quotes per section; every page gets a "Last updated: YYYY-MM-DD" sticker; every page repeats the canonical entity name 12 times per section; every page plants 40-75-word answer-bait passages; every "social proof" section uses a templated "customer name + dated stat + outcome" sentence regardless of whether the customer is real. The output is structurally compliant. AI engines catch within 1-2 indexing cycles (template-detected pages enter "too-optimized therefore distrust" tier). Human visitors recognize the template and bounce.

The judge must score for OUTCOMES, not surface markers. SE-1 must test for whether the human persona converts, not whether the hero contains the "X is Y for Z" template fields. SE-2 must test for whether an AI engine would cite a passage in real category-query context, not whether the page contains the surface markers of citation-shape. SE-5 must test for substantive freshness (current-year body content, dated customer references, recent product changes), not the presence of a "Last updated" stamp.

The score-0 anchors should explicitly target the template-slot-fill failure mode: SE-1 score-0 includes "templated 'X for Y' hero without specific persona commitment or named alternative"; SE-2 score-0 includes "citation-stuffed prose where no individual passage stands alone as a substantive answer to a real category query"; SE-5 score-0 includes "freshness stamp present but body copy stale or undated stats".

---

## Recommendations for the v1 site_engine judge

**R1. Keep the five outcome questions from the Step-1 spec.** SE-1 through SE-5 cover the dual-audience surface adequately. Do not add a sixth criterion for "dual-audience balance" — that introduces a feature-checking surface where the workflow can optimize for the meta-criterion rather than the underlying outcomes.

**R2. Strengthen the score-1 anchors on SE-1 and SE-2 to require AND-conjunction on the conflict surfaces.** SE-1's current score-1 anchor requires hero scannability + single CTA + named evidence element. Add: "the visible viewport contains warmth signals — named-human voice, customer-with-outcome story, or photographic / illustrative evidence of named team — sufficient that a returning human visitor would not file the page as AI-generated template." SE-2's current score-1 anchor requires answer-first + entity-grounded + evidence-injected + self-contained 40-75-word passages. Add: "the page also contains at least one semantic-completeness-shaped (~134-167 word) passage answering a real category question in canonical reference form, AND named off-domain validation rendered on-page (analyst quote, press citation, named-customer story with attribution)."

**R3. Add an explicit Goodhart-resistance verification on SE-1 / SE-2 / SE-5.** SE-1: templated hero without specific persona commitment fails. SE-2: citation-stuffed prose without individual-passage substantive completeness fails. SE-5: freshness stamp without substantive current-year body content fails. These are not anti-gaming clauses (which the design guide §12.12 classifies as theatrical). These are score-0 anchor extensions that specify the failure shape behaviorally.

**R4. Route the off-domain validation depth check into the judge, not `structural_gate`.** Structural_gate can verify that a third-party-validation block exists on the page; it cannot verify that the cited validation is substantive (named source + specific claim + dated context). The substantive validation check is a judge call. SE-2's CoT step 2 ("Map to {answer-first lead, evidence injection, passage self-containment, entity consistency, third-party validation}") already includes this; the score-1 anchor should reinforce it.

**R5. Do not weight criteria by page type or client intent.** The site_engine lane will see fixtures across multiple page types (landing pages, SEO hub pages, comparison pages, product pages, FAQ pages). The judge should score the same five outcome questions on every artifact. Page-type-specific weighting introduces a feature-checking pre-classifier that becomes its own Goodhart-collapse surface. Where a page type structurally cannot earn one criterion (e.g., an FAQ-only sub-page cannot earn SE-1 as a primary-CTA criterion), the criterion should score 0.5-unknown with a one-sentence note, not a re-weighted partial.

**R6. Calibrate against named real-world exemplars at the boundary.** Stripe.com, Linear.app, Anthropic.com, Vercel.com, Cursor.com pass the dual-audience test cleanly. AI-generated landing-page slop (lime-purple gradient mesh + three-icon trio + "AI-powered platform for modern teams" + six identical bordered cards) fails both readers. Use these as calibration-set anchors when stress-testing the rubric on 100 fixtures per the design guide §15 cadence. The hedged-example pattern from the judge design guide ("do not optimize toward this") must apply — Stripe is illustrative of behavior, not a slot-fill target.

**R7. First-cohort overfitting watch — generalize anchors across the gofreddy fixture cohort.** The current first-cohort includes Klinika Melitus (b2c aesthetic dermatology), DWF (b2b legal services), Anthropic / Perplexity (AI research labs / b2b tech). The dual-audience tension shape differs subtly per vertical: aesthetic-derm pages weight visual proof (before-after imagery banned per client denylist) and local-trust signals; legal-services pages weight directory rankings and partner credentials; AI-lab pages weight technical depth and named-research credibility. The score-1 anchors should generalize across all three — not anchor on any one. If a 50-generation evolution loop overfits to one vertical's surface markers, the rubric has failed.

---

## Open questions

**OQ1. Does FAQPage schema deserve its own structural_gate validation or should the FAQ-section presence be a judge-call?** Recommendation lean: structural_gate validates schema.org markup syntax (deterministic); judge scores whether FAQ content is substantive (qualitative). Split per the OpenRubrics Hard-Rules-vs-Principles separation in the design guide §1.2.

**OQ2. How does the judge handle multi-page artifacts vs single-page artifacts in the same lane?** The current site_engine spec assumes single-page landing surfaces. Future fixtures may produce full sites (multiple linked pages). For multi-page, criteria need aggregate tests (does the SITE earn fan-out, not just one page). Deferred per Step-1 spec §9 open question #1.

**OQ3. How does the site_engine judge reconcile with the GEO lane judge when both score the same page?** The Step-1 spec §9 open question #2 flags this. Proposed boundary: GEO judges a single page in narrow AI-citation context; site_engine judges full landing-page surfaces with co-equal human-AI reader weighting. If a fixture produces a single page optimized purely for AI citation, GEO is the right lane. If a fixture produces a landing page expected to serve both readers, site_engine is the right lane. Confirm boundary holds when fixtures run through both judges and compare scores.

**OQ4. Does the AND-conjunction requirement on score-1 anchors produce false-zeros on partial-render artifacts?** Possible failure mode: a workflow ships a hero-only render for an iteration test; the page is human-warm + AI-citable in shape but lacks FAQ / footer / structured-data sections. The 0.5-unknown anchor handles this (per design guide §3) but the rate of 0.5-unknowns should be monitored — if > 20% of fixtures land on 0.5 across multiple criteria, the structural_gate is letting incomplete artifacts through and should be tightened.

**OQ5. How fast will the Q1 2026 citation-divergence trend continue?** Ahrefs Q1 2025 = 76% top-10 overlap; Q1 2026 = 38%. Linear extrapolation suggests Q1 2027 = sub-15%. The judge will face fixtures generated against an increasingly diverging citation-vs-ranking landscape. The score-1 anchors should not embed the specific 2026 numbers in rubric prose (per design guide §1.1 outcome-not-feature discipline) — the outcome questions should remain framing-stable across the trend.

---

## Citations

### 2026 AEO + AI Overview citation data
- Ahrefs Q1 2026: "Update — 38% of AI Overview Citations Pull From Top 10" — citation-overlap drop from 76% to 38% over twelve months
- AirOps 2026 State of AI Search — 85% of brand mentions for AI discovery come from external domains; brands with off-domain presence 6.5× more likely to earn AI visibility; YouTube and branded web mentions top correlated factors
- ALM Corp 2026 — AEO vs Traditional SEO 2026 strategy guide — Google AI Overview citation drop from top-ranking pages
- Conductor 2026 — Future of AEO & Content Marketing trends
- HubSpot AEO Guide — 27% AI-traffic-to-SQL conversion among early AEO adopters; 30% higher time-on-site vs traditional search
- Semrush 2026 — AI Search Trust Signals practical audit
- Webfx / Wellows / Trysight / Onely 2026 — AI ranking factors guides (semantic-completeness 4.2× citation multiplier at 8.5/10+ scoring)
- PPC.land 2026 — 23 factors that get content cited by AI search engines

### 2026 conversion rate optimization data
- Digital Applied 2026 — 2,000 landing pages tested study: AI copy +3% on B2B SaaS, +4% on lead-gen; -2% DTC ecommerce, -5% webinar; pages with "delve / leverage / synergize / optimize your experience" lose 8% CVR; > 2 em-dashes per 100 words lose 5%; "amazing / innovative / cutting-edge" lose 4%
- Tatvic Analytics 2026 — Landing Page Optimization in 2026 Has Two Audiences — dual-audience framing crystallization
- SaaS Hero 2026 — single-CTA pages convert at 13.5% vs 10.5% for multi-CTA pages; 3-5 form-field maximum; per-field cost ~10-15% CVR
- Adobe-Ahrefs Q1-Q2 2026 — AI-referred traffic conversion 14.2% vs Google organic 2.8%; 48% longer per visit, 23% lower bounce rate
- CXL 2026 — AEO Comprehensive Guide; hero-audit framework; 6-second value-proposition test

### Conversion design practitioner consensus
- Peep Laja / CXL hero-audit framework — six diagnostic questions
- April Dunford — Obviously Awesome (2019) + Sales Pitch (2023) — competitive alternatives include "do nothing" / "hire an assistant"
- Brian Balfour — positioning-first growth model
- Harry Dry / Marketing Examples — teardown vocabulary (feature dump, logo-walled, throat-clearing, manifesto-lead, claim inflation)
- Animalz — testimonial structure: tried before / why failed / what changed / result
- Julian Shapiro — friction-per-form-field rule
- Wynter — B2B user-testing pattern library
- Pencil Pages — B2B teardown corpus

### AEO / GEO foundational + 2026 follow-up
- Aggarwal et al. (Princeton) — GEO: Generative Engine Optimization arxiv:2311.09735 (KDD 2024) — Statistics +30-40%, Quotation +28-40%, Cite Sources +30-40%, Fluency +15-30%, domain-conditional method mix
- Cyrus Shepard (Zyppy) — AI Citation Ranking Factors meta-analysis (54 experiments)
- Andrea Volpini (WordLift) — asymmetric-retriever argument; declarative-document register favoring
- Profound 10K-passage study — 40-75-word passage citation multiplier 3.1× vs longer
- Yext 17.2M-citation analysis
- Skywork — Perplexity accuracy work
- Forrester 2026 — AI-buyer-validation research
- Kalicube / Jason Barnard — Entity SEO + Semantic Triple framework
- Search Engine Land 8K-citation study — 44% of AI Overview citations from current-year content
- Wellows 2026 — Google AI Overviews ranking factors; semantic-completeness vector r=0.84

### 2026 AEO practitioner playbooks
- ALM Corp — Answer Engine Optimization 2026: Practical Playbook
- Cubitrek — AEO 101 Definitive Guide 2026
- Frase.io — Complete AEO Guide 2026
- AirOps — AEO Complete Guide 2026
- GenOptima — AEO Techniques 2026
- LLMrefs — Answer Engine Optimization Complete Guide 2026
- Conductor Academy — Future of AEO & Content Marketing
- monday.com — Answer engine optimization practical framework 2026

### Real-world dual-audience exemplars
- Stripe.com — evidence injection + named customers + clear primary CTA + developer-credibility signals
- Linear.app — declarative hero + single CTA + product surface visible + named customers
- Anthropic.com — persona-separated landing surfaces + fresh research signals + named expert credibility
- Cursor.com — concrete value proposition + named differentiator
- Vercel.com — passage self-containment + technical clarity
- Mayo Clinic / Cleveland Clinic — nested declarative-claim + depth pattern in regulated-content domains

### Companion gofreddy research deliverables
- docs/research/2026-05-18-judges-domain-site-engine.md — primary site_engine domain research
- docs/research/2026-05-18-geo-dual-audience-tension.md — parallel GEO dual-audience axis (narrower scope)
- docs/research/2026-05-18-ci-vertical-conventions.md — first-cohort vertical-overfit pattern reference
- docs/rubrics/judge-design-guide.md — outcome-question discipline + Goodhart-resistance pattern
- docs/handoffs/2026-05-18-judge-design-step1-site-engine.md — Step-1 optimal-output spec being deepened here

---

## 4-line summary

- Word count: ~3050.
- Top-3 conflict surfaces between human visitor and AI engine on landing pages: (1) keyword + entity density beyond hero (AI rewards; humans bounce on AI-template copy at measured -8% CVR on "delve/leverage" register), (2) FAQ / glossary depth above conversion CTA (AEO leverage vs Wynter CRO data showing long-FAQ-above-CTA depresses CVR), (3) declarative-document register vs warmth + named-human voice + named-customer story.
- Top-3 2026 AEO updates load-bearing for the judge: (a) Ahrefs Q1 2026 AI Overview citation-to-top-10 overlap dropped 76% → 38% in twelve months — citation has decoupled from ranking; (b) brand-mention correlation rose to r=0.664 vs backlink r=0.218 — off-domain validation now load-bearing for citation; (c) semantic-completeness scoring surfaced — 134-167-word self-contained passages cited 4.2× more.
- Verdict for judge design: keep SE-1..SE-5; strengthen score-1 anchors on SE-1 / SE-2 / SE-5 to require AND-conjunction on the conflict surfaces (the page must demonstrate BOTH human-warmth AND AI-citation-shape, not a weighted blend); add Goodhart-resistance score-0 anchors explicit to template-slot-fill collapse modes; do not weight criteria by page type or client intent.
