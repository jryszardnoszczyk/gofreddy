---
date: 2026-05-18
type: research deliverable
status: complete
topic: domain research — site_engine lane (dual audience)
parent: docs/rubrics/judge-design-guide.md
siblings:
  - docs/research/2026-05-15-judges-domain-competitive.md
  - docs/research/2026-05-15-judges-domain-geo.md
existing_artifact: docs/rubrics/site-quality.md
---

# Domain Research: What Makes an Excellent Landing-Page Surface (Dual Audience)

**Purpose.** Ground the `site_engine` lane judge in published landing-page research, conversion-design practitioner work, and answer-engine-optimization (AEO/GEO) literature. The reader is dual: a human web visitor evaluating the company AND an AI search engine indexing the page for citation. A landing page is a single artifact serving both; criteria must work for both simultaneously.

**Scope.** Synthesis across (a) conversion-design practitioners — Peep Laja/CXL, Marketing Examples (Harry Dry), Julian Shapiro, April Dunford, Brian Balfour, Wynter, Pencil Pages, Animalz; (b) the AEO/GEO literature already mined in `docs/research/2026-05-15-judges-domain-geo.md` extended to full landing-page surfaces; (c) named real-world exemplars; (d) the design guide's outcome-question discipline.

---

## 1. What makes a landing page work — dual audience

A landing page in 2026 must clear two distinct outcome tests. The human visitor decides in roughly six to ten seconds whether to commit attention; the AI search engine decides per-passage whether the page is citable when answering a related question. The strongest pages do both with the same surface. The mediocre ones treat them as separate optimizations and lose both.

### 1a. The human reader (~400 words)

The human reader is not a generic "visitor." Three specific personas appear repeatedly in B2B SaaS landing-page literature and they want different things from the same page:

- **Founder evaluating a vendor.** Has a near-term problem, scanning to decide whether to take a 30-minute call. Wants the proposition restated in their own words within the hero, evidence the vendor has solved this exact problem before, pricing or at least pricing shape (not "contact sales" alone), and a low-cost next step (book demo, free audit, sandbox).
- **Recruiter / candidate checking legitimacy.** Looking for clarity that the company is real and the team is credible. Wants founder name surfaced, recent activity proof (changelog, blog dated within 90 days, current-year copyright), specific customers named with context (not logo-walls).
- **Prospective client doing diligence after a referral.** Already warm. Wants to confirm category fit and risk profile fast. Wants concrete capabilities ("we do X for Y"), surface of the pricing model, and one specific named customer or case-study link they can audit.

What converts across all three is the same small set of design moves, repeatedly named by Peep Laja (CXL), April Dunford (positioning), Brian Balfour (positioning-first), Harry Dry (Marketing Examples), and Julian Shapiro:

1. **The hero answers "what is it, who is it for, why is it different" in a single visible block.** Dunford's positioning framework explicitly: competitive alternatives → unique attributes → value → target market → market category. CXL's hero-section audit framework names six elements: clarity of value proposition, relevance to traffic source, scannability, conversion friction, social proof in viewport, single primary CTA.
2. **One primary CTA, not three.** Wynter user-testing data repeatedly shows competing CTAs in the hero depress total clicks. Pencil Pages teardowns highlight this as the #1 fixable pattern.
3. **Specific social proof above the fold.** Harry Dry's Marketing Examples rule: a quote from a named customer with a specific outcome beats any logo wall. Animalz's distillation: the testimonial that converts says *what was tried before, why it failed, what changed, and what the result was*.
4. **Pricing visible or pricing shape visible.** April Dunford in *Sales Pitch* (2023) and Brian Balfour's positioning content both treat pricing opacity as a positioning failure. The page that hides pricing forces the visitor to invest before they qualify themselves.
5. **Friction-removal in the form / CTA.** Julian Shapiro's rule: every required form field costs ~10% completion. The best B2B landing pages now ask for one field (work email or company URL).

The synthesizing outcome question: **after roughly ten seconds, would a relevant human visitor commit to the primary CTA — book demo, start trial, request audit?**

### 1b. The AI search engine as reader (~400 words)

The AI search engine is now a first-class reader. Ahrefs Q1 2026 data: only 12% of AI-cited URLs overlap with Google's top 10. Citation diverges from ranking. The page must be designed for citation, not search.

What the AEO literature (Aggarwal et al. KDD 2024 GEO paper, Cyrus Shepard's Zyppy meta-analysis of 54 experiments, Andrea Volpini at WordLift, Profound's 10K-passage study, Yext's 17.2M-citation analysis, Skywork's Perplexity citation work) converges on:

