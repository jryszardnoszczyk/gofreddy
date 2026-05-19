# ig_carousel skeleton (5-10 × 1080x1080)

Use this skeleton for Instagram carousel posts. TD-41 two-step
storytelling: outline pass → per-slide fal-prompts with previous-
slide visual context echoed.

## meta.json shape (write at drafts/<draft_id>/meta.json)

```json
{
  "draft_id": "<slug>",
  "topic": "<from $IMAGE_ENGINE_TOPIC>",
  "format": "ig_carousel",
  "voice_persona": "<from $IMAGE_ENGINE_VOICE_PERSONA_REF>",
  "brand_tokens_path": "<from $IMAGE_ENGINE_BRAND_TOKENS_PATH>",
  "slide_count": <5-10>,
  "outline": [
    {"slide_n": 1, "role": "cover", "headline": "...", "key_visual_concept": "..."},
    {"slide_n": 2, "role": "stakes", "headline": "...", "key_visual_concept": "..."},
    ...
  ],
  "alt_text_per_slide": ["...", "...", ...],
  "caption": "<carousel-level Instagram caption>"
}
```

## Steps (TD-41 two-step)

### Step A: outline pass (claude/opus)

Emit `[{slide_n, role, headline, key_visual_concept}]` where role
follows the hook-stakes-value(×4)-proof-cta arc. Cover slide gets a
dedicated `cover` archetype.

### Step B: per-slide fal-prompts (parallel inside batches of 3)

Each slide's prompt receives:
- slide_n, role, headline
- previous_slide_visual_summary (1-sentence factual recap)
- brand_tokens + palette
- archetype (from templates/image_engine/fal_prompts/ig_carousel/)

The `previous_slide_visual_summary` keeps palette + composition
coherent without serial blocking.

### Step C: composite + save

Pillow-composite logo (≤8% frame) + slide number "N/M" indicator +
swipe-indicator arrow + optional headline overlay on each slide.
Save as `drafts/<draft_id>/slide_NN.png`.
