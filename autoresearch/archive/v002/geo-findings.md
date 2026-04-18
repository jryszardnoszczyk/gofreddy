<!-- Bootstrap findings from validated session traces. -->

# Global GEO Findings

## Confirmed

### [CONTENT] FAQ + FAQPage JSON-LD improves RAG score across all page types
**Evidence:** Semrush session: /pricing/ RAG 0.05→0.62, /features/ 0.05→0.62, /competitor-website-analysis-tools/ 0.10→0.65. Pattern held across thin AND content-rich pages.
**Detail:** Self-contained answers with at least one concrete detail (number, comparison, named competitor) per answer are required. Shallow answers without specifics don't move the score.

### [CONTENT] Structural optimization on JS-blocked pricing pages can pass grounding
**Evidence:** Semrush /pricing/ page (159 words static HTML) can be optimized with FAQ + HOWTO blocks using plan tier names and feature differences visible in static HTML.
**Detail:** Ground claims only in pages/{slug}.json content. Do not invent dollar amounts. Use plan/tier names, feature lists, and plan-selection guidance. Mark dynamic content as [DYNAMIC: verify at URL].

### [PROCESS] Competitive rate-limiting wastes wall time without benefit
**Evidence:** All visibility queries rate-limited on ChatGPT/Perplexity/Gemini in every semrush session attempted. No competitive data obtained despite significant wait time across multiple runs.
**Detail:** In EFFICIENCY MODE, run max 1 visibility query. Fail fast on rate-limit. Skip competitive phase rather than waiting for multiple timeouts.

## Observations

### [CONTENT] Pricing pages are highest-priority evaluation fixtures
**Evidence:** The canary fixture is geo-semrush-pricing. If the pricing page is not optimized, grounding_passed=false and score=0.0 regardless of other page quality.
**Detail:** Always include the pricing page in the top-3 optimization queue even with thin content.
