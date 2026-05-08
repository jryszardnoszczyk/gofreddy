"""Shared report generation infrastructure for all autoresearch workflows.

Provides data loading, HTML helpers, shared renderers, CSS, PDF conversion,
and the build_html_document() scaffold used by all domain-specific generators.

Usage from a domain generator:
    from autoresearch.report_base import (
        load_json, load_jsonl, load_markdown, parse_findings,
        esc, truncate, md_to_html,
        render_findings, render_session_log, render_logs_appendix,
        render_session_summary, render_report_md,
        build_html_document, find_chrome, html_to_pdf,
        common_argparse,
        BASE_CSS, BADGE_COLORS,
    )
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

import mistune

# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def load_json(path: Path) -> dict | list | None:
    """Load a JSON file, returning None on failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        print(f"  WARNING: could not load {path}: {exc}", file=sys.stderr)
        return None


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file into a list of dicts."""
    entries: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except (FileNotFoundError, OSError) as exc:
        print(f"  WARNING: could not load {path}: {exc}", file=sys.stderr)
    return entries


def load_markdown(path: Path) -> str:
    """Load a markdown file, returning empty string on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return ""


# ---------------------------------------------------------------------------
# Findings parser (enhanced with [CATEGORY] badges)
# ---------------------------------------------------------------------------

BADGE_COLORS: dict[str, str] = {
    "CONTENT": "#4caf50",
    "SCHEMA": "#2196f3",
    "INFRA": "#ff9800",
    "PROCESS": "#9c27b0",
    "API": "#f44336",
    "QUALITY": "#00bcd4",
}


_CATEGORY_MAP = {
    "confirmed": "confirmed",
    "disproved": "disproved",
    "observations": "observations",
}

_TITLE_RE = re.compile(r"^\s*(?:\[(\w+)\]\s+)?(.+?)\s*$")
_FIELD_RE = re.compile(r"^\s*(Evidence|Detail)\s*:\s*(.*?)\s*$", re.IGNORECASE)


_LINE_BREAK_TYPES = {"list_item", "paragraph", "block_text", "block_code"}


def _node_text(node: dict | list | str | None) -> str:
    """Flatten a mistune AST node (or children list) back to plain text.

    Block-level containers (list items, paragraphs) emit trailing
    newlines so the field-extractor can run line-by-line.
    """
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_node_text(child) for child in node)
    if isinstance(node, dict):
        ntype = node.get("type")
        if ntype in {"text", "codespan", "inline_html", "html_block", "block_html"}:
            return str(node.get("raw", ""))
        if ntype in {"linebreak", "softbreak"}:
            return "\n"
        children = node.get("children")
        if children:
            rendered = _node_text(children)
            if ntype in _LINE_BREAK_TYPES and not rendered.endswith("\n"):
                rendered += "\n"
            return rendered
        return str(node.get("raw", ""))
    return ""


def _extract_fields(text: str) -> dict[str, str]:
    """Pull ``Evidence:`` / ``Detail:`` values out of a flattened text blob.

    Accepts bullets with or without a leading ``- `` and with or without
    the ``**`` emphasis the agents sometimes drop. Later occurrences of
    the same field win — matches the previous regex-state-machine
    behaviour where the last assignment replaced the first.
    """
    fields: dict[str, str] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.lstrip("-*• ").strip()
        if not stripped:
            continue
        match = _FIELD_RE.match(stripped)
        if match:
            key = match.group(1).lower()
            fields[key] = match.group(2).strip()
    return fields


