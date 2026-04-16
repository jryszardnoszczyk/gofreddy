#!/usr/bin/env python3
"""Generate a comprehensive HTML+PDF monitoring/brand intelligence report.

Renders all stages: mention data overview, anomaly alerts, story cards with
engagement density, per-story synthesis, recommendations, and full logs.

Usage:
    python3 configs/monitoring/scripts/generate_report.py sessions/monitoring/Notion
"""

from __future__ import annotations

import re
import sys
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
    truncate,
    unavailable_banner,
)

# ---------------------------------------------------------------------------
# Monitoring-specific CSS
# ---------------------------------------------------------------------------

MONITORING_CSS = """\
.story-card { background: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 12px 0; page-break-inside: avoid; }
.story-card h3 { margin-top: 0; }
.story-type-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75em; font-weight: 600; color: #fff; }
.type-organic { background: #4caf50; }
.type-launch { background: #2196f3; }
.type-security { background: #f44336; }
.type-default { background: #757575; }
.anomaly-card { background: #fff3e0; border-left: 4px solid #ff9800; padding: 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.anomaly-crisis { border-left-color: #f44336; background: #fce4ec; }
.anomaly-opportunity { border-left-color: #4caf50; background: #e8f5e9; }
.anomaly-watchlist { border-left-color: #ff9800; background: #fff3e0; }
.engagement-bar { background: #e0e0e0; border-radius: 4px; height: 18px; margin: 3px 0; position: relative; }
.engagement-fill { height: 100%; border-radius: 4px; background: #e94560; display: flex; align-items: center; padding-left: 6px; font-size: 0.7em; color: #fff; font-weight: 600; }
.mention-card { background: #f0f4ff; padding: 10px; border-radius: 6px; margin: 6px 0; font-size: 0.85em; }
.signal-badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 600; }
.signal-pass { background: #e8f5e9; color: #2e7d32; }
.signal-fail { background: #fce4ec; color: #c62828; }
.data-coverage { background: #e8eaf6; padding: 12px; border-radius: 6px; margin: 10px 0; font-size: 0.9em; }
"""

STORY_TYPE_CSS: dict[str, str] = {
    "organic_ecosystem": "type-organic",
    "product_launch": "type-launch",
    "security_watchlist": "type-security",
}


# ---------------------------------------------------------------------------
# Monitoring-specific renderers
# ---------------------------------------------------------------------------


def render_header(session_md: str, session_dir: Path, results: list[dict]) -> str:
    """Render monitoring report header."""
    def extract(pattern: str) -> str:
        m = re.search(pattern, session_md, re.MULTILINE)
        return m.group(1).strip() if m else ""

    brand = session_dir.name
    period = extract(r"Period:\s*(.+)")
    mentions_loaded = extract(r"Mentions loaded:\s*(\d+)") or "?"
    true_product = extract(r"True product:\s*(\d+)") or "?"
    false_pos = extract(r"False positives:\s*(\d+)") or "?"
    stories = extract(r"Stories clustered:\s*(\d+)") or "?"
    status = extract(r"## Status:\s*(.+)") or extract(r"Status:\s*(.+)")

    # Avg delta from synthesize entries
    synth_entries = [e for e in results if e.get("type") == "synthesize" and e.get("status") == "kept"]
    deltas = [e.get("delta", 0) for e in synth_entries]
    avg_delta = sum(deltas) / len(deltas) if deltas else 0

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return f"""\
<h1>Brand Intelligence Report &mdash; {esc(brand)}</h1>
<div class="story-meta">
  <strong>Brand:</strong> {esc(brand)} &nbsp;|&nbsp;
  <strong>Period:</strong> {esc(period)} &nbsp;|&nbsp;
  <strong>Date:</strong> {date_str} &nbsp;|&nbsp;
  <strong>Mentions:</strong> {esc(mentions_loaded)} ({esc(true_product)} true, {esc(false_pos)} false pos) &nbsp;|&nbsp;
  <strong>Stories:</strong> {esc(stories)} &nbsp;|&nbsp;
  <strong>Avg Delta:</strong> {avg_delta:+.2f} &nbsp;|&nbsp;
  <strong>Status:</strong> {esc(status)}
</div>
"""


