from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from workflows import get_workflow_spec


def load_json_output(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def append_results_entry(session_dir: Path, entry: dict) -> None:
    results_file = session_dir / "results.jsonl"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with results_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def downgrade_complete_status(session_dir: Path, note: str) -> None:
    session_md = session_dir / "session.md"
    if not session_md.exists():
        return
    text = session_md.read_text(encoding="utf-8", errors="replace")
    if "## Status: COMPLETE" in text:
        text = text.replace("## Status: COMPLETE", "## Status: RUNNING", 1)
    marker = "## Completion Guard"
    if marker in text:
        head, _, _tail = text.partition(marker)
        text = head.rstrip() + "\n\n" + marker + "\n" + note.strip() + "\n"
    else:
        text = text.rstrip() + "\n\n" + marker + "\n" + note.strip() + "\n"
    session_md.write_text(text, encoding="utf-8")


def run_session_evaluator(
    domain: str,
    artifact: Path,
    session_dir: Path,
    output_path: Path,
    run_script: Callable[..., None],
    *,
    mode: str = "full",
) -> dict | None:
    if not artifact.exists():
        return None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "--domain",
        domain,
        "--artifact",
        str(artifact),
        "--session-dir",
        str(session_dir),
    ]
    if mode != "full":
        args.extend(["--mode", mode])
    run_script("evaluate_session.py", *args, stdout_file=output_path)
    return load_json_output(output_path)


def snapshot_session_evaluations(
    domain: str,
    session_dir: Path,
    run_script: Callable[..., None],
) -> dict[str, object]:
    spec = get_workflow_spec(domain)
    return spec.snapshot_evaluations(
        session_dir,
        lambda eval_domain, artifact, session_root, output_path, mode="full": run_session_evaluator(
            eval_domain,
            artifact,
            session_root,
            output_path,
            run_script,
            mode=mode,
        ),
    )


def enforce_completion_guard(
    domain: str,
    session_dir: Path,
    eval_summary: dict[str, object],
    *,
    is_complete: Callable[[Path], bool],
) -> None:
    if not is_complete(session_dir):
        return

    note, evidence = get_workflow_spec(domain).completion_guard(eval_summary)

    if note:
        downgrade_complete_status(session_dir, note)
        append_results_entry(
            session_dir,
            {
                "type": "session_evaluator_guard",
                "status": "rework_required",
                "artifact": evidence,
                "reason": note,
            },
        )


def post_session_hooks(
    domain: str,
    session_dir: Path,
    client: str,
    *,
    run_script: Callable[..., None],
    is_complete: Callable[[Path], bool],
) -> None:
    get_workflow_spec(domain).pre_summary_hooks(session_dir, client, run_script)

    eval_summary = snapshot_session_evaluations(domain, session_dir, run_script)
    enforce_completion_guard(domain, session_dir, eval_summary, is_complete=is_complete)

    run_script("summarize_session.py", str(session_dir), domain, client)
    # Anchor promote_findings at the canonical variant dir. Without --variant-dir,
    # promote_findings.ROOT resolves to whichever tree launched the script,
    # which is current_runtime/ (gitignored) when _run_script runs from there.
    # session_dir is archive/<variant>/sessions/<domain>/<client>, so parents[2]
    # is the variant root.
    try:
        variant_dir = str(session_dir.resolve().parents[2])
        run_script("promote_findings.py", domain, "--variant-dir", variant_dir)
    except IndexError:
        run_script("promote_findings.py", domain)
    run_script("strip_repeated_diffs.py", str(session_dir))
