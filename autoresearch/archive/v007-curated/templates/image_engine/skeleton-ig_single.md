# ig_single skeleton (1080x1080)

Use this skeleton for Instagram single-image posts. One focal subject;
hook-text ≤7 words; legible at 120px thumbnail.

## meta.json shape (write at drafts/<draft_id>.meta.json)

```json
{
  "draft_id": "<slug>",
  "topic": "<from $IMAGE_ENGINE_TOPIC>",
  "format": "ig_single",
  "voice_persona": "<from $IMAGE_ENGINE_VOICE_PERSONA_REF>",
  "brand_tokens_path": "<from $IMAGE_ENGINE_BRAND_TOKENS_PATH>",
  "archetype": "product-spotlight | data-callout",
  "alt_text": "<≤120 chars; describes KEY information>",
  "caption": "<voice-persona-consistent caption for Instagram register>"
}
```

## Steps

1. Pick archetype from `templates/image_engine/fal_prompts/ig_single/`.
2. Fill the fal prompt's `{subject}`, `{action}`, `{brand_palette_hex}`,
   `{lighting}` slots.
3. One critique pass against IE-1/IE-2/IE-5 hints.
4. fal.ai generate (gated by `fal_image_semaphore`).
5. Pillow-composite logo (bottom-right, ≤8% frame) + optional headline overlay.
6. Write alt_text + caption matching voice persona.
7. Save as `drafts/<draft_id>.png` + write meta.json sibling.