1. **Answer-first passages, BLUF register.** Perplexity's top-cited pages answer the core question in the first 100 words 90% of the time. The hero on a landing page IS the BLUF passage — declarative-document register ("Freddy is a content engine for regulated B2B"), not query-echo register ("What is Freddy?").
2. **Evidence injection: stats, quotations, citations.** Aggarwal's top three optimization methods (+28–40% visibility lift each) are all verifiable-evidence tactics. A landing page that says "trusted by leading firms" loses to one that says "used by Dentons and Pinsent Masons since 2025" with a footnote link.
3. **Passage self-containment.** Profound's finding: passages of 40–75 words cited 3.1× more than longer ones; tables cited 4.2× more than equivalent prose. Each section block on the landing page must read standalone — entity named, claim complete, no "as mentioned above."
4. **Entity consistency.** Same brand name, same one-sentence definition, repeated across hero, footer, structured data, and FAQ. Kalicube's Semantic Triple framework — subject/predicate/object statements that knowledge graphs ingest. Drift between "Acme Pay" and "AcmePay" fragments citation signal.
5. **Third-party validation visible on-page.** Forrester 2026: AI buyers validate vendor claims externally. A page citing zero analysts, no customer voices, no comparison content reads as marketing and gets discounted. Ahrefs r=0.664 brand-mention correlation is driven by *external text* — which only happens when the page acknowledges and engages a category.
6. **Freshness signal visible.** Visible date, current-year reference in copy, recent change. Search Engine Land 8K-citation study: 44% of AI Overview citations from current-year content.
7. **Schema.org markup where it earns its weight.** Organization, Product, FAQPage, BreadcrumbList. This is structured-gate work, not judge work — present/absent is verifiable; the judge does not score it.
8. **Intent-format match.** Shepard's #6 factor at correlation 9.0/10. Pricing pages need tables; FAQ needs Q-then-A; comparison pages need side-by-side; landing hero needs declarative lead.

The synthesizing outcome question: **if an AI engine were answering a real query in this company's category, would it cite a passage from this page?**

The dual-audience symmetry is real but not automatic. A page can be human-converting and AI-uncitable (vague hero + great hand-drawn social proof). A page can be AI-citable and human-cold (dense passage-perfect content with no warmth). The world-class pages — Stripe, Linear, Anthropic for different reasons — do both.

---

## 2. Great vs mediocre — named failure modes

Eight failure modes recur across the conversion-design and AEO literature, each diagnostic enough to call by name. (~500 words)

**FM-1: AI-generated landing-page slop.** The 2024–2026 template: lime-and-purple gradient mesh hero, three-icon trio at 33% width each, "AI-powered platform for modern teams," six identical bordered cards, stock testimonial grid with circular placeholder avatars. Both Pencil Pages and Marketing Examples teardowns treat this as the dead giveaway. Fails the AI-engine test too — zero entity specificity, zero verifiable evidence, no third-party voice.

**FM-2: Generic SaaS template copy.** "Built for teams of all sizes." "The all-in-one platform for X." "Modern, scalable, enterprise-ready." Dunford's diagnostic: if you can swap the company name and the copy still works, the positioning has failed. Wynter user-testing data: this register actively confuses early-stage visitors, who can't infer category placement.

**FM-3: Hero-section claim inflation.** "World's best." "Industry-leading." "Next-generation." "10× faster." Hedge ("up to 10×") is worse than no claim — Aggarwal et al.'s data: unsubstantiated comparatives correlate negatively with AI citation. CXL: hero claim inflation depresses conversion in A/B tests because it raises the credibility threshold higher than the rest of the page can clear.

**FM-4: Vague benefit copy.** "Save time." "Increase productivity." "Make better decisions." The Product Marketing Alliance frames this directly: actionable insights must be "specific and measurable." Marketing Examples / Harry Dry: a benefit becomes copy-worthy when you can name *who*, *what they used before*, *what changed in measurable terms*. "Save 6 hours of review-cycle time per brief" beats "improve productivity."

**FM-5: Social proof that's logos with no context.** A wall of customer logos with no quote, no outcome, no link to a case study. Animalz, Marketing Examples, and Pencil Pages all flag this. AI engines treat unattributed logos as decorative — no entity grounding, no evidence injection. Human visitors discount the wall by default (logos are easy to obtain or fabricate); the named-customer-with-specific-outcome quote is the form that converts.

