"""Local session state management — ~/.freddy/session.json."""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


_SESSION_FILE = Path.home() / ".freddy" / "session.json"


@dataclass(frozen=True, slots=True)
class LocalSession:
    session_id: str
    client_name: str
    session_type: str = "ad_hoc"
    purpose: str | None = None


def get_active_session() -> LocalSession | None:
    """Read the active session from disk. Returns None if no session."""
    if not _SESSION_FILE.exists():
        return None
    try:
        data = json.loads(_SESSION_FILE.read_text())
        return LocalSession(
            session_id=data["session_id"],
            client_name=data["client_name"],
            session_type=data.get("session_type", "ad_hoc"),
            purpose=data.get("purpose"),
        )
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def save_session(session: LocalSession) -> None:
    """Save session state to disk."""
    _SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(_SESSION_FILE.parent, 0o700)
    _SESSION_FILE.write_text(json.dumps(asdict(session), indent=2))
    os.chmod(_SESSION_FILE, 0o600)


def clear_session() -> bool:
    """Remove session state. Returns True if removed."""
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()
        return True
    return False
