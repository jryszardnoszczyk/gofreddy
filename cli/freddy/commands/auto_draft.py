"""Auto-draft worker: evaluates trigger conditions and generates drafts."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

import typer
import yaml

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
    if not config.exists():
        typer.echo(f"Config file not found: {config}", err=True)
        raise typer.Exit(code=1)

    try:
        with open(config) as f:
            cfg = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        json.dump(
            {"error": {"code": "invalid_yaml", "message": f"Failed to parse YAML config: {exc}"}},
            sys.stderr,
        )
        sys.stderr.write("\n")
        raise typer.Exit(code=1)

    drafts = cfg.get("drafts", [])
    if not drafts:
        typer.echo("No draft entries in config.")
        return

    triggered = 0
    skipped = 0
    failed = 0

    for entry in drafts:
        name = entry.get("name", "unnamed")
        trigger = entry.get("trigger", {})
        action = entry.get("action", {})

        if not _check_trigger(trigger, base_dir):
            skipped += 1
            typer.echo(f"[SKIP] {name}: trigger not met")
            continue

        cmd = _build_command(action)
        # Substitute template variables
        trigger_vars = {
            "monitor_id": trigger.get("monitor_id", ""),
            "session_dir": trigger.get("session_dir", ""),
        }
        cmd = [part.format(**trigger_vars) for part in cmd]

        if dry_run:
            typer.echo(f"[DRY-RUN] {name}: would execute: {' '.join(cmd)}")
            triggered += 1
            continue

        typer.echo(f"[RUN] {name}: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, timeout=120, capture_output=True, text=True)
            if result.returncode == 0:
                triggered += 1
                typer.echo(f"  ✓ Success")
            else:
                failed += 1
                typer.echo(f"  ✗ Failed (exit {result.returncode}): {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            failed += 1
            typer.echo(f"  ✗ Timeout after 120s")
        except Exception as exc:
            failed += 1
            typer.echo(f"  ✗ Error: {exc}")

    typer.echo(f"\nSummary: triggered={triggered}, skipped={skipped}, failed={failed}")
