"""Cloro AI search monitoring client.

Queries ChatGPT, Perplexity, Gemini, Grok, Copilot, Google AI Mode, Claude
via Cloro unified API. Uses Freddy's CircuitBreaker (not aiobreaker).
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from ...common.circuit_breaker import CircuitBreaker
from ...common.cost_recorder import cost_recorder as _cost_recorder

logger = logging.getLogger(__name__)


# ============================================================================
# Response Models
# ============================================================================


class CitationMetrics(BaseModel):
    """Positional metrics for a citation within an AI response.

    Attributes:
        word_count: Word count of the full AI response text.
        position: 1-based position of this citation in the response (1st, 2nd, 3rd...).
        position_weight: Weight based on position (1st=1.0, 2nd=0.8, 3rd=0.6, etc.).
        word_pos_score: word_count × position_weight — higher means more prominent citation.
    """

    word_count: int = 0
    position: int = 0
    position_weight: float = 0.0
    word_pos_score: float = 0.0


def _position_weight(position: int) -> float:
    """Compute position weight: 1st=1.0, 2nd=0.8, 3rd=0.6, 4th+=0.4 (floor)."""
    if position <= 0:
        return 0.0
    return max(0.4, 1.0 - (position - 1) * 0.2)


class Citation(BaseModel):
    """Extracted citation from AI response."""

    url: str
    title: str = ""
    source: str = ""
    metrics: CitationMetrics | None = None


class AIResponse(BaseModel):
    """Normalized response from a single AI platform."""

    platform: str
    text: str
    markdown: str | None = None
    citations: list[Citation] = Field(default_factory=list)


class QueryResult(BaseModel):
    """Result from querying multiple platforms."""

    results: dict[str, AIResponse] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)

    @property
    def has_results(self) -> bool:
        return len(self.results) > 0


# ============================================================================
# Request Validation
# ============================================================================

VALID_PLATFORMS = frozenset({
    "chatgpt",
    "perplexity",
    "gemini",
    "grok",
    "google_ai_mode",
    "copilot",
    "claude",
})


class QueryRequest(BaseModel):
    """Validated query request."""

    prompt: str = Field(..., min_length=1, max_length=10_000)
    platforms: list[str] = Field(
        default_factory=lambda: ["chatgpt", "perplexity", "gemini"]
    )
    country: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 country code",
    )

    @field_validator("platforms")
    @classmethod
    def validate_platforms(cls, v: list[str]) -> list[str]:
        if not v:
            return ["chatgpt", "perplexity", "gemini"]
        if len(v) > 10:
            raise ValueError("Too many platforms (max 10)")
        invalid = set(v) - VALID_PLATFORMS
        if invalid:
            raise ValueError(f"Invalid platforms: {invalid}. Valid: {VALID_PLATFORMS}")
        return v


# ============================================================================
# Cloro Client
# ============================================================================

# Cloro API cost estimate per query (for cost recording)
CLORO_COST_PER_QUERY = 0.01


class CloroError(Exception):
    """Cloro API error."""

    def __init__(self, message: str, platform: str | None = None):
        self.platform = platform
        super().__init__(message)


class CloroClientError(CloroError):
    """Client error (4xx except 429) - should NOT trip circuit breaker."""

    pass


class CloroRateLimitError(CloroError):
    """429 rate limit - retryable."""

    pass


@dataclass
class CloroClient:
    """Cloro API client with Freddy's CircuitBreaker."""

    api_key: str = field(repr=False)
    base_url: str = "https://api.cloro.dev/v1/monitor"
    timeout: float = 60.0  # 60s+ per plan requirement
    _breaker: CircuitBreaker = field(default=None, repr=False, init=False)
    _client: httpx.AsyncClient = field(default=None, repr=False, init=False)

    def __post_init__(self):
        self._breaker = CircuitBreaker(
            failure_threshold=3,
            reset_timeout=300.0,  # 5 minutes
            name="cloro",
        )
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        """Close the persistent HTTP client."""
        if self._client:
            await self._client.aclose()

    @property
    def is_available(self) -> bool:
        return self._breaker.allow_request()

    @property
    def circuit_state(self) -> str:
        return self._breaker.state.value

    async def query(self, request: QueryRequest) -> QueryResult:
        """Query multiple AI platforms via Cloro."""

        async def query_platform(
            platform: str,
        ) -> tuple[str, AIResponse | None, str | None]:
            if not self._breaker.allow_request():
                return platform, None, "Service temporarily unavailable (circuit open)"
            try:
                response = await self._request_with_retry(platform, request.prompt, request.country)
                self._breaker.record_success()
                return platform, response, None
            except CloroClientError as e:
                # 4xx errors don't trip circuit
                return platform, None, str(e)
            except CloroError as e:
                # retry helper already recorded breaker failure
                return platform, None, str(e)
            except Exception as e:
                logger.exception("Unexpected error querying %s", platform)
                return platform, None, "An unexpected error occurred"

        tasks = [query_platform(p) for p in request.platforms]
        results = await asyncio.gather(*tasks)

        successful = {}
        errors = {}
        for platform, response, error in results:
            if response:
                successful[platform] = response
            if error:
                errors[platform] = error

        return QueryResult(results=successful, errors=errors)

    async def _request_with_retry(self, platform: str, prompt: str, country: str | None, max_retries: int = 3) -> AIResponse:
        """Make request with exponential backoff and circuit breaker awareness."""
        for attempt in range(max_retries):
            try:
                return await self._make_request(platform, prompt, country)
            except CloroClientError:
                raise  # 4xx: do not retry, do not trip breaker
            except CloroError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt * 2)  # 2s, 4s, 8s
                    continue
                self._breaker.record_failure()
                raise

    async def _make_request(
        self, platform: str, prompt: str, country: str | None
    ) -> AIResponse:
        """Make single platform request to Cloro."""
        url = f"{self.base_url}/{platform}"

        payload: dict[str, Any] = {
            "prompt": prompt,
            "include": {"markdown": True},
            # Cloro API (2026-04-xx onwards) requires `country` as mandatory.
            # Default to US when caller doesn't specify a country code.
            "country": country or "US",
        }

        try:
            response = await self._client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 401:
                raise CloroClientError("Invalid API key", platform)
            elif status == 403:
                raise CloroClientError("Access forbidden", platform)
            elif status == 400:
                raise CloroClientError("Bad request", platform)
            elif status == 404:
                raise CloroClientError(f"Platform not found: {platform}", platform)
            elif status == 429:
                raise CloroRateLimitError("Rate limit exceeded", platform)
            elif status >= 500:
                raise CloroError(f"Cloro server error: {status}", platform)
            else:
                raise CloroClientError(f"Client error: {status}", platform)
        except httpx.TimeoutException:
            raise CloroError(f"Request timed out after {self.timeout}s", platform)
        except httpx.RequestError as e:
            raise CloroError(f"Request failed: {e}", platform)

        # Record cost
        await _cost_recorder.record(
            "cloro",
            f"{platform}_query",
            cost_usd=CLORO_COST_PER_QUERY,
        )

        return self._parse_response(platform, response)

    def _parse_response(self, platform: str, response: httpx.Response) -> AIResponse:
        """Parse and validate Cloro response."""
        try:
            data = response.json()
        except ValueError as e:
            raise CloroError(f"Invalid JSON response: {e}", platform)

        if not data.get("success"):
            error_obj = data.get("error", {})
            error_msg = error_obj.get("message", "Unknown error") if isinstance(error_obj, dict) else str(error_obj)
            low = error_msg.lower()
            if "credit" in low or "quota" in low or "exhausted" in low:
                raise CloroClientError(f"Cloro credit/quota exhausted: {error_msg}", platform)
            raise CloroError(f"Cloro returned error: {error_msg}", platform)

        result = data.get("result", {})
        response_text = result.get("text", "")

        return AIResponse(
            platform=platform,
            text=response_text,
            markdown=result.get("markdown"),
            citations=self._extract_citations(result, response_text),
        )

    def _extract_citations(
        self, result: dict[str, Any], response_text: str = "",
    ) -> list[Citation]:
        """Extract citations from Cloro response with positional metrics.

        Metrics computed per citation:
        - Word: word count of the full AI response text
        - Pos: 1-based position among all citations
        - WordPos: word_count × position_weight (1st=1.0, 2nd=0.8, 3rd=0.6, 4th+=0.4)
        """
        raw_citations: list[tuple[str, str, str]] = []  # (url, title, source)

        for card in result.get("shoppingCards", []):
            if url := card.get("url"):
                raw_citations.append((url, card.get("title", ""), card.get("merchant", "")))

        for src in result.get("sources", []):
            if url := src.get("url"):
                raw_citations.append((url, src.get("title", ""), src.get("source", "")))

        word_count = len(response_text.split()) if response_text else 0

        citations = []
        for i, (url, title, source) in enumerate(raw_citations, start=1):
            weight = _position_weight(i)
            citations.append(
                Citation(
                    url=url,
                    title=title,
                    source=source,
                    metrics=CitationMetrics(
                        word_count=word_count,
                        position=i,
                        position_weight=round(weight, 2),
                        word_pos_score=round(word_count * weight, 1),
                    ),
                )
            )

        return citations
