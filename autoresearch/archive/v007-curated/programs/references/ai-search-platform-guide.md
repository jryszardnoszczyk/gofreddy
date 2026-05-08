# AI Search Platform Guide — Per-Platform Citation Levers

Source: adapted from Corey Haines's `ai-seo` skill (content-patterns + platform-ranking-factors references).
URL: https://github.com/coreyhaines31/marketingskills/tree/main/skills/ai-seo
Cited studies throughout: Princeton GEO (KDD 2024), SE Ranking 129K-domain analysis, ZipTie 400K-page content-answer fit analysis.

Use this file as a reference when choosing per-page optimization moves. The quantified impacts are directional — real boost depends on baseline and query category.

---

## Platform-by-platform priorities

### Google AI Overviews (~45% of Google searches)
- **Schema markup is the single biggest lever** (+30-40% visibility). Article, FAQPage, HowTo, Product.
- Authoritative citations inside body copy correlate with +132% visibility; authoritative (non-salesy) tone adds another +89%.
- Only ~15% of AI Overview sources overlap with traditional top-10. A page that can't rank on page 1 can still get cited if structured and sourced well.
- E-E-A-T weighted heavily. Named authors + credentials + topical clusters with internal linking.

### ChatGPT (Bing-indexed + training)
- **Content-answer fit ≈ 55% of citation likelihood** (ZipTie, 400K pages). Writing in ChatGPT's own answer format beats domain authority (12%) and on-page structure (14%).
- Freshness: content updated within 30 days gets cited ~3.2x more often.
- Domain authority still matters (~40% of signal per SE Ranking). Sites with 350K+ referring domains avg 8.4 citations/response vs 6 at 91-96 trust band.
- Wikipedia = 7.8% of all ChatGPT citations. Reddit = 1.8%. Forbes = 1.1%. Third-party presence is load-bearing.

### Perplexity (own index + Google + rerank)
- **FAQPage JSON-LD is specifically privileged.** Implement on any Q&A content.
- Publicly accessible PDFs (whitepapers, research reports) are prioritized. Ungate authoritative PDFs where possible.
- Publishing velocity > keyword targeting. Time-decay algorithm evaluates new content quickly.
- Self-contained, atomic paragraphs extract cleanly. Curated authoritative domains (Amazon, GitHub, academic) get ranking boosts.

### Microsoft Copilot (Bing index)
- Sub-2-second load time is a hard threshold.
- LinkedIn and GitHub mentions provide ranking boosts other platforms don't offer.
- Submit via Bing Webmaster Tools + IndexNow for fast indexing.
- Explicit, extractable entity definitions win.

### Claude (Brave Search backend)
- Extremely selective — low citation rate, high bar. Rewards factual density: specific numbers, named sources, dated statistics.
- Verify presence at search.brave.com before assuming Claude can find the page.
- Allow `ClaudeBot` and `anthropic-ai` user agents in robots.txt.

---

## Princeton GEO study — full ranked lever table

Empirical visibility boost per content modification (KDD 2024, Perplexity.ai baseline):

| Method | Boost | Notes |
|--------|------:|-------|
| Cite sources | +40% | Authoritative references with links |
| Add statistics | +37% | Specific numbers with sources (largest single tactical lever) |
| Add quotations | +30% | Named expert + title |
| Authoritative tone | +25% | Demonstrated expertise, not salesy |
| Improve clarity | +20% | Simplify complex concepts |
| Technical terms | +18% | Domain-specific vocabulary |
| Unique vocabulary | +15% | Word diversity |
| Fluency optimization | +15-30% | Readability and flow |
| Keyword stuffing | **-10%** | Actively penalized in AI search |

**Best combination:** Fluency + Statistics = maximum boost.
**Low-ranking sites benefit most:** up to +115% visibility when these modifications combine.

---

## Content block patterns (use per query type)

| Query pattern | Block type | Keep-it-right |
|---------------|------------|---------------|
| "What is X?" | Definition block | 1-sentence definition, then 1-2 sentences of context. ≤60 words total. |
| "How to X" | Step block | 5-7 numbered steps, each with a named action. |
| "X vs Y" | Comparison table | Named criteria rows. Include where the competitor wins. Bottom-line recommendation. |
| "Is X worth it?" | Pros/cons | Balanced. Verdict sentence with conditional recommendation. |
| FAQ pages | FAQ block | Natural question phrasing. Direct answer first sentence. 50-100 words per answer. |
| "Best X for Y" | Listicle | Numbered items. Selection criteria stated up front. |

### Answer passage rules
- Lead every section with a direct answer. Do not bury it.
- 40-60 words is the sweet spot for snippet extraction.
- One idea per paragraph. Self-contained — readable without the section above it.
- Tables beat prose for comparison. Numbered lists beat paragraphs for process.

### Additional citable block patterns

Beyond the query-to-block table above, these are higher-density citation patterns worth planting explicitly on target pages:

**Statistic Citation Block** (raises AI citation rates +15-30% when sources included):
> [Claim statement]. According to [Source/Organization], [specific statistic with number + timeframe]. [Context for why this matters].

**Expert Quote Block** (+30% citation likelihood per Princeton):
> "[Direct quote from expert]," says [Expert Name], [Title/Role] at [Organization]. [1 sentence of context].

