"""Configuration management — env var + ~/.freddy/config.json."""

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path


_CONFIG_DIR = Path.home() / ".freddy"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


@dataclass(frozen=True, slots=True)
class Config:
    api_key: str
    base_url: str


def _ensure_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(_CONFIG_DIR, 0o700)


def load_config() -> Config | None:
    """Load config from env var (preferred) or config file (fallback)."""
    api_key = os.environ.get("FREDDY_API_KEY")
    base_url = os.environ.get("FREDDY_API_URL", "")

    if api_key:
        return Config(api_key=api_key, base_url=base_url or _read_base_url_from_file())

    # Fallback to config file
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text())
            file_key = data.get("api_key", "")
            if file_key:
                return Config(
                    api_key=file_key,
                    base_url=base_url or data.get("base_url", "https://api.freddy.example"),
                )
        except (json.JSONDecodeError, OSError):
            pass

    return None


def _read_base_url_from_file() -> str:
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text())
            return data.get("base_url", "https://api.freddy.example")
        except (json.JSONDecodeError, OSError):
            pass
    return "https://api.freddy.example"


def save_config(api_key: str, base_url: str = "https://api.freddy.example") -> None:
    """Save config to ~/.freddy/config.json with 0600 permissions."""
    _ensure_dir()
    data = {"api_key": api_key, "base_url": base_url}
    _CONFIG_FILE.write_text(json.dumps(data, indent=2))
    os.chmod(_CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0600


def delete_config() -> bool:
    """Securely delete config file. Returns True if deleted."""
    if _CONFIG_FILE.exists():
        # Overwrite before deleting
        _CONFIG_FILE.write_text("{}")
        _CONFIG_FILE.unlink()
        return True
    return False
