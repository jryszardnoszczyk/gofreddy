# ad_static / offer-pull archetype

Ad creative anchored on a specific offer or incentive. Visual
emphasizes the offer; the offer text overlay is the focal point.

## Prompt template

A clean static ad creative with the visual subordinate to a forth-
coming offer overlay. Subject: {subject} — small, supporting,
positioned in a lower third or as a background anchor. Lighting:
{lighting}. Composition: top two-thirds is empty whitespace for the
offer headline + sub-copy (Pillow-composited); bottom third holds
the supporting visual. Palette: {brand_palette_hex}. Aspect ratio
per platform. NO rendered text in image. NO CTA button — that's
Pillow-composited.

## Slots

- `{subject}`           — supporting visual anchor (small, lower third)
- `{lighting}`          — lighting register
- `{brand_palette_hex}` — brand HEX codes
- platform-specific aspect ratio set in meta.json

## When to use

- Limited-time-offer paid ads
- Promo/discount ad creative
- Direct-response ad formats
