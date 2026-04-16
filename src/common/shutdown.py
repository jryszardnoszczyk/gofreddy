"""Shared SIGTERM handler — single registration, both workers read."""

import logging
import signal
from typing import Any

logger = logging.getLogger(__name__)

_shutdown_requested = False


def _handle_sigterm(_signum: int, _frame: Any) -> None:
    global _shutdown_requested
    _shutdown_requested = True
    logger.warning("SIGTERM received, will checkpoint after current unit of work")


signal.signal(signal.SIGTERM, _handle_sigterm)


def is_shutdown_requested() -> bool:
    return _shutdown_requested


def reset_shutdown_state() -> None:
    """Reset shutdown state (for testing)."""
    global _shutdown_requested
    _shutdown_requested = False
