"""Exception handlers — normalize all errors into {"error": {"code", "message"}}.

Ported from freddy/src/api/exceptions.py with the domain-specific handlers
removed (GeminiRateLimitError, InsufficientCredits, CreatorNotFoundError,
VideoUnavailableError, QueryParseError, SearchError) — gofreddy doesn't have
those domains.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_STATUS_CODE_MAP = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    503: "service_unavailable",
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers producing normalized error envelopes."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Normalize HTTPExceptions to {"error": {...}} envelope."""
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail},
            )
        code = _STATUS_CODE_MAP.get(exc.status_code, "error")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": str(exc.detail)}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Strip input values + context from validation errors to prevent
        leaking user data or internal details in responses."""
        safe_errors = [
            {k: v for k, v in err.items() if k in ("type", "loc", "msg")}
            for err in exc.errors()
        ]
        field_hints = [
            f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
            for err in safe_errors
            if err.get("loc") and err.get("msg")
        ]
        summary = "; ".join(field_hints[:3])
        message = (
            f"Request validation failed: {summary}"
            if summary
            else "Request validation failed"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "validation_error",
                    "message": message,
                    "details": safe_errors,
                }
            },
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(
        request: Request, exc: PermissionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": "forbidden",
                    "message": str(exc) or "Permission denied",
                }
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "bad_request",
                    "message": str(exc) or "Invalid request",
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        error_id = str(uuid.uuid4())[:8]
        logger.error(
            f"Unhandled exception [{error_id}]: {exc}",
            exc_info=True,
            extra={
                "error_id": error_id,
                "path": str(request.url),
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": f"Internal server error. Reference: {error_id}",
                }
            },
        )
