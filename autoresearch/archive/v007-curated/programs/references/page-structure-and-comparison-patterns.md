# Page Structure & Comparison Patterns — Templates That Get Cited

Sources (Corey Haines marketingskills repo):
- `competitor-alternatives` + refs: https://github.com/coreyhaines31/marketingskills/tree/main/skills/competitor-alternatives
- `site-architecture` + refs: https://github.com/coreyhaines31/marketingskills/tree/main/skills/site-architecture
- `programmatic-seo` + refs: https://github.com/coreyhaines31/marketingskills/tree/main/skills/programmatic-seo
- `content-strategy` + refs: https://github.com/coreyhaines31/marketingskills/tree/main/skills/content-strategy
- `copywriting/references/copy-frameworks.md`

Comparison articles are ~33% of all AI citations (the single largest format share — see `ai-search-platform-guide.md`). This reference gives concrete templates and URL/IA patterns for GEO sessions whose optimization target is a comparison, alternative, or programmatic page pattern.

---

## Page-pattern taxonomy

Classify each target page against these 12 programmatic-SEO playbooks before optimizing. Each has a different primary citation format.

| Playbook | URL pattern | Citation format |
|----------|-------------|-----------------|
| Integrations | `/integrations/{product}/` | HowTo schema, setup steps |
| Locations | `/locations/{city}/` | Locally-grounded data (not just swapped city names) |
| Personas | `/for/{persona}/` | Testimonials from that segment |
| Comparisons | `/compare/{a}-vs-{b}/` or `/vs/{competitor}/` | FAQPage schema + per-row winner column |
| Glossary | `/glossary/{term}/` | Definition block, ≤60 words |
| Templates | `/templates/{category}/{slug}/` | Downloadable artifact + usage guide |
| Curation | `/best/{category}/` | Listicle block, numbered |
| Conversions | `/convert/{from}-to-{to}/` | Step block |
| Examples | `/examples/{use-case}/` | Worked example + outcome |
| Directory | `/directory/{filter}/` | ItemList schema |
| Profiles | `/profiles/{slug}/` | Person or Organization schema |
| Translations | `/{lang}/{path}/` | hreflang + localized data |

**Rule:** if the client has thin variations (city names swapped in, templates that differ only by `{name}` token), those need `noindex` or differentiated data — otherwise Google's Helpful Content demotes the cluster. Aligns with CQ-11 (page-specific FAQs; minimum 3 for thin pages).

---

## Four comparison-page formats

All four are indexed by AI search and the URL pattern signals intent. Pick deliberately.

