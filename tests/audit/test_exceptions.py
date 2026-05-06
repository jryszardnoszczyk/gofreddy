"""Exception hierarchy tests — every typed error inherits from AuditError."""
from __future__ import annotations

import pytest

from src.audit.exceptions import (
    AuditError,
    EvolveLockHeld,
    LaneRegistrationError,
    MalformedSubSignalError,
    RateLimitHit,
    ViableResumeFailed,
)


@pytest.mark.parametrize(
    "exc_cls",
    [
        RateLimitHit,
        ViableResumeFailed,
        MalformedSubSignalError,
        LaneRegistrationError,
        EvolveLockHeld,
    ],
)
def test_inherits_from_audit_error(exc_cls):
    assert issubclass(exc_cls, AuditError)
    instance = exc_cls("boom")
    assert isinstance(instance, AuditError)
    assert isinstance(instance, Exception)
    assert str(instance) == "boom"


def test_audit_error_is_an_exception():
    assert issubclass(AuditError, Exception)


def test_typed_errors_carry_message():
    err = RateLimitHit("rate limit hit, resets at ...")
    assert "rate limit" in str(err)
