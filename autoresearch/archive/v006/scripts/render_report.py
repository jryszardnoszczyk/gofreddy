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
)

# Sibling script
_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from extract_reasoning import extract_session  # noqa: E402


# ============================================================================
# Helpers
# ============================================================================

def safe_read(p: Path, max_chars: int | None = None) -> str | None:
    if not p.exists() or not p.is_file():
        return None
    try:
        txt = p.read_text(errors="replace")
        return txt[:max_chars] if max_chars else txt
    except OSError:
        return None


def safe_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None


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
    """Minimal markdown → HTML for code spans + bold."""
    if not s:
        return ""
    s = h(s)
    import re
    s = re.sub(r"`([^`]+)`", r'<code>\1</code>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


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

def compose_geo(session_dir: Path, client: str, extract: dict) -> list[tuple[str, str]]:
    summary = safe_json(session_dir / "session_summary.json") or {}
    gap = safe_json(session_dir / "gap_allocation.json") or {}
    visibility = safe_json(session_dir / "competitors" / "visibility.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
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

    # Quick stats
    pages_dir = session_dir / "pages"
    pages = list(pages_dir.glob("*.json")) if pages_dir.exists() else []
    optimized_dir = session_dir / "optimized"
    opt_files = list(optimized_dir.glob("*.md")) if optimized_dir.exists() else []
    citations = (visibility.get("summary") or {}).get("total_brand_citations", 0)
    stats = [
        ("Iterations", str(iter_count)),
        ("Pages cached", str(len(pages))),
        ("Optimized", str(len(opt_files))),
        ("Citations", str(citations)),
    ]
    sections.append(("stats", build_stat_grid(stats)))

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

    if competitors:
        out = [f'<h2>Competitor data files ({len(competitors)})</h2>']
        for c in competitors[:8]:
            out.append(f'<div class="rprt-callout"><div class="ckind">{h(c.name)}</div></div>')
        sections.append(("competitors", "\n".join(out)))

    sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    sections.append(("phases", f'<h2>Phase ledger · results.jsonl</h2>{build_phase_ledger(results)}'))
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

    sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    sections.append(("phases", f'<h2>Phase ledger</h2>{build_phase_ledger(results)}'))
    return sections


def compose_storyboard(session_dir: Path, client: str, extract: dict) -> list[tuple[str, str]]:
    summary = safe_json(session_dir / "session_summary.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
    videos = safe_json(session_dir / "selection" / "videos.json") or {}
    results = []
    rj = session_dir / "results.jsonl"
    if rj.exists():
        for line in rj.read_text().splitlines():
            try:
                results.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                pass

    sections = [("hero", build_hero(f"STORYBOARD · {client}",
                                     f"Creator video pattern analysis for **{client}**."))]

    items = []
    if isinstance(videos, dict):
        items = videos.get("items") or videos.get("selected") or videos.get("videos") or []
    elif isinstance(videos, list):
        items = videos

    sections.append(("stats", build_stat_grid([
        ("Iterations", str(summary.get("iterations", {}).get("total", "?"))),
        ("Videos selected", str(len(items))),
        ("Findings", str(summary.get("findings_count", "?"))),
        ("Status", str(summary.get("status", "—"))),
    ])))

    if items:
        out = [f'<h2>Selected videos ({len(items)})</h2>']
        out.append('<table class="rprt-key-table"><thead><tr><th style="width:50px">#</th><th>Title</th><th style="width:140px">Views</th><th style="width:140px">Score</th></tr></thead><tbody>')
        for i, v in enumerate(items[:20]):
            title = v.get("title", v.get("name", "?")) if isinstance(v, dict) else str(v)
            views = (v.get("views", v.get("view_count", 0)) if isinstance(v, dict) else 0) or 0
            score = (v.get("score", v.get("engagement_score", 0)) if isinstance(v, dict) else 0) or 0
            out.append(f'<tr><td>{i+1}</td><td>{h(str(title))}</td><td>{int(views):,}</td><td>{int(score):,}</td></tr>')
        out.append('</tbody></table>')
        sections.append(("videos", "\n".join(out)))

    sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    sections.append(("phases", f'<h2>Phase ledger</h2>{build_phase_ledger(results)}'))
    return sections


COMPOSERS = {
    "geo": compose_geo,
    "competitive": compose_competitive,
    "monitoring": compose_monitoring,
    "storyboard": compose_storyboard,
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


def maybe_cli_synthesis(domain: str, client: str, beats: dict,
                          findings_md: str | None) -> str | None:
    """Spawn a CLI agent (codex / claude / opencode) to write a 1-3 sentence
    cross-section synthesis paragraph for the report header. Falls back to
    None when no CLI is reachable or RENDER_BACKEND is set to "none".

    Pattern matches evolve.py's auth probe + program_prescription_critic.py's
    subprocess invocation. No Anthropic SDK / API key required — the user's
    existing CLI subscription handles auth.
    """
    backend = os.environ.get("RENDER_BACKEND", "codex").lower()
    if backend in ("none", "off", "skip"):
        return None

    # Compose a tight prompt — single shot, no tools, fixed-length answer.
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
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  WARNING: {backend} synthesis unavailable ({type(e).__name__}); "
              f"falling back to deterministic-only render.", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(f"  WARNING: {backend} returned rc={result.returncode}; "
              f"falling back to deterministic.", file=sys.stderr)
        return None

    text = result.stdout.decode("utf-8", errors="replace").strip()
    # Most CLIs prefix with whitespace / boilerplate; trim aggressively.
    text = text.strip().strip("\n").strip()
    if not text or len(text) < 30:
        return None
    print(f"  ✓ {backend} synthesis produced {len(text)} chars", file=sys.stderr)
    return text[:1200]


# Backwards-compat alias for any caller that imported the old name
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

    # Stage 2 enrichment via CLI agent (codex / claude / opencode subprocess)
    findings_md = safe_read(session_dir / "findings.md", 5000) or ""
    synthesis = maybe_cli_synthesis(domain, client, extract, findings_md)
    if synthesis:
        sections.insert(1, ("synthesis", (
            f'<div class="rprt-meta-pattern">'
            f'<div class="label">↳ Stage-2 synthesis · {os.environ.get("RENDER_BACKEND", "codex")} CLI</div>'
            f'<h3>What this run actually means</h3>'
            f'<p>{md_inline(synthesis)}</p>'
            f'</div>'
        )))

    # Wrap with build_html_document
    summary = safe_json(session_dir / "session_summary.json") or {}
    title = f"FREDDY · {domain.upper()} · {client}"
    meta_strip = build_meta_strip(domain, client, summary)
    sections_with_meta = [("meta", meta_strip)] + sections
    html_str = build_html_document(title=title, sections=sections_with_meta)
    # Wrap body content in .rprt-page for typographic consistency
    html_str = html_str.replace("<body>", '<body><div class="rprt-page">').replace("</body>", "</div></body>")

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
