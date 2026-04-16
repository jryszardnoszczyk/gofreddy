"""MentionFetcher protocol and BaseMentionFetcher ABC with shared resilience logic."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Protocol

from ..common.circuit_breaker import CircuitBreaker
from .config import MonitoringSettings
from .exceptions import MentionFetchError
from .models import DataSource, RawMention

logger = logging.getLogger(__name__)


class MentionFetcher(Protocol):
    """Protocol for monitoring data source adapters.

    Each adapter fetches mentions for a query from one external source.
    Implementations in PR-065 (NewsData, Xpoz, TikTok), PR-069, PR-070.
    """

    @property
    def source(self) -> DataSource: ...

    async def fetch_mentions(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        """Fetch mentions matching query.

        Returns:
            Tuple of (mentions, next_cursor). next_cursor is None when exhausted.

        Raises:
            MentionFetchError: On unrecoverable fetch failure
        """
        ...


class BaseMentionFetcher(ABC):
    """ABC with shared retry, circuit breaker, and semaphore logic.

    Subclasses implement _do_fetch() with source-specific API calls.
    """

    MAX_RETRIES = 3
    BASE_DELAY = 1.0

    def __init__(
        self,
        settings: MonitoringSettings | None = None,
        timeout_override: float | None = None,
    ) -> None:
        self._settings = settings or MonitoringSettings()
        self._timeout_override = timeout_override
        self._semaphore = asyncio.Semaphore(self._settings.adapter_concurrency)
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self._settings.circuit_breaker_threshold,
            reset_timeout=self._settings.circuit_breaker_reset_seconds,
            name=self.source.value,
        )

    @property
    @abstractmethod
    def source(self) -> DataSource:
        """The data source this adapter handles."""

    @abstractmethod
    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        """Source-specific fetch implementation."""

    async def fetch_mentions(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        """Fetch with circuit breaker, retry, and semaphore."""
        if not self._circuit_breaker.allow_request():
            logger.warning(
                "adapter_circuit_open",
                extra={"source": self.source.value},
            )
            raise MentionFetchError(
                f"Circuit breaker open for {self.source.value}"
            )

        async with self._semaphore:
            last_error: Exception | None = None
            timeout = self._timeout_override or self._settings.adapter_timeout_seconds
            for attempt in range(self.MAX_RETRIES):
                try:
                    result = await asyncio.wait_for(
                        self._do_fetch(query, cursor=cursor, limit=limit),
                        timeout=timeout,
                    )
                    self._circuit_breaker.record_success()
                    return result
                except asyncio.TimeoutError:
                    last_error = MentionFetchError(
                        f"{self.source.value} timeout after {timeout}s"
                    )
                    self._circuit_breaker.record_failure()
                except MentionFetchError:
                    raise  # Unrecoverable — don't retry
                except Exception as e:
                    last_error = e
                    self._circuit_breaker.record_failure()
                    logger.warning(
                        "adapter_fetch_retry",
                        extra={
                            "source": self.source.value,
                            "attempt": attempt + 1,
                            "error": str(e),
                        },
                    )

                if attempt < self.MAX_RETRIES - 1:
                    delay = self.BASE_DELAY * (2**attempt)
                    await asyncio.sleep(delay)

            raise MentionFetchError(
                f"{self.source.value} failed after {self.MAX_RETRIES} attempts: "
                f"{last_error}"
            )

    async def close(self) -> None:
        """Clean up adapter resources. Override in subclasses that hold connections."""
