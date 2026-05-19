# li_doc_carousel / case-study archetype

LinkedIn document carousel narrating a case study via PSR (Problem-
Stakes-Resolution) arc. Each slide advances the narrative.

## Prompt template (per slide)

A restrained editorial slide for a B2B LinkedIn case-study carousel.
Slide {slide_n} of {slide_count}. Role: {role}. Layout: title bar
(top ~120px) empty for headline; body area (middle) showing
{key_visual_concept} — abstracted scene that signals the case-study
moment (a workflow diagram fragment, a milestone marker, an icon
anchored to the brand vertical); footer (~120px) empty for slide
number + brand logo. Palette: {brand_palette_hex} only. NO stock-
photo people. Visual continuity: {previous_slide_visual_summary}.
Square aspect ratio 1:1, 1080×1080. NO emoji.

## Slots

- `{slide_n}`, `{slide_count}`, `{role}` — slide context
- `{headline}` — slide title (≤10 words)
- `{key_visual_concept}` — what the slide shows (≤15 words)
- `{previous_slide_visual_summary}` — prior slide recap
- `{brand_palette_hex}` — restrained brand palette

## When to use

- DWF client representation case studies (anonymized)
- gofreddy operational case studies (audit-to-implementation arcs)
- Enterprise B2B case-study formats
