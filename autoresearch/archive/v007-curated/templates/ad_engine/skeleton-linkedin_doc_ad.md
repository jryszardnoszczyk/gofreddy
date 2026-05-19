# linkedin_doc_ad skeleton

Variant artifact JSON shape for LinkedIn Document Ad (3-10 slide
carousel; sweet spot 5-7).

```json
{
  "variant_id": "<slug>",
  "format": "linkedin_doc_ad",
  "platform": "linkedin",
  "hook_archetype": "<one of: case_study | framework | mistake_list | data_visualization>",
  "ad_creative": {
    "hook": "<cover-slide headline that works standalone>",
    "body": "<intro text accompanying the document carousel>",
    "cta": {"verb": "<LinkedIn-native>", "text": "<≤4 words>"},
    "image_brief": "<document carousel: 5-7 slides; cover + 3-5 body + CTA>",
    "slide_outline": [
      {"slide_n": 1, "role": "cover", "headline": "<works standalone>", "key_visual": "..."},
      {"slide_n": 2, "role": "problem", "headline": "...", "key_visual": "..."},
      {"slide_n": 3, "role": "insight", "headline": "...", "key_visual": "..."},
      {"slide_n": 4, "role": "proof", "headline": "...", "key_visual": "..."},
      {"slide_n": 5, "role": "cta", "headline": "...", "key_visual": "..."}
    ],
    "proof_noun": "<single concrete noun>"
  },
  "lp_hero": {
    "headline": "<shares core promise + proof_noun with cover headline>",
    "subhead": "<≤14 words>",
    "primary_cta": {"verb": "<EXACT MATCH>", "text": "<button>"},
    "proof_point": "<contains ad.body.proof_noun>"
  }
}
```

Constraints:
- Diversity dim: content shape (case-study / framework / mistake-list / data-viz)
- Slide count 3-10 (sweet spot 5-7)
- Cover slide works as standalone
- ≤30 words per body slide
- Variants: 3 per platform-format (fewer than other formats — heavier)
