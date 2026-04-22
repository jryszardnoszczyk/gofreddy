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


def render_logs_appendix(logs_dir: Path, *, label: str = "Iteration Logs") -> str:
    """Render iteration log files as a collapsible appendix."""
    if not logs_dir.is_dir():
        return ""
    log_files = sorted(logs_dir.glob("*.log"))
    if not log_files:
        return ""

    parts: list[str] = [
        f'<h2><span class="phase-header">Appendix</span> {esc(label)}</h2>'
    ]
    for log_file in log_files:
        try:
            content = log_file.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not content:
            continue
        name = log_file.stem.replace("_", " ").title()
        # Collapsible for large logs
        if len(content) > 2000:
            parts.append(
                f"<details><summary><strong>{esc(name)}</strong> "
                f"({len(content)} chars)</summary>"
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
