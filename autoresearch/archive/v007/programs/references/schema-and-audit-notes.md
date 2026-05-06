# Schema Markup + SEO Audit Notes — Infrastructure Detail

Sources (Corey Haines marketingskills repo):
- `schema-markup` + `references/schema-examples.md`: https://github.com/coreyhaines31/marketingskills/tree/main/skills/schema-markup
- `seo-audit` + refs: https://github.com/coreyhaines31/marketingskills/tree/main/skills/seo-audit

Consult when `freddy detect` or `freddy seo` output needs interpretation, or when recommending schema changes as part of optimization.

---

## Schema detection caveat — do NOT trust static fetch alone

`<script type="application/ld+json">` blocks are frequently injected by client-side JavaScript (Yoast, RankMath, AIOSEO, Next.js, Gatsby, Nuxt). A static `curl` or server-side fetch strips the JS-rendered DOM and will falsely report "no schema found."

**Before concluding a page has no schema:**
1. Check `freddy detect` rendered-DOM output, not raw HTML.
2. Cross-check via Google Rich Results Test: `https://search.google.com/test/rich-results`.
3. Cross-check via Schema.org validator: `https://validator.schema.org/`.
4. In-browser DevTools: `document.querySelectorAll('script[type="application/ld+json"]')`.

Reporting "no schema found" from a static scrape is an unforced error that zeroes GEO-8 (technical fixes are real).

---

## `@graph` pattern for multi-type schema on one page

The current CQ-10 rule ("exactly one schema block per page") is correct but the format inside that block should be a `@graph` array combining multiple related types via `@id` references. This is Google's preferred pattern:

```json
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://example.com/#org",
      "name": "Example",
      "url": "https://example.com",
      "sameAs": ["https://twitter.com/example", "https://linkedin.com/company/example"]
    },
    {
      "@type": "WebSite",
      "@id": "https://example.com/#site",
      "url": "https://example.com",
      "publisher": {"@id": "https://example.com/#org"},
      "potentialAction": {
        "@type": "SearchAction",
        "target": "https://example.com/search?q={query}",
        "query-input": "required name=query"
      }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://example.com/pricing/#breadcrumb",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com"},
        {"@type": "ListItem", "position": 2, "name": "Pricing", "item": "https://example.com/pricing/"}
      ]
    }
  ]
}
</script>
```

This is ONE script block (satisfies CQ-10) but carries multiple typed entities that reference each other via `@id`. Use this pattern for homepage + any page needing more than one schema type.

---

## Per-type required-property matrix

AI search validators and Google Rich Results Test reject schema missing required properties. Target these minimums per type:

| @type | Required | Recommended |
|-------|----------|-------------|
| Article / BlogPosting | `headline`, `image`, `datePublished`, `author` | `dateModified`, `publisher`, `mainEntityOfPage` |
| Product | `name`, `image`, `offers` | `description`, `brand`, `sku`, `aggregateRating`, `review` |
| SoftwareApplication | `name`, `operatingSystem`, `applicationCategory`, `offers` | `aggregateRating`, `author`, `screenshot` |
| FAQPage | `mainEntity` (array of Question → acceptedAnswer) | — |
| HowTo | `name`, `step` (array of HowToStep) | `totalTime`, `tool`, `supply`, `image` |
| BreadcrumbList | `itemListElement` (array with position, name, item) | — |
| Organization | `name`, `url` | `logo`, `sameAs`, `contactPoint` |
| WebSite | `name`, `url` | `potentialAction` (SearchAction for sitelinks search) |
| Review | `itemReviewed`, `author`, `reviewRating` | `datePublished`, `publisher` |

**Validation workflow:** after injecting schema, run both `https://search.google.com/test/rich-results` AND `https://validator.schema.org/`. Rich Results Test checks Google eligibility; Schema.org validator checks spec compliance. Both passing = GEO-8 clear.

---

## SoftwareApplication vs Product (SaaS clients)

SaaS clients should use **SoftwareApplication**, not Product. The difference is material: SoftwareApplication carries `applicationCategory`, `operatingSystem`, and SaaS-appropriate `offers`. Product is physical-goods-first and misses the SaaS-relevant signals.

```json
{
  "@type": "SoftwareApplication",
  "name": "Example SaaS",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web",
  "offers": {
    "@type": "Offer",
    "price": "29.00",
    "priceCurrency": "USD",
    "priceValidUntil": "2027-12-31"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "1247"
  }
}
```