def parse_findings(md: str) -> dict[str, list[dict]]:
    """Parse findings.md into {category: [{title, evidence, detail, tag}]}.

    Walks the mistune AST: H2 headings switch category (Confirmed /
    Disproved / Observations), each following H3 opens a finding, and
    subsequent sibling list/paragraph nodes contribute ``Evidence:`` /
    ``Detail:`` fields until the next H3 or H2.

    Handles both ``### [TAG] Title`` and plain ``### Title`` formats.
    Preserves the shape consumed by ``render_findings`` downstream.
    """
    result: dict[str, list[dict]] = {
        "confirmed": [],
        "disproved": [],
        "observations": [],
    }

    if not md:
        return result

    ast = mistune.create_markdown(renderer="ast", plugins=["table", "strikethrough"])(md)
    if not isinstance(ast, list):
        return result

    current_category: str | None = None
    current_finding: dict | None = None
    field_buffer: list[str] = []

    def _flush_finding() -> None:
        nonlocal current_finding, field_buffer
        if current_finding is None or current_category is None:
            current_finding = None
            field_buffer = []
            return
        if field_buffer:
            fields = _extract_fields("\n".join(field_buffer))
            if "evidence" in fields:
                current_finding["evidence"] = fields["evidence"]
            if "detail" in fields:
                current_finding["detail"] = fields["detail"]
        result[current_category].append(current_finding)
        current_finding = None
        field_buffer = []

    for node in ast:
        if not isinstance(node, dict):
            continue
        if node.get("type") != "heading":
            # Accumulate content belonging to the open finding.
            if current_finding is not None:
                field_buffer.append(_node_text(node))
            continue

        level = (node.get("attrs") or {}).get("level")
        heading_text = _node_text(node.get("children")).strip()

        if level == 2:
            _flush_finding()
            # First word (case-insensitive) picks the category; anything
            # else resets to "no category" so stray H2 (e.g. a preamble
            # "## Notes") doesn't swallow findings.
            first_word = heading_text.split()[0].lower() if heading_text else ""
            current_category = _CATEGORY_MAP.get(first_word)
            continue

        if level == 3 and current_category is not None:
            _flush_finding()
            match = _TITLE_RE.match(heading_text)
            if match:
                tag = match.group(1)
                title = match.group(2).strip()
            else:
                tag = None
                title = heading_text
            current_finding = {
                "title": title,
                "tag": tag,
                "evidence": "",
                "detail": "",
            }
            continue

        # Any other heading (H1, H4+) closes the open finding without
        # opening a new one — matches the old state machine's behaviour.
        if current_finding is not None:
            _flush_finding()

    _flush_finding()
    return result


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------


def esc(text: str | None) -> str:
    """HTML-escape, returning empty string for None."""
    if text is None:
        return ""
    return html.escape(str(text))


def truncate(text: str | None, maxlen: int = 120) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    s = str(text)
    return s if len(s) <= maxlen else s[: maxlen] + "..."


_md_renderer = mistune.create_markdown(plugins=["table", "strikethrough"])


def md_to_html(text: str) -> str:
    """Convert markdown string to HTML via mistune."""
    if not text:
        return ""
    return str(_md_renderer(text))


def render_report_md(report_md_text: str) -> str:
    """Convert a report.md to styled HTML, stripping the title/metadata block."""
    if not report_md_text:
        return ""
    lines = report_md_text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if (
            line.startswith("# ")
            or not line.strip()
            or line.startswith("**")
            or line.startswith("---")
        ):
            start = i + 1
        else:
            break
    body = "\n".join(lines[start:])
    return f'<div class="report-md">\n{md_to_html(body)}\n</div>'


def unavailable_banner(message: str) -> str:
    """Render a grey 'data unavailable' banner."""
    return (
        f'<div style="background:#f5f5f5;padding:15px;border-radius:8px;'
        f'color:#888;text-align:center;margin:10px 0;">{esc(message)}</div>'
    )


# ---------------------------------------------------------------------------
# Shared renderers
# ---------------------------------------------------------------------------


def render_findings(findings: dict[str, list[dict]], *, heading: str = "Findings") -> str:
    """Render findings with category badges and color-coded borders."""
    all_empty = all(len(v) == 0 for v in findings.values())
    if all_empty:
        return ""

    parts: list[str] = [
        f'<h2><span class="phase-header">Research</span> {esc(heading)}</h2>'
    ]

    for category, css_class in [
        ("confirmed", ""),
        ("disproved", "disproved"),
        ("observations", "observation"),
    ]:
        items = findings.get(category, [])
        if not items:
            continue
        parts.append(f"<h3>{category.title()} ({len(items)})</h3>")
        for f in items:
            cls = f" {css_class}" if css_class else ""
            title = esc(f.get("title", ""))
            tag = f.get("tag")
            evidence = esc(f.get("evidence", ""))
            detail = esc(f.get("detail", ""))

            # Category badge
            badge_html = ""
            if tag:
                color = BADGE_COLORS.get(tag, "#757575")
                badge_html = (
                    f'<span class="badge" style="background:{color};color:#fff;'
                    f'padding:2px 8px;border-radius:3px;font-size:0.75em;'
                    f'margin-right:6px;">{esc(tag)}</span>'
                )

            evidence_html = (
                f"<br><strong>Evidence:</strong> {evidence}" if evidence else ""
            )
            detail_html = (
                f"<br><strong>Detail:</strong> {detail}" if detail else ""
            )

            parts.append(
                f'<div class="finding{cls}">{badge_html}<strong>{title}</strong>'
                f"{evidence_html}{detail_html}</div>"
            )

    return "\n".join(parts)


