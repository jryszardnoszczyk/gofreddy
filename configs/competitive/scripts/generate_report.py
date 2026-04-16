#!/usr/bin/env python3
"""Generate a comprehensive HTML+PDF competitive intelligence report.

Renders all stages: competitor profiles, ad creative analysis, per-competitor
deep dives, cross-competitor comparison, findings, and full iteration logs.

Usage:
    python3 configs/competitive/scripts/generate_report.py sessions/competitive/figma
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
# Competitive-specific CSS
# ---------------------------------------------------------------------------

COMPETITIVE_CSS = """\
.competitor-card { background: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 12px 0; page-break-inside: avoid; }
.competitor-card h3 { margin-top: 0; }
.tier-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75em; font-weight: 600; color: #fff; }
.tier-full { background: #4caf50; }
.tier-scrape { background: #ff9800; }
.tier-detect { background: #2196f3; }
.threat-badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 600; margin-left: 6px; }
.bar-container { background: #e0e0e0; border-radius: 4px; height: 20px; margin: 3px 0; position: relative; }
.bar-fill { height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 6px; font-size: 0.75em; color: #fff; font-weight: 600; }
.bar-video { background: #e94560; }
.bar-static { background: #0f3460; }
.bar-dco { background: #ff9800; }
.ad-timeline { font-size: 0.85em; }
.quality-badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; font-weight: 600; }
.quality-pass { background: #e8f5e9; color: #2e7d32; }
.quality-fail { background: #fce4ec; color: #c62828; }
"""

# Threat archetype colors
THREAT_COLORS: dict[str, str] = {
    "adjacent-erosion": "#ff9800",
    "pipeline-capture": "#f44336",
    "upstream-displacement": "#9c27b0",
    "niche-recapture": "#2196f3",
    "ecosystem-encirclement": "#4caf50",
}


# ---------------------------------------------------------------------------
# Competitive-specific renderers
# ---------------------------------------------------------------------------


def render_header(session_md: str, session_dir: Path, results: list[dict]) -> str:
    """Render competitive report header."""
    def extract(pattern: str) -> str:
        m = re.search(pattern, session_md, re.MULTILINE)
        return m.group(1).strip() if m else ""

    client = extract(r"# Session:\s*(.+)") or session_dir.name
    status = extract(r"## Status:\s*(.+)") or extract(r"Status:\s*(.+)")

    # Count competitors from gather entries
    gather = [e for e in results if e.get("type") == "gather"]
    competitor_count = gather[0].get("competitors", 0) if gather else 0

    # Quality score from analyze entries
    analyze_entries = [e for e in results if e.get("type") == "analyze"]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return f"""\
<h1>Competitive Intelligence Report &mdash; {esc(client)}</h1>
<div class="story-meta">
  <strong>Client:</strong> {esc(client)} &nbsp;|&nbsp;
  <strong>Date:</strong> {date_str} &nbsp;|&nbsp;
  <strong>Competitors:</strong> {competitor_count} &nbsp;|&nbsp;
  <strong>Analyses:</strong> {len(analyze_entries)} &nbsp;|&nbsp;
  <strong>Status:</strong> {esc(status)}
</div>
"""


def render_competitor_cards(session_dir: Path) -> str:
    """Render competitor profile cards from competitors/*.json."""
    comp_dir = session_dir / "competitors"
    if not comp_dir.is_dir():
        return unavailable_banner("No competitor data collected")

    files = sorted(comp_dir.glob("*.json"))
    if not files:
        return unavailable_banner("No competitor data collected")

    parts: list[str] = [
        '<h2><span class="phase-header">Profiles</span> Competitor Overview</h2>'
    ]

    for f in files:
        data = load_json(f)
        if not data or not isinstance(data, dict):
            continue

        name = data.get("competitor", data.get("domain", f.stem))
        domain = data.get("domain", "")
        tier = data.get("data_tier", "unknown")

        # Tier badge
        tier_css = {"full": "tier-full", "scrape_only": "tier-scrape", "detect_only": "tier-detect"}.get(tier, "tier-detect")
        tier_label = tier.replace("_", " ").title()

        # Positioning
        positioning = data.get("positioning", {})
        if isinstance(positioning, str):
            headline = positioning
            ai_stance = ""
        else:
            headline = positioning.get("headline", "")
            ai_stance = positioning.get("ai_stance", "")
        if not ai_stance:
            scrape_notes = data.get("scrape_notes", {})
            if isinstance(scrape_notes, dict):
                ai_stance = scrape_notes.get("ai_stance", "")

        # GEO signals
        geo = data.get("geo_infrastructure", {})
        schema = "Yes" if geo.get("schema_markup", {}).get("detected") else "No"
        llms_txt = "Yes" if geo.get("llms_txt", {}).get("detected") else "No"
        bot_access = geo.get("ai_bot_access", {})
        bot_status = bot_access.get("details", "Unknown")

        # Ad count
        ad_summary = data.get("ad_summary", {})
        total_ads = ad_summary.get("total_ads", 0)

        parts.append(f"""\
<div class="competitor-card">
  <h3>{esc(name)} <span class="tier-badge {tier_css}">{esc(tier_label)}</span></h3>
  <strong>Domain:</strong> {esc(domain)} &nbsp;|&nbsp;
  <strong>Ads:</strong> {total_ads} &nbsp;|&nbsp;
  <strong>Schema:</strong> {schema} &nbsp;|&nbsp;
  <strong>llms.txt:</strong> {llms_txt} &nbsp;|&nbsp;
  <strong>AI Bots:</strong> {esc(bot_status)}<br>
  <strong>AI Stance:</strong> {esc(ai_stance)}<br>
  {f'<strong>Positioning:</strong> {esc(headline)}' if headline else ''}
</div>""")

    return "\n".join(parts)


def render_ad_analysis(session_dir: Path) -> str:
    """Render ad creative analysis for full-tier competitors."""
    comp_dir = session_dir / "competitors"
    if not comp_dir.is_dir():
        return ""

    parts: list[str] = [
        '<h2><span class="phase-header">Creative</span> Ad Analysis</h2>'
    ]
    has_ads = False

    for f in sorted(comp_dir.glob("*.json")):
        data = load_json(f)
        if not data or not isinstance(data, dict):
            continue

        ad_summary = data.get("ad_summary", {})
        total_ads = ad_summary.get("total_ads", 0)
        if total_ads == 0:
            continue

        has_ads = True
        name = data.get("competitor", f.stem)

        # Format distribution bars
        ad_types = ad_summary.get("ad_types", {})
        video = ad_types.get("video", 0)
        static = ad_types.get("image", 0)
        dco = ad_types.get("dco", 0)

        total = video + static + dco or 1
        video_pct = video / total * 100
        static_pct = static / total * 100
        dco_pct = dco / total * 100

        # Deployment timeline
        deployment = ad_summary.get("deployment_by_date", {})
        deployment_html = ""
        if deployment:
            rows = "".join(
                f"<tr><td>{esc(date)}</td><td>{count}</td></tr>"
                for date, count in sorted(deployment.items())
            )
            deployment_html = (
                '<table class="ad-timeline"><thead><tr><th>Date</th><th>Ads</th></tr></thead>'
                f"<tbody>{rows}</tbody></table>"
            )

        # Top CTAs
        top_ctas = ad_summary.get("top_ctas", {})
        cta_html = ""
        if top_ctas:
            cta_items = ", ".join(
                f"{esc(cta)} ({count})"
                for cta, count in sorted(top_ctas.items(), key=lambda x: -x[1])[:5]
            )
            cta_html = f"<p><strong>Top CTAs:</strong> {cta_items}</p>"

        # Key headlines
        headlines = data.get("key_headlines", [])[:5]
        headlines_html = ""
        if headlines:
            items = "".join(f"<li>{esc(h)}</li>" for h in headlines)
            headlines_html = f"<p><strong>Top Headlines:</strong></p><ul>{items}</ul>"

        parts.append(f"""\
<div class="competitor-card">
  <h3>{esc(name)} — {total_ads} Ads</h3>
  <p><strong>Format Distribution:</strong></p>
  <div class="bar-container">
    <div class="bar-fill bar-video" style="width:{video_pct:.0f}%">Video {video}</div>
  </div>
  <div class="bar-container">
    <div class="bar-fill bar-static" style="width:{static_pct:.0f}%">Static {static}</div>
  </div>
  <div class="bar-container">
    <div class="bar-fill bar-dco" style="width:{dco_pct:.0f}%">DCO {dco}</div>
  </div>
  <p><strong>Deployment:</strong> {esc(ad_summary.get('deployment_pattern', ''))}</p>
  {deployment_html}
  {cta_html}
  {headlines_html}
</div>""")

    if not has_ads:
        return unavailable_banner("No ad creative data available")

    return "\n".join(parts)


def render_per_competitor_analysis(session_dir: Path, results: list[dict]) -> str:
    """Render per-competitor deep dive analyses as collapsible sections."""
    analyses_dir = session_dir / "analyses"
    if not analyses_dir.is_dir():
        return ""

    files = sorted(analyses_dir.glob("*.md"))
    if not files:
        return ""

    # Build quality lookup from results
    quality_lookup: dict[str, dict] = {}
    for entry in results:
        if entry.get("type") == "analyze":
            comp = entry.get("competitor", "").lower()
            quality_lookup[comp] = entry

    parts: list[str] = [
        '<h2><span class="phase-header">Deep Dives</span> Per-Competitor Analysis</h2>'
    ]

    for f in files:
        text = load_markdown(f)
        if not text:
            continue

        name = f.stem.replace("-", " ").title()
        quality_entry = quality_lookup.get(f.stem.lower(), {})

        # Quality badges
        score = quality_entry.get("quality_score", "")
        strategist = quality_entry.get("strategist_test", "")
        novelty = quality_entry.get("novelty_test", "")

        badges = ""
        if score:
            badges += f'<span class="quality-badge quality-pass">{esc(score)}</span> '
        if strategist:
            css = "quality-pass" if strategist == "PASS" else "quality-fail"
            badges += f'<span class="quality-badge {css}">Strategist: {esc(strategist)}</span> '
        if novelty:
            css = "quality-pass" if novelty == "PASS" else "quality-fail"
            badges += f'<span class="quality-badge {css}">Novelty: {esc(novelty)}</span> '

        parts.append(
            f"<details><summary><strong>{esc(name)}</strong> {badges}</summary>"
            f'<div class="report-md">{md_to_html(text)}</div></details>'
        )

    return "\n".join(parts)


def render_cross_comparison(session_md: str, results: list[dict]) -> str:
    """Render cross-competitor comparison table."""
    # Try to extract from session.md taxonomy section
    taxonomy_match = re.search(
        r"## Cross-competitor Taxonomy\s*\n(.*?)(?=\n## |\Z)",
        session_md, re.DOTALL,
    )

    # Also build from analyze results
    analyze_entries = [e for e in results if e.get("type") == "analyze"]
    if not analyze_entries and not taxonomy_match:
        return ""

    parts: list[str] = [
        '<h2><span class="phase-header">Comparison</span> Cross-Competitor Analysis</h2>'
    ]

    # Render taxonomy section if exists
    if taxonomy_match:
        parts.append(f'<div class="report-md">{md_to_html(taxonomy_match.group(1))}</div>')

    # Comparison table from analyze results
    if analyze_entries:
        parts.append(
            "<table><thead><tr><th>Competitor</th><th>Data Tier</th>"
            "<th>Quality</th><th>Strategist</th><th>Novelty</th>"
            "<th>Key Findings</th></tr></thead><tbody>"
        )

        for entry in analyze_entries:
            comp = esc(entry.get("competitor", ""))
            tier = esc(entry.get("data_tier", ""))
            score = esc(str(entry.get("quality_score", "")))
            strat = entry.get("strategist_test", "")
            strat_css = "quality-pass" if strat == "PASS" else "quality-fail"
            nov = entry.get("novelty_test", "")
            nov_css = "quality-pass" if nov == "PASS" else "quality-fail"
            findings = entry.get("key_findings", [])
            findings_str = esc(truncate("; ".join(findings), 150))

            parts.append(
                f"<tr><td><strong>{comp}</strong></td><td>{tier}</td>"
                f"<td>{score}</td>"
                f'<td><span class="quality-badge {strat_css}">{esc(strat)}</span></td>'
                f'<td><span class="quality-badge {nov_css}">{esc(nov)}</span></td>'
                f"<td>{findings_str}</td></tr>"
            )

        parts.append("</tbody></table>")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = common_argparse("Generate comprehensive HTML+PDF competitive intelligence report.")
    args = parser.parse_args()

    session_dir: Path = args.session_dir.resolve()
    if not session_dir.is_dir():
        print(f"ERROR: Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Session directory: {session_dir}", file=sys.stderr)
    print("Loading session data...", file=sys.stderr)

    # ---- Load data ----
    # brief.md is the canonical deliverable for competitive. report.md was
    # removed after the run #6 triage (Unit 13 in the fix plan) because it
    # was near-identical to brief.md and drifted silently. Older sessions
    # may still have report.md on disk; load it as a fallback only.
    session_md = load_markdown(session_dir / "session.md")
    results = load_jsonl(session_dir / "results.jsonl")
    brief_md = load_markdown(session_dir / "brief.md")
    legacy_report_md = load_markdown(session_dir / "report.md")
    findings_md = load_markdown(session_dir / "findings.md")
    findings = parse_findings(findings_md)
    session_summary_raw = load_json(session_dir / "session_summary.json")
    session_summary = session_summary_raw if isinstance(session_summary_raw, dict) else None

    print(f"  results.jsonl: {len(results)} entries", file=sys.stderr)
    print(f"  brief.md: {len(brief_md)} chars", file=sys.stderr)
    if legacy_report_md:
        print(f"  report.md (legacy): {len(legacy_report_md)} chars", file=sys.stderr)

    # ---- Export directory ----
    export_dir = session_dir / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    # ---- Build sections ----
    print("Generating HTML report...", file=sys.stderr)

    primary_report_md = brief_md or legacy_report_md
    sections: list[tuple[str, str]] = [
        ("header", render_header(session_md, session_dir, results)),
        ("report", render_report_md(primary_report_md)),
        ("brief", ""),
        ("profiles", render_competitor_cards(session_dir)),
        ("ads", render_ad_analysis(session_dir)),
        ("deep_dives", render_per_competitor_analysis(session_dir, results)),
        ("comparison", render_cross_comparison(session_md, results)),
        ("findings", render_findings(findings, heading="Validated Findings")),
        ("session_log", render_session_log(
            results,
            extra_columns=["quality_score", "strategist_test", "novelty_test"],
        )),
    ]

    if not args.skip_logs:
        sections.append(("logs", render_logs_appendix(session_dir / "logs")))

    sections.append(("summary", render_session_summary(session_summary)))

    html_content = build_html_document(
        title="Competitive Intelligence Report",
        sections=sections,
        css_extra=COMPETITIVE_CSS,
    )

    html_path = export_dir / "competitive-report.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"  HTML report: {html_path} ({html_path.stat().st_size // 1024}KB)", file=sys.stderr)

    # ---- Convert to PDF ----
    if not args.skip_pdf:
        pdf_path = export_dir / "competitive-report.pdf"
        html_to_pdf(html_path, pdf_path)
    else:
        print("  Skipping PDF generation (--skip-pdf)", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
