"""Tests for shared CircuitBreaker."""

import time
from unittest.mock import patch

from src.common.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreakerStates:
    def test_starts_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert not cb.is_open()
        assert cb.allow_request()

    def test_closed_to_open_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.is_open()
        assert not cb.allow_request()

    def test_open_to_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=1.0)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Simulate time passing
        cb._last_failure_time = time.monotonic() - 2.0
        assert cb.state == CircuitState.HALF_OPEN
        assert not cb.is_open()
        assert cb.allow_request()

    def test_half_open_to_closed_on_success(self):
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        cb._last_failure_time = time.monotonic() - 1.0
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request()

    def test_half_open_to_open_on_failure(self):
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        cb._last_failure_time = time.monotonic() - 1.0
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

        # Need full threshold again
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

    def test_is_open_backward_compatible(self):
        """is_open() returns True when OPEN, False when CLOSED or HALF_OPEN."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.01)
        assert not cb.is_open()  # CLOSED

        cb.record_failure()
        assert cb.is_open()  # OPEN

        cb._last_failure_time = time.monotonic() - 1.0
        assert not cb.is_open()  # HALF_OPEN

    def test_name_parameter(self):
        cb = CircuitBreaker(name="test_source")
        assert cb.name == "test_source"

    def test_uses_monotonic_time(self):
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=10.0)
        with patch("src.common.circuit_breaker.time.monotonic", return_value=100.0):
            cb.record_failure()
        assert cb._last_failure_time == 100.0

    def test_custom_thresholds(self):
        cb = CircuitBreaker(failure_threshold=5, reset_timeout=120.0)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