def render_session_log(entries: list[dict], *, extra_columns: list[str] | None = None) -> str:
    """Render results.jsonl as a session log table.

    Color-codes kept/discarded/rework rows. ``extra_columns`` adds domain-specific
    columns (e.g. ``["quality_score", "strategist_test"]``).
    """
    if not entries:
        return ""

    extra_cols = extra_columns or []
    extra_th = "".join(f"<th>{esc(c)}</th>" for c in extra_cols)

    parts: list[str] = [
        '<h2><span class="phase-header">Session</span> Iteration Log</h2>',
        '<div class="iteration-log">',
        "<table>",
        f"<thead><tr><th>Iter</th><th>Type</th><th>Status</th>{extra_th}<th>Notes</th></tr></thead>",
        "<tbody>",
    ]

    STATUS_COLORS = {
        "kept": "#e8f5e9",
        "complete": "#e8f5e9",
        "done": "#e8f5e9",
        "pass": "#e8f5e9",
        "discarded": "#fce4ec",
        "dropped": "#fce4ec",
        "fail": "#fce4ec",
        "failed": "#fce4ec",
        "rate_limited": "#fff3e0",
        "rework": "#fff8e1",
    }

    for entry in entries:
        iteration = esc(str(entry.get("iteration", "")))
        etype = esc(entry.get("type", ""))
        status = entry.get("status", "")
        row_bg = STATUS_COLORS.get(status, "")
        style = f' style="background:{row_bg}"' if row_bg else ""

        # Build notes from notable fields
        notes_parts: list[str] = []
        for key in ("page", "story", "competitor", "title", "approach", "notes"):
            val = entry.get(key)
            if val:
                notes_parts.append(str(val))

        # Numeric context
        for key in (
            "pages_found", "pages_audited",
            "avg_infra_score", "mentions_loaded", "stories_found",
            "word_count", "sections",
        ):
            val = entry.get(key)
            if val is not None:
                notes_parts.append(f"{key}={val}")

        summary = esc(truncate(" | ".join(notes_parts), 200))

        # Extra columns
        extra_td = ""
        for col in extra_cols:
            extra_td += f"<td>{esc(str(entry.get(col, '')))}</td>"

        parts.append(
            f"<tr{style}><td>{iteration}</td><td>{etype}</td>"
            f"<td>{esc(status)}</td>{extra_td}<td>{summary}</td></tr>"
        )

    parts.extend(["</tbody>", "</table>", "</div>"])
    return "\n".join(parts)


def render_logs_appendix(
    logs_dir: Path,
    *,
    label: str = "Iteration Logs",
    glob: str = "*.log",
    max_per_file_chars: int = 0,
    scrub_pii: bool = False,
) -> str:
    """Render log files (matching ``glob``) as a collapsible appendix.

    The default behaviour (``glob="*.log"``, no truncation, no scrub) preserves
    backwards compatibility with the original signature. Pass
    ``glob="*.log.err"`` + ``max_per_file_chars=12000`` + ``scrub_pii=True`` to
    surface autoresearch agent transcripts (the .err files contain ~80% of a
    session's bytes; truncating + scrubbing keeps the appendix viewable).
    """
    if not logs_dir.is_dir():
        return ""
    log_files = sorted(logs_dir.glob(glob))
    if not log_files:
        return ""

    if scrub_pii:
        from .scrub import scrub as _scrub_text
    else:
        _scrub_text = None  # type: ignore[assignment]

    parts: list[str] = [
        f'<h2><span class="phase-header">Appendix</span> {esc(label)}</h2>'
    ]
    for log_file in log_files:
        try:
            content = log_file.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if not content:
            continue

        original_len = len(content)
        if max_per_file_chars > 0 and original_len > max_per_file_chars:
            half = max_per_file_chars // 2
            content = (
                content[:half]
                + f"\n\n[...truncated {original_len - max_per_file_chars} chars...]\n\n"
                + content[-half:]
            )
        if _scrub_text is not None:
            content = _scrub_text(content)

        name = log_file.stem.replace("_", " ").title()
        kb = original_len // 1024
        size_label = f"{kb} KB" if kb else f"{original_len} chars"
        # Collapsible for everything in non-default modes (transcripts are
        # always large), or above 2000 chars in default mode.
        if max_per_file_chars > 0 or len(content) > 2000:
            parts.append(
                f"<details><summary><strong>{esc(name)}</strong> "
                f"({size_label})</summary>"
                f'<div class="appendix-log">{esc(content)}</div></details>'
            )
        else:
            parts.append(f"<h3>{esc(name)}</h3>")
            parts.append(f'<div class="appendix-log">{esc(content)}</div>')

    return "\n".join(parts) if len(parts) > 1 else ""


