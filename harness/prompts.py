"""Prompt template substitution. Three public functions render the three agent prompts.

Reads markdown under harness/prompts/, applies {placeholder} substitution with str.replace,
writes the rendered prompt to a tempfile under run_dir, returns that path.
SEED + inventory are appended to evaluator prompts only.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from harness.findings import Finding

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _render(template_name: str, substitutions: dict[str, str], run_dir: Path) -> Path:
    template = (_PROMPTS_DIR / template_name).read_text(encoding="utf-8")
    for key, value in substitutions.items():
        template = template.replace("{" + key + "}", value)
    run_dir.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix=template_name.replace(".md", "-"), suffix=".md", dir=run_dir)
    Path(path).write_text(template, encoding="utf-8")
    import os
    os.close(fd)
    return Path(path)


def render_evaluator(track: str, cycle: int, run_dir: Path, wt_path: Path) -> Path:
    """Render the evaluator prompt for a given track/cycle. Appends SEED + inventory."""
    seed = (wt_path / "harness" / "SEED.md").read_text(encoding="utf-8") if (wt_path / "harness" / "SEED.md").exists() else ""
    inventory_path = run_dir / "inventory.md"
    inventory = inventory_path.read_text(encoding="utf-8") if inventory_path.exists() else ""
    track_tail = (_PROMPTS_DIR / f"evaluator-track-{track}.md").read_text(encoding="utf-8")
    sentinel_path = run_dir / f"track-{track}" / f"cycle-{cycle}" / "sentinel.txt"
    findings_path = run_dir / f"track-{track}" / f"cycle-{cycle}" / "findings.md"
    substitutions = {
        "track": track,
        "cycle": str(cycle),
        "worktree": str(wt_path),
        "findings_output": str(findings_path),
        "sentinel_path": str(sentinel_path),
        "seed": seed,
        "inventory": inventory,
        "track_specific": track_tail,
    }
    return _render("evaluator-base.md", substitutions, run_dir)


def render_fixer(finding: Finding, run_dir: Path) -> Path:
    substitutions = {
        "track": finding.track,
        "finding_id": finding.id,
        "category": finding.category,
        "summary": finding.summary,
        "evidence": finding.evidence,
        "reproduction": finding.reproduction,
        "files": "\n".join(f"- {f}" for f in finding.files),
    }
    return _render("fixer.md", substitutions, run_dir)


def render_verifier(finding: Finding, run_dir: Path) -> Path:
    verdict_path = run_dir / f"verdict-{finding.id}.yaml"
    substitutions = {
        "track": finding.track,
        "finding_id": finding.id,
        "category": finding.category,
        "summary": finding.summary,
        "reproduction": finding.reproduction,
        "files": "\n".join(f"- {f}" for f in finding.files),
        "verdict_path": str(verdict_path),
    }
    return _render("verifier.md", substitutions, run_dir)