def render_data_overview(session_dir: Path) -> str:
    """Render mention data overview from mentions/week-*.json."""
    mentions_dir = session_dir / "mentions"
    if not mentions_dir.is_dir():
        return unavailable_banner("No mention data available")

    all_mentions: list[dict] = []
    for f in sorted(mentions_dir.glob("week-*.json")):
        data = load_json(f)
        if data and isinstance(data, dict):
            all_mentions.extend(data.get("mentions", []))
        elif data and isinstance(data, list):
            all_mentions.extend(data)

    if not all_mentions:
        return unavailable_banner("No mention data available")

    # Source breakdown
    source_counts: dict[str, int] = {}
    source_engagement: dict[str, int] = {}
    date_counts: dict[str, dict] = {}

    for m in all_mentions:
        src = m.get("source", "unknown")
        eng = m.get("engagement_total", 0) or 0
        source_counts[src] = source_counts.get(src, 0) + 1
        source_engagement[src] = source_engagement.get(src, 0) + eng

        pub = m.get("published_at", "")[:10]
        if pub:
            if pub not in date_counts:
                date_counts[pub] = {"mentions": 0, "engagement": 0}
            date_counts[pub]["mentions"] += 1
            date_counts[pub]["engagement"] += eng

    parts: list[str] = [
        '<h2><span class="phase-header">Data</span> Mention Overview</h2>',
        f'<div class="data-coverage"><strong>Total mentions:</strong> {len(all_mentions)}</div>',
    ]

    # Source table
    parts.append(
        "<table><thead><tr><th>Source</th><th>Mentions</th><th>Engagement</th></tr></thead><tbody>"
    )
    for src in sorted(source_counts, key=lambda s: -source_counts[s]):
        parts.append(
            f"<tr><td>{esc(src)}</td><td>{source_counts[src]}</td>"
            f"<td>{source_engagement.get(src, 0):,}</td></tr>"
        )
    parts.append("</tbody></table>")

    # Temporal distribution
    if date_counts:
        max_eng = max(d["engagement"] for d in date_counts.values()) or 1
        parts.append("<h3>Temporal Distribution</h3><table><thead><tr><th>Date</th><th>Mentions</th><th>Engagement</th><th></th></tr></thead><tbody>")
        for date in sorted(date_counts):
            d = date_counts[date]
            pct = d["engagement"] / max_eng * 100
            parts.append(
                f'<tr><td>{esc(date)}</td><td>{d["mentions"]}</td>'
                f'<td>{d["engagement"]:,}</td>'
                f'<td><div class="engagement-bar"><div class="engagement-fill" '
                f'style="width:{pct:.0f}%">{d["engagement"]:,}</div></div></td></tr>'
            )
        parts.append("</tbody></table>")

    # Top mentions by engagement
    sorted_mentions = sorted(all_mentions, key=lambda m: m.get("engagement_total", 0) or 0, reverse=True)
    top = sorted_mentions[:10]
    if top:
        parts.append("<h3>Top Mentions by Engagement</h3>")
        for m in top:
            handle = esc(m.get("author_handle", "unknown"))
            content = esc(truncate(m.get("content", ""), 200))
            eng = m.get("engagement_total", 0)
            src = esc(m.get("source", ""))
            parts.append(
                f'<div class="mention-card">'
                f"<strong>@{handle}</strong> ({src}) — {eng:,} engagement<br>"
                f"{content}</div>"
            )

    return "\n".join(parts)


