---
date: 2026-05-18 v3 (Option D surgical edits 2026-05-19 per spot-check audit)
type: judge-design Step 1 — site_engine optimal-output spec (dual audience; Component A judge + lane-roadmap pointer)
status: DRAFT v3 — Option D surgical edits per 2026-05-19 spot-check; judge layer LOCKED at SE-A..SE-E single landing-page surface (criterion prose unchanged from v1); lane-roadmap content (3-phase deliverable list, modern-lever detail catalog, sibling-fork operational triggers) extracted to parallel plan-002 input doc; Substrate-Readiness Gate added; sibling-fork priority reordered for first-cohort vertical mix; "must produce" softened to capability framing
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
gold_standard_exemplar: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI v3.4)
roadmap_extraction: docs/handoffs/2026-05-19-site-engine-roadmap.md (3-phase deliverable list + modern-lever cuts/adds detail catalog + sibling-fork operational triggers — extracted from v3 per spot-check)
companions:
  - docs/research/2026-05-18-judges-domain-site-engine.md (generalist dual-audience domain research)
  - docs/research/2026-05-18-site-engine-cxl-hero-audit.md (hero-axis deep research, SE-A)
  - docs/research/2026-05-18-site-engine-dual-audience-tension.md (conflict-surface deep research)
  - docs/research/2026-05-18-site-engine-vertical-conventions.md (vertical-divergent anchor research)
  - docs/research/2026-05-18-site-engine-site-quality-md-retirement.md (retirement triage)
  - docs/research/2026-05-19-site-engine-comprehensive-scope.md (scope-broadening research; 30 axes across 8 clusters; 3-phase staged deliverable; comparison-page sibling-fork recommended)
  - docs/handoffs/2026-05-19-site-engine-v2-spot-check.md (adversarial spot-check audit that drove v2→v3 Option D edits)
retires: docs/rubrics/site-quality.md (SE-1..SE-8, authored 2026-05-13; superseded — header-in-place, file unmoved; retirement timing dependent on site_engine lane shipping to v006 per U15b)
revision_history:
  - 2026-05-18 v0 — initial draft proposing SE-1..SE-5 replacement of legacy SE-1..SE-8
  - 2026-05-18 v1 — locked under JR decisions: renamed SE-1..SE-5 → SE-A..SE-E (avoid collision with retired rubric);
      restored §1.5 Artifact-shape (LOCKED single landing-page surface, out-of-scope shapes named);
      AND-conjunction wrapper language made explicit across SE-A/B/D/E score-1 anchors;
      3 vertical-divergent score-1 anchors per criterion on SE-A, SE-B, SE-D;
      "We help X do Y" template entered as named Goodhart entry on SE-A;
      §3 mediocre catalog expanded with three named modes;
      §3 structural_gate routing list expanded to 8 verifiables;
      §8 deferrals on cross-ref cleanup, structural_gate expansion, legacy site-quality.md retirement.
  - 2026-05-19 v2 — School-B restructure: keep v1 SE-A..SE-E judge layer atomic + UNCHANGED at the criterion-prose level (5 criteria, no documented exception); broaden LANE scope to 3-phase staged comprehensive site program per `docs/research/2026-05-19-site-engine-comprehensive-scope.md`;
      §1 substitute readers broadened US-primary across 10 categories (SaaS / AI lab / agency / service firm / finance / fintech / e-commerce / B2C app / marketplace / dev-tool);
      §1.5 form-factor LOCKED for judge (Component A: home + 2-3 primary landing pages) + EXPANDED for lane (Phase-1 / Phase-2 / Phase-3 deliverable lists + size envelopes; Phases 2-3 validated by structural_gate not the judge);
      §2 success expanded — what the reader DOES across the program (commit to redesign / execute Phase 1 within 30 days / roll out Phase 2 by Day 60 / run Phase 3 CRO+measurement program ongoing) + exemplars across 10 verticals;
      §3 mediocre expanded with 14 cuts + 15 modern-lever adds; §3 SITE-specific AI-failure surfaces all routed to structural_gate;
      §4 criterion prose UNCHANGED — modern-lever bias added to score-1 anchors only where research adds apply;
      §5 wrapper UNCHANGED + landing-page core scope reaffirmed;
      §6 Goodhart-resistance UNCHANGED + per-component modes added;
      §7 verification — 5-criterion ceiling preserved; no documented exception;
      §8 sibling-fork triggers documented (`comparison_engine` first; `cro_test_program`; `site_landing_variants`) + retirement migration plan unchanged.
  - 2026-05-19 v3 — Option D surgical edits per spot-check audit (`docs/handoffs/2026-05-19-site-engine-v2-spot-check.md`).
      ~4,400 words of roadmap content extracted to `docs/handoffs/2026-05-19-site-engine-roadmap.md` (Phase-1/2/3 deliverable enumeration, 14-cuts + 15-adds detail catalog, sibling-fork operational triggers, multi-deliverable evolution-loop architecture, cross-lane consistency design, retainer-shape revenue model commentary).
      §1.5b "must produce" softened to "capable of producing under scope-appropriate engagement" — capability framing not delivery commitment.
      §1.5 Substrate-Readiness Gate clause added — Phase 1 ships at substrate-current; Phase 2 + Phase 3 ship as substrate emission catches up; site_engine lane itself unshipped (U15b unshipped) so even Phase 1 judging gated on lane scaffolding landing first.
      Sibling-fork priority REORDERED (site_audit_engine HIGHEST PRIORITY; comparison_engine SECOND) per first-cohort vertical-mix analysis — 2 of 3 active first-cohort (Klinika regulated-medical + DWF regulated-legal) fit poorly with comparison_engine; site_audit_engine generalizes across all 3 first-cohort verticals. Trigger for site_audit_engine: ≥3 clients OR ≥15% revenue. Trigger for comparison_engine: ≥3 clients in unregulated-vertical contexts OR ≥15% revenue.
      §1 first-cohort overfitting clause explicit + legacy `site-quality.md` retirement timing dependency surfaced (retirement gated on site_engine lane shipping to v006).
      SE-A..SE-E criterion prose UNCHANGED (per design-guide protect); AND-conjunction wrapper UNCHANGED; 5-criterion ceiling preserved with no documented exception; all v1 surgical restorations preserved; no scope-reduction from substrate-target perspective (Phase 1+2+3 stays in v3 just routed to roadmap doc for the lane-program detail).
---

# Site Engine — Optimal-Output Spec (DRAFT v3)

Conforms to `docs/rubrics/judge-design-guide.md`. **No documented breach of the ≤5 criterion ceiling.** The lane's AI-failure surfaces (entity confabulation, source confabulation, recency-cutoff distortion, schema fabrication, persona-misclassification under multi-page generation) all route to `structural_gate` as deterministic checks rather than warranting a 6th semantic criterion. Frameworks (CXL Hero Audit / Peep Laja, April Dunford positioning, Brian Balfour positioning-first, Aggarwal KDD 2024 GEO evidence-injection, Marketing Examples / Harry Dry teardowns, Animalz, Wynter, Pencil Pages, Volpini / Kalicube AEO patterns, Profound passage-citation work, Ahrefs Q1 2026 citation-divergence findings, Kalicube / Jason Barnard Entity SEO, Anthropic / Mintlify llms.txt convention) inform the reader/success/failure spec and constitute the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

**v3 architectural posture (Option D surgical edits per 2026-05-19 spot-check):** keep v1 SE-A..SE-E LOCKED at the judge layer for the landing-page surface (the single most-load-bearing artifact in any modern agency engagement, the front door the dual-audience symmetry has to be earned on); the LANE's broader deliverable scope (3-phase staged comprehensive site program a 2026 AI-native agency can produce per `docs/research/2026-05-19-site-engine-comprehensive-scope.md`) is documented in the parallel roadmap doc `docs/handoffs/2026-05-19-site-engine-roadmap.md` rather than enumerated inside this judge spec. The judge scopes **Component A** (Phase-1 home + 2-3 primary landing pages); `structural_gate` validates Phases 2-3 deliverables via the 8 verifiables routing list (schema.org markup validity, Lighthouse performance, axe-core a11y, brand-token compliance, image alt-text, broken-link check, mobile responsive render, robots.txt validity). Comparison-page warfare, customer-story library, per-vertical industry pages, blog architecture, resource center, CRO test program, AEO citation tracking, and Knowledge Panel + Wikipedia + Wikidata integration are **lane deliverables judged by `structural_gate` deterministic conformance plus broader-program outcomes** — sibling-fork triggers documented in the roadmap doc (`site_audit_engine` HIGHEST PRIORITY, `comparison_engine` SECOND — priority reordered v3 per first-cohort vertical-mix analysis; 2 of 3 active first-cohort clients fit poorly with comparison_engine; site_audit_engine generalizes cross-vertically).

The dual-audience symmetry is the lane's structural posture on Component A. The lane's broader program adds modern-lever bias (AEO-native architecture, demo-direct CTAs, founder visibility, named-customer outcomes, per-ICP variants, pricing transparency, comparison warfare, current-year cohort data, compounding cadence) that the v1 spec underweighted — these survive as inline ADD references in score-1 anchor sub-points where the research-adds apply, and the full detail catalog lives in the roadmap doc. **Criterion prose at the judge layer is unchanged from v1.**

