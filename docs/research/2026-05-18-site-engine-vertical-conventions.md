---
date: 2026-05-18
type: research deliverable
status: complete
topic: site_engine vertical-specific conventions (landing-page architecture across categories)
parent: docs/handoffs/2026-05-18-judge-design-step1-site-engine.md
siblings:
  - docs/research/2026-05-18-judges-domain-site-engine.md
  - docs/research/2026-05-18-ci-vertical-conventions.md
  - docs/research/2026-05-18-monitoring-vertical-conventions.md
---

# Site Engine — Vertical Conventions in Landing-Page Architecture
## How locked architecture, CTA framing, and "great vs slop" diverge across B2B SaaS / e-commerce / professional services / marketplace / API-dev-tool / B2C app / fintech — and what the site_engine judge must anchor across to avoid first-cohort overfit

**Companion to:** `2026-05-18-judges-domain-site-engine.md` (the generalist CXL/Dunford/Balfour/AEO synthesis that produced SE-1..SE-5). This pass goes vertical-specific so the site_engine judge does not silently optimize for a single category archetype — currently the spec leans on B2B SaaS exemplars (Linear, Stripe, Anthropic) and a single services exemplar (DWF). A 50-generation evolution loop against that anchor set will produce B2B-SaaS-shaped pages across every fixture, regardless of whether the fixture is a law firm, a fintech, an e-commerce brand, or a healthcare practice.

**Why this exists.** A landing page that earns 5/5 on SE-1 (human CTA) against a Linear or Stripe fixture could earn 1/5 against an Allbirds fixture for reasons that are *category conventions*, not quality. The "declarative hero + single CTA + named-customer-quote" template that wins on B2B SaaS is wrong-genre on e-commerce (where the hero IS the product photo + price + add-to-cart) and wrong-register on professional services (where the hero is a track record + named partners + signal of gravitas). If the rubric doesn't see that, the judge will reward category-mismatch faithfulness and punish category-appropriate excellence.

---

## 1. TL;DR (350 words)

### Top vertical-specific findings (one per category)

**B2B SaaS (Linear, Vercel, Stripe, Notion, Anthropic, Cursor):** Locked architecture is hero → social-proof logo strip → feature triptych → use-case slabs → integrations grid → pricing table → final CTA. Dominant CTA framing is "Start free" (PLG) or "Get a demo" (sales-led); both visible. Anti-pattern: query-echo hero ("What is X?").

**E-commerce / DTC (Allbirds, Warby Parker, Glossier, Patagonia):** Locked architecture is hero-image-with-price → category navigation → trending products grid → trust-signal strip (free shipping, returns, sustainability) → press-quote row → email-capture. Dominant CTA framing is "Shop" or "Add to bag" — never "Get a demo." Anti-pattern: hero copy that explains the product instead of showing it.

**Professional services — legal/consulting/accounting (DWF, Pinsent Masons, McKinsey, Slaughter & May, EY):** Locked architecture is hero-with-gravitas-statement → practice-area grid → named-partner-with-credentials grid → recent-matters/case-studies → insights/thought-leadership feed → office-locations footer. Dominant CTA framing is "Contact us" or "Speak to a partner" — never "Start free." Anti-pattern: SaaS-style PLG CTA, conversational hero copy ("Hey! We're DWF"), pricing tables.

**Marketplace (Airbnb, Etsy, DoorDash, Uber):** Locked architecture is dual-search-bar hero → category tiles → demand-side-quality-signal row → supply-side recruit-CTA (host/seller). Dominant CTA framing is split — "Find/Book" for demand; "Become a host" / "Start selling" for supply. Anti-pattern: single-CTA hero (collapses the two-sided structure).

**API / developer-tool (Anthropic Console, OpenAI Platform, Stripe Docs, Twilio, Vercel, Cloudflare):** Locked architecture is declarative-hero-with-code-block → install/quickstart-with-curl → SDK-language-tabs → docs-and-API-reference → integrations → pricing-per-unit. Dominant CTA framing is "Read the docs" + "Get API key" — often equal visual weight. Anti-pattern: marketing-copy hero with no code visible above fold.

**B2C app — wellness, fitness, finance-consumer (Calm, Headspace, Strava, Robinhood, Cash App):** Locked architecture is emotion-led hero (warm photography or video) → outcome-promise → app-store CTAs (Apple + Google badges) → social-proof rating ("4.8 stars, 600K reviews") → feature scroll → press-mentions. Dominant CTA framing is "Download" / "Get the app" — store badges as primary. Anti-pattern: enterprise-style "Book demo" CTA.

**Fintech (Stripe, Mercury, Ramp, Wise, Brex):** Locked architecture is hybrid SaaS-with-product-screenshot → social-proof-of-trust (regulatory badges, "$X processed", named-customer-with-context) → feature-slab → security/compliance signal-row → developer-credibility section → pricing transparency. Dominant CTA framing is "Open account" / "Sign up" with secondary "Talk to sales." Anti-pattern: missing security/compliance signal-row (instant credibility kill).

### Strongest single recommendation for the site_engine spec

**Add a "category-context probe" to the judge-prompt wrapper** asking the judge to first identify the page's apparent category from the artifact, then apply category-appropriate expectations. SE-1, SE-2, and SE-4 score-1 anchors need three vertical-divergent example pairs (B2B SaaS / professional services / e-commerce or DTC) — not three flavors of the same B2B SaaS exemplar. Without this, the loop converges on Linear's hero pattern.

---