**FM-6: FAQ that doesn't answer real questions.** "What is X?" with the company's own product as the answer; "Why choose us?" with marketing copy as the answer. Real FAQ — the form that earns AI citations and human trust — answers the questions visitors actually have: pricing model, contract terms, integration list, comparison to named alternatives, what happens if you cancel. Schema.org FAQPage markup on a fake FAQ is worse than no markup; it tells the AI engine the page lies about its structure.

**FM-7: Pricing pages that hide the price.** April Dunford and Brian Balfour both treat this as a positioning failure: vendor refuses to commit to a price band because the positioning doesn't justify any specific band. Forces qualified buyers into a sales call before they've decided to engage. The fix is not always "publish the price" — sometimes it's "publish the pricing shape" (per-seat, per-usage, custom-enterprise) with one anchor data point.

**FM-8: Buried answer / scroll-to-find-it lead.** The page opens with a brand video, a manifesto paragraph, or a "What is X?" rhetorical question. Profound: 44% of AI citations come from the top third of a page; Perplexity's 90/100-words finding. CXL's six-second-test: if a relevant visitor can't state the value proposition after six seconds of viewing, the hero has failed.

The pattern beneath all eight: **failure to commit to a specific reader and a specific outcome.** Each failure mode trades specificity for surface-area, hoping the page works for "everyone." It works for no one.

---

## 3. Industry frameworks (judge's reasoning toolkit)

Five frameworks worth the judge's understanding. Each is a reasoning tool, not a feature-checklist. (~500 words)

**CXL Hero Audit (Peep Laja).** Six diagnostic questions: (1) Is the value proposition clear within five seconds? (2) Is the page relevant to the traffic source? (3) Is the page scannable for the impatient reader? (4) Is conversion friction minimized in the primary path? (5) Is social proof in the viewport? (6) Is there a single primary CTA? The strength here is *speed of evaluation* — a judge can walk these six in under a minute and have a defensible reading. CXL teardowns are the public-facing artifact of this framework; reading one or two gives a calibrated sense of what each question means.

**April Dunford positioning (Obviously Awesome + Sales Pitch).** Five elements: competitive alternatives → unique attributes → value → target market → market category. The diagnostic for a landing page: can the visitor infer all five from the visible-without-scroll surface? Critical refinement from *Sales Pitch* (2023): competitive alternatives include "do nothing" and "hire an assistant" — not just named competitors. A landing page that ignores the do-nothing alternative is over-confident about the buyer's urgency.

**Brian Balfour positioning-first growth model.** Balfour's framework reverses the standard funnel: positioning → product → market → model → channel. The relevance for a landing page: every page is downstream of positioning, and a "growth-hack" applied to a page with broken positioning amplifies the failure. The diagnostic: if a landing page A/B test improves conversion 30% by making the hero punchier, but the positioning underneath was wrong, the win is paying you to ship more wrong buyers further into the funnel.

**AEO patterns (Aggarwal KDD 2024 + practitioner consolidation).** The five evidence-injection moves with measured visibility lift: Quotation Addition (+28–40%), Statistics Addition (+30–40%), Cite Sources (+30–40%), Fluency Optimization (+15–30%), Authoritative tone (+15–30%). The diagnostic for a landing page: where on this page does the AI engine find a quotable passage with a verifiable claim and a third-party citation? If the answer is "nowhere," the page is uncitable regardless of how it ranks. Aggarwal's domain-specific finding extends this — Statistics Addition wins for Law/Government; Quotation Addition wins for People/Society; Fluency wins for Health/Business. The judge can read the page's evident category and ask whether the matching method is in use.

**Marketing Examples / Pencil Pages teardown vocabulary (Harry Dry et al.).** Less formal but operationally dense. Recurring critique vocabulary: "feature dump" (lists capabilities without value), "logo-walled" (social proof reduced to brand names), "throat-clearing" (hero copy that talks about itself before answering "what is this?"), "manifesto-lead" (brand-narrative opener where a declarative lead was needed), "claim inflation" (superlatives without backing). The diagnostic value: these are reader-language critiques. A judge that can identify "this is a feature dump" with a one-line rationale is doing the same work a Marketing Examples teardown does.

These five share a structural property: **none of them is a checklist.** Each is a reasoning tool that produces a judgment. The design guide's outcome-question discipline aligns with this tradition. Anti-patterns from the same tradition: WCAG-style multi-rule audits that pass on rule-compliance with broken outcome (matches the design guide §11.4 Feature-level Proxy Compression risk).

---

## 4. Proposed judge criteria — five outcome questions

Each criterion is an outcome question with binary anchors per the design guide. Hedged examples; no anti-gaming clauses; no framework-name embedding in rubric prose. Verifiables route to `structural_gate`. (~500 words)

