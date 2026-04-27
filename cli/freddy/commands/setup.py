"""Setup command — check provider credentials."""
import os

from ..config import load_config
from ..output import emit


def setup_command() -> None:
    """Interactive setup: verify provider credentials."""
    config = load_config()
    clients_dir = config.clients_dir if config and config.clients_dir else None

    checks = [
        ("DATAFORSEO_LOGIN", "DataForSEO"),
        ("COMPETITIVE_FOREPLAY_API_KEY", "Foreplay"),
        ("COMPETITIVE_ADYNTEL_API_KEY", "Adyntel"),
        ("MONITORING_XPOZ_API_KEY", "Xpoz"),
        ("MONITORING_NEWSDATA_API_KEY", "NewsData"),
        ("GOOGLE_API_KEY", "Gemini"),
    ]
    providers = {
        name: "configured" if os.environ.get(env_var) else "not set"
        for env_var, name in checks
    }

    output = {
        "clients_dir": clients_dir,
        "providers": providers,
        "hint": "Copy .env.example to .env and fill in credentials.",
        "status": "ok",
    }

    from ..main import get_state
    emit(output, human=get_state().human)