## 2. Vertical A — B2B SaaS (Linear, Vercel, Stripe-as-SaaS, Notion, Anthropic, Cursor)

### 2.1 Locked architecture

The B2B SaaS landing-page architecture has been the most studied of any category in 2020–2026. CXL teardowns, Pencil Pages, Marketing Examples, Wynter, and Animalz converge on essentially the same eight-section structure:

1. **Hero** — declarative one-line value proposition, ONE primary CTA (usually visually dominant), product surface visible (screenshot, mock, or interactive demo). Linear (`https://linear.app`) is the canonical example: "Linear is a purpose-built tool for planning and building products" + single "Start building" CTA + product UI screenshot.
2. **Social-proof logo strip** — 6–8 customer logos immediately under hero, often with a "Trusted by" or "Built with Linear" header. Vercel, Notion, and Stripe all use this slot identically.
3. **Feature triptych** — three icon-led feature blocks arguing the product's main capabilities. The format is so canonical that AI-slop generators produce nothing else.
4. **Use-case slabs** — alternating left/right layout, each showing one user scenario with a screenshot. Linear's "Issue tracking," "Sprints," "Roadmaps" slabs are the prototype.
5. **Integrations grid** — partner logos arranged in a tight grid, "Works with the tools you already use."
6. **Customer quote / case study slab** — one named customer, with role, headshot, dated quote, and outcome metric.
7. **Pricing table** — three tiers (Free/Pro/Enterprise), monthly toggle, feature comparison. Sometimes deferred to a separate `/pricing` page but always one click away.
8. **Final CTA + footer** — large CTA block ("Ready to ship faster?") + comprehensive footer with docs, careers, security, status.

### 2.2 Dominant CTA framing

**PLG-mode (product-led growth):** "Start free" / "Get started" / "Try it free" — the visitor self-serves into a free tier and converts on usage. Linear, Vercel, Notion, Cursor all default here. Secondary CTA: "Talk to sales" or "Contact us" smaller and to the right.

**Sales-led-mode:** "Get a demo" / "Book a demo" / "Request a demo" — the visitor enters a sales motion. Used by enterprise-tier products where ACV >$50K. Stripe Atlas, Anthropic Enterprise, some Notion Enterprise pages.

**Hybrid:** Both CTAs visible. Stripe homepage shows "Start now" (PLG-shape) + "Contact sales" simultaneously. Mercury, Ramp use this pattern.

Conversion-design dogma (Wynter, CXL): one CTA should be visually dominant; the second is acceptable but must be subordinate (smaller, lighter weight, secondary color). Equal-weight CTAs are an anti-pattern — the visitor stalls between paths.

### 2.3 What "great" looks like

The published-and-praised B2B SaaS landing pages converge on a specific quality bar:

- **Linear** (`https://linear.app`): canonical declarative hero, product visible, named customers (Ramp, Loom, Vercel) in proof strip, single PLG CTA. Marketing Examples and Pencil Pages cite as the modern gold standard.
- **Vercel** (`https://vercel.com`): passage-self-containment + technical clarity. Hero is "Build and deploy on the AI cloud" — declarative; mid-page passages read like docs ("Frontend Cloud," "AI cloud," "Backend Cloud" with concrete capabilities).
- **Stripe** (`https://stripe.com`): evidence-injection champion. Hero includes "millions of businesses use Stripe" with case study links to Atlassian, Shopify, Lyft — every claim sourced.
- **Anthropic** (`https://anthropic.com`): persona separation — "For developers" and "For enterprises" surface as distinct pages, neither averages across the other.
- **Cursor** (`https://cursor.com`): concrete differentiator ("The AI Code Editor"), product video above fold, named adopters.
- **Notion** (`https://notion.so`): intent-format match — product pages have different formats from pricing pages from template gallery from blog.

### 2.4 Failure modes specific to B2B SaaS

- **AI-slop template.** Lime-purple gradient mesh hero, three-icon trio, "AI-powered platform for modern teams," six identical bordered cards, stock-testimonial-grid with circular placeholder avatars. Pencil Pages, Marketing Examples, and Refrens teardowns all flag this as the dead giveaway.
- **Query-echo hero.** "What is [Product]?" as the H1. Aggarwal GEO finding: query-echo passages cited 60% less than declarative ones. SaaS-specific: query-echo signals the writer doesn't know how to introduce the product.
- **Feature dump masquerading as use cases.** Use-case slabs that just describe features in different words. The diagnostic from Animalz: a real use case names *who* the user is, *what they were trying to do*, and *what changed*.
- **Logo-walled social proof.** Six logos with no quote, no link, no context. Reads as cargo-cult social proof.

---

## 3. Vertical B — E-commerce / DTC (Allbirds, Warby Parker, Glossier, Patagonia)

### 3.1 Locked architecture

E-commerce landing pages share NONE of the B2B SaaS structure. The product IS the landing page. The architecture converges on:

1. **Hero-with-product** — full-bleed hero image (lifestyle or product) with a single product-detail CTA, OR a featured-product carousel with price visible. Allbirds (`https://allbirds.com`) leads with seasonal hero image + "Shop Wool Runners" CTA.
2. **Category navigation strip** — Shoes/Apparel/Accessories or category-tiles immediately under hero.
3. **Trending products grid** — 4–8 product cards, each with image, name, price, rating stars, quick-add-to-bag.
4. **Trust-signal strip** — free shipping over $X, free returns, sustainability commitments (Allbirds: "Our impact"), warranty.
5. **Press-quote row** — small attributed pull-quotes from Vogue, NYT, The Cut, Wired.
6. **Email-capture** — newsletter signup at the bottom, often with discount-on-signup incentive ("10% off first order").

