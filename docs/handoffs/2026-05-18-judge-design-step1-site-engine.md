---
date: 2026-05-18 v1
type: judge-design Step 1 — site_engine optimal-output spec (dual audience)
status: DRAFT v1 — design-locked per JR; ready for redundancy check + fixture validation
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
gold_standard_exemplar: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI v3.3)
companions:
  - docs/research/2026-05-18-judges-domain-site-engine.md (generalist dual-audience domain research)
  - docs/research/2026-05-18-site-engine-cxl-hero-audit.md (hero-axis deep research, SE-A)
  - docs/research/2026-05-18-site-engine-dual-audience-tension.md (conflict-surface deep research)
  - docs/research/2026-05-18-site-engine-vertical-conventions.md (vertical-divergent anchor research)
  - docs/research/2026-05-18-site-engine-site-quality-md-retirement.md (retirement triage)
retires: docs/rubrics/site-quality.md (SE-1..SE-8, authored 2026-05-13; superseded — header-in-place, file unmoved)
revision_history:
  - 2026-05-18 v0 — initial draft proposing SE-1..SE-5 replacement of legacy SE-1..SE-8
  - 2026-05-18 v1 — locked under JR decisions: renamed SE-1..SE-5 → SE-A..SE-E (avoid collision with retired rubric);
      restored §1.5 Artifact-shape (LOCKED single landing-page surface, out-of-scope shapes named);
      AND-conjunction wrapper language made explicit across SE-A/B/D/E score-1 anchors;
      3 vertical-divergent score-1 anchors per criterion on SE-A, SE-B, SE-D (SaaS + services + e-commerce/DTC minimum);
      "We help X do Y" template entered as named Goodhart entry on SE-A;
      Ahrefs trajectory corrected to 76% → 38% AI Overview overlap with organic top-10 (v0 cited stale 12% baseline);
      §3 mediocre catalog expanded with three named modes (AI-slop landing-page, dated-but-AI-uncitable, AI-citable-but-human-cold);
      §3 structural_gate routing list expanded to 8 verifiables (schema.org, Lighthouse, axe-core, brand-token, alt-text, broken-link, mobile responsive, robots.txt);
      §8 open questions: cross-ref cleanup of 8 doc files DEFERRED to plan-002 next iteration; structural_gate expansion DEFERRED (spec first, code later); legacy `docs/rubrics/site-quality.md` retirement = deprecation-header-in-place only;
      first-cohort overfit watch added (§1 substitute-readers + §1.5 empirical-validation scope).
---

# Site Engine — Optimal-Output Spec (DRAFT v1)

Conforms to `docs/rubrics/judge-design-guide.md`. No documented breach of the ≤5 criterion ceiling — the lane's AI-failure surfaces (entity confabulation, source confabulation, recency-cutoff distortion) all route to `structural_gate` as deterministic checks rather than warranting a 6th semantic criterion. Frameworks (CXL Hero Audit / Peep Laja, April Dunford positioning, Brian Balfour positioning-first, Aggarwal KDD 2024 GEO evidence-injection, Marketing Examples / Harry Dry teardowns, Animalz, Wynter, Pencil Pages, Volpini / Kalicube AEO patterns, Profound passage-citation work, Ahrefs Q1 2026 citation-divergence findings) inform the reader/success/failure spec and constitute the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

Site engine is a **dual-audience lane** — human web visitor AND AI search engine — operating on a **single landing-page surface**. Criteria work for both readers simultaneously on the same artifact, not as separate optimizations on different surfaces. The dual-audience symmetry is real but not automatic, and the score-1 anchors that touch the conflict surface (SE-A, SE-B, SE-D, SE-E) explicitly require AND-conjunction on the behavioral description — the page must demonstrate BOTH the AI-citable form AND the human-trust substance, not a weighted blend the workflow can game by maxing the cheap side and paying the floor on the expensive side.

This v1 supersedes v0 after JR decisions applied: criterion renaming (SE-A..SE-E avoids collision with the retired SE-1..SE-8 rubric), §1.5 artifact-shape LOCKED, three vertical-divergent score-1 anchors on the vertical-sensitive criteria (SaaS + services + e-commerce/DTC minimum), explicit AND-conjunction language in the shared wrapper and per-criterion anchors, expanded structural_gate routing list, deferred cross-ref cleanup.

---

## 1. Reader — dual audience (LOCKED 2026-05-18)

The page has two co-equal readers operating in real time on the same surface.

**Primary human reader — three sub-personas, distinct but the same page must serve all three within ~10 seconds:**

- **Founder evaluating a vendor.** Has a near-term problem; scanning to decide whether to take a 30-minute call. Wants the proposition restated in their own words within the hero, evidence the vendor has solved this exact problem before, pricing or at least pricing shape (not "contact sales" alone), and a low-cost next step (book demo, free audit, sandbox). Decision time-horizon: minutes to days.
- **Recruiter / candidate checking legitimacy.** Looking for clarity that the company is real and the team is credible. Wants founder name surfaced, recent activity proof (changelog, blog dated within 90 days, current-year copyright), specific customers named with context, not logo-walls. Decision time-horizon: minutes (binary disqualify / continue).
- **Prospective client doing diligence after a referral.** Already warm. Wants to confirm category fit and risk profile fast — concrete capabilities ("we do X for Y"), surface of the pricing model, and one specific named customer or case-study link they can audit. Decision time-horizon: 10–30 minutes; will file the page as a reference if not converting immediately.

All three are smart, time-poor, and skeptical. They have seen enough AI-generated landing pages (lime-purple gradient mesh + three-icon trio + "AI-powered platform for modern teams") to recognize template-fill. They will quote one or two sentences from the page if challenged later. They have authority to act on their conclusion: book the call, file the lead, surface the company to a colleague.

**Secondary AI-engine readers** — ChatGPT, Perplexity, Claude, Google AI Mode, Gemini, You.com (the major frontier consumer-facing AI search surfaces as of Q2 2026). Each consumes the page as a passage-extraction candidate when answering a real query in this company's category. Per Ahrefs Q1 2026, AI Overview citation overlap with Google's top 10 has dropped from 76% to 38% over the prior twelve months — citation has decoupled from organic ranking faster than the SEO industry anticipated. A page that ranks #1 organically can be cited zero times by AI engines if it is not citation-shaped; the inverse is increasingly true (pages cited heavily without ranking organically). The page must earn citation on its own merits, not by proxy of ranking.