This v3 preserves v2's lane-scope research grounding while moving the lane-program enumeration to where lane-program material belongs (the parallel roadmap doc). The judge spec retains comprehensive-scope reference at §1.5a + per-criterion ADD/CUT examples in §3 via inline brief mentions.

---

## 1. Reader — dual audience (LOCKED 2026-05-18 v1; broadened 2026-05-19 v2)

The page has two co-equal readers operating in real time on the same surface.

**Primary human reader — three sub-personas, distinct but the same page must serve all three within ~10 seconds (UNCHANGED from v1):**

- **Founder evaluating a vendor.** Has a near-term problem; scanning to decide whether to take a 30-minute call. Wants the proposition restated in their own words within the hero, evidence the vendor has solved this exact problem before, pricing or at least pricing shape (not "contact sales" alone), and a low-cost next step (book demo, free audit, sandbox). Decision time-horizon: minutes to days.
- **Recruiter / candidate checking legitimacy.** Looking for clarity that the company is real and the team is credible. Wants founder name surfaced, recent activity proof (changelog, blog dated within 90 days, current-year copyright), specific customers named with context, not logo-walls. Decision time-horizon: minutes (binary disqualify / continue).
- **Prospective client doing diligence after a referral.** Already warm. Wants to confirm category fit and risk profile fast — concrete capabilities ("we do X for Y"), surface of the pricing model, and one specific named customer or case-study link they can audit. Decision time-horizon: 10–30 minutes; will file the page as a reference if not converting immediately.

All three are smart, time-poor, and skeptical. They have seen enough AI-generated landing pages (lime-purple gradient mesh + three-icon trio + "AI-powered platform for modern teams") to recognize template-fill. They will quote one or two sentences from the page if challenged later. They have authority to act on their conclusion: book the call, file the lead, surface the company to a colleague.

**Secondary AI-engine readers** — ChatGPT, Perplexity, Claude, Google AI Mode, Gemini, You.com (the major frontier consumer-facing AI search surfaces as of Q2 2026). Each consumes the page as a passage-extraction candidate when answering a real query in this company's category. Per Ahrefs Q1 2026, AI Overview citation overlap with Google's top 10 has dropped from 76% to 38% over the prior twelve months — citation has decoupled from organic ranking faster than the SEO industry anticipated. A page that ranks #1 organically can be cited zero times by AI engines if it is not citation-shaped; the inverse is increasingly true (pages cited heavily without ranking organically). The page must earn citation on its own merits, not by proxy of ranking.

Per the Aggarwal/Volpini/Shepard/Profound/Yext literature, AI engines prefer: answer-first declarative passages (BLUF register, not query-echo), evidence injection (quotes / stats / citations with verifiable provenance), passage self-containment (40–75-word blocks and 134–167-word semantic-completeness blocks), entity stability (canonical-form naming, no drift across hero / footer / structured data), third-party validation visible on-page (analyst quotes, press citations, named-customer outcomes — Ahrefs r=0.664 brand-mention correlation versus r=0.218 backlinks), visible freshness signals (publication / update date, current-year reference, recent change), and intent-format match (pricing-page wants tables; FAQ wants Q-then-A; hero wants declarative lead).

The two readers AGREE on roughly two-thirds of the page surface — a specific value proposition + named-customer-with-outcome social proof + visible pricing shape + single primary CTA + freshness signals + canonical entity naming + third-party validation all reward both readers simultaneously, which is the dual-aligned bulk the marketing-tech consensus has correctly identified. They DISAGREE on the remaining one-third — entity-density beyond the hero, FAQ depth versus above-fold conversion path, declarative-document register versus warmth and named-human voice, third-party-validation depth versus viewport budget. The disagreement is where workflows under selection pressure will collapse; the criteria below test for the AND-conjunction on the conflict surface.

**Substitute readers the same page should also serve — US-primary, 10 categories (BROADENED 2026-05-19 v2):**

The v1 substitute-reader list (Head of Product / Marketing or Growth lead / owner-operator services / owner-operator local-market / e-commerce DTC operator / B2B SaaS founder / fintech operator) is preserved and re-organized into the 10 categories the lane's deliverable scope explicitly addresses (per research §4 vertical adjustments):

1. **B2B SaaS (PLG and sales-led, including dev-tool subgenre)** — startup founders, growth leads, RevOps, IT decision-makers at any stage company evaluating positioning, channel, or platform vendor. Exemplars: Linear, Vercel, Stripe, Notion, Cal.com, Plausible, PostHog, Modal, Twilio.
2. **AI labs / AI-native infrastructure** — researchers, infrastructure leads, developer-platform evaluators, enterprise procurement teams at AI labs evaluating positioning or competitor-product threats. Exemplars: Anthropic, OpenAI, Mistral, Cohere, Hugging Face.
3. **Agency / consulting / content brand** — agency principals, content-program leads, named-author thought-leaders evaluating positioning or platform partner. Exemplars: Animalz, First Round Capital, Wynter, Marketing Examples, Pencil Pages. (gofreddy itself fits here.)
4. **Professional services (legal, accounting, consulting, financial advisory)** — partner committees, owner-operators at small-to-mid services firms; managing partners at BigLaw / consulting evaluating lateral-flight or competitive moves. Exemplars: Slaughter & May, Pinsent Masons, DWF, McKinsey, EY, Skadden.
5. **Finance / fintech / financial services** — operator at fintech or regulated-finance company; B2B-fintech sales target (CFO, finance ops); B2C-fintech consumer. Exemplars: Mercury, Ramp, Brex, Stripe, Wise, Wealthfront, Cash App, Robinhood.
6. **E-commerce / DTC** — DTC operator, brand director, e-commerce platform evaluator. Exemplars: Allbirds, Warby Parker, Glossier, Patagonia, Aesop, Everlane.
7. **B2C app (wellness / fitness / consumer-finance / productivity)** — consumer reading app-store landing surfaces; investor or media reading for company diligence. Exemplars: Calm, Headspace, Strava, Cash App, Robinhood, Notion mobile.
8. **Marketplace / two-sided platform** — demand-side discovery user; supply-side recruitment target; investor or strategy lead evaluating marketplace dynamics. Exemplars: Airbnb, Etsy, DoorDash, Uber, Upwork.
9. **Dev-tool / API platform (subgenre of B2B SaaS, called out separately because the form factor is structurally different)** — developer evaluating API; engineering lead evaluating platform; technical buyer with code-block-in-hero expectation. Exemplars: Stripe, Twilio, Vercel, Cloudflare, Anthropic API, OpenAI Platform, Modal, Replicate.
10. **Healthcare / aesthetic-medical (regulated)** — practice owner; medical director; patient evaluating provider; jurisdiction-specific regulatory constraints (Polish medical advertising, US HIPAA) materially affect form. Exemplars: Mayo Clinic, Cleveland Clinic, Klinika Melitus (gofreddy first-cohort canonical), Curology.

**First-cohort anchoring is concrete, not architectural (UNCHANGED).** The b2b-tech (Anthropic, Perplexity, gofreddy.ai itself) + b2b-regulated-services (DWF) + b2c-aesthetics-healthcare (Klinika Melitus) reference set exists because those are gofreddy's current first-cohort fixture clients. They are **not** the architectural target — they are concrete anchors. The spec is designed to generalize to tech-savvy founder / early-co clients across the 10 categories above; first-cohort overfitting is an explicit risk to monitor (see §8).

**First-cohort overfitting — explicit posture clause (v3 surfaced).** The spec's substitute-reader breadth (10 categories) and modern-lever bias (research-grounded against B2B SaaS / AI lab / fintech exemplars) is intentionally broader than the current first-cohort fixture mix. Two consequences this clause makes explicit:

1. **Sibling-fork prioritization must engage with the actual first-cohort vertical mix, not the SaaS-canonical exemplar set.** Per the 2026-05-19 spot-check finding: comparison_engine fits poorly for regulated-vertical first-cohort (Klinika medical advertising, DWF legal marketing) — site_audit_engine generalizes across all 3 first-cohort verticals. v3 reorders sibling-fork priority accordingly (see §8b).
2. **Legacy `docs/rubrics/site-quality.md` retirement timing is dependent on the site_engine lane actually shipping to v006** (per project memory: U15b unshipped). The spec proposes SE-A..SE-E as the replacement scoring surface, but no production code consumes the new spec yet; the legacy SE-1..SE-8 rubric stays in place with the deprecation-header pattern until lane scaffolding lands and historical-fixture attribution migration is possible. Retirement is a downstream consequence of lane shipping, not a precondition.

**NOT the reader:** the search-engine crawler reading solely for ranking (handled by the GEO lane plus `structural_gate`, not the site_engine judge); the brand-loyalist already on the site looking for product detail (different surface — product documentation, not landing-page); the investor doing deep diligence (different artifact — data room, not landing-page).

---

## 1.5. Artifact shape — judge layer LOCKED, lane scope BROADENED (2026-05-19 v2)

### 1.5a. Judge artifact (Component A) — LOCKED at single landing-page surface

**The judge scores ONE landing-page surface format.** A single HTML page, possibly with deep-link references to product / pricing / about / FAQ subpages but rendered and judged as a single primary entry-point surface. Locked because shape-drift Goodhart is a documented failure mode in evolution loops: under 50-generation selection pressure, the workflow learns that single-page surfaces score well on SE-A (10-second human commit) while multi-page hub surfaces score well on SE-B (deeper passage-extractable content) and produces Frankenstein artifacts (long-scroll mega-pages, hub-with-no-hero) that don't serve any coherent reader. The lock prevents this.

