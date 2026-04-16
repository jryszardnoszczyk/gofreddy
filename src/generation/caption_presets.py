"""Static caption style presets for video composition."""

from .models import CaptionStyle

DEFAULT = CaptionStyle(
    name="default",
    font_name="Arial",
    font_size=24,
    primary_colour="&H00FFFFFF",
    outline_colour="&H00000000",
    back_colour="&H80000000",
    border_style=3,
    outline_width=2,
    alignment=2,
    margin_v=30,
)

HORMOZI = CaptionStyle(
    name="hormozi",
    font_name="Montserrat Bold",
    font_size=48,
    primary_colour="&H00FFFFFF",
    outline_colour="&H00000000",
    back_colour="&H00000000",
    border_style=1,
    outline_width=4,
    bold=True,
    alignment=2,
    margin_v=40,
)

MINIMAL = CaptionStyle(
    name="minimal",
    font_name="Arial",
    font_size=18,
    primary_colour="&H00FFFFFF",
    outline_colour="&H00000000",
    back_colour="&H00000000",
    border_style=1,
    outline_width=1,
    alignment=6,  # top-center
    margin_v=20,
)

ELEGANT = CaptionStyle(
    name="elegant",
    font_name="Playfair Display",
    font_size=22,
    primary_colour="&H00FFFFFF",
    outline_colour="&H00000000",
    back_colour="&H00000000",
    border_style=1,
    outline_width=1,
    shadow_depth=2,
    italic=True,
    alignment=10,  # middle-center
    margin_v=30,
)

CINEMATIC = CaptionStyle(
    name="cinematic",
    font_name="Arial",
    font_size=24,
    primary_colour="&H0000FFFF",  # yellow (AABBGGRR)
    outline_colour="&H00000000",
    back_colour="&H00000000",
    border_style=1,
    outline_width=2,
    alignment=2,
    margin_v=30,
)

NEON = CaptionStyle(
    name="neon",
    font_name="Montserrat Bold",
    font_size=28,
    primary_colour="&H00FFFF00",  # cyan (AABBGGRR)
    outline_colour="&H00FF00FF",  # magenta
    back_colour="&H00000000",
    border_style=1,
    outline_width=4,
    bold=True,
    alignment=10,  # middle-center
    margin_v=30,
)

_PRESETS: dict[str, CaptionStyle] = {
    "default": DEFAULT,
    "hormozi": HORMOZI,
    "minimal": MINIMAL,
    "elegant": ELEGANT,
    "cinematic": CINEMATIC,
    "neon": NEON,
}


def get_preset(name: str) -> CaptionStyle:
    """Look up a caption preset by name, falling back to default."""
    return _PRESETS.get(name, DEFAULT)
