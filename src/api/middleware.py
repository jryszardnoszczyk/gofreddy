"""Request-ID middleware + body size limit.

RequestIDMiddleware is ported verbatim from freddy/src/api/main.py L42-84 —
it uses raw ASGI protocol instead of BaseHTTPMiddleware to preserve the
ContextVar across async boundaries (BaseHTTPMiddleware breaks it).
"""
from __future__ import annotations

import re
import uuid
from contextvars import ContextVar

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders

# Sole source of request-trace truth. Set by RequestIDMiddleware on every
# HTTP request; read by structured loggers (future) to correlate log lines.
trace_context: ContextVar[dict[str, str]] = ContextVar("trace_context", default={})


class RequestIDMiddleware:
    """Pure ASGI middleware for X-Request-ID header + ContextVar propagation."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        raw_headers = scope.get("headers", [])
        req_id = next(
            (v.decode() for k, v in raw_headers if k == b"x-request-id"),
            None,
        ) or str(uuid.uuid4())

        token = trace_context.set({"request_id": req_id})

        async def send_with_id(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("X-Request-ID", req_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            trace_context.reset(token)


# Paths exempt from the 1MB request body limit. Phase 1 has no large-payload
# endpoints; Phase 3 `/v1/clients/<slug>/snapshot` (CLI sync tarball) will
# need to be added here.
_EXEMPT_BODY_LIMIT_PATHS = re.compile(r"(?!)")  # matches nothing by default


async def limit_request_body(request: Request, call_next):
    """Reject requests with Content-Length > 1MB outside exempt paths."""
    if _EXEMPT_BODY_LIMIT_PATHS.match(request.url.path):
        return await call_next(request)
    content_length = request.headers.get("content-length")
    try:
        if content_length and int(content_length) > 1_048_576:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "payload_too_large",
                        "message": "Request body exceeds 1MB limit",
                    }
                },
            )
    except (ValueError, TypeError):
        pass
    return await call_next(request)
