"""Client workspace management — freddy client new/list/log/report."""
from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import typer

from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Client workspace management.", no_args_is_help=True)

# Same check as supabase/migrations/20260417000001_init.sql clients_slug_format.
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


def _clients_dir() -> Path:
    cfg = load_config()
    if cfg is None or cfg.clients_dir is None:
        raise typer.BadParameter(
            "No clients_dir configured. Run `freddy setup` or set FREDDY_CLIENTS_DIR."
        )
    return cfg.clients_dir


def _client_dir(name: str) -> Path:
    return _clients_dir() / name


def _register_client_in_db(slug: str) -> None:
    """Insert the client + a membership for the caller into the backend so
    `session start --client <slug>` and other API-backed commands can resolve
    the slug AND pass the scope check.

    No-op when DATABASE_URL is unset (CLI-only workflows against a remote API)
    or when the slug doesn't match the DB's slug CHECK constraint.
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url or not _SLUG_RE.match(slug):
        return

    # Resolve the caller's user_id so the new client is actually accessible —
    # without a membership, a non-admin user hits 403 on session start even
    # though the slug now exists.
    from ..api import api_request, make_client
    cfg = load_config()
    if cfg is None or cfg.api_key is None or cfg.base_url is None:
        return
    try:
        me = api_request(make_client(cfg), "GET", "/v1/auth/me")
    except SystemExit:
        return  # API unreachable; skip DB registration — filesystem workspace already created
    user_id = me.get("user_id")
    if not user_id:
        return

    async def _insert() -> None:
        import asyncpg  # local import so non-DB CLI paths don't pay the cost
        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute(
                "INSERT INTO clients (slug, name) VALUES ($1, $2) ON CONFLICT (slug) DO NOTHING",
                slug, slug,
            )
            await conn.execute(
                "INSERT INTO user_client_memberships (user_id, client_id, role) "
                "SELECT $1::uuid, id, 'owner' FROM clients WHERE slug = $2 "
                "ON CONFLICT (user_id, client_id) DO NOTHING",
                user_id, slug,
            )
        finally:
            await conn.close()

    asyncio.run(_insert())


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
    _register_client_in_db(name)
    from ..main import get_state
    emit({"status": "created", "client": name, "path": str(d)}, human=get_state().human)


@app.command(name="list")
def list_clients() -> None:
    """List all client workspaces."""
    from ..main import get_state
    cdir = _clients_dir()
    if not cdir.exists():
        emit({"clients": []}, human=get_state().human)
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
    emit({"clients": clients}, human=get_state().human)


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
    from ..main import get_state
    sessions_dir = d / "sessions"
    if not sessions_dir.exists():
        emit({"client": name, "actions": []}, human=get_state().human)
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
    emit({"client": name, "total_actions": len(actions), "actions": actions}, human=get_state().human)


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
    from ..main import get_state
    emit({
        "client": name,
        "total_sessions": total_sessions,
        "total_actions": total_actions,
        "total_cost_usd": round(total_cost, 4),
    }, human=get_state().human)