Per the Aggarwal/Volpini/Shepard/Profound/Yext literature, AI engines prefer: answer-first declarative passages (BLUF register, not query-echo), evidence injection (quotes / stats / citations with verifiable provenance), passage self-containment (40–75-word blocks and 134–167-word semantic-completeness blocks), entity stability (canonical-form naming, no drift across hero / footer / structured data), third-party validation visible on-page (analyst quotes, press citations, named-customer outcomes — Ahrefs r=0.664 brand-mention correlation versus r=0.218 backlinks), visible freshness signals (publication / update date, current-year reference, recent change), and intent-format match (pricing-page wants tables; FAQ wants Q-then-A; hero wants declarative lead).

The two readers AGREE on roughly two-thirds of the page surface — a specific value proposition + named-customer-with-outcome social proof + visible pricing shape + single primary CTA + freshness signals + canonical entity naming + third-party validation all reward both readers simultaneously, which is the dual-aligned bulk the marketing-tech consensus has correctly identified. They DISAGREE on the remaining one-third — entity-density beyond the hero, FAQ depth versus above-fold conversion path, declarative-document register versus warmth and named-human voice, third-party-validation depth versus viewport budget. The disagreement is where workflows under selection pressure will collapse; the criteria below test for the AND-conjunction on the conflict surface.

**Substitute readers the same page should also serve:** Head of Product evaluating a vendor for an upcoming roadmap decision; Marketing or Growth lead at an early- or mid-stage company evaluating a positioning or channel partner; owner-operator at a small-to-mid services firm (legal, consulting, accounting, agency, financial advisory) evaluating a vendor for an internal capability; owner-operator at a small-to-mid local-market business (healthcare practice, hospitality, retail, professional services) evaluating a digital-presence partner; e-commerce / DTC operator evaluating a platform or services vendor; B2B SaaS founder at any stage evaluating a positioning or content vendor; fintech or regulated-finance operator evaluating a tooling or service vendor.

**First-cohort anchoring is concrete, not architectural.** The b2b-tech (Anthropic, Perplexity, gofreddy.ai itself) + b2b-regulated-services (DWF) + b2c-aesthetics-healthcare (Klinika Melitus) reference set in this spec exists because those are gofreddy's current first-cohort fixture clients. They are **not** the architectural target — they are concrete anchors. The spec is designed to generalize to tech-savvy founder / early-co clients across verticals; first-cohort overfitting is an explicit risk to monitor (see §8).

**NOT the reader:** the search-engine crawler reading solely for ranking (handled by the GEO lane plus `structural_gate`, not the site_engine judge); the brand-loyalist already on the site looking for product detail (different surface — product documentation, not landing-page); the investor doing deep diligence (different artifact — data room, not landing-page).

---

## 1.5. Artifact shape (LOCKED 2026-05-18)

**The lane produces ONE landing-page surface format.** A single HTML page, possibly with deep-link references to product / pricing / about / FAQ subpages but rendered and judged as a single primary entry-point surface. Locked because shape-drift Goodhart is a documented failure mode in evolution loops: under 50-generation selection pressure, the workflow learns that single-page surfaces score well on SE-A (10-second human commit) while multi-page hub surfaces score well on SE-B (deeper passage-extractable content) and produces Frankenstein artifacts (long-scroll mega-pages, hub-with-no-hero) that don't serve any coherent reader. The lock prevents this.

**Form factor:**

- Single landing-page surface, rendered as one HTML document
- Above-fold viewport contains the hero block (value proposition + primary CTA + at least one in-viewport evidence element)
- Page contains 4–8 substantive sections below the hero: features / use-cases / social proof / pricing-or-pricing-shape / FAQ / final CTA / footer
- Category-appropriate CTA vocabulary (SaaS PLG "Start free" / sales-led "Get a demo"; services "Contact us" / "Speak to a partner"; e-commerce "Shop" / "Add to cart"; marketplace dual-CTA demand+supply; dev-tool "Read the docs" + "Get API key"; fintech "Open account" / "Sign up")
- One primary visually-dominant CTA in the hero viewport; secondary CTAs clearly demoted (smaller, lighter, secondary color, text-link weight)
- Named entity surface stable across hero / footer / structured-data / FAQ (no name drift)
- Visible publication or update date and/or current-year reference in body copy
- At least one passage self-contained in 40–75 words (hero-shape) AND at least one passage self-contained in 134–167 words (semantic-completeness shape) somewhere on the page

**Out of scope shapes (the lane will NOT produce these):**

- Multi-page site (homepage + product subpages + pricing subpage as a single unit) — future scope; for now a multi-page site is judged page-by-page with the homepage as the primary site_engine artifact
- Blog post / article / long-form content (handled by the article_engine lane)
- Hub page / topic-cluster pillar page (handled by the SEO / content-engine lanes)
- Documentation page / API reference (different reader posture; handled by the dev-docs lane when it exists)
- Pure product page (e-commerce single-product surface — judged as e-commerce-vertical landing page if it carries hero + price + add-to-cart + trust strip + reviews + email-capture)
- Pricing-only page (a `/pricing` deep-link is in-scope as an artifact only if it carries hero + tier comparison + named-customer outcomes + final-CTA pattern matching the landing-page form)

**Why one shape:** the §1 Reader spec (3-sub-persona human + AI-engine) and §2 Success spec (10-second-human-commit AND AI-engine-cite-on-category-query) point unambiguously to single-page landing-surface form. SE-A's hero-block test, SE-B's passage-extraction test, SE-C's claim-survival test, SE-D's persona-commitment test, and SE-E's freshness-and-entity-stability test all presume a coherent single-page surface where the reader can resolve their question without site-graph navigation. Multi-page hub artifacts would require an aggregate test ("does the site rank in fan-out, not just one page") which is deferred to future lane work.

**Shape enforcement lives in `structural_gate`, NOT in the judge criteria.** The judge tests outcomes (SE-A..SE-E below); the workflow's structural_gate tests artifact-shape conformance (single-page rendering, hero block presence, primary-CTA visual dominance, named-entity consistency, visible-date presence, schema.org markup validity, broken-link check, mobile responsive render, robots.txt, axe-core a11y, Lighthouse perf, brand-token compliance, image alt-text). Per design guide §11.1, this preserves the outcome-question-not-feature-check discipline at the judge layer while still defending against shape-drift and surfacing deterministic-failure modes upstream.

**Empirical validation scope.** The single landing-page form factor is research-grounded against b2b-tech / b2b-regulated-services / b2c-aesthetics-healthcare fixtures (current first-cohort: Anthropic, Perplexity, gofreddy.ai itself, DWF, Klinika Melitus) and 2026-05-13 calibration-session pages. When fixtures from structurally-divergent categories appear (marketplace two-sided pages, B2C-app store-badge-led pages, dev-tool code-block-led pages, full multi-page sites), re-validate the form factor — different categories may need shape adjustments (e.g., marketplace pages may need a split-CTA hero variant; dev-tool pages may need a code-block-in-hero variant; multi-page sites may need an aggregate scoring policy). The §1.5 lock is the b2b-tech-default; lane scope may expand or sibling-fork as the client mix evolves.

