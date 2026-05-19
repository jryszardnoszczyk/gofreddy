---
date: 2026-05-19
type: research deliverable — scope-broadening pass
status: complete (input to plan-002 next iteration; NOT a judge spec)
topic: site_engine — full comprehensive surface of an AI-native agency's website work
parent: docs/handoffs/2026-05-18-judge-design-step1-site-engine.md
companions:
  - docs/research/2026-05-18-site-engine-dual-audience-tension.md
  - docs/research/2026-05-18-site-engine-cxl-hero-audit.md
  - docs/research/2026-05-18-site-engine-vertical-conventions.md
  - docs/research/2026-05-18-site-engine-site-quality-md-retirement.md
guide: docs/rubrics/judge-design-guide.md
scope_relationship_to_v1: This is a SCOPE-BROADENING pass. The Step-1 v1 spec locks the JUDGE ARTIFACT
  to a single landing-page surface (SE-A..SE-E). That lock stays — judge artifact shape is a separate
  decision from lane deliverable scope. This deliverable proposes the FULL site_engine OUTPUT SURFACE
  a modern AI-native agency must deliver. The judge can stay narrow while the lane produces broadly.
constraints:
  - DO NOT propose criterion prose
  - DO NOT restate v1 judge spec
  - DO NOT re-litigate the LOCKED single-landing-page artifact shape for the JUDGE
  - Modern lever bias (AEO-native, founder visibility, named-customer outcomes, demo-direct)
  - US-primary; SaaS/AI/agency/service-firm/finance/ecom mix
audience: plan-002 author; judge-design propagator; gofreddy product leadership
---

# Site Engine — Comprehensive Scope (2026-05-19)

## TL;DR

**The current v1 scope is too narrow.** The Step-1 judge spec correctly LOCKS the judge artifact to a
single landing-page surface for Goodhart-resistance reasons (shape-drift defense, dual-audience AND-conjunction,
fixture-validation discipline). That lock is right for the JUDGE. It is wrong as the boundary of what
the site_engine LANE delivers.

A modern AI-native agency in 2026 does not sell "one landing page redesign." It sells **website transformation
across 30+ surfaces, AEO-native architecture, founder-visibility integration, comparison-page warfare, a CRO test
program, and a measurement layer** — delivered as a multi-output bundle that compounds over months. Selling
"landing page rebuild" against Linear, Vercel, Stripe, Anthropic, Mercury, Ramp, Allbirds, Pinsent Masons,
or Slaughter & May is selling 1990s-shaped scope to clients whose competitors are buying 2026-shaped scope from
better agencies.

**The scope problem in one sentence:** SE-A..SE-E judges whether the front door is excellent; site_engine as a
lane must produce the whole house. A page that judge-passes SE-A..SE-E on the front door while the rest of the
site fails the comparison-page war, hides pricing, leaks the wrong founder voice, has no llms.txt, has logo-wall
trust-theatre on the customer page, runs ungated forms, has a 404 that doesn't navigate, has no demo-direct CTA,
and ranks zero times on "[client category] vs [competitor]" queries — that client is still losing in 2026.

**This deliverable proposes ~30 deliverable axes** across eight clusters: (1) audit + IA, (2) page-surface
inventory (~14 distinct page types), (3) discoverability + machine-reading, (4) trust + credibility + founder
visibility, (5) conversion + measurement + CRO test program, (6) compliance + accessibility + performance,
(7) growth-loop integration (post-signup onboarding, email-capture-to-nurture, channel-tied landing variants),
(8) longitudinal program management (30/60/90 + freshness cadence + comparison-page coverage).

**Modern lever bias is sharp**: AEO-native architecture replaces classical-SEO; named-customer-outcomes
replace logo walls; demo-direct CTAs replace contact-sales-walls; founder visibility (LinkedIn, X, podcast,
about-page identity) replaces faceless-brand; comparison pages replace defensive silence; visible pricing
replaces enterprise-mystery; llms.txt + Schema.org + dual-audience copy replace robots.txt-only signals;
current-year cohort data replaces "Last updated YYYY-MM-DD" stamps on stale body copy; founder-voiced
about page replaces stock-photo "Our team" grids; in-viewport product surface replaces hero-illustration
that explains nothing.

**Vertical adjustments matter**: SaaS (PLG vs sales-led split + dev-tool subgenre), agency (case-study density
+ named-founder gravitas), services firm (partner-led credibility + practice areas + matters), finance/fintech
(security + compliance + regulatory-badge row + $X-processed signal), e-commerce/DTC (product photo IS the hero +
review-velocity + shipping-strip + sustainability differentiator). Each vertical's deliverable mix shifts;
the underlying surface inventory is the same with category-appropriate emphasis.

**Deliverable architecture**: site audit (current state across all axes) → IA redesign → page-surface inventory
build-out (12-18 pages first wave, +blog + resource center + comparison program over months) → AEO + Schema +
llms.txt → trust architecture (named-customer with outcomes; founder visibility; pricing transparency) → CRO test
program (initial test backlog + measurement-layer setup) → 30/60/90 execution roadmap → compounding-content
cadence (freshness, comparison expansion, case-study velocity). Size envelope: a v1 client engagement produces
~12-18 distinct deliverables in the first 60 days, +30 over 90 days, then compounds.

