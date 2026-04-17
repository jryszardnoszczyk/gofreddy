"""Configuration — env vars + ~/.freddy/config.json.

Merged schema: nullable fields for agency (clients_dir) + freddy (api_key, base_url).
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv

CONFIG_PATH = Path.home() / ".freddy" / "config.json"


@dataclass
class Config:
    clients_dir: Path | None = None
    api_key: str | None = None
    base_url: str | None = None


def load_config() -> Config | None:
    """Load config from disk + env. Returns None if no config file exists.

    Env fallbacks: FREDDY_CLIENTS_DIR fills clients_dir when file is absent.
    """
    load_dotenv()
    if not CONFIG_PATH.exists():
        env_clients = os.environ.get("FREDDY_CLIENTS_DIR")
        if env_clients:
            return Config(clients_dir=Path(env_clients))
        return None
    data = json.loads(CONFIG_PATH.read_text())
    return Config(
        clients_dir=Path(data["clients_dir"]) if data.get("clients_dir") else None,
        api_key=data.get("api_key"),
        base_url=data.get("base_url"),
    )


def save_config(**kwargs) -> None:
    """Merge the given fields into the on-disk config (creating it if missing)."""
    existing = load_config() or Config()
    for k, v in kwargs.items():
        if v is not None:
            setattr(existing, k, v)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        k: (str(v) if isinstance(v, Path) else v)
        for k, v in asdict(existing).items()
        if v is not None
    }
    CONFIG_PATH.write_text(json.dumps(payload))
    os.chmod(CONFIG_PATH, 0o600)


def delete_config() -> bool:
    """Delete the config file. Returns True if a file was removed."""
    try:
        CONFIG_PATH.unlink()
        return True
    except FileNotFoundError:
        return False
