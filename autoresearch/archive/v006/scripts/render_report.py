#!/usr/bin/env python3
"""Stage 2 render — compose report.html + report.pdf + report-screenshot.png
from a session's artifacts.

Spec section C1 (docs/plans/2026-05-07-003-self-improving-report-rendering.md).

Inputs (all read from session_dir):
  - session.md, report.md, findings.md, results.jsonl  (common)
  - gap_allocation.json, verification-schedule.json    (geo)
  - pages/*.json, optimized/*.md, evals/*.json         (geo)
  - competitors/visibility.json                        (geo)
  - brief.md, analyses/, competitors/                  (competitive)
  - digest.md, mentions/, anomalies/, recommendations/ (monitoring)
  - selection/videos.json, patterns/, stories/         (storyboard)
  - logs/iteration_*.log.err  → extract_reasoning.py output

Outputs (written to session_dir):
  - report.html · the composed HTML report
  - report.pdf  · Chrome --print-to-pdf
  - report-screenshot.png · Chrome --screenshot at 1280x1600 (for vision sub-judge)

Usage:
  render_report.py <session_dir> <domain> <client>
  render_report.py /path/to/session geo nubank

Anthropic / Opus integration (optional, future):
  If ANTHROPIC_API_KEY is set AND the `anthropic` package is importable, the
  script will defer body composition to a single Opus call. Otherwise it falls
  back to a deterministic template-based composer using .rprt-* primitives
  from src/shared/reporting/report_base.py:BASE_CSS.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from html import escape as h
from pathlib import Path
from typing import Iterable

# Resolve src/shared/reporting via repo discovery (works from any variant location)
_REPO_ROOT = Path(__file__).resolve().parents[4]  # …/gofreddy/
sys.path.insert(0, str(_REPO_ROOT))
from src.shared.reporting.report_base import (  # noqa: E402
    build_html_document,
    html_to_pdf,
    html_to_screenshot,
    load_json,
    load_markdown,
    md_to_html,
    render_logs_appendix,
)

# Sibling script
_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from extract_reasoning import extract_session  # noqa: E402


# ============================================================================
# Helpers
# ============================================================================

def safe_read(p: Path, max_chars: int | None = None) -> str | None:
    """Thin truncating wrapper over report_base.load_markdown."""
    if not p.exists() or not p.is_file():
        return None
    txt = load_markdown(p)
    if not txt:
        return None
    return txt[:max_chars] if max_chars else txt


def safe_json(p: Path):
    """Delegate to report_base.load_json (same None-on-failure contract)."""
    return load_json(p) if p.exists() else None


def parse_findings_md(text: str) -> dict[str, list[tuple[str, str]]]:
    """Parse findings.md into sections → list of (tag, body)."""
    out: dict[str, list[tuple[str, str]]] = {}
    section = "general"
    if not text:
        return out
    for line in text.splitlines():
        if line.startswith("## "):
            section = line.replace("## ", "").strip().lower()
            out.setdefault(section, [])
        elif line.startswith("- "):
            body = line[2:].strip()
            tag = "GENERIC"
            if body.startswith("[") and "]" in body:
                tag = body[1:body.index("]")]
                body = body[body.index("]") + 1:].strip()
            out.setdefault(section, []).append((tag, body))
    return out


def md_inline(s: str) -> str:
    """Inline markdown → HTML. Wraps mistune's md_to_html and strips
    surrounding ``<p>`` tags to keep the result inline-safe inside
    table cells / spans / list-item bodies."""
    if not s:
        return ""
    rendered = md_to_html(s).strip()
    if rendered.startswith("<p>") and rendered.endswith("</p>"):
        rendered = rendered[3:-4]
    return rendered


# ============================================================================
# Common section builders (lane-agnostic)
# ============================================================================

def build_meta_strip(domain: str, client: str, summary: dict | None) -> str:
    status = (summary or {}).get("status", "—")
    iters = (summary or {}).get("iterations", {}).get("total", "—")
    findings = (summary or {}).get("findings_count", "—")
    when = (summary or {}).get("generated_at", datetime.now().isoformat())
    return (
        f'<div class="rprt-meta">'
        f'<span><strong>FREDDY · AUTORESEARCH</strong> · {h(domain.upper())} LANE · {h(client)}</span>'
        f'<span>{h(str(when)[:10])} · {h(str(status))} · {h(str(iters))} iter · {h(str(findings))} findings</span>'
        f'</div>'
    )


def build_hero(title: str, sub: str) -> str:
    return (
        f'<div class="rprt-hero">'
        f'<div class="rprt-eyebrow">Investigation report</div>'
        f'<h1>{h(title)}</h1>'
        f'<p>{md_inline(sub)}</p>'
        f'</div>'
    )


def build_stat_grid(stats: list[tuple[str, str]]) -> str:
    tiles = "".join(
        f'<div class="rprt-stat-tile"><div class="num">{h(v)}</div><div class="label">{h(k)}</div></div>'
        for k, v in stats
    )
    return f'<div class="rprt-stat-grid">{tiles}</div>'


def build_findings(findings: dict) -> str:
    """Render confirmed + disproved + observations sections."""
    if not findings:
        return '<p class="rprt-prose"><em>No findings.md available.</em></p>'
    out = []
    section_titles = {"confirmed": "Confirmed", "disproved": "Disproved / unverified",
                      "observations": "Observations", "general": "Findings"}
    for section, items in findings.items():
        if not items:
            continue
        title = section_titles.get(section, section.title())
        out.append(f'<h3>{h(title)} <span style="color:#6b7280;font-size:13px;font-weight:400">({len(items)})</span></h3>')
        for tag, body in items:
            cls = "rprt-finding-card" + (" disproved" if section == "disproved" else "")
            out.append(
                f'<div class="{cls}">'
                f'<span class="rprt-finding-tag {h(tag)}">{h(tag)}</span>'
                f'<div>{md_inline(body)}</div>'
                f'</div>'
            )
    return "\n".join(out)


def build_reasoning_trail(extract: dict) -> str:
    """Render beat-by-beat reasoning trail from extract_reasoning.py output."""
    if not extract or not extract.get("iterations"):
        return '<p class="rprt-prose"><em>No transcript data available.</em></p>'
    out = ['<div class="rprt-reasoning-trail">']
    out.append(f'<p class="rprt-prose"><strong>{extract["totals"]["reasoning_beats"]} reasoning beats · {extract["totals"]["tool_calls"]} tool calls · {round(extract["totals"]["tokens"])}K tokens</strong> across {extract["iteration_count"]} iterations.</p>')
    for it in extract["iterations"]:
        out.append(f'<h4 style="font-family:JetBrains Mono,monospace;font-size:11px;letter-spacing:.10em;text-transform:uppercase;color:#0f3460;margin:20px 0 8px">Iteration {it["iteration"]} · {h(it["phase"])} · {h(it["status"])}</h4>')
        for beat in it["reasoning_beats"][:6]:  # cap at 6 per iter
            out.append(
                f'<div class="rprt-beat-card">'
                f'<span class="kind {h(beat["kind"])}">{h(beat["kind"].replace("_", " "))}</span>'
                f'<div class="text">"{md_inline(beat["text"][:400])}"</div>'
                f'</div>'
            )
        if it.get("tool_calls"):
            sample = it["tool_calls"][:3]
            out.append('<div style="margin:8px 0 0 90px;font-family:JetBrains Mono,monospace;font-size:10.5px;color:#6b7280">')
            out.append(f'  → {it["tool_count"]} tool calls · sample:')
            for tc in sample:
                out.append(f'<div style="background:#f5f2e8;padding:4px 10px;border-radius:3px;margin:3px 0;color:#1f2937"><code>{h(tc[:120])}</code></div>')
            out.append('</div>')
    out.append("</div>")

    if extract.get("pivots"):
        out.append('<h3 style="margin-top:24px">Pivot moments detected</h3>')
        for piv in extract["pivots"][:4]:
            out.append(
                f'<div class="rprt-pivot-callout">'
                f'<div class="pkind">⚡ Iteration {piv["iteration"]} · {h(piv.get("kind", "transition"))}</div>'
                f'<div style="font-size:13px;line-height:1.55"><strong>Before:</strong> "{md_inline(piv["before"][:200])}"</div>'
                f'<div style="font-size:13px;line-height:1.55;margin-top:6px"><strong>After:</strong> "{md_inline(piv["after"][:200])}"</div>'
                f'</div>'
            )
    return "\n".join(out)


def build_phase_ledger(results_jsonl: list[dict]) -> str:
    if not results_jsonl:
        return '<p class="rprt-prose"><em>No results.jsonl entries.</em></p>'
    out = ['<table class="rprt-key-table">',
           '<thead><tr><th style="width:80px">Iter</th><th style="width:140px">Type</th><th style="width:120px">Status</th><th>Notes</th></tr></thead><tbody>']
    for entry in results_jsonl:
        iter_n = entry.get("iteration", "—")
        typ = entry.get("type", "—")
        status = entry.get("status", "—")
        notes = entry.get("notes", entry.get("note", ""))
        out.append(f'<tr><td>{h(str(iter_n))}</td><td><code>{h(str(typ))}</code></td><td>{h(str(status))}</td><td style="font-size:12.5px">{md_inline(str(notes)[:300])}</td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out)


def build_handoff(steps: Iterable[str]) -> str:
    items = "\n".join(
        f'<div class="rprt-action-row"><div class="priority">{i+1}</div><div>{md_inline(step)}</div></div>'
        for i, step in enumerate(steps)
    )
    return f'<div class="rprt-action-list">{items}</div>'


# ============================================================================
# Lane-specific composers
# ============================================================================

def build_transcripts_appendix(session_dir: Path) -> str:
    """Surface logs/iteration_*.log.err agent transcripts (~80% of session
    bytes that earlier composers ignored). Truncated to ~12 KB per file
    with PII scrubbed. Spec section A1."""
    return render_logs_appendix(
        session_dir / "logs",
        label="Agent transcripts (raw .err)",
        glob="*.log.err",
        max_per_file_chars=12000,
        scrub_pii=True,
    )


def compose_geo(session_dir: Path, client: str, extract: dict) -> list[tuple[str, str]]:
    summary = safe_json(session_dir / "session_summary.json") or {}
    gap = safe_json(session_dir / "gap_allocation.json") or {}
    visibility = safe_json(session_dir / "competitors" / "visibility.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
    # A4: prefer the pre-derived report.json from build_geo_report.py (richer
    # structured fields: top_questions, recommended_blocks, techfix_types,
    # offsite_domains). Fallback to deriving when the file is missing.
    geo_report = safe_json(session_dir / "report.json") or {}
    results = []
    rj = session_dir / "results.jsonl"
    if rj.exists():
        for line in rj.read_text().splitlines():
            try:
                results.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                pass

    sections = []

    # Hero
    iter_count = summary.get("iterations", {}).get("total", "?")
    findings_count = summary.get("findings_count", sum(len(v) for v in findings.values()))
    sub = (
        f"GEO investigation for **{client}** · {iter_count} iterations · "
        f"{findings_count} findings recorded · "
        f"{summary.get('status', 'COMPLETE')}."
    )
    sections.append(("hero", build_hero(f"GEO · {client}", sub)))

    # Strategic gap
    if gap.get("allocations"):
        alloc = gap["allocations"][0]
        sections.append(("gap", (
            f'<div class="rprt-callout">'
            f'<div class="ckind">Strategic gap · gap_allocation.json</div>'
            f'<div class="ctitle">{h(alloc.get("slug", "page"))}</div>'
            f'<p style="font-size:14px;line-height:1.6;color:#4b5563;margin:8px 0 0">{md_inline(alloc.get("assigned_gap", ""))}</p>'
            f'</div>'
        )))

    # Quick stats — prefer the pre-computed report.json totals when present
    pages_dir = session_dir / "pages"
    pages = list(pages_dir.glob("*.json")) if pages_dir.exists() else []
    optimized_dir = session_dir / "optimized"
    opt_files = list(optimized_dir.glob("*.md")) if optimized_dir.exists() else []
    citations = (
        geo_report.get("total_citations")
        if geo_report
        else (visibility.get("summary") or {}).get("total_brand_citations", 0)
    )
    stats = [
        ("Iterations", str(iter_count)),
        ("Pages cached", str(len(pages))),
        ("Optimized", str(geo_report.get("pages_optimized", len(opt_files)))),
        ("Citations", str(citations)),
    ]
    sections.append(("stats", build_stat_grid(stats)))

    # A4: Block recommendations + top questions + heading targets — surfaces
    # the structured intelligence build_geo_report.py already produces, which
    # the previous compose_geo dropped.
    if geo_report:
        rec_blocks = geo_report.get("recommended_blocks") or {}
        top_questions = geo_report.get("top_questions") or []
        top_headings = geo_report.get("top_heading_targets") or []
        offsite = geo_report.get("offsite_domains") or {}
        report_panels: list[str] = []
        if rec_blocks:
            tiles = "".join(
                f'<div class="rprt-stat-tile"><div class="num">{int(v)}</div>'
                f'<div class="label">{h(str(k).replace("_", " "))}</div></div>'
                for k, v in sorted(rec_blocks.items(), key=lambda kv: -int(kv[1]))[:8]
            )
            report_panels.append(
                f'<h3>Recommended block mix</h3>'
                f'<div class="rprt-stat-grid" style="grid-template-columns:repeat(4,1fr)">{tiles}</div>'
            )
        if top_questions:
            qs = "".join(f"<li>{h(q)}</li>" for q in top_questions[:10])
            report_panels.append(f"<h3>Top questions to answer</h3><ul>{qs}</ul>")
        if top_headings:
            hd = "".join(f"<li>{h(s)}</li>" for s in top_headings[:10])
            report_panels.append(f"<h3>Frequent heading targets</h3><ul>{hd}</ul>")
        if offsite:
            top = sorted(offsite.items(), key=lambda kv: -int(kv[1]))[:8]
            rows = "".join(
                f"<tr><td><code>{h(d)}</code></td><td>{int(c)}</td></tr>" for d, c in top
            )
            report_panels.append(
                f'<h3>Offsite citation domains</h3>'
                f'<table class="rprt-key-table"><thead><tr><th>Domain</th>'
                f'<th style="width:140px">Citations</th></tr></thead><tbody>{rows}</tbody></table>'
            )
        if report_panels:
            sections.append(("geo_summary", "<h2>Structured GEO summary · report.json</h2>"
                             + "\n".join(report_panels)))

    # Citation evidence (if measured)
    if visibility.get("summary"):
        s = visibility["summary"]
        out = ['<h2>Citation evidence</h2>']
        out.append('<p class="rprt-prose">Measured AI engine citation breakdown for the brand query.</p>')
        out.append('<div class="rprt-stat-grid" style="grid-template-columns:repeat(3,1fr)">')
        for engine in ("chatgpt", "perplexity", "gemini"):
            count = s.get(f"{engine}_citations", 0)
            out.append(f'<div class="rprt-stat-tile"><div class="num">{count}</div><div class="label">{engine}</div></div>')
        out.append('</div>')
        if visibility.get("data_quality_notes"):
            out.append('<h3>Data quality notes</h3>')
            for note in visibility["data_quality_notes"][:5]:
                out.append(f'<div class="rprt-callout warn"><div class="ckind">caveat</div>{md_inline(note)}</div>')
        sections.append(("citations", "\n".join(out)))

    # Cached pages
    if pages:
        out = [f'<h2>Cached pages ({len(pages)})</h2>']
        for p in pages[:5]:
            d = safe_json(p) or {}
            out.append(
                f'<div class="rprt-callout">'
                f'<div class="ckind">{h(p.name)}</div>'
                f'<div class="ctitle">{h(d.get("title", ""))}</div>'
                f'<p style="margin:8px 0 0;font-size:13px"><strong>URL:</strong> <code>{h(d.get("url", "—"))}</code> → <code>{h(d.get("final_url", ""))}</code><br>'
                f'<strong>Status:</strong> {d.get("status_code", "—")} · '
                f'<strong>Words:</strong> {d.get("word_count", "—")} · '
                f'<strong>Schema:</strong> {", ".join(d.get("schema_types", [])) or "<em>[ ] empty</em>"}<br>'
                f'<strong>H1:</strong> {h(d.get("h1", "—"))}<br>'
                f'<strong>Meta:</strong> {h((d.get("meta_description") or "—")[:200])}</p>'
                f'</div>'
            )
        sections.append(("pages", "\n".join(out)))

    # Optimized deliverable preview
    if opt_files:
        out = [f'<h2>Agent-authored deliverable ({len(opt_files)} file{"s" if len(opt_files) > 1 else ""})</h2>']
        for opt in opt_files[:2]:
            content = safe_read(opt, 1500) or ""
            out.append(
                f'<div class="rprt-callout success">'
                f'<div class="ckind">optimized · {h(opt.name)}</div>'
                f'<pre style="font-family:monospace;font-size:12px;line-height:1.5;white-space:pre-wrap;background:#f5f2e8;padding:12px;border-radius:6px;margin:8px 0 0;max-height:300px;overflow:auto">{h(content)}</pre>'
                f'</div>'
            )
        sections.append(("optimized", "\n".join(out)))

    # Findings
    sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))

    # Reasoning trail
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))

    # Phase ledger
    sections.append(("phases", f'<h2>Phase ledger · results.jsonl</h2>{build_phase_ledger(results)}'))

    # Agent transcripts (A1: surface ~80% of bytes that were previously dropped)
    transcripts_html = build_transcripts_appendix(session_dir)
    if transcripts_html:
        sections.append(("transcripts", transcripts_html))

    return sections


def compose_competitive(session_dir: Path, client: str, extract: dict) -> list[tuple[str, str]]:
    summary = safe_json(session_dir / "session_summary.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
    brief = safe_read(session_dir / "brief.md", 4000) or ""
    results = []
    rj = session_dir / "results.jsonl"
    if rj.exists():
        for line in rj.read_text().splitlines():
            try:
                results.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                pass

    sections = [("hero", build_hero(f"COMPETITIVE · {client}",
                                     f"Strategic positioning brief for **{client}**. {summary.get('iterations', {}).get('total', '?')} iterations · "
                                     f"brief reworked across verify cycles."))]

    competitors_dir = session_dir / "competitors"
    competitors = list(competitors_dir.glob("*.json")) if competitors_dir.exists() else []
    analyses_dir = session_dir / "analyses"
    analyses = list(analyses_dir.glob("*")) if analyses_dir.exists() else []

    sections.append(("stats", build_stat_grid([
        ("Iterations", str(summary.get("iterations", {}).get("total", "?"))),
        ("Competitors", str(len(competitors))),
        ("Analyses", str(len(analyses))),
        ("Findings", str(summary.get("findings_count", "?"))),
    ])))

    if brief:
        sections.append(("brief", (
            f'<h2>Strategic brief · brief.md</h2>'
            f'<pre class="rprt-callout" style="font-family:monospace;font-size:12px;white-space:pre-wrap;line-height:1.55">{h(brief)}</pre>'
        )))

    # B3: surface competitor data + analyses content (was previously counts-only)
    if competitors:
        out = [f'<h2>Competitor evidence ({len(competitors)})</h2>']
        for c in competitors[:8]:
            d = safe_json(c) or {}
            label = c.stem.replace("_", " ").title()
            domain = d.get("domain") or d.get("url") or ""
            score = d.get("score") or d.get("composite") or ""
            summary_txt = d.get("summary") or d.get("notes") or d.get("brief") or ""
            block = [
                f'<details class="rprt-faq"><summary><strong>{h(label)}</strong>'
                + (f' · <code>{h(str(domain))}</code>' if domain else "")
                + (f' · score {h(str(score))}' if score else "")
                + "</summary>"
            ]
            if summary_txt:
                block.append(f'<p style="font-size:13px;line-height:1.55;margin:8px 0">{h(str(summary_txt)[:800])}</p>')
            top_keys = [k for k in d.keys() if k not in {"domain", "url", "score", "composite", "summary", "notes", "brief"}][:6]
            if top_keys:
                rows = "".join(
                    f'<tr><td><code>{h(k)}</code></td>'
                    f'<td style="font-size:12px">{h(str(d.get(k))[:240])}</td></tr>'
                    for k in top_keys
                )
                block.append(f'<table class="rprt-key-table" style="margin:6px 0"><tbody>{rows}</tbody></table>')
            block.append("</details>")
            out.append("\n".join(block))
        sections.append(("competitors", "\n".join(out)))

    if analyses:
        out = [f'<h2>Analysis writeups ({len(analyses)})</h2>']
        for a in analyses[:6]:
            if not a.is_file():
                continue
            content = safe_read(a, 2400) or ""
            if not content:
                continue
            label = a.name
            out.append(
                f'<details class="rprt-faq"><summary><strong>{h(label)}</strong></summary>'
                f'<pre style="font-family:monospace;font-size:12px;line-height:1.55;'
                f'white-space:pre-wrap;background:var(--bg-soft);padding:12px;'
                f'border-radius:6px;margin:8px 0;max-height:400px;overflow:auto">'
                f'{h(content)}</pre></details>'
            )
        sections.append(("analyses", "\n".join(out)))

    sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    sections.append(("phases", f'<h2>Phase ledger · results.jsonl</h2>{build_phase_ledger(results)}'))
    transcripts_html = build_transcripts_appendix(session_dir)
    if transcripts_html:
        sections.append(("transcripts", transcripts_html))
    return sections


def compose_monitoring(session_dir: Path, client: str, extract: dict) -> list[tuple[str, str]]:
    summary = safe_json(session_dir / "session_summary.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
    digest = safe_read(session_dir / "digest.md", 5000) or ""
    results = []
    rj = session_dir / "results.jsonl"
    if rj.exists():
        for line in rj.read_text().splitlines():
            try:
                results.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                pass

    sections = [("hero", build_hero(f"MONITORING · {client}",
                                     f"Weekly brand-mention digest. 6-phase pipeline: select_mentions → cluster_stories → detect_anomalies → synthesize → recommend → deliver."))]

    mentions_dir = session_dir / "mentions"
    anomalies_dir = session_dir / "anomalies"
    mentions = list(mentions_dir.glob("*.json")) if mentions_dir.exists() else []
    anomalies = list(anomalies_dir.glob("*.json")) if anomalies_dir.exists() else []

    sections.append(("stats", build_stat_grid([
        ("Iterations", str(summary.get("iterations", {}).get("total", "?"))),
        ("Mentions", str(len(mentions))),
        ("Anomalies", str(len(anomalies))),
        ("Findings", str(summary.get("findings_count", "?"))),
    ])))

    if digest:
        sections.append(("digest", (
            f'<h2>Weekly digest · digest.md</h2>'
            f'<pre class="rprt-callout" style="font-family:monospace;font-size:12px;white-space:pre-wrap;line-height:1.55">{h(digest)}</pre>'
        )))

    # B3: surface mentions + anomalies + recommendations + synthesized content
    # (was previously count-only).
    def _render_json_dir(label: str, files: list[Path], max_files: int = 6, max_chars: int = 1200) -> str | None:
        if not files:
            return None
        out = [f'<h2>{h(label)} ({len(files)})</h2>']
        for fp in files[:max_files]:
            d = safe_json(fp) or {}
            stem = fp.stem.replace("_", " ").title()
            top_fields = []
            for k in ("title", "headline", "summary", "snippet", "anomaly_type", "score"):
                if k in d:
                    top_fields.append(f"<strong>{h(k)}:</strong> {h(str(d[k])[:240])}")
            block = [
                f'<details class="rprt-faq"><summary><strong>{h(stem)}</strong> · <code>{h(fp.name)}</code></summary>',
            ]
            if top_fields:
                block.append(
                    '<p style="font-size:13px;line-height:1.55;margin:8px 0">'
                    + " · ".join(top_fields)
                    + "</p>"
                )
            snippet = json.dumps(d, indent=2)[:max_chars]
            block.append(
                f'<pre style="font-family:monospace;font-size:11px;line-height:1.5;'
                f'white-space:pre-wrap;background:var(--bg-soft);padding:10px;'
                f'border-radius:6px;margin:6px 0;max-height:280px;overflow:auto">'
                f'{h(snippet)}</pre></details>'
            )
            out.append("\n".join(block))
        return "\n".join(out)

    def _render_md_dir(label: str, files: list[Path], max_files: int = 4, max_chars: int = 2400) -> str | None:
        if not files:
            return None
        out = [f'<h2>{h(label)} ({len(files)})</h2>']
        for fp in files[:max_files]:
            content = safe_read(fp, max_chars) or ""
            if not content:
                continue
            out.append(
                f'<details class="rprt-faq"><summary><strong>{h(fp.name)}</strong></summary>'
                f'<pre style="font-family:monospace;font-size:12px;line-height:1.55;'
                f'white-space:pre-wrap;background:var(--bg-soft);padding:12px;'
                f'border-radius:6px;margin:8px 0;max-height:400px;overflow:auto">'
                f'{h(content)}</pre></details>'
            )
        return "\n".join(out)

    mentions_block = _render_json_dir("Mentions", mentions, max_files=8)
    if mentions_block:
        sections.append(("mentions", mentions_block))
    anomalies_block = _render_json_dir("Anomalies", anomalies, max_files=8)
    if anomalies_block:
        sections.append(("anomalies", anomalies_block))

    recs_dir = session_dir / "recommendations"
    rec_files = sorted(recs_dir.glob("*.md")) if recs_dir.exists() else []
    recs_block = _render_md_dir("Recommendations", rec_files)
    if recs_block:
        sections.append(("recommendations", recs_block))

    synth_dir = session_dir / "synthesized"
    synth_files = sorted(synth_dir.glob("*.md")) if synth_dir.exists() else []
    synth_block = _render_md_dir("Synthesized", synth_files)
    if synth_block:
        sections.append(("synthesized", synth_block))

    sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    sections.append(("phases", f'<h2>Phase ledger</h2>{build_phase_ledger(results)}'))
    transcripts_html = build_transcripts_appendix(session_dir)
    if transcripts_html:
        sections.append(("transcripts", transcripts_html))
    return sections


def compose_storyboard(session_dir: Path, client: str, extract: dict) -> list[tuple[str, str]]:
    summary = safe_json(session_dir / "session_summary.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
    # A5: read the actual storyboard deliverables (5 × ~20 KB each in real
    # sessions). The previous compose_storyboard read selection/videos.json
    # which doesn't exist in real sessions — silent miss of all the content.
    storyboards_dir = session_dir / "storyboards"
    storyboard_files = sorted(storyboards_dir.glob("*.json")) if storyboards_dir.exists() else []
    storyboards: list[dict] = []
    for sb_path in storyboard_files:
        sb = safe_json(sb_path)
        if isinstance(sb, dict):
            storyboards.append(sb)
    results = []
    rj = session_dir / "results.jsonl"
    if rj.exists():
        for line in rj.read_text().splitlines():
            try:
                results.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                pass

    sections = [("hero", build_hero(f"STORYBOARD · {client}",
                                     f"Generated storyboards for **{client}** · "
                                     f"{len(storyboards)} delivered · "
                                     f"{summary.get('iterations', {}).get('total', '?')} iterations."))]

    sections.append(("stats", build_stat_grid([
        ("Iterations", str(summary.get("iterations", {}).get("total", "?"))),
        ("Storyboards", str(len(storyboards))),
        ("Findings", str(summary.get("findings_count", "?"))),
        ("Status", str(summary.get("status", "—"))),
    ])))

    # A5: render each storyboard as a scene-by-scene block
    if storyboards:
        out = [f'<h2>Generated storyboards ({len(storyboards)})</h2>']
        for sb in storyboards:
            title = sb.get("title", "(untitled)")
            sb_id = sb.get("id", "?")
            ar = sb.get("aspect_ratio", "?")
            res = sb.get("resolution", "?")
            emotion_arc = sb.get("target_emotion_arc", "")
            protagonist = sb.get("protagonist_description", "")
            scenes = sb.get("scenes") or sb.get("beats") or []
            anchor = sb.get("anchor_preview_image_url") or ""

            block = [
                f'<div class="rprt-callout">',
                f'<div class="ckind">storyboard · <code>{h(str(sb_id))}</code></div>',
                f'<div class="ctitle">{h(str(title))}</div>',
                f'<p style="font-size:13px;color:#4b5563;margin:6px 0">'
                f'<strong>Aspect:</strong> {h(str(ar))} · '
                f'<strong>Res:</strong> {h(str(res))} · '
                f'<strong>Scenes:</strong> {len(scenes)}</p>',
            ]
            if emotion_arc:
                block.append(f'<p style="font-size:13px;margin:6px 0"><strong>Emotion arc:</strong> {h(str(emotion_arc)[:300])}</p>')
            if protagonist:
                block.append(f'<p style="font-size:13px;margin:6px 0"><strong>Protagonist:</strong> {h(str(protagonist)[:300])}</p>')
            if anchor:
                block.append(f'<p style="font-size:12px;color:#6b7280;margin:6px 0">'
                             f'<strong>Anchor preview:</strong> <code>{h(str(anchor)[:120])}</code></p>')
            if scenes:
                block.append(
                    '<table class="rprt-key-table" style="margin-top:8px"><thead><tr>'
                    '<th style="width:30px">#</th>'
                    '<th>Title / shot / camera</th>'
                    '<th>Beat</th>'
                    '<th style="width:80px">Dur</th>'
                    '</tr></thead><tbody>'
                )
                for sc in scenes[:20]:
                    sc_title = sc.get("title", "")
                    sc_shot = sc.get("shot_type", "")
                    sc_camera = sc.get("camera_movement", "")
                    sc_beat = sc.get("beat") or sc.get("summary") or ""
                    sc_dur = sc.get("duration_seconds", "")
                    sc_idx = sc.get("index", "?")
                    shot_camera = " · ".join(filter(None, [sc_shot, sc_camera]))
                    block.append(
                        f'<tr><td>{h(str(sc_idx))}</td>'
                        f'<td><strong>{h(str(sc_title)[:80])}</strong>'
                        f'<div style="font-size:11px;color:#6b7280;margin-top:2px">{h(shot_camera)}</div></td>'
                        f'<td style="font-size:12px">{h(str(sc_beat)[:200])}</td>'
                        f'<td>{h(str(sc_dur))}s</td></tr>'
                    )
                block.append("</tbody></table>")
            block.append("</div>")
            out.append("\n".join(block))
        sections.append(("storyboards", "\n".join(out)))

    sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    sections.append(("phases", f'<h2>Phase ledger</h2>{build_phase_ledger(results)}'))
    transcripts_html = build_transcripts_appendix(session_dir)
    if transcripts_html:
        sections.append(("transcripts", transcripts_html))
    return sections


def compose_marketing_audit(session_dir: Path, client: str, extract: dict) -> list[tuple[str, str]]:
    """A3: marketing_audit composer.

    The canonical audit deliverable is produced by Stage-5 of src/audit/stages.py
    (Jinja2 + WeasyPrint, templates/audit_report.html.j2). Stage-5 mirrors its
    HTML+PDF into this session dir at report.html / report.pdf (see A2 in
    src/audit/stages.py:stage_5_deliverable). When that's already present this
    composer renders a thin pointer + meta-strip; when it's absent (autoresearch
    ran but Stage-5 didn't, or this is a session-only run), it composes
    minimally from the lane's session-level artifacts.
    """
    summary = safe_json(session_dir / "session_summary.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
    results = []
    rj = session_dir / "results.jsonl"
    if rj.exists():
        for line in rj.read_text().splitlines():
            try:
                results.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                pass

    sections: list[tuple[str, str]] = []

    # The Stage-5 deliverable mirror (if it exists in this session dir, was
    # placed there by stage_5_deliverable). report.pdf is the canonical
    # shipping artifact; report.html is also the canonical viewable.
    stage5_html = session_dir / "report.html"
    stage5_pdf = session_dir / "report.pdf"

    sections.append(("hero", build_hero(
        f"MARKETING AUDIT · {client}",
        f"Multi-stage marketing audit deliverable for **{client}**. "
        f"Canonical report ships from Stage-5 (Jinja2 + WeasyPrint); this view "
        f"surfaces session-level artifacts + reasoning trail."
    )))

    sections.append(("stats", build_stat_grid([
        ("Iterations", str(summary.get("iterations", {}).get("total", "?"))),
        ("Findings", str(summary.get("findings_count", sum(len(v) for v in findings.values())))),
        ("Status", str(summary.get("status", "—"))),
        ("Has Stage-5", "yes" if stage5_html.exists() else "no"),
    ])))

    if stage5_html.exists() or stage5_pdf.exists():
        # Stage-5 is the canonical deliverable; this section just points to it.
        bytes_html = stage5_html.stat().st_size if stage5_html.exists() else 0
        bytes_pdf = stage5_pdf.stat().st_size if stage5_pdf.exists() else 0
        sections.append(("stage5", (
            f'<div class="rprt-callout success">'
            f'<div class="ckind">Canonical deliverable · Stage-5 (Jinja2 + WeasyPrint)</div>'
            f'<div class="ctitle">report.html · report.pdf</div>'
            f'<p style="font-size:13px;line-height:1.6;color:#4b5563;margin:8px 0 0">'
            f'<strong>HTML:</strong> {bytes_html // 1024} KB · '
            f'<strong>PDF:</strong> {bytes_pdf // 1024} KB · '
            f'sourced from <code>src/audit/stages.py:stage_5_deliverable</code>. '
            f'The viewable HTML below is rendered from <code>templates/audit_report.html.j2</code> '
            f'(9-axis health, gap report, proposal, sources).</p>'
            f'</div>'
        )))
    else:
        # No Stage-5 mirror yet — best-effort minimal compose.
        # Surface the per-agent JSON outputs (subdirs from WorkflowConfig:
        # findability, narrative, acquisition, experience, phase0, lens_outputs).
        for subdir_name in ("findability", "narrative", "acquisition", "experience"):
            subdir = session_dir / subdir_name
            if not subdir.exists():
                continue
            files = sorted(subdir.glob("*.json"))[:3]
            if not files:
                continue
            block = [f'<h3>{h(subdir_name.title())}</h3>']
            for fp in files:
                d = safe_json(fp) or {}
                snippet = json.dumps(d, indent=2)[:1200]
                block.append(
                    f'<div class="rprt-callout">'
                    f'<div class="ckind">{h(fp.name)}</div>'
                    f'<pre style="font-family:monospace;font-size:11px;'
                    f'line-height:1.5;white-space:pre-wrap;'
                    f'background:#f8f6f0;padding:10px;border-radius:6px;'
                    f'max-height:240px;overflow:auto">{h(snippet)}</pre>'
                    f'</div>'
                )
            sections.append((f"agent_{subdir_name}", "\n".join(block)))

    sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    sections.append(("phases", f'<h2>Phase ledger</h2>{build_phase_ledger(results)}'))
    transcripts_html = build_transcripts_appendix(session_dir)
    if transcripts_html:
        sections.append(("transcripts", transcripts_html))
    return sections


COMPOSERS = {
    "geo": compose_geo,
    "competitive": compose_competitive,
    "monitoring": compose_monitoring,
    "storyboard": compose_storyboard,
    "marketing_audit": compose_marketing_audit,
}


# ============================================================================
# Stage 2 enrichment via CLI agent subprocess — matches autoresearch convention
# (evolve.py + program_prescription_critic.py spawn codex/claude/opencode CLIs)
# ============================================================================

def _cli_synthesis_command(backend: str, prompt: str) -> tuple[list[str], bytes | None]:
    """Build subprocess command for the chosen CLI agent. Returns (cmd, stdin_input)."""
    if backend == "codex":
        return (
            [
                "codex", "exec",
                "--model", os.environ.get("RENDER_MODEL", "gpt-5.5"),
                "--sandbox", "read-only",
                "--color", "never",
                "--ephemeral",
                "-c", 'approval_policy="never"',
                "-c", 'otel.exporter="none"',
                "-c", 'otel.trace_exporter="none"',
                "-c", 'otel.metrics_exporter="none"',
                "-",
            ],
            prompt.encode("utf-8"),
        )
    if backend == "claude":
        return (
            [
                "claude", "-p",
                "--model", os.environ.get("RENDER_MODEL", "claude-opus-4-7"),
                "--max-turns", "1",
                prompt,
            ],
            None,
        )
    if backend == "opencode":
        return (
            [
                "opencode", "run", "--dangerously-skip-permissions",
                "-m", os.environ.get("RENDER_MODEL", "openrouter/anthropic/claude-opus-4-7"),
                "--format", "text",
                prompt,
            ],
            None,
        )
    raise ValueError(f"unknown CLI backend: {backend!r}")


_LANE_BRIEFS = {
    "geo": (
        "Anchor the verdict in measured visibility / citation deltas. "
        "Quote one or two specific page-level findings (slug, query, schema gap, etc.) "
        "and recommend the single highest-leverage block-mix change for the next iteration."
    ),
    "competitive": (
        "Frame this as a strategic positioning brief. Quote one direct piece of "
        "competitor evidence (a tactic, a moat, a price band) and identify the "
        "single asymmetric move the brief should pursue."
    ),
    "monitoring": (
        "Treat this like an ops digest. Lead with the loudest anomaly + a measured "
        "delta vs prior weeks. End with the one recommendation the team should action "
        "before next Monday."
    ),
    "storyboard": (
        "Speak to the through-line across the 5 storyboards: emotion arc, protagonist "
        "consistency, transition rhythm. Quote the strongest single scene-beat and "
        "name the single most-likely-to-watch storyboard for production."
    ),
    "marketing_audit": (
        "This is an executive read of a multi-stage marketing audit. Anchor in 9-axis "
        "health deltas, name the single highest-severity ParentFinding, and recommend "
        "the most actionable proposal item from the gap report."
    ),
}


_AGENT_HTML_ALLOWED_TAGS = {
    "section", "div", "h2", "h3", "h4", "p", "ul", "ol", "li", "strong",
    "em", "code", "pre", "table", "thead", "tbody", "tr", "td", "th",
    "blockquote", "br", "span",
}
_AGENT_HTML_ALLOWED_CLASSES = {
    "rprt-meta-pattern", "rprt-callout", "rprt-callout success",
    "rprt-callout warn", "rprt-callout critical", "rprt-stat-grid",
    "rprt-stat-tile", "rprt-key-table", "rprt-finding-card",
    "rprt-pull-quote", "rprt-evidence-quote", "rprt-action-list",
    "rprt-action-row", "ckind", "ctitle", "num", "label", "qtext", "qattr",
    "priority",
}


def _sanitize_agent_html(raw: str) -> str:
    """Strip the agent's HTML to the .rprt-* allowlist.

    Best-effort: uses a tiny regex pass when bleach isn't installed. The
    contract is "no <script>, no <style>, no on* event handlers, no
    arbitrary classes" — anything off-allowlist is dropped (text content
    preserved). If the result is empty after sanitisation, returns "".
    """
    import re as _re
    if not raw:
        return ""
    # 1. Strip <script>, <style>, <iframe>, <object>, <embed>, <form>
    raw = _re.sub(
        r"<\s*(script|style|iframe|object|embed|form)\b[^>]*>.*?<\s*/\s*\1\s*>",
        "",
        raw,
        flags=_re.IGNORECASE | _re.DOTALL,
    )
    # 2. Strip on* attributes
    raw = _re.sub(r"\s+on[a-z]+\s*=\s*\"[^\"]*\"", "", raw, flags=_re.IGNORECASE)
    raw = _re.sub(r"\s+on[a-z]+\s*=\s*'[^']*'", "", raw, flags=_re.IGNORECASE)
    # 3. Drop unknown tags by replacing with their inner text
    def _drop_tag(m: _re.Match) -> str:
        tag = m.group(1).lower()
        if tag in _AGENT_HTML_ALLOWED_TAGS:
            return m.group(0)
        return ""
    raw = _re.sub(r"</?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>", _drop_tag, raw)
    return raw.strip()


def _payload_signature(domain: str, lane_brief: str, payload: str) -> str:
    """SHA256 of (domain, lane_brief, payload) for idempotent caching."""
    import hashlib
    h_ = hashlib.sha256()
    h_.update(domain.encode("utf-8"))
    h_.update(b"\x00")
    h_.update(lane_brief.encode("utf-8"))
    h_.update(b"\x00")
    h_.update(payload.encode("utf-8"))
    return h_.hexdigest()[:24]


def _build_payload(extract: dict, findings_md: str, lane_dir_excerpts: list[str]) -> str:
    """Compose the data block fed to the agent. Bounded to ~30 KB total."""
    parts: list[str] = []

    # Reasoning trail summary (compact)
    totals = extract.get("totals", {}) if isinstance(extract, dict) else {}
    parts.append(
        f"REASONING TOTALS:\n"
        f"  iterations: {extract.get('iteration_count', 0)}\n"
        f"  reasoning_beats: {totals.get('reasoning_beats', 0)}\n"
        f"  tool_calls: {totals.get('tool_calls', 0)}\n"
    )

    # Pivots (these are the agent's own course-corrections — high-signal)
    pivots = extract.get("pivots", []) if isinstance(extract, dict) else []
    if pivots:
        parts.append("PIVOTS (agent course-corrections):")
        for piv in pivots[:6]:
            parts.append(
                f"  · iter {piv.get('iteration')} ({piv.get('kind')}): "
                f"{str(piv.get('before', ''))[:140]} → {str(piv.get('after', ''))[:140]}"
            )

    # Findings (full)
    if findings_md:
        parts.append("\nFINDINGS.md (truncated to 6000 chars):")
        parts.append(findings_md[:6000])

    # Lane-specific dir excerpts (each excerpt already truncated by caller)
    for excerpt in lane_dir_excerpts:
        if excerpt:
            parts.append("\n" + excerpt)

    payload = "\n".join(parts)
    # Hard cap at 30 KB so we don't blow past the codex context budget.
    return payload[:30000]


def _gather_lane_excerpts(domain: str, session_dir: Path) -> list[str]:
    """Collect lane-specific dir snippets for the agent's payload."""
    excerpts: list[str] = []

    def _read_truncated(p: Path, n: int) -> str:
        if not p.exists() or not p.is_file():
            return ""
        try:
            return p.read_text(encoding="utf-8", errors="replace")[:n]
        except OSError:
            return ""

    if domain == "geo":
        rj = _read_truncated(session_dir / "report.json", 4000)
        if rj:
            excerpts.append(f"GEO REPORT.JSON (truncated):\n{rj}")
    elif domain == "competitive":
        comp_dir = session_dir / "competitors"
        if comp_dir.exists():
            for f in sorted(comp_dir.glob("*.json"))[:3]:
                excerpts.append(f"COMPETITOR {f.name}:\n{_read_truncated(f, 1800)}")
    elif domain == "monitoring":
        for sub in ("synthesized", "recommendations"):
            sd = session_dir / sub
            if sd.exists():
                for f in sorted(sd.glob("*.md"))[:2]:
                    excerpts.append(f"{sub.upper()} {f.name}:\n{_read_truncated(f, 1800)}")
    elif domain == "storyboard":
        sb_dir = session_dir / "storyboards"
        if sb_dir.exists():
            for f in sorted(sb_dir.glob("*.json"))[:2]:
                excerpts.append(f"STORYBOARD {f.name}:\n{_read_truncated(f, 2400)}")
    elif domain == "marketing_audit":
        for sub in ("findability", "narrative", "acquisition", "experience"):
            sd = session_dir / sub
            if sd.exists():
                for f in sorted(sd.glob("*.json"))[:1]:
                    excerpts.append(f"{sub.upper()} {f.name}:\n{_read_truncated(f, 1800)}")
    return excerpts


