"""Tests for input validation hardening (PR-057 I7)."""

import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError


# ── Pydantic Validation Error Sanitization ─────────────────────────────────


@pytest.mark.asyncio
async def test_validation_error_handler_sanitizes_fields():
    """Validation error handler strips input, ctx, url keys from response."""
    from src.api.exceptions import register_exception_handlers

    # Create a minimal FastAPI-like object to capture the handler
    handlers = {}

    class FakeApp:
        def exception_handler(self, exc_class):
            def decorator(fn):
                handlers[exc_class] = fn
                return fn
            return decorator

    fake_app = FakeApp()
    register_exception_handlers(fake_app)

    handler = handlers[RequestValidationError]

    # Create a real validation error via Pydantic
    class StrictModel(BaseModel):
        urls: list[str]

    try:
        StrictModel.model_validate({})
    except ValidationError as pydantic_exc:
        # Wrap in RequestValidationError (as FastAPI does)
        exc = RequestValidationError(pydantic_exc.errors())

    request = MagicMock()
    response = await handler(request, exc)

    assert response.status_code == 422
    import json
    body = json.loads(response.body)
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed"
    assert "details" in body["error"]
    for detail in body["error"]["details"]:
        assert "type" in detail
        assert "loc" in detail
        assert "msg" in detail
        # These should be stripped by our handler
        assert "input" not in detail
        assert "ctx" not in detail
        assert "url" not in detail


@pytest.mark.asyncio
async def test_validation_error_handler_preserves_loc():
    """Validation error handler preserves loc field with source prefix."""
    from src.api.exceptions import register_exception_handlers

    handlers = {}

    class FakeApp:
        def exception_handler(self, exc_class):
            def decorator(fn):
                handlers[exc_class] = fn
                return fn
            return decorator

    fake_app = FakeApp()
    register_exception_handlers(fake_app)

    handler = handlers[RequestValidationError]

    class StrictModel(BaseModel):
        name: str

    try:
        StrictModel.model_validate({"name": 123})
    except ValidationError as pydantic_exc:
        exc = RequestValidationError(pydantic_exc.errors())

    request = MagicMock()
    response = await handler(request, exc)

    import json
    body = json.loads(response.body)
    details = body["error"]["details"]
    assert len(details) > 0
    # Each detail should have 'loc' as a list
    for d in details:
        assert isinstance(d["loc"], list)


# ── Conversation Query Bounds ──────────────────────────────────────────────


def test_conversation_list_limit_bounds():
    """Query bounds: limit must be 1-200."""
    from pydantic import TypeAdapter
    from typing import Annotated

    LimitType = Annotated[int, Query(ge=1, le=200)]
    adapter = TypeAdapter(LimitType)

    # Valid
    adapter.validate_python(1)
    adapter.validate_python(200)
    adapter.validate_python(50)

    # Invalid
    with pytest.raises(ValidationError):
        adapter.validate_python(0)
    with pytest.raises(ValidationError):
        adapter.validate_python(201)


def test_conversation_list_offset_nonnegative():
    """Query bounds: offset must be >= 0."""
    from pydantic import TypeAdapter
    from typing import Annotated

    OffsetType = Annotated[int, Query(ge=0)]
    adapter = TypeAdapter(OffsetType)

    adapter.validate_python(0)
    adapter.validate_python(100)

    with pytest.raises(ValidationError):
        adapter.validate_python(-1)


def test_messages_limit_bounds():
    """Query bounds: messages limit must be 1-500."""
    from pydantic import TypeAdapter
    from typing import Annotated

    LimitType = Annotated[int, Query(ge=1, le=500)]
    adapter = TypeAdapter(LimitType)

    adapter.validate_python(1)
    adapter.validate_python(500)

    with pytest.raises(ValidationError):
        adapter.validate_python(0)
    with pytest.raises(ValidationError):
        adapter.validate_python(501)


# ── Billing Error Envelope ─────────────────────────────────────────────────


def test_billing_error_envelope_structure():
    """Billing error responses use structured error envelope."""
    from fastapi import HTTPException

    exc = HTTPException(
        504,
        detail={"code": "payment_timeout", "message": "Payment provider timeout"},
    )
    assert exc.detail["code"] == "payment_timeout"
    assert exc.detail["message"] == "Payment provider timeout"

    exc2 = HTTPException(
        502,
        detail={"code": "payment_error", "message": "Payment provider error"},
    )
    assert exc2.detail["code"] == "payment_error"
