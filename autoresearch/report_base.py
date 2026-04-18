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


def parse_findings(md: str) -> dict[str, list[dict]]:
    """Parse findings.md into {category: [{title, evidence, detail, tag}]}.

    Handles both ``### [TAG] Title`` and plain ``### Title`` formats.
    """
    result: dict[str, list[dict]] = {
        "confirmed": [],
        "disproved": [],
        "observations": [],
    }
    current_category = ""
    current_finding: dict | None = None

    for line in md.splitlines():
        stripped = line.strip()

        # Category headers — flush current finding BEFORE switching
        if stripped.startswith("## Confirmed"):
            if current_finding and current_category:
                result[current_category].append(current_finding)
                current_finding = None
            current_category = "confirmed"
            continue
        elif stripped.startswith("## Disproved"):
            if current_finding and current_category:
                result[current_category].append(current_finding)
                current_finding = None
            current_category = "disproved"
            continue
        elif stripped.startswith("## Observations"):
            if current_finding and current_category:
                result[current_category].append(current_finding)
                current_finding = None
            current_category = "observations"
            continue

        # Finding title: ### [TAG] Title  or  ### Title
        m = re.match(r"^###\s+(?:\[(\w+)\]\s+)?(.+)$", line)
        if m and current_category:
            if current_finding:
                result[current_category].append(current_finding)
            current_finding = {
                "title": m.group(2).strip(),
                "tag": m.group(1),  # e.g. "CONTENT", or None
                "evidence": "",
                "detail": "",
            }
            continue

        if current_finding:
            if line.startswith("- **Evidence:**") or line.startswith("**Evidence:**"):
                current_finding["evidence"] = (
                    line.replace("- **Evidence:**", "")
                    .replace("**Evidence:**", "")
                    .strip()
                )
            elif line.startswith("- **Detail:**") or line.startswith("**Detail:**"):
                current_finding["detail"] = (
                    line.replace("- **Detail:**", "")
                    .replace("**Detail:**", "")
                    .strip()
                )

    # Flush last finding
    if current_finding and current_category:
        result[current_category].append(current_finding)

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