---

## 2. Success — what the readers DO (LOCKED 2026-05-18)

**Human reader.** After a ~10-second skim of the visible-without-scroll surface, the targeted persona commits to a single concrete action on the page. The action may be:

- A **primary-CTA click** — book demo, start trial, request audit, get API key, open account, shop a category, download the app, contact us, speak to a partner, depending on category-appropriate framing
- A **filing-as-reference** — the page is bookmarked, sent to a colleague, or quoted into a Slack thread as "this is the vendor we should talk to"
- A **deeper-engagement scroll** — for high-consideration categories (services, enterprise fintech), the targeted reader scrolls past the hero into the next substantive section because the hero earned the attention, with intent to continue evaluating

The reader could quote one specific sentence from the page to a peer unprompted. The action is appropriate to the page's apparent category — a "Start free trial" commitment is right for SaaS PLG and category-malformed for a Magic Circle law firm; a "Speak to a partner" commitment is right for services and category-malformed for a self-serve consumer app. **Sleep test:** if the reader slept on the page overnight, would they still send the link to a colleague tomorrow — does the page's substance survive 24h reflection, not just momentum?

**AI-engine reader.** When an AI search engine answers a real query in this company's category over the next 12 months, the page is in the candidate retrieval set AND at least one passage from the page is cited in the synthesized answer. The page recurs across query variants (fan-out coverage) and across related questions because entity, claims, and supporting evidence are stable, canonical-form, and corroborated by off-domain mentions.

**Both outcomes earned by the same page.** The dual-audience symmetry is the lane's structural posture: a page that converts humans and is AI-uncitable fails SE-B; a page that is AI-citable and human-cold fails SE-A. The AND-conjunction is explicit in every criterion that touches the conflict surface.

World-class real-world exemplars — quality anchors, NOT templates to copy:

**B2B SaaS (PLG canonical):**