def render_session_summary(summary: dict | None) -> str:
    """Render session_summary.json as a metadata card."""
    if not summary:
        return ""
    iterations = summary.get("iterations", {})
    errors = summary.get("errors", [])
    deliverables = summary.get("deliverables", [])
    quality = summary.get("quality_metrics", {})

    error_html = ""
    if errors:
        error_html = (
            f"<br><strong>Errors:</strong> "
            f"{esc(', '.join(str(e) for e in errors))}"
        )

    deliverables_html = ""
    if deliverables:
        items = "".join(f"<li>{esc(str(d))}</li>" for d in deliverables)
        deliverables_html = f"<br><strong>Deliverables:</strong><ul>{items}</ul>"

    return f"""\
<h2><span class="phase-header">Session</span> Summary</h2>
<div class="session-summary">
  <strong>Status:</strong> {esc(summary.get('status', ''))} &nbsp;|&nbsp;
  <strong>Exit Reason:</strong> {esc(summary.get('exit_reason', ''))} &nbsp;|&nbsp;
  <strong>Generated:</strong> {esc(summary.get('generated_at', ''))}<br>
  <strong>Iterations:</strong>
    total={iterations.get('total', '?')},
    productive={iterations.get('productive', '?')},
    blocked={iterations.get('blocked', '?')},
    failed={iterations.get('failed', '?')},
    skipped={iterations.get('skipped', '?')}
  {error_html}
  {deliverables_html}
</div>
"""


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

