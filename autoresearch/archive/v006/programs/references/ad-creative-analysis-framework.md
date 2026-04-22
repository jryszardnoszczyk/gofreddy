# Ad Creative Analysis Framework — Competitor Ad Decoding

Source: adapted from Corey Haines's `ad-creative` and `marketing-psychology` skills.
URL: https://github.com/coreyhaines31/marketingskills/tree/main/skills/ad-creative
URL: https://github.com/coreyhaines31/marketingskills/tree/main/skills/marketing-psychology

Use this as a reference when reading competitor ads gathered from Foreplay / Adyntel / search-content. The point is to name what each ad is doing so the brief can describe competitor strategy in analytical vocabulary rather than "they run a lot of ads."

---

## Step 1 — Classify the angle

Every ad operates on one of these motivational angles. Tag each competitor ad with its angle (multiple tags allowed for hybrids).

| Angle | Shape of the hook | Example |
|-------|-------------------|---------|
| Pain point | "Stop [bad thing]" | "Stop building reports by hand" |
| Outcome | "[Result] in [timeframe]" | "Ship code 3x faster" |
| Social proof | "Join [N] [tribe]" | "10,000+ teams trust X" |
| Curiosity | "The [thing] top [role] use" | "The secret top CMOs use" |
| Comparison | "Unlike X, we [Y]" | "Unlike Salesforce, no setup" |
| Urgency | "Limited time / ending soon" | "First 500 get it free" |
| Identity | "Built for [specific role/type]" | "Made for solo founders" |
| Contrarian | "Why [common belief] is wrong" | "Why daily standups don't work" |

Observable signal: angle distribution across a competitor's ad set tells you who they're actually targeting.

## Step 2 — Name the psychological mechanism

Pair the angle tag with the cognitive bias the ad is trying to activate. A competitor running 40 ads with the same bias is telegraphing their core conversion bet.

| Mechanism | Description | Marker words |
|-----------|-------------|--------------|
| Social proof / bandwagon | Popularity as quality signal | "10,000+ teams", "trusted by", logo bar |
| Scarcity / urgency | Limited availability raises value | "Only 50 left", "Ends Friday" |
| Loss aversion | Fear of missing out / losing what you have | "Don't lose ground to competitors" |
| Anchoring | Set a reference point to make price feel smaller | "Normally $X, yours for $Y" |
| Authority | Credentials borrow trust | "Ex-Google", "Featured in WSJ" |
| Reciprocity | Give value first to trigger obligation | Free tool, free audit, free template |
| Commitment/consistency | Small yes primes bigger yes | Email capture → trial → paid |
| Endowment | Once it feels "owned," it's hard to give up | Long free trial, freemium |
| Zero-price | Free is psychologically distinct from $1 | "Free forever", "No credit card" |
| Status quo bias reversal | Remove switching friction | "One-click import from X" |
| Identity / unity | Tribe membership | "Built by marketers for marketers" |
| Hyperbolic discounting | Immediate > future benefit | "Save time today" not "ROI in 6 months" |
| Paradox of choice reduction | Fewer options, clearer pick | Three tiers, "best for most" highlighted |

## Step 3 — Decode structural patterns

Pattern spotting across a competitor's ad set reveals strategy:

