"""Client workspace management — freddy client new/list/log/report."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from ..api import emit, emit_error
from ..config import load_config

app = typer.Typer(help="Client workspace management.", no_args_is_help=True)


def _clients_dir() -> Path:
    return load_config().clients_dir


def _client_dir(name: str) -> Path:
    return _clients_dir() / name


@app.command()
def new(name: str = typer.Argument(..., help="Client name (used as directory name)")) -> None:
    """Create a new client workspace."""
    d = _client_dir(name)
    if d.exists():
        emit_error("client_exists", f"Client '{name}' already exists at {d}")
        raise SystemExit(1)
    d.mkdir(parents=True, exist_ok=True)
    (d / "sessions").mkdir(exist_ok=True)
    (d / "artifacts").mkdir(exist_ok=True)
    config = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }
    (d / "config.json").write_text(json.dumps(config, indent=2))
    emit({"status": "created", "client": name, "path": str(d)})


@app.command(name="list")
def list_clients() -> None:
    """List all client workspaces."""
    cdir = _clients_dir()
    if not cdir.exists():
        emit({"clients": []})
        return
    clients = []
    for entry in sorted(cdir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        config_path = entry / "config.json"
        config: dict = {}
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        sessions_dir = entry / "sessions"
        session_count = len(list(sessions_dir.iterdir())) if sessions_dir.exists() else 0
        clients.append({
            "name": entry.name,
            "status": config.get("status", "unknown"),
            "created_at": config.get("created_at"),
            "session_count": session_count,
        })
    emit({"clients": clients})


@app.command()
def log(
    name: str = typer.Argument(..., help="Client name"),
    limit: int = typer.Option(50, "--limit", help="Max entries"),
) -> None:
    """Show audit trail for a client."""
    d = _client_dir(name)
    if not d.exists():
        emit_error("client_not_found", f"Client '{name}' not found")
        raise SystemExit(1)
    sessions_dir = d / "sessions"
    if not sessions_dir.exists():
        emit({"client": name, "actions": []})
        return
    actions: list[dict] = []
    for session_dir in sorted(sessions_dir.iterdir(), reverse=True):
        if not session_dir.is_dir():
            continue
        actions_path = session_dir / "actions.jsonl"
        if not actions_path.exists():
            continue
        for line in actions_path.read_text().strip().split("\n"):
            if not line:
                continue
            try:
                actions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(actions) >= limit:
                break
        if len(actions) >= limit:
            break
    emit({"client": name, "total_actions": len(actions), "actions": actions})


@app.command()
def report(name: str = typer.Argument(..., help="Client name")) -> None:
    """Generate a summary report for a client."""
    d = _client_dir(name)
    if not d.exists():
        emit_error("client_not_found", f"Client '{name}' not found")
        raise SystemExit(1)
    sessions_dir = d / "sessions"
    total_sessions = 0
    total_actions = 0
    total_cost = 0.0
    if sessions_dir.exists():
        for session_dir in sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue
            total_sessions += 1
            actions_path = session_dir / "actions.jsonl"
            if actions_path.exists():
                for line in actions_path.read_text().strip().split("\n"):
                    if line:
                        total_actions += 1
    cost_log = d / "cost_log.jsonl"
    if cost_log.exists():
        for line in cost_log.read_text().strip().split("\n"):
            if not line:
                continue
            try:
                total_cost += (json.loads(line).get("cost_usd") or 0.0)
            except json.JSONDecodeError:
                continue
    emit({
        "client": name,
        "total_sessions": total_sessions,
        "total_actions": total_actions,
        "total_cost_usd": round(total_cost, 4),
    })