---

## WebSite + SearchAction (homepage sitelinks search box)

Homepage-only pattern. Triggers Google's sitelinks search box when the brand is searched. Absent from most GEO sessions' recommendations.

```json
{
  "@type": "WebSite",
  "url": "https://example.com/",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://example.com/search?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
```

---

## Title tag discipline (complements CQ-1)

CQ-1 covers answer-first intro; the `<title>` tag has its own rules AI search parses separately:

- **50-60 characters** is the display sweet spot. Over 60 = Google truncates.
- Primary keyword **near the beginning** of the tag.
- **No leading brand name** — Google often prepends it anyway. `Pricing – Example` reads cleaner than `Example - Pricing`.
- Each tag **unique site-wide** — duplicate titles across pages collapse in Google's index.

---

## Core Web Vitals thresholds (Copilot sub-2s rule made specific)

The existing platform guide says "sub-2s load time" for Copilot. Concrete thresholds:

- **LCP** (Largest Contentful Paint) < 2.5s
- **INP** (Interaction to Next Paint) < 200ms
- **CLS** (Cumulative Layout Shift) < 0.1

Run via PageSpeed Insights (already available through `freddy detect --full`) and report the three metrics specifically, not a summary score. A client hitting 2.8s LCP needs different fixes than one hitting 400ms INP.

---

## Indexation pitfalls checklist (for `freddy detect` interpretation)

When auditing a client's infrastructure, check explicitly:

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `noindex` on important pages | Meta robots `noindex` or X-Robots-Tag header | Remove; audit every important URL |
| Canonical loops | A → B canonical → A | Pick one canonical; break the loop |
| Canonical to wrong URL | Product page canonical → homepage | Canonical should be self or the deliberate cluster head |
| Redirect chains | 301 → 301 → 301 → 200 | Collapse to single 301 |
| Soft 404s | 200 status with "not found" body | Return real 404 or redirect |
| Parameter URLs indexed | `?utm_source=...` duplicates | Canonical to clean URL or block via robots.txt |
| Mobile/desktop version split | Separate m.example.com | Responsive design; single canonical URL |
| Pagination without rel | `?page=2` duplicates | Self-canonical + strong internal linking |

Report findings against this list; CQ-14 (robots.txt) already covers bot access but not these on-page indexation signals.

---

## robots.txt × sitemap interactions

Known gotchas when client's robots.txt and sitemap.xml disagree:
- URL in sitemap.xml but blocked in robots.txt: Google reports "indexed though blocked" warnings; AI bots can't crawl. Remove from sitemap.
- Sitemap referenced in robots.txt but 404: breaks discovery. Absolute URL required (`Sitemap: https://example.com/sitemap.xml`).
- Sitemap over 50,000 URLs or 50MB: split into sitemap index. Aging CMS often exceeds without warning.

---

## LocalBusiness schema (for clients with physical locations)

SaaS clients rarely need this, but clients with offices, stores, clinics, restaurants, or physical service areas ship LocalBusiness. Triggers map-pack / local-pack placements on Google.

```json
{
  "@type": "LocalBusiness",
  "name": "Example Co",
  "image": "https://example.com/storefront.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "San Francisco",
    "addressRegion": "CA",
    "postalCode": "94107",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "37.7749",
    "longitude": "-122.4194"
  },
  "telephone": "+1-555-555-5555",
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "08:00",
      "closes": "18:00"
    }
  ],
  "priceRange": "$$"
}
```

## Event schema (for webinars, launches, conferences)

Relevant when the client runs live or virtual events. Can be cited by AI search for "{category} events" or "{topic} webinar" queries.

```json
{
  "@type": "Event",
  "name": "Annual Marketing Conference",
  "startDate": "2026-06-15T09:00:00-07:00",
  "endDate": "2026-06-15T17:00:00-07:00",
  "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": {
    "@type": "VirtualLocation",
    "url": "https://example.com/conference"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/tickets",
    "price": "199",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "validFrom": "2026-01-01"
  },
  "organizer": {
    "@type": "Organization",
    "name": "Example Co",
    "url": "https://example.com"
  }
}
```

---

## E-E-A-T signals (the four weighted heavily by Google AI Overviews)

E-E-A-T = Experience + Expertise + Authoritativeness + Trustworthiness. Each has distinct signals to plant on a page. AI Overviews weight E-E-A-T via author + site + content signals combined.