- **Burst vs sustain vs drip-burst vs dump-and-coast** — use `started_at` timestamps in the ad data to classify deployment cadence. A burst of 30 ads over 2 weeks followed by silence reads very differently from sustained 2-per-week publishing.
- **Launch-phase reading of bursts.** A burst that coincides with a Product Hunt listing, a waitlist-open announcement, a changelog entry, or a dashboard "Beta" sticker is a GTM-phase commitment (Internal → Alpha → Beta → Early Access → Full Launch), not sustained performance testing. Before classifying a burst as performance-testing, check for waitlist pages, "Coming soon" landing pages, and recent launch signals. Source: Corey Haines `launch-strategy` (Five-Phase Launch Approach).
- **Headline-heavy vs creative-heavy** — copy-only ads signal direct-response testing; video/image-heavy ads signal brand investment.
- **Angle concentration vs angle spread** — a competitor running 10 variations of one angle is testing execution; 10 different angles is testing positioning.
- **Funnel-stage mix via copy inference.** Ads with cold-audience copy (broad problem framing, strong social proof lead) vs. retargeting copy (specific objection-handling, urgency, cart-abandon language) tell you how a competitor allocates between prospecting and conversion. A competitor running 100% cold-prospecting copy is likely under-investing in mid-funnel; a competitor running heavy retargeting without brand/prospecting is drafting on someone else's demand-generation. Source: Corey Haines `paid-ads` (Retargeting — Funnel-Based Approach).
- **Creative-testing maturity signal.** Same ad set with 10 headline variations + 1 creative = direct-response testing (mature account). 10 creative variations + 1 headline = brand investment (mid-maturity). 10 angle variations = early positioning search (immature / pre-PMF). Operationalizes "angle concentration vs spread" by adding maturity tagging. Source: Corey Haines `paid-ads` (Creative Testing Hierarchy).
- **Character-limit behavior** — ads consistently hitting platform max (Google RSA: 30/90, Meta: 40/125, LinkedIn: 70/150) were likely written against the spec deliberately; short ads signal a different strategy.
- **Google RSA combinatorial awareness.** Google Responsive Search Ads require 3-15 headlines and 2-4 descriptions; any 3 are shown together at run time. A burst of "40 ads" on Google Search may actually be 15 headlines × combinatorial testing of 3-headline combinations, not 40 distinct concepts. Count headline slots, not ad count. Pinning reduces optimization surface. Source: Corey Haines `ad-creative/platform-specs.md`.
- **Meta placement reads.** Feed shows all copy; Stories/Reels overlay keeps primary text visible only under 72 chars; right-column shows headline only. A burst with 2000-char primary text is targeting feed placement exclusively — placement, not just count, is a strategic tell.
- **LinkedIn Message Ad (InMail) is a distinct format**: 60-char subject, 1500-char body, 20-char CTA. A competitor running InMail + feed ads vs feed-only signals different motions (ABM/BDR-augmented vs pure self-serve).

### Platform spec reference (for reading what's possible)

| Platform | Headline | Body/primary | Description |
|----------|---------:|-------------:|------------:|
| Google RSA | 30 chars × ≤15 | — | 90 chars × ≤4 |
| Meta | 40 rec | 125 visible / 2200 max | 30 rec |
| LinkedIn | 70 rec / 200 max | 150 rec / 600 max | 100 rec / 300 max |
| TikTok | — | 80 rec / 100 max | — |
| X | 70 card | 280 tweet | 200 card |

---

## Step 4 — Write the analytical line

A competitor ad-analysis line in `analyses/{name}.md` should contain: angle tag, mechanism tag, cadence classification, evidence (ad count + example headlines + started_at range).

**Template:**

> **{Competitor}** runs a {cadence} pattern on {platform}: N ads between {date} and {date}, {M}% tagged `{angle}` activating `{mechanism}`. Example headlines: "{h1}", "{h2}", "{h3}". Relative to the rest of the set, this is {concentrated|spread}. Open question: {thing you can't see}.

**Bad line:** "Sketch runs a lot of Facebook ads."

**Good line:** "Sketch runs a burst-and-coast on Meta: 26 ads between 2026-01-12 and 2026-02-03, then nothing. 18 of 26 (69%) tag as `outcome` activating `hyperbolic discounting` ('Ship designs faster today'). Cadence matches a launch rather than ongoing performance testing. Unknown: whether the coast is intentional or a budget signal."

---

## What to skip

- **Counting raw ad volume as a finding.** "X ran 40 ads" is not a finding. The pattern across those 40 ads is the finding.
- **Interpreting a single ad in isolation.** One ad is an execution; a pattern across the set is a strategy.
- **Assuming what's absent is intentional.** If you didn't find LinkedIn ads for competitor Z, that's a data gap, not a strategic choice by Z. State what you searched, per the program's analytical-honesty standards.
