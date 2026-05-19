# li_doc_carousel skeleton (8-12 × 1080x1080 or 1080x1350 portrait)

Use this skeleton for LinkedIn document-style carousels. B2B
aesthetic: restrained palette, data-density preferred, PSR
(Problem-Stakes-Resolution) arc.

## Constraints

- ≤60 words per slide (hard limit; IE-3 caps at 3 if exceeded)
- ≥24pt body type
- Restrained palette (brand-only; no decorative accents)
- Inter / Söhne / Geist-class typography
- Data visualizations preferred over decorative imagery
- NO emoji, NO meme-format

## meta.json shape (write at drafts/<draft_id>/meta.json)

```json
{
  "draft_id": "<slug>",
  "topic": "<from $IMAGE_ENGINE_TOPIC>",
  "format": "li_doc_carousel",
  "voice_persona": "<from $IMAGE_ENGINE_VOICE_PERSONA_REF>",
  "brand_tokens_path": "<from $IMAGE_ENGINE_BRAND_TOKENS_PATH>",
  "slide_count": <8-12>,
  "outline": [
    {"slide_n": 1, "role": "cover", "headline": "...", "key_visual_concept": "..."},
    {"slide_n": 2, "role": "problem", "headline": "...", "key_visual_concept": "..."},
    {"slide_n": 3, "role": "stakes", "headline": "...", "key_visual_concept": "..."},
    {"slide_n": 4, "role": "insight_1", "headline": "...", "key_visual_concept": "..."},
    ...
    {"slide_n": N-1, "role": "proof", "headline": "...", "key_visual_concept": "..."},
    {"slide_n": N, "role": "cta", "headline": "...", "key_visual_concept": "..."}
  ],
  "alt_text_per_slide": ["..."],
  "caption": "<LinkedIn-register caption; B2B-restrained>"
}
```

## Steps

Same TD-41 two-step as ig_carousel:
1. **Outline pass** — emit PSR-structured outline.
2. **Per-slide fal-prompts** — batched 3, with previous-slide visual context.
3. **Pillow-composite** — body text overlay, slide N/M indicator, logo.

Save each slide as `drafts/<draft_id>/slide_NN.png`.
