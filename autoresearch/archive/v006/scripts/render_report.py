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
import re
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
    make_session_bundle,
    md_to_html,
    render_logs_appendix,
)

# Sibling script
_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from extract_reasoning import extract_session  # noqa: E402
from charts_svg import (  # noqa: E402
    bar_chart as _chart_bar,
    sparkline as _chart_spark,
    donut as _chart_donut,
    timeline_dots as _chart_timeline,
)


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


def _render_beat_card(beat: dict) -> str:
    """One beat as an .rprt-beat-card div (text not truncated; the parent
    block handles overflow visually)."""
    return (
        f'<div class="rprt-beat-card">'
        f'<span class="kind {h(beat["kind"])}">{h(beat["kind"].replace("_", " "))}</span>'
        f'<div class="text">"{md_inline(beat["text"])}"</div>'
        f'</div>'
    )


def build_reasoning_trail(extract: dict) -> str:
    """Render beat-by-beat reasoning trail from extract_reasoning.py output.

    Keeps the original "first 6 beats inline" preview as the open-by-default
    summary so the report still scans quickly. Any remaining beats are
    rendered inside a closed-by-default <details> ("Show all N beats")
    so the data-transparency target is met without burying the report
    in a wall of text. Tool calls follow the same pattern: first 3 inline,
    rest under <details>.
    """
    if not extract or not extract.get("iterations"):
        return '<p class="rprt-prose"><em>No transcript data available.</em></p>'
    out = ['<div class="rprt-reasoning-trail">']
    totals = extract["totals"]
    out.append(
        f'<p class="rprt-prose"><strong>{totals["reasoning_beats"]} reasoning '
        f'beats · {totals["tool_calls"]} tool calls · '
        f'{round(totals["tokens"])}K tokens</strong> across '
        f'{extract["iteration_count"]} iterations.</p>'
    )
    for it in extract["iterations"]:
        out.append(
            f'<h4 style="font-family:JetBrains Mono,monospace;font-size:11px;'
            f'letter-spacing:.10em;text-transform:uppercase;color:#0f3460;'
            f'margin:20px 0 8px">Iteration {it["iteration"]} · '
            f'{h(it["phase"])} · {h(it["status"])} · '
            f'{len(it["reasoning_beats"])} beats · {it["tool_count"]} tools</h4>'
        )
        beats = it["reasoning_beats"]
        for beat in beats[:6]:
            out.append(_render_beat_card(beat))
        if len(beats) > 6:
            extras = beats[6:]
            out.append(
                f'<details style="margin:8px 0"><summary style="cursor:pointer;'
                f'font-size:12px;color:#6b7280">Show all '
                f'{len(beats)} beats ({len(extras)} more)</summary>'
                f'<div style="margin-top:6px">'
                + "\n".join(_render_beat_card(b) for b in extras)
                + "</div></details>"
            )
        if it.get("tool_calls"):
            tcs = it["tool_calls"]
            sample = tcs[:3]
            out.append(
                '<div style="margin:8px 0 0 90px;font-family:JetBrains Mono,'
                'monospace;font-size:10.5px;color:#6b7280">'
            )
            out.append(f'  → {it["tool_count"]} tool calls · sample:')
            for tc in sample:
                out.append(
                    f'<div style="background:#f5f2e8;padding:4px 10px;'
                    f'border-radius:3px;margin:3px 0;color:#1f2937">'
                    f'<code>{h(tc[:200])}</code></div>'
                )
            if len(tcs) > 3:
                rest = "\n".join(
                    f'<div style="background:#f5f2e8;padding:4px 10px;'
                    f'border-radius:3px;margin:3px 0;color:#1f2937">'
                    f'<code>{h(tc[:200])}</code></div>'
                    for tc in tcs[3:]
                )
                out.append(
                    f'<details style="margin-top:4px"><summary style="cursor:'
                    f'pointer">Show all {len(tcs)} tool calls</summary>'
                    f'{rest}</details>'
                )
            out.append("</div>")
    out.append("</div>")

    if extract.get("pivots"):
        out.append('<h3 style="margin-top:24px">Pivot moments detected</h3>')
        for piv in extract["pivots"][:4]:
            out.append(
                f'<div class="rprt-pivot-callout">'
                f'<div class="pkind">⚡ Iteration {piv["iteration"]} · '
                f'{h(piv.get("kind", "transition"))}</div>'
                f'<div style="font-size:13px;line-height:1.55">'
                f'<strong>Before:</strong> "{md_inline(piv["before"][:300])}"</div>'
                f'<div style="font-size:13px;line-height:1.55;margin-top:6px">'
                f'<strong>After:</strong> "{md_inline(piv["after"][:300])}"</div>'
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
    """Surface every transcript file in logs/.

    Two passes:

    1) ``*.log.err`` — the raw agent-session stderr (codex/claude/opencode
       merged reasoning beats + tool I/O). NO byte cap — render everything
       inline. The bundle.tar.gz is the redundant offline fallback;
       Chrome PDF was empirically validated to handle 60+ MB of HTML
       cleanly (agent #3 benchmark, 2026-05-08).

    2) ``iteration_*.log`` and ``multiturn_session.log`` — the stdout side
       (typically a phase-completion checklist: "what was persisted +
       evaluator verdict"). Audit-2026-05-08 flagged this as
       complementary, not redundant, with .log.err. Rendered inline as a
       second appendix.

    Catastrophic-outlier safety valve: any single file above 5 MB is
    head/tail-truncated to keep HTML render time bounded. The bundle
    still has the full bytes.
    """
    parts: list[str] = []
    err_appendix = render_logs_appendix(
        session_dir / "logs",
        label="Agent transcripts (.log.err — full reasoning + tool I/O)",
        glob="*.log.err",
        max_per_file_chars=5 * 1024 * 1024,  # 5 MB safety valve only
        scrub_pii=True,
    )
    if err_appendix:
        parts.append(err_appendix)

    # iteration_*.log + multiturn_session.log — the stdout summary. The
    # default render_logs_appendix glob is *.log so we'd over-match the
    # .err side; pass an exact glob to scope to non-err logs only. Drop
    # PII scrub here — the stdout summaries are persistence checklists,
    # not reasoning text.
    stdout_appendix = render_logs_appendix(
        session_dir / "logs",
        label="Phase persistence summary (.log — stdout / what landed on disk)",
        glob="iteration_*.log",
        max_per_file_chars=0,  # no truncation — these are tiny (< 2 KB)
        scrub_pii=False,
    )
    if stdout_appendix:
        parts.append(stdout_appendix)
    multiturn_appendix = render_logs_appendix(
        session_dir / "logs",
        label="Multiturn session stdout (.log)",
        glob="multiturn_session.log",
        max_per_file_chars=0,
        scrub_pii=False,
    )
    if multiturn_appendix:
        parts.append(multiturn_appendix)

    return "\n\n".join(parts)


def build_session_md_block(session_dir: Path) -> str:
    """Surface session.md (the prompt the agent received) as an expandable
    top-level section.

    session.md is the highest-signal context for "what was the agent asked
    to do?" — system message + program doc + runtime context concatenated.
    Every lane writes one but no composer rendered it before this branch.
    Defaults closed because the file is typically 30-60 KB and the
    deliverable matters more than the prompt for skim reading.
    """
    sm = session_dir / "session.md"
    if not sm.is_file():
        return ""
    content = safe_read(sm) or ""
    if not content:
        return ""
    kb = len(content) // 1024
    return (
        f'<details class="rprt-faq" style="margin:16px 0">'
        f'<summary><strong>What the agent was asked to do</strong> · '
        f'<code>session.md</code> ({kb} KB)</summary>'
        f'<pre style="font-family:monospace;font-size:11.5px;line-height:1.55;'
        f'white-space:pre-wrap;background:var(--bg-soft);padding:12px;'
        f'border-radius:6px;margin:8px 0;max-height:600px;overflow:auto">'
        f'{h(content)}</pre></details>'
    )


def _walk_eval_files(session_dir: Path) -> list[Path]:
    """Find every *_eval.json + eval_feedback.json + drafts/*.eval.json +
    evals/*.json in a session_dir, sorted by relative path.

    Lane-agnostic: each lane writes its evaluator outputs differently
    (digest_eval.json for monitoring; eval_feedback.json for marketing_audit
    + competitive; drafts/*.eval.json for x_engine + linkedin_engine;
    evals/*.json for storyboard + monitoring + geo). This walks them all.
    """
    paths: list[Path] = []
    # Top-level *_eval.json (digest_eval, eval_feedback, etc.)
    for p in sorted(session_dir.glob("*_eval.json")):
        if p.is_file():
            paths.append(p)
    fb = session_dir / "eval_feedback.json"
    if fb.is_file() and fb not in paths:
        paths.append(fb)
    # Subdir evals
    evals_dir = session_dir / "evals"
    if evals_dir.is_dir():
        for p in sorted(evals_dir.glob("*.json")):
            if p.is_file():
                paths.append(p)
    drafts_dir = session_dir / "drafts"
    if drafts_dir.is_dir():
        for p in sorted(drafts_dir.glob("*.eval.json")):
            if p.is_file():
                paths.append(p)
    return paths


def build_evals_appendix(session_dir: Path) -> str:
    """Render every eval JSON the substrate wrote into the session, one
    <details> per file. Surfaces judge per-criterion scores, KEEP/REVISE
    decisions, and rationale prose that no composer rendered before.
    """
    eval_files = _walk_eval_files(session_dir)
    if not eval_files:
        return ""
    out = [f'<h2>Session evaluator outputs ({len(eval_files)})</h2>',
           '<p class="rprt-prose">Every <code>*_eval.json</code> + '
           '<code>eval_feedback.json</code> + per-artefact eval the substrate '
           'wrote during this session. Judge scores, KEEP/REVISE decisions, '
           'and rationale prose.</p>']
    for fp in eval_files:
        rel = fp.relative_to(session_dir)
        d = safe_json(fp)
        if d is None:
            out.append(
                f'<details class="rprt-faq"><summary><strong>{h(str(rel))}</strong> · '
                f'<em>(unreadable / malformed)</em></summary></details>'
            )
            continue
        # Surface top-level fields conspicuously (decision, score, criteria)
        decision = d.get("decision") if isinstance(d, dict) else None
        score = d.get("score") or d.get("composite") if isinstance(d, dict) else None
        size_kb = max(1, fp.stat().st_size // 1024)
        summary_chip = (
            f' · <code>{h(str(decision))}</code>' if decision else ""
        ) + (
            f' · score {h(str(score))}' if score is not None else ""
        )
        body = json.dumps(d, indent=2)
        # Defensive cap so a 5 MB eval JSON doesn't blow up the report; the
        # full file is on disk for anyone who needs it.
        if len(body) > 80000:
            body = body[:60000] + f"\n\n[...truncated {len(body) - 80000} chars...]\n\n" + body[-20000:]
        out.append(
            f'<details class="rprt-faq"><summary><strong>{h(str(rel))}</strong>'
            f' ({size_kb} KB){summary_chip}</summary>'
            f'<pre style="font-family:monospace;font-size:11px;line-height:1.5;'
            f'white-space:pre-wrap;background:var(--bg-soft);padding:10px;'
            f'border-radius:6px;margin:6px 0;max-height:500px;overflow:auto">'
            f'{h(body)}</pre></details>'
        )
    return "\n".join(out)


def build_intermediate_state_appendix(session_dir: Path) -> str:
    """Surface dot-prefixed cache/state files the agent + substrate wrote.

    Includes .last_eval_cache.json, .progress_snapshot, and any contents of
    .render_synthesis_cache/. These are the agent's intermediate / cached
    reasoning — often interesting because they show what the agent retried
    or what was cached vs recomputed.
    """
    interesting: list[Path] = []
    for name in (".last_eval_cache.json", ".progress_snapshot",
                 ".stage5_mirror"):
        p = session_dir / name
        if p.is_file():
            interesting.append(p)
    cache_dir = session_dir / ".render_synthesis_cache"
    if cache_dir.is_dir():
        for p in sorted(cache_dir.glob("*")):
            if p.is_file():
                interesting.append(p)
    if not interesting:
        return ""
    out = [f'<h2>Intermediate state ({len(interesting)})</h2>',
           '<p class="rprt-prose">Cache + progress + Stage-2 synthesis '
           'artefacts. These are not deliverables — they are what the agent '
           'and substrate wrote during the run. Surfaced for transparency.</p>']
    for fp in interesting:
        rel = fp.relative_to(session_dir)
        size_kb = max(1, fp.stat().st_size // 1024)
        # Try JSON first; fall back to raw text.
        d = safe_json(fp)
        if d is not None:
            body = json.dumps(d, indent=2)[:8000]
        else:
            body = (safe_read(fp, 8000) or "")[:8000]
        out.append(
            f'<details class="rprt-faq"><summary><strong>{h(str(rel))}</strong>'
            f' ({size_kb} KB)</summary>'
            f'<pre style="font-family:monospace;font-size:11px;line-height:1.5;'
            f'white-space:pre-wrap;background:var(--bg-soft);padding:10px;'
            f'border-radius:6px;margin:6px 0;max-height:400px;overflow:auto">'
            f'{h(body)}</pre></details>'
        )
    return "\n".join(out)


def build_decisions_panel(session_dir: Path) -> str:
    """Render KEEP/DISCARD/REVISE decisions per artefact when the lane
    snapshots them.

    x_engine + linkedin_engine write `eval_summary.draft_decisions` from
    `snapshot_evaluations`. Other lanes don't, but if results.jsonl carries
    a `decision` field we surface that too. Returns empty string when no
    structured decisions are available.
    """
    rows: list[tuple[str, str, str]] = []  # (artefact, decision, source)
    summary = safe_json(session_dir / "session_summary.json") or {}
    eval_summary = (summary.get("eval_summary")
                    or safe_json(session_dir / ".last_eval_cache.json")
                    or {})
    for d in (eval_summary.get("draft_decisions") or []):
        if isinstance(d, dict):
            rows.append((
                str(d.get("artifact", "?")),
                str(d.get("decision", "?")),
                "snapshot_evaluations",
            ))
    rj = session_dir / "results.jsonl"
    if rj.is_file():
        for line in rj.read_text(errors="replace").splitlines():
            try:
                obj = json.loads(line)
            except (ValueError, json.JSONDecodeError):
                continue
            if isinstance(obj, dict) and obj.get("decision"):
                rows.append((
                    str(obj.get("artifact", obj.get("type", "?"))),
                    str(obj["decision"]),
                    "results.jsonl",
                ))
    if not rows:
        return ""
    out = [
        '<h2>Per-artefact decisions</h2>',
        '<p class="rprt-prose">KEEP / DISCARD / REVISE per deliverable, '
        'sourced from the lane\'s snapshot_evaluations and results.jsonl.</p>',
        '<table class="rprt-key-table"><thead><tr>',
        '<th style="width:50%">Artefact</th>',
        '<th style="width:120px">Decision</th>',
        '<th>Source</th></tr></thead><tbody>',
    ]
    for art, dec, src in rows:
        out.append(
            f'<tr><td><code>{h(art)}</code></td>'
            f'<td><strong>{h(dec)}</strong></td>'
            f'<td style="font-size:11px;color:#6b7280"><code>{h(src)}</code></td></tr>'
        )
    out.append("</tbody></table>")
    return "\n".join(out)


def _render_subdir_dump(label: str, files: list[Path], session_dir: Path,
                       *, inline_top_n: int = 0, max_chars: int = 1500) -> str:
    """Render an arbitrary list of files (already filtered by the caller) as
    one section: optionally first N inline, the rest in a single <details>.

    Used by composers when they want to surface "everything in this subdir
    without dropping anything" — the silent-cap pattern is replaced with
    visible-but-collapsed.
    """
    if not files:
        return ""
    out = [f'<h2>{h(label)} ({len(files)})</h2>']
    for fp in files[:inline_top_n]:
        rel = fp.relative_to(session_dir)
        size_kb = max(1, fp.stat().st_size // 1024)
        if fp.suffix == ".json":
            d = safe_json(fp)
            body = json.dumps(d, indent=2)[:max_chars] if d is not None else (
                safe_read(fp, max_chars) or "")
        else:
            body = safe_read(fp, max_chars) or ""
        out.append(
            f'<div class="rprt-callout">'
            f'<div class="ckind"><code>{h(str(rel))}</code> ({size_kb} KB)</div>'
            f'<pre style="font-family:monospace;font-size:11px;line-height:1.5;'
            f'white-space:pre-wrap;background:#f8f6f0;padding:10px;'
            f'border-radius:6px;margin:6px 0;max-height:300px;overflow:auto">'
            f'{h(body)}</pre></div>'
        )
    rest = files[inline_top_n:]
    if rest:
        rest_blocks: list[str] = []
        for fp in rest:
            rel = fp.relative_to(session_dir)
            size_kb = max(1, fp.stat().st_size // 1024)
            if fp.suffix == ".json":
                d = safe_json(fp)
                body = json.dumps(d, indent=2)[:max_chars] if d is not None else (
                    safe_read(fp, max_chars) or "")
            else:
                body = safe_read(fp, max_chars) or ""
            rest_blocks.append(
                f'<details style="margin:6px 0"><summary><strong>'
                f'<code>{h(str(rel))}</code></strong> ({size_kb} KB)</summary>'
                f'<pre style="font-family:monospace;font-size:11px;line-height:1.5;'
                f'white-space:pre-wrap;background:#f8f6f0;padding:8px;'
                f'border-radius:6px;margin:6px 0;max-height:300px;overflow:auto">'
                f'{h(body)}</pre></details>'
            )
        out.append(
            f'<details class="rprt-faq" style="margin-top:8px">'
            f'<summary><strong>+ {len(rest)} more</strong></summary>'
            + "\n".join(rest_blocks) + "</details>"
        )
    return "\n".join(out)


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

    _append_data_transparency_sections(sections, session_dir, extract)

    return sections


_TOOL_KIND_BADGE = {
    "read":       "#dbeafe",  # light blue
    "search":     "#fef3c7",  # light amber
    "freddy_cli": "#dcfce7",  # light green
    "python":     "#ede9fe",  # light purple
    "git":        "#fee2e2",  # light red
    "fs_write":   "#fde2e2",  # peach
    "network":    "#cffafe",  # cyan
    "shell":      "#f5f2e8",  # neutral
}


def build_tool_io_timeline(extract: dict) -> str:
    """Per-iteration table of every ^exec$ tool call: kind badge, command,
    duration, expandable full output. Surfaces ~100% of the agent's tool
    interactions, structured.
    """
    if not extract or not extract.get("iterations"):
        return ""
    iterations = [
        it for it in extract["iterations"] if it.get("tool_call_records")
    ]
    if not iterations:
        return ""

    total_calls = sum(len(it["tool_call_records"]) for it in iterations)
    succeeded = sum(
        1 for it in iterations for r in it["tool_call_records"]
        if r.get("succeeded") is True
    )
    failed = sum(
        1 for it in iterations for r in it["tool_call_records"]
        if r.get("succeeded") is False
    )

    out = [
        '<h2>Tool I/O timeline · every <code>exec</code> call</h2>',
        f'<p class="rprt-prose">{total_calls} tool calls across '
        f'{len(iterations)} iterations · {succeeded} succeeded · {failed} '
        f'failed · the rest had no detected footer (typical for codex CLI '
        f'when output streamed late). Click a row to expand the full '
        f'command output the agent saw.</p>',
    ]

    for it in iterations:
        records = it["tool_call_records"]
        if not records:
            continue
        out.append(
            f'<h3 style="font-family:JetBrains Mono,monospace;font-size:12px;'
            f'letter-spacing:.10em;text-transform:uppercase;color:#0f3460;'
            f'margin:18px 0 6px">Iteration {it["iteration"]} · '
            f'{h(it["phase"])} · {len(records)} calls</h3>'
        )
        rows: list[str] = []
        for r in records:
            kind = r.get("kind", "shell")
            badge_color = _TOOL_KIND_BADGE.get(kind, "#f5f2e8")
            cmd = (r.get("command") or "").strip()
            output = (r.get("output") or "").strip()
            duration = r.get("duration_ms")
            succ = r.get("succeeded")
            paths = r.get("paths_read") or []
            duration_str = (
                f"{duration} ms" if duration is not None
                else "—"
            )
            succ_chip = (
                '<span style="color:#16a34a">✓</span>' if succ is True
                else '<span style="color:#dc2626">✗</span>' if succ is False
                else '<span style="color:#9ca3af">·</span>'
            )
            kind_chip = (
                f'<span style="background:{badge_color};padding:2px 8px;'
                f'border-radius:10px;font-size:10px;font-family:JetBrains Mono,'
                f'monospace;text-transform:uppercase;letter-spacing:.05em">'
                f'{h(kind)}</span>'
            )
            paths_chip = (
                f' <span style="color:#6b7280;font-size:11px">'
                f'reads: {h(", ".join(paths[:3]))}'
                f'{" ..." if len(paths) > 3 else ""}</span>'
                if paths else ""
            )
            cmd_summary = h(cmd[:160] + ("…" if len(cmd) > 160 else ""))
            output_block = ""
            if output:
                trimmed = output
                if len(trimmed) > 8000:
                    trimmed = trimmed[:6000] + (
                        f"\n\n[...truncated {len(output) - 8000} chars; "
                        f"full content in bundle.tar.gz...]\n\n"
                    ) + trimmed[-2000:]
                output_block = (
                    f'<details style="margin:4px 0 4px 1.4em">'
                    f'<summary style="cursor:pointer;font-size:11px;'
                    f'color:#6b7280">show output ({len(output)} chars)</summary>'
                    f'<pre style="font-family:monospace;font-size:11px;'
                    f'line-height:1.5;white-space:pre-wrap;background:#f5f2e8;'
                    f'padding:10px;border-radius:6px;margin:6px 0;'
                    f'max-height:400px;overflow:auto">{h(trimmed)}</pre>'
                    f'</details>'
                )
            rows.append(
                f'<li class="rprt-tool-row" style="padding:6px 0;'
                f'list-style:none;border-bottom:1px solid #f0ebe0">'
                f'{succ_chip} {kind_chip} '
                f'<code style="font-size:12px">{cmd_summary}</code> '
                f'<span style="color:#6b7280;font-size:11px">'
                f'· {duration_str}</span>{paths_chip}'
                f'{output_block}</li>'
            )
        out.append(
            f'<ul style="padding-left:0;margin:6px 0">{"".join(rows)}</ul>'
        )

    return "\n".join(out)


def build_files_agent_read_panel(extract: dict, session_dir: Path) -> str:
    """Surface every file the agent appears to have READ during execution
    (cat / head / tail / sed / less / read-tool etc.), deduplicated, with
    the actual file content rendered inline when available on disk.

    Powerful for "what did the agent see at decision time?" — without this,
    a reviewer has to manually grep transcripts for read patterns.
    """
    if not extract or not extract.get("iterations"):
        return ""
    paths_to_iters: dict[str, list[int]] = {}
    for it in extract["iterations"]:
        for r in it.get("tool_call_records", []):
            for p in r.get("paths_read") or []:
                # Filter out things that obviously aren't real files
                if "/" not in p and "." not in p:
                    continue
                paths_to_iters.setdefault(p, []).append(it["iteration"])
    if not paths_to_iters:
        return ""

    out = [
        f'<h2>Files the agent read ({len(paths_to_iters)})</h2>',
        '<p class="rprt-prose">Every file path the agent dereferenced via '
        '<code>cat</code> / <code>head</code> / <code>tail</code> / '
        '<code>sed</code> / etc. across all iterations. Inline preview '
        'shows the file as it exists on disk now (which may differ from '
        'what the agent saw mid-run if subsequent iterations rewrote it). '
        'Listed in order of first read.</p>',
    ]

    # Group by top-level subdirectory for readability
    groups: dict[str, list[str]] = {}
    seen_order: list[str] = []
    for p in paths_to_iters:
        if p not in seen_order:
            seen_order.append(p)
        top = p.split("/", 1)[0] if "/" in p else "(other)"
        groups.setdefault(top, []).append(p)

    for top in sorted(groups):
        paths_in_group = groups[top]
        out.append(
            f'<details open style="margin:8px 0">'
            f'<summary style="cursor:pointer;font-weight:600">'
            f'<code>{h(top)}/</code> · {len(paths_in_group)} read'
            f'{"s" if len(paths_in_group) != 1 else ""}</summary>'
            f'<ul style="padding-left:0;margin:6px 0">'
        )
        for p in paths_in_group:
            iters = sorted(set(paths_to_iters[p]))
            iter_chip = (
                f'<span style="color:#6b7280;font-size:11px;'
                f'font-family:JetBrains Mono,monospace">'
                f'iter {",".join(str(i) for i in iters)}</span>'
            )
            disk_path = session_dir / p
            preview = ""
            if not disk_path.is_absolute():
                # Try several anchors: session_dir, session_dir.parents[3]
                # (variant root), CWD
                candidates = [disk_path]
                if len(session_dir.parents) >= 3:
                    candidates.append(session_dir.parents[2] / p)
                for cand in candidates:
                    if cand.is_file() and cand.suffix.lower() in {
                        ".md", ".txt", ".json", ".yaml", ".yml", ".log", ".err",
                        ".jsonl", ".csv", ".html", ".sh", ".py",
                    } and cand.stat().st_size <= 64 * 1024:
                        try:
                            preview = cand.read_text(
                                encoding="utf-8", errors="replace"
                            )[:32000]
                            break
                        except OSError:
                            pass
            preview_block = ""
            if preview:
                preview_block = (
                    f'<details style="margin:4px 0 4px 1.4em">'
                    f'<summary style="cursor:pointer;font-size:11px;'
                    f'color:#6b7280">show inline ({len(preview)} chars)'
                    f'</summary>'
                    f'<pre style="font-family:monospace;font-size:11px;'
                    f'line-height:1.5;white-space:pre-wrap;background:#f5f2e8;'
                    f'padding:10px;border-radius:6px;margin:6px 0;'
                    f'max-height:400px;overflow:auto">{h(preview)}</pre>'
                    f'</details>'
                )
            out.append(
                f'<li style="padding:4px 0;list-style:none;'
                f'border-bottom:1px solid #f0ebe0">'
                f'<code style="font-size:12px">{h(p)}</code> {iter_chip}'
                f'{preview_block}</li>'
            )
        out.append('</ul></details>')

    return "\n".join(out)


def build_session_events_timeline(session_dir: Path) -> str:
    """Render session_dir/events.jsonl as a timeline table.

    The events log is populated by harness.agent._emit_session_event at
    agent_spawn + agent_complete points. Operators can disable via
    AUTORESEARCH_SESSION_EVENTS=0; if disabled or empty, this section
    is omitted entirely.
    """
    events_path = session_dir / "events.jsonl"
    if not events_path.is_file() or events_path.stat().st_size == 0:
        return ""
    rows: list[dict] = []
    try:
        for line in events_path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                continue
    except OSError:
        return ""
    if not rows:
        return ""
    out = [
        '<h2>Session event timeline · events.jsonl</h2>',
        '<p class="rprt-prose">Structured per-event log of agent spawns + '
        'completions, written via the autoresearch.events module '
        '(flock + rotation + atomic flush). One row per event in '
        'chronological order.</p>',
        '<table class="rprt-key-table"><thead><tr>',
        '<th style="width:200px">Timestamp (UTC)</th>',
        '<th style="width:140px">Event</th>',
        '<th>Details</th></tr></thead><tbody>',
    ]
    for ev in rows:
        ts = str(ev.get("timestamp", "—"))
        kind = str(ev.get("kind", "—"))
        details = {
            k: v for k, v in ev.items()
            if k not in ("timestamp", "kind")
        }
        details_str = " · ".join(
            f"<code>{h(k)}</code>=<code>{h(str(v)[:200])}</code>"
            for k, v in details.items()
        )
        out.append(
            f'<tr><td style="font-size:11px;font-family:monospace">{h(ts)}</td>'
            f'<td><strong>{h(kind)}</strong></td>'
            f'<td style="font-size:12px">{details_str}</td></tr>'
        )
    out.append("</tbody></table>")
    return "\n".join(out)


def _append_data_transparency_sections(
    sections: list[tuple[str, str]], session_dir: Path,
    extract: dict | None = None,
) -> None:
    """Append the cross-lane "everything visible" sections to every composer.

    Order: per-artefact decisions → evals appendix → events timeline →
    tool I/O timeline → files-agent-read panel → session.md (the prompt) →
    intermediate state → transcripts. The intent is "deliverable +
    reasoning first; raw substrate second." All sections default-closed
    inside their own <details> blocks (except the section <h2>) so HTML
    stays paginated in PDF output.
    """
    decisions_html = build_decisions_panel(session_dir)
    if decisions_html:
        sections.append(("decisions", decisions_html))
    evals_html = build_evals_appendix(session_dir)
    if evals_html:
        sections.append(("evals", evals_html))
    events_html = build_session_events_timeline(session_dir)
    if events_html:
        sections.append(("events", events_html))
    if extract:
        tool_io_html = build_tool_io_timeline(extract)
        if tool_io_html:
            sections.append(("tool_io", tool_io_html))
        files_read_html = build_files_agent_read_panel(extract, session_dir)
        if files_read_html:
            sections.append(("files_read", files_read_html))
    session_md_html = build_session_md_block(session_dir)
    if session_md_html:
        sections.append((
            "session_md",
            f'<h2>Prompt the agent received</h2>{session_md_html}',
        ))
    interm_html = build_intermediate_state_appendix(session_dir)
    if interm_html:
        sections.append(("intermediate", interm_html))
    transcripts_html = build_transcripts_appendix(session_dir)
    if transcripts_html:
        sections.append(("transcripts", transcripts_html))


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
    _append_data_transparency_sections(sections, session_dir, extract)
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
    _append_data_transparency_sections(sections, session_dir, extract)
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
    _append_data_transparency_sections(sections, session_dir, extract)
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

    # The Stage-5 deliverable mirror — detect by the marker file written by
    # _mirror_deliverable_to_session_dir, NOT by report.html existence (the
    # composer would otherwise read its own prior output as a "Stage-5 mirror"
    # on rerun, caught by 2026-05-08 correctness review).
    stage5_marker = session_dir / ".stage5_mirror"
    is_stage5_mirror = stage5_marker.exists()
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
        ("Has Stage-5", "yes" if is_stage5_mirror else "no"),
    ])))

    if is_stage5_mirror and (stage5_html.exists() or stage5_pdf.exists()):
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
    _append_data_transparency_sections(sections, session_dir, extract)
    return sections


_X_LENGTH_BRACKETS = {
    "sharp": (250, 300),
    "build": (500, 900),
    "case_study": (1000, 1500),
}

_LINKEDIN_LENGTH_BRACKETS = {
    "short_take": (500, 900),
    "thought_leader": (1500, 2500),
    "case_study": (2500, 3000),
}


def _parse_draft_md(text: str) -> dict:
    """Parse a draft .md file into structured fields.

    The contract (per master plan v13 §2.2 + session_eval_x_engine.py /
    session_eval_linkedin_engine.py):
      - YAML frontmatter at the top: ``---\\n<key>: <val>\\n---``
      - One ``[BODY] ... [/BODY]`` block (the post text)
      - One ``[META] ... [/META]`` block (hook, authority_anchor,
        specific_number, attribution; LinkedIn adds hashtags)

    Returns: ``{frontmatter: dict, body: str, meta: dict, raw: str,
    char_count: int}``. Missing pieces stay empty; the gates report
    structural failures via session_eval_*.py, not here.
    """
    result = {"frontmatter": {}, "body": "", "meta": {}, "raw": text,
              "char_count": 0}
    # Frontmatter
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if fm:
        for line in fm.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                result["frontmatter"][k.strip()] = v.strip()
    body_m = re.search(r"\[BODY\]\s*\n(.*?)\n\[/BODY\]", text, re.DOTALL)
    if body_m:
        body = body_m.group(1).strip()
        result["body"] = body
        result["char_count"] = len(body)
    meta_m = re.search(r"\[META\]\s*\n(.*?)\n\[/META\]", text, re.DOTALL)
    if meta_m:
        for line in meta_m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                result["meta"][k.strip()] = v.strip()
    return result


def _render_drafts_section(
    session_dir: Path,
    *,
    platform: str,
    length_brackets: dict[str, tuple[int, int]],
) -> tuple[list[tuple[str, str]], int, int]:
    """Render every drafts/<id>.md as one block: frontmatter + body + meta
    + per-draft eval JSON. Mirrors compose_marketing_audit's "everything
    visible" stance — no top-N caps; rest of drafts go inside <details>.

    Returns (sections, total_drafts, ship_eligible_drafts).
    """
    sections: list[tuple[str, str]] = []
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.is_dir():
        return sections, 0, 0
    drafts = sorted(drafts_dir.glob("*.md"))
    if not drafts:
        return sections, 0, 0

    rendered_blocks: list[str] = []
    ship_eligible = 0
    for draft_path in drafts:
        text = safe_read(draft_path) or ""
        parsed = _parse_draft_md(text)
        eval_path = draft_path.with_suffix(".eval.json")
        eval_data = safe_json(eval_path) if eval_path.exists() else None
        decision = (eval_data or {}).get("decision") if isinstance(eval_data, dict) else None
        if str(decision).upper() == "KEEP":
            ship_eligible += 1
        bracket = parsed["frontmatter"].get("length_bracket", "?")
        bracket_lo, bracket_hi = length_brackets.get(bracket, (0, 0))
        char_count = parsed["char_count"]
        in_bracket = (
            bracket in length_brackets
            and bracket_lo <= char_count <= bracket_hi
        )
        bracket_label = (
            f"{char_count} chars · {bracket} [{bracket_lo}-{bracket_hi}]"
            if bracket in length_brackets
            else f"{char_count} chars · bracket={bracket}"
        )
        bracket_class = "success" if in_bracket else "warn"
        decision_chip = (
            f' · <strong>{h(str(decision))}</strong>' if decision else ""
        )
        # Hero card
        block = [
            f'<div class="rprt-callout {bracket_class}">',
            f'<div class="ckind">{h(platform)} draft · '
            f'<code>{h(draft_path.name)}</code>{decision_chip}</div>',
            f'<div class="ctitle">{h(parsed["frontmatter"].get("draft_id", draft_path.stem))} '
            f'<span style="font-size:13px;font-weight:400;color:#6b7280">· '
            f'angle <code>{h(parsed["frontmatter"].get("angle_id", "?"))}</code></span></div>',
            f'<p style="font-size:12px;color:#6b7280;margin:6px 0">'
            f'<strong>Bracket:</strong> {h(bracket_label)} · '
            f'<strong>Voice pillar:</strong> '
            f'<code>{h(parsed["frontmatter"].get("voice_pillar", "—"))}</code></p>',
        ]
        # Body
        if parsed["body"]:
            block.append(
                f'<details open style="margin:8px 0">'
                f'<summary><strong>[BODY]</strong> ({char_count} chars)</summary>'
                f'<pre style="font-family:Georgia,serif;font-size:13.5px;'
                f'line-height:1.6;white-space:pre-wrap;background:#fffaf0;'
                f'padding:12px;border-radius:6px;margin:6px 0">'
                f'{h(parsed["body"])}</pre></details>'
            )
        # Meta block
        if parsed["meta"]:
            meta_rows = "".join(
                f'<tr><td><code>{h(k)}</code></td>'
                f'<td style="font-size:12.5px">{h(v)}</td></tr>'
                for k, v in parsed["meta"].items()
            )
            block.append(
                f'<details style="margin:8px 0"><summary><strong>[META]</strong>'
                f' ({len(parsed["meta"])} fields)</summary>'
                f'<table class="rprt-key-table" style="margin:6px 0">'
                f'<tbody>{meta_rows}</tbody></table></details>'
            )
        # Per-draft eval
        if eval_data is not None:
            eval_body = json.dumps(eval_data, indent=2)
            if len(eval_body) > 8000:
                eval_body = eval_body[:8000] + f"\n\n[...truncated {len(eval_body) - 8000} chars...]\n"
            block.append(
                f'<details style="margin:8px 0">'
                f'<summary><strong>Per-draft eval</strong> · '
                f'<code>{h(eval_path.name)}</code></summary>'
                f'<pre style="font-family:monospace;font-size:11px;'
                f'line-height:1.5;white-space:pre-wrap;background:var(--bg-soft);'
                f'padding:10px;border-radius:6px;margin:6px 0;max-height:400px;'
                f'overflow:auto">{h(eval_body)}</pre></details>'
            )
        # Frontmatter dump (for transparency)
        if parsed["frontmatter"]:
            fm_rows = "".join(
                f'<tr><td><code>{h(k)}</code></td>'
                f'<td style="font-size:12.5px">{h(v)}</td></tr>'
                for k, v in parsed["frontmatter"].items()
            )
            block.append(
                f'<details style="margin:8px 0">'
                f'<summary><strong>YAML frontmatter</strong></summary>'
                f'<table class="rprt-key-table" style="margin:6px 0">'
                f'<tbody>{fm_rows}</tbody></table></details>'
            )
        # Raw markdown (full file)
        size_kb = max(1, draft_path.stat().st_size // 1024)
        block.append(
            f'<details style="margin:8px 0">'
            f'<summary><strong>Raw <code>{h(draft_path.name)}</code></strong> '
            f'({size_kb} KB)</summary>'
            f'<pre style="font-family:monospace;font-size:11.5px;'
            f'line-height:1.55;white-space:pre-wrap;background:#f5f2e8;'
            f'padding:10px;border-radius:6px;margin:6px 0;max-height:500px;'
            f'overflow:auto">{h(parsed["raw"])}</pre></details>'
        )
        block.append("</div>")
        rendered_blocks.append("\n".join(block))

    # Render: first 2 inline (open), rest behind a single <details>
    out = [f'<h2>Drafts ({len(drafts)} · {ship_eligible} ship-eligible)</h2>']
    for blk in rendered_blocks[:2]:
        out.append(blk)
    if len(rendered_blocks) > 2:
        out.append(
            f'<details class="rprt-faq" style="margin-top:8px">'
            f'<summary><strong>+ {len(rendered_blocks) - 2} more drafts</strong>'
            f'</summary>'
            + "\n".join(rendered_blocks[2:]) + "</details>"
        )
    sections.append((f"{platform.lower()}_drafts", "\n".join(out)))
    return sections, len(drafts), ship_eligible


def _render_angle_section(session_dir: Path) -> str:
    """Surface the angle JSON the agent worked from (drafts/ are written
    in response to one angle per session)."""
    angles_dir = session_dir / "angles"
    if not angles_dir.is_dir():
        return ""
    angles = sorted(angles_dir.glob("*.json"))
    if not angles:
        return ""
    out = [f'<h2>Source angles ({len(angles)})</h2>',
           '<p class="rprt-prose">The agent generated drafts in response '
           'to these angles. Cached at session start via '
           '<code>xeng angle-show $ANGLE_ID</code>.</p>']
    for fp in angles:
        d = safe_json(fp) or {}
        size_kb = max(1, fp.stat().st_size // 1024)
        body = json.dumps(d, indent=2)
        if len(body) > 6000:
            body = body[:6000] + f"\n\n[...truncated {len(body) - 6000} chars...]"
        title = d.get("title") or d.get("angle_title") or fp.stem
        out.append(
            f'<details class="rprt-faq" open><summary><strong>{h(str(title))}</strong>'
            f' · <code>{h(fp.name)}</code> ({size_kb} KB)</summary>'
            f'<pre style="font-family:monospace;font-size:11.5px;line-height:1.55;'
            f'white-space:pre-wrap;background:var(--bg-soft);padding:10px;'
            f'border-radius:6px;margin:6px 0;max-height:480px;overflow:auto">'
            f'{h(body)}</pre></details>'
        )
    return "\n".join(out)


def compose_x_engine(
    session_dir: Path, client: str, extract: dict
) -> list[tuple[str, str]]:
    """X engine composer.

    Surfaces every draft as a first-class card (frontmatter + body + meta +
    per-draft eval JSON), the angles/<angle>.json source data, full
    findings + reasoning + transcripts via the cross-lane helpers.
    """
    summary = safe_json(session_dir / "session_summary.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
    results: list[dict] = []
    rj = session_dir / "results.jsonl"
    if rj.exists():
        for line in rj.read_text(errors="replace").splitlines():
            try:
                results.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                pass

    drafts_sections, draft_count, ship_eligible = _render_drafts_section(
        session_dir, platform="X", length_brackets=_X_LENGTH_BRACKETS,
    )

    sections: list[tuple[str, str]] = [
        ("hero", build_hero(
            f"X ENGINE · {client}",
            f"X drafts for **{client}** · {draft_count} drafts written · "
            f"{ship_eligible} ship-eligible · "
            f"{summary.get('iterations', {}).get('total', '?')} iterations.",
        )),
        ("stats", build_stat_grid([
            ("Iterations", str(summary.get("iterations", {}).get("total", "?"))),
            ("Drafts", str(draft_count)),
            ("Ship-eligible", str(ship_eligible)),
            ("Status", str(summary.get("status", "—"))),
        ])),
    ]
    sections.extend(drafts_sections)

    angle_html = _render_angle_section(session_dir)
    if angle_html:
        sections.append(("angles", angle_html))

    if findings:
        sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    if results:
        sections.append(("phases", f'<h2>Phase ledger · results.jsonl</h2>{build_phase_ledger(results)}'))
    _append_data_transparency_sections(sections, session_dir, extract)
    return sections


def compose_linkedin_engine(
    session_dir: Path, client: str, extract: dict
) -> list[tuple[str, str]]:
    """LinkedIn engine composer — sibling of compose_x_engine.

    Same shape as X engine. Length brackets differ (short_take 500-900,
    thought_leader 1500-2500, case_study 2500-3000) and the [META] block
    must include a ``hashtags`` field on top of the X-shape requirements.
    """
    summary = safe_json(session_dir / "session_summary.json") or {}
    findings = parse_findings_md(safe_read(session_dir / "findings.md") or "")
    results: list[dict] = []
    rj = session_dir / "results.jsonl"
    if rj.exists():
        for line in rj.read_text(errors="replace").splitlines():
            try:
                results.append(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                pass

    drafts_sections, draft_count, ship_eligible = _render_drafts_section(
        session_dir, platform="LinkedIn",
        length_brackets=_LINKEDIN_LENGTH_BRACKETS,
    )

    sections: list[tuple[str, str]] = [
        ("hero", build_hero(
            f"LINKEDIN ENGINE · {client}",
            f"LinkedIn drafts for **{client}** · {draft_count} drafts written · "
            f"{ship_eligible} ship-eligible · "
            f"{summary.get('iterations', {}).get('total', '?')} iterations.",
        )),
        ("stats", build_stat_grid([
            ("Iterations", str(summary.get("iterations", {}).get("total", "?"))),
            ("Drafts", str(draft_count)),
            ("Ship-eligible", str(ship_eligible)),
            ("Status", str(summary.get("status", "—"))),
        ])),
    ]
    sections.extend(drafts_sections)

    angle_html = _render_angle_section(session_dir)
    if angle_html:
        sections.append(("angles", angle_html))

    if findings:
        sections.append(("findings", f'<h2>Findings</h2>{build_findings(findings)}'))
    sections.append(("reasoning", f'<h2>Investigation trail</h2>{build_reasoning_trail(extract)}'))
    if results:
        sections.append(("phases", f'<h2>Phase ledger · results.jsonl</h2>{build_phase_ledger(results)}'))
    _append_data_transparency_sections(sections, session_dir, extract)
    return sections


# ============================================================================
# Session bundle + downloadable file tree
# ============================================================================

# File extensions that get an inline preview <details> alongside the download
# link. Anything else is a download-only link. The threshold is conservative —
# small text/JSON inlines, big binaries don't.
_INLINE_PREVIEW_EXTS = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".log", ".err",
    ".html", ".htm", ".jsonl", ".csv", ".xml", ".sh", ".py",
}
_INLINE_PREVIEW_BYTES = 128 * 1024  # 128 KB cap for inlining
_INLINE_PREVIEW_RENDER_BYTES = 96 * 1024  # render at most 96 KB per file


def _guess_mime(p: Path) -> str:
    suf = p.suffix.lower()
    if suf in (".md", ".txt", ".log", ".err", ".csv"):
        return "text/plain; charset=utf-8"
    if suf in (".json", ".jsonl"):
        return "application/json; charset=utf-8"
    if suf in (".html", ".htm"):
        return "text/html; charset=utf-8"
    if suf in (".yaml", ".yml"):
        return "application/yaml; charset=utf-8"
    if suf == ".png":
        return "image/png"
    if suf in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suf == ".pdf":
        return "application/pdf"
    if suf in (".js", ".mjs"):
        return "text/javascript; charset=utf-8"
    return "application/octet-stream"


def _file_tree_groups(
    session_dir: Path,
    *,
    exclude: tuple[str, ...] = (
        "report.html", "report.pdf", "report-screenshot.png", "bundle.tar.gz",
        ".report-print.html",
    ),
) -> dict[str, list[Path]]:
    """Group every file in session_dir by its top-level subdirectory ('' for
    files at the root). Excludes the rendered artefacts themselves so the
    bundle/tree don't recurse on their own outputs.
    """
    groups: dict[str, list[Path]] = {}
    for p in sorted(session_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name in exclude:
            continue
        rel = p.relative_to(session_dir)
        top = rel.parts[0] if len(rel.parts) > 1 else ""
        groups.setdefault(top, []).append(p)
    return groups


def _render_file_row(p: Path, session_dir: Path) -> str:
    """One file row: relative-href download link + (text-only) inline preview
    in a closed <details>. Relative href works on local-disk reading and via
    the portal route (task #14) once that lands.
    """
    rel = p.relative_to(session_dir)
    rel_str = str(rel)
    size = p.stat().st_size
    size_label = (
        f"{size} B" if size < 1024
        else f"{size // 1024} KB" if size < 1024 * 1024
        else f"{size / (1024 * 1024):.1f} MB"
    )
    download_link = (
        f'<a href="{h(rel_str)}" download="{h(p.name)}">'
        f'<code>{h(rel_str)}</code></a> '
        f'<span style="color:#6b7280;font-size:11px">({size_label})</span>'
    )

    # Inline preview only for text/JSON-ish files under the cap.
    can_preview = (
        p.suffix.lower() in _INLINE_PREVIEW_EXTS
        and size > 0
        and size <= _INLINE_PREVIEW_BYTES
    )
    if not can_preview:
        return f'<li class="rprt-file-row">{download_link}</li>'

    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return f'<li class="rprt-file-row">{download_link}</li>'
    if len(content) > _INLINE_PREVIEW_RENDER_BYTES:
        content = (
            content[: _INLINE_PREVIEW_RENDER_BYTES // 2]
            + f"\n\n[...truncated {len(content) - _INLINE_PREVIEW_RENDER_BYTES} chars; "
            + f"download <code>{rel_str}</code> for full content...]\n\n"
            + content[-_INLINE_PREVIEW_RENDER_BYTES // 2:]
        )
    return (
        f'<li class="rprt-file-row">{download_link}'
        f'<details style="margin:4px 0 4px 1.4em"><summary style="cursor:pointer;'
        f'font-size:11px;color:#6b7280">show inline</summary>'
        f'<pre style="font-family:monospace;font-size:11px;line-height:1.5;'
        f'white-space:pre-wrap;background:#f5f2e8;padding:8px;border-radius:6px;'
        f'margin:6px 0;max-height:480px;overflow:auto">{h(content)}</pre>'
        f'</details></li>'
    )


def build_session_bundle_section(
    session_dir: Path, bundle_path: Path | None
) -> str:
    """Top-level "Session bundle + every file" section.

    HTML mode: renders the full file tree grouped by top-level directory,
    each file with a relative `<a download>` link and (for small text/JSON)
    an inline preview in a closed <details>. PDF mode: hidden via
    `@media print` CSS injected at the section level — the PDF instead
    shows only a one-line "download bundle.tar.gz at <portal-URL>" stub
    inside the section's `.rprt-bundle-print` block.
    """
    groups = _file_tree_groups(session_dir)
    file_count = sum(len(v) for v in groups.values())
    bundle_kb = (
        bundle_path.stat().st_size // 1024
        if bundle_path is not None and bundle_path.is_file()
        else 0
    )
    bundle_link = (
        f'<a href="bundle.tar.gz" download="bundle.tar.gz" '
        f'style="display:inline-block;padding:8px 16px;'
        f'background:var(--accent,#0f3460);color:white;border-radius:6px;'
        f'text-decoration:none;font-weight:600">'
        f'⬇ Download all ({bundle_kb} KB · {file_count} files)</a>'
        if bundle_path is not None
        else (
            f'<em style="color:#6b7280">bundle.tar.gz not generated '
            f'(no files to bundle)</em>'
        )
    )

    # Per-section PDF/print rules: hide the file tree and the data-URI list
    # in the PDF so the printable artefact stays slim. PDF gets the bundle
    # link only.
    css = (
        '<style>'
        '.rprt-bundle-print { display:none }'
        '@media print {'
        '  .rprt-bundle-tree { display:none }'
        '  .rprt-bundle-print { display:block }'
        '}'
        '.rprt-file-row { padding:3px 0; list-style:none; '
        '  border-bottom:1px solid #f0ebe0 }'
        '.rprt-bundle-tree ul { padding-left:0; margin:6px 0 }'
        '.rprt-bundle-tree details > summary { cursor:pointer; '
        '  font-weight:600; padding:6px 0 }'
        '</style>'
    )

    blocks: list[str] = [css]
    blocks.append('<h2>Session bundle · every file</h2>')
    blocks.append(
        '<p class="rprt-prose">Every file the substrate or agent wrote into '
        'this session’s directory. Click a row to download. For small '
        'text / JSON files an inline preview is one click away. Use '
        '<strong>Download all</strong> to grab the whole session as one '
        '<code>.tar.gz</code>.</p>'
    )

    blocks.append(
        f'<div class="rprt-callout success" style="margin:12px 0">'
        f'<div class="ckind">single-archive download</div>'
        f'<div class="ctitle">Whole session in one tarball</div>'
        f'<p style="margin:8px 0">{bundle_link}</p></div>'
    )

    # PDF-only stub
    blocks.append(
        '<div class="rprt-bundle-print" style="margin:12px 0">'
        '<p class="rprt-prose">'
        '<strong>Full session artefacts:</strong> the printable PDF omits '
        f'the {file_count}-file inline tree to stay slim. '
        f'Open <code>report.html</code> alongside this PDF, or download '
        f'<code>bundle.tar.gz</code> ({bundle_kb} KB) for the complete set.'
        '</p></div>'
    )

    # HTML-only file tree
    tree_blocks: list[str] = ['<div class="rprt-bundle-tree">']
    # Root-level files first (key="")
    if "" in groups:
        rows = "".join(_render_file_row(p, session_dir) for p in groups[""])
        tree_blocks.append(
            '<details open><summary><strong>(root)</strong> '
            f'· {len(groups[""])} file{"s" if len(groups[""]) != 1 else ""}'
            f'</summary><ul>{rows}</ul></details>'
        )
    # Then subdirectories
    for top in sorted(k for k in groups if k):
        files = groups[top]
        rows = "".join(_render_file_row(p, session_dir) for p in files)
        tree_blocks.append(
            f'<details><summary><strong><code>{h(top)}/</code></strong>'
            f' · {len(files)} file{"s" if len(files) != 1 else ""}'
            f'</summary><ul>{rows}</ul></details>'
        )
    tree_blocks.append('</div>')
    blocks.append("\n".join(tree_blocks))

    return "\n".join(blocks)


COMPOSERS = {
    "geo": compose_geo,
    "competitive": compose_competitive,
    "monitoring": compose_monitoring,
    "storyboard": compose_storyboard,
    "marketing_audit": compose_marketing_audit,
    "x_engine": compose_x_engine,
    "linkedin_engine": compose_linkedin_engine,
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
    "blockquote", "br", "span", "details", "summary",
    # SVG primitives — agent-authored charts. NO foreignObject (would let
    # arbitrary HTML escape via <svg>), NO image / use / script. Note: nh3
    # tokenises HTML5-style and lowercases tag names, so we keep the SVG
    # set lowercase here. linearGradient + stop are intentionally omitted
    # for now (sticking to solid fills keeps the case-folding question
    # moot; gradients can land later behind a separate review).
    "svg", "g", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "path", "text", "tspan", "title", "defs",
}

# Class allowlist enforced via nh3.clean(allowed_classes=...). Any class
# outside this set is stripped from the rendered class attribute. Per-tag
# rather than global — keeps an attacker from using class collisions to
# steer the document's shipped CSS through unrelated tags.
_AGENT_HTML_ALLOWED_CLASS_NAMES = {
    "rprt-meta-pattern", "rprt-callout", "success", "warn", "critical",
    "rprt-stat-grid", "rprt-stat-tile", "rprt-key-table",
    "rprt-finding-card", "rprt-pull-quote", "rprt-evidence-quote",
    "rprt-action-list", "rprt-action-row", "ckind", "ctitle",
    "num", "label", "qtext", "qattr", "priority",
    # New: visual-rich findings classes
    "rprt-spotlight", "rprt-chart", "rprt-insight", "rprt-metric",
    "rprt-recommendation", "rprt-evidence-row",
}
_AGENT_HTML_ALLOWED_CLASSES_PER_TAG = {
    tag: _AGENT_HTML_ALLOWED_CLASS_NAMES for tag in _AGENT_HTML_ALLOWED_TAGS
}

# SVG attributes the sanitizer keeps. NO event handlers (on*), NO style
# (would let CSS-injection via url() work), NO href / xlink:href (would let
# external resource fetch + javascript: URIs slip past the URL allowlist).
# All visual properties live in attributes that nh3's URL filter doesn't
# need to consult.
_SVG_ALLOWED_ATTRS = {
    # nh3 case-folds attribute names to lowercase before comparing against
    # this set; SVG spec is camelCase but the tokeniser normalises.
    "viewbox", "width", "height", "x", "y", "x1", "y1", "x2", "y2",
    "cx", "cy", "r", "rx", "ry", "d", "points", "fill", "stroke",
    "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-dasharray",
    "transform", "opacity", "fill-opacity", "stroke-opacity",
    "font-family", "font-size", "font-weight", "font-style",
    "text-anchor", "dominant-baseline", "alignment-baseline",
    "preserveaspectratio",
    "xmlns",
}

# Per-tag attribute allowlist for SVG. Other tags still get only `class`.
_SVG_TAGS = {
    "svg", "g", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "path", "text", "tspan", "title", "defs",
}

# Sanitizer version — bumped whenever the allowlist or sanitization rules
# change. Folded into the synthesis cache key so a sanitizer tightening
# invalidates stale cached HTML produced under the old contract.
_SANITIZER_VERSION = "v3-svg"


def _sanitize_agent_html(raw: str) -> str:
    """Strip the agent's HTML to the .rprt-* allowlist via nh3 (Rust ammonia).

    The previous regex-based implementation had multiple confirmed bypasses
    flagged by 2026-05-08 review: unquoted ``onclick=``, ``style=url(...)``
    exfil via the still-allowed style attribute, malformed
    ``<span/onclick=...>``, nested same-tag pairs. nh3 is a real
    HTML5-tokenizer-backed sanitizer so those bypass classes are no longer
    reachable — the cost is one direct dependency that's already in
    pyproject.toml.

    Contract:
      - tags  → only those in _AGENT_HTML_ALLOWED_TAGS survive
      - attrs → only ``class`` survives, and class values are filtered
                against _AGENT_HTML_ALLOWED_CLASS_NAMES (everything else
                including style / src / href / srcdoc / on* / title / lang
                / tabindex / data-* is stripped via attribute_filter)
      - comments stripped
      - URL schemes restricted to https/mailto (defense in depth — none of
        the allowed tags consume URL attrs anyway)

    Empty/None input returns "".
    """
    if not raw:
        return ""
    try:
        import nh3
    except ImportError:
        # nh3 is a direct pyproject dependency; if it ever goes missing,
        # drop the agent HTML rather than re-introduce the regex bypasses.
        print("  WARNING: nh3 not installed; dropping agent HTML for safety.",
              file=sys.stderr)
        return ""

    def _attribute_filter(tag: str, attr: str, value: str) -> str | None:
        """Per-tag attribute filter.

        - Non-SVG tags: only ``class`` (filtered against the allowlist).
        - SVG tags: ``class`` + the visual-attribute allowlist (no event
          handlers, no style, no href/xlink:href).

        Returning None drops the attribute. Returning a string keeps it.
        """
        if attr == "class":
            kept = " ".join(
                c for c in str(value).split()
                if c in _AGENT_HTML_ALLOWED_CLASS_NAMES
            )
            return kept if kept else None
        if tag in _SVG_TAGS and attr in _SVG_ALLOWED_ATTRS:
            # SVG attribute values are presentational — defense-in-depth
            # rejects values containing javascript: / data: / url() so
            # even a misclassified attribute can't smuggle a URL exploit.
            v = str(value).strip()
            low = v.lower()
            if any(s in low for s in ("javascript:", "data:", "url(")):
                return None
            return v
        return None

    # Per-tag attribute allowlist passed to nh3 — SVG tags get the visual
    # attribute set in addition to `class`; everything else gets only
    # `class`. The per-attribute filter above does the actual value-level
    # filtering; this just opens the gate at the tokenizer level.
    attributes_per_tag: dict[str, set[str]] = {}
    for tag in _AGENT_HTML_ALLOWED_TAGS:
        if tag in _SVG_TAGS:
            attributes_per_tag[tag] = {"class"} | _SVG_ALLOWED_ATTRS
        else:
            attributes_per_tag[tag] = {"class"}

    cleaned = nh3.clean(
        raw,
        tags=_AGENT_HTML_ALLOWED_TAGS,
        attributes=attributes_per_tag,
        attribute_filter=_attribute_filter,
        strip_comments=True,
        url_schemes={"https", "mailto"},
    )
    return cleaned.strip()


def _payload_signature(domain: str, lane_brief: str, payload: str) -> str:
    """SHA256 of (sanitizer_version, domain, lane_brief, payload) for idempotent caching.

    Sanitizer version is folded into the key so a tightening of
    _AGENT_HTML_ALLOWED_TAGS / _AGENT_HTML_ALLOWED_CLASS_NAMES /
    _sanitize_agent_html invalidates stale cached HTML produced under the
    old contract — caught by 2026-05-08 review (cache poisoning across
    sanitizer changes).
    """
    import hashlib
    h_ = hashlib.sha256()
    h_.update(_SANITIZER_VERSION.encode("utf-8"))
    h_.update(b"\x00")
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

    # Persist the prompt alongside the cached response. Same signature
    # ties request to response so a reviewer can audit "what we asked"
    # vs "what we got." Best-effort; never blocks.
    try:
        (cache_dir / f"{sig}.prompt.txt").write_text(prompt, encoding="utf-8")
    except OSError:
        pass

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


# ============================================================================
# Multi-section dynamic synthesis — agent picks N components and writes each
# ============================================================================

# Per-section briefs. Each is a self-contained framing of "what this section
# should accomplish" — the agent gets the same payload (extract + findings +
# lane excerpts) but a different editorial brief per call. This is what the
# user means by "the agent dynamically decides and writes code for components."
#
# Order matters: sections render in this order in the final report.
_MULTI_SECTION_BRIEFS: list[tuple[str, str]] = [
    (
        "executive_summary",
        "Write a 2-paragraph executive summary: lead with the verdict in one "
        "sentence, support with two specific measured deltas (numbers, proper "
        "nouns), and close with the single sharpest implication for the "
        "reader. Use <p> blocks. NO bullet lists. ~120 words rendered."
    ),
    (
        "top_finding_spotlight",
        "Pick the single most important finding from the data and dramatise "
        "it. Wrap in <div class='rprt-spotlight'>. Open with a 1-sentence "
        "hook in <strong>, then a <div class='rprt-pull-quote'><div "
        "class='qtext'>quoted evidence (max 30 words from the source data)"
        "</div><div class='qattr'>— attribution / source</div></div>, then "
        "a 2-3 sentence interpretation paragraph. ~80 words rendered."
    ),
    (
        "chart_view",
        "Pick ONE quantitative angle from the data that benefits from a "
        "chart and emit a CHART DIRECTIVE that the renderer will substitute "
        "with SVG. Format: [[chart:bar:label1=value1,label2=value2,...|"
        "title=Optional Title]] (or :donut: instead of :bar: for shares "
        "summing to 100). Wrap the directive in "
        "<div class='rprt-chart'>...</div>. Add a <p> below explaining what "
        "the chart shows + the takeaway. Skip this section entirely if no "
        "quantitative angle is interesting — output the literal string SKIP."
    ),
    (
        "what_changed",
        "Surface 1-3 pivot moments where the agent course-corrected mid-"
        "session: the failure / friction, then the adaptation, then the "
        "outcome. Use <div class='rprt-evidence-row'>...</div> blocks. "
        "Reference iteration numbers + specific evidence from the pivots "
        "block. ~150 words rendered."
    ),
    (
        "recommendations",
        "Compose a prioritised next-step action list. Use <div "
        "class='rprt-action-list'>...</div> wrapping <div "
        "class='rprt-action-row'><div class='priority'>1</div>"
        "<div>action text</div></div> blocks (3-5 items). Each action must "
        "be specific and tied to data above (mention slug / number / proper "
        "noun). NO generic advice."
    ),
]


_CHART_DIRECTIVE_RE = re.compile(
    r"\[\[chart:(?P<kind>bar|donut|sparkline|timeline):"
    r"(?P<data>[^|\]]*)"
    r"(?:\|title=(?P<title>[^\]]*))?\]\]"
)


def _substitute_chart_directives(html: str) -> str:
    """Replace `[[chart:KIND:k=v,k=v|title=...]]` directives with inline SVG.

    Supported kinds: bar, donut, sparkline, timeline. Numeric values only;
    non-numeric values are dropped. Malformed directives are removed
    silently rather than rendered as literal text (less surprising in
    a report).
    """
    def _parse_data(raw: str) -> list[tuple[str, float]]:
        pairs: list[tuple[str, float]] = []
        for chunk in raw.split(","):
            chunk = chunk.strip()
            if not chunk or "=" not in chunk:
                continue
            label, _, val = chunk.partition("=")
            label = label.strip()
            try:
                num = float(val.strip())
            except ValueError:
                continue
            if label:
                pairs.append((label, num))
        return pairs

    def _replace(m: re.Match) -> str:
        kind = m.group("kind")
        data_raw = m.group("data") or ""
        title = (m.group("title") or "").strip() or None
        pairs = _parse_data(data_raw)
        if kind == "bar":
            return _chart_bar(pairs, title=title)
        if kind == "donut":
            return _chart_donut(pairs, title=title)
        if kind == "sparkline":
            return _chart_spark([v for _, v in pairs])
        if kind == "timeline":
            # Treat values as 0..1 fractions; clamp.
            evs = [(lab, max(0.0, min(1.0, v))) for lab, v in pairs]
            return _chart_timeline(evs)
        return ""

    return _CHART_DIRECTIVE_RE.sub(_replace, html)


def agent_compose_multi_section(
    domain: str,
    client: str,
    session_dir: Path,
    extract: dict,
    findings_md: str | None,
) -> list[tuple[str, str]]:
    """Orchestrate N parallel-shape Stage-2 calls — one per
    ``_MULTI_SECTION_BRIEFS`` entry — so the agent dynamically writes a
    custom HTML+SVG block per concern.

    Returns list of (section_id, sanitized_html) pairs. Empty list when
    the backend is disabled (RENDER_BACKEND=none) or every section's
    output is too short / contains the literal `SKIP`.

    Each section is cached independently by (sanitizer_version, domain,
    section_id, payload-hash) so a re-render after a config change only
    re-spawns the affected sections.

    AUTORESEARCH_RENDER_MULTI_SECTION env var:
      - default on. Set to 0/off/false/skip to fall back to the legacy
        single-section path (one call instead of N).
    """
    multi_val = os.environ.get(
        "AUTORESEARCH_RENDER_MULTI_SECTION", "1"
    ).strip().lower()
    if multi_val in ("0", "off", "false", "no", "skip"):
        return []
    backend = os.environ.get("RENDER_BACKEND", "codex").lower()
    if backend in ("none", "off", "skip"):
        return []

    excerpts = _gather_lane_excerpts(domain, session_dir)
    payload = _build_payload(extract, findings_md or "", excerpts)
    cache_dir = session_dir / ".render_synthesis_cache"
    cache_dir.mkdir(exist_ok=True)
    out: list[tuple[str, str]] = []

    for section_id, section_brief in _MULTI_SECTION_BRIEFS:
        # Per-section signature so a brief tweak only re-renders that one
        # section.
        sig = _payload_signature(
            domain, f"{section_id}::{section_brief}", payload,
        )
        cache_path = cache_dir / f"sec-{section_id}-{sig}.html"
        if cache_path.exists():
            try:
                cached = cache_path.read_text(encoding="utf-8")
                if cached.strip() and cached.strip() != "SKIP":
                    out.append((section_id, _substitute_chart_directives(cached)))
                    print(f"  ✓ multi-section[{section_id}] cache hit "
                          f"({len(cached)} chars · {sig})", file=sys.stderr)
                continue
            except OSError:
                pass

        prompt = (
            f"You are the report editor for the FREDDY autoresearch system.\n"
            f"Lane: {domain} · Client: {client} · Section: {section_id}\n\n"
            f"SECTION BRIEF:\n{section_brief}\n\n"
            f"CONSTRAINTS — strictly enforced by sanitizer:\n"
            f"  - Output ONLY HTML; no markdown, no preamble, no closing.\n"
            f"  - Allowed tags: section, div, h3, h4, p, ul, ol, li, strong,\n"
            f"    em, code, table, thead, tbody, tr, td, th, blockquote, span,\n"
            f"    br, details, summary, plus svg + g + rect + circle + line +\n"
            f"    polyline + polygon + path + text + tspan (for charts).\n"
            f"  - Allowed classes: rprt-callout (with success/warn/critical),\n"
            f"    ckind, ctitle, rprt-stat-grid, rprt-stat-tile (.num + .label),\n"
            f"    rprt-pull-quote (.qtext + .qattr), rprt-evidence-quote,\n"
            f"    rprt-action-list, rprt-action-row (.priority), rprt-spotlight,\n"
            f"    rprt-chart, rprt-insight, rprt-metric, rprt-recommendation,\n"
            f"    rprt-evidence-row.\n"
            f"  - SVG attrs allowed: viewBox, width, height, x/y/x1/y1/x2/y2,\n"
            f"    cx/cy/r/rx/ry, d, points, fill, stroke, stroke-width,\n"
            f"    stroke-linecap, transform, font-family, font-size, font-weight,\n"
            f"    text-anchor. NO style, NO event handlers, NO href.\n"
            f"  - Charts: prefer the directive form\n"
            f"    [[chart:bar:label1=value1,label2=value2|title=...]] which the\n"
            f"    renderer substitutes with proper SVG. Hand-rolled SVG is\n"
            f"    allowed but the directive form is sturdier.\n"
            f"  - Surface SPECIFIC numbers, slugs, and proper nouns from the\n"
            f"    data. Do NOT summarise abstractly.\n"
            f"  - If this section has no useful content for THIS session,\n"
            f"    output ONLY the literal text `SKIP` and nothing else.\n\n"
            f"=== SESSION DATA ===\n{payload}\n=== END DATA ===\n\n"
            f"Now emit the HTML for this section."
        )

        try:
            (cache_dir / f"sec-{section_id}-{sig}.prompt.txt").write_text(
                prompt, encoding="utf-8"
            )
        except OSError:
            pass

        cmd, stdin_input = _cli_synthesis_command(backend, prompt)
        try:
            result = subprocess.run(
                cmd, input=stdin_input,
                capture_output=True,
                timeout=int(os.environ.get("RENDER_TIMEOUT_SECONDS", "90")),
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(
                f"  WARNING: multi-section[{section_id}] {backend} unavailable "
                f"({type(e).__name__}); skipping section.",
                file=sys.stderr,
            )
            continue
        if result.returncode != 0:
            print(
                f"  WARNING: multi-section[{section_id}] returned rc="
                f"{result.returncode}; skipping section.",
                file=sys.stderr,
            )
            continue

        text = result.stdout.decode("utf-8", errors="replace").strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        if text.upper() == "SKIP" or not text:
            try:
                cache_path.write_text("SKIP", encoding="utf-8")
            except OSError:
                pass
            print(
                f"  ✓ multi-section[{section_id}] SKIP (agent declined)",
                file=sys.stderr,
            )
            continue

        # Substitute chart directives BEFORE sanitization so the resulting
        # SVG has its tags in the allowlist.
        text_with_charts = _substitute_chart_directives(text)
        sanitized = _sanitize_agent_html(text_with_charts)
        if not sanitized or len(sanitized) < 60:
            print(
                f"  WARNING: multi-section[{section_id}] too short after "
                f"sanitize ({len(sanitized)} chars); skipping.",
                file=sys.stderr,
            )
            continue

        try:
            cache_path.write_text(sanitized, encoding="utf-8")
        except OSError:
            pass
        print(
            f"  ✓ multi-section[{section_id}] produced {len(sanitized)} chars",
            file=sys.stderr,
        )
        out.append((section_id, sanitized))

    return out


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

    # P1 #10 follow-up — short-circuit when a Stage-5 mirror is already
    # present. Without this, render() would overwrite the canonical
    # Stage-5 deliverable with its own minimal-compose output, AND leave
    # the .stage5_mirror marker behind so the next compose call would
    # falsely claim "Stage-5 deliverable here" while pointing at our
    # autoresearch composition (the original P1 #10 bug, just shifted
    # by one rerun — caught by 2026-05-08 re-review C1).
    stage5_marker = session_dir / ".stage5_mirror"
    stage5_html = session_dir / "report.html"
    stage5_pdf = session_dir / "report.pdf"
    if (stage5_marker.exists() and stage5_html.is_file()
            and not stage5_html.is_symlink()):
        print(
            f"  render: Stage-5 mirror present at {session_dir} — skipping "
            f"autoresearch overwrite. Use `freddy audit` to refresh the canonical "
            f"deliverable.",
            file=sys.stderr,
        )
        return {
            "html": str(stage5_html),
            "pdf": str(stage5_pdf) if stage5_pdf.exists() else None,
            "png": None,
            "html_bytes": stage5_html.stat().st_size,
            "stage5_mirror": True,
        }

    # Extract reasoning beats (Stage 1)
    print(f"  Extracting reasoning trail from {session_dir}/logs/", file=sys.stderr)
    try:
        extract = extract_session(session_dir)
    except Exception as e:
        print(f"  WARNING: extract_session failed: {e}", file=sys.stderr)
        extract = {"iterations": [], "totals": {"reasoning_beats": 0, "tool_calls": 0, "tokens": 0}, "iteration_count": 0}

    # Persist the structured extract alongside the raw .log.err transcripts
    # so downstream consumers (data-transparency rubric judge, evolution
    # loop, ad-hoc analysis) get a stable JSON instead of re-running the
    # heuristic regex parser. Best-effort: failure here doesn't block the
    # render — the in-memory extract still drives this report.
    try:
        (session_dir / "reasoning.json").write_text(
            json.dumps(extract, indent=2), encoding="utf-8"
        )
    except OSError as e:
        print(f"  WARNING: could not persist reasoning.json: {e}", file=sys.stderr)

    # Compose sections
    print(f"  Composing {domain} report for {client}", file=sys.stderr)
    sections = composer(session_dir, client, extract)

    # B2: Stage-2 agent-authored inner HTML — full payload (extract + findings
    # + lane-specific dir excerpts), sanitized + cached. Falls back silently
    # when the CLI is unreachable or produces unsafe output.
    findings_md = safe_read(session_dir / "findings.md", 6000) or ""

    # Multi-section dynamic synthesis (preferred). Each call writes a custom
    # HTML+SVG block per concern; SKIP allowed when a section has no signal.
    # Insert each section as its own (id, html) pair so the renderer's
    # outer scaffolding wraps them with consistent margins.
    multi_sections = agent_compose_multi_section(
        domain, client, session_dir, extract, findings_md,
    )
    if multi_sections:
        backend_label = os.environ.get("RENDER_BACKEND", "codex")
        # Insert in reverse so they end up in defined order at indices 1..N
        for offset, (sec_id, html_str) in enumerate(multi_sections):
            sections.insert(1 + offset, (
                f"synthesis_{sec_id}",
                f'<div class="rprt-meta-pattern">'
                f'<div class="label">↳ {h(sec_id.replace("_", " "))} · '
                f'{h(backend_label)} CLI · {domain}</div>'
                f'{html_str}'
                f'</div>'
            ))
    else:
        # Fallback: legacy single-section path (one call instead of N).
        # Keeps the existing behaviour when AUTORESEARCH_RENDER_MULTI_SECTION=0
        # or the multi-section orchestrator returned no usable output.
        agent_html = agent_compose_section(
            domain, client, session_dir, extract, findings_md,
        )
        if agent_html:
            sections.insert(1, ("synthesis", (
                f'<div class="rprt-meta-pattern">'
                f'<div class="label">↳ Stage-2 agent-authored · '
                f'{os.environ.get("RENDER_BACKEND", "codex")} CLI · {domain}</div>'
                f'{agent_html}'
                f'</div>'
            )))

    # Generate the session bundle BEFORE composing the tree section so the
    # section can size-stamp the .tar.gz. The bundle excludes the rendered
    # artefacts themselves (report.html / .pdf / .png / bundle.tar.gz) so
    # subsequent re-renders don't recurse on their own outputs.
    try:
        bundle_path = make_session_bundle(session_dir)
    except OSError as e:
        print(f"  WARNING: bundle creation failed: {e}", file=sys.stderr)
        bundle_path = None

    # Append the file tree + bundle download as the FINAL section so prior
    # narrative + reasoning + transcripts read first, and the catch-all
    # "everything visible + downloadable" lives at the bottom.
    sections.append((
        "session_bundle",
        build_session_bundle_section(session_dir, bundle_path),
    ))

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
