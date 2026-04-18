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
    """Load config from disk + env. Returns None if no config file exists AND no env.

    Env fallbacks (match freddy/cli/freddy/config.py behavior so ported commands work):
      - FREDDY_API_KEY fills api_key
      - FREDDY_API_URL or FREDDY_API_BASE_URL fills base_url
      - FREDDY_CLIENTS_DIR fills clients_dir
    Env wins over file values so CI / dev loops don't need a config.json.
    """
    load_dotenv()
    env_key = os.environ.get("FREDDY_API_KEY")
    env_base = os.environ.get("FREDDY_API_URL") or os.environ.get("FREDDY_API_BASE_URL")
    env_clients = os.environ.get("FREDDY_CLIENTS_DIR")

    file_data: dict = {}
    if CONFIG_PATH.exists():
        try:
            file_data = json.loads(CONFIG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            file_data = {}

    api_key = env_key or file_data.get("api_key")
    base_url = env_base or file_data.get("base_url")
    clients_dir_val = env_clients or file_data.get("clients_dir")

    if not any([api_key, base_url, clients_dir_val]):
        return None

    return Config(
        clients_dir=Path(clients_dir_val) if clients_dir_val else None,
        api_key=api_key,
        base_url=base_url,
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
