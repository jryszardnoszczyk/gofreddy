"""Compose review.md (everything not PR-worthy) and pr-body.md (verified fixes)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from harness.findings import DEFECT_CATEGORIES, Finding

_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:bearer\s+)?eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
    re.compile(r"(?i)\b[A-Za-z0-9+/=]{40,}\b"),
    re.compile(r"(?i)(api[_-]?key|secret|token)[=:\s\"]+[A-Za-z0-9_\-]{16,}"),
)


@dataclass
class CommitRecord:
    sha: str
    finding_id: str
    summary: str
    track: str
    files: tuple[str, ...]
    reproduction: str = ""
    adjacent_checked: tuple[str, ...] = ()


def _scrub(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    return text


def compose(run_dir: Path, commits: list[CommitRecord], all_findings: list[Finding], tip_smoke_ok: bool) -> str:
    parts = [f"# harness review — {run_dir.name}\n"]
    if not tip_smoke_ok:
        parts.append("## ⚠️ Tip-smoke FAILED\n\nThe staging branch tip did not pass smoke checks. Review before merging.\n")

    parts.append(_section("Verified & committed", _format_commits(commits)))
    parts.append(_section(
        "Doc drift (not fixed; docs/reality diverge)",
        _format_findings([f for f in all_findings if f.category == "doc-drift"]),
    ))
    parts.append(_section(
        "Low confidence (not fixed; human judgement)",
        _format_findings([f for f in all_findings if f.confidence == "low" and f.category in DEFECT_CATEGORIES]),
    ))
    parts.append(_section(
        "Rolled back (scope / leak / verifier failed)",
        _format_rollbacks(run_dir),
    ))
    return _scrub("\n\n".join(p for p in parts if p).strip() + "\n")


def pr_body(run_dir: Path, commits: list[CommitRecord], tip_smoke_ok: bool) -> str:
    parts = [f"# harness: run {run_dir.name} — {len(commits)} verified fixes\n"]
    if not tip_smoke_ok:
        parts.append("> ⚠️ Tip-smoke check FAILED. Review before merging.\n")
    by_track: dict[str, list[CommitRecord]] = {"a": [], "b": [], "c": []}
    for c in commits:
        by_track.setdefault(c.track, []).append(c)
    for track in ("a", "b", "c"):
        items = by_track.get(track, [])
        if not items:
            continue
        parts.append(f"## Track {track.upper()} ({len(items)} fixes)\n")
        for c in items:
            files = "\n".join(f"  - `{f}`" for f in c.files) or "  - _no files recorded_"
            adj = ", ".join(c.adjacent_checked) or "_none recorded_"
            parts.append(
                f"- **{c.finding_id}** `{c.sha[:8]}` — {c.summary}\n"
                f"  - files touched:\n{files}\n"
                f"  - adjacent checked: {adj}"
            )
    return _scrub("\n".join(parts).strip() + "\n")


def _section(title: str, body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    return f"## {title}\n\n{body}"


def _format_commits(commits: list[CommitRecord]) -> str:
    if not commits:
        return "_none_"
    return "\n".join(f"- `{c.sha[:8]}` **{c.finding_id}** ({c.track}): {c.summary}" for c in commits)


def _format_findings(findings: list[Finding]) -> str:
    if not findings:
        return "_none_"
    return "\n".join(
        f"- **{f.id}** ({f.track} / {f.category} / {f.confidence}): {f.summary}"
        for f in findings
    )


def _format_rollbacks(run_dir: Path) -> str:
    patches_dir = run_dir / "fix-diffs"
    if not patches_dir.is_dir():
        return "_none_"
    lines = []
    for patch in sorted(patches_dir.glob("F-*.patch")):
        lines.append(f"- `{patch.relative_to(run_dir)}`")
    return "\n".join(lines) if lines else "_none_"
