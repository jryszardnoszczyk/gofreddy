# ad_static skeleton (platform-specific dimensions)

Use this skeleton for static ad creative. Text-overlay <20% pixel
area (hard fail >15% area is text); LinkedIn billboard rule ≤7
words overlay.

## Platform-specific dimensions

| Platform           | Dimensions     | Text-overlay rule        |
|--------------------|----------------|--------------------------|
| Meta (FB/IG feed)  | 1080×1080      | <20% area; soft penalty  |
| Meta story         | 1080×1920      | <20% area                |
| LinkedIn sponsored | 1200×627       | ≤7 words overlay         |
| Twitter/X promoted | 1200×675       | <20% area                |
| Google Display     | 300×600, etc.  | <20% area                |

## meta.json shape (write at drafts/<draft_id>.meta.json)

```json
{
  "draft_id": "<slug>",
  "topic": "<from $IMAGE_ENGINE_TOPIC>",
  "format": "ad_static",
  "voice_persona": "<from $IMAGE_ENGINE_VOICE_PERSONA_REF>",
  "brand_tokens_path": "<from $IMAGE_ENGINE_BRAND_TOKENS_PATH>",
  "platform_target": "meta_feed | li_sponsored | ...",
  "archetype": "value-prop | offer-pull",
  "headline": "<≤7 words for LinkedIn>",
  "cta": "<button text>",
  "alt_text": "<≤120 chars>"
}
```

## Steps

1. Pick archetype.
2. Fill fal prompt slots based on platform_target dimensions.
3. fal.ai generate.
4. Pillow-composite headline + CTA + logo within pixel-area cap.
5. Save as `drafts/<draft_id>.png` + meta.json sibling.