Warby Parker (`https://warbyparker.com`) adds a vertical-specific step: virtual try-on tile. Glossier (`https://glossier.com`) adds user-generated-content grid mid-page. Patagonia (`https://patagonia.com`) replaces the trust-strip with an environmental-activism slab — the brand is the trust signal.

### 3.2 Dominant CTA framing

The CTA vocabulary is completely different from B2B SaaS:

- **"Shop [category]"** — leads to a category page (Allbirds: "Shop Wool Runners")
- **"Add to bag"** — direct purchase intent on product tiles
- **"Buy now"** — for single-product DTCs (Casper, Bombas)
- **"Find your fit"** — for sized-product DTCs (Warby Parker, Allbirds)
- **"Get the look"** — for fashion DTCs

Never: "Get a demo," "Start free," "Talk to sales." These would be category-malformed.

### 3.3 What "great" looks like

- **Allbirds** (`https://allbirds.com`): sustainability is the differentiator; hero often features a single hero product with material origin story link.
- **Warby Parker** (`https://warbyparker.com`): virtual-try-on integration + home-try-on box program both surfaced in hero.
- **Glossier** (`https://glossier.com`): UGC-as-social-proof, customer photos integrated into product grids.
- **Patagonia** (`https://patagonia.com`): brand-narrative-as-conversion. Activist commitments above commercial CTAs.
- **Aesop** (`https://aesop.com`): editorial restraint. Product photography against minimal copy. No price-bombs.

### 3.4 Failure modes specific to e-commerce

- **Hero copy that explains the product instead of showing it.** "Sustainable footwear made from natural materials" as H1 with a small thumbnail. The product photo IS the hero — copy gets in the way.
- **B2B-SaaS templating ported to DTC.** Three-icon trio + feature-bullet copy on a shoe brand. Wrong genre, instant credibility kill.
- **Price hidden.** E-commerce buyers expect price in hero or one-click away. "Contact us for pricing" on a consumer product is a category violation.
- **Cart-friction theater.** Forcing email/account creation before showing cart. Baymard Institute data: 21% cart abandonment is due to forced account creation.
- **Trust-signal absence.** No free-shipping/returns strip on a DTC page. Cart abandonment doubles when returns policy isn't visible.

---

## 4. Vertical C — Professional services (DWF, Pinsent Masons, McKinsey, Slaughter & May, EY, KPMG)

### 4.1 Locked architecture

Professional services landing pages are structurally distinct from both B2B SaaS and e-commerce. The "product" is the firm's people and track record. Architecture:

1. **Hero with gravitas statement** — typically a value statement, sometimes a brief "what we do" + named differentiator. Slaughter & May (`https://slaughterandmay.com`) opens with "We are a leading international law firm." McKinsey (`https://mckinsey.com`) opens with rotating insights stories.
2. **Practice-area / service-line grid** — for law firms, this is the practice groups (Corporate, Litigation, Tax, Employment). For consulting, the industries and capabilities. The grid is often the primary navigation surface.
3. **Named-partner / leadership grid** — partners with photos, credentials, and short bios. DWF, Pinsent Masons, Slaughter & May all carry partner-prominent pages. The partners ARE the brand.
4. **Recent matters / case studies** — named matters where confidentiality allows, anonymized otherwise. "Advised [Client] on [Transaction]" patterns.
5. **Insights / thought-leadership feed** — recent articles, briefings, podcast episodes. The signal of intellectual capital.
6. **Office locations footer** — global office grid, often the longest tail-navigation surface.

### 4.2 Dominant CTA framing

The vocabulary is contact-heavy and gravitas-laden:

- **"Contact us"** — generic but dominant
- **"Speak to a partner"** — premium-firm framing
- **"Get in touch"** — UK-firm convention
- **"Request a consultation"** — consulting-firm convention
- **"Find a lawyer"** — large-firm directory pattern

Never: "Start free," "Get a demo," "Add to bag," "Download the app." Category-malformed.

McKinsey, Bain, BCG don't carry a single primary CTA — the page leads with thought-leadership, and contact is buried in footer/header navigation. The CTA model is *attract via authority, not capture via CTA*.

### 4.3 What "great" looks like

- **Slaughter & May** (`https://slaughterandmay.com`): editorial restraint, no marketing froth, partner-led credibility. The hero is a statement, not a pitch.
- **Skadden Arps** (`https://skadden.com`): matter-led landing pages — recent deal-of-the-year work prominently featured.
- **McKinsey** (`https://mckinsey.com`): rotating insights hero + topic-led navigation. Conversion isn't the goal; thought-leadership consumption is.
- **Pinsent Masons** (`https://pinsentmasons.com`): sector-led structure ("Energy," "Financial Services," etc.) — buyers self-segment by industry.
- **EY** (`https://ey.com`): combines services × industries × insights navigation — orchestrated for enterprise buyers who already know what they need.

### 4.4 Failure modes specific to professional services

