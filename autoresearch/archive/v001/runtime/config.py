from __future__ import annotations

import os
import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from workflows import WORKFLOW_SPECS, get_workflow_spec

# Phase 5 (Unit 11 sub-task 2): DOMAIN_CONFIG removed — it duplicated
# WORKFLOW_SPECS. Callers now resolve via `get_workflow_spec(domain).config`
# directly. Pre-flight check confirmed every DOMAIN_CONFIG key was a strict
# subset of `WorkflowConfig` fields.

SESSION_MODEL = "sonnet"
SESSION_MAX_ITER = 50
FRESH_MAX_TURNS = 100
MAX_PARALLEL = 4
MONITORING_PLACEHOLDER_CONTEXTS = {
    "b0000000-0000-0000-0000-000000000001",
    "b0000000-0000-0000-0000-000000000002",
    "b0000000-0000-0000-0000-000000000003",
}


def domain_env_prefix(domain: str) -> str:
    return domain.upper()


def resolve_domain_target(
    domain: str,
    client_override: str | None = None,
    context_override: str | None = None,
    *,
    allow_placeholder: bool = False,
) -> tuple[str, str, str | None]:
    cfg = get_workflow_spec(domain).config
    prefix = domain_env_prefix(domain)
    client = (
        client_override
        or os.environ.get(f"AUTORESEARCH_{prefix}_CLIENT", "").strip()
        or cfg.default_client
    )
    context = (
        context_override
        or os.environ.get(f"AUTORESEARCH_{prefix}_CONTEXT", "").strip()
        or cfg.default_context
    )

    warning = None
    if domain == "monitoring":
        if not client or not context:
            raise ValueError(
                "Monitoring target is not configured. "
                "Set AUTORESEARCH_MONITORING_CLIENT and AUTORESEARCH_MONITORING_CONTEXT "
                "or pass an explicit client and monitor ID."
            )
        if context in MONITORING_PLACEHOLDER_CONTEXTS:
            warning = (
                "Monitoring context is still a placeholder UUID. "
                "Set AUTORESEARCH_MONITORING_CONTEXT or pass an explicit monitor ID."
            )
            if not allow_placeholder:
                raise ValueError(warning)

    return client, context, warning


def render_template(text: str, client: str, context: str, _domain: str = "") -> str:
    text = text.replace("{client}", client)
    text = text.replace("{site}", context)
    text = text.replace("{storyboard_count}", os.environ.get("STORYBOARD_COUNT", "5"))
    text = text.replace("{week_start}", os.environ.get("WEEK_START", "TBD"))
    text = text.replace("{week_end}", os.environ.get("WEEK_END", "TBD"))
    return text


def is_complete(session_dir: Path) -> bool:
    session_md = session_dir / "session.md"
    return session_md.exists() and "## Status: COMPLETE" in session_md.read_text()


def is_blocked(session_dir: Path) -> bool:
    session_md = session_dir / "session.md"
    return session_md.exists() and "## Status: BLOCKED" in session_md.read_text()


def resolve_monitoring_week() -> tuple[str, str]:
    pinned_start = os.environ.get("AUTORESEARCH_WEEK_START", "").strip()
    pinned_end = os.environ.get("AUTORESEARCH_WEEK_END", "").strip()
    if pinned_start or pinned_end:
        if not pinned_start or not pinned_end:
            raise ValueError(
                "Monitoring benchmark week pins must define both "
                "AUTORESEARCH_WEEK_START and AUTORESEARCH_WEEK_END."
            )
        try:
            week_start = date.fromisoformat(pinned_start)
            week_end = date.fromisoformat(pinned_end)
        except ValueError as exc:
            raise ValueError(
                "AUTORESEARCH_WEEK_START and AUTORESEARCH_WEEK_END must use YYYY-MM-DD format."
            ) from exc
        if week_end < week_start:
            raise ValueError("AUTORESEARCH_WEEK_END must be on or after AUTORESEARCH_WEEK_START.")
        return week_start.isoformat(), week_end.isoformat()

    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    week_end = today - timedelta(days=days_since_sunday)
    week_start = week_end - timedelta(days=6)
    return week_start.isoformat(), week_end.isoformat()


def configure_domain_env(domain: str, client: str) -> None:
    os.environ["AUTORESEARCH_DOMAIN"] = domain
    os.environ["AUTORESEARCH_CLIENT"] = client
    get_workflow_spec(domain).configure_env(client)


def reset_interrupted_session(session_dir: Path) -> None:
    session_md = session_dir / "session.md"
    if not session_md.exists():
        return
    text = session_md.read_text()
    if "## Status: IN_PROGRESS" in text:
        session_md.write_text(text.replace("## Status: IN_PROGRESS", "## Status: RUNNING"))


def render_prompt(
    script_dir: Path,
    program_path: Path,
    client: str,
    context: str,
    domain: str,
    *,
    strategy: str,
    session_backend: Callable[[], str],
    session_model: Callable[[], str],
) -> str:
    text = program_path.read_text()
    text = render_template(text, client, context, domain)

    # Fresh override prepended at top — the most critical behavioral constraint
    # must be the first thing the agent reads.
    if strategy == "fresh":
        fresh_block = """\
## Fresh Session Override

OVERRIDE: You are running in fresh-session mode for this invocation only.

- Complete exactly ONE phase, persist state to files, then stop.
- Do NOT continue automatically into the next phase after phase completion.
- Your conversation state will not be preserved after this process exits.
- Files remain the only state that survives to the next invocation.

"""
        text = fresh_block + text

    findings_path = script_dir / f"{domain}-findings.md"
    if findings_path.exists():
        findings_content = findings_path.read_text()
        if len(findings_content) > 4000:
            findings_content = findings_content[:4000] + "\n\n(truncated — oldest findings retained)"
        text += f"\n## Global Findings (from prior sessions)\n{findings_content}"

    text += f"""

## Runtime Context

- Domain: {domain}
- Client: {client}
- Context: {context}
- Strategy: {strategy}
- Session backend: {session_backend()}
- Session model: {session_model()}
- Session directory: {script_dir / "sessions" / domain / client}
- The runner does NOT auto-run `scripts/evaluate_session.py` or create `eval_feedback.json` mid-session.
- `post_session_hooks()` only runs after the overall session process exits, where it persists final evaluator snapshots and completion guards.
- If an instruction mentions a hook-generated file, verify it exists before relying on it.
- If a `freddy` flag or subcommand behaves differently than expected, check `freddy --help` / subcommand help and adapt instead of assuming the prompt is correct.
- Prefer shipping a narrower, evidence-backed deliverable over following stale ceremony that blocks progress.
- In multiturn strategy, persist state after each completed phase and continue until the session reaches COMPLETE or BLOCKED.
"""

    return text


def default_session_model(backend: str | None = None) -> str:
    selected = backend or ("codex" if shutil.which("codex") else "claude")
    return SESSION_MODEL if selected == "claude" else "gpt-5.4"


def config_dir_name(domain: str) -> str:
    return get_workflow_spec(domain).config_dir_name