BASE_CSS = """\
body { font-family: 'Helvetica Neue', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; color: #1a1a2e; }
h1 { color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 10px; }
h2 { color: #0f3460; margin-top: 40px; border-bottom: 2px solid #e94560; padding-bottom: 5px; page-break-before: always; }
h2:first-of-type { page-break-before: avoid; }
h3 { color: #e94560; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; }
td, th { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 0.85em; }
th { background: #f0f4ff; }
.phase-header { background: #0f3460; color: white; padding: 8px 15px; border-radius: 6px; margin-top: 30px; }
.finding { background: #f9fbe7; padding: 10px; border-left: 3px solid #8bc34a; margin: 8px 0; border-radius: 4px; }
.finding.disproved { border-left-color: #ef5350; background: #fce4ec; }
.finding.observation { border-left-color: #42a5f5; background: #e3f2fd; }
.iteration-log { font-size: 0.8em; }
.appendix-log { background: #f5f5f5; padding: 12px; border-radius: 6px; margin: 8px 0; font-size: 0.85em; white-space: pre-wrap; font-family: monospace; max-height: 400px; overflow-y: auto; }
.session-summary { background: #e8eaf6; padding: 15px; border-radius: 8px; margin: 10px 0; }
.report-md blockquote { border-left: 3px solid #0f3460; padding-left: 12px; color: #555; margin: 10px 0; }
.report-md code { background: #f0f4ff; padding: 2px 6px; border-radius: 3px; font-size: 0.85em; }
.report-md hr { border: none; border-top: 2px solid #e94560; margin: 30px 0; page-break-before: avoid; }
.report-md ol, .report-md ul { padding-left: 20px; }
.report-md em { color: #555; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 600; }
.story-meta { background: #f0f4ff; padding: 15px; border-radius: 8px; margin: 10px 0; }
details { margin: 8px 0; }
details summary { cursor: pointer; font-weight: 600; padding: 8px; background: #f0f4ff; border-radius: 4px; }
details[open] summary { border-radius: 4px 4px 0 0; }

/* ===========================================================================
 * .rprt-* section-element library (spec A1)
 * Used by render_report.py composers (geo, competitive, monitoring, storyboard).
 * 14 primitives covering content + transcript surfaces. Lane-agnostic.
 * docs/plans/2026-05-07-003-self-improving-report-rendering.md §A1
 * =========================================================================== */
.rprt-page { max-width: 920px; margin: 0 auto; padding: 0 32px; font-family: 'Inter Tight', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #0a1929; }
.rprt-meta { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid #e6dfc8; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; letter-spacing: 0.04em; color: #6b7280; text-transform: uppercase; margin-bottom: 32px; }
.rprt-eyebrow { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #d62828; margin-bottom: 12px; }
.rprt-hero h1 { font-family: 'Fraunces', Georgia, serif; font-weight: 300; font-size: 56px; line-height: 1; letter-spacing: -0.03em; margin: 0 0 16px; color: #0a1929; border: none; padding: 0; }
.rprt-hero p { font-size: 17px; color: #4b5563; max-width: 640px; line-height: 1.55; margin: 0 0 24px; }
.rprt-prose { font-size: 16px; line-height: 1.65; color: #1f2937; margin: 0 0 18px; }
.rprt-prose strong { color: #0a1929; font-weight: 700; }
.rprt-prose code { background: #f5f2e8; padding: 1px 6px; border-radius: 3px; font-size: 13px; font-family: 'JetBrains Mono', ui-monospace, monospace; }
.rprt-callout { background: #ffffff; border-left: 3px solid #1d4ed8; padding: 16px 22px; margin: 16px 0; border-radius: 6px; box-shadow: 0 1px 2px rgba(10,25,41,.04); }
.rprt-callout.success { border-left-color: #15803d; }
.rprt-callout.warn { border-left-color: #b58105; }
.rprt-callout.critical { border-left-color: #d62828; }
.rprt-callout .ckind { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 10px; font-weight: 700; letter-spacing: 0.10em; text-transform: uppercase; margin-bottom: 6px; color: #1d4ed8; }
.rprt-callout.success .ckind { color: #15803d; } .rprt-callout.warn .ckind { color: #b58105; } .rprt-callout.critical .ckind { color: #d62828; }
.rprt-callout .ctitle { font-size: 16px; font-weight: 700; color: #0a1929; margin-bottom: 4px; }
.rprt-stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }
.rprt-stat-tile { background: #ffffff; border: 1px solid #e6dfc8; border-radius: 10px; padding: 16px 18px; box-shadow: 0 1px 2px rgba(10,25,41,.04); }
.rprt-stat-tile .num { font-family: 'Fraunces', Georgia, serif; font-weight: 400; font-size: 30px; line-height: 1; letter-spacing: -0.02em; color: #0f3460; margin-bottom: 6px; }
.rprt-stat-tile .label { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 10px; text-transform: uppercase; letter-spacing: 0.10em; color: #6b7280; font-weight: 600; }
.rprt-key-table { width: 100%; border-collapse: collapse; margin: 18px 0; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 2px rgba(10,25,41,.04); border: 1px solid #e6dfc8; }
.rprt-key-table thead th { background: #0a1929; color: white; text-align: left; padding: 12px 16px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 10px; letter-spacing: 0.10em; text-transform: uppercase; font-weight: 700; }
.rprt-key-table tbody td { padding: 14px 16px; border-top: 1px solid #e6dfc8; font-size: 13.5px; line-height: 1.5; vertical-align: top; }
.rprt-key-table tbody tr:first-child td { border-top: none; }
.rprt-finding-card { display: grid; grid-template-columns: 80px 1fr; gap: 14px; padding: 12px 16px; background: #ffffff; border: 1px solid #e6dfc8; border-radius: 8px; margin-bottom: 6px; font-size: 13.5px; line-height: 1.55; align-items: start; }
.rprt-finding-card.disproved { opacity: 0.65; border-left: 2px solid #fde8e8; }
.rprt-finding-tag { padding: 3px 8px; border-radius: 4px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 9px; font-weight: 800; letter-spacing: 0.06em; text-align: center; }
.rprt-finding-tag.SEO, .rprt-finding-tag.API { background: #dbeafe; color: #1e40af; }
.rprt-finding-tag.QUALITY { background: #ccf5ec; color: #0d6e5c; }
.rprt-finding-tag.CONTENT { background: #f3e8ff; color: #6b21a8; }
.rprt-finding-tag.SCHEMA { background: #fef3c7; color: #92400e; }
.rprt-finding-tag.INFRA { background: #fce7f1; color: #9b1c4f; }
.rprt-finding-tag.PROCESS { background: #e0e7ff; color: #3730a3; }
.rprt-finding-tag.REPORT { background: #e2e8f0; color: #1f2937; }
.rprt-action-list { display: flex; flex-direction: column; gap: 8px; margin: 16px 0; }
.rprt-action-row { display: grid; grid-template-columns: 36px 1fr; gap: 16px; align-items: start; padding: 14px 18px; background: #ffffff; border: 1px solid #e6dfc8; border-radius: 8px; }
.rprt-action-row .priority { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 16px; font-weight: 800; color: #d62828; line-height: 1; padding-top: 2px; }
.rprt-pull-quote { margin: 24px 0; padding: 22px 28px; background: #ffffff; border: 1px solid #e6dfc8; border-radius: 12px; position: relative; box-shadow: 0 1px 2px rgba(10,25,41,.04); }
.rprt-pull-quote::before { content: '"'; position: absolute; top: 8px; left: 16px; font-family: 'Fraunces', Georgia, serif; font-size: 64px; line-height: 1; color: #d62828; opacity: 0.18; }
.rprt-pull-quote .qtext { font-family: 'Fraunces', Georgia, serif; font-size: 18px; line-height: 1.4; font-weight: 400; color: #0a1929; font-style: italic; }
.rprt-pull-quote .qattr { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: #6b7280; margin-top: 12px; font-weight: 700; }
.rprt-evidence-quote { margin: 12px 0; padding: 12px 18px; background: #f5f2e8; border-left: 2px solid #d4c8a3; border-radius: 4px; font-size: 13.5px; line-height: 1.55; color: #1f2937; font-style: italic; }
.rprt-page-screenshot { margin: 18px 0; border-radius: 12px; overflow: hidden; border: 1px solid #e6dfc8; box-shadow: 0 1px 2px rgba(10,25,41,.04), 0 8px 24px rgba(10,25,41,.06); }
.rprt-page-screenshot img { display: block; width: 100%; height: auto; }
.rprt-page-screenshot .caption { padding: 10px 16px; background: #f5f2e8; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; color: #6b7280; }
.rprt-faq { display: flex; flex-direction: column; gap: 4px; margin: 16px 0; }
.rprt-faq details { background: #ffffff; border: 1px solid #e6dfc8; border-radius: 8px; padding: 0; margin: 0; }
.rprt-faq details summary { padding: 14px 18px; font-size: 14px; font-weight: 600; color: #0a1929; cursor: pointer; background: #ffffff; border-radius: 8px; }
.rprt-faq details[open] summary { border-bottom: 1px solid #e6dfc8; border-radius: 8px 8px 0 0; }
.rprt-faq details > *:not(summary) { padding: 0 18px 14px; font-size: 13.5px; line-height: 1.6; color: #1f2937; }
.rprt-section-divider { height: 1px; background: #e6dfc8; margin: 32px 0; }
.rprt-reasoning-trail { margin: 16px 0; }
.rprt-beat-card { display: grid; grid-template-columns: 80px 1fr; gap: 14px; padding: 10px 14px; background: #ffffff; border: 1px solid #e6dfc8; border-radius: 8px; margin-bottom: 6px; font-size: 13px; line-height: 1.55; align-items: start; }
.rprt-beat-card .kind { padding: 3px 7px; border-radius: 3px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 9px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; align-self: start; margin-top: 1px; background: #f5f2e8; color: #4b5563; }
.rprt-beat-card .kind.first_move { background: #0a1929; color: #fff; }
.rprt-beat-card .kind.decide, .rprt-beat-card .kind.adapt { background: #fdf3d4; color: #b58105; }
.rprt-beat-card .kind.hit_failure { background: #fde8e8; color: #d62828; }
.rprt-beat-card .kind.recover, .rprt-beat-card .kind.ship { background: #dcf6e3; color: #15803d; }
.rprt-beat-card .text { font-family: 'Fraunces', Georgia, serif; font-style: italic; color: #1f2937; }
.rprt-pivot-callout { background: linear-gradient(135deg, #fdf3d4 0%, #fde8e8 100%); border: 1px solid #d4c8a3; border-radius: 12px; padding: 18px 22px; margin: 16px 0; }
.rprt-pivot-callout .pkind { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 10px; letter-spacing: 0.10em; text-transform: uppercase; font-weight: 800; color: #d62828; margin-bottom: 8px; }
.rprt-meta-pattern { background: #0a1929; color: white; border-radius: 14px; padding: 20px 24px; margin: 20px 0; }
.rprt-meta-pattern .label { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: #fbbf24; font-weight: 800; margin-bottom: 8px; }
.rprt-meta-pattern h3 { font-family: 'Fraunces', Georgia, serif; font-size: 22px; font-weight: 400; color: white; margin: 0 0 8px; border: none; padding: 0; }
.rprt-meta-pattern p { font-size: 13.5px; line-height: 1.6; color: rgba(255,255,255,.85); margin: 0; }
.rprt-meta-pattern code { background: rgba(255,255,255,.10); color: #fbbf24; padding: 1px 5px; border-radius: 3px; font-family: 'JetBrains Mono', ui-monospace, monospace; }

@media print {
  .rprt-page { max-width: 100%; padding: 0 24px; }
  .rprt-stat-grid { page-break-inside: avoid; }
  .rprt-finding-card, .rprt-action-row, .rprt-callout, .rprt-pivot-callout { page-break-inside: avoid; box-shadow: none; }
  .rprt-key-table { box-shadow: none; }
  .rprt-key-table thead { display: table-header-group; }
  .rprt-page-screenshot { box-shadow: none; }
  .rprt-meta-pattern { background: var(--meta-bg, #0a1929); -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}

/* ===========================================================================
 * Phase B1 — Per-lane visual themes
 * Each .rprt-theme-<lane> overrides CSS vars consumed by the .rprt-* primitives
 * above. Add a class to .rprt-page (e.g. <div class="rprt-page rprt-theme-geo">)
 * and the report inherits that lane's identity. Uses cascade — defaults stay
 * in .rprt-page so lane-less callers (legacy) keep working.
 * Spec section B1 (docs/plans/2026-05-07-003-self-improving-report-rendering.md
 * + 2026-05-08-002-self-improving-reports-gap-audit.md).
 * =========================================================================== */
.rprt-page {
  /* Defaults — match the previous hardcoded palette. Lane themes override. */
  --accent: #d62828;          /* red — pull-quote glyph, eyebrow, action priority */
  --accent-soft: #fde8e8;     /* light tint for badges */
  --headline-color: #0a1929;  /* serif headlines */
  --headline-typo: 'Fraunces', Georgia, serif;
  --body-color: #1f2937;
  --body-typo: 'Inter Tight', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --bg-tone: #ffffff;
  --bg-soft: #f5f2e8;
  --border-color: #e6dfc8;
  --meta-bg: #0a1929;
  --meta-fg: #ffffff;
}
.rprt-page { background: var(--bg-tone); color: var(--body-color); font-family: var(--body-typo); }
.rprt-hero h1 { font-family: var(--headline-typo); color: var(--headline-color); }
.rprt-eyebrow { color: var(--accent); }
.rprt-pull-quote::before { color: var(--accent); }
.rprt-pull-quote .qtext { font-family: var(--headline-typo); color: var(--headline-color); }
.rprt-action-row .priority { color: var(--accent); }
.rprt-callout { border-left-color: var(--accent); }
.rprt-callout .ckind { color: var(--accent); }
.rprt-stat-tile { background: var(--bg-tone); border-color: var(--border-color); }
.rprt-stat-tile .num { font-family: var(--headline-typo); color: var(--headline-color); }
.rprt-key-table { background: var(--bg-tone); border-color: var(--border-color); }
.rprt-key-table thead th { background: var(--headline-color); color: var(--meta-fg); }
.rprt-finding-card { background: var(--bg-tone); border-color: var(--border-color); }
.rprt-pivot-callout .pkind { color: var(--accent); }
.rprt-meta-pattern { background: var(--meta-bg); color: var(--meta-fg); }
.rprt-meta-pattern h3 { font-family: var(--headline-typo); color: var(--meta-fg); }
.rprt-prose code { background: var(--bg-soft); }
.rprt-evidence-quote { background: var(--bg-soft); border-color: var(--border-color); }
.rprt-beat-card { background: var(--bg-tone); border-color: var(--border-color); }
.rprt-beat-card .text { font-family: var(--headline-typo); color: var(--body-color); }

/* GEO — clinical / typographic / data-tables-first */
.rprt-page.rprt-theme-geo {
  --accent: #2c5282;           /* clinical blue */
  --accent-soft: #dbeafe;
  --headline-color: #1a365d;
  --headline-typo: 'Charter', 'Iowan Old Style', Georgia, serif;
  --body-typo: 'Inter Tight', sans-serif;
  --bg-tone: #f7fafc;
  --bg-soft: #edf2f7;
  --border-color: #cbd5e0;
  --meta-bg: #1a365d;
}

/* COMPETITIVE — editorial / pull-quote heavy / red accent */
.rprt-page.rprt-theme-competitive {
  --accent: #c53030;
  --accent-soft: #fed7d7;
  --headline-color: #1a202c;
  --headline-typo: 'Source Serif 4', 'Fraunces', Georgia, serif;
  --body-typo: 'Source Sans 3', 'Inter Tight', sans-serif;
  --bg-tone: #fffaf0;
  --bg-soft: #faf089;
  --border-color: #e0d8b6;
  --meta-bg: #2d1b1b;
}

/* MONITORING — ops dashboard / dense / green accent */
.rprt-page.rprt-theme-monitoring {
  --accent: #2f855a;
  --accent-soft: #c6f6d5;
  --headline-color: #1a202c;
  --headline-typo: 'IBM Plex Sans', 'Inter', sans-serif;
  --body-typo: 'IBM Plex Sans', 'Inter Tight', sans-serif;
  --bg-tone: #f0fff4;
  --bg-soft: #e6fffa;
  --border-color: #b2f5ea;
  --meta-bg: #22543d;
}

/* STORYBOARD — cinematic / dark mode / amber accent */
.rprt-page.rprt-theme-storyboard {
  --accent: #ed8936;
  --accent-soft: #feebc8;
  --headline-color: #f7fafc;
  --headline-typo: 'Inter', 'Inter Tight', sans-serif;
  --body-typo: 'Inter', sans-serif;
  --body-color: #e2e8f0;
  --bg-tone: #1a202c;
  --bg-soft: #2d3748;
  --border-color: #4a5568;
  --meta-bg: #ed8936;
  --meta-fg: #1a202c;
}
.rprt-page.rprt-theme-storyboard h2,
.rprt-page.rprt-theme-storyboard h3 { color: #f6e05e; border-bottom-color: #4a5568; }
.rprt-page.rprt-theme-storyboard .rprt-stat-tile,
.rprt-page.rprt-theme-storyboard .rprt-callout,
.rprt-page.rprt-theme-storyboard .rprt-finding-card,
.rprt-page.rprt-theme-storyboard .rprt-key-table,
.rprt-page.rprt-theme-storyboard .rprt-beat-card { background: #2d3748; }
.rprt-page.rprt-theme-storyboard .rprt-key-table thead th { background: #ed8936; color: #1a202c; }

/* MARKETING_AUDIT — advisory / amber-on-cream / Playfair */
.rprt-page.rprt-theme-marketing_audit {
  --accent: #d69e2e;
  --accent-soft: #faf089;
  --headline-color: #744210;
  --headline-typo: 'Playfair Display', 'Fraunces', Georgia, serif;
  --body-typo: 'Source Sans 3', 'Inter Tight', sans-serif;
  --bg-tone: #fffff0;
  --bg-soft: #fefce8;
  --border-color: #ecc94b;
  --meta-bg: #744210;
}
"""