- **SaaS-style PLG CTA on a law firm.** "Start free trial" on a Magic Circle firm's website is category malpractice. Yet AI-slop generators trained on B2B SaaS templates produce this regularly when given a "law firm landing page" prompt.
- **Conversational hero copy.** "Hey! We're DWF and we love what we do." Wrong register — destroys gravitas instantly. Professional services readers (GCs, finance directors, board members) expect formal voice.
- **Pricing tables.** Law firms, consulting firms, accounting firms don't publish pricing. A pricing table on a Slaughter & May-tier page is a category violation; on a mid-market firm it's a positioning signal of "we compete on price."
- **Stock photography of "diverse team in modern office."** Generic and brand-destroying. Professional services brands invest in custom partner photography; stock signals "we don't have real partners to show."
- **Missing partner names.** A law-firm landing page that doesn't surface named partners has hidden the actual product. The named partners are why clients hire the firm.
- **Generic "thought leadership."** "Our latest insights" with three undated, unauthored blog posts. The thought-leadership shelf is theater unless authored by named partners with publication dates.

### 4.5 The DWF-specific anchor

DWF (~90 lawyers, Polish RES practice, mid-market UK/Polish) is the gofreddy first-cohort professional-services fixture. The Pinsent Masons 6-partner pull from CMS/Dentons/DLA/GT (May 2026) showed what competitive-pressure looks like in this category. A DWF landing page that wins on SE-1..SE-5 looks like:

- Hero: practice-area statement + named senior partner (Maciej Jamka) + Polish-EN-DE jurisdictional badge
- Below fold: recent matters in RES with anonymized client identifiers
- Partner grid: photos, dates of practice, named specialisms
- Insights: dated articles by named partners on Polish regulatory shifts
- Contact: office-by-office (Warsaw / Manchester / London), partner-level contact

A page that wins on SE-1..SE-5 against a Linear-style B2B SaaS scoring lens against this fixture would still be category-wrong. The judge needs to apply the professional-services convention set, not the SaaS one.

---

## 5. Vertical D — Marketplace (Airbnb, Etsy, DoorDash, Uber)

### 5.1 Locked architecture

Marketplaces have the most distinctive landing-page architecture of any category — two-sided by structural necessity. Both the demand-side and supply-side audiences must be served on the same surface:

1. **Search-bar hero (demand-side primary)** — Airbnb (`https://airbnb.com`) opens with a destination + dates + guests search field. The hero IS the search. Etsy, DoorDash, Uber follow this pattern.
2. **Category tiles** — popular destinations / shop categories / cuisines / ride-types.
3. **Demand-side-quality-signal row** — "Over X million stays / 4.8 stars / 2M+ products" — scale and quality.
4. **Supply-side recruit slab** — a separate panel inviting hosts/sellers/drivers. Airbnb: "Become a host." Etsy: "Sell on Etsy."
5. **Editorial collections** — curated lists, trending searches, seasonal pushes.
6. **Trust signals** — guarantees, insurance, dispute resolution.

### 5.2 Dominant CTA framing

Marketplace pages ALWAYS carry two CTA tracks:

- **Demand-side primary:** "Find/Book/Order/Get a ride" — search-form-based, the visible default
- **Supply-side secondary:** "Become a host" / "Start selling" / "Drive with [Brand]" / "Become a Dasher" — usually in header nav + dedicated mid-page panel

Single-CTA marketplaces don't exist at scale. The supply-side recruitment IS competitive — Uber recruits drivers against Lyft; Airbnb recruits hosts against Vrbo; Etsy recruits sellers against Shopify — and the recruitment surface lives on the landing page.

### 5.3 What "great" looks like

- **Airbnb** (`https://airbnb.com`): search-as-hero + visual-rich category tiles + clear "Become a host" pathway.
- **Etsy** (`https://etsy.com`): search + curated collections + "Sell on Etsy" — the sellers ARE the supply story.
- **DoorDash** (`https://doordash.com`): cuisine-led category tiles, restaurant-recruitment surface separately.
- **Uber** (`https://uber.com`): rider-driver split is the entire homepage architecture; each gets equal visual weight.

### 5.4 Failure modes specific to marketplaces

- **Single-CTA hero on a two-sided marketplace.** Collapses the structural reality. The supply side disappears.
- **No search bar.** A marketplace without search-as-hero is hiding its core surface.
- **Demand-side feature dump.** Marketplaces don't have "features" in the SaaS sense — they have inventory and trust. Listing "10X faster" or "AI-powered matching" is category-malformed.
- **Quality signals via product features.** "Verified hosts" matters; "machine-learning recommendations" doesn't. The signal must be about the marketplace's content, not its tech.

---

## 6. Vertical E — API / developer tools (Anthropic Console, OpenAI Platform, Twilio, Stripe Docs)

### 6.1 Locked architecture

API/dev-tool landing pages serve developers as primary readers. Architecture diverges from generalist B2B SaaS:

1. **Declarative hero with code block** — Twilio (`https://twilio.com`), Stripe (`https://stripe.com`), Anthropic API docs all open with a code snippet visible above fold. The code IS the proof.
2. **Install / quickstart with curl** — copy-paste-able commands that work in 60 seconds.
3. **SDK-language tabs** — Python / JS / Ruby / Go / Java / cURL toggles on the code samples.
4. **API reference link** — primary CTA to docs alongside or above primary CTA to signup.
5. **Integration / partner section** — frameworks supported, language coverage.
6. **Pricing-per-unit** — per-call, per-token, per-message pricing rather than monthly tiers. Transparent and granular.

### 6.2 Dominant CTA framing

- **Primary:** "Read the docs" — equal or greater weight to the signup CTA. This is the dev-tool category signature.
- **Secondary:** "Get API key" / "Start free" / "Sign up" — the signup CTA exists but is not the only path.
- **Tertiary:** "View on GitHub" — for open-source-adjacent tools.

