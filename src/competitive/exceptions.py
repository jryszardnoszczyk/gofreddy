"""Competitive intelligence exceptions."""


class CompetitiveError(Exception):
    """Base exception for competitive intelligence operations."""


class ForeplayError(CompetitiveError):
    """Foreplay API errors."""


class AdyntelError(CompetitiveError):
    """Adyntel API errors."""


class ProviderUnavailableError(CompetitiveError):
    """Raised when a single provider's circuit breaker is open."""


class AllProvidersUnavailableError(CompetitiveError):
    """Raised when no ad provider is reachable."""


class BriefNotFoundError(CompetitiveError):
    """Raised when a brief is not found or ownership check fails."""


class BriefGenerationError(CompetitiveError):
    """Raised when brief generation fails."""
