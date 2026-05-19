"""HTML allowlist sanitizer for site_engine variants (U15b / TD-43 Pass 1).

Per the U15b §approach Pass-1 structural gate: section HTML goes
through nh3 (Rust-backed bleach successor) with a section-scoped
allowlist. Sanitized output is compared against input; ANY difference
fails the variant.

OWASP XSS filter-evasion vectors are the library's responsibility
(nh3/ammonia maintains their own bypass corpus); this module just
wires the allowlist + delta-detection logic that the lane's
structural gate calls.

Per Pass-5 audit: 3-4 representative round-trip assertions in tests/
verify the wiring (script tag, iframe srcdoc, javascript: URL); we
don't maintain a separate OWASP corpus here.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Section-scoped allowlist per the U15b plan §approach Pass-1.
# Tags + per-tag attributes + URL schemes.
_ALLOWED_TAGS: frozenset[str] = frozenset({
    "a", "article", "aside", "blockquote", "br", "button", "code",
    "details", "div", "em", "figcaption", "figure", "footer", "h1",
    "h2", "h3", "h4", "h5", "h6", "header", "hr", "img", "li", "main",
    "nav", "ol", "p", "picture", "pre", "section", "small", "source",
    "span", "strong", "summary", "table", "tbody", "td", "th", "thead",
    "tr", "ul",
})

# Allowed attributes per-tag. nh3 takes a dict-of-frozensets for the
# attribute allowlist.
_ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "*": {"id", "class", "lang", "dir", "title", "aria-label",
          "aria-hidden", "aria-describedby", "aria-labelledby",
          "role", "tabindex", "data-section", "data-element",
          "data-recommended", "data-layout"},
    "a": {"href", "target", "rel"},  # operator-managed rel attribute
    "button": {"type", "disabled", "name", "value", "form"},
    "img": {"src", "srcset", "alt", "width", "height", "loading",
            "decoding"},
    "source": {"src", "srcset", "type", "media", "sizes"},
    "details": {"open"},
    "table": {"role"},
    "th": {"scope", "colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
}

# URL scheme allowlist for href + src attributes. Per Pass-1: {https,
# data:image/*, relative}. http rejected (forces https in publish-
# context); data:image/* allowed for inline svg/png; relative allowed.
_ALLOWED_URL_SCHEMES: frozenset[str] = frozenset({"https", "mailto", "tel"})


@dataclass(frozen=True)
class SanitizerDelta:
    """One difference between input and sanitized output."""

    kind: str   # "tag_stripped" | "attribute_stripped" | "url_rejected"
    detail: str


@dataclass(frozen=True)
class SanitizerResult:
    """Result of section-HTML sanitization.

    `clean` is the sanitized output. `deltas` is the list of
    differences from input; non-empty list = structural-gate
    fail. `safe` is a derived bool — True when deltas is empty
    (input passed through unchanged) AND no errors were raised
    during sanitization.
    """

    clean: str
    deltas: list[SanitizerDelta]
    safe: bool


def sanitize_section_html(raw_html: str) -> SanitizerResult:
    """Run the section-scoped allowlist sanitizer.

    Returns a `SanitizerResult` with the sanitized output + delta
    list. The caller (session_eval_site_engine.structural_gate)
    fails the variant when deltas is non-empty.

    Per defense-in-depth: this same sanitizer runs again at publish
    time (per U15b §approach publish-pipeline-sanitizer). Two-pass
    enforcement means a single-stage bypass doesn't reach production.
    """
    try:
        import nh3
    except ImportError as exc:  # pragma: no cover — nh3 is in main deps
        raise ImportError(
            "nh3 is required for site_engine HTML sanitization. "
            "Verify it's installed via the project's main dependencies."
        ) from exc

    # Build the attribute allowlist in nh3's shape (dict[str, set[str]]).
    attributes = {k: set(v) for k, v in _ALLOWED_ATTRIBUTES.items()}

    clean = nh3.clean(
        raw_html,
        tags=set(_ALLOWED_TAGS),
        attributes=attributes,
        url_schemes=set(_ALLOWED_URL_SCHEMES),
        # `link_rel=None` lets us manage `rel` as a normal attribute
        # so well-formed inputs survive the round-trip unchanged.
        # The publish-pipeline sanitizer (defense-in-depth) re-adds
        # `rel="noopener noreferrer"` at publish time.
        link_rel=None,
        strip_comments=True,
    )

    deltas = _diff_to_deltas(raw_html, clean)
    return SanitizerResult(clean=clean, deltas=deltas, safe=(not deltas))


def _diff_to_deltas(raw: str, clean: str) -> list[SanitizerDelta]:
    """Detect what was stripped between raw input and sanitized output.

    nh3 doesn't expose a structured diff API; the simplest robust
    check is "did the output change?". For better error messages we
    do a lightweight string-level diff to identify the most likely
    cause class (stripped tag vs. stripped attribute vs. rejected URL).

    A more precise diff (HTML parse tree comparison) is deferred —
    the structural gate just needs to fail-loud; operator looks at
    the variant to see what was wrong.
    """
    if raw == clean:
        return []

    deltas: list[SanitizerDelta] = []

    # Cheap heuristics — flag the most common attack-vector classes.
    raw_lower = raw.lower()
    if "<script" in raw_lower and "<script" not in clean.lower():
        deltas.append(SanitizerDelta(
            kind="tag_stripped",
            detail="<script> tag stripped (anti-XSS).",
        ))
    if "<iframe" in raw_lower and "<iframe" not in clean.lower():
        deltas.append(SanitizerDelta(
            kind="tag_stripped",
            detail="<iframe> tag stripped (anti-clickjack).",
        ))
    if "<object" in raw_lower and "<object" not in clean.lower():
        deltas.append(SanitizerDelta(
            kind="tag_stripped",
            detail="<object> tag stripped.",
        ))
    if "<embed" in raw_lower and "<embed" not in clean.lower():
        deltas.append(SanitizerDelta(
            kind="tag_stripped",
            detail="<embed> tag stripped.",
        ))
    if "javascript:" in raw_lower and "javascript:" not in clean.lower():
        deltas.append(SanitizerDelta(
            kind="url_rejected",
            detail="javascript: URL scheme rejected.",
        ))
    if "data:text" in raw_lower and "data:text" not in clean.lower():
        deltas.append(SanitizerDelta(
            kind="url_rejected",
            detail="data:text/* URL scheme rejected (anti-XSS).",
        ))
    if "<svg" in raw_lower and "<svg" not in clean.lower():
        deltas.append(SanitizerDelta(
            kind="tag_stripped",
            detail="<svg> tag stripped (out of section allowlist).",
        ))
    if "onerror=" in raw_lower or "onclick=" in raw_lower:
        if "onerror=" not in clean.lower() and "onclick=" not in clean.lower():
            deltas.append(SanitizerDelta(
                kind="attribute_stripped",
                detail="on* event-handler attribute(s) stripped.",
            ))

    if not deltas:
        # Catch-all: output differs but no specific class identified.
        # Operator must inspect the variant to see what was stripped.
        deltas.append(SanitizerDelta(
            kind="tag_stripped",
            detail="Non-allowlisted construct stripped (inspect variant for details).",
        ))
    return deltas


__all__ = [
    "SanitizerDelta",
    "SanitizerResult",
    "sanitize_section_html",
]
