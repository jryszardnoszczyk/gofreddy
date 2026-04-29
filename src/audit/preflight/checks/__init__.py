"""Check modules — one per thematic group of deterministic preflight checks.

Each module exposes `async def check(domain: str) -> dict`. The return dict
is free-form per module (each produces a different signal shape) and becomes
a context key downstream agents read verbatim.

See `src/audit/preflight/runner.py` for dispatch and aggregation.
"""
from __future__ import annotations

from . import assets, badges, dns, headers, schema, social, tooling, wellknown

__all__ = [
    "assets", "badges", "dns", "headers",
    "schema", "social", "tooling", "wellknown",
]
