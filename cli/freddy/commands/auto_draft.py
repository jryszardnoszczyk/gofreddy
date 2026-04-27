"""Auto-draft worker: evaluates trigger conditions and generates drafts."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import typer
import yaml

from ..output import emit, emit_error

logger = logging.getLogger(__name__)

app = typer.Typer(help="Auto-draft worker for cron-driven draft generation.")


def _check_trigger(trigger: dict, base_dir: Path) -> bool:
    """Check if a trigger condition is met."""
    trigger_type = trigger.get("type", "")

    if trigger_type == "digest_available":
        monitor_id = trigger.get("monitor_id", "")
        digest_path = base_dir / "sessions" / "monitoring" / monitor_id / "digest.md"
        return digest_path.exists()

    if trigger_type == "brief_available":
        session_dir = trigger.get("session_dir", "")
        session_path = base_dir / session_dir
        return (session_path / "brief.md").exists() or (session_path / "digest.md").exists()

    if trigger_type == "cron":
        return True  # Always trigger; schedule enforcement is external

    logger.warning("Unknown trigger type: %s", trigger_type)
    return False


def _build_command(action: dict) -> list[str]:
    """Build CLI command from action spec."""
    command = action.get("command", "")
    args = action.get("args", {})
    parts = command.split()
    for key, value in args.items():
        flag = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                parts.append(flag)
        else:
            parts.extend([flag, str(value)])
    return parts


@app.command("run")
def auto_draft(
    config: Path = typer.Option(..., "--config", help="Path to auto-drafts.yaml config"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print what would be drafted without executing"),
    base_dir: Path = typer.Option(Path("."), "--base-dir", help="Base directory for resolving paths"),
) -> None:
    """Evaluate triggers and generate drafts from YAML config."""
    from ..main import get_state
    human = get_state().human
    if not config.exists():
        emit_error("config_not_found", f"Config file not found: {config}")

    try:
        with open(config) as f:
            cfg = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        emit_error("invalid_yaml", f"Invalid YAML in {config}: {exc}")

    if not isinstance(cfg, dict):
        # F-a-5-1: yaml.safe_load returns the raw type for scalar / list / null
        # roots — `cfg.get(...)` then crashes with AttributeError. Reject with
        # the same structured error YAMLError already produces.
        emit_error(
            "invalid_yaml",
            f"Config root must be a mapping with a 'drafts' key, got "
            f"{type(cfg).__name__}",
        )

    drafts = cfg.get("drafts", [])
    if not drafts:
        emit({"info": "No draft entries in config."}, human=human)
        return

    triggered = 0
    skipped = 0
    failed = 0

    entries: list[dict] = []
    for entry in drafts:
        name = entry.get("name", "unnamed")
        trigger = entry.get("trigger", {})
        action = entry.get("action", {})
        entry_record: dict = {"name": name}

        if not _check_trigger(trigger, base_dir):
            skipped += 1
            entry_record["status"] = "skipped"
            entry_record["reason"] = "trigger not met"
            entries.append(entry_record)
            continue

        cmd = _build_command(action)
        # Substitute template variables
        trigger_vars = {
            "monitor_id": trigger.get("monitor_id", ""),
            "session_dir": trigger.get("session_dir", ""),
        }
        cmd = [part.format(**trigger_vars) for part in cmd]
        entry_record["cmd"] = cmd

        if dry_run:
            entry_record["status"] = "dry-run"
            triggered += 1
            entries.append(entry_record)
            continue

        try:
            result = subprocess.run(cmd, timeout=120, capture_output=True, text=True)
            if result.returncode == 0:
                triggered += 1
                entry_record["status"] = "success"
            else:
                failed += 1
                entry_record["status"] = "failed"
                entry_record["exit_code"] = result.returncode
                entry_record["stderr"] = result.stderr[:200]
        except subprocess.TimeoutExpired:
            failed += 1
            entry_record["status"] = "timeout"
        except Exception as exc:
            failed += 1
            entry_record["status"] = "error"
            entry_record["error"] = str(exc)
        entries.append(entry_record)

    emit(
        {
            "summary": {"triggered": triggered, "skipped": skipped, "failed": failed},
            "entries": entries,
        },
        human=human,
    )
