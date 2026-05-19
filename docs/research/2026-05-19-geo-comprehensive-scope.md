---
date: 2026-05-19
type: research deliverable
status: complete (full-surface scope-expansion pass for GEO lane v1+)
topic: full comprehensive surface of valuable GEO / AEO activities for a 2026 AI-native agency
parent: docs/handoffs/2026-05-18-judge-design-step1-geo.md
siblings:
  - docs/research/2026-05-15-judges-domain-geo.md
  - docs/research/2026-05-18-geo-vertical-conventions.md
  - docs/research/2026-05-18-geo-artifact-taxonomy.md
  - docs/research/2026-05-18-geo-ai-failure-modes.md
  - docs/research/2026-05-18-geo-dual-audience-tension.md
reader: JR + future GEO-lane plan author + autoresearch evolution-loop architect
posture: comprehensive (do NOT scope-reduce); modern-lever bias; US-primary defaults; Poland first-cohort context only
---

# GEO / AEO — The Full Comprehensive Surface for a 2026 AI-Native Agency
## What the lane should actually cover when the v1 single-page framing is too narrow

The current v1 GEO spec (`docs/handoffs/2026-05-18-judge-design-step1-geo.md`) scopes the lane to **one optimized page** in one of 10 form factors. This is the right MVP, but it is **not the right ceiling**. By Q3-2026 a generic AI-native agency serving SaaS / AI-lab / agency / service-business / finance / e-commerce founders is responsible for at least **22 distinct GEO-relevant activity axes**, only ~5 of which are single-page concerns. The remaining ~17 — site architecture, off-page signal engineering, comparison-page warfare, brand-mention engineering, retrieval testing, cross-engine optimization, custom-GPT distribution, knowledge-panel capture, author/founder E-E-A-T construction, negative-AEO defense — are where the differentiated 2026 wins live, and where the deprecated 2018-era SEO playbook gets cut.

This deliverable maps the full surface so the GEO lane can either (a) absorb the expansion into its `geo_format` enum + structural-gate routing as v1.x, (b) sibling-fork specific axes into adjacent lanes (`site_engine`, `monitoring`, a new `off_page_signal_engineering` lane), or (c) declare them out-of-scope for the autoresearch loop and route to operator-side runbooks. The decision is JR's. The mapping is exhaustive so that decision is informed.

---

## TL;DR — 7 load-bearing recommendations

1. **GEO is a portfolio, not a page.** The full surface is ~22 axes across 6 layers (page, site, off-page, distribution, monitoring, defense). v1 covers ~5 (page-level). To remain competitive in 2026 the lane needs to address at least 14 — the cut points are real, but defaulting to "page only" loses ~70% of the actual value.

2. **The deprecated half of the old SEO playbook is bigger than people admit.** Keyword density, exact-match anchor text, content-velocity-for-its-own-sake, generic listicles, mass directory submissions, EMD (exact-match domain) plays, link-building outreach campaigns, schema-stuffing without substance, page-speed-for-its-own-sake, AMP, and most of the "technical SEO checklist" canon contribute ≤0 to AI-engine citation rate in 2026. The modern levers that replace them carry r=0.4 to r=0.7 correlation with AI Overview / ChatGPT / Perplexity citation share.

3. **Brand mentions r=0.664 > backlinks r=0.218 with AI Overview visibility (Ahrefs 75K-brand 2025).** This single finding flips the priority stack. PR, podcast appearances, founder visibility, Reddit / Wikipedia / Wikidata anchoring, and unlinked third-party mentions now matter ~3× more than the link-building outreach that consumed the 2018-2022 budget. A comprehensive GEO lane must produce *off-page signal plans*, not just on-page artifacts.

4. **Comparison-page warfare is the highest-leverage activity for B2B SaaS / professional services / AI tooling.** "X vs Y" / "alternatives to Z" / "best of category" pages account for 43.8% of all ChatGPT citations (Ahrefs 26K-URL 2026). Xero deliberately published dozens of "Xero vs QuickBooks" pages over years to win the category; NetSuite and Sage Intacct dominate mid-market ERP queries via the same playbook. The lane should produce a comparison-page target list — who to compare against, which dimensions to compete on, when to publish — as a first-class deliverable.

5. **Off-page signal engineering is the *single* biggest gap in v1.** Reddit alone is the #1 source in 6 of 7 verticals studied (Foundation 2026, 20.8% top-50 share); Wikipedia is ChatGPT's #1 cited source globally (7.8% all citations); Wikidata anchoring resolves entity confabulation. None of these surface in v1 because v1 only scores the page. The lane needs to produce *Reddit answer-shape recommendations*, *Wikipedia editing targets*, *Wikidata seeding actions*, and *podcast appearance + PR placement targets* — not as a side channel but as a primary deliverable axis.

6. **Multi-part deliverable, not multi-file deliverable.** Run a single coherent ~12,000-18,000-word multi-section artifact (the "GEO Strategic Plan") with 8-12 named sections that the evolution loop can iterate on as a whole. Don't fan out to 12 separate artifacts (kills loop coherence; produces local-optima drift per section). Don't compress to a single page (loses the comparison-page warfare + off-page signal axes). The CI-pattern of "one rich brief, multiple sections" is the right precedent.

7. **Engine-specific optimization is now a real axis (not a single universal target).** ChatGPT prefers Wikipedia + Reddit; Perplexity prefers 12-18mo freshness + 21+ source citation density (especially on medical); Claude prefers official docs + low-citation-fabrication (94% accuracy); Gemini / Google AI Mode now pulls 38% from outside organic top-10 (down from 76%) and weights brand mentions r=0.664. The lane should produce *per-engine retrieval probes* and *per-engine optimization tactics* — not one undifferentiated "AI-friendly" target.

---

## §1 — Full surface mapping: 22 GEO/AEO activity axes a 2026 agency owns

Grouped into 6 layers. v1 currently lives in Layer 1 axes 1-5; everything else is the expansion.

### Layer 1 — Page-level optimization (5 axes, v1 covers)

**Axis 1.1 — BLUF / declarative answer-first lead.** First 40-75 words contain a complete citable answer (Volpini Matryoshka Paragraph + Perplexity 90/100-words finding). Already in v1 as GEO-1.

**Axis 1.2 — Evidence injection: stats, quotes, citations.** Per Aggarwal KDD 2024, the optimal method is domain-conditioned — Statistics Addition wins in Law & Government / Opinion (+28-40% citation lift); Quotation Addition wins in People & Society / History; Fluency Optimization wins in Health & Business. v1 covers as GEO-2 but does not yet route by domain.

**Axis 1.3 — Passage self-containment (chunk-completeness).** Each 40-75 word passage works standalone (Profound 3.1× citation lift). v1 covers as GEO-3.

**Axis 1.4 — Entity stability + canonical naming.** Same name everywhere; schema.org `@id`; OpenGraph; H1; BLUF first sentence. v1 covers as GEO-4. Adjacent: disambiguation block against most-confusable similar-name target (e.g., "Cursor IDE, not the data-cursor library").

**Axis 1.5 — Format-intent match + freshness signal.** 10 canonical form factors (definition / how-to / comparison / listicle / FAQ / glossary / pillar-hub / integration / pricing / product-landing) per `geo-artifact-taxonomy.md`. v1 covers as GEO-5 with per-fixture enum routing.

### Layer 2 — Site architecture (4 axes, v1 partially / not at all)

**Axis 2.1 — Entity graph + knowledge-graph anchoring.** Schema.org `sameAs` to Wikidata / Crunchbase / SEC EDGAR / LinkedIn / Google Business Profile; Organization + Person + Place schema; internal `@id` consistency across all pages naming the entity. Kalicube's working framework. **Cuts entity confabulation** (Q1 of `geo-ai-failure-modes.md`) at the structural-gate level. Currently absent in v1 except as a single line in the proposed structural-gate.