**Authoritative Claim Block** (structured for easy extraction):
> [Topic] [is/has/requires/involves] [clear, specific claim]. [Source] [confirms/reports/found] that [supporting evidence]. This [means/explains/suggests] [implication or action].

**Self-Contained Answer Block** (quotable, standalone, no surrounding context needed):
> **[Topic/Question]**: [Complete answer in 2-3 sentences with specific details, numbers, or examples. Readable on its own without the heading context.]

**Evidence Sandwich Block** (claim → bulleted evidence → conclusion):
> [Opening claim statement].
>
> Evidence supporting this includes:
> - [Data point 1 with source]
> - [Data point 2 with source]
> - [Data point 3 with source]
>
> [Concluding statement connecting evidence to actionable insight].

### Domain-specific authority signals

AI search weights authority signals differently by domain. When the target page is in one of these verticals, plant the signals listed:

| Domain | Authority signals to include |
|--------|------------------------------|
| Technology | Technical precision + correct terminology, version numbers + dates for software/tools, official documentation references, code examples where relevant |
| Health / Medical | Peer-reviewed studies with publication details, expert credentials (MD, RN, PhD), study limitations + context, "last reviewed" dates |
| Financial | Regulatory bodies (SEC, FTC), specific numbers + timeframes, educational-not-advice disclaimers, recognized financial institutions cited |
| Legal | Specific laws/statutes/regulations, jurisdiction clearly named, professional disclaimers, "consult a lawyer" framing |
| Business / Marketing | Case studies with measurable results, industry research + reports, percentage changes + timeframes, recognized thought-leader quotes |

Match signals to the client's domain before drafting — a health page without expert credentials or study citations will under-perform regardless of structural optimization.

### Voice search optimization

For pages targeting voice-assistant query patterns (Siri, Alexa, Google Assistant, Copilot voice):

- **Question-format headings:** "What is…", "How do I…", "Where can I find…", "Why does…", "When should I…", "Who is…".
- **Answer length under 30 words** for voice-optimized blocks — voice assistants truncate hard.
- Natural, conversational language — avoid jargon unless targeting expert audience.
- Include local context where relevant (voice queries often imply location).

---

## Machine-readable files for AI agents

AI agents increasingly evaluate products programmatically before a human visits the site. Opaque pricing and JS-rendered specs get filtered out of agent-mediated buying journeys.

### `/pricing.md` (or `.txt`)

Structured, parseable pricing at site root. Example:

```markdown
# Pricing — {Product}

## Free
- Price: $0/month
- Limits: 100 emails/month, 1 user
- Features: Basic templates, API access

## Pro
- Price: $29/month (annual) | $35/month (monthly)
- Limits: 10,000 emails/month, 5 users
- Features: Custom domains, analytics, priority support

## Enterprise
- Price: Custom — contact sales@example.com
```

Rules: consistent units, specific numeric limits (not just feature names), cumulative tier contents, linked from sitemap and main pricing page.

### `/llms.txt`

See llmstxt.org. A short context file pointing AI systems to what the product is, who it's for, and links to key pages (including `/pricing.md`).

---

## robots.txt — AI bot allowlist

Block any of these and the corresponding platform cannot cite you:

```
User-agent: GPTBot           # ChatGPT search
User-agent: ChatGPT-User     # ChatGPT browsing
User-agent: PerplexityBot    # Perplexity
User-agent: ClaudeBot        # Claude
User-agent: anthropic-ai     # Claude (alt UA)
User-agent: Google-Extended  # Gemini + AI Overviews
User-agent: Bingbot          # Copilot
Allow: /
```

**Training vs search:** `GPTBot` covers both for OpenAI — cannot separate. `CCBot` (Common Crawl) is training-only and safe to block without losing AI search citations.

---

## Citation-share of content formats

Ranked by share of AI citations observed (order-of-magnitude, not precise):

| Format | Share | Why |
|--------|------:|-----|
| Comparison articles | ~33% | Structured, high-intent, balanced |
| Definitive guides | ~15% | Comprehensive, authoritative |
| Original research/data | ~12% | Unique citable statistics |
| Best-of / listicles | ~10% | Clear structure, entity-rich |
| Product pages (with specifics) | ~10% | AI can extract concrete claims |
| Opinion/analysis | ~10% | Expert perspective, quotable |
| How-to guides | ~8% | Step-by-step structure |

Underperformers: generic undated posts, thin product pages, gated content, PDF-only resources on AI-blocked hosts.

---

## How to apply in a GEO session

1. **Before writing:** decide which platform matters most for this client's query set. Optimize accordingly — a comparison page ships FAQPage schema for Perplexity, a product page ships `/pricing.md` for agents, a how-to ships HowTo schema for Google AI Overviews.
2. **Per page:** pick the block pattern matching the target query type. Enforce the 40-60 word answer rule on the first paragraph (CQ-1).
3. **Authority pass:** add ≥1 cited source, ≥1 statistic with source, ≥1 named quotation where natural. Check tone is authoritative not salesy.
4. **Infra pass:** verify robots.txt allowlist, `/pricing.md` exists for SaaS clients, schema validates.
5. **Third-party pass:** note if the client has a Wikipedia entry, Reddit presence, or review-site profile — off-site presence is the 6.5x citation multiplier.