### SE-A — Would a relevant human visitor commit to the primary CTA?

**Outcome question.** After ~10 seconds on the page, would the targeted persona (founder evaluating, recruiter checking, prospect doing diligence) click the primary CTA — book demo, start trial, request audit — based on what's visible without scroll?

**Score 1.** The visible hero block answers "what is this, who is it for, what's different" in declarative register; one primary CTA is visually dominant; at least one specific evidence element (named customer + outcome, dated stat, founder name) is in the viewport. Example (do not optimize toward this): Linear's hero — declarative "for modern software teams" + named customers + visible product surface + single "Get started" CTA.

**Score 0.** Hero opens with a question, a manifesto, or a vague benefit ("save time"); multiple competing CTAs of equal visual weight; social proof is logo-only or absent from viewport; visitor cannot infer category placement from visible copy.

**Score 0.5 (unknown).** Artifact is a section-only render and CTA / above-fold context cannot be inferred. Emit 0.5 + "unknown" + one sentence on what would have to be present.

**Required CoT.** (1) Identify the named target persona and the primary CTA. (2) Walk the visible hero block and identify which of {value proposition, category placement, differentiator, evidence element} are present. (3) Commit to verdict + one-sentence justification.

### SE-B — Would an AI engine cite a passage from this page?

**Outcome question.** When an AI search engine answers a real query in this company's category, would it find a citable passage on this page — answer-first, evidence-injected, entity-grounded, self-contained?

**Score 1.** At least one passage on the page (typically hero or a section opener) reads in declarative-document register, names the entity in canonical form, contains a verifiable specific (number with source, named customer, dated quote), and stands alone if extracted as a 40–75-word block. Example (do not optimize toward this): Stripe's homepage hero plus the "Used by millions of businesses, from startups to public companies" line with named customer logos linking to case studies.

**Score 0.** Page leads with query-echo ("What is X?") or marketing copy; all claims are vague qualitatives ("leading," "trusted"); no third-party voice cited; passages contain floating pronouns or require prior context to parse.

**Score 0.5 (unknown).** Entity canonical naming cannot be assessed from the artifact alone.

**Required CoT.** (1) List the named entities and specific claims in the artifact. (2) Map to {answer-first lead, evidence injection, passage self-containment, entity consistency, third-party validation}. (3) Verdict + justification.

### SE-C — Is the proposition specific enough to fail a credibility test?

**Outcome question.** If a hostile reader (skeptical analyst, prospective customer in diligence) interrogated each claim on the page, would specific claims survive — or would they retreat to "we meant that loosely"?

**Score 1.** Page contains at least three claims that are (a) concrete (numeric, dated, or named-entity), (b) backed by an artifact the company could produce within 24 hours (case study, screenshot, log, contract), (c) phrased without hedge ("up to," "as much as," "designed to"). Example (do not optimize toward this): "149 lenses across 9 dimensions" — backed by the rubric file.

**Score 0.** All capability claims are abstract ("autonomous," "intelligent," "comprehensive"); numbers are unsourced or hedged; comparative claims unsubstantiated.

**Score 0.5 (unknown).** Claims present but artifact does not surface evidence trails.

### SE-D — Does the page commit to a specific reader rather than averaging across all of them?

**Outcome question.** Reading the page cold, can a senior marketer name the intended persona, their named alternative (including "do nothing"), and the one decision the page asks them to make?

**Score 1.** Hero copy names or unambiguously implies the target persona; competitive alternatives (including non-product alternatives) are acknowledged somewhere on page; primary CTA maps to a single decision. Example (do not optimize toward this): Anthropic's "For developers" vs "For enterprises" surface separation — neither page averages across the other's persona.

**Score 0.** Copy reads as if written for "everyone in your industry"; no acknowledgement of competitive landscape or do-nothing alternative; multiple CTAs imply multiple personas without resolving which is primary.

### SE-E — Does the page provide enough freshness and entity-stability signal for AI engines to trust it?

**Outcome question.** Would an AI engine, given two pages making similar claims, prefer this one based on freshness and entity-grounding signals visible in the artifact?

**Score 1.** Visible publication or update date within prior 12 months; current-year reference in body copy; consistent canonical entity naming throughout; at least one dated third-party reference. Example (do not optimize toward this): a changelog dated within 30 days surfaced in the footer of a SaaS landing page.

**Score 0.** No visible date; copyright stuck on prior year; entity-name drift across sections; all stats undated.

Each criterion stays at the design guide's ~150-word budget. No framework names in prose. No anti-gaming clauses (the design guide §12.3 anti-pattern). Anchor examples hedged "do not optimize toward this" per §7.