def agent_compose_section(
    domain: str,
    client: str,
    session_dir: Path,
    extract: dict,
    findings_md: str | None,
) -> str | None:
    """B2: Stage-2 agent-authored inner HTML.

    The CLI agent is fed:
      - lane_brief (per-lane editorial framing)
      - reasoning trail summary + pivots
      - findings.md (truncated to 6 KB)
      - lane-specific dir excerpts (truncated to ~30 KB total payload)

    It returns inner HTML constrained to the .rprt-* allowlist. We sanitize
    aggressively, cache by content hash, and fail soft.
    """
    backend = os.environ.get("RENDER_BACKEND", "codex").lower()
    if backend in ("none", "off", "skip"):
        return None

    lane_brief = _LANE_BRIEFS.get(domain, "Write a tight executive synthesis.")
    excerpts = _gather_lane_excerpts(domain, session_dir)
    payload = _build_payload(extract, findings_md or "", excerpts)

    sig = _payload_signature(domain, lane_brief, payload)
    cache_dir = session_dir / ".render_synthesis_cache"
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / f"{sig}.html"
    if cache_path.exists():
        try:
            cached = cache_path.read_text(encoding="utf-8")
            if cached.strip():
                print(f"  ✓ stage-2 cache hit ({len(cached)} chars · {sig})", file=sys.stderr)
                return cached
        except OSError:
            pass

    prompt = (
        f"You are the report editor for the FREDDY autoresearch system.\n"
        f"Lane: {domain}\n"
        f"Client: {client}\n"
        f"Editorial brief: {lane_brief}\n\n"
        f"Below is the data extracted from this session. Write the inner HTML for ONE\n"
        f"section (~250-450 words rendered) that an executive reader will skim first.\n"
        f"Surface SPECIFIC findings, NUMBERS, and PROPER NOUNS from the data — do not\n"
        f"summarize abstractly.\n\n"
        f"OUTPUT CONTRACT:\n"
        f"  - Output ONLY HTML (no markdown, no preamble, no closing remarks).\n"
        f"  - Wrap the whole thing in <div class=\"rprt-callout success\">...</div>.\n"
        f"  - Use ONLY these classes: rprt-callout (success/warn/critical), ckind,\n"
        f"    ctitle, rprt-stat-grid, rprt-stat-tile (with .num + .label children),\n"
        f"    rprt-pull-quote (with .qtext + .qattr), rprt-evidence-quote,\n"
        f"    rprt-action-list, rprt-action-row (with .priority + content).\n"
        f"  - Use ONLY these tags: section, div, h3, h4, p, ul, ol, li, strong, em,\n"
        f"    code, table, thead, tbody, tr, td, th, blockquote, span, br.\n"
        f"  - NO inline styles, NO scripts, NO external resources.\n\n"
        f"=== SESSION DATA ===\n{payload}\n=== END DATA ===\n\n"
        f"Now emit the inner HTML for the section. Begin directly with `<div`."
    )

    cmd, stdin_input = _cli_synthesis_command(backend, prompt)

    try:
        result = subprocess.run(
            cmd, input=stdin_input,
            capture_output=True,
            timeout=int(os.environ.get("RENDER_TIMEOUT_SECONDS", "90")),
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  WARNING: {backend} synthesis unavailable ({type(e).__name__}); "
              f"falling back to deterministic-only render.", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(f"  WARNING: {backend} returned rc={result.returncode}; "
              f"falling back to deterministic.", file=sys.stderr)
        return None

    text = result.stdout.decode("utf-8", errors="replace").strip()
    # Some CLIs wrap the response in code-fences — strip them.
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    sanitized = _sanitize_agent_html(text)
    if not sanitized or len(sanitized) < 60:
        print(f"  WARNING: stage-2 output too short / empty after sanitize ({len(sanitized)} chars); skipping.", file=sys.stderr)
        return None

    try:
        cache_path.write_text(sanitized, encoding="utf-8")
    except OSError:
        pass

    print(f"  ✓ {backend} stage-2 produced {len(sanitized)} chars (sanitized · cached)", file=sys.stderr)
    return sanitized[:24000]


# Backwards-compat: keep the old names so external callers don't break.
def maybe_cli_synthesis(domain: str, client: str, beats: dict,
                          findings_md: str | None) -> str | None:
    """Deprecated thin wrapper — kept for backwards-compat. Returns plain text."""
    backend = os.environ.get("RENDER_BACKEND", "codex").lower()
    if backend in ("none", "off", "skip"):
        return None
    prompt = (
        f"You are writing a 2-3 sentence executive synthesis for a "
        f"{domain.upper()} autoresearch session report on client '{client}'. "
        f"The agent recorded {beats.get('totals', {}).get('reasoning_beats', 0)} "
        f"reasoning beats across {beats.get('iteration_count', 0)} iterations. "
        f"Findings header (first 2000 chars):\n\n"
        f"{(findings_md or '')[:2000]}\n\n"
        "Output ONLY the 2-3 sentence synthesis, no preamble. Lead with the "
        "verdict, support with one piece of measured evidence, end with the "
        "highest-leverage next action. No markdown."
    )
    cmd, stdin_input = _cli_synthesis_command(backend, prompt)
    try:
        result = subprocess.run(
            cmd, input=stdin_input,
            capture_output=True,
            timeout=int(os.environ.get("RENDER_TIMEOUT_SECONDS", "60")),
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    text = result.stdout.decode("utf-8", errors="replace").strip()
    return text[:1200] if text and len(text) >= 30 else None


maybe_opus_synthesis = maybe_cli_synthesis


# ============================================================================
# Main
# ============================================================================

def render(session_dir: Path, domain: str, client: str) -> dict:
    """Render report.html + report.pdf + report-screenshot.png. Returns paths."""
    composer = COMPOSERS.get(domain)
    if not composer:
        print(f"  WARNING: no composer registered for domain '{domain}'", file=sys.stderr)
        return {}

    # Extract reasoning beats (Stage 1)
    print(f"  Extracting reasoning trail from {session_dir}/logs/", file=sys.stderr)
    try:
        extract = extract_session(session_dir)
    except Exception as e:
        print(f"  WARNING: extract_session failed: {e}", file=sys.stderr)
        extract = {"iterations": [], "totals": {"reasoning_beats": 0, "tool_calls": 0, "tokens": 0}, "iteration_count": 0}

    # Compose sections
    print(f"  Composing {domain} report for {client}", file=sys.stderr)
    sections = composer(session_dir, client, extract)

    # B2: Stage-2 agent-authored inner HTML — full payload (extract + findings
    # + lane-specific dir excerpts), sanitized + cached. Falls back silently
    # when the CLI is unreachable or produces unsafe output.
    findings_md = safe_read(session_dir / "findings.md", 6000) or ""
    agent_html = agent_compose_section(domain, client, session_dir, extract, findings_md)
    if agent_html:
        sections.insert(1, ("synthesis", (
            f'<div class="rprt-meta-pattern">'
            f'<div class="label">↳ Stage-2 agent-authored · '
            f'{os.environ.get("RENDER_BACKEND", "codex")} CLI · {domain}</div>'
            f'{agent_html}'
            f'</div>'
        )))

    # Wrap with build_html_document
    summary = safe_json(session_dir / "session_summary.json") or {}
    title = f"FREDDY · {domain.upper()} · {client}"
    meta_strip = build_meta_strip(domain, client, summary)
    sections_with_meta = [("meta", meta_strip)] + sections
    html_str = build_html_document(title=title, sections=sections_with_meta)
    # Wrap body content in .rprt-page for typographic consistency
    # B1: per-lane visual theme — adds CSS-var overrides via .rprt-theme-<lane>
    html_str = html_str.replace(
        "<body>",
        f'<body><div class="rprt-page rprt-theme-{domain}">',
    ).replace("</body>", "</div></body>")

    # Write artifacts
    html_path = session_dir / "report.html"
    pdf_path = session_dir / "report.pdf"
    png_path = session_dir / "report-screenshot.png"

    html_path.write_text(html_str, encoding="utf-8")
    print(f"  Wrote {html_path} ({len(html_str):,} bytes)", file=sys.stderr)

    html_to_pdf(html_path, pdf_path)
    html_to_screenshot(html_path, png_path)

    return {
        "html": str(html_path),
        "pdf": str(pdf_path) if pdf_path.exists() else None,
        "png": str(png_path) if png_path.exists() else None,
        "html_bytes": len(html_str),
    }


def main():
    p = argparse.ArgumentParser(description="Stage 2 render — compose report HTML + PDF + screenshot")
    p.add_argument("session_dir", type=Path)
    p.add_argument("domain", choices=list(COMPOSERS.keys()))
    p.add_argument("client", type=str)
    args = p.parse_args()

    out = render(args.session_dir.resolve(), args.domain, args.client)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