### 1. `/alternatives/{competitor}` — singular alternative
- **Search intent:** actively switching from a specific competitor.
- **Page structure:** pain validation → you-as-alternative TL;DR → detailed comparison → who should switch (and who shouldn't) → migration path → switcher social proof → CTA.
- **AI-citation hook:** the honest "who shouldn't switch" section is what gets cited in Perplexity / ChatGPT "alternatives to X" queries (see GEO CQ-3 — honest competitive positioning).

### 2. `/alternatives/{competitor}-alternatives` — plural
- **Search intent:** researching options, earlier in journey.
- **Page structure:** common pain points → evaluation criteria framework → list of 4-7 real alternatives (you first, but real others included) → summary table → detailed breakdown → recommendation by use case → CTA.
- **Rule:** include 4-7 real alternatives. Being genuinely helpful builds trust AND ranks better. A plural page with only your product and two straw competitors is a zero on CQ-3.

### 3. `/vs/{competitor}` or `/compare/{you}-vs-{competitor}` — direct head-to-head
- **Search intent:** directly comparing you to competitor.
- **Page structure:** TL;DR summary (2-3 sentences) → at-a-glance table → detailed comparison by category (Features / Pricing / Support / Ease / Integrations) → who {you} is best for → who {competitor} is best for (honest) → switcher testimonials → migration → CTA.
- The **"who {competitor} is best for"** section is CQ-3 made concrete. This is the hardest line to write; it's also the one that gets cited.

### 4. `/compare/{a}-vs-{b}` — competitor-vs-competitor
- **Search intent:** user comparing two competitors, not you directly.
- **Page structure:** overview both products → comparison by category → who each is best for → the third option (introduce yourself) → three-way table → CTA.
- **Why this works:** captures search traffic where you aren't even named; positions you as knowledgeable. Especially high leverage for under-$10B categories where user doesn't yet know all options.

---

## Competitor data YAML schema (one file per competitor)

When GEO optimization includes a comparison target, keep a single source of truth per competitor. Update propagates to all comparison pages. Schema from Corey's content-architecture reference:

```yaml
name: Competitor Name
website: https://example.com
tagline: "Their positioning tagline"
founded: 2015
positioning:
  primary_use_case: "..."
  target_audience: "..."
  market_position: "leader | challenger | emerging"
pricing:
  model: per-seat | per-usage | per-feature | flat | hybrid
  free_tier: true | false
  starter_price: 29
  business_price: 99
  enterprise_price: custom
features:
  - name: "..."
    rating: 1-5
    notes: "..."
strengths: ["...", "..."]
weaknesses: ["...", "..."]
best_for: "specific ICP"
not_ideal_for: "specific anti-ICP"
common_complaints: ["...", "..."]     # from G2 1-3 star reviews
migration_from:
  difficulty: easy | moderate | complex
  data_export: formats available
  what_transfers: ["...", "..."]
  what_doesnt: ["...", "..."]
  time_estimate: "2-3 hours"
```

The `best_for`, `not_ideal_for`, and `common_complaints` fields are what CQ-3 (honest comparison) and CQ-4 (comparison table) are evaluated against. GEO's existing `competitors/visibility.json` doesn't carry these; add them.

---

## TL;DR summary pattern (CQ-3 execution)

The single hardest line in a comparison page. Use this template:

> **[Competitor] excels at [specific strength] but struggles with [specific weakness]. [You] is built for [specific focus], offering [unique differentiator]. Choose [Competitor] if [case — name the ICP]. Choose [You] if [case — name the ICP].**

Example:
> Intercom excels at human-agent chat support but is expensive for lean teams. Crisp is built for support-led product teams, offering shared inbox + Slack-native routing. Choose Intercom if you have a full support org and need enterprise SLAs. Choose Crisp if you're a PLG SaaS under 50 employees and support is a founder-engineer function.

---

## Paragraph-comparison rule

Tables alone are insufficient. For each major dimension (Features, Pricing, Support, Ease, Integrations), write a paragraph explaining the differences and when each matters. AI engines extract prose passages more readily than cell contents, and the paragraph is where the CQ-3 honesty actually lives ("cell values" can be gamed; a paragraph explaining "their tiering rewards volume-heavy teams; ours rewards feature-heavy teams" is harder to fake).

---

## Pricing-comparison section

Ship all three:
1. **Line-item table:** tier × competitor with price + key limits per cell.
2. **What's included narrative:** what's *actually* in each tier (features, not just names).
3. **Total-cost-of-ownership paragraph:** worked calculation for a 10-person team over 1 year across tiers, including overage costs and hidden charges (SSO tax, etc.).

This is the format AI agents parse cleanly — see CQ-13 (`/pricing.md`).

---

## Migration section structure

For any "alternative" or "vs" page, include:
- What transfers (data types, integrations, config).
- What needs reconfiguration.
- Migration support offered (docs, CSM, migration team).
- 1-2 quotes from real switchers.

Maps to ad-creative-analysis-framework mechanisms: activates **status-quo-bias reversal** ("one-click import"), **endowment** (existing data preserved), and **zero-price** (migration support free).

---

## URL structure rules (load-bearing for indexation)

- Lowercase only.
- Hyphens, not underscores (Google treats underscores as word-joiners, hyphens as separators).
- Reflect hierarchy: `/alternatives/intercom/` not `/intercom-alternatives/` when part of a cluster.
- Consistent trailing slash (pick one, enforce).
- **No dates in evergreen URLs**: `/blog/post-title` not `/blog/2024/01/15/post-title` — dates decay the URL's perceived freshness.
- No IDs: `/products/slack-integration` not `/products/id=472`.
- No query-param content: URLs should be canonical paths.
- **Subfolders, not subdomains:** `site.com/templates/resume/` consolidates authority; `templates.site.com/resume/` splits it.

---

## 3-click rule + no-orphan-pages

- Critical pages must be reachable within 3 clicks from the homepage. Buried pages lose indexation and citation.
- Every optimized page must have ≥1 internal link pointing to it (not just outbound). Orphans don't recrawl.
- Hub-and-spoke model: hub is comprehensive (category page), every spoke links back, spokes cross-link laterally. Operationalizes GEO's CQ-6 (cross-page coherence) and CQ-9 (different primary competitive angle) with an internal-linking counterpart.
- Header nav carries the strongest internal PageRank — if a page isn't in header or footer, don't expect compounding citation boost even with good content.

---

## Footer internal-linking pattern for comparison content

Sitewide footer columns:
- "{Product} vs" — N links to head-to-head pages
- "Alternatives to" — N links to singular-alternative pages
- "Compare" — N links to A-vs-B pages

Passes equity across all comparison content uniformly. For a client with 20+ comparison pages, this is the distribution primitive that gets them to critical mass.

---

## Headline formula taxonomy (for hero sections)

Five formulas, pick per page type. All should be answer-first (CQ-1) and within 40-60 words for the immediate subhead.

| Formula | Shape | Example |
|---------|-------|---------|
| Outcome-focused | "{outcome} without {pain}" | "Ship production Rails in 15 minutes without managing servers" |
| Problem-focused | "Never {event} again" | "Never lose a lead to stale CRM data again" |
| Audience-focused | "{feature} for {audience}" | "Error monitoring for teams that ship daily" |
| Differentiation | "The {category} that {differentiator}" | "The CRM that reads your email so you don't have to" |
| Proof-focused | "[N] [people] use [product] to [outcome]" | "10,000 dev teams use Linear to ship faster" |

---

## Testimonial quality gate

Testimonials need all three or they're filler:
1. **Specific result** (number or named outcome).
2. **Before/after context.**
3. **Role + company + photo.**

"Great product!" / "Love it!" / "Highly recommend!" — these count as zero on AI extraction signal (no extractable claim). One good testimonial beats ten generic ones.

---

## Searchable vs shareable classification (CQ-9 calibration)

Before writing, tag each planned page:
- **Searchable:** captures existing demand. Optimize for keyword match, answer-first, schema-dense. Comparison pages, glossary, how-to.
- **Shareable:** creates demand. Lead with novel insight / proprietary data / counterintuitive take. Original research, opinion, manifesto.

A session optimizing three pages **should not pick all three from the same bucket** — diversifying across searchable and shareable is how a client's GEO footprint grows beyond saturated query categories. Directly operationalizes CQ-9 (different primary competitive angle).

---

## Buyer-stage query mapping (upgrades CI analyses that touch GEO keyword gaps)

When analyzing a competitor's content coverage, tag each of their pages by buyer stage:

| Stage | Query patterns |
|-------|----------------|
| Awareness | "what is", "how to", "guide to" |
| Consideration | "best", "top", "vs", "alternatives" |
| Decision | "pricing", "reviews", "demo" |
| Implementation | "templates", "tutorial", "setup" |

A competitor saturating Consideration queries but absent on Implementation is leaving the retention loop to the client to win. Cross-lane insight — tag this in competitive briefs too.

---

## Data defensibility hierarchy (CQ-5 reinforcement)

When claiming a citability moat (CQ-5), the claim's durability depends on data type:

1. **Proprietary** (client-internal metrics, customer-panel data) — strongest moat.
2. **Product-derived** (usage telemetry, aggregate outputs from client's product) — strong.
3. **User-generated** (reviews, forum posts on client's platform) — moderate.
4. **Licensed** (paid data sets, named sources) — moderate.
5. **Public** (government, scraped) — weakest; anyone can match.

A CQ-5 moat claim anchored in category 4-5 is vulnerable. Flag this during evaluation.
