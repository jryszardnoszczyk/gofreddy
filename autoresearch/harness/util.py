"""Shared utilities -- subprocess helpers, JSON loading, timeout defaults.

Per Plan B U11b (2026-05-11): the per-fixture session lock (acquire_lock /
release_lock / _lock_path) was stubbed to no-ops — 0 collisions across
147 archived variants per docs/research/2026-05-11-001 §7. Function
signatures preserved so v006/run.py imports keep working without any
edit to the archived runner.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import harness  # noqa: F401,E402  # ensure package-level path setup runs

from workflows import get_workflow_spec  # type: ignore  # noqa: E402

SCRIPT_DIR = harness.ARCHIVE_CURRENT_DIR


def acquire_lock(domain: str, client: str, fixture_id: str | None = None) -> int:
    """No-op stub. Returns a sentinel fd so callers' `if fd is None` branch
    never fires. Audit: 0 collisions in 147 archived variants — the lock
    was theatre."""
    return 0


def release_lock(fd: int | None, domain: str, client: str, fixture_id: str | None = None) -> None:
    """No-op stub paired with acquire_lock."""
    return None


def default_timeout_for_strategy(domain: str, strategy: str) -> int:
    cfg = get_workflow_spec(domain).config
    if strategy == "multiturn":
        return cfg.multiturn_timeout or max(cfg.default_timeout, 7200)
    return cfg.default_timeout


def _load_json_output(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


_RUN_SCRIPT_DEFAULT_TIMEOUT = 120

# Per-script timeout overrides for scripts that legitimately exceed the
# default. Keep this list short — most post-session scripts complete in a
# few seconds; the entries here are scripts whose work cost is dominated
# by external subprocess calls (chromium for render, gemini for evals).
_RUN_SCRIPT_TIMEOUTS = {
    # render_report.py: Stage-2 codex enrichment (~30-90s) + html_to_pdf
    # (Chrome ~30-60s) + html_to_screenshot (Chrome ~30-60s) easily clears
    # 120s when RENDER_BACKEND defaults to codex. 360s gives all 3 phases
    # room to complete with a safety margin. Surfaced 2026-05-08 evening
    # when the storyboard auto-render hit the 120s wall after session
    # produced 5 KEEP storyboards.
    "render_report.py": 360,
}


def _run_script(script_name: str, *args, stdout_file: Path | None = None,
                timeout: int | None = None):
    """Run a script. Resolves variant-side first, then live-side fallback. Non-fatal.

    Lookup order:

    1. ``SCRIPT_DIR/scripts/<script_name>`` — the variant's own copy (e.g.
       ``archive/current_runtime/scripts/<script_name>``). A meta-agent that
       mutates a script lives here.
    2. ``AUTORESEARCH_DIR/scripts/<script_name>`` — the live shared copy under
       ``autoresearch/scripts/``. One source of truth for utility scripts the
       evolution loop doesn't need to mutate per variant (summarize_session,
       etc.). Lets us delete the per-archive copies once each variant's local
       script is identical to live.

    Timeout: default 120s, overridable via ``timeout`` arg or per-script
    entries in ``_RUN_SCRIPT_TIMEOUTS``. Render-pipeline scripts that
    invoke chromium + codex are pre-tuned for higher ceilings.

    Returns silently when neither exists (callers tolerate missing scripts —
    e.g. lanes that don't ship a generate_report.py).
    """
    variant_script = SCRIPT_DIR / "scripts" / script_name
    live_script = AUTORESEARCH_DIR / "scripts" / script_name
    script = variant_script if variant_script.exists() else live_script
    if not script.exists():
        return
    effective_timeout = (
        timeout if timeout is not None
        else _RUN_SCRIPT_TIMEOUTS.get(script_name, _RUN_SCRIPT_DEFAULT_TIMEOUT)
    )
    try:
        cmd = ["python3", str(script)] + list(args)
        if stdout_file:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=effective_timeout,
            )
            stdout_file.write_text(result.stdout)
        else:
            subprocess.run(
                cmd, capture_output=True, text=True, timeout=effective_timeout,
            )
    except Exception as e:
        print(f"WARNING: {script_name} failed: {e}")


def _run_subprocess(cmd: list[str]):
    """Run arbitrary subprocess. Non-fatal."""
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as e:
        print(f"WARNING: {cmd[0]} failed: {e}")