**Axis 2.2 — Hub-and-spoke topology (pillar + cluster).** Pillar page orchestrating 8-20 cluster children; cluster children linking back to pillar; pillar linking out to clusters. HubSpot's original taxonomy still applies but with 2026 caveats: thin pillars demoted by Google March/April 2026 updates; cluster children must carry real original content; topical-bloat sitewide classifier kicks in if pillars are >40% of site content. v1 explicitly defers this to `site_engine`; the comprehensive scope says the boundary needs adjudication — at minimum, GEO should produce *pillar-and-cluster topology recommendations* as part of its strategic plan even if the actual page implementation lives elsewhere.

**Axis 2.3 — Internal linking + breadcrumbs.** Breadcrumb schema; descriptive anchor text (NOT exact-match-keyword anchors — that's the deprecated tactic); strategic linking from high-authority pages to commercial / conversion targets; orphan-page elimination. Modern caveat: AI engines don't care about PageRank flow nearly as much as Google did; what matters is whether the cluster-child can be retrieved standalone, and breadcrumbs help fan-out queries route correctly.

**Axis 2.4 — Canonical URL hygiene + sitemap + robots.** `rel="canonical"` matching served URL; sitemap.xml with `<lastmod>` accurate per page; robots.txt allowing OAI-SearchBot / PerplexityBot / ChatGPT-User / GPTBot / Google-Extended / Claude-Web / CCBot per your retrieval-eligibility intent (NOTE: blocking GPTBot blocks training but allowing OAI-SearchBot allows retrieval — these are separate user agents in 2026). Per ALM Corp 2026: 23% of sites accidentally block AI retrieval bots and don't know it.

### Layer 3 — Structured data + AEO infrastructure (3 axes, v1 partial)

**Axis 3.1 — Schema.org markup mix.** Per form factor: Organization + Person + LocalBusiness (universal); Article / NewsArticle / BlogPosting (content); Product / Offer / AggregateRating / Review (DTC); SoftwareApplication / SaaSProduct (B2B SaaS); FAQPage (now schema-only AI signal after Google killed rich results May 7 2026; still 3.2× AI Overview lift per Frase 2026); HowTo (demoted on non-primary content per Google March 2026); MedicalEntity / MedicalCondition / MedicalProcedure (healthcare YMYL); DefinedTerm + DefinedTermSet (glossary); BreadcrumbList (navigation); Speakable (voice / smart-speaker eligibility); ItemList (listicle); QAPage (single Q+A pages — distinct from FAQPage); VideoObject + Clip + WatchAction (video content); JobPosting (recruiting); Event (events). **The lane should specify which markup is mandatory vs optional per `geo_format`** — currently the v1 spec gestures at this but doesn't lock it.

**Axis 3.2 — llms.txt + llms-full.txt + skill.md.** Anthropic, Cursor, Perplexity, Stripe, Mintlify-hosted docs ship `/llms.txt` and `/llms-full.txt` files in markdown for AI agents to ingest directly. Standard published by Jeremy Howard (Answer.AI) Sept 2024. By Q2-2026 the practitioner-canonical default is `llms.txt` for navigation + `llms-full.txt` for full markdown dump + per-page `*.md` siblings. **This is a 2026-specific tactic with no 2018 equivalent.** The lane should produce *llms.txt + llms-full.txt templates* per client as a deliverable. Currently absent from v1.

**Axis 3.3 — Server-rendered HTML + cache headers + Core Web Vitals (de-prioritized).** Critical content must be in server-rendered HTML (no JS-only pricing — Similarweb 2026 CRM case study: 23% vs 78% citation rate from JS vs HTML pricing). Cache-Control headers so AI crawlers don't get stale 304s. **Core Web Vitals (LCP / INP / CLS) matter less for AI citation than they did for Google ranking** — but still matter for the human-reader half of dual audience. Don't deprioritize entirely; don't lead with it as 2019-era SEO did.

### Layer 4 — Off-page signal engineering (5 axes, v1 ZERO coverage — the single biggest gap)

**Axis 4.1 — Reddit answer-shape engineering.** Reddit is the #1 source in 6 of 7 verticals studied (Foundation 2026); 20.8% of top-50 ChatGPT citations across studied prompts; 21-24% of AI citations on Perplexity for product queries. Modern tactic: identify the 5-15 subreddits relevant to each client's category; produce answer-shape recommendations (NOT astroturfing — that's bannable; rather, genuinely answer questions where the brand has expertise + cite case studies + link out only where natural). Founders or named team members post under real identities; the substrate of cited Reddit content for AI engines is real-account-built, not throwaway. **The agency's deliverable is a Reddit-engagement plan: subreddit list, comment-quality criteria, escalation rules, founder-vs-team assignment, monthly cadence.** This is closer to PR than to SEO.

**Axis 4.2 — Wikipedia editing + Wikidata anchoring.** Wikipedia is ChatGPT's #1 cited source globally (7.8% all citations, 47.9% of top-10 share). For brands large enough to have a Wikipedia article: maintain it accurately (no self-edits — disclose conflict of interest, work through neutral editors); ensure the article reflects current product/service offering; cite primary sources properly. For brands without a Wikipedia article: don't manufacture one (will be deleted); instead seed Wikidata. Wikidata (the structured-data sister) accepts smaller-business entries with proper sourcing; a Wikidata Q-ID with `sameAs` from the brand's schema.org Organization JSON-LD resolves a meaningful fraction of entity-confabulation failures. **The agency's deliverable is a Wikipedia-and-Wikidata audit + editing-target list per client.** Polish clients (Klinika, DWF Poland) also have Polish Wikipedia + Wikidata in PL — both matter for AI engines responding in Polish.

**Axis 4.3 — Quora + StackExchange + niche-community answers.** Quora has lost ChatGPT citation share over 2024-2026 but remains in top-20 for many B2B queries; StackExchange (incl. Stack Overflow, Server Fault, Mathematics) is the #1 cited source for technical / developer / AI-engineering queries — Claude / GPT-5.5 / Gemini all over-cite Stack Overflow accepted answers. Niche communities (Indie Hackers, Hacker News, dev.to, Lobsters, RealSelf for aesthetics, Avvo for legal, WebMD forums for health) matter per-vertical. **The deliverable is a per-vertical community-engagement map** — which forums matter, what answer shapes earn citation, who posts.

**Axis 4.4 — PR + podcast appearances + founder visibility.** Ahrefs 75K-brand study: brand mentions correlate r=0.664 with AI Overview visibility — **three times the backlink correlation (r=0.218).** Unlinked mentions in third-party text (Tier-1 publications, podcasts, industry analyst posts, Substack newsletters) are the driver. The agency's responsibility: identify podcast appearance targets (Tier-1 broad: Lex Fridman / Tim Ferriss for AI / founder; Tier-2 vertical: SaaStr / Indie Hackers / Latent Space / Practical AI / The Twenty Minute VC for SaaS; per-vertical equivalents); PR placement targets per Tier (TechCrunch / The Information / Stratechery / Pirate Wires for AI; AmLaw / Above the Law for legal; Allure / Vogue for aesthetic-derm); founder-LinkedIn-and-Twitter posting cadence; named-byline guest-post placements. **This is the single highest-ROI activity per the 2026 evidence and it has nothing to do with the page.**

**Axis 4.5 — Citation building (.gov / .edu / journal / industry-association mentions).** Different from backlinks — these are *unlinked* citations on high-authority domains. Sponsoring a research project at a university; contributing data to an industry-association report; being quoted in a .gov regulatory comment; being cited in a peer-reviewed paper. Long-tail but compounding. For finance / fintech / healthcare / legal clients, regulator-aligned content (SEC comment letters, FDA citizen petitions, NIST submissions) carries citation weight far above the equivalent backlink.

### Layer 5 — Distribution + AI-engine-native channels (4 axes, v1 ZERO coverage)

**Axis 5.1 — Custom GPT / Claude Project / Gemini Gem / Perplexity Space distribution.** Custom GPTs in the OpenAI GPT Store now serve ~3M monthly active users (Q1 2026); Claude Projects (Anthropic) have crossed 1M shared-project users; Perplexity Spaces; Gemini Gems. Brands publishing a Custom GPT with their domain knowledge + branded prompts + named knowledge sources turn the brand itself into a distribution channel inside ChatGPT — and these Custom GPTs are now ranked in OpenAI's GPT Store category pages. **For B2B SaaS / consulting / AI clients this is a primary 2026 distribution surface.** Klinika could publish "Aesthetic Dermatology Procedure Guide" Custom GPT; DWF could publish a regulatory-update Claude Project. The agency's deliverable: identify which Custom GPT / Claude Project / etc. each client should publish, draft the system prompt + knowledge sources, monitor usage analytics.

**Axis 5.2 — Agentic-commerce protocol integration (DTC + B2B).** OpenAI/Stripe ACP (Sept 2025); Google UCP (Jan 2026 with Walmart / Target / Shopify / Etsy / 20+ partners); Anthropic MCP for B2B tooling integration. DTC e-commerce clients now need Product / Offer / AggregateRating schema *plus* ACP integration for ChatGPT-resident commerce. B2B SaaS clients now need MCP tool definitions so agents can use the product programmatically. **The agency's deliverable is an agentic-commerce integration plan per applicable client** — schema mapping, payment flow, agent-readable product catalog.

**Axis 5.3 — Knowledge Panel + Google Business Profile + Bing Places optimization.** Google Knowledge Panel triggers on branded queries; AI engines often defer to the Knowledge Panel's entity attributes when synthesizing brand info. The Knowledge Panel is built from Wikidata + Crunchbase + structured-data + Google Business Profile + Wikipedia. The agency's deliverable: claim the Knowledge Panel where applicable; ensure GBP / Bing Places NAP consistency; submit corrections via the "Suggest an edit" flow. For local clients (Klinika, regional law firms, local accounting): Google Business Profile is the #1 surface for "best X in [city]" AI Overview citation.

**Axis 5.4 — Multilingual + international AEO.** `hreflang` tags; regional content variants; per-language schema.org `inLanguage`; per-language Wikidata + Wikipedia entries; per-language Reddit equivalents (PL: Wykop; DE: Reddit-de + StackExchange-de; FR: Twitch communities for AI). Polish clients need both English (for international AI engine queries about EU / Poland) and Polish content (for Polish-language queries — Perplexity / ChatGPT now route by user-locale to language-specific corpora). DWF and Klinika both fall here.

### Layer 6 — Monitoring + defense + measurement (5 axes, v1 ZERO coverage)

**Axis 6.1 — Cross-engine retrieval testing (citation share monitoring).** Profound (founded 2024, Index of AI-search visibility); Ahrefs Brand Radar (2025); SE Ranking's AI Visibility; Otterly.AI; AthenaHQ; Peec AI; SemRush AI Toolkit. Probe ChatGPT / Perplexity / Claude / Gemini / Google AI Mode / You.com / Bing Copilot weekly for category queries + branded queries; track citation rate, position in answer, sentiment, attribution accuracy. **The agency's deliverable: a per-client retrieval dashboard + weekly digest.** This is the AI-era equivalent of rank-tracking — Profound is the AI-era equivalent of SEMrush.

**Axis 6.2 — Engine selection + per-engine optimization.** Not all engines weight the same signals. ChatGPT favors Wikipedia + Reddit + named-authority sites. Perplexity favors freshness (12-18mo) + citation density (21+ for medical) + named-clinician / named-author bylines. Claude favors official docs + low-citation-fab → over-cites primary sources. Google AI Mode now pulls 38% from outside organic top-10 (down from 76%) + weights brand mentions r=0.664 heavily. Gemini in Google ecosystem deferential to Google Knowledge Graph. The agency's responsibility: per client + per query class, decide which engines matter most and prioritize accordingly. A Polish aesthetic-derm clinic optimizes differently for Perplexity-in-Polish than for ChatGPT-in-English.

**Axis 6.3 — Negative AEO defense / brand-reputation management.** Adversaries publishing pages that mis-attribute facts about the brand (Q4 of `geo-ai-failure-modes.md` — inverted-citation attack). Competitors publishing comparison pages designed to lose for the brand. AI engines repeating misinformation from old sources. The agency's deliverable: monitor third-party content for brand mentions; flag inversions; remediation playbook (corrections via outlet editors; Wikipedia correction; counter-evidence publication; legal escalation for libel). For YMYL clients (healthcare, legal, finance) this matters acutely — a mis-attributed regulatory claim about a fintech is a compliance issue, not just a SEO issue.

**Axis 6.4 — Author / founder bio engineering for E-E-A-T.** Per-author bio pages with credentials, dated history, named publications, linked sameAs to Wikidata / LinkedIn / Crunchbase / ORCID / academic-institution profile; Person schema; consistent name across all bio surfaces. For YMYL: clinician bios with bar / board / FAA-equivalent credentials; for AI-labs: researcher bios with arxiv author IDs + GitHub + publication history; for legal: attorney bios with jurisdiction + bar number + practice areas; for finance: compliance-officer bios with regulator-license disclosure. **This is the load-bearing E-E-A-T signal in 2026 — and the agency's deliverable is the bio architecture, not just the bio prose.**

**Axis 6.5 — Comparison-page warfare measurement (offensive + defensive).** Offensive: produce "X vs Competitor" pages where X is the client and the comparison is honest but framed to highlight client strengths in genuine head-to-heads. Defensive: monitor competitor "vs X" pages where the client is X; respond with rebuttal comparisons or schema-corrections; flag biased "best of" listicles. The Verge documented Google AI Mode catching vendor-authored "best of" lists where vendor is #1 — so self-puffery is self-defeating; but well-constructed comparison pages remain the highest-citation-rate form factor. **The deliverable is the comparison-target list + framing playbook + monitoring cadence.**

---

## §2 — What gets CUT from the old-school SEO playbook

The 2018-2022 SEO playbook contains ~20 tactics that contribute zero or negative value to 2026 AI citation. Cutting these is half the modernization. Concrete cuts (with reasoning):

**CUT 1 — Keyword density / exact-match repetition.** Aggarwal KDD 2024 explicitly documents keyword stuffing as a *negative* signal for AI citation. ChatGPT / Perplexity / Claude all penalize entity-name repetition past natural cadence. The 2018 "use the keyword 5-7 times in body content" rule actively hurts in 2026.

**CUT 2 — Exact-match anchor text in internal links.** Engines extract semantic relationships, not anchor-text matches. Descriptive anchor text ("read the comparison of CRM platforms for SMB") performs better than keyword-only anchor text ("best CRM"). Reduces over-optimization signals.

**CUT 3 — Mass directory submissions.** DMOZ-era tactic (DMOZ shut 2017). Most directory citations are de-weighted; relevant exceptions are vertical-specific (Avvo for legal, RealSelf for aesthetic-derm, G2/Capterra/TrustRadius for B2B SaaS, Crunchbase / Wikidata for tech). Don't submit to "1000 directories"; submit to the 3-7 vertical-relevant ones.

**CUT 4 — Generic listicles (templated AI-generated roundups).** Google's April 2026 update explicitly demoted "thin listicles, templated roundups, and AI-assisted content with no original input" by 25-35% in competitive niches. A "Top 10 X" page with no methodology, no named research, no first-party data is now actively de-cited.

**CUT 5 — Link-building outreach campaigns.** Backlinks correlate r=0.218 with AI Overview visibility vs brand mentions r=0.664 (Ahrefs 75K-brand 2025). The "cold outreach to 500 sites for guest posts" tactic is 3× less efficient than the equivalent PR effort or podcast appearance. Don't kill outreach entirely (real publication placements still help) — kill the cold-outreach-for-do-follow-link mechanic.

**CUT 6 — Schema stuffing without substance.** FAQPage schema on pages without organic FAQ load; Review schema on pages without visible reviews; HowTo schema on non-primary content. ALM Corp 2026: schema-without-substance teaches AI engines to distrust the domain. Google's March 2026 update narrowed schema eligibility.

**CUT 7 — AMP (Accelerated Mobile Pages).** Google deprioritized AMP for News in 2021; the broader AMP ecosystem is functionally end-of-life. Don't build new AMP. If you have AMP, migrate to standard mobile.

**CUT 8 — EMD (exact-match domain) plays.** "bestcrm.com" / "warsaw-derm.pl" domain games. Google's EMD update was 2012; AI engines weight even less. Branded domain > EMD in 2026.

**CUT 9 — Content velocity for its own sake.** "Publish 4 blog posts per week" goalposting. AI engines preferentially cite a smaller number of authoritative pages over high-velocity thin content. Google's Helpful Content sitewide classifier penalizes thin-content density. Better: publish 1-2 substantive pieces per month with original research / dated data / named-author byline.

**CUT 10 — Page-speed obsession beyond table stakes.** LCP < 2.5s is table stakes; INP < 200ms matters; CLS matters. Beyond that, Core Web Vitals optimization is diminishing returns for AI citation specifically. The 2019-2022 "shave 100ms off LCP" effort doesn't pay back in AI citation share.

**CUT 11 — Generic FAQ pages.** Google killed FAQ rich results May 7 2026. FAQ as standalone page is mostly dead; FAQ as appendix-to-article is still useful (3.2× AI Overview lift per Frase 2026); but the "build a 200-question FAQ page to capture long-tail traffic" tactic is over.

**CUT 12 — Pure-product-storytelling pages without functional attributes.** DTC "our story + lifestyle photography" pages don't get cited. AI engines preferentially cite product pages with named functional attributes (brand, model, material, capacity, use case, named technical specs).

**CUT 13 — Pillar pages with thin sub-section stubs.** "Hub bloat" — Google March/April 2026 demoted explicitly. A pillar with 30 sub-section stubs without real children hurts sitewide.

**CUT 14 — Auto-generated meta descriptions.** Most AI engines don't use meta descriptions for synthesis (they extract from body content). Don't spend cycles on meta-description-per-page; let the page lead with a BLUF answer instead.

**CUT 15 — Glossary bloat (hundreds of thin entries).** Demoted by Google March 2026 as "intermediary-content" / "topical bloat" sitewide classifier. Build 30-60 substantive glossary entries that answer real queries, not 800 thin entries to capture keyword variants.

**CUT 16 — Reciprocal linking schemes.** Same era as directory submissions, same end-of-life status.

**CUT 17 — PBN (Private Blog Network) tactics.** Black-hat; Google has been detecting and penalizing for years; AI engines actively de-rank.

**CUT 18 — Schema-only signals without on-page support.** "5-star rating schema on a page with no visible reviews is one of the fastest ways to erode AI trust" (Frase 2026). Schema mirrors on-page reality, never substitutes for it.

**CUT 19 — Targeting "featured snippet" position 0.** Featured snippets are being displaced by AI Overviews; the answer-snippet structure that earned position 0 still helps AI Overview citation, but the *target* changes from SERP feature to retrieval-shape.

**CUT 20 — Mass guest-post campaigns.** Per CUT 5 — don't kill guest posts entirely, but the "publish on 50 low-tier blogs for a do-follow link" mechanic is dead.

**Posture for what remains.** The 2018 SEO playbook had ~40 tactics; ~20 cut above; the surviving 20 are either renamed (technical-SEO baseline → AEO infrastructure) or modernized (content marketing → declarative-document-register content + comparison-page warfare). The replacement levers below are larger in total than the cuts.

---

## §3 — What gets ADDED as modern AEO levers (the 2026 replacement playbook)

15 modern levers that did not exist or were not load-bearing in 2018. Each replaces 1-3 cuts.

**ADD 1 — Declarative-document register (RETRIEVAL_DOCUMENT not BLOG_POST).** Volpini's framing. Lead with the declarative answer in 40-75 words. Each passage works standalone. Replaces CUT 1 + CUT 11 + CUT 14.

**ADD 2 — Comparison-page warfare.** "X vs Y" / "alternatives to Z" / "best of category" pages. 43.8% of all ChatGPT citations. Highest-leverage form factor for B2B SaaS / professional services / AI tooling. Replaces CUT 4 + CUT 20.

**ADD 3 — Brand-mention engineering (PR, podcast, founder visibility).** r=0.664 vs r=0.218 backlinks. Replaces CUT 5.

**ADD 4 — Reddit answer-shape engineering.** 20.8% top-50 ChatGPT citation share; #1 source in 6 of 7 verticals. Real-account engagement, not astroturfing. Replaces CUT 16 + CUT 17.

**ADD 5 — Wikipedia + Wikidata anchoring.** Wikipedia ChatGPT #1 source globally; Wikidata resolves entity confabulation. Replaces CUT 3 + portion of CUT 14.

**ADD 6 — llms.txt + llms-full.txt + per-page markdown siblings.** Pure 2026 tactic with zero 2018 equivalent. Mintlify-served by Anthropic / Cursor / Perplexity / Stripe. No cut to replace — net add.

**ADD 7 — Custom GPT / Claude Project / Gemini Gem / Perplexity Space publication.** Brand-as-distribution-channel-inside-AI-engine. Net add.

**ADD 8 — Agentic-commerce protocol integration (ACP / UCP / MCP).** For DTC / B2B SaaS. Net add.

**ADD 9 — Knowledge Panel + Wikidata Q-ID seeding.** Entity-anchor in AI engine KGs. Replaces portion of CUT 3 + CUT 18.

**ADD 10 — Per-engine retrieval testing dashboard (Profound / Ahrefs Brand Radar / Otterly).** AI-era replacement for SEMrush rank-tracking. Replaces portion of CUT 19.

**ADD 11 — Author / founder bio engineering for E-E-A-T.** Per-author Person schema + sameAs anchors + credentials + dated history. Replaces CUT 14 (auto-meta-descriptions) + amplifies surviving on-page E-E-A-T signals.

**ADD 12 — Original research / first-party data publication.** Yext 4.31× citation multiplier for first-party data vs aggregator listings. Replaces CUT 9 (velocity-for-velocity's-sake).

**ADD 13 — Speakable schema + voice-friendly answer structures.** Voice assistants (Alexa, Google Assistant, Siri-with-Apple-Intelligence) preferentially read Speakable-marked content; this is a low-cost net add for clients with voice-relevant content (recipes, how-tos, definitions).

**ADD 14 — Per-vertical community engagement maps (Stack Overflow, Indie Hackers, HN, RealSelf, Avvo).** Replaces CUT 16 (reciprocal linking) and complements ADD 4.

**ADD 15 — Negative-AEO defense + brand-reputation monitoring.** Per Axis 6.3 — monitor third-party mentions, flag inversions, remediation playbook. Net add (didn't exist as 2018 lever).

**Net change.** ~20 cuts → ~15 adds. The adds are larger in total weighted value because the top 3 adds (comparison-page warfare, brand-mention engineering, Reddit answer-shape) each individually outweigh most cuts.

---

## §4 — Vertical-specific adjustments per cohort

Per `geo-vertical-conventions.md`, the citation substrate diverges sharply across verticals. The comprehensive-scope deliverable must flex by cohort. What's invariant vs what flexes:

### Invariant across all verticals
- Declarative-document register (BLUF / Matryoshka Paragraph)
- Passage self-containment
- Entity stability + canonical naming
- Visible freshness signal (cadence varies)
- llms.txt + llms-full.txt + markdown siblings
- Schema.org Organization + entity-anchoring sameAs to Wikidata or equivalent
- Cross-engine retrieval testing
- Author / founder bio E-E-A-T construction

### B2B SaaS (Linear, Stripe, Notion, Anthropic API, gofreddy itself)
- **Heavy comparison-page warfare** (X vs Y, alternatives-to-Z, best-of-category). Highest-leverage form factor.
- **G2 / Capterra / TrustRadius profile maintenance** as the gatekeeper aggregator layer.
- **Custom GPT / Claude Project publication** with brand knowledge.
- **MCP tool definitions** for product to be agent-usable.
- **Integration / use-case pages** scoped to buyer persona.
- **Pricing page server-rendered HTML** with SoftwareApplication + Offer schema.
- **API docs as citation substrate** if the product has a developer surface.
- LIGHTER on author/founder bio; HEAVIER on customer-logos / case studies / G2-reviews.
- LIGHTER on YMYL gating; freshness cadence is quarter-level.

### AI labs / developer tools (Anthropic, Perplexity, Cursor, gofreddy's AI-adjacent clients)
- **Developer documentation IS the citation substrate.** Mintlify-style, llms-full.txt, per-page markdown siblings.
- **arxiv + GitHub + paperswithcode anchoring** for research publications.
- **Model cards + benchmark cards with reproducible methodology** + independent-eval cross-references (Epoch AI, Artificial Analysis, LMSYS).
- **Analyst Substack appearances** (Stratechery, Interconnects, Latent Space, Practical AI, State of AI).
- **Researcher / engineer founder visibility** (Twitter / X / LinkedIn / podcast).
- **Custom GPT / Claude Project publication** with technical knowledge.
- **Dated changelog / release notes** with breaking-change disclosure.
- LIGHTER on Reddit (engine-engineer users skew to HN / Lobsters / X); HEAVIER on Hacker News / Lobsters / GitHub Discussions / dev.to.

### Agency / consulting / professional services (gofreddy itself, plus consulting clients)
- **Head-to-head comparison editorial** on own domain (Xero playbook).
- **Named-author insight pieces** with partner / principal byline + dated + original analysis.
- **Case studies with named-client + named-outcome + dated period + verifiable metrics.**
- **Podcast appearances + thought-leadership Substacks** (this is the brand-mention play).
- **Per-vertical specialization signaling** (depth > breadth — "we serve X type of client" beats "we serve everyone").
- LIGHTER on schema markup beyond Organization + Person; HEAVIER on author bio + case study structure.

### Service business / local (Klinika, regional law firms, accounting / financial-planning local)
- **Google Business Profile + Bing Places NAP consistency** as the load-bearing local signal.
- **Local-pack SEO via reviews + photos + Q&A.**
- **Local-citation directories** (Yelp + vertical-specific: RealSelf for aesthetic, Avvo for legal, Zocdoc for medical, Healthgrades).
- **Service / procedure pages with named provider + credentials + before-after / case examples + local-context.**
- **Local language + cultural framing** (Klinika needs Polish + Warsaw-context for local queries).
- **Reviews schema + AggregateRating with off-domain validation** (RealSelf reviews surfaced).
- LIGHTER on national / global content; HEAVIER on hyperlocal entity-anchoring.

### Finance / fintech (US-primary fintech clients + Poland regulated-finance)
- **Regulator-aligned definitional explainer** with SEC / FINRA / CFPB / FCA / MAS / KNF (Polish) citation.
- **Risk-disclosure FAQ + per-jurisdiction scope notes.**
- **As-of-date stamps on rate / yield / fee data** (week-level cadence).
- **Compliance-officer / regulator-licensed author byline.**
- **NO promotional / product-marketing register on YMYL queries** — preferentially de-cited.
- **OCC SR 11-7 model-risk framework reference** if claiming AI-driven advisory.
- **Heavy disclaimer prose** is correct, not over-engineering.

### E-commerce / DTC (US-primary DTC clients)
- **Product / Offer / AggregateRating / Review schema** — operationally mandatory.
- **ACP / UCP integration** for ChatGPT / Google AI Mode resident commerce.
- **UGC review surfacing** (Reddit + YouTube + niche-community) — 21-24% of Perplexity product citations.
- **Current-week pricing + availability stamps.**
- **Named functional attributes in product title** ("Brand Model — Material — Capacity — Use Case").
- **Comparison pages with UGC review pull-quotes.**
- LIGHTER on long-form editorial; HEAVIER on schema density + UGC surfacing + recency cadence.

### Healthcare / aesthetic medicine (Klinika + future medical clients)
- **YMYL gating: clinician-authored + medical-reviewer byline + last-medically-reviewed date + named guideline citation (NICE / USPSTF / AAD / WHO).**
- **Local pack capture** for procedure-comparison queries (RealSelf + Healthgrades + Google Maps).
- **Procedure-comparison glossary** clinically grounded.
- **Before-after gallery with consent + HIPAA-compliant.**
- **NAP consistency across GBP + RealSelf + Healthgrades + practice site.**
- **Polish + English** content for Klinika specifically (Perplexity routes by locale).

### Legal services (DWF + future legal clients)
- **Jurisdiction-scoped FAQ** + author-attributed long-form explainer.
- **Statute / case / regulator citation** required per claim.
- **Attorney byline + bar number where applicable.**
- **Last-reviewed date** with statute-version reference.
- **Disclaimer prose operationally mandatory.**
- **Practice-area-specific hub pages** with jurisdictional sub-pages.
- **Avvo / Martindale / Chambers / Legal 500 directory profiles** maintained.

---

## §5 — Proposed comprehensive multi-part deliverable architecture

### The unit: one "GEO Strategic Plan" artifact per client per cycle

Don't fan out into 12 separate files. Don't compress to one page. Run a single coherent multi-section artifact that the autoresearch evolution loop iterates on as a whole — the same way CI produces one executive-briefing artifact, not 8 separate sections each scored separately.

### Size envelope

**Total: 12,000-18,000 words across 8-12 named sections.** Larger than v1's single-page; smaller than 12 separate artifacts. Coherent enough to read end-to-end; granular enough that each section has clear local quality.

**Per-section budgets:**

- §A — Current-state AEO audit (per axis): 1,500-2,500 words
- §B — Cut/Reduce/Add prescription: 800-1,200 words
- §C — Page-level optimization recommendations + sample sections: 1,500-2,500 words
- §D — Site-architecture recommendations (entity graph, hub-and-spoke, internal linking): 800-1,500 words
- §E — Off-page signal plan (Reddit + Wikipedia + Wikidata + Quora + community map + PR / podcast targets): 1,500-2,500 words
- §F — Comparison-page warfare plan (target list + framing + cadence): 800-1,500 words
- §G — Distribution + AI-engine-native plan (Custom GPT + agentic-commerce + Knowledge Panel + multilingual): 800-1,200 words
- §H — Cross-engine retrieval testing plan + per-engine optimization tactics: 600-1,000 words
- §I — Author / founder bio engineering recommendations: 400-800 words
- §J — Negative-AEO defense + brand-reputation monitoring: 400-800 words
- §K — 30/60/90 execution roadmap with named owners + measurable outcomes: 600-1,000 words
- §L — Appendices: schema markup snippets ready to deploy; llms.txt template; sample Reddit-answer-shape; sample Wikipedia edit; sample comparison page outline: 1,500-2,500 words

**Total ceiling 18,000 words** is wide enough to be comprehensive but tight enough that evolution iteration is tractable (~$15-25 per generation at frontier inner-loop rates per `geo-ai-failure-modes.md` cost notes).

### Why ONE artifact, not 12

1. **Loop coherence.** The evolution loop optimizes whatever is in front of it. If the artifact is 12 separate files, the loop optimizes each in isolation and produces local-optima drift (one file recommends Reddit-heavy; another recommends Reddit-light; the strategic plan is inconsistent).
2. **Single rubric.** The 5 GEO criteria in v1 + GEO-6 (engine-side citation resilience) can score one rich artifact across all sections. Separate artifacts would require per-artifact rubrics, multiplying maintenance.
3. **CI precedent.** CI executive-briefing-shape spec locked at ~12,000 words across 9 sections. Same architecture; vertical findings differ. Pattern proven.
4. **Reader workflow.** A founder reading the plan reads it end-to-end once; revisits sections by name. Multi-file fragments require navigation overhead the reader doesn't want.

### Where the boundary draws between GEO lane and adjacent lanes

- **GEO lane owns:** §A audit, §B cut/add prescription, §C page-level, §D site-architecture *recommendations* (not implementation), §E off-page signal plan, §F comparison-page warfare, §G distribution, §H retrieval testing plan, §I bio engineering, §J defense, §K roadmap, §L appendices.
- **`site_engine` lane (separate) implements** the site-architecture recommendations as actual page builds. The GEO plan specifies what to build; site_engine builds it.
- **`monitoring` lane runs** the live retrieval-testing dashboard from §H (weekly probes against ChatGPT / Perplexity / Claude / Gemini / etc.) — GEO plan specifies the dashboard design; monitoring runs it operationally.
- **`marketing_audit` lane (existing) handles** competitive intelligence inputs that feed §A and §F.
- **A new lane `off_page_signal_engineering` could split out §E** if Reddit / Wikipedia / podcast outreach becomes a regular cadence operation rather than a one-time plan deliverable. Defer that decision until 2-3 clients are running the comprehensive scope.

### Per-fixture variability

The `geo_format` per-fixture enum in v1 still applies — but at the *page* level within §C. The strategic plan as a whole is one artifact per client; the page examples inside §C are typed by `geo_format`. This preserves v1's form-factor routing while letting the strategic plan be coherent.

---

## §6 — Evolution-loop architecture considerations

How does a 12,000-18,000-word multi-section artifact iterate inside autoresearch?

### Mutation surface

The plan has ~12 sections × ~1,200 words average = ~14,000 words. The evolution-loop mutator (per `meta.md` per lane) can mutate (a) section content, (b) section order, (c) section emphasis, (d) the recommendations within each section. The mutation surface is large but bounded.

**Recommendation: mutation targets sections, not the whole plan.** Each generation, the meta-agent picks 1-3 sections to mutate; the rest carry forward. This keeps generation-to-generation diff small + interpretable + auditable. CI follows this pattern; GEO should too.

### Scoring granularity

The judge scores the whole plan against 5 criteria (GEO-1..GEO-5) + GEO-6 (citation resilience). Each criterion looks at the whole artifact, not section-by-section. Per-section scoring would fragment the judge and re-introduce the multi-artifact problem.

**Per-section rubric anchors are fine in score-1 anchors** — e.g., "§E off-page signal plan names ≥3 subreddits with specific answer-shape recommendations" — but the score is one number per criterion across the whole artifact.

### Evolution-loop cost envelope

Per `geo-ai-failure-modes.md` Δcost estimates: GEO-6 adds ~$0.06/judgment × 3-model panel × 5-30 fixtures × 50 generations = $45-450 per lane-run. Plus structural-gate checks (URL HEAD, quote-grep): ~$15-100 per lane-run. Plus inner-loop generation cost for a 12-18K-word artifact: per token rates at codex/gpt-5.5 inner: ~$0.50-1.50 per artifact × 50 generations × 5-10 fixtures = $125-750 per lane-run.

**Total per-run envelope: $185-1,300.** Higher than v1's single-page envelope (~$80-200) but materially cheaper than the alternative of running 12 separate artifacts ($1,500-3,000) or running a single page that misses 70% of the value (incalculable).

### Fixture set implication

To score across 22 axes, the fixture set needs to span verticals + page-types + off-page-substrate. Per `geo-vertical-conventions.md` Recommendation 5: fixture set should include at least one of each load-bearing vertical (legal / healthcare / B2B SaaS / fintech / AI-lab / DTC / professional-services). For the comprehensive scope, fixtures need to additionally span:

- 1-2 fixtures requiring substantial off-page signal plans (Reddit-heavy DTC; Wikipedia-heavy enterprise B2B).
- 1-2 fixtures requiring comparison-page warfare (B2B SaaS category prompt).
- 1-2 fixtures requiring local + multilingual (Klinika Polish + English; regional law firm).
- 1-2 fixtures requiring Custom GPT / Claude Project distribution (AI-lab; B2B SaaS).
- 1-2 fixtures requiring agentic-commerce integration (DTC).

**Recommended fixture count: 8-12.** Above v1's 5-fixture target but below the 30-fixture upper bound — enough to validate the comprehensive scope without overwhelming the loop budget.

### Promotion gate

Per `judge-design-guide.md` §9: pointwise digest + pairwise gate. With a 12,000-18,000-word artifact, the pairwise comparison cost scales — the judge has to read both candidate and head at the gate. Mitigation: pairwise gate runs only on sections that mutated this generation, not the whole artifact. Sections that didn't mutate carry forward by reference. Reduces pairwise cost by ~70%.

### Goodhart-collapse risks specific to the multi-section artifact

1. **Section-rotation slot-fill.** Workflow learns that mutating §E (off-page signal plan) earns +0.3 reward (the section is new + judges weight novelty); rotates through sections gaming the novelty signal. **Mitigation:** judge prose explicitly weights *outcome* (does the plan actually move citation share?), not *novelty per section*.
2. **Long-document length bloat.** Workflow learns to write 18,000-word artifacts because longer artifacts have more passages to score against GEO-3 (passage self-containment). **Mitigation:** structural-gate caps total length at 20,000 words; per-section caps; word-count audit in CI.
3. **Section-decoupling.** Workflow learns to write each section to maximize its own score without cross-section coherence; the plan becomes 12 disjoint mini-plans. **Mitigation:** GEO-1 (BLUF / declarative) applies to the whole plan — the plan's executive summary must be coherent; if it isn't, GEO-1 = 0.

---

## §7 — SOTA exemplar inventory across the full surface

Real practitioners + companies + agencies operating across the comprehensive scope (not just narrow-axis):

### Full-stack AEO agencies (2026 SOTA)

- **Profound (tryprofound.com).** AI-search visibility platform + the agency's own content strategy = full-stack. Founded 2024 by Tejas Manohar (founder of Hightouch); product is a Profound Index measuring citation share across ChatGPT / Perplexity / Claude / Gemini / Google AI Mode. They publish their own methodology + blog content following all the modern levers (declarative-lead + named-clinician / named-author / dated content + Reddit visibility + comparison-page warfare).
- **Wordlift (wordlift.io).** Andrea Volpini's agency + product. SOTA on entity-graph + schema.org + Wikidata anchoring + RETRIEVAL_DOCUMENT register. Volpini coined "Matryoshka Paragraph" and "fan-out query optimization." Wordlift product injects schema.org markup programmatically; Wordlift blog is the canonical reference for the declarative-document register approach.
- **Kalicube (kalicube.com).** Jason Barnard. SOTA on entity-anchoring + Knowledge Panel optimization. Barnard's "Brand SERP" and "AEO" coinages predate the broader 2024 explosion. Kalicube Pro product tracks Knowledge Panel composition + entity-attribute drift.
- **Animalz (animalz.co).** Long-form B2B SaaS content + comparison-page warfare + content-as-strategy. The Animalz blog is the practitioner-canonical reference for declarative-document register applied to B2B SaaS. Animalz's own "AEO Glossary" is the working glossary-entry form factor example.
- **Backlinko (backlinko.com — Brian Dean → Semrush).** Long-tail SEO turned AEO. Backlinko's data-driven research posts are Yext 4.31× first-party-data multiplier examples. Now part of Semrush; Semrush AI Toolkit is the rank-tracking equivalent for AI engines.
- **Ahrefs blog (ahrefs.com/blog).** Tim Soulo + team. Ahrefs publishes large-scale citation studies (the 75K-brand study; the 26,283-URL ChatGPT analysis; the 17M-citation freshness study). Ahrefs Brand Radar product (launched 2025) is the AI Overview / ChatGPT citation tracking tool. Ahrefs blog applies its own methodology — declarative-lead + first-party-data + named-author bylines.

### Vertical-specialist agencies (vertical-deep)

- **Lexicon Legal Content (legal vertical).** lexiconlegalcontent.com. SOTA on jurisdiction-scoped legal content + attorney-byline E-E-A-T + statute-citation discipline. They publish their own "Generative Engine Optimization Strategy Guide for Law Firms" which exemplifies the legal-vertical citation substrate.
- **DoctorRank / MaximusLabs (healthcare vertical).** doctorrank.com / maximuslabs.ai. SOTA on healthcare YMYL E-E-A-T + clinical-guideline citation + medical-reviewer byline.
- **Stridec (healthcare-adjacent).** stridec.com. AEO for healthcare with clinician-authored content.
- **5W PR (professional services / accounting).** 5wpr.com. Published the 2026 AI Visibility Index for accounting/finance — documents the Xero / NetSuite / Sage Intacct comparison-page warfare playbook.
- **upGrowth (fintech + healthcare).** upgrowth.in. Published the 2026 Fintech CMO + Healthcare YMYL playbooks.
- **Discovered Labs (B2B SaaS AEO).** discoveredlabs.com. Specialist B2B SaaS AEO agency.
- **Beomniscient / Omniscient Digital (B2B SaaS).** beomniscient.com. Published the G2 Acquisition + AI citation share research.

### Real-world full-surface practitioners (clients, not agencies)

- **Stripe (developer-tools + B2B SaaS).** Full-stack execution: Mintlify-style docs with llms-full.txt; comparison-page warfare (Stripe vs Adyen / Braintree / Square); brand-mention engineering via TechCrunch / The Information / a16z podcast / Stratechery placements; founder visibility (Patrick + John Collison); Custom GPT publication; agentic-commerce protocol (ACP co-author with OpenAI); Knowledge Panel + Wikidata anchored.
- **Anthropic (AI-lab).** Mintlify docs with llms-full.txt; published model cards with reproducible benchmarks; arxiv / Anthropic blog substrate; Stratechery + Interconnects + Latent Space + Practical AI appearances; founder visibility (Dario Amodei interviews); Custom GPT + Claude Projects distribution; Knowledge Panel anchored.
- **Xero (accounting SaaS).** SOTA exemplar for comparison-page warfare. Deliberately published dozens of Xero-vs-QuickBooks pages over years; dominates "QuickBooks alternative" queries; named in 5W PR 2026 AI Visibility Index as the leading example.
- **NetSuite + Sage Intacct (mid-market ERP).** Both run head-to-head comparison editorial on own domains; both dominate mid-market ERP AI queries; both published in the 5W PR 2026 Index.
- **Linear (B2B SaaS).** Comparison pages (Linear vs Jira / Asana / Notion); named-customer logos (OpenAI, Cash App, Vercel); founder visibility (Karri Saarinen on podcasts + Twitter); developer-doc substrate; Custom GPT published.
- **HubSpot (B2B SaaS).** Inventor of the pillar-and-cluster model; SOTA on hub-and-spoke topology; comparison-page warfare (HubSpot vs Salesforce / Marketo / Pardot); founder visibility (Dharmesh Shah + Brian Halligan); Knowledge Panel anchored.
- **Stripe (mentioned above, deserves second listing — full-stack).**
- **Cursor (AI-IDE).** llms-full.txt + per-page markdown siblings; developer-doc substrate via Mintlify; comparison content (Cursor vs VS Code / Copilot / Windsurf); founder + team visibility on HN + Twitter + Latent Space podcast.

### Specialist tooling / monitoring vendors (the AI-era SEMrush layer)

- **Profound** (already named).
- **Ahrefs Brand Radar.**
- **Semrush AI Toolkit.**
- **Otterly.AI.**
- **AthenaHQ.**
- **Peec AI.**
- **SE Ranking AI Visibility.**

### Open-source / standards

- **llms.txt** — Jeremy Howard (Answer.AI) standard, Sept 2024. https://llmstxt.org.
- **Schema.org** — Google / Microsoft / Yahoo / Yandex consortium. https://schema.org.
- **Wikidata** — Wikimedia Foundation. https://www.wikidata.org.
- **Open Graph Protocol** — Facebook (still relevant for image-card rendering when AI engines surface citations).

---

## §8 — Open questions for JR

1. **Adopt the comprehensive scope as v2 of the GEO lane, or sibling-fork the new axes into separate lanes?** The lane can absorb the expansion via section-rotation mutation + per-fixture form-factor enum + GEO-6 (citation resilience). Or §E (off-page signal) can sibling-fork into a new `off_page_signal_engineering` lane; §H (retrieval testing) can fold into `monitoring`. Adjudication depends on cadence: if §E + §H run weekly/monthly per client, they're operational lanes, not strategic-plan lanes; if they run quarterly as part of the strategic plan refresh, they belong in GEO.

2. **Fixture set expansion: from 5 to 8-12?** Comprehensive scope needs more vertical + axis coverage. Cost of fixture-build: ~1-2 days per fixture. Trade-off: locking GEO criteria via redundancy check needs ≥5 diverse fixtures; comprehensive scope needs ≥8 to score across 22 axes meaningfully. Build the additional 3-7 fixtures incrementally as new-vertical clients onboard?

3. **Per-fixture `geo_artifact` enum: page-level vs plan-level?** v1's `geo_format` enum is page-level (definition / how-to / etc.). Comprehensive scope adds plan-level: should there be a parallel `geo_artifact` enum at the *fixture* level — {`single_page`, `strategic_plan`, `audit_only`, `comparison_target_list`, `off_page_signal_plan`}? Or is the strategic-plan-as-default with per-section emphasis enough?

4. **Boundary with `site_engine` on hub-and-spoke topology + sitemap.** GEO produces recommendations; site_engine implements pages. Concrete handoff: GEO's §D outputs a topology spec (named pillars + cluster lists + internal-link graph); site_engine consumes that spec + builds pages. Document the contract.

5. **Boundary with `monitoring` on cross-engine retrieval dashboard.** GEO plan specifies the dashboard design + per-engine query list + cadence; monitoring runs it operationally. Same contract pattern as above. Should monitoring lane absorb a "retrieval probe" task type, or stay focused on competitive / brand-mention monitoring?

6. **Polish-language coverage as first-class or as overlay?** Klinika + DWF Poland both need Polish + English. Per-language fixtures? Per-language section in the strategic plan? Or treat as a single multilingual axis with per-client weighting? Recommend: treat as Axis 5.4 (multilingual) with section emphasis per client need; do not bifurcate the spec.

7. **Custom GPT / Claude Project / Gemini Gem publication as a deliverable the agency builds vs recommends?** Building the Custom GPT requires access to client's domain knowledge + ongoing maintenance. Is gofreddy in the business of building + maintaining client Custom GPTs, or just recommending what to build? Affects whether §G is a deliverable spec or an implementation spec.

8. **Negative-AEO defense: full lane, sub-section, or escalation to monitoring?** Axis 6.3 monitors third-party content for brand inversions. Could be a sub-section of the strategic plan (recommend monitoring cadence + remediation playbook); could be an operational task for monitoring lane (run the queries); could be a full standalone lane. Recommend: §J of the strategic plan specifies the design; monitoring lane runs it operationally.

9. **Agentic-commerce protocol integration (ACP / UCP / MCP): which clients need it now vs later?** For DTC e-commerce clients: now. For B2B SaaS with developer surface: now (MCP tool definitions). For service-business / professional-services / agency clients: probably not. Build per-client decision criteria into §G.

10. **Quote-grep cosine-similarity threshold tuning + URL HEAD check failure mode.** Per `geo-ai-failure-modes.md`: quote-grep at 0.85 cosine; URL HEAD within 5s. For the comprehensive-scope plan with 50-100 cited URLs across all sections, URL HEAD becomes the long-pole structural-gate check. Mitigation: parallelize + cache + rate-limit-aware. Confirm the structural-gate budget can absorb this.

11. **Engine-rotation cadence for the panel.** Per `judge-design-guide.md` §8: rotate within-family minor versions every ~5 generations. With a comprehensive-scope artifact, the rotation cost is higher (each rotation re-runs the panel on all fixtures). Stick with the 5-generation cadence, or extend to 10?

12. **The first-cohort overfit watch trigger.** Per `geo-vertical-conventions.md` Recommendation 5 + `geo-artifact-taxonomy.md` Open Question 7: any new-vertical fixture should prompt re-validation of GEO-1..GEO-5 anchor adequacy. For the comprehensive-scope expansion, the trigger should also apply to any new axis being added (e.g., when agentic-commerce-protocol integration becomes a primary deliverable for first DTC client). Confirm same trigger applies.

---

## Appendix A — Crosswalk: where each comprehensive-scope axis lives in the deliverable artifact

| # | Axis | Layer | Deliverable section | v1 coverage | Adjacent-lane handoff |
|---|---|---|---|---|---|
| 1.1 | BLUF / declarative lead | Page | §C | YES (GEO-1) | — |
| 1.2 | Evidence injection | Page | §C | YES (GEO-2) | — |
| 1.3 | Passage self-containment | Page | §C | YES (GEO-3) | — |
| 1.4 | Entity stability | Page | §C + §I | YES (GEO-4) | — |
| 1.5 | Format-intent match | Page | §C | YES (GEO-5) | — |
| 2.1 | Entity graph + KG anchoring | Site | §D + §L | NO | site_engine builds |
| 2.2 | Hub-and-spoke topology | Site | §D | NO | site_engine builds |
| 2.3 | Internal linking + breadcrumbs | Site | §D | NO | site_engine builds |
| 2.4 | Canonical / sitemap / robots | Site | §D + §L | partial | site_engine implements |
| 3.1 | Schema.org markup mix | Infra | §C + §L | partial | site_engine implements |
| 3.2 | llms.txt + llms-full.txt | Infra | §L | NO | site_engine ships |
| 3.3 | Server-rendered HTML + CWV | Infra | §D | partial | site_engine implements |
| 4.1 | Reddit answer-shape | Off-page | §E | NO | possibly off_page lane |
| 4.2 | Wikipedia + Wikidata | Off-page | §E | NO | possibly off_page lane |
| 4.3 | Quora + Stack + community | Off-page | §E | NO | possibly off_page lane |
| 4.4 | PR + podcast + founder vis | Off-page | §E | NO | possibly off_page lane |
| 4.5 | Citation building (.gov / .edu) | Off-page | §E | NO | possibly off_page lane |
| 5.1 | Custom GPT / Claude Project | Distribution | §G | NO | new build / operate |
| 5.2 | Agentic-commerce (ACP/UCP/MCP) | Distribution | §G | NO | engineering + GEO |
| 5.3 | Knowledge Panel + GBP | Distribution | §G | NO | GEO + operations |
| 5.4 | Multilingual + international | Distribution | §C + §G | partial | site_engine + GEO |
| 6.1 | Cross-engine retrieval testing | Monitor | §H | NO | monitoring runs |
| 6.2 | Engine selection / per-engine | Monitor | §H | NO | monitoring runs |
| 6.3 | Negative-AEO defense | Defense | §J | NO | monitoring runs |
| 6.4 | Author / founder bio E-E-A-T | E-E-A-T | §I | partial | GEO + content |
| 6.5 | Comparison-page warfare | Offensive | §F + §C | partial | GEO produces |

---

## Appendix B — 30/60/90 execution roadmap template (the §K spec)

**Day 0-30 (foundation + diagnostics):**
- §A current-state audit completed (all 22 axes scored)
- §B cut-list + add-list with reasoning
- Structural fixes: server-rendered HTML; canonical URL tags; robots.txt + sitemap.xml; Schema.org Organization + Person; llms.txt + llms-full.txt drafted
- Author / founder bio page(s) drafted with credentials + sameAs anchors
- Wikidata Q-ID claim or seed
- Cross-engine retrieval baseline (Profound / Ahrefs Brand Radar / manual probes against ChatGPT / Perplexity / Claude / Gemini / Google AI Mode)

**Day 31-60 (page + site execution):**
- §C page-level optimization on top 5-10 commercial pages (format-intent match per geo_format; BLUF; evidence; passage self-containment)
- §D site-architecture: pillar-and-cluster topology shipped for primary category; internal linking audit complete
- §F comparison-page warfare: 3-5 "X vs Y" / alternatives pages shipped on highest-value comparison targets
- §I bio pages shipped with full E-E-A-T architecture
- §G distribution: Custom GPT / Claude Project drafted + published if applicable

**Day 61-90 (off-page + distribution + monitoring):**
- §E off-page signal plan executed: 5-15 Reddit engagement actions; Wikipedia / Wikidata corrections submitted; 2-3 podcast appearance pitches sent; PR placement targets actively pursued
- §G Knowledge Panel + GBP claims complete; agentic-commerce integration shipped if applicable
- §H cross-engine retrieval dashboard live with weekly digest
- §J negative-AEO monitoring live with remediation playbook
- §K iteration plan: which axes scored highest impact in Days 1-90; double-down recommendations for Days 91-180

---

## Appendix C — Brief notes on what the v1 spec gets *right* and should retain

The v1 GEO spec (`docs/handoffs/2026-05-18-judge-design-step1-geo.md`) is correct on:

- **Form-factor per-fixture routing** via `geo_format` enum (page-level form-factor variety is real).
- **Five outcome criteria + GEO-6 documented-exception for citation resilience** (the criterion-count discipline holds; GEO-6 earns the breach per design-guide §5 v2.1).
- **Structural-gate for AI-failure-mode checks** (Q1-Q5 of `geo-ai-failure-modes.md` correctly routed deterministic).
- **Dual-audience framing** (human researcher + AI engine; per `geo-dual-audience-tension.md`).
- **First-cohort overfit watch** (per `geo-vertical-conventions.md` Recommendation 5).

The comprehensive scope expands the spec's *artifact scope* and *axis coverage*, not its rubric architecture. The 5+1 criterion design + structural-gate split + cross-family panel + pointwise digest + pairwise gate all carry forward. What changes: the artifact gets bigger (single page → multi-section strategic plan); the per-fixture enum gets richer (page form-factor → plan + page combined); the deliverable axes get wider (5 page-level axes → 22 full-surface axes); the off-page + distribution + monitoring + defense axes become first-class.

---

## Citations + sources

This deliverable synthesizes from prior research already in the project — see frontmatter siblings. Primary external sources reinforced in this pass:

**Comparison-page warfare + listicle dominance:**
- Ahrefs ChatGPT 26,283-URL citation analysis (750 search terms) — 43.8% citation share to listicles.
- 5W PR "Accounting & Finance Software AI Visibility Index 2026" — Xero / NetSuite / Sage Intacct head-to-head editorial pattern.

**Brand-mention vs backlink correlation:**
- Ahrefs 75K-brand mention-correlation study (Patel Long 2025) — brand mentions r=0.664; backlinks r=0.218; AI Overview visibility.

**Reddit citation share:**
- Foundation 2026 — Reddit 20.8% top-50 ChatGPT citation share; #1 source in 6 of 7 verticals.
- ALM Corp + various 2026 — 21-24% of Perplexity product-query citations.

**Wikipedia citation share:**
- Profound / Ahrefs / multiple — Wikipedia 7.8% of all ChatGPT citations globally; 47.9% of top-10 share.

**llms.txt standard:**
- Jeremy Howard / Answer.AI Sept 2024 — https://llmstxt.org.
- Mintlify documentation platform — practitioner-canonical implementation (Anthropic, Cursor, Perplexity, Stripe).

**Engine-specific:**
- Skywork 2025 — Claude with search 94% citation accuracy.
- Perplexity Deep Research 2025 — 37% citation-fabrication rate.
- Ahrefs Q1 2026 AI Overview retrospective — 38% citations from organic top-10 (down from 76%).

**Schema.org + structured data:**
- Frase.io 2026 — 3.2× AI Overview rate for FAQ-schema pages.
- ALM Corp 2026 — 89% of e-commerce sites implement Product schema incorrectly.
- Similarweb 2026 — CRM market-leader case study (23% vs 78% citation rate from JS vs HTML pricing).

**Custom GPT / Claude Project distribution:**
- OpenAI GPT Store metrics (Q1 2026 public stats).
- Anthropic Claude Projects (1M+ shared-project users, Q1 2026).

**Agentic-commerce protocols:**
- OpenAI/Stripe Agentic Commerce Protocol (ACP) — live in ChatGPT since Sept 2025.
- Google Universal Commerce Protocol (UCP) — announced Jan 2026 with Walmart, Target, Shopify, Etsy + 20 partners.

**SOTA vendor agencies:**
- Profound (tryprofound.com), Wordlift (wordlift.io), Kalicube (kalicube.com), Animalz (animalz.co), Backlinko/Semrush, Ahrefs blog — all named in §7 with URLs.

**Internal project context:**
- `docs/handoffs/2026-05-18-judge-design-step1-geo.md` v0 — current spec being expanded.
- `docs/research/2026-05-18-geo-vertical-conventions.md` — per-vertical citation substrate.
- `docs/research/2026-05-18-geo-artifact-taxonomy.md` — 10 form-factor taxonomy.
- `docs/research/2026-05-18-geo-ai-failure-modes.md` — 5 LLM-specific failure surfaces.
- `docs/research/2026-05-18-geo-dual-audience-tension.md` — human + engine reader split.
- `docs/research/2026-05-15-judges-domain-geo.md` — generalist GEO synthesis (Aggarwal / Volpini / Shepard / Profound).
- `docs/rubrics/judge-design-guide.md` v2.1 — judge-architecture guide this deliverable conforms to.