- **Linear (https://linear.app)** — declarative hero "Linear is a purpose-built tool for planning and building products," single "Start building" CTA, named customer logos (Ramp, Loom, Vercel, OpenAI, Cash App, Scale, Mercury) below, visible product surface (issue tracker UI) in viewport.
- **Vercel (https://vercel.com)** — declarative hero "Build and deploy on the AI Cloud," passage self-contained answer to "what is Vercel" in the first 100 words, single primary CTA "Start Deploying" plus clearly-secondary "Get a Demo," named-customer carousel below (Under Armour, eBay, Sonos, Adobe, Notion, Stripe).
- **Stripe (https://stripe.com)** — category-defining hero "Financial infrastructure to grow your revenue," named-customer scale claim ("Millions of companies of all sizes use Stripe…"), single CTA "Start now," product surface visible.

**Professional services (gravitas-led):**

- **Slaughter & May (https://slaughterandmay.com)** — editorial-restraint hero, partner-led credibility surface, recent matters with anonymized clients, "Get in touch" contact CTA in header, no marketing froth.
- **Pinsent Masons (https://pinsentmasons.com)** — sector-led structure (Energy, Financial Services, etc.), buyers self-segment by industry, named partners surfaced in leadership grid.

**E-commerce / DTC (product-led):**

- **Allbirds (https://allbirds.com)** — full-bleed seasonal hero image + featured-product carousel with prices + "Shop Wool Runners" category-CTA + sustainability differentiator surfaced + free-shipping trust-strip.
- **Warby Parker (https://warbyparker.com)** — virtual-try-on integration + home-try-on box program both surfaced in hero, single "Find your fit" CTA.

What ties these together: category-appropriate hero content (declarative copy for SaaS; gravitas statement for services; product photo for e-commerce), one visually-dominant primary CTA matched to category, category-appropriate trust signal (named-customer-with-outcome for SaaS; named partners + matters for services; press mentions + ratings for e-commerce), at least one in-viewport evidence element, passage self-containment that serves AI-engine extraction.

---

## 3. Failure — mediocre and Goodhart-collapse (LOCKED 2026-05-18)

### 3a. Mediocre — three failure modes the judge must discriminate against

**AI-generated landing-page slop.** The 2024–2026 template: lime-and-purple gradient mesh hero + three-icon trio at 33% width each + "AI-powered platform for modern teams" / "We help [target] [verb] [outcome]" hero copy + six identical bordered cards + stock testimonial grid with circular placeholder avatars. Both Pencil Pages and Marketing Examples teardowns treat this as the dead giveaway. Fails both readers: zero entity specificity, zero verifiable evidence, no third-party voice, no category-appropriate trust signal, no in-viewport proof element. AI engines catch within 1–2 indexing cycles (template-detected pages enter "too-optimized therefore distrust" tier). Human visitors recognize the template and bounce.

**Dated-but-AI-uncitable (CRO-optimized but unparseable).** Pages converted via 2018–2022-era CRO-only optimization: strong visual hierarchy, single dominant CTA, named customers in viewport, A/B-tested headline copy — but zero content shaped as "Q: ... A: ..." or passage-self-contained 40–75-word blocks, zero off-domain validation visible, query-echo hero ("What is X?"), entity-name drift across hero / footer / structured data ("Acme Pay" / "AcmePay" / "Acme Payments"), all stats undated. Wins the 2024 conversion-design audit; loses the 2026 AI-engine citation channel entirely. Per Ahrefs Q1 2026, the page can rank #1 organically and earn zero AI citations.

**AI-citable-but-human-cold (passage-perfect but no hero proof).** Pages converted via 2025–2026-era AEO-only optimization: declarative-document register at the hero ("Acme Corp is a content engine for regulated B2B verticals serving legal, financial, and healthcare clients with AI-native research workflows"), entity-rich passages throughout, FAQPage schema with 15 question/answer pairs above the conversion CTA, citation-stuffed prose, "Last updated: 2026-05-18" stamp present — but zero warmth in the viewport, no named-human voice, no named-customer-with-outcome quote in the hero, no visible product surface, no founder name surfaced. Wins the AI-citation channel; the 18% bounce-rate delta the 2025-2026 "AI-content-hurts-SEO" studies measure as the cost. Per Digital Applied 2026 (2,000-page study): pages using "delve / leverage / synergize / optimize your experience" lose 8% CVR; pages with > 2 em-dashes per 100 words lose 5%.

### 3b. Goodhart-collapse — feature-shaped slot-fill under selection pressure

**The "We help X do Y" template convergence (primary Goodhart attack on SE-A).** AI-generated landing-page heroes converge sharply to **"We help [target] [verb] [outcome]"** — sometimes prefixed "Built for," "Trusted by," "The platform for." The template passes a feature-shaped check ("does the hero state who it's for and what it does?") with a yes — and fails the outcome test in three ways: the reader cannot name a differentiator (the template is true of GitHub, GitLab, Linear, Shortcut, Jira, Atlassian, Vercel, Render, Fly, and roughly every developer tool); the hero has no in-viewport evidence element (the template fills the viewport with positioning and leaves no room for proof); the hero invites template stacking (pages with "We help X do Y" hero almost always have feature-icon trio + bordered-card features + stock testimonial grid beneath). Defense in SE-A: score-1 anchor explicitly requires AT LEAST ONE specific evidence element in the viewport (named customer + outcome, dated stat, founder name, visible product surface, or named differentiator with concrete backing) AND warmth signals (named-human voice, customer-with-outcome story, photographic / illustrative evidence of named team) sufficient that the page does not parse as AI-generated template.

**50-generation slot-fill (broader pathology the judge must defend against).** Under 50-generation selection pressure against feature-checking judges, the workflow learns to slot-fill BOTH the human-conversion surface AND the AI-citation surface as templated patterns: every hero gets a "X is Y for Z" canonical-form template; every page stuffs three named-customer-with-outcome quotes per section; every page gets a "Last updated: YYYY-MM-DD" sticker that's always current-year; every page repeats the canonical entity name 12 times per section; every page plants 40–75-word answer-bait passages; every "social proof" section uses a templated "customer name + dated stat + outcome" sentence regardless of whether the customer is real. Structurally compliant. AI engines catch within 1–2 indexing cycles. Human visitors recognize the template and bounce. Page scores HIGH on a feature-checking judge AND LOW on actual citation and conversion. The judge must test for OUTCOMES, not surface markers.

**Historical context.** The sibling CI / MON / J1–J4 lanes have triggered three prior rollbacks for the same underlying feature-checking pathology: `2ce99bb` (σ-widening prose, J1–J4), `ca4a256` (v2 contract-prose), `698e658` → `c76f051` (Phase 4 feature-checking). The criteria below are designed to resist re-creating any of them on site_engine.

**Deterministic AI-failure checks live in `structural_gate`** — per the OpenRubrics design principle (Hard Rules → structural_gate, Principles → judge). Eight verifiables routed from judge to `structural_gate` (full list in §8):

- **Schema.org markup validity** — Organization / Product / FAQPage / BreadcrumbList syntactic validation
- **Lighthouse performance metrics** — FCP < 1.5s, CLS < 0.05, TBT < 200ms, payload ≤ section-type budget
- **axe-core a11y violations** — zero violations of severity ≥ "moderate"; WCAG AA contrast on body, AAA on critical CTAs
- **Brand-token compliance** — color / font / spacing extracted from rendered output, compared to `client_config.brand_tokens` set membership
- **Image alt-text presence** — `<img>` elements carrying meaning must have non-empty alt
- **Broken-link check** — URL HEAD resolution on cited customer / case-study links and external references
- **Mobile responsive render** — viewport meta tag present, no horizontal scroll at standard mobile widths, primary CTA reachable on mobile viewport
- **robots.txt validity** — page is crawler-accessible to the major AI-engine user agents

These are factual checks, not semantic judgments — the judge cannot deterministically verify schema validity, Lighthouse metrics, axe violations, brand-token equality, alt-text presence, URL resolution, viewport behavior, or robots.txt parsing. Routing them to `structural_gate` preserves the judge's attention for the dual-audience outcome questions and shrinks the Goodhart attack surface on the judge.

---

## 4. Criteria — outcome questions (5)

### SE-A — Human visitor commits to primary CTA

**Outcome question (binary):**
After ~10 seconds on the visible-without-scroll surface, would the targeted human persona (founder evaluating, recruiter checking, prospect doing diligence) commit to the page's primary intended action — book demo, start trial, request audit, contact us, shop a category, open account, download the app, read the docs — based on what's visible without scroll AND on the warmth signals that distinguish a real product surface from AI-generated template? Could they explain to a peer in one sentence what the company does, who it's for, and why it's different?

**Score 1 (yes)** — The visible hero block answers "what is this / who is it for / what's different" in category-appropriate register (declarative copy for SaaS; gravitas statement for services; product photo + price for e-commerce; search bar for marketplace; code block for dev tool; lifestyle photo + app-store badges for B2C app; dashboard + scale claim for fintech). ONE primary CTA is visually dominant; competing CTAs (if present) are clearly demoted in size / weight / color. At least one specific evidence element is in the viewport (named customer + outcome, dated stat, founder name, visible product surface, or named differentiator with concrete backing). **AND** the viewport contains warmth signals — named-human voice, customer-with-outcome story, photographic / illustrative evidence of named team, or concrete-specific copy that wouldn't fit any other client's site — sufficient that a returning human visitor would not file the page as AI-generated template.

Example A (do not optimize toward this): **Linear's hero** — "Linear is a purpose-built tool for planning and building products" + named customers (Ramp, Loom, Vercel, OpenAI, Cash App) + single "Start building" CTA + visible issue-tracker UI in viewport. **B2B SaaS PLG shape.**

Example B (do not optimize toward this): **Slaughter & May's homepage** — practice-area-led navigation + named-partner credibility surface + recent matters section with anonymized clients + "Get in touch" contact CTA in header. Editorial restraint; no marketing froth. **Professional-services gravitas shape.**

Example C (do not optimize toward this): **Allbirds' homepage** — full-bleed seasonal hero image + featured-product carousel with visible prices + "Shop Wool Runners" category-CTA + sustainability differentiator surfaced + free-shipping trust-strip. The product photo IS the hero. **E-commerce DTC shape.**

**Score 0 (no)** — Hero opens with a question ("What is X?"), a manifesto ("We believe…"), or a vague benefit ("save time," "increase productivity"). OR the hero is the "We help [target] [verb] [outcome]" template with no in-viewport evidence element. OR multiple competing CTAs of equal visual weight stall the reader between paths. OR social proof is logo-only or absent from viewport. OR visitor cannot infer category placement from visible copy. OR the CTA framing is category-malformed for the page's apparent category ("Start free trial" on a Magic Circle law firm; "Schedule a demo" on a meditation app; "Contact sales" on a self-serve consumer DTC product).

**Score 0.5 (unknown)** — Artifact is a section-only render and CTA / above-fold context cannot be inferred from what was provided. Emit 0.5 + "unknown" + one sentence on what would have to be present to commit to 1.

**Required CoT:**
- Step 1: Identify the page's apparent category (B2B SaaS / professional services / e-commerce or DTC / marketplace / API or developer tool / B2C app / fintech / other) from visible signals (CTA vocabulary, hero content, social-proof form, pricing convention, target reader register). Identify the named target persona and the page's primary intended action.
- Step 2: Walk the visible hero block. Identify which of {category-appropriate value proposition, category placement, differentiator, primary-CTA visual dominance, in-viewport evidence element, warmth signals} are present.
- Step 3: Emit verdict + one-sentence justification. Score 1 requires evidence-element AND warmth — not one without the other.

Do not score: schema.org markup, page-load speed, image alt-text, color-contrast ratio, brand-token equality, broken-link count, mobile-viewport behavior, robots.txt validity. Those live in `structural_gate`.

### SE-B — AI engine would cite a passage from this page

**Outcome question (binary):**
When an AI search engine answers a real query in this company's category over the next 12 months, would it find a citable passage on this page — answer-first, evidence-injected, entity-grounded, self-contained — AND would the page's off-domain corroboration surface (analyst quotes, press citations, named-customer outcomes rendered on-page) give the engine enough to cross-reference and trust?

**Score 1 (yes)** — At least one passage on the page (typically hero or a section opener) reads in declarative-document register, names the entity in canonical form, contains a verifiable specific (number with source, named customer with outcome, dated quote), and stands alone if extracted as a 40–75-word block. **AND** the page contains at least one semantic-completeness-shaped passage (~134–167 words) answering a real category question in canonical reference form (typically in FAQ, glossary, or explainer section). **AND** named off-domain validation is rendered on-page (analyst quote, press citation, named-customer story with attribution, third-party review) — not just owned-content claims about the entity.

Example A (do not optimize toward this): **Stripe's homepage** — "Used by millions of businesses, from startups to public companies, Stripe powers payments online and in person" + named customer logos linking to case studies (Atlassian, Shopify, Lyft) + per-call pricing transparent in a dedicated section + named developer-credibility section. The hero passage is extractable; the case-study links provide corroboration. **B2B fintech / SaaS evidence-injection shape.**

Example B (do not optimize toward this): **Slaughter & May's recent-matters section** — "Advised [Named Client] on [Named Transaction]" patterns with named partner attribution + dated insights articles authored by named partners on regulatory shifts + named press citations in thought-leadership feed. Extractable as standalone matter-statements; corroborated by named partner authorship. **Professional services gravitas-evidence shape.**

Example C (do not optimize toward this): **Allbirds' product page** — "Tree Runners: Made from eucalyptus tree fiber. 30% lighter than wool. Free shipping and returns." + verified-review counts and ratings + sustainability third-party certifications (B-Corp, FSC) visible + Patagonia-style impact-disclosure linked. Extractable as a passage answering "what are Allbirds shoes made of"; corroborated by third-party certs. **E-commerce DTC evidence-injection shape.**

**Score 0 (no)** — Page leads with query-echo ("What is X?") or manifesto / brand-narrative copy. All claims are vague qualitatives ("leading," "trusted," "next-generation"). Passages contain floating pronouns or require prior context to parse. Citation-stuffed prose where no individual passage stands alone as a substantive answer to a real category query. Entity-name drift across sections ("Acme Pay" / "AcmePay" / "Acme Payments"). Zero off-domain validation visible on-page. Logo-walled social proof with no quote / outcome / link / context.

**Score 0.5 (unknown)** — Entity canonical naming cannot be assessed from the artifact alone, OR the off-domain validation surface is partially-rendered and corroboration shape cannot be confirmed. Emit 0.5 + "unknown" + one sentence on what would have to be present.

**Required CoT:**
- Step 1: Extract 2–3 substantive passages from the page (hero, mid-page section opener, FAQ / explainer block). Identify the named entities and specific claims in each.
- Step 2: Test each passage for {answer-first register, evidence injection with verifiable specifics, passage self-containment at 40–75 words AND at 134–167 words, entity consistency canonical-form, named third-party / off-domain validation rendered on-page}.
- Step 3: Emit verdict + one-sentence justification. Score 1 requires extractable passage AND semantic-completeness shape AND off-domain corroboration — not one without the others.

Do not score: passage count, presence of schema markup, page word-count totals, FAQPage schema syntactic validity, URL resolution on cited links. Those live in `structural_gate`.

### SE-C — Proposition is specific enough to fail a credibility test

**Outcome question (binary):**
If a hostile reader (skeptical analyst, prospective customer in diligence, competitor's CMO running a teardown) interrogated each claim on the page, would specific claims survive — or would they retreat to "we meant that loosely"? Could the company produce the artifact backing each numeric / dated / comparative / capability claim within 24 hours?

**Score 1 (yes)** — Page contains at least 3 claims that are (a) concrete (numeric, dated, or named-entity), (b) backed by an artifact the company could produce within 24 hours (case study, screenshot, log, contract, audit report, dated changelog, named-customer quote on file), AND (c) phrased without hedge ("up to," "as much as," "designed to," "world's best," "industry-leading," "10× faster," "next-generation"). Capability claims describe MECHANISM rather than magic ("AI agents draft, engineer + human review every output" rather than "autonomous AI does the work").

Example (do not optimize toward this): "149 lenses across 9 dimensions" — specific, backed by the rubric file, no hedge. Or "Saved Cocoon 40 hours per month on expense reconciliation, per their case study dated Q1 2026" — named customer, dated outcome, specific quantification, link to verifiable artifact.

**Score 0 (no)** — All capability claims are abstract ("autonomous," "intelligent," "comprehensive," "leading," "trusted," "scalable," "enterprise-ready"). Numbers unsourced or hedged ("up to 10× faster"). Comparative claims unsubstantiated ("faster than the alternatives"). Anthropomorphized agent capability ("the AI thinks," "the platform understands") when the actual mechanism is mechanical. Hero claim inflation ("world's best," "industry-leading," "next-generation") without supporting evidence elsewhere on the page.

**Score 0.5 (unknown)** — Claims present but the artifact does not surface the evidence trails needed to evaluate whether the company could produce backing within 24 hours. Emit 0.5 + "unknown" + one sentence on what would have to be visible.

**Required CoT:**
- Step 1: List every specific claim on the page (numbers, dated facts, named entities, comparative claims, capability claims).
- Step 2: For each, test whether it is concrete + backable-within-24h + unhedged + mechanism-described (not magic-described).
- Step 3: Emit verdict + one-sentence justification.

Do not score: total claim count, claim accuracy (the judge tests for shape, not verifies factual content — fact-checking is out of scope for the semantic judge), or use of statistics in isolation. URL HEAD resolution on cited sources lives in `structural_gate`.

### SE-D — Page commits to a specific reader rather than averaging across all of them

**Outcome question (binary):**
Reading the page cold, can a senior marketer name (a) the intended persona, (b) the named alternative the page is positioning against (including non-product alternatives like "do nothing," "hire an assistant," "build in-house"), and (c) the one decision the page asks them to make? Or does the page read as written for "everyone in your industry"?

**Score 1 (yes)** — Hero copy names or unambiguously implies the target persona via choice of category placement, named customers in the viewport, voice register, or explicit "for [persona]" framing. Competitive alternatives are acknowledged somewhere on the page — either named competitors, or the non-product alternatives (status quo, in-house build, do nothing, hire a contractor) — at minimum implicitly via the differentiator framing. Primary CTA maps to a single decision the named persona could make.

Example A (do not optimize toward this): **Anthropic's persona-separated surfaces** — "For developers" (https://anthropic.com/api) vs "For enterprises" (https://anthropic.com/enterprise) as distinct landing surfaces; neither averages across the other's persona; alternatives are implicit via the explicit segmentation. **B2B AI-lab persona-commitment shape.**

Example B (do not optimize toward this): **DWF Polish RES practice page** — names the practice area (Restructuring & Insolvency) + named senior partner (Maciej Jamka) + Polish-EN-DE jurisdictional badge + recent matters with anonymized client identifiers + "Speak to a partner" contact CTA. Persona implied (Polish-market mid-cap company facing RES situation); alternative implicit (CMS / Dentons / DLA / GT BigLaw competitors). **Professional-services persona-commitment shape.**

Example C (do not optimize toward this): **Mercury's homepage** — "Banking for startups" hero + named-customer-with-outcome ("Cocoon saved 40 hours/mo") + security/compliance signal-row + "Open account" primary CTA. Persona named (startup founder / operator); alternative implicit (Brex, Bank of America business banking, traditional commercial banks). **B2B fintech persona-commitment shape.**

**Score 0 (no)** — Copy reads as written for "everyone in your industry" ("built for teams of all sizes," "the all-in-one platform for X," "modern, scalable, enterprise-ready"). No acknowledgement of competitive landscape or non-product alternatives. Multiple CTAs imply multiple personas without resolving which is primary. The page works for any company because it commits to none.

**Score 0.5 (unknown)** — Persona stated but the implied alternatives cannot be inferred from the artifact alone, or the page surfaces a persona separation in nav but the rendered artifact is one of the segmented sub-surfaces and the cross-persona context is not visible. Emit 0.5 + "unknown" + one sentence on what would resolve.

**Required CoT:**
- Step 1: Identify the target persona implied by the hero / page copy / named customers / category placement / voice register.
- Step 2: Identify the named alternatives (competitor / status quo / in-house build / hire-an-assistant / do-nothing) and the single decision the primary CTA asks for.
- Step 3: Emit verdict + one-sentence justification.

Do not score: persona-specific page variants (the artifact is one surface), header navigation structure, persona-targeting widgets (modal pop-ups, geographic banners), or explicit "For [persona]" copy presence as a feature check.

### SE-E — Provides enough freshness and entity-stability signal for AI engines to trust

**Outcome question (binary):**
Given two pages making similar claims in the same category, would an AI engine prefer THIS one based on freshness and entity-grounding signals visible in the artifact — visible date, current-year reference, consistent canonical entity naming throughout, dated third-party reference, and substantive body-content recency? AND does the freshness signal substantively reflect current reality rather than being a "Last updated YYYY-MM-DD" stamp on stale body copy?

**Score 1 (yes)** — Visible publication or update date within prior 12 months. Current-year reference in body copy (not just footer copyright). Consistent canonical entity naming throughout the page (no drift across hero / footer / FAQ / structured-data — "Stripe" not "Stripe Inc." in one place and "Stripe Payments" in another). At least one dated third-party reference (analyst report dated, press citation dated, customer case study dated). Body content references recent reality (a Q1 2026 cohort, a 2026 product launch, a recent regulatory shift, a current pricing tier) — not 2024-era claims with a freshness stamp pasted on.

Example (do not optimize toward this): a changelog dated within 30 days surfaced in the footer of a SaaS landing page, plus body copy referencing "Q1 2026" cohort data, plus a dated Forrester citation from 2026, plus consistent canonical entity name across hero / footer / Organization schema.

**Score 0 (no)** — No visible date. Copyright stuck on prior year. Entity-name drift across sections. All stats undated. OR a "Last updated YYYY-MM-DD" stamp is present but body copy is stale (references 2024 regulatory environment, named competitors that have since merged or rebranded, pricing tiers that don't match the current /pricing page, customer logos for companies that have churned).

**Score 0.5 (unknown)** — Some freshness present but one signal is stale or ambiguous (e.g., visible date present but body content recency cannot be assessed from the artifact alone). Emit 0.5 + "unknown" + one sentence on which signal.

**Required CoT:**
- Step 1: Identify visible date(s), current-year references in body copy, canonical entity naming across sections, dated third-party references.
- Step 2: Test whether body content substantively reflects current reality (current-year cohort data, current regulatory environment, current product / pricing surface) — not just whether a freshness stamp is present.
- Step 3: Emit verdict + one-sentence justification. Score 1 requires visible-date AND current-year-body-reference AND entity-consistency AND dated-third-party — not one without the others.

Do not score: schema.org markup specifics, JSON-LD validity, sitemap presence, structured-data dates as deterministic check (those live in `structural_gate`). Visible date presence as a binary check is deterministic and also lives in `structural_gate`; the judge scores whether the visible-date signal corresponds to substantive body recency.

---

## 5. Shared judge-prompt wrapper

```
You are scoring a single landing-page surface intended for BOTH a
human visitor (founder evaluating a vendor, recruiter checking
legitimacy, prospect doing diligence after referral) AND AI search
engines (ChatGPT, Perplexity, Claude, Google AI Mode, Gemini,
You.com).

The page is the lane's locked artifact shape: a single HTML
landing-page surface with a hero block in the above-fold viewport,
4–8 substantive sections below the hero, one visually-dominant
primary CTA in the hero, category-appropriate CTA vocabulary
(SaaS / services / e-commerce / marketplace / dev-tool / B2C-app /
fintech vary structurally), named-entity surface stable across
hero / footer / structured-data / FAQ, visible date or current-year
reference, at least one 40–75-word self-contained passage AND at
least one 134–167-word semantic-completeness passage.

First identify the page's apparent category (B2B SaaS / professional
services / e-commerce or DTC / marketplace / API or developer tool /
B2C app / fintech / other) from visible signals (CTA vocabulary,
hero content, social-proof form, pricing convention, target reader
register). Apply category-appropriate expectations when scoring. A
"Start free" CTA is correct for B2B SaaS PLG and category-malformed
for a Magic Circle law firm; a "Speak to a partner" CTA is correct
for professional services and category-malformed for a self-serve
consumer app. Score for category-appropriate excellence, not for any
single category's template.

Score each criterion independently with 0, 0.5, or 1 plus a
one-sentence rationale that follows the per-criterion CoT steps.
Do not blend criteria. Do not infer criteria not stated. If a
criterion's condition is ambiguous from the artifact alone, emit
0.5 + "unknown" + one sentence on what would have to be present
to commit to 1.

The dual-audience nature is structural — a page can convert humans
and be AI-uncitable, or vice versa. World-class pages do both on
the same surface. The score-1 anchors on SE-A, SE-B, SE-D, and SE-E
require AND-conjunction on the conflict surface: the page must
demonstrate BOTH the AI-citable form AND the human-trust substance,
not a weighted blend. If a page is human-warm but AI-uncitable, SE-B
fails. If a page is AI-citable but human-cold, SE-A fails. Score for
the OUTCOMES — would the human commit, would the engine cite — not
for the presence of section headers, schema markup, template
fields, or named frameworks.

The reader (human) is smart, time-poor, and skeptical. They have
seen enough AI-generated landing pages to recognize template-fill.
Test for whether the page would actually convert a specific named
persona — not for whether the hero contains the "X for Y because Z"
template fields. The reader (AI engine) reads as passage-extraction
candidate. Test for whether at least one passage stands alone as a
substantive answer to a real category query with verifiable
specifics and off-domain corroboration — not for whether the page
contains entity-stuffing or freshness-stamps.

Do not score: schema.org markup validity, page-load speed,
image alt-text, color-contrast, brand-token equality, broken-link
count, mobile-viewport behavior, robots.txt, axe-core a11y
violations, or other deterministic checks — those live in
`structural_gate`.

Emit per-criterion JSON:
{"criterion_id": "SE-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 6. Goodhart-resistance verification

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **SE-A**: The "We help [target] [verb] [outcome]" templated hero doesn't pass — must include at least one specific evidence element in the viewport AND warmth signals sufficient that the page doesn't parse as AI-generated template. Templated "X for Y because Z" hero without persona commitment OR named alternative scores 0. Category-malformed CTA framing (SaaS PLG on a Magic Circle firm; enterprise demo on a meditation app) scores 0.
- **SE-B**: Citation stuffing doesn't pass — passages must be substantively self-contained at 40–75 words AND semantic-completeness shape at 134–167 words AND off-domain corroboration rendered on-page. Entity-stuffing (canonical entity name repeated 12 times per section without substantive context) scores 0. Logo-walled social proof without quote / outcome / link scores 0.
- **SE-C**: "Designed to" / "up to 10× faster" / "industry-leading" hedged or inflated claims don't pass — must be unhedged + backable-within-24h + mechanism-described. Anthropomorphized capability claims ("autonomous," "intelligent," "thinking") without described mechanism score 0.
- **SE-D**: Generic "for everyone in your industry" copy doesn't pass — must acknowledge competitive alternatives including non-product alternatives (do nothing, hire-an-assistant, in-house build). Multiple equal-weight CTAs implying multiple personas without resolving primary score 0.
- **SE-E**: "Last updated YYYY-MM-DD" stamp without substantive current-year body content doesn't pass — freshness must be reflected in body copy (current-year cohort data, current regulatory environment, current product / pricing surface). Entity-name drift across sections scores 0.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0. The AND-conjunction on SE-A / SE-B / SE-D / SE-E score-1 anchors is the structural defense — the judge requires both the AI-citable form AND the human-trust substance on the same artifact.

---

## 7. Verification — does the v1 spec conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (3 vertical-divergent examples on SE-A, SE-B, SE-D; single hedged example on SE-C and SE-E where vertical-invariant) ✓
- §5 criterion count: **5 (no documented exception)** — the lane's AI-failure surfaces (entity confabulation, source confabulation, recency-cutoff distortion) all route to `structural_gate` rather than warranting a 6th semantic criterion (per retirement-triage research §3) ✓
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3 steps each) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §10 input sanitization: lives in `evaluate_variant.py` (per design guide), not in this spec ✓
- §11 Goodhart-resistance verification ✓
- §13 specimen criterion template followed ✓

Length per criterion ≈ 230 words on the three-vertical-example criteria (SE-A, SE-B, SE-D) and ≈ 170 words on the single-example criteria (SE-C, SE-E); longer than the design guide's 150-word target on the vertical-anchor criteria due to 3 examples per, absorbable per CI v3.3 precedent. Total spec body ≈ 4700 words including §1.5 artifact-shape and §3 expanded mediocre catalog.

---

## 8. Open questions (after v0 review + JR decisions applied)

Reader / Artifact-shape / Success / Failure / 5 Criteria are LOCKED at v1. Remaining:

1. **Redundancy check pending (urgent).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 5 criteria × 3 panel models = ~75 calls (~$30). Drop any criterion correlating > 0.7 with another. Expected live floor 3–4. Most-likely-to-merge pairs: SE-A ↔ SE-D (both test human reader fit — a page that fails persona commitment typically also fails to convert); SE-B ↔ SE-E (both test AI-engine signals — passage citability and entity stability may correlate). If both pairs merge, live floor is 3 (SE-A+D human, SE-B+E AI-engine, SE-C proposition specificity). The ≤5 ceiling is preserved either way; don't fight an absorption when it happens.

2. **Fixture validation.** Run 5 existing site_engine fixtures (gofreddy.ai canonical + DWF + Klinika Melitus + 1 b2b-tech beyond gofreddy + 1 e-commerce or DTC if available) through the locked criteria; eyeball judge rationales. If the rationales don't match human reasoning about quality, the prose is wrong, not the design. Surface findings before propagating.

3. **`structural_gate` expansion — DEFERRED (spec first, code later).** Same pattern as CI v3.3. Items moving from judge to `structural_gate` (8 verifiables already listed in §3 + a freshness-presence check from SE-E):
   - **Schema.org markup validity** — Organization / Product / FAQPage / BreadcrumbList syntactic validation
   - **Lighthouse performance metrics** — FCP < 1.5s, CLS < 0.05, TBT < 200ms, payload ≤ section-type budget
   - **axe-core a11y violations** — zero violations of severity ≥ "moderate"; WCAG AA contrast on body, AAA on critical CTAs
   - **Brand-token compliance** — color / font / spacing extracted from rendered output, compared to `client_config.brand_tokens`
   - **Image alt-text presence** — `<img>` elements carrying meaning must have non-empty alt
   - **Broken-link check** — URL HEAD resolution on cited customer / case-study links and external references
   - **Mobile responsive render** — viewport meta tag present, no horizontal scroll at standard mobile widths
   - **robots.txt validity** — page is crawler-accessible to major AI-engine user agents
   - **Visible-date presence check** — date surfaced within prior 12 months (deterministic SE-E underlying signal; the judge scores substantive body-content recency, not the binary date-presence)
   - **Entity-name consistency** — regex / token match across hero / footer / structured data; flag drift ("Acme Pay" / "AcmePay" / "Acme Payments")

   Implementation deferred. The lane v1 ships with the judge spec locked; `structural_gate` expansion lands in plan-002 next iteration alongside U15b (rubric template wiring). The existing v006 checks (3+ headings, 2+ citations, ≤2000 words, banned-phrases) stay.

4. **Legacy `docs/rubrics/site-quality.md` retirement — deprecation-header-in-place only.** Per JR posture: add a deprecation header in place pointing to this spec; DO NOT move the file yet. Moving the file breaks ~20 cross-references in `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` plus 7 other doc files (see #5 below). The file stays at `docs/rubrics/site-quality.md` with a frontmatter banner explicitly marking it superseded by this spec; historical scored variants whose `rubric_version: site-quality-v1` field references the legacy rubric stay attributable (per legacy revision policy line 330–333 and design guide §15 per-version calibration). No re-scoring of historical fixtures.

5. **Cross-reference cleanup of 8 doc files — DEFERRED to plan-002 next iteration.** Documentation files mentioning `site-quality.md` or `SE-[1-8]` that need updating once the new spec is locked:

   | File | Reference count | Action |
   |------|----------------|--------|
   | `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` | ~20 | Heaviest cleanup — TD-30, R29-R34, D26, D27, U15b, S2. Bundle into single plan-002 patch commit. |
   | `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` | self | THIS FILE — promoted to source-of-truth at v1; status updated. |
   | `docs/research/2026-05-18-judges-domain-site-engine.md` | 1 | Add "implemented in [link]" footer reference to this spec. |
   | `docs/handoffs/2026-05-18-judge-design-next-session-brief.md` | 1 | Update reference. |
   | `docs/handoffs/2026-05-15-judge-design-next-session-brief.md` | 1+ | Update reference. |
   | `docs/handoffs/2026-05-18-judge-design-7-lanes-research-dispatch.md` | 1+ | Update reference. |
   | `docs/research/2026-05-18-geo-dual-audience-tension.md` | 1 | Update reference. |
   | `docs/rubrics/site-quality.md` itself | self | Deprecation-header-in-place (no move). |

   All 8 deferred to plan-002 next iteration to avoid blocking the judge-design propagation work. No source code consumes the legacy rubric yet (U15b hasn't shipped); the migration is documentation-side only at this stage.

6. **Vertical fixture coverage.** Currently have b2b-tech (gofreddy.ai canonical) + b2b-regulated-services (DWF) + b2c-aesthetics-healthcare (Klinika Melitus) coverage in fixtures. Need to add: 1+ e-commerce / DTC fixture (to validate SE-A Example C and SE-B Example C vertical-divergence) and 1+ B2B SaaS fixture beyond gofreddy.ai itself (Anthropic or Perplexity reasonable seeds). Marketplace, dev-tool, B2C app, fintech fixtures deferred to future scope.

7. **First-cohort overfitting watch.** v1 broadened §1 Reader substitute-readers and added §1.5 Empirical-validation-scope note to reduce DWF / Klinika / gofreddy-only anchoring, but the underlying research (vertical-conventions, dual-audience-tension) was still done against b2b-tech / b2b-regulated-services / b2c-aesthetics-healthcare verticals. Monitor: when client #5+ onboards (DTC e-commerce, fintech, hospitality, regulated finance, marketplaces, B2C-app, dev-tool, content-led), check whether the spec's substitute-readers + §1.5 form factor + SE-A / SE-B / SE-D vertical anchors generalize OR whether per-vertical adjustment is needed. Re-validation trigger: any fixture from a vertical not in {b2b-tech, b2b-regulated-services, b2c-aesthetics-healthcare, b2b-SaaS, e-commerce-DTC} should prompt a quick re-validation pass on SE-A / SE-B / SE-D anchors.

8. **Overlap with GEO lane.** GEO is narrow (one landing page optimized purely for AI citation in a specific category-query context); site_engine is broader (full landing-page surface, dual audience with co-equal human-AI reader weighting). Proposed boundary: GEO judge focuses on a single page's citation-readiness in narrow AI-citation context; site_engine judge weighs both citation + human conversion + multi-section consistency on the same artifact. Confirm boundary holds when fixtures run through both judges and scores compare cleanly (no double-counting, no fragmentation of the same outcome). The dual-audience-tension research's OQ3 flags this; resolution deferred to first-fixture-pass.

9. **Voice-persona reassignment.** Legacy SE-4 (voice persona fit) reassigned to shared `voice_persona` infrastructure (article_engine, ad_engine, image_engine, linkedin_engine, x_engine all consume the same `ClientConfig.voice_persona`). Open whether site_engine should retain a `structural_gate`-level corpus-distance check (per legacy SE-4 falsifiability) for cases where landing-page copy has voice-fit signals other lanes don't surface as cleanly ("Powered by AI" boilerplate on a manifestly anti-AI-slop brand). Defer to first fixture pass; the shared voice-persona framework handles the cross-lane work, the structural_gate retention is a narrow site_engine-specific decision.

10. **Propagation to other 6 lanes.** Once site_engine v1 validates on real fixtures, this brings 2-of-8 lanes to design-locked v1 (CI v3.3, site_engine v1). Remaining 6: GEO, MON, MA, SB, X, LI. Each gets its own optimal-output-spec pass + per-lane deep-research dispatches as needed — NOT a mechanical site_engine-shaped repeat. The site_engine dual-audience structure is specific to landing-page surfaces and does not transfer to monitoring digests, ad creatives, or social posts; per-lane domain research scopes the criteria.

11. **Anti-slop calibration data lifecycle.** The legacy SE-8 anti-slop feature-checklist (lime-purple palette, three-icon trio, "We help you" pattern, six bordered cards, gradient mesh) remains useful as workflow-side meta-agent training material ("do not produce content matching `docs/rubrics/site-quality.md` §SE-8") without being judge-side scoring criteria. Clean separation: workflow-side anti-pattern awareness ≠ judge-side feature-checking. Confirm the workflow-side incorporation doesn't drift back into judge prose. The deprecation-header-in-place pattern (open question 4) preserves the legacy SE-8 catalog for workflow-side consumption without re-routing it to the judge.
