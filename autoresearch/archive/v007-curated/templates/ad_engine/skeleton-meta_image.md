# meta_image skeleton

Variant artifact JSON shape for Meta Image Ad (1:1 1080×1080 primary,
4:5 1080×1350 secondary).

```json
{
  "variant_id": "<slug>",
  "format": "meta_image",
  "platform": "meta",
  "hook_archetype": "<one of: outcome | status | efficiency | risk_reduction>",
  "ad_creative": {
    "hook": "<falsifiable claim / named entity / concrete result>",
    "body": "<≤125 char primary text, front-loaded in first 80>",
    "cta": {"verb": "<Meta-native>", "text": "<≤4 words>"},
    "image_brief": "<single-image composition; text-in-image <20% frame>",
    "headline": "<≤27 chars>",
    "description": "<≤30 chars>",
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
- Diversity dim: promise type (no two variants share outcome/status/efficiency/risk-reduction)
- Character limits: primary 125, headline 27, description 30
- Text-in-image <20% pixel area (Meta penalty)
