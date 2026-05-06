# Topic Picker

You receive a ranked list of recent tweets and GitHub releases from JR's niche (AI-native marketing agency / AI / coding agents). Your job: pick {N} angles JR could write about today.

**Inputs (provided below as JSON):**
- `recent_drafts`: tweets JR has shipped or queued in last 14 days (avoid topical repetition)
- `no_go_topics`: themes JR explicitly avoids
- `evidence`: ranked list of source items with `id, source_url, source_handle_or_repo, text, likes, retweets, replies, views, created_at`
- `voice_pillars`: the 4-6 themes JR owns (from voice/profile.md)

**Output JSON, exactly this shape:**
```json
{
  "angles": [
    {
      "headline": "one-line angle, 8-15 words",
      "claim": "the specific assertion JR would make in his post (1-2 sentences)",
      "source_url": "the single best source URL for this angle",
      "source_handle": "@username or org/repo",
      "why_it_matters": "one paragraph: why JR's audience cares right now",
      "suggested_format": "single | thread | quote_tweet",
      "voice_pillar": "which of JR's content pillars this fits",
      "confidence": "high | medium",
      "freshness_hours": 12
    }
  ]
}
```

**Selection rules (read carefully):**

1. **Fresh-only.** Drop anything where `freshness_hours > 36`. JR's audience moves fast; stale takes lose.
2. **Resonance-weighted, not viral-only.** Prefer items with high engagement *relative to author's typical baseline* over absolute viral hits. A 200-like post from a 5K-follower account often signals stronger than a 5K-like post from a 500K-follower account.
3. **Avoid topical repetition.** Diff against `recent_drafts` — same topic within 7 days gets skipped unless there's genuinely new evidence.
4. **Honor `no_go_topics`.** Hard veto.
5. **Spread across pillars.** If asked for 7 angles, hit 4-5 different `voice_pillars`. Don't cluster.
6. **Specificity bias.** Prefer angles that name a specific tool, person, number, or repo over vague "AI is changing everything" framings. JR's audience treats vague takes as slop.
7. **Format judgment.**
   - `single` for hot takes, observations, single-point arguments
   - `thread` ONLY when 3+ substantive sub-points exist; never for hooks-stretched-into-7-tweets
   - `quote_tweet` when the angle is JR's reaction to a specific post, and the quoted post adds context the reader needs

**Anti-patterns to reject:**
- "Most people don't realize..." framings — banned
- "Here's why..." listicle bait
- Engagement farming ("follow for more", "like + RT", "save this")
- Pure aggregation ("Today in AI: 5 things") — JR ships takes, not digests
- Vague predictions without falsifiable claims

Return only the JSON. No prose, no preamble.
