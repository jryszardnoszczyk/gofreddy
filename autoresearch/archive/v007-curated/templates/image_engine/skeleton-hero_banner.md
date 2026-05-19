# hero_banner skeleton (1600x900)

Use this skeleton for website hero banners. Single-glance
comprehension <1s; F-pattern composition; WCAG 2.2 contrast on text.

## Composition

- **Hierarchy:** headline > subhead > CTA > visual
- **CTA placement:** top-right or center-low (F-pattern eye flow)
- **Typography:** ≤2 typefaces
- **Contrast:** ≥4.5:1 on all overlaid text (WCAG 2.2 AA)

## meta.json shape (write at drafts/<draft_id>.meta.json)

```json
{
  "draft_id": "<slug>",
  "topic": "<from $IMAGE_ENGINE_TOPIC>",
  "format": "hero_banner",
  "voice_persona": "<from $IMAGE_ENGINE_VOICE_PERSONA_REF>",
  "brand_tokens_path": "<from $IMAGE_ENGINE_BRAND_TOKENS_PATH>",
  "archetype": "product-shot | abstract-brand-anchor",
  "headline": "<≤8 words>",
  "subhead": "<optional, ≤14 words>",
  "cta": "<button text, ≤4 words>",
  "alt_text": "<≤120 chars>"
}
```

## Steps

1. Pick archetype.
2. Fill fal prompt slots. 16:9 aspect ratio.
3. fal.ai generate base imagery.
4. Pillow-composite headline + subhead + CTA button + logo.
5. Verify contrast ratio ≥4.5:1 on overlaid text.
6. Save as `drafts/<draft_id>.png` + meta.json sibling.