def render_anomaly_alerts(session_dir: Path) -> str:
    """Render anomaly detection results from anomalies/week-*.json."""
    anomaly_dir = session_dir / "anomalies"
    if not anomaly_dir.is_dir():
        return unavailable_banner("No anomaly detection data")

    all_anomalies: list[dict] = []
    layer1_flags: list[dict] = []

    for f in sorted(anomaly_dir.glob("*.json")):
        data = load_json(f)
        if not data or not isinstance(data, dict):
            continue

        # Layer 1 statistical
        l1 = data.get("layer_1_statistical", {})
        for signal_name, signal_data in l1.items():
            if isinstance(signal_data, dict) and signal_data.get("detected"):
                layer1_flags.append({"signal": signal_name, **signal_data})

        # Layer 3 classification
        l3 = data.get("layer_3_classification", [])
        all_anomalies.extend(l3)

    if not all_anomalies and not layer1_flags:
        return (
            '<h2><span class="phase-header">Anomalies</span> Alert Summary</h2>'
            '<div class="data-coverage">No anomalies detected this period.</div>'
        )

    parts: list[str] = [
        '<h2><span class="phase-header">Anomalies</span> Alert Summary</h2>'
    ]

    # Layer 1 flags
    if layer1_flags:
        parts.append("<h3>Statistical Flags</h3>")
        for flag in layer1_flags:
            signal = esc(flag.get("signal", "").replace("_", " ").title())
            note = esc(flag.get("note", flag.get("driver", "")))
            parts.append(f'<div class="anomaly-card"><strong>{signal}</strong><br>{note}</div>')

    # Layer 3 classifications
    if all_anomalies:
        parts.append(
            "<h3>Classified Anomalies</h3>"
            "<table><thead><tr><th>Story</th><th>Type</th><th>Confidence</th>"
            "<th>Action</th></tr></thead><tbody>"
        )
        for a in all_anomalies:
            story = esc(a.get("story", ""))
            atype = a.get("type", "")
            css = f"anomaly-{atype}" if atype in ("crisis", "opportunity", "watchlist") else ""
            confidence = esc(a.get("confidence", ""))
            action = esc(truncate(a.get("recommended_action", ""), 150))
            parts.append(
                f'<tr class="{css}"><td>{story}</td><td>{esc(atype)}</td>'
                f"<td>{confidence}</td><td>{action}</td></tr>"
            )
        parts.append("</tbody></table>")

    return "\n".join(parts)


def render_story_cards(session_dir: Path) -> str:
    """Render story cards from stories/story-*.json."""
    stories_dir = session_dir / "stories"
    if not stories_dir.is_dir():
        return ""

    stories: list[dict] = []
    for f in sorted(stories_dir.glob("story-*.json")):
        data = load_json(f)
        if data and isinstance(data, dict):
            stories.append(data)

    if not stories:
        return ""

    stories.sort(key=lambda s: s.get("rank", 999))

    # Max engagement for bar scaling
    max_eng = max(s.get("engagement_total", 0) for s in stories) or 1

    parts: list[str] = [
        '<h2><span class="phase-header">Stories</span> Story Analysis</h2>'
    ]

    for story in stories:
        slug = story.get("slug", "")
        label = story.get("label", slug)
        story_type = story.get("story_type", "")
        type_css = STORY_TYPE_CSS.get(story_type, "type-default")
        type_label = story_type.replace("_", " ").title()

        mentions = story.get("mentions", 0)
        eng_total = story.get("engagement_total", 0)
        multiplier = story.get("engagement_multiplier", "?")
        share = story.get("engagement_share_of_week", "?")
        anomaly = story.get("anomaly_linked", False)
        anomaly_type = story.get("anomaly_type", "")
        signal = story.get("signal", "")

        eng_pct = (eng_total / max_eng * 100) if max_eng else 0

        # Anomaly indicator
        anomaly_html = ""
        if anomaly and anomaly_type:
            anomaly_html = (
                f' <span class="signal-badge signal-fail">'
                f'ANOMALY: {esc(anomaly_type)}</span>'
            )

        # Key mentions
        key_mentions = story.get("key_mentions", [])
        km_html = ""
        if key_mentions:
            km_items = "".join(
                f'<div class="mention-card"><strong>@{esc(km.get("handle", ""))}</strong>'
                f' — {km.get("engagement", 0):,} engagement<br>'
                f'{esc(truncate(km.get("content", ""), 150))}</div>'
                for km in key_mentions[:3]
            )
            km_html = f"<h4>Key Mentions</h4>{km_items}"

        parts.append(f"""\
<div class="story-card">
  <h3>#{story.get('rank', '?')}. {esc(label)}
    <span class="story-type-badge {type_css}">{esc(type_label)}</span>
    {anomaly_html}
  </h3>
  <strong>Mentions:</strong> {mentions} &nbsp;|&nbsp;
  <strong>Engagement:</strong> {eng_total:,} &nbsp;|&nbsp;
  <strong>Multiplier:</strong> {esc(str(multiplier))} &nbsp;|&nbsp;
  <strong>Share:</strong> {esc(str(share))}
  <div class="engagement-bar" style="margin-top:8px">
    <div class="engagement-fill" style="width:{eng_pct:.0f}%">{eng_total:,}</div>
  </div>
  <p><em>{esc(truncate(signal, 300))}</em></p>
  {km_html}
</div>""")

    return "\n".join(parts)


