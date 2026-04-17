"""Rate limiting configuration (slowapi).

Ported from freddy/src/api/rate_limit.py with the Redis branch dropped —
Phase 1 runs on a single Fly VM so in-memory storage is sufficient. When we
scale to 2+ VMs, read REDIS_URL from env and pass it as storage_uri.
"""
from __future__ import annotations

import logging

from slowapi import Limiter
from starlette.requests import Request

logger = logging.getLogger(__name__)


def get_real_client_ip(request: Request) -> str:
    """Extract real client IP.

    Fly.io injects Fly-Client-IP. We fall back to request.client.host when the
    header is absent (e.g., local uvicorn, cURL directly).
    """
    fly_ip = request.headers.get("fly-client-ip")
    if fly_ip:
        return fly_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


# Module-level limiter — @limiter.limit() decorators capture this at import time,
# so it must be created once and referenced from main.py.
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["30/minute"],
    storage_uri="memory://",
)
