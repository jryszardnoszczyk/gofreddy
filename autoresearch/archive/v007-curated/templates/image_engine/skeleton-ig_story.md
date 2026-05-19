# ig_story skeleton (1080x1920 vertical)

Use this skeleton for Instagram story posts. Vertical format; respect
the 3-zone hierarchy and IG safe-zones.

## Zone hierarchy

- **Top 250px** — IG UI safe-zone. Reserved for brand strip only;
  no critical text or focal subject.
- **Middle ~1420px** — focal subject. Centered, vertically dominant.
- **Bottom 250px** — IG UI safe-zone. CTA + swipe-up affordance only;
  no critical content.

## meta.json shape (write at drafts/<draft_id>.meta.json)

```json
{
  "draft_id": "<slug>",
  "topic": "<from $IMAGE_ENGINE_TOPIC>",
  "format": "ig_story",
  "voice_persona": "<from $IMAGE_ENGINE_VOICE_PERSONA_REF>",
  "brand_tokens_path": "<from $IMAGE_ENGINE_BRAND_TOKENS_PATH>",
  "archetype": "<archetype slug>",
  "alt_text": "<≤120 chars>",
  "caption": "<sticker-style sub-caption, if used>"
}
```

## Steps

1. Pick archetype.
2. Fill fal prompt slots — `{subject}`, `{action}`, `{brand_palette_hex}`,
   `{lighting}`. Vertical aspect ratio: 9:16.
3. fal.ai generate.
4. Pillow-composite top brand strip + middle focal anchor + bottom
   CTA. Respect 250px safe-zones.
5. Save as `drafts/<draft_id>.png` + meta.json sibling.