**Why this matters now**: gofreddy's first-cohort (Klinika, DWF, plus Anthropic/Perplexity as canonical
exemplars) plus expected fan-out (SaaS, AI startups, agencies, services, finance, e-commerce) cannot be
served by a one-landing-page lane. The lane has to deliver the surface that wins against the same competitors
the client is competing against — and those competitors (Stripe, Linear, Mercury, Ramp, Vercel, Anthropic,
Cursor, Allbirds, Warby Parker, DWF's own Pinsent Masons competition) are running 30-surface programs, not
hero-rebuild engagements.

---

## §1. Full surface mapping (30 axes)

This is the comprehensive surface of an AI-native agency's website work. I have grouped 30+ axes into
eight clusters. Each axis names what it covers, what "modern AI-native 2026" looks like, what's getting cut,
and which SOTA exemplar(s) instantiate the modern pattern.

### Cluster A — Audit + Information Architecture (5 axes)

**A1. Site audit — current state across all dimensions.** Before any production work, produce a current-state
inventory: every URL crawled, every page categorized (home / landing / pricing / comparison / product / use-case /
industry / about / customer-story / blog / resource / docs / demo / contact / legal / careers / 404 / other),
every page scored against AEO + CRO + accessibility + performance + trust + freshness + entity-stability axes.
The audit is the input to all subsequent work and the baseline for measurement. Modern audit covers crawled-by-AI
status (ChatGPT, Perplexity, Claude, Gemini, Google AI Mode, You.com), not just Google indexability. SOTA pattern:
Yext / Profound / AirOps audit decks; Ahrefs / Semrush AEO audits as inputs.

**A2. Information architecture — sitemap, page hierarchy, breadcrumbs, internal linking.** A 2026 IA is not
just hub-and-spoke for SEO; it is **passage-graph design for AI engines** plus **persona-segmented entry paths
for humans**. Sitemap depth should support: per-ICP landing pages, per-vertical industry pages, per-competitor
comparison pages, per-use-case pages, per-channel landing variants (LinkedIn-paid, X-paid, organic-AEO, podcast-driven,
newsletter-driven, conference-driven). Internal linking should pass entity weight to canonical pages (per Volpini /
Kalicube entity-SEO playbook) AND support persona pathfinding (founder → product → pricing → demo; recruiter →
about → careers; analyst → blog → research → press). Breadcrumbs render BOTH for humans AND as
BreadcrumbList schema. Cut: orphan pages, IA driven purely by historical organic-ranking patterns, "About" / "Team"
deep-nested where founder credibility is load-bearing. SOTA: Stripe (https://stripe.com), Notion
(https://notion.so) — multi-axis IA with persona, product, vertical, channel paths visible in nav.

**A3. URL architecture + canonical strategy + redirects.** URL patterns matter for AI-engine parsing (`/saas/`
vs `/products/saas-platform/` are differently parsed entity-paths). Canonical tags must be consistent
across crawler-presented and human-presented variants. 301 redirects from legacy URLs must be in place to preserve
brand-mention authority (Ahrefs r=0.664 brand-mention correlation with AI citation — redirects preserve the
off-domain mention pointer). Cut: trailing-slash inconsistency, mixed case URLs, query-string fragmentation
of indexable URLs. SOTA: Stripe.com URL discipline (every entity has one canonical URL).

**A4. Navigation architecture — primary nav, mega-menus, footer nav, mobile nav.** Modern primary nav has 5-7
top-level items maximum (Wynter / CXL data: nav with > 7 items depresses engagement); category-led nav serves
B2B SaaS, persona-led nav serves multi-segment products (Anthropic's "For developers / For enterprises"),
practice-led nav serves professional services (DWF / Pinsent Masons / Slaughter & May), category-tile nav serves
marketplaces and e-commerce. Footer nav is **load-bearing for AI engines** (footer = the canonical-entity surface
the engine ingests as the company's self-description). Cut: hamburger-only desktop nav, dropdowns with > 12 items,
footer-as-link-dump with no canonical-entity description. SOTA: Linear footer (compact, entity-led), Vercel footer
(dense but categorized), Anthropic footer (research / product / company tracks).

**A5. Page-type taxonomy and template strategy.** Distinct page types need distinct templates. Mixing landing-page
template with blog template with case-study template produces template inconsistency that humans read as
"this site is incoherent." Modern taxonomy: home, ICP landing, vertical landing, channel landing, product, feature,
use-case, comparison ("vs"), alternative-to ("alternative-to-X"), pricing, customer-story, blog post, blog hub,
resource (gated lead magnet), demo, docs, API reference, about, founders, team, careers, contact, security,
legal, 404, sitemap-HTML. Each template carries category-appropriate hero, CTA framing, trust signals, and
schema markup. Cut: one-template-for-everything (the WordPress 2015 default). SOTA: Stripe.com (visibly distinct
templates for products, pricing, docs, customer stories).

### Cluster B — Page-surface inventory (14 distinct page types)

**B1. Home page** — the primary landing surface for direct-navigation and brand-search traffic. Must serve all
three human personas (founder evaluating, recruiter checking, prospect-after-referral diligencing) plus AI-engine
passage-extraction. This is what the Step-1 judge spec (SE-A..SE-E) tests. **In modern AI-native 2026 form**:
declarative hero with named-customer-with-outcome in viewport, single visually-dominant primary CTA, in-viewport
product surface (SaaS) or product photo (e-commerce) or gravitas statement (services) or code block (dev-tool),
named founder surfaced somewhere on the page, visible pricing or pricing shape, current-year cohort data in body
copy, dated case-study reference, canonical-form entity name across hero / footer / structured-data,
40-75-word self-contained passage AND 134-167-word semantic-completeness passage. **CUT**: query-echo hero
("What is X?"), manifesto lead ("We believe..."), three-icon-trio feature dump, logo-walled trust theatre,
"all-in-one platform for modern teams" template hero, gradient-mesh + bordered-card AI-slop. **SOTA**: Linear
(https://linear.app), Vercel (https://vercel.com), Stripe (https://stripe.com), Anthropic (https://anthropic.com).

**B2. ICP / persona / campaign landing pages** — per-ICP variants, per-paid-channel variants. A SaaS targeting both
"startup founders" and "enterprise IT" needs two landing surfaces, not one averaged page (per Anthropic
"For developers" vs "For enterprises" pattern, https://anthropic.com/api vs https://anthropic.com/enterprise).
Per-channel variants align CTA framing and copy to the channel's expected register (LinkedIn-paid lands on
business-formal page; X-paid lands on developer-direct page; podcast-driven lands on founder-narrative page;
newsletter-driven lands on long-scroll-essay page). **Modern form**: same SE-A..SE-E quality bar, persona-specific
named customer in viewport, persona-specific outcome metric, persona-specific CTA action verb. **CUT**: one home
page being run as the landing page for paid social (lights money on fire — Wynter / CXL data: per-channel
variants lift CVR 30-60% vs generic). **SOTA**: Notion's `/personal`, `/teams`, `/enterprise` split; Stripe's
`/payments`, `/billing`, `/connect`, `/atlas`, `/issuing` product-line splits.

**B3. Pricing page — Dunford-grade pricing warfare.** Pricing visibility is a positioning weapon. April Dunford
and Brian Balfour both treat pricing opacity as a positioning failure ("contact sales" reads as evasion to humans
AND gives AI engines no semantic-triple data to ingest as the company's pricing entity). **Modern form**: named
tiers (Free / Pro / Business / Enterprise — or category-appropriate variants), per-tier feature list with explicit
yes/no, named target user per tier ("for solo developers" / "for growing teams" / "for organizations with security
requirements"), at least one anchor price-point visible (even if enterprise is "Talk to us"), comparison
table format, FAQ on pricing logic, named-customer per tier where possible, current-year reference. Per-seat /
per-usage / per-event / flat-rate pricing shapes are entity-data the AI engine ingests. **CUT**: "Contact us" as
only signal across all tiers; "Starting at $X" with no tier definition; pricing page locked behind email-gate.
**SOTA**: Linear pricing (https://linear.app/pricing) — three tiers, feature comparison, named per-tier
targeting; Vercel pricing (https://vercel.com/pricing); Mercury (https://mercury.com/pricing); Notion pricing.
Pinsent Masons / DWF: services firms cannot list per-engagement pricing publicly; **modern form for services**
is rate-card transparency where regulatorily possible OR explicit "engagement shapes" page with phased pricing
("3-week scoping at $X; 12-week build at $X-Y range; ongoing retainer at $X/month") — much more than
"contact us." Slaughter & May does NOT publish pricing; they publish partner-rate-bands implicitly via
peer-firm convention. Vertical-conditional.

**B4. Comparison pages — "vs X", "alternative-to-Y", "best-of-category"** — comparison-page warfare is
**the single highest-leverage content surface in 2026 AEO** that classical-SEO playbooks underweighted.
AI engines answer "Linear vs Jira", "Mercury vs Brex", "Cursor vs Copilot", "Stripe vs Adyen", "DWF vs DLA Piper
Poland" queries directly; pages that own those query slots earn outsized AI-citation share AND high-intent
human traffic. **Modern form**: per-named-competitor page; objective comparison table (feature, pricing, target
user, integrations); honest acknowledgment of where the competitor wins (Dunford "competitive alternatives include
do nothing" applied honestly); named-customer-who-switched quote ("We moved from X to Y because Z"); category-aware
CTA. **CUT**: defensive silence on competitors; comparison pages that read as smear campaigns ("Why X is bad");
unattributed "We're 10x better than [competitor]" claims; comparison tables where every row magically favors the
publisher. **SOTA**: Mercury vs Brex (https://mercury.com/compare/brex), HubSpot vs Salesforce
(https://www.hubspot.com/comparisons/hubspot-vs-salesforce), Notion vs Confluence pattern, Cursor vs Copilot
positioning pages, Wynter's own competitive-research case studies. For services: DWF and Pinsent Masons can do
practice-area-strength comparison pages ("Why choose DWF for Polish RES vs international BigLaw") with
geographic + cost + responsiveness framing.

**B5. Product / feature pages** — deep-link pages per product or major feature. **Modern form**: in-viewport
product surface (screenshot, video, interactive demo), specific capability claim with mechanism described
("Our agent drafts a first pass; engineers review every output before delivery" not "AI does the work"),
named customer using that specific feature, integrated FAQ at section bottom, related-feature internal
linking, schema.org Product markup. **CUT**: feature pages that are 80% screenshot + 20% three-bullet
benefit list; feature pages with no named user / customer. **SOTA**: Stripe's per-product pages
(`/payments`, `/billing`, `/connect`); Linear's per-product pages.

**B6. Use-case pages — "for [job-to-be-done]" variants.** Job-to-be-done framing: a use-case page targets a
specific outcome the buyer is trying to accomplish, not a product feature. "Process expense reports faster"
is a use-case; "OCR for receipts" is a feature. **Modern form**: outcome-led hero, before/after narrative
(time saved, error reduction, headcount avoided), named-customer-with-outcome at top, walkthrough of the
workflow, related-product internal linking, AEO-targeted Q&A in FAQ. **CUT**: use-case pages that read like
feature pages with different headlines; vague use-cases ("improve productivity") without measurable outcome.
**SOTA**: Notion use-case pages (https://www.notion.so/teams/engineering), Vercel use-case pages.

**B7. Industry / vertical pages — "for [vertical]" variants.** Industry-specific landing surfaces for products
that cross verticals (Stripe for SaaS / Retail / B2B; Notion for engineering / sales / HR; Anthropic for legal /
healthcare / financial-services / education). Pinsent Masons and DWF are practice-area / sector-led by default
(sector IS their primary IA axis). **Modern form**: vertical-specific named customer in viewport; vertical-specific
regulatory or compliance context surfaced; vertical-specific use-case examples; vertical-specific CTA. **CUT**:
industry pages that swap the customer logos and keep all other copy identical (humans and AI engines both detect
the template). **SOTA**: Stripe for B2B SaaS (https://stripe.com/use-cases/saas), Pinsent Masons sector pages,
Cloudflare for E-commerce.

**B8. About / Team / Founders — E-E-A-T + credibility surface.** Critical for AI-engine entity-grounding AND
recruiter / candidate human-trust testing. **Modern form**: named founder(s) with photos, named senior team with
roles and brief bios, company-formation date and milestone narrative, named press / podcast / speaking
appearances, investor names where applicable, named advisors where applicable, location and team-distribution
context, link-outs to founder LinkedIn + X + speaking-engagements + Substack / blog. **CUT**: "Our team" page
that's a grid of generic illustrated avatars with first names only; About page with no founder name; About
page that's a brand-narrative manifesto with zero specific facts. **SOTA**: Linear's founders page (specific
named founders + provenance), Mercury about page (founders + investors + location), Anthropic team
visibility, Cursor founder visibility, Cal.com (founder Peer Richelsen and Bailey Pumfleet named with public
LinkedIn / X), Plausible (founder-led, named clearly). Services firms (DWF, Pinsent, Slaughter): named partner
bios with credentials, deal history, contact info. Klinika: named Dr. Maria Noszczyk with credentials,
medical-license number where regulatorily required (Polish medical advertising rules require this).

**B9. Customer / case-study / testimonial pages** — the "Proof" surface. **Modern form**: per-customer case
study with named customer, named contact at customer (role + photo + LinkedIn), specific quantified outcome
("Cocoon saved 40 hours/month on expense reconciliation"), dated context (when implemented, when measured),
methodology of measurement (how the outcome was attributed), industry + size + use-case context, related-customer
discovery. Plus a customer-stories hub page that filters by vertical / use-case / size. **CUT**: logo-wall
"Trusted by 500+ companies" with no per-customer detail; unattributed testimonials ("This product is amazing!");
testimonials with first name only ("Sarah, Marketing Manager"); case studies that are 80% the publisher's
brand-narrative and 20% the customer. **SOTA**: Stripe customer stories (https://stripe.com/customers),
Linear customers, Vercel customers, Mercury customers, Notion customer-stories. Services: DWF / Pinsent
"recent matters" anonymized for confidentiality but specific on transaction shape, value, and partner
attribution. Klinika: before-and-after imagery IS BANNED per client denylist (regulatory), so the modern
form is dated testimonials with full patient consent + procedure-name + practitioner-name + outcome description.

**B10. Blog architecture — hub-and-spoke pillar pages, post-level pages, freshness cadence.** The blog is
the **freshness signal source** for AI engines (Search Engine Land 8K-citation study: 44% of AI Overview
citations are from current-year content). Modern form: pillar hub per major topic-cluster, post-level pages
with dated authorship + author bio + canonical entity name + Schema.org Article markup + internal linking
to related pillars; weekly or biweekly publication cadence; named-author posts (not generic-brand authorship).
**CUT**: blog dormant for > 6 months (signals to humans the company is sleeping; signals to AI engines the
entity is stale); generic-brand authorship; SEO-keyword-stuffed body copy that no human would read end-to-end;
posts that are 80% throat-clearing intro before the answer. **SOTA**: Stripe blog (https://stripe.com/blog),
Vercel blog, Anthropic research / news, Linear changelog-as-blog, Mercury blog (founder-voiced),
First Round Capital blog (for venture-backed agency exemplar), Animalz blog (for agency tone), Marketing
Examples (for agency content-density exemplar).

**B11. Resource center / lead magnets — gated content + ungated content split.** Modern form: ungated
canonical resources (free templates, calculators, frameworks, checklists) for AEO citation share; gated
high-value resources (whitepapers, benchmark reports, original research) for email capture; per-resource
named author + date + outcome-led title. **CUT**: every resource gated behind email-gate (AEO suicide:
the AI engine cannot read the body content if it's behind a gate); resources without authorship; resources
that are 80% generic and 20% client-specific. **SOTA**: HubSpot resource center, Wynter benchmark reports
(named Peep Laja authored), Animalz playbook library, OpenView SaaS metrics, ProfitWell pricing research,
First Round Review.

**B12. Documentation + API reference — for dev-tools.** Critical surface for developer-led products.
Modern form: live API reference with code samples in 5+ languages, interactive request-response, quickstart
in 10 minutes, dedicated SDK docs per language, changelog with semantic versioning + dated releases,
status page link. The docs themselves are an AEO surface — AI engines cite docs heavily when answering
"how do I do X with Y" queries. **CUT**: docs as PDF download; docs hidden behind login; docs dated by
file timestamp (no human-readable date). **SOTA**: Stripe docs (https://stripe.com/docs), Twilio docs,
Vercel docs (https://vercel.com/docs), Anthropic docs (https://docs.anthropic.com), OpenAI Platform docs,
Cloudflare docs.

**B13. Demo / interactive product surface — "show, don't tell"** — in 2026 the demo CTA goes direct.
Modern form: in-page interactive demo (sandbox, replay, video walkthrough — no gate); recorded product
tour with chapter markers; "demo on demand" calendar link (Cal.com / Calendly direct integration) so the
founder evaluates → books a 15-minute call same-hour. **CUT**: "Request a demo" form with 12 fields and
a 3-day SLA before someone responds (Wynter / Drift 2024-2026 data: high-intent buyers expect demo within
4 hours; same-week is acceptable for enterprise; 3-day SLA loses the deal). **SOTA**: Cursor (downloadable
free; the product IS the demo); Anthropic Console (free tier as demo); Mercury (open account = demo);
Notion templates as demo; Cal.com direct-booking-as-demo; Linear sandbox demo; Vercel deploy-demo
preview environment.

**B14. Contact + sales pages + intake forms** — modern form: per-purpose contact paths (general,
sales, support, partnerships, press, careers), short forms (3-5 fields max per Julian Shapiro friction-
per-form-field rule), named recipient where possible ("Reach Sarah, our head of partnerships"),
direct-booking calendar link as alternative to form, response-time SLA stated. **CUT**: generic
"Contact us" form with 12 fields, no named recipient, no SLA, no calendar alternative; sales-only
contact path (humans without sales motion can't find anyone); contact form behind login. **SOTA**:
Cal.com (Calendly-led contact); Linear contact; Mercury contact (categorized intake paths).

### Cluster C — Discoverability + machine-reading (5 axes)

**C1. AEO-native site architecture — dual-audience design throughout.** The Step-1 judge spec (SE-A..SE-E)
tests this on the home page. The LANE must deliver it across every page: declarative hero per page, 40-75
word passage AND 134-167 word semantic-completeness passage per major page, canonical entity name consistency,
named third-party validation per page, current-year reference per page. **CUT**: AEO retrofitted as a single
"AI search" page on the site; AEO treated as a footer-schema add-on; AEO ignored on customer / pricing / about
pages where it's load-bearing for entity-grounding. **SOTA**: Stripe (entity-grounded across every page),
Cloudflare blog (semantic-completeness shaped), Anthropic research pages (passage-extractable).

**C2. Schema.org structured data — Organization, Product, FAQPage, HowTo, BreadcrumbList, Speakable, Article,
LocalBusiness, MedicalBusiness, LegalService, FinancialService.** Per page-type schema requirement.
Organization schema on every page. Product schema on product pages. FAQPage schema where Q&A exists.
HowTo schema on tutorial / use-case pages. BreadcrumbList on every non-home page. Speakable for content
intended for voice-assistant extraction. Article + Author schema on blog. LocalBusiness for services
(Klinika Melitus). LegalService for DWF / Pinsent / Slaughter. MedicalBusiness for healthcare. FinancialService
for fintech. **CUT**: schema generated once and left to rot when content changes; schema validated only at
publish-time, not in CI. **SOTA**: Mayo Clinic (deep medical-business schema), Cloudflare blog
(Article + Speakable), Stripe (Organization + Product across the site).

**C3. llms.txt + robots.txt + sitemap.xml + canonical tags.** llms.txt is the **2025-2026 emerging standard**
for declaring to AI engines what the site authoritatively says (similar in spirit to robots.txt but for
content-extraction guidance). Per Anthropic / Mintlify / Claude convention: a `/llms.txt` file at the root
declares which pages are canonical reference content, which are FAQ-shaped, which are pricing, which are
documentation. robots.txt must allow ChatGPT, Perplexity, Claude, Gemini, Google AI Mode, You.com user-agents
explicitly (some sites block these, then complain about missing AI citation). Sitemap.xml current and dated.
Canonical tags consistent. **CUT**: blocking AI crawlers by default ("we'll figure out monetization later");
sitemap.xml not auto-regenerated on content publish; canonical tags missing on tag-archive / pagination
pages. **SOTA**: Anthropic's llms.txt convention (https://docs.anthropic.com/llms.txt), Mintlify-generated
llms.txt patterns, Cloudflare developer docs.

**C4. AEO integration plan — site_engine + GEO interplay.** The site_engine lane produces full landing-page
surfaces with co-equal human + AI reader weighting. The GEO lane produces narrow single-page AI-citation
optimization. Both serve the same client. Integration: site_engine OUTPUT goes through GEO LANE validation
pass on every page; GEO lane optimization recommendations apply at the per-page level WITHOUT breaking
site_engine's dual-audience requirements. **CUT**: GEO-only optimization that breaks human conversion; site_engine
optimization that ignores AI-engine citation entirely (the 2024 SEO-only playbook re-applied in 2026).
**SOTA**: gofreddy's own emerging dual-lane architecture; Profound's per-passage scoring approach.

**C5. Knowledge Panel + Brand SERP + Wikipedia + Wikidata integration.** AI engines cross-reference brand
entities against Wikipedia / Wikidata / Knowledge Graph. A brand without Wikipedia presence, without Wikidata
entity, without Knowledge Panel triggers gets lower-confidence AI citation. **Modern form**: Wikipedia article
exists (or strategy to earn one via notability); Wikidata entity created and maintained; LinkedIn company
page populated; Crunchbase entry; Schema.org Organization on every page declares canonical entity; consistent
brand-name across all surfaces. **CUT**: relying on owned content alone to establish entity; ignoring
Wikipedia / Wikidata / Crunchbase. **SOTA**: Stripe Knowledge Panel + Wikipedia + Wikidata complete; Anthropic
complete; Mercury complete; smaller players with strategy: Cursor (rapid Wikipedia inclusion 2024-2026).
Per Kalicube / Jason Barnard Entity SEO + Semantic Triple framework.

### Cluster D — Trust + credibility + founder visibility (5 axes)

**D1. Named-customer outcomes — not logo walls.** Logo walls signal "we have customers" without signaling
"customers got outcomes." Modern form is named-customer + outcome + quote + link to case study. The
named-customer-with-outcome appears in viewport on the home page AND has a dedicated customer-story page.
**CUT**: logo wall as only social proof; "Trusted by 500+ companies" counter without per-customer detail;
testimonials with no attribution or vague attribution ("Sarah K., Director"). **SOTA**: Mercury home page
("Cocoon saved 40 hours/month..."), Stripe customer-story linkage, Linear named-customer logos that go
to case studies, Cursor named-developer testimonials.

**D2. Founder visibility — LinkedIn, X, podcast appearances, conference talks.** In 2026, faceless brand
is a liability. AI engines weight named-founder credibility; humans (especially recruiters and prospects-
after-referral) test founder legitimacy. Modern form: founder named on home page (about-link or quote);
founder LinkedIn / X linked from about page; founder podcast appearances surfaced; founder conference talks
surfaced; founder Substack / blog linked if exists. **CUT**: anonymous brand; About page with no founder
name; founder LinkedIn missing or set to private. **SOTA**: Cal.com (Peer Richelsen + Bailey Pumfleet
prominently named, both public on LinkedIn + X), Plausible (Marko Saric + Uku Täht prominently named),
Mercury (Immad Akhund named + active on X), Posthog (James Hawkins + Tim Glaser named), Cursor founders
named, Anthropic founders (Dario + Daniela Amodei) named, Linear (Karri Saarinen named).

**D3. Pricing transparency — visible, structured, comparable.** Per B3 above + interaction with trust: pricing
opacity reads as evasion. Modern form: pricing visible with at least one anchor; per-tier feature list;
comparison-shaped table; FAQ on pricing logic. **CUT**: "Contact us for pricing" as only signal; pricing
behind email-gate; pricing tiers without named per-tier targeting. **SOTA**: per B3.

**D4. Trust signals — security badges, compliance certifications, customer counts, financial backing.**
Modern form: SOC 2 / ISO 27001 / GDPR / HIPAA / PCI-DSS badges where applicable (with link to compliance
report or trust center); security trust center URL; compliance posture page; named investors where the
investor-class is a credibility signal (YC, a16z, Sequoia, Founders Fund, Index, Benchmark); financial backing
amount if material; uptime / status page link; bug-bounty program link if relevant. **CUT**: security badges
without underlying compliance ("SOC 2 in progress" is honest; SOC 2 badge without certification is fraud);
investor logos without named individuals; "ISO certified" without specifying which ISO. **SOTA**: Stripe
trust center (https://stripe.com/about/security), Vercel security page, Mercury compliance, Anthropic
trust center, Cloudflare trust. Klinika: Polish medical-license credentials surfaced. DWF: regulatory
authorizations surfaced.

**D5. Content velocity + freshness signals.** Per SE-E in the v1 judge spec + propagated across the site.
Modern form: changelog dated within 30 days (SaaS); blog post dated within 90 days; case-study dated within
12 months; copyright year current; named-current-year body references; press / awards section dated within
12 months. **CUT**: "Last updated YYYY-MM-DD" stamp on stale body copy; copyright stuck on prior year;
blog dormant > 6 months; press / awards page with content > 2 years old. **SOTA**: Linear changelog
(https://linear.app/changelog) — dated weekly; Vercel changelog; Stripe blog cadence; Anthropic research
+ news cadence.

### Cluster E — Conversion + measurement + CRO test program (5 axes)

**E1. CTA strategy — primary, secondary, scroll-aware, sticky, demo-direct.** Modern form: one primary
CTA per page (visually dominant, named-action verb), at most one secondary CTA (clearly demoted), scroll-aware
CTA that appears after user passes hero + key sections (sticky bottom-bar OR fixed-position CTA),
demo-direct (Cal.com / Calendly link in primary CTA path so high-intent buyers skip the form). **CUT**:
3+ equal-weight CTAs in hero; "Get Started" CTA without context (what does "started" mean?); scroll-aware
CTA that fires before user has any reason to commit (Wynter data: pre-mature scroll CTA depresses overall
CVR 8-15%); contact-form-only path with no calendar alternative. **SOTA**: Linear (single "Start building"
CTA + minor "Get a demo" secondary); Mercury (single "Open account"); Cursor (single "Download"); Cal.com
("Get started for free" with direct-link booking secondary).

**E2. Form optimization — email capture, lead-magnet-gate, sales intake.** Modern form: minimum-viable
fields (email only for lead magnet; 3 fields for newsletter; 5 fields max for sales intake); progressive
profiling (later forms ask incrementally for more); single-column layout; visible privacy statement;
GDPR / CCPA-compliant; named-recipient where applicable; calendar alternative on sales forms. Per Julian
Shapiro friction-per-form-field rule: each field costs ~10-15% conversion; field count is the load-bearing
variable. **CUT**: 12-field intake forms; multi-column forms; forms behind captcha that fail on mobile;
forms with no privacy statement; forms that re-ask data the user has provided previously. **SOTA**:
Cal.com lead-capture (email only); Plausible newsletter (email only); HubSpot progressive profiling
mechanics (the canonical 2018-2024 playbook); Wynter signup (4 fields max).

**E3. Live chat / Intercom / Drift / inbound conversational layer.** Modern form: conversational widget
that's responsive (4-hour response SLA at minimum; same-hour preferable for high-intent), routes by intent
(sales vs support vs partnerships), supports both AI-first response (for FAQ-level queries) and human
handoff (for high-intent), surfaces the named human responding once handoff completes. **CUT**: chat widget
with no staff coverage; chat widget that promises "instant response" and then doesn't deliver; chat widget
that's a forms-disguised-as-chat (interrogating user with form fields in chat UI). **SOTA**: Stripe support
(routed by product); Mercury support (named team members); Drift / Intercom canonical implementations.

**E4. CRO test program — A/B test framework, hypothesis-driven, statistical-significance discipline.**
Modern form: test backlog ranked by ICE (impact × confidence × effort); per-test hypothesis stated;
per-test sample-size calculation; per-test ship-or-kill decision threshold; learnings repository accumulated.
Tools: Google Optimize / VWO / Optimizely / Convert / Statsig / GrowthBook. **CUT**: A/B testing without
hypothesis (button-color tests with no theory); A/B testing that calls winners at 50-visit sample sizes;
A/B testing that doesn't accumulate learnings. **SOTA**: Booking.com (industry-leading test cadence —
1000+ concurrent tests reportedly); ConvertKit / Wynter / CXL test-program documentation; Statsig and
GrowthBook open-source frameworks.

**E5. Analytics + measurement — GA4, Plausible, PostHog, Mixpanel.** Modern form: page-level events
captured (pageview + scroll-depth + CTA-click + form-submit + form-field-engagement); funnel measurement
(home → product → pricing → demo → signup); cohort analysis (per-channel CVR comparison); revenue
attribution where possible (e-commerce); privacy-respecting measurement (Plausible / PostHog over GA4
for privacy-first brands; GA4 + consent management for default). **CUT**: GA4 default setup that captures
nothing meaningful; pageviews as only KPI; no funnel definition; no cohort comparison. **SOTA**: Plausible
(privacy-first canonical), PostHog (product-analytics canonical), Mixpanel, Amplitude.

### Cluster F — Compliance + accessibility + performance (5 axes)

**F1. Accessibility — WCAG AA + axe-core CI integration.** Modern form: axe-core run in CI on every PR;
WCAG AA contrast on body copy + AAA on critical CTAs; semantic HTML throughout; keyboard navigation reachable;
screen-reader-friendly markup; image alt-text required and meaningful; form labels associated; ARIA only
where native semantics insufficient. **CUT**: accessibility as post-launch retrofit; "accessibility tested
manually quarterly" without CI integration; alt-text auto-generated from filenames. **SOTA**: government
sites are usually best (legally required); GitHub accessibility (https://github.com/accessibility),
Microsoft Inclusive Design, gov.uk design system. Per legacy SE-6 the deterministic checks route to
structural_gate in the judge layer.

**F2. Page speed — LCP, FID, CLS, TBT, INP.** Modern form: Core Web Vitals green on PageSpeed Insights;
LCP < 2.5s; CLS < 0.1; INP < 200ms; payload budget per page type (home < 1.5MB; landing < 1MB; blog post
< 800KB); image optimization (WebP / AVIF with srcset); lazy loading; CDN delivery; HTTP/3; preconnect /
preload directives where load-bearing. **CUT**: 5MB hero video on home page; unoptimized images; render-
blocking JavaScript; no CDN. **SOTA**: Vercel canonical (the company is built on it); Cloudflare; Stripe
(documented performance discipline); Linear.

**F3. Mobile UX optimization.** Modern form: mobile-first responsive design; primary CTA reachable
within first viewport on mobile; touch targets sized appropriately (44px minimum per Apple HIG); no
horizontal scroll; mobile-specific navigation pattern (bottom-bar or hamburger); fast-tap CTAs (no
300ms delay); App-Store badges for mobile-app products; click-to-call CTAs for services. **CUT**:
desktop-only design; tiny tap targets; CTAs that disappear on mobile; mobile menus that don't close
on selection. **SOTA**: Stripe mobile, Mercury mobile, Linear mobile, Allbirds mobile (e-commerce).

**F4. Cookie + privacy + GDPR + CCPA compliance.** Modern form: cookie banner that respects consent
(default to no-consent for non-essential cookies in EU); per-category cookie consent (necessary /
analytics / marketing); cookie policy linked; privacy policy GDPR + CCPA + Polish RODO + applicable
sectoral (HIPAA for healthcare, PCI for payments) compliant; data-subject-access-request mechanism;
data-portability mechanism; named DPO where required. **CUT**: cookie banner that defaults to all-consent;
cookie policy that's a copy-paste template with placeholder text; missing GDPR / CCPA mention for
EU + California audiences. **SOTA**: post-Schrems-II 2023-2026 compliance industry-wide; Stripe,
Mercury, Linear all canonical; specifically EU-headquartered companies (Cal.com, Plausible) lead.

**F5. Legal pages — Privacy, Terms, Security, Trust, Compliance, Accessibility statement.** Modern form:
discoverable from footer; current-dated; named DPO / general counsel where applicable; GDPR + CCPA +
sectoral compliance; security page with trust-center link; compliance page listing certifications + reports;
accessibility statement with WCAG conformance level + contact for issues. **CUT**: legal pages outdated;
boilerplate without company-specific adaptation; missing accessibility statement (legally required in
several jurisdictions). **SOTA**: per F4 + Stripe's published list at the footer.

### Cluster G — Growth-loop integration (3 axes)

**G1. Onboarding sequence integration — post-signup, post-demo, post-form-submit.** The website's job
doesn't end at the form submit; the post-conversion sequence is integral. Modern form: per-conversion-path
follow-up (signup → onboarding email sequence; demo-request → calendar booking + prep email; form-submit
→ thank-you page with next-step CTA + resource list); analytics tracking through to product activation;
named-human follow-up where applicable. **CUT**: "Thank you" page as dead-end; no email follow-up;
sales follow-up SLA > 24 hours. **SOTA**: HubSpot's own onboarding (per HubSpot's playbook); Linear
post-signup; Mercury post-account-open; Notion post-signup template recommendation.

**G2. Email capture-to-nurture integration.** Email signups (newsletter, lead-magnet, gated content)
feed into a nurture sequence that delivers value before asking for sale. Modern form: per-source nurture
sequence (newsletter signup gets different nurture than lead-magnet download); per-segment branching
(persona-detected from form signal); unsubscribe respected; double-opt-in for EU compliance. **CUT**:
email-list-as-spam-channel; one-size-fits-all nurture; no segmentation; no unsubscribe mechanism.
**SOTA**: Wynter newsletter (Peep Laja's), CXL Institute (Peep Laja's), HubSpot, Animalz, First Round
Review.

**G3. Channel-tied landing variants — paid LinkedIn, paid X, paid Google, organic AEO, podcast, newsletter
referral, conference referral, partner referral.** Per B2 above + integration with growth-team channel
strategy. Each channel has expected register, intent shape, and CTA framing. **CUT**: one home page for
all channels; no UTM-based variant routing; no per-channel measurement. **SOTA**: Wynter campaign-specific
LPs; Drift channel-LP discipline.

### Cluster H — Longitudinal program management (2 axes)

**H1. 30/60/90 execution roadmap.** A site_engine engagement is not one-shot; it's a compounding program.
Modern 30/60/90 shape: **Days 0-30** — audit + IA redesign + home + 2-3 ICP landing pages + pricing
page + about + 1 customer-story + foundational schema/llms.txt. **Days 31-60** — comparison-page launch
(top 3 competitors) + 3-5 additional ICP / industry / use-case pages + blog hub + 4 initial blog posts
(named-author) + resource center skeleton + first CRO tests live. **Days 61-90** — comparison-page expansion
(next 3-5 competitors) + customer-story library expansion (4-6 case studies) + blog cadence (1-2/week)
+ AEO + freshness audit + measurement dashboard live + retainer transition. **Beyond 90** — compounding
content cadence, monthly comparison expansion, quarterly conversion audit, ongoing freshness/cadence.
**CUT**: one-shot site rebuild engagement with no retainer continuity; no measurement before/after;
no compounding plan.

**H2. Compounding content cadence — freshness, comparison expansion, case-study velocity.** Per H1
beyond-90 + the freshness lever throughout. Modern form: 2-4 blog posts per month, 1 case study per
month, 1 comparison page per month, monthly freshness audit (refresh dates / current-year refs / dead
links / churned customer logos), quarterly entity-stability audit (canonical name across surfaces),
quarterly AEO citation audit (which AI engines cite which pages on which queries). **CUT**: content
cadence drops to zero after engagement ends; no freshness mechanism; no entity-stability discipline.

---

## §2. Cuts (old-school removed)

The 2026 modern lever bias cuts ~12 patterns aggressively. Each is named with the failure mode and the
modern replacement.

**Cut 1 — Logo-wall social proof without context.** "Trusted by thousands of teams" + 8 logos in a row, no
quotes, no outcomes, no links. Reads as theatre to humans; provides no extractable claim for AI engines.
*Replace with*: named-customer + named outcome + named role + dated quote + link to case study.

**Cut 2 — "We're trusted by thousands" / "leading platform" trust theatre.** Unsubstantiated superlatives.
Fails SE-C (proposition survives credibility test). *Replace with*: specific named metric backed by 24-hour-
producible artifact ("$1.2B processed since 2022, audited Q1 2026 — see security report").

**Cut 3 — Vague benefit copy ("save time," "increase productivity," "drive growth").** Digital Applied 2026
2,000-page study: vague benefit copy underperforms specific outcome copy by 4-8% CVR. *Replace with*: named
outcome with mechanism ("Cut review time from 90 minutes to 9; agent drafts first pass + human review every output").

**Cut 4 — Generic SaaS template hero ("all-in-one platform for modern teams").** True of GitHub, GitLab,
Linear, Shortcut, Jira, Atlassian, Vercel, Render, Fly. Zero positioning value. *Replace with*: named category
+ named target + named differentiator ("Linear is the modern issue tracker for high-performing software
teams" — Linear, https://linear.app).

**Cut 5 — AI-generated landing-page slop (gradient mesh + three-icon trio + bordered cards + stock testimonial
grid).** The 2024-2026 template defaulted-to by every model in zero-shot landing-page generation. Both Pencil
Pages and Marketing Examples treat this as the dead giveaway. *Replace with*: client-specific visual identity,
in-viewport product surface (or product photo for e-commerce), named-human voice somewhere on the page,
warmth signals (photographic or illustrative evidence of named team).

**Cut 6 — Classical-SEO keyword stuffing.** Body copy written for organic-rank keyword density. Reads as
machine-generated to humans (Digital Applied 2026: -8% CVR on "delve / leverage / synergize" usage). Parses
worse for AI engines than declarative-document register (Volpini asymmetric-retriever argument). *Replace
with*: AEO-native passage-shaped content (40-75 word self-contained + 134-167 word semantic-completeness
passages) with declarative register + entity-grounding + evidence injection.

**Cut 7 — "Last updated YYYY-MM-DD" sticker without substance.** Freshness theatre. SE-E score-0 in the
v1 judge spec. *Replace with*: substantive current-year body content (current-year cohort data, current
regulatory environment, current pricing surface, current product changes) AND visible date as the
corroborating signal.

**Cut 8 — Generic CTA "Get Started" / "Learn More" without context.** What does "started" mean? Why would I
"learn more"? CTAs need named-action verbs tied to the page's primary intended action. *Replace with*:
category-appropriate verb-phrase ("Start free" / "Book demo" / "Open account" / "Shop Wool Runners" /
"Speak to a partner" / "Read the docs" / "Get API key").

**Cut 9 — Hidden pricing ("Contact us for pricing" across all tiers).** Reads as evasion to humans (Dunford
positioning failure). Provides no semantic-triple data to AI engines for pricing-shape ingestion. *Replace
with*: tier transparency with at least one anchor price-point; per-tier feature comparison; FAQ on pricing
logic. Services firms: rate-band or engagement-shape transparency.

**Cut 10 — FAQ that doesn't answer real questions.** "Q: Is your platform secure? A: Yes, security is our
top priority." Junk Q-A pairs that exist only to fill the FAQ-section template. Provides no AEO citation
value; humans skip past. *Replace with*: FAQ-shaped answers to real category queries (questions humans
actually ask + AI-engines actually receive), authored as substantive 40-75 word passages, with FAQPage
schema.

**Cut 11 — Faceless brand (no founder named, no team named, no human voice).** 2026 trust expectation
includes named-founder visibility. *Replace with*: per D2 — founder named + linked + active on LinkedIn /
X / podcast / Substack.

**Cut 12 — Defensive silence on competitors.** "We don't compare ourselves to others." Cedes the comparison-
query AEO surface to competitors who DO publish comparison pages. *Replace with*: per B4 — comparison-page
warfare; honest acknowledgment of where competitor wins; objective comparison table.

**Cut 13 — Contact-form-only path (no demo-direct, no calendar link).** High-intent buyers want to talk
within hours; 3-day SLA loses the deal. *Replace with*: Cal.com / Calendly direct-booking link as primary
CTA path option; form-submit-with-named-recipient + stated SLA as secondary.

**Cut 14 — Generic stock-photo "Our team" page.** Illustrated avatars with first-names-only. Provides
zero credibility to humans, zero entity-grounding to AI engines. *Replace with*: per B8 — named-founder
+ photos + bios + role + LinkedIn + provenance.

---

## §3. Adds (modern levers added)

Beyond replacing the cuts, here are the net-new modern levers a 2026 AI-native engagement must add.

**Add 1 — AEO-native architecture from the foundation.** Not retrofitted. Every page authored with dual-
audience (human + AI) reading in mind. Declarative leads, passage-shaped sections, entity-stable naming,
schema markup, llms.txt declaration, named third-party validation rendered on-page.

**Add 2 — Comparison-page warfare program.** Per-competitor comparison pages with objective tables and
honest acknowledgment of competitor wins. Single highest-leverage AEO surface in 2026 per the dual-audience
research.

**Add 3 — Demo-direct CTA — Cal.com / Calendly integration.** Replace contact-form-only paths with direct
calendar booking. High-intent buyers book within minutes; sales pipeline accelerates.

**Add 4 — Founder visibility integration.** Named founder on home; LinkedIn + X + podcast appearance
surface; founder-voiced about page; founder Substack / blog if exists. Per Cal.com / Plausible /
Mercury / Cursor model.

**Add 5 — Named-customer-with-outcome program.** Per-customer case studies with named contact + dated
outcome + measurable result. Replaces logo-wall. Drives both AEO citation AND human conversion.

**Add 6 — Per-vertical / per-ICP landing surface.** Persona-segmented landing pages (Anthropic For-developers
vs For-enterprises pattern). Per-channel landing variants for paid acquisition.

**Add 7 — Pricing transparency.** Visible pricing with named tiers + per-tier targeting + comparison
table + FAQ. Services: rate-band or engagement-shape transparency.

**Add 8 — llms.txt + Schema.org full coverage + robots.txt allow-list.** Discoverability for AI engines
as first-class concern. Per Anthropic / Mintlify convention.

**Add 9 — Current-year cohort data + dated case studies + named-author blog cadence.** Substantive freshness
that survives the SE-E "freshness reflects substantive current reality" test.

**Add 10 — Knowledge Panel + Wikipedia + Wikidata strategy.** Off-domain entity-grounding. Per Kalicube /
Jason Barnard Entity SEO playbook. AI engines weight off-domain corroboration r=0.664 vs backlinks r=0.218
(Ahrefs 2026).

**Add 11 — CRO test program — hypothesis-driven, statistical-significance discipline.** Test backlog +
ranking + sample sizing + learnings repository. Not button-color testing.

**Add 12 — Sticky / scroll-aware CTA strategy.** CTAs that follow the user without being intrusive. Scroll-
aware visibility timing.

**Add 13 — Live conversational layer with AI-first triage + human-handoff.** Modern chat that responds in
seconds (AI) and routes to named-human within hours (sales / partnerships).

**Add 14 — Onboarding-sequence integration post-conversion.** The website's job continues into the email
sequence and product activation.

**Add 15 — Compounding content cadence + freshness audit + entity-stability audit.** Monthly cadence;
quarterly audits.

---

## §4. Vertical adjustments

The 30+ axes from §1 apply to every vertical, but emphasis and form-factor shift per category. Below is
the per-vertical adjustment map. Each lists the dominant page-type weighting, the load-bearing trust signals,
the CTA framing convention, the AEO emphasis, and named exemplars.

### Vertical V1 — B2B SaaS (PLG and sales-led)

**Dominant page weighting**: home + per-product + per-feature + pricing + comparison + customer-story +
blog + docs + careers. Comparison-page program is critical (Linear vs Jira; Notion vs Confluence; Mercury
vs Brex). **CTA framing**: PLG "Start free" / sales-led "Get a demo" / hybrid both visible with PLG dominant.
**Trust signals**: named customer logos with case studies, SOC 2 / ISO 27001 / GDPR / HIPAA where applicable,
named investors, founder visibility, changelog freshness. **AEO emphasis**: declarative-document register
across every page; FAQ on every major surface; comparison pages own competitor-query AEO; docs surface
heavily cited. **Exemplars**: Linear (https://linear.app), Vercel (https://vercel.com), Stripe
(https://stripe.com), Notion (https://notion.so), Anthropic (https://anthropic.com), Cursor
(https://cursor.com), Cal.com (https://cal.com), Plausible (https://plausible.io), Posthog
(https://posthog.com), Twilio (https://twilio.com), Cloudflare (https://cloudflare.com), Modal (https://modal.com).

### Vertical V2 — AI labs / AI-native infrastructure

**Dominant weighting**: home + per-product (API + Console + Models) + research + safety + per-vertical
(legal, healthcare, finance, education) + pricing + docs + careers. Research / safety surfaces are
load-bearing for AI labs specifically (E-E-A-T compounded). **CTA framing**: "Try the API" / "Read the
docs" / "Talk to us" with developer-direct path AND enterprise-direct path. **Trust signals**: named
researchers, named papers, safety / responsible-AI page, named enterprise customers, security posture,
investor backing. **AEO emphasis**: research papers ARE the entity-grounding surface; per-paper landing
with declarative-document register; FAQ-shaped Q&A on capability / limitation / pricing. **Exemplars**:
Anthropic (https://anthropic.com), OpenAI (https://openai.com), Mistral (https://mistral.ai),
Cohere (https://cohere.com), Hugging Face (https://huggingface.co).

### Vertical V3 — Agency / consulting / services firm

**Dominant weighting**: home + services / capabilities + case-studies / portfolio + about / founders +
team + insights / blog + contact + per-vertical-served pages. Case-study density IS the proof surface;
home page typically leads with case-study rotation. **CTA framing**: "Start a project" / "Speak to us" /
"Book a strategy call" — services dominant. **Trust signals**: named-founder gravitas, named team with
roles + credentials, case studies with named clients + outcomes, press / speaking / podcast appearances,
agency-of-record awards. **AEO emphasis**: case-study pages ARE the AEO surface (named-client + outcome +
methodology); thought-leadership blog with named-author posts; comparison-implicit-through-positioning
(rather than "vs X" pages, services firms use "Why us over [BigCo competitor]" framing). **Exemplars**:
Animalz (https://animalz.co), First Round Capital (https://review.firstround.com — for the agency-adjacent
content brand), Wynter (https://wynter.com), Pencil Pages (for the teardown brand), Marketing Examples
(https://marketingexamples.com). gofreddy itself fits here.

### Vertical V4 — Professional services (legal / accounting / consulting)

**Dominant weighting**: home + practice areas / sectors + people / lawyers / partners + matters / case-
studies / engagements + insights / publications + offices / locations + careers + contact. Practice-area
+ people are the dual load-bearing surfaces. **CTA framing**: "Get in touch" / "Speak to a partner" /
"Contact the team" — never "Start free." **Trust signals**: named partners with credentials + practice
specialties + dated bar / professional admissions, recent matters with anonymized client identifiers,
named clients-on-record where confidentiality permits, league-table rankings (Chambers, Legal 500, etc.),
named publications + speaking engagements, office locations. **AEO emphasis**: practice-area pages own
the "[legal area] firm [city]" query; named-partner pages own the partner-name query; matters pages provide
the entity-grounding for transaction-shape AEO. **Exemplars**: Slaughter & May (https://slaughterandmay.com),
Pinsent Masons (https://pinsentmasons.com), DWF (https://dwfgroup.com), McKinsey (https://mckinsey.com),
EY (https://ey.com), Skadden (https://skadden.com). DWF's Polish RES practice page is the gofreddy
fixture canonical.

### Vertical V5 — Healthcare / aesthetic-medical (regulated)

**Dominant weighting**: home + treatments / services + practitioners / doctors + clinic / locations +
about + testimonials + booking. Regulatory constraints heavy — Polish medical advertising rules constrain
before-after imagery (Klinika denylist); HIPAA constrains testimonial content in US. **CTA framing**:
"Book consultation" / "Schedule appointment" — service-dominant. **Trust signals**: named-practitioner
credentials with license-number-where-required, named-procedure + outcome + dated context (no before-
after imagery per Klinika denylist), board certifications, association memberships, peer reviews + ratings.
**AEO emphasis**: per-treatment pages own "[procedure] [city]" query; practitioner pages own practitioner-
name + credential query; LocalBusiness + MedicalBusiness schema heavy. **Exemplars**: Mayo Clinic
(https://mayoclinic.org — deep institutional E-E-A-T pattern), Cleveland Clinic, Klinika Melitus
(canonical for gofreddy first cohort), Curology (https://curology.com — DTC-adjacent telehealth pattern).

### Vertical V6 — Fintech / financial services

**Dominant weighting**: home + per-product (banking / cards / payments / treasury / lending) + pricing /
fees + security / compliance + customer stories + about / founders + investors + careers + developers
(API + docs if applicable). Security / compliance surface IS the proof. **CTA framing**: "Open account"
/ "Sign up" / "Get started" with developer-direct "Read the docs" / "Get API key" parallel where dev-
audience exists. **Trust signals**: SOC 2 / PCI / financial-regulator licensure (FinCEN / OCC / state-by-
state for US; FCA for UK; KNF for Poland), named-investors (especially Sequoia / a16z / Founders Fund signal),
named-customer-with-outcome ("Cocoon saved 40 hours" Mercury pattern), $X processed / $X in deposits
signal, named-founder + named-team. **AEO emphasis**: security / compliance pages are load-bearing for
B2B fintech (enterprise procurement reads them); per-product pages own per-product AEO. **Exemplars**:
Mercury (https://mercury.com), Ramp (https://ramp.com), Brex (https://brex.com), Stripe
(https://stripe.com), Wise (https://wise.com), Wealthfront (https://wealthfront.com), Cash App
(https://cash.app), Robinhood (https://robinhood.com).

### Vertical V7 — E-commerce / DTC

**Dominant weighting**: home (product-photo dominant) + product pages + category pages + customer reviews
+ sustainability / impact + about / founder + shipping-returns + email-capture. Product page IS the
landing page for paid acquisition. **CTA framing**: "Shop" / "Add to bag" / "Buy now" / "Pre-order" —
purchase-dominant. **Trust signals**: customer reviews with photos + verified-purchase badges (Yotpo /
Okendo / Stamped pattern); sustainability / impact certifications (B-Corp, FSC, GOTS); press features;
shipping-returns + warranty trust-strip; named-founder + provenance story. **AEO emphasis**: product
pages with rich Schema.org Product + Review + AggregateRating markup; per-category buying-guide content
for "[product type] best of [year]" query coverage; sustainability + impact pages own ethical-purchase
AEO. **Exemplars**: Allbirds (https://allbirds.com), Warby Parker (https://warbyparker.com), Glossier
(https://glossier.com), Patagonia (https://patagonia.com), Aesop (https://aesop.com), Everlane
(https://everlane.com).

### Vertical V8 — B2C app (wellness / fitness / consumer-finance / productivity)

**Dominant weighting**: home (emotion-led + app-store-CTA) + features + reviews / social proof + per-
platform (iOS, Android, Web) + about + privacy / data-policy + support. App-store CTA path dominant. **CTA
framing**: "Download" / "Get the app" with App-Store + Play-Store badges. **Trust signals**: app-store
ratings ("4.8 stars, 600K reviews"), named press features, named celebrity / athlete endorsements where
applicable, privacy-policy clarity, data-handling transparency. **AEO emphasis**: app-store SEO
intersects with web AEO; "[app category] best of [year]" comparison content; FAQ on subscription / privacy
/ data. **Exemplars**: Calm (https://calm.com), Headspace (https://headspace.com), Strava
(https://strava.com), Cash App (https://cash.app), Robinhood (https://robinhood.com), Notion mobile
(https://notion.com/mobile).

### Vertical V9 — Marketplace / two-sided platform

**Dominant weighting**: home (dual-search + dual-CTA hero) + demand-side experience + supply-side
recruitment + categories + trust + safety + about + careers. Dual-CTA structure throughout. **CTA framing**:
demand-side "Find / Book / Search" + supply-side "Become a host / Start selling / List your X" — both
visible at hero. **Trust signals**: reviews on both sides; named-counterparty-with-context; safety policy;
verification badges; counterparty support. **AEO emphasis**: "[marketplace] vs [competitor]" comparison
pages; per-category landing for "[category] near me" / "[category] in [city]" queries. **Exemplars**:
Airbnb (https://airbnb.com), Etsy (https://etsy.com), DoorDash (https://doordash.com), Uber (https://uber.com),
Upwork (https://upwork.com).

### Vertical V10 — Developer tool / API platform (subgenre of B2B SaaS)

**Dominant weighting**: home (code-block-in-hero) + docs + API reference + SDKs + integrations + pricing
(per-unit) + community + status + about + careers. Docs surface is co-equal with home. **CTA framing**:
"Read the docs" + "Get API key" — equal visual weight (per vertical-conventions research). **Trust signals**:
named developer adopters, named engineering blog posts, named-engineers-on-record speaking at conferences,
GitHub presence, status page, SLA. **AEO emphasis**: docs heavily cited (developers ask AI assistants
"how do I do X with [API]"); per-SDK landing for per-language AEO; comparison pages own competitor-query.
**Exemplars**: Stripe (https://stripe.com), Twilio (https://twilio.com), Vercel (https://vercel.com),
Cloudflare (https://cloudflare.com), Anthropic (https://anthropic.com/api), OpenAI Platform
(https://platform.openai.com), Modal (https://modal.com), Replicate (https://replicate.com).

---

## §5. Deliverable architecture

Given the 30+ axes and per-vertical adjustments, the site_engine LANE produces a multi-deliverable
bundle. Below is the recommended deliverable architecture across three engagement-phases (initial /
expansion / compounding).

### Phase 1 — Initial engagement (Days 0-30) — ~10-12 deliverables

1. **Site audit** (current state across AEO + CRO + accessibility + performance + trust + freshness +
   entity-stability). Output: audit deck + scored heatmap + prioritized fix list.
2. **Information architecture redesign** (sitemap + page-type taxonomy + URL structure + nav + footer +
   internal-linking strategy). Output: IA document + sitemap.xml + URL redirect map.
3. **Cut / Reduce / Add prescription** (per the §2 cuts + §3 adds, customized per client vertical).
   Output: prescription document with per-element rationale.
4. **Home page redesign** (the artifact the v1 judge tests SE-A..SE-E on). Output: home page wireframe +
   copy + final HTML + responsive variants.
5. **ICP / persona landing pages — 2-3 variants** (per primary ICPs identified in client positioning).
   Output: per-ICP landing surface.
6. **Pricing page redesign** (per B3 above — tier transparency + comparison table + FAQ). Output:
   pricing page with named tiers + comparison + FAQ.
7. **About / Founders page redesign** (per B8 above — named founder + team + provenance + LinkedIn /
   X / podcast linkage). Output: about page + per-founder bio + linked external presence.
8. **First customer-story page** (per B9 above — named customer + outcome + dated context). Output:
   case-study template + first 1-2 case studies authored.
9. **Schema.org coverage + llms.txt + robots.txt + sitemap.xml** (per C2 + C3 above). Output: schema
   per page-type + llms.txt at root + robots.txt allow-list + sitemap.xml generation.
10. **Foundational AEO integration** (per C1 above — declarative leads + passage-shaping + entity-
    stability — across every page in Phase 1). Output: AEO audit checklist applied to all Phase 1 pages.
11. **Performance + accessibility baseline** (per F1 + F2 above — axe-core CI + Lighthouse baseline).
    Output: CI-integrated checks + baseline scorecards.
12. **Measurement layer setup** (per E5 above — GA4 + Plausible / PostHog + funnel + cohort + dashboard).
    Output: measurement plan + dashboard live.

### Phase 2 — Expansion (Days 31-60) — ~12-15 deliverables

13. **Comparison-page program launch** — top 3 named competitors (per B4 above). Output: 3 comparison
    pages with objective tables + named-customer-who-switched quotes.
14. **3-5 additional ICP / industry / use-case pages** (per B6 + B7 + B2 above).
15. **Blog hub + 4 initial blog posts** (per B10 above — named-author + dated + canonical entity + schema).
16. **Resource center skeleton + 2-3 initial resources** (per B11 above — ungated canonical + 1-2 gated).
17. **First CRO tests live** (per E4 above — initial test backlog ranked by ICE; first 2-3 tests running).
18. **Sticky / scroll-aware CTA strategy** (per E1 above).
19. **Form optimization pass** (per E2 above — field reduction + progressive profiling + privacy).
20. **Live chat / conversational layer** (per E3 above — AI-first triage + human-handoff).
21. **Founder visibility integration** (per D2 above — LinkedIn / X / podcast / Substack surfacing across
    site).
22. **Trust signal expansion** (per D4 above — security badges + compliance + investors + status page).
23. **Cookie + privacy + GDPR + CCPA compliance pass** (per F4 above).
24. **Legal pages update** (per F5 above — privacy + terms + security + accessibility statement).
25. **Mobile UX optimization pass** (per F3 above — mobile-first + touch targets + click-to-call).
26. **Demo-direct CTA integration** (per E1 above — Cal.com / Calendly + named-recipient SLAs).
27. **Knowledge Panel + Wikipedia / Wikidata strategy launch** (per C5 above — Wikidata entity creation
    + Wikipedia notability strategy where possible).

### Phase 3 — Compounding (Days 61-90+) — ongoing cadence

28. **Comparison-page expansion** (next 3-5 named competitors monthly).
29. **Customer-story library expansion** (1 case-study per month minimum; 4-6 in first quarter).
30. **Blog cadence** (1-2 named-author posts per week minimum; pillar pages every quarter).
31. **AEO citation audit** (quarterly — which AI engines cite which pages on which queries; refresh /
    re-shape underperformers).
32. **Freshness audit + entity-stability audit** (monthly freshness; quarterly entity-stability across
    surfaces).
33. **CRO test cadence** (monthly test cycles with hypothesis + sample + decision + learning).
34. **Channel-tied landing variants** (per B2 + G3 above — per-paid-channel variants as growth team
    requests).
35. **30/60/90 → retainer transition** (per H1 above — retainer-shaped engagement covering compounding
    work).

### Multi-part artifact structure

Each Phase 1-3 deliverable is one or more of: (a) **HTML artifact** (the page itself, judge-testable via
SE-A..SE-E or future per-page-type criteria); (b) **Documentation artifact** (audit decks, IA docs,
prescription documents, test backlogs, AEO audit results); (c) **Code artifact** (Schema markup snippets,
llms.txt, robots.txt, CI-integrated checks, redirect maps); (d) **Measurement artifact** (dashboards,
funnel definitions, cohort comparisons). The lane's evolution loop currently judges (a); the lane's
output as a whole includes (a) + (b) + (c) + (d). Plan-002 next iteration must decide how (b)/(c)/(d)
artifacts get evaluated (probably via per-artifact-type judges or via integration tests, not the
SE-A..SE-E semantic judge).

### Size envelope

**v1 client engagement (Days 0-30)**: ~10-12 distinct deliverables; 6-8 distinct page surfaces shipped;
foundational AEO + measurement layer + audit baseline complete. **Days 0-60**: ~22-27 cumulative
deliverables; 12-18 page surfaces; comparison-page program launched; CRO test program live.
**Days 0-90**: ~30-35 cumulative deliverables; 20-25 page surfaces; compounding-content cadence active;
retainer transition complete. **Beyond 90**: ongoing 8-12 deliverables/month (comparison + customer-
story + blog + freshness + CRO + AEO audit).

---

## §6. Evolution-loop considerations

The site_engine lane's evolution loop currently iterates on a single HTML landing-page artifact and judges
it with SE-A..SE-E. The scope-broadening proposed in this deliverable raises three considerations for
the evolution architecture.

### EL1 — Multi-output evaluation cannot reduce to one judge call

A site_engine engagement produces ~30 deliverables across 4 artifact types over 90 days. The current
loop's single-artifact / single-judge architecture cannot evaluate this surface coherently. Three
options:

- **Option A — Single primary artifact + sibling lanes.** The site_engine lane continues to iterate on
  the landing-page artifact (judge: SE-A..SE-E); sibling lanes (`site_audit`, `pricing_engine`,
  `comparison_engine`, `customer_story_engine`, `case_study_engine`, `aeo_audit`, `cro_test_program`,
  etc.) handle other deliverables. Each sibling lane has its own optimal-output spec + criteria. This
  is the **incremental, low-risk path** — preserves the Step-1 v1 spec + extends via new lanes.
- **Option B — site_engine lane with multi-artifact judging.** site_engine produces multiple artifacts
  per iteration; the judge scores each artifact type with its own criteria; the lane's promotion
  decision aggregates across artifacts. **Higher complexity**; risks Goodhart on the aggregation function;
  requires the loop's evaluate_variant.py to handle multi-output.
- **Option C — Hybrid.** site_engine produces landing-page as primary; sibling artifacts (pricing,
  comparison, customer-story) are produced AS related outputs in the same iteration but judged via
  per-artifact-type sub-criteria. The lane treats the bundle as the artifact; judge scores per-artifact-
  type with category-appropriate criteria.

**Recommendation**: Option A (incremental). Each new artifact type gets its own lane. The Step-1 v1
spec doesn't need to change; the SCOPE of work site_engine does in production is just one of N lanes
in the suite. This preserves the design-guide ≤5 criterion ceiling per lane and the AND-conjunction
discipline on the dual-audience surface, while accommodating broader scope through lane proliferation.

### EL2 — Comparison-page lane is the highest-leverage NEXT lane to design

Per the §1 + §3 + §4 analysis: comparison-page warfare is the single highest-leverage 2026 AEO surface
that classical-SEO playbooks under-served. The 8 lanes currently in plan-002 (CI / MON / MA / SB / X /
LI / GEO / site_engine) do not include a comparison-page lane. Recommend adding `comparison_engine` as
the 9th lane in plan-002 next iteration. Its judge would test outcomes: would a hostile competitor's
CMO running a teardown call the comparison honest; would AI engines retrieve this page on "[client]
vs [competitor]" queries; would a buyer in evaluation use this page to make their decision.

### EL3 — Per-page-type judge variants vs one site_engine judge

The Step-1 v1 spec locks the judge artifact to a single landing-page surface. If site_engine continues
to deliver other page types (pricing, comparison, customer-story, about, blog) as a single lane, the
judge will eventually face fixtures from page types it wasn't designed for. Two paths:

- **Path A — sibling-fork the lane.** Per page type: `landing_engine` (current site_engine), `pricing_engine`,
  `comparison_engine`, `case_study_engine`, etc. Each lane has its own ≤5 criteria optimal-output spec.
- **Path B — page-type-conditional within site_engine.** The judge wrapper first identifies the page
  type (the v1 spec already has a "category-context probe" wrapper); criteria branch by page type.

**Recommendation**: Path A (sibling-fork). Aligns with the design guide's per-lane scoping discipline.
Path B risks growing the criteria count past the ≤5 ceiling per category and re-introducing the
feature-checking pre-classifier the v1 spec deliberately avoids.

### EL4 — Goodhart-resistance under multi-deliverable selection pressure

If site_engine evolution is judged across 5 criteria (SE-A..SE-E), the workflow under 50-generation
selection pressure converges on landing-page-template-fill (the Goodhart-collapse the v1 spec already
defends against). If the loop is judged across 30 deliverables, the workflow's Goodhart attack surface
multiplies — every additional artifact + criterion is a slot the workflow can game. The defense is
the same as v1: outcome-questions across every criterion + AND-conjunction across every dual-audience
test + structural_gate routing for deterministic checks + per-criterion CoT + redundancy compression
to live floor 3-4. Adding lanes (Option A above) keeps each lane's criteria count low; growing one
lane's criteria past 5 invites Goodhart.

---

## §7. SOTA exemplars — named with URLs

Below is the per-vertical exemplar table. Each entry names the URL, the vertical, the load-bearing
surface, and the specific dimension the exemplar demonstrates.

### B2B SaaS — PLG / dev-tool

- **Linear** — https://linear.app — canonical declarative hero + single CTA + named customers in viewport
  + visible product surface + dated changelog. Reference for SE-A on B2B SaaS.
- **Vercel** — https://vercel.com — passage self-containment + technical clarity + named customers +
  dual PLG + sales CTA. Reference for AEO-native B2B SaaS.
- **Stripe** — https://stripe.com — evidence injection + named customer scale + per-product page
  discipline + comprehensive trust center. Reference across all axes.
- **Notion** — https://notion.so — persona segmentation (`/personal`, `/teams`, `/enterprise`) +
  template gallery as demo path + multi-format IA.
- **Anthropic** — https://anthropic.com — persona-separated landing (`/api`, `/enterprise`) + named
  research + named team + responsible-AI surface.
- **Cursor** — https://cursor.com — concrete differentiator + product video + named adopters + rapid
  Wikipedia inclusion 2024-2026.
- **Cal.com** — https://cal.com — founder visibility + open-source + scheduling-as-product canonical.
- **Plausible** — https://plausible.io — founder-led + privacy-first positioning + transparent business.
- **PostHog** — https://posthog.com — open-source + founder visibility + product-analytics canonical.
- **Modal** — https://modal.com — modern AI infrastructure landing + code-block hero.
- **Twilio** — https://twilio.com — long-standing API-platform canonical.
- **Cloudflare** — https://cloudflare.com — security + performance + dev-platform canonical.

### Professional services — legal / consulting

- **Slaughter & May** — https://slaughterandmay.com — editorial restraint + named-partner credibility +
  recent matters with anonymized clients + gravitas hero.
- **Pinsent Masons** — https://pinsentmasons.com — sector-led IA + named partners + recent matters +
  practice-area pages.
- **DWF** — https://dwfgroup.com — sector + practice-area + named-partner pattern with Polish RES practice
  page as gofreddy fixture canonical.
- **McKinsey** — https://mckinsey.com — insights-led + named-author thought leadership + global office
  structure.
- **EY** — https://ey.com — service-line + sector matrix IA.
- **Skadden** — https://skadden.com — partner-led credibility + transaction history.

### Fintech / financial services

- **Mercury** — https://mercury.com — "Banking for startups" persona-committed hero + named-customer
  outcomes + Cocoon canonical + named founder.
- **Ramp** — https://ramp.com — corporate cards + spend management + named-customer outcomes + per-vertical
  pages.
- **Brex** — https://brex.com — corporate cards canonical + per-segment landing.
- **Stripe** — https://stripe.com (per above) — payments + financial infrastructure canonical.
- **Wise** — https://wise.com — international transfers + transparency canonical.
- **Wealthfront** — https://wealthfront.com — robo-advisor canonical.
- **Cash App** — https://cash.app — B2C fintech + emotion-led + app-store CTA.
- **Robinhood** — https://robinhood.com — consumer brokerage canonical.

### E-commerce / DTC

- **Allbirds** — https://allbirds.com — product-photo-as-hero + sustainability differentiator +
  free-shipping trust strip.
- **Warby Parker** — https://warbyparker.com — virtual try-on + home-try-on box program + "Find your
  fit" CTA.
- **Glossier** — https://glossier.com — beauty DTC canonical + named-founder narrative.
- **Patagonia** — https://patagonia.com — sustainability + impact + activism integrated into product
  surface.
- **Aesop** — https://aesop.com — editorial brand voice + product photography discipline.
- **Everlane** — https://everlane.com — transparent pricing + supply-chain provenance.

### Marketplace / two-sided

- **Airbnb** — https://airbnb.com — dual-search + dual-CTA pattern + per-category landing.
- **Etsy** — https://etsy.com — supply-side recruitment + demand-side discovery + category tiles.
- **DoorDash** — https://doordash.com — geographic search + demand-side discovery + Dasher recruitment.
- **Uber** — https://uber.com — dual-app paths (rider + driver) + per-product (Eats, Freight).
- **Upwork** — https://upwork.com — talent + client dual-surface.

### B2C app / consumer

- **Calm** — https://calm.com — emotion-led + app-store CTA + named-celebrity association.
- **Headspace** — https://headspace.com — wellness canonical + emotion-led + outcome promise.
- **Strava** — https://strava.com — fitness community + leaderboard + premium tier.
- **Notion mobile** — https://notion.com/mobile — productivity app + per-platform landing.

### AI labs / AI infrastructure

- **Anthropic** — https://anthropic.com (per above).
- **OpenAI** — https://openai.com — AI lab canonical + research + product split.
- **Mistral** — https://mistral.ai — open-weights positioning + European AI canonical.
- **Cohere** — https://cohere.com — enterprise-AI canonical.
- **Hugging Face** — https://huggingface.co — community + open-source + platform integration.

### Healthcare / aesthetic-medical (regulated)

- **Mayo Clinic** — https://mayoclinic.org — institutional E-E-A-T + nested declarative-claim pattern.
- **Cleveland Clinic** — https://my.clevelandclinic.org — institutional pattern.
- **Klinika Melitus** — gofreddy first-cohort canonical (Warsaw aesthetic dermatology + Dr. Maria Noszczyk).
- **Curology** — https://curology.com — DTC telehealth pattern.

### Agency / content brand (for gofreddy positioning context)

- **Animalz** — https://animalz.co — content-agency canonical + named-author thought leadership.
- **First Round Capital** — https://firstround.com / https://review.firstround.com — venture brand +
  content as moat.
- **Wynter** — https://wynter.com — B2B research + Peep Laja named visibility.
- **Marketing Examples** — https://marketingexamples.com — Harry Dry named visibility + teardown brand.
- **Pencil Pages** — https://pencilpages.com — B2B teardown brand.

### Modern small-to-medium AI-native company sites

- **Cursor** — https://cursor.com (per above) — AI-native developer tool.
- **Cal.com** — https://cal.com (per above) — open-source + founder-visible.
- **Plausible** — https://plausible.io (per above) — privacy-first + founder-visible.
- **PostHog** — https://posthog.com (per above) — open-source product-analytics.
- **Mercury** — https://mercury.com (per above) — modern fintech.
- **Modal** — https://modal.com — AI infrastructure.
- **Replicate** — https://replicate.com — ML model marketplace.
- **Vercel** — https://vercel.com (per above) — frontend cloud.
- **Mintlify** — https://mintlify.com — docs-as-product, llms.txt convention canonical.
- **Resend** — https://resend.com — modern email API canonical.
- **Linear** — https://linear.app (per above) — issue tracker canonical.

### 2026 winners — companies whose web presence visibly leveled up in 2026

- **Cursor** — rapid Wikipedia inclusion + persona-committed hero + named-developer adoption.
- **Anthropic** — persona-separated landing pattern + responsible-AI surface + research-led trust.
- **Mercury** — named-customer Cocoon outcome quote + founder visibility + open-source positioning.
- **Resend** — modern API platform launch with docs-first IA.
- **Modal** — AI-infrastructure landing with code-block hero canonical.
- **Cal.com** — open-source positioning + founder + scheduling-as-product.
- **Mintlify** — llms.txt convention canonical + docs-as-product canonical.

---

## §8. Open questions

The scope-broadening proposed in this deliverable raises questions plan-002 next iteration must resolve.

**OQ1 — Lane decomposition strategy.** Per §6 EL1: Option A (sibling-fork into 9-15 lanes) vs Option B
(multi-artifact site_engine) vs Option C (hybrid). Recommend Option A. **Decision required from plan
author**: which sibling lanes to add in plan-002 next iteration? Top candidates: `comparison_engine`,
`pricing_engine`, `customer_story_engine`, `aeo_audit_engine`, `cro_test_program`, `site_audit_engine`,
`founder_visibility_engine`, `case_study_engine`, `industry_landing_engine`. Likely Phase 1 priority:
`comparison_engine` (highest 2026 AEO leverage), `customer_story_engine` (foundational trust signal),
`site_audit_engine` (input to all other lanes).

**OQ2 — Page-type judge variant strategy.** Per §6 EL3: sibling-fork by page type vs page-type-
conditional judging. Recommend sibling-fork. **Decision required**: how granular? Per-page-type (12+
lanes) vs per-page-cluster (4-6 lanes: landing / pricing / proof / docs / etc.). Plan author triage.

**OQ3 — Multi-deliverable evolution-loop architecture.** Per §6 EL1 + EL4: how does the evolution loop
handle bundles of related deliverables? Current loop iterates one artifact + judges with one rubric.
The lane SCOPE proposed here is bundle-shaped. **Decision required**: does each lane iterate its own
single artifact (Option A), or does site_engine become a bundle-producing lane (Option B)?

**OQ4 — Cross-lane consistency enforcement.** If `comparison_engine` and `landing_engine` and
`customer_story_engine` are sibling lanes serving the same client, they must enforce entity-stability
across artifacts (canonical entity name; canonical positioning; canonical voice persona). Currently
`ClientConfig.voice_persona` handles voice; what handles entity / positioning / canonical-customer-
naming consistency across lanes? **Decision required**: is `ClientConfig.entity_stability_anchor` a
new infrastructure surface? Where do canonical claims live?

**OQ5 — Comparison-page lane design — what's the optimal-output spec?** If `comparison_engine` is the
recommended 9th lane, it needs its own Step-1 spec. **Question**: who is the reader? (Buyer in evaluation
+ AI engine answering "X vs Y" query.) What's the artifact? (Single comparison page per competitor.)
What are the criteria? (Honest acknowledgment of competitor wins; objective comparison; named-customer-
who-switched quote; surviving hostile-CMO teardown.) Plan-002 next iteration triage.

**OQ6 — Founder-visibility lane vs founder-visibility integration?** Founder visibility (D2 above) is
load-bearing across many deliverables. Question: is it its own lane (`founder_visibility_engine`)
producing per-founder LinkedIn / X / Substack / about / speaking-engagement strategy as artifact? Or
is it cross-cutting infrastructure that every lane consumes? **Recommendation lean**: cross-cutting
infrastructure (one `FounderProfile` per client; consumed by site_engine + linkedin_engine + x_engine +
article_engine). **Decision required**.

**OQ7 — Site-wide AEO citation tracking — own lane or measurement layer?** The §5 Phase 3 work includes
quarterly AEO citation audits. Question: is `aeo_audit` a lane (produces audit deliverable) or a
measurement layer (continuously tracks)? **Recommendation lean**: measurement layer + audit-deliverable
hybrid. Measurement is continuous (track which AI engines cite which pages on which queries); audit
deliverable is quarterly (synthesize + recommend). Plan author triage.

**OQ8 — Comparison-page warfare ethical / legal framing.** Per §4: comparison pages must honestly
acknowledge where competitor wins. Open question: how does the lane enforce this when the workflow's
selection pressure rewards "we win on every row" claims? **Recommendation lean**: structural_gate
check on every comparison page — at minimum one row must explicitly favor the competitor — to defend
against optimization toward smear-campaign output. Plan-002 next iteration design.

**OQ9 — Vertical-specific page-type weighting.** Per §4: services firms weight people / matters /
practice-area pages over pricing; e-commerce weights product pages over feature pages. Question: how
does the lane infer vertical from client metadata, and how does it weight Phase 1-3 deliverables
accordingly? **Recommendation lean**: `ClientConfig.vertical` + per-vertical Phase 1-3 deliverable
template. Plan-002 design.

**OQ10 — Channel-tied landing variant production scale.** Per B2 + G3: per-paid-channel landing
variants are a 30-60% CVR lift opportunity. Open question: how many variants does the lane produce
in Phase 1 vs Phase 2 vs Phase 3? **Recommendation lean**: 0 in Phase 1 (foundational work); 3-5 in
Phase 2 (first paid channels); ongoing in Phase 3 as growth-team requests. Plan author triage.

**OQ11 — Knowledge Panel + Wikipedia + Wikidata strategy lane assignment.** Per C5: off-domain entity-
grounding is load-bearing. Open question: is this part of site_engine, AEO lane, GEO lane, or its own
`entity_grounding` lane? **Recommendation lean**: own lane (`entity_grounding`) or fold into GEO. Plan
author triage.

**OQ12 — Demo-direct CTA implementation responsibility.** Per E1 + B13: Cal.com / Calendly direct-booking
in primary CTA path. Open question: this requires CRM / calendar integration outside the website
build itself. How does the lane handle the integration boundary? **Recommendation lean**: deliverable
includes integration spec; client's operations team or gofreddy's integration sub-lane handles the
actual integration. Plan author triage.

**OQ13 — When does plan-002 add these lanes?** Per OQ1: the lane fan-out proposed here is large.
Realistic phasing: plan-002 v1 ships with current 8 lanes + site_engine v1 spec; plan-002 v2 adds
`comparison_engine` + `customer_story_engine` as the highest-leverage adds; plan-002 v3 adds the
remaining sibling lanes as needed. The current v1 plan should NOT try to absorb all 9-15 lanes at
once — the design guide's per-lane discipline argues for incremental lane addition with first-fixture
validation before the next lane lands.

**OQ14 — Retainer-shape revenue model implications.** The 30/60/90 → retainer transition (H1 above)
implies gofreddy's revenue model includes ongoing retainer engagements, not one-shot rebuild deals.
Open question: how does this affect pricing / packaging / sales? **Recommendation lean**: this is
business-model commentary outside the lane's design scope but worth surfacing as a product question.

**OQ15 — First-cohort overfit watch broadened.** The v1 judge spec's first-cohort overfit watch (§1
substitute-readers + §1.5 empirical-validation scope) extends to the lane's deliverable scope. Open
question: which Phase 1-3 deliverables are b2b-tech-first-cohort-shaped vs cross-vertical? Specifically:
the comparison-page program (§5 step 13) is highly category-conditional; the customer-story lane is
highly category-conditional (services firms anonymize; B2B SaaS name explicitly; healthcare obscures
patient data); the founder-visibility surface is category-conditional (services firms surface named-
partners over founder; B2B SaaS surfaces founder over team). Each deliverable's vertical-anchor set
needs the same 3-vertical-divergent-example discipline the v1 judge spec applies on SE-A / SE-B / SE-D.

---

## Closing

The Step-1 v1 judge spec is correctly scoped at the JUDGE level: single landing-page surface, ≤5 criteria,
AND-conjunction on dual-audience tests, Goodhart-resistance discipline. That should not change.

The scope of what the site_engine LANE delivers in production has been too narrow. A modern AI-native
agency in 2026 sells a 30-deliverable bundle across audit, IA, page-surface inventory, AEO + machine-
reading, trust + founder visibility, CRO + measurement, compliance + performance, growth-loop
integration, and longitudinal compounding cadence. The lane should produce all of this — likely through
sibling-fork into 9-15 lanes (recommendation: incremental adds of `comparison_engine`,
`customer_story_engine`, `site_audit_engine` as Phase 1 priorities for plan-002 next iteration).

The modern lever bias is sharp: AEO-native architecture replaces classical-SEO; named-customer-outcomes
replace logo walls; demo-direct CTAs replace contact-form-only paths; founder visibility replaces
faceless brand; comparison-page warfare replaces defensive silence; visible pricing replaces enterprise-
mystery; current-year cohort data replaces freshness theatre; in-viewport product surface replaces
hero-illustrations that explain nothing.

Per-vertical adjustments are real — SaaS vs services vs fintech vs e-commerce vs healthcare vs marketplace
vs dev-tool vs B2C-app each have category-appropriate emphasis. The underlying 30-axis surface is the
same; the weighting and form-factor shift.

The first-cohort overfit watch from the v1 judge spec extends to the lane's deliverable scope: every
deliverable proposed here needs the same 3-vertical-divergent-example discipline before it gets locked
as a lane.

Plan-002 next iteration is where the lane-decomposition + page-type-judge + cross-lane-consistency
decisions land. This deliverable is the scoping input; the plan author triages OQ1-OQ15 against current
client cohort needs and engineering capacity.
