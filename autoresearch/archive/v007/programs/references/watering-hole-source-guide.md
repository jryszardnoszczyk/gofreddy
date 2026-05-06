# Digital Watering Hole Source Guide — Reading Mention Data by Platform

Source: adapted from Corey Haines's `customer-research` skill, Mode 2 "Digital Watering Hole Research" and `references/source-guides.md`.
URL: https://github.com/coreyhaines31/marketingskills/tree/main/skills/customer-research

Use this file when interpreting mention data in `mentions/*.json`. The point is to calibrate what each platform's signal actually means before aggregating across sources.

---

## Source-by-source calibration

### Reddit
- **Skew:** Technical, skeptical, power-user. Over-indexes complaints and edge cases vs. mainstream buyer sentiment.
- **Signal hierarchy:** Upvote ratio is the deepest trust signal — high ratio (>95%) = uncontroversial consensus. Comment depth indicates controversy. High-upvote / low-comment = broadly accepted. High-upvote / deep-comment = contested and load-bearing.
- **High-signal thread types:** "What tools do you use for X?" (alternatives + vocab), "Frustrated with [X] looking for alternatives" (pain + switching triggers), "Is [category] worth it?" (objections + evaluation criteria), complaint threads about competitors (gaps to fill).
- **Stories-to-pull:** a Reddit thread that has both a 1000+ upvote top comment AND a 200+ upvote counter-comment is a controversy story, not a consensus story. Classify accordingly.

### G2 / Capterra / Trustpilot
- **Skew:** Power users and strong-opinion holders. Silent majority missing.
- **Star-rating signal hierarchy** (highest to lowest signal for monitoring):
  1. **3-star reviews** — the most honest. User stayed but felt something missing. Best source of unmet need language.
  2. **1-star reviews** — failure modes. Separate product issues from support/onboarding issues before reporting.
  3. **4-star reviews** — often hide "the only thing I wish…" buried in praise. Treat as competitor-gap intel when they're on a competitor page.
  4. **5-star reviews** — proof-point language, but biased high. Useful for "what they love" but not for severity.
- **Competitor 4-star reviews are the single highest-value source for brand monitoring when the client is on a nearby product category page.**
- **Trustpilot skews B2C.** AppSumo skews SMB/prosumer. Don't treat them as equivalent to G2 for B2B SaaS mentions.

### Hacker News
- **Skew:** Technical builders + skeptics. Strong opinions on pricing models (especially subscription-based) and underlying architecture.
- **First-principles objections** surface here that rarely surface elsewhere. If an HN comment cluster says the business model won't work, that's a leading signal even with low raw volume.

### LinkedIn
- **Skew:** Self-promotional, public-persona. Comments are higher signal than likes — 20 thoughtful comments > 200 likes for reach.
- **Job postings as pain signals:** When a client competitor starts posting roles that mention a specific tool, that tool is being considered. Monitoring blind spot: job postings aren't in most mention APIs but are a leading competitive signal.

### YouTube comments
- **Signal:** Timestamped comments are gold — they point to exact confusion moments in a workflow demo.
- **"Does this work for [specific use case]?"** comments reveal edge-case demand.
- Surface "I tried this but…" comments as unmet-need evidence.

### Twitter / X
- **Skew:** Real-time, emotional, first 30 minutes of velocity determine reach. Short posts (<100 char) outperform.
- Quote-tweets with added context are higher signal than plain retweets. A competitor taking a quote-tweet beating on a feature decision is a story worth tracking.

### App Store / Play Store
- **Skew:** Consumer, post-purchase frustration. 1-3 star reviews are the mining target.
- Version number matters — tie review dates to app release dates to separate "new bug" from "chronic complaint."

### News / Trustpilot / Newsdata
- Journalistic framing ≠ end-user sentiment. News mentions tell you what PR/marketing is achieving, not what customers are feeling.

---

## Confidence scoring (pair with the existing MON-2 severity rules)

When calling severity, tag each story with a frequency × intensity × independence score:

| Confidence | Independent sources | Unprompted mentions | Emotional language |
|------------|---------------------|---------------------|---------------------|
| **High** | 3+ | Yes | Consistent across segments |
| **Medium** | 2 | Mostly | Limited to one segment |
| **Low** | 1 | No / only prompted | Could be outlier |

This aligns with program rule: "Sources < 2 caps confidence at LOW-MEDIUM. Data window < 3 days caps at MEDIUM."

---

## Recency weighting

- **12-month window** — recent sources weighted more heavily than older. Markets shift.
- **App version tie-in** — for app-store mentions, anchor to release date so a "new bug" story isn't diluted by chronic-complaint history.
- **Platform decay profiles differ:**
  - Twitter/X — 24-hour half-life on velocity signal
  - Reddit — 7-day half-life, but top-of-all-time posts stay indexable
  - G2/Trustpilot — slow decay; a 3-month-old complaint is still active intel
  - HN — very short (<48h) for front-page stories, but archived discussion retains signal

---

## Applying this to a monitoring digest

