# ig_carousel / listicle archetype

For carousels structured as a numbered list of N points. Cover slide
introduces the list ("5 ways to..."); interior slides each present
one point with consistent layout.

## Prompt template (per slide)

A clean editorial slide for a numbered list carousel. Slide
{slide_n} of {slide_count}. Role: {role}. Headline area (top
third): empty whitespace where "{headline}" will be Pillow-
composited. Focal area (middle third): {key_visual_concept} —
illustrative rather than literal; use {brand_palette_hex} as the
accent palette. Footer (bottom third): empty whitespace for slide
number "N/M" indicator + brand logo (Pillow-composited). Visual
continuity: {previous_slide_visual_summary} — match palette and
composition style. Square aspect ratio 1:1, 1080×1080.

## Slots

- `{slide_n}`, `{slide_count}`, `{role}` — slide context
- `{headline}` — short headline for this slide (≤8 words)
- `{key_visual_concept}` — what the visual shows (≤12 words)
- `{previous_slide_visual_summary}` — 1-sentence factual recap of prior slide
- `{brand_palette_hex}` — comma-separated HEX codes

## When to use

- "5 ways to X" carousels
- Step-by-step process carousels
- Numbered insight lists
