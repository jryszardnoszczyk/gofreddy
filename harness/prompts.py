"""Prompt rendering for the QA eval-fix harness.

Assembles evaluator (cycle 1 + cycle 2+), fixer, scope, grade-delta,
and attempt-tracker prompts from templates in ``harness/prompts/``.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from harness.config import Config, normalize_id
from harness.scorecard import (
    Finding,
    Scorecard,
    parse_track_caps,
    resolve_scope_caps,
)

# Root of the prompts directory (co-located with this file).
_PROMPTS_DIR = Path(__file__).parent / "prompts"

# Grade ordering for delta computation.
_GRADE_RANK = {"BLOCKED": 0, "FAIL": 1, "PARTIAL": 2, "PASS": 3}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_eval_prompt(
    track: str,
    cycle: int,
    scorecard_path: str,
    config: Config,
    run_dir: Path,
) -> Path:
    """Assemble the evaluator prompt and write it to a tempfile.

    Returns the path to the written file.

    Cycle 1: scope banner + track header + base prompt + track prompt
             + scope block + dry-run override.
    Cycle 2+: scope banner + re-eval header + previous fixes + previous
              scorecard + instructions + scope block.
    """
    scope_banner = render_scope_override_banner(track, config)
    scope_block = render_scope_block(config)

    dry_run_override = ""
    if config.dry_run and track == "a":
        dry_run_override = (
            "DRY RUN OVERRIDE: Ignore the normal Track A assignment. "
            "Test ONLY capability A-1 / A1 "
            '("Search for TikTok cooking videos"). '
            "Do not test any other capability, flow, or page."
        )

    lines: list[str] = []

    if cycle == 1:
        # -- Primacy banner (top of file, so no model can claim it missed it)
        if scope_banner:
            lines.append(scope_banner)

        # -- Track header
        lines.append(f"You are Evaluator Track {track.upper()}. Cycle: {cycle}.")
        lines.append(f"Your scorecard path: {scorecard_path}")
        lines.append(f"Frontend URL: {config.frontend_url}")
        lines.append(
            f"Auth: Navigate to {config.frontend_url}/dashboard?__e2e_auth=1"
        )
        lines.append(
            f"Playwright session name: track-{track} — pass `-s=track-{track}` "
            f"to EVERY playwright-cli command (open, goto, snapshot, click, type, "
            f"eval, console, network, close). All tracks run in parallel; without "
            f"this flag your browser session will collide with other tracks and "
            f"you will see foreign prompts in your conversations."
        )
        if dry_run_override:
            lines.append(dry_run_override)
        lines.append("")

        # -- Base prompt
        base_content = (_PROMPTS_DIR / "evaluator-base.md").read_text(encoding="utf-8")
        lines.append(base_content)
        lines.append("")

        # -- Track-specific prompt
        lines.append("--- YOUR TRACK ASSIGNMENT ---")
        lines.append("")
        track_content = (
            _PROMPTS_DIR / f"evaluator-track-{track}.md"
        ).read_text(encoding="utf-8")
        lines.append(track_content)

        # -- Scope block
        if scope_block:
            lines.append(scope_block)

        # -- Dry-run override (repeated at end for recency bias)
        if dry_run_override:
            lines.append("")
            lines.append("--- DRY RUN OVERRIDE ---")
            lines.append("")
            lines.append(dry_run_override)
    else:
        # -- Cycle 2+ re-evaluation prompt
        prev_scorecard_path = run_dir / f"scorecard-{cycle - 1}-track-{track}.md"
        prev_fixes_path = run_dir / f"fixes-{cycle - 1}.md"

        if scope_banner:
            lines.append(scope_banner)

        lines.append(f"# Cycle {cycle} \u2014 Re-evaluation")
        lines.append("")
        lines.append(f"You are continuing as Evaluator Track {track.upper()}.")
        lines.append(f"Your scorecard path: {scorecard_path}")
        lines.append(
            f"Playwright session name: track-{track} — pass `-s=track-{track}` "
            f"to EVERY playwright-cli command. Tracks A/B/C run in parallel; "
            f"without this flag your browser session will collide with other tracks."
        )
        lines.append("")
        lines.append("## What changed since last cycle")
        lines.append("")

        if prev_fixes_path.exists():
            lines.append("The fixer applied changes. Their report:")
            lines.append("```")
            lines.append(prev_fixes_path.read_text(encoding="utf-8"))
            lines.append("```")
        else:
            lines.append(f"No fixer report found for cycle {cycle - 1}.")

        lines.append("")
        lines.append("## Your previous scorecard")
        lines.append("")
        if prev_scorecard_path.exists():
            lines.append("```")
            lines.append(prev_scorecard_path.read_text(encoding="utf-8"))
            lines.append("```")

        lines.append("")
        lines.append("## Instructions")
        lines.append("")
        lines.append(
            "Re-test ALL capabilities in your track. Focus especially on:"
        )
        lines.append(
            "1. Capabilities that were FAIL or PARTIAL last cycle "
            "\u2014 verify if the fixer resolved them"
        )
        lines.append(
            "2. Capabilities that were PASS last cycle "
            "\u2014 verify no regressions from the fixer's changes"
        )
        lines.append(
            "3. Capabilities that were BLOCKED \u2014 retry them "
            "(the blocker may be resolved)"
        )
        lines.append("")
        lines.append(f"Write your updated scorecard to: {scorecard_path}")
        lines.append("Use the same YAML frontmatter format as before.")

        if scope_block:
            lines.append(scope_block)

        if dry_run_override:
            lines.append("")
            lines.append(dry_run_override)

    # Write to tempfile
    tmpfile = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        dir=str(run_dir),
        delete=False,
        encoding="utf-8",
    )
    tmpfile.write("\n".join(lines))
    tmpfile.close()
    return Path(tmpfile.name)


def render_fixer_prompt(
    cycle: int,
    merged_path: str,
    fixes_path: str,
    config: Config,
    run_dir: Path,
    full_merged_path: str | None = None,
    scope_ids: str = "all",
) -> Path:
    """Assemble the fixer prompt and write it to a tempfile.

    Returns the path to the written file.
    """
    prev_fixes_path_str = ""
    if cycle > 1:
        candidate = run_dir / f"fixes-{cycle - 1}.md"
        if candidate.exists():
            prev_fixes_path_str = str(candidate)

    tracker_block = ""
    grade_delta_block = ""
    if cycle > 1:
        tracker_block = render_attempt_tracker_block(
            cycle, run_dir, config.max_fix_attempts
        )
        prev_merged = run_dir / f"scorecard-{cycle - 1}-merged.md"
        curr_merged_for_delta = Path(full_merged_path or merged_path)
        if prev_merged.exists():
            grade_delta_block = render_grade_delta_block(
                prev_merged, curr_merged_for_delta
            )

    # Scope header for scoped fixer
    scope_header = ""
    if scope_ids != "all" and scope_ids:
        scope_header = (
            "\u26a0\ufe0f  SCOPED FIXER \u2014 READ THIS FIRST \u26a0\ufe0f\n\n"
            f"Scoped findings: [{scope_ids}]\n"
            "Fix ONLY the IDs above.\n\n"
            "==="
        )

    lines: list[str] = []

    if scope_header:
        lines.append(scope_header)

    lines.append(f"Cycle: {cycle}")
    lines.append(f"Merged scorecard: {merged_path}")

    if full_merged_path and full_merged_path != merged_path:
        lines.append(
            f"Full merged scorecard (READ ONLY): {full_merged_path}"
        )

    lines.append(f"Fixes report path: {fixes_path}")

    if prev_fixes_path_str:
        lines.append(f"Previous cycle fixes report: {prev_fixes_path_str}")
    else:
        first_cycle_note = " \u2014 first cycle" if cycle == 1 else ""
        lines.append(
            f"Previous cycle fixes report: (none{first_cycle_note})"
        )

    if grade_delta_block:
        lines.append("")
        lines.append(grade_delta_block)

    lines.append("")
    fixer_content = (_PROMPTS_DIR / "fixer.md").read_text(encoding="utf-8")
    lines.append(fixer_content)

    if tracker_block:
        lines.append("")
        lines.append(tracker_block)

    tmpfile = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        dir=str(run_dir),
        delete=False,
        encoding="utf-8",
    )
    tmpfile.write("\n".join(lines))
    tmpfile.close()
    return Path(tmpfile.name)


def render_verifier_prompt(
    cycle: int,
    domain_letter: str,
    focus_findings: list[Finding],
    report_path: str,
    run_dir: Path,
    config: Config,
    abs_test_matrix_path: Path,
) -> Path:
    """Assemble the verifier prompt and write it to a tempfile.

    *abs_test_matrix_path* must be an absolute path to the pristine
    (main-checkout) test-matrix.md so the verifier cannot accidentally
    read a worktree copy tampered with by the fixer.

    Returns the path to the written file.
    """
    letter = (domain_letter or "").lower()

    lines: list[str] = [
        f"Cycle: {cycle}",
        f"Domain: {letter}",
        f"Verifier session name: verifier-{letter} — "
        f"pass `-s=verifier-{letter}` to EVERY playwright-cli command.",
        f"Frontend URL: {config.frontend_url}",
        f"Auth: {config.frontend_url}/dashboard?__e2e_auth=1",
        f"Verifier report path: {report_path}",
        f"TEST_MATRIX_PATH: {abs_test_matrix_path}",
        "",
    ]

    if focus_findings:
        lines.append("Scoped findings (verify ONLY these IDs):")
        for f in focus_findings:
            lines.append(f"  - {f.id}: {f.capability} ({f.grade})")
    else:
        lines.append(
            "Scoped findings: (none) — no active findings to verify. "
            "Write an empty-findings verdict file and exit cleanly."
        )

    lines.append("")
    lines.append("===")
    lines.append("")
    lines.append(
        (_PROMPTS_DIR / "verifier.md").read_text(encoding="utf-8")
    )

    tmpfile = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        dir=str(run_dir),
        delete=False,
        encoding="utf-8",
    )
    tmpfile.write("\n".join(lines))
    tmpfile.close()
    return Path(tmpfile.name)


# ---------------------------------------------------------------------------
# Scope rendering
# ---------------------------------------------------------------------------


def render_scope_block(config: Config) -> str:
    """Render the CAPABILITIES IN SCOPE block for evaluator prompts.

    Returns empty string when there's no scope restriction (phase=all,
    no skip, no only).
    """
    if config.phase == "all" and not config.skip and not config.only:
        return ""

    matrix_path = Path(__file__).parent / "test-matrix.md"
    caps = resolve_scope_caps(config.only, config.phase, matrix_path)

    parts: list[str] = ["\n--- CAPABILITIES IN SCOPE ---\n"]

    if config.only:
        caps_str = ",".join(config.only) if config.only else "all"
        parts.append(
            f"HARNESS_ONLY={caps_str} \u2014 test ONLY: "
            f"{','.join(caps) if caps else 'all'}\n"
            "Every other capability must be omitted."
        )
    elif config.phase != "all" and caps is not None and caps:
        parts.append(
            f"PHASE={config.phase} \u2014 test ONLY: {','.join(caps)}\n"
            "Every other capability must be omitted."
        )

    if config.skip:
        parts.append(
            f"\nHARNESS_SKIP={','.join(config.skip)} "
            "\u2014 do NOT test these IDs (mark SKIPPED)."
        )

    parts.append("\n")
    return "\n".join(parts)


def render_scope_override_banner(track: str, config: Config) -> str:
    """Render the mandatory scope override banner (primacy position).

    Returns empty string when there's no scope restriction.
    """
    if config.phase == "all" and not config.skip and not config.only:
        return ""

    matrix_path = Path(__file__).parent / "test-matrix.md"
    base_caps = resolve_scope_caps(config.only, config.phase, matrix_path)
    track_upper = track.upper() if track else ""

    scope_source = (
        f"HARNESS_ONLY={','.join(config.only)}"
        if config.only
        else f"PHASE={config.phase}"
    )

    parts: list[str] = [
        "\u26a0\ufe0f  MANDATORY SCOPE OVERRIDE \u2014 READ THIS FIRST \u26a0\ufe0f\n"
    ]

    if base_caps is not None and base_caps:
        track_caps: list[str] = []
        if track:
            assigned = parse_track_caps(track, matrix_path)
            if assigned:
                # Intersect base_caps with assigned track caps
                base_set = set(base_caps)
                track_caps = sorted(
                    [c for c in assigned if c in base_set],
                    key=lambda x: base_caps.index(x) if x in base_caps else 999,
                )

        if track_upper and track_caps:
            parts.append(
                f"Scoped to {scope_source}. YOU ARE TRACK {track_upper}.\n"
            )
            parts.append(
                f"Your ENTIRE scope is exactly: {','.join(track_caps)}"
            )
            parts.append(
                f"({len(track_caps)} IDs \u2014 test each once and STOP. "
                "Omit everything else.)\n"
            )
        elif track_upper:
            parts.append(
                f"Scoped to {scope_source}. TRACK {track_upper} "
                "has ZERO in-scope caps.\n"
                "Produce an empty scorecard and exit immediately.\n"
            )
        else:
            parts.append(
                f"Scoped to {scope_source}. Test ONLY: {','.join(base_caps)}\n"
            )

    if config.skip:
        parts.append(
            f"HARNESS_SKIP={','.join(config.skip)} "
            "\u2014 do NOT test these IDs.\n"
        )

    parts.append("===\n\n\n")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Grade delta
# ---------------------------------------------------------------------------


def render_grade_delta_block(
    prev_merged: Path,
    curr_merged: Path,
) -> str:
    """Render a markdown table comparing id:grade pairs between cycles.

    Returns empty string if either file is missing or curr has no grades.
    """
    if not prev_merged.exists() or not curr_merged.exists():
        return ""

    prev_sc = Scorecard.from_yaml(prev_merged)
    curr_sc = Scorecard.from_yaml(curr_merged)

    prev_grades = prev_sc.extract_grades()
    curr_grades = curr_sc.extract_grades()

    if not curr_grades:
        return ""

    lines: list[str] = [
        "## Grade Delta (previous \u2192 current cycle)\n",
        "| ID | Previous | Current | Delta |",
        "|---|---|---|---|",
    ]

    for cid, cgrade in curr_grades.items():
        pgrade = prev_grades.get(cid)
        if pgrade is None:
            delta = "NEW"
        else:
            prev_rank = _GRADE_RANK.get(pgrade.upper(), 0)
            curr_rank = _GRADE_RANK.get(cgrade.upper(), 0)
            if curr_rank > prev_rank:
                delta = "IMPROVED"
            elif curr_rank < prev_rank:
                delta = "REGRESSED"
            else:
                delta = "unchanged"
        lines.append(
            f"| {cid} | {pgrade or '\u2014'} | {cgrade} | {delta} |"
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Attempt tracker
# ---------------------------------------------------------------------------


def _count_finding_attempts_with_cycles(
    run_dir: Path, current_cycle: int
) -> dict[str, tuple[int, list[int]]]:
    """Count attempts AND collect cycle numbers for each finding.

    Returns ``{normalized_id: (count, [cycle_numbers])}``.
    Extended version of ``scorecard.count_finding_attempts`` that also
    tracks which cycles each finding was attempted in (needed for the
    attempt tracker prompt block).
    """
    counts: dict[str, int] = {}
    cycles: dict[str, list[int]] = {}

    for cycle_i in range(1, current_cycle):
        fixes_path = run_dir / f"fixes-{cycle_i}.md"
        if not fixes_path.exists():
            continue
        text = fixes_path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            data = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            continue
        addressed = data.get("findings_addressed", [])
        if isinstance(addressed, str):
            addressed = [x.strip() for x in addressed.split(",") if x.strip()]
        if not isinstance(addressed, list):
            continue
        for raw_id in addressed:
            nid = normalize_id(str(raw_id))
            counts[nid] = counts.get(nid, 0) + 1
            cycles.setdefault(nid, []).append(cycle_i)

    return {
        fid: (count, cycles.get(fid, []))
        for fid, count in counts.items()
    }


def render_attempt_tracker_block(
    cycle: int,
    run_dir: Path,
    max_attempts: int = 2,
) -> str:
    """Render the finding attempt tracker for cycle 2+ fixer prompts.

    Returns empty string if cycle <= 1 or no previous fix attempts exist.
    """
    if cycle <= 1:
        return ""

    attempts = _count_finding_attempts_with_cycles(run_dir, cycle)
    if not attempts:
        return ""

    lines: list[str] = [
        "\n## Finding attempt tracker\n",
        f"MAX_FIX_ATTEMPTS = {max_attempts}. The harness has computed the "
        "cycle history for every finding ID you previously attempted:\n",
    ]

    for fid in sorted(attempts.keys()):
        count, cycle_list = attempts[fid]
        cycles_str = ",".join(str(c) for c in cycle_list)
        next_attempt = count + 1

        if count >= max_attempts:
            lines.append(
                f"- `{fid}`: attempted in cycles [{cycles_str}] "
                f"\u2014 **ALREADY ESCALATED**. Do NOT attempt to fix. "
                "Copy this ID into the `findings_escalated:` field of your "
                "fixes report and leave it alone. Convergence ignores "
                "escalated findings."
            )
        else:
            entry = (
                f"- `{fid}`: attempted in cycles [{cycles_str}] "
                f"\u2014 this is attempt {next_attempt} of {max_attempts}"
            )
            if next_attempt >= max_attempts:
                entry += (
                    ". If the finding is still present after this attempt, "
                    "it MUST escalate next cycle (the harness will "
                    "auto-escalate it)"
                )
            entry += "."
            lines.append(entry)

    lines.append("")
    return "\n".join(lines)
