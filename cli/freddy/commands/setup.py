"""Setup command — check provider credentials."""
import os

from ..config import load_config


def setup_command() -> None:
    """Interactive setup: verify provider credentials."""
    print("Freddy Agency CLI — Setup")
    print("=" * 40)

    config = load_config()
    clients_dir = config.clients_dir if config and config.clients_dir else "(not configured)"
    print(f"\nClients directory: {clients_dir}")

    checks = [
        ("DATAFORSEO_LOGIN", "DataForSEO"),
        ("COMPETITIVE_FOREPLAY_API_KEY", "Foreplay"),
        ("COMPETITIVE_ADYNTEL_API_KEY", "Adyntel"),
        ("MONITORING_XPOZ_API_KEY", "Xpoz"),
        ("MONITORING_NEWSDATA_API_KEY", "NewsData"),
        ("GOOGLE_API_KEY", "Gemini"),
    ]
    print("\nProvider credentials:")
    for env_var, name in checks:
        status = "configured" if os.environ.get(env_var) else "not set"
        print(f"  {name}: {status}")

    print("\nCopy .env.example to .env and fill in credentials.")
    print("Setup complete!")
