"""Shared reporting primitives — promoted from ``autoresearch/report_base.py``.

Two consumers today:
- ``configs/{seo,competitive,monitoring,storyboard}/scripts/generate_report.py``
  build HTML+PDF session reports.
- ``harness/review.py`` uses ``scrub`` / ``SECRET_PATTERNS`` to redact
  credentials from review.md and pr-body.md before publishing.

The package is intentionally a single ``report_base`` module + a thin
``scrub`` extraction. Splitting along section comments (parsers / renderers
/ scaffold / pdf / cli) is deferred until the audit plan's Stage 5 actually
needs the categorical separation — splitting framework-ahead-of-need is the
anti-pattern this promotion is avoiding.

Exports use an enumerated ``__all__`` (not a star re-export) so
underscore-prefixed helpers consumers may rely on aren't silently dropped.
"""

from __future__ import annotations

from src.shared.reporting.report_base import (
    BADGE_COLORS,
    BASE_CSS,
    build_html_document,
    common_argparse,
    esc,
    find_chrome,
    html_to_pdf,
    load_json,
    load_jsonl,
    load_markdown,
    md_to_html,
    parse_findings,
    render_findings,
    render_logs_appendix,
    render_report_md,
    render_session_log,
    render_session_summary,
    truncate,
    unavailable_banner,
)
from src.shared.reporting.scrub import SECRET_PATTERNS, scrub

__all__ = [
    "load_json",
    "load_jsonl",
    "load_markdown",
    "parse_findings",
    "render_findings",
    "render_session_log",
    "render_logs_appendix",
    "render_session_summary",
    "render_report_md",
    "unavailable_banner",
    "build_html_document",
    "BASE_CSS",
    "BADGE_COLORS",
    "esc",
    "truncate",
    "md_to_html",
    "find_chrome",
    "html_to_pdf",
    "common_argparse",
    "scrub",
    "SECRET_PATTERNS",
]
