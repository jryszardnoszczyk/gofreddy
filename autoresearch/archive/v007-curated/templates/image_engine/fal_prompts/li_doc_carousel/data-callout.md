# li_doc_carousel / data-callout archetype

LinkedIn document carousel emphasizing data points. B2B aesthetic;
restrained palette; data visualizations preferred over decorative
imagery.

## Prompt template (per slide)

A restrained editorial slide for a B2B LinkedIn document carousel.
Slide {slide_n} of {slide_count}. Role: {role}. Layout: title bar
(top ~120px) empty for Pillow-composited headline; body area
(middle) showing {key_visual_concept} — prefer abstracted chart,
table fragment, or data-anchor visual over decorative imagery;
footer (~120px) empty for slide number + brand logo. Palette:
{brand_palette_hex} only — NO decorative accent colors. Typography
hint: brand sans-serif (e.g., Inter / Söhne / Geist). Visual
continuity: {previous_slide_visual_summary}. Square aspect ratio
1:1, 1080×1080. NO emoji. NO meme format.

## Slots

- `{slide_n}`, `{slide_count}`, `{role}` — slide context
- `{headline}` — slide title (≤10 words; B2B-restrained)
- `{key_visual_concept}` — data visualization concept (≤15 words)
- `{previous_slide_visual_summary}` — prior slide recap
- `{brand_palette_hex}` — comma-separated HEX codes (restrained set)

## When to use

- DWF KSeF regulatory timeline carousels
- B2B SaaS data-anchored insights
- Enterprise white-paper-style carousels
