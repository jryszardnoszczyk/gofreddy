"""Strict backend → ConcurrencyController resource mapping in evaluate_variant.

Replaces the silent ``.get(backend, "opencode")`` fallback that would route
unknown backends to the wrong cap. Anything outside {claude,codex,opencode}
must raise loudly so misconfiguration fails closed instead of blowing past
the configured global cap.
"""

from __future__ import annotations

import pytest

import evaluate_variant


def test_resource_for_backend_known_backends_map_directly():
    assert evaluate_variant._resource_for_backend("claude") == "claude"
    assert evaluate_variant._resource_for_backend("codex") == "codex"
    assert evaluate_variant._resource_for_backend("opencode") == "opencode"


def test_resource_for_backend_unknown_raises_value_error():
    with pytest.raises(ValueError, match="Unknown eval backend"):
        evaluate_variant._resource_for_backend("anthropic_sdk")
    with pytest.raises(ValueError, match="Unknown eval backend"):
        evaluate_variant._resource_for_backend("")
    with pytest.raises(ValueError, match="Unknown eval backend"):
        evaluate_variant._resource_for_backend("CLAUDE")  # case-sensitive


def test_resource_for_backend_error_lists_known_backends():
    """The error message must guide the operator to the fix location."""
    try:
        evaluate_variant._resource_for_backend("gemini")
    except ValueError as exc:
        message = str(exc)
        assert "claude" in message and "codex" in message and "opencode" in message
        assert "_BACKEND_TO_RESOURCE" in message
    else:
        pytest.fail("expected ValueError for unknown backend")
