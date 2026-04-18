"""Search module exceptions."""


class SearchError(Exception):
    """Base search exception."""

    pass


class QueryParseError(SearchError):
    """Failed to parse natural language query."""

    def __init__(self, message: str, raw_query: str) -> None:
        self.raw_query = raw_query
        super().__init__(message)


class PlatformSearchError(SearchError):
    """Error during platform-specific search."""

    def __init__(self, platform: str, message: str) -> None:
        self.platform = platform
        super().__init__(f"[{platform}] {message}")


class ProviderUnavailableError(SearchError):
    """Raised when a search provider (IC or IIQ) is unavailable."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self._detail = detail
        super().__init__(f"Provider unavailable (HTTP {status_code})")

    @property
    def detail(self) -> str:
        """Access raw detail for structured logging only."""
        return self._detail


class ICUnavailableError(ProviderUnavailableError):
    """Influencers.club unavailable — caller should fall back."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code, detail)
        Exception.__init__(self, f"IC unavailable (HTTP {status_code})")
