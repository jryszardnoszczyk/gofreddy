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
