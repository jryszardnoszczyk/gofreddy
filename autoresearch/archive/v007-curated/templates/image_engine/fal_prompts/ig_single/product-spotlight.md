# ig_single / product-spotlight archetype

Single focal subject; product or named entity centered; brand palette
applied via hex codes in prompt.

## Prompt template

A clean studio photograph of {subject} in a {lighting} setup.
Composition: centered focal subject, ample whitespace at top and
bottom thirds, no decorative clutter. Brand palette dominant:
{brand_palette_hex} (use these HEX codes for accent colors only; do
not render any text overlays). Square aspect ratio 1:1, 1080×1080.
Photography style: minimal, product-spotlight, magazine-grade
lighting. NO logos, NO marketing copy, NO call-to-action text
embedded in the image — those will be Pillow-composited after.

## Slots

- `{subject}`           — the product / named object
- `{lighting}`          — e.g., "soft natural", "studio strobe", "golden hour"
- `{brand_palette_hex}` — comma-separated HEX codes, e.g., "#FF6B35, #1F3A5F"

## When to use

- Klinika procedure-spotlight (treatment product or device)
- gofreddy tool-spotlight (Claude Code, Codex, OpenClaw)
- Single-product e-commerce posts
