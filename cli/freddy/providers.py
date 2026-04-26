"""Provider factory and CLI helpers."""
from __future__ import annotations

import functools
import json
import sys
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class CLIError:
    code: str
    message: str
    input_data: dict[str, Any] | None = None


# ── Backward-compat stubs (commands migrating to direct provider calls) ──
def make_client(*args: Any, **kwargs: Any) -> Any:
    raise NotImplementedError(
        "Command not migrated. Use 'freddy audit' or 'freddy client' commands."
    )


def api_request(*args: Any, **kwargs: Any) -> dict[str, Any]:
    raise NotImplementedError("Command not migrated.")


def log_action_to_session(*args: Any, **kwargs: Any) -> None:
    pass  # no-op


def set_global_timeout(seconds: float | None) -> None:
    pass  # no-op


# ── Provider factory ─────────────────────────────────────────────────────
def get_provider(name: str) -> Any:
    """Instantiate a provider using its module's Settings class."""
    if name == "dataforseo":
        from src.seo.config import SeoSettings
        from src.seo.providers.dataforseo import DataForSeoProvider
        s = SeoSettings()
        return DataForSeoProvider(login=s.dataforseo_login, password=s.dataforseo_password)
    if name == "foreplay":
        from src.competitive.config import CompetitiveSettings
        from src.competitive.providers.foreplay import ForeplayProvider
        s = CompetitiveSettings()
        return ForeplayProvider(api_key=s.foreplay_api_key.get_secret_value())
    if name == "adyntel":
        from src.competitive.config import CompetitiveSettings
        from src.competitive.providers.adyntel import AdyntelProvider
        s = CompetitiveSettings()
        return AdyntelProvider(
            api_key=s.adyntel_api_key.get_secret_value(),
            email=s.adyntel_email,
        )
    if name == "xpoz":
        from src.monitoring.adapters.xpoz import XpozAdapter
        from src.monitoring.config import MonitoringSettings
        return XpozAdapter(MonitoringSettings())
    if name == "newsdata":
        from src.monitoring.adapters.news import NewsDataAdapter
        from src.monitoring.config import MonitoringSettings
        return NewsDataAdapter(MonitoringSettings())
    raise ValueError(f"Unknown provider: {name}")


# ── Output helpers ───────────────────────────────────────────────────────
def emit(data: Any) -> None:
    json.dump(data, sys.stdout, default=str, indent=2)
    sys.stdout.write("\n")


def emit_error(code: str, message: str) -> None:
    json.dump({"error": {"code": code, "message": message}}, sys.stderr)
    sys.stderr.write("\n")


def handle_errors(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except SystemExit:
            raise
        except Exception as exc:
            emit_error("unexpected_error", str(exc))
            raise SystemExit(1)
    return wrapper
