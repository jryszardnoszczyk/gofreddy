"""Setup command — interactive onboarding."""

import json
import os
import sys

import typer

from ..config import load_config, save_config


def setup_command() -> None:
    """Interactive setup: API key, default client, environment check."""
    print("Freddy CLI Setup")
    print("=" * 40)

    # Step 1: API key
    config = load_config()
    if config:
        print(f"\nAPI key: configured (ends in ...{config.api_key[-4:]})")
        change = typer.confirm("Change API key?", default=False)
        if change:
            api_key = typer.prompt("Enter your API key")
            base_url = typer.prompt("API base URL", default=config.base_url)
            save_config(api_key=api_key, base_url=base_url)
            print("API key saved.")
    else:
        api_key = typer.prompt("Enter your API key")
        base_url = typer.prompt("API base URL", default="https://api.freddy.example")
        save_config(api_key=api_key, base_url=base_url)
        print("API key saved.")

    # Step 2: Default client
    print("\nDefault Client:")
    default_client = typer.prompt("Default client name for sessions", default="default")
    print(f"  Default client: {default_client}")
    print("  Tip: Use --client flag to override per session:")
    print(f"    freddy session start --client {default_client}")

    # Step 3: Check environment integration
    print("\nEnvironment Integration:")
    env_key = os.environ.get("FREDDY_API_KEY")
    if env_key:
        print("  FREDDY_API_KEY: set in environment")
    else:
        print("  FREDDY_API_KEY: not set")
        print("  Tip: Add to your shell profile for agent sessions:")
        print("    export FREDDY_API_KEY=<your-key>")

    print("\nSetup complete!")
