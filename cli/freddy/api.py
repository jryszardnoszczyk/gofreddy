"""HTTP client for Freddy REST API."""

import functools
import json
import sys
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from .config import Config
from .session import get_active_session

_DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=180.0, write=5.0, pool=5.0)
_LOG_TIMEOUT = httpx.Timeout(connect=2.0, read=2.0, write=2.0, pool=1.0)

# Global read-timeout override set by main_callback's --timeout flag.
# Applies to every make_client() call site as defense-in-depth against backend stalls.
_global_timeout_seconds: float | None = None


def set_global_timeout(seconds: float | None) -> None:
    """Set a process-wide read timeout override. Called by main_callback."""
    global _global_timeout_seconds
    _global_timeout_seconds = seconds


@dataclass(frozen=True, slots=True)
class CLIError:
    code: str
    message: str
    input_data: dict[str, Any] | None = None


def make_client(
    config: Config,
    *,
    timeout_seconds: float | None = None,
) -> httpx.Client:
    """Create a configured httpx client.

    timeout_seconds overrides the default read timeout when provided
    (connect/write/pool remain at defaults). Use this for defense-in-depth
    against backend stalls — the CLI will abort after the specified deadline.
    """
    headers: dict[str, str] = {
        "X-API-Key": config.api_key,
        "Accept": "application/json",
        "User-Agent": "freddy-cli/0.1",
    }
    session = get_active_session()
    if session:
        headers["X-Session-Id"] = session.session_id

    effective_timeout = (
        timeout_seconds if timeout_seconds is not None else _global_timeout_seconds
    )
    if effective_timeout is not None:
        timeout = httpx.Timeout(
            connect=5.0,
            read=effective_timeout,
            write=5.0,
            pool=5.0,
        )
    else:
        timeout = _DEFAULT_TIMEOUT

    return httpx.Client(
        base_url=config.base_url.rstrip("/"),
        headers=headers,
        timeout=timeout,
        follow_redirects=False,
    )


def api_request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make an API request and return parsed JSON.

    Raises CLIError-wrapped SystemExit on failure.
    """
    # Filter None values from params
    if params:
        params = {k: v for k, v in params.items() if v is not None}

    response = client.request(method, path, json=json_data, params=params or None)

    if response.status_code >= 400:
        try:
            body = response.json()
            error = body.get("error", body.get("detail", {}))
            if isinstance(error, dict):
                code = error.get("code", f"http_{response.status_code}")
                message = error.get("message", response.text)
                # If backend returned structured `details` (e.g. validation errors
                # with field-level hints), append the first few to the message so
                # the caller sees which field is wrong without parsing JSON.
                details = error.get("details", [])
                if (
                    isinstance(details, list)
                    and details
                    and not message.endswith(":")
                    and ":" not in message.split(" ", 2)[-1][:20]
                ):
                    field_hints: list[str] = []
                    for entry in details[:3]:
                        if not isinstance(entry, dict):
                            continue
                        loc = entry.get("loc") or []
                        msg = entry.get("msg") or ""
                        if loc and msg:
                            field_hints.append(
                                f"{'.'.join(str(p) for p in loc)}: {msg}"
                            )
                    if field_hints and all(h not in message for h in field_hints):
                        message = f"{message} [{'; '.join(field_hints)}]"
            else:
                code = f"http_{response.status_code}"
                message = str(error)
        except (json.JSONDecodeError, ValueError):
            code = f"http_{response.status_code}"
            message = response.text

        _emit_error(CLIError(code=code, message=message))
        raise SystemExit(1)

    if response.status_code == 204:
        return {}

    return response.json()


def log_action_to_session(
    client: httpx.Client,
    session_id: str,
    tool_name: str,
    input_summary: dict[str, Any] | None = None,
    output_summary: dict[str, Any] | None = None,
    duration_ms: int | None = None,
) -> None:
    """Log an action to the active session. Non-fatal — warns on failure."""
    payload: dict[str, Any] = {"tool_name": tool_name}
    if input_summary is not None:
        payload["input_summary"] = input_summary
    if output_summary is not None:
        payload["output_summary"] = output_summary
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms

    for attempt in range(2):
        try:
            resp = client.post(
                f"/v1/sessions/{session_id}/actions",
                json=payload,
                timeout=_LOG_TIMEOUT,
            )
            if resp.status_code < 400:
                return
            if attempt == 0:
                continue
            _warn(f"Action logging failed: HTTP {resp.status_code}")
            return
        except httpx.HTTPError:
            if attempt == 0:
                continue
            _warn("Action logging failed: connection error")
            return


def _emit_error(error: CLIError) -> None:
    """Write structured error to stderr."""
    obj: dict[str, Any] = {"error": {"code": error.code, "message": error.message}}
    if error.input_data:
        obj["error"]["input"] = error.input_data
    json.dump(obj, sys.stderr)
    sys.stderr.write("\n")


def _warn(message: str) -> None:
    """Write warning to stderr."""
    json.dump({"warning": message}, sys.stderr)
    sys.stderr.write("\n")


def handle_errors(fn: Callable) -> Callable:
    """Decorator wrapping CLI commands for structured error output."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except SystemExit:
            raise  # Already handled with structured error
        except httpx.ConnectError:
            _emit_error(CLIError(code="connection_error", message="Could not connect to API server"))
            raise SystemExit(1)
        except httpx.TimeoutException:
            _emit_error(CLIError(code="timeout", message="API request timed out"))
            raise SystemExit(1)
        except httpx.HTTPError as exc:
            _emit_error(CLIError(code="http_error", message=f"HTTP error: {type(exc).__name__}"))
            raise SystemExit(1)
        except Exception:
            _emit_error(CLIError(code="unexpected_error", message="An unexpected error occurred"))
            raise SystemExit(1)

    return wrapper
