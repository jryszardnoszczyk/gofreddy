"""Configuration — env vars + ~/.freddy/config.json."""
from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_CONFIG_DIR = Path.home() / ".freddy"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


@dataclass(frozen=True, slots=True)
class Config:
    clients_dir: Path = field(default_factory=lambda: Path("./clients"))


def _ensure_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(_CONFIG_DIR, 0o700)


def load_config() -> Config:
    load_dotenv()
    clients_dir = Path(os.environ.get("FREDDY_CLIENTS_DIR", "./clients"))
    return Config(clients_dir=clients_dir)


def save_config(clients_dir: str | None = None) -> None:
    _ensure_dir()
    data: dict = {}
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    if clients_dir is not None:
        data["clients_dir"] = clients_dir
    _CONFIG_FILE.write_text(json.dumps(data, indent=2))
    os.chmod(_CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