1. **Per-story source mix line.** State how many independent platforms contributed. "Story pulls from r/devops (3 threads, +1800 upvotes), G2 4-star reviews on competitor (5 mentions), HN (1 top comment) — 3 independent sources, High confidence."
2. **Bias acknowledgment when platform-skewed.** If a story is all Reddit, flag: "Reddit-dominated: skews technical/skeptical vs. mainstream-buyer sentiment. Treat the volume spike as a power-user signal, not broad-market." This strengthens MON-2.
3. **4-star competitor reviews as a distinct cluster.** When monitoring a competitor, 4-star G2 reviews are a higher-signal cluster than 1-star — call them out separately.
4. **"What didn't happen" framing for MON-6.** The absence of expected sources is a finding. If LinkedIn normally produces N mentions per week on this topic and this week produced zero, report the absence with the recency-window expectation.

---

## Source-confidence weighting table (for MON-2 severity calibration)

Extends the frequency × intensity × independence scoring with per-source weighting. Higher-weight sources carry more MON-2 signal per mention than lower-weight sources.

| Source type | Confidence weight | Why |
|-------------|-------------------|-----|
| Customer interview / sales call transcripts | Very high | Direct speech, context-rich, unprompted within topic |
| Win/loss interviews | High | Pain + trigger + alternative, one artifact |
| G2 / Capterra / AppSumo reviews | High | Identity-attached, platform-verified |
| App store 1-3 star reviews (version-anchored) | High | Timestamped to release; high signal density |
| Reddit (top-voted threads) | Medium-high | Upvote ratio confirms peer-consensus; comment depth calibrates |
| SparkToro audience data | Medium-high | Behavioral aggregate — good for "what/where," medium for "why" |
| Customer support ticket threads | Medium | Problem-biased; confusion ≠ dissatisfaction |
| Survey open-ended responses | Medium | Self-selected; emotional markers carry |
| NPS verbatims | Medium | Score + verbatim together is the signal; score alone is low |
| YouTube / TikTok comments (timestamped) | Medium | Time-anchored to exact workflow moments |
| Twitter/X (min 10 likes, no replies filter) | Medium-low | Real-time but noisy; velocity matters more than volume |
| LinkedIn posts | Medium-low | Self-promotion biased; comments higher signal than likes |
| Survey multiple-choice responses | Low-medium | Prompted, closed-ended; low on "why" |
| Job postings (as pain signals) | Low-medium | Pain inferred, not stated; adjacent-tool signal |
| News articles / press releases | Low | Journalistic framing ≠ end-user sentiment |
| Trustpilot (B2B context) | Low | Skews B2C; strong-opinion bias |

**MON-2 integration:** when calculating confidence, weight each source by its tier before applying the frequency × intensity × independence rule. "Three sources" of Medium-low tier doesn't match "three sources" of Very-high tier for the same archetype.

---

## LinkedIn job postings as pain signals

Job postings aren't in most mention APIs but are a leading competitive signal. When one surfaces in the mention stream:

- **"Required" tools vs "nice to have":** required tools reveal the current stack; nice-to-have reveals adjacent-tool intent. A client competitor posting a role that lists "[client's product] a plus" is an intent signal; one listing it as "required" is already adopted.
- **Metrics in the role description** reveal the job-to-be-done. "Report MoM growth" → reporting tool-of-choice tells you their analytics stack.
- **Role seniority shifts:** a competitor posting their first VP-level role in a function is a motion-change signal (org is formalizing that function).

---

## Character-length and hashtag context per platform

Calibration reading the engagement numbers:

| Platform | Visible-before-more / ideal | Hashtag rule | Interpretation |
|----------|-----------------------------|--------------|----------------|
| LinkedIn | 210 chars visible; 1200-1500 char sweet spot | 3-5 relevant | Document/carousel posts reach strongest; polls drive engagement not authority |
| Twitter/X | 280 char tweets; <100 chars get more engagement | — | First 30-min velocity sets reach; quote-tweets with added insight outperform RTs |
| Facebook | 40-80 char engagement sweet spot | — | External links kill reach — mentions without external links ≠ low-sentiment, could be link-demoted content |
| Instagram | 125 chars visible; 2200 max | 3-10 (30 max but algorithm penalizes) | Reels get 2× reach of static; saves + shares > likes |
| TikTok | 150 char visible; 80-100 best | **5 max (Aug 2025)** — older mentions with more predate rule | Watch-through + shares > likes; hook in first 1-2s |
| YouTube | Title visible ~70 of 100 chars | **>15 hashtags = ALL ignored** | Engagement anomalies: check hashtag count before concluding algorithmic suppression |
| Threads | — | **1 topic tag per post** | Multiple topic tags = likely auto-generated/bot content, not organic |

**Monitoring implication:** a TikTok post dated before August 2025 with 8 hashtags is not comparable to a post dated after with 4 hashtags — the algorithm rule changed. Version-aware interpretation prevents false delta-framing errors (MON-1).

---

## Theme-tag system (optional schema extension for stories)

Corey's customer-research tagging taxonomy. Can be adopted as a light schema on `stories/*.json` entries for cross-story pattern mining (MON-5):

- `#pain` — the problem stated
- `#trigger` — event that caused the search for solution
- `#outcome` — desired end state
- `#language` — exact vocabulary (for copy)
- `#alternative` — what they're using instead
- `#objection` — resistance to a solution
- `#competitor` — named competitor mention

Multi-tag stories surface cross-cluster patterns — e.g., #pain + #competitor clusters are competitive-pull archetype (see `churn-signal-patterns.md`).
