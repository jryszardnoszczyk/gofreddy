# meta_reels skeleton

Variant artifact JSON shape for Meta Reels Ad (vertical 9:16,
1080×1920, 9-15s, hook in first 0.8-1.2s).

```json
{
  "variant_id": "<slug>",
  "format": "meta_reels",
  "platform": "meta",
  "hook_archetype": "<one of: statistic | pain | contrarian | demo_tease | pattern_break>",
  "ad_creative": {
    "hook": "<first-frame line — falsifiable claim, named entity, or concrete result>",
    "body": "<≤125 char primary text, front-loaded>",
    "cta": {"verb": "<Meta-native: Shop Now | Get Quote | Book Now>", "text": "<≤4 words>"},
    "image_brief": "<3-shot storyboard description for image_engine handoff: hook / demo / CTA>",
    "voiceover": "<15-30 word VO script>",
    "on_screen_text": "<≤8 word overlay>",
    "proof_noun": "<single concrete noun the body anchors on>"
  },
  "lp_hero": {
    "headline": "<shares core promise + proof_noun with ad.hook>",
    "subhead": "<≤14 words>",
    "primary_cta": {"verb": "<EXACT MATCH ad.cta.verb>", "text": "<button>"},
    "proof_point": "<contains ad.body.proof_noun>"
  }
}
```

Constraints:
- Diversity dim: hook_archetype (no two variants share)
- Character limits: primary text 125, headline (if used) 27, description 30
- Banned terms: Meta health-vertical hard-gate for health clients