The "read the docs" CTA is the load-bearing dev-tool signature. A developer-targeted page where docs are buried fails the category test.

### 6.3 What "great" looks like

- **Stripe** (`https://stripe.com`): code block in hero + comprehensive docs + named-developer testimonials.
- **Twilio** (`https://twilio.com`): per-product code samples, multi-language SDK coverage.
- **Anthropic** (`https://anthropic.com/api`): code-first hero, persona-aware (developer vs enterprise surfaces).
- **OpenAI Platform** (`https://platform.openai.com`): playground-as-landing — try-it-yourself integrated.
- **Cloudflare** (`https://cloudflare.com`): wide product surface with per-product code examples and developer-tier free signup.

### 6.4 Failure modes specific to dev tools

- **Marketing-copy hero with no code visible.** Developers infer "this is targeted at procurement, not me." Instant credibility kill.
- **Pricing tier opacity.** "Contact us for pricing" on a developer-facing API ends the evaluation immediately. Even enterprise APIs need a published-pricing teaser.
- **Hidden docs.** Docs link buried in footer. The category convention is docs-prominent.
- **No SDK language coverage signal.** Developers want to know "is my language supported" within 5 seconds.

---

## 7. Vertical F — B2C app (Calm, Headspace, Strava, Robinhood, Cash App)

### 7.1 Locked architecture

B2C app landing pages share the e-commerce DTC DNA but with mobile-app primary outcomes:

1. **Emotion-led hero** — warm photography or short video showing the outcome state (calm meditator, runner mid-stride, person checking finances in cafe).
2. **Outcome promise** — "Find your calm." "Run smarter." "Investing for everyone."
3. **App-store CTAs as primary** — Apple App Store badge + Google Play badge, often the dominant CTAs (web signup secondary or absent for app-first products).
4. **Social-proof rating** — "4.8 stars, 600K reviews." Often the most credible signal for B2C app downloads.
5. **Feature scroll** — phone mockups with feature highlights, vertically stacked or carousel.
6. **Press mentions** — "Featured in NYT / Wired / The Atlantic" — third-party media bylines.

### 7.2 Dominant CTA framing

- **Primary:** "Download" / "Get the app" + app-store badges (these often ARE the CTAs)
- **Secondary:** "Try free for 7 days" / "Start your trial" (for subscription apps)
- **Tertiary:** "Browse [content]" (for content-led apps like Calm, Headspace)

Never: "Get a demo," "Talk to sales," "Add to bag" (unless the app sells physical products). Category-malformed.

### 7.3 What "great" looks like

- **Calm** (`https://calm.com`): emotion-first hero, sound preview, app-store badges + web subscription CTA.
- **Headspace** (`https://headspace.com`): bright illustrated hero, single-message outcome promise, app badges prominent.
- **Strava** (`https://strava.com`): athlete-photography hero, route-map visuals, free-tier CTA + premium upsell.
- **Robinhood** (`https://robinhood.com`): clean financial product hero, no marketing fluff, app + web signup.
- **Cash App** (`https://cash.app`): culture-forward design, celebrity associations as social proof.

### 7.4 Failure modes specific to B2C apps

- **Enterprise-style CTAs.** "Schedule a demo" on a meditation app. Wrong genre.
- **Missing app-store badges.** App-first product without visible badges signals "we don't expect downloads" — confusing.
- **Dense feature copy.** B2C app buyers don't read; they look, decide, install. A 200-word feature paragraph buries the install action.
- **Missing rating proof.** Without a star rating + review count, the page misses the most credible social proof in the category.

---

## 8. Vertical G — Fintech (Stripe, Mercury, Ramp, Wise, Brex, Wealthfront)

### 8.1 Locked architecture

Fintech sits at the intersection of B2B SaaS and consumer financial services — and inherits unique trust-signal requirements:

1. **Hybrid SaaS hero** — declarative value prop + often a product screenshot (dashboard, transaction view, card image).
2. **Trust-of-scale signal** — "$X processed," "X businesses funded," "Y countries supported." Mercury, Stripe, Wise lead with these.
3. **Named-customer-with-context** — specific company + outcome. Ramp shows named customers + cost-savings outcomes.
4. **Feature slabs** — payments, expense management, banking, cards.
5. **Security / compliance signal row** — SOC 2, PCI DSS, FDIC insurance, regulatory licenses. This is fintech's load-bearing trust band.
6. **Developer-credibility section** (for embedded fintech) — API/docs link, sandbox access.
7. **Pricing transparency** — per-transaction, per-card, or monthly fees published. Hidden pricing is anti-pattern.

### 8.2 Dominant CTA framing

- **Primary:** "Open account" / "Sign up" / "Get started" — direct-conversion bias
- **Secondary:** "Talk to sales" — for enterprise fintech (Mercury Treasury, Brex Enterprise)
- **Tertiary:** "View docs" — for API-fintech (Stripe, Plaid)

The CTA expectation is "I can open an account today" — fintech consumers and SMBs are conditioned to instant signup. "Schedule a consultation" is wrong-shape unless the product is high-touch ($10K+ ACV).

### 8.3 What "great" looks like