### Experience (first-hand, demonstrated)
- First-hand experience demonstrated in prose ("we ran this for 18 months," "I talked to 47 users")
- Original insights or data (not summaries of third-party studies)
- Real examples and case studies with named clients/users

### Expertise (subject-matter credibility)
- Author credentials visible on the page (bio + role + organization)
- Accurate, specific, detailed information — vague generalities signal absence
- Properly sourced claims with linkable citations

### Authoritativeness (recognition in the space)
- Cited by other authoritative sources
- Industry credentials or titles referenced ("Principal Engineer at X," "Author of Y")
- Contributor to known publications, conferences, or open source projects

### Trustworthiness (site + page level)
- Accurate information cross-checks against other sources
- Transparent about who runs the business (about page, team page)
- Contact information visible (not just a form)
- Privacy policy + terms + HTTPS
- No deceptive patterns (hidden subscriptions, bait-and-switch pricing)

**Principle:** an unsigned article on an unsecured site with stock-photo author avatars fails E-E-A-T regardless of content quality. Audit the signals before optimizing copy.

---

## Keyword cannibalization audit

Two or more pages on the same client site targeting the same primary keyword compete with each other in both traditional search and AI search. AI engines often cite the weaker of the two — or neither, splitting the citation signal.

**Detection:**
- Search `site:client.com "target keyword"` — if multiple pages return for the same exact phrase, check if they're intentionally differentiated.
- Check the client's existing GSC data (if available) for pages where the same query has multiple URLs in search-query performance reports.
- Review title tags + H1s across the site for near-duplicates.

**Fix pattern:**
- Consolidate the two pages into one authoritative version (301 redirect the weaker).
- OR differentiate target keywords explicitly (Good-Better-Best structured) and set cross-canonical links.
- OR move one page to a sub-keyword / long-tail variant and link it from the primary.

Cannibalization is especially common on client sites with long histories of SEO content (10+ posts on slight variations of one topic).

---

## Image optimization (often overlooked; affects Copilot sub-2s + Google AI Overviews)

Common miss: image optimization zeroed on pages that otherwise pass every GEO check.

| Check | Signal |
|-------|--------|
| Descriptive file names | `golden-gate-bridge-fog.jpg` not `IMG_4892.jpg` |
| Alt text on every image | Empty `alt=""` permitted only for truly decorative; everything else needs text |
| Alt text describes image | "Accountant reviewing spreadsheet" not "accountant.jpg" |
| Compressed file sizes | <200KB for hero images, <100KB for inline |
| Modern formats | WebP / AVIF with fallback; avoid PNG for photos |
| Lazy loading | `loading="lazy"` below the fold |
| Responsive images | `<picture>` or `srcset` for multiple resolutions |

Report image issues alongside `freddy detect --full` output. A 4MB hero image will blow past LCP 2.5s no matter how good the content is.

---

## Common issues by client site type

Different site types have different characteristic failure modes. Focus audit effort accordingly:

### SaaS / product sites
- Thin product pages with marketing fluff, no specific claims (GEO CQ-7 quantified outcomes fails)
- Gated authoritative content (AI bots can't crawl — see CQ-14)
- Hidden pricing ("contact sales" — see CQ-13)
- Docs on a separate subdomain that doesn't pass equity (fix via site-architecture subfolder rule)
- Missing SoftwareApplication schema — using Product instead (see CQ-16)

### E-commerce
- Thin category pages with only product grids
- Missing Product / AggregateRating schema
- Duplicate product pages for color/size variants (cannibalization)
- Session-param URLs polluting index

### Content / blog sites
- Undated posts lose to dated (content becomes stale-looking even when current)
- Missing author attribution / bio (E-E-A-T failure)
- Category pages used as landing pages without unique content
- Tag pages that mirror category pages (cannibalization)

### Local business
- Missing LocalBusiness schema or wrong NAP (name / address / phone) across listings
- No location-specific content on location pages (swapped city name only)
- Google Business Profile disconnected from site

---

## Quick validation URLs (bookmark these in the session)

- Rich Results Test: `https://search.google.com/test/rich-results`
- Schema.org validator: `https://validator.schema.org/`
- Mobile-Friendly Test: `https://search.google.com/test/mobile-friendly`
- PageSpeed Insights: `https://pagespeed.web.dev/`
- robots.txt tester: `https://www.google.com/webmasters/tools/robots-testing-tool` (requires GSC access)