**Component A = the home page + 2-3 primary landing pages (per-ICP / per-channel variants).** These are the judge-tested artifacts. Form factor (UNCHANGED from v1):

- Single landing-page surface, rendered as one HTML document
- Above-fold viewport contains the hero block (value proposition + primary CTA + at least one in-viewport evidence element)
- Page contains 4–8 substantive sections below the hero: features / use-cases / social proof / pricing-or-pricing-shape / FAQ / final CTA / footer
- Category-appropriate CTA vocabulary (SaaS PLG "Start free" / sales-led "Get a demo"; services "Contact us" / "Speak to a partner"; e-commerce "Shop" / "Add to cart"; marketplace dual-CTA demand+supply; dev-tool "Read the docs" + "Get API key"; fintech "Open account" / "Sign up"; B2C app "Download" + app-store badges; AI lab "Try the API" + "Talk to us"; agency "Start a project" + "Book a call")
- One primary visually-dominant CTA in the hero viewport; secondary CTAs clearly demoted (smaller, lighter, secondary color, text-link weight)
- Named entity surface stable across hero / footer / structured-data / FAQ (no name drift)
- Visible publication or update date and/or current-year reference in body copy
- At least one passage self-contained in 40–75 words (hero-shape) AND at least one passage self-contained in 134–167 words (semantic-completeness shape) somewhere on the page

**Out of scope shapes for the judge (the judge will NOT score these):**

- Multi-page site as a single unit (homepage + product subpages + pricing subpage judged together) — judged page-by-page with the homepage as the primary site_engine judge-artifact
- Blog post / article / long-form content (handled by the article_engine lane)
- Hub page / topic-cluster pillar page (handled by the SEO / content-engine lanes)
- Documentation page / API reference (different reader posture; handled by the dev-docs lane when it exists)
- Pure product page (judged as e-commerce-vertical landing page if it carries hero + price + add-to-cart + trust strip + reviews + email-capture)
- Pricing-only page (a `/pricing` deep-link is in-scope as a judge-artifact only if it carries hero + tier comparison + named-customer outcomes + final-CTA pattern matching the landing-page form)

### 1.5b. Lane scope — capability framing + roadmap extraction (v3)

**The lane is CAPABLE of producing a 3-phase staged comprehensive site program when engagement scope demands it.** Not all engagements require all deliverables; substrate-readiness gates apply per deliverable. The full Phase-1 / Phase-2 / Phase-3 deliverable enumeration + per-phase size envelopes has been extracted to the parallel roadmap doc — see below.

**Roadmap content (3-phase deliverable list, modern-lever cuts/adds detail catalog, sibling-fork operational triggers) extracted to `docs/handoffs/2026-05-19-site-engine-roadmap.md`. Spec retains comprehensive-scope reference at §1.5a + per-criterion ADD/CUT examples in §3a/c via inline brief mentions.**

**Capability framing (not delivery commitment).** Per the 2026-05-19 spot-check finding: the lane is **capable of producing the following deliverables when engagement scope demands them; not all engagements require all deliverables; substrate-readiness gates apply per deliverable**. The 30/60/90 timing in the roadmap doc is the SOTA-anchored comprehensive workflow target (research-derived from Stripe / Linear / Mercury / Anthropic exemplars), NOT a hard delivery commitment against any specific client engagement. First-cohort retainer reality is unobserved as of 2026-05-19 (neither Klinika nor DWF has shipped a retainer engagement); the 30-deliverable program describes the agency's CAPABILITY ceiling, not its observed cadence.

**Component A remains the judge-tested core** (Phase 1 home + 2-3 primary landing pages); Phases 2-3 deliverables are validated by `structural_gate` deterministic checks and broader-program outcomes, not the SE-A..SE-E semantic judge.

**Substrate-readiness gate.** The 3-phase comprehensive site program (Phase 1 Days 0-30 [judge core: home + 2-3 primary landing pages] + Phase 2 Days 31-60 [comparison pages + use-case + industry + product + customer pages + blog architecture + resource center] + Phase 3 Days 61-90+ [CRO + email + chat + GDPR + sticky CTA + onboarding + Custom GPT + Knowledge Panel + analytics]) describes the COMPREHENSIVE workflow target. Phase 1 judge core (home + 2-3 primary landing pages) ships at substrate-current. Phase 2 + Phase 3 deliverables ship as substrate emission catches up — each requires its own workflow tooling (comparison-page generator for §F; CRO test framework for Phase 3; etc.). Until each phase's substrate emits, structural_gate validates Phase 1 only. Comprehensive scope is the SPEC TARGET; client-side shipping gated on substrate readiness. site_engine lane itself has not been shipped to v006 (per memory: U15b unshipped) — even Phase 1 judging requires the lane scaffolding to land first.

### 1.5c. Shape enforcement split

**Component A (Phase-1 home + 2-3 primary landing pages) → judge (SE-A..SE-E outcomes).** The judge tests OUTCOMES (would the human commit; would the engine cite; would the proposition survive credibility; does it commit to a specific reader; is freshness substantive).

**Phases 2-3 deliverables → `structural_gate` 8 verifiables + broader-program outcomes.** Per design guide §11.1 (Hard Rules → structural_gate, Principles → judge), `structural_gate` validates:

1. **Schema.org markup validity** — Organization / Product / FAQPage / BreadcrumbList / Article / Speakable / LocalBusiness / MedicalBusiness / LegalService / FinancialService syntactic validation, per page-type
2. **Lighthouse performance metrics** — FCP < 1.5s, CLS < 0.05, TBT < 200ms, LCP < 2.5s, INP < 200ms, payload ≤ section-type budget
3. **axe-core a11y violations** — zero violations of severity ≥ "moderate"; WCAG AA contrast on body, AAA on critical CTAs
4. **Brand-token compliance** — color / font / spacing extracted from rendered output, compared to `client_config.brand_tokens` set membership
5. **Image alt-text presence** — `<img>` elements carrying meaning must have non-empty alt
6. **Broken-link check** — URL HEAD resolution on cited customer / case-study links and external references
7. **Mobile responsive render** — viewport meta tag present, no horizontal scroll at standard mobile widths, primary CTA reachable on mobile viewport
8. **robots.txt validity** — page is crawler-accessible to the major AI-engine user agents (ChatGPT, Perplexity, Claude, Gemini, Google AI Mode, You.com)

These are factual checks, not semantic judgments. Routing them to `structural_gate` preserves the judge's attention for the dual-audience outcome questions and shrinks the Goodhart attack surface on the judge.

**Empirical validation scope.** The single landing-page form factor (Component A) is research-grounded against b2b-tech / b2b-regulated-services / b2c-aesthetics-healthcare fixtures (current first-cohort: Anthropic, Perplexity, gofreddy.ai itself, DWF, Klinika Melitus) and 2026-05-13 calibration-session pages. The 10-category vertical mix above (§1) is the v2 broadened anchor. When fixtures from structurally-divergent categories appear (marketplace two-sided pages, B2C-app store-badge-led pages, dev-tool code-block-led pages, full multi-page sites), re-validate the form factor — different categories may need shape adjustments (e.g., marketplace pages may need a split-CTA hero variant; dev-tool pages may need a code-block-in-hero variant; multi-page sites may need an aggregate scoring policy). The §1.5a Component-A lock is the b2b-tech-default + extended-by-the-10-category-mix; lane scope may expand or sibling-fork as the client mix evolves (see §8).

---

## 2. Success — what the readers DO across the program (LOCKED 2026-05-18 v1; broadened 2026-05-19 v2)

### 2a. Component-A success — the judge tests this

**Human reader.** After a ~10-second skim of the visible-without-scroll surface, the targeted persona commits to a single concrete action on the page. The action may be:

- A **primary-CTA click** — book demo, start trial, request audit, get API key, open account, shop a category, download the app, contact us, speak to a partner, depending on category-appropriate framing
- A **filing-as-reference** — the page is bookmarked, sent to a colleague, or quoted into a Slack thread as "this is the vendor we should talk to"
- A **deeper-engagement scroll** — for high-consideration categories (services, enterprise fintech), the targeted reader scrolls past the hero into the next substantive section because the hero earned the attention, with intent to continue evaluating

The reader could quote one specific sentence from the page to a peer unprompted. The action is appropriate to the page's apparent category. **Sleep test:** if the reader slept on the page overnight, would they still send the link to a colleague tomorrow — does the page's substance survive 24h reflection, not just momentum?

**AI-engine reader.** When an AI search engine answers a real query in this company's category over the next 12 months, the page is in the candidate retrieval set AND at least one passage from the page is cited in the synthesized answer. The page recurs across query variants (fan-out coverage) and across related questions because entity, claims, and supporting evidence are stable, canonical-form, and corroborated by off-domain mentions.

**Both outcomes earned by the same page.** The dual-audience symmetry is the lane's structural posture: a page that converts humans and is AI-uncitable fails SE-B; a page that is AI-citable and human-cold fails SE-A. The AND-conjunction is explicit in every criterion that touches the conflict surface.

### 2b. Program-level success — what the reader DOES across the engagement (structural_gate + outcome telemetry)

The site_engine engagement is a multi-component compounding program, not a one-shot landing-page rebuild. Program-level success is the reader (the client decision-maker, typically the founder or the marketing / growth lead) committing to and executing the full 3-phase program:

