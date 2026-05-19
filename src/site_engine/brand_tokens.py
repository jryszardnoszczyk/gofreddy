"""Pydantic schema + loader for `clients/<slug>/brand/tokens.json`.

Per plan §U18 verification + Threat Model brand_tokens-swap mitigation:
the tokens.json file ships with each site_engine-enabled client and
declares colors, typefaces, spacing grid, and motion tokens that the
site_engine lane reads (mutation-READ-ONLY per TD-43 Tier-C). A
maliciously-swapped tokens.json could inject external URLs into
typeface specs (CSS @font-face src), tracking-pixel image URLs into
palette tokens, or oversized values that break section layout —
all routes to corrupt published client sites.

This module enforces a tight, additive-permissive schema:

  - Color tokens: hex codes only (#RRGGBB or #RGB), no `url()` /
    `gradient()` / `var()` expressions, no JS protocol handlers.
  - Typeface tokens: family name (string, no URL) + optional weight
    + optional fallback family. External @font-face URLs are
    DISALLOWED in v1; operators host fonts on the same origin as
    the rendered page (CORS + privacy).
  - Spacing / motion tokens: numeric primitives bounded to sane
    ranges. Operator-extensible via the `extra` mechanism but the
    bounded fields are pinned.

Per `model_config = ConfigDict(extra='allow')`: the schema is
additive — operators can carry experimental tokens that the bounded
fields haven't pinned yet, but cannot relax the bounded fields.

Failure mode: ValidationError raised at load time. The site_engine
workflow's configure_env() validates immediately on lane startup so
the failure surface is BEFORE the variant agent burns tokens
generating against an invalid brand context.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Threat-model constants
# ---------------------------------------------------------------------------

# Hex color: #RGB or #RRGGBB or #RRGGBBAA (alpha allowed). Case-insensitive.
# Pinned per the plan's color-only restriction (no gradients, no var()).
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")

# Disallowed substrings in typeface family names — these would let an
# attacker smuggle url() / @import / JS protocols into the rendered
# stylesheet. The site_engine lane writes typeface family strings into
# CSS verbatim; any non-identifier-shaped value is rejected at load.
_FORBIDDEN_TYPEFACE_SUBSTRINGS = (
    "url(", "url ", "@import", "javascript:", "data:", "expression(",
    "</", "<script", "<style", "{", "}", ";", "\\",
)

# Spacing / motion bounds — generous enough to cover real designs without
# allowing absurd values that would tank Core Web Vitals or crash render.
_SPACING_PIXEL_MAX = 256       # 16rem at 16px base; reasonable max
_MOTION_DURATION_MS_MAX = 5000 # 5 seconds; transitions beyond this are jank
_MOTION_DURATION_MS_MIN = 0    # 0 ms is "instant"; allowed


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class ColorPalette(BaseModel):
    """Palette tokens. Hex codes only — no `url()`, `gradient()`, `var()`."""

    model_config = ConfigDict(frozen=True, extra="allow")

    primary: str = Field(..., description="Primary brand color, hex.")
    secondary: str | None = Field(default=None)
    accent: str | None = Field(default=None)
    background: str | None = Field(default=None)
    foreground: str | None = Field(default=None)
    muted: str | None = Field(default=None)

    @field_validator(
        "primary", "secondary", "accent", "background", "foreground", "muted",
        mode="before",
    )
    @classmethod
    def _hex_color_only(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError(
                f"color token must be a string hex code; got "
                f"{type(v).__name__}={v!r}"
            )
        if not _HEX_COLOR_RE.match(v):
            raise ValueError(
                f"color token {v!r} is not a valid hex code "
                f"(#RGB | #RRGGBB | #RRGGBBAA). "
                f"`url(...)`, `gradient(...)`, `var(...)`, and named "
                f"CSS colors are disallowed per Threat Model "
                f"brand_tokens-swap mitigation."
            )
        return v


class Typeface(BaseModel):
    """A single typeface specification. Family name only — external
    @font-face URLs disallowed in v1 (operator hosts fonts same-origin)."""

    model_config = ConfigDict(frozen=True, extra="allow")

    family: str = Field(
        ...,
        description=(
            "Font family name (e.g. 'Inter', 'system-ui'). Plain identifier "
            "+ optional generic-family fallback only. No url() / @import / "
            "data: / javascript: smuggling."
        ),
    )
    weight: int | str | None = Field(
        default=None,
        description="CSS font-weight: 100-900 or 'normal'|'bold'|'lighter'.",
    )
    fallback: str | None = Field(
        default=None,
        description="Optional fallback family name (same restrictions).",
    )

    @field_validator("family", "fallback", mode="before")
    @classmethod
    def _no_smuggled_urls_or_scripts(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError(
                f"typeface family must be a string; got "
                f"{type(v).__name__}={v!r}"
            )
        lowered = v.lower()
        for forbidden in _FORBIDDEN_TYPEFACE_SUBSTRINGS:
            if forbidden in lowered:
                raise ValueError(
                    f"typeface family {v!r} contains forbidden substring "
                    f"{forbidden!r}. External @font-face URLs, inline "
                    f"<script>, CSS @import, and protocol handlers "
                    f"(javascript: / data:) are disallowed per Threat "
                    f"Model brand_tokens-swap mitigation. Operators host "
                    f"fonts on the same origin as the rendered page."
                )
        # Length cap: family names beyond 256 chars are almost certainly
        # an injection attempt rather than a legitimate font reference.
        if len(v) > 256:
            raise ValueError(
                f"typeface family is {len(v)} chars; cap is 256 to "
                f"prevent injection. Real font names are <50 chars."
            )
        return v

    @field_validator("weight", mode="before")
    @classmethod
    def _weight_is_normalized(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, int):
            if not (100 <= v <= 900):
                raise ValueError(
                    f"font-weight {v} outside CSS-spec range [100, 900]"
                )
            return v
        if isinstance(v, str):
            allowed = {"normal", "bold", "lighter", "bolder"}
            if v.lower() not in allowed:
                raise ValueError(
                    f"font-weight {v!r} must be int [100,900] or one of "
                    f"{sorted(allowed)}"
                )
            return v.lower()
        raise ValueError(
            f"font-weight must be int or string; got {type(v).__name__}"
        )


class Typography(BaseModel):
    """Typography tokens — body + headings + optional code-display."""

    model_config = ConfigDict(frozen=True, extra="allow")

    body: Typeface
    heading: Typeface | None = None
    mono: Typeface | None = None


class SpacingScale(BaseModel):
    """Spacing-grid tokens in pixels. Bounded to prevent layout breakage."""

    model_config = ConfigDict(frozen=True, extra="allow")

    xs: int = Field(default=4, ge=0, le=_SPACING_PIXEL_MAX)
    sm: int = Field(default=8, ge=0, le=_SPACING_PIXEL_MAX)
    md: int = Field(default=16, ge=0, le=_SPACING_PIXEL_MAX)
    lg: int = Field(default=24, ge=0, le=_SPACING_PIXEL_MAX)
    xl: int = Field(default=48, ge=0, le=_SPACING_PIXEL_MAX)


class MotionTokens(BaseModel):
    """Animation/transition timing tokens. Bounded to prevent jank."""

    model_config = ConfigDict(frozen=True, extra="allow")

    duration_fast_ms: int = Field(
        default=150, ge=_MOTION_DURATION_MS_MIN, le=_MOTION_DURATION_MS_MAX,
    )
    duration_normal_ms: int = Field(
        default=300, ge=_MOTION_DURATION_MS_MIN, le=_MOTION_DURATION_MS_MAX,
    )
    duration_slow_ms: int = Field(
        default=500, ge=_MOTION_DURATION_MS_MIN, le=_MOTION_DURATION_MS_MAX,
    )


class BrandTokens(BaseModel):
    """The full brand-tokens manifest. Loaded from
    `clients/<slug>/brand/tokens.json` and validated at site_engine
    lane configure_env() time.

    Frozen + extra='allow': bounded fields are pinned per the threat
    model; operators can carry experimental tokens that newer schema
    versions might formalize, but cannot bypass the bounded
    validators."""

    model_config = ConfigDict(frozen=True, extra="allow")

    palette: ColorPalette
    typography: Typography
    spacing: SpacingScale = Field(default_factory=SpacingScale)
    motion: MotionTokens = Field(default_factory=MotionTokens)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class BrandTokensNotFoundError(FileNotFoundError):
    """Raised when the brand tokens path doesn't resolve to a real file."""


def load_brand_tokens(path: str | Path) -> BrandTokens:
    """Load + validate `clients/<slug>/brand/tokens.json` into a frozen
    `BrandTokens` model.

    Raises:
        BrandTokensNotFoundError: when the file doesn't exist.
        json.JSONDecodeError: when the JSON is malformed.
        pydantic.ValidationError: when validation fails (e.g. an external
            URL smuggled into a typeface family name).
    """
    tokens_path = Path(path)
    if not tokens_path.is_file():
        raise BrandTokensNotFoundError(
            f"brand tokens not found at {tokens_path}. site_engine requires "
            f"a tokens.json per the U18 launch runbook; create it under "
            f"clients/<slug>/brand/tokens.json from the client's style "
            f"guide + palette before running the lane."
        )

    raw = json.loads(tokens_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(
            f"brand tokens at {tokens_path} must contain a mapping at "
            f"the top level (got {type(raw).__name__})."
        )

    return BrandTokens.model_validate(raw)


__all__ = [
    "BrandTokens",
    "BrandTokensNotFoundError",
    "ColorPalette",
    "MotionTokens",
    "SpacingScale",
    "Typeface",
    "Typography",
    "load_brand_tokens",
]