---

## 5. Sources cited + comparison to existing `docs/rubrics/site-quality.md`

**Sources.** Aggarwal et al. "GEO: Generative Engine Optimization" arXiv:2311.09735 (KDD 2024). Cyrus Shepard, AI Citation Ranking Factors meta-analysis, Zyppy 2025. Andrea Volpini (WordLift) on retrieval evolution, embeddings asymmetry, knowledge-graph grounding. Profound 10K-passage study (2025). Yext 17.2M-citation analysis (2025). Ahrefs Q1 2026 update on AI Overview citation overlap (12% with top-10). Peep Laja / CXL hero audit framework. April Dunford *Obviously Awesome* (2019) + *Sales Pitch* (2023). Brian Balfour positioning-first model. Marketing Examples (Harry Dry) teardowns. Animalz content-strategy work. Wynter user-testing pattern library. Pencil Pages B2B teardowns. Skywork Perplexity accuracy work (2025). Forrester 2026 AI-buyer-validation research. Kalicube (Jason Barnard) Entity SEO and Semantic Triple framework. Search Engine Land 8K-citation AEO study. Real-world exemplars referenced: Stripe.com (evidence-injection, named customers), Linear.app (declarative hero, single CTA), Vercel.com (passage self-containment, technical clarity), Notion.so (intent-format match across product pages), Anthropic.com (persona separation, fresh authority signal), Cursor.com (concrete value proposition, named differentiator).

**Comparison to existing `docs/rubrics/site-quality.md` (SE-1..SE-8).** The existing rubric was authored 2026-05-13, before the design guide. It carries three structural patterns the design guide now classifies as anti-patterns:

1. **1/3/5 scoring scale with described levels.** Design guide §3 + anti-pattern catalogue §12.4: "Broad-scale anchorless rubrics → central-tendency collapse." The 1/3/5 scale with prose anchors at every level invites the central-tendency bias Arize and Hamel Husain's surveys flag. The new rubric should be binary 0/1 with 0.5-as-unknown only.
2. **Anti-gaming clauses on every axis.** Every existing SE axis carries an "Anti-gaming" subsection ("Cannot be earned by..."). Design guide §12.12 + §10: anti-bias / anti-gaming clauses in rubric prose are "theatrical" — arxiv 2506.13639 + Eugene Yan: they perturb score distribution without changing rank order. The new rubric should drop them entirely.
3. **Eight criteria.** Design guide §5: ≤5 criteria per lane; live floor 3–4 after redundancy check. Eight criteria invite cross-criterion synthesis bias and dilute attention.

What the existing rubric got right: the falsifiability tests are concrete (3-reader eye-flow test, blind-attribution test, axe-core run, Lighthouse metrics). These belong in `structural_gate`, not in the judge. SE-6 (accessibility) and SE-7 (performance) are almost entirely structural — they should leave the judge entirely and live in the workflow's deterministic pre-check. SE-1, SE-2, SE-5, SE-8 collapse into the proposed SE-A and SE-D (human-outcome). SE-3 maps to SE-C. SE-4 (voice) is real but distinct and may belong in the brand-voice lane rather than site_engine.

The existing rubric also lacks any AI-engine-as-reader criterion. The 2026-05-15 GEO research and Q1 2026 citation-divergence findings make this a load-bearing gap.

**Verdict.** The existing SE-1..SE-8 rubric needs to be rewritten under the design guide. Five outcome-question criteria (SE-A..SE-E above) covering dual audience replace the eight-axis 1/3/5 scale. Verifiables (axe-core, Lighthouse, brand-token check, schema.org markup) move to `structural_gate`. Anti-gaming clauses are removed.

---

## 4-line summary

- Word count: ~2480.
- Top-3 frameworks as judge reasoning toolkit: CXL Hero Audit (six diagnostic questions), April Dunford positioning (competitive alternatives including do-nothing), Aggarwal GEO evidence-injection hierarchy (quotes/stats/citations top three at +28–40%).
- Top-3 named failure modes: AI-generated landing-page slop (gradient mesh + three-icon trio + generic copy), social proof reduced to logo-walls without context, hero-section claim inflation (superlatives + hedged "up to N×").
- Verdict on existing SE-1..SE-8: needs rewriting under the design guide — 1/3/5 scale invites central-tendency collapse, anti-gaming clauses are theatrical, eight axes exceed the ≤5 ceiling, accessibility/performance/brand-token are structural verifiables that should move to `structural_gate`, and the rubric lacks any AI-engine-as-reader criterion despite Q1 2026 data showing AI citation diverging from organic ranking.
