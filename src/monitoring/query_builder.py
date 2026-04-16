"""Shared query builder for monitor configurations.

Stateless/pure — no service dependencies to avoid circular imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Monitor


def build_monitor_query(monitor: Monitor) -> str:
    """Build canonical query from monitor config.

    Priority:
    1. boolean_query if explicitly set
    2. All keywords joined with OR
    3. Empty string fallback (will be rejected by sanitizers)
    """
    if monitor.boolean_query:
        return monitor.boolean_query
    if monitor.keywords:
        return " OR ".join(monitor.keywords)
    return ""
