# Signal aggregator brief synthesis prompt

You are summarizing aggregated competitive + SERP + first-party SEO
signal into a 6-10 bullet creative brief for the ad_engine agent.

## Inputs you receive

- **top_competitor_ads** (up to 8): ranked by `longevity_days ×
  cross_source_confidence × format_match_to_target`. Each carries
  `{hook_text, body_excerpt, format, days_running, sources[]}`.
- **recurring_hook_archetypes**: cluster labels + frequency counts
  observed across the competitor library.
- **serp_signal**: top-5 organic results for the offer's keywords +
  intent classification.
- **gsc_signal**: top-10 first-party queries with impressions, CTR,
  position deltas from the prior 28d window.
- **competitor_voice_anti_examples**: 3-5 verbatim hooks the
  variant should NOT mimic.

## Output shape

A 6-10 bullet markdown list. Each bullet is one of:
- **What's working** — patterns saturating the category (cite
  competitor + count).
- **What's saturated** — opening 3-grams or formats that ≥3
  competitors share (so the agent counter-positions, not echoes).
- **What's an opening** — gap in the competitor library or unmet
  buyer-intent signal from SERP/GSC.

Each bullet ≤25 words. Cite specific competitors or queries with
named source attribution ("per top-5 SERP for 'X' query"; "Adyntel
shows 12 ads using 'tired of X' opener over 60 days").

## Output ONLY the bullet list, no preamble.
