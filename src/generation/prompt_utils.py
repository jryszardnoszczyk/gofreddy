"""Shared prompt utilities for the generation module."""

import unicodedata

from ..common.sanitize import _CONTROL_CHARS, _INJECTION_PATTERN, _ZERO_WIDTH

BEAT_COMPOSITION: dict[str, str] = {
    "hook": "Maximize visual impact: extreme contrast, tight framing, arresting element",
    "setup": "Establish environment: wide shot, balanced composition, warm lighting",
    "rising": "Build tension: tighter framing, increasing contrast, dynamic angles",
    "climax": "Peak intensity: extreme close-up or dramatic wide, high contrast, bold color",
    "resolution": "Release tension: soft lighting, open composition, calm palette",
    "cta": "Direct engagement: centered subject, clean background, clear focal point",
}

CAMERA_TO_COMPOSITION: dict[str, str] = {
    "dolly": "gradually shifting perspective, depth emphasis",
    "tracking": "wide-angle lateral view, subject in motion",
    "pan": "panoramic composition, horizontal sweep",
    "tilt": "vertical perspective shift, dramatic angle",
    "zoom": "tight framing with bokeh background",
    "static": "",
    "handheld": "intimate, slightly off-center framing",
}


def sanitize_prompt(text: str, max_length: int | None = None) -> str:
    """Remove control characters and filter injection patterns. Optionally truncate."""
    cleaned = _CONTROL_CHARS.sub("", text)
    cleaned = unicodedata.normalize("NFKC", cleaned)
    cleaned = _ZERO_WIDTH.sub("", cleaned)
    cleaned = _INJECTION_PATTERN.sub("[FILTERED]", cleaned)
    if max_length is not None:
        return cleaned[:max_length]
    return cleaned
