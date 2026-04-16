"""PublishAdapter protocol and BasePublisher ABC with shared resilience logic."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Protocol

from ..common.circuit_breaker import CircuitBreaker
from .config import PublishingSettings
from .exceptions import AdapterError, CredentialError
from .models import PublishPlatform, PublishResult, QueueItem

logger = logging.getLogger(__name__)


class PublishAdapter(Protocol):
    """Protocol for publishing platform adapters."""

    @property
    def platform(self) -> PublishPlatform: ...

    async def publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult: ...

    async def validate_credentials(self, credentials: dict[str, str]) -> bool: ...


class BasePublisher(ABC):
    """ABC with shared retry, circuit breaker, and semaphore logic.

    Subclasses implement _do_publish() with platform-specific API calls.
    Mirrors BaseMentionFetcher from src/monitoring/fetcher_protocol.py.
    """

    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    PUBLISH_TIMEOUT: float | None = None

    def __init__(self, settings: PublishingSettings | None = None) -> None:
        self._settings = settings or PublishingSettings()
        self._semaphore = asyncio.Semaphore(self._settings.adapter_concurrency)
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self._settings.circuit_breaker_threshold,
            reset_timeout=self._settings.circuit_breaker_reset_seconds,
            name=f"publisher_{self.platform.value}",
        )

    @property
    @abstractmethod
    def platform(self) -> PublishPlatform: ...

    @abstractmethod
    async def _do_publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult: ...

    @abstractmethod
    async def validate_credentials(self, credentials: dict[str, str]) -> bool: ...

    async def publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult:
        """Publish with circuit breaker, retry, semaphore, and per-item timeout."""
        if not self._circuit_breaker.allow_request():
            logger.warning(
                "publisher_circuit_open",
                extra={"platform": self.platform.value},
            )
            return PublishResult(
                success=False,
                error_message=f"Circuit breaker open for {self.platform.value}",
            )

        async with self._semaphore:
            last_error: str | None = None
            timeout = self.PUBLISH_TIMEOUT or self._settings.adapter_timeout_seconds

            for attempt in range(self.MAX_RETRIES):
                try:
                    result = await asyncio.wait_for(
                        self._do_publish(item, credentials),
                        timeout=timeout,
                    )
                    self._circuit_breaker.record_success()
                    return result
                except asyncio.TimeoutError:
                    last_error = f"{self.platform.value} timeout after {timeout}s"
                    self._circuit_breaker.record_failure()
                except (CredentialError, AdapterError) as e:
                    # Non-retryable — auth/config errors
                    self._circuit_breaker.record_failure()
                    return PublishResult(
                        success=False,
                        error_message=str(e),
                    )
                except Exception:
                    last_error = f"{self.platform.value} publish error"
                    self._circuit_breaker.record_failure()
                    logger.warning(
                        "publisher_retry",
                        extra={
                            "platform": self.platform.value,
                            "attempt": attempt + 1,
                        },
                        exc_info=True,
                    )

                if attempt < self.MAX_RETRIES - 1:
                    delay = self.BASE_DELAY * (2**attempt)
                    await asyncio.sleep(delay)

            return PublishResult(
                success=False,
                error_message=last_error
                or f"{self.platform.value} failed after {self.MAX_RETRIES} attempts",
            )

    async def close(self) -> None:
        """Clean up adapter resources. Override in subclasses."""