- **Commits to the redesign program.** After reading the site audit + IA recommendations + prescription document, the client commits to the engagement — signs the SOW, dedicates internal team capacity, sets the kickoff date. The audit deck and prescription doc must surface enough specific gaps (named pages failing named axes, named competitors winning named comparison-query slots, named missing AEO infrastructure) that the client cannot rationalize delay.
- **Executes Phase 1 within 30 days.** Home page + 2-3 primary landing pages ship live (judge-tested via SE-A..SE-E); pricing page redesigned with tier transparency; about / founders page surfaces named-founder + LinkedIn / X / podcast linkage; first customer-story authored; llms.txt + Schema.org + robots.txt + sitemap.xml deployed; mobile UX + axe-core a11y + Lighthouse baseline + measurement layer live.
- **Rolls out Phase 2 by Day 60.** Comparison pages live (top 3 competitors); use-case + industry + product / feature pages; blog hub with 4 initial named-author posts; resource center skeleton + 2-3 resources; first CRO tests running.
- **Runs Phase 3 CRO / measurement program ongoing.** CRO test cadence (monthly cycles with hypothesis + sample + decision + learning); email capture + form optimization; live chat with AI-first triage + human handoff; cookie / privacy compliance; sticky / scroll-aware CTA; onboarding integration; Knowledge Panel + Wikipedia + Wikidata strategy; AEO citation audit on quarterly cadence; compounding content cadence (1-2 blog posts/week; 1 case study/month; 1 comparison page/month; monthly freshness audit; quarterly entity-stability audit; quarterly AEO citation audit).

The 30/60/90 → retainer transition is the lane's deliverable arc; the retainer covers ongoing compounding work. Program-level outcomes are tracked via the measurement layer (E5 in research) — funnel CVR, per-channel CVR, AI-citation share by engine, comparison-page win/loss rate, blog publication cadence, freshness-audit lapse rate.

### 2c. Exemplars across 10 verticals (modern-lever bias; do not optimize toward these)

World-class real-world program-level exemplars — quality anchors, NOT templates to copy:

**B2B SaaS (PLG canonical):**

