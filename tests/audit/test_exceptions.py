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


def test_rate_limit_hit_carries_metadata():
    err = RateLimitHit(
        resets_at=1735689600,
        rate_limit_type="5h",
        overage_disabled_reason="account_disabled",
    )
    assert isinstance(err, AuditError)
    assert err.resets_at == 1735689600
    assert err.rate_limit_type == "5h"
    assert err.overage_disabled_reason == "account_disabled"
    assert "resetsAt=1735689600" in str(err)
    assert "5h" in str(err)
    assert "account_disabled" in str(err)


def test_rate_limit_hit_default_construction():
    err = RateLimitHit()
    assert err.resets_at == 0
    assert err.rate_limit_type == ""
    assert err.overage_disabled_reason == ""


def test_audit_error_is_an_exception():
    assert issubclass(AuditError, Exception)
