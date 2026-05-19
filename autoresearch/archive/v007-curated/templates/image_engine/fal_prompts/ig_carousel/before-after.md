# ig_carousel / before-after archetype

For carousels showing transformation arcs (before/after, problem/
solution, old/new). Cover slide promises the comparison; alternating
slides present each pole.

## Prompt template (per slide)

A clean editorial slide for a before/after carousel. Slide
{slide_n} of {slide_count}. Role: {role}. Two-zone composition: top
half = "BEFORE state" or "AFTER state" label area (empty whitespace
for Pillow-composited label); bottom half = {key_visual_concept}
illustrating that state. Color treatment differs per pole:
{brand_palette_hex} for the "after" pole; muted/desaturated for
"before". Visual continuity: {previous_slide_visual_summary}. Square
aspect ratio 1:1, 1080×1080.

## Slots

- `{slide_n}`, `{slide_count}`, `{role}` — slide context
- `{headline}` — pole label ("Before consent" / "After treatment")
- `{key_visual_concept}` — what each state looks like
- `{previous_slide_visual_summary}` — prior slide recap
- `{brand_palette_hex}` — comma-separated HEX codes

## When to use

- Klinika treatment transformation arcs (where compliant)
- Workflow before/after migrations
- Product evolution carousels