- **Linear (https://linear.app)** — declarative hero + named customers (Ramp, Loom, Vercel, OpenAI, Cash App, Scale, Mercury) + visible product surface + single "Start building" CTA + dated changelog + comparison program (Linear vs Jira, Linear vs Asana) + founder visibility (Karri Saarinen named) + transparent pricing.
- **Vercel (https://vercel.com)** — declarative hero + passage self-containment + named-customer carousel (Under Armour, eBay, Sonos, Adobe, Notion, Stripe) + per-product page discipline + dated changelog + AEO-native docs.
- **Stripe (https://stripe.com)** — evidence injection + named customer scale + per-product / per-vertical / per-developer pages + comprehensive trust center + dense docs cited heavily by AI engines + visible pricing transparency.
- **Notion (https://notion.so)** — persona segmentation (`/personal`, `/teams`, `/enterprise`) + template gallery as demo path + multi-format IA.

**AI labs / AI infrastructure:**

- **Anthropic (https://anthropic.com)** — persona-separated landing (`/api`, `/enterprise`) + named research + named team (Dario + Daniela Amodei) + responsible-AI surface + research papers as entity-grounding surface + llms.txt canonical (https://docs.anthropic.com/llms.txt).
- **OpenAI (https://openai.com)** — AI lab canonical + research + product split.

**Professional services (gravitas-led):**

- **Slaughter & May (https://slaughterandmay.com)** — editorial-restraint hero + partner-led credibility + recent matters with anonymized clients + "Get in touch" contact CTA + no marketing froth.
- **Pinsent Masons (https://pinsentmasons.com)** — sector-led IA + named partners + recent matters + practice-area pages.
- **DWF (https://dwfgroup.com)** — sector + practice-area + named-partner pattern with Polish RES practice page as gofreddy fixture canonical.

**Fintech / financial services:**

- **Mercury (https://mercury.com)** — "Banking for startups" persona-committed hero + named-customer-with-outcome ("Cocoon saved 40 hours/month on expense reconciliation") + named founder (Immad Akhund) + comparison page (Mercury vs Brex) + security / compliance posture.
- **Ramp (https://ramp.com)** — corporate cards + spend management + named-customer outcomes + per-vertical pages.
- **Stripe (per above)** — financial infrastructure canonical.

**E-commerce / DTC (product-led):**

- **Allbirds (https://allbirds.com)** — full-bleed seasonal hero image + featured-product carousel with prices + "Shop Wool Runners" category-CTA + sustainability differentiator surfaced + free-shipping trust-strip + verified-review counts.
- **Warby Parker (https://warbyparker.com)** — virtual-try-on integration + home-try-on box program + "Find your fit" CTA.
- **Glossier (https://glossier.com)** — beauty DTC canonical + named-founder narrative.

**B2C app:**

- **Calm (https://calm.com)** — emotion-led + app-store CTA + named-celebrity association.
- **Headspace (https://headspace.com)** — wellness canonical + emotion-led + outcome promise.

**Marketplace / two-sided:**

- **Airbnb (https://airbnb.com)** — dual-search + dual-CTA pattern + per-category landing.
- **Etsy (https://etsy.com)** — supply-side recruitment + demand-side discovery + category tiles.

**Dev-tool / API platform:**

- **Stripe / Twilio / Vercel / Cloudflare (per above)** — docs heavily cited by AI engines on "how do I do X with Y" queries.
- **Modal (https://modal.com)** — modern AI infrastructure landing with code-block hero.
- **Mintlify (https://mintlify.com)** — docs-as-product, llms.txt convention canonical.

**Agency / content brand (for gofreddy positioning context):**

- **Animalz (https://animalz.co)** — content-agency canonical + named-author thought leadership.
- **Wynter (https://wynter.com)** — B2B research + Peep Laja named visibility.
- **Marketing Examples (https://marketingexamples.com)** — Harry Dry named visibility + teardown brand.

**Healthcare / aesthetic-medical (regulated):**

- **Mayo Clinic (https://mayoclinic.org)** — institutional E-E-A-T + nested declarative-claim pattern.
- **Klinika Melitus** — gofreddy first-cohort canonical (Warsaw aesthetic dermatology + Dr. Maria Noszczyk; Polish regulatory constraints on before-after imagery).

What ties these together at the program level: category-appropriate hero content (declarative copy for SaaS; gravitas statement for services; product photo for e-commerce; code block for dev-tool), one visually-dominant primary CTA matched to category, category-appropriate trust signal (named-customer-with-outcome for SaaS; named partners + matters for services; press mentions + ratings for e-commerce; named researchers for AI labs), comparison-page coverage of dominant competitors, founder visibility surfaced, pricing transparent (or services-appropriate engagement-shape transparency), AEO-native architecture across pages (declarative leads, passage shapes, schema, llms.txt, robots.txt allow-list), dated current-year content with substantive recency, CRO test cadence, compounding content cadence.

---

## 3. Failure — mediocre, Goodhart-collapse, and AI-failure surfaces (LOCKED 2026-05-18 v1; broadened 2026-05-19 v2)

### 3a. Mediocre — modern-lever cuts (brief inline reference; full detail in roadmap doc)

Per research §2, the 2026 modern lever bias cuts 14 patterns aggressively at the lane level — logo-wall social-proof theatre, vague benefit copy, generic SaaS template hero, AI-slop landing-page pattern, classical-SEO keyword stuffing, freshness stickers without substance, generic CTAs, hidden pricing, junk FAQ, faceless brand, defensive silence on competitors, contact-form-only paths, stock-photo team pages, one home page for all paid channels. Each is named with a modern replacement (named-customer-with-outcome over logo-wall; named-mechanism over vague-benefit; demo-direct over contact-form-only; etc.).

**Full 14-cuts detail catalog (named replacement per cut + research citations) extracted to `docs/handoffs/2026-05-19-site-engine-roadmap.md` §2.** The judge tests for the OUTCOMES that result from the removal (SE-A..SE-E catch the cut patterns on Component A); the cuts apply across the full deliverable program at the lane level. Score-1 anchors below reference the modern replacements as inline ADD examples where the research-adds apply (named-customer-with-outcome preferred over logo-wall in SE-A; demo-direct CTA framing where category supports; founder visibility surfaced where category supports; pricing transparency where regulatorily possible in SE-C).

### 3b. Modern levers added — net-new deliverables (brief inline reference; full detail in roadmap doc)

Per research §3, beyond replacing the 14 cuts, the lane explicitly ADDS 15 modern levers as net-new deliverables — AEO-native architecture, comparison-page warfare, demo-direct CTAs, founder visibility integration, named-customer-with-outcome program, per-vertical / per-ICP landing surface, pricing transparency, llms.txt + Schema.org + robots.txt, current-year cohort data + dated case studies + named-author blog cadence, Knowledge Panel + Wikipedia + Wikidata strategy, CRO test program, sticky / scroll-aware CTA strategy, live chat with handoff, onboarding integration, compounding cadence.

**Full 15-adds detail catalog (per-add framing + research citations + named exemplars) extracted to `docs/handoffs/2026-05-19-site-engine-roadmap.md` §3.** These are lane-program outputs validated by `structural_gate` + program-outcome telemetry, not judge criteria — but the score-1 anchors absorb the modern-lever bias where the research-adds apply to Component A (named-customer-with-outcome quotes corroborated by external case-study links in SE-B; current-year cohort data + dated case studies in SE-E; per-ICP persona-commitment in SE-D).

### 3c. Mediocre — Component-A failure modes the judge must discriminate against (UNCHANGED from v1)

On Component A (Phase-1 home + 2-3 primary landing pages judged via SE-A..SE-E), three named mediocre modes the judge has to catch:

**AI-generated landing-page slop.** Per cut 4 above + v1 prose. Both Pencil Pages and Marketing Examples teardowns treat this as the dead giveaway. Fails both readers: zero entity specificity, zero verifiable evidence, no third-party voice, no category-appropriate trust signal, no in-viewport proof element. AI engines catch within 1–2 indexing cycles. Human visitors recognize the template and bounce.

**Dated-but-AI-uncitable (CRO-optimized but unparseable).** Pages converted via 2018–2022-era CRO-only optimization: strong visual hierarchy, single dominant CTA, named customers in viewport, A/B-tested headline copy — but zero content shaped as "Q: ... A: ..." or passage-self-contained 40–75-word blocks, zero off-domain validation visible, query-echo hero ("What is X?"), entity-name drift across hero / footer / structured data, all stats undated. Wins the 2024 conversion-design audit; loses the 2026 AI-engine citation channel entirely.

**AI-citable-but-human-cold (passage-perfect but no hero proof).** Pages converted via 2025–2026-era AEO-only optimization: declarative-document register at the hero, entity-rich passages, FAQPage schema with 15 Q-A pairs above the CTA, citation-stuffed prose, "Last updated: 2026-05-18" stamp — but zero warmth in the viewport, no named-human voice, no named-customer-with-outcome quote in the hero, no visible product surface, no founder name surfaced. Wins the AI-citation channel; loses 18% bounce-rate per 2025-2026 AI-content-hurts-SEO studies. Per Digital Applied 2026: pages using "delve / leverage / synergize / optimize your experience" lose 8% CVR; pages with > 2 em-dashes per 100 words lose 5%.

### 3d. Goodhart-collapse — feature-shaped slot-fill under selection pressure (UNCHANGED from v1)

**The "We help X do Y" template convergence (primary Goodhart attack on SE-A).** AI-generated landing-page heroes converge sharply to **"We help [target] [verb] [outcome]"** — sometimes prefixed "Built for," "Trusted by," "The platform for." The template passes a feature-shaped check ("does the hero state who it's for and what it does?") with a yes — and fails the outcome test in three ways: the reader cannot name a differentiator (the template is true of GitHub, GitLab, Linear, Shortcut, Jira, Atlassian, Vercel, Render, Fly, and roughly every developer tool); the hero has no in-viewport evidence element (the template fills the viewport with positioning and leaves no room for proof); the hero invites template stacking (pages with "We help X do Y" hero almost always have feature-icon trio + bordered-card features + stock testimonial grid beneath). Defense in SE-A: score-1 anchor explicitly requires AT LEAST ONE specific evidence element in the viewport AND warmth signals sufficient that the page does not parse as AI-generated template.

**50-generation slot-fill (broader pathology).** Under 50-generation selection pressure against feature-checking judges, the workflow learns to slot-fill BOTH the human-conversion surface AND the AI-citation surface as templated patterns: every hero gets a "X is Y for Z" canonical-form template; every page stuffs three named-customer-with-outcome quotes per section; every page gets a "Last updated: YYYY-MM-DD" sticker that's always current-year; every page repeats the canonical entity name 12 times per section; every page plants 40–75-word answer-bait passages; every "social proof" section uses a templated "customer name + dated stat + outcome" sentence regardless of whether the customer is real. Structurally compliant. AI engines catch within 1–2 indexing cycles. Human visitors recognize the template and bounce. Page scores HIGH on a feature-checking judge AND LOW on actual citation and conversion. The judge must test for OUTCOMES, not surface markers.

**Per-component Goodhart modes (new in v2; relevant to Phases 2-3 program-level work even though structural_gate-validated):**

- **Comparison-page Goodhart.** Workflow learns to publish "X vs Y" pages where every row of the comparison table magically favors the client. Reads as smear campaign; loses AEO trust signal; loses buyer trust. Defense: research §8 OQ8 + sibling-fork `comparison_engine` lane (deferred to §8 here) gets its own optimal-output spec including a `structural_gate` check that at minimum one row explicitly favors the competitor.
- **Customer-story Goodhart.** Workflow learns to publish case studies with fabricated customer names + outcomes when the client doesn't have enough real customer-story material. Defense: `structural_gate` HEAD-resolution on linked-customer URLs + named-recipient verification.
- **Persona-misclassification under multi-page generation.** Workflow under selection pressure generates multiple "ICP" landing pages that average across personas rather than committing. Defense: SE-D applied per landing page; persona-commitment AND-conjunction at the score-1 anchor.
- **Schema-fabrication.** Workflow learns to plant Schema.org markup that's syntactically valid but doesn't reflect the page's actual content (claiming Product schema on a non-product page; claiming FAQPage schema without Q-A pairs in the body). Defense: `structural_gate` cross-validates schema markup against rendered body content.
- **llms.txt poisoning.** Workflow learns to publish llms.txt declaring canonical content that doesn't match what the page actually serves. Defense: `structural_gate` validates llms.txt entries resolve to live pages with matching content.

### 3e. SITE-specific AI-failure surfaces (all routed to `structural_gate`)

Per design guide §5: no documented exception for SITE lane. The site_engine lane has AI-failure surfaces analogous to the CI lane's entity-confabulation / source-confabulation / recency-cutoff distortion modes, but each routes to `structural_gate` as a deterministic check rather than warranting a 6th semantic criterion:

- **Entity confabulation in customer-story / comparison pages.** Workflow invents customer names, fabricates customer-outcome quotes, conflates similarly-named entities. Documented at 19.9% citation-fabrication rate for GPT-4o; 37% failure rate in Perplexity production retrospectives. Routes to `structural_gate` via URL HEAD resolution + entity-existence lookup + quote-grep against source corpus.
- **Source confabulation on named third-party validation.** Workflow invents press quotes, analyst reports never published, customer-LinkedIn profiles that 404. Per HalluLens / FAITH / CompoundDeception benchmarks. Routes to `structural_gate` via URL HEAD resolution + quote-grep.
- **Recency / training-cutoff distortion.** Workflow plants "Q1 2026 cohort" copy when training cutoff is mid-2025; "recent" announcements that are months / years old; current-year copyright on stale body content. Routes to `structural_gate` via dated-source resolution + freshness-presence check (visible-date within prior 12 months) + entity-name-drift token-match.
- **Schema fabrication.** As per per-component Goodhart mode above. Routes to `structural_gate` via schema-vs-body cross-validation.
- **Persona-misclassification under multi-page generation.** As per per-component Goodhart mode above. The page-level outcome question (SE-D) catches Component-A persona-commitment; the multi-page case routes to `structural_gate` via per-page persona-tag consistency check.

**Eight verifiables routed from judge to `structural_gate` (consolidated list, applies across Component A judge surface AND Phases 2-3 lane deliverables):**

- **Schema.org markup validity** — Organization / Product / FAQPage / BreadcrumbList / Article / Speakable / LocalBusiness / MedicalBusiness / LegalService / FinancialService syntactic validation, per page-type
- **Lighthouse performance metrics** — FCP < 1.5s, CLS < 0.05, TBT < 200ms, LCP < 2.5s, INP < 200ms, payload ≤ section-type budget
- **axe-core a11y violations** — zero violations of severity ≥ "moderate"; WCAG AA contrast on body, AAA on critical CTAs
- **Brand-token compliance** — color / font / spacing extracted from rendered output, compared to `client_config.brand_tokens` set membership
- **Image alt-text presence** — `<img>` elements carrying meaning must have non-empty alt
- **Broken-link check** — URL HEAD resolution on cited customer / case-study / external-reference links
- **Mobile responsive render** — viewport meta tag present, no horizontal scroll at standard mobile widths, primary CTA reachable on mobile viewport
- **robots.txt validity** — page is crawler-accessible to the major AI-engine user agents

These are factual checks, not semantic judgments — the judge cannot deterministically verify schema validity, Lighthouse metrics, axe violations, brand-token equality, alt-text presence, URL resolution, viewport behavior, or robots.txt parsing. Routing them to `structural_gate` preserves the judge's attention for the dual-audience outcome questions and shrinks the Goodhart attack surface on the judge. **No 6th criterion needed; all AI-failure surfaces deterministically handled.**

---

## 4. Criteria — outcome questions (5; UNCHANGED at criterion-prose level from v1; modern-lever bias additions noted)

**Criterion prose at the judge layer is UNCHANGED from v1.** The 5 criteria SE-A..SE-E continue to score Component A (Phase-1 home + 2-3 primary landing pages) on the same outcome questions, score-1 / score-0 / score-0.5 anchors, and per-criterion CoT steps as v1. The v2 modern-lever bias additions are flagged inline where the research-adds apply — the criterion prose absorbs the modern-lever language (named-customer-with-outcome over logo-wall; demo-direct CTA framing; founder visibility surfaced; pricing transparency; current-year cohort substance) within the existing v1 score-1 anchors without changing what those anchors test.

### SE-A — Human visitor commits to primary CTA

**Outcome question (binary):**
After ~10 seconds on the visible-without-scroll surface, would the targeted human persona (founder evaluating, recruiter checking, prospect doing diligence) commit to the page's primary intended action — book demo, start trial, request audit, contact us, shop a category, open account, download the app, read the docs — based on what's visible without scroll AND on the warmth signals that distinguish a real product surface from AI-generated template? Could they explain to a peer in one sentence what the company does, who it's for, and why it's different?

**Score 1 (yes)** — The visible hero block answers "what is this / who is it for / what's different" in category-appropriate register (declarative copy for SaaS; gravitas statement for services; product photo + price for e-commerce; search bar for marketplace; code block for dev tool; lifestyle photo + app-store badges for B2C app; dashboard + scale claim for fintech). ONE primary CTA is visually dominant; competing CTAs (if present) are clearly demoted in size / weight / color. At least one specific evidence element is in the viewport (named customer + outcome, dated stat, founder name, visible product surface, or named differentiator with concrete backing). **AND** the viewport contains warmth signals — named-human voice, customer-with-outcome story, photographic / illustrative evidence of named team, or concrete-specific copy that wouldn't fit any other client's site — sufficient that a returning human visitor would not file the page as AI-generated template. (Modern-lever bias: named-customer-with-outcome preferred over logo-wall; demo-direct CTA framing where category supports; founder visibility surfaced where category supports.)

Example A (do not optimize toward this): **Linear's hero** — "Linear is a purpose-built tool for planning and building products" + named customers (Ramp, Loom, Vercel, OpenAI, Cash App) + single "Start building" CTA + visible issue-tracker UI in viewport. **B2B SaaS PLG shape.**

Example B (do not optimize toward this): **Slaughter & May's homepage** — practice-area-led navigation + named-partner credibility surface + recent matters section with anonymized clients + "Get in touch" contact CTA in header. Editorial restraint; no marketing froth. **Professional-services gravitas shape.**

Example C (do not optimize toward this): **Allbirds' homepage** — full-bleed seasonal hero image + featured-product carousel with visible prices + "Shop Wool Runners" category-CTA + sustainability differentiator surfaced + free-shipping trust-strip. The product photo IS the hero. **E-commerce DTC shape.**

**Score 0 (no)** — Hero opens with a question ("What is X?"), a manifesto ("We believe…"), or a vague benefit ("save time," "increase productivity"). OR the hero is the "We help [target] [verb] [outcome]" template with no in-viewport evidence element. OR multiple competing CTAs of equal visual weight stall the reader between paths. OR social proof is logo-only or absent from viewport. OR visitor cannot infer category placement from visible copy. OR the CTA framing is category-malformed for the page's apparent category ("Start free trial" on a Magic Circle law firm; "Schedule a demo" on a meditation app; "Contact sales" on a self-serve consumer DTC product).

**Score 0.5 (unknown)** — Artifact is a section-only render and CTA / above-fold context cannot be inferred from what was provided. Emit 0.5 + "unknown" + one sentence on what would have to be present to commit to 1.

**Required CoT:**
- Step 1: Identify the page's apparent category (B2B SaaS / professional services / e-commerce or DTC / marketplace / API or developer tool / B2C app / fintech / AI lab / agency / healthcare) from visible signals (CTA vocabulary, hero content, social-proof form, pricing convention, target reader register). Identify the named target persona and the page's primary intended action.
- Step 2: Walk the visible hero block. Identify which of {category-appropriate value proposition, category placement, differentiator, primary-CTA visual dominance, in-viewport evidence element, warmth signals} are present.
- Step 3: Emit verdict + one-sentence justification. Score 1 requires evidence-element AND warmth — not one without the other.

Do not score: schema.org markup, page-load speed, image alt-text, color-contrast ratio, brand-token equality, broken-link count, mobile-viewport behavior, robots.txt validity. Those live in `structural_gate`.

### SE-B — AI engine would cite a passage from this page

**Outcome question (binary):**
When an AI search engine answers a real query in this company's category over the next 12 months, would it find a citable passage on this page — answer-first, evidence-injected, entity-grounded, self-contained — AND would the page's off-domain corroboration surface (analyst quotes, press citations, named-customer outcomes rendered on-page) give the engine enough to cross-reference and trust?

**Score 1 (yes)** — At least one passage on the page (typically hero or a section opener) reads in declarative-document register, names the entity in canonical form, contains a verifiable specific (number with source, named customer with outcome, dated quote), and stands alone if extracted as a 40–75-word block. **AND** the page contains at least one semantic-completeness-shaped passage (~134–167 words) answering a real category question in canonical reference form (typically in FAQ, glossary, or explainer section). **AND** named off-domain validation is rendered on-page (analyst quote, press citation, named-customer story with attribution, third-party review) — not just owned-content claims about the entity. (Modern-lever bias: named off-domain validation should include current-year cohort data, dated press citations, named-customer-with-outcome quotes corroborated by external case-study links.)

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

**Score 1 (yes)** — Page contains at least 3 claims that are (a) concrete (numeric, dated, or named-entity), (b) backed by an artifact the company could produce within 24 hours (case study, screenshot, log, contract, audit report, dated changelog, named-customer quote on file), AND (c) phrased without hedge ("up to," "as much as," "designed to," "world's best," "industry-leading," "10× faster," "next-generation"). Capability claims describe MECHANISM rather than magic ("AI agents draft, engineer + human review every output" rather than "autonomous AI does the work"). (Modern-lever bias: pricing transparency where regulatorily possible serves as a credibility signal; "Contact us" across all tiers reads as evasion and works against this criterion.)

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

**Score 1 (yes)** — Hero copy names or unambiguously implies the target persona via choice of category placement, named customers in the viewport, voice register, or explicit "for [persona]" framing. Competitive alternatives are acknowledged somewhere on the page — either named competitors, or the non-product alternatives (status quo, in-house build, do nothing, hire a contractor) — at minimum implicitly via the differentiator framing. Primary CTA maps to a single decision the named persona could make. (Modern-lever bias: per-ICP variants are an expected lane deliverable in Phase 1; this criterion catches the case where the page averages across all personas instead of committing to one.)

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

**Score 1 (yes)** — Visible publication or update date within prior 12 months. Current-year reference in body copy (not just footer copyright). Consistent canonical entity naming throughout the page (no drift across hero / footer / FAQ / structured-data — "Stripe" not "Stripe Inc." in one place and "Stripe Payments" in another). At least one dated third-party reference (analyst report dated, press citation dated, customer case study dated). Body content references recent reality (a Q1 2026 cohort, a 2026 product launch, a recent regulatory shift, a current pricing tier) — not 2024-era claims with a freshness stamp pasted on. (Modern-lever bias: current-year cohort data + dated case studies + named-author blog cadence are expected lane deliverables; SE-E catches the case where freshness is theatrical rather than substantive.)

Example (do not optimize toward this): a changelog dated within 30 days surfaced in the footer of a SaaS landing page, plus body copy referencing "Q1 2026" cohort data, plus a dated Forrester citation from 2026, plus consistent canonical entity name across hero / footer / Organization schema.

**Score 0 (no)** — No visible date. Copyright stuck on prior year. Entity-name drift across sections. All stats undated. OR a "Last updated YYYY-MM-DD" stamp is present but body copy is stale (references 2024 regulatory environment, named competitors that have since merged or rebranded, pricing tiers that don't match the current /pricing page, customer logos for companies that have churned).

**Score 0.5 (unknown)** — Some freshness present but one signal is stale or ambiguous (e.g., visible date present but body content recency cannot be assessed from the artifact alone). Emit 0.5 + "unknown" + one sentence on which signal.

**Required CoT:**
- Step 1: Identify visible date(s), current-year references in body copy, canonical entity naming across sections, dated third-party references.
- Step 2: Test whether body content substantively reflects current reality (current-year cohort data, current regulatory environment, current product / pricing surface) — not just whether a freshness stamp is present.
- Step 3: Emit verdict + one-sentence justification. Score 1 requires visible-date AND current-year-body-reference AND entity-consistency AND dated-third-party — not one without the others.

Do not score: schema.org markup specifics, JSON-LD validity, sitemap presence, structured-data dates as deterministic check (those live in `structural_gate`). Visible date presence as a binary check is deterministic and also lives in `structural_gate`; the judge scores whether the visible-date signal corresponds to substantive body recency.

---

## 5. Shared judge-prompt wrapper (UNCHANGED from v1; landing-page core scope reaffirmed)

```
You are scoring a single landing-page surface intended for BOTH a
human visitor (founder evaluating a vendor, recruiter checking
legitimacy, prospect doing diligence after referral) AND AI search
engines (ChatGPT, Perplexity, Claude, Google AI Mode, Gemini,
You.com).

The page is the lane's locked judge-artifact shape: a single HTML
landing-page surface (Component A — the Phase-1 home page or one
of the 2-3 primary landing pages produced in the first 30 days of
the engagement) with a hero block in the above-fold viewport,
4–8 substantive sections below the hero, one visually-dominant
primary CTA in the hero, category-appropriate CTA vocabulary
(SaaS / services / e-commerce / marketplace / dev-tool / B2C-app /
fintech / AI-lab / agency / healthcare vary structurally), named-
entity surface stable across hero / footer / structured-data / FAQ,
visible date or current-year reference, at least one 40–75-word
self-contained passage AND at least one 134–167-word semantic-
completeness passage.

First identify the page's apparent category (B2B SaaS / professional
services / e-commerce or DTC / marketplace / API or developer tool /
B2C app / fintech / AI lab / agency / healthcare / other) from
visible signals (CTA vocabulary, hero content, social-proof form,
pricing convention, target reader register). Apply category-
appropriate expectations when scoring. A "Start free" CTA is correct
for B2B SaaS PLG and category-malformed for a Magic Circle law firm;
a "Speak to a partner" CTA is correct for professional services and
category-malformed for a self-serve consumer app. Score for category-
appropriate excellence, not for any single category's template.

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
`structural_gate`. Phases 2-3 deliverables (comparison pages,
use-case pages, customer-story library, blog hub, resource center,
CRO test program, AEO citation tracking, Knowledge Panel strategy)
are out of scope for this judge — they are validated by
`structural_gate` and by program-level outcome telemetry, not by
SE-A..SE-E semantic judgment.

Emit per-criterion JSON:
{"criterion_id": "SE-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 6. Goodhart-resistance verification (UNCHANGED at criterion level; per-component modes added)

### 6a. Per-criterion Goodhart resistance (UNCHANGED from v1)

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **SE-A**: The "We help [target] [verb] [outcome]" templated hero doesn't pass — must include at least one specific evidence element in the viewport AND warmth signals sufficient that the page doesn't parse as AI-generated template. Templated "X for Y because Z" hero without persona commitment OR named alternative scores 0. Category-malformed CTA framing (SaaS PLG on a Magic Circle firm; enterprise demo on a meditation app) scores 0.
- **SE-B**: Citation stuffing doesn't pass — passages must be substantively self-contained at 40–75 words AND semantic-completeness shape at 134–167 words AND off-domain corroboration rendered on-page. Entity-stuffing (canonical entity name repeated 12 times per section without substantive context) scores 0. Logo-walled social proof without quote / outcome / link scores 0.
- **SE-C**: "Designed to" / "up to 10× faster" / "industry-leading" hedged or inflated claims don't pass — must be unhedged + backable-within-24h + mechanism-described. Anthropomorphized capability claims ("autonomous," "intelligent," "thinking") without described mechanism score 0.
- **SE-D**: Generic "for everyone in your industry" copy doesn't pass — must acknowledge competitive alternatives including non-product alternatives (do nothing, hire-an-assistant, in-house build). Multiple equal-weight CTAs implying multiple personas without resolving primary score 0.
- **SE-E**: "Last updated YYYY-MM-DD" stamp without substantive current-year body content doesn't pass — freshness must be reflected in body copy (current-year cohort data, current regulatory environment, current product / pricing surface). Entity-name drift across sections scores 0.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0. The AND-conjunction on SE-A / SE-B / SE-D / SE-E score-1 anchors is the structural defense — the judge requires both the AI-citable form AND the human-trust substance on the same artifact.

### 6b. Per-component Goodhart modes (NEW in v2; handled by `structural_gate` + sibling-fork triggers)

The v2 lane scope adds Phases 2-3 deliverables that are NOT judge-scored but ARE subject to selection pressure when the workflow optimizes the program as a whole. Each per-component Goodhart mode is handled at the appropriate layer:

- **Comparison-page Goodhart** (workflow learns to publish "X vs Y" pages where every row magically favors the client) → handled at `structural_gate` by a check that at minimum one row explicitly favors the competitor (per research §8 OQ8); also a sibling-fork trigger for `comparison_engine` when comparison-page volume crosses 3+ clients (§8 below).
- **Customer-story Goodhart** (fabricated customer names + outcomes) → handled at `structural_gate` by URL HEAD resolution on linked-customer URLs + named-recipient verification + quote-grep.
- **Persona-misclassification under multi-page generation** (per-ICP variants averaging across personas) → handled at the judge layer per-page (SE-D); the multi-page case routes to `structural_gate` via per-page persona-tag consistency check.
- **Schema-fabrication** (syntactically valid markup that doesn't match body content) → handled at `structural_gate` via schema-vs-body cross-validation.
- **llms.txt poisoning** (declaring canonical content that doesn't match what the page serves) → handled at `structural_gate` via llms.txt-entry resolution + content matching.
- **CRO test program Goodhart** (running statistically-underpowered tests to "prove" a hypothesis; calling winners at 50-visit sample sizes) → handled at `structural_gate` via sample-size + significance-threshold validation on logged tests; sibling-fork trigger for `cro_test_program` when CRO testing volume becomes load-bearing.

---

## 7. Verification — does the v3 spec conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (3 vertical-divergent examples on SE-A, SE-B, SE-D; single hedged example on SE-C and SE-E where vertical-invariant) ✓
- §5 criterion count: **5 (no documented exception)** — the lane's AI-failure surfaces (entity confabulation in customer-story / comparison pages, source confabulation on named third-party validation, recency / training-cutoff distortion, schema fabrication, persona-misclassification under multi-page generation, llms.txt poisoning) all route to `structural_gate` rather than warranting a 6th semantic criterion. **The Phases 2-3 deliverable expansion does NOT add criteria at the judge layer** — Component A (Phase-1 home + 2-3 landing pages) remains the sole judge surface; Phases 2-3 are `structural_gate` + program-outcome territory. ✓
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3 steps each) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §10 input sanitization: lives in `evaluate_variant.py` (per design guide), not in this spec ✓
- §11 Goodhart-resistance verification (per-criterion v1 anchors + per-component v2 modes routed to structural_gate / sibling-fork) ✓
- §13 specimen criterion template followed ✓

Length per criterion ≈ 230 words on the three-vertical-example criteria (SE-A, SE-B, SE-D) and ≈ 170 words on the single-example criteria (SE-C, SE-E); longer than the design guide's 150-word target on the vertical-anchor criteria due to 3 examples per, absorbable per CI v3.3 precedent. **Total v3 spec body ≈ 7,100 words after Option D surgical extraction of ~4,400 words of lane-roadmap content (Phase-1/2/3 deliverable enumeration, 14-cuts + 15-adds detail catalog, sibling-fork operational triggers, multi-deliverable evolution-loop architecture, cross-lane consistency design, retainer-shape revenue model commentary) to `docs/handoffs/2026-05-19-site-engine-roadmap.md`.** v3 retains §1 broadened readers (10-category mix), §1.5a Component A judge-artifact lock, §1.5b capability framing + Substrate-Readiness Gate, §1.5c shape-enforcement split (8 verifiables routing), §2c 10-vertical exemplars, §3a/b brief inline modern-lever bias references, §3c-d Component A failure modes, §3e SITE-specific AI-failure surfaces routed to structural_gate, §6b per-component Goodhart modes, §8 open questions + reordered sibling-fork priority pointer. Criterion prose at the judge layer is unchanged from v1.

---

## 8. Open questions, sibling-fork triggers, retirement migration (after v1 + v2 restructure + v3 surgical edits)

Reader / Artifact-shape / Success / Failure / 5 Criteria are LOCKED at v1 (criterion-prose unchanged in v2 and v3). Lane scope broadened in v2; v3 extracted lane-roadmap content to parallel doc and reordered sibling-fork priority. Remaining open questions:

### 8a. Judge-layer open questions (carried over from v1; status updated)

1. **Redundancy check pending (urgent).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 5 criteria × 3 panel models = ~75 calls (~$30). Drop any criterion correlating > 0.7 with another. Expected live floor 3–4. Most-likely-to-merge pairs: SE-A ↔ SE-D (both test human reader fit — a page that fails persona commitment typically also fails to convert); SE-B ↔ SE-E (both test AI-engine signals — passage citability and entity stability may correlate). If both pairs merge, live floor is 3 (SE-A+D human, SE-B+E AI-engine, SE-C proposition specificity). The ≤5 ceiling is preserved either way; don't fight an absorption when it happens.

2. **Fixture validation.** Run 5 existing site_engine fixtures (gofreddy.ai canonical + DWF + Klinika Melitus + 1 b2b-tech beyond gofreddy + 1 e-commerce or DTC if available) through the locked criteria; eyeball judge rationales. If the rationales don't match human reasoning about quality, the prose is wrong, not the design. Surface findings before propagating.

3. **`structural_gate` expansion — DEFERRED (spec first, code later).** Same pattern as CI v3.4. Eight verifiables listed in §3e + §1.5c (schema validity, Lighthouse, axe-core, brand-token, alt-text, broken-link, mobile responsive, robots.txt) + additional checks for Phases 2-3 deliverables (URL HEAD resolution on customer-story / comparison-page external references, quote-grep on customer quotes, entity-existence lookup, schema-vs-body cross-validation, llms.txt-entry resolution, CRO test sample-size + significance validation, comparison-page "at least one row favors competitor" check). Implementation deferred to plan-002 next iteration alongside U15b (rubric template wiring). The existing v006 checks (3+ headings, 2+ citations, ≤2000 words, banned-phrases) stay.

4. **Legacy `docs/rubrics/site-quality.md` retirement — deprecation-header-in-place only (UNCHANGED from v1).** Per JR posture: add a deprecation header in place pointing to this spec; DO NOT move the file yet. Moving the file breaks ~20 cross-references in `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` plus 7 other doc files (see #5 below). The file stays at `docs/rubrics/site-quality.md` with a frontmatter banner explicitly marking it superseded by this spec; historical scored variants whose `rubric_version: site-quality-v1` field references the legacy rubric stay attributable (per legacy revision policy line 330–333 and design guide §15 per-version calibration). No re-scoring of historical fixtures.

5. **Cross-reference cleanup of 8 doc files — DEFERRED to plan-002 next iteration (UNCHANGED from v1).** Documentation files mentioning `site-quality.md` or `SE-[1-8]` that need updating once the new spec is locked:

   | File | Reference count | Action |
   |------|----------------|--------|
   | `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` | ~20 | Heaviest cleanup — TD-30, R29-R34, D26, D27, U15b, S2. Bundle into single plan-002 patch commit. |
   | `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` | self | THIS FILE — promoted to source-of-truth at v2; status updated. |
   | `docs/research/2026-05-18-judges-domain-site-engine.md` | 1 | Add "implemented in [link]" footer reference to this spec. |
   | `docs/handoffs/2026-05-18-judge-design-next-session-brief.md` | 1 | Update reference. |
   | `docs/handoffs/2026-05-15-judge-design-next-session-brief.md` | 1+ | Update reference. |
   | `docs/handoffs/2026-05-18-judge-design-7-lanes-research-dispatch.md` | 1+ | Update reference. |
   | `docs/research/2026-05-18-geo-dual-audience-tension.md` | 1 | Update reference. |
   | `docs/rubrics/site-quality.md` itself | self | Deprecation-header-in-place (no move). |

   All 8 deferred to plan-002 next iteration to avoid blocking the judge-design propagation work. No source code consumes the legacy rubric yet (U15b hasn't shipped); the migration is documentation-side only at this stage.

6. **Vertical fixture coverage (BROADENED v2).** Currently have b2b-tech (gofreddy.ai canonical) + b2b-regulated-services (DWF) + b2c-aesthetics-healthcare (Klinika Melitus) coverage in fixtures. v2 broadens the substitute-reader set to 10 categories. Need to add: 1+ e-commerce / DTC fixture (to validate SE-A Example C and SE-B Example C vertical-divergence), 1+ B2B SaaS fixture beyond gofreddy.ai itself (Anthropic or Perplexity reasonable seeds), 1+ marketplace fixture, 1+ B2C-app fixture, 1+ dev-tool / API platform fixture, 1+ fintech fixture, 1+ AI lab fixture (Anthropic / OpenAI / Mistral), 1+ agency fixture (Animalz / First Round / Wynter). Phase 1 priority: B2B SaaS + AI lab + fintech (highest expected client overlap); marketplace + dev-tool + B2C-app deferred to future scope.

7. **First-cohort overfitting watch (BROADENED v2).** v1 broadened §1 Reader substitute-readers and added §1.5 Empirical-validation-scope note to reduce DWF / Klinika / gofreddy-only anchoring; v2 broadens further to 10 categories across §1 and §2c. The underlying research (vertical-conventions, dual-audience-tension, comprehensive-scope §4 vertical adjustments) was done against b2b-tech / b2b-regulated-services / b2c-aesthetics-healthcare verticals with comprehensive-scope adding broader vertical coverage. Monitor: when client #5+ onboards (any vertical outside the first-cohort triple), check whether the spec's substitute-readers + §1.5 form factor + SE-A / SE-B / SE-D vertical anchors generalize OR whether per-vertical adjustment is needed. Re-validation trigger: any fixture from a vertical not in the 10-category list above should prompt a quick re-validation pass on SE-A / SE-B / SE-D anchors.

8. **Overlap with GEO lane (UNCHANGED from v1).** GEO is narrow (one landing page optimized purely for AI citation in a specific category-query context); site_engine is broader (full landing-page surface, dual audience with co-equal human-AI reader weighting). Proposed boundary: GEO judge focuses on a single page's citation-readiness in narrow AI-citation context; site_engine judge weighs both citation + human conversion + multi-section consistency on the same artifact. Confirm boundary holds when fixtures run through both judges and scores compare cleanly (no double-counting, no fragmentation of the same outcome). The dual-audience-tension research's OQ3 flags this; resolution deferred to first-fixture-pass.

9. **Voice-persona reassignment (UNCHANGED from v1).** Legacy SE-4 (voice persona fit) reassigned to shared `voice_persona` infrastructure (article_engine, ad_engine, image_engine, linkedin_engine, x_engine all consume the same `ClientConfig.voice_persona`). Open whether site_engine should retain a `structural_gate`-level corpus-distance check (per legacy SE-4 falsifiability) for cases where landing-page copy has voice-fit signals other lanes don't surface as cleanly ("Powered by AI" boilerplate on a manifestly anti-AI-slop brand). Defer to first fixture pass; the shared voice-persona framework handles the cross-lane work, the structural_gate retention is a narrow site_engine-specific decision.

10. **Propagation to other 6 lanes (UNCHANGED from v1).** Once site_engine v2 validates on real fixtures, this brings 2-of-8 lanes to design-locked spec (CI v3.4, site_engine v2). Remaining 6: GEO, MON, MA, SB, X, LI. Each gets its own optimal-output-spec pass + per-lane deep-research dispatches as needed — NOT a mechanical site_engine-shaped repeat. The site_engine dual-audience structure is specific to landing-page surfaces and does not transfer to monitoring digests, ad creatives, or social posts; per-lane domain research scopes the criteria.

11. **Anti-slop calibration data lifecycle (UNCHANGED from v1).** The legacy SE-8 anti-slop feature-checklist (lime-purple palette, three-icon trio, "We help you" pattern, six bordered cards, gradient mesh) remains useful as workflow-side meta-agent training material ("do not produce content matching `docs/rubrics/site-quality.md` §SE-8") without being judge-side scoring criteria. Clean separation: workflow-side anti-pattern awareness ≠ judge-side feature-checking. Confirm the workflow-side incorporation doesn't drift back into judge prose. The deprecation-header-in-place pattern (open question 4) preserves the legacy SE-8 catalog for workflow-side consumption without re-routing it to the judge.

### 8b. Sibling-fork triggers — priority reordered v3; full triggers in roadmap doc

The lane-scope broadening (3-phase staged comprehensive site program) is **incremental sibling-fork-ready, not multi-artifact-judge-in-one-lane.** Per research §6 recommendation (Option A: sibling-fork), the site_engine lane continues to iterate on Component A (landing-page artifact); sibling lanes handle other deliverables when demand crosses sibling-fork triggers. This preserves the design-guide ≤5 criterion ceiling per lane and the AND-conjunction discipline on Component A.

**Priority reorder (v3, per 2026-05-19 spot-check first-cohort vertical-mix analysis):**

1. **`site_audit_engine` — HIGHEST PRIORITY (reordered from §8b deferred → v3 elevated).** Site audit generalizes across all 10 verticals and across all 3 active first-cohort clients (Klinika healthcare + DWF regulated-legal + gofreddy b2b-tech). **Trigger: fork `site_audit_engine` when audit-as-deliverable demand crosses ≥3 clients OR ≥15% of agency-side site_engine revenue, fork.**
2. **`comparison_engine` — SECOND PRIORITY (reordered from v2 HIGHEST → v3 second).** Comparison-page warfare is the single highest-leverage 2026 AEO surface for unregulated-vertical contexts; fits poorly for Klinika (regulated medical advertising) and DWF (regulated legal marketing) — 2 of 3 active first-cohort. **Trigger: fork `comparison_engine` when comparison-page demand crosses ≥3 clients in unregulated-vertical contexts (B2B SaaS / AI lab / agency / dev-tool) OR ≥15% of agency-side site_engine revenue, fork.**
3. **`cro_test_program` — THIRD PRIORITY.** Defer until at least one Phase-3 retainer is running CRO at sustained cadence.
4. **`site_landing_variants` — FOURTH PRIORITY.** Defer until at least one client requires per-ICP / per-channel variant cadence beyond the Phase-1 2-3 variants.

**Full sibling-fork operational triggers + multi-deliverable evolution-loop architecture (EL1/EL3/EL4) + cross-lane consistency enforcement (`ClientConfig.entity_anchor` proposed infrastructure) + retainer-shape revenue model commentary extracted to `docs/handoffs/2026-05-19-site-engine-roadmap.md` §4-§7.** That content is plan-002 input material, not judge-design content per the 2026-05-19 spot-check finding.

**Other sibling-fork candidates from research §8 OQ1 — DEFERRED beyond first-cohort:** `customer_story_engine` (foundational trust signal; may absorb into site_engine for now), `aeo_audit_engine` (may fold into GEO lane), `founder_visibility_engine` (research §8 OQ6 recommends cross-cutting infrastructure: one `FounderProfile` per client; consumed by site_engine + linkedin_engine + x_engine + article_engine), `entity_grounding` Knowledge-Panel-Wikipedia-Wikidata lane (research §8 OQ11 recommends fold into GEO or own lane).

---

**End of v3.** Component A (Phase-1 home + 2-3 primary landing pages) is judge-tested by SE-A..SE-E with criterion prose unchanged from v1; Phases 2-3 deliverables are `structural_gate` + program-outcome territory; sibling-fork triggers documented with v3-reordered priority (site_audit_engine HIGHEST, comparison_engine SECOND); ≤5 criterion ceiling preserved with no documented exception; modern-lever bias applied throughout §3 cuts/adds (full detail in roadmap doc) and §2c exemplars across 10 verticals; first-cohort overfitting watch broadened with 10-category vertical mix + explicit posture clause; legacy site-quality.md retirement timing dependent on lane shipping; Substrate-Readiness Gate clause acknowledges U15b lane scaffolding unshipped. ~4,400 words of roadmap content extracted to `docs/handoffs/2026-05-19-site-engine-roadmap.md` per spot-check audit.
