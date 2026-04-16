#!/usr/bin/env python3
"""Generate a comprehensive HTML+PDF GEO+SEO report from a session directory.

Renders all stages: discovery, baseline, competitive, per-page optimization
with content block previews, findings, and full iteration logs.

Usage:
    python3 configs/seo/scripts/generate_report.py sessions/geo/notion
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_project_root = Path(__file__).resolve().parents[3]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from autoresearch.report_base import (
    build_html_document,
    common_argparse,
    esc,
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
    unavailable_banner,
)

# ---------------------------------------------------------------------------
# GEO-specific CSS
# ---------------------------------------------------------------------------

GEO_CSS = """\
.block-intro { border-left: 4px solid #2196f3; background: #e3f2fd; padding: 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.block-fill { border-left: 4px solid #4caf50; background: #e8f5e9; padding: 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.block-faq { border-left: 4px solid #9c27b0; background: #f3e5f5; padding: 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.block-schema { border-left: 4px solid #ff9800; background: #fff3e0; padding: 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.block-techfix { border-left: 4px solid #f44336; background: #fce4ec; padding: 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.block-label { display: inline-block; background: rgba(0,0,0,0.1); padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 600; margin-bottom: 6px; }
.placement { color: #888; font-size: 0.8em; font-style: italic; }
.score-matrix td { text-align: center; }
.score-matrix .delta-pos { color: #2e7d32; font-weight: 600; }
.score-matrix .delta-neg { color: #c62828; font-weight: 600; }
.simulated-badge { background: #fff3e0; color: #e65100; padding: 1px 6px; border-radius: 3px; font-size: 0.7em; }
.page-card { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; page-break-inside: avoid; }
.page-card h3 { margin-top: 0; }
dt { font-weight: 600; margin-top: 8px; }
dd { margin-left: 0; margin-bottom: 4px; }
"""

# ---------------------------------------------------------------------------
# GEO content block parser
# ---------------------------------------------------------------------------

BLOCK_RE = re.compile(
    r"\[(\w+(?:-\w+)?)\]\s*(?:(?:type|placement):\s*(.+?)\n)?(.*?)\[/\1\]",
    re.DOTALL,
)


@dataclass
class ContentBlock:
    block_type: str  # INTRO, FILL, FAQ, SCHEMA, TECHFIX, FAQ-SCHEMA
    directive: str  # placement or type directive
    content: str


def parse_content_blocks(text: str) -> list[ContentBlock]:
    """Parse optimized/*.md into structured content blocks."""
    blocks: list[ContentBlock] = []
    for m in BLOCK_RE.finditer(text):
        blocks.append(
            ContentBlock(
                block_type=m.group(1).upper(),
                directive=m.group(2) or "",
                content=m.group(3).strip(),
            )
        )
    return blocks


def render_content_block(block: ContentBlock) -> str:
    """Render a single content block with type-specific styling."""
    bt = block.block_type
    css_class = {
        "INTRO": "block-intro",
        "FILL": "block-fill",
        "FAQ": "block-faq",
        "FAQ-SCHEMA": "block-schema",
        "SCHEMA": "block-schema",
        "TECHFIX": "block-techfix",
    }.get(bt, "block-fill")

    label = esc(bt)
    directive_html = (
        f'<div class="placement">{esc(block.directive)}</div>'
        if block.directive
        else ""
    )

    # Render content based on type
    if bt == "FAQ":
        # Parse Q/A pairs
        content_html = _render_faq_pairs(block.content)
    elif bt in ("FAQ-SCHEMA", "SCHEMA"):
        # JSON-LD in collapsible code block
        content_html = (
            f"<details><summary>JSON-LD Schema</summary>"
            f"<pre><code>{esc(block.content)}</code></pre></details>"
        )
    elif bt == "TECHFIX":
        content_html = f"<pre>{esc(block.content)}</pre>"
    else:
        # INTRO, FILL — render as markdown, truncated for FILL
        text = block.content
        if bt == "FILL" and len(text) > 500:
            text = text[:500] + "\n\n*... (truncated)*"
        content_html = md_to_html(text)

    return (
        f'<div class="{css_class}">'
        f'<span class="block-label">{label}</span>'
        f"{directive_html}{content_html}</div>"
    )


def _render_faq_pairs(text: str) -> str:
    """Parse Q:/A: pairs and render as <dl>."""
    pairs: list[tuple[str, str]] = []
    current_q = ""
    current_a_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("Q:"):
            if current_q and current_a_lines:
                pairs.append((current_q, "\n".join(current_a_lines)))
            current_q = line[2:].strip()
            current_a_lines = []
        elif line.startswith("A:"):
            current_a_lines.append(line[2:].strip())
        elif current_a_lines:
            current_a_lines.append(line.strip())

    if current_q and current_a_lines:
        pairs.append((current_q, "\n".join(current_a_lines)))

    if not pairs:
        return md_to_html(text)

    items = "".join(
        f"<dt>{esc(q)}</dt><dd>{esc(a)}</dd>" for q, a in pairs
    )
    return f"<dl>{items}</dl><p><em>{len(pairs)} FAQ pairs</em></p>"


# ---------------------------------------------------------------------------
# GEO-specific renderers
# ---------------------------------------------------------------------------


def render_header(session_md: str, session_dir: Path, results: list[dict]) -> str:
    """Render GEO report header with key metrics."""
    # Parse metadata from session.md
    def extract(pattern: str) -> str:
        m = re.search(pattern, session_md, re.MULTILINE)
        return m.group(1).strip() if m else ""

    site = extract(r"url:\s*(.+)") or extract(r"Site:\s*(.+)") or session_dir.name
    status = extract(r"## Status:\s*(.+)")

    # Compute metrics from results
    optimize_entries = [e for e in results if e.get("type") == "optimize"]
    pages_optimized = len([e for e in optimize_entries if e.get("status") == "kept"])
    pages_total = len({e.get("page", "") for e in optimize_entries})

    deltas = [e.get("delta", 0) for e in optimize_entries if e.get("status") == "kept"]
    avg_delta = sum(deltas) / len(deltas) if deltas else 0

    befores = [e.get("before", 0) for e in optimize_entries if e.get("status") == "kept"]
    afters = [e.get("after", 0) for e in optimize_entries if e.get("status") == "kept"]
    avg_before = sum(befores) / len(befores) if befores else 0
    avg_after = sum(afters) / len(afters) if afters else 0

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return f"""\
<h1>GEO+SEO Report &mdash; {esc(site)}</h1>
<div class="story-meta">
  <strong>Site:</strong> {esc(site)} &nbsp;|&nbsp;
  <strong>Date:</strong> {date_str} &nbsp;|&nbsp;
  <strong>Pages:</strong> {pages_optimized}/{pages_total} optimized &nbsp;|&nbsp;
  <strong>Avg Score:</strong> {avg_before:.2f} → {avg_after:.2f} (+{avg_delta:.2f}) &nbsp;|&nbsp;
  <strong>Status:</strong> {esc(status)}
</div>
"""


def render_seo_baseline(session_dir: Path) -> str:
    """Render SEO infrastructure baseline from baselines/summary.md."""
    baseline_md = load_markdown(session_dir / "baselines" / "summary.md")
    if not baseline_md:
        return unavailable_banner("SEO baseline data not available")

    return (
        '<h2><span class="phase-header">Infrastructure</span> SEO Baseline</h2>'
        f'<div class="report-md">{md_to_html(baseline_md)}</div>'
    )


def render_competitive_citations(session_dir: Path) -> str:
    """Render competitive citation data from competitors/visibility.json."""
    vis_path = session_dir / "competitors" / "visibility.json"
    vis_data = load_json(vis_path)

    if not vis_data or not isinstance(vis_data, dict):
        # Check if directory has any files
        comp_dir = session_dir / "competitors"
        if comp_dir.is_dir() and any(comp_dir.iterdir()):
            # Has files but no visibility.json
            return unavailable_banner(
                "Competitive visibility data not available (API rate-limited)"
            )
        return unavailable_banner("No competitive data collected")

    # Check for simulated/research-based data
    method = vis_data.get("method", vis_data.get("_meta", {}).get("method", ""))
    if isinstance(method, str) and method:
        parts_prefix = f'<p><em>Method: {esc(method)}</em></p>'
    else:
        parts_prefix = ""

    parts: list[str] = [
        '<h2><span class="phase-header">Competitive</span> AI Citation Analysis</h2>',
        parts_prefix,
    ]

    queries = vis_data.get("queries", [])

    # Format A: list of {query, platforms: {platform: {citations: [...]}}}
    if isinstance(queries, list):
        for q_entry in queries:
            if not isinstance(q_entry, dict):
                continue
            query_text = q_entry.get("query", "")
            platforms = q_entry.get("platforms", {})
            if not isinstance(platforms, dict) or not platforms:
                continue

            parts.append(f"<h3>{esc(query_text)}</h3>")
            parts.append(
                "<table><thead><tr><th>Platform</th><th>Cited</th>"
                "<th>Position</th><th>Total Citations</th>"
                "<th>Top Competitors</th></tr></thead><tbody>"
            )
            for plat_name, plat_data in platforms.items():
                if not isinstance(plat_data, dict):
                    continue
                cited = plat_data.get("canva_cited", plat_data.get("cited", False))
                position = plat_data.get("canva_position", plat_data.get("position", "-"))
                total = plat_data.get("total_citations", "?")
                citations_list = plat_data.get("citations", [])
                top_comps = esc(", ".join(str(c) for c in citations_list[:5]))
                cited_str = "Yes" if cited else "No"
                bg = "background:#e8f5e9" if cited else ""
                style = f' style="{bg}"' if bg else ""
                parts.append(
                    f"<tr{style}><td>{esc(plat_name)}</td><td>{cited_str}</td>"
                    f"<td>{position}</td><td>{total}</td>"
                    f"<td>{top_comps}</td></tr>"
                )
            parts.append("</tbody></table>")

    # Format B: dict of {query_text: {citations: [...]}}
    elif isinstance(queries, dict):
        for query_text, data in queries.items():
            parts.append(f"<h3>{esc(query_text)}</h3>")
            citations = data.get("citations", data) if isinstance(data, dict) else []
            if isinstance(citations, list):
                parts.append(
                    "<table><thead><tr><th>Competitor</th><th>Citations</th>"
                    "<th>Platforms</th></tr></thead><tbody>"
                )
                for c in citations:
                    if not isinstance(c, dict):
                        continue
                    name = esc(c.get("name", c.get("competitor", "")))
                    count = c.get("count", c.get("citations", 0))
                    plats = ", ".join(c.get("platforms", []))
                    parts.append(
                        f"<tr><td>{name}</td><td>{count}</td>"
                        f"<td>{esc(plats)}</td></tr>"
                    )
                parts.append("</tbody></table>")

    return "\n".join(parts)


def render_page_score_matrix(results: list[dict]) -> str:
    """Render per-page before/after score matrix from results.jsonl."""
    optimize_entries = [e for e in results if e.get("type") == "optimize"]
    if not optimize_entries:
        return ""

    parts: list[str] = [
        '<h2><span class="phase-header">Scores</span> Page Score Matrix</h2>',
        '<table class="score-matrix">',
        "<thead><tr><th>Page</th><th>Before</th><th>After</th><th>Delta</th>"
        "<th>RAG</th><th>Quality</th><th>Infra</th><th>Status</th></tr></thead>",
        "<tbody>",
    ]

    for entry in optimize_entries:
        page = esc(entry.get("page", ""))
        before = entry.get("before", 0)
        after = entry.get("after", 0)
        delta = entry.get("delta", 0)
        status = entry.get("status", "")

        scores = entry.get("scores", {})
        rag = scores.get("rag", {})
        quality = scores.get("quality", {})
        infra = scores.get("infra", {})

        delta_class = "delta-pos" if delta > 0 else "delta-neg" if delta < 0 else ""
        status_bg = "#e8f5e9" if status == "kept" else "#fce4ec" if status == "discarded" else ""
        style = f' style="background:{status_bg}"' if status_bg else ""

        rag_str = f"{rag.get('before', '?')}→{rag.get('after', '?')}"
        qual_str = f"{quality.get('before', '?')}→{quality.get('after', '?')}"
        infra_str = f"{infra.get('before', '?')}→{infra.get('after', '?')}"

        attempt = entry.get("attempt", 1)
        attempt_badge = f" <sup>attempt {attempt}</sup>" if attempt > 1 else ""

        parts.append(
            f"<tr{style}><td>{page}{attempt_badge}</td>"
            f"<td>{before:.2f}</td><td>{after:.2f}</td>"
            f'<td class="{delta_class}">+{delta:.2f}</td>'
            f"<td>{rag_str}</td><td>{qual_str}</td><td>{infra_str}</td>"
            f"<td>{esc(status)}</td></tr>"
        )

    parts.extend(["</tbody>", "</table>"])
    return "\n".join(parts)


def render_optimized_content(session_dir: Path) -> str:
    """Render content block previews from optimized/*.md files."""
    opt_dir = session_dir / "optimized"
    if not opt_dir.is_dir():
        return ""

    files = sorted(opt_dir.glob("*.md"))
    if not files:
        return ""

    parts: list[str] = [
        '<h2><span class="phase-header">Content</span> Optimized Pages</h2>'
    ]

    for f in files:
        text = load_markdown(f)
        if not text:
            continue

        page_name = f.stem.replace("-", " ").title()

        # Extract metadata from header comments
        header_lines = []
        for line in text.splitlines()[:10]:
            if line.startswith("#"):
                header_lines.append(line.lstrip("# ").strip())

        blocks = parse_content_blocks(text)

        parts.append(f'<div class="page-card">')
        parts.append(f"<h3>{esc(page_name)}</h3>")

        if header_lines:
            meta = " &nbsp;|&nbsp; ".join(esc(h) for h in header_lines[:3])
            parts.append(f'<div class="placement">{meta}</div>')

        if blocks:
            # Summary: block type counts
            type_counts: dict[str, int] = {}
            for b in blocks:
                type_counts[b.block_type] = type_counts.get(b.block_type, 0) + 1
            summary = ", ".join(f"{t}: {c}" for t, c in type_counts.items())
            parts.append(f"<p><em>Blocks: {esc(summary)}</em></p>")

            for block in blocks:
                parts.append(render_content_block(block))
        else:
            # No parseable blocks — render as markdown
            parts.append(f'<div class="report-md">{md_to_html(text[:2000])}</div>')

        parts.append("</div>")  # close page-card

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = common_argparse("Generate comprehensive HTML+PDF GEO+SEO report.")
    args = parser.parse_args()

    session_dir: Path = args.session_dir.resolve()
    if not session_dir.is_dir():
        print(f"ERROR: Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Session directory: {session_dir}", file=sys.stderr)
    print("Loading session data...", file=sys.stderr)

    # ---- Load data ----
    session_md = load_markdown(session_dir / "session.md")
    results = load_jsonl(session_dir / "results.jsonl")
    report_md = load_markdown(session_dir / "report.md")
    findings_md = load_markdown(session_dir / "findings.md")
    findings = parse_findings(findings_md)
    session_summary_raw = load_json(session_dir / "session_summary.json")
    session_summary = session_summary_raw if isinstance(session_summary_raw, dict) else None

    print(f"  results.jsonl: {len(results)} entries", file=sys.stderr)
    print(f"  report.md: {len(report_md)} chars", file=sys.stderr)

    # ---- Export directory ----
    export_dir = session_dir / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    # ---- Build sections ----
    print("Generating HTML report...", file=sys.stderr)

    sections: list[tuple[str, str]] = [
        ("header", render_header(session_md, session_dir, results)),
        ("report", render_report_md(report_md)),
        ("baseline", render_seo_baseline(session_dir)),
        ("competitive", render_competitive_citations(session_dir)),
        ("scores", render_page_score_matrix(results)),
        ("content", render_optimized_content(session_dir)),
        ("findings", render_findings(findings, heading="Validated Findings")),
        ("session_log", render_session_log(results)),
    ]

    if not args.skip_logs:
        sections.append(("logs", render_logs_appendix(session_dir / "logs")))

    sections.append(("summary", render_session_summary(session_summary)))

    html_content = build_html_document(
        title="GEO+SEO Report",
        sections=sections,
        css_extra=GEO_CSS,
    )

    html_path = export_dir / "geo-report.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"  HTML report: {html_path} ({html_path.stat().st_size // 1024}KB)", file=sys.stderr)

    # ---- Convert to PDF ----
    if not args.skip_pdf:
        pdf_path = export_dir / "geo-report.pdf"
        html_to_pdf(html_path, pdf_path)
    else:
        print("  Skipping PDF generation (--skip-pdf)", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
