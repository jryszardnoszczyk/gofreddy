# linkedin_sponsored skeleton

Variant artifact JSON shape for LinkedIn Sponsored Content (single
image + intro text).

```json
{
  "variant_id": "<slug>",
  "format": "linkedin_sponsored",
  "platform": "linkedin",
  "hook_archetype": "<one of: observation | framework | contrarian_take | numbered_list>",
  "ad_creative": {
    "hook": "<first-person, ≤8 words for the opening hook>",
    "intro": "<≤150 char intro, front-loaded>",
    "body": "<≤150 char body recommended>",
    "headline": "<1-2 lines>",
    "cta": {"verb": "<LinkedIn-native: Apply | Download | Sign Up>", "text": "<≤4 words>"},
    "image_brief": "<no stock photos — 0% of top-2%-CTR ads use stock>",
    "proof_noun": "<single concrete noun>"
  },
  "lp_hero": {
    "headline": "<shares core promise + proof_noun>",
    "subhead": "<≤14 words>",
    "primary_cta": {"verb": "<EXACT MATCH>", "text": "<button>"},
    "proof_point": "<contains ad.body.proof_noun>"
  }
}
```

Constraints:
- Diversity dim: insight angle (observation / framework / contrarian / list)
- First-person voice (LinkedIn data: outperforms "we")
- NO stock photos
- Banned phrases: "guaranteed ROI", "secret hack", "instant hire", "aggressive"
