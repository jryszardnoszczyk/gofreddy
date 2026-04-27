"""Save data to the client workspace — local file I/O.

Data-only tool. No API calls. Writes under the same workspace that
`freddy client new <client>` creates so `client log`/`report` and other
client-scoped tools see the same tree.
"""

import json

import typer

from .client import _clients_dir
from ..output import emit, emit_error


def save_command(
    client: str = typer.Argument(..., help="Client name (must match `freddy client new`)"),
    key: str = typer.Argument(..., help="Data key (becomes filename, e.g. 'competitors/Nike')"),
    data: str = typer.Argument(..., help="JSON data to save"),
) -> None:
    """Save data into the client workspace at <clients_dir>/<client>/<key>.json."""
    client_dir = _clients_dir() / client

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        emit_error("invalid_json", "Data argument must be valid JSON")
        return

    base = client_dir.resolve()
    target = (client_dir / f"{key}.json").resolve()
    try:
        target.relative_to(base)
    except ValueError:
        emit_error("path_traversal", "Key must not escape client workspace")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(parsed, indent=2, default=str))

    from ..main import get_state
    emit({"saved": str(target), "key": key, "client": client}, human=get_state().human)