- **Stripe** (`https://stripe.com`): evidence-injection champion, named-customers throughout, transparent per-call pricing.
- **Mercury** (`https://mercury.com`): startup-focused hero, named-customer-with-outcome (e.g., "Cocoon saved 40 hours/mo"), security badges visible.
- **Ramp** (`https://ramp.com`): cost-savings outcome leads ("Save 5% on average"), named customers, developer surface for embedded.
- **Wise** (`https://wise.com`): transparent FX-fee comparison vs incumbent banks, regulatory-trust signal-row.
- **Brex** (`https://brex.com`): persona separation (startups vs enterprise), card-image-as-hero, financial-product clarity.

### 8.4 Failure modes specific to fintech

- **Missing security/compliance signal row.** A fintech page without SOC 2 / PCI / FDIC / regulatory badges signals "we're not serious." Instant credibility kill.
- **Vague trust claims.** "Bank-grade security" without naming compliance frameworks. The specific certifications matter.
- **Hidden pricing.** Fintech buyers want to know the cost-per-transaction before signup. Opaque pricing is a positioning failure.
- **B2C tone on B2B fintech.** "Banking made fun" on a corporate-card product. Wrong register for CFOs.
- **Missing developer-credibility for embedded fintech.** A payments API without visible code / docs / SDK is unserious.

---

## 9. Cross-vertical synthesis (650 words)

### What's universal across all seven categories

Three patterns hold across B2B SaaS / e-commerce / professional services / marketplace / API-dev-tool / B2C app / fintech:

1. **One dominant action above the fold.** Every category converges on ONE visually dominant CTA, even when multiple paths exist. The dominance hierarchy is universal even though the CTA *vocabulary* differs wildly. Wynter / CXL data: competing equal-weight CTAs collapse total click-through across all categories.
2. **Category-appropriate trust signals.** B2B SaaS uses named-customer logos + quotes; e-commerce uses press mentions + ratings; professional services uses named partners + recent matters; marketplaces use scale numbers; dev tools use code + docs prominence; B2C apps use store ratings + downloads; fintech uses compliance badges + scale. The *form* of trust signal varies but its mandatory presence does not.
3. **Reader-question answered within ~10 seconds.** "What is this, who is it for, why should I care?" gets answered in some category-appropriate way in every successful landing page. The format varies — declarative copy (SaaS), product photo (e-commerce), partner gravitas (services), search bar (marketplace), code block (dev tool), app-store badges + outcome (B2C app), value prop + scale signal (fintech) — but the function is invariant.

### What's vertical-specific and load-bearing

Six dimensions vary structurally enough that single-spec rubrics will silently overfit:

1. **The hero's primary content.** Declarative copy (SaaS) vs product photo (e-commerce) vs gravitas statement (services) vs search bar (marketplace) vs code block (dev tool) vs lifestyle photo (B2C app) vs dashboard screenshot (fintech). The site_engine spec's current example anchor (Linear's declarative copy) is correct for one of seven categories.
2. **CTA vocabulary.** "Start free" / "Get demo" / "Shop now" / "Contact us" / "Open account" / "Download" / "Read docs" — each is category-locked. A "Start free trial" CTA on a Magic Circle law firm is category malpractice; a "Speak to a partner" CTA on Linear is the same.
3. **Pricing convention.** SaaS publishes tiers; e-commerce publishes per-product price; services publishes nothing; marketplaces publish commission shape; dev tools publish per-unit; B2C apps publish subscription or one-time; fintech publishes per-transaction or monthly. "Pricing transparent" means seven different things.
4. **Social-proof form.** Logo strips (SaaS) / press mentions + ratings (e-commerce) / named partners + matters (services) / scale numbers (marketplace) / GitHub stars + customer-developer quotes (dev tool) / app-store ratings (B2C app) / compliance + scale (fintech). The judge needs to recognize the genre to score the proof.
5. **Reader-decision time horizon.** SaaS = days-to-weeks (try, evaluate, decide). E-commerce = minutes (impulse + cart). Services = months (RFP, partner introduction, engagement). Marketplace = seconds (search, transact). Dev tools = minutes (try the API). B2C app = seconds-to-minutes (install + try). Fintech = days (compare, open account). The "10-second decision" in SE-1 is wrong-horizon for services (where the decision is "do I want to read more / book a call in 6 weeks") and for marketplace (where the decision is "do I want to search now").
6. **Goodhart-collapse target.** SaaS = AI-slop gradient mesh + three-icon trio. E-commerce = stock-photo lifestyle hero, opacity on price. Services = generic "trusted advisor" hero, missing partner names. Marketplace = single-CTA collapse. Dev tools = marketing-copy hero with no code. B2C app = enterprise-style CTAs. Fintech = missing security signal-row, vague trust claims. The site_engine spec's current Goodhart-resistance anchors only on SaaS-shape collapses.

### Single most important takeaway

The current site_engine v0 spec uses three exemplars (Linear, Stripe, Anthropic) — all B2B SaaS or B2B SaaS-adjacent. The proposed score-1 anchor examples on SE-1, SE-2, SE-3, SE-4, SE-5 are all SaaS-shape. A 50-generation evolution loop against this anchor set will produce SaaS-shape outputs across every fixture, including any future law-firm, e-commerce, marketplace, dev-tool, B2C-app, or fintech fixture. The fix is structurally analogous to the CI v2 fix in the companion CI-vertical-conventions deliverable: **three vertical-divergent score-1 anchor examples per criterion**, ideally pulling from at least three of the seven categories above (with a strong recommendation that SaaS + services + e-commerce or DTC be the three, since these span the dominant structural divergences).

---

## 10. Implications for site_engine v0 spec (450 words)

### Concrete recommendations

**1. Add per-vertical score-1 anchor examples to SE-1, SE-2, SE-4.** SE-3 (proposition specificity) and SE-5 (freshness/entity stability) appear vertical-invariant. SE-1, SE-2, SE-4 are vertical-sensitive. Recommendation: three anchors per criterion, drawn from structurally-divergent categories. Worked example for SE-1:

> Example A (do not optimize toward): Linear's hero — "Linear is the modern issue tracker for high-performing software teams" + named customers (Ramp, Loom, Vercel) + single "Get started" CTA + product surface visible. **B2B SaaS PLG shape.**
>
> Example B: Slaughter & May's homepage — practice-area-led navigation + named partners surfaced in leadership grid + recent-matters section with anonymized clients + "Get in touch" contact CTA in header. **Professional services gravitas shape.**
>
> Example C: Allbirds' homepage — full-bleed seasonal hero image + featured-product carousel with prices + "Shop Wool Runners" CTA + sustainability differentiator surfaced + free-shipping trust-strip. **E-commerce DTC shape.**

**2. Generalize SE-1's "10-second decision" anchor.** Current: "After ~10 seconds on the page, would the targeted human persona click the primary CTA — book demo, start trial, request audit." Replace with: "Within the time-budget appropriate to the page's apparent category (10 seconds for impulse-CTA categories like SaaS PLG, e-commerce, B2C apps; longer for high-consideration categories like professional services or enterprise fintech where the 'commitment' may be reading further or filing for later), would the targeted persona take the page's primary intended action — which may be click-CTA, scroll-to-engage, or file-as-reference?"

**3. Add a category-context probe to the judge-prompt wrapper.** Current wrapper says the judge sees a landing-page surface. Add: "First identify the page's apparent category (B2B SaaS / e-commerce / professional services / marketplace / API or developer tool / B2C app / fintech / other) from visible signals (CTA vocabulary, hero content, social-proof form, pricing convention, target reader register). Apply category-appropriate expectations when scoring. A 'Start free' CTA is correct for B2B SaaS PLG and wrong for professional services; a published pricing table is correct for SaaS and wrong for law firms. Score for category-appropriate excellence, not for any single category's template."

**4. Expand SE-2's "AI engine citation" thinking across categories.** Currently anchored on B2B SaaS exemplars (Stripe-style "used by millions of businesses"). The AI-engine-citation logic is similar across categories but the *citable passage form* differs: SaaS = declarative entity + customer + outcome. Services = named partner + named matter + dated outcome. E-commerce = named product + verified review + dated claim. Marketplace = named place/host + scale number. Dev tool = code block + named integration. B2C app = outcome promise + named feature + dated rating. Fintech = scale claim + compliance frame + named customer.

**5. Add vertical-specific Goodhart-collapse modes to §6.** Currently the verification section anchors on templated B2B SaaS slop (gradient-mesh hero, three-icon trio, "X for Y because Z" hero). Add:
- **Services-template-on-SaaS** (overly formal hero on a PLG product — wrong-warm-direction)
- **SaaS-template-on-services** (PLG CTA on a law firm — wrong-warmth-direction)
- **B2B-template-on-e-commerce** (icon-trio + feature-copy on a shoe brand — wrong-genre)
- **Single-CTA-on-marketplace** (collapsing the two-sided structure)
- **Missing-trust-band-on-fintech** (no compliance signals)
- **Marketing-hero-on-dev-tool** (no code above fold)
- **Enterprise-CTA-on-B2C-app** ("Schedule demo" on meditation app)

**6. Defer fixture validation until after vertical-anchor expansion.** Don't bifurcate the criteria yet. The site_engine fixture cohort currently includes gofreddy.ai itself + DWF (services) + Klinika Melitus (healthcare). Run those three through SE-1..SE-5 with the three vertical anchor examples above. If the judge produces category-discriminating rationales (recognizing that DWF should be services-shape, not SaaS-shape), single-spec + diverse-anchors is sufficient. If it produces single-vertical-skewed rationales, escalate to per-vertical sub-specs.

---

## 11. Open questions

1. **Healthcare-practice category — does it merit its own row?** Klinika Melitus is a fixture; aesthetic-dermatology landing pages are arguably a sub-category of professional services (named medical director, named procedures, gravitas) but with e-commerce-like elements (price-led promo bundles, before/after photo carousels, online booking widgets). Provisionally treated as professional services with e-commerce elements; revisit if fixture cohort grows.
2. **Multi-page sites vs single landing pages.** Current SE-1..SE-5 score a single page artifact. Some categories (professional services, marketplace, fintech) effectively require multi-page reading — the landing page is a portal, not a complete page. SE-1's "hero answers everything in 10 seconds" anchor may be category-wrong for these. Open question: should the judge be told whether the artifact is a single page or a full site, and adjust expectations accordingly?
3. **Internationalization conventions.** Polish, German, French B2B sites carry different conventions than US/UK pages — more formal voice, denser copy, less PLG-style direct CTAs. The DWF Polish page should be judged against Polish convention, not against Linear convention. Spec doesn't currently distinguish.
4. **Mobile-first vs desktop-first.** B2C apps and e-commerce are mobile-first by default; B2B SaaS and services are desktop-first; dev tools are split. The "above the fold" anchor depends on which fold. Spec doesn't currently distinguish artifact-as-mobile vs artifact-as-desktop.
5. **Newsletter / content-led landing pages.** Substack writers, podcast pages, course landing pages have a different architecture (lead-magnet-led, email-capture-primary, social-proof via author credentials + previous-issue archives). Not in current fixture set but may become so as content_engine lanes mature.

---

## 12. Sources

### B2B SaaS conventions
- [Linear — purpose-built tool for planning and building products](https://linear.app)
- [Vercel — Build and deploy on the AI cloud](https://vercel.com)
- [Stripe — Payments infrastructure for the internet](https://stripe.com)
- [Notion — All-in-one workspace](https://notion.so)
- [Anthropic — AI safety company](https://anthropic.com)
- [Cursor — The AI Code Editor](https://cursor.com)
- [CXL Institute — Conversion Rate Optimization Training](https://cxl.com/institute/)
- [Marketing Examples — Harry Dry's teardowns](https://marketingexamples.com)
- [Pencil Pages — B2B teardowns](https://pencilpages.com)
- [April Dunford — Obviously Awesome (2019) + Sales Pitch (2023)](https://www.aprildunford.com/)
- [Brian Balfour — Positioning-First Growth](https://brianbalfour.com/)
- [Wynter — B2B audience research](https://wynter.com)
- [Animalz — Content strategy](https://animalz.co)

### E-commerce / DTC conventions
- [Allbirds — Sustainable footwear](https://allbirds.com)
- [Warby Parker — Eyewear](https://warbyparker.com)
- [Glossier — Beauty](https://glossier.com)
- [Patagonia — Outdoor apparel + activism](https://patagonia.com)
- [Aesop — Personal care editorial restraint](https://aesop.com)
- [Baymard Institute — E-commerce UX research](https://baymard.com/)
- [Casper — Direct-to-consumer mattress](https://casper.com)
- [Bombas — DTC socks](https://bombas.com)

### Professional services conventions
- [Slaughter & May](https://slaughterandmay.com)
- [Pinsent Masons](https://pinsentmasons.com)
- [DWF Group](https://dwfgroup.com)
- [McKinsey & Company](https://mckinsey.com)
- [Skadden Arps Slate Meagher & Flom](https://skadden.com)
- [EY — Building a better working world](https://ey.com)
- [KPMG](https://kpmg.com)
- [Bain & Company](https://bain.com)
- [BCG](https://bcg.com)
- [Companion deliverable: 2026-05-18-ci-vertical-conventions.md §2](./2026-05-18-ci-vertical-conventions.md) for BigLaw evidence-substrate norms

### Marketplace conventions
- [Airbnb — Vacation rentals + experiences](https://airbnb.com)
- [Etsy — Handmade and vintage marketplace](https://etsy.com)
- [DoorDash — Food delivery](https://doordash.com)
- [Uber](https://uber.com)
- [Lyft](https://lyft.com)
- [Vrbo](https://vrbo.com)

### API / developer-tool conventions
- [Anthropic API documentation](https://docs.anthropic.com)
- [OpenAI Platform](https://platform.openai.com)
- [Twilio](https://twilio.com)
- [Stripe Docs](https://stripe.com/docs)
- [Cloudflare](https://cloudflare.com)
- [Vercel — developer surface](https://vercel.com)
- [Plaid](https://plaid.com)

### B2C app conventions
- [Calm](https://calm.com)
- [Headspace](https://headspace.com)
- [Strava](https://strava.com)
- [Robinhood](https://robinhood.com)
- [Cash App](https://cash.app)
- [Duolingo](https://duolingo.com)

### Fintech conventions
- [Stripe](https://stripe.com)
- [Mercury — banking for startups](https://mercury.com)
- [Ramp — corporate cards + spend management](https://ramp.com)
- [Wise — international transfers](https://wise.com)
- [Brex — startup financial stack](https://brex.com)
- [Wealthfront](https://wealthfront.com)

### AEO / GEO citation research (carried from sibling deliverable)
- Aggarwal et al. "GEO: Generative Engine Optimization" arXiv:2311.09735 (KDD 2024)
- [Ahrefs Q1 2026 AI Overview citation overlap](https://ahrefs.com/blog/ai-search-data/)
- Cyrus Shepard — AI Citation Ranking Factors meta-analysis (Zyppy 2025)
- Profound 10K-passage study (2025)
- Yext 17.2M-citation analysis (2025)
- Search Engine Land 8K-citation AEO study (2025)
- Kalicube — Entity SEO and Semantic Triple framework

### Sibling deliverables
- [2026-05-18-judges-domain-site-engine.md](./2026-05-18-judges-domain-site-engine.md) — generalist domain research (parent)
- [2026-05-18-ci-vertical-conventions.md](./2026-05-18-ci-vertical-conventions.md) — pattern reference for vertical-conventions axis
- [2026-05-18-monitoring-vertical-conventions.md](./2026-05-18-monitoring-vertical-conventions.md) — pattern reference

---

## 4-line summary

- Word count: ~3050.
- Seven categories surveyed (B2B SaaS / e-commerce / professional services / marketplace / API-dev-tool / B2C app / fintech), each with distinct locked architecture, CTA vocabulary, trust-signal form, pricing convention, and Goodhart-collapse mode.
- Strongest recommendation: add three vertical-divergent score-1 anchor examples (SaaS + services + e-commerce or DTC, at minimum) to SE-1, SE-2, SE-4 in site_engine spec — anchored exactly as the CI v2 fix does, without naming the category in rubric prose.
- Universal across all seven categories: one dominant CTA above fold, category-appropriate trust signal, ~10-second reader-question answered (in category-appropriate form). Everything else is convention, not quality.
