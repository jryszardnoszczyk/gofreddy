"""Save data to the client workspace — local file I/O.

Data-only tool. No API calls. Writes under the same workspace that
`freddy client new <client>` creates so `client log`/`report` and other
client-scoped tools see the same tree.
"""

import json
import re
from datetime import datetime, timezone

import typer

from ..config import load_config
from ..output import emit, emit_error

# Reject keys that produce hidden files (".json"), bare dot names ("..json"),
# or otherwise non-descriptive filenames. Path-traversal escapes are caught
# separately by the resolve() check below — this rule covers what stays
# inside the session dir but still creates pathological filenames (F-a-5-2).
_INVALID_KEY_RE = re.compile(r"^\.*$")


def save_command(
    client: str = typer.Argument(..., help="Client name"),
    key: str = typer.Argument(..., help="Data key (becomes filename, e.g. 'competitors/Nike')"),
    data: str = typer.Argument(..., help="JSON data to save"),
) -> None:
    """Save data into the client workspace at <clients_dir>/<client>/<key>.json."""
    if _INVALID_KEY_RE.match(key.strip()) or "/" not in key and not key.strip():
        emit_error(
            "invalid_key",
            f"Key {key!r} is empty or only dots; pick a non-empty descriptive key",
        )
    # Each path segment of `key` must be non-empty and non-dot-only,
    # and must fit within the filesystem's per-component name limit
    # (~255 bytes; .json suffix consumes 5).
    for segment in key.split("/"):
        if _INVALID_KEY_RE.match(segment):
            emit_error(
                "invalid_key",
                f"Key segment {segment!r} (in {key!r}) is empty or only dots",
            )
        if len(segment) > 250:
            emit_error(
                "invalid_key",
                f"Key segment is {len(segment)} characters; max 250 (filesystem name-length limit)",
            )

    # `client` must be a single slug — no path separators, not empty, not
    # dot-only. Without this, `client='../../..'` escapes the session jail
    # because both sides of the resolve()/startswith check below are derived
    # from the unsanitized value and end up pointing to the same escaped path.
    if _INVALID_KEY_RE.match(client.strip()) or "/" in client or "\\" in client:
        emit_error(
            "invalid_client",
            f"Client {client!r} must be a non-empty slug without path separators",
        )

    # F-a-8-3: refuse unknown clients. Same gate as `client log`/`client report`
    # (sibling commands on the same conceptual `client` argument): a typoed
    # slug used to silently create orphan dirs under sessions/competitive/<typo>/
    # that no other command could read back.
    cfg = load_config()
    if cfg is None or cfg.clients_dir is None:
        emit_error(
            "client_not_found",
            f"Client '{client}' not found (no clients_dir configured; "
            f"run `freddy setup` or set FREDDY_CLIENTS_DIR).",
        )
    client_dir = cfg.clients_dir / client
    if not client_dir.exists():
        emit_error("client_not_found", f"Client '{client}' not found")
    if not (client_dir / "config.json").exists():
        emit_error(
            "client_not_found",
            f"Client '{client}' has no config.json (stray directory). "
            f"Run `freddy client new {client}` to register it properly.",
        )

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        emit_error("invalid_json", "Data argument must be valid JSON")
        return

    # Resolve path safely — prevent directory traversal
    base = client_dir.resolve()
    target = (client_dir / f"{key}.json").resolve()
    try:
        target.relative_to(base)
    except ValueError:
        emit_error("path_traversal", "Key must not escape client workspace")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(parsed, indent=2, default=str))

    # F-a-2-1: append an action-trail row so `client log`/`client report`
    # surface this save (the prior F-a-1-1@c1 fix landed save under
    # clients/<client>/<key>.json but the audit-trail commands only walk
    # sessions/*/actions.jsonl, so saved data was still invisible).
    save_session_dir = client_dir / "sessions" / "save"
    save_session_dir.mkdir(parents=True, exist_ok=True)
    action_row = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool_name": "save",
        "status": "ok",
        "key": key,
        "path": str(target),
    }
    with (save_session_dir / "actions.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(action_row, default=str) + "\n")

    from ..main import get_state
    emit({"saved": str(target), "key": key, "client": client}, human=get_state().human)
