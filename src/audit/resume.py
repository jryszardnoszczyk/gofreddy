"""Resume planning — what can re-attach to a claude session vs must restart.

``viable_resume_id`` is a port of ``harness/run.py:197`` adapted for the
audit's ``audit_dir`` (instead of harness's ``wt_path``). The viability
rule is identical: a session is resume-eligible only if ``status="running"``
AND the local conversation JSONL exists at
``~/.claude/projects/<encoded-cwd>/<session_id>.jsonl``. Missing JSONL =
claude silent-hung before its first token; ``--resume`` would error out,
so the caller must spawn a fresh session.

``build_resume_plan`` is the entry point ``freddy audit resume <id>``
calls. It validates that ``audit_dir`` still exists (a deleted directory
makes Unit 3's ``cwd.is_dir()`` precondition fire downstream with an
opaque AssertionError; raising ``ViableResumeFailed`` here gives the
operator a clear typed error). Then it partitions the session ledger
into ``can_resume`` (running + viable JSONL), ``must_restart`` (running
but no JSONL, or status=failed), and surfaces the audit's
``completed_lenses`` as ``stage_2_skip`` so the lens fan-out doesn't
re-run already-completed lenses.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harness.sessions import SessionRecord, SessionsFile, claude_session_jsonl

from src.audit.exceptions import ViableResumeFailed
from src.audit.state import AuditState


@dataclass(frozen=True)
class ResumePlan:
    """Decision matrix for resuming an audit.

    ``must_restart`` and ``can_resume`` are agent_keys (e.g. ``"stage_1b"``,
    ``"stage_2_lens_L-A-01"``); ``stage_2_skip`` is lens IDs the runner
    must NOT re-fan-out (already in ``completed_lenses``)."""

    must_restart: tuple[str, ...]
    can_resume: dict[str, str]
    stage_2_skip: tuple[str, ...]


def viable_resume_id(record: SessionRecord | None, audit_dir: Path) -> str | None:
    """Return the session_id if claude can actually resume it, else None.

    Port of ``harness/run.py:197`` — viability rule unchanged. Audit
    directory replaces harness's worktree path as the cwd that claude
    encoded into its projects/ subdir."""
    if not record or record.status != "running":
        return None
    jsonl = claude_session_jsonl(audit_dir, record.session_id)
    if not jsonl.is_file():
        return None
    return record.session_id


def build_resume_plan(
    audit_dir: Path, sessions: SessionsFile, state: AuditState
) -> ResumePlan:
    """Partition the session ledger into resume vs restart.

    Raises ``ViableResumeFailed`` if ``audit_dir`` is missing (the operator
    deleted it, or pointed ``freddy audit resume`` at a non-existent id) —
    this is the right place to fail loud, before downstream code asserts
    on the directory."""
    if not audit_dir.is_dir():
        raise ViableResumeFailed(
            f"audit_dir missing: {audit_dir}; cannot resume audit {state.audit_id}"
        )

    must_restart: list[str] = []
    can_resume: dict[str, str] = {}
    for agent_key, record in sessions.all().items():
        if record.status == "complete":
            continue  # nothing to do
        if record.status == "failed":
            must_restart.append(agent_key)
            continue
        # status == "running" — check JSONL viability
        sid = viable_resume_id(record, audit_dir)
        if sid is not None:
            can_resume[agent_key] = sid
        else:
            must_restart.append(agent_key)

    return ResumePlan(
        must_restart=tuple(must_restart),
        can_resume=can_resume,
        stage_2_skip=state.completed_lenses,
    )