# ---------------------------------------------------------------------------
# HTML document scaffold
# ---------------------------------------------------------------------------


def build_html_document(
    title: str,
    sections: list[tuple[str, str]],
    *,
    css_extra: str = "",
) -> str:
    """Build a complete HTML document from a list of (section_title, section_html).

    Empty section_html entries are skipped. section_title is ignored in the
    output (it's for the caller's reference) — the section_html should contain
    its own ``<h2>`` etc.
    """
    body = "\n".join(html_content for _, html_content in sections if html_content)

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>
{BASE_CSS}
{css_extra}
</style>
</head>
<body>
{body}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# PDF conversion
# ---------------------------------------------------------------------------

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "chromium",
    "google-chrome",
    "google-chrome-stable",
    "chromium-browser",
]


def find_chrome() -> str | None:
    """Find an available Chrome/Chromium binary."""
    import shutil

    for candidate in CHROME_CANDIDATES:
        if "/" in candidate:
            if Path(candidate).is_file():
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def html_to_screenshot(
    html_path: Path,
    png_path: Path,
    *,
    viewport_width: int = 1280,
    viewport_height: int = 1600,
) -> bool:
    """Convert HTML to PNG screenshot using headless Chrome. Returns True on success.

    Sibling to html_to_pdf; uses Chrome's --screenshot flag at the given viewport.
    Default 1280x1600 captures hero + first ~3 fold-lines of a typical report —
    enough surface for the visual sub-judge (Gemini Flash) to grade typography,
    hierarchy, and density without redundancy.

    Spec section A2 (docs/plans/2026-05-07-003-self-improving-report-rendering.md).
    """
    chrome = find_chrome()
    if not chrome:
        print(
            "  WARNING: No Chrome/Chromium found. Skipping screenshot.",
            file=sys.stderr,
        )
        return False
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--screenshot={png_path}",
        f"--window-size={viewport_width},{viewport_height}",
        str(html_path),
    ]
    print(f"  Capturing screenshot with: {Path(chrome).name}", file=sys.stderr)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and png_path.exists():
            print(
                f"  Screenshot saved: {png_path} ({png_path.stat().st_size // 1024}KB)",
                file=sys.stderr,
            )
            return True
        else:
            print(
                f"  Screenshot failed (rc={result.returncode})", file=sys.stderr
            )
            if result.stderr:
                print(f"  stderr: {result.stderr[:500]}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("  Screenshot timed out after 60s.", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"  Chrome binary not found at: {chrome}", file=sys.stderr)
        return False


def html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Convert HTML to PDF using headless Chrome. Returns True on success."""
    chrome = find_chrome()
    if not chrome:
        print(
            "  WARNING: No Chrome/Chromium found. Skipping PDF generation.",
            file=sys.stderr,
        )
        return False

    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={pdf_path}",
        "--print-to-pdf-no-header",
        str(html_path),
    ]
    print(f"  Converting to PDF with: {Path(chrome).name}", file=sys.stderr)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and pdf_path.exists():
            print(
                f"  PDF generated: {pdf_path} ({pdf_path.stat().st_size // 1024}KB)",
                file=sys.stderr,
            )
            return True
        else:
            print(
                f"  PDF generation failed (rc={result.returncode})", file=sys.stderr
            )
            if result.stderr:
                print(f"  stderr: {result.stderr[:500]}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("  PDF generation timed out after 60s.", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"  Chrome binary not found at: {chrome}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Common argparse
# ---------------------------------------------------------------------------


def common_argparse(description: str) -> argparse.ArgumentParser:
    """Create an argument parser with the shared session_dir + flags."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "session_dir",
        type=Path,
        help="Path to the session directory",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Skip PDF generation (HTML only)",
    )
    parser.add_argument(
        "--skip-logs",
        action="store_true",
        help="Skip iteration log appendix",
    )
    return parser
