"""Deprecated shim — use ``src.shared.reporting`` directly.

This module was promoted to ``src/shared/reporting/`` (R-#16). All
public symbols are re-exported by name so existing
``from autoresearch.report_base import …`` calls in
``configs/{seo,competitive,monitoring,storyboard}/scripts/generate_report.py``
keep working unchanged. Update those imports at next touch; the shim
will be removed 4 weeks after Phase 3 of the pipeline-simplifications
refactor lands.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "autoresearch.report_base is deprecated; import from src.shared.reporting "
    "(scrub/SECRET_PATTERNS live in src.shared.reporting.scrub).",
    DeprecationWarning,
    stacklevel=2,
)

from src.shared.reporting import (  # noqa: E402
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
from src.shared.reporting.scrub import SECRET_PATTERNS, scrub  # noqa: E402

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