def render_story_syntheses(session_dir: Path, results: list[dict]) -> str:
    """Render per-story synthesis as collapsible sections."""
    synth_dir = session_dir / "synthesized"
    if not synth_dir.is_dir():
        return ""

    files = sorted(f for f in synth_dir.glob("*.md") if f.name != "digest.md")
    if not files:
        return ""

    # Build signal lookup from results
    signal_lookup: dict[str, dict] = {}
    for entry in results:
        if entry.get("type") == "synthesize":
            slug = entry.get("story", "")
            signal_lookup[slug] = entry

    parts: list[str] = [
        '<h2><span class="phase-header">Synthesis</span> Per-Story Narratives</h2>'
    ]

    for f in files:
        text = load_markdown(f)
        if not text:
            continue

        slug = f.stem
        name = slug.replace("-", " ").title()
        entry = signal_lookup.get(slug, {})

        # Signal badges
        badges = ""
        before = entry.get("before")
        after = entry.get("after")
        delta = entry.get("delta")
        status = entry.get("status", "")
        if before is not None and after is not None:
            delta_str = f"+{delta:.2f}" if delta and delta > 0 else f"{delta:.2f}" if delta else "?"
            css = "signal-pass" if status == "kept" else "signal-fail"
            badges = (
                f'<span class="signal-badge {css}">'
                f"{before:.2f}→{after:.2f} ({delta_str})</span> "
            )

        parts.append(
            f"<details><summary><strong>{esc(name)}</strong> {badges}</summary>"
            f'<div class="report-md">{md_to_html(text)}</div></details>'
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = common_argparse("Generate comprehensive HTML+PDF monitoring report.")
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

    # Digest: check root first, then synthesized/
    digest_md = load_markdown(session_dir / "digest.md")
    if not digest_md:
        digest_md = load_markdown(session_dir / "synthesized" / "digest.md")

    # Load recommendations from separate section files (A day-1 change) or legacy single file
    rec_dir = session_dir / "recommendations"
    if rec_dir.is_dir():
        recommendations_md = ""
        for fname in ("executive_summary.md", "action_items.md", "cross_story_patterns.md"):
            section = load_markdown(rec_dir / fname)
            if section:
                recommendations_md += section + "\n\n---\n\n"
    else:
        recommendations_md = load_markdown(session_dir / "recommendations.md")
    findings_md = load_markdown(session_dir / "findings.md")
    findings = parse_findings(findings_md)
    session_summary_raw = load_json(session_dir / "session_summary.json")
    session_summary = session_summary_raw if isinstance(session_summary_raw, dict) else None

    print(f"  results.jsonl: {len(results)} entries", file=sys.stderr)
    print(f"  digest.md: {len(digest_md)} chars", file=sys.stderr)
    print(f"  recommendations: {len(recommendations_md)} chars", file=sys.stderr)

    # ---- Export directory ----
    export_dir = session_dir / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    # ---- Build sections ----
    print("Generating HTML report...", file=sys.stderr)

    sections: list[tuple[str, str]] = [
        ("header", render_header(session_md, session_dir, results)),
        ("digest", render_report_md(digest_md)),
        ("recommendations", render_report_md(recommendations_md) if recommendations_md else ""),
        ("data", render_data_overview(session_dir)),
        ("anomalies", render_anomaly_alerts(session_dir)),
        ("stories", render_story_cards(session_dir)),
        ("syntheses", render_story_syntheses(session_dir, results)),
        ("findings", render_findings(findings, heading="Validated Findings")),
        ("session_log", render_session_log(results)),
    ]

    if not args.skip_logs:
        sections.append(("logs", render_logs_appendix(session_dir / "logs")))

    sections.append(("summary", render_session_summary(session_summary)))

    html_content = build_html_document(
        title="Brand Intelligence Report",
        sections=sections,
        css_extra=MONITORING_CSS,
    )

    html_path = export_dir / "monitoring-report.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"  HTML report: {html_path} ({html_path.stat().st_size // 1024}KB)", file=sys.stderr)

    # ---- Convert to PDF ----
    if not args.skip_pdf:
        pdf_path = export_dir / "monitoring-report.pdf"
        html_to_pdf(html_path, pdf_path)
    else:
        print("  Skipping PDF generation (--skip-pdf)", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
